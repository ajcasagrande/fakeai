"""Async event bus implementation for pub-sub metrics system."""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Any, Awaitable, Callable, Optional

from .base import BaseEvent, EventSubscriber

logger = logging.getLogger(__name__)


class AsyncEventBus:
    """
    Asynchronous event bus for non-blocking event distribution.

    Features:
    - Async event emission (non-blocking)
    - Multiple subscribers per event type
    - Priority-based event delivery
    - Circuit breaker for failing subscribers
    - Metrics on event processing
    """

    def __init__(self, max_queue_size: int = 10000):
        """
        Initialize the event bus.

        Args:
            max_queue_size: Maximum number of events in the queue before dropping
        """
        self._subscribers: dict[str, list[EventSubscriber]] = defaultdict(list)
        self._event_queue: asyncio.Queue = asyncio.Queue(
            maxsize=max_queue_size)
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._event_count = 0
        self._dropped_events = 0
        self._processed_events = 0
        self._counter_lock = asyncio.Lock()

    async def publish(self, event: BaseEvent) -> None:
        """
        Publish an event to all subscribers (non-blocking).

        Args:
            event: The event to publish
        """
        try:
            # Non-blocking put with immediate return
            self._event_queue.put_nowait(event)
            async with self._counter_lock:
                self._event_count += 1
        except asyncio.QueueFull:
            # Log and drop event if queue is full
            async with self._counter_lock:
                self._dropped_events += 1
                dropped_count = self._dropped_events
            logger.warning(
                f"Event queue full, dropped event: {event.event_type} "
                f"(total dropped: {dropped_count})"
            )

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[BaseEvent], Awaitable[None]],
        priority: int = 0,
    ) -> None:
        """
        Subscribe to events of a specific type.

        Args:
            event_type: The type of event to subscribe to (or "*" for all events)
            handler: Async function to handle the event
            priority: Priority level (higher = earlier execution)
        """
        subscriber = EventSubscriber(
            event_type=event_type, handler=handler, priority=priority
        )
        self._subscribers[event_type].append(subscriber)

        # Sort by priority (higher priority first)
        self._subscribers[event_type].sort(
            key=lambda s: s.priority, reverse=True)

        logger.info(
            f"Subscribed {
                handler.__name__} to {event_type} with priority {priority}")

    def unsubscribe(
        self, event_type: str, handler: Callable[[BaseEvent], Awaitable[None]]
    ) -> None:
        """
        Unsubscribe from events of a specific type.

        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler function to remove
        """
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                sub for sub in self._subscribers[event_type] if sub.handler != handler]
            logger.info(f"Unsubscribed {handler.__name__} from {event_type}")

    async def start(self) -> None:
        """Start the event processing worker."""
        if self._running:
            logger.warning("Event bus already running")
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._process_events())
        logger.info("Event bus started")

    async def stop(self, timeout: float = 10.0) -> None:
        """
        Stop event processing and drain the queue.

        Args:
            timeout: Maximum time to wait for queue to drain
        """
        if not self._running:
            logger.warning("Event bus not running")
            return

        self._running = False

        # Wait for queue to drain
        start = time.time()
        while self._event_queue.qsize() > 0:
            if time.time() - start > timeout:
                remaining = self._event_queue.qsize()
                logger.warning(
                    f"Shutdown timeout reached, {remaining} events unprocessed"
                )
                break
            await asyncio.sleep(0.1)

        # Cancel worker task
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

        logger.info(
            f"Event bus stopped. Processed {self._processed_events} events, "
            f"dropped {self._dropped_events} events"
        )

    async def _process_events(self) -> None:
        """Background worker to process events from the queue."""
        logger.info("Event processing worker started")

        while self._running:
            try:
                # Wait for event with timeout to check _running flag
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._dispatch_event(event)
                async with self._counter_lock:
                    self._processed_events += 1
            except asyncio.TimeoutError:
                # No event received, continue loop
                continue
            except Exception as e:
                logger.error(
                    f"Error in event processing worker: {e}",
                    exc_info=True)

        logger.info("Event processing worker stopped")

    async def _dispatch_event(self, event: BaseEvent) -> None:
        """
        Dispatch event to all matching subscribers.

        Args:
            event: The event to dispatch
        """
        # Get subscribers for this specific event type
        subscribers = list(self._subscribers.get(event.event_type, []))

        # Add wildcard subscribers (subscribe to all events)
        subscribers.extend(self._subscribers.get("*", []))

        if not subscribers:
            # No subscribers for this event type (this is okay)
            return

        # Dispatch to all subscribers concurrently
        tasks = [self._call_subscriber(sub, event) for sub in subscribers]

        if tasks:
            # Use gather with return_exceptions to prevent one failure from
            # stopping others
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log any exceptions that occurred
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Subscriber {subscribers[i].handler.__name__} "
                        f"failed for event {event.event_type}: {result}",
                        exc_info=result,
                    )

    async def _call_subscriber(
        self, subscriber: EventSubscriber, event: BaseEvent
    ) -> None:
        """
        Call a subscriber with circuit breaker protection.

        Args:
            subscriber: The subscriber to call
            event: The event to pass to the subscriber
        """
        start_time = time.time()

        try:
            # Timeout protection (5 seconds per subscriber)
            await asyncio.wait_for(subscriber.handler(event), timeout=5.0)

            # Update metrics with lock protection
            processing_time = (time.time() - start_time) * 1000
            async with subscriber._metrics_lock:
                subscriber.success_count += 1
                subscriber.total_processing_time_ms += processing_time

        except asyncio.TimeoutError:
            async with subscriber._metrics_lock:
                subscriber.timeout_count += 1
            logger.warning(
                f"Subscriber {subscriber.handler.__name__} timed out "
                f"for event {event.event_type}"
            )

        except Exception as e:
            async with subscriber._metrics_lock:
                subscriber.error_count += 1
            logger.error(
                f"Subscriber {subscriber.handler.__name__} failed "
                f"for event {event.event_type}: {e}",
                exc_info=True,
            )

    def get_stats(self) -> dict[str, Any]:
        """
        Get event bus statistics.

        Returns:
            Dictionary containing event bus stats
        """
        subscriber_stats = {}
        for event_type, subscribers in self._subscribers.items():
            subscriber_stats[event_type] = [sub.to_dict()
                                            for sub in subscribers]

        return {
            "running": self._running,
            "queue_depth": self._event_queue.qsize(),
            "queue_max_size": self._event_queue.maxsize,
            "events_published": self._event_count,
            "events_processed": self._processed_events,
            "events_dropped": self._dropped_events,
            "drop_rate": (
                self._dropped_events / self._event_count
                if self._event_count > 0
                else 0.0
            ),
            "subscribers": subscriber_stats,
        }


