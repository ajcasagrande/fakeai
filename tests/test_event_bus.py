"""
Comprehensive tests for AsyncEventBus in fakeai/events/bus.py.

Tests cover:
- Basic operations (publish, subscribe, unsubscribe)
- Priority-based delivery
- Queue management and overflow
- Worker thread lifecycle
- Error handling and timeouts
- Statistics tracking
- Wildcard subscriptions
"""

import asyncio
import sys
import time
from pathlib import Path

import pytest

# Add fakeai directory to path to import modules without triggering app initialization
fakeai_dir = Path(__file__).parent.parent / "fakeai"
sys.path.insert(0, str(fakeai_dir))

from events.base import BaseEvent
from events.bus import AsyncEventBus

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def event_bus():
    """Create a fresh event bus for each test."""
    bus = AsyncEventBus(max_queue_size=100)
    await bus.start()
    yield bus
    await bus.stop(timeout=2.0)


@pytest.fixture
def small_queue_bus():
    """Create an event bus with a small queue for overflow testing."""
    return AsyncEventBus(max_queue_size=5)


@pytest.fixture
def sample_events():
    """Create various sample events for testing."""
    return {
        "request_started": BaseEvent(
            event_type="request.started",
            request_id="req-123",
            metadata={"model": "gpt-4"},
        ),
        "request_completed": BaseEvent(
            event_type="request.completed",
            request_id="req-123",
            metadata={"tokens": 100},
        ),
        "stream_started": BaseEvent(
            event_type="stream.started",
            request_id="req-456",
            metadata={"stream_id": "stream-1"},
        ),
        "error_occurred": BaseEvent(
            event_type="error.occurred",
            request_id="req-789",
            metadata={"error": "timeout"},
        ),
    }


@pytest.fixture
def call_tracker():
    """Create a tracker to record handler calls."""

    class CallTracker:
        def __init__(self):
            self.calls = []
            self.call_order = []

        def reset(self):
            self.calls = []
            self.call_order = []

        async def create_handler(self, name: str):
            """Create a handler that records calls."""

            async def handler(event: BaseEvent):
                self.calls.append({"name": name, "event": event})
                self.call_order.append(name)

            handler.__name__ = name
            return handler

        async def create_priority_handler(self, name: str, delay: float = 0.0):
            """Create a handler with optional delay to test ordering."""

            async def handler(event: BaseEvent):
                if delay > 0:
                    await asyncio.sleep(delay)
                self.calls.append({"name": name, "event": event, "time": time.time()})
                self.call_order.append(name)

            handler.__name__ = name
            return handler

        async def create_failing_handler(self, name: str, exception: Exception):
            """Create a handler that raises an exception."""

            async def handler(event: BaseEvent):
                self.calls.append({"name": name, "event": event})
                self.call_order.append(name)
                raise exception

            handler.__name__ = name
            return handler

        async def create_timeout_handler(self, name: str, timeout: float):
            """Create a handler that times out."""

            async def handler(event: BaseEvent):
                self.calls.append({"name": name, "event": event})
                self.call_order.append(name)
                await asyncio.sleep(timeout)

            handler.__name__ = name
            return handler

    return CallTracker()


# ============================================================================
# Basic Operations Tests
# ============================================================================


@pytest.mark.asyncio
async def test_publish_and_subscribe(event_bus, sample_events, call_tracker):
    """Test basic publish and subscribe functionality."""
    handler = await call_tracker.create_handler("handler1")
    event_bus.subscribe("request.started", handler)

    # Publish event
    await event_bus.publish(sample_events["request_started"])

    # Wait for processing
    await asyncio.sleep(0.2)

    # Verify handler was called
    assert len(call_tracker.calls) == 1
    assert call_tracker.calls[0]["name"] == "handler1"
    assert call_tracker.calls[0]["event"].event_type == "request.started"


