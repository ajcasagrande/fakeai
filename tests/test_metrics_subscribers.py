"""
Comprehensive tests for all metric subscribers in fakeai/events/subscribers.py.

Tests cover all subscriber classes and their event handling methods:
- MetricsTrackerSubscriber
- StreamingMetricsSubscriber
- ErrorMetricsSubscriber
- CostTrackerSubscriber
- DynamoMetricsSubscriber
- ModelMetricsSubscriber
- KVCacheMetricsSubscriber
"""

from unittest.mock import Mock

import pytest

from fakeai.events.event_types import (
    BatchSizeChangedEvent,
    CacheLookupEvent,
    CacheSpeedupMeasuredEvent,
    CostCalculatedEvent,
    DecodeStartedEvent,
    ErrorOccurredEvent,
    FirstTokenGeneratedEvent,
    ModelSelectedEvent,
    PrefillCompletedEvent,
    PrefillStartedEvent,
    QueueDepthChangedEvent,
    RequestCompletedEvent,
    RequestFailedEvent,
    RequestStartedEvent,
    StreamCompletedEvent,
    StreamFailedEvent,
    StreamingTokenGeneratedEvent,
    StreamStartedEvent,
)
from fakeai.events.subscribers import (
    CostTrackerSubscriber,
    DynamoMetricsSubscriber,
    ErrorMetricsSubscriber,
    KVCacheMetricsSubscriber,
    MetricsTrackerSubscriber,
    ModelMetricsSubscriber,
    StreamingMetricsSubscriber,
)


@pytest.mark.unit
@pytest.mark.metrics
class TestMetricsTrackerSubscriber:
    """Test MetricsTrackerSubscriber event handling."""

    @pytest.fixture
    def mock_tracker(self):
        """Create a mock MetricsTracker."""
        tracker = Mock()
        tracker.track_request = Mock()
        tracker.track_response = Mock()
        tracker.track_tokens = Mock()
        tracker.track_error = Mock()
        return tracker

    @pytest.fixture
    def subscriber(self, mock_tracker):
        """Create a MetricsTrackerSubscriber with mock tracker."""
        return MetricsTrackerSubscriber(mock_tracker)

    @pytest.mark.asyncio
    async def test_on_request_started_calls_track_request(
        self, subscriber, mock_tracker
    ):
        """on_request_started() should call track_request() with endpoint."""
        event = RequestStartedEvent(
            request_id="req-123",
            endpoint="/v1/chat/completions",
            method="POST",
            model="gpt-4",
        )

        await subscriber.on_request_started(event)

        mock_tracker.track_request.assert_called_once_with("/v1/chat/completions")

    @pytest.mark.asyncio
    async def test_on_request_completed_calls_track_response(
        self, subscriber, mock_tracker
    ):
        """on_request_completed() should call track_response() with endpoint and latency."""
        event = RequestCompletedEvent(
            request_id="req-123",
            endpoint="/v1/embeddings",
            model="text-embedding-ada-002",
            duration_ms=250.5,
            input_tokens=100,
            output_tokens=0,
            status_code=200,
        )

        await subscriber.on_request_completed(event)

        # Duration should be converted from ms to seconds
        mock_tracker.track_response.assert_called_once_with(
            "/v1/embeddings", 0.2505
        )

    @pytest.mark.asyncio
    async def test_on_request_completed_calls_track_tokens(
        self, subscriber, mock_tracker
    ):
        """on_request_completed() should call track_tokens() when tokens generated."""
        event = RequestCompletedEvent(
            request_id="req-123",
            endpoint="/v1/chat/completions",
            model="gpt-4",
            duration_ms=1500.0,
            input_tokens=50,
            output_tokens=150,
            status_code=200,
        )

        await subscriber.on_request_completed(event)

        # Should track total tokens (input + output)
        mock_tracker.track_tokens.assert_called_once_with(
            "/v1/chat/completions", 200
        )

    @pytest.mark.asyncio
    async def test_on_request_completed_skips_tokens_when_zero(
        self, subscriber, mock_tracker
    ):
        """on_request_completed() should not track tokens when count is zero."""
        event = RequestCompletedEvent(
            request_id="req-123",
            endpoint="/v1/models",
            model="",
            duration_ms=100.0,
            input_tokens=0,
            output_tokens=0,
            status_code=200,
        )

        await subscriber.on_request_completed(event)

        # Should not call track_tokens when no tokens generated
        mock_tracker.track_tokens.assert_not_called()
        # But should still track response
        mock_tracker.track_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_request_failed_calls_track_error(self, subscriber, mock_tracker):
        """on_request_failed() should call track_error() with endpoint."""
        event = RequestFailedEvent(
            request_id="req-123",
            endpoint="/v1/chat/completions",
            model="gpt-4",
            error_type="RateLimitError",
            error_message="Rate limit exceeded",
            status_code=429,
            duration_ms=50.0,
        )

        await subscriber.on_request_failed(event)

        mock_tracker.track_error.assert_called_once_with("/v1/chat/completions")


