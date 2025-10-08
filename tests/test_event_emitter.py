"""
Comprehensive tests for EventEmitterMixin.

Tests mixin integration, event emission, auto-fill request ID,
event bus configuration, and edge cases.
"""

import asyncio
from dataclasses import dataclass
from typing import Optional

import pytest

from fakeai.events.base import BaseEvent
from fakeai.events.bus import AsyncEventBus
from fakeai.events.emitter import EventEmitterMixin


# Test event classes
@dataclass
class TestEvent(BaseEvent):
    """Test event for basic emission."""

    event_type: str = "test.event"
    message: str = ""


@dataclass
class RequestEvent(BaseEvent):
    """Test event with request context."""

    event_type: str = "test.request"
    data: str = ""


# Mock context class
class MockContext:
    """Mock context with request_id."""

    def __init__(self, request_id: str):
        self.request_id = request_id


# Test classes that use the mixin
class SimpleEmitter(EventEmitterMixin):
    """Simple class that uses EventEmitterMixin."""



class EmitterWithParent:
    """Parent class with __init__."""

    def __init__(self, name: str):
        self.name = name


class MultiInheritanceEmitter(EventEmitterMixin, EmitterWithParent):
    """Test mixin with multiple inheritance."""

    def __init__(self, name: str, event_bus: Optional[AsyncEventBus] = None):
        super().__init__(name=name, event_bus=event_bus)


class EmitterWithContext(EventEmitterMixin):
    """Emitter with context attribute for auto-fill testing."""

    def __init__(self, context: MockContext, event_bus: Optional[AsyncEventBus] = None):
        super().__init__(event_bus=event_bus)
        self.context = context


class EmitterWithoutContext(EventEmitterMixin):
    """Emitter without context attribute."""



@pytest.fixture
async def event_bus():
    """Create and start an event bus for testing."""
    bus = AsyncEventBus(max_queue_size=100)
    await bus.start()
    yield bus
    await bus.stop(timeout=2.0)


@pytest.fixture
def event_collector():
    """Collector to capture events for verification."""
    collected_events = []

    async def collect(event: BaseEvent):
        collected_events.append(event)

    collect.events = collected_events
    return collect


class TestMixinIntegration:
    """Test mixin integration with various class structures."""

    def test_simple_mixin_integration(self):
        """Test that mixin can be mixed into simple class."""
        emitter = SimpleEmitter()
        assert hasattr(emitter, "emit")
        assert hasattr(emitter, "set_event_bus")
        assert hasattr(emitter, "has_event_bus")
        assert emitter._event_bus is None

    def test_mixin_with_event_bus(self, event_bus):
        """Test mixin initialization with event bus."""
        emitter = SimpleEmitter(event_bus=event_bus)
        assert emitter._event_bus is event_bus
        assert emitter.has_event_bus()

    def test_multiple_inheritance(self):
        """Test mixin works with multiple inheritance."""
        emitter = MultiInheritanceEmitter(name="test")
        assert emitter.name == "test"
        assert hasattr(emitter, "emit")
        assert not emitter.has_event_bus()

    def test_multiple_inheritance_with_event_bus(self, event_bus):
        """Test multiple inheritance with event bus."""
        emitter = MultiInheritanceEmitter(name="test", event_bus=event_bus)
        assert emitter.name == "test"
        assert emitter.has_event_bus()
        assert emitter._event_bus is event_bus

    def test_parent_init_not_interfered(self):
        """Test that parent __init__ is properly called."""
        emitter = MultiInheritanceEmitter(name="parent_test")
        # Parent's __init__ should have been called
        assert hasattr(emitter, "name")
        assert emitter.name == "parent_test"


