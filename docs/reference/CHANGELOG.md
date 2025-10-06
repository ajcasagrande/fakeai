# Changelog

All notable changes to FakeAI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2025-10-05 - "Perfection Edition"

### Major Architectural Changes
- **Modular Model System**: Complete refactor to modular model definitions in `models/` package
  - Separated concerns: `_base.py`, `_content.py`, `chat.py`, `embeddings.py`, `audio.py`, `images.py`, `batches.py`
  - Improved maintainability and extensibility
  - Better Pydantic 2.x compatibility

- **Model Registry System**: New comprehensive model catalog and discovery system
  - Support for 50+ models from OpenAI, Anthropic, Meta, DeepSeek, Mistral, NVIDIA
  - Model capabilities tracking (streaming, tools, vision, reasoning, MoE)
  - Automatic model discovery and registration
  - LoRA fine-tuned model support (`ft:base:org::id` format)

- **Service Layer Architecture**: Extracted services into dedicated modules
  - `services/audio_service.py` - Audio/TTS operations
  - `services/embedding_service.py` - Embedding generation
  - `services/image_generation_service.py` - Image synthesis
  - `services/file_service.py` - File management
  - `services/batch_service.py` - Batch operations
  - `services/moderation_service.py` - Content moderation

- **Configuration System Refactor**: Split monolithic config into focused modules
  - `config/base.py` - Core settings
  - `config/auth.py` - Authentication
  - `config/server.py` - Server configuration
  - `config/generation.py` - Text generation
  - `config/kv_cache.py` - KV cache settings
  - `config/metrics.py` - Metrics configuration
  - `config/rate_limits.py` - Rate limiting
  - `config/security.py` - Security settings
  - `config/storage.py` - Storage configuration
  - `config/features.py` - Feature flags

### New Features

#### Advanced KV Cache & Smart Routing (AI-Dynamo)
- **Advanced KV Cache System** (`kv_cache_advanced.py`):
  - Multi-tenant request isolation
  - Prefix-aware eviction policies (LRU, LFU, TTL)
  - Speculative execution support
  - Cache warming and prefetching
  - Block-level deduplication
  - Advanced metrics and analytics

- **Smart Router Advanced** (`smart_router_advanced.py`):
  - Multi-objective optimization (latency, throughput, cost, power)
  - Workload profiling and prediction
  - Adaptive learning from routing decisions
  - Request batching and coalescing
  - Circuit breaker patterns
  - A/B testing support

- **Dynamo Metrics Advanced** (`dynamo_metrics_advanced.py`):
  - DCGM-style GPU metrics simulation
  - Per-model performance tracking
  - Cache efficiency analytics
  - Request pattern analysis
  - Latency percentiles (P50, P95, P99)
  - Throughput optimization insights

#### Enhanced Metrics & Monitoring
- **Metrics Aggregator** (`metrics_aggregator.py`):
  - Time-window based aggregation
  - Configurable retention policies
  - Statistical summaries (mean, median, percentiles)
  - Trend analysis

- **Metrics Streaming** (`metrics_streaming.py`):
  - Real-time metrics streaming via WebSocket
  - Configurable update intervals
  - Metric filtering and subscriptions
  - Client-side aggregation support

- **Model Metrics** (`model_metrics.py`):
  - Per-model performance tracking
  - Request distribution analysis
  - Error rate monitoring
  - Latency profiling per model

- **Batch Metrics** (`batch_metrics.py`):
  - Batch job tracking
  - Queue depth monitoring
  - Completion rate analysis
  - Cost estimation

- **Latency Histograms** (`latency_histograms.py`):
  - High-resolution latency distribution
  - Configurable bucket sizes
  - P50/P95/P99 calculations
  - Outlier detection

- **Latency Profiles** (`latency_profiles.py`):
  - Model-specific latency profiles
  - Input size correlation
  - Hardware acceleration simulation
  - Batch size impact modeling

- **Cost Tracker** (`cost_tracker.py`):
  - Per-request cost calculation
  - Model-specific pricing
  - Usage-based billing simulation
  - Cost optimization recommendations