@pytest.mark.unit
@pytest.mark.metrics
class TestStreamingMetricsSubscriber:
    """Test StreamingMetricsSubscriber event handling."""

    @pytest.fixture
    def mock_tracker(self):
        """Create a mock StreamingMetricsTracker."""
        tracker = Mock()
        tracker.start_stream = Mock()
        tracker.record_token = Mock()
        tracker.record_first_token_time = Mock()
        tracker.complete_stream = Mock()
        tracker.fail_stream = Mock()
        return tracker

    @pytest.fixture
    def subscriber(self, mock_tracker):
        """Create a StreamingMetricsSubscriber with mock tracker."""
        return StreamingMetricsSubscriber(mock_tracker)

    @pytest.mark.asyncio
    async def test_on_stream_started_creates_stream(self, subscriber, mock_tracker):
        """on_stream_started() should call start_stream() with correct parameters."""
        event = StreamStartedEvent(
            request_id="req-123",
            stream_id="stream-456",
            endpoint="/v1/chat/completions",
            model="gpt-4",
            input_tokens=100,
            temperature=0.7,
            max_tokens=500,
        )

        await subscriber.on_stream_started(event)

        mock_tracker.start_stream.assert_called_once_with(
            stream_id="stream-456",
            model="gpt-4",
            prompt_tokens=100,
            temperature=0.7,
            max_tokens=500,
        )

    @pytest.mark.asyncio
    async def test_on_stream_token_records_token(self, subscriber, mock_tracker):
        """on_stream_token() should call record_token() with token data."""
        event = StreamingTokenGeneratedEvent(
            request_id="req-123",
            stream_id="stream-456",
            token="Hello",
            sequence_number=1,
            timestamp_ns=1234567890,
            chunk_size_bytes=5,
        )

        await subscriber.on_stream_token(event)

        mock_tracker.record_token.assert_called_once_with(
            stream_id="stream-456", token="Hello", chunk_size_bytes=5
        )

    @pytest.mark.asyncio
    async def test_on_stream_token_handles_none_chunk_size(
        self, subscriber, mock_tracker
    ):
        """on_stream_token() should handle None chunk_size_bytes."""
        event = StreamingTokenGeneratedEvent(
            request_id="req-123",
            stream_id="stream-456",
            token="World",
            sequence_number=2,
            timestamp_ns=1234567891,
            chunk_size_bytes=None,
        )

        await subscriber.on_stream_token(event)

        mock_tracker.record_token.assert_called_once_with(
            stream_id="stream-456", token="World", chunk_size_bytes=0
        )

    @pytest.mark.asyncio
    async def test_on_first_token_records_ttft(self, subscriber, mock_tracker):
        """on_first_token() should call record_first_token_time() if method exists."""
        event = FirstTokenGeneratedEvent(
            request_id="req-123",
            stream_id="stream-456",
            ttft_ms=125.5,
        )

        await subscriber.on_first_token(event)

        mock_tracker.record_first_token_time.assert_called_once_with(
            "stream-456", 125.5
        )

    @pytest.mark.asyncio
    async def test_on_first_token_handles_missing_method(
        self, subscriber, mock_tracker
    ):
        """on_first_token() should handle tracker without record_first_token_time."""
        # Remove the method from the mock
        del mock_tracker.record_first_token_time

        event = FirstTokenGeneratedEvent(
            request_id="req-123",
            stream_id="stream-456",
            ttft_ms=125.5,
        )

        # Should not raise an error
        await subscriber.on_first_token(event)

    @pytest.mark.asyncio
    async def test_on_stream_completed_completes_stream(
        self, subscriber, mock_tracker
    ):
        """on_stream_completed() should call complete_stream() with finish reason."""
        event = StreamCompletedEvent(
            request_id="req-123",
            stream_id="stream-456",
            endpoint="/v1/chat/completions",
            duration_ms=2500.0,
            token_count=150,
            finish_reason="stop",
        )

        await subscriber.on_stream_completed(event)

        mock_tracker.complete_stream.assert_called_once_with(
            stream_id="stream-456", finish_reason="stop"
        )

    @pytest.mark.asyncio
    async def test_on_stream_failed_fails_stream(self, subscriber, mock_tracker):
        """on_stream_failed() should call fail_stream() if method exists."""
        event = StreamFailedEvent(
            request_id="req-123",
            stream_id="stream-456",
            endpoint="/v1/chat/completions",
            duration_ms=500.0,
            error_message="Connection lost",
            token_count=25,
        )

        await subscriber.on_stream_failed(event)

        mock_tracker.fail_stream.assert_called_once_with(
            "stream-456", "Connection lost"
        )

    @pytest.mark.asyncio
    async def test_on_stream_failed_handles_missing_method(
        self, subscriber, mock_tracker
    ):
        """on_stream_failed() should handle tracker without fail_stream method."""
        # Remove the method from the mock
        del mock_tracker.fail_stream

        event = StreamFailedEvent(
            request_id="req-123",
            stream_id="stream-456",
            endpoint="/v1/chat/completions",
            duration_ms=500.0,
            error_message="Connection lost",
            token_count=25,
        )

        # Should not raise an error
        await subscriber.on_stream_failed(event)


