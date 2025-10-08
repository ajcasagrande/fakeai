"""
Comprehensive tests for all event types in fakeai/events/event_types.py.

This test file imports event modules directly to avoid the RuntimeError
from fakeai's __init__.py which initializes the app with async tasks.
"""

import json
import sys
import time
import uuid

# Block problematic imports before they happen
from unittest.mock import MagicMock

import pytest

_mock_app = MagicMock()
_mock_service = MagicMock()
sys.modules.setdefault('fakeai.app', _mock_app)
sys.modules.setdefault('fakeai.fakeai_service', _mock_service)

# Now we can safely import from fakeai.events
from fakeai.events.base import BaseEvent
from fakeai.events.event_types import (  # Request Lifecycle; Token Events; Stream Lifecycle; Latency & Performance; Cache Events; Model & Resource; Error & Recovery; Network & Client; Usage & Billing
    BackpressureDetectedEvent,
    BatchSizeChangedEvent,
    CacheEvictionEvent,
    CacheHitEvent,
    CacheLookupEvent,
    CacheMissEvent,
    CacheSpeedupMeasuredEvent,
    ChunkSentEvent,
    ClientDisconnectedEvent,
    CostCalculatedEvent,
    DecodeCompletedEvent,
    DecodeStartedEvent,
    ErrorOccurredEvent,
    ErrorPatternDetectedEvent,
    FirstTokenGeneratedEvent,
    GPUMetricsEvent,
    LatencyMeasuredEvent,
    ModelSelectedEvent,
    NetworkLatencyMeasuredEvent,
    PrefillCompletedEvent,
    PrefillStartedEvent,
    QueueDepthChangedEvent,
    QuotaUpdatedEvent,
    RateLimitHitEvent,
    RecoveryAttemptedEvent,
    RecoverySucceededEvent,
    RequestCompletedEvent,
    RequestDequeuedEvent,
    RequestFailedEvent,
    RequestQueuedEvent,
    RequestRoutedEvent,
    RequestStartedEvent,
    ResourceUtilizationEvent,
    SLOViolationEvent,
    StreamCancelledEvent,
    StreamCompletedEvent,
    StreamFailedEvent,
    StreamingTokenGeneratedEvent,
    StreamProgressEvent,
    StreamStartedEvent,
    ThroughputMeasuredEvent,
    TokenBatchGeneratedEvent,
    TokensGeneratedEvent,
    UsageRecordedEvent,
    WorkerAssignedEvent,
    WorkerCompletedEvent,
)

# ============================================================================
# Test Base Event Functionality
# ============================================================================


class TestBaseEventFunctionality:
    """Test base event features inherited by all event types."""

    def test_base_event_auto_generates_event_id(self):
        """Test that event_id is auto-generated."""
        event = BaseEvent()
        assert event.event_id is not None
        assert isinstance(event.event_id, str)
        # Should be a valid UUID
        uuid.UUID(event.event_id)

    def test_base_event_auto_generates_timestamp(self):
        """Test that timestamp is auto-generated."""
        before = time.time()
        event = BaseEvent()
        after = time.time()
        assert before <= event.timestamp <= after

    def test_base_event_unique_ids(self):
        """Test that each event gets a unique ID."""
        event1 = BaseEvent()
        event2 = BaseEvent()
        assert event1.event_id != event2.event_id

    def test_base_event_custom_request_id(self):
        """Test setting custom request_id."""
        request_id = "req-123"
        event = BaseEvent(request_id=request_id)
        assert event.request_id == request_id

    def test_base_event_metadata(self):
        """Test metadata field."""
        metadata = {"user": "test", "region": "us-west"}
        event = BaseEvent(metadata=metadata)
        assert event.metadata == metadata

    def test_base_event_to_dict(self):
        """Test to_dict serialization."""
        event = BaseEvent(
            request_id="req-456", metadata={"key": "value"}
        )
        event_dict = event.to_dict()

        assert isinstance(event_dict, dict)
        assert event_dict["event_id"] == event.event_id
        assert event_dict["event_type"] == "base.event"
        assert event_dict["timestamp"] == event.timestamp
        assert event_dict["request_id"] == "req-456"
        assert event_dict["metadata"] == {"key": "value"}

    def test_base_event_to_dict_json_serializable(self):
        """Test that to_dict output is JSON serializable."""
        event = BaseEvent(request_id="req-789")
        event_dict = event.to_dict()
        # Should not raise
        json_str = json.dumps(event_dict)
        assert isinstance(json_str, str)

    def test_base_event_to_dict_no_circular_references(self):
        """Test that to_dict doesn't create circular references."""
        event = BaseEvent()
        event_dict = event.to_dict()
        # Should be able to serialize deeply
        json.dumps(event_dict)


# ============================================================================
# Test Request Lifecycle Events
# ============================================================================


