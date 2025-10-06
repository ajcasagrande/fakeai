# CLAUDE.md - FakeAI Project Knowledge Base

**Version:** 3.0.0 "Perfection Edition"
**Purpose:** Essential knowledge for AI assistants working on FakeAI
**Last Updated:** October 5, 2025

---

## Project Overview

FakeAI is the most advanced OpenAI-compatible API server for testing and development, featuring **90+ beautifully architected modules**, **1,400+ comprehensive tests**, and **production-grade engineering** throughout.

**Core Goal:** 100% schema compliance with OpenAI API specs

**Key Design Principles:**
- **Modular Architecture** - 90+ single-responsibility modules
- **Zero Duplication** - Shared utilities eliminate repetition
- **Test-Driven** - 90%+ coverage (1,400+ tests, 0.87:1 test-to-code ratio)
- **Production-Ready** - Thread-safe singletons, async throughout, battle-tested patterns
- **Schema-First** - Pydantic validation, backward compatibility
- **Extensible** - Easy to add endpoints, models, features

---

## Architecture

### Module Organization (90+ Modules)

```
fakeai/
 Core Application (4 modules)
    app.py                    # FastAPI routes (100+ endpoints)
    fakeai_service.py         # Main service orchestration
    cli.py                    # CLI interface (cyclopts)
    async_server.py           # Async server (uvloop)

 Configuration System (11 modules)
    config/__init__.py        # Unified AppConfig
    config/base.py            # Base configuration classes
    config/server.py          # Server settings
    config/auth.py            # Authentication config
    config/rate_limits.py     # Rate limiting settings
    config/kv_cache.py        # KV cache config
    config/generation.py      # Generation settings
    config/metrics.py         # Metrics config
    config/storage.py         # Storage settings
    config/security.py        # Security config
    config/features.py        # Feature flags

 Data Models (7 organized modules)
    models/__init__.py        # Re-export all models
    models/_base.py           # Base models (Model, Usage, etc.)
    models/_content.py        # Content parts (Text, Image, Video, Audio)
    models/chat.py            # Chat completion models (23 models)
    models/embeddings.py      # Embedding models (4 models)
    models/images.py          # Image generation models (8 models)
    models/audio.py           # Audio models (9 models)
    models/batches.py         # Batch processing models (6 models)

 Model Registry (9 modules)
    models_registry/registry.py       # Central ModelRegistry
    models_registry/definition.py     # ModelDefinition schema
    models_registry/capabilities.py   # ModelCapabilities schema
    models_registry/discovery.py      # Fuzzy matching, inference
    models_registry/catalog/          # Provider catalogs (6 providers, 43 models)
        openai.py, anthropic.py, meta.py, mistral.py, deepseek.py, nvidia.py
        registry_loader.py

 Service Layer (6 extracted services)
    services/embedding_service.py         # 218 lines, 25 tests
    services/image_generation_service.py  # 282 lines, 30 tests
    services/audio_service.py             # 160 lines, 24 tests
    services/moderation_service.py        # 370 lines, 21 tests
    services/file_service.py              # 374 lines, 43 tests
    services/batch_service.py             # 560 lines, 23 tests

 Shared Utilities (8 modules - ZERO duplication)
    shared/content_utils.py       # Multi-modal content extraction (8 functions, 62 tests)
    shared/delay_utils.py         # Named delay patterns (15 functions, 31 tests)
    shared/id_generators.py       # All ID types (37 functions, 62 tests)
    shared/timestamp_utils.py     # Time operations (13 functions, 36 tests)
    shared/usage_builder.py       # Fluent Usage API (29 tests)
    shared/decorators.py          # Common patterns (10 decorators, 40 tests)
    shared/validators.py          # Parameter validation (24 validators, 95 tests)

 Utilities (6 focused modules)
    utils/tokens.py               # Token calculation
    utils/embeddings.py           # Embedding generation
    utils/text_generation.py      # Text generation helpers
    utils/audio_generation.py     # Audio synthesis helpers
    utils/async_executor.py       # Async execution patterns

 Metrics Systems (18 modules)
    metrics.py                    # Core MetricsTracker (singleton)
    metrics_aggregator.py         # Cross-system aggregation
    metrics_persistence.py        # SQLite time-series storage
    metrics_streaming.py          # WebSocket real-time streaming
    batch_metrics.py              # Batch processing metrics
    model_metrics.py              # Per-model tracking
    streaming_metrics.py          # Streaming-specific metrics
    error_metrics.py              # Error tracking
    rate_limiter_metrics.py       # Rate limiting metrics
    cost_tracker.py               # Cost analytics and optimization
    latency_histograms.py         # HDR histogram percentiles
    latency_profiles.py           # 37 model-specific profiles
    kv_cache.py                   # KV cache (radix tree)
    kv_cache_advanced.py          # Advanced cache features
    smart_router_advanced.py      # Smart routing algorithms
    dynamo_metrics.py             # AI-Dynamo metrics
    dynamo_metrics_advanced.py    # Advanced Dynamo features
    dcgm_metrics.py               # DCGM GPU telemetry (100+ fields)

 Content Generation (6 modules)
    tokenizers.py                 # Tiktoken integration (95%+ accuracy)
    llm_generator.py              # Optional LLM inference (DistilGPT-2/GPT-2)
    semantic_embeddings.py        # Sentence transformers
    vector_store_engine.py        # Vector store operations
    image_generator.py            # Image generation (actual PNGs)
    audio_transcriber.py          # Whisper-compatible transcription

 Infrastructure (10 modules)
     error_injector.py             # Error injection for testing
     context_validator.py          # Context length validation
     rate_limiter.py               # Rate limiting enforcement
     security.py                   # Security features (abuse detection)
     file_manager.py               # File storage and management
     tool_calling.py               # Function calling support
     structured_outputs.py         # JSON Schema validation
     logprobs_enhanced.py          # Enhanced logprobs
     vision.py                     # Vision processing
     video.py                      # Video processing (Cosmos)
```

