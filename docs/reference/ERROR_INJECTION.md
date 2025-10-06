# Error Injection System

## Overview

The Error Injection system in FakeAI provides a decoupled, configurable way to simulate realistic API failures for testing error handling in client applications. This is essential for building robust applications that gracefully handle various error scenarios.

## Features

- **Configurable Error Rates**: Set error rates from 0.0 to 1.0 (0% to 100%)
- **Global and Per-Endpoint Rates**: Apply different error rates to different endpoints
- **Multiple Error Types**: Simulate 6 different types of errors (500, 502, 503, 504, 429, 400)
- **Load Spike Simulation**: Temporarily increase error rates to simulate traffic spikes
- **Thread-Safe**: Safe to use across multiple threads/requests
- **Prometheus Metrics**: Export error injection metrics for monitoring
- **Statistics Tracking**: Track errors by type and endpoint

## Error Types

| Error Type | Status Code | Description |
|------------|-------------|-------------|
| `INTERNAL_ERROR` | 500 | Generic server error |
| `BAD_GATEWAY` | 502 | Invalid upstream response |
| `SERVICE_UNAVAILABLE` | 503 | Server overloaded or maintenance |
| `GATEWAY_TIMEOUT` | 504 | Timeout waiting for model |
| `RATE_LIMIT_QUOTA` | 429 | Quota exceeded |
| `CONTEXT_LENGTH_EXCEEDED` | 400 | Context window exceeded |

## Configuration

### Environment Variables

```bash
# Enable error injection
export FAKEAI_ERROR_INJECTION_ENABLED=true

# Set global error rate (0.0-1.0)
export FAKEAI_ERROR_INJECTION_RATE=0.15

# Specify error types to inject (JSON list)
export FAKEAI_ERROR_INJECTION_TYPES='["internal_error", "service_unavailable"]'
```

### Programmatic Configuration

```python
from fakeai.config import AppConfig

config = AppConfig(
    error_injection_enabled=True,
    error_injection_rate=0.15,
    error_injection_types=["internal_error", "service_unavailable"],
)
```

## Usage

### Basic Usage

```python
from fakeai.error_injector import ErrorInjector, get_error_injector

# Get singleton instance
injector = get_error_injector()

# Enable and set global rate
injector.enable()
injector.set_global_error_rate(0.1)  # 10% error rate

# Check if error should be injected
should_inject, error_response = injector.should_inject_error("/v1/chat/completions")

if should_inject:
    # error_response contains:
    # {
    #   "status_code": 503,
    #   "error": {
    #     "message": "The server is overloaded...",
    #     "type": "service_unavailable",
    #     "code": "service_unavailable"
    #   }
    # }
    return JSONResponse(
        status_code=error_response["status_code"],
        content=error_response
    )
```

### Per-Endpoint Error Rates

```python
# Set different error rates for different endpoints
injector.set_endpoint_error_rate("/v1/chat/completions", 0.2)  # 20%
injector.set_endpoint_error_rate("/v1/embeddings", 0.05)       # 5%

# Clear endpoint-specific rate (reverts to global rate)
injector.clear_endpoint_error_rate("/v1/chat/completions")
```

### Specific Error Types

```python
from fakeai.error_injector import ErrorType

# Only inject specific error types
injector.set_error_types([
    ErrorType.SERVICE_UNAVAILABLE,
    ErrorType.GATEWAY_TIMEOUT,
])

# Always inject errors with 100% rate for testing
injector.set_global_error_rate(1.0)
```

### Load Spike Simulation

```python
# Simulate a load spike for 30 seconds with 3x error rate
injector.simulate_load_spike(
    duration_seconds=30.0,
    error_rate_multiplier=3.0
)

# During the spike, a 10% base rate becomes 30%
# After 30 seconds, error rate returns to normal

# Clear spike early if needed
injector.clear_load_spike()
```

### Statistics and Monitoring

```python
# Get detailed statistics
stats = injector.get_error_stats()

print(f"Total checks: {stats['statistics']['total_checks']}")
print(f"Total errors: {stats['statistics']['total_errors_injected']}")
print(f"Error rate: {stats['statistics']['overall_error_rate']:.2%}")

# Errors by type
for error_type, count in stats['statistics']['errors_by_type'].items():
    print(f"  {error_type}: {count}")

# Errors by endpoint
for endpoint, count in stats['statistics']['errors_by_endpoint'].items():
    print(f"  {endpoint}: {count}")

# Check if load spike is active
if stats['load_spike']:
    print(f"Load spike active: {stats['load_spike']['remaining_seconds']}s remaining")
```

### Prometheus Metrics

```python
# Export Prometheus metrics
metrics = injector.get_prometheus_metrics()

# Metrics include:
# - fakeai_error_injection_enabled
# - fakeai_error_injection_global_rate
# - fakeai_error_injection_checks_total
# - fakeai_error_injection_errors_total
# - fakeai_error_injection_rate
# - fakeai_error_injection_by_type_total{type="..."}
# - fakeai_error_injection_by_endpoint_total{endpoint="..."}
# - fakeai_error_injection_load_spike_active
# - fakeai_error_injection_load_spike_multiplier
```

## Testing Patterns

### Test Retry Logic

