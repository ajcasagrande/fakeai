# FakeAI Middleware Architecture

**Version:** 1.0.0
**Status:** Complete Implementation
**Last Updated:** 2025-10-05

## Overview

FakeAI's middleware architecture provides a comprehensive, composable system for handling cross-cutting concerns. The architecture is built on:

- **Protocol-based design**: Clean separation between interface and implementation
- **Pipeline execution**: Ordered, predictable middleware execution
- **Context propagation**: Shared state across middleware chain
- **Short-circuit support**: Early termination for auth, rate limiting, etc.
- **Error handling**: Middleware-specific error handlers
- **Configuration**: Per-middleware and per-endpoint configuration

## Architecture Components

### 1. Core Abstractions

#### Middleware Protocol

```python
class Middleware(Protocol):
    """Protocol that all middleware must implement."""

    config: MiddlewareConfig

    async def before_request(
        self, context: MiddlewareContext
    ) -> MiddlewareContext | Response:
        """Pre-process request (can short-circuit)."""
        ...

    async def after_response(
        self, context: MiddlewareContext, response: Response
    ) -> Response:
        """Post-process response."""
        ...

    async def on_error(
        self, context: MiddlewareContext, error: Exception
    ) -> Response | None:
        """Handle errors."""
        ...
```

#### MiddlewareContext

The context object passed through the middleware pipeline:

```python
@dataclass
class MiddlewareContext:
    """Context shared across middleware pipeline."""

    request: Request
    data: dict[str, Any]  # Shared data
    metadata: dict[str, Any]  # Metadata
    start_time: float
    request_id: str
    client_ip: str
    endpoint: str
    api_key: str | None
```

#### MiddlewareConfig

Configuration for middleware behavior:

```python
@dataclass
class MiddlewareConfig:
    """Configuration for middleware."""

    enabled: bool = True
    priority: int = 0  # Lower numbers execute first
    endpoints: list[str] | None = None  # None = all
    exclude_endpoints: list[str] | None = None
    metadata: dict[str, Any]
```

### 2. Middleware Pipeline

The pipeline manages ordered execution of middleware:

```python
class MiddlewarePipeline:
    """Executes middleware in order."""

    def __init__(self, middlewares: list[Middleware]):
        """Initialize with middleware list (sorted by priority)."""
        self.middlewares = sorted(middlewares, key=lambda m: m.config.priority)

    async def process_request(
        self, context: MiddlewareContext
    ) -> MiddlewareContext | Response:
        """Process through middleware chain (can short-circuit)."""
        ...

    async def process_response(
        self, context: MiddlewareContext, response: Response
    ) -> Response:
        """Process response in reverse order."""
        ...
```

### 3. Execution Flow

```
Client Request
     |
     v

  Request Phase (in order)           

  1. SecurityMiddleware (priority 0) 
     - IP ban check                  
     - Payload validation            
     - Injection detection           
                                     
  2. AuthenticationMiddleware (10)   
     - Extract API key               
     - Validate key                  
     - Store in context              
                                     
  3. RateLimitMiddleware (20)        
     - Check rate limits             
     - Short-circuit if exceeded     
                                     
  4. RequestLoggingMiddleware (30)   
     - Generate request ID           
     - Log request details           
                                     
  5. MetricsMiddleware (40)          
     - Track request count           
     - Record start time             
                                     
  6. CachingMiddleware (50)          
     - Check cache                   
     - Return cached if available    
                                     
  7. ErrorInjectionMiddleware (60)   
     - Inject errors (if enabled)    

     |
     v

  Request Handler                    
  (FastAPI route)                    

     |
     v

  Response Phase (reverse order)     

  7. ErrorInjectionMiddleware        
  6. CachingMiddleware               
     - Store response in cache       
  5. MetricsMiddleware               
     - Track response time           
  4. RequestLoggingMiddleware        
     - Log response status           
  3. RateLimitMiddleware             
     - Add rate limit headers        
  2. AuthenticationMiddleware        
  1. SecurityMiddleware              
     - Add security headers          

     |
     v
Client Response
```