### Request Flow

```
Client Request
    ↓
FastAPI Middleware
    ↓
Authentication (API Key via config/auth.py)
    ↓
Rate Limiting (if enabled via rate_limiter.py)
    ↓
Error Injection (if enabled via error_injector.py)
    ↓
Route Handler (app.py)
    ↓
Request Validation (Pydantic models/*)
    ↓
Service Layer (services/* or fakeai_service.py)
    ↓
Model Auto-Creation (_ensure_model_exists via models_registry)
    ↓
Content Extraction (shared/content_utils.py)
    ↓
Response Generation (with delays via shared/delay_utils.py)
    ↓
ID Generation (shared/id_generators.py)
    ↓
Usage Construction (shared/usage_builder.py)
    ↓
KV Cache Update (if enabled via kv_cache.py)
    ↓
Metrics Recording (metrics_*.py systems)
    ↓
Response Serialization (Pydantic)
    ↓
Client Response
```

---

## Critical Implementation Patterns

### 1. Shared Utilities (ZERO Duplication)

**All common patterns are in `/home/anthony/projects/fakeai/fakeai/shared/`:**

#### Content Extraction (`shared/content_utils.py`)
```python
from fakeai.shared.content_utils import extract_text_content, extract_all_content_parts

# Multi-modal content extraction
text = extract_text_content(message.content)  # Handles str, list, None
parts = extract_all_content_parts(message.content)  # Returns list of content parts
```

**8 functions, 62 tests:**
- `extract_text_content()` - Extract text from any content format
- `extract_all_content_parts()` - Extract all content parts
- `has_image_content()`, `has_audio_content()`, `has_video_content()`
- `count_content_parts()`, `get_first_text_content()`, `is_text_only_content()`

#### Delay Patterns (`shared/delay_utils.py`)
```python
from fakeai.shared.delay_utils import generate_chat_delay, generate_embedding_delay

# Named delay patterns (no magic numbers!)
await generate_chat_delay()  # TTFT: 20ms, ITL: 5ms with ±10% variance
await generate_embedding_delay()  # Realistic embedding delay
```

**15 functions, 31 tests:**
- `generate_chat_delay()`, `generate_completion_delay()`, `generate_embedding_delay()`
- `generate_image_delay()`, `generate_audio_delay()`, `generate_moderation_delay()`
- `generate_streaming_first_token_delay()`, `generate_streaming_inter_token_delay()`
- Plus variance helpers, custom delays, synchronous variants