class TestRequestLifecycleEvents:
    """Test request lifecycle event types."""

    def test_request_started_event_creation(self):
        """Test RequestStartedEvent can be instantiated."""
        event = RequestStartedEvent(
            endpoint="/v1/chat/completions",
            method="POST",
            model="gpt-4",
            user_id="user-123",
            api_key="sk-test",
            client_ip="192.168.1.1",
            streaming=True,
            input_tokens=100,
        )
        assert event.event_type == "request.started"
        assert event.endpoint == "/v1/chat/completions"
        assert event.method == "POST"
        assert event.model == "gpt-4"
        assert event.user_id == "user-123"
        assert event.api_key == "sk-test"
        assert event.client_ip == "192.168.1.1"
        assert event.streaming is True
        assert event.input_tokens == 100

    def test_request_started_event_defaults(self):
        """Test RequestStartedEvent default values."""
        event = RequestStartedEvent()
        assert event.endpoint == ""
        assert event.method == "POST"
        assert event.model is None
        assert event.user_id is None
        assert event.api_key is None
        assert event.client_ip is None
        assert event.streaming is False
        assert event.input_tokens is None

    def test_request_started_event_serialization(self):
        """Test RequestStartedEvent to_dict."""
        event = RequestStartedEvent(
            endpoint="/v1/completions",
            model="gpt-3.5-turbo",
            streaming=True,
        )
        event_dict = event.to_dict()

        assert event_dict["event_type"] == "request.started"
        assert event_dict["endpoint"] == "/v1/completions"
        assert event_dict["model"] == "gpt-3.5-turbo"
        assert event_dict["streaming"] is True
        # Should be JSON serializable
        json.dumps(event_dict)

    def test_request_completed_event_creation(self):
        """Test RequestCompletedEvent with all fields."""
        event = RequestCompletedEvent(
            endpoint="/v1/chat/completions",
            model="gpt-4",
            duration_ms=1234.5,
            status_code=200,
            input_tokens=50,
            output_tokens=150,
            cached_tokens=10,
            finish_reason="stop",
        )
        assert event.event_type == "request.completed"
        assert event.endpoint == "/v1/chat/completions"
        assert event.model == "gpt-4"
        assert event.duration_ms == 1234.5
        assert event.status_code == 200
        assert event.input_tokens == 50
        assert event.output_tokens == 150
        assert event.cached_tokens == 10
        assert event.finish_reason == "stop"

    def test_request_completed_event_defaults(self):
        """Test RequestCompletedEvent default values."""
        event = RequestCompletedEvent()
        assert event.duration_ms == 0.0
        assert event.status_code == 200
        assert event.input_tokens == 0
        assert event.output_tokens == 0
        assert event.cached_tokens == 0
        assert event.finish_reason is None

    def test_request_failed_event_creation(self):
        """Test RequestFailedEvent with error details."""
        event = RequestFailedEvent(
            endpoint="/v1/chat/completions",
            model="gpt-4",
            duration_ms=500.0,
            error_type="RateLimitError",
            error_message="Rate limit exceeded",
            status_code=429,
        )
        assert event.event_type == "request.failed"
        assert event.endpoint == "/v1/chat/completions"
        assert event.model == "gpt-4"
        assert event.duration_ms == 500.0
        assert event.error_type == "RateLimitError"
        assert event.error_message == "Rate limit exceeded"
        assert event.status_code == 429

    def test_request_failed_event_defaults(self):
        """Test RequestFailedEvent default values."""
        event = RequestFailedEvent()
        assert event.error_type == ""
        assert event.error_message == ""
        assert event.status_code == 500

    def test_request_queued_event(self):
        """Test RequestQueuedEvent."""
        event = RequestQueuedEvent(queue_name="high_priority", queue_depth=15)
        assert event.event_type == "request.queued"
        assert event.queue_name == "high_priority"
        assert event.queue_depth == 15

    def test_request_dequeued_event(self):
        """Test RequestDequeuedEvent."""
        event = RequestDequeuedEvent(queue_name="normal", wait_time_ms=234.5)
        assert event.event_type == "request.dequeued"
        assert event.queue_name == "normal"
        assert event.wait_time_ms == 234.5

    def test_request_routed_event(self):
        """Test RequestRoutedEvent."""
        event = RequestRoutedEvent(worker_id="worker-01", routing_cost_ms=5.2)
        assert event.event_type == "request.routed"
        assert event.worker_id == "worker-01"
        assert event.routing_cost_ms == 5.2


# ============================================================================
# Test Token Events
# ============================================================================