@pytest.mark.unit
@pytest.mark.metrics
class TestErrorMetricsSubscriber:
    """Test ErrorMetricsSubscriber event handling."""

    @pytest.fixture
    def mock_tracker(self):
        """Create a mock ErrorMetricsTracker."""
        tracker = Mock()
        tracker.record_error = Mock()
        tracker.record_success = Mock()
        return tracker

    @pytest.fixture
    def subscriber(self, mock_tracker):
        """Create an ErrorMetricsSubscriber with mock tracker."""
        return ErrorMetricsSubscriber(mock_tracker)

    @pytest.mark.asyncio
    async def test_on_error_occurred_records_error(self, subscriber, mock_tracker):
        """on_error_occurred() should record error with correct parameters."""
        event = ErrorOccurredEvent(
            request_id="req-123",
            endpoint="/v1/chat/completions",
            model="gpt-4",
            error_type="ValidationError",
            error_message="Invalid parameter",
            stack_trace="...",
            metadata={"api_key": "sk-test123"},
        )

        await subscriber.on_error_occurred(event)

        mock_tracker.record_error.assert_called_once_with(
            endpoint="/v1/chat/completions",
            status_code=500,  # Default
            error_type="ValidationError",
            error_message="Invalid parameter",
            model="gpt-4",
            api_key="sk-test123",
            request_id="req-123",
        )

    @pytest.mark.asyncio
    async def test_on_error_occurred_handles_missing_api_key(
        self, subscriber, mock_tracker
    ):
        """on_error_occurred() should handle missing api_key in metadata."""
        event = ErrorOccurredEvent(
            request_id="req-123",
            endpoint="/v1/embeddings",
            model="text-embedding-ada-002",
            error_type="TimeoutError",
            error_message="Request timeout",
            metadata={},
        )

        await subscriber.on_error_occurred(event)

        mock_tracker.record_error.assert_called_once()
        call_kwargs = mock_tracker.record_error.call_args[1]
        assert call_kwargs["api_key"] is None

    @pytest.mark.asyncio
    async def test_on_request_failed_records_error(self, subscriber, mock_tracker):
        """on_request_failed() should record error with status code."""
        event = RequestFailedEvent(
            request_id="req-123",
            endpoint="/v1/completions",
            model="gpt-3.5-turbo",
            error_type="RateLimitError",
            error_message="Rate limit exceeded",
            status_code=429,
            duration_ms=100.0,
            metadata={"api_key": "sk-test456"},
        )

        await subscriber.on_request_failed(event)

        mock_tracker.record_error.assert_called_once_with(
            endpoint="/v1/completions",
            status_code=429,
            error_type="RateLimitError",
            error_message="Rate limit exceeded",
            model="gpt-3.5-turbo",
            api_key="sk-test456",
            request_id="req-123",
        )

    @pytest.mark.asyncio
    async def test_on_request_completed_records_success(
        self, subscriber, mock_tracker
    ):
        """on_request_completed() should record success for error rate calculation."""
        event = RequestCompletedEvent(
            request_id="req-123",
            endpoint="/v1/chat/completions",
            model="gpt-4",
            duration_ms=1500.0,
            input_tokens=50,
            output_tokens=150,
            status_code=200,
        )

        await subscriber.on_request_completed(event)

        mock_tracker.record_success.assert_called_once_with(
            endpoint="/v1/chat/completions", model="gpt-4"
        )