#### ID Generation (`shared/id_generators.py`)
```python
from fakeai.shared.id_generators import generate_chat_completion_id, generate_embedding_id

# All ID types (37 functions)
chat_id = generate_chat_completion_id()  # chatcmpl-xxx
embedding_id = generate_embedding_id()   # emb-xxx
batch_id = generate_batch_id()           # batch-xxx
```

**37 functions, 62 tests** - Every ID type in the OpenAI API

#### Timestamp Operations (`shared/timestamp_utils.py`)
```python
from fakeai.shared.timestamp_utils import get_current_timestamp, format_iso_timestamp

# Time operations
timestamp = get_current_timestamp()  # Unix timestamp
iso = format_iso_timestamp(timestamp)  # ISO 8601
```

**13 functions, 36 tests:**
- `get_current_timestamp()`, `get_timestamp_ms()`, `get_timestamp_ns()`
- `format_iso_timestamp()`, `parse_iso_timestamp()`
- `add_seconds()`, `subtract_seconds()`, date calculations

#### Usage Construction (`shared/usage_builder.py`)
```python
from fakeai.shared.usage_builder import UsageBuilder

# Fluent API for Usage objects
usage = (UsageBuilder()
    .with_prompt_tokens(100)
    .with_completion_tokens(50)
    .with_reasoning_tokens(25)  # For reasoning models
    .with_audio_tokens(30)      # For audio
    .with_cached_tokens(20)     # For prompt caching
    .build())
```

**29 tests** - Covers all usage field combinations

#### Decorators (`shared/decorators.py`)
```python
from fakeai.shared.decorators import with_metrics, with_error_handling, with_retry

# Common patterns
@with_metrics(endpoint="/v1/chat/completions")
@with_error_handling
@with_retry(max_attempts=3)
async def my_handler(...):
    ...
```

**10 decorators, 40 tests:**
- `@with_metrics`, `@with_error_handling`, `@with_retry`
- `@with_timeout`, `@with_rate_limit`, `@with_auth`
- `@with_validation`, `@with_caching`, `@with_logging`
- `@with_profiling`

#### Validators (`shared/validators.py`)
```python
from fakeai.shared.validators import validate_temperature, validate_max_tokens

# Parameter validation
validate_temperature(0.7)  # Raises if invalid
validate_max_tokens(4096, model="openai/gpt-oss-120b")
```

**24 validators, 95 tests:**
- `validate_temperature()`, `validate_top_p()`, `validate_frequency_penalty()`
- `validate_presence_penalty()`, `validate_max_tokens()`, `validate_n()`
- `validate_stop_sequences()`, `validate_response_format()`
- Plus validators for all OpenAI API parameters

### 2. Model Registry (Capability-Based Queries)

**Auto-discovery, fuzzy matching, capability queries:**

```python
from fakeai.models_registry import get_global_registry

registry = get_global_registry()

# Fuzzy matching (handles typos, variations)
model = registry.discover_model("gpt4o")  # Finds "openai/gpt-oss-120b"
model = registry.discover_model("llama3")  # Finds "meta-llama/Llama-3.1-8B-Instruct"

# Capability queries
vision_models = registry.search(capabilities={"vision": True})
reasoning_models = registry.search(capabilities={"reasoning": True})
moe_models = registry.search(capabilities={"moe": True})

# Provider filtering
nvidia_models = registry.search(provider="nvidia")
openai_models = registry.search(provider="openai")

# Get model definition
definition = registry.get_model("openai/gpt-oss-120b")
print(definition.context_window)  # 128000
print(definition.capabilities.vision)  # True
```

**9 modules, 48 tests, 43 pre-configured models**

### 3. Service Layer Pattern

**Extracted services follow consistent patterns:**

```python
from fakeai.services.embedding_service import EmbeddingService
from fakeai.config import AppConfig

# Initialize service
config = AppConfig()
service = EmbeddingService(config)

# Use service (all async)
response = await service.create_embedding(request)

# Services handle:
# 1. Model validation (_ensure_model_exists)
# 2. Content extraction (shared/content_utils.py)
# 3. Response generation (with delays via shared/delay_utils.py)
# 4. ID generation (shared/id_generators.py)
# 5. Usage construction (shared/usage_builder.py)
# 6. Metrics recording (metrics.py)
```

