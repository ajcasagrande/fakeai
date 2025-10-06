# Handler Framework - Quick Reference

A cheat sheet for implementing new endpoint handlers in FakeAI.

## Quick Start

### 1. Create Handler File

```bash
touch fakeai/handlers/my_handler.py
touch tests/test_handlers/test_my_handler.py
```

### 2. Basic Handler Template

```python
"""My handler module."""
from fakeai.handlers.base import EndpointHandler, RequestContext
from fakeai.handlers.registry import register_handler
from fakeai.models import MyRequest, MyResponse


@register_handler("/v1/my/endpoint")
class MyHandler(EndpointHandler[MyRequest, MyResponse]):
    """Handler for my endpoint."""

    def get_endpoint_name(self) -> str:
        """Return endpoint name for metrics."""
        return "/v1/my/endpoint"

    async def execute(
        self,
        request: MyRequest,
        context: RequestContext,
    ) -> MyResponse:
        """
        Execute request logic.

        Args:
            request: Validated request object
            context: Request context with metadata

        Returns:
            Response object
        """
        # Delegate to service
        response = await self.service.my_method(request)

        # Store in context for post-processing
        context.metadata["response"] = response

        return response

    async def post_process(
        self,
        request: MyRequest,
        response: MyResponse,
        context: RequestContext,
    ) -> None:
        """Track metrics after successful completion."""
        await super().post_process(request, response, context)

        # Track per-model metrics
        self.model_metrics_tracker.track_request(
            model=request.model,
            endpoint=self.get_endpoint_name(),
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            latency_ms=context.elapsed_ms(),
            user=self.extract_user_from_auth(context.api_key),
            error=False,
        )
```

### 3. Streaming Handler Template

```python
"""My streaming handler module."""
from typing import AsyncGenerator
from fakeai.handlers.base import StreamingHandler, RequestContext
from fakeai.handlers.registry import register_handler
from fakeai.models import MyRequest, MyResponse, MyChunk


@register_handler("/v1/my/streaming/endpoint")
class MyStreamingHandler(StreamingHandler[MyRequest, MyResponse]):
    """Handler for streaming endpoint."""

    def get_endpoint_name(self) -> str:
        return "/v1/my/streaming/endpoint"

    async def execute(
        self,
        request: MyRequest,
        context: RequestContext,
    ) -> MyResponse:
        """Non-streaming execution."""
        return await self.service.my_method(request)

    async def execute_stream(
        self,
        request: MyRequest,
        context: RequestContext,
    ) -> AsyncGenerator[MyChunk, None]:
        """Streaming execution."""
        async for chunk in self.service.my_stream_method(request):
            yield chunk

    async def post_process_stream(
        self,
        request: MyRequest,
        context: RequestContext,
    ) -> None:
        """Track metrics after streaming completion."""
        await super().post_process_stream(request, context)

        chunk_count = context.metadata.get("chunk_count", 0)
        self.logger.info(
            f"[{context.request_id}] Stream completed: {chunk_count} chunks"
        )
```

### 4. Register in Package

```python
# fakeai/handlers/__init__.py
from fakeai.handlers import my_handler  # Import to trigger registration
```

### 5. Add Route in app.py

```python
# app.py
import fakeai.handlers.my_handler  # Import to register

@app.post("/v1/my/endpoint", dependencies=[Depends(verify_api_key)])
async def my_endpoint(
    request: MyRequest,
    fastapi_request: Request,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None
):
    """My endpoint using handler framework."""
    context = create_request_context(
        fastapi_request,
        extract_api_key(authorization)
    )

    handler = handler_registry.get_handler(
        "/v1/my/endpoint",
        service=fakeai_service,
        metrics_tracker=metrics_tracker,
        model_metrics_tracker=model_metrics_tracker,
    )

    return await handler.handle(request, context)
```

### 6. Write Tests

```python
# tests/test_handlers/test_my_handler.py
import pytest
from unittest.mock import Mock, AsyncMock
import time

from fakeai.handlers.my_handler import MyHandler
from fakeai.handlers.base import RequestContext
from fakeai.models import MyRequest, MyResponse


@pytest.fixture
def handler():
    """Create handler with mocks."""
    service = Mock()
    metrics = Mock()
    model_metrics = Mock()
    return MyHandler(service, metrics, model_metrics)


@pytest.fixture
def context():
    """Create request context."""
    return RequestContext(
        request_id="test-123",
        api_key="sk-test",
        user_id="sk-test"[:20],
        client_ip="127.0.0.1",
        start_time=time.time(),
        endpoint="/v1/my/endpoint",
    )


@pytest.mark.asyncio
async def test_my_handler(handler, context):
    """Test my handler."""
    request = MyRequest(...)
    expected = MyResponse(...)

    handler.service.my_method = AsyncMock(return_value=expected)

    response = await handler.handle(request, context)

    assert response == expected
    handler.service.my_method.assert_called_once_with(request)
```

