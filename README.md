![FakeAI](https://github.com/ajcasagrande/fakeai/blob/main/docs/images/fakeai.png?raw=true)

[![PyPI version](https://img.shields.io/pypi/v/fakeai.svg)](https://pypi.org/project/fakeai/)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![codecov](https://codecov.io/gh/ajcasagrande/fakeai/branch/main/graph/badge.svg)](https://codecov.io/gh/ajcasagrande/fakeai)

---

# FakeAI
*The AI is fake. The API is fake. The responses are fake. But your code? That's real. Or is it? Welcome to the simulation.*

FakeAI simulates the complete OpenAI API, as well as numerous NVIDIA AI services (NIM, AI-Dynamo, DCGM, Cosmos) with instant feedback and reproducible results. Develop and optimize your applications locally with realistic service behavior, then deploy to production infrastructure when ready.

---

## Why FakeAI?

### Instant Feedback for Rapid Iteration
- **Millisecond response times** - Test and debug without waiting for infrastructure
- **Reproducible results** - Consistent behavior across development, CI/CD, and testing
- **Performance optimization** - Profile and tune before production deployment
- **Local development** - Full-featured testing environment on any machine

### Realistic NVIDIA Service Simulation
- **NIM (NVIDIA Inference Microservices)** - Reranking API and optimized model endpoints
- **AI-Dynamo** - KV cache management, smart routing, and prefix caching
- **DCGM** - 100+ GPU telemetry metrics for A100, H100, H200, Blackwell
- **Cosmos** - Video understanding with token calculation
- **Real implementations** - Actual service logic, not mocks or stubs

### Comprehensive API Coverage
- **100+ endpoints** - Chat, embeddings, images, audio, fine-tuning, vector stores
- **Streaming support** - Realistic TTFT and ITL with 37+ model-specific profiles
- **Advanced features** - Function calling, structured outputs, vision, reasoning models
- **Drop-in replacement** - Works with OpenAI SDK, LangChain, LlamaIndex

### Performance Testing and Benchmarking
- **AIPerf integration** - Industry-standard performance profiling
- **KV cache metrics** - Analyze cache hit rates and optimization opportunities
- **Load testing** - Validate behavior under various concurrency levels
- **Latency profiling** - Realistic timing for capacity planning

---

## Table of Contents

- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [NVIDIA Features](#nvidia-features)
- [AIPerf Benchmarking](#aiperf-benchmarking)
- [Advanced Features](#advanced-features)
- [Configuration](#configuration)
- [Installation](#installation)
- [Use Cases](#use-cases)
- [Documentation](#documentation)

---

## Key Features

### Core OpenAI API

- **Chat Completions** - Streaming/non-streaming with 62 parameters
- **Text Completions** - Legacy endpoint support
- **Embeddings** - L2-normalized vectors with semantic similarity
- **Image Generation** - DALL-E compatible with actual PNG generation
- **Audio (TTS)** - Text-to-speech with multiple voices and formats
- **Audio (STT)** - Whisper-compatible transcription
- **Moderation** - 11-category content safety
- **File Management** - Upload, retrieve, delete with metadata
- **Batch Processing** - Async job execution with status tracking

### Advanced OpenAI Features

- **Realtime API** - WebSocket bidirectional streaming
- **Responses API** - Stateful conversation management
- **Function Calling** - Parallel tool execution
- **Structured Outputs** - JSON Schema validation
- **Vision** - Multi-modal image input
- **Video** - Multi-modal video input (Cosmos)
- **Reasoning Models** - O1-style chain-of-thought
- **Predicted Outputs** - EAGLE speculative decoding (3-5× speedup)
- **Fine-tuning** - Complete job lifecycle with LoRA
- **Vector Stores** - RAG infrastructure

### Organization & Enterprise

- **Organization Management** - Users, roles, invites
- **Project Management** - Multi-tenancy with isolation
- **Service Accounts** - API key management
- **Usage Tracking** - Detailed usage metrics by endpoint
- **Cost Analytics** - Estimated costs with breakdowns
- **Rate Limiting** - Per-key RPM, TPM, RPD, TPD with tiers

### Security & Reliability

- **API Key Authentication** - Bearer token with SHA-256 hashing
- **Rate Limiting** - Configurable tiers (Free, Tier 1-5)
- **Abuse Detection** - Anomaly detection and IP banning
- **Input Validation** - Injection attack detection
- **Error Injection** - Configurable failure simulation
- **CORS Configuration** - Cross-origin control

---

## Quick Start

### Installation

```bash
pip install fakeai
```

### Start Server

```bash
# Basic startup (localhost:8000)
fakeai server

# Custom configuration
fakeai server --port 9000 --host 0.0.0.0

# Zero latency for maximum throughput
fakeai server --ttft 0 --itl 0
```

### Use with OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(
    api_key="any-key-works",
    base_url="http://localhost:8000"
)

# Chat completion
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)

# Streaming
stream = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Count to 10"}],
    stream=True
)
for chunk in stream:
    print(chunk.choices[0].delta.content, end="", flush=True)
```

### Check Health & Metrics

```bash
# Health check
curl http://localhost:8000/health

# Server metrics
curl http://localhost:8000/metrics

# KV cache stats
curl http://localhost:8000/kv-cache/metrics

# DCGM GPU metrics
curl http://localhost:8000/dcgm/metrics/json

# Dynamo inference metrics
curl http://localhost:8000/dynamo/metrics/json
```

---

## API Endpoints

### Core OpenAI API

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/v1/models` | GET | List available models |
| `/v1/models/{id}` | GET | Get model details |
| `/v1/models/{id}/capabilities` | GET | Get model capabilities (context, pricing, features) |
| `/v1/chat/completions` | POST | Chat completions (streaming/non-streaming) |
| `/v1/completions` | POST | Text completions (legacy) |
| `/v1/embeddings` | POST | Generate embeddings |
| `/v1/images/generations` | POST | Generate images |
| `/v1/audio/speech` | POST | Text-to-speech synthesis |
| `/v1/audio/transcriptions` | POST | Audio transcription |
| `/v1/moderations` | POST | Content moderation |
| `/images/{id}.png` | GET | Retrieve generated image |

### File & Batch Operations

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/v1/files` | GET, POST | File management |
| `/v1/files/{id}` | GET, DELETE | File operations |
| `/v1/files/{id}/content` | GET | Download file content |
| `/v1/batches` | POST, GET | Batch processing |
| `/v1/batches/{id}` | GET | Batch status |
| `/v1/batches/{id}/cancel` | POST | Cancel batch |

### Fine-tuning

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/v1/fine_tuning/jobs` | POST, GET | Create and list fine-tuning jobs |
| `/v1/fine_tuning/jobs/{id}` | GET | Get job details |
| `/v1/fine_tuning/jobs/{id}/cancel` | POST | Cancel job |
| `/v1/fine_tuning/jobs/{id}/events` | GET | Stream job events (SSE) |
| `/v1/fine_tuning/jobs/{id}/checkpoints` | GET | List checkpoints |

### Vector Stores (RAG)

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/v1/vector_stores` | POST, GET | Create and list vector stores |
| `/v1/vector_stores/{id}` | GET, POST, DELETE | Vector store operations |
| `/v1/vector_stores/{id}/files` | POST, GET | File management |
| `/v1/vector_stores/{id}/files/{file_id}` | GET, DELETE | File operations |
| `/v1/vector_stores/{id}/file_batches` | POST, GET | Batch file operations |
| `/v1/vector_stores/{id}/file_batches/{batch_id}` | GET, POST | Batch operations |
| `/v1/vector_stores/{id}/file_batches/{batch_id}/files` | GET | List files in batch |

### Organization Management

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/v1/organization/users` | GET, POST | User management |
| `/v1/organization/users/{id}` | GET, POST, DELETE | User operations |
| `/v1/organization/invites` | GET, POST | Invitation management |
| `/v1/organization/invites/{id}` | GET, DELETE | Invite operations |
| `/v1/organization/projects` | GET, POST | Project management |
| `/v1/organization/projects/{id}` | GET, POST | Project operations |
| `/v1/organization/projects/{id}/archive` | POST | Archive project |
| `/v1/organization/projects/{id}/users` | GET, POST | Project user management |
| `/v1/organization/projects/{id}/users/{user_id}` | GET, POST, DELETE | User operations |
| `/v1/organization/projects/{id}/service_accounts` | GET, POST | Service account management |
| `/v1/organization/projects/{id}/service_accounts/{sa_id}` | GET, DELETE | Service account operations |

### Usage & Billing

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/v1/organization/usage/completions` | GET | Completions usage by time bucket |
| `/v1/organization/usage/embeddings` | GET | Embeddings usage by time bucket |
| `/v1/organization/usage/images` | GET | Images usage by time bucket |
| `/v1/organization/usage/audio_speeches` | GET | TTS usage by time bucket |
| `/v1/organization/usage/audio_transcriptions` | GET | STT usage by time bucket |
| `/v1/organization/costs` | GET | Cost data with grouping |

### Extended APIs

| Endpoint | Protocol | Description |
|----------|----------|-------------|
| `/v1/realtime` | WebSocket | Real-time bidirectional streaming |
| `/v1/responses` | POST | Stateful conversation API |
| `/v1/ranking` | POST | NVIDIA NIM reranking |
| `/v1/text/generation` | POST | Azure text generation compatibility |
| `/rag/api/prompt` | POST | Solido RAG retrieval-augmented generation |

### Monitoring & Health

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/health` | GET | Basic health check |
| `/health/detailed` | GET | Detailed health with metrics summary |
| `/dashboard` | GET | Interactive metrics dashboard |
| `/dashboard/dynamo` | GET | Advanced Dynamo dashboard |

### Core Metrics

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/metrics` | GET | Server metrics (JSON) |
| `/metrics/prometheus` | GET | Prometheus metrics format |
| `/metrics/csv` | GET | CSV export |
| `/metrics/stream` | WebSocket | Real-time metrics streaming |

### Per-Model Metrics

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/metrics/by-model` | GET | All models stats (JSON) |
| `/metrics/by-model/prometheus` | GET | Per-model Prometheus metrics |
| `/metrics/by-model/{id}` | GET | Specific model stats |
| `/metrics/compare` | GET | Compare two models (query params) |
| `/metrics/ranking` | GET | Rank models by metric |
| `/metrics/costs` | GET | Cost breakdown by model |
| `/metrics/multi-dimensional` | GET | 2D breakdowns (model×endpoint, model×user, model×time) |

### KV Cache & Dynamo

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/kv-cache/metrics` | GET | KV cache and smart routing stats |
| `/dynamo/metrics` | GET | AI-Dynamo metrics (Prometheus) |
| `/dynamo/metrics/json` | GET | AI-Dynamo metrics (JSON) |

### DCGM GPU Metrics

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/dcgm/metrics` | GET | DCGM GPU metrics (Prometheus) |
| `/dcgm/metrics/json` | GET | DCGM GPU metrics (JSON) |

### Rate Limiting Metrics

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/metrics/rate-limits` | GET | Comprehensive rate limiting metrics |
| `/metrics/rate-limits/key/{key}` | GET | Per-key statistics |
| `/metrics/rate-limits/tier` | GET | Per-tier aggregations |
| `/metrics/rate-limits/throttle-analytics` | GET | Throttling analytics |
| `/metrics/rate-limits/abuse-patterns` | GET | Abuse pattern detection |

---

## NVIDIA Features

FakeAI includes comprehensive NVIDIA AI infrastructure simulation with real implementations (not stubs).

### AI-Dynamo

**Advanced KV cache management and smart routing**

**Features:**
- **Radix Tree Prefix Matching** - SGLang-style efficient prefix matching
- **Block-level Caching** - Configurable block size (default: 16 tokens)
- **Multi-worker Simulation** - Simulates distributed workers
- **Smart Request Routing** - Cost-based routing with cache overlap scoring
- **Prefix Caching** - Automatic shared prompt detection
- **Cache Metrics** - Hit rates, token reuse, overlap statistics

**Configuration:**
```bash
export FAKEAI_KV_CACHE_ENABLED=true
export FAKEAI_KV_CACHE_BLOCK_SIZE=16
export FAKEAI_KV_CACHE_NUM_WORKERS=4
export FAKEAI_KV_OVERLAP_WEIGHT=1.0
fakeai server
```

**Metrics:**
```bash
curl http://localhost:8000/kv-cache/metrics
```

**Benefits:**
- Realistic TTFT speedup on cache hits (60-80% reduction)
- Simulates cache warming and reuse patterns
- Worker load balancing with cache affinity

### DCGM (Data Center GPU Manager)

**100+ GPU telemetry metrics in Prometheus format**

**Simulated Metrics:**
- **GPU Utilization** - Compute, memory, tensor core activity
- **Temperature** - GPU, memory, thermal throttling
- **Power** - Current draw, limits, violations
- **Memory** - Used, free, bandwidth, ECC errors
- **Clock Frequencies** - SM clock, memory clock, throttling
- **NVLink** - Traffic, bandwidth, topology
- **Health Status** - Thermal violations, power throttling, ECC errors
- **Multi-GPU** - Coordination, load balancing
- **PCIe** - Replay counters, bandwidth saturation
- **Process Tracking** - Per-process GPU/memory usage

**Supported GPU Models:**
- NVIDIA A100 (80GB)
- NVIDIA H100 (80GB)
- NVIDIA H200 (141GB)
- NVIDIA B100/B200 (Blackwell)

**Configuration:**
```bash
export FAKEAI_DCGM_GPU_MODEL=H100-80GB
export FAKEAI_DCGM_GPU_COUNT=8
export FAKEAI_DCGM_WORKLOAD_INTENSITY=high
fakeai server
```

**Prometheus Endpoint:**
```bash
curl http://localhost:8000/dcgm/metrics
```

**Grafana Integration:**
- 100% compatible with NVIDIA DCGM dashboards
- Pre-configured Prometheus exporters
- Real-time GPU monitoring visualization

### Cosmos

**Video understanding and token calculation**

**Features:**
- **Video Token Calculation** - Resolution, duration, FPS-aware
- **Frame Extraction** - Configurable frame sampling
- **Multi-modal Input** - Video + text in chat completions
- **Detail Levels** - Auto, low, high with token scaling
- **URL Metadata** - Extract video metadata from URLs

**Example:**
```python
response = client.chat.completions.create(
    model="nvidia/cosmos-vision",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Describe this video"},
            {"type": "video_url", "video_url": {
                "url": "https://example.com/video.mp4?width=512&height=288&duration=5.0&fps=4"
            }}
        ]
    }]
)
```

**Token Calculation:**
- Base tokens: 85
- Per-frame tokens: 10-50 depending on resolution and detail level
- Total = base + (frames × tokens_per_frame)

### NIM (NVIDIA Inference Microservices)

**Reranking API and optimized models**

**Reranking Endpoint:**
```bash
POST /v1/ranking
```

**Example:**
```python
import requests

response = requests.post("http://localhost:8000/v1/ranking", json={
    "model": "nvidia/nv-rerank-qa-mistral-4b",
    "query": "What is machine learning?",
    "documents": [
        {"text": "Machine learning is a subset of AI..."},
        {"text": "Deep learning uses neural networks..."},
        {"text": "Python is a programming language..."}
    ],
    "top_n": 2
})

print(response.json())
# Returns documents ranked by relevance
```

**NIM Models in Catalog:**
- `nvidia/cosmos-vision` - Video understanding
- `nvidia/llama-3.1-nemotron-70b-instruct` - Optimized Llama 3.1 70B
- `nvidia/nv-rerank-qa-mistral-4b` - Reranking for Q&A

**Features:**
- Document reranking for RAG pipelines
- Configurable top_n results
- Query-document relevance scoring
- Compatible with NVIDIA NIM format

### Dynamo Inference Metrics

**Comprehensive LLM inference metrics**

**Tracked Metrics:**
- **Latency Breakdown:**
  - TTFT (Time To First Token)
  - ITL (Inter-Token Latency)
  - TPOT (Time Per Output Token)
  - Queue time, prefill time, decode time

- **Throughput:**
  - Request throughput (rps)
  - Token throughput (tokens/sec)
  - Batch efficiency

- **KV Cache:**
  - Cache hit rate
  - Blocks matched
  - Overlap scores

- **Worker Statistics:**
  - Request distribution
  - Worker utilization
  - Routing costs

**Prometheus Endpoint:**
```bash
curl http://localhost:8000/dynamo/metrics
```

**JSON Endpoint:**
```bash
curl http://localhost:8000/dynamo/metrics/json
```

### Latency Profiles

**37+ model-specific latency profiles with realistic TTFT/ITL**

Pre-configured profiles for:
- GPT-4, GPT-4o, GPT-3.5 Turbo
- Llama 3, Llama 3.1, Llama 3.2 (8B, 70B, 405B)
- DeepSeek-V3, DeepSeek-R1
- Mixtral 8x7B, 8x22B
- Claude 3.5 Sonnet, Claude 3 Opus
- And 20+ more...

**Dynamic Adjustments:**
- Prompt length affects TTFT
- KV cache hits reduce TTFT by 60-80%
- Concurrent load adds queuing delays
- Temperature affects generation speed
- Model size scales latency

---

## AIPerf Benchmarking

FakeAI has comprehensive integration with **AIPerf** (NVIDIA's LLM benchmarking tool) for industry-standard performance testing.

### Features

- **Full OpenAI API Compatibility** - Works seamlessly with AIPerf
- **Realistic Timing Simulation** - 37+ model-specific latency profiles
- **Comprehensive Metrics** - TTFT, ITL, TPOT, throughput
- **Automated Test Suites** - Multi-model, multi-concurrency benchmark runner
- **Detailed Reporting** - JSON + Markdown reports with comparisons
- **CI/CD Integration** - Automated benchmarking in GitHub Actions

### Quick Benchmark

```bash
# Install AIPerf
pip install aiperf

# Start FakeAI with realistic latency
fakeai server --ttft 20 --itl 5

# Run benchmark
aiperf profile \
  --model openai/gpt-oss-120b \
  --url http://localhost:8000 \
  --endpoint-type chat \
  --streaming \
  --concurrency 100 \
  --request-count 1000
```

### Automated Benchmark Suite

```bash
cd benchmarks

# Quick test (1 config per model)
python run_aiperf_benchmarks.py --quick

# Specific models
python run_aiperf_benchmarks.py \
  --models openai/gpt-oss-120b deepseek-ai/DeepSeek-R1

# Custom concurrency levels
python run_aiperf_benchmarks.py --concurrency 50 100 250

# Full sweep
python run_aiperf_benchmarks.py --all
```

### Metrics Captured

**Latency:**
- TTFT (Time To First Token) - p50, p90, p99
- ITL (Inter-Token Latency) - p50, p90, p99
- TPOT (Time Per Output Token)
- Request Latency - avg, p50, p90, p99

**Throughput:**
- Request throughput (requests/sec)
- Output token throughput (tokens/sec)
- Input token throughput (tokens/sec)

**Token Statistics:**
- Input sequence length (avg, min, max, percentiles)
- Output sequence length (avg, min, max, percentiles)

### Use Cases

- **Performance Regression Testing** - Detect performance changes
- **Model Comparison** - Compare different model configurations
- **Load Testing** - Test system under various concurrency levels
- **API Compatibility** - Validate OpenAI API compliance
- **CI/CD Integration** - Automated performance testing

---

## Advanced Features

### Solido RAG

**Retrieval-augmented generation with document filtering**

```bash
POST /rag/api/prompt
```

**Example:**
```python
import requests

response = requests.post("http://localhost:8000/rag/api/prompt", json={
    "query": "What is PVTMC?",
    "filters": {"family": "Solido", "tool": "SDE"},
    "inference_model": "meta-llama/Llama-3.1-70B-Instruct",
    "top_k": 5
})

result = response.json()
print(result["content"])
print(f"Retrieved {len(result['retrieved_docs'])} documents")
```

**Features:**
- Document retrieval with filtering
- Context-aware response generation
- Configurable top_k results
- Multi-tool support

### Reasoning Models

**O1-style chain-of-thought reasoning**

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Solve: 2x + 5 = 13"}]
)

print(response.choices[0].message.reasoning_content)
print(f"Reasoning tokens: {response.usage.reasoning_tokens}")
```

**Supported Models:**
- `openai/gpt-oss-120b` - OpenAI O1-style reasoning
- `deepseek-ai/DeepSeek-R1` - DeepSeek reasoning model

### Predicted Outputs (EAGLE)

**Speculative decoding for 3-5× speedup**

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "The capital of France is"}],
    prediction={
        "type": "content",
        "content": "Paris, and the capital of Germany is Berlin"
    }
)

print(f"Accepted: {response.usage.accepted_prediction_tokens}")
print(f"Rejected: {response.usage.rejected_prediction_tokens}")
```

### Structured Outputs

**JSON Schema validation**

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Generate a person profile"}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "person",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                    "skills": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["name", "age"]
            }
        }
    }
)
```

### Function Calling

**Parallel tool execution**

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                }
            }
        }
    }
]

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "What's the weather in SF and NYC?"}],
    tools=tools,
    tool_choice="auto"
)
```

### Vision

**Multi-modal image input**

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What's in this image?"},
            {"type": "image_url", "image_url": {
                "url": "https://example.com/image.jpg",
                "detail": "high"
            }}
        ]
    }]
)
```

