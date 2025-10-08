"""Specific event type definitions for the FakeAI metrics system."""

from dataclasses import dataclass, field
from typing import Optional

from .base import BaseEvent

# ============================================================================
# Request Lifecycle Events
# ============================================================================


@dataclass
class RequestStartedEvent(BaseEvent):
    """Event emitted when a request starts processing."""

    event_type: str = "request.started"
    endpoint: str = ""
    method: str = "POST"
    model: Optional[str] = None
    user_id: Optional[str] = None
    api_key: Optional[str] = None
    client_ip: Optional[str] = None
    streaming: bool = False
    input_tokens: Optional[int] = None


@dataclass
class RequestCompletedEvent(BaseEvent):
    """Event emitted when a request completes successfully."""

    event_type: str = "request.completed"
    endpoint: str = ""
    model: str = ""
    duration_ms: float = 0.0
    status_code: int = 200
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    finish_reason: Optional[str] = None


@dataclass
class RequestFailedEvent(BaseEvent):
    """Event emitted when a request fails."""

    event_type: str = "request.failed"
    endpoint: str = ""
    model: Optional[str] = None
    duration_ms: float = 0.0
    error_type: str = ""
    error_message: str = ""
    status_code: int = 500


@dataclass
class RequestQueuedEvent(BaseEvent):
    """Event emitted when a request is added to a queue."""

    event_type: str = "request.queued"
    queue_name: str = ""
    queue_depth: int = 0


@dataclass
class RequestDequeuedEvent(BaseEvent):
    """Event emitted when a request is removed from a queue."""

    event_type: str = "request.dequeued"
    queue_name: str = ""
    wait_time_ms: float = 0.0


@dataclass
class RequestRoutedEvent(BaseEvent):
    """Event emitted when a request is routed to a worker."""

    event_type: str = "request.routed"
    worker_id: str = ""
    routing_cost_ms: float = 0.0


# ============================================================================
# Token Events
# ============================================================================


@dataclass
class TokensGeneratedEvent(BaseEvent):
    """Event emitted when tokens are generated for a request."""

    event_type: str = "tokens.generated"
    endpoint: str = ""
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0


@dataclass
class TokenBatchGeneratedEvent(BaseEvent):
    """Event emitted when a batch of tokens is generated."""

    event_type: str = "tokens.batch_generated"
    batch_size: int = 0
    tokens: list[str] = field(default_factory=list)


@dataclass
class StreamingTokenGeneratedEvent(BaseEvent):
    """Event emitted for each token in a streaming response."""

    event_type: str = "stream.token_generated"
    stream_id: str = ""
    token: str = ""
    sequence_number: int = 0
    timestamp_ns: int = 0
    chunk_size_bytes: Optional[int] = None


@dataclass
class FirstTokenGeneratedEvent(BaseEvent):
    """Event emitted when the first token is generated in a stream."""

    event_type: str = "stream.first_token"
    stream_id: str = ""
    ttft_ms: float = 0.0


# ============================================================================
# Stream Lifecycle Events
# ============================================================================


@dataclass
class StreamStartedEvent(BaseEvent):
    """Event emitted when a streaming response starts."""

    event_type: str = "stream.started"
    stream_id: str = ""
    endpoint: str = ""
    model: str = ""
    input_tokens: int = 0
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    client_id: Optional[str] = None


@dataclass
class StreamProgressEvent(BaseEvent):
    """Event emitted periodically during streaming to report progress."""

    event_type: str = "stream.progress"
    stream_id: str = ""
    tokens_generated: int = 0
    elapsed_ms: float = 0.0


@dataclass
class StreamCompletedEvent(BaseEvent):
    """Event emitted when a stream completes successfully."""

    event_type: str = "stream.completed"
    stream_id: str = ""
    endpoint: str = ""
    duration_ms: float = 0.0
    token_count: int = 0
    finish_reason: str = "stop"
    client_id: Optional[str] = None


@dataclass
class StreamFailedEvent(BaseEvent):
    """Event emitted when a stream fails."""

    event_type: str = "stream.failed"
    stream_id: str = ""
    endpoint: str = ""
    duration_ms: float = 0.0
    error_message: str = ""
    token_count: int = 0
    client_id: Optional[str] = None