---

## Lifecycle Hooks

### Available Hooks (Override as Needed)

```python
class MyHandler(EndpointHandler):
    async def pre_process(self, request, context):
        """Called BEFORE execute(). Use for validation, enrichment."""
        await super().pre_process(request, context)
        # Your pre-processing logic

    async def execute(self, request, context):
        """Called to execute main logic. REQUIRED."""
        return await self.service.my_method(request)

    async def post_process(self, request, response, context):
        """Called AFTER execute(). Use for metrics, logging."""
        await super().post_process(request, response, context)
        # Your post-processing logic

    async def on_error(self, error, request, context):
        """Called on exceptions. Use for error tracking."""
        await super().on_error(error, request, context)
        # Your error handling logic
```

### Streaming Hooks (StreamingHandler)

```python
class MyStreamingHandler(StreamingHandler):
    async def execute_stream(self, request, context):
        """Streaming execution. Yield chunks."""
        async for chunk in self.service.stream_method(request):
            yield chunk

    async def on_stream_start(self, request, context):
        """Called when streaming starts."""
        pass

    async def on_stream_chunk(self, chunk, request, context):
        """Called for each chunk (optional)."""
        pass

    async def on_stream_end(self, request, context):
        """Called when streaming ends."""
        pass

    async def post_process_stream(self, request, context):
        """Called after stream completes."""
        pass
```

---

## RequestContext Usage

```python
# Access request metadata
context.request_id       # Unique request ID
context.api_key          # API key (if provided)
context.user_id          # User ID derived from API key
context.client_ip        # Client IP address
context.endpoint         # Endpoint path
context.start_time       # Request start time (float)

# Calculate elapsed time
elapsed = context.elapsed_ms()  # Returns milliseconds

# Store custom metadata
context.metadata["my_key"] = "my_value"
context.metadata["chunk_count"] = 42

# Access later
value = context.metadata.get("my_key")
```

---

## Common Patterns

### Pattern 1: Extract Model from Request

```python
async def post_process(self, request, response, context):
    model = self.extract_model_from_request(request)  # Gets request.model
    # Use model...
```

### Pattern 2: Extract User from API Key

```python
async def post_process(self, request, response, context):
    user = self.extract_user_from_auth(context.api_key)  # First 20 chars
    # Use user...
```

### Pattern 3: Track Metrics

```python
async def post_process(self, request, response, context):
    await super().post_process(request, response, context)

    if response.usage:
        self.model_metrics_tracker.track_request(
            model=request.model,
            endpoint=self.get_endpoint_name(),
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            latency_ms=context.elapsed_ms(),
            user=self.extract_user_from_auth(context.api_key),
            error=False,
        )
```

### Pattern 4: Track Errors

```python
async def on_error(self, error, request, context):
    await super().on_error(error, request, context)

    # Track in model metrics
    self.model_metrics_tracker.track_request(
        model=request.model,
        endpoint=self.get_endpoint_name(),
        prompt_tokens=0,
        completion_tokens=0,
        latency_ms=context.elapsed_ms(),
        user=self.extract_user_from_auth(context.api_key),
        error=True,
    )

    # Log details
    self.logger.error(
        f"[{context.request_id}] Failed: {error}"
    )
```

### Pattern 5: Validate in pre_process

```python
async def pre_process(self, request, context):
    await super().pre_process(request, context)

    # Validate request
    if not request.messages:
        raise ValueError("Messages cannot be empty")

    # Enrich context
    context.metadata["message_count"] = len(request.messages)
    context.metadata["has_system"] = any(m.role == "system" for m in request.messages)
```

### Pattern 6: Count Streaming Chunks

```python
async def on_stream_chunk(self, chunk, request, context):
    """Track chunk count."""
    count = context.metadata.get("chunk_count", 0)
    context.metadata["chunk_count"] = count + 1
```

---

## Testing Patterns

### Pattern 1: Basic Unit Test

```python
@pytest.mark.asyncio
async def test_success(handler, context):
    """Test successful request."""
    request = MyRequest(...)
    expected = MyResponse(...)

    handler.service.method = AsyncMock(return_value=expected)

    response = await handler.handle(request, context)

    assert response == expected
```

### Pattern 2: Error Test

```python
@pytest.mark.asyncio
async def test_error(handler, context):
    """Test error handling."""
    request = MyRequest(...)
    error = ValueError("Test error")

    handler.service.method = AsyncMock(side_effect=error)

    with pytest.raises(ValueError, match="Test error"):
        await handler.handle(request, context)

    handler.metrics_tracker.track_error.assert_called_once()
```

### Pattern 3: Streaming Test