## Middleware Implementations

### 1. SecurityMiddleware

**Purpose:** First line of defense against threats

**Features:**
- IP ban checking (integrates with AbuseDetector)
- Payload size validation
- Injection attack detection
- Input sanitization
- Security headers (X-Frame-Options, HSTS, etc.)

**Configuration:**
```python
SecurityMiddleware(
    config=MiddlewareConfig(
        enabled=True,
        priority=0,  # Execute first
        exclude_endpoints=["/health", "/metrics"],
    ),
    enable_abuse_detection=True,
    enable_input_validation=True,
    enable_injection_detection=True,
    max_request_size=10 * 1024 * 1024,  # 10 MB
)
```

**Short-circuits on:**
- Banned IP (403)
- Oversized payload (413)
- Injection attack detected (400)

### 2. AuthenticationMiddleware

**Purpose:** API key validation

**Features:**
- API key extraction from Authorization header
- Key validation (with optional hashing)
- Failed attempt tracking
- API key stored in context for downstream use

**Configuration:**
```python
AuthenticationMiddleware(
    config=MiddlewareConfig(
        enabled=True,
        priority=10,
        exclude_endpoints=["/health", "/docs", "/openapi.json"],
    ),
    api_key_manager=api_key_manager,
    abuse_detector=abuse_detector,
    require_api_key=True,
)
```

**Short-circuits on:**
- Missing API key (401)
- Invalid API key (401)

### 3. RateLimitMiddleware

**Purpose:** Request rate limiting per API key

**Features:**
- Token bucket algorithm
- RPM and TPM limits
- Token estimation from request body
- Rate limit headers in responses
- Retry-After header on limit exceeded

**Configuration:**
```python
RateLimitMiddleware(
    config=MiddlewareConfig(
        enabled=True,
        priority=20,
        endpoints=[
            "/v1/chat/completions",
            "/v1/completions",
            "/v1/embeddings",
        ],
    ),
    rate_limiter=rate_limiter,
    enabled=True,
)
```

**Short-circuits on:**
- Rate limit exceeded (429)

### 4. RequestLoggingMiddleware

**Purpose:** Request/response logging

**Features:**
- Request ID generation
- Incoming request logging
- Response status and timing logging
- Optional request/response body logging
- X-Request-ID header in responses

**Configuration:**
```python
RequestLoggingMiddleware(
    config=MiddlewareConfig(
        enabled=True,
        priority=30,
    ),
    log_level=logging.INFO,
    log_request_body=False,
    log_response_body=False,
)
```

**Never short-circuits**

### 5. MetricsMiddleware

**Purpose:** Metrics collection

**Features:**
- Request count tracking
- Response time measurement
- Error tracking
- Per-endpoint metrics
- Integration with MetricsTracker singleton

**Configuration:**
```python
MetricsMiddleware(
    config=MiddlewareConfig(
        enabled=True,
        priority=40,
    ),
    metrics_tracker=metrics_tracker,
)
```

**Never short-circuits**

### 6. CachingMiddleware

**Purpose:** Response caching

**Features:**
- In-memory cache with TTL
- Cache key generation from request
- ETag and Cache-Control headers
- LRU eviction
- Per-endpoint caching
- Cache statistics

**Configuration:**
```python
CachingMiddleware(
    config=MiddlewareConfig(
        enabled=True,
        priority=50,
        endpoints=["/v1/models", "/v1/models/*"],
    ),
    enabled=False,  # Disabled by default
    default_ttl=300.0,  # 5 minutes
    max_cache_size=1000,
    cacheable_methods=["GET"],
)
```

**Short-circuits on:**
- Cache hit (returns cached response)

### 7. ErrorInjectionMiddleware

**Purpose:** Chaos engineering and testing

**Features:**
- Configurable error injection rates
- HTTP error code injection
- Latency injection
- Per-endpoint configuration
- Circuit breaker simulation

**Configuration:**
```python
ErrorInjectionMiddleware(
    config=MiddlewareConfig(
        enabled=False,  # Disabled by default
        priority=60,
    ),
    error_injector=error_injector,
    enabled=False,
)
```