### Error Injection

**Configurable failure simulation for testing**

```bash
export FAKEAI_ERROR_INJECTION_ENABLED=true
export FAKEAI_ERROR_INJECTION_RATE=0.15  # 15% error rate
export FAKEAI_ERROR_INJECTION_TYPES='["internal_error", "service_unavailable"]'
fakeai server
```

**Error Types:**
- `internal_error` (500)
- `bad_gateway` (502)
- `service_unavailable` (503)
- `gateway_timeout` (504)
- `rate_limit_quota` (429)
- `context_length_exceeded` (400)

---

## Configuration

### Environment Variables

```bash
# Server
FAKEAI_HOST=0.0.0.0                    # Server host
FAKEAI_PORT=8000                       # Server port
FAKEAI_DEBUG=false                     # Debug mode

# Authentication
FAKEAI_REQUIRE_API_KEY=true            # Require API key
FAKEAI_API_KEYS=key1,key2,key3         # Comma-separated keys
FAKEAI_HASH_API_KEYS=false             # SHA-256 hashing

# Timing
FAKEAI_TTFT_MS=20                      # Time to first token (ms)
FAKEAI_TTFT_VARIANCE_PERCENT=10        # TTFT variance (%)
FAKEAI_ITL_MS=5                        # Inter-token latency (ms)
FAKEAI_ITL_VARIANCE_PERCENT=10         # ITL variance (%)

# KV Cache (AI-Dynamo)
FAKEAI_KV_CACHE_ENABLED=true           # Enable KV cache
FAKEAI_KV_CACHE_BLOCK_SIZE=16          # Block size (tokens)
FAKEAI_KV_CACHE_NUM_WORKERS=4          # Simulated workers
FAKEAI_KV_OVERLAP_WEIGHT=1.0           # Cache overlap weight

# Rate Limiting
FAKEAI_RATE_LIMIT_ENABLED=false        # Enable rate limiting
FAKEAI_RATE_LIMIT_TIER=tier-1          # Tier (tier-1 through tier-5)
FAKEAI_RATE_LIMIT_RPM=500              # Requests per minute
FAKEAI_RATE_LIMIT_TPM=10000            # Tokens per minute

# Error Injection
FAKEAI_ERROR_INJECTION_ENABLED=false   # Enable error injection
FAKEAI_ERROR_INJECTION_RATE=0.0        # Error rate (0.0-1.0)

# Security
FAKEAI_ENABLE_ABUSE_DETECTION=false    # Enable abuse detection
FAKEAI_ENABLE_INPUT_VALIDATION=false   # Enable input validation

# CORS
FAKEAI_CORS_ALLOWED_ORIGINS=*          # Allowed origins
FAKEAI_CORS_ALLOW_CREDENTIALS=true     # Allow credentials
```