class TestTokenEvents:
    """Test token-related event types."""

    def test_tokens_generated_event(self):
        """Test TokensGeneratedEvent."""
        event = TokensGeneratedEvent(
            endpoint="/v1/chat/completions",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=200,
            cached_tokens=50,
        )
        assert event.event_type == "tokens.generated"
        assert event.endpoint == "/v1/chat/completions"
        assert event.model == "gpt-4"
        assert event.prompt_tokens == 100
        assert event.completion_tokens == 200
        assert event.cached_tokens == 50

    def test_token_batch_generated_event_with_tokens(self):
        """Test TokenBatchGeneratedEvent with token list."""
        tokens = ["hello", "world", "!"]
        event = TokenBatchGeneratedEvent(batch_size=3, tokens=tokens)
        assert event.event_type == "tokens.batch_generated"
        assert event.batch_size == 3
        assert event.tokens == tokens

    def test_token_batch_generated_event_default_tokens(self):
        """Test TokenBatchGeneratedEvent default tokens list."""
        event = TokenBatchGeneratedEvent(batch_size=0)
        assert event.tokens == []
        assert isinstance(event.tokens, list)

    def test_token_batch_post_init_hook(self):
        """Test TokenBatchGeneratedEvent __post_init__ initializes tokens."""
        event = TokenBatchGeneratedEvent(batch_size=0, tokens=None)
        # __post_init__ should convert None to []
        assert event.tokens == []

    def test_streaming_token_generated_event(self):
        """Test StreamingTokenGeneratedEvent with sequence."""
        event = StreamingTokenGeneratedEvent(
            stream_id="stream-123",
            token="Hello",
            sequence_number=5,
            timestamp_ns=1234567890,
            chunk_size_bytes=50,
        )
        assert event.event_type == "stream.token_generated"
        assert event.stream_id == "stream-123"
        assert event.token == "Hello"
        assert event.sequence_number == 5
        assert event.timestamp_ns == 1234567890
        assert event.chunk_size_bytes == 50

    def test_streaming_token_generated_event_sequence(self):
        """Test StreamingTokenGeneratedEvent sequence ordering."""
        events = [
            StreamingTokenGeneratedEvent(
                stream_id="stream-456", token=f"token_{i}", sequence_number=i
            )
            for i in range(5)
        ]
        for i, event in enumerate(events):
            assert event.sequence_number == i
            assert event.token == f"token_{i}"

    def test_first_token_generated_event(self):
        """Test FirstTokenGeneratedEvent."""
        event = FirstTokenGeneratedEvent(stream_id="stream-789", ttft_ms=123.45)
        assert event.event_type == "stream.first_token"
        assert event.stream_id == "stream-789"
        assert event.ttft_ms == 123.45


# ============================================================================
# Test Stream Lifecycle Events
# ============================================================================


class TestStreamLifecycleEvents:
    """Test stream lifecycle event types."""

    def test_stream_started_event(self):
        """Test StreamStartedEvent with all fields."""
        event = StreamStartedEvent(
            stream_id="stream-001",
            endpoint="/v1/chat/completions",
            model="gpt-4",
            input_tokens=50,
            temperature=0.7,
            max_tokens=150,
            client_id="client-123",
        )
        assert event.event_type == "stream.started"
        assert event.stream_id == "stream-001"
        assert event.endpoint == "/v1/chat/completions"
        assert event.model == "gpt-4"
        assert event.input_tokens == 50
        assert event.temperature == 0.7
        assert event.max_tokens == 150
        assert event.client_id == "client-123"

    def test_stream_started_event_optional_fields(self):
        """Test StreamStartedEvent optional fields."""
        event = StreamStartedEvent(stream_id="stream-002")
        assert event.temperature is None
        assert event.max_tokens is None
        assert event.client_id is None

    def test_stream_progress_event(self):
        """Test StreamProgressEvent."""
        event = StreamProgressEvent(
            stream_id="stream-003", tokens_generated=50, elapsed_ms=500.0
        )
        assert event.event_type == "stream.progress"
        assert event.stream_id == "stream-003"
        assert event.tokens_generated == 50
        assert event.elapsed_ms == 500.0

    def test_stream_completed_event(self):
        """Test StreamCompletedEvent."""
        event = StreamCompletedEvent(
            stream_id="stream-004",
            endpoint="/v1/completions",
            duration_ms=2500.0,
            token_count=100,
            finish_reason="stop",
            client_id="client-456",
        )
        assert event.event_type == "stream.completed"
        assert event.stream_id == "stream-004"
        assert event.endpoint == "/v1/completions"
        assert event.duration_ms == 2500.0
        assert event.token_count == 100
        assert event.finish_reason == "stop"
        assert event.client_id == "client-456"

    def test_stream_completed_event_default_finish_reason(self):
        """Test StreamCompletedEvent default finish_reason."""
        event = StreamCompletedEvent(stream_id="stream-005")
        assert event.finish_reason == "stop"

    def test_stream_failed_event(self):
        """Test StreamFailedEvent."""
        event = StreamFailedEvent(
            stream_id="stream-006",
            endpoint="/v1/chat/completions",
            duration_ms=1000.0,
            error_message="Connection timeout",
            token_count=25,
            client_id="client-789",
        )
        assert event.event_type == "stream.failed"
        assert event.stream_id == "stream-006"
        assert event.error_message == "Connection timeout"
        assert event.token_count == 25

    def test_stream_cancelled_event(self):
        """Test StreamCancelledEvent."""
        event = StreamCancelledEvent(
            stream_id="stream-007",
            cancellation_point="mid_stream",
            reason="User disconnected",
        )
        assert event.event_type == "stream.cancelled"
        assert event.stream_id == "stream-007"
        assert event.cancellation_point == "mid_stream"
        assert event.reason == "User disconnected"


# ============================================================================
# Test Latency & Performance Events
# ============================================================================


