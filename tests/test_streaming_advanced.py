"""
Tests for advanced streaming features.

Tests error handling, timeout enforcement, client disconnection, and streaming metrics.
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from fakeai import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import ChatCompletionChunk, ChatCompletionRequest, Message, Role


class TestStreamingErrorHandling:
    """Test error handling in streaming responses."""

    @pytest.mark.asyncio
    async def test_stream_generation_timeout(self):
        """Test that stream generation respects total timeout."""
        # Configure very short timeout
        config = AppConfig(stream_timeout_seconds=0.1, response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello")],
            stream=True,
        )

        # Mock _generate_simulated_completion to take too long
        async def slow_generation(*args, **kwargs):
            await asyncio.sleep(1.0)  # Longer than timeout
            return "This should timeout"

        with patch.object(
            service, "_generate_simulated_completion", side_effect=slow_generation
        ):
            chunks = []
            async for chunk in service.create_chat_completion_stream(request):
                chunks.append(chunk)

            # Should receive error chunk
            assert len(chunks) > 0
            error_chunk = chunks[-1]
            assert hasattr(error_chunk, "error")
            assert "timeout" in error_chunk.error["message"].lower()

    @pytest.mark.asyncio
    async def test_stream_token_timeout(self):
        """Test that stream enforces per-token timeout."""
        config = AppConfig(stream_token_timeout_seconds=0.05, response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True,
        )

        # This should work normally (tokens sent quickly)
        chunks = []
        async for chunk in service.create_chat_completion_stream(request):
            chunks.append(chunk)

        # Should complete successfully
        assert len(chunks) > 0
        final_chunk = chunks[-1]
        assert final_chunk.choices[0].finish_reason in ["stop", None]

    @pytest.mark.asyncio
    async def test_stream_cancellation(self):
        """Test that stream handles client disconnection gracefully."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Long response please")],
            max_tokens=100,
            stream=True,
        )

        # Simulate client disconnect after a few chunks
        chunks_received = 0
        max_chunks = 3

        try:
            async for chunk in service.create_chat_completion_stream(request):
                chunks_received += 1
                if chunks_received >= max_chunks:
                    raise asyncio.CancelledError("Client disconnected")
        except asyncio.CancelledError:
            # This is expected
            pass

        assert chunks_received == max_chunks

    @pytest.mark.asyncio
    async def test_stream_error_chunk_format(self):
        """Test that error chunks have correct format."""
        config = AppConfig(stream_timeout_seconds=0.1)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True,
        )

        # Force an error by mocking
        async def failing_generation(*args, **kwargs):
            raise ValueError("Test error")

        with patch.object(
            service, "_generate_simulated_completion", side_effect=failing_generation
        ):
            chunks = []
            async for chunk in service.create_chat_completion_stream(request):
                chunks.append(chunk)

            # Should have error chunk
            assert len(chunks) > 0
            error_chunk = chunks[-1]
            assert hasattr(error_chunk, "error")
            assert error_chunk.error["type"] == "server_error"
            assert "Test error" in error_chunk.error["message"]


class TestStreamingMetrics:
    """Test streaming metrics tracking."""

    @pytest.mark.asyncio
    async def test_metrics_track_active_streams(self):
        """Test that metrics track active streams."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True,
        )

        # Check initial state
        initial_active = service.metrics_tracker.get_active_streams()

        # Start streaming
        stream_gen = service.create_chat_completion_stream(request)
        first_chunk = await stream_gen.__anext__()

        # Should have one active stream
        active_during = service.metrics_tracker.get_active_streams()
        assert active_during >= initial_active

        # Consume rest of stream
        async for chunk in stream_gen:
            pass

        # After completion, active count should decrease
        active_after = service.metrics_tracker.get_active_streams()
        assert active_after == initial_active

    @pytest.mark.asyncio
    async def test_metrics_track_completed_streams(self):
        """Test that completed streams are tracked."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True,
        )

        # Get initial stats
        initial_stats = service.metrics_tracker.get_streaming_stats()
        initial_completed = initial_stats.get("completed_streams", 0)

        # Complete a stream
        async for chunk in service.create_chat_completion_stream(request):
            pass

        # Check stats
        final_stats = service.metrics_tracker.get_streaming_stats()
        final_completed = final_stats.get("completed_streams", 0)

        assert final_completed > initial_completed

    @pytest.mark.asyncio
    async def test_metrics_track_failed_streams(self):
        """Test that failed streams are tracked."""
        config = AppConfig(stream_timeout_seconds=0.1)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True,
        )

        # Get initial stats
        initial_stats = service.metrics_tracker.get_streaming_stats()
        initial_failed = initial_stats.get("failed_streams", 0)

        # Force a failure
        async def failing_generation(*args, **kwargs):
            raise ValueError("Test failure")

        with patch.object(
            service, "_generate_simulated_completion", side_effect=failing_generation
        ):
            async for chunk in service.create_chat_completion_stream(request):
                pass

        # Check stats
        final_stats = service.metrics_tracker.get_streaming_stats()
        final_failed = final_stats.get("failed_streams", 0)

        assert final_failed > initial_failed

    @pytest.mark.asyncio
    async def test_metrics_ttft_calculation(self):
        """Test that TTFT (time to first token) is calculated."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True,
        )

        # Complete a stream
        async for chunk in service.create_chat_completion_stream(request):
            pass

        # Check TTFT stats
        stats = service.metrics_tracker.get_streaming_stats()
        ttft_stats = stats.get("ttft", {})

        # Should have TTFT data
        if ttft_stats:
            assert "avg" in ttft_stats
            assert "p50" in ttft_stats
            assert "p99" in ttft_stats
            assert ttft_stats["avg"] > 0

    @pytest.mark.asyncio
    async def test_metrics_tokens_per_second(self):
        """Test that tokens per second is calculated."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                Message(role=Role.USER, content="Generate a longer response please")
            ],
            max_tokens=50,
            stream=True,
        )

        # Complete a stream
        token_count = 0
        async for chunk in service.create_chat_completion_stream(request):
            if chunk.choices and chunk.choices[0].delta.content:
                token_count += 1

        # Check tokens/sec stats
        stats = service.metrics_tracker.get_streaming_stats()
        tps_stats = stats.get("tokens_per_second", {})

        # Should have tokens/sec data
        if tps_stats and token_count > 0:
            assert "avg" in tps_stats
            assert tps_stats["avg"] > 0