### CLI Options

```bash
fakeai server --help

Options:
  --host TEXT              Server host (default: 0.0.0.0)
  --port INTEGER           Server port (default: 8000)
  --debug                  Enable debug mode
  --ttft FLOAT             Time to first token in ms (default: 20)
  --itl FLOAT              Inter-token latency in ms (default: 5)
  --require-api-key        Require API key authentication
  --api-keys TEXT          Comma-separated API keys
  --kv-cache-enabled       Enable KV cache simulation
  --rate-limit-enabled     Enable rate limiting
```

---

## Installation

### From PyPI

```bash
pip install fakeai
```

### From Source

```bash
git clone https://github.com/ajcasagrande/fakeai.git
cd fakeai
pip install -e .
```

### Optional Dependencies

```bash
# Development tools
pip install -e ".[dev]"

# LLM generation (tiktoken, transformers, torch)
pip install -e ".[llm]"

# Semantic embeddings (sentence-transformers)
pip install -e ".[embeddings]"

# Vector stores (faiss)
pip install -e ".[vector]"

# All features
pip install -e ".[all]"
```

---

## Use Cases

### Development

```bash
# Start with zero latency for fast iteration
fakeai server --ttft 0 --itl 0

# Test your application
python my_app.py
```

### Testing

```python
import pytest
from openai import OpenAI

@pytest.fixture
def client():
    return OpenAI(api_key="test", base_url="http://localhost:8000")

def test_chat_completion(client):
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Test"}]
    )
    assert response.choices[0].message.content
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start FakeAI
        run: |
          pip install fakeai
          fakeai server --ttft 0 --itl 0 &
          sleep 5
      - name: Run tests
        run: pytest tests/
```