** WARNING:** Only enable in development/testing!

**Short-circuits on:**
- Error injected (configurable status code)

## Integration with FastAPI

### Option 1: FastAPI Middleware Integration (Recommended)

Create a FastAPI middleware wrapper:

```python
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

class MiddlewarePipelineWrapper(BaseHTTPMiddleware):
    """Wrapper to integrate MiddlewarePipeline with FastAPI."""

    def __init__(self, app: FastAPI, pipeline: MiddlewarePipeline):
        super().__init__(app)
        self.pipeline = pipeline

    async def dispatch(self, request: Request, call_next):
        """Process request through middleware pipeline."""
        # Create context
        context = MiddlewareContext(
            request=request,
            start_time=time.time(),
            request_id=f"{int(time.time())}-{random.randint(1000, 9999)}",
            client_ip=request.client.host if request.client else "unknown",
            endpoint=request.url.path,
        )

        # Process through request middleware
        result = await self.pipeline.process_request(context)

        # Check for short-circuit
        if isinstance(result, Response):
            return result

        # Continue to handler
        response = await call_next(request)

        # Process through response middleware
        response = await self.pipeline.process_response(context, response)

        return response

# Usage
app = FastAPI()

pipeline = MiddlewarePipeline([
    SecurityMiddleware(...),
    AuthenticationMiddleware(...),
    RateLimitMiddleware(...),
    RequestLoggingMiddleware(...),
    MetricsMiddleware(...),
])

app.add_middleware(MiddlewarePipelineWrapper, pipeline=pipeline)
```

### Option 2: Dependency Injection

Use middleware as FastAPI dependencies:

```python
async def middleware_pipeline_dependency(request: Request):
    """Run middleware as a dependency."""
    context = create_context(request)
    result = await pipeline.process_request(context)

    if isinstance(result, Response):
        raise HTTPException(...)

    return context

@app.post("/v1/chat/completions", dependencies=[Depends(middleware_pipeline_dependency)])
async def chat_completions(request: ChatCompletionRequest, context: MiddlewareContext):
    ...
```

## Configuration Best Practices

### Priority Ordering

Recommended priority order:

| Priority | Middleware               | Reason                          |
|----------|--------------------------|--------------------------------|
| 0        | SecurityMiddleware       | Block threats early            |
| 10       | AuthenticationMiddleware | Validate identity              |
| 20       | RateLimitMiddleware      | Prevent abuse                  |
| 30       | RequestLoggingMiddleware | Log all requests               |
| 40       | MetricsMiddleware        | Track all metrics              |
| 50       | CachingMiddleware        | Check cache before processing  |
| 60       | ErrorInjectionMiddleware | Last resort (testing only)     |

### Per-Endpoint Configuration

Configure middleware per endpoint:

```python
# Only protect API endpoints, not health/metrics
AuthenticationMiddleware(
    config=MiddlewareConfig(
        exclude_endpoints=["/health", "/metrics", "/docs"],
    ),
)

# Only rate limit high-cost endpoints
RateLimitMiddleware(
    config=MiddlewareConfig(
        endpoints=[
            "/v1/chat/completions",
            "/v1/completions",
            "/v1/embeddings",
        ],
    ),
)

# Only cache GET requests to models endpoint
CachingMiddleware(
    config=MiddlewareConfig(
        endpoints=["/v1/models", "/v1/models/*"],
    ),
    cacheable_methods=["GET"],
)
```

### Environment-Based Configuration

```python
import os

# Security
security_enabled = os.getenv("FAKEAI_SECURITY_ENABLED", "true") == "true"
abuse_detection = os.getenv("FAKEAI_ABUSE_DETECTION", "false") == "true"

# Rate limiting
rate_limit_enabled = os.getenv("FAKEAI_RATE_LIMIT_ENABLED", "false") == "true"

# Caching
cache_enabled = os.getenv("FAKEAI_CACHE_ENABLED", "false") == "true"
cache_ttl = float(os.getenv("FAKEAI_CACHE_TTL", "300"))

# Error injection (NEVER enable in production!)
error_injection = os.getenv("FAKEAI_ERROR_INJECTION", "false") == "true"
if error_injection and os.getenv("ENV") == "production":
    raise ValueError("Error injection cannot be enabled in production!")
```

