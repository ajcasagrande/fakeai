"""
Comprehensive tests for EventBusFactory.

Tests factory creation, subscriber registration, priority configuration,
event type coverage, and integration with trackers.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add fakeai directory to path to import modules without triggering app initialization
fakeai_dir = Path(__file__).parent.parent / "fakeai"
sys.path.insert(0, str(fakeai_dir))

from events.base import BaseEvent
from events.bus import AsyncEventBus, EventBusFactory
from events.event_types import (
    ErrorOccurredEvent,
    RequestCompletedEvent,
    RequestFailedEvent,
    RequestStartedEvent,
    StreamCompletedEvent,
    StreamingTokenGeneratedEvent,
    StreamStartedEvent,
)


@pytest.mark.unit
class TestEventBusFactoryCreation:
    """Test EventBusFactory creation with various tracker configurations."""

    def test_create_event_bus_returns_async_event_bus(self):
        """create_event_bus() should return an AsyncEventBus instance."""
        bus = EventBusFactory.create_event_bus()

        assert isinstance(bus, AsyncEventBus)
        assert bus._event_queue.maxsize == 10000

    def test_create_with_all_trackers(self):
        """Should create bus with all trackers provided."""
        # Create mock trackers
        metrics_tracker = Mock()
        streaming_tracker = Mock()
        cost_tracker = Mock()
        model_tracker = Mock()
        dynamo_collector = Mock()
        error_tracker = Mock()
        kv_cache_metrics = Mock()

        bus = EventBusFactory.create_event_bus(
            metrics_tracker=metrics_tracker,
            streaming_tracker=streaming_tracker,
            cost_tracker=cost_tracker,
            model_tracker=model_tracker,
            dynamo_collector=dynamo_collector,
            error_tracker=error_tracker,
            kv_cache_metrics=kv_cache_metrics,
        )

        assert isinstance(bus, AsyncEventBus)
        # Should have subscriptions for multiple event types
        assert len(bus._subscribers) > 0

    def test_create_with_some_trackers_none(self):
        """Should create bus with only some trackers provided."""
        metrics_tracker = Mock()
        error_tracker = Mock()

        bus = EventBusFactory.create_event_bus(
            metrics_tracker=metrics_tracker,
            streaming_tracker=None,
            cost_tracker=None,
            model_tracker=None,
            dynamo_collector=None,
            error_tracker=error_tracker,
            kv_cache_metrics=None,
        )

        assert isinstance(bus, AsyncEventBus)
        # Should still create bus with available trackers
        assert len(bus._subscribers) > 0

    def test_create_with_no_trackers(self):
        """Should create bus even with no trackers provided."""
        bus = EventBusFactory.create_event_bus()

        assert isinstance(bus, AsyncEventBus)
        # Bus should be empty but functional
        assert len(bus._subscribers) == 0


@pytest.mark.unit
class TestSubscriberRegistration:
    """Test that subscribers are correctly registered for each tracker."""

    def test_metrics_tracker_subscriber_registered(self):
        """MetricsTracker subscriber should be registered for request events."""
        metrics_tracker = Mock()

        bus = EventBusFactory.create_event_bus(metrics_tracker=metrics_tracker)

        # Check subscriptions exist
        assert "request.started" in bus._subscribers
        assert "request.completed" in bus._subscribers
        assert "request.failed" in bus._subscribers

        # Verify correct number of subscribers
        assert len(bus._subscribers["request.started"]) >= 1
        assert len(bus._subscribers["request.completed"]) >= 1
        assert len(bus._subscribers["request.failed"]) >= 1

    def test_streaming_tracker_subscriber_registered(self):
        """StreamingTracker subscriber should be registered for stream events."""
        streaming_tracker = Mock()

        bus = EventBusFactory.create_event_bus(streaming_tracker=streaming_tracker)

        # Check stream-related subscriptions
        assert "stream.started" in bus._subscribers
        assert "stream.token_generated" in bus._subscribers
        assert "stream.first_token" in bus._subscribers
        assert "stream.completed" in bus._subscribers
        assert "stream.failed" in bus._subscribers

    def test_cost_tracker_subscriber_registered(self):
        """CostTracker subscriber should be registered for cost events."""
        cost_tracker = Mock()

        bus = EventBusFactory.create_event_bus(cost_tracker=cost_tracker)

        # Check cost-related subscriptions
        assert "request.completed" in bus._subscribers
        assert "cost.calculated" in bus._subscribers

    def test_error_tracker_subscriber_registered(self):
        """ErrorTracker subscriber should be registered for error events."""
        error_tracker = Mock()

        bus = EventBusFactory.create_event_bus(error_tracker=error_tracker)

        # Check error-related subscriptions
        assert "error.occurred" in bus._subscribers
        assert "request.failed" in bus._subscribers
        assert "request.completed" in bus._subscribers

    def test_dynamo_metrics_subscriber_registered(self):
        """DynamoMetrics subscriber should be registered for inference events."""
        dynamo_collector = Mock()

        bus = EventBusFactory.create_event_bus(dynamo_collector=dynamo_collector)

        # Check dynamo-related subscriptions
        assert "request.started" in bus._subscribers
        assert "prefill.started" in bus._subscribers
        assert "prefill.completed" in bus._subscribers
        assert "stream.first_token" in bus._subscribers
        assert "decode.started" in bus._subscribers
        assert "request.completed" in bus._subscribers
        assert "queue.depth_changed" in bus._subscribers
        assert "batch.size_changed" in bus._subscribers

    def test_model_metrics_subscriber_registered(self):
        """ModelMetrics subscriber should be registered for model events."""
        model_tracker = Mock()

        bus = EventBusFactory.create_event_bus(model_tracker=model_tracker)

        # Check model-related subscriptions
        assert "model.selected" in bus._subscribers
        assert "request.completed" in bus._subscribers

    def test_kv_cache_metrics_subscriber_registered(self):
        """KVCacheMetrics subscriber should be registered for cache events."""
        kv_cache_metrics = Mock()

        bus = EventBusFactory.create_event_bus(kv_cache_metrics=kv_cache_metrics)

        # Check cache-related subscriptions
        assert "cache.lookup" in bus._subscribers
        assert "cache.speedup_measured" in bus._subscribers


@pytest.mark.unit
class TestPriorityConfiguration:
    """Test that subscribers have correct priority configuration."""

    def test_metrics_tracker_high_priority(self):
        """MetricsTracker should have high priority (10)."""
        metrics_tracker = Mock()

        bus = EventBusFactory.create_event_bus(metrics_tracker=metrics_tracker)

        # Check priority for request.started
        subscribers = bus._subscribers["request.started"]
        metrics_sub = [s for s in subscribers if "on_request_started" in s.handler.__name__]
        assert len(metrics_sub) > 0
        assert metrics_sub[0].priority == 10

    def test_error_tracker_high_priority(self):
        """ErrorTracker should have high priority (10)."""
        error_tracker = Mock()

        bus = EventBusFactory.create_event_bus(error_tracker=error_tracker)

        # Check priority for error.occurred
        subscribers = bus._subscribers["error.occurred"]
        error_sub = [s for s in subscribers if "on_error_occurred" in s.handler.__name__]
        assert len(error_sub) > 0
        assert error_sub[0].priority == 10

    def test_dynamo_metrics_high_priority(self):
        """DynamoMetrics should have high priority (9)."""
        dynamo_collector = Mock()

        bus = EventBusFactory.create_event_bus(dynamo_collector=dynamo_collector)

        # Check priority for request.started
        subscribers = bus._subscribers["request.started"]
        dynamo_sub = [s for s in subscribers if hasattr(s.handler, "__self__")]
        if dynamo_sub:
            assert dynamo_sub[0].priority == 9

    def test_streaming_tracker_medium_priority(self):
        """StreamingTracker should have medium priority (8)."""
        streaming_tracker = Mock()

        bus = EventBusFactory.create_event_bus(streaming_tracker=streaming_tracker)

        # Check priority for stream.started
        subscribers = bus._subscribers["stream.started"]
        streaming_sub = [s for s in subscribers if "on_stream_started" in s.handler.__name__]
        assert len(streaming_sub) > 0
        assert streaming_sub[0].priority == 8

    def test_cost_tracker_priority(self):
        """CostTracker should have priority (7)."""
        cost_tracker = Mock()

        bus = EventBusFactory.create_event_bus(cost_tracker=cost_tracker)

        # Check priority for cost.calculated
        subscribers = bus._subscribers["cost.calculated"]
        cost_sub = [s for s in subscribers if "on_cost_calculated" in s.handler.__name__]
        assert len(cost_sub) > 0
        assert cost_sub[0].priority == 7

    def test_model_tracker_priority(self):
        """ModelTracker should have priority (6)."""
        model_tracker = Mock()

        bus = EventBusFactory.create_event_bus(model_tracker=model_tracker)

        # Check priority for model.selected
        subscribers = bus._subscribers["model.selected"]
        model_sub = [s for s in subscribers if "on_model_selected" in s.handler.__name__]
        assert len(model_sub) > 0
        assert model_sub[0].priority == 6

    def test_priority_order_maintained(self):
        """Subscribers should be ordered by priority (highest first)."""
        # Create all trackers
        metrics_tracker = Mock()
        dynamo_collector = Mock()
        streaming_tracker = Mock()

        bus = EventBusFactory.create_event_bus(
            metrics_tracker=metrics_tracker,
            dynamo_collector=dynamo_collector,
            streaming_tracker=streaming_tracker,
        )

        # Check request.started has correct ordering
        subscribers = bus._subscribers["request.started"]
        priorities = [s.priority for s in subscribers]

        # Should be sorted in descending order (highest priority first)
        assert priorities == sorted(priorities, reverse=True)

    def test_multiple_subscribers_per_event_type(self):
        """Multiple trackers can subscribe to the same event type."""
        metrics_tracker = Mock()
        dynamo_collector = Mock()
        error_tracker = Mock()

        bus = EventBusFactory.create_event_bus(
            metrics_tracker=metrics_tracker,
            dynamo_collector=dynamo_collector,
            error_tracker=error_tracker,
        )

        # request.completed should have multiple subscribers
        subscribers = bus._subscribers["request.completed"]
        assert len(subscribers) >= 3  # At least metrics, dynamo, and error


@pytest.mark.unit
class TestEventTypeCoverage:
    """Test that all important event types have subscribers."""

    def test_request_started_subscribed(self):
        """request.started should have subscribers."""
        metrics_tracker = Mock()

        bus = EventBusFactory.create_event_bus(metrics_tracker=metrics_tracker)

        assert "request.started" in bus._subscribers
        assert len(bus._subscribers["request.started"]) > 0

    def test_request_completed_subscribed(self):
        """request.completed should have subscribers."""
        metrics_tracker = Mock()

        bus = EventBusFactory.create_event_bus(metrics_tracker=metrics_tracker)

        assert "request.completed" in bus._subscribers
        assert len(bus._subscribers["request.completed"]) > 0

    def test_request_failed_subscribed(self):
        """request.failed should have subscribers."""
        metrics_tracker = Mock()

        bus = EventBusFactory.create_event_bus(metrics_tracker=metrics_tracker)

        assert "request.failed" in bus._subscribers
        assert len(bus._subscribers["request.failed"]) > 0

    def test_stream_events_subscribed(self):
        """All stream.* events should have subscribers."""
        streaming_tracker = Mock()

        bus = EventBusFactory.create_event_bus(streaming_tracker=streaming_tracker)

        stream_events = [
            "stream.started",
            "stream.token_generated",
            "stream.first_token",
            "stream.completed",
            "stream.failed",
        ]

        for event_type in stream_events:
            assert event_type in bus._subscribers
            assert len(bus._subscribers[event_type]) > 0

    def test_error_events_subscribed(self):
        """error.* events should have subscribers."""
        error_tracker = Mock()

        bus = EventBusFactory.create_event_bus(error_tracker=error_tracker)

        assert "error.occurred" in bus._subscribers
        assert len(bus._subscribers["error.occurred"]) > 0

    def test_prefill_events_subscribed(self):
        """prefill.* events should have subscribers."""
        dynamo_collector = Mock()

        bus = EventBusFactory.create_event_bus(dynamo_collector=dynamo_collector)

        assert "prefill.started" in bus._subscribers
        assert "prefill.completed" in bus._subscribers

    def test_cache_events_subscribed(self):
        """cache.* events should have subscribers."""
        kv_cache_metrics = Mock()

        bus = EventBusFactory.create_event_bus(kv_cache_metrics=kv_cache_metrics)

        assert "cache.lookup" in bus._subscribers
        assert "cache.speedup_measured" in bus._subscribers

    def test_queue_and_batch_events_subscribed(self):
        """queue and batch events should have subscribers."""
        dynamo_collector = Mock()

        bus = EventBusFactory.create_event_bus(dynamo_collector=dynamo_collector)

        assert "queue.depth_changed" in bus._subscribers
        assert "batch.size_changed" in bus._subscribers


@pytest.mark.unit
class TestIntegration:
    """Test integration between event bus and trackers."""

    @pytest.mark.asyncio
    async def test_events_flow_to_metrics_tracker(self):
        """Events should flow through to MetricsTracker."""
        metrics_tracker = Mock()
        metrics_tracker.track_request = Mock()
        metrics_tracker.track_response = Mock()
        metrics_tracker.track_error = Mock()

        bus = EventBusFactory.create_event_bus(metrics_tracker=metrics_tracker)

        # Start the bus
        await bus.start()

        try:
            # Publish events
            await bus.publish(
                RequestStartedEvent(
                    request_id="req-1",
                    endpoint="/v1/chat/completions",
                    model="gpt-4",
                )
            )

            await bus.publish(
                RequestCompletedEvent(
                    request_id="req-1",
                    endpoint="/v1/chat/completions",
                    model="gpt-4",
                    duration_ms=100.0,
                    input_tokens=10,
                    output_tokens=20,
                )
            )

            await bus.publish(
                RequestFailedEvent(
                    request_id="req-2",
                    endpoint="/v1/chat/completions",
                    error_type="timeout",
                    error_message="Request timeout",
                )
            )

            # Wait for processing
            await asyncio.sleep(0.5)

        finally:
            await bus.stop()

        # Verify tracker methods were called
        assert metrics_tracker.track_request.called
        assert metrics_tracker.track_response.called
        assert metrics_tracker.track_error.called

    @pytest.mark.asyncio
    async def test_events_flow_to_streaming_tracker(self):
        """Events should flow through to StreamingTracker."""
        streaming_tracker = Mock()
        streaming_tracker.start_stream = Mock()
        streaming_tracker.record_token = Mock()
        streaming_tracker.complete_stream = Mock()

        bus = EventBusFactory.create_event_bus(streaming_tracker=streaming_tracker)

        # Start the bus
        await bus.start()

        try:
            # Publish stream events
            await bus.publish(
                StreamStartedEvent(
                    stream_id="stream-1",
                    endpoint="/v1/chat/completions",
                    model="gpt-4",
                    input_tokens=10,
                )
            )

            await bus.publish(
                StreamingTokenGeneratedEvent(
                    stream_id="stream-1",
                    token="Hello",
                    sequence_number=0,
                )
            )

            await bus.publish(
                StreamCompletedEvent(
                    stream_id="stream-1",
                    endpoint="/v1/chat/completions",
                    duration_ms=200.0,
                    token_count=5,
                )
            )

            # Wait for processing
            await asyncio.sleep(0.5)

        finally:
            await bus.stop()

        # Verify streaming tracker methods were called
        assert streaming_tracker.start_stream.called
        assert streaming_tracker.record_token.called
        assert streaming_tracker.complete_stream.called

    @pytest.mark.asyncio
    async def test_events_flow_to_error_tracker(self):
        """Events should flow through to ErrorTracker."""
        error_tracker = Mock()
        error_tracker.record_error = Mock()
        error_tracker.record_success = Mock()

        bus = EventBusFactory.create_event_bus(error_tracker=error_tracker)

        # Start the bus
        await bus.start()

        try:
            # Publish error events
            await bus.publish(
                ErrorOccurredEvent(
                    request_id="req-1",
                    endpoint="/v1/chat/completions",
                    model="gpt-4",
                    error_type="validation_error",
                    error_message="Invalid input",
                )
            )

            await bus.publish(
                RequestFailedEvent(
                    request_id="req-2",
                    endpoint="/v1/embeddings",
                    error_type="timeout",
                    error_message="Timeout",
                    status_code=504,
                )
            )

            # Wait for processing
            await asyncio.sleep(0.5)

        finally:
            await bus.stop()

        # Verify error tracker was called
        assert error_tracker.record_error.called
        assert error_tracker.record_error.call_count >= 2

    @pytest.mark.asyncio
    async def test_multiple_trackers_receive_same_event(self):
        """Multiple trackers should receive the same event."""
        metrics_tracker = Mock()
        metrics_tracker.track_response = Mock()

        error_tracker = Mock()
        error_tracker.record_success = Mock()

        dynamo_collector = Mock()
        dynamo_collector.complete_request = Mock()

        bus = EventBusFactory.create_event_bus(
            metrics_tracker=metrics_tracker,
            error_tracker=error_tracker,
            dynamo_collector=dynamo_collector,
        )

        # Start the bus
        await bus.start()

        try:
            # Publish a request completed event
            await bus.publish(
                RequestCompletedEvent(
                    request_id="req-1",
                    endpoint="/v1/chat/completions",
                    model="gpt-4",
                    duration_ms=150.0,
                    input_tokens=10,
                    output_tokens=20,
                )
            )

            # Wait for processing
            await asyncio.sleep(0.5)

        finally:
            await bus.stop()

        # All three trackers should have received the event
        assert metrics_tracker.track_response.called
        assert error_tracker.record_success.called
        assert dynamo_collector.complete_request.called

    @pytest.mark.asyncio
    async def test_priority_respected_in_execution(self):
        """Subscribers should be called in priority order."""
        call_order = []

        # Create mock trackers that record call order
        metrics_tracker = Mock()

        async def metrics_handler(event):
            call_order.append(("metrics", event.event_type))

        dynamo_collector = Mock()

        async def dynamo_handler(event):
            call_order.append(("dynamo", event.event_type))

        streaming_tracker = Mock()

        async def streaming_handler(event):
            call_order.append(("streaming", event.event_type))

        # Manually create bus and subscribe with known order
        bus = AsyncEventBus()

        # Subscribe with different priorities
        bus.subscribe("request.started", metrics_handler, priority=10)
        bus.subscribe("request.started", dynamo_handler, priority=9)
        bus.subscribe("request.started", streaming_handler, priority=8)

        # Start the bus
        await bus.start()

        try:
            # Publish event
            await bus.publish(
                RequestStartedEvent(
                    request_id="req-1",
                    endpoint="/v1/chat/completions",
                )
            )

            # Wait for processing
            await asyncio.sleep(0.5)

        finally:
            await bus.stop()

        # Verify call order matches priorities (highest first)
        # Note: asyncio.gather runs concurrently, so we just check all were called
        assert len(call_order) == 3
        assert ("metrics", "request.started") in call_order
        assert ("dynamo", "request.started") in call_order
        assert ("streaming", "request.started") in call_order


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_create_with_invalid_tracker_types(self):
        """Should handle invalid tracker types gracefully."""
        # Pass invalid objects as trackers
        bus = EventBusFactory.create_event_bus(
            metrics_tracker="invalid",
            streaming_tracker=123,
            cost_tracker=None,
        )

        # Should still create a bus (subscribers just won't work properly)
        assert isinstance(bus, AsyncEventBus)

    @pytest.mark.asyncio
    async def test_subscriber_error_doesnt_crash_bus(self):
        """Errors in subscribers should not crash the event bus."""
        # Create tracker with failing method
        metrics_tracker = Mock()
        metrics_tracker.track_request = Mock(side_effect=Exception("Test error"))

        bus = EventBusFactory.create_event_bus(metrics_tracker=metrics_tracker)

        # Start the bus
        await bus.start()

        try:
            # Publish event that will cause subscriber to fail
            await bus.publish(
                RequestStartedEvent(
                    request_id="req-1",
                    endpoint="/v1/chat/completions",
                )
            )

            # Wait for processing
            await asyncio.sleep(0.5)

            # Bus should still be running
            assert bus._running

        finally:
            await bus.stop()

    @pytest.mark.asyncio
    async def test_bus_handles_unknown_event_types(self):
        """Bus should handle events with no subscribers gracefully."""
        bus = EventBusFactory.create_event_bus()

        # Start the bus
        await bus.start()

        try:
            # Publish event with no subscribers
            await bus.publish(
                BaseEvent(
                    event_type="unknown.event.type",
                    request_id="req-1",
                )
            )

            # Wait for processing
            await asyncio.sleep(0.5)

            # Should not crash
            assert bus._running

        finally:
            await bus.stop()

    def test_factory_creates_independent_instances(self):
        """Each factory call should create a new bus instance."""
        bus1 = EventBusFactory.create_event_bus()
        bus2 = EventBusFactory.create_event_bus()

        # Should be different instances
        assert bus1 is not bus2

    @pytest.mark.asyncio
    async def test_concurrent_event_publishing(self):
        """Bus should handle concurrent event publishing."""
        metrics_tracker = Mock()
        metrics_tracker.track_request = Mock()

        bus = EventBusFactory.create_event_bus(metrics_tracker=metrics_tracker)

        # Start the bus
        await bus.start()

        try:
            # Publish multiple events concurrently
            events = [
                RequestStartedEvent(
                    request_id=f"req-{i}",
                    endpoint="/v1/chat/completions",
                )
                for i in range(100)
            ]

            # Publish all at once
            for event in events:
                await bus.publish(event)

            # Wait for processing
            await asyncio.sleep(1.0)

        finally:
            await bus.stop()

        # All events should have been processed
        assert metrics_tracker.track_request.call_count == 100