#### Advanced Text Generation
- **LLM Generator** (`llm_generator.py`):
  - Transformer-based text generation
  - Multi-model support (GPT, Llama, Mistral)
  - Temperature and top-p sampling
  - Optional HuggingFace integration
  - Streaming generation

- **Tokenizers** (`tokenizers.py`):
  - tiktoken integration
  - Model-specific tokenization
  - Token counting utilities
  - Batch tokenization support

- **Semantic Embeddings** (`semantic_embeddings.py`):
  - sentence-transformers integration
  - Cosine similarity calculations
  - Batch embedding generation
  - Dimension reduction support

#### Image & Audio Processing
- **Image Generator** (`image_generator.py`):
  - Style-aware generation
  - Multiple format support (PNG, JPEG, WebP)
  - Resolution-based token calculation
  - Quality parameter simulation

- **Audio Transcriber** (`audio_transcriber.py`):
  - Multi-format support (WAV, MP3, M4A, FLAC)
  - Language detection
  - Timestamp generation
  - Word-level transcription

- **Audio Utilities** (`utils/audio_generation.py`):
  - Audio format conversion
  - Sample rate adjustment
  - Duration estimation
  - Bitrate calculation

#### Vector Storage
- **Vector Store Engine** (`vector_store_engine.py`):
  - FAISS integration (optional)
  - In-memory vector storage
  - Cosine similarity search
  - Metadata filtering
  - Batch operations

#### Security & Validation
- **Security Module** (`security.py`):
  - Input sanitization
  - SQL injection prevention
  - XSS protection
  - Rate limit bypass detection
  - Suspicious pattern detection

- **Context Validator** (`context_validator.py`):
  - Model-specific context length validation
  - Token counting with tiktoken
  - Graceful degradation strategies
  - Warning thresholds

- **Validation Pipeline** (`validation/pipeline.py`):
  - Multi-stage validation
  - Schema validation
  - Content validation
  - Security checks
  - Performance profiling

#### Error Handling & Resilience
- **Error Injector** (`error_injector.py`):
  - Configurable error injection
  - Multiple error types (timeout, rate limit, invalid request)
  - Probabilistic failures
  - Testing chaos engineering

- **Error Metrics** (`error_metrics.py`):
  - Error rate tracking
  - Error type classification
  - Recovery time analysis
  - Failure pattern detection

#### Tool Calling & Structured Outputs
- **Enhanced Tool Calling** (`tool_calling.py`):
  - Parallel tool execution
  - Streaming tool calls
  - Tool result validation
  - Error handling

- **Structured Outputs** (`structured_outputs.py`):
  - JSON schema validation
  - Pydantic model support
  - Strict mode enforcement
  - Schema generation

#### Rate Limiting
- **Rate Limiter** (`rate_limiter.py`):
  - Token bucket algorithm
  - Per-API-key limits
  - Tier-based limits
  - Request and token rate limiting
  - Sliding window implementation

- **Rate Limiter Metrics** (`rate_limiter_metrics.py`):
  - Limit hit tracking
  - Rejection rate analysis
  - Quota usage monitoring
  - Per-key analytics

### API Enhancements
- **Batch API**: Complete implementation with status tracking
- **Files API**: Full file management with metadata
- **Moderation API**: Content safety checks with categories
- **Organization API**: Project and user management
- **Fine-tuning API**: LoRA model management
- **Vector Stores API**: RAG integration
- **Assistants API**: Stateful conversation threads
- **Realtime API**: WebSocket bidirectional streaming
- **Responses API**: Stateful conversation management

### Model Support
- **GPT-OSS Models**: Open-source reasoning models (Apache 2.0)
  - `gpt-oss-120b` (MoE 120B parameters)
  - `gpt-oss-20b` (20B parameters)
  - Reasoning content generation
  - Predicted outputs (EAGLE speculative decoding)

- **DeepSeek Models**:
  - `deepseek-ai/DeepSeek-R1` (reasoning)
  - `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B`
  - `deepseek-v3` (671B MoE)

