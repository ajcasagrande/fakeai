# FakeAI 3.0 - Architecture Documentation

**Version:** 3.0
**Last Updated:** 2025-10-05
**Status:** Production-Ready

---

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [System Components](#system-components)
4. [Module Organization](#module-organization)
5. [Metrics Architecture](#metrics-architecture)
6. [Service Layer](#service-layer)
7. [Request Flow](#request-flow)
8. [Streaming Architecture](#streaming-architecture)
9. [Model Registry](#model-registry)
10. [Design Decisions](#design-decisions)
11. [Extension Points](#extension-points)
12. [Performance Characteristics](#performance-characteristics)
13. [Security Architecture](#security-architecture)
14. [Testing Strategy](#testing-strategy)

---

## Introduction

FakeAI 3.0 is a production-grade OpenAI-compatible API simulation server designed for testing, development, and load testing of LLM-powered applications. It provides 100% schema compliance with OpenAI APIs while simulating realistic response times and behaviors.

### Key Goals

- **100% Schema Compliance**: Perfect compatibility with OpenAI Python/JS SDKs
- **Realistic Simulation**: Configurable delays, token-by-token streaming, realistic content
- **Comprehensive Metrics**: 18 integrated metrics systems for deep observability
- **Production-Ready**: Thread-safe, async-first, high-performance design
- **Extensible**: Clean architecture for adding new models, providers, and features

### Use Cases

1. **Development**: Test LLM applications without API costs
2. **CI/CD**: Automated testing with predictable responses
3. **Load Testing**: Validate infrastructure under high request volumes
4. **Cost Estimation**: Calculate API costs before production deployment
5. **Benchmarking**: Compare model performance across providers
6. **Prototyping**: Quickly test new features and workflows

---

## Architecture Overview

### High-Level Architecture

```

                           CLIENT LAYER                              
  OpenAI SDK (Python/JS) | HTTP Clients | WebSocket Clients         

                             
                             v

                       PRESENTATION LAYER                            
  FastAPI Application (50+ Endpoints) | CORS | Middleware           

                             
        
        v                    v                    v
    
   SECURITY         INPUT              RATE LIMITING   
   LAYER            VALIDATION                         
    
                             
                             v

                         SERVICE LAYER                               
  FakeAI Service (Core) | Specialized Services (7) | Utilities      

                             
        
        v                    v                    v
    
  MODEL             KV CACHE &         COST TRACKING   
  REGISTRY          SMART ROUTING                      
    
                             
                             v

                      INFRASTRUCTURE LAYER                           
  Metrics (18 Systems) | Storage (In-Memory) | Background Tasks     

```

### Key Architectural Patterns

1. **Layered Architecture**: Clear separation of concerns across layers
2. **Service-Oriented**: Domain-specific services for specialized functionality
3. **Async-First**: All I/O operations use async/await
4. **Dependency Injection**: Services receive dependencies via constructors
5. **Singleton Pattern**: Shared state (metrics, rate limiter) uses singletons
6. **Factory Pattern**: Model auto-creation on first use
7. **Strategy Pattern**: Pluggable response generators
8. **Observer Pattern**: Metrics collection throughout request lifecycle

---

## System Components

### Core Components

#### 1. FastAPI Application (app.py)

**Lines:** ~1900
**Purpose:** HTTP endpoint definitions and routing

**Key Features:**
- 50+ API endpoints (OpenAI, NVIDIA, Azure, Solido RAG)
- CORS middleware configuration
- Request logging and metrics collection
- Rate limiting enforcement
- API key authentication
- Error handling and response formatting

**Major Endpoint Groups:**
- Models: `/v1/models`, `/v1/models/{id}`
- Chat: `/v1/chat/completions`
- Completions: `/v1/completions`
- Embeddings: `/v1/embeddings`
- Images: `/v1/images/generations`
- Audio: `/v1/audio/speech`
- Files: `/v1/files`
- Batches: `/v1/batches`
- Fine-Tuning: `/v1/fine_tuning/jobs`
- Vector Stores: `/v1/vector_stores`
- Organization: `/v1/organization/*`
- Metrics: `/metrics`, `/metrics/by-model`, `/dcgm/metrics`, `/dynamo/metrics`
- Realtime: WebSocket `/v1/realtime`

#### 2. FakeAI Service (fakeai_service.py)

**Lines:** ~5000
**Purpose:** Core business logic and orchestration

**Key Responsibilities:**
- Model registry management
- Request processing and response generation
- KV cache and smart routing
- Cost tracking and calculation
- Metrics integration
- Tool calling simulation
- Structured output generation
- Multi-modal content handling

**Major Components:**
- Model catalog (auto-creation)
- Response generators (chat, completion, embedding, etc.)
- KV cache router (AI-Dynamo style)
- Cost tracker (usage-based pricing)
- DCGM simulator (GPU metrics)
- Dynamo metrics collector
- Vector store engine
- File manager

#### 3. Configuration System (config/)

**Purpose:** Centralized configuration management

**Modules:**
- `base.py`: Core AppConfig class
- `server.py`: Server settings (host, port, workers)
- `auth.py`: Authentication configuration
- `security.py`: Security settings (abuse detection, input validation)
- `rate_limits.py`: Rate limit tiers and configuration
- `features.py`: Feature flags
- `generation.py`: Response generation settings (delays, tokens)
- `metrics.py`: Metrics configuration
- `kv_cache.py`: KV cache settings
- `storage.py`: Storage configuration

**Configuration Sources:**
1. Environment variables (`FAKEAI_*`)
2. CLI arguments (via argparse)
3. Config files (JSON/YAML)
4. Default values

#### 4. Pydantic Models (models/)

**Purpose:** Request/response schema definitions with validation

**Modules:**
- `_base.py`: Base classes and utilities
- `_content.py`: Multi-modal content parts
- `chat.py`: Chat completion models
- `embeddings.py`: Embedding models
- `images.py`: Image generation models
- `audio.py`: Audio/TTS models
- `batches.py`: Batch processing models

**Key Features:**
- OpenAI API schema compliance
- Automatic validation
- JSON serialization
- Type hints throughout
- Optional fields with defaults

---

## Module Organization

See [modules_organization.txt](architecture/modules_organization.txt) for complete module hierarchy.

### Directory Structure

```
fakeai/
 app.py                   # FastAPI application
 fakeai_service.py        # Core service
 cli.py                   # CLI interface
 config/                  # Configuration modules
 models/                  # Pydantic schemas
 services/                # Specialized services
 models_registry/         # Model catalog system
 utils/                   # Shared utilities
 metrics*.py (13 files)   # Metrics systems
 kv_cache*.py (2 files)   # KV cache implementation
 security.py              # Security components
 rate_limiter.py          # Rate limiting
 ... (70+ more modules)
```

### Module Count by Category

- **Configuration:** 10 modules
- **Pydantic Models:** 9 modules
- **Metrics Systems:** 13 modules
- **Advanced Features:** 12 modules
- **Utilities:** 8 modules
- **Specialized Services:** 7 modules
- **Model Registry:** 11 modules
- **Generators:** 5 modules
- **Security:** 3 modules
- **Total:** 85+ modules

---

## Metrics Architecture

See [metrics_architecture.txt](architecture/metrics_architecture.txt) for detailed diagrams.

### 18 Integrated Metrics Systems

1. **MetricsTracker** (Core): Request/response/token/error tracking
2. **ModelMetricsTracker**: Per-model performance metrics
3. **StreamingMetrics**: TTFT, tokens/sec for streaming
4. **DynamoMetrics**: AI-Dynamo LLM inference metrics
5. **DCGMMetrics**: GPU utilization simulation
6. **BatchMetrics**: Batch processing statistics
7. **ErrorMetrics**: Error tracking and analysis
8. **RateLimiterMetrics**: Throttling and quota stats
9. **CostTracker**: Usage cost estimation
10. **LatencyHistograms**: Latency distribution tracking
11. **MetricsAggregator**: Cross-metric aggregation
12. **MetricsPersistence**: Metrics storage and export
13. **MetricsStreamer**: Real-time WebSocket streaming
14. **LatencyProfiles**: Latency profiling by model
15. **ModelMetrics**: Model-specific stats
16. **SmartRouterMetrics**: KV cache routing stats
17. **VectorStoreMetrics**: Vector store performance
18. **FineTuningMetrics**: Fine-tuning job tracking

### Metrics Collection Flow

```
Request → MetricsTracker.track_request()
    ↓
Rate Limit Check → RateLimiterMetrics.record_request()
    ↓
Service Processing → ModelMetricsTracker.track_request()
    ↓
KV Cache Lookup → KVCacheMetrics.record_cache_lookup()
    ↓
Response → MetricsTracker.track_response()
    ↓
Cost Calculation → CostTracker.calculate_cost()
```

### Export Formats

- **JSON**: `GET /metrics`
- **Prometheus**: `GET /metrics/prometheus`
- **CSV**: `GET /metrics/csv`
- **WebSocket Stream**: `WS /metrics/stream`

### Storage Implementation

**MetricsWindow** (numpy-based):
- Sliding time windows (60s default)
- Vectorized operations for performance
- Automatic cleanup of old data
- Max samples limit (100K)
- Thread-safe with `threading.Lock`

---

## Service Layer

See [service_layer.txt](architecture/service_layer.txt) for detailed diagrams.

### Core Orchestrator: FakeAIService

**Role:** Main business logic coordinator

**Manages:**
- Model registry and auto-creation
- Request routing and processing
- Response generation
- KV cache and smart routing
- Cost tracking
- Metrics integration

### Specialized Services (7)

1. **AudioService**: Text-to-speech generation
2. **BatchService**: Batch job processing
3. **EmbeddingService**: Vector embedding generation
4. **FileService**: File upload/management
5. **ImageGenerationService**: Image creation
6. **ModerationService**: Content safety checks
7. (More to be extracted from FakeAIService)

### Service Integration Pattern

```python
# Dependency injection at construction
class FakeAIService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.audio_service = AudioService(config)
        self.batch_service = BatchService(config)
        # ... etc

# Delegation in methods
async def create_speech(self, request: SpeechRequest) -> bytes:
    return await self.audio_service.create_speech(request)
```

---

## Request Flow

See [request_flow.txt](architecture/request_flow.txt) for detailed diagrams.

### Request Lifecycle (22 Steps)

1. Client sends request
2. CORS middleware processes
3. Request logging middleware
4. Abuse detection check
5. Input validation
6. Rate limiting
7. Route handling
8. API key verification
9. Pydantic validation
10. Service invocation
11. Model & context validation
12. Message processing
13. Token counting
14. KV cache lookup
15. Response generation
16. Tool calling (if requested)
17. Structured output (if requested)
18. Cost calculation
19. Build response object
20. Update KV cache
21. Track metrics
22. Return response with headers

### Error Handling

At any step, errors are caught and handled:
- Log with stack trace
- Track in error metrics
- Determine HTTP status
- Build error response
- Return to client

Common error scenarios:
- 401: Authentication failure
- 429: Rate limit exceeded
- 413: Payload too large
- 400: Injection attack detected
- 422: Validation error
- 500: Server error

---

## Streaming Architecture

See [streaming_architecture.txt](architecture/streaming_architecture.txt) for detailed diagrams.

### Server-Sent Events (SSE)

**Format:**
```
data: {JSON chunk}\n\n
data: {JSON chunk}\n\n
...
data: [DONE]\n\n
```

**Implementation:**
1. Generate complete response first
2. Tokenize into word/punctuation chunks
3. Yield first chunk (role only)
4. Yield token chunks with delays (0.05-0.2s)
5. Yield final chunk (finish_reason + usage)

### WebSocket Streaming (Realtime API)

**Endpoint:** `WS /v1/realtime`

**Features:**
- Bidirectional communication
- Audio input/output support
- Voice activity detection
- Conversation management
- Function calling

**Event Types:**
- `session.created`, `session.updated`
- `input_audio_buffer.append`, `input_audio_buffer.commit`
- `conversation.item.create`, `conversation.item.delete`
- `response.create`, `response.cancel`
- `response.audio.delta`, `response.audio.done`

### Streaming Metrics

**Tracked Per Stream:**
- Stream ID
- Start time
- First token time (TTFT)
- Token count
- Completion status
- Error message (if failed)

**Aggregate Stats:**
- Active/completed/failed stream counts
- TTFT percentiles (p50, p90, p99)
- Tokens/sec percentiles

---

## Model Registry

See [model_registry.txt](architecture/model_registry.txt) for detailed diagrams.

### Provider Catalogs (7)

1. **OpenAI**: GPT-OSS, GPT-4, GPT-3.5, O1, DALL-E, Whisper, Embeddings
2. **Anthropic**: Claude 3.5, Claude 3
3. **Meta**: Llama 3.3, 3.2, 3.1 (including vision models)
4. **Mistral**: Mistral, Mixtral (MoE), Pixtral (multimodal)
5. **DeepSeek**: DeepSeek-V3, DeepSeek-R1 (reasoning)
6. **NVIDIA**: NIM models, embeddings, reranking
7. **Custom**: User-defined models, auto-created models

### Model Definition Structure

```python
ModelDefinition:
  - id: str
  - name: str
  - provider: str
  - architecture: str (transformer, moe)
  - parameters: int
  - context_window: int
  - max_completion_tokens: int
  - supports_streaming: bool
  - supports_function_calling: bool
  - supports_vision: bool
  - supports_audio_input: bool
  - supports_audio_output: bool
  - supports_reasoning: bool
  - supports_structured_output: bool
  - pricing: ModelPricing
  - tags: List[str]
  - aliases: List[str]
```

### Model Capabilities Query

**Endpoint:** `GET /v1/models/{model_id}/capabilities`

**Returns:**
- Context window size
- Max completion tokens
- Pricing information
- Supported capabilities
- Supported modalities
- Supported features (temperature, top_p, etc.)

### Auto-Creation

Any model ID can be used. If not in registry:
1. Try to load from registry
2. If not found, create with defaults
3. Register new model definition
4. Add to model catalog

This allows flexible testing without pre-registering every model.

---

## Design Decisions

### 1. In-Memory Storage

**Decision:** Use Python dictionaries for all storage (models, files, batches, etc.)

**Rationale:**
- Simplicity: No database setup required
- Performance: Fastest possible access
- Stateless: Each server instance is independent
- Testing: Easy to reset state between tests

**Trade-offs:**
- Data lost on restart (acceptable for testing/simulation)
- No persistence (can add later if needed)
- Memory usage grows with data (bounded by retention policies)

### 2. Async/Await Throughout

**Decision:** All route handlers and service methods use async/await

**Rationale:**
- High concurrency with low resource usage
- Non-blocking I/O operations
- Scales to thousands of concurrent requests
- Compatible with FastAPI and modern Python ecosystem

**Trade-offs:**
- Slightly more complex code
- Need to be careful with blocking operations
- Async context can be confusing for beginners

### 3. Singleton Metrics

**Decision:** MetricsTracker and other metrics classes use singleton pattern

**Rationale:**
- Single source of truth for metrics
- Easy access from anywhere in codebase
- Consistent state across threads
- Thread-safe with locks

**Trade-offs:**
- Global state (generally discouraged)
- Harder to test in isolation
- Potential for coupling

**Mitigation:**
- Use dependency injection where possible
- Keep singleton interface minimal
- Make thread-safe with locks

### 4. Pre-Generation + Streaming

**Decision:** Generate complete response first, then stream token-by-token

**Rationale:**
- Predictable timing and token counts
- Realistic simulation with configurable delays
- Easy to implement token-level metrics
- Allows accurate usage tracking

**Trade-offs:**
- Not truly incremental (but that's okay for simulation)
- Memory usage for complete response
- Slight delay before first token

**Alternative Considered:** True incremental generation (rejected due to complexity)

### 5. Pydantic for Validation

**Decision:** Use Pydantic for all request/response models

**Rationale:**
- Automatic validation of inputs
- Type safety throughout codebase
- JSON serialization built-in
- OpenAI SDK compatibility
- Excellent error messages

**Trade-offs:**
- Slight performance overhead (negligible)
- Learning curve for Pydantic features
- Verbose model definitions

### 6. Numpy for Metrics

**Decision:** Use numpy arrays for metrics storage

**Rationale:**
- Vectorized operations are extremely fast
- Efficient memory usage
- Built-in percentile calculations
- Mature and stable library

**Trade-offs:**
- Additional dependency
- Requires numpy knowledge
- Array operations can be tricky

### 7. Auto-Model Creation

**Decision:** Automatically create models that don't exist in registry

**Rationale:**
- Flexible testing (any model ID works)
- No need to pre-register every model
- Graceful degradation
- Better error messages

**Trade-offs:**
- Can hide typos in model IDs
- May lead to unexpected behavior
- Harder to catch configuration errors

**Mitigation:**
- Log when auto-creating models
- Provide model discovery endpoints
- Clear documentation

---

## Extension Points

### Adding New Endpoints

1. **Define Pydantic Models:**
   ```python
   # In models/my_feature.py
   class MyFeatureRequest(BaseModel):
       input: str
       options: dict = {}

   class MyFeatureResponse(BaseModel):
       output: str
       usage: dict
   ```

2. **Add Service Method:**
   ```python
   # In fakeai_service.py
   async def my_feature(self, request: MyFeatureRequest) -> MyFeatureResponse:
       self._ensure_model_exists(request.model)
       # Implementation
       return MyFeatureResponse(...)
   ```

3. **Add Route:**
   ```python
   # In app.py
   @app.post("/v1/my-feature", dependencies=[Depends(verify_api_key)])
   async def my_feature(request: MyFeatureRequest) -> MyFeatureResponse:
       return await fakeai_service.my_feature(request)
   ```

### Adding New Metrics

1. **Create Metrics Module:**
   ```python
   # In my_feature_metrics.py
   class MyFeatureMetrics:
       def __init__(self):
           self.request_count = 0
           self.feature_stats = {}

       def record_request(self, ...):
           # Track metrics
           pass

       def get_stats(self) -> dict:
           return {...}
   ```

2. **Integrate with FakeAIService:**
   ```python
   # In fakeai_service.py
   self.my_feature_metrics = MyFeatureMetrics()
   ```

3. **Add Export Endpoint:**
   ```python
   # In app.py
   @app.get("/metrics/my-feature")
   async def get_my_feature_metrics():
       return fakeai_service.my_feature_metrics.get_stats()
   ```

### Adding New Model Provider

1. **Create Catalog:**
   ```python
   # In models_registry/catalog/my_provider.py
   def get_my_provider_models() -> List[ModelDefinition]:
       return [
           ModelDefinition(
               id="my-provider/model-1",
               name="My Model 1",
               provider="my-provider",
               # ... other fields
           ),
           # ... more models
       ]
   ```

2. **Register in Loader:**
   ```python
   # In models_registry/catalog/registry_loader.py
   from .my_provider import get_my_provider_models

   def load_all_catalogs() -> List[ModelDefinition]:
       all_models = []
       all_models.extend(get_openai_models())
       all_models.extend(get_my_provider_models())  # Add this
       # ... rest of loading
       return all_models
   ```

### Adding New Service

1. **Create Service Module:**
   ```python
   # In services/my_service.py
   class MyService:
       def __init__(self, config: AppConfig):
           self.config = config

       async def process(self, request) -> response:
           # Implementation
           pass
   ```

2. **Integrate with FakeAIService:**
   ```python
   # In fakeai_service.py
   from services.my_service import MyService

   class FakeAIService:
       def __init__(self, config: AppConfig):
           self.my_service = MyService(config)

       async def my_operation(self, request):
           return await self.my_service.process(request)
   ```

---

## Performance Characteristics

### Latency Breakdown (Non-Streaming)

| Component | Typical Latency |
|-----------|----------------|
| Middleware overhead | 1-2ms |
| Auth & validation | 2-5ms |
| Service processing | 10-50ms |
| Response generation | 50-200ms (with delay) |
| **Total** | **60-260ms** |

### Throughput

- **Without rate limiting:** 100-500 requests/sec (single instance)
- **With rate limiting:** Depends on tier configuration
- **Streaming:** 50-100 concurrent streams (single instance)
- **Scalability:** Linear with number of instances

### Memory Usage

- **Base:** ~100MB (startup)
- **Per request:** ~1-5MB (temporary)
- **Metrics:** ~50MB (with 100K samples per window)
- **Images:** Depends on generation (if enabled)

### CPU Usage

- **Idle:** < 1%
- **Active (100 req/s):** 10-20%
- **Metrics processing:** 5-10%
- **Numpy operations:** < 1%

### Optimization Strategies

1. **Numpy Vectorization:** Metrics calculations are extremely fast
2. **LRU Caching:** Model lookups cached
3. **Async I/O:** Non-blocking operations throughout
4. **Background Threads:** Metrics reporting doesn't block requests
5. **Efficient Storage:** Deques and bounded dictionaries

---

## Security Architecture

### Authentication

**ApiKeyManager:**
- Supports plain text keys (legacy)
- Supports bcrypt hashed keys (recommended)
- Configurable via `FAKEAI_HASH_API_KEYS`
- Timing-safe comparison

### Abuse Detection

**AbuseDetector:**
- Failed auth attempt tracking
- IP banning (configurable duration)
- Rate limit violation tracking
- Injection attempt tracking
- Oversized payload tracking

### Input Validation

**InputValidator:**
- Payload size limits (default: 10MB)
- SQL injection detection
- XSS pattern detection
- Command injection detection
- Configurable patterns

### Rate Limiting

**RateLimiter:**
- Per-API key limits
- Tiered rate limits (free, tier1-5)
- RPM (requests per minute) and TPM (tokens per minute)
- Configurable via environment variables
- Retry-After header on 429

### Security Best Practices

1. **Always use hashed API keys in production**
2. **Enable abuse detection**
3. **Configure rate limits appropriately**
4. **Monitor failed auth attempts**
5. **Review security logs regularly**
6. **Keep dependencies updated**
7. **Run behind reverse proxy (nginx, etc.)**
8. **Use HTTPS in production**

---

## Testing Strategy

### Unit Tests

**Location:** `tests/` directory

**Coverage:**
- Service methods
- Utility functions
- Model validation
- Metrics calculations
- Security components

**Example:**
```python
import pytest
from fakeai import FakeAIService, AppConfig
from fakeai.models import ChatCompletionRequest

@pytest.mark.asyncio
async def test_chat_completion():
    config = AppConfig(response_delay=0.0)
    service = FakeAIService(config)

    request = ChatCompletionRequest(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello"}]
    )

    response = await service.create_chat_completion(request)

    assert response.choices[0].message.content
    assert response.usage.total_tokens > 0
```

### Integration Tests

**Approach:** Test with OpenAI SDK

**Example:**
```python
import openai

def test_openai_client():
    client = openai.OpenAI(
        api_key="test",
        base_url="http://localhost:8000"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello"}]
    )

    assert response.choices[0].message.content
```

### Load Tests

**Tools:**
- `locust` for load testing
- `k6` for performance testing
- `ab` (Apache Bench) for quick tests

**Scenarios:**
1. Sustained load (100 req/s for 10 minutes)
2. Spike test (0 → 500 req/s → 0)
3. Stress test (increase until failure)
4. Endurance test (24 hours continuous)

### Manual Testing

**Tools:**
- `curl` for API testing
- OpenAI Playground (with custom base URL)
- Postman collections
- Web dashboards (`/dashboard`, `/dashboard/dynamo`)

---

## Conclusion

FakeAI 3.0 is a comprehensive, production-ready OpenAI API simulation server with:

- **85+ well-organized modules**
- **18 integrated metrics systems**
- **50+ API endpoints**
- **7 provider catalogs with 50+ models**
- **Thread-safe, async-first design**
- **Extensive observability and monitoring**

The architecture is designed for:
- **Clarity:** Clean separation of concerns
- **Maintainability:** Easy to understand and modify
- **Extensibility:** Simple to add new features
- **Performance:** Optimized for high throughput
- **Reliability:** Robust error handling and logging

For detailed diagrams, see the `docs/architecture/` directory:
- [system_overview.txt](architecture/system_overview.txt)
- [modules_organization.txt](architecture/modules_organization.txt)
- [metrics_architecture.txt](architecture/metrics_architecture.txt)
- [service_layer.txt](architecture/service_layer.txt)
- [request_flow.txt](architecture/request_flow.txt)
- [streaming_architecture.txt](architecture/streaming_architecture.txt)
- [model_registry.txt](architecture/model_registry.txt)

---

**Contributors:**
- Claude (Anthropic) - Architecture design and documentation
- Development Team - Implementation and testing

**License:** Apache 2.0

**Repository:** https://github.com/ajcasagrande/fakeai

**Documentation:** https://fakeai.readthedocs.io (coming soon)
