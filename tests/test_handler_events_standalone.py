#!/usr/bin/env python3
"""
Standalone test for handler event integration.
Run directly without pytest to avoid conftest issues.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataclasses import dataclass
from typing import AsyncGenerator
from unittest.mock import Mock

from fakeai.config.__init__ import AppConfig

# Import directly from submodules
from fakeai.events.base import BaseEvent
from fakeai.events.bus import AsyncEventBus
from fakeai.events.event_types import (
    RequestCompletedEvent,
    RequestFailedEvent,
    RequestStartedEvent,
    StreamCompletedEvent,
    StreamStartedEvent,
)
from fakeai.handlers.base import EndpointHandler, RequestContext, StreamingHandler
from fakeai.metrics import MetricsTracker


# Mock request/response
@dataclass
class TestRequest:
    data: str
    model: str = "gpt-4"


@dataclass
class TestResponse:
    result: str


# Mock handler
class TestHandler(EndpointHandler[TestRequest, TestResponse]):
    def endpoint_path(self) -> str:
        return "/v1/test"

    async def execute(self, request: TestRequest, context: RequestContext) -> TestResponse:
        await asyncio.sleep(0.01)
        return TestResponse(result=f"processed: {request.data}")


# Mock streaming handler
class TestStreamHandler(StreamingHandler[TestRequest, dict]):
    def endpoint_path(self) -> str:
        return "/v1/test/stream"

    async def execute_stream(
        self, request: TestRequest, context: RequestContext
    ) -> AsyncGenerator[dict, None]:
        for i in range(3):
            await asyncio.sleep(0.01)
            yield {"chunk": i}


# Event collector
class EventCollector:
    def __init__(self):
        self.events = []

    async def collect(self, event: BaseEvent):
        self.events.append(event)


async def test_endpoint_handler_events():
    """Test that EndpointHandler emits events."""
    print("\n=== Testing EndpointHandler Events ===")

    # Create event bus
    bus = AsyncEventBus(max_queue_size=100)
    await bus.start()

    # Create collector
    collector = EventCollector()
    bus.subscribe("request.started", collector.collect)
    bus.subscribe("request.completed", collector.collect)

    # Create handler
    config = AppConfig()
    metrics = MetricsTracker()
    handler = TestHandler(config, metrics, event_bus=bus)

    # Create mock FastAPI request
    fastapi_request = Mock()
    fastapi_request.headers.get.return_value = "Bearer sk-user-test123"
    fastapi_request.client = Mock()
    fastapi_request.client.host = "127.0.0.1"

    # Execute handler
    request = TestRequest(data="test", model="gpt-4")
    response = await handler(request, fastapi_request, "req-001")

    # Wait for events
    await asyncio.sleep(0.2)

    # Verify events
    assert len(collector.events) == 2, f"Expected 2 events, got {len(collector.events)}"
    assert isinstance(collector.events[0], RequestStartedEvent)
    assert isinstance(collector.events[1], RequestCompletedEvent)
    assert collector.events[0].request_id == "req-001"
    assert collector.events[1].request_id == "req-001"

    await bus.stop(timeout=2.0)
    print("✓ EndpointHandler events test passed")


async def test_streaming_handler_events():
    """Test that StreamingHandler emits events."""
    print("\n=== Testing StreamingHandler Events ===")

    # Create event bus
    bus = AsyncEventBus(max_queue_size=100)
    await bus.start()

    # Create collector
    collector = EventCollector()
    bus.subscribe("request.started", collector.collect)
    bus.subscribe("stream.started", collector.collect)
    bus.subscribe("stream.completed", collector.collect)

    # Create handler
    config = AppConfig()
    metrics = MetricsTracker()
    handler = TestStreamHandler(config, metrics, event_bus=bus)

    # Create mock FastAPI request
    fastapi_request = Mock()
    fastapi_request.headers.get.return_value = "Bearer sk-user-test456"
    fastapi_request.client = Mock()
    fastapi_request.client.host = "127.0.0.1"

    # Execute handler
    request = TestRequest(data="stream", model="gpt-4")
    chunks = []
    async for chunk in handler(request, fastapi_request, "req-002"):
        chunks.append(chunk)

    # Wait for events
    await asyncio.sleep(0.2)

    # Verify events
    assert len(collector.events) == 3, f"Expected 3 events, got {len(collector.events)}"
    assert isinstance(collector.events[0], RequestStartedEvent)
    assert isinstance(collector.events[1], StreamStartedEvent)
    assert isinstance(collector.events[2], StreamCompletedEvent)
    assert collector.events[0].streaming is True
    assert len(chunks) == 3

    await bus.stop(timeout=2.0)
    print("✓ StreamingHandler events test passed")


async def test_error_handling():
    """Test that errors emit RequestFailedEvent."""
    print("\n=== Testing Error Handling Events ===")

    class FailingHandler(EndpointHandler[TestRequest, TestResponse]):
        def endpoint_path(self) -> str:
            return "/v1/test/fail"

        async def execute(self, request: TestRequest, context: RequestContext) -> TestResponse:
            raise ValueError("Test error")

    # Create event bus
    bus = AsyncEventBus(max_queue_size=100)
    await bus.start()

    # Create collector
    collector = EventCollector()
    bus.subscribe("request.failed", collector.collect)

    # Create handler
    config = AppConfig()
    metrics = MetricsTracker()
    handler = FailingHandler(config, metrics, event_bus=bus)

    # Create mock FastAPI request
    fastapi_request = Mock()
    fastapi_request.headers.get.return_value = "Bearer sk-user-test789"
    fastapi_request.client = Mock()
    fastapi_request.client.host = "127.0.0.1"

    # Execute handler (should fail)
    request = TestRequest(data="test", model="gpt-4")
    try:
        await handler(request, fastapi_request, "req-003")
        assert False, "Handler should have failed"
    except ValueError:
        pass

    # Wait for events
    await asyncio.sleep(0.2)

    # Verify events
    assert len(collector.events) == 1, f"Expected 1 event, got {len(collector.events)}"
    assert isinstance(collector.events[0], RequestFailedEvent)
    assert collector.events[0].request_id == "req-003"
    assert collector.events[0].error_type == "ValueError"
    assert "Test error" in collector.events[0].error_message

    await bus.stop(timeout=2.0)
    print("✓ Error handling events test passed")


async def test_request_context_autofill():
    """Test that request context is auto-filled in events."""
    print("\n=== Testing Request Context Auto-Fill ===")

    # Create event bus
    bus = AsyncEventBus(max_queue_size=100)
    await bus.start()

    # Create collector
    collector = EventCollector()
    bus.subscribe("request.started", collector.collect)

    # Create handler
    config = AppConfig()
    metrics = MetricsTracker()
    handler = TestHandler(config, metrics, event_bus=bus)

    # Create mock FastAPI request with custom auth
    fastapi_request = Mock()
    fastapi_request.headers.get.return_value = "Bearer sk-user-alice999"
    fastapi_request.client = Mock()
    fastapi_request.client.host = "192.168.1.100"

    # Execute handler
    request = TestRequest(data="test", model="gpt-3.5-turbo")
    await handler(request, fastapi_request, "req-context")

    # Wait for events
    await asyncio.sleep(0.2)

    # Verify event fields
    event = collector.events[0]
    assert event.request_id == "req-context"
    assert event.endpoint == "/v1/test"
    assert event.model == "gpt-3.5-turbo"
    assert event.user_id == "user-alice999"
    assert event.client_ip == "192.168.1.100"

    await bus.stop(timeout=2.0)
    print("✓ Request context auto-fill test passed")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Handler Event Integration Tests (Standalone)")
    print("=" * 60)

    try:
        await test_endpoint_handler_events()
        await test_streaming_handler_events()
        await test_error_handling()
        await test_request_context_autofill()

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