- **Mistral Models**:
  - `mixtral-8x7b` (56B MoE)
  - `mixtral-8x22b` (176B MoE)

- **Anthropic Models**:
  - Claude 3.5 Sonnet/Haiku
  - Claude Opus
  - Vision support

- **Meta Models**:
  - Llama 3.1/3.2/3.3
  - Multimodal Llama variants

- **NVIDIA NIM**:
  - Cosmos video models
  - Ranking API support

### Performance & Optimization
- **Code Formatting**: Full codebase formatted with Black (88 char) and isort
- **Type Annotations**: Comprehensive type hints throughout
- **Async/Await**: Full async support for I/O operations
- **LRU Caching**: Strategic caching for token counting and embeddings
- **Memory Optimization**: Efficient data structures and algorithms

### Testing & Quality
- **791 Test Markers**: Comprehensive pytest marker coverage
  - `@pytest.mark.unit` - Unit tests
  - `@pytest.mark.integration` - Integration tests
  - `@pytest.mark.service` - Service layer tests
  - `@pytest.mark.streaming` - Streaming tests
  - `@pytest.mark.metrics` - Metrics tests
  - `@pytest.mark.stress` - Load tests

- **Test Organization**: Tests organized by feature area
  - Core services tests in `tests/services/`
  - Model tests in `tests/test_models_*.py`
  - Integration tests in `tests/test_*_complete.py`

### CLI Enhancements
- `fakeai server` - Start server with flexible configuration
- `fakeai status` - Check server health
- `fakeai metrics` - Display metrics dashboard
- `fakeai cache-stats` - KV cache statistics
- `fakeai interactive` - Interactive REPL

### Documentation
- **CLAUDE.md**: Comprehensive project knowledge base
- **Inline Docstrings**: 2000+ docstrings across codebase
- **API Examples**: 40+ example scripts in `examples/`
- **Benchmarks**: Performance benchmarking suite in `benchmarks/`

### Dependencies
- **Core Dependencies**:
  - fastapi >= 0.103.0
  - uvicorn >= 0.23.0
  - hypercorn >= 0.16.0
  - pydantic >= 2.0.0
  - numpy >= 1.24.0
  - faker >= 13.0.0
  - cyclopts >= 3.0.0
  - aiohttp >= 3.9.0

- **Optional Dependencies**:
  - **dev**: pytest, black, isort, mypy, openai, httpx
  - **llm**: tiktoken, transformers, torch
  - **embeddings**: sentence-transformers
  - **vector**: faiss-cpu

### Breaking Changes
- **Model structure changed**: Old `models.py` split into modular `models/` package
- **Config structure changed**: Old `config.py` split into `config/` modules
- **Service methods moved**: Audio/embedding/image services now in dedicated modules
- **Version bump**: 0.0.5 → 3.0.0 (following semver for major refactor)

### Migration Guide
```python
# Old imports (0.0.5)
from fakeai.models import ChatCompletionRequest
from fakeai.config import AppConfig

# New imports (3.0.0)
from fakeai.models.chat import ChatCompletionRequest
from fakeai.config import AppConfig  # or from fakeai.config.base import CoreConfig

# Service usage unchanged
from fakeai.fakeai_service import FakeAIService
service = FakeAIService(config)
```

### Deprecated
- `fakeai-server` command (use `fakeai server` instead)
- Monolithic `models.py` (use `models/` package)
- Direct `config.py` usage (use `config/` modules)

### Fixed
- Streaming metrics accuracy
- Token counting edge cases
- Memory leaks in long-running servers
- Race conditions in metrics collection
- Type annotation completeness

### Internal Changes
- 212 files reformatted with Black
- 119 files reorganized with isort
- Relaxed mypy settings for gradual typing
- Enhanced error handling throughout
- Improved logging granularity

---

## [0.0.5] - Previous Release

Initial release with basic OpenAI API simulation, streaming support, and metrics tracking.

[3.0.0]: https://github.com/ajcasagrande/fakeai/compare/v0.0.5...v3.0.0
[0.0.5]: https://github.com/ajcasagrande/fakeai/releases/tag/v0.0.5