@pytest.mark.unit
@pytest.mark.metrics
class TestCostTrackerSubscriber:
    """Test CostTrackerSubscriber event handling."""

    @pytest.fixture
    def mock_tracker(self):
        """Create a mock CostTracker."""
        tracker = Mock()
        tracker.track_usage = Mock()
        return tracker

    @pytest.fixture
    def subscriber(self, mock_tracker):
        """Create a CostTrackerSubscriber with mock tracker."""
        return CostTrackerSubscriber(mock_tracker)

    @pytest.mark.asyncio
    async def test_on_request_completed_tracks_usage(self, subscriber, mock_tracker):
        """on_request_completed() should track usage with all parameters."""
        event = RequestCompletedEvent(
            request_id="req-123",
            endpoint="/v1/chat/completions",
            model="gpt-4",
            duration_ms=2000.0,
            input_tokens=100,
            output_tokens=250,
            cached_tokens=20,
            status_code=200,
            metadata={"api_key": "sk-test789", "user_id": "user-001"},
        )

        await subscriber.on_request_completed(event)

        mock_tracker.track_usage.assert_called_once_with(
            api_key="sk-test789",
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=250,
            cached_tokens=20,
            user_id="user-001",
        )

    @pytest.mark.asyncio
    async def test_on_request_completed_uses_default_api_key(
        self, subscriber, mock_tracker
    ):
        """on_request_completed() should use 'default' when api_key not in metadata."""
        event = RequestCompletedEvent(
            request_id="req-123",
            endpoint="/v1/embeddings",
            model="text-embedding-ada-002",
            duration_ms=500.0,
            input_tokens=100,
            output_tokens=0,
            status_code=200,
            metadata={},
        )

        await subscriber.on_request_completed(event)

        call_kwargs = mock_tracker.track_usage.call_args[1]
        assert call_kwargs["api_key"] == "default"
        assert call_kwargs["user_id"] is None

    @pytest.mark.asyncio
    async def test_on_request_completed_handles_cached_tokens(
        self, subscriber, mock_tracker
    ):
        """on_request_completed() should properly pass cached tokens."""
        event = RequestCompletedEvent(
            request_id="req-123",
            endpoint="/v1/chat/completions",
            model="gpt-4",
            duration_ms=1000.0,
            input_tokens=200,
            output_tokens=100,
            cached_tokens=50,
            status_code=200,
            metadata={"api_key": "sk-cached"},
        )

        await subscriber.on_request_completed(event)

        call_kwargs = mock_tracker.track_usage.call_args[1]
        assert call_kwargs["cached_tokens"] == 50

    @pytest.mark.asyncio
    async def test_on_cost_calculated_logs_cost(self, subscriber, mock_tracker):
        """on_cost_calculated() should log cost information (debug logging)."""
        event = CostCalculatedEvent(
            request_id="req-123",
            model="gpt-4",
            input_cost=0.003,
            output_cost=0.012,
            total_cost=0.015,
        )

        # Should not raise any errors
        await subscriber.on_cost_calculated(event)