```python
# Test that your client retries on 503 errors
injector = ErrorInjector(
    global_error_rate=1.0,
    enabled=True,
    error_types=[ErrorType.SERVICE_UNAVAILABLE]
)

# Make request (should fail with 503)
# Verify client retries
# Disable error injection
injector.disable()
# Verify request succeeds
```

### Test Exponential Backoff

```python
# Inject rate limit errors
injector = ErrorInjector(
    global_error_rate=0.5,
    enabled=True,
    error_types=[ErrorType.RATE_LIMIT_QUOTA]
)

# Make multiple requests
# Verify client implements exponential backoff
# Monitor retry timing between requests
```

### Test Circuit Breaker

```python
# Simulate cascading failures
injector.set_endpoint_error_rate("/v1/chat/completions", 0.8)

# Make many requests
# Verify circuit breaker opens after threshold
# Verify half-open state after cooldown
```

### Test Graceful Degradation

```python
# Simulate partial outage
injector.set_endpoint_error_rate("/v1/embeddings", 1.0)  # Complete failure
injector.set_endpoint_error_rate("/v1/chat/completions", 0.1)  # Minor issues

# Verify application degrades gracefully
# Verify fallback mechanisms work
```

## Integration with FastAPI

```python
from fastapi import FastAPI, HTTPException
from fakeai.error_injector import get_error_injector

app = FastAPI()
injector = get_error_injector()

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    # Check for error injection
    should_inject, error_response = injector.should_inject_error("/v1/chat/completions")

    if should_inject:
        raise HTTPException(
            status_code=error_response["status_code"],
            detail=error_response["error"]
        )

    # Normal processing
    return process_chat_request(request)
```

## Best Practices

1. **Start with Low Error Rates**: Begin with 1-5% error rates to avoid overwhelming tests
2. **Test Each Error Type**: Ensure your client handles each error type appropriately
3. **Use Per-Endpoint Rates**: Simulate realistic scenarios where some endpoints fail more
4. **Monitor Statistics**: Use `get_error_stats()` to verify error injection is working
5. **Reset Between Tests**: Call `reset_stats()` between test runs for clean data
6. **Test Load Spikes**: Verify your application handles temporary traffic spikes
7. **Document Expected Behavior**: Document how your application should respond to each error type

## Thread Safety

The ErrorInjector is thread-safe and uses `threading.Lock()` to protect shared state. Safe to use across multiple threads/requests simultaneously:

```python
import threading

def worker():
    injector = get_error_injector()
    for _ in range(100):
        should_inject, error = injector.should_inject_error("/v1/chat/completions")
        # Process request...

threads = [threading.Thread(target=worker) for _ in range(10)]
for t in threads:
    t.start()
```

## Troubleshooting

### No Errors Being Injected

```python
# Check if enabled
injector = get_error_injector()
print(f"Enabled: {injector.enabled}")

# Check error rate
stats = injector.get_error_stats()
print(f"Global rate: {stats['global_error_rate']}")

# Enable if needed
injector.enable()
injector.set_global_error_rate(0.1)
```

### Too Many Errors

```python
# Check if load spike is active
stats = injector.get_error_stats()
if stats['load_spike']:
    print("Load spike is active!")
    injector.clear_load_spike()

# Reduce error rate
injector.set_global_error_rate(0.05)
```

### Statistics Not Updating

```python
# Ensure you're using the singleton instance
injector = get_error_injector()  # Always use this!

# Don't create new instances
# injector = ErrorInjector()  # Wrong! Creates separate instance
```

## Examples

See `/home/anthony/projects/fakeai/examples/error_injection_example.py` for complete working examples of:
- Basic error injection
- Per-endpoint error rates
- Specific error types
- Load spike simulation
- Configuration integration
- Prometheus metrics export

## API Reference

### ErrorInjector

#### `__init__(global_error_rate: float = 0.0, enabled: bool = False, error_types: list[ErrorType] | None = None)`

Initialize error injector.

#### `enable() -> None`

Enable error injection.

#### `disable() -> None`

Disable error injection.

#### `set_global_error_rate(rate: float) -> None`

Set global error rate (0.0-1.0).

#### `set_endpoint_error_rate(endpoint: str, rate: float) -> None`

Set error rate for specific endpoint.

#### `clear_endpoint_error_rate(endpoint: str) -> None`

Clear endpoint-specific error rate.

#### `set_error_types(error_types: list[ErrorType]) -> None`

Set which error types to inject.

#### `simulate_load_spike(duration_seconds: float, error_rate_multiplier: float = 3.0) -> None`

Simulate temporary load spike.

#### `clear_load_spike() -> None`

Clear active load spike.

#### `should_inject_error(endpoint: str) -> tuple[bool, dict | None]`

Check if error should be injected. Returns (should_inject, error_response).

#### `get_error_stats() -> dict`

Get error injection statistics.

#### `reset_stats() -> None`

Reset statistics counters.

#### `get_prometheus_metrics() -> str`

Export Prometheus-formatted metrics.

### Helper Functions

#### `get_error_injector() -> ErrorInjector`

Get singleton ErrorInjector instance.

#### `set_error_injector(injector: ErrorInjector) -> None`

Set custom ErrorInjector instance (for testing).