class TestLatencyPerformanceEvents:
    """Test latency and performance event types."""

    def test_prefill_started_event(self):
        """Test PrefillStartedEvent."""
        event = PrefillStartedEvent(input_tokens=100)
        assert event.event_type == "prefill.started"
        assert event.input_tokens == 100

    def test_prefill_completed_event(self):
        """Test PrefillCompletedEvent."""
        event = PrefillCompletedEvent(prefill_time_ms=50.5)
        assert event.event_type == "prefill.completed"
        assert event.prefill_time_ms == 50.5

    def test_decode_started_event(self):
        """Test DecodeStartedEvent."""
        event = DecodeStartedEvent()
        assert event.event_type == "decode.started"

    def test_decode_completed_event(self):
        """Test DecodeCompletedEvent."""
        event = DecodeCompletedEvent(decode_time_ms=200.0, output_tokens=50)
        assert event.event_type == "decode.completed"
        assert event.decode_time_ms == 200.0
        assert event.output_tokens == 50

    def test_latency_measured_event_ttft(self):
        """Test LatencyMeasuredEvent for TTFT."""
        event = LatencyMeasuredEvent(
            endpoint="/v1/chat/completions",
            latency_type="ttft",
            value_ms=123.45,
        )
        assert event.event_type == "latency.measured"
        assert event.endpoint == "/v1/chat/completions"
        assert event.latency_type == "ttft"
        assert event.value_ms == 123.45

    def test_latency_measured_event_tpot(self):
        """Test LatencyMeasuredEvent for TPOT."""
        event = LatencyMeasuredEvent(
            endpoint="/v1/completions", latency_type="tpot", value_ms=15.2
        )
        assert event.latency_type == "tpot"
        assert event.value_ms == 15.2

    def test_latency_measured_event_total(self):
        """Test LatencyMeasuredEvent for total latency."""
        event = LatencyMeasuredEvent(
            endpoint="/v1/embeddings", latency_type="total", value_ms=2000.0
        )
        assert event.latency_type == "total"
        assert event.value_ms == 2000.0

    def test_throughput_measured_event(self):
        """Test ThroughputMeasuredEvent."""
        event = ThroughputMeasuredEvent(
            endpoint="/v1/chat/completions",
            model="gpt-4",
            rps=10.5,
            tps=500.0,
            window_seconds=60,
        )
        assert event.event_type == "throughput.measured"
        assert event.endpoint == "/v1/chat/completions"
        assert event.model == "gpt-4"
        assert event.rps == 10.5
        assert event.tps == 500.0
        assert event.window_seconds == 60

    def test_queue_depth_changed_event(self):
        """Test QueueDepthChangedEvent."""
        event = QueueDepthChangedEvent(
            queue_name="high_priority", depth=50, max_depth=100
        )
        assert event.event_type == "queue.depth_changed"
        assert event.queue_name == "high_priority"
        assert event.depth == 50
        assert event.max_depth == 100

    def test_batch_size_changed_event(self):
        """Test BatchSizeChangedEvent."""
        event = BatchSizeChangedEvent(batch_size=32, avg_batch_size=28.5)
        assert event.event_type == "batch.size_changed"
        assert event.batch_size == 32
        assert event.avg_batch_size == 28.5


# ============================================================================
# Test Cache Events
# ============================================================================


class TestCacheEvents:
    """Test cache-related event types."""

    def test_cache_lookup_event(self):
        """Test CacheLookupEvent."""
        event = CacheLookupEvent(
            cache_type="kv",
            total_tokens=100,
            matched_tokens=75,
            hit_ratio=0.75,
        )
        assert event.event_type == "cache.lookup"
        assert event.cache_type == "kv"
        assert event.total_tokens == 100
        assert event.matched_tokens == 75
        assert event.hit_ratio == 0.75

    def test_cache_hit_event(self):
        """Test CacheHitEvent."""
        event = CacheHitEvent(
            cache_type="prompt", cached_tokens=50, speedup_ms=100.0
        )
        assert event.event_type == "cache.hit"
        assert event.cache_type == "prompt"
        assert event.cached_tokens == 50
        assert event.speedup_ms == 100.0

    def test_cache_miss_event(self):
        """Test CacheMissEvent."""
        event = CacheMissEvent(cache_type="kv")
        assert event.event_type == "cache.miss"
        assert event.cache_type == "kv"

    def test_cache_speedup_measured_event(self):
        """Test CacheSpeedupMeasuredEvent."""
        event = CacheSpeedupMeasuredEvent(
            baseline_ttft_ms=200.0,
            actual_ttft_ms=50.0,
            cache_hit_ratio=0.8,
        )
        assert event.event_type == "cache.speedup_measured"
        assert event.baseline_ttft_ms == 200.0
        assert event.actual_ttft_ms == 50.0
        assert event.cache_hit_ratio == 0.8

    def test_cache_eviction_event(self):
        """Test CacheEvictionEvent."""
        event = CacheEvictionEvent(
            cache_type="kv", evicted_entries=100, reason="memory_pressure"
        )
        assert event.event_type == "cache.eviction"
        assert event.cache_type == "kv"
        assert event.evicted_entries == 100
        assert event.reason == "memory_pressure"


# ============================================================================
# Test Model & Resource Events
# ============================================================================


