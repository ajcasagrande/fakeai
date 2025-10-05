# FakeAI

**OpenAI-Compatible API Server for Testing, Development & Benchmarking**

[![PyPI version](https://badge.fury.io/py/fakeai.svg)](https://badge.fury.io/py/fakeai)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Tests](https://github.com/ajcasagrande/fakeai/workflows/Tests/badge.svg)](https://github.com/ajcasagrande/fakeai/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/ajcasagrande/fakeai/branch/main/graph/badge.svg)](https://codecov.io/gh/ajcasagrande/fakeai)

FakeAI is a high-performance simulation of the OpenAI API that returns realistic responses without performing actual inference. Ideal for development, testing, CI/CD pipelines, and LLM application benchmarking.

## Key Features

- Zero-cost testing with unlimited requests
- 100% OpenAI schema compliance
- No external dependencies or API keys required
- Handles 10,000+ concurrent requests
- Comprehensive metrics and monitoring
- AIPerf benchmarking support

## Installation

```bash
pip install fakeai
```

## Quick Start

```bash
# Start server
fakeai-server

# Use with OpenAI client
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

## Core Features

### OpenAI API Compatibility

- **Chat Completions** - Streaming, tools, multi-modal content
- **Embeddings** - Vector generation for RAG applications
- **Images** - DALL-E simulation
- **Audio** - Speech synthesis and transcription
- **Moderations** - Content safety classification
- **Files** - Upload and management
- **Batches** - Asynchronous batch processing
- **Tool Calling** - Function calls with parallel execution
- **Structured Outputs** - JSON Schema validation
- **Log Probabilities** - Token-level logprobs
- **Responses API** - March 2025 format
- **Vector Stores** - Document storage and retrieval

### NVIDIA AI-Dynamo Features

- **KV Cache Reuse** - Radix tree prefix matching with smart routing
- **Smart Router** - Cache-aware request routing
- **KVBM** - 4-tier memory hierarchy (GPU HBM, CPU DRAM, SSD, Remote)
- **SLA-Based Planner** - Load prediction with ARIMA and Prophet
- **DCGM Metrics** - GPU metrics simulation (25+ field IDs)
- **Dynamo Metrics** - TTFT, ITL, TPOT, latency breakdown

### Performance & Monitoring

- **uvloop Integration** - 2-4x faster async I/O
- **Numpy Metrics** - Sliding window rate calculations
- **Prometheus Export** - Standard metrics format
- **Real-Time Dashboards** - Web UI with Chart.js
- **Configurable Latency** - TTFT and ITL with variance control

## Configuration

### Environment Variables

```bash
# Server
export FAKEAI_HOST=0.0.0.0
export FAKEAI_PORT=9001

# Latency (milliseconds)
export FAKEAI_TTFT_MS=20
export FAKEAI_ITL_MS=5

# Security (disabled by default)
export FAKEAI_ENABLE_SECURITY=false
export FAKEAI_REQUIRE_API_KEY=false
```

### CLI Arguments

```bash
# Basic usage
fakeai-server --host 0.0.0.0 --port 9001

# Configure latency
fakeai-server --ttft 20 --itl 5

# Latency with variance
fakeai-server --ttft 50:30 --itl 10:20  # 50ms ±30%, 10ms ±20%

# Enable security
fakeai-server --enable-security --api-key sk-test-key
```

### Config File

Create `fakeai.yaml`:

```yaml
host: 0.0.0.0
port: 9001
ttft_ms: 20.0
itl_ms: 5.0
kv_cache_enabled: true
enable_security: false
```

Run with config:

```bash
fakeai-server --config-file fakeai.yaml
```

## API Endpoints

### Core OpenAI API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | Chat completions with streaming and tools |
| `/v1/completions` | POST | Text completions |
| `/v1/embeddings` | POST | Text embeddings |
| `/v1/images/generations` | POST | Image generation |
| `/v1/audio/speech` | POST | Text-to-speech |
| `/v1/moderations` | POST | Content moderation |
| `/v1/models` | GET | List models |
| `/v1/files` | GET/POST/DELETE | File management |
| `/v1/batches` | POST/GET | Batch processing |

### Extended APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/responses` | POST | Responses API (March 2025) |
| `/v1/ranking` | POST | NVIDIA NIM Rankings |
| `/v1/vector_stores` | POST/GET/DELETE | Vector store management |

### Organization APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/organization/users` | GET/POST | User management |
| `/v1/organization/projects` | GET/POST | Project management |
| `/v1/organization/usage/*` | GET | Usage tracking |
| `/v1/organization/costs` | GET | Cost tracking |

### Monitoring

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/metrics` | GET | JSON metrics |
| `/metrics/prometheus` | GET | Prometheus format |
| `/kv-cache-metrics` | GET | KV cache performance |
| `/dcgm-metrics` | GET | GPU metrics |
| `/dynamo-metrics` | GET | Inference metrics |
| `/dashboard` | GET | Main dashboard |
| `/dashboard/dynamo` | GET | Advanced metrics dashboard |

## Examples

### Basic Chat

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000", api_key="not-needed")

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing."}
    ]
)
print(response.choices[0].message.content)
```

### Streaming

```python
stream = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Write a haiku"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### Tool Calling

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
        }
    }
}]

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Weather in Tokyo?"}],
    tools=tools
)

for tool_call in response.choices[0].message.tool_calls:
    print(f"{tool_call.function.name}: {tool_call.function.arguments}")
```

### Structured Outputs

```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Extract: Alice is 25"}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "person",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "number"}
                },
                "required": ["name", "age"]
            }
        }
    }
)
```

### Embeddings

```python
response = client.embeddings.create(
    model="sentence-transformers/all-mpnet-base-v2",
    input="The quick brown fox jumps over the lazy dog"
)
print(f"Dimensions: {len(response.data[0].embedding)}")
```

### Reasoning Models

```python
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1",
    messages=[{"role": "user", "content": "Solve: 2x + 5 = 15"}]
)

print("Reasoning:", response.choices[0].message.reasoning_content)
print("Answer:", response.choices[0].message.content)
```

### NVIDIA NIM Rankings

```python
import httpx

response = httpx.post(
    "http://localhost:8000/v1/ranking",
    json={
        "model": "nvidia/nv-rerankqa-mistral-4b-v3",
        "query": {"text": "What is machine learning?"},
        "passages": [
            {"text": "Machine learning is a subset of AI"},
            {"text": "Python is a programming language"}
        ]
    }
)
```

## Benchmarking

FakeAI supports [AIPerf](https://github.com/ai-dynamo/aiperf), the successor to NVIDIA GenAI-Perf.

### Install AIPerf

```bash
pip install aiperf
```

### Run Benchmark

```bash
# Start server
fakeai-server --port 9001 --ttft 20 --itl 5

# Run benchmark
aiperf profile \
  --model openai/gpt-oss-120b \
  --url http://localhost:9001 \
  --endpoint-type chat \
  --service-kind openai \
  --streaming \
  --concurrency 100 \
  --request-count 1000
```

### Automated Suite

```bash
cd benchmarks
python run_aiperf_benchmarks.py --quick
```

See `benchmarks/README.md` for complete benchmarking guide.

## Performance

Benchmarked performance at concurrency 500, 1000 requests:

```
Request Throughput:        930 req/s
Output Token Throughput:   198,910 tokens/s
Average Latency:           492 ms
P99 Latency:               636 ms
Time to First Token:       492 ms (avg), 636 ms (p99)
```

Proven capacity: 10,000 concurrent requests with 100% success rate.

## Monitoring

### Metrics Endpoints

```bash
# JSON format
curl http://localhost:8000/metrics

# Prometheus format
curl http://localhost:8000/metrics/prometheus

# KV cache metrics
curl http://localhost:8000/kv-cache-metrics

# GPU metrics
curl http://localhost:8000/dcgm-metrics

# Inference metrics
curl http://localhost:8000/dynamo-metrics
```

### CLI Tools

```bash
# Show metrics
fakeai-server metrics

# Watch metrics (refresh every 5s)
fakeai-server metrics --watch

# Check server status
fakeai-server status

# KV cache statistics
fakeai-server cache-stats
```

### Dashboards

- Main dashboard: `http://localhost:8000/dashboard`
- Advanced metrics: `http://localhost:8000/dashboard/dynamo`

## Supported Models

### Chat Models

- `openai/gpt-oss-120b` - 117B MoE
- `openai/gpt-oss-20b` - 20B dense
- `meta-llama/Llama-3.1-8B-Instruct` - Llama 3.1 8B
- `meta-llama/Llama-3.1-70B-Instruct` - Llama 3.1 70B
- `deepseek-ai/DeepSeek-R1` - 671B MoE with reasoning
- `mistralai/Mixtral-8x7B-Instruct-v0.1` - Mixtral 8x7B

### Embedding Models

- `sentence-transformers/all-mpnet-base-v2` - 768 dimensions
- `nomic-ai/nomic-embed-text-v1.5` - 768 dimensions
- `BAAI/bge-m3` - Multilingual

### Image Models

- `stabilityai/stable-diffusion-2-1`
- `stabilityai/stable-diffusion-xl-base-1.0`

### Audio Models

- `whisper-1` - Speech recognition
- `tts-1`, `tts-1-hd` - Text-to-speech

### Dynamic Model Support

Any model ID is automatically created on first use, including LoRA fine-tuned models using the format `ft:base_model:org:id`.

## Advanced Features

### AI-Dynamo KV Cache

Simulates NVIDIA AI-Dynamo's datacenter-scale KV cache optimization:

- Radix tree with O(k) prefix matching
- Smart router with cache-aware routing
- 4 simulated workers with block management
- Configurable block size and overlap weight

Metrics available at `/kv-cache-metrics`.

### DCGM GPU Metrics

Simulates NVIDIA DCGM metrics without real GPUs:

- GPU utilization, temperature, power
- Memory usage and bandwidth
- SM occupancy, tensor core activity
- PCIe and NVLink throughput
- ECC errors and thermal throttling

Available in Prometheus format at `/dcgm-metrics`.

### Dynamo Inference Metrics

LLM inference metrics in NVIDIA Dynamo style:

- Time to First Token (TTFT): p50, p90, p99
- Inter-Token Latency (ITL): p50, p90, p99
- Time Per Output Token (TPOT)
- Latency breakdown: Queue, Prefill, Decode, Total
- Request and token throughput

Available at `/dynamo-metrics` (Prometheus) and `/dynamo-metrics/json`.

## Configuration Reference

### Server Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `FAKEAI_HOST` | `127.0.0.1` | Host to bind |
| `FAKEAI_PORT` | `8000` | Port number |
| `FAKEAI_DEBUG` | `false` | Debug mode |

### Latency Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `FAKEAI_TTFT_MS` | `20` | Time to first token (ms) |
| `FAKEAI_TTFT_VARIANCE_PERCENT` | `10` | TTFT variance (%) |
| `FAKEAI_ITL_MS` | `5` | Inter-token latency (ms) |
| `FAKEAI_ITL_VARIANCE_PERCENT` | `10` | ITL variance (%) |

### Security Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `FAKEAI_ENABLE_SECURITY` | `false` | Master security flag |
| `FAKEAI_API_KEYS` | - | Comma-separated API keys |
| `FAKEAI_REQUIRE_API_KEY` | `false` | Require authentication |
| `FAKEAI_MAX_REQUEST_SIZE` | `104857600` | Max request size (100 MB) |

### Performance Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `FAKEAI_KV_CACHE_ENABLED` | `true` | Enable KV cache |
| `FAKEAI_KV_CACHE_NUM_WORKERS` | `4` | Cache workers |
| `FAKEAI_RATE_LIMIT_ENABLED` | `false` | Enable rate limiting |

See `CONFIGURATION_REFERENCE.md` for complete list.

## CLI Commands

```bash
# Start server
fakeai-server

# Server options
fakeai-server --host 0.0.0.0 --port 9001 --debug
fakeai-server --ttft 20 --itl 5
fakeai-server --enable-security --api-key sk-test

# Monitoring
fakeai-server status
fakeai-server metrics
fakeai-server metrics --watch
fakeai-server cache-stats

# Interactive mode
fakeai-server interactive
```

## Use Cases

### Local Development

```bash
fakeai-server
```

Test OpenAI API integrations locally without API costs or rate limits.

### CI/CD Pipelines

```yaml
- name: Start FakeAI
  run: |
    pip install fakeai
    fakeai-server --port 8000 &
    sleep 2

- name: Run tests
  run: pytest tests/
  env:
    OPENAI_BASE_URL: http://localhost:8000
    OPENAI_API_KEY: not-needed
```

### Benchmarking

```bash
# Minimal latency
fakeai-server --ttft 5 --itl 1

# Run AIPerf
aiperf profile \
  --model openai/gpt-oss-120b \
  --url http://localhost:8000 \
  --concurrency 500 \
  --request-count 5000
```

### RAG Development

```python
# Generate embeddings
embeddings = client.embeddings.create(
    model="sentence-transformers/all-mpnet-base-v2",
    input=["doc1", "doc2", "doc3"]
)

# Rerank results
import httpx
rankings = httpx.post(
    "http://localhost:8000/v1/ranking",
    json={
        "model": "nvidia/nv-rerankqa-mistral-4b-v3",
        "query": {"text": "user query"},
        "passages": [{"text": "doc1"}, {"text": "doc2"}]
    }
)
```

## Architecture

```
fakeai/
├── app.py                # FastAPI application (60+ endpoints)
├── fakeai_service.py     # Core business logic
├── models.py             # Pydantic schemas
├── config.py             # Configuration management
├── metrics.py            # Numpy sliding window metrics
├── kv_cache.py           # AI-Dynamo KV cache
├── dcgm_metrics.py       # GPU metrics simulator
├── dynamo_metrics.py     # LLM inference metrics
├── dynamo_advanced.py    # KVBM, SLA planner, router
├── async_server.py       # uvloop utilities
├── cli.py                # CLI interface
└── utils.py              # Utilities and generators
```

## Development

### Setup

```bash
git clone https://github.com/ajcasagrande/fakeai.git
cd fakeai
pip install -e ".[dev]"
```

### Testing

```bash
pytest
pytest tests/test_numpy_metrics_window.py -v
pytest --cov=fakeai
```

### Code Quality

```bash
black fakeai/
isort fakeai/
mypy fakeai/
```

## Docker

```bash
# Build
docker build -t fakeai .

# Run
docker run -p 8000:8000 fakeai

# With environment variables
docker run -p 9001:9001 \
  -e FAKEAI_PORT=9001 \
  -e FAKEAI_TTFT_MS=10 \
  fakeai
```

## Deployment

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fakeai
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: fakeai
        image: fakeai:latest
        ports:
        - containerPort: 8000
        env:
        - name: FAKEAI_HOST
          value: "0.0.0.0"
```

See `DEPLOYMENT_K8S.md` for complete manifests.

### Cloud Platforms

- AWS: See `DEPLOYMENT_AWS.md`
- Google Cloud: See `DEPLOYMENT_CLOUD_RUN.md`
- Azure: See `DEPLOYMENT_AZURE.md`

## Documentation

- `CLAUDE.md` - Project knowledge base
- `API_REFERENCE.md` - Complete API reference
- `CONFIGURATION_REFERENCE.md` - All configuration options
- `PERFORMANCE.md` - Performance tuning guide
- `SECURITY.md` - Security features
- `benchmarks/README.md` - Benchmarking guide
- Auto-generated docs at `http://localhost:8000/docs`

## Troubleshooting

**Port already in use:**
```bash
fakeai-server --port 9001
```

**Slow performance:**
```bash
pip install uvloop
fakeai-server --ttft 5 --itl 1
```

**AIPerf benchmark fails:**
```bash
# Always include http:// in URL
aiperf profile --url http://localhost:8000  # Correct
```

**Dashboard not loading:**
```bash
curl http://localhost:8000/health  # Verify server running
```

## Contributing

Contributions welcome. Please follow PEP-8, KISS, and DRY principles. Add tests for new features.

See `CONTRIBUTING.md` for guidelines.

## Related Projects

- [AIPerf](https://github.com/ai-dynamo/aiperf) - LLM benchmarking
- [OpenAI Python](https://github.com/openai/openai-python) - Official client
- [vLLM](https://github.com/vllm-project/vllm) - LLM inference engine
- [NVIDIA Triton](https://github.com/triton-inference-server/server) - Inference serving

## License

Apache License 2.0. See LICENSE file for details.

## Links

- **GitHub:** https://github.com/ajcasagrande/fakeai
- **PyPI:** https://pypi.org/project/fakeai/
- **Issues:** https://github.com/ajcasagrande/fakeai/issues

---

**Version:** 0.0.5
**Python:** 3.10, 3.11, 3.12
**Status:** Active Development
