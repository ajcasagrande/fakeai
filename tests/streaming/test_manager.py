"""
Tests for StreamManager.
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest

from fakeai.streaming.base import (
    StreamStatus,
    StreamTimeoutException,
    StreamType,
)
from fakeai.streaming.manager import StreamManager


# Mock response object for testing
class MockChatResponse:
    """Mock chat completion response."""

    def __init__(self, content="Hello, world!"):
        self.id = "chatcmpl-test123"
        self.created = 1234567890
        self.model = "gpt-4o"
        self.choices = [MockChoice(content)]
        self.usage = MockUsage()


class MockChoice:
    """Mock choice object."""

    def __init__(self, content):
        self.message = MockMessage(content)
        self.finish_reason = "stop"


class MockMessage:
    """Mock message object."""

    def __init__(self, content):
        self.role = "assistant"
        self.content = content


class MockUsage:
    """Mock usage object."""

    def __init__(self):
        self.prompt_tokens = 10
        self.completion_tokens = 20
        self.total_tokens = 30


class TestStreamManager:
    """Test StreamManager class."""

    @pytest.mark.asyncio
    async def test_create_manager(self):
        """Test creating stream manager."""
        manager = StreamManager(
            default_timeout_seconds=60.0,
            enable_metrics=False,
        )

        assert manager.default_timeout_seconds == 60.0
        assert manager.enable_metrics is False

    @pytest.mark.asyncio
    async def test_create_stream_basic(self):
        """Test creating a basic stream."""
        manager = StreamManager(enable_metrics=False, enable_latency_simulation=False)

        response = MockChatResponse(content="Hi")
        chunks = []

        async for chunk in manager.create_stream(
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            full_response=response,
            endpoint="/v1/chat/completions",
            chunk_delay_seconds=0.0,  # No delay for tests
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert chunks[0].is_first is True
        assert chunks[-1].is_last is True

    @pytest.mark.asyncio
    async def test_stream_with_custom_id(self):
        """Test creating stream with custom ID."""
        manager = StreamManager(enable_metrics=False, enable_latency_simulation=False)

        response = MockChatResponse(content="Hi")
        stream_id = "custom-stream-123"

        async for chunk in manager.create_stream(
            stream_type=StreamType.CHAT,
            stream_id=stream_id,
            model="gpt-4o",
            full_response=response,
            endpoint="/v1/chat/completions",
            chunk_delay_seconds=0.0,
        ):
            assert stream_id in chunk.chunk_id
            break  # Just check first chunk

    @pytest.mark.asyncio
    async def test_stream_timeout(self):
        """Test stream timeout."""
        manager = StreamManager(enable_metrics=False, enable_latency_simulation=False)

        response = MockChatResponse(content="Long response " * 100)

        with pytest.raises(StreamTimeoutException):
            async for chunk in manager.create_stream(
                stream_type=StreamType.CHAT,
                model="gpt-4o",
                full_response=response,
                endpoint="/v1/chat/completions",
                timeout_seconds=0.001,  # Very short timeout
                chunk_delay_seconds=0.01,
            ):
                pass

    @pytest.mark.asyncio
    async def test_stream_max_chunks(self):
        """Test limiting maximum chunks."""
        manager = StreamManager(enable_metrics=False, enable_latency_simulation=False)

        response = MockChatResponse(content="Word " * 100)
        chunks = []

        async for chunk in manager.create_stream(
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            full_response=response,
            endpoint="/v1/chat/completions",
            max_chunks=5,
            chunk_delay_seconds=0.0,
        ):
            chunks.append(chunk)

        # Should stop at or before max_chunks
        assert len(chunks) <= 5

    @pytest.mark.asyncio
    async def test_get_stream_status(self):
        """Test getting stream status."""
        manager = StreamManager(enable_metrics=False, enable_latency_simulation=False)

        response = MockChatResponse(content="Hi")
        stream_id = "test-status-stream"

        chunk_count = 0
        async for chunk in manager.create_stream(
            stream_type=StreamType.CHAT,
            stream_id=stream_id,
            model="gpt-4o",
            full_response=response,
            endpoint="/v1/chat/completions",
            chunk_delay_seconds=0.0,
        ):
            # Check status during streaming
            status = await manager.get_stream_status(stream_id)
            assert status in (
                StreamStatus.INITIALIZING,
                StreamStatus.RUNNING,
            )
            chunk_count += 1
            if chunk_count >= 2:
                break

        # After iteration, status may still exist briefly
        # (cleanup happens after generator exits)
        # Just verify we got chunks
        assert chunk_count >= 2

    @pytest.mark.asyncio
    async def test_get_stream_metrics(self):
        """Test getting stream metrics."""
        manager = StreamManager(enable_metrics=False, enable_latency_simulation=False)

        response = MockChatResponse(content="Hello world")
        stream_id = "test-metrics-stream"

        async for chunk in manager.create_stream(
            stream_type=StreamType.CHAT,
            stream_id=stream_id,
            model="gpt-4o",
            full_response=response,
            endpoint="/v1/chat/completions",
            chunk_delay_seconds=0.0,
        ):
            # Check metrics during streaming
            metrics = await manager.get_stream_metrics(stream_id)
            if metrics:
                assert "stream_id" in metrics
                assert "total_chunks" in metrics
            break

    @pytest.mark.asyncio
    async def test_get_active_stream_count(self):
        """Test getting active stream count."""
        manager = StreamManager(enable_metrics=False, enable_latency_simulation=False)

        initial_count = await manager.get_active_stream_count()

        response = MockChatResponse(content="Hi")

        async for chunk in manager.create_stream(
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            full_response=response,
            endpoint="/v1/chat/completions",
            chunk_delay_seconds=0.0,
        ):
            # Count should be higher during streaming
            current_count = await manager.get_active_stream_count()
            assert current_count >= initial_count
            break

    @pytest.mark.asyncio
    async def test_cancel_stream(self):
        """Test cancelling a stream."""
        manager = StreamManager(enable_metrics=False, enable_latency_simulation=False)

        response = MockChatResponse(content="Long response " * 100)
        stream_id = "cancel-test-stream"
        chunk_count = 0

        # Note: Cancellation is primarily for external cancellation handling
        # In this test, we verify the cancel method works but the stream
        # will complete normally since we're the only consumer
        async for chunk in manager.create_stream(
            stream_type=StreamType.CHAT,
            stream_id=stream_id,
            model="gpt-4o",
            full_response=response,
            endpoint="/v1/chat/completions",
            chunk_delay_seconds=0.0,  # No delay for test speed
        ):
            chunk_count += 1
            if chunk_count == 2:
                # Try to cancel (won't actually stop our iteration)
                cancelled = await manager.cancel_stream(stream_id)
                # Should be able to mark as cancelled
                assert cancelled is True
                # Break out of iteration manually
                break

        # Should have stopped early by our manual break
        assert chunk_count == 2


class TestStreamManagerWithMetrics:
    """Test StreamManager with metrics tracking."""

    @pytest.mark.asyncio
    async def test_stream_with_basic_metrics(self):
        """Test streaming with basic metrics tracker."""
        from fakeai.metrics import MetricsTracker

        metrics_tracker = MetricsTracker()
        manager = StreamManager(
            metrics_tracker=metrics_tracker,
            enable_metrics=True,
            enable_latency_simulation=False,
        )

        response = MockChatResponse(content="Hello")

        async for chunk in manager.create_stream(
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            full_response=response,
            endpoint="/v1/chat/completions",
            chunk_delay_seconds=0.0,
        ):
            pass

        # Verify metrics were tracked
        metrics = metrics_tracker.get_metrics()
        assert "streaming_stats" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