@pytest.mark.unit
@pytest.mark.metrics
class TestDynamoMetricsSubscriber:
    """Test DynamoMetricsSubscriber event handling."""

    @pytest.fixture
    def mock_collector(self):
        """Create a mock DynamoMetricsCollector."""
        collector = Mock()
        collector.start_request = Mock()
        collector.record_prefill_start = Mock()
        collector.record_first_token = Mock()
        collector.record_decode_start = Mock()
        collector.complete_request = Mock()
        collector.record_queue_depth = Mock()
        collector.record_batch_size = Mock()
        return collector

    @pytest.fixture
    def subscriber(self, mock_collector):
        """Create a DynamoMetricsSubscriber with mock collector."""
        return DynamoMetricsSubscriber(mock_collector)

    @pytest.mark.asyncio
    async def test_on_request_started_starts_request(
        self, subscriber, mock_collector
    ):
        """on_request_started() should call start_request() with request details."""
        event = RequestStartedEvent(
            request_id="req-123",
            endpoint="/v1/chat/completions",
            model="gpt-4",
            input_tokens=100,
        )

        await subscriber.on_request_started(event)

        mock_collector.start_request.assert_called_once_with(
            request_id="req-123",
            model="gpt-4",
            endpoint="/v1/chat/completions",
            input_tokens=100,
        )

    @pytest.mark.asyncio
    async def test_on_request_started_handles_none_model(
        self, subscriber, mock_collector
    ):
        """on_request_started() should use 'unknown' when model is None."""
        event = RequestStartedEvent(
            request_id="req-123",
            endpoint="/v1/models",
            model=None,
            input_tokens=None,
        )

        await subscriber.on_request_started(event)

        call_kwargs = mock_collector.start_request.call_args[1]
        assert call_kwargs["model"] == "unknown"
        assert call_kwargs["input_tokens"] == 0

    @pytest.mark.asyncio
    async def test_on_request_started_skips_without_request_id(
        self, subscriber, mock_collector
    ):
        """on_request_started() should skip when request_id is None."""
        event = RequestStartedEvent(
            request_id=None,
            endpoint="/v1/chat/completions",
            model="gpt-4",
        )

        await subscriber.on_request_started(event)

        mock_collector.start_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_prefill_started_records_prefill(
        self, subscriber, mock_collector
    ):
        """on_prefill_started() should call record_prefill_start()."""
        event = PrefillStartedEvent(
            request_id="req-123",
            input_tokens=100,
        )

        await subscriber.on_prefill_started(event)

        mock_collector.record_prefill_start.assert_called_once_with("req-123")

    @pytest.mark.asyncio
    async def test_on_prefill_started_skips_without_request_id(
        self, subscriber, mock_collector
    ):
        """on_prefill_started() should skip when request_id is None."""
        event = PrefillStartedEvent(
            request_id=None,
            input_tokens=100,
        )

        await subscriber.on_prefill_started(event)

        mock_collector.record_prefill_start.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_prefill_completed_does_nothing(
        self, subscriber, mock_collector
    ):
        """on_prefill_completed() should pass (tracked internally by collector)."""
        event = PrefillCompletedEvent(
            request_id="req-123",
            prefill_time_ms=150.0,
        )

        # Should not raise any errors
        await subscriber.on_prefill_completed(event)

    @pytest.mark.asyncio
    async def test_on_first_token_records_timing(self, subscriber, mock_collector):
        """on_first_token() should call record_first_token()."""
        event = FirstTokenGeneratedEvent(
            request_id="req-123",
            stream_id="stream-456",
            ttft_ms=125.5,
        )

        await subscriber.on_first_token(event)

        mock_collector.record_first_token.assert_called_once_with("req-123")

    @pytest.mark.asyncio
    async def test_on_first_token_uses_stream_id_as_fallback(
        self, subscriber, mock_collector
    ):
        """on_first_token() should use stream_id when request_id is None."""
        event = FirstTokenGeneratedEvent(
            request_id=None,
            stream_id="stream-789",
            ttft_ms=125.5,
        )

        await subscriber.on_first_token(event)

        mock_collector.record_first_token.assert_called_once_with("stream-789")

    @pytest.mark.asyncio
    async def test_on_first_token_skips_without_id(self, subscriber, mock_collector):
        """on_first_token() should skip when both request_id and stream_id are None."""
        event = FirstTokenGeneratedEvent(
            request_id=None,
            stream_id="",
            ttft_ms=125.5,
        )

        await subscriber.on_first_token(event)

        mock_collector.record_first_token.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_decode_started_records_decode(self, subscriber, mock_collector):
        """on_decode_started() should call record_decode_start()."""
        event = DecodeStartedEvent(
            request_id="req-123",
        )

        await subscriber.on_decode_started(event)

        mock_collector.record_decode_start.assert_called_once_with("req-123")

    @pytest.mark.asyncio
    async def test_on_request_completed_completes_request(
        self, subscriber, mock_collector
    ):
        """on_request_completed() should call complete_request() with all details."""
        event = RequestCompletedEvent(
            request_id="req-123",
            endpoint="/v1/chat/completions",
            model="gpt-4",
            duration_ms=2000.0,
            input_tokens=100,
            output_tokens=250,
            cached_tokens=20,
            finish_reason="stop",
            status_code=200,
            metadata={"worker_id": "worker-01", "kv_cache_hit": True},
        )

        await subscriber.on_request_completed(event)

        mock_collector.complete_request.assert_called_once_with(
            request_id="req-123",
            output_tokens=250,
            cached_tokens=20,
            kv_cache_hit=True,
            worker_id="worker-01",
            success=True,
            finish_reason="stop",
        )

    @pytest.mark.asyncio
    async def test_on_request_completed_uses_defaults(
        self, subscriber, mock_collector
    ):
        """on_request_completed() should use defaults when metadata fields missing."""
        event = RequestCompletedEvent(
            request_id="req-123",
            endpoint="/v1/embeddings",
            model="text-embedding-ada-002",
            duration_ms=500.0,
            input_tokens=100,
            output_tokens=0,
            cached_tokens=0,
            status_code=200,
            metadata={},
        )

        await subscriber.on_request_completed(event)

        call_kwargs = mock_collector.complete_request.call_args[1]
        assert call_kwargs["worker_id"] == "default"
        assert call_kwargs["kv_cache_hit"] is False

    @pytest.mark.asyncio
    async def test_on_request_completed_skips_without_request_id(
        self, subscriber, mock_collector
    ):
        """on_request_completed() should skip when request_id is None."""
        event = RequestCompletedEvent(
            request_id=None,
            endpoint="/v1/chat/completions",
            model="gpt-4",
            duration_ms=1000.0,
            input_tokens=50,
            output_tokens=100,
            status_code=200,
        )

        await subscriber.on_request_completed(event)

        mock_collector.complete_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_queue_depth_changed_records_depth(
        self, subscriber, mock_collector
    ):
        """on_queue_depth_changed() should call record_queue_depth()."""
        event = QueueDepthChangedEvent(
            request_id="req-123",
            queue_name="main-queue",
            depth=15,
            max_depth=100,
        )

        await subscriber.on_queue_depth_changed(event)

        mock_collector.record_queue_depth.assert_called_once_with(15)

    @pytest.mark.asyncio
    async def test_on_batch_size_changed_records_batch_size(
        self, subscriber, mock_collector
    ):
        """on_batch_size_changed() should call record_batch_size()."""
        event = BatchSizeChangedEvent(
            request_id="req-123",
            batch_size=8,
            avg_batch_size=6.5,
        )

        await subscriber.on_batch_size_changed(event)

        mock_collector.record_batch_size.assert_called_once_with(8)


