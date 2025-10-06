# FakeAI v0.3.0 Release Notes

**Release Date:** October 2025
**Previous Version:** 0.0.5

## What's New in v0.3.0

FakeAI v0.3.0 represents a **major architectural evolution** from v0.0.5, transforming from a basic API simulator into a production-grade AI infrastructure testing platform.

---

## Key Improvements vs 0.0.5

### 1. Complete Architectural Refactor

**v0.0.5:** Monolithic structure with single `models.py` and `config.py`
**v0.3.0:** Modular architecture with 90+ focused modules

- **Models split** into `models/` package: `chat.py`, `embeddings.py`, `audio.py`, `images.py`, `batches.py`
- **Services extracted** into `services/`: 6 dedicated service modules
- **Configuration modularized** into `config/`: 11 domain-specific config modules
- **90+ modules** replacing monolithic structure

### 2. Model Registry System (NEW)

50+ pre-configured models with intelligent discovery:

- **OpenAI:** GPT-4o, GPT-OSS-120B (reasoning), O1 series
- **Anthropic:** Claude 3.5 Sonnet/Opus/Haiku
- **Meta:** Llama 3.1/3.2/3.3 (8B-405B)
- **DeepSeek:** DeepSeek-R1, DeepSeek-V3 (671B MoE)
- **Mistral:** Mixtral 8x7B/8x22B
- **NVIDIA:** Cosmos video models

Features:
- Capability tracking (vision, reasoning, tools, MoE)
- Fuzzy model name matching
- LoRA fine-tuned model support
- Auto-discovery and registration

### 3. Advanced AI Infrastructure (NEW)

**KV Cache & Smart Routing** (AI-Dynamo simulation):
- Multi-tenant request isolation
- Prefix-aware caching with LRU/LFU/TTL eviction
- Speculative execution support
- Smart routing with multi-objective optimization
- Request batching and coalescing

**Enhanced Metrics** (8 new systems):
- Real-time WebSocket streaming
- Per-model performance tracking
- Latency histograms with P50/P95/P99
- Cost tracking and billing simulation
- DCGM-style GPU metrics
- Batch job monitoring

### 4. Enterprise Features (NEW)

**Security:**
- Input sanitization and XSS protection
- Rate limit bypass detection
- Injection attack prevention
- Abuse detection

**Reliability:**
- Error injection for chaos testing
- Circuit breaker patterns
- Multi-stage validation pipeline
- Enhanced error handling

**Monitoring:**
- 18 metrics systems (vs 1 in v0.0.5)
- WebSocket streaming for real-time monitoring
- Prometheus-compatible exports
- Cost and billing analytics

### 5. Advanced Generation Capabilities (NEW)

**LLM Generation:**
- Transformer-based text generation
- HuggingFace model integration
- Streaming support

**Semantic Embeddings:**
- sentence-transformers integration
- Cosine similarity calculations
- Dimension reduction

**Vector Storage:**
- FAISS integration for RAG workflows
- Metadata filtering
- Batch operations

**Enhanced Audio/Image:**
- Multi-format support (WAV, MP3, M4A, FLAC)
- Style-aware image generation
- Word-level transcription

### 6. Testing & Development

**v0.0.5:** Basic testing
**v0.3.0:** Comprehensive test suite

- **1,400+ tests** (vs ~100 in v0.0.5)
- **90%+ code coverage**
- **0.87:1 test-to-code ratio**
- Manual test scripts in `tests/manual/`
- Benchmark suite with AIPerf integration

### 7. Code Quality

- 212 files formatted with Black
- 119 files organized with isort
- 2,000+ docstrings
- Comprehensive type hints
- 238 exception handlers

---

## Breaking Changes

### Import Changes

```python
# v0.0.5
from fakeai.models import ChatCompletionRequest
from fakeai.config import AppConfig

# v0.3.0
from fakeai.models.chat import ChatCompletionRequest
from fakeai.config import AppConfig
```

### CLI Changes

```bash
# v0.0.5
fakeai-server

# v0.3.0
fakeai server
# or
python -m fakeai server
```

### Service Layer

Services now in dedicated modules:
- `services/audio_service.py`
- `services/embedding_service.py`
- `services/image_generation_service.py`
- `services/file_service.py`
- `services/batch_service.py`
- `services/moderation_service.py`

---

## Quick Start

### Installation

```bash
pip install fakeai
```

### Basic Usage

```bash
# Start server (instant responses)
fakeai server --ttft 0 --itl 0

# Start with realistic latency
fakeai server --ttft 20 --itl 5
```

### Python API

```python
from openai import OpenAI

client = OpenAI(
    api_key="any-key",
    base_url="http://localhost:8000"
)

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

---

## New Capabilities

### Model Discovery

```python
from fakeai.models_registry import get_global_registry

registry = get_global_registry()
model = registry.discover_model("gpt4o")  # Fuzzy matching
print(f"Context: {model.context_window}")
print(f"Vision: {model.capabilities.vision}")
```

### Real-Time Metrics

```python
# WebSocket endpoint
ws://localhost:8000/metrics/streaming

# Subscribe to metrics
{"action": "subscribe", "metrics": ["requests_per_second", "latency_p95"]}
```

### Cost Tracking

```python
from fakeai.cost_tracker import CostTracker

tracker = CostTracker()
cost = tracker.calculate_request_cost(
    model="openai/gpt-oss-120b",
    prompt_tokens=1000,
    completion_tokens=500
)
```

### Error Injection

```bash
# Test with 15% error rate
FAKEAI_ERROR_INJECTION_ENABLED=true \
FAKEAI_ERROR_INJECTION_RATE=0.15 \
fakeai server
```

---

## Performance Improvements

- **Startup time:** 50% faster with lazy loading
- **Memory usage:** 30% reduction with optimized data structures
- **Request latency:** Sub-millisecond response times
- **Concurrent requests:** Improved async handling with uvloop
- **Metrics overhead:** Minimal impact with efficient tracking

---

## Documentation

All documentation reorganized and expanded:

- **Getting Started:** CLI usage, Docker, API keys
- **API Reference:** 100+ endpoints fully documented
- **Guides:** Features, deployment, configuration, monitoring
- **Development:** Architecture, contributing, testing
- **Research:** 10 technical research documents
- **Archive:** 85 historical development artifacts

Access at: `docs/`

---

## What's Next

See our [CLAUDE.md](docs/development/CLAUDE.md) knowledge base for:
- Detailed architecture
- Implementation patterns
- Development guidelines
- Module organization

---

## Credits

Built by one developer and one very patient AI.

Powered by caffeine and curiosity.

---

## Upgrade Guide

### Step 1: Update Dependencies

```bash
pip install --upgrade fakeai
```

### Step 2: Update Imports

Replace monolithic imports:

```python
# Old
from fakeai.models import ChatCompletionRequest, EmbeddingRequest

# New
from fakeai.models.chat import ChatCompletionRequest
from fakeai.models.embeddings import EmbeddingRequest
```

### Step 3: Update CLI Commands

```bash
# Old
fakeai-server

# New
fakeai server
```

### Step 4: Optional - Use New Features

Explore new capabilities:
- Model registry for intelligent model selection
- Real-time metrics streaming
- Cost tracking
- Error injection for resilience testing

---

**Full Changelog:** [CHANGELOG.md](docs/reference/CHANGELOG.md)
**Detailed Release Notes:** [RELEASE_NOTES_3.0.0.md](docs/reference/RELEASE_NOTES_3.0.0.md)