**6 extracted services, 166 tests:**
- `EmbeddingService` (218 lines, 25 tests)
- `ImageGenerationService` (282 lines, 30 tests)
- `AudioService` (160 lines, 24 tests)
- `ModerationService` (370 lines, 21 tests)
- `FileService` (374 lines, 43 tests)
- `BatchService` (560 lines, 23 tests)

### 4. Configuration System

**Modular configuration with type safety:**

```python
from fakeai.config import AppConfig
from fakeai.config.auth import AuthConfig
from fakeai.config.rate_limits import RateLimitConfig

# Unified config (auto-loads from environment)
config = AppConfig()

# Access domain-specific configs
auth_config = config.auth       # AuthConfig
rate_config = config.rate_limit  # RateLimitConfig
kv_config = config.kv_cache      # KVCacheConfig

# All configs support:
# 1. Environment variables (FAKEAI_*)
# 2. CLI argument overrides
# 3. Type validation (Pydantic)
# 4. Sensible defaults
```

**11 domain configs, 79 tests:**
- `ServerConfig`, `AuthConfig`, `RateLimitConfig`, `KVCacheConfig`
- `GenerationConfig`, `MetricsConfig`, `StorageConfig`, `SecurityConfig`
- `FeaturesConfig`, `CORSConfig`, `LoggingConfig`

### 5. Metrics Systems (18 Production-Grade Modules)

**Real metrics, no stubs:**

```python
from fakeai.metrics import MetricsTracker
from fakeai.kv_cache import KVCacheMetrics
from fakeai.model_metrics import ModelMetricsTracker

# Singleton pattern (thread-safe)
metrics = MetricsTracker()
kv_metrics = KVCacheMetrics()
model_metrics = ModelMetricsTracker()

# Record metrics
metrics.record_request(endpoint="/v1/chat/completions", latency_ms=123.45)
kv_metrics.record_cache_lookup(endpoint="/v1/chat/completions",
                                prompt_tokens=100, matched_tokens=80)
model_metrics.record_request(model="openai/gpt-oss-120b",
                              endpoint="/v1/chat/completions",
                              latency_ms=123.45, tokens=150)

# Get stats (all thread-safe)
stats = metrics.get_stats()
cache_stats = kv_metrics.get_stats()
model_stats = model_metrics.get_model_stats("openai/gpt-oss-120b")
```

**18 systems, 300+ tests:**
- Core metrics, aggregation, persistence, streaming
- KV cache, DCGM, Dynamo, per-model metrics
- Cost tracking, histograms, error tracking

### 6. Multi-Modal Content (Use Shared Utils!)

**Always use `shared/content_utils.py`, never inline extraction:**

```python
from fakeai.shared.content_utils import (
    extract_text_content,
    extract_all_content_parts,
    has_image_content,
    has_video_content
)

# Extract text from any content format
text = extract_text_content(message.content)  # Handles str, list[ContentPart], None

# Check for specific content types
if has_image_content(message.content):
    # Handle vision request
    pass

if has_video_content(message.content):
    # Handle video request
    pass

# Get all content parts
parts = extract_all_content_parts(message.content)
for part in parts:
    if part.type == "text":
        process_text(part.text)
    elif part.type == "image_url":
        process_image(part.image_url.url)
```

### 7. Streaming Implementation

**Token-by-token streaming with realistic delays:**

```python
from fakeai.shared.delay_utils import (
    generate_streaming_first_token_delay,
    generate_streaming_inter_token_delay
)
from fakeai.shared.id_generators import generate_chat_completion_id
from fakeai.utils.tokens import tokenize_text

async def stream_response(content: str, model: str):
    # Generate complete response first
    response_id = generate_chat_completion_id()
    tokens = tokenize_text(content)  # Regex-based tokenization

    # First chunk: role only
    await generate_streaming_first_token_delay()
    yield first_chunk(response_id)

    # Stream tokens with inter-token delay
    for token in tokens:
        await generate_streaming_inter_token_delay()
        yield content_chunk(response_id, token)

    # Final chunk: finish_reason
    yield final_chunk(response_id, finish_reason="stop")
```