@dataclass
class StreamCancelledEvent(BaseEvent):
    """Event emitted when a stream is cancelled."""

    event_type: str = "stream.cancelled"
    stream_id: str = ""
    cancellation_point: str = ""
    reason: str = ""


# ============================================================================
# Latency & Performance Events
# ============================================================================


@dataclass
class PrefillStartedEvent(BaseEvent):
    """Event emitted when KV cache prefill phase starts."""

    event_type: str = "prefill.started"
    input_tokens: int = 0


@dataclass
class PrefillCompletedEvent(BaseEvent):
    """Event emitted when KV cache prefill phase completes."""

    event_type: str = "prefill.completed"
    prefill_time_ms: float = 0.0


@dataclass
class DecodeStartedEvent(BaseEvent):
    """Event emitted when decode phase starts."""

    event_type: str = "decode.started"


@dataclass
class DecodeCompletedEvent(BaseEvent):
    """Event emitted when decode phase completes."""

    event_type: str = "decode.completed"
    decode_time_ms: float = 0.0
    output_tokens: int = 0


@dataclass
class LatencyMeasuredEvent(BaseEvent):
    """Event emitted when a latency measurement is recorded."""

    event_type: str = "latency.measured"
    endpoint: str = ""
    latency_type: str = ""  # "ttft", "tpot", "total", etc.
    value_ms: float = 0.0


@dataclass
class ThroughputMeasuredEvent(BaseEvent):
    """Event emitted when throughput is measured."""

    event_type: str = "throughput.measured"
    endpoint: str = ""
    model: str = ""
    rps: float = 0.0  # Requests per second
    tps: float = 0.0  # Tokens per second
    window_seconds: int = 60


@dataclass
class QueueDepthChangedEvent(BaseEvent):
    """Event emitted when queue depth changes significantly."""

    event_type: str = "queue.depth_changed"
    queue_name: str = ""
    depth: int = 0
    max_depth: int = 0


@dataclass
class BatchSizeChangedEvent(BaseEvent):
    """Event emitted when batch size changes."""

    event_type: str = "batch.size_changed"
    batch_size: int = 0
    avg_batch_size: float = 0.0


# ============================================================================
# Cache Events
# ============================================================================


@dataclass
class CacheLookupEvent(BaseEvent):
    """Event emitted when a cache lookup occurs."""

    event_type: str = "cache.lookup"
    cache_type: str = ""  # "kv", "prompt", etc.
    total_tokens: int = 0
    matched_tokens: int = 0
    hit_ratio: float = 0.0


@dataclass
class CacheHitEvent(BaseEvent):
    """Event emitted on a cache hit."""

    event_type: str = "cache.hit"
    cache_type: str = ""
    cached_tokens: int = 0
    speedup_ms: float = 0.0


@dataclass
class CacheMissEvent(BaseEvent):
    """Event emitted on a cache miss."""

    event_type: str = "cache.miss"
    cache_type: str = ""


@dataclass
class CacheSpeedupMeasuredEvent(BaseEvent):
    """Event emitted when cache speedup is measured."""

    event_type: str = "cache.speedup_measured"
    baseline_ttft_ms: float = 0.0
    actual_ttft_ms: float = 0.0
    cache_hit_ratio: float = 0.0


@dataclass
class CacheEvictionEvent(BaseEvent):
    """Event emitted when cache entries are evicted."""

    event_type: str = "cache.eviction"
    cache_type: str = ""
    evicted_entries: int = 0
    reason: str = ""


# ============================================================================
# Model & Resource Events
# ============================================================================


@dataclass
class ModelSelectedEvent(BaseEvent):
    """Event emitted when a model is selected for a request."""

    event_type: str = "model.selected"
    model_id: str = ""
    context_window: int = 0


@dataclass
class WorkerAssignedEvent(BaseEvent):
    """Event emitted when a worker is assigned to a request."""

    event_type: str = "worker.assigned"
    worker_id: str = ""
    worker_load: float = 0.0
    routing_cost_ms: float = 0.0


@dataclass
class WorkerCompletedEvent(BaseEvent):
    """Event emitted when a worker completes a request."""

    event_type: str = "worker.completed"
    worker_id: str = ""
    duration_ms: float = 0.0
    success: bool = True