class TestEventEmission:
    """Test event emission functionality."""

    @pytest.mark.asyncio
    async def test_emit_publishes_to_bus(self, event_bus, event_collector):
        """Test that emit() publishes events to the event bus."""
        # Subscribe to test events
        event_bus.subscribe("test.event", event_collector)

        # Create emitter and emit event
        emitter = SimpleEmitter(event_bus=event_bus)
        test_event = TestEvent(message="test message")
        await emitter.emit(test_event)

        # Give event bus time to process
        await asyncio.sleep(0.1)

        # Verify event was received
        assert len(event_collector.events) == 1
        assert event_collector.events[0].message == "test message"

    @pytest.mark.asyncio
    async def test_events_reach_subscribers(self, event_bus, event_collector):
        """Test that events reach all subscribers."""
        # Subscribe to multiple event types
        event_bus.subscribe("test.event", event_collector)
        event_bus.subscribe("test.request", event_collector)

        emitter = SimpleEmitter(event_bus=event_bus)

        # Emit different event types
        await emitter.emit(TestEvent(message="first"))
        await emitter.emit(RequestEvent(data="second"))

        # Wait for processing
        await asyncio.sleep(0.1)

        # Should receive both events
        assert len(event_collector.events) == 2
        assert event_collector.events[0].event_type == "test.event"
        assert event_collector.events[1].event_type == "test.request"

    @pytest.mark.asyncio
    async def test_non_blocking_emission(self, event_bus):
        """Test that emit() is non-blocking."""
        slow_events = []

        async def slow_handler(event: BaseEvent):
            await asyncio.sleep(0.5)  # Slow handler
            slow_events.append(event)

        event_bus.subscribe("test.event", slow_handler)

        emitter = SimpleEmitter(event_bus=event_bus)

        # Emit should return immediately even with slow handler
        start = asyncio.get_event_loop().time()
        await emitter.emit(TestEvent(message="test"))
        elapsed = asyncio.get_event_loop().time() - start

        # Should complete quickly (not wait for handler)
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_multiple_subscribers_receive_event(self, event_bus):
        """Test that multiple subscribers receive the same event."""
        collector1_events = []
        collector2_events = []

        async def collector1(event: BaseEvent):
            collector1_events.append(event)

        async def collector2(event: BaseEvent):
            collector2_events.append(event)

        event_bus.subscribe("test.event", collector1)
        event_bus.subscribe("test.event", collector2)

        emitter = SimpleEmitter(event_bus=event_bus)
        await emitter.emit(TestEvent(message="broadcast"))

        await asyncio.sleep(0.1)

        # Both collectors should receive the event
        assert len(collector1_events) == 1
        assert len(collector2_events) == 1
        assert collector1_events[0].message == "broadcast"
        assert collector2_events[0].message == "broadcast"


class TestAutoFillRequestID:
    """Test automatic request_id filling from context."""

    @pytest.mark.asyncio
    async def test_auto_fill_from_context(self, event_bus, event_collector):
        """Test that request_id is auto-filled from context."""
        event_bus.subscribe("test.event", event_collector)

        context = MockContext(request_id="req-123")
        emitter = EmitterWithContext(context=context, event_bus=event_bus)

        # Emit event without request_id
        event = TestEvent(message="test")
        assert event.request_id is None

        await emitter.emit(event)
        await asyncio.sleep(0.1)

        # Event should have request_id from context
        assert event_collector.events[0].request_id == "req-123"

    @pytest.mark.asyncio
    async def test_does_not_override_existing_request_id(self, event_bus, event_collector):
        """Test that existing request_id is not overridden."""
        event_bus.subscribe("test.event", event_collector)

        context = MockContext(request_id="req-context")
        emitter = EmitterWithContext(context=context, event_bus=event_bus)

        # Emit event with explicit request_id
        event = TestEvent(message="test", request_id="req-explicit")
        await emitter.emit(event)
        await asyncio.sleep(0.1)

        # Should keep original request_id
        assert event_collector.events[0].request_id == "req-explicit"

    @pytest.mark.asyncio
    async def test_works_without_context(self, event_bus, event_collector):
        """Test that emission works without context attribute."""
        event_bus.subscribe("test.event", event_collector)

        emitter = EmitterWithoutContext(event_bus=event_bus)

        # Should not raise error
        event = TestEvent(message="test")
        await emitter.emit(event)
        await asyncio.sleep(0.1)

        # Event should be emitted successfully
        assert len(event_collector.events) == 1
        assert event_collector.events[0].request_id is None

    @pytest.mark.asyncio
    async def test_context_without_request_id(self, event_bus, event_collector):
        """Test handling of context without request_id attribute."""
        event_bus.subscribe("test.event", event_collector)

        class BadContext:
            pass

        emitter = EmitterWithContext(context=BadContext(), event_bus=event_bus)

        # Should handle missing request_id gracefully
        event = TestEvent(message="test")
        await emitter.emit(event)
        await asyncio.sleep(0.1)

        assert len(event_collector.events) == 1
        assert event_collector.events[0].request_id is None