## Migration Guide

### Migrating from Current app.py Middleware

Current implementation (app.py lines 226-388):

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and enforce rate limits with security checks"""
    # ... 160+ lines of mixed concerns
```

**Migration steps:**

1. **Create middleware pipeline:**

```python
# Initialize security components
api_key_manager = ApiKeyManager()
abuse_detector = AbuseDetector()
input_validator = InputValidator()
rate_limiter = RateLimiter()
metrics_tracker = MetricsTracker()

# Create middleware pipeline
pipeline = MiddlewarePipeline([
    SecurityMiddleware(
        config=MiddlewareConfig(
            priority=0,
            exclude_endpoints=["/health", "/metrics"],
        ),
        abuse_detector=abuse_detector,
        input_validator=input_validator,
        enable_abuse_detection=config.enable_abuse_detection,
        enable_input_validation=config.enable_input_validation,
        enable_injection_detection=config.enable_injection_detection,
        max_request_size=config.max_request_size,
    ),
    AuthenticationMiddleware(
        config=MiddlewareConfig(
            priority=10,
            exclude_endpoints=["/health", "/metrics", "/docs", "/openapi.json"],
        ),
        api_key_manager=api_key_manager,
        abuse_detector=abuse_detector,
        require_api_key=config.require_api_key,
    ),
    RateLimitMiddleware(
        config=MiddlewareConfig(
            priority=20,
            endpoints=[
                "/v1/chat/completions",
                "/v1/completions",
                "/v1/embeddings",
            ],
        ),
        rate_limiter=rate_limiter,
        abuse_detector=abuse_detector,
        enabled=config.rate_limit_enabled,
    ),
    RequestLoggingMiddleware(
        config=MiddlewareConfig(priority=30),
        log_level=logging.DEBUG if config.debug else logging.INFO,
    ),
    MetricsMiddleware(
        config=MiddlewareConfig(priority=40),
        metrics_tracker=metrics_tracker,
    ),
])
```

2. **Add pipeline wrapper:**

```python
app.add_middleware(MiddlewarePipelineWrapper, pipeline=pipeline)
```

3. **Remove old middleware:**

```python
# DELETE lines 226-388 from app.py
# @app.middleware("http")
# async def log_requests(...):
#     ...
```

4. **Remove verify_api_key dependency:**

Since authentication is now handled by middleware, remove the `verify_api_key` dependency from route definitions:

```python
# Before
@app.post("/v1/chat/completions", dependencies=[Depends(verify_api_key)])
async def create_chat_completion(request: ChatCompletionRequest):
    ...

# After
@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    ...
```

API key is now available in the context, stored during request processing.

### Testing the Migration

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    return TestClient(app)

def test_security_middleware(client):
    """Test IP ban blocking."""
    # Simulate banned IP
    response = client.get("/v1/models", headers={"X-Forwarded-For": "1.2.3.4"})
    assert response.status_code == 403

def test_auth_middleware(client):
    """Test API key validation."""
    response = client.get("/v1/models")
    assert response.status_code == 401

    response = client.get("/v1/models", headers={"Authorization": "Bearer test"})
    assert response.status_code == 200

def test_rate_limit_middleware(client):
    """Test rate limiting."""
    for _ in range(100):
        response = client.post("/v1/chat/completions", ...)

    # Should eventually hit rate limit
    assert response.status_code == 429
    assert "Retry-After" in response.headers

def test_metrics_middleware(client):
    """Test metrics collection."""
    client.get("/v1/models")
    metrics = client.get("/metrics").json()

    assert metrics["total_requests"] > 0

def test_caching_middleware(client):
    """Test response caching."""
    # First request
    response1 = client.get("/v1/models")
    assert response1.headers.get("X-Cache") == "MISS"

    # Second request (should be cached)
    response2 = client.get("/v1/models")
    assert response2.headers.get("X-Cache") == "HIT"
```

## Performance Considerations

### Overhead

- **Per-request overhead:** ~1-2ms for full pipeline (7 middleware)
- **Memory overhead:** ~1KB per request (context object)
- **Cache overhead:** Depends on cache size (default 1000 entries)

### Optimization Tips

1. **Disable unused middleware:**
   ```python
   CachingMiddleware(config=MiddlewareConfig(enabled=False))
   ```

2. **Exclude health check endpoints:**
   ```python
   config=MiddlewareConfig(exclude_endpoints=["/health", "/metrics"])
   ```

3. **Use per-endpoint configuration:**
   ```python
   # Only rate limit expensive endpoints
   RateLimitMiddleware(config=MiddlewareConfig(
       endpoints=["/v1/chat/completions"]
   ))
   ```

4. **Adjust priorities:**
   Lower priorities execute first - put fast checks early.

## Monitoring and Debugging

### Metrics

Access middleware metrics:

```python
# Cache stats
cache_stats = caching_middleware.get_stats()
print(f"Cache hit rate: {cache_stats['hit_rate']:.2%}")

# Rate limiter stats
rate_stats = rate_limiter.get_stats()
print(f"Throttled requests: {rate_stats['throttled_count']}")
```

### Logging

Enable debug logging:

```python
logging.basicConfig(level=logging.DEBUG)

# Output:
# [12345-6789] GET /v1/models from 127.0.0.1
# Request short-circuited by CachingMiddleware
# [12345-6789] Completed in 0.5ms with status 200
```

### Tracing

Middleware context includes request ID for distributed tracing:

```python
# In middleware
logger.info(f"[{context.request_id}] Processing request")

# In handler
logger.info(f"[{context.request_id}] Generating response")
```

## Security Considerations

### API Key Storage

- Store API keys hashed (use ApiKeyManager with hashing)
- Never log full API keys (use prefix only)
- Rotate keys regularly

### Input Validation

- Always enable SecurityMiddleware in production
- Set reasonable payload size limits
- Enable injection detection for user-facing APIs

### Rate Limiting

- Configure appropriate limits per tier
- Monitor for rate limit abuse
- Use progressive bans for repeated violations

### Error Injection

- **NEVER** enable ErrorInjectionMiddleware in production
- Guard with environment checks
- Use only in isolated testing environments

## Future Enhancements

### Planned Features

1. **Distributed Caching**: Redis/Memcached backend
2. **Circuit Breaker**: Automatic service degradation
3. **Request Transformation**: Modify requests before processing
4. **Response Compression**: Gzip/Brotli compression
5. **WebSocket Support**: Middleware for WebSocket connections
6. **Metrics Export**: Prometheus/OpenTelemetry integration
7. **A/B Testing**: Traffic splitting middleware
8. **Request Replay**: Record/replay for debugging

### Extension API

Create custom middleware:

```python
class CustomMiddleware(BaseMiddleware):
    """Your custom middleware."""

    async def before_request(
        self, context: MiddlewareContext
    ) -> MiddlewareContext | Response:
        """Pre-process request."""
        # Your logic here
        context.set("custom_data", "value")
        return context

    async def after_response(
        self, context: MiddlewareContext, response: Response
    ) -> Response:
        """Post-process response."""
        custom_data = context.get("custom_data")
        response.headers["X-Custom"] = custom_data
        return response

# Add to pipeline
pipeline.add_middleware(CustomMiddleware(
    config=MiddlewareConfig(priority=100)
))
```

## References

- FastAPI Middleware: https://fastapi.tiangolo.com/advanced/middleware/
- Starlette Middleware: https://www.starlette.io/middleware/
- Token Bucket Algorithm: https://en.wikipedia.org/wiki/Token_bucket
- Circuit Breaker Pattern: https://martinfowler.com/bliki/CircuitBreaker.html

---

**Document Version:** 1.0.0
**Last Updated:** 2025-10-05
**Maintainer:** FakeAI Team
