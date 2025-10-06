# FakeAI Performance Guide

**Version:** 1.0.0
**Last Updated:** 2025-10-04
**Purpose:** Performance characteristics, KV cache optimization, and monitoring guide

---

## Table of Contents

1. [Overview](#overview)
2. [KV Cache System](#kv-cache-system)
3. [Smart Routing](#smart-routing)
4. [Performance Monitoring](#performance-monitoring)
5. [Optimization Tips](#optimization-tips)
6. [Rate Limiting](#rate-limiting)
7. [Benchmarking](#benchmarking)
8. [Troubleshooting](#troubleshooting)

---

## Overview

FakeAI simulates NVIDIA AI-Dynamo's KV cache reuse system with radix tree prefix matching and intelligent request routing. This guide explains how to monitor and optimize cache performance.

### Key Performance Features

- **KV Cache Reuse**: Radix tree-based prefix matching reduces redundant computation
- **Smart Routing**: Cache-aware load balancing across workers
- **Rate Limiting**: Per-API-key RPM/TPM limits
- **Metrics Tracking**: Real-time performance monitoring
- **Configurable Delays**: Simulate realistic response times

---

## KV Cache System

### Architecture

```
Request → Tokenize → Radix Tree Lookup → Cache Hit/Miss
                           ↓
                    Smart Router
                           ↓
              Route to Optimal Worker
                           ↓
            Process (reuse cached KV blocks)
                           ↓
              Update Cache → Response
```

### Components

#### 1. Radix Tree

**Purpose:** Efficient O(n) prefix matching for token sequences.

**Structure:**
- Each node represents a token
- Complete blocks (16 tokens) are marked as cached
- Workers associated with each cached prefix

**Operations:**
- `insert(tokens, worker_id)`: Add token sequence to tree
- `find_longest_prefix(tokens)`: Find matching prefix
- `get_stats()`: Get tree statistics

#### 2. Smart Router

**Purpose:** Route requests to workers with best cache overlap.

**Routing Algorithm:**
```
cost = kv_overlap_weight × prefill_blocks +
       decode_blocks +
       load_balance_weight × active_requests
```

**Choose worker with lowest cost.**

**Parameters:**
- `kv_overlap_weight` (default: 1.0) - Weight for cache overlap
- `load_balance_weight` (default: 0.5) - Weight for load balancing
- `block_size` (default: 16) - Tokens per cache block
- `num_workers` (default: 4) - Number of simulated workers

#### 3. KV Cache Metrics

**Purpose:** Track cache performance.

**Metrics:**
- **Cache hit rate**: Percentage of requests with cache hits
- **Token reuse rate**: Percentage of tokens reused from cache
- **Average prefix length**: Mean matched prefix size
- **Per-endpoint stats**: Cache performance by API endpoint

### How Caching Works

**Step 1: Tokenization**
```python
from fakeai.kv_cache import tokenize_for_cache

text = "What is machine learning?"
tokens = tokenize_for_cache(text)
# Returns: [12847, 318, 4572, 4673, ...]
```

Uses stable MD5 hashing to convert text → deterministic token IDs.

**Step 2: Prefix Matching**
```python
matched_tokens, matched_blocks, workers = radix_tree.find_longest_prefix(tokens)
# matched_tokens: 128 (out of 256 total)
# matched_blocks: 8 (8 × 16 = 128 tokens)
# workers: {"worker-0", "worker-2"}
```

**Step 3: Routing**
```python
worker_id, matched, blocks = kv_cache_router.route_request(tokens)
# worker_id: "worker-0" (has best cache overlap + lowest load)
```

**Step 4: Processing**
- Only 128 tokens need prefill (50% saved)
- Decode phase proceeds normally

**Step 5: Cache Update**
```python
kv_cache_router.complete_request(worker_id, tokens, output_tokens)
# Updates radix tree
# Marks blocks as cached on worker
```

### Cache Performance Characteristics

**Best Case: 90%+ Cache Hit Rate**
- Repeated similar prompts (e.g., RAG with same context)
- Multi-turn conversations
- Batch requests with shared prefixes

**Typical Case: 50-70% Cache Hit Rate**
- Mix of new and repeated prompts
- Similar templates with variations

**Worst Case: 0-20% Cache Hit Rate**
- Completely unique prompts
- Random text generation
- No pattern in requests

**Token Reuse Example:**
```
Request 1: "Explain quantum computing in detail" → 0% cached
Request 2: "Explain quantum computing applications" → 60% cached
Request 3: "Explain quantum computing history" → 55% cached
```

Shared prefix "Explain quantum computing" is reused.

---

## Smart Routing

### Routing Decision Factors

**1. KV Cache Overlap**
- Primary factor (weight: 1.0)
- Prefers workers with matching prefixes
- Reduces prefill computation

**2. Worker Load**
- Secondary factor (weight: 0.5)
- Balances across workers
- Prevents overload on single worker

**3. Prefill vs Decode Cost**
- Prefill: Expensive (proportional to input length)
- Decode: Cheaper (per-token generation)

### Cost Calculation

```python
def calculate_cost(tokens, matched_tokens, worker, estimated_output):
    tokens_to_prefill = len(tokens) - matched_tokens
    prefill_blocks = tokens_to_prefill / block_size  # 16 tokens/block
    decode_blocks = estimated_output / block_size
    load = worker.active_requests

    cost = (
        kv_overlap_weight * prefill_blocks +     # 1.0 × prefill
        decode_blocks +                          # 1.0 × decode
        load_balance_weight * load               # 0.5 × load
    )

    return cost
```

**Example:**
```
Worker 0: matched=128 tokens, load=2 requests
  prefill_blocks = (256 - 128) / 16 = 8
  decode_blocks = 100 / 16 = 6.25
  cost = 1.0×8 + 6.25 + 0.5×2 = 15.25

Worker 1: matched=64 tokens, load=1 request
  prefill_blocks = (256 - 64) / 16 = 12
  decode_blocks = 6.25
  cost = 1.0×12 + 6.25 + 0.5×1 = 18.75

→ Choose Worker 0 (lower cost)
```

### Multi-Worker Simulation

FakeAI simulates 4 workers by default:
- `worker-0`, `worker-1`, `worker-2`, `worker-3`
- Each tracks active requests, cached blocks, tokens processed
- Router balances load while maximizing cache hits

### Optimizing Routing

**Increase KV Overlap Weight** (better cache utilization):
```python
self.kv_cache_router = SmartRouter(
    kv_overlap_weight=2.0,  # Prioritize cache hits
    load_balance_weight=0.3,
    block_size=16,
    num_workers=4
)
```

**Increase Load Balance Weight** (better distribution):
```python
self.kv_cache_router = SmartRouter(
    kv_overlap_weight=0.8,
    load_balance_weight=1.0,  # Prioritize load balancing
    block_size=16,
    num_workers=4
)
```

---

## Performance Monitoring

### Accessing Metrics

**Server Metrics:**
```bash
curl http://localhost:8000/metrics | jq
```

**KV Cache Metrics:**
```bash
curl http://localhost:8000/kv-cache-metrics | jq
```

### Interpreting Cache Metrics

```json
{
  "cache_performance": {
    "cache_hit_rate": 65.3,           // % of requests with cache hits
    "token_reuse_rate": 42.8,         // % of tokens reused
    "total_cache_hits": 1250,         // Total hits
    "total_cache_misses": 665,        // Total misses
    "total_tokens_processed": 150000, // Total tokens
    "cached_tokens_reused": 64200,    // Tokens from cache
    "avg_prefix_length": 128.5,       // Average matched prefix
    "by_endpoint": {
      "/v1/chat/completions": {
        "hits": 1200,
        "misses": 600
      }
    }
  }
}
```

**Key Metrics:**

1. **Cache Hit Rate** (target: >50%)
   - % of requests that found matching prefixes
   - Higher = better cache utilization

2. **Token Reuse Rate** (target: >30%)
   - % of tokens served from cache
   - Directly correlates to cost savings

3. **Average Prefix Length** (target: >64 tokens)
   - Longer prefixes = more reuse
   - Depends on request similarity

### Router Statistics

```json
{
  "smart_router": {
    "workers": {
      "worker-0": {
        "active_requests": 2,          // Current load
        "total_requests": 500,         // Lifetime requests
        "cached_blocks": 1250,         // Cached blocks
        "tokens_processed": 50000      // Lifetime tokens
      }
    },
    "radix_tree": {
      "total_nodes": 5000,             // Tree size
      "total_cached_blocks": 4800      // Cached blocks
    }
  }
}
```

**Load Balancing Check:**
- Compare `total_requests` across workers
- Should be relatively even (within 20%)
- Imbalance indicates routing issues

**Cache Size:**
- `total_cached_blocks` grows over time
- Represents cached knowledge
- No eviction policy (simulation only)

### Response Time Metrics

```json
{
  "responses": {
    "/v1/chat/completions": {
      "rate": 10.4,      // Requests per second
      "avg": 0.15,       // Average latency (seconds)
      "min": 0.12,       // Minimum latency
      "max": 0.18,       // Maximum latency
      "p50": 0.15,       // 50th percentile
      "p90": 0.17,       // 90th percentile
      "p99": 0.18        // 99th percentile
    }
  }
}
```

**Latency Targets:**
- `p50 < 200ms`: Good for testing
- `p90 < 500ms`: Acceptable simulation
- `p99 < 1s`: Worst-case reasonable

### Token Rate

```json
{
  "tokens": {
    "/v1/chat/completions": {
      "rate": 520.3  // Tokens per second
    }
  }
}
```

Useful for load testing and capacity planning.

---

## Optimization Tips

### 1. Maximize Cache Hits

**Use Shared Prefixes:**
```python
# Good: Shared system message
system = "You are a helpful assistant."
messages = [
    {"role": "system", "content": system},
    {"role": "user", "content": query}
]

# Bad: Random system messages
messages = [
    {"role": "system", "content": f"Assistant {random.randint(1, 100)}"},
    {"role": "user", "content": query}
]
```

**RAG Pattern:**
```python
# Reuse context across queries
context = load_rag_context()  # Same for many queries
for query in queries:
    messages = [
        {"role": "system", "content": context},
        {"role": "user", "content": query}
    ]
    # High cache hit on context
```

**Template-Based Prompts:**
```python
template = "Summarize the following text:\n\n{text}"
# Shared prefix "Summarize the following text:"
```

### 2. Tune Response Delays

**Default delays simulate realistic inference:**
```python
# Environment variables
export FAKEAI_RESPONSE_DELAY=0.5      # Base delay (seconds)
export FAKEAI_RANDOM_DELAY=true       # Add variance
export FAKEAI_MAX_VARIANCE=0.3        # Max ±30%
```

**For testing (minimal delay):**
```python
export FAKEAI_RESPONSE_DELAY=0.0
export FAKEAI_RANDOM_DELAY=false
```

**For load testing (realistic):**
```python
export FAKEAI_RESPONSE_DELAY=0.3
export FAKEAI_RANDOM_DELAY=true
export FAKEAI_MAX_VARIANCE=0.5
```

### 3. Configure Rate Limiting

**Disable for benchmarking:**
```bash
export FAKEAI_RATE_LIMIT_ENABLED=false
```

**Enable for realistic testing:**
```bash
export FAKEAI_RATE_LIMIT_ENABLED=true
export FAKEAI_RATE_LIMIT_TIER=tier1
# tier1: 500 RPM, 10k TPM
```

**Custom limits:**
```bash
export FAKEAI_RATE_LIMIT_RPM=1000
export FAKEAI_RATE_LIMIT_TPM=50000
```

### 4. Optimize Worker Configuration

**More workers (better parallelism):**
```python
# In fakeai_service.py
self.kv_cache_router = SmartRouter(
    kv_overlap_weight=1.0,
    load_balance_weight=0.5,
    block_size=16,
    num_workers=8  # Increase from 4
)
```

**Larger block size (coarser caching):**
```python
self.kv_cache_router = SmartRouter(
    kv_overlap_weight=1.0,
    load_balance_weight=0.5,
    block_size=32,  # Increase from 16
    num_workers=4
)
```

### 5. Monitor Continuously

**Prometheus-style scraping:**
```bash
while true; do
  curl -s http://localhost:8000/kv-cache-metrics | \
    jq '.cache_performance.cache_hit_rate'
  sleep 10
done
```

**Log to file:**
```bash
while true; do
  curl -s http://localhost:8000/kv-cache-metrics >> cache_metrics.jsonl
  echo >> cache_metrics.jsonl
  sleep 60
done
```

---

## Rate Limiting

### Configuration

**Tier-based limits:**
```bash
export FAKEAI_RATE_LIMIT_TIER=tier3
```

**Tiers:**
| Tier | RPM | TPM |
|------|-----|-----|
| free | 60 | 1,000 |
| tier1 | 500 | 10,000 |
| tier2 | 1,000 | 50,000 |
| tier3 | 5,000 | 200,000 |
| tier4 | 10,000 | 500,000 |
| tier5 | 30,000 | 1,500,000 |

**Custom overrides:**
```bash
export FAKEAI_RATE_LIMIT_RPM=1000
export FAKEAI_RATE_LIMIT_TPM=50000
```

### Monitoring Rate Limits

**Response headers:**
```
X-RateLimit-Limit-Requests: 10000
X-RateLimit-Limit-Tokens: 2000000
X-RateLimit-Remaining-Requests: 9850
X-RateLimit-Remaining-Tokens: 1950000
X-RateLimit-Reset-Requests: 45s
X-RateLimit-Reset-Tokens: 45s
```

**429 Response:**
```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded.",
    "type": "rate_limit_error"
  }
}
```

**Retry-After header:**
```
Retry-After: 30
```

### Handling Rate Limits

**Exponential backoff:**
```python
import time
import random

def call_with_retry(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
```

**Check remaining:**
```python
response = client.chat.completions.create(...)
remaining = response.headers.get('X-RateLimit-Remaining-Requests')
if int(remaining) < 10:
    time.sleep(5)  # Throttle
```

---

## Benchmarking

### Load Testing Setup

**1. Install tools:**
```bash
pip install locust httpx
```

**2. Create locustfile.py:**
```python
from locust import HttpUser, task, between

class OpenAIUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self):
        self.headers = {
            "Authorization": "Bearer sk-fakeai-1234567890abcdef",
            "Content-Type": "application/json"
        }

    @task
    def chat_completion(self):
        self.client.post("/v1/chat/completions",
            headers=self.headers,
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "user", "content": "Hello"}
                ]
            }
        )
```

**3. Run test:**
```bash
locust -f locustfile.py --host http://localhost:8000
```

Open http://localhost:8089 and start test.

### Benchmark Scenarios

**Scenario 1: High Cache Hit**
```python
# Shared prefix across requests
@task
def chat_with_shared_prefix(self):
    self.client.post("/v1/chat/completions",
        headers=self.headers,
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Question {random.randint(1, 100)}"}
            ]
        }
    )
```

Expected: 60-80% cache hit rate

**Scenario 2: Low Cache Hit**
```python
@task
def chat_unique(self):
    self.client.post("/v1/chat/completions",
        headers=self.headers,
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [
                {"role": "user", "content": str(uuid.uuid4())}
            ]
        }
    )
```

Expected: 0-10% cache hit rate

**Scenario 3: Streaming**
```python
@task
def chat_streaming(self):
    with self.client.post("/v1/chat/completions",
        headers=self.headers,
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Write a story"}],
            "stream": True
        },
        stream=True
    ) as response:
        for line in response.iter_lines():
            pass  # Consume stream
```

### Analyzing Results

**Key metrics to track:**
1. **Requests/sec** (target: >100 for testing)
2. **Response time p95** (target: <500ms)
3. **Cache hit rate** (target: >50% for similar requests)
4. **Token reuse rate** (target: >30%)
5. **Error rate** (target: <0.1%)

**Example results:**
```
Requests/sec: 250
Response time p50: 150ms
Response time p95: 350ms
Cache hit rate: 68%
Token reuse rate: 45%
Error rate: 0%
```

---

## Troubleshooting

### Low Cache Hit Rate

**Symptom:** `cache_hit_rate < 30%`

**Possible causes:**
1. Unique prompts with no shared prefixes
2. Short prompts (< 32 tokens)
3. Randomized system messages

**Solutions:**
- Use consistent system messages
- Template-based prompts with shared prefixes
- Batch similar requests together

### Uneven Worker Distribution

**Symptom:** One worker has 80% of requests

**Possible causes:**
1. `load_balance_weight` too low
2. All requests have same prefix (go to same worker)

**Solutions:**
- Increase `load_balance_weight` to 1.0
- Verify prompt diversity

### High p99 Latency

**Symptom:** `p99 > 2 seconds`

**Possible causes:**
1. `FAKEAI_RESPONSE_DELAY` too high
2. Streaming with large outputs
3. Long prompts causing token calculation overhead

**Solutions:**
- Reduce `FAKEAI_RESPONSE_DELAY`
- Set `FAKEAI_RANDOM_DELAY=false`
- Check for very long prompts (>10k tokens)

### Memory Usage Growing

**Symptom:** Process memory increases over time

**Possible causes:**
1. Radix tree growing unbounded
2. Metrics accumulating

**Solutions:**
- Restart server periodically (simulation only)
- In production, implement cache eviction (not in FakeAI)

### Rate Limit False Positives

**Symptom:** 429 errors with low load

**Possible causes:**
1. Sliding window timing
2. Token estimation too high

**Solutions:**
- Increase rate limits
- Wait for window reset
- Check `X-RateLimit-Reset-Requests` header

---

## Best Practices Summary

### Cache Optimization

 **DO:**
- Use shared system messages
- Template-based prompts
- Batch similar requests
- Monitor cache hit rate

 **DON'T:**
- Randomize system messages
- Use unique prompts unnecessarily
- Ignore cache metrics

### Performance Testing

 **DO:**
- Test with realistic request patterns
- Monitor cache metrics during tests
- Use multiple API keys for load testing
- Measure p50, p90, p99 latencies

 **DON'T:**
- Test with all unique prompts
- Ignore rate limiting
- Run single-threaded tests
- Forget to check metrics

### Production-Like Testing

 **DO:**
- Enable rate limiting
- Configure realistic delays
- Use multiple workers
- Monitor continuously

 **DON'T:**
- Disable all limits for "realistic" test
- Use zero delays
- Ignore error rates

---

## Metrics Dashboard Example

**Create simple dashboard:**
```python
import time
import httpx
from rich.console import Console
from rich.table import Table

console = Console()

while True:
    metrics = httpx.get("http://localhost:8000/kv-cache-metrics").json()
    cache = metrics["cache_performance"]

    table = Table(title="FakeAI Cache Performance")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Cache Hit Rate", f"{cache['cache_hit_rate']:.1f}%")
    table.add_row("Token Reuse Rate", f"{cache['token_reuse_rate']:.1f}%")
    table.add_row("Total Hits", str(cache['total_cache_hits']))
    table.add_row("Total Misses", str(cache['total_cache_misses']))
    table.add_row("Avg Prefix Length", f"{cache['avg_prefix_length']:.1f}")

    console.clear()
    console.print(table)

    time.sleep(5)
```

Run: `python dashboard.py`

---

## Conclusion

FakeAI's KV cache system provides realistic simulation of production caching behavior:

- **Radix tree** for efficient prefix matching
- **Smart routing** for cache-aware load balancing
- **Comprehensive metrics** for monitoring
- **Configurable** for different testing scenarios

Use this guide to optimize your testing, monitor performance, and understand cache behavior before deploying to production AI inference systems.

---

**Last Updated:** 2025-10-04
**Version:** 1.0.0