class TestEventBusConfiguration:
    """Test event bus configuration methods."""

    def test_set_event_bus(self):
        """Test set_event_bus() updates the bus."""
        emitter = SimpleEmitter()
        assert not emitter.has_event_bus()

        bus = AsyncEventBus()
        emitter.set_event_bus(bus)

        assert emitter.has_event_bus()
        assert emitter._event_bus is bus

    def test_has_event_bus_correct_status(self, event_bus):
        """Test has_event_bus() returns correct status."""
        # Without bus
        emitter1 = SimpleEmitter()
        assert not emitter1.has_event_bus()

        # With bus
        emitter2 = SimpleEmitter(event_bus=event_bus)
        assert emitter2.has_event_bus()

    def test_set_event_bus_replaces_existing(self, event_bus):
        """Test that set_event_bus() replaces existing bus."""
        emitter = SimpleEmitter(event_bus=event_bus)
        assert emitter._event_bus is event_bus

        new_bus = AsyncEventBus()
        emitter.set_event_bus(new_bus)

        assert emitter._event_bus is new_bus
        assert emitter._event_bus is not event_bus

    @pytest.mark.asyncio
    async def test_emit_with_none_event_bus(self):
        """Test that emit with None event_bus silently skips."""
        emitter = SimpleEmitter(event_bus=None)

        # Should not raise error
        event = TestEvent(message="test")
        await emitter.emit(event)  # Should complete without error

    @pytest.mark.asyncio
    async def test_emit_without_event_bus_configured(self):
        """Test emit without any event bus configured."""
        emitter = SimpleEmitter()
        assert not emitter.has_event_bus()

        # Should not raise error, silently skip
        event = TestEvent(message="test")
        await emitter.emit(event)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_emit_without_event_bus_configured(self):
        """Test emit without event bus configured."""
        emitter = SimpleEmitter()

        # Should not raise error
        await emitter.emit(TestEvent(message="test"))
        # If we get here without exception, test passes

    @pytest.mark.asyncio
    async def test_multiple_emits_in_sequence(self, event_bus, event_collector):
        """Test multiple emissions in sequence."""
        event_bus.subscribe("test.event", event_collector)
        emitter = SimpleEmitter(event_bus=event_bus)

        # Emit multiple events
        for i in range(10):
            await emitter.emit(TestEvent(message=f"event-{i}"))

        await asyncio.sleep(0.2)

        # All events should be received
        assert len(event_collector.events) == 10
        for i in range(10):
            assert event_collector.events[i].message == f"event-{i}"

    @pytest.mark.asyncio
    async def test_concurrent_emissions_same_instance(self, event_bus, event_collector):
        """Test concurrent emissions from the same emitter instance."""
        event_bus.subscribe("test.event", event_collector)
        emitter = SimpleEmitter(event_bus=event_bus)

        # Emit events concurrently
        tasks = [
            emitter.emit(TestEvent(message=f"concurrent-{i}")) for i in range(20)
        ]
        await asyncio.gather(*tasks)

        await asyncio.sleep(0.2)

        # All events should be received
        assert len(event_collector.events) == 20

    @pytest.mark.asyncio
    async def test_concurrent_emissions_different_instances(
        self, event_bus, event_collector
    ):
        """Test concurrent emissions from different emitter instances."""
        event_bus.subscribe("test.event", event_collector)

        # Create multiple emitters
        emitters = [SimpleEmitter(event_bus=event_bus) for _ in range(5)]

        # Each emitter emits multiple events concurrently
        tasks = []
        for i, emitter in enumerate(emitters):
            for j in range(4):
                tasks.append(emitter.emit(TestEvent(message=f"emitter-{i}-event-{j}")))

        await asyncio.gather(*tasks)
        await asyncio.sleep(0.2)

        # Should receive all events (5 emitters * 4 events each)
        assert len(event_collector.events) == 20

    @pytest.mark.asyncio
    async def test_emit_with_failing_subscriber(self, event_bus, event_collector):
        """Test that emission continues even if subscriber fails."""

        async def failing_handler(event: BaseEvent):
            raise Exception("Handler failed")

        # Subscribe both failing and working handlers
        event_bus.subscribe("test.event", failing_handler)
        event_bus.subscribe("test.event", event_collector)

        emitter = SimpleEmitter(event_bus=event_bus)
        await emitter.emit(TestEvent(message="test"))

        await asyncio.sleep(0.1)

        # Working handler should still receive event
        assert len(event_collector.events) == 1

    @pytest.mark.asyncio
    async def test_rapid_bus_reconfiguration(self, event_bus):
        """Test rapidly changing event bus configuration."""
        emitter = SimpleEmitter(event_bus=event_bus)

        # Rapidly change bus configuration
        for _ in range(10):
            new_bus = AsyncEventBus()
            emitter.set_event_bus(new_bus)
            await emitter.emit(TestEvent(message="test"))

        # Should complete without error

    @pytest.mark.asyncio
    async def test_emit_with_event_id_preserved(self, event_bus, event_collector):
        """Test that event_id is preserved during emission."""
        event_bus.subscribe("test.event", event_collector)
        emitter = SimpleEmitter(event_bus=event_bus)

        event = TestEvent(message="test", event_id="custom-event-id")
        await emitter.emit(event)

        await asyncio.sleep(0.1)

        # Event ID should be preserved
        assert event_collector.events[0].event_id == "custom-event-id"

    @pytest.mark.asyncio
    async def test_emit_with_metadata(self, event_bus, event_collector):
        """Test emission of events with metadata."""
        event_bus.subscribe("test.event", event_collector)
        emitter = SimpleEmitter(event_bus=event_bus)

        event = TestEvent(
            message="test", metadata={"key1": "value1", "key2": 123, "key3": True}
        )
        await emitter.emit(event)

        await asyncio.sleep(0.1)

        # Metadata should be preserved
        assert event_collector.events[0].metadata == {
            "key1": "value1",
            "key2": 123,
            "key3": True,
        }

    @pytest.mark.asyncio
    async def test_wildcard_subscriber_receives_events(self, event_bus):
        """Test that wildcard (*) subscribers receive all events."""
        wildcard_events = []

        async def wildcard_handler(event: BaseEvent):
            wildcard_events.append(event)

        # Subscribe to all events with wildcard
        event_bus.subscribe("*", wildcard_handler)

        emitter = SimpleEmitter(event_bus=event_bus)

        # Emit different event types
        await emitter.emit(TestEvent(message="test1"))
        await emitter.emit(RequestEvent(data="test2"))

        await asyncio.sleep(0.1)

        # Wildcard handler should receive both
        assert len(wildcard_events) == 2


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_handler_lifecycle_scenario(self, event_bus, event_collector):
        """Test realistic handler lifecycle with events."""
        event_bus.subscribe("request.started", event_collector)
        event_bus.subscribe("request.processing", event_collector)
        event_bus.subscribe("request.completed", event_collector)

        context = MockContext(request_id="req-integration")
        emitter = EmitterWithContext(context=context, event_bus=event_bus)

        # Simulate request lifecycle
        await emitter.emit(
            BaseEvent(event_type="request.started", metadata={"method": "POST"})
        )
        await emitter.emit(
            BaseEvent(event_type="request.processing", metadata={"step": 1})
        )
        await emitter.emit(
            BaseEvent(event_type="request.processing", metadata={"step": 2})
        )
        await emitter.emit(
            BaseEvent(event_type="request.completed", metadata={"status": "success"})
        )

        await asyncio.sleep(0.2)

        # All events should be received with request_id
        assert len(event_collector.events) == 4
        for event in event_collector.events:
            assert event.request_id == "req-integration"

    @pytest.mark.asyncio
    async def test_multiple_emitters_different_contexts(self, event_bus, event_collector):
        """Test multiple emitters with different contexts."""
        event_bus.subscribe("test.event", event_collector)

        # Create multiple emitters with different contexts
        emitter1 = EmitterWithContext(
            context=MockContext(request_id="req-1"), event_bus=event_bus
        )
        emitter2 = EmitterWithContext(
            context=MockContext(request_id="req-2"), event_bus=event_bus
        )
        emitter3 = EmitterWithContext(
            context=MockContext(request_id="req-3"), event_bus=event_bus
        )

        # Emit from different emitters
        await emitter1.emit(TestEvent(message="from-1"))
        await emitter2.emit(TestEvent(message="from-2"))
        await emitter3.emit(TestEvent(message="from-3"))

        await asyncio.sleep(0.1)

        # Each event should have its emitter's request_id
        assert len(event_collector.events) == 3
        assert event_collector.events[0].request_id == "req-1"
        assert event_collector.events[1].request_id == "req-2"
        assert event_collector.events[2].request_id == "req-3"
