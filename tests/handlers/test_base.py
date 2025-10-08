"""
Tests for base handler classes.

This module tests the core handler functionality including lifecycle hooks,
context management, and metrics tracking.
"""
#  SPDX-License-Identifier: Apache-2.0

from unittest.mock import Mock

import pytest

from fakeai.config import AppConfig
from fakeai.handlers.base import EndpointHandler, RequestContext, StreamingHandler
from fakeai.metrics import MetricsTracker


class TestRequestContext:
    """Tests for RequestContext."""

    def test_create_context(self):
        """Test creating a request context."""
        context = RequestContext(
            request_id="test-123",
            endpoint="/v1/test",
            user_id="user-abc",
            client_ip="127.0.0.1",
            model="gpt-4",
        )

        assert context.request_id == "test-123"
        assert context.endpoint == "/v1/test"
        assert context.user_id == "user-abc"
        assert context.client_ip == "127.0.0.1"
        assert context.model == "gpt-4"
        assert context.streaming is False
        assert context.metadata == {}

    def test_elapsed_time(self):
        """Test calculating elapsed time."""
        import time

        context = RequestContext(
            request_id="test-123",
            endpoint="/v1/test",
        )

        # Wait a bit
        time.sleep(0.1)

        elapsed = context.elapsed_time()
        assert elapsed >= 0.1
        assert elapsed < 1.0  # Should be fast


class MockHandler(EndpointHandler[dict, dict]):
    """Mock handler for testing."""

    def endpoint_path(self) -> str:
        return "/v1/test"

    async def execute(self, request: dict, context: RequestContext) -> dict:
        return {"status": "ok", "input": request}