class TestModelResourceEvents:
    """Test model and resource event types."""

    def test_model_selected_event(self):
        """Test ModelSelectedEvent."""
        event = ModelSelectedEvent(model_id="gpt-4", context_window=8192)
        assert event.event_type == "model.selected"
        assert event.model_id == "gpt-4"
        assert event.context_window == 8192

    def test_worker_assigned_event(self):
        """Test WorkerAssignedEvent."""
        event = WorkerAssignedEvent(
            worker_id="worker-01", worker_load=0.75, routing_cost_ms=5.0
        )
        assert event.event_type == "worker.assigned"
        assert event.worker_id == "worker-01"
        assert event.worker_load == 0.75
        assert event.routing_cost_ms == 5.0

    def test_worker_completed_event(self):
        """Test WorkerCompletedEvent."""
        event = WorkerCompletedEvent(
            worker_id="worker-02", duration_ms=1234.5, success=True
        )
        assert event.event_type == "worker.completed"
        assert event.worker_id == "worker-02"
        assert event.duration_ms == 1234.5
        assert event.success is True

    def test_worker_completed_event_failure(self):
        """Test WorkerCompletedEvent with failure."""
        event = WorkerCompletedEvent(worker_id="worker-03", success=False)
        assert event.success is False

    def test_resource_utilization_event(self):
        """Test ResourceUtilizationEvent."""
        event = ResourceUtilizationEvent(
            resource_type="cpu",
            resource_id="cpu-0",
            utilization_percent=75.5,
        )
        assert event.event_type == "resource.utilization"
        assert event.resource_type == "cpu"
        assert event.resource_id == "cpu-0"
        assert event.utilization_percent == 75.5

    def test_gpu_metrics_event(self):
        """Test GPUMetricsEvent."""
        event = GPUMetricsEvent(
            gpu_id="GPU-0",
            utilization=85.5,
            memory_used=8000,
            memory_total=16000,
            power_watts=250.0,
            temperature=75.0,
        )
        assert event.event_type == "gpu.metrics"
        assert event.gpu_id == "GPU-0"
        assert event.utilization == 85.5
        assert event.memory_used == 8000
        assert event.memory_total == 16000
        assert event.power_watts == 250.0
        assert event.temperature == 75.0


# ============================================================================
# Test Error & Recovery Events
# ============================================================================


class TestErrorRecoveryEvents:
    """Test error and recovery event types."""

    def test_error_occurred_event(self):
        """Test ErrorOccurredEvent with all fields."""
        stack_trace = "Traceback (most recent call last):\n  File..."
        event = ErrorOccurredEvent(
            endpoint="/v1/chat/completions",
            model="gpt-4",
            error_type="TimeoutError",
            error_message="Request timed out after 30s",
            stack_trace=stack_trace,
        )
        assert event.event_type == "error.occurred"
        assert event.endpoint == "/v1/chat/completions"
        assert event.model == "gpt-4"
        assert event.error_type == "TimeoutError"
        assert event.error_message == "Request timed out after 30s"
        assert event.stack_trace == stack_trace

    def test_error_occurred_event_fingerprinting(self):
        """Test ErrorOccurredEvent for error fingerprinting."""
        event1 = ErrorOccurredEvent(
            error_type="RateLimitError",
            error_message="Rate limit exceeded",
        )
        event2 = ErrorOccurredEvent(
            error_type="RateLimitError",
            error_message="Rate limit exceeded",
        )
        # Same error type and message should allow grouping
        assert event1.error_type == event2.error_type
        assert event1.error_message == event2.error_message

    def test_error_occurred_event_optional_fields(self):
        """Test ErrorOccurredEvent optional fields."""
        event = ErrorOccurredEvent(error_type="ValueError")
        assert event.model is None
        assert event.stack_trace is None

    def test_error_pattern_detected_event(self):
        """Test ErrorPatternDetectedEvent."""
        endpoints = ["/v1/chat/completions", "/v1/completions"]
        event = ErrorPatternDetectedEvent(
            error_signature="RateLimitError:exceeded",
            error_type="RateLimitError",
            count=10,
            affected_endpoints=endpoints,
        )
        assert event.event_type == "error.pattern_detected"
        assert event.error_signature == "RateLimitError:exceeded"
        assert event.error_type == "RateLimitError"
        assert event.count == 10
        assert event.affected_endpoints == endpoints

    def test_error_pattern_detected_event_default_endpoints(self):
        """Test ErrorPatternDetectedEvent default endpoints list."""
        event = ErrorPatternDetectedEvent(error_signature="sig", error_type="err")
        assert event.affected_endpoints == []
        assert isinstance(event.affected_endpoints, list)

    def test_error_pattern_detected_post_init(self):
        """Test ErrorPatternDetectedEvent __post_init__ initializes list."""
        event = ErrorPatternDetectedEvent(
            error_signature="sig", error_type="err", affected_endpoints=None
        )
        assert event.affected_endpoints == []

    def test_recovery_attempted_event(self):
        """Test RecoveryAttemptedEvent."""
        event = RecoveryAttemptedEvent(retry_count=3)
        assert event.event_type == "recovery.attempted"
        assert event.retry_count == 3

    def test_recovery_succeeded_event(self):
        """Test RecoverySucceededEvent."""
        event = RecoverySucceededEvent(time_to_recovery_ms=500.0)
        assert event.event_type == "recovery.succeeded"
        assert event.time_to_recovery_ms == 500.0

    def test_slo_violation_event(self):
        """Test SLOViolationEvent."""
        event = SLOViolationEvent(
            endpoint="/v1/chat/completions",
            slo_type="latency",
            threshold_value=1000.0,
            actual_value=1500.0,
            severity="warning",
        )
        assert event.event_type == "slo.violation"
        assert event.endpoint == "/v1/chat/completions"
        assert event.slo_type == "latency"
        assert event.threshold_value == 1000.0
        assert event.actual_value == 1500.0
        assert event.severity == "warning"

    def test_slo_violation_event_critical(self):
        """Test SLOViolationEvent with critical severity."""
        event = SLOViolationEvent(
            endpoint="/v1/completions",
            slo_type="error_rate",
            threshold_value=0.01,
            actual_value=0.05,
            severity="critical",
        )
        assert event.severity == "critical"