### Performance Baseline

```bash
# Establish baseline with AIPerf
aiperf profile \
  --model openai/gpt-oss-120b \
  --url http://localhost:8000 \
  --endpoint-type chat \
  --streaming \
  --concurrency 100 \
  --request-count 1000
```

### Load Testing

```bash
# Test at various concurrency levels
for concurrency in 10 50 100 250 500; do
    aiperf profile \
      --model openai/gpt-oss-120b \
      --url http://localhost:8000 \
      --endpoint-type chat \
      --concurrency $concurrency \
      --request-count 500
done
```

---

## Documentation

### Getting Started

- **[CLI Usage](docs/getting-started/CLI_USAGE.md)** - Command-line interface guide
- **[API Key Guide](docs/getting-started/API_KEY_GUIDE.md)** - Authentication setup
- **[Docker](docs/getting-started/DOCKER.md)** - Docker deployment

### API Reference

- **[API Reference](docs/api/API_REFERENCE.md)** - Complete API documentation
- **[Endpoints](docs/api/ENDPOINTS.md)** - All available endpoints
- **[Schemas](docs/api/SCHEMAS.md)** - Request/response schemas
- **[Examples](docs/api/EXAMPLES.md)** - Code examples
- **[Realtime API](docs/api/REALTIME_API.md)** - WebSocket streaming

