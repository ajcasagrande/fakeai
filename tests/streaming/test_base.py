"""
Tests for streaming base types and protocols.
"""

#  SPDX-License-Identifier: Apache-2.0

import time

import pytest

from fakeai.streaming.base import (
    ErrorSeverity,
    StreamCancelledException,
    StreamChunk,
    StreamContext,
    StreamError,
    StreamMetrics,
    StreamStatus,
    StreamTimeoutException,
    StreamType,
)


class TestStreamType:
    """Test StreamType enum."""

    def test_stream_types(self):
        """Test all stream type values."""
        assert StreamType.CHAT.value == "chat"
        assert StreamType.COMPLETION.value == "completion"
        assert StreamType.AUDIO.value == "audio"
        assert StreamType.REALTIME.value == "realtime"


class TestStreamStatus:
    """Test StreamStatus enum."""

    def test_stream_statuses(self):
        """Test all stream status values."""
        assert StreamStatus.INITIALIZING.value == "initializing"
        assert StreamStatus.RUNNING.value == "running"
        assert StreamStatus.COMPLETED.value == "completed"
        assert StreamStatus.FAILED.value == "failed"
        assert StreamStatus.CANCELLED.value == "cancelled"
        assert StreamStatus.TIMEOUT.value == "timeout"


class TestErrorSeverity:
    """Test ErrorSeverity enum."""

    def test_error_severities(self):
        """Test all error severity values."""
        assert ErrorSeverity.INFO.value == "info"
        assert ErrorSeverity.WARNING.value == "warning"
        assert ErrorSeverity.ERROR.value == "error"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestStreamContext:
    """Test StreamContext dataclass."""

    def test_create_context(self):
        """Test creating a stream context."""
        context = StreamContext(
            stream_id="test-123",
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
        )

        assert context.stream_id == "test-123"
        assert context.stream_type == StreamType.CHAT
        assert context.model == "gpt-4o"
        assert context.endpoint == "/v1/chat/completions"
        assert context.timeout_seconds is None
        assert context.chunk_delay_seconds == 0.05
        assert context.enable_metrics is True

    def test_elapsed_time(self):
        """Test elapsed time calculation."""
        context = StreamContext(
            stream_id="test-123",
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            start_time=time.time() - 1.0,
        )

        elapsed = context.elapsed_time()
        assert elapsed >= 1.0
        assert elapsed < 1.1

    def test_is_timeout_no_timeout_set(self):
        """Test timeout check when no timeout is set."""
        context = StreamContext(
            stream_id="test-123",
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
        )

        assert context.is_timeout() is False

    def test_is_timeout_within_limit(self):
        """Test timeout check within limit."""
        context = StreamContext(
            stream_id="test-123",
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            timeout_seconds=10.0,
            start_time=time.time(),
        )

        assert context.is_timeout() is False

    def test_is_timeout_exceeded(self):
        """Test timeout check when exceeded."""
        context = StreamContext(
            stream_id="test-123",
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            timeout_seconds=0.1,
            start_time=time.time() - 0.2,
        )

        assert context.is_timeout() is True


class TestStreamChunk:
    """Test StreamChunk dataclass."""

    def test_create_chunk(self):
        """Test creating a stream chunk."""
        chunk = StreamChunk(
            chunk_id="chunk-1",
            sequence_number=0,
            data={"content": "Hello"},
            chunk_type="chat.completion.chunk",
            token_count=1,
            is_first=True,
            is_last=False,
        )

        assert chunk.chunk_id == "chunk-1"
        assert chunk.sequence_number == 0
        assert chunk.data == {"content": "Hello"}
        assert chunk.chunk_type == "chat.completion.chunk"
        assert chunk.token_count == 1
        assert chunk.is_first is True
        assert chunk.is_last is False

    def test_chunk_to_dict(self):
        """Test converting chunk to dictionary."""
        chunk = StreamChunk(
            chunk_id="chunk-1",
            sequence_number=0,
            data={"content": "Hello"},
            token_count=1,
        )

        chunk_dict = chunk.to_dict()

        assert chunk_dict["chunk_id"] == "chunk-1"
        assert chunk_dict["sequence_number"] == 0
        assert chunk_dict["data"] == {"content": "Hello"}
        assert chunk_dict["token_count"] == 1
        assert "timestamp" in chunk_dict
        assert "metadata" in chunk_dict