# ============================================================================
# Test Network & Client Events
# ============================================================================


class TestNetworkClientEvents:
    """Test network and client event types."""

    def test_chunk_sent_event(self):
        """Test ChunkSentEvent."""
        event = ChunkSentEvent(stream_id="stream-001", chunk_size_bytes=1024)
        assert event.event_type == "network.chunk_sent"
        assert event.stream_id == "stream-001"
        assert event.chunk_size_bytes == 1024

    def test_backpressure_detected_event(self):
        """Test BackpressureDetectedEvent."""
        event = BackpressureDetectedEvent(
            stream_id="stream-002", buffer_size=10000
        )
        assert event.event_type == "network.backpressure"
        assert event.stream_id == "stream-002"
        assert event.buffer_size == 10000

    def test_client_disconnected_event(self):
        """Test ClientDisconnectedEvent."""
        event = ClientDisconnectedEvent(
            stream_id="stream-003",
            reason="Connection closed by client",
            tokens_sent=50,
        )
        assert event.event_type == "client.disconnected"
        assert event.stream_id == "stream-003"
        assert event.reason == "Connection closed by client"
        assert event.tokens_sent == 50

    def test_network_latency_measured_event(self):
        """Test NetworkLatencyMeasuredEvent."""
        event = NetworkLatencyMeasuredEvent(latency_ms=25.5)
        assert event.event_type == "network.latency_measured"
        assert event.latency_ms == 25.5


# ============================================================================
# Test Usage & Billing Events
# ============================================================================


class TestUsageBillingEvents:
    """Test usage and billing event types."""

    def test_usage_recorded_event(self):
        """Test UsageRecordedEvent."""
        event = UsageRecordedEvent(
            user_id="user-123",
            project_id="project-456",
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=200,
            cost_usd=0.015,
        )
        assert event.event_type == "usage.recorded"
        assert event.user_id == "user-123"
        assert event.project_id == "project-456"
        assert event.model == "gpt-4"
        assert event.endpoint == "/v1/chat/completions"
        assert event.prompt_tokens == 100
        assert event.completion_tokens == 200
        assert event.cost_usd == 0.015

    def test_usage_recorded_event_optional_project(self):
        """Test UsageRecordedEvent with optional project_id."""
        event = UsageRecordedEvent(
            user_id="user-789", model="gpt-3.5-turbo", endpoint="/v1/completions"
        )
        assert event.project_id is None

    def test_quota_updated_event(self):
        """Test QuotaUpdatedEvent."""
        event = QuotaUpdatedEvent(
            user_id="user-123",
            quota_type="tokens",
            used=50000.0,
            limit=100000.0,
        )
        assert event.event_type == "quota.updated"
        assert event.user_id == "user-123"
        assert event.quota_type == "tokens"
        assert event.used == 50000.0
        assert event.limit == 100000.0

    def test_rate_limit_hit_event(self):
        """Test RateLimitHitEvent."""
        event = RateLimitHitEvent(
            user_id="user-456",
            endpoint="/v1/chat/completions",
            limit_type="requests",
            current_value=100,
            limit_value=100,
            retry_after_seconds=60,
        )
        assert event.event_type == "ratelimit.hit"
        assert event.user_id == "user-456"
        assert event.endpoint == "/v1/chat/completions"
        assert event.limit_type == "requests"
        assert event.current_value == 100
        assert event.limit_value == 100
        assert event.retry_after_seconds == 60

    def test_cost_calculated_event(self):
        """Test CostCalculatedEvent."""
        event = CostCalculatedEvent(
            model="gpt-4",
            input_cost=0.005,
            output_cost=0.010,
            total_cost=0.015,
        )
        assert event.event_type == "cost.calculated"
        assert event.model == "gpt-4"
        assert event.input_cost == 0.005
        assert event.output_cost == 0.010
        assert event.total_cost == 0.015

    def test_cost_calculated_event_with_decimal(self):
        """Test CostCalculatedEvent with Decimal values."""
        # Test that float values work (Decimal would be better but float is ok)
        input_cost = 0.00001
        output_cost = 0.00002
        total_cost = 0.00003
        event = CostCalculatedEvent(
            model="gpt-3.5-turbo",
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
        )
        assert event.input_cost == input_cost
        assert event.output_cost == output_cost
        assert event.total_cost == total_cost


# ============================================================================
# Test Event Serialization and JSON Compatibility
# ============================================================================