### Features

- **[Features Overview](docs/guides/features/FEATURES.md)** - Complete feature list
- **[Reasoning Support](docs/guides/features/REASONING_SUPPORT.md)** - Advanced reasoning
- **[Structured Outputs](docs/guides/features/STRUCTURED_OUTPUTS.md)** - JSON schema validation
- **[Tool Calling](docs/guides/features/TOOL_CALLING.md)** - Function calling
- **[Multimodal](docs/guides/features/MULTIMODAL.md)** - Vision, audio, video
- **[Image Generation](docs/guides/features/IMAGE_GENERATION_README.md)** - Image creation
- **[Semantic Embeddings](docs/guides/features/SEMANTIC_EMBEDDINGS.md)** - Vector embeddings
- **[Streaming](docs/guides/features/STREAMING_ADVANCED_IMPLEMENTATION.md)** - Advanced streaming
- **[Safety](docs/guides/features/SAFETY_IMPLEMENTATION.md)** - Content moderation

### Deployment

- **[AWS Deployment](docs/guides/deployment/DEPLOYMENT_AWS.md)** - Deploy to AWS
- **[Azure Deployment](docs/guides/deployment/DEPLOYMENT_AZURE.md)** - Deploy to Azure
- **[Cloud Run](docs/guides/deployment/DEPLOYMENT_CLOUD_RUN.md)** - Deploy to GCP Cloud Run
- **[Kubernetes](docs/guides/deployment/DEPLOYMENT_K8S.md)** - Deploy to Kubernetes
- **[HTTP/2 Guide](docs/guides/deployment/HTTP2_GUIDE.md)** - Enable HTTP/2

