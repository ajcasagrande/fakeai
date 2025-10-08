"""Subscriber implementations for existing metrics trackers."""

import logging
from typing import TYPE_CHECKING, cast

from .base import BaseEvent
from .event_types import (
    BatchSizeChangedEvent,
    CacheLookupEvent,
    CacheSpeedupMeasuredEvent,
    CostCalculatedEvent,
    DecodeStartedEvent,
    ErrorOccurredEvent,
    FirstTokenGeneratedEvent,
    ModelSelectedEvent,
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

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from ..cost_tracker import CostTracker
    from ..dynamo_metrics import DynamoMetricsCollector
    from ..kv_cache import KVCacheMetrics
    from ..metrics import MetricsTracker
    from ..model_metrics import ModelMetricsTracker

logger = logging.getLogger(__name__)


class MetricsTrackerSubscriber:
    """
    Subscriber that updates the existing MetricsTracker.

    Handles: requests, responses, tokens, errors, latency
    """

    def __init__(self, metrics_tracker: "MetricsTracker"):
        self.tracker = metrics_tracker

    async def on_request_started(self, event: BaseEvent) -> None:
        """Handle request started event."""
        evt = cast(RequestStartedEvent, event)
        self.tracker.track_request(evt.endpoint)

    async def on_request_completed(self, event: BaseEvent) -> None:
        """Handle request completed event."""
        evt = cast(RequestCompletedEvent, event)
        # Track response with latency
        self.tracker.track_response(evt.endpoint, evt.duration_ms / 1000)

        # Track tokens if any were generated
        total_tokens = evt.input_tokens + evt.output_tokens
        if total_tokens > 0:
            self.tracker.track_tokens(evt.endpoint, total_tokens)

    async def on_request_failed(self, event: BaseEvent) -> None:
        """Handle request failed event."""
        evt = cast(RequestFailedEvent, event)
        self.tracker.track_error(evt.endpoint)


class StreamingMetricsSubscriber:
    """
    Subscriber for detailed streaming metrics.

    Handles: stream lifecycle, token timings, quality metrics
    """

    def __init__(self, streaming_tracker):
        self.tracker = streaming_tracker

    async def on_stream_started(self, event: BaseEvent) -> None:
        """Handle stream started event."""
        evt = cast(StreamStartedEvent, event)
        self.tracker.start_stream(
            stream_id=evt.stream_id,
            model=evt.model,
            prompt_tokens=evt.input_tokens,
            temperature=evt.temperature,
            max_tokens=evt.max_tokens,
        )

    async def on_first_token(self, event: BaseEvent) -> None:
        """Handle first token generated event."""
        evt = cast(FirstTokenGeneratedEvent, event)
        self.tracker.record_first_token_time(evt.stream_id, evt.ttft_ms)

    async def on_stream_token(self, event: BaseEvent) -> None:
        """Handle stream token generated event."""
        evt = cast(StreamingTokenGeneratedEvent, event)
        self.tracker.record_token(
            stream_id=evt.stream_id,
            token=evt.token,
            chunk_size_bytes=evt.chunk_size_bytes or 0,
        )

    async def on_stream_completed(self, event: BaseEvent) -> None:
        """Handle stream completed event."""
        evt = cast(StreamCompletedEvent, event)
        self.tracker.complete_stream(
            stream_id=evt.stream_id, finish_reason=evt.finish_reason
        )

    async def on_stream_failed(self, event: BaseEvent) -> None:
        """Handle stream failed event."""
        evt = cast(StreamFailedEvent, event)
        self.tracker.fail_stream(evt.stream_id, evt.error_message)


class CostTrackerSubscriber:
    """
    Subscriber for cost tracking and budget management.

    Handles: cost accrual, budget thresholds
    """

    def __init__(self, cost_tracker: "CostTracker"):
        self.tracker = cost_tracker

    async def on_request_completed(self, event: BaseEvent) -> None:
        """Handle request completed event and track usage."""
        evt = cast(RequestCompletedEvent, event)
        # Extract API key from metadata
        api_key = evt.metadata.get("api_key", "default")
        user_id = evt.metadata.get("user_id")

        # Record usage (CostTracker uses record_usage, not track_usage)
        self.tracker.record_usage(
            api_key=api_key,
            model=evt.model,
            endpoint=evt.endpoint,
            prompt_tokens=evt.input_tokens,
            completion_tokens=evt.output_tokens,
            cached_tokens=evt.cached_tokens,
            metadata={"user_id": user_id} if user_id else {},
        )

    async def on_cost_calculated(self, event: BaseEvent) -> None:
        """Handle cost calculated event."""
        evt = cast(CostCalculatedEvent, event)
        # This can be used for additional cost-related tracking
        logger.debug(
            f"Cost calculated for model {evt.model}: ${evt.total_cost:.4f}"
        )


class ModelMetricsSubscriber:
    """
    Subscriber for per-model statistics.

    Handles: model requests, latency, token usage
    """

    def __init__(self, model_tracker: "ModelMetricsTracker"):
        self.tracker = model_tracker

    async def on_model_selected(self, event: BaseEvent) -> None:
        """Handle model selected event."""
        evt = cast(ModelSelectedEvent, event)
        # Can track model selection patterns if needed
        logger.debug(f"Model selected: {evt.model_id}")

    async def on_request_completed(self, event: BaseEvent) -> None:
        """Handle request completed and track model-specific metrics."""
        evt = cast(RequestCompletedEvent, event)
        # Extract user from metadata
        user = evt.metadata.get("user_id")
        error = None

        self.tracker.track_request(
            model=evt.model,
            endpoint=evt.endpoint,
            prompt_tokens=evt.input_tokens,
            completion_tokens=evt.output_tokens,
            latency_ms=evt.duration_ms,
            user=user,
            error=error,
        )


class DynamoMetricsSubscriber:
    """
    Subscriber for AI-Dynamo style inference metrics.

    Handles: request lifecycle, latency breakdown, throughput
    """

    def __init__(self, dynamo_collector: "DynamoMetricsCollector"):
        self.collector = dynamo_collector

    async def on_request_started(self, event: BaseEvent) -> None:
        """Handle request started event."""
        evt = cast(RequestStartedEvent, event)
        if not evt.request_id:
            return

        self.collector.start_request(
            request_id=evt.request_id,
            model=evt.model or "unknown",
            endpoint=evt.endpoint,
            input_tokens=evt.input_tokens or 0,
        )

    async def on_prefill_started(self, event: BaseEvent) -> None:
        """Handle prefill started event."""
        evt = cast(PrefillStartedEvent, event)
        if not evt.request_id:
            return

        self.collector.record_prefill_start(evt.request_id)

    async def on_prefill_completed(self, event: BaseEvent) -> None:
        """Handle prefill completed event."""
        # Dynamo collector tracks this internally via timing

    async def on_first_token(self, event: BaseEvent) -> None:
        """Handle first token generated event."""
        evt = cast(FirstTokenGeneratedEvent, event)
        # Extract request_id from stream_id or event metadata
        request_id = evt.request_id or evt.stream_id

        if request_id:
            self.collector.record_first_token(request_id)

    async def on_decode_started(self, event: BaseEvent) -> None:
        """Handle decode started event."""
        evt = cast(DecodeStartedEvent, event)
        if not evt.request_id:
            return

        self.collector.record_decode_start(evt.request_id)

    async def on_request_completed(self, event: BaseEvent) -> None:
        """Handle request completed event."""
        evt = cast(RequestCompletedEvent, event)
        if not evt.request_id:
            return

        # Extract worker_id from metadata if available
        worker_id = evt.metadata.get("worker_id", "default")
        kv_cache_hit = evt.metadata.get("kv_cache_hit", False)

        self.collector.complete_request(
            request_id=evt.request_id,
            output_tokens=evt.output_tokens,
            cached_tokens=evt.cached_tokens,
            kv_cache_hit=kv_cache_hit,
            worker_id=worker_id,
            success=True,
            finish_reason=evt.finish_reason,
        )

    async def on_queue_depth_changed(self, event: BaseEvent) -> None:
        """Handle queue depth changed event."""
        evt = cast(QueueDepthChangedEvent, event)
        self.collector.record_queue_depth(evt.depth)

    async def on_batch_size_changed(self, event: BaseEvent) -> None:
        """Handle batch size changed event."""
        evt = cast(BatchSizeChangedEvent, event)
        self.collector.record_batch_size(evt.batch_size)


class ErrorMetricsSubscriber:
    """
    Subscriber for comprehensive error tracking.

    Handles: error occurrence, classification, pattern detection
    """

    def __init__(self, error_tracker):
        self.tracker = error_tracker

    async def on_error_occurred(self, event: BaseEvent) -> None:
        """Handle error occurred event."""
        evt = cast(ErrorOccurredEvent, event)
        api_key = evt.metadata.get("api_key")

        self.tracker.record_error(
            endpoint=evt.endpoint,
            status_code=500,
            error_type=evt.error_type,
            error_message=evt.error_message,
            model=evt.model,
            api_key=api_key,
            request_id=evt.request_id,
        )

    async def on_request_failed(self, event: BaseEvent) -> None:
        """Handle request failed event."""
        evt = cast(RequestFailedEvent, event)
        api_key = evt.metadata.get("api_key")

        self.tracker.record_error(
            endpoint=evt.endpoint,
            status_code=evt.status_code,
            error_type=evt.error_type,
            error_message=evt.error_message,
            model=evt.model,
            api_key=api_key,
            request_id=evt.request_id,
        )

    async def on_request_completed(self, event: BaseEvent) -> None:
        """Handle successful request completion."""
        evt = cast(RequestCompletedEvent, event)
        # Extract api_key from metadata
        api_key = evt.metadata.get("api_key")
        self.tracker.record_success(endpoint=evt.endpoint, api_key=api_key)


class KVCacheMetricsSubscriber:
    """
    Subscriber for KV cache metrics.

    Handles: cache lookups, hits/misses, speedup measurements
    """

    def __init__(self, kv_cache_metrics: "KVCacheMetrics"):
        self.metrics = kv_cache_metrics

    async def on_cache_lookup(self, event: BaseEvent) -> None:
        """Handle cache lookup event."""
        evt = cast(CacheLookupEvent, event)
        # Extract endpoint from metadata
        endpoint = evt.metadata.get("endpoint", "unknown")

        self.metrics.record_cache_lookup(
            endpoint=endpoint,
            total_tokens=evt.total_tokens,
            matched_tokens=evt.matched_tokens,
        )

    async def on_speedup_measured(self, event: BaseEvent) -> None:
        """Handle cache speedup measured event."""
        evt = cast(CacheSpeedupMeasuredEvent, event)
        # Extract endpoint from metadata
        endpoint = evt.metadata.get("endpoint", "unknown")

        self.metrics.record_speedup(
            endpoint=endpoint,
            baseline_ttft=evt.baseline_ttft_ms,
            actual_ttft=evt.actual_ttft_ms,
            cache_hit_ratio=evt.cache_hit_ratio,
        )