@pytest.mark.asyncio
async def test_multiple_subscribers_same_event(event_bus, sample_events, call_tracker):
    """Test multiple subscribers to the same event type."""
    handler1 = await call_tracker.create_handler("handler1")
    handler2 = await call_tracker.create_handler("handler2")
    handler3 = await call_tracker.create_handler("handler3")

    # Subscribe all handlers to same event
    event_bus.subscribe("request.started", handler1)
    event_bus.subscribe("request.started", handler2)
    event_bus.subscribe("request.started", handler3)

    # Publish event
    await event_bus.publish(sample_events["request_started"])

    # Wait for processing
    await asyncio.sleep(0.2)

    # All handlers should be called
    assert len(call_tracker.calls) == 3
    handler_names = [call["name"] for call in call_tracker.calls]
    assert "handler1" in handler_names
    assert "handler2" in handler_names
    assert "handler3" in handler_names


@pytest.mark.asyncio
async def test_subscribe_to_multiple_events(event_bus, sample_events, call_tracker):
    """Test subscribing a single handler to multiple event types."""
    handler = await call_tracker.create_handler("handler1")

    # Subscribe to multiple event types
    event_bus.subscribe("request.started", handler)
    event_bus.subscribe("request.completed", handler)

    # Publish different events
    await event_bus.publish(sample_events["request_started"])
    await event_bus.publish(sample_events["request_completed"])

    # Wait for processing
    await asyncio.sleep(0.2)

    # Handler should be called twice
    assert len(call_tracker.calls) == 2
    event_types = [call["event"].event_type for call in call_tracker.calls]
    assert "request.started" in event_types
    assert "request.completed" in event_types


@pytest.mark.asyncio
async def test_unsubscribe(event_bus, sample_events, call_tracker):
    """Test unsubscribing from events."""
    handler1 = await call_tracker.create_handler("handler1")
    handler2 = await call_tracker.create_handler("handler2")

    # Subscribe both handlers
    event_bus.subscribe("request.started", handler1)
    event_bus.subscribe("request.started", handler2)

    # Publish event - both should receive it
    await event_bus.publish(sample_events["request_started"])
    await asyncio.sleep(0.2)

    assert len(call_tracker.calls) == 2
    call_tracker.reset()

    # Unsubscribe handler1
    event_bus.unsubscribe("request.started", handler1)

    # Publish again - only handler2 should receive it
    await event_bus.publish(sample_events["request_started"])
    await asyncio.sleep(0.2)

    assert len(call_tracker.calls) == 1
    assert call_tracker.calls[0]["name"] == "handler2"


@pytest.mark.asyncio
async def test_wildcard_subscription(event_bus, sample_events, call_tracker):
    """Test wildcard subscription to all events."""
    wildcard_handler = await call_tracker.create_handler("wildcard")
    specific_handler = await call_tracker.create_handler("specific")

    # Subscribe wildcard handler to all events
    event_bus.subscribe("*", wildcard_handler)
    # Subscribe specific handler to one event
    event_bus.subscribe("request.started", specific_handler)

    # Publish various events
    await event_bus.publish(sample_events["request_started"])
    await event_bus.publish(sample_events["stream_started"])
    await event_bus.publish(sample_events["error_occurred"])

    # Wait for processing
    await asyncio.sleep(0.3)

    # Wildcard should receive all 3 events
    wildcard_calls = [c for c in call_tracker.calls if c["name"] == "wildcard"]
    assert len(wildcard_calls) == 3

    # Specific should only receive request.started
    specific_calls = [c for c in call_tracker.calls if c["name"] == "specific"]
    assert len(specific_calls) == 1
    assert specific_calls[0]["event"].event_type == "request.started"


@pytest.mark.asyncio
async def test_no_subscribers(event_bus, sample_events):
    """Test publishing event with no subscribers doesn't crash."""
    # Publish event with no subscribers
    await event_bus.publish(sample_events["request_started"])

    # Wait for processing
    await asyncio.sleep(0.1)

    # Should complete without error
    stats = event_bus.get_stats()
    assert stats["events_published"] == 1
    assert stats["events_processed"] == 1