@pytest.mark.unit
@pytest.mark.metrics
class TestModelMetricsSubscriber:
    """Test ModelMetricsSubscriber event handling."""

    @pytest.fixture
    def mock_tracker(self):
        """Create a mock ModelMetricsTracker."""
        tracker = Mock()
        tracker.track_request = Mock()
        return tracker

    @pytest.fixture
    def subscriber(self, mock_tracker):
        """Create a ModelMetricsSubscriber with mock tracker."""
        return ModelMetricsSubscriber(mock_tracker)

    @pytest.mark.asyncio
    async def test_on_model_selected_logs_selection(self, subscriber, mock_tracker):
        """on_model_selected() should log model selection (debug logging)."""
        event = ModelSelectedEvent(
            request_id="req-123",
            model_id="gpt-4",
            context_window=8192,
        )

        # Should not raise any errors
        await subscriber.on_model_selected(event)

    @pytest.mark.asyncio
    async def test_on_request_completed_tracks_request(
        self, subscriber, mock_tracker
    ):
        """on_request_completed() should track model-specific request metrics."""
        event = RequestCompletedEvent(
            request_id="req-123",
            endpoint="/v1/chat/completions",
            model="gpt-4",
            duration_ms=1500.0,
            input_tokens=100,
            output_tokens=200,
            status_code=200,
            metadata={"user_id": "user-001"},
        )

        await subscriber.on_request_completed(event)

        mock_tracker.track_request.assert_called_once_with(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=200,
            latency_ms=1500.0,
            user="user-001",
            error=None,
        )

    @pytest.mark.asyncio
    async def test_on_request_completed_handles_missing_user(
        self, subscriber, mock_tracker
    ):
        """on_request_completed() should handle missing user_id in metadata."""
        event = RequestCompletedEvent(
            request_id="req-123",
            endpoint="/v1/embeddings",
            model="text-embedding-ada-002",
            duration_ms=500.0,
            input_tokens=100,
            output_tokens=0,
            status_code=200,
            metadata={},
        )

        await subscriber.on_request_completed(event)

        call_kwargs = mock_tracker.track_request.call_args[1]
        assert call_kwargs["user"] is None
        assert call_kwargs["error"] is None