class TestStreamError:
    """Test StreamError dataclass."""

    def test_create_error(self):
        """Test creating a stream error."""
        error = StreamError(
            error_code="test_error",
            message="Test error message",
            severity=ErrorSeverity.ERROR,
            recoverable=True,
            retry_after_seconds=1.0,
        )

        assert error.error_code == "test_error"
        assert error.message == "Test error message"
        assert error.severity == ErrorSeverity.ERROR
        assert error.recoverable is True
        assert error.retry_after_seconds == 1.0

    def test_error_to_dict(self):
        """Test converting error to dictionary."""
        error = StreamError(
            error_code="test_error",
            message="Test error message",
            severity=ErrorSeverity.WARNING,
        )

        error_dict = error.to_dict()

        assert error_dict["error_code"] == "test_error"
        assert error_dict["message"] == "Test error message"
        assert error_dict["severity"] == "warning"
        assert error_dict["recoverable"] is False
        assert "timestamp" in error_dict


class TestStreamMetrics:
    """Test StreamMetrics dataclass."""

    def test_create_metrics(self):
        """Test creating stream metrics."""
        metrics = StreamMetrics(
            stream_id="test-123",
            start_time=time.time(),
        )

        assert metrics.stream_id == "test-123"
        assert metrics.total_chunks == 0
        assert metrics.total_tokens == 0
        assert metrics.first_chunk_time is None

    def test_time_to_first_chunk(self):
        """Test time to first chunk calculation."""
        start = time.time()
        metrics = StreamMetrics(
            stream_id="test-123",
            start_time=start,
            first_chunk_time=start + 0.1,
        )

        ttfc = metrics.time_to_first_chunk_ms()
        assert ttfc is not None
        assert 95 <= ttfc <= 105  # ~100ms with some tolerance

    def test_total_duration(self):
        """Test total duration calculation."""
        start = time.time()
        metrics = StreamMetrics(
            stream_id="test-123",
            start_time=start,
            completion_time=start + 1.0,
        )

        duration = metrics.total_duration_ms()
        assert duration is not None
        assert 950 <= duration <= 1050  # ~1000ms with some tolerance

    def test_tokens_per_second(self):
        """Test tokens per second calculation."""
        start = time.time()
        metrics = StreamMetrics(
            stream_id="test-123",
            start_time=start,
            first_chunk_time=start + 0.1,
            completion_time=start + 1.1,
            total_tokens=50,
        )

        tps = metrics.tokens_per_second()
        assert tps is not None
        assert 45 <= tps <= 55  # ~50 tokens/sec with some tolerance

    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = StreamMetrics(
            stream_id="test-123",
            start_time=time.time(),
            total_chunks=10,
            total_tokens=50,
        )

        metrics_dict = metrics.to_dict()

        assert metrics_dict["stream_id"] == "test-123"
        assert metrics_dict["total_chunks"] == 10
        assert metrics_dict["total_tokens"] == 50
        assert "time_to_first_chunk_ms" in metrics_dict
        assert "tokens_per_second" in metrics_dict


class TestExceptions:
    """Test custom exceptions."""

    def test_stream_cancelled_exception(self):
        """Test StreamCancelledException."""
        exc = StreamCancelledException(
            stream_id="test-123",
            message="Cancelled by user",
        )

        assert exc.stream_id == "test-123"
        assert exc.message == "Cancelled by user"
        assert "test-123" in str(exc)

    def test_stream_timeout_exception(self):
        """Test StreamTimeoutException."""
        exc = StreamTimeoutException(
            stream_id="test-123",
            timeout_seconds=30.0,
            message="Timeout exceeded",
        )

        assert exc.stream_id == "test-123"
        assert exc.timeout_seconds == 30.0
        assert exc.message == "Timeout exceeded"
        assert "30.0" in str(exc)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