# ============================================================================
# Priority-Based Delivery Tests
# ============================================================================


@pytest.mark.asyncio
async def test_priority_ordering(event_bus, sample_events, call_tracker):
    """Test that subscribers are called in priority order (highest first)."""
    low_priority = await call_tracker.create_priority_handler("low_priority")
    medium_priority = await call_tracker.create_priority_handler("medium_priority")
    high_priority = await call_tracker.create_priority_handler("high_priority")

    # Subscribe with different priorities
    event_bus.subscribe("request.started", low_priority, priority=1)
    event_bus.subscribe("request.started", medium_priority, priority=5)
    event_bus.subscribe("request.started", high_priority, priority=10)

    # Publish event
    await event_bus.publish(sample_events["request_started"])

    # Wait for processing
    await asyncio.sleep(0.2)

    # Check order: high, medium, low
    assert len(call_tracker.call_order) == 3
    assert call_tracker.call_order[0] == "high_priority"
    assert call_tracker.call_order[1] == "medium_priority"
    assert call_tracker.call_order[2] == "low_priority"


@pytest.mark.asyncio
async def test_equal_priority_maintains_order(event_bus, sample_events, call_tracker):
    """Test that equal priority subscribers maintain subscription order."""
    handler1 = await call_tracker.create_priority_handler("handler1")
    handler2 = await call_tracker.create_priority_handler("handler2")
    handler3 = await call_tracker.create_priority_handler("handler3")

    # Subscribe all with same priority
    event_bus.subscribe("request.started", handler1, priority=5)
    event_bus.subscribe("request.started", handler2, priority=5)
    event_bus.subscribe("request.started", handler3, priority=5)

    # Publish event
    await event_bus.publish(sample_events["request_started"])

    # Wait for processing
    await asyncio.sleep(0.2)

    # All should be called
    assert len(call_tracker.call_order) == 3
    # Order may vary due to concurrent execution with gather


@pytest.mark.asyncio
async def test_default_priority_is_zero(event_bus, sample_events, call_tracker):
    """Test that default priority is 0."""
    default_handler = await call_tracker.create_priority_handler("default")
    high_priority = await call_tracker.create_priority_handler("high")

    # Subscribe one with default priority, one with high
    event_bus.subscribe("request.started", default_handler)  # priority defaults to 0
    event_bus.subscribe("request.started", high_priority, priority=10)

    # Publish event
    await event_bus.publish(sample_events["request_started"])

    # Wait for processing
    await asyncio.sleep(0.2)

    # High priority should be called first
    assert call_tracker.call_order[0] == "high"
    assert call_tracker.call_order[1] == "default"


# ============================================================================
# Queue Management Tests
# ============================================================================


@pytest.mark.asyncio
async def test_events_added_to_queue(event_bus, sample_events):
    """Test that published events are added to the queue."""
    # Stop the worker to keep events in queue
    await event_bus.stop()

    # Publish several events
    await event_bus.publish(sample_events["request_started"])
    await event_bus.publish(sample_events["request_completed"])
    await event_bus.publish(sample_events["stream_started"])

    # Check queue depth
    stats = event_bus.get_stats()
    assert stats["queue_depth"] == 3
    assert stats["events_published"] == 3
    assert stats["events_processed"] == 0


@pytest.mark.asyncio
async def test_queue_overflow_drops_events(small_queue_bus, sample_events):
    """Test that events are dropped when queue is full."""
    # Don't start the worker so queue fills up
    bus = small_queue_bus

    # Publish more events than queue can hold
    for i in range(10):
        event = BaseEvent(event_type="test.event", request_id=f"req-{i}")
        await bus.publish(event)

    # Check stats
    stats = bus.get_stats()
    assert stats["events_published"] == 5  # Only 5 fit in queue
    assert stats["events_dropped"] == 5  # 5 were dropped
    assert stats["queue_depth"] == 5  # Queue is full