@dataclass
class ResourceUtilizationEvent(BaseEvent):
    """Event emitted for resource utilization metrics."""

    event_type: str = "resource.utilization"
    resource_type: str = ""  # "cpu", "memory", "gpu", etc.
    resource_id: str = ""
    utilization_percent: float = 0.0


@dataclass
class GPUMetricsEvent(BaseEvent):
    """Event emitted for GPU metrics."""

    event_type: str = "gpu.metrics"
    gpu_id: str = ""
    utilization: float = 0.0
    memory_used: int = 0
    memory_total: int = 0
    power_watts: float = 0.0
    temperature: float = 0.0


# ============================================================================
# Error & Recovery Events
# ============================================================================


@dataclass
class ErrorOccurredEvent(BaseEvent):
    """Event emitted when an error occurs."""

    event_type: str = "error.occurred"
    endpoint: str = ""
    model: Optional[str] = None
    error_type: str = ""
    error_message: str = ""
    stack_trace: Optional[str] = None


@dataclass
class ErrorPatternDetectedEvent(BaseEvent):
    """Event emitted when an error pattern is detected."""

    event_type: str = "error.pattern_detected"
    error_signature: str = ""
    error_type: str = ""
    count: int = 0
    affected_endpoints: list[str] = field(default_factory=list)


@dataclass
class RecoveryAttemptedEvent(BaseEvent):
    """Event emitted when error recovery is attempted."""

    event_type: str = "recovery.attempted"
    retry_count: int = 0


@dataclass
class RecoverySucceededEvent(BaseEvent):
    """Event emitted when recovery succeeds."""

    event_type: str = "recovery.succeeded"
    time_to_recovery_ms: float = 0.0


@dataclass
class SLOViolationEvent(BaseEvent):
    """Event emitted when an SLO is violated."""

    event_type: str = "slo.violation"
    endpoint: str = ""
    slo_type: str = ""  # "latency", "error_rate", etc.
    threshold_value: float = 0.0
    actual_value: float = 0.0
    severity: str = "warning"  # "warning", "critical"


# ============================================================================
# Network & Client Events
# ============================================================================


@dataclass
class ChunkSentEvent(BaseEvent):
    """Event emitted when a chunk is sent to a client."""

    event_type: str = "network.chunk_sent"
    stream_id: str = ""
    chunk_size_bytes: int = 0


@dataclass
class BackpressureDetectedEvent(BaseEvent):
    """Event emitted when network backpressure is detected."""

    event_type: str = "network.backpressure"
    stream_id: str = ""
    buffer_size: int = 0


@dataclass
class ClientDisconnectedEvent(BaseEvent):
    """Event emitted when a client disconnects."""

    event_type: str = "client.disconnected"
    stream_id: str = ""
    reason: str = ""
    tokens_sent: int = 0


@dataclass
class NetworkLatencyMeasuredEvent(BaseEvent):
    """Event emitted when network latency is measured."""

    event_type: str = "network.latency_measured"
    latency_ms: float = 0.0


# ============================================================================
# Usage & Billing Events
# ============================================================================


@dataclass
class UsageRecordedEvent(BaseEvent):
    """Event emitted when usage is recorded for billing."""

    event_type: str = "usage.recorded"
    user_id: str = ""
    project_id: Optional[str] = None
    model: str = ""
    endpoint: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class QuotaUpdatedEvent(BaseEvent):
    """Event emitted when a quota is updated."""

    event_type: str = "quota.updated"
    user_id: str = ""
    quota_type: str = ""
    used: float = 0.0
    limit: float = 0.0


@dataclass
class RateLimitHitEvent(BaseEvent):
    """Event emitted when a rate limit is hit."""

    event_type: str = "ratelimit.hit"
    user_id: str = ""
    endpoint: str = ""
    limit_type: str = ""  # "requests", "tokens"
    current_value: int = 0
    limit_value: int = 0
    retry_after_seconds: int = 0


@dataclass
class CostCalculatedEvent(BaseEvent):
    """Event emitted when cost is calculated."""

    event_type: str = "cost.calculated"
    model: str = ""
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0
