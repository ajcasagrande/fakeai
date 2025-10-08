"""
Comprehensive tests for handler integration with event system.

Tests the complete event emission flow from handlers:
- EndpointHandler event emission (RequestStarted, RequestCompleted, RequestFailed)
- StreamingHandler event emission (StreamStarted, StreamCompleted, tokens)
- Event bus integration with HandlerRegistry
- Request context auto-fill in events
- Error handling and event emission
"""

import asyncio
import time
from dataclasses import dataclass
from typing import AsyncGenerator
from unittest.mock import Mock

import pytest

# Import directly from modules to avoid loading the app
from fakeai.config import AppConfig
from fakeai.events.bus import AsyncEventBus
from fakeai.events.event_types import (
    RequestCompletedEvent,
    RequestFailedEvent,
    RequestStartedEvent,
    StreamCompletedEvent,
    StreamFailedEvent,
    StreamStartedEvent,
)
from fakeai.handlers.base import EndpointHandler, RequestContext, StreamingHandler
from fakeai.handlers.registry import HandlerRegistry
from fakeai.metrics import MetricsTracker

# ==============================================================================
# Mock Handlers for Testing
# ==============================================================================


@dataclass
class MockRequest:
    """Mock request with model field."""

    data: str
    model: str = "gpt-4"


@dataclass
class MockResponse:
    """Mock response with usage information."""

    result: str
    usage: "MockUsage" = None

    def __post_init__(self):
        if self.usage is None:
            self.usage = MockUsage()


@dataclass
class MockUsage:
    """Mock usage information."""

    prompt_tokens: int = 10
    completion_tokens: int = 20
    cached_tokens: int = 5


class MockEndpointHandler(EndpointHandler[MockRequest, MockResponse]):
    """Mock endpoint handler for testing."""

    def endpoint_path(self) -> str:
        return "/v1/test/endpoint"

    async def execute(self, request: MockRequest, context: RequestContext) -> MockResponse:
        # Simulate some processing
        await asyncio.sleep(0.01)
        return MockResponse(result=f"processed: {request.data}")


class FailingEndpointHandler(EndpointHandler[MockRequest, MockResponse]):
    """Handler that fails during execution."""

    def endpoint_path(self) -> str:
        return "/v1/test/failing"

    async def execute(self, request: MockRequest, context: RequestContext) -> MockResponse:
        raise ValueError("Simulated execution error")


class MockStreamingHandler(StreamingHandler[MockRequest, dict]):
    """Mock streaming handler for testing."""

    def endpoint_path(self) -> str:
        return "/v1/test/stream"

    async def execute_stream(
        self, request: MockRequest, context: RequestContext
    ) -> AsyncGenerator[dict, None]:
        """Generate streaming chunks."""
        for i in range(5):
            await asyncio.sleep(0.01)
            yield {"chunk": i, "data": request.data}


class FailingStreamingHandler(StreamingHandler[MockRequest, dict]):
    """Streaming handler that fails during streaming."""

    def endpoint_path(self) -> str:
        return "/v1/test/stream-failing"

    async def execute_stream(
        self, request: MockRequest, context: RequestContext
    ) -> AsyncGenerator[dict, None]:
        """Generate some chunks then fail."""
        yield {"chunk": 0}
        yield {"chunk": 1}
        raise RuntimeError("Stream processing error")


# ==============================================================================
# Test Fixtures
# ==============================================================================


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

    async def collect(event):
        collected_events.append(event)

    collect.events = collected_events
    return collect


@pytest.fixture
def config():
    """Create test configuration."""
    return AppConfig()


@pytest.fixture
def metrics_tracker():
    """Create test metrics tracker."""
    return MetricsTracker()


@pytest.fixture
def fastapi_request():
    """Create mock FastAPI request."""
    request = Mock()
    request.headers.get.return_value = "Bearer sk-user-testuser123"
    request.client = Mock()
    request.client.host = "127.0.0.1"
    return request