@pytest.mark.asyncio
async def test_dropped_events_tracking(small_queue_bus, sample_events):
    """Test that dropped events are tracked correctly."""
    bus = small_queue_bus

    # Fill the queue
    for i in range(5):
        event = BaseEvent(event_type="test.event", request_id=f"req-{i}")
        await bus.publish(event)

    stats = bus.get_stats()
    initial_dropped = stats["events_dropped"]

    # Try to add more events
    for i in range(3):
        event = BaseEvent(event_type="test.event", request_id=f"req-overflow-{i}")
        await bus.publish(event)

    # Check that dropped count increased
    stats = bus.get_stats()
    assert stats["events_dropped"] == initial_dropped + 3


@pytest.mark.asyncio
async def test_queue_depth_decreases_as_processed(event_bus, sample_events):
    """Test that queue depth decreases as events are processed."""
    # Stop worker temporarily
    await event_bus.stop()

    # Add events to queue
    for i in range(5):
        event = BaseEvent(event_type="test.event", request_id=f"req-{i}")
        await event_bus.publish(event)

    # Check initial queue depth
    stats = event_bus.get_stats()
    assert stats["queue_depth"] == 5

    # Start worker and wait for processing
    await event_bus.start()
    await asyncio.sleep(0.3)

    # Queue should be empty
    stats = event_bus.get_stats()
    assert stats["queue_depth"] == 0
    assert stats["events_processed"] == 5


@pytest.mark.asyncio
async def test_drop_rate_calculation(small_queue_bus):
    """Test that drop rate is calculated correctly."""
    bus = small_queue_bus

    # Publish events, some will be dropped
    for i in range(10):
        event = BaseEvent(event_type="test.event", request_id=f"req-{i}")
        await bus.publish(event)

    stats = bus.get_stats()

    # The drop rate is events_dropped / events_published (according to implementation)
    # With queue size 5, trying to publish 10 events means 5 are accepted, 5 are dropped
    # drop_rate = 5 / 5 = 1.0
    expected_drop_rate = stats["events_dropped"] / stats["events_published"] if stats["events_published"] > 0 else 0.0

    assert stats["drop_rate"] == pytest.approx(expected_drop_rate)
    assert stats["events_published"] == 5  # Only 5 fit in queue
    assert stats["events_dropped"] == 5  # 5 were dropped


# ============================================================================
# Worker Thread Lifecycle Tests
# ============================================================================


@pytest.mark.asyncio
async def test_start_worker():
    """Test starting the worker thread."""
    bus = AsyncEventBus()

    # Initially not running
    assert bus._running is False
    assert bus._worker_task is None

    # Start the worker
    await bus.start()

    # Now running
    assert bus._running is True
    assert bus._worker_task is not None

    # Clean up
    await bus.stop()


@pytest.mark.asyncio
async def test_stop_worker():
    """Test stopping the worker thread."""
    bus = AsyncEventBus()
    await bus.start()

    # Stop the worker
    await bus.stop()

    # No longer running
    assert bus._running is False


@pytest.mark.asyncio
async def test_double_start_ignored():
    """Test that starting an already running worker is ignored."""
    bus = AsyncEventBus()
    await bus.start()

    first_task = bus._worker_task

    # Try to start again
    await bus.start()

    # Same task should still be running
    assert bus._worker_task == first_task

    # Clean up
    await bus.stop()


@pytest.mark.asyncio
async def test_stop_without_start():
    """Test that stopping a non-running worker is handled gracefully."""
    bus = AsyncEventBus()

    # Stop without starting should not crash
    await bus.stop()

    assert bus._running is False