@pytest.mark.unit
@pytest.mark.metrics
class TestKVCacheMetricsSubscriber:
    """Test KVCacheMetricsSubscriber event handling."""

    @pytest.fixture
    def mock_metrics(self):
        """Create a mock KVCacheMetrics."""
        metrics = Mock()
        metrics.record_cache_lookup = Mock()
        metrics.record_speedup = Mock()
        return metrics

    @pytest.fixture
    def subscriber(self, mock_metrics):
        """Create a KVCacheMetricsSubscriber with mock metrics."""
        return KVCacheMetricsSubscriber(mock_metrics)

    @pytest.mark.asyncio
    async def test_on_cache_lookup_records_lookup(self, subscriber, mock_metrics):
        """on_cache_lookup() should record cache lookup with tokens."""
        event = CacheLookupEvent(
            request_id="req-123",
            cache_type="kv",
            total_tokens=100,
            matched_tokens=75,
            hit_ratio=0.75,
            metadata={"endpoint": "/v1/chat/completions"},
        )

        await subscriber.on_cache_lookup(event)

        mock_metrics.record_cache_lookup.assert_called_once_with(
            endpoint="/v1/chat/completions",
            total_tokens=100,
            matched_tokens=75,
        )

    @pytest.mark.asyncio
    async def test_on_cache_lookup_uses_unknown_endpoint(
        self, subscriber, mock_metrics
    ):
        """on_cache_lookup() should use 'unknown' when endpoint not in metadata."""
        event = CacheLookupEvent(
            request_id="req-123",
            cache_type="kv",
            total_tokens=100,
            matched_tokens=50,
            hit_ratio=0.5,
            metadata={},
        )

        await subscriber.on_cache_lookup(event)

        call_kwargs = mock_metrics.record_cache_lookup.call_args[1]
        assert call_kwargs["endpoint"] == "unknown"

    @pytest.mark.asyncio
    async def test_on_speedup_measured_records_speedup(self, subscriber, mock_metrics):
        """on_speedup_measured() should record speedup measurements."""
        event = CacheSpeedupMeasuredEvent(
            request_id="req-123",
            baseline_ttft_ms=500.0,
            actual_ttft_ms=150.0,
            cache_hit_ratio=0.75,
            metadata={"endpoint": "/v1/chat/completions"},
        )

        await subscriber.on_speedup_measured(event)

        mock_metrics.record_speedup.assert_called_once_with(
            endpoint="/v1/chat/completions",
            baseline_ttft=500.0,
            actual_ttft=150.0,
            cache_hit_ratio=0.75,
        )

    @pytest.mark.asyncio
    async def test_on_speedup_measured_uses_unknown_endpoint(
        self, subscriber, mock_metrics
    ):
        """on_speedup_measured() should use 'unknown' when endpoint not in metadata."""
        event = CacheSpeedupMeasuredEvent(
            request_id="req-123",
            baseline_ttft_ms=500.0,
            actual_ttft_ms=200.0,
            cache_hit_ratio=0.6,
            metadata={},
        )

        await subscriber.on_speedup_measured(event)

        call_kwargs = mock_metrics.record_speedup.call_args[1]
        assert call_kwargs["endpoint"] == "unknown"