# ==============================================================================
# Test EndpointHandler Event Emission
# ==============================================================================


class TestEndpointHandlerEvents:
    """Test event emission from EndpointHandler."""

    @pytest.mark.asyncio
    async def test_handler_emits_request_started_event(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that handler emits RequestStartedEvent."""
        # Subscribe to request.started events
        event_bus.subscribe("request.started", event_collector)

        # Create handler with event bus
        handler = MockEndpointHandler(config, metrics_tracker, event_bus=event_bus)

        # Execute request
        request = MockRequest(data="test", model="gpt-4")
        response = await handler(request, fastapi_request, "req-123")

        # Wait for event processing
        await asyncio.sleep(0.1)

        # Verify RequestStartedEvent was emitted
        assert len(event_collector.events) == 1
        event = event_collector.events[0]
        assert isinstance(event, RequestStartedEvent)
        assert event.request_id == "req-123"
        assert event.endpoint == "/v1/test/endpoint"
        assert event.method == "POST"
        assert event.model == "gpt-4"
        assert event.user_id == "user-testuser123"
        assert event.client_ip == "127.0.0.1"
        assert event.streaming is False

    @pytest.mark.asyncio
    async def test_handler_emits_request_completed_event(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that handler emits RequestCompletedEvent on success."""
        # Subscribe to request.completed events
        event_bus.subscribe("request.completed", event_collector)

        handler = MockEndpointHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="test", model="gpt-4")

        response = await handler(request, fastapi_request, "req-456")
        await asyncio.sleep(0.1)

        # Verify RequestCompletedEvent was emitted
        assert len(event_collector.events) == 1
        event = event_collector.events[0]
        assert isinstance(event, RequestCompletedEvent)
        assert event.request_id == "req-456"
        assert event.endpoint == "/v1/test/endpoint"
        assert event.model == "gpt-4"
        assert event.status_code == 200
        assert event.duration_ms > 0
        assert event.input_tokens == 10
        assert event.output_tokens == 20
        assert event.cached_tokens == 5

    @pytest.mark.asyncio
    async def test_handler_emits_both_started_and_completed(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that handler emits both started and completed events."""
        # Subscribe to all request events
        event_bus.subscribe("request.started", event_collector)
        event_bus.subscribe("request.completed", event_collector)

        handler = MockEndpointHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="test", model="gpt-4")

        response = await handler(request, fastapi_request, "req-789")
        await asyncio.sleep(0.1)

        # Verify both events were emitted in order
        assert len(event_collector.events) == 2
        assert isinstance(event_collector.events[0], RequestStartedEvent)
        assert isinstance(event_collector.events[1], RequestCompletedEvent)
        assert event_collector.events[0].request_id == "req-789"
        assert event_collector.events[1].request_id == "req-789"

    @pytest.mark.asyncio
    async def test_event_fields_populated_correctly(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that all event fields are populated correctly."""
        event_bus.subscribe("request.started", event_collector)
        event_bus.subscribe("request.completed", event_collector)

        handler = MockEndpointHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="test-data", model="gpt-3.5-turbo")

        start_time = time.time()
        response = await handler(request, fastapi_request, "req-fields")
        end_time = time.time()
        await asyncio.sleep(0.1)

        # Verify started event fields
        started_event = event_collector.events[0]
        assert started_event.request_id == "req-fields"
        assert started_event.endpoint == "/v1/test/endpoint"
        assert started_event.method == "POST"
        assert started_event.model == "gpt-3.5-turbo"
        assert started_event.user_id == "user-testuser123"
        assert started_event.streaming is False
        assert start_time <= started_event.timestamp <= end_time

        # Verify completed event fields
        completed_event = event_collector.events[1]
        assert completed_event.request_id == "req-fields"
        assert completed_event.endpoint == "/v1/test/endpoint"
        assert completed_event.model == "gpt-3.5-turbo"
        assert completed_event.status_code == 200
        assert completed_event.duration_ms >= 0
        assert completed_event.input_tokens == 10
        assert completed_event.output_tokens == 20