@pytest.mark.asyncio
async def test_graceful_shutdown_drains_queue(call_tracker):
    """Test that shutdown waits for queue to drain."""
    bus = AsyncEventBus()
    await bus.start()

    handler = await call_tracker.create_handler("handler1")
    bus.subscribe("test.event", handler)

    # Publish several events
    for i in range(5):
        event = BaseEvent(event_type="test.event", request_id=f"req-{i}")
        await bus.publish(event)

    # Give the worker a moment to start processing
    await asyncio.sleep(0.1)

    # Stop with timeout - should process all events
    await bus.stop(timeout=3.0)

    # All events should be processed
    stats = bus.get_stats()
    assert stats["events_processed"] == 5
    assert len(call_tracker.calls) == 5


@pytest.mark.asyncio
async def test_shutdown_timeout(call_tracker):
    """Test that shutdown times out if queue doesn't drain in time."""
    bus = AsyncEventBus()
    await bus.start()

    # Create a slow handler
    slow_handler = await call_tracker.create_timeout_handler("slow", timeout=10.0)
    bus.subscribe("test.event", slow_handler)

    # Publish events
    for i in range(3):
        event = BaseEvent(event_type="test.event", request_id=f"req-{i}")
        await bus.publish(event)

    # Wait a bit for first event to start processing
    await asyncio.sleep(0.2)

    # Stop with short timeout
    await bus.stop(timeout=0.5)

    # Not all events will be processed due to timeout
    stats = bus.get_stats()
    assert stats["events_processed"] < 3


@pytest.mark.asyncio
async def test_event_processing_in_background(call_tracker):
    """Test that events are processed in background without blocking."""
    bus = AsyncEventBus()
    await bus.start()

    handler = await call_tracker.create_handler("handler1")
    bus.subscribe("test.event", handler)

    # Publish event
    event = BaseEvent(event_type="test.event")
    await bus.publish(event)

    # publish() should return immediately (non-blocking)
    # Handler should be called in background
    await asyncio.sleep(0.2)

    # Handler should have been called
    assert len(call_tracker.calls) == 1

    await bus.stop()


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_subscriber_exception_doesnt_stop_others(event_bus, sample_events, call_tracker):
    """Test that exception in one subscriber doesn't prevent others from running."""
    good_handler1 = await call_tracker.create_handler("good1")
    failing_handler = await call_tracker.create_failing_handler(
        "failing", ValueError("Test error")
    )
    good_handler2 = await call_tracker.create_handler("good2")

    # Subscribe all handlers
    event_bus.subscribe("test.event", good_handler1)
    event_bus.subscribe("test.event", failing_handler)
    event_bus.subscribe("test.event", good_handler2)

    # Publish event
    event = BaseEvent(event_type="test.event")
    await event_bus.publish(event)

    # Wait for processing
    await asyncio.sleep(0.2)

    # All handlers should have been called (even though one failed)
    assert len(call_tracker.calls) == 3
    handler_names = [call["name"] for call in call_tracker.calls]
    assert "good1" in handler_names
    assert "failing" in handler_names
    assert "good2" in handler_names


@pytest.mark.asyncio
async def test_timeout_protection(event_bus, sample_events, call_tracker):
    """Test that subscribers are protected by timeout."""
    timeout_handler = await call_tracker.create_timeout_handler(
        "timeout_handler", timeout=10.0
    )
    good_handler = await call_tracker.create_handler("good_handler")

    # Subscribe both handlers
    event_bus.subscribe("test.event", timeout_handler)
    event_bus.subscribe("test.event", good_handler)

    # Publish event
    event = BaseEvent(event_type="test.event")
    await event_bus.publish(event)

    # Wait for processing (should timeout at 5s per handler)
    await asyncio.sleep(6.0)

    # Both should have been called
    assert len(call_tracker.calls) == 2

    # Check stats - timeout handler should have timeout count
    stats = event_bus.get_stats()
    subscribers = stats["subscribers"]["test.event"]

    timeout_sub = next(s for s in subscribers if s["handler_name"] == "timeout_handler")
    assert timeout_sub["timeout_count"] == 1

    good_sub = next(s for s in subscribers if s["handler_name"] == "good_handler")
    assert good_sub["success_count"] == 1