**Key points:**
- TTFT (Time To First Token): 20ms default (configurable via latency profiles)
- ITL (Inter-Token Latency): 5ms default with ±10% variance
- Use `shared/delay_utils.py` for all delays
- Use `shared/id_generators.py` for IDs
- Use `utils/tokens.py` for tokenization

### 8. Model Auto-Creation with Registry

**Models auto-created on first use:**

```python
from fakeai.models_registry import get_global_registry

def _ensure_model_exists(self, model_id: str) -> None:
    """Ensure model exists in registry, create if needed."""
    registry = get_global_registry()

    # Check if model exists
    if registry.get_model(model_id):
        return

    # Try discovery (fuzzy matching)
    definition = registry.discover_model(model_id)
    if definition:
        return

    # Create custom model
    registry.register_model(
        model_id=model_id,
        provider="custom",
        context_window=128000,
        created=int(time.time()) - 10000
    )
```

**Benefits:**
- Any model ID automatically works
- Fuzzy matching handles typos
- Capability queries work immediately
- Pre-configured models have realistic specs

### 9. Error Injection for Testing

**Configurable failure simulation:**

```python
from fakeai.error_injector import get_error_injector, ErrorType

# Get singleton
injector = get_error_injector()

# Configure (via environment or programmatically)
injector.set_enabled(True)
injector.set_global_error_rate(0.15)  # 15% error rate
injector.set_endpoint_error_rate("/v1/chat/completions", 0.20)

# Check if should inject error
should_inject, error_response = injector.should_inject_error("/v1/chat/completions")
if should_inject:
    raise HTTPException(
        status_code=error_response["status_code"],
        detail=error_response["error"]
    )

# Simulate load spike
injector.simulate_load_spike(duration_seconds=10.0, error_rate_multiplier=3.0)

# Get statistics
stats = injector.get_error_stats()
```

**Error types:**
- `INTERNAL_ERROR` (500), `BAD_GATEWAY` (502), `SERVICE_UNAVAILABLE` (503)
- `GATEWAY_TIMEOUT` (504), `RATE_LIMIT_QUOTA` (429), `CONTEXT_LENGTH_EXCEEDED` (400)

**Configuration:**
```bash
export FAKEAI_ERROR_INJECTION_ENABLED=true
export FAKEAI_ERROR_INJECTION_RATE=0.15
export FAKEAI_ERROR_INJECTION_TYPES='["internal_error", "service_unavailable"]'
```

---

## API Endpoints

### Core Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/models` | GET | List models (auto-creates via `_ensure_model_exists`) |
| `/v1/models/{id}` | GET | Get model details (from registry) |
| `/v1/models/{id}/capabilities` | GET | Get model capabilities (from registry) |
| `/v1/chat/completions` | POST | Chat (streaming/non-streaming, 62 params) |
| `/v1/completions` | POST | Text completion (legacy) |
| `/v1/embeddings` | POST | L2-normalized embeddings (hash-based or semantic) |
| `/v1/images/generations` | POST | Image generation simulation (ImageGenerationService) |
| `/v1/audio/speech` | POST | Text-to-speech synthesis (AudioService) |
| `/v1/audio/transcriptions` | POST | Audio transcription (Whisper-compatible) |
| `/v1/moderations` | POST | Content moderation (ModerationService) |
| `/v1/files` | GET/POST/DELETE | File management (FileService) |
| `/v1/batches` | POST/GET | Batch processing (BatchService) |
| `/v1/realtime` | WebSocket | Real-time bidirectional streaming |
| `/v1/responses` | POST | Stateful conversation API |
| `/v1/ranking` | POST | NVIDIA NIM reranking |
| `/rag/api/prompt` | POST | Solido RAG retrieval-augmented generation |

### Monitoring Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Basic health check |
| `/metrics` | GET | Server metrics (JSON) |
| `/metrics/prometheus` | GET | Prometheus metrics |
| `/kv-cache/metrics` | GET | KV cache performance |
| `/dcgm/metrics` | GET | DCGM GPU metrics (Prometheus) |
| `/dynamo/metrics` | GET | AI-Dynamo metrics (Prometheus) |
| `/metrics/streaming` | WebSocket | Real-time metrics streaming |

---

## Code Standards

### Style
- **PEP 8** - Python style guide
- **Black** (88 char) - Code formatting
- **isort** - Import sorting
- **Type hints** - Always use (Python 3.10+ union syntax: `str | int | None`)