# ==============================================================================
# Test Error Handling with Events
# ==============================================================================


class TestErrorHandlingEvents:
    """Test event emission during error scenarios."""

    @pytest.mark.asyncio
    async def test_handler_emits_request_failed_event(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that handler emits RequestFailedEvent on error."""
        event_bus.subscribe("request.failed", event_collector)

        handler = FailingEndpointHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="test", model="gpt-4")

        with pytest.raises(ValueError, match="Simulated execution error"):
            await handler(request, fastapi_request, "req-error")

        await asyncio.sleep(0.1)

        # Verify RequestFailedEvent was emitted
        assert len(event_collector.events) == 1
        event = event_collector.events[0]
        assert isinstance(event, RequestFailedEvent)
        assert event.request_id == "req-error"
        assert event.endpoint == "/v1/test/failing"
        assert event.error_type == "ValueError"
        assert event.error_message == "Simulated execution error"
        assert event.status_code == 500
        assert event.duration_ms > 0

    @pytest.mark.asyncio
    async def test_error_details_captured(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that error details are captured correctly."""
        event_bus.subscribe("request.failed", event_collector)

        handler = FailingEndpointHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="test", model="gpt-4")

        with pytest.raises(ValueError):
            await handler(request, fastapi_request, "req-details")

        await asyncio.sleep(0.1)

        event = event_collector.events[0]
        assert "ValueError" in event.error_type
        assert "Simulated execution error" in event.error_message
        assert event.model == "gpt-4"

    @pytest.mark.asyncio
    async def test_started_event_emitted_before_failure(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that started event is emitted even if handler fails."""
        event_bus.subscribe("request.started", event_collector)
        event_bus.subscribe("request.failed", event_collector)

        handler = FailingEndpointHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="test", model="gpt-4")

        with pytest.raises(ValueError):
            await handler(request, fastapi_request, "req-fail-order")

        await asyncio.sleep(0.1)

        # Both events should be emitted
        assert len(event_collector.events) == 2
        assert isinstance(event_collector.events[0], RequestStartedEvent)
        assert isinstance(event_collector.events[1], RequestFailedEvent)
        assert event_collector.events[0].request_id == "req-fail-order"
        assert event_collector.events[1].request_id == "req-fail-order"


# ==============================================================================
# Test StreamingHandler Event Emission
# ==============================================================================


class TestStreamingHandlerEvents:
    """Test event emission from StreamingHandler."""

    @pytest.mark.asyncio
    async def test_streaming_handler_emits_request_started(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that streaming handler emits RequestStartedEvent."""
        event_bus.subscribe("request.started", event_collector)

        handler = MockStreamingHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="stream", model="gpt-4")

        # Consume stream
        async for chunk in handler(request, fastapi_request, "req-stream"):
            pass

        await asyncio.sleep(0.1)

        # Verify started event
        assert len(event_collector.events) == 1
        event = event_collector.events[0]
        assert isinstance(event, RequestStartedEvent)
        assert event.request_id == "req-stream"
        assert event.streaming is True

    @pytest.mark.asyncio
    async def test_streaming_handler_emits_stream_started(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that streaming handler emits StreamStartedEvent."""
        event_bus.subscribe("stream.started", event_collector)

        handler = MockStreamingHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="stream", model="gpt-4")

        async for chunk in handler(request, fastapi_request, "req-stream-2"):
            pass

        await asyncio.sleep(0.1)

        # Verify stream started event
        assert len(event_collector.events) == 1
        event = event_collector.events[0]
        assert isinstance(event, StreamStartedEvent)
        assert event.request_id == "req-stream-2"
        assert event.stream_id == "req-stream-2"
        assert event.endpoint == "/v1/test/stream"
        assert event.model == "gpt-4"

    @pytest.mark.asyncio
    async def test_streaming_handler_emits_stream_completed(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that streaming handler emits StreamCompletedEvent."""
        event_bus.subscribe("stream.completed", event_collector)

        handler = MockStreamingHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="stream", model="gpt-4")

        chunk_count = 0
        async for chunk in handler(request, fastapi_request, "req-stream-3"):
            chunk_count += 1

        await asyncio.sleep(0.1)

        # Verify stream completed event
        assert len(event_collector.events) == 1
        event = event_collector.events[0]
        assert isinstance(event, StreamCompletedEvent)
        assert event.request_id == "req-stream-3"
        assert event.stream_id == "req-stream-3"
        assert event.token_count == chunk_count
        assert event.finish_reason == "stop"
        assert event.duration_ms > 0

    @pytest.mark.asyncio
    async def test_streaming_emits_all_lifecycle_events(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that streaming emits all lifecycle events in order."""
        event_bus.subscribe("request.started", event_collector)
        event_bus.subscribe("stream.started", event_collector)
        event_bus.subscribe("stream.completed", event_collector)

        handler = MockStreamingHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="stream", model="gpt-4")

        async for chunk in handler(request, fastapi_request, "req-lifecycle"):
            pass

        await asyncio.sleep(0.1)

        # Verify all three events
        assert len(event_collector.events) == 3
        assert isinstance(event_collector.events[0], RequestStartedEvent)
        assert isinstance(event_collector.events[1], StreamStartedEvent)
        assert isinstance(event_collector.events[2], StreamCompletedEvent)

        # All should have same request_id
        for event in event_collector.events:
            assert event.request_id == "req-lifecycle"

    @pytest.mark.asyncio
    async def test_streaming_handler_tracks_chunk_count(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that streaming tracks chunk count correctly."""
        event_bus.subscribe("stream.completed", event_collector)

        handler = MockStreamingHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="stream", model="gpt-4")

        chunks = []
        async for chunk in handler(request, fastapi_request, "req-chunks"):
            chunks.append(chunk)

        await asyncio.sleep(0.1)

        # Verify chunk count matches
        event = event_collector.events[0]
        assert event.token_count == len(chunks)
        assert event.token_count == 5  # MockStreamingHandler yields 5 chunks

    @pytest.mark.asyncio
    async def test_streaming_handler_error_emits_failed_event(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that streaming handler emits StreamFailedEvent on error."""
        event_bus.subscribe("stream.failed", event_collector)

        handler = FailingStreamingHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="stream", model="gpt-4")

        with pytest.raises(RuntimeError, match="Stream processing error"):
            async for chunk in handler(request, fastapi_request, "req-stream-fail"):
                pass

        await asyncio.sleep(0.1)

        # Verify stream failed event
        assert len(event_collector.events) == 1
        event = event_collector.events[0]
        assert isinstance(event, StreamFailedEvent)
        assert event.request_id == "req-stream-fail"
        assert event.stream_id == "req-stream-fail"
        assert "Stream processing error" in event.error_message
        assert event.token_count == 2  # 2 chunks were yielded before failure


# ==============================================================================
# Test Event Bus Integration
# ==============================================================================


class TestEventBusIntegration:
    """Test integration between handlers and event bus."""

    @pytest.mark.asyncio
    async def test_handler_receives_event_bus_in_init(
        self, config, metrics_tracker, event_bus
    ):
        """Test that handler receives and stores event bus."""
        handler = MockEndpointHandler(config, metrics_tracker, event_bus=event_bus)

        assert handler._event_bus is event_bus
        assert handler.has_event_bus()

    @pytest.mark.asyncio
    async def test_handler_works_without_event_bus(
        self, config, metrics_tracker, fastapi_request
    ):
        """Test that handler works without event bus (backward compatibility)."""
        handler = MockEndpointHandler(config, metrics_tracker, event_bus=None)

        assert not handler.has_event_bus()

        # Should still work, just without events
        request = MockRequest(data="test", model="gpt-4")
        response = await handler(request, fastapi_request, "req-no-bus")

        assert response.result == "processed: test"

    @pytest.mark.asyncio
    async def test_set_event_bus_updates_bus(self, config, metrics_tracker, event_bus):
        """Test that set_event_bus() updates the event bus."""
        handler = MockEndpointHandler(config, metrics_tracker, event_bus=None)
        assert not handler.has_event_bus()

        handler.set_event_bus(event_bus)
        assert handler.has_event_bus()
        assert handler._event_bus is event_bus

    @pytest.mark.asyncio
    async def test_event_emitter_mixin_works(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that EventEmitterMixin integration works."""
        event_bus.subscribe("request.started", event_collector)

        handler = MockEndpointHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="test", model="gpt-4")

        # Handler uses emit() from EventEmitterMixin
        await handler(request, fastapi_request, "req-mixin")
        await asyncio.sleep(0.1)

        # Event should be emitted
        assert len(event_collector.events) == 1