@pytest.mark.unit
@pytest.mark.metrics
class TestSubscriberIntegration:
    """Test integration scenarios with multiple subscribers."""

    @pytest.mark.asyncio
    async def test_multiple_subscribers_same_event(self):
        """Multiple subscribers should be able to handle the same event independently."""
        # Create mocks
        mock_metrics_tracker = Mock()
        mock_metrics_tracker.track_request = Mock()
        mock_dynamo_collector = Mock()
        mock_dynamo_collector.start_request = Mock()

        # Create subscribers
        metrics_sub = MetricsTrackerSubscriber(mock_metrics_tracker)
        dynamo_sub = DynamoMetricsSubscriber(mock_dynamo_collector)

        # Create event
        event = RequestStartedEvent(
            request_id="req-123",
            endpoint="/v1/chat/completions",
            model="gpt-4",
            input_tokens=100,
        )

        # Both should handle the event
        await metrics_sub.on_request_started(event)
        await dynamo_sub.on_request_started(event)

        # Both should have been called
        mock_metrics_tracker.track_request.assert_called_once()
        mock_dynamo_collector.start_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscriber_handles_event_with_minimal_data(self):
        """Subscribers should handle events with minimal required data."""
        mock_tracker = Mock()
        mock_tracker.track_request = Mock()
        subscriber = MetricsTrackerSubscriber(mock_tracker)

        # Event with only required fields
        event = RequestStartedEvent(
            endpoint="/v1/completions",
        )

        await subscriber.on_request_started(event)

        mock_tracker.track_request.assert_called_once_with("/v1/completions")

    @pytest.mark.asyncio
    async def test_cost_tracker_extracts_correct_metadata(self):
        """CostTrackerSubscriber should correctly extract metadata fields."""
        mock_tracker = Mock()
        mock_tracker.track_usage = Mock()
        subscriber = CostTrackerSubscriber(mock_tracker)

        event = RequestCompletedEvent(
            request_id="req-123",
            endpoint="/v1/chat/completions",
            model="gpt-4-turbo",
            duration_ms=2500.0,
            input_tokens=500,
            output_tokens=1000,
            cached_tokens=100,
            status_code=200,
            metadata={
                "api_key": "sk-production-key",
                "user_id": "user-premium-001",
                "extra_field": "ignored",
            },
        )

        await subscriber.on_request_completed(event)

        mock_tracker.track_usage.assert_called_once_with(
            api_key="sk-production-key",
            model="gpt-4-turbo",
            endpoint="/v1/chat/completions",
            prompt_tokens=500,
            completion_tokens=1000,
            cached_tokens=100,
            user_id="user-premium-001",
        )