```python
@pytest.mark.asyncio
async def test_streaming(handler, context):
    """Test streaming."""
    request = MyRequest(...)

    async def mock_stream():
        yield MyChunk(content="Hello")
        yield MyChunk(content=" World")

    handler.service.stream_method = mock_stream

    chunks = []
    async for chunk in handler.handle_stream(request, context):
        chunks.append(chunk)

    assert len(chunks) == 2
    assert chunks[0].content == "Hello"
```

### Pattern 4: Metrics Test

```python
@pytest.mark.asyncio
async def test_metrics(handler, context):
    """Test metrics tracking."""
    request = MyRequest(model="test-model")
    response = MyResponse(usage=Usage(prompt_tokens=10, completion_tokens=5))

    handler.service.method = AsyncMock(return_value=response)

    await handler.handle(request, context)

    # Verify metrics tracked
    handler.model_metrics_tracker.track_request.assert_called_once()
    call_args = handler.model_metrics_tracker.track_request.call_args
    assert call_args.kwargs["model"] == "test-model"
    assert call_args.kwargs["prompt_tokens"] == 10
    assert call_args.kwargs["error"] is False
```

---

## Checklist for New Handlers

- [ ] Create handler file `fakeai/handlers/my_handler.py`
- [ ] Extend `EndpointHandler` or `StreamingHandler`
- [ ] Implement `execute()` method
- [ ] Implement `get_endpoint_name()` method
- [ ] Override hooks as needed (pre_process, post_process, on_error)
- [ ] Add `@register_handler` decorator
- [ ] Import in `fakeai/handlers/__init__.py`
- [ ] Add route in `app.py`
- [ ] Create test file `tests/test_handlers/test_my_handler.py`
- [ ] Write unit tests (>90% coverage)
- [ ] Write integration tests
- [ ] Add type hints throughout
- [ ] Add docstrings for all methods
- [ ] Format with Black
- [ ] Run linting
- [ ] Update documentation

---

## Common Mistakes

###  Don't: Forget to call super()

```python
async def post_process(self, request, response, context):
    # Missing super() call!
    self.model_metrics_tracker.track_request(...)
```

###  Do: Always call super()

```python
async def post_process(self, request, response, context):
    await super().post_process(request, response, context)
    self.model_metrics_tracker.track_request(...)
```

###  Don't: Forget @register_handler

```python
class MyHandler(EndpointHandler):  # Not registered!
    pass
```

###  Do: Use decorator

```python
@register_handler("/v1/my/endpoint")
class MyHandler(EndpointHandler):
    pass
```

###  Don't: Import handler in service

```python
# fakeai_service.py
from fakeai.handlers.my_handler import MyHandler  # Wrong!
```

###  Do: Import in app.py or handlers/__init__.py

```python
# app.py or handlers/__init__.py
import fakeai.handlers.my_handler  # Correct!
```

###  Don't: Put business logic in handler

```python
async def execute(self, request, context):
    # Don't do this!
    result = self._complex_business_logic(request)
    return result
```

###  Do: Delegate to service

```python
async def execute(self, request, context):
    # Delegate to service
    return await self.service.my_method(request)
```

---

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.getLogger("fakeai.handlers").setLevel(logging.DEBUG)
```

### Add Custom Logging

```python
async def execute(self, request, context):
    self.logger.debug(f"[{context.request_id}] Processing request: {request}")
    response = await self.service.method(request)
    self.logger.debug(f"[{context.request_id}] Got response: {response}")
    return response
```

### Inspect Context

```python
async def post_process(self, request, response, context):
    self.logger.info(f"Context metadata: {context.metadata}")
    self.logger.info(f"Elapsed: {context.elapsed_ms():.2f}ms")
```

### Test in Isolation

```python
# Test handler directly without app.py
handler = MyHandler(mock_service, mock_metrics, mock_model_metrics)
context = RequestContext(...)
result = await handler.handle(request, context)
```

---

## Performance Tips

1. **Handler Caching**: Registry caches handler instances automatically
2. **Async Throughout**: Always use `async def` for handler methods
3. **Minimal Work in Hooks**: Keep pre/post processing lightweight
4. **Delegate Heavy Work**: Put complex logic in service, not handler
5. **Avoid Blocking**: Never use blocking I/O in handlers

---

## Resources

- **Full Design**: [HANDLER_FRAMEWORK_DESIGN.md](HANDLER_FRAMEWORK_DESIGN.md)
- **Implementation Example**: [HANDLER_IMPLEMENTATION_EXAMPLE.md](HANDLER_IMPLEMENTATION_EXAMPLE.md)
- **Migration Guide**: [HANDLER_MIGRATION_GUIDE.md](HANDLER_MIGRATION_GUIDE.md)
- **Summary**: [HANDLER_FRAMEWORK_SUMMARY.md](HANDLER_FRAMEWORK_SUMMARY.md)
- **Project Standards**: [CLAUDE.md](CLAUDE.md)

---

**Questions?** Check the full documentation or ask in team chat!