class TestEventSerialization:
    """Test that all events serialize correctly."""

    @pytest.mark.parametrize(
        "event_class,kwargs",
        [
            (RequestStartedEvent, {"endpoint": "/test"}),
            (RequestCompletedEvent, {"model": "test"}),
            (RequestFailedEvent, {"error_type": "test"}),
            (TokensGeneratedEvent, {"model": "test"}),
            (StreamingTokenGeneratedEvent, {"stream_id": "test"}),
            (StreamStartedEvent, {"stream_id": "test"}),
            (StreamCompletedEvent, {"stream_id": "test"}),
            (LatencyMeasuredEvent, {"latency_type": "ttft"}),
            (CacheHitEvent, {"cache_type": "kv"}),
            (ErrorOccurredEvent, {"error_type": "test"}),
            (GPUMetricsEvent, {"gpu_id": "test"}),
            (ChunkSentEvent, {"stream_id": "test"}),
            (UsageRecordedEvent, {"user_id": "test", "model": "test"}),
            (CostCalculatedEvent, {"model": "test"}),
        ],
    )
    def test_event_to_dict_json_serializable(self, event_class, kwargs):
        """Test that all event types produce JSON-serializable output."""
        event = event_class(**kwargs)
        event_dict = event.to_dict()
        # Should not raise
        json_str = json.dumps(event_dict)
        assert isinstance(json_str, str)
        # Should be deserializable
        deserialized = json.loads(json_str)
        assert isinstance(deserialized, dict)

    def test_all_events_have_base_fields(self):
        """Test that all events have base fields."""
        events = [
            RequestStartedEvent(),
            RequestCompletedEvent(),
            TokensGeneratedEvent(),
            StreamStartedEvent(stream_id="test"),
            ErrorOccurredEvent(error_type="test"),
            CostCalculatedEvent(model="test"),
        ]
        for event in events:
            event_dict = event.to_dict()
            assert "event_id" in event_dict
            assert "event_type" in event_dict
            assert "timestamp" in event_dict
            assert "request_id" in event_dict
            assert "metadata" in event_dict

    def test_event_serialization_includes_all_fields(self):
        """Test that to_dict includes all fields."""
        event = RequestStartedEvent(
            endpoint="/v1/chat/completions",
            method="POST",
            model="gpt-4",
            streaming=True,
        )
        event_dict = event.to_dict()
        # Should include all fields
        assert event_dict["endpoint"] == "/v1/chat/completions"
        assert event_dict["method"] == "POST"
        assert event_dict["model"] == "gpt-4"
        assert event_dict["streaming"] is True


# ============================================================================
# Test Field Validation and Type Checking
# ============================================================================


class TestFieldValidation:
    """Test field validation and type checking."""

    def test_event_with_invalid_types_still_instantiates(self):
        """Test that dataclasses allow wrong types (no runtime validation)."""
        # Dataclasses don't enforce types at runtime by default
        event = RequestCompletedEvent(
            endpoint="/test",
            model="gpt-4",
            duration_ms="not_a_float",  # Wrong type
        )
        # This actually works in Python - types are hints
        assert event.duration_ms == "not_a_float"

    def test_required_fields_with_defaults(self):
        """Test that fields with defaults can be omitted."""
        # All our events have defaults, so this should work
        event = RequestStartedEvent()
        assert event.endpoint == ""
        assert event.method == "POST"

    def test_optional_fields_can_be_none(self):
        """Test that Optional fields can be None."""
        event = RequestStartedEvent(
            endpoint="/test",
            model=None,  # Optional field
            user_id=None,  # Optional field
        )
        assert event.model is None
        assert event.user_id is None

    def test_list_fields_with_post_init(self):
        """Test that list fields with __post_init__ work correctly."""
        # TokenBatchGeneratedEvent has __post_init__ for tokens
        event1 = TokenBatchGeneratedEvent(batch_size=0)
        assert event1.tokens == []

        event2 = TokenBatchGeneratedEvent(batch_size=0, tokens=None)
        assert event2.tokens == []

        event3 = TokenBatchGeneratedEvent(batch_size=2, tokens=["a", "b"])
        assert event3.tokens == ["a", "b"]

    def test_error_pattern_detected_post_init(self):
        """Test ErrorPatternDetectedEvent __post_init__ hook."""
        event1 = ErrorPatternDetectedEvent(
            error_signature="sig", error_type="err"
        )
        assert event1.affected_endpoints == []

        event2 = ErrorPatternDetectedEvent(
            error_signature="sig", error_type="err", affected_endpoints=None
        )
        assert event2.affected_endpoints == []

        event3 = ErrorPatternDetectedEvent(
            error_signature="sig",
            error_type="err",
            affected_endpoints=["/v1/test"],
        )
        assert event3.affected_endpoints == ["/v1/test"]


# ============================================================================
# Test Event Type Completeness
# ============================================================================


