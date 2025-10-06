# Middleware Architecture Quick Reference

**Version:** 1.0.0
**Last Updated:** 2025-10-05

## Installation

No installation needed - middleware is part of FakeAI core.

```python
from fakeai.middleware import (
    MiddlewarePipeline,
    SecurityMiddleware,
    AuthenticationMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    MetricsMiddleware,
    CachingMiddleware,
    ErrorInjectionMiddleware,
)
```

## Quick Start

### Basic Usage

```python
from fastapi import FastAPI
from fakeai.middleware.integration import (
    create_default_pipeline,
    MiddlewarePipelineWrapper,
)

# Create app
app = FastAPI()

# Create middleware pipeline
pipeline = create_default_pipeline(
    config=config,
    api_key_manager=api_key_manager,
    abuse_detector=abuse_detector,
    input_validator=input_validator,
    rate_limiter=rate_limiter,
    metrics_tracker=metrics_tracker,
)

# Register with FastAPI
app.add_middleware(MiddlewarePipelineWrapper, pipeline=pipeline)
```

### Custom Pipeline

```python
from fakeai.middleware import MiddlewarePipeline
from fakeai.middleware.base import MiddlewareConfig

# Create custom pipeline
pipeline = MiddlewarePipeline([
    SecurityMiddleware(
        config=MiddlewareConfig(priority=0, enabled=True),
        enable_abuse_detection=True,
    ),
    AuthenticationMiddleware(
        config=MiddlewareConfig(priority=10, enabled=True),
        require_api_key=True,
    ),
    MetricsMiddleware(
        config=MiddlewareConfig(priority=20, enabled=True),
    ),
])
```

## Middleware Cheat Sheet

| Middleware | Priority | Purpose | Short-circuits? |
|-----------|----------|---------|----------------|
| SecurityMiddleware | 0 | IP bans, payload validation, injection detection | Yes (403, 413, 400) |
| AuthenticationMiddleware | 10 | API key validation | Yes (401) |
| RateLimitMiddleware | 20 | Rate limiting (RPM/TPM) | Yes (429) |
| RequestLoggingMiddleware | 30 | Request/response logging | No |
| MetricsMiddleware | 40 | Metrics collection | No |
| CachingMiddleware | 50 | Response caching | Yes (cache hit) |
| ErrorInjectionMiddleware | 60 | Error injection (testing) | Yes (configurable) |

## Configuration Templates

### Development

```python
# Development: Relaxed security, verbose logging
SecurityMiddleware(
    config=MiddlewareConfig(enabled=False),
)

AuthenticationMiddleware(
    config=MiddlewareConfig(enabled=False),
    require_api_key=False,
)

RequestLoggingMiddleware(
    config=MiddlewareConfig(enabled=True),
    log_level=logging.DEBUG,
    log_request_body=True,
)
```

### Staging

```python
# Staging: Full features, verbose logging
SecurityMiddleware(
    config=MiddlewareConfig(enabled=True),
    enable_abuse_detection=True,
    enable_injection_detection=True,
)

AuthenticationMiddleware(
    config=MiddlewareConfig(enabled=True),
    require_api_key=True,
)

RateLimitMiddleware(
    config=MiddlewareConfig(enabled=True),
    enabled=True,
)

ErrorInjectionMiddleware(
    config=MiddlewareConfig(enabled=True),
    enabled=True,  # For chaos testing
)
```

### Production

```python
# Production: Security hardened, performance optimized
SecurityMiddleware(
    config=MiddlewareConfig(
        enabled=True,
        exclude_endpoints=["/health", "/metrics"],
    ),
    enable_abuse_detection=True,
    enable_input_validation=True,
    enable_injection_detection=True,
)

AuthenticationMiddleware(
    config=MiddlewareConfig(
        enabled=True,
        exclude_endpoints=["/health", "/metrics"],
    ),
    require_api_key=True,
)

RateLimitMiddleware(
    config=MiddlewareConfig(enabled=True),
    enabled=True,
)

RequestLoggingMiddleware(
    config=MiddlewareConfig(enabled=True),
    log_level=logging.INFO,  # Less verbose
    log_request_body=False,  # Privacy
)

ErrorInjectionMiddleware(
    config=MiddlewareConfig(enabled=False),
    enabled=False,  # NEVER in production!
)
```

## Common Patterns

### Per-Endpoint Configuration

```python
# Only protect API endpoints
AuthenticationMiddleware(
    config=MiddlewareConfig(
        exclude_endpoints=[
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ],
    ),
)

# Only rate limit expensive endpoints
RateLimitMiddleware(
    config=MiddlewareConfig(
        endpoints=[
            "/v1/chat/completions",
            "/v1/completions",
            "/v1/embeddings",
        ],
    ),
)

# Only cache read endpoints
CachingMiddleware(
    config=MiddlewareConfig(
        endpoints=["/v1/models", "/v1/models/*"],
    ),
    cacheable_methods=["GET"],
)
```

### Custom Middleware

```python
from fakeai.middleware.base import BaseMiddleware

class CustomMiddleware(BaseMiddleware):
    async def before_request(self, context):
        # Pre-process request
        context.set("custom_data", "value")
        return context

    async def after_response(self, context, response):
        # Post-process response
        response.headers["X-Custom"] = context.get("custom_data")
        return response

# Add to pipeline
pipeline.add_middleware(CustomMiddleware(
    config=MiddlewareConfig(priority=100)
))
```