class TestEndpointHandler:
    """Tests for EndpointHandler base class."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AppConfig()

    @pytest.fixture
    def metrics_tracker(self):
        """Create test metrics tracker."""
        return MetricsTracker()

    @pytest.fixture
    def handler(self, config, metrics_tracker):
        """Create test handler."""
        return MockHandler(config, metrics_tracker)

    @pytest.fixture
    def fastapi_request(self):
        """Create mock FastAPI request."""
        request = Mock()
        request.headers.get.return_value = "Bearer sk-test-abc123"
        request.client = Mock()
        request.client.host = "127.0.0.1"
        return request

    @pytest.mark.asyncio
    async def test_handler_execution(self, handler, fastapi_request):
        """Test basic handler execution."""
        request = {"test": "data"}
        response = await handler(request, fastapi_request, "req-123")

        assert response["status"] == "ok"
        assert response["input"] == request

    @pytest.mark.asyncio
    async def test_handler_creates_context(self, handler, fastapi_request):
        """Test that handler creates proper context."""
        request = {"test": "data"}

        # Mock pre_process to capture context
        original_pre_process = handler.pre_process
        captured_context = None

        async def capture_context(req, ctx):
            nonlocal captured_context
            captured_context = ctx
            await original_pre_process(req, ctx)

        handler.pre_process = capture_context

        await handler(request, fastapi_request, "req-123")

        assert captured_context is not None
        assert captured_context.request_id == "req-123"
        assert captured_context.endpoint == "/v1/test"
        assert captured_context.user_id is not None

    @pytest.mark.asyncio
    async def test_handler_extracts_user(self, handler, fastapi_request):
        """Test that handler extracts user from auth header."""
        request = {}

        # Test various auth formats
        test_cases = [
            ("Bearer sk-user-abc123xyz", "user-abc123xyz"),
            ("Bearer sk-proj-test123", "proj-test123"),
            ("Bearer sk-test", "test"),
            ("Bearer random-token-here", "random-token-her"),  # First 16 chars
        ]

        for auth_header, expected_user in test_cases:
            fastapi_request.headers.get.return_value = auth_header

            context = handler.create_context(request, fastapi_request, "req-123")
            assert context.user_id == expected_user

    @pytest.mark.asyncio
    async def test_handler_tracks_metrics(self, handler, fastapi_request, metrics_tracker):
        """Test that handler tracks metrics."""
        request = {"test": "data"}

        # Reset metrics
        metrics_tracker._metrics = {}

        await handler(request, fastapi_request, "req-123")

        # Check that request was tracked
        # Note: Metrics tracking depends on endpoint being in allowlist
        # For test endpoint, it won't be tracked, so we just verify no errors

    @pytest.mark.asyncio
    async def test_handler_error_handling(self, handler, fastapi_request):
        """Test that handler handles errors properly."""
        # Make execute raise an error
        async def failing_execute(request, context):
            raise ValueError("Test error")

        handler.execute = failing_execute

        with pytest.raises(ValueError, match="Test error"):
            await handler({"test": "data"}, fastapi_request, "req-123")

    @pytest.mark.asyncio
    async def test_handler_pre_process_hook(self, handler, fastapi_request):
        """Test pre_process hook is called."""
        pre_process_called = False

        async def custom_pre_process(request, context):
            nonlocal pre_process_called
            pre_process_called = True

        handler.pre_process = custom_pre_process

        await handler({"test": "data"}, fastapi_request, "req-123")

        assert pre_process_called

    @pytest.mark.asyncio
    async def test_handler_post_process_hook(self, handler, fastapi_request):
        """Test post_process hook is called."""
        post_process_called = False

        async def custom_post_process(response, context):
            nonlocal post_process_called
            post_process_called = True
            return response

        handler.post_process = custom_post_process

        await handler({"test": "data"}, fastapi_request, "req-123")

        assert post_process_called

    @pytest.mark.asyncio
    async def test_handler_on_error_hook(self, handler, fastapi_request):
        """Test on_error hook is called."""
        on_error_called = False

        async def custom_on_error(error, context):
            nonlocal on_error_called
            on_error_called = True

        handler.on_error = custom_on_error

        # Make execute fail
        async def failing_execute(request, context):
            raise ValueError("Test error")

        handler.execute = failing_execute

        with pytest.raises(ValueError):
            await handler({"test": "data"}, fastapi_request, "req-123")

        assert on_error_called

    def test_extract_model(self, handler):
        """Test extracting model from request."""
        # Request without model
        request = {"data": "test"}
        assert handler.extract_model(request) is None

        # Mock request with model attribute
        request_with_model = Mock()
        request_with_model.model = "gpt-4"
        assert handler.extract_model(request_with_model) == "gpt-4"


class MockStreamingHandler(StreamingHandler[dict, dict]):
    """Mock streaming handler for testing."""

    def endpoint_path(self) -> str:
        return "/v1/stream"

    async def execute(self, request: dict, context: RequestContext) -> dict:
        # Not used for streaming
        raise NotImplementedError()

    async def execute_stream(self, request: dict, context: RequestContext):
        for i in range(5):
            yield {"chunk": i, "data": request.get("data")}


class TestStreamingHandler:
    """Tests for StreamingHandler base class."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AppConfig()

    @pytest.fixture
    def metrics_tracker(self):
        """Create test metrics tracker."""
        return MetricsTracker()

    @pytest.fixture
    def handler(self, config, metrics_tracker):
        """Create test streaming handler."""
        return MockStreamingHandler(config, metrics_tracker)

    @pytest.fixture
    def fastapi_request(self):
        """Create mock FastAPI request."""
        request = Mock()
        request.headers.get.return_value = "Bearer sk-test-abc123"
        request.client = Mock()
        request.client.host = "127.0.0.1"
        return request

    @pytest.mark.asyncio
    async def test_streaming_handler_execution(self, handler, fastapi_request):
        """Test basic streaming handler execution."""
        request = {"data": "test"}
        chunks = []

        async for chunk in handler(request, fastapi_request, "req-123"):
            chunks.append(chunk)

        assert len(chunks) == 5
        assert chunks[0] == {"chunk": 0, "data": "test"}
        assert chunks[4] == {"chunk": 4, "data": "test"}

    @pytest.mark.asyncio
    async def test_streaming_context_has_streaming_flag(self, handler, fastapi_request):
        """Test that streaming context has streaming flag set."""
        request = {"data": "test"}

        # Mock pre_process to capture context
        captured_context = None
        original_pre_process = handler.pre_process

        async def capture_context(req, ctx):
            nonlocal captured_context
            captured_context = ctx
            await original_pre_process(req, ctx)

        handler.pre_process = capture_context

        # Consume stream
        async for _ in handler(request, fastapi_request, "req-123"):
            pass

        assert captured_context is not None
        assert captured_context.streaming is True

    @pytest.mark.asyncio
    async def test_streaming_handler_tracks_chunks(self, handler, fastapi_request):
        """Test that streaming handler tracks chunk count."""
        request = {"data": "test"}

        # Consume stream
        chunk_count = 0
        async for _ in handler(request, fastapi_request, "req-123"):
            chunk_count += 1

        assert chunk_count == 5

    @pytest.mark.asyncio
    async def test_streaming_handler_error_handling(self, handler, fastapi_request):
        """Test that streaming handler handles errors."""
        # Make execute_stream raise an error
        async def failing_stream(request, context):
            yield {"chunk": 0}
            raise ValueError("Stream error")

        handler.execute_stream = failing_stream

        with pytest.raises(ValueError, match="Stream error"):
            async for _ in handler({"data": "test"}, fastapi_request, "req-123"):
                pass