class TestEventTypeCompleteness:
    """Test that we have comprehensive coverage of event types."""

    def test_all_request_lifecycle_events_covered(self):
        """Test all request lifecycle events are instantiable."""
        events = [
            RequestStartedEvent(),
            RequestCompletedEvent(),
            RequestFailedEvent(),
            RequestQueuedEvent(),
            RequestDequeuedEvent(),
            RequestRoutedEvent(worker_id="test"),
        ]
        for event in events:
            assert hasattr(event, "event_type")
            assert hasattr(event, "event_id")

    def test_all_stream_events_covered(self):
        """Test all stream events are instantiable."""
        events = [
            StreamStartedEvent(stream_id="test"),
            StreamProgressEvent(stream_id="test"),
            StreamCompletedEvent(stream_id="test"),
            StreamFailedEvent(stream_id="test"),
            StreamCancelledEvent(stream_id="test"),
            StreamingTokenGeneratedEvent(stream_id="test"),
            FirstTokenGeneratedEvent(stream_id="test"),
        ]
        for event in events:
            assert "stream" in event.event_type.lower()

    def test_all_cache_events_covered(self):
        """Test all cache events are instantiable."""
        events = [
            CacheLookupEvent(),
            CacheHitEvent(),
            CacheMissEvent(),
            CacheSpeedupMeasuredEvent(),
            CacheEvictionEvent(),
        ]
        for event in events:
            assert "cache" in event.event_type

    def test_all_error_events_covered(self):
        """Test all error events are instantiable."""
        events = [
            ErrorOccurredEvent(error_type="test"),
            ErrorPatternDetectedEvent(error_signature="test", error_type="test"),
            RecoveryAttemptedEvent(),
            RecoverySucceededEvent(),
            SLOViolationEvent(slo_type="test"),
        ]
        for event in events:
            assert hasattr(event, "event_type")

    def test_all_network_events_covered(self):
        """Test all network events are instantiable."""
        events = [
            ChunkSentEvent(stream_id="test"),
            BackpressureDetectedEvent(stream_id="test"),
            ClientDisconnectedEvent(stream_id="test"),
            NetworkLatencyMeasuredEvent(),
        ]
        for event in events:
            assert hasattr(event, "event_type")

    def test_all_billing_events_covered(self):
        """Test all billing events are instantiable."""
        events = [
            UsageRecordedEvent(user_id="test", model="test"),
            QuotaUpdatedEvent(user_id="test"),
            RateLimitHitEvent(user_id="test"),
            CostCalculatedEvent(model="test"),
        ]
        for event in events:
            assert hasattr(event, "event_type")


# ============================================================================
# Test Event Type Strings
# ============================================================================


class TestEventTypeStrings:
    """Test that event_type strings follow conventions."""

    def test_event_types_use_dot_notation(self):
        """Test that event types use dot notation."""
        events = [
            (RequestStartedEvent(), "request.started"),
            (RequestCompletedEvent(), "request.completed"),
            (StreamStartedEvent(stream_id="test"), "stream.started"),
            (TokensGeneratedEvent(), "tokens.generated"),
            (CacheHitEvent(), "cache.hit"),
            (ErrorOccurredEvent(error_type="test"), "error.occurred"),
        ]
        for event, expected_type in events:
            assert event.event_type == expected_type
            assert "." in event.event_type

    def test_event_types_are_descriptive(self):
        """Test that event types are descriptive."""
        event = LatencyMeasuredEvent(latency_type="ttft")
        assert event.event_type == "latency.measured"
        assert len(event.event_type.split(".")) == 2

        event = CacheSpeedupMeasuredEvent()
        assert event.event_type == "cache.speedup_measured"


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_event_with_empty_strings(self):
        """Test events with empty string fields."""
        event = RequestStartedEvent(endpoint="", model="")
        assert event.endpoint == ""
        assert event.model == ""

    def test_event_with_zero_values(self):
        """Test events with zero numeric values."""
        event = RequestCompletedEvent(
            duration_ms=0.0,
            input_tokens=0,
            output_tokens=0,
        )
        assert event.duration_ms == 0.0
        assert event.input_tokens == 0
        assert event.output_tokens == 0

    def test_event_with_negative_values(self):
        """Test events with negative values (shouldn't break)."""
        # While semantically wrong, dataclasses allow it
        event = LatencyMeasuredEvent(value_ms=-10.0)
        assert event.value_ms == -10.0

    def test_event_with_very_large_values(self):
        """Test events with very large values."""
        event = ThroughputMeasuredEvent(
            rps=999999.0,
            tps=10000000.0,
        )
        assert event.rps == 999999.0
        assert event.tps == 10000000.0

    def test_event_with_special_characters(self):
        """Test events with special characters in strings."""
        event = ErrorOccurredEvent(
            error_type="ValueError",
            error_message="Error: 'foo' != \"bar\" \n\t",
        )
        assert "Error:" in event.error_message
        assert "\n" in event.error_message
        # Should still serialize
        json.dumps(event.to_dict())

    def test_event_metadata_with_nested_data(self):
        """Test events with complex nested metadata."""
        metadata = {
            "user": {"id": "123", "org": "test"},
            "tags": ["production", "high_priority"],
            "config": {"retry": True, "timeout": 30},
        }
        event = BaseEvent(metadata=metadata)
        assert event.metadata == metadata
        # Should serialize
        event_dict = event.to_dict()
        json.dumps(event_dict)

    def test_multiple_events_same_request_id(self):
        """Test multiple events with the same request_id."""
        request_id = "req-shared-123"
        events = [
            RequestStartedEvent(request_id=request_id),
            TokensGeneratedEvent(request_id=request_id),
            RequestCompletedEvent(request_id=request_id),
        ]
        for event in events:
            assert event.request_id == request_id

    def test_event_timestamps_are_sequential(self):
        """Test that events created sequentially have increasing timestamps."""
        event1 = BaseEvent()
        time.sleep(0.001)  # Small delay
        event2 = BaseEvent()
        assert event2.timestamp >= event1.timestamp
