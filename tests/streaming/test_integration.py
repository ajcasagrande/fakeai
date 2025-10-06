"""
Integration tests for the complete streaming framework.

These tests verify end-to-end streaming workflows with all components.
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest

from fakeai.streaming import (
    JSONLinesFormatter,
    SSEFormatter,
    StreamManager,
    StreamType,
)


# Mock response objects
class MockChatResponse:
    """Mock chat completion response."""

    def __init__(self, content="Hello, world!"):
        self.id = "chatcmpl-test123"
        self.created = 1234567890
        self.model = "gpt-4o"
        self.choices = [MockChatChoice(content)]
        self.usage = MockUsage()


class MockChatChoice:
    """Mock chat choice."""

    def __init__(self, content):
        self.message = MockMessage(content)
        self.finish_reason = "stop"


class MockMessage:
    """Mock message."""

    def __init__(self, content):
        self.role = "assistant"
        self.content = content


class MockUsage:
    """Mock usage."""

    def __init__(self):
        self.prompt_tokens = 10
        self.completion_tokens = 20
        self.total_tokens = 30


class TestStreamingIntegration:
    """Integration tests for complete streaming workflow."""

    @pytest.mark.asyncio
    async def test_end_to_end_chat_streaming(self):
        """Test complete chat streaming workflow."""
        # Create manager
        manager = StreamManager(
            enable_metrics=False,
            enable_latency_simulation=False,
        )

        # Create response
        response = MockChatResponse(content="Hello, how are you?")

        # Stream and format as SSE
        sse_chunks = []

        async for chunk in manager.create_stream(
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            full_response=response,
            endpoint="/v1/chat/completions",
            chunk_delay_seconds=0.0,
        ):
            # Format as SSE
            sse_formatted = SSEFormatter.format(chunk)
            sse_chunks.append(sse_formatted)

        # Verify we got SSE-formatted output
        assert len(sse_chunks) > 0
        assert all("data: " in chunk for chunk in sse_chunks)

        # Verify final done signal
        done_signal = SSEFormatter.format_done()
        assert done_signal == "data: [DONE]\n\n"

    @pytest.mark.asyncio
    async def test_end_to_end_jsonl_streaming(self):
        """Test complete streaming workflow with JSON Lines format."""
        manager = StreamManager(
            enable_metrics=False,
            enable_latency_simulation=False,
        )

        response = MockChatResponse(content="Test message")

        jsonl_chunks = []

        async for chunk in manager.create_stream(
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            full_response=response,
            endpoint="/v1/chat/completions",
            chunk_delay_seconds=0.0,
        ):
            # Format as JSON Lines
            jsonl_formatted = JSONLinesFormatter.format(chunk)
            jsonl_chunks.append(jsonl_formatted)

        # Verify JSON Lines format
        assert len(jsonl_chunks) > 0
        assert all(chunk.endswith("\n") for chunk in jsonl_chunks)

        # Each line should be valid JSON
        import json

        for chunk_str in jsonl_chunks:
            parsed = json.loads(chunk_str.strip())
            assert "type" in parsed
            assert "sequence" in parsed

    @pytest.mark.asyncio
    async def test_streaming_with_metrics(self):
        """Test streaming with full metrics tracking."""
        from fakeai.metrics import MetricsTracker
        from fakeai.streaming_metrics import StreamingMetricsTracker

        # Create metrics trackers
        metrics_tracker = MetricsTracker()
        streaming_metrics_tracker = StreamingMetricsTracker()

        # Create manager with metrics
        manager = StreamManager(
            metrics_tracker=metrics_tracker,
            streaming_metrics_tracker=streaming_metrics_tracker,
            enable_metrics=True,
            enable_latency_simulation=False,
        )

        response = MockChatResponse(content="Test with metrics")

        async for chunk in manager.create_stream(
            stream_type=StreamType.CHAT,
            stream_id="metrics-test-stream",
            model="gpt-4o",
            full_response=response,
            endpoint="/v1/chat/completions",
            prompt_tokens=50,
            chunk_delay_seconds=0.0,
        ):
            pass

        # Verify basic metrics were tracked
        basic_metrics = metrics_tracker.get_metrics()
        assert "streaming_stats" in basic_metrics

        # Verify detailed streaming metrics were tracked
        assert streaming_metrics_tracker.get_completed_stream_count() > 0

    @pytest.mark.asyncio
    async def test_streaming_with_latency_simulation(self):
        """Test streaming with realistic latency simulation."""
        from fakeai.latency_profiles import LatencyProfileManager

        # Create latency manager
        latency_manager = LatencyProfileManager()

        # Create manager with latency simulation
        manager = StreamManager(
            latency_manager=latency_manager,
            enable_metrics=False,
            enable_latency_simulation=True,
        )

        response = MockChatResponse(content="Test latency")

        import time

        start_time = time.time()
        chunk_count = 0

        async for chunk in manager.create_stream(
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            full_response=response,
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            temperature=1.0,
        ):
            chunk_count += 1

        elapsed = time.time() - start_time

        # With latency simulation, should take some time
        # (TTFT + ITL per token)
        assert elapsed > 0.01  # At least some delay
        assert chunk_count > 0

    @pytest.mark.asyncio
    async def test_streaming_with_timeout_handling(self):
        """Test proper timeout handling in streaming."""
        from fakeai.streaming.base import StreamTimeoutException

        manager = StreamManager(
            enable_metrics=False,
            enable_latency_simulation=False,
        )

        # Create long response
        response = MockChatResponse(content="Word " * 1000)

        # Should timeout
        with pytest.raises(StreamTimeoutException) as exc_info:
            async for chunk in manager.create_stream(
                stream_type=StreamType.CHAT,
                model="gpt-4o",
                full_response=response,
                endpoint="/v1/chat/completions",
                timeout_seconds=0.01,  # Very short timeout
                chunk_delay_seconds=0.01,
            ):
                pass

        assert exc_info.value.timeout_seconds == 0.01

    @pytest.mark.asyncio
    async def test_multiple_concurrent_streams(self):
        """Test handling multiple concurrent streams."""
        import asyncio

        manager = StreamManager(
            enable_metrics=False,
            enable_latency_simulation=False,
        )

        async def create_test_stream(stream_id: str):
            """Create a test stream."""
            response = MockChatResponse(content=f"Stream {stream_id}")
            chunks = []

            async for chunk in manager.create_stream(
                stream_type=StreamType.CHAT,
                stream_id=stream_id,
                model="gpt-4o",
                full_response=response,
                endpoint="/v1/chat/completions",
                chunk_delay_seconds=0.0,
            ):
                chunks.append(chunk)

            return len(chunks)

        # Create multiple streams concurrently
        results = await asyncio.gather(
            create_test_stream("stream-1"),
            create_test_stream("stream-2"),
            create_test_stream("stream-3"),
        )

        # All streams should complete successfully
        assert all(count > 0 for count in results)

    @pytest.mark.asyncio
    async def test_streaming_error_handling(self):
        """Test error handling in streaming."""
        manager = StreamManager(
            enable_metrics=False,
            enable_latency_simulation=False,
        )

        # Create response with None content (should cause error)
        class BadResponse:
            choices = []

        response = BadResponse()

        chunks = []

        # Should complete without errors (just no chunks)
        async for chunk in manager.create_stream(
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            full_response=response,
            endpoint="/v1/chat/completions",
            chunk_delay_seconds=0.0,
        ):
            chunks.append(chunk)

        # Should get no chunks from empty response
        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_streaming_progress_tracking(self):
        """Test progress tracking during streaming."""
        manager = StreamManager(
            enable_metrics=False,
            enable_latency_simulation=False,
        )

        response = MockChatResponse(content="Progress test message")
        stream_id = "progress-test-stream"

        async for chunk in manager.create_stream(
            stream_type=StreamType.CHAT,
            stream_id=stream_id,
            model="gpt-4o",
            full_response=response,
            endpoint="/v1/chat/completions",
            chunk_delay_seconds=0.0,
        ):
            # Get metrics during streaming
            metrics = await manager.get_stream_metrics(stream_id)

            if metrics:
                # Verify metrics are being tracked
                assert "total_chunks" in metrics
                assert metrics["total_chunks"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