### Configuration

- **[Configuration Reference](docs/guides/configuration/CONFIGURATION_REFERENCE.md)** - All config options
- **[Configuration Summary](docs/guides/configuration/CONFIGURATION_SUMMARY.md)** - Quick reference
- **[Context Validator](docs/guides/configuration/CONTEXT_VALIDATOR_README.md)** - Context length validation

### Monitoring & Performance

- **[Monitoring System](docs/guides/monitoring/MONITORING_SYSTEM.md)** - Metrics and monitoring
- **[Metrics Streaming](docs/guides/monitoring/METRICS_STREAMING.md)** - Real-time metrics
- **[Model Metrics](docs/guides/monitoring/MODEL_METRICS_README.md)** - Per-model tracking
- **[Operations](docs/guides/monitoring/OPERATIONS.md)** - Operational guide
- **[Performance](docs/guides/performance/PERFORMANCE.md)** - Performance benchmarks
- **[Performance Tuning](docs/guides/performance/PERFORMANCE_TUNING.md)** - Optimization guide

### Development

- **[Contributing](docs/development/CONTRIBUTING.md)** - Contribution guidelines
- **[Architecture](docs/development/ARCHITECTURE.md)** - System architecture
- **[Development Guide](docs/development/DEVELOPMENT.md)** - Developer setup
- **[Testing](docs/development/TESTING.md)** - Testing guide
- **[CLAUDE.md](docs/development/CLAUDE.md)** - AI assistant knowledge base
- **[Migration Guide](docs/development/MIGRATION_GUIDE.md)** - Version upgrades
- **[Middleware Architecture](docs/development/MIDDLEWARE_ARCHITECTURE.md)** - Middleware system