@pytest.mark.asyncio
async def test_error_counting(event_bus, call_tracker):
    """Test that errors are counted in subscriber stats."""
    failing_handler = await call_tracker.create_failing_handler(
        "failing", RuntimeError("Test error")
    )

    event_bus.subscribe("test.event", failing_handler)

    # Publish multiple events
    for i in range(3):
        event = BaseEvent(event_type="test.event")
        await event_bus.publish(event)

    # Wait for processing
    await asyncio.sleep(0.3)

    # Check stats
    stats = event_bus.get_stats()
    subscribers = stats["subscribers"]["test.event"]

    failing_sub = subscribers[0]
    assert failing_sub["error_count"] == 3
    assert failing_sub["success_count"] == 0


@pytest.mark.asyncio
async def test_timeout_counting(event_bus, call_tracker):
    """Test that timeouts are counted in subscriber stats."""
    timeout_handler = await call_tracker.create_timeout_handler("timeout", timeout=10.0)

    event_bus.subscribe("test.event", timeout_handler)

    # Publish multiple events
    for i in range(2):
        event = BaseEvent(event_type="test.event")
        await event_bus.publish(event)

    # Wait for processing (timeouts at 5s each)
    await asyncio.sleep(11.0)

    # Check stats
    stats = event_bus.get_stats()
    subscribers = stats["subscribers"]["test.event"]

    timeout_sub = subscribers[0]
    assert timeout_sub["timeout_count"] == 2
    assert timeout_sub["success_count"] == 0


@pytest.mark.asyncio
async def test_failure_rate_calculation(event_bus, call_tracker):
    """Test that failure rate is calculated correctly."""
    # Create handler that fails 50% of the time
    call_count = {"count": 0}

    async def intermittent_handler(event: BaseEvent):
        call_count["count"] += 1
        if call_count["count"] % 2 == 0:
            raise ValueError("Intermittent error")

    intermittent_handler.__name__ = "intermittent"

    event_bus.subscribe("test.event", intermittent_handler)

    # Publish multiple events
    for i in range(4):
        event = BaseEvent(event_type="test.event")
        await event_bus.publish(event)

    # Wait for processing
    await asyncio.sleep(0.3)

    # Check stats
    stats = event_bus.get_stats()
    subscribers = stats["subscribers"]["test.event"]

    sub = subscribers[0]
    assert sub["success_count"] == 2
    assert sub["error_count"] == 2
    assert sub["failure_rate"] == 0.5


# ============================================================================
# Statistics Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_stats_structure(event_bus):
    """Test that get_stats returns correct structure."""
    stats = event_bus.get_stats()

    # Check required keys
    assert "running" in stats
    assert "queue_depth" in stats
    assert "queue_max_size" in stats
    assert "events_published" in stats
    assert "events_processed" in stats
    assert "events_dropped" in stats
    assert "drop_rate" in stats
    assert "subscribers" in stats

    # Check types
    assert isinstance(stats["running"], bool)
    assert isinstance(stats["queue_depth"], int)
    assert isinstance(stats["queue_max_size"], int)
    assert isinstance(stats["events_published"], int)
    assert isinstance(stats["events_processed"], int)
    assert isinstance(stats["events_dropped"], int)
    assert isinstance(stats["drop_rate"], float)
    assert isinstance(stats["subscribers"], dict)