### Naming
- **PascalCase** - Classes (`ChatCompletionRequest`, `MetricsTracker`)
- **snake_case** - Functions, variables (`extract_text_content`, `generate_chat_delay`)
- **UPPER_CASE** - Constants (`MAX_TOKENS`, `DEFAULT_TEMPERATURE`)
- **_leading_underscore** - Private (`_ensure_model_exists`, `_generate_response`)

### Architecture
- **Single Responsibility** - Each module has one clear purpose
- **DRY** - Use shared utilities, never duplicate
- **Async Throughout** - Always `async/await` for I/O
- **Thread-Safe** - Singleton patterns with locks
- **Type-Safe** - Full type hints everywhere
- **Test-Driven** - Write tests first, aim for 90%+ coverage

### Common Patterns
```python
# 1. Use shared utilities (NEVER inline common patterns)
from fakeai.shared.content_utils import extract_text_content
from fakeai.shared.delay_utils import generate_chat_delay
from fakeai.shared.id_generators import generate_chat_completion_id
from fakeai.shared.usage_builder import UsageBuilder

# 2. Use model registry (NEVER hardcode models)
from fakeai.models_registry import get_global_registry

# 3. Use services (NEVER put business logic in routes)
from fakeai.services.embedding_service import EmbeddingService

# 4. Use config (NEVER hardcode settings)
from fakeai.config import AppConfig

# 5. Record metrics (ALWAYS track performance)
from fakeai.metrics import MetricsTracker
```

---

## Common Pitfalls

###  DON'T DO THIS:
```python
# DON'T inline content extraction
if isinstance(content, str):
    text = content
elif isinstance(content, list):
    text = " ".join([p["text"] for p in content if p["type"] == "text"])

# DON'T use magic numbers for delays
await asyncio.sleep(0.05)

# DON'T hardcode ID generation
completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"

# DON'T build Usage manually
usage = Usage(
    prompt_tokens=prompt_tokens,
    completion_tokens=completion_tokens,
    total_tokens=prompt_tokens + completion_tokens
)
```

###  DO THIS INSTEAD:
```python
# DO use shared utilities
from fakeai.shared.content_utils import extract_text_content
from fakeai.shared.delay_utils import generate_streaming_inter_token_delay
from fakeai.shared.id_generators import generate_chat_completion_id
from fakeai.shared.usage_builder import UsageBuilder

text = extract_text_content(content)
await generate_streaming_inter_token_delay()
completion_id = generate_chat_completion_id()
usage = UsageBuilder().with_prompt_tokens(prompt_tokens).with_completion_tokens(completion_tokens).build()
```

### Key Rules
1. **Multi-modal content:** Always use `extract_text_content()` from `shared/content_utils.py`
2. **Delays:** Always use functions from `shared/delay_utils.py`
3. **IDs:** Always use generators from `shared/id_generators.py`
4. **Usage:** Always use `UsageBuilder` from `shared/usage_builder.py`
5. **Models:** Always use `models_registry` for model operations
6. **Config:** Always use `AppConfig` and domain configs
7. **Services:** Always use service layer for business logic
8. **Metrics:** Always record metrics with `MetricsTracker`
9. **Tests:** Always write tests (aim for 90%+ coverage)
10. **Async:** Always use `async/await` for I/O operations

---

## Adding New Endpoints

### Step-by-Step Process

1. **Define Models** (`models/` or create new module)
```python
# fakeai/models/my_feature.py
from pydantic import BaseModel, Field
from fakeai.models._base import Usage

class MyFeatureRequest(BaseModel):
    model: str
    prompt: str
    # ... other fields with defaults

class MyFeatureResponse(BaseModel):
    id: str
    object: str = "my.feature.response"
    created: int
    model: str
    result: str
    usage: Usage
```