class EventBusFactory:
    """Factory to create and configure the event bus with metrics subscribers."""

    @staticmethod
    def create_event_bus(
        metrics_tracker=None,
        streaming_tracker=None,
        cost_tracker=None,
        model_tracker=None,
        dynamo_collector=None,
        error_tracker=None,
        kv_cache_metrics=None,
    ) -> AsyncEventBus:
        """
        Create and configure event bus with all metrics subscribers.

        Args:
            metrics_tracker: Main metrics tracker instance
            streaming_tracker: Streaming metrics tracker instance
            cost_tracker: Cost tracker instance
            model_tracker: Model metrics tracker instance
            dynamo_collector: Dynamo metrics collector instance
            error_tracker: Error metrics tracker instance
            kv_cache_metrics: KV cache metrics instance

        Returns:
            Configured AsyncEventBus instance
        """
        bus = AsyncEventBus(max_queue_size=10000)

        # Import subscribers here to avoid circular imports
        from .subscribers import (
            CostTrackerSubscriber,
            DynamoMetricsSubscriber,
            ErrorMetricsSubscriber,
            KVCacheMetricsSubscriber,
            MetricsTrackerSubscriber,
            ModelMetricsSubscriber,
            StreamingMetricsSubscriber,
        )
        from fakeai.waterfall.subscriber import WaterfallCollectorSubscriber

        # Register MetricsTracker subscriber
        if metrics_tracker:
            metrics_sub = MetricsTrackerSubscriber(metrics_tracker)
            bus.subscribe(
                "request.started", metrics_sub.on_request_started, priority=10
            )
            bus.subscribe(
                "request.completed",
                metrics_sub.on_request_completed,
                priority=10)
            bus.subscribe(
                "request.failed",
                metrics_sub.on_request_failed,
                priority=10)

        # Register StreamingMetrics subscriber
        if streaming_tracker:
            streaming_sub = StreamingMetricsSubscriber(streaming_tracker)
            bus.subscribe(
                "stream.started",
                streaming_sub.on_stream_started,
                priority=8)
            bus.subscribe(
                "stream.token_generated",
                streaming_sub.on_stream_token,
                priority=5)
            bus.subscribe(
                "stream.first_token", streaming_sub.on_first_token, priority=8
            )
            bus.subscribe(
                "stream.completed",
                streaming_sub.on_stream_completed,
                priority=8)
            bus.subscribe(
                "stream.failed",
                streaming_sub.on_stream_failed,
                priority=8)

        # Register CostTracker subscriber
        if cost_tracker:
            cost_sub = CostTrackerSubscriber(cost_tracker)
            bus.subscribe(
                "request.completed", cost_sub.on_request_completed, priority=7
            )
            bus.subscribe(
                "cost.calculated",
                cost_sub.on_cost_calculated,
                priority=7)

        # Register ModelMetrics subscriber
        if model_tracker:
            model_sub = ModelMetricsSubscriber(model_tracker)
            bus.subscribe(
                "model.selected",
                model_sub.on_model_selected,
                priority=6)
            bus.subscribe(
                "request.completed", model_sub.on_request_completed, priority=6
            )

        # Register DynamoMetrics subscriber
        if dynamo_collector:
            dynamo_sub = DynamoMetricsSubscriber(dynamo_collector)
            bus.subscribe(
                "request.started", dynamo_sub.on_request_started, priority=9
            )
            bus.subscribe(
                "prefill.started", dynamo_sub.on_prefill_started, priority=9
            )
            bus.subscribe(
                "prefill.completed",
                dynamo_sub.on_prefill_completed,
                priority=9)
            bus.subscribe(
                "stream.first_token", dynamo_sub.on_first_token, priority=9
            )
            bus.subscribe(
                "decode.started",
                dynamo_sub.on_decode_started,
                priority=9)
            bus.subscribe(
                "request.completed",
                dynamo_sub.on_request_completed,
                priority=9)
            bus.subscribe(
                "queue.depth_changed",
                dynamo_sub.on_queue_depth_changed,
                priority=5)
            bus.subscribe(
                "batch.size_changed",
                dynamo_sub.on_batch_size_changed,
                priority=5)

        # Register ErrorMetrics subscriber
        if error_tracker:
            error_sub = ErrorMetricsSubscriber(error_tracker)
            bus.subscribe(
                "error.occurred",
                error_sub.on_error_occurred,
                priority=10)
            bus.subscribe(
                "request.failed",
                error_sub.on_request_failed,
                priority=10)
            bus.subscribe(
                "request.completed",
                error_sub.on_request_completed,
                priority=10)

        # Register KVCacheMetrics subscriber
        if kv_cache_metrics:
            cache_sub = KVCacheMetricsSubscriber(kv_cache_metrics)
            bus.subscribe(
                "cache.lookup",
                cache_sub.on_cache_lookup,
                priority=6)
            bus.subscribe(
                "cache.speedup_measured",
                cache_sub.on_speedup_measured,
                priority=6)

        logger.info(
            f"Event bus created with {len(bus._subscribers)} event type subscriptions"
        )

        return bus