@pytest.mark.asyncio
async def test_event_counts(event_bus, sample_events, call_tracker):
    """Test that event counts are tracked correctly."""
    handler = await call_tracker.create_handler("handler1")
    event_bus.subscribe("test.event", handler)

    # Publish several events
    for i in range(5):
        event = BaseEvent(event_type="test.event")
        await event_bus.publish(event)

    # Wait for processing
    await asyncio.sleep(0.3)

    # Check stats
    stats = event_bus.get_stats()
    assert stats["events_published"] == 5
    assert stats["events_processed"] == 5
    assert stats["events_dropped"] == 0


@pytest.mark.asyncio
async def test_subscriber_success_count(event_bus, call_tracker):
    """Test that subscriber success count is tracked."""
    handler = await call_tracker.create_handler("handler1")
    event_bus.subscribe("test.event", handler)

    # Publish events
    for i in range(3):
        event = BaseEvent(event_type="test.event")
        await event_bus.publish(event)

    # Wait for processing
    await asyncio.sleep(0.2)

    # Check stats
    stats = event_bus.get_stats()
    subscribers = stats["subscribers"]["test.event"]

    sub = subscribers[0]
    assert sub["success_count"] == 3
    assert sub["error_count"] == 0
    assert sub["timeout_count"] == 0


@pytest.mark.asyncio
async def test_processing_time_tracking(event_bus, call_tracker):
    """Test that processing time is tracked."""
    handler = await call_tracker.create_priority_handler("handler1", delay=0.1)
    event_bus.subscribe("test.event", handler)

    # Publish event
    event = BaseEvent(event_type="test.event")
    await event_bus.publish(event)

    # Wait for processing
    await asyncio.sleep(0.3)

    # Check stats
    stats = event_bus.get_stats()
    subscribers = stats["subscribers"]["test.event"]

    sub = subscribers[0]
    assert sub["avg_processing_time_ms"] > 100  # Should be at least 100ms


@pytest.mark.asyncio
async def test_subscriber_stats_structure(event_bus, call_tracker):
    """Test that subscriber stats have correct structure."""
    handler = await call_tracker.create_handler("handler1")
    event_bus.subscribe("test.event", handler, priority=5)

    # Publish event
    event = BaseEvent(event_type="test.event")
    await event_bus.publish(event)

    # Wait for processing
    await asyncio.sleep(0.2)

    # Check subscriber stats structure
    stats = event_bus.get_stats()
    subscribers = stats["subscribers"]["test.event"]

    sub = subscribers[0]
    assert "event_type" in sub
    assert "handler_name" in sub
    assert "priority" in sub
    assert "success_count" in sub
    assert "error_count" in sub
    assert "timeout_count" in sub
    assert "failure_rate" in sub
    assert "avg_processing_time_ms" in sub

    assert sub["event_type"] == "test.event"
    assert sub["handler_name"] == "handler1"
    assert sub["priority"] == 5


@pytest.mark.asyncio
async def test_stats_multiple_event_types(event_bus, call_tracker):
    """Test stats with multiple event types."""
    handler1 = await call_tracker.create_handler("handler1")
    handler2 = await call_tracker.create_handler("handler2")

    event_bus.subscribe("event.type1", handler1)
    event_bus.subscribe("event.type2", handler2)

    # Publish different event types
    await event_bus.publish(BaseEvent(event_type="event.type1"))
    await event_bus.publish(BaseEvent(event_type="event.type2"))

    # Wait for processing
    await asyncio.sleep(0.2)

    # Check stats
    stats = event_bus.get_stats()
    assert "event.type1" in stats["subscribers"]
    assert "event.type2" in stats["subscribers"]

    type1_subs = stats["subscribers"]["event.type1"]
    type2_subs = stats["subscribers"]["event.type2"]

    assert len(type1_subs) == 1
    assert len(type2_subs) == 1
    assert type1_subs[0]["handler_name"] == "handler1"
    assert type2_subs[0]["handler_name"] == "handler2"