### Conditional Middleware

```python
# Enable based on environment
if os.getenv("ENV") == "production":
    pipeline.add_middleware(SecurityMiddleware(...))
else:
    pipeline.add_middleware(ErrorInjectionMiddleware(...))

# Enable based on feature flag
if config.enable_caching:
    pipeline.add_middleware(CachingMiddleware(...))
```

## Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Output:
# [12345-6789] GET /v1/models from 127.0.0.1
# Request short-circuited by CachingMiddleware
# [12345-6789] Completed in 0.5ms with status 200
```

### Check Middleware Execution

```python
# Print middleware pipeline
print(pipeline)
# Output: MiddlewarePipeline([SecurityMiddleware, AuthenticationMiddleware, ...])

# Get specific middleware
auth_middlewares = pipeline.get_middleware(AuthenticationMiddleware)
print(f"Found {len(auth_middlewares)} auth middleware")

# Remove middleware
pipeline.remove_middleware(ErrorInjectionMiddleware)
```

### Access Context Data

```python
# In middleware
context.set("my_data", {"key": "value"})

# In handler
my_data = context.get("my_data")
```

## Performance Tips

### Minimize Overhead

1. **Disable unused middleware:**
   ```python
   config=MiddlewareConfig(enabled=False)
   ```

2. **Exclude health checks:**
   ```python
   config=MiddlewareConfig(
       exclude_endpoints=["/health", "/metrics"]
   )
   ```

3. **Optimize priorities:**
   Put fast checks first (security before expensive operations)

### Caching

```python
# Enable caching for read-heavy endpoints
CachingMiddleware(
    config=MiddlewareConfig(
        endpoints=["/v1/models"],
    ),
    enabled=True,
    default_ttl=300.0,  # 5 minutes
    max_cache_size=1000,
)

# Check cache stats
stats = caching_middleware.get_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

## Testing

### Unit Test

```python
import pytest
from fakeai.middleware import AuthenticationMiddleware

@pytest.mark.asyncio
async def test_auth_middleware():
    middleware = AuthenticationMiddleware(require_api_key=True)
    context = create_test_context()

    result = await middleware.before_request(context)

    assert isinstance(result, Response)
    assert result.status_code == 401
```

### Integration Test

```python
from fastapi.testclient import TestClient

def test_middleware_pipeline(client):
    response = client.get("/v1/models")
    assert response.status_code == 401  # No API key

    response = client.get(
        "/v1/models",
        headers={"Authorization": "Bearer test"}
    )
    assert response.status_code == 200  # With API key
```

## Monitoring

### Metrics

```python
# Get metrics
metrics = metrics_tracker.get_metrics()
print(f"Total requests: {metrics['total_requests']}")

# Get cache stats
cache_stats = caching_middleware.get_stats()
print(f"Cache hit rate: {cache_stats['hit_rate']:.2%}")

# Get rate limit stats
rate_stats = rate_limiter.get_stats()
print(f"Throttled: {rate_stats['throttled_count']}")
```

### Health Check

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

## Common Issues

### Issue: 401 Unauthorized

**Cause:** Missing or invalid API key

**Solution:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/v1/models
```

### Issue: 429 Rate Limit Exceeded

**Cause:** Too many requests

**Solution:**
- Wait for rate limit to reset (check Retry-After header)
- Upgrade to higher tier
- Increase rate limits in config

### Issue: 403 Forbidden

**Cause:** IP banned due to abuse

**Solution:**
- Wait for ban to expire
- Check abuse_detector logs
- Whitelist IP if legitimate

### Issue: Middleware not executing

**Cause:** Endpoint excluded or middleware disabled

**Solution:**
- Check `config.enabled`
- Check `config.endpoints` and `config.exclude_endpoints`
- Verify middleware is in pipeline

## Environment Variables

```bash
# Security
export FAKEAI_SECURITY_ENABLED=true
export FAKEAI_ABUSE_DETECTION=true
export FAKEAI_INJECTION_DETECTION=true

# Authentication
export FAKEAI_REQUIRE_API_KEY=true
export FAKEAI_API_KEYS='["key1", "key2"]'

# Rate limiting
export FAKEAI_RATE_LIMIT_ENABLED=true
export FAKEAI_RATE_LIMIT_TIER=tier-2
export FAKEAI_RATE_LIMIT_RPM=1000
export FAKEAI_RATE_LIMIT_TPM=100000

# Caching
export FAKEAI_CACHE_ENABLED=true
export FAKEAI_CACHE_TTL=300

# Logging
export FAKEAI_DEBUG=true
export FAKEAI_LOG_LEVEL=DEBUG
```

## Migration Checklist

- [ ] Review current middleware implementation
- [ ] Create middleware pipeline
- [ ] Add feature flag (`use_new_middleware`)
- [ ] Test with flag disabled (old middleware)
- [ ] Test with flag enabled (new middleware)
- [ ] Compare metrics and logs
- [ ] Enable by default
- [ ] Remove `dependencies=[Depends(verify_api_key)]` from routes
- [ ] Monitor in production
- [ ] Remove old middleware code
- [ ] Update documentation

## Resources

- **Architecture Guide:** [MIDDLEWARE_ARCHITECTURE.md](MIDDLEWARE_ARCHITECTURE.md)
- **Source Code:** `fakeai/middleware/`
- **Tests:** `tests/test_middleware_*.py`

---

**Quick Reference Version:** 1.0.0
**Last Updated:** 2025-10-05