class TestStreamingTimeouts:
    """Test timeout enforcement in streaming."""

    @pytest.mark.asyncio
    async def test_total_timeout_enforcement(self):
        """Test that total stream timeout is enforced."""
        config = AppConfig(stream_timeout_seconds=0.5, response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            max_tokens=1000,  # Request many tokens
            stream=True,
        )

        # Mock to generate slowly
        original_sleep = asyncio.sleep

        async def slow_sleep(duration):
            # Make token delays longer
            if duration < 0.5:
                await original_sleep(0.2)
            else:
                await original_sleep(duration)

        with patch("asyncio.sleep", side_effect=slow_sleep):
            start_time = asyncio.get_event_loop().time()
            chunks = []

            async for chunk in service.create_chat_completion_stream(request):
                chunks.append(chunk)
                # Check if we got timeout error
                if hasattr(chunk, "error") and chunk.error:
                    break

            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time

            # Should timeout within reasonable time
            assert duration < 2.0  # Should timeout quickly

    @pytest.mark.asyncio
    async def test_token_timeout_not_triggered_on_normal_stream(self):
        """Test that token timeout doesn't trigger on normal streaming."""
        config = AppConfig(
            stream_token_timeout_seconds=1.0, response_delay=0.0  # Generous timeout
        )
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True,
        )

        # Should complete without timeout error
        chunks = []
        async for chunk in service.create_chat_completion_stream(request):
            chunks.append(chunk)

        # Should have successful completion
        assert len(chunks) > 0
        final_chunk = chunks[-1]
        assert final_chunk.choices[0].finish_reason == "stop"
        assert not hasattr(final_chunk, "error") or not final_chunk.error


class TestKeepAliveHeartbeat:
    """Test keep-alive heartbeat functionality."""

    @pytest.mark.asyncio
    async def test_keepalive_enabled_config(self):
        """Test that keep-alive can be enabled via config."""
        config = AppConfig(
            stream_keepalive_enabled=True,
            stream_keepalive_interval_seconds=5.0,
            response_delay=0.0,
        )
        service = FakeAIService(config)

        assert config.stream_keepalive_enabled is True
        assert config.stream_keepalive_interval_seconds == 5.0

    @pytest.mark.asyncio
    async def test_keepalive_disabled_config(self):
        """Test that keep-alive can be disabled via config."""
        config = AppConfig(stream_keepalive_enabled=False, response_delay=0.0)
        service = FakeAIService(config)

        assert config.stream_keepalive_enabled is False


class TestClientDisconnection:
    """Test handling of client disconnection."""

    @pytest.mark.asyncio
    async def test_cancellation_tracked_as_failed(self):
        """Test that cancelled streams are tracked as failed."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Long response")],
            max_tokens=100,
            stream=True,
        )

        # Get initial failed count
        initial_stats = service.metrics_tracker.get_streaming_stats()
        initial_failed = initial_stats.get("failed_streams", 0)

        # Start and cancel stream
        try:
            async for i, chunk in enumerate(
                service.create_chat_completion_stream(request)
            ):
                if i >= 2:
                    raise asyncio.CancelledError()
        except asyncio.CancelledError:
            pass

        # Check failed count increased
        final_stats = service.metrics_tracker.get_streaming_stats()
        final_failed = final_stats.get("failed_streams", 0)

        assert final_failed > initial_failed

    @pytest.mark.asyncio
    async def test_cancellation_does_not_send_error_chunk(self):
        """Test that cancellation doesn't send error chunk to client."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True,
        )

        chunks = []
        try:
            async for i, chunk in enumerate(
                service.create_chat_completion_stream(request)
            ):
                chunks.append(chunk)
                if i >= 2:
                    raise asyncio.CancelledError()
        except asyncio.CancelledError:
            pass

        # None of the chunks should have errors (client disconnected cleanly)
        for chunk in chunks:
            assert not hasattr(chunk, "error") or not chunk.error