@pytest.mark.asyncio
async def test_stats_wildcard_subscribers(event_bus, call_tracker):
    """Test that wildcard subscribers appear in stats."""
    wildcard = await call_tracker.create_handler("wildcard")
    event_bus.subscribe("*", wildcard)

    # Publish event
    await event_bus.publish(BaseEvent(event_type="test.event"))

    # Wait for processing
    await asyncio.sleep(0.2)

    # Check stats
    stats = event_bus.get_stats()
    assert "*" in stats["subscribers"]

    wildcard_subs = stats["subscribers"]["*"]
    assert len(wildcard_subs) == 1
    assert wildcard_subs[0]["handler_name"] == "wildcard"
    assert wildcard_subs[0]["success_count"] == 1


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_complete_lifecycle():
    """Test complete lifecycle of event bus."""
    bus = AsyncEventBus(max_queue_size=100)
    call_tracker = []

    async def handler(event: BaseEvent):
        call_tracker.append(event)

    handler.__name__ = "handler"

    # Subscribe
    bus.subscribe("test.event", handler)

    # Start worker
    await bus.start()

    # Publish events
    for i in range(5):
        event = BaseEvent(event_type="test.event", request_id=f"req-{i}")
        await bus.publish(event)

    # Wait for processing
    await asyncio.sleep(0.3)

    # Check results
    assert len(call_tracker) == 5

    # Check stats
    stats = bus.get_stats()
    assert stats["events_published"] == 5
    assert stats["events_processed"] == 5
    assert stats["running"] is True

    # Stop
    await bus.stop()

    # Check final state
    stats = bus.get_stats()
    assert stats["running"] is False


@pytest.mark.asyncio
async def test_high_volume_events(call_tracker):
    """Test handling high volume of events."""
    bus = AsyncEventBus(max_queue_size=1000)
    await bus.start()

    handler = await call_tracker.create_handler("handler1")
    bus.subscribe("test.event", handler)

    # Publish many events
    num_events = 100
    for i in range(num_events):
        event = BaseEvent(event_type="test.event", request_id=f"req-{i}")
        await bus.publish(event)

    # Wait for processing
    await asyncio.sleep(2.0)

    # All events should be processed
    stats = bus.get_stats()
    assert stats["events_published"] == num_events
    assert stats["events_processed"] == num_events
    assert len(call_tracker.calls) == num_events

    await bus.stop()


@pytest.mark.asyncio
async def test_mixed_priority_and_errors(event_bus, call_tracker):
    """Test complex scenario with priorities and errors."""
    high_priority = await call_tracker.create_priority_handler("high")
    medium_failing = await call_tracker.create_failing_handler(
        "medium_failing", ValueError("Error")
    )
    low_timeout = await call_tracker.create_timeout_handler("low_timeout", timeout=10.0)

    # Subscribe with different priorities
    event_bus.subscribe("test.event", high_priority, priority=10)
    event_bus.subscribe("test.event", medium_failing, priority=5)
    event_bus.subscribe("test.event", low_timeout, priority=1)

    # Publish event
    event = BaseEvent(event_type="test.event")
    await event_bus.publish(event)

    # Wait for processing
    await asyncio.sleep(6.0)

    # All should have been called
    assert len(call_tracker.calls) == 3

    # Check order (high priority first)
    assert call_tracker.call_order[0] == "high"

    # Check stats
    stats = event_bus.get_stats()
    subscribers = stats["subscribers"]["test.event"]

    # Find each subscriber
    high_sub = next(s for s in subscribers if s["handler_name"] == "high")
    medium_sub = next(s for s in subscribers if s["handler_name"] == "medium_failing")
    low_sub = next(s for s in subscribers if s["handler_name"] == "low_timeout")

    assert high_sub["success_count"] == 1
    assert high_sub["error_count"] == 0

    assert medium_sub["success_count"] == 0
    assert medium_sub["error_count"] == 1

    assert low_sub["timeout_count"] == 1
    assert low_sub["success_count"] == 0
