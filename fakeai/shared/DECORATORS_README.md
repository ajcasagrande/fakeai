# FakeAI Shared Decorators

A comprehensive collection of reusable decorators for common service patterns in FakeAI.

## Overview

The `fakeai.shared.decorators` module provides production-ready decorators that simplify common operations like model validation, metrics tracking, caching, retry logic, and more. These decorators follow Python best practices and can be combined for powerful behavior.

## Available Decorators

### 1. `@ensure_model_exists`

Automatically validates and creates models before method execution.

```python
from fakeai.shared.decorators import ensure_model_exists

@ensure_model_exists
async def create_chat_completion(self, request):
    # Model is guaranteed to exist here
    return {"model": request.model, "response": "..."}
```

**Features:**
- Extracts model ID from request object
- Calls `_ensure_model_exists()` method on service
- Auto-creates missing models
- No-op if model already exists

### 2. `@track_metrics(endpoint)`

Automatic metrics tracking for request latency and errors.

```python
from fakeai.shared.decorators import track_metrics

@track_metrics("chat_completions")
async def create_chat_completion(self, request):
    # Latency and errors automatically tracked
    return result
```

**Features:**
- Tracks request latency in milliseconds
- Records successful responses
- Records errors with endpoint name
- Integrates with `MetricsTracker`

### 3. `@validate_context_length(max_context)`

Validates request token count against context window limits.

```python
from fakeai.shared.decorators import validate_context_length

@validate_context_length(max_context=4096)
async def create_completion(self, request):
    # Context length validated before execution
    return result
```

**Features:**
- Counts tokens in messages and prompts
- Handles multi-modal content
- Uses config default if `max_context` not specified
- Raises `ValueError` if limit exceeded

### 4. `@retry_on_failure(max_retries, delay, backoff)`

Retry logic with exponential backoff for transient failures.

```python
from fakeai.shared.decorators import retry_on_failure

@retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
async def unstable_api_call(self):
    # Automatically retries on failure
    return result
```

**Features:**
- Exponential backoff between retries
- Configurable retry count and delays
- Logs retry attempts
- Re-raises exception after max retries

### 5. `@cache_response(ttl, key_func)`

Response caching with TTL (Time To Live).

```python
from fakeai.shared.decorators import cache_response

@cache_response(ttl=300)  # 5 minute cache
async def expensive_operation(self, param):
    # Result cached for 5 minutes
    return result

# Custom key function
@cache_response(ttl=600, key_func=lambda self, req: req.model)
async def get_model_info(self, request):
    return model_info
```

**Features:**
- Automatic cache key generation
- Custom key function support
- TTL-based expiration
- Cache statistics via `get_cache_stats()`
- Manual cache clearing via `clear_cache()`

### 6. `@log_execution(log_level, log_args)`

Automatic execution logging with entry/exit and duration.

```python
from fakeai.shared.decorators import log_execution
import logging

@log_execution(log_level=logging.INFO, log_args=True)
async def important_operation(self, param1, param2):
    # Entry, exit, and duration logged automatically
    return result
```

**Features:**
- Logs function entry and exit
- Logs execution duration in milliseconds
- Optional argument logging
- Error logging with stack traces

### 7. `@rate_limit(max_calls, time_window)`

Rate limiting for function calls.

```python
from fakeai.shared.decorators import rate_limit

@rate_limit(max_calls=10, time_window=60.0)  # 10 calls per minute
async def api_endpoint(self):
    # Rate limited to 10 calls per minute
    return result
```

**Features:**
- Sliding window rate limiting
- Raises `RuntimeError` when limit exceeded
- Automatic window expiration
- Per-function rate tracking

### 8. `@timeout(seconds)`

Enforces timeout on async function execution.

```python
from fakeai.shared.decorators import timeout

@timeout(30.0)  # 30 second timeout
async def long_running_operation(self):
    # Will timeout if takes longer than 30s
    return result
```

**Features:**
- Uses `asyncio.wait_for()`
- Raises `asyncio.TimeoutError`
- Logs timeout events
- Configurable timeout per function

### 9. `@measure_performance`

Measures and logs performance metrics.

```python
from fakeai.shared.decorators import measure_performance

@measure_performance
async def resource_intensive_task(self):
    # Performance metrics logged automatically
    return result
```

**Features:**
- Logs execution duration
- Logs memory usage (if `psutil` available)
- Detailed performance information
- No configuration required

### 10. `@validate_request(validator, error_message)`

Custom request validation with flexible validation logic.

```python
from fakeai.shared.decorators import validate_request

@validate_request(
    validator=lambda req: req.max_tokens <= 4096,
    error_message="max_tokens must be <= 4096"
)
async def create_completion(self, request):
    # Request validated before execution
    return result
```

**Features:**
- Custom validation function
- Clear error messages
- Early validation before processing
- Composable with other decorators

## Combining Decorators

Decorators can be stacked for powerful behavior:

```python
from fakeai.shared.decorators import (
    ensure_model_exists,
    track_metrics,
    cache_response,
    log_execution,
    retry_on_failure,
)

@ensure_model_exists
@track_metrics("advanced_chat")
@cache_response(ttl=300)
@log_execution(log_level=logging.DEBUG)
@retry_on_failure(max_retries=2, delay=0.5)
async def advanced_chat_completion(self, request):
    """
    This method has:
    - Model validation
    - Metrics tracking
    - Response caching
    - Execution logging
    - Retry logic
    """
    return result
```

**Note:** Order matters! Decorators are applied bottom-to-top, so innermost decorators run first.

## Best Practices

### 1. Decorator Order

Recommended order (top to bottom):
1. `@ensure_model_exists` - Model validation first
2. `@track_metrics` - Track overall request
3. `@cache_response` - Cache after validation
4. `@log_execution` - Log execution details
5. `@retry_on_failure` - Retry transient failures
6. `@validate_context_length` - Validate input
7. `@validate_request` - Custom validation
8. Business logic

### 2. Use Specific Decorators

Choose decorators based on specific needs:
- Use `@track_metrics` for all public API methods
- Use `@cache_response` for expensive, idempotent operations
- Use `@retry_on_failure` for external API calls
- Use `@validate_context_length` for LLM endpoints
- Use `@log_execution` for debugging complex operations

### 3. Configure Appropriately

Tune decorator parameters for your use case:
- Cache TTL: Balance freshness vs. performance
- Retry count: Balance reliability vs. latency
- Timeouts: Set based on expected operation duration
- Rate limits: Align with infrastructure capacity

### 4. Test Decorated Functions

Test both decorated and undecorated behavior:
```python
# Test decorated function
result = await service.decorated_method(request)

# Test underlying logic
result = await service.decorated_method.__wrapped__(service, request)
```

## Examples

See `/examples/decorators_demo.py` for comprehensive examples of all decorators.

## Testing

Run the test suite:
```bash
pytest tests/test_shared_decorators.py -v
```

All 40+ tests cover:
- Individual decorator functionality
- Error handling
- Edge cases
- Decorator combinations
- Performance characteristics

## Implementation Notes

- All decorators preserve function metadata via `functools.wraps()`
- Decorators are async-compatible
- Thread-safe for concurrent use
- Minimal performance overhead
- Graceful degradation (e.g., `@measure_performance` works without psutil)

## Future Enhancements

Potential additions:
- Circuit breaker pattern
- Bulkhead isolation
- Distributed caching
- Prometheus metrics integration
- Async context manager decorators
- Conditional execution decorators

## License

Apache-2.0 (same as FakeAI project)