# ==============================================================================
# Test Request Context Auto-Fill
# ==============================================================================


class TestRequestContextAutoFill:
    """Test automatic request context population in events."""

    @pytest.mark.asyncio
    async def test_request_id_auto_filled(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that request_id is auto-filled in events."""
        event_bus.subscribe("request.started", event_collector)

        handler = MockEndpointHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="test", model="gpt-4")

        await handler(request, fastapi_request, "req-auto-123")
        await asyncio.sleep(0.1)

        event = event_collector.events[0]
        assert event.request_id == "req-auto-123"

    @pytest.mark.asyncio
    async def test_endpoint_extracted_correctly(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that endpoint is extracted from handler."""
        event_bus.subscribe("request.started", event_collector)

        handler = MockEndpointHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="test", model="gpt-4")

        await handler(request, fastapi_request, "req-endpoint")
        await asyncio.sleep(0.1)

        event = event_collector.events[0]
        assert event.endpoint == "/v1/test/endpoint"

    @pytest.mark.asyncio
    async def test_user_id_extracted_from_auth(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that user_id is extracted from authorization header."""
        event_bus.subscribe("request.started", event_collector)

        # Set auth header
        fastapi_request.headers.get.return_value = "Bearer sk-user-alice123"

        handler = MockEndpointHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="test", model="gpt-4")

        await handler(request, fastapi_request, "req-user")
        await asyncio.sleep(0.1)

        event = event_collector.events[0]
        assert event.user_id == "user-alice123"

    @pytest.mark.asyncio
    async def test_model_extracted_from_request(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that model is extracted from request."""
        event_bus.subscribe("request.started", event_collector)

        handler = MockEndpointHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="test", model="gpt-3.5-turbo")

        await handler(request, fastapi_request, "req-model")
        await asyncio.sleep(0.1)

        event = event_collector.events[0]
        assert event.model == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_client_ip_extracted(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that client IP is extracted from request."""
        event_bus.subscribe("request.started", event_collector)

        fastapi_request.client.host = "192.168.1.100"

        handler = MockEndpointHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="test", model="gpt-4")

        await handler(request, fastapi_request, "req-ip")
        await asyncio.sleep(0.1)

        event = event_collector.events[0]
        assert event.client_ip == "192.168.1.100"


# ==============================================================================
# Test Registry Integration
# ==============================================================================


class TestRegistryIntegration:
    """Test integration between HandlerRegistry and event bus."""

    @pytest.mark.asyncio
    async def test_registry_passes_event_bus_to_handler(
        self, config, metrics_tracker, event_bus
    ):
        """Test that registry passes event_bus to handlers."""
        registry = HandlerRegistry()
        registry.register(MockEndpointHandler)

        # Get handler with event bus
        handler = registry.get_handler(
            "/v1/test/endpoint",
            config=config,
            metrics_tracker=metrics_tracker,
            event_bus=event_bus,
        )

        assert handler is not None
        assert handler.has_event_bus()
        assert handler._event_bus is event_bus

    @pytest.mark.asyncio
    async def test_registry_instantiates_handlers_with_event_bus(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that handlers instantiated by registry can emit events."""
        event_bus.subscribe("request.started", event_collector)

        registry = HandlerRegistry()
        registry.register(MockEndpointHandler)

        handler = registry.get_handler(
            "/v1/test/endpoint",
            config=config,
            metrics_tracker=metrics_tracker,
            event_bus=event_bus,
        )

        request = MockRequest(data="test", model="gpt-4")
        await handler(request, fastapi_request, "req-registry")
        await asyncio.sleep(0.1)

        # Event should be emitted
        assert len(event_collector.events) == 1
        assert event_collector.events[0].request_id == "req-registry"

    @pytest.mark.asyncio
    async def test_multiple_handlers_share_same_bus(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that multiple handlers can share the same event bus."""
        event_bus.subscribe("request.started", event_collector)

        registry = HandlerRegistry()
        registry.register(MockEndpointHandler)
        registry.register(MockStreamingHandler)

        handler1 = registry.get_handler(
            "/v1/test/endpoint",
            config=config,
            metrics_tracker=metrics_tracker,
            event_bus=event_bus,
        )
        handler2 = registry.get_handler(
            "/v1/test/stream",
            config=config,
            metrics_tracker=metrics_tracker,
            event_bus=event_bus,
        )

        # Both handlers share the same bus
        assert handler1._event_bus is event_bus
        assert handler2._event_bus is event_bus

        # Both can emit events
        request = MockRequest(data="test", model="gpt-4")
        await handler1(request, fastapi_request, "req-1")
        async for chunk in handler2(request, fastapi_request, "req-2"):
            pass

        await asyncio.sleep(0.1)

        # Both events received
        assert len(event_collector.events) == 2
        assert event_collector.events[0].request_id == "req-1"
        assert event_collector.events[1].request_id == "req-2"

    @pytest.mark.asyncio
    async def test_registry_updates_event_bus_on_cached_handler(
        self, config, metrics_tracker, event_bus
    ):
        """Test that registry updates event bus on cached handlers."""
        registry = HandlerRegistry()
        registry.register(MockEndpointHandler)

        # Get handler first time (creates instance)
        handler1 = registry.get_handler(
            "/v1/test/endpoint",
            config=config,
            metrics_tracker=metrics_tracker,
            event_bus=None,
        )
        assert not handler1.has_event_bus()

        # Get handler second time with event bus
        handler2 = registry.get_handler(
            "/v1/test/endpoint",
            config=config,
            metrics_tracker=metrics_tracker,
            event_bus=event_bus,
        )

        # Should be same instance
        assert handler1 is handler2

        # But event bus should be updated
        assert handler2.has_event_bus()
        assert handler2._event_bus is event_bus

    def test_registry_cleanup(self):
        """Test that registry can be cleared."""
        registry = HandlerRegistry()
        registry.register(MockEndpointHandler)

        assert registry.is_registered("/v1/test/endpoint")

        registry.clear()
        assert not registry.is_registered("/v1/test/endpoint")


# ==============================================================================
# Test Edge Cases and Integration Scenarios
# ==============================================================================


class TestEdgeCasesAndIntegration:
    """Test edge cases and realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_concurrent_handler_executions_with_events(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test concurrent handler executions all emit events."""
        event_bus.subscribe("request.started", event_collector)
        event_bus.subscribe("request.completed", event_collector)

        handler = MockEndpointHandler(config, metrics_tracker, event_bus=event_bus)

        # Execute multiple requests concurrently
        tasks = []
        for i in range(10):
            request = MockRequest(data=f"test-{i}", model="gpt-4")
            tasks.append(handler(request, fastapi_request, f"req-concurrent-{i}"))

        responses = await asyncio.gather(*tasks)
        await asyncio.sleep(0.2)

        # Should receive 20 events (10 started, 10 completed)
        assert len(event_collector.events) == 20

        # Count event types
        started_events = [e for e in event_collector.events if isinstance(e, RequestStartedEvent)]
        completed_events = [e for e in event_collector.events if isinstance(e, RequestCompletedEvent)]
        assert len(started_events) == 10
        assert len(completed_events) == 10

    @pytest.mark.asyncio
    async def test_handler_with_custom_pre_process_emits_events(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that handlers with custom pre_process still emit events."""
        event_bus.subscribe("request.started", event_collector)

        handler = MockEndpointHandler(config, metrics_tracker, event_bus=event_bus)

        # Add custom pre_process
        pre_process_called = False

        async def custom_pre_process(req, ctx):
            nonlocal pre_process_called
            pre_process_called = True

        handler.pre_process = custom_pre_process

        request = MockRequest(data="test", model="gpt-4")
        await handler(request, fastapi_request, "req-custom")
        await asyncio.sleep(0.1)

        # Both pre_process and event emission should work
        assert pre_process_called
        assert len(event_collector.events) == 1

    @pytest.mark.asyncio
    async def test_streaming_with_many_chunks(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test streaming with many chunks emits correct events."""

        class LargeStreamHandler(StreamingHandler[MockRequest, dict]):
            def endpoint_path(self) -> str:
                return "/v1/test/large-stream"

            async def execute_stream(
                self, request: MockRequest, context: RequestContext
            ) -> AsyncGenerator[dict, None]:
                for i in range(100):
                    yield {"chunk": i}

        event_bus.subscribe("stream.completed", event_collector)

        handler = LargeStreamHandler(config, metrics_tracker, event_bus=event_bus)
        request = MockRequest(data="test", model="gpt-4")

        chunk_count = 0
        async for chunk in handler(request, fastapi_request, "req-large"):
            chunk_count += 1

        await asyncio.sleep(0.1)

        # Verify completed event has correct count
        assert len(event_collector.events) == 1
        event = event_collector.events[0]
        assert event.token_count == 100
        assert chunk_count == 100

    @pytest.mark.asyncio
    async def test_handler_without_model_field(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test handler with request that doesn't have model field."""

        class NoModelHandler(EndpointHandler[dict, dict]):
            def endpoint_path(self) -> str:
                return "/v1/test/no-model"

            async def execute(self, request: dict, context: RequestContext) -> dict:
                return {"result": "ok"}

        event_bus.subscribe("request.started", event_collector)

        handler = NoModelHandler(config, metrics_tracker, event_bus=event_bus)
        await handler({}, fastapi_request, "req-no-model")
        await asyncio.sleep(0.1)

        # Event should be emitted with None model
        event = event_collector.events[0]
        assert event.model is None

    @pytest.mark.asyncio
    async def test_events_contain_unique_event_ids(
        self, config, metrics_tracker, event_bus, event_collector, fastapi_request
    ):
        """Test that all events have unique event IDs."""
        event_bus.subscribe("request.started", event_collector)
        event_bus.subscribe("request.completed", event_collector)

        handler = MockEndpointHandler(config, metrics_tracker, event_bus=event_bus)

        # Execute multiple requests
        for i in range(5):
            request = MockRequest(data=f"test-{i}", model="gpt-4")
            await handler(request, fastapi_request, f"req-{i}")

        await asyncio.sleep(0.2)

        # Collect all event IDs
        event_ids = [e.event_id for e in event_collector.events]

        # All should be unique
        assert len(event_ids) == len(set(event_ids))
        assert len(event_ids) == 10  # 5 started + 5 completed