2. **Create Service** (`services/` if complex)
```python
# fakeai/services/my_feature_service.py
from fakeai.config import AppConfig
from fakeai.shared.content_utils import extract_text_content
from fakeai.shared.delay_utils import generate_custom_delay
from fakeai.shared.id_generators import generate_custom_id
from fakeai.shared.usage_builder import UsageBuilder
from fakeai.models.my_feature import MyFeatureRequest, MyFeatureResponse

class MyFeatureService:
    def __init__(self, config: AppConfig):
        self.config = config
        self._ensure_model_exists = ...  # Inject from main service

    async def create_my_feature(self, request: MyFeatureRequest) -> MyFeatureResponse:
        # 1. Ensure model exists
        self._ensure_model_exists(request.model)

        # 2. Extract content
        prompt_text = extract_text_content(request.prompt)

        # 3. Generate response (with delay)
        await generate_custom_delay(self.config, delay_type="my_feature")
        result = self._generate_result(prompt_text)

        # 4. Build usage
        usage = (UsageBuilder()
            .with_prompt_tokens(len(prompt_text.split()))
            .with_completion_tokens(len(result.split()))
            .build())

        # 5. Return response
        return MyFeatureResponse(
            id=generate_custom_id("myfeat"),
            created=int(time.time()),
            model=request.model,
            result=result,
            usage=usage
        )
```

3. **Add Route** (`app.py`)
```python
from fakeai.services.my_feature_service import MyFeatureService
from fakeai.models.my_feature import MyFeatureRequest, MyFeatureResponse

# In app.py
@app.post("/v1/my-feature", response_model=MyFeatureResponse)
async def create_my_feature(
    request: MyFeatureRequest,
    api_key: str = Depends(verify_api_key)
):
    service = MyFeatureService(config)
    service._ensure_model_exists = fakeai_service._ensure_model_exists
    return await service.create_my_feature(request)
```

4. **Write Tests** (`tests/test_my_feature.py`)
```python
import pytest
from fakeai.services.my_feature_service import MyFeatureService
from fakeai.models.my_feature import MyFeatureRequest
from fakeai.config import AppConfig

@pytest.mark.asyncio
async def test_my_feature_basic():
    config = AppConfig(response_delay=0.0)
    service = MyFeatureService(config)

    request = MyFeatureRequest(
        model="openai/gpt-oss-120b",
        prompt="Test prompt"
    )

    response = await service.create_my_feature(request)

    assert response.id.startswith("myfeat-")
    assert response.result
    assert response.usage.total_tokens > 0
```

---

## Testing

### Running Tests
```bash
# All tests
pytest -v

# Specific module
pytest tests/test_embedding_service.py -v

# With coverage
pytest --cov=fakeai --cov-report=html

# Specific markers
pytest -m unit -v
pytest -m integration -v
pytest -m service -v
```

### Test Structure
```python
import pytest
from fakeai.services.my_service import MyService
from fakeai.config import AppConfig

class TestMyService:
    """Test suite for MyService"""

    @pytest.fixture
    def config(self):
        """Provide test config with zero delays"""
        return AppConfig(response_delay=0.0)

    @pytest.fixture
    def service(self, config):
        """Provide service instance"""
        return MyService(config)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_basic_functionality(self, service):
        """Test basic functionality"""
        # Arrange
        request = ...

        # Act
        response = await service.method(request)

        # Assert
        assert response.field == expected

    @pytest.mark.asyncio
    @pytest.mark.edge_case
    async def test_error_handling(self, service):
        """Test error handling"""
        with pytest.raises(ValueError):
            await service.method(invalid_request)
```

### Test Markers
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.service` - Service layer tests
- `@pytest.mark.edge_case` - Edge case tests
- `@pytest.mark.slow` - Slow tests
- `@pytest.mark.asyncio` - Async tests (required for async)

---

## Quick Reference

### Key Imports
```python
# Shared Utilities (use these ALWAYS)
from fakeai.shared.content_utils import extract_text_content
from fakeai.shared.delay_utils import generate_chat_delay
from fakeai.shared.id_generators import generate_chat_completion_id
from fakeai.shared.usage_builder import UsageBuilder
from fakeai.shared.decorators import with_metrics, with_error_handling
from fakeai.shared.validators import validate_temperature, validate_max_tokens

# Model Registry
from fakeai.models_registry import get_global_registry

# Services
from fakeai.services.embedding_service import EmbeddingService
from fakeai.services.image_generation_service import ImageGenerationService
from fakeai.services.audio_service import AudioService
from fakeai.services.moderation_service import ModerationService
from fakeai.services.file_service import FileService
from fakeai.services.batch_service import BatchService