### Reference

- **[Changelog](docs/reference/CHANGELOG.md)** - Version history
- **[Security](docs/reference/SECURITY.md)** - Security features
- **[Client SDK](docs/reference/CLIENT_SDK.md)** - SDK documentation
- **[Error Injection](docs/reference/ERROR_INJECTION.md)** - Testing with errors

### Research

Background research and technical analysis documents:

- **[DCGM Health Metrics](docs/research/DCGM_HEALTH_METRICS_RESEARCH.md)** - DCGM health monitoring metrics
- **[DCGM Profiling](docs/research/DCGM_PROFILING_RESEARCH.md)** - GPU profiling with DCGM
- **[Dynamo Inference Metrics](docs/research/DYNAMO_INFERENCE_METRICS_RESEARCH.md)** - AI-Dynamo metrics system
- **[Fine-tuning](docs/research/FINE_TUNING_RESEARCH.md)** - Fine-tuning API research
- **[GPU Architecture Metrics](docs/research/GPU_ARCHITECTURE_METRICS_CATALOG.md)** - Comprehensive GPU metrics catalog
- **[gRPC HTTP/2](docs/research/GRPC_HTTP2_RESEARCH.md)** - gRPC and HTTP/2 analysis
- **[Realtime API](docs/research/REALTIME_API_RESEARCH.md)** - OpenAI Realtime API research
- **[TensorRT-LLM Metrics](docs/research/TENSORRT_LLM_METRICS.md)** - TensorRT-LLM performance metrics
- **[Triton Metrics](docs/research/TRITON_METRICS_RESEARCH.md)** - NVIDIA Triton metrics
- **[Usage Billing API](docs/research/USAGE_BILLING_API_RESEARCH.md)** - OpenAI usage tracking research