# Configuration
from fakeai.config import AppConfig
from fakeai.config.auth import AuthConfig
from fakeai.config.rate_limits import RateLimitConfig

# Metrics
from fakeai.metrics import MetricsTracker
from fakeai.kv_cache import KVCacheMetrics
from fakeai.model_metrics import ModelMetricsTracker

# Error Injection
from fakeai.error_injector import get_error_injector

# Models (use organized modules)
from fakeai.models.chat import ChatCompletionRequest, ChatCompletionResponse
from fakeai.models.embeddings import EmbeddingRequest, EmbeddingResponse
from fakeai.models.images import ImageGenerationRequest, ImageGenerationResponse
from fakeai.models.audio import AudioSpeechRequest
from fakeai.models.batches import BatchRequest, BatchResponse
from fakeai.models._base import Model, Usage, ErrorResponse
```

### Common Commands
```bash
# Start server
fakeai server                     # Production mode
fakeai server --debug             # Debug mode
fakeai server --response-delay 0  # No delays

# Check status
fakeai status                     # Health check
fakeai metrics                    # Metrics summary
fakeai cache-stats                # KV cache stats

# Development
pytest -v                         # Run tests
pytest --cov=fakeai --cov-report=html  # Coverage report
black fakeai/ && isort fakeai/    # Format code
mypy fakeai/                      # Type checking

# Build
python -m build                   # Build package
```

### Environment Variables
```bash
# Most important settings
FAKEAI_PORT=8000
FAKEAI_HOST=0.0.0.0
FAKEAI_DEBUG=false
FAKEAI_RESPONSE_DELAY=0.5

# Features
FAKEAI_KV_CACHE_ENABLED=true
FAKEAI_RATE_LIMIT_ENABLED=false
FAKEAI_ERROR_INJECTION_ENABLED=false

# Authentication
FAKEAI_REQUIRE_API_KEY=true
FAKEAI_API_KEYS=key1,key2,key3
```

---

## Troubleshooting

### Model not found
```python
#  Model not found error
# FIX: Always call _ensure_model_exists()
self._ensure_model_exists(model_id)
```

### Multi-modal content breaks
```python
#  AttributeError on content
# FIX: Use extract_text_content()
from fakeai.shared.content_utils import extract_text_content
text = extract_text_content(message.content)
```

### Metrics not updating
```python
#  Creating new MetricsTracker instance
metrics = MetricsTracker()  # Wrong!

# FIX: Use singleton
from fakeai.metrics import get_metrics_tracker
metrics = get_metrics_tracker()  # Correct!
```

### Import errors
```python
#  Importing from wrong location
from fakeai.utils import extract_text_content  # Doesn't exist!

# FIX: Import from shared
from fakeai.shared.content_utils import extract_text_content
```

### Tests not running
```bash
#  Missing asyncio marker
def test_my_async_function():  # Won't run!

# FIX: Add @pytest.mark.asyncio
@pytest.mark.asyncio
async def test_my_async_function():
    await my_function()
```

---

## Version History

### Version 3.0.0 "Perfection Edition" (October 2025)
- **90+ modules** - Complete architectural transformation
- **1,400+ tests** - 90%+ coverage, 0.87:1 test-to-code ratio
- **8 shared utilities** - Zero duplication
- **11 configuration modules** - Type-safe, domain-specific
- **7 model modules** - Organized by feature
- **9 registry modules** - Fuzzy matching, capability queries
- **6 extracted services** - Single responsibility
- **18 metrics systems** - Production-grade monitoring
- **100% stub elimination** - All metrics are real
- **70% duplication reduction** - Shared utilities throughout

### Version 0.0.5 (Pre-transformation)
- Original monolithic architecture
- Single models.py (3,046 lines)
- Single utils.py (1,031 lines)
- Basic metrics with stubs
- Limited testing

---

## Resources

- **[README.md](../../README.md)** - Project overview and features
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture documentation
- **[API_REFERENCE.md](../api/API_REFERENCE.md)** - Complete API documentation
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **examples/** - 50+ comprehensive examples
- **tests/** - 1,400+ tests with 90%+ coverage

---

*Keep this document updated as the project evolves.*
*Last updated: October 5, 2025*
*Version: 3.0.0 "Perfection Edition"*