### Interactive Documentation

When the server is running:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Metrics Dashboard:** http://localhost:8000/dashboard
- **Dynamo Dashboard:** http://localhost:8000/dashboard/dynamo

---

## Testing

### Run Tests

```bash
# All tests (2,500+ tests)
pytest -v

# Specific module
pytest tests/test_embedding_service.py -v

# With coverage
pytest --cov=fakeai --cov-report=html

# Specific markers
pytest -m unit -v                # Unit tests
pytest -m integration -v         # Integration tests
pytest -m service -v             # Service layer tests
```

---

## Compatibility

FakeAI is 100% compatible with:

- **OpenAI Python SDK** (v1.0+)
- **OpenAI Node SDK** (v4.0+)
- **NVIDIA AIPerf** (v1.0+)
- **NVIDIA NIM** - Native NIM endpoint support
- **LangChain** (via OpenAI integration)
- **LlamaIndex** (via OpenAI integration)
- **Any OpenAI-compatible client**

---

## Requirements

- **Python 3.10+**
- **FastAPI** - Web framework
- **Pydantic v2** - Data validation
- **uvicorn** - ASGI server
- **hypercorn** - HTTP/2 support
- **numpy** - Numerical operations
- **faker** - Realistic data generation

---

## Architecture

FakeAI is built with **90+ modular components** organized into:

- **4 core modules** - app, service, CLI, async server
- **11 configuration modules** - Type-safe, domain-specific configs
- **7 model modules** - Organized by feature (chat, embeddings, images, audio, batches)
- **9 registry modules** - Model catalog with fuzzy matching and capabilities
- **8 service modules** - Single-responsibility business logic
- **8 shared utilities** - Zero code duplication
- **18 metrics systems** - Production-grade monitoring
- **6 content generation modules** - Optional ML integration
- **10+ infrastructure modules** - Security, rate limiting, file management

**Design Principles:**
- Single Responsibility - Each module has one clear purpose
- Zero Duplication - Shared utilities eliminate repetition
- Test-Driven - 2,500+ tests with behavior-driven design
- Type-Safe - Full type hints with Python 3.10+ syntax
- Thread-Safe - Singleton patterns with locks
- Async Throughout - High-performance async/await
- Production-Ready - Battle-tested patterns

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](docs/development/CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/ajcasagrande/fakeai.git
cd fakeai

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Format code
black fakeai/ && isort fakeai/

# Run linters
flake8 fakeai/
mypy fakeai/
```

---

## License

Apache-2.0

---

## Support

- **Issues:** https://github.com/ajcasagrande/fakeai/issues
- **Discussions:** https://github.com/ajcasagrande/fakeai/discussions

---

## Acknowledgments

FakeAI is built with production-grade engineering practices and is actively used for development, testing, and benchmarking of AI applications. Special thanks to:

- **NVIDIA AI-Dynamo** - KV cache and smart routing inspiration
- **NVIDIA NIM** - Inference microservices standards
- **NVIDIA DCGM** - GPU telemetry standards
- **NVIDIA Cosmos** - Video understanding capabilities
- **AIPerf** - Comprehensive benchmarking framework
- **Solido** - RAG integration patterns
- **OpenAI** - API specification and standards

---

**Note:** FakeAI is a simulation server for testing and development. For production inference, use actual inference servers like NVIDIA Dynamo.
