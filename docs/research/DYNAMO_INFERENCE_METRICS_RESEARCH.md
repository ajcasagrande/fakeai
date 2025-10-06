# NVIDIA AI-Dynamo Inference Metrics Research

**Version:** 1.0.0
**Date:** 2025-10-04
**Purpose:** Comprehensive research on NVIDIA Dynamo and vLLM inference metrics for potential FakeAI integration

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [NVIDIA Dynamo Overview](#2-nvidia-dynamo-overview)
3. [Request-Level Metrics](#3-request-level-metrics)
4. [Prefill Metrics](#4-prefill-metrics)
5. [Decode Metrics](#5-decode-metrics)
6. [KV Cache Metrics](#6-kv-cache-metrics)
7. [Routing Metrics](#7-routing-metrics)
8. [Model-Specific Metrics](#8-model-specific-metrics)
9. [Worker Metrics](#9-worker-metrics)
10. [End-to-End Latency Breakdown](#10-end-to-end-latency-breakdown)
11. [vLLM Metrics (Dynamo Backend)](#11-vllm-metrics-dynamo-backend)
12. [Prometheus Metrics Format](#12-prometheus-metrics-format)
13. [Collection Methods](#13-collection-methods)
14. [Implementation Recommendations for FakeAI](#14-implementation-recommendations-for-fakeai)
15. [References](#15-references)

---

## 1. Executive Summary

NVIDIA Dynamo is an open-source, low-latency distributed inference framework announced at GTC 2025 that provides comprehensive metrics for monitoring LLM inference performance across distributed GPU clusters. This research document catalogs all identified metrics to inform potential integration into FakeAI.

### Key Findings

- **30x throughput improvement** for DeepSeek-R1 671B on NVIDIA GB200 NVL72
- **3x improvement in TTFT** through KV-aware routing
- **2x reduction in average request latency** on real workloads
- Comprehensive metrics exposed via `/metrics` endpoint in OpenMetrics format
- Integration with Prometheus/Grafana for observability
- vLLM serves as the primary backend engine with KV cache routing

---

## 2. NVIDIA Dynamo Overview

### 2.1 What is Dynamo?

NVIDIA Dynamo is a datacenter-scale distributed inference serving framework that:

- Maps KV cache knowledge across thousands of GPUs
- Routes requests to GPUs with best knowledge match
- Avoids costly recomputations through intelligent routing
- Supports prefill-decode disaggregation
- Provides SLO-based autoscaling

### 2.2 Architecture Components

1. **GPU Resource Planner** - Monitors capacity and adjusts GPU resources
2. **Smart Router** - KV-cache-aware routing engine
3. **Low Latency Communication Library (NIXL)** - Accelerates KV cache transfer
4. **KV Cache Manager** - Cost-aware KV cache offloading across memory tiers

### 2.3 Metrics Collection Architecture

- **Frontend Component** exposes metrics on HTTP port
- **Worker Component** exposes metrics on system port
- Both expose `/metrics` endpoint in OpenMetrics format
- Automatic labels added: `nvidia.com/metrics-enabled: "true"` and `nvidia.com/dynamo-component-type: "frontend|worker"`
- Integration with kube-prometheus-stack via PodMonitors

---

## 3. Request-Level Metrics

### 3.1 Time to First Token (TTFT)

**Definition:** Time from submitting the query to receiving the first token

**Formula:**
```
TTFT = Request_queuing_time + Prefill_time + Network_latency
```

**Units:** Seconds (s) or Milliseconds (ms)

**Metric Names:**
- vLLM: `vllm:time_to_first_token_seconds` (Histogram)
- FakeAI: `fakeai_ttft_seconds` (Summary with quantiles)

**Key Characteristics:**
- Longer prompts increase TTFT
- Primarily compute-bound operation
- Critical for interactive applications and user experience
- Dynamo achieves 3x improvement through KV-aware routing

**Collection Method:**
```python
ttft = first_token_timestamp - request_submitted_timestamp
```

### 3.2 Time Per Output Token (TPOT) / Inter-Token Latency (ITL)

**Definition:** Average time between consecutive token generations

**Formula:**
```
TPOT = (e2e_latency - TTFT) / (Total_output_tokens - 1)
```

**Units:** Seconds per token (s/tok) or Milliseconds per token (ms/tok)

**Metric Names:**
- vLLM: `vllm:time_per_output_token_seconds` (Histogram)
- NVIDIA NIM: Also called Inter-Token Latency (ITL)

**Key Characteristics:**
- Memory-bound operation (not compute-bound)
- Determines how "fast" the model feels to users
- Lower TPOT = higher tokens per second per user
- Example: 100 ms/tok = 10 tok/s = ~450 words/minute

**Collection Method:**
```python
# For each token after the first
itl = current_token_timestamp - previous_token_timestamp
tpot = sum(all_itl) / (num_tokens - 1)
```

### 3.3 End-to-End Request Latency

**Definition:** Total time from query submission to full response completion

**Formula:**
```
e2e_latency = TTFT + Generation_time
e2e_latency = TTFT + (TPOT × num_output_tokens)
```

**Units:** Seconds (s)

**Metric Names:**
- vLLM: `vllm:e2e_request_latency_seconds` (Histogram)
- FakeAI: `fakeai_latency_seconds` (Summary with quantiles)

**Key Characteristics:**
- Includes all phases: queuing, prefill, decode, network
- Most comprehensive latency metric
- Used for SLA monitoring

**Percentiles Tracked:**
- P50 (median)
- P90
- P99
- Average
- Min/Max

### 3.4 Request Queue Time

**Definition:** Time spent waiting to be scheduled before processing begins

**Metric Name:**
- vLLM: `vllm:request_queue_time_seconds` (Histogram)

**Key Characteristics:**
- Indicates system load and queuing pressure
- High queue time suggests insufficient capacity
- Used for autoscaling decisions

### 3.5 Request Success Rate

**Metric Name:**
- vLLM: `vllm:request_success_total` (Counter)

**Labels:**
- `finished_reason`: "stop" (EOS token) or "length" (max tokens reached)
- `model_name`: Name of the model served

**Example:**
```
vllm:request_success_total{finished_reason="stop",model_name="meta-llama/Llama-3.1-8B-Instruct"} 1.0
vllm:request_success_total{finished_reason="length",model_name="meta-llama/Llama-3.1-8B-Instruct"} 131.0
```

---

## 4. Prefill Metrics

### 4.1 Prefill Phase Definition

The prefill phase processes all input tokens in parallel to:
- Compute the KV cache for all prompt tokens
- Generate the first output token
- Highly parallelized, compute-bound operation

### 4.2 Prefill Time

**Metric Name:**
- vLLM: `vllm:request_prefill_time_seconds` (Histogram)

**Key Characteristics:**
- Measures time spent in prefill phase
- Directly impacts TTFT
- Compute-bound workload
- Benefits from high GPU compute utilization

### 4.3 Prefill Batch Size

**Definition:** Number of prefill requests batched together

**Configuration Parameter:**
- vLLM: `max_num_batched_tokens` (default: 2048)

**Key Characteristics:**
- Higher batch size → better TTFT (more prefills in batch)
- Lower batch size → better ITL (fewer interruptions to decode)
- Tradeoff between throughput and latency

**During Warmup:**
- System determines `MAX_BATCH_PREFILL_TOKENS` (max tokens per forward pass)
- System determines `MAX_BATCH_TOTAL_TOKENS` (max concurrent tokens)

### 4.4 Prompt Tokens Processed

**Metric Names:**
- vLLM: `vllm:prompt_tokens_total` (Counter) - Cumulative
- vLLM: `vllm:request_prompt_tokens` (Histogram) - Per request

**Units:** Token count

**Key Characteristics:**
- Tracks total prefill workload
- Used for capacity planning
- Affects prefill cost in routing decisions

### 4.5 Chunked Prefill Metrics

**Definition:** Large prefills chunked into smaller pieces and batched with decode requests

**Benefits:**
- Reduces head-of-line blocking
- Improves ITL by avoiding long decode pauses
- Better resource utilization

**Key Metrics:**
- Chunk size (configurable)
- Number of chunks per prefill
- Impact on TTFT vs ITL tradeoff

---

## 5. Decode Metrics

### 5.1 Decode Phase Definition

The decode phase generates output tokens autoregressively:
- One token at a time per sequence
- Memory-bound operation (not compute-bound)
- Underutilizes GPU compute compared to prefill
- Latency dominated by memory bandwidth

### 5.2 Decode Time

**Metric Name:**
- vLLM: `vllm:request_decode_time_seconds` (Histogram)

**Key Characteristics:**
- Measures time spent in decode phase
- Memory-bound, not compute-bound
- Affects ITL and overall throughput

### 5.3 Generation Tokens Produced

**Metric Names:**
- vLLM: `vllm:generation_tokens_total` (Counter) - Cumulative
- vLLM: `vllm:request_generation_tokens` (Histogram) - Per request

**Units:** Token count

**Key Characteristics:**
- Tracks total decode workload
- Used for throughput calculations
- Affects decode cost in routing decisions

### 5.4 Decode Batch Size

**Definition:** Number of sequences being decoded simultaneously

**Configuration Parameter:**
- vLLM: `max_num_seqs` - Maximum concurrent sequences

**Key Characteristics:**
- Larger batch → better throughput
- Smaller batch → better latency per request
- Limited by KV cache memory availability

### 5.5 Tokens Per Second (TPS)

**Definition:** Number of tokens generated per second

**Two Calculation Methods:**

1. **Total System TPS:**
```
TPS_system = Total_output_tokens / (Last_response_timestamp - First_request_timestamp)
```

2. **Per-User TPS:**
```
TPS_per_user = Output_sequence_length / e2e_latency
```

**Metric Names:**
- vLLM: Custom calculation from `generation_tokens_total` and timestamps
- FakeAI: `fakeai_tokens_per_second` (Gauge)

**Key Characteristics:**
- Indicates system throughput capacity
- Affected by batch size and memory bandwidth
- Multiblock attention (H200): 3.5x improvement for long sequences

---

## 6. KV Cache Metrics

### 6.1 KV Cache Overview

Key-Value cache stores intermediate attention states to avoid recomputation:
- Grows linearly with batch size and sequence length
- Major memory bottleneck in LLM inference
- Critical for prefix caching and request routing

### 6.2 GPU Cache Usage

**Metric Name:**
- vLLM: `vllm:gpu_cache_usage_perc` (Gauge)

**Units:** Percentage (0-1, where 1 = 100%)

**Formula:**
```
gpu_cache_usage = allocated_blocks / total_blocks
```

**Key Characteristics:**
- Indicates GPU memory pressure
- Used for admission control decisions
- High usage may trigger swapping or preemption

**Memory Size Calculations:**
```
KV_cache_size_bytes = batch_size × sequence_length × 2 × num_layers × hidden_size × sizeof(FP16)
```

**Examples:**
- Llama 3 8B, 1 token: 131,072 bytes (0.1 MB)
- Llama 3 8B, 8192 tokens: 1.1 GB
- Llama 3 70B, 8191 tokens: 2.7 GB
- Llama 3 70B, 128k context (batch=1): 40 GB

### 6.3 CPU Cache Usage

**Metric Name:**
- vLLM: `vllm:cpu_cache_usage_perc` (Gauge)

**Units:** Percentage (0-1)

**Key Characteristics:**
- Tracks CPU-side KV cache for offloading
- Part of tiered memory strategy (GPU → CPU → SSD → Object Storage)
- Enables larger context windows beyond GPU memory

### 6.4 GPU Prefix Cache Hit Rate

**Metric Name:**
- vLLM: `vllm:gpu_prefix_cache_hit_rate` (Gauge)

**Units:** Percentage (0-1)

**Formula:**
```
hit_rate = cached_blocks / total_blocks
# OR
hit_rate = cached_tokens / total_tokens
```

**Example Calculation:**
- Prompt: 207 tokens
- Cached: 192 tokens
- Uncached: 15 tokens (not enough for full block with block_size=32)
- Hit rate: 192/207 = 92.75%

**Key Characteristics:**
- Highly application-specific
- Measures reuse of shared prefixes across requests
- Higher hit rate = better TTFT and throughput
- Prefix caching uses hash-based matching with LRU eviction

### 6.5 CPU Prefix Cache Hit Rate

**Metric Name:**
- vLLM: `vllm:cpu_prefix_cache_hit_rate` (Gauge)

**Units:** Percentage (0-1)

**Key Characteristics:**
- Tracks CPU-side prefix cache hits
- Part of tiered caching strategy
- Lower latency than recomputing, higher than GPU cache

### 6.6 KV Cache Memory Tiers

**Dynamo Strategy:**
1. **GPU Memory** (Tier 1) - Lowest latency, highest cost
2. **CPU Memory** (Tier 2) - Medium latency via NIXL transfers
3. **SSD Storage** (Tier 3) - Higher latency, larger capacity
4. **Object Storage** (Tier 4) - Highest latency, unlimited capacity

**Offloading Metrics:**
- Blocks offloaded per tier
- Blocks loaded back from tier
- Transfer latency per tier
- Hit rate per tier

**Benefits:**
- Preserves large prompt prefixes
- Avoids recomputation
- Improves TTFT and throughput
- Extends effective context window

### 6.7 KV Cache Quantization

**Memory Savings:**
- 2-3x reduction in KV cache size
- Frees up tens of gigabytes
- Minimal accuracy impact

**Potential Metrics:**
- Quantization level (INT8, INT4)
- Memory saved vs baseline
- Accuracy degradation (if any)

---

## 7. Routing Metrics

### 7.1 Cache Overlap Score

**Definition:** Similarity between incoming request and existing KV cache blocks across GPU fleet

**Configuration Parameter:**
- Dynamo: `--kv-overlap-score-weight` (default: varies)

**Key Characteristics:**
- Higher weight → better TTFT (prioritize cache reuse)
- Lower weight → better load balancing
- Weight of 0 → pure load balancing (ignore cache)

**Usage:**
```
cost = overlap_score_weight × prefill_blocks + decode_blocks
```

**Routing Decision:**
- Compute overlap score for each worker
- Combine with load metrics
- Route to worker with lowest cost (or sampled by temperature)

### 7.2 Router Temperature

**Configuration Parameter:**
- Dynamo: `--router-temperature` (default: 0)

**Key Characteristics:**
- Temperature 0: Deterministic routing to lowest-cost worker
- Higher temperature: Introduces randomness in routing
- Helps distribute load and avoid hotspots

### 7.3 Routing Cost Function

**Formula:**
```
cost = overlap_score_weight × prefill_cost + decode_load
```

**Where:**
- `prefill_cost` = Number of prefill blocks (influenced by cached blocks)
- `decode_load` = Estimated decode blocks based on active sequences

**Optimization Goal:**
- Maximize cache reuse (lower prefill cost)
- Balance load across workers (distribute decode load)
- Minimize overall latency (TTFT and ITL)

### 7.4 Active Blocks Tracking

**Definition:** Blocks currently being used for active generation requests

**Key Characteristics:**
- Ephemeral state (resets when router replica starts)
- Eventually consistent across router replicas
- Used for decode load estimation

**Metrics:**
- Active blocks per worker
- Total active blocks in cluster
- Block utilization distribution

### 7.5 Load Distribution Metrics

**Key Metrics:**
- Requests per worker
- Active sequences per worker
- Cache hit rate per worker
- Throughput per worker (tokens/sec)
- Latency per worker (TTFT, ITL)

**Goals:**
- Avoid hotspots (some workers overloaded, others idle)
- Maximize cluster-wide throughput
- Meet per-request latency SLOs

### 7.6 Inter-Router Communication Events

**Event Types:**

1. **AddRequest**
   - Tracks request assignment to worker
   - Updates worker load calculations

2. **MarkPrefillCompleted**
   - Updates worker load after prefill phase
   - Adjusts routing decisions

3. **Free**
   - Signals request completion
   - Releases worker resources

**Potential Metrics:**
- Event rate per type
- Processing latency per event
- Queue depth for events

---

## 8. Model-Specific Metrics

### 8.1 Requests Per Model

**Definition:** Number of requests served by each model

**Metric Structure:**
- Counter per model
- Rate per model (requests/second)

**Labels:**
- `model_name`: Identifier of the model

**Key Characteristics:**
- Tracks workload distribution across models
- Informs capacity planning
- Enables per-model billing/accounting

### 8.2 Tokens Per Model

**Definition:** Number of tokens processed (prompt + generation) per model

**Metrics:**
- Prompt tokens per model
- Generation tokens per model
- Total tokens per model

**Labels:**
- `model_name`: Identifier of the model

**Key Characteristics:**
- Tracks computational workload per model
- Basis for usage-based billing
- Identifies high-utilization models

### 8.3 Latency Per Model

**Metrics:**
- TTFT per model (with percentiles)
- TPOT per model (with percentiles)
- E2E latency per model (with percentiles)

**Labels:**
- `model_name`: Identifier of the model

**Key Characteristics:**
- Different models have different performance characteristics
- Larger models typically have higher latency
- Enables per-model SLO monitoring

### 8.4 Throughput Per Model

**Metrics:**
- Requests/second per model
- Tokens/second per model
- Batch size per model

**Key Characteristics:**
- Tracks model serving capacity
- Identifies bottlenecks
- Guides resource allocation

### 8.5 Model Load Metrics Endpoint

**Endpoint:** `{model_name}.backend.load_metrics`

**Example:** `llama3-1-8b.backend.load_metrics`

**Exposed Metrics:**
- GPU cache usage for this model
- Number of requests waiting for this model
- Active sequences for this model
- Prefix cache hit rate for this model

**Integration:**
- Added by KV metrics publisher in vLLM
- Used by Dynamo router for intelligent routing
- Enables per-model autoscaling

---

## 9. Worker Metrics

### 9.1 Active Requests

**Metric Name:**
- vLLM: `vllm:num_requests_running` (Gauge)

**Definition:** Number of requests currently running on GPU (in model execution batches)

**Key Characteristics:**
- Indicates current worker load
- Used for load balancing decisions
- May stay at 1 even with waiting requests (reported issue)

### 9.2 Waiting Requests

**Metric Name:**
- vLLM: `vllm:num_requests_waiting` (Gauge)

**Definition:** Number of requests waiting to be scheduled/processed

**Key Characteristics:**
- Indicates queuing pressure
- High values suggest capacity shortage
- Used for autoscaling triggers

### 9.3 Swapped Requests

**Metric Name:**
- vLLM: `vllm:num_requests_swapped` (Gauge)

**Definition:** Number of requests swapped to CPU due to GPU memory pressure

**Key Characteristics:**
- Indicates memory pressure
- Swapped requests have higher latency when resumed
- Suggests need for additional GPU capacity

### 9.4 Worker Throughput

**Metrics:**
- Tokens/second per worker
- Requests/second per worker
- Batch size per worker

**Key Characteristics:**
- Indicates worker efficiency
- Used for load balancing
- Identifies underperforming workers

### 9.5 Worker Utilization

**Metrics:**
- GPU compute utilization (%)
- GPU memory utilization (%)
- KV cache utilization (%)
- Decode blocks active vs capacity

**Key Characteristics:**
- Indicates resource efficiency
- High compute utilization in prefill (good)
- High memory bandwidth utilization in decode (expected)
- Low utilization suggests inefficient batching

**Dynamo GPU Planner:**
- Continuously monitors GPU capacity metrics
- Tracks average KV block utilization across decode GPUs
- Tracks volume of pending prefill requests in global queue
- Combines with SLOs (TTFT, ITL) for resource decisions

### 9.6 Preemptions

**Metric Name:**
- vLLM: `vllm:num_preemptions_total` (Counter)

**Definition:** Cumulative number of preemption requests

**Key Characteristics:**
- Indicates memory pressure events
- Preempted requests must be resumed later
- Increases latency variance
- Can be monitored via `disable_log_stats=False`

---

## 10. End-to-End Latency Breakdown

### 10.1 Latency Components

```
E2E_latency = Network_ingress + Queue_time + Prefill_time + Decode_time + Network_egress
```

**Detailed Breakdown:**

1. **Network Ingress** (Client → Server)
   - Request serialization
   - Network transmission
   - Request deserialization

2. **Queue Time** (Waiting for scheduling)
   - Admission control delay
   - Scheduler queue depth
   - Resource availability wait

3. **Prefill Time** (Input processing)
   - Token encoding
   - Parallel attention computation
   - KV cache population
   - First token generation

4. **Decode Time** (Output generation)
   - Autoregressive token generation
   - Repeated attention + MLP
   - KV cache update per token
   - Token count × TPOT

5. **Network Egress** (Server → Client)
   - Response serialization
   - Network transmission
   - Response deserialization

### 10.2 Prefill vs Decode Characteristics

| Aspect | Prefill | Decode |
|--------|---------|--------|
| Computation | Parallel (matrix-matrix) | Sequential (matrix-vector) |
| Bottleneck | Compute-bound | Memory-bound |
| GPU Utilization | High | Low (memory bandwidth limited) |
| Batching Benefit | Very high | Medium |
| Cache Reuse | Critical (prefix caching) | Less critical |
| Latency Impact | TTFT | ITL, Total latency |

### 10.3 Scheduling Strategies Impact

**Static Batching:**
- Fixed batch size
- All requests wait for batch to fill
- Poor GPU utilization when batch incomplete

**Continuous Batching (Orca):**
- Iteration-level scheduling
- New requests replace completed sequences
- Much better GPU utilization
- 23x throughput improvement (benchmark)

**Hybrid Batching:**
- Mix prefill and decode in same batch
- Requires careful balancing
- Prefill can pause ongoing decodes → higher TBT
- Decode interrupted by large prefills → generation stalls

**Chunked Prefill:**
- Split large prefills into smaller chunks
- Batch chunks with decode requests
- Reduces head-of-line blocking
- Better ITL, slightly higher TTFT

**Prefill-Decode Disaggregation (Dynamo):**
- Separate GPUs for prefill and decode
- Specialized resource allocation
- Better resource utilization per phase
- Requires KV cache transfer between GPU sets

### 10.4 Time-Series Latency Tracking

**Percentile Tracking:**
- P50 (median): Typical request experience
- P90: 90% of requests faster than this
- P99: 99% of requests faster than this (tail latency)
- P99.9: Extreme tail latency

**Window-Based Calculation:**
- Sliding window (e.g., last 5 minutes)
- Real-time percentile calculation
- Histogram buckets for efficiency

**Visualization:**
- Latency over time (line chart)
- Latency distribution (histogram)
- Heatmap (time × latency)

---

## 11. vLLM Metrics (Dynamo Backend)

### 11.1 vLLM as Dynamo Backend

NVIDIA Dynamo uses vLLM as the primary backend inference engine:
- Patched vLLM with KV cache event reporting
- Exposes `load_metrics` endpoint for router integration
- Native KV cache tracking for routing decisions

### 11.2 Complete vLLM Metrics List

#### System State Metrics (Gauge)

1. **Scheduler State**
   - `vllm:num_requests_running` - Requests in GPU execution batches
   - `vllm:num_requests_waiting` - Requests waiting for scheduling
   - `vllm:num_requests_swapped` - Requests swapped to CPU

2. **Cache Usage**
   - `vllm:gpu_cache_usage_perc` - GPU KV-cache usage percentage
   - `vllm:cpu_cache_usage_perc` - CPU KV-cache usage percentage

3. **Prefix Caching**
   - `vllm:gpu_prefix_cache_hit_rate` - GPU prefix cache block hit rate
   - `vllm:cpu_prefix_cache_hit_rate` - CPU prefix cache block hit rate

4. **LoRA Adapters**
   - `vllm:lora_requests_info` - Current LoRA adapter request information

#### Request Timing Metrics (Histogram)

1. **Latency Breakdown**
   - `vllm:time_to_first_token_seconds` - Time until first token generation
   - `vllm:time_per_output_token_seconds` - Latency between token generations
   - `vllm:e2e_request_latency_seconds` - Total request processing time
   - `vllm:request_queue_time_seconds` - Time waiting to be scheduled
   - `vllm:request_prefill_time_seconds` - Time in prefill phase
   - `vllm:request_decode_time_seconds` - Time in decode phase

2. **Token Counts**
   - `vllm:request_prompt_tokens` - Number of input tokens per request
   - `vllm:request_generation_tokens` - Number of generated tokens per request

#### Cumulative Metrics (Counter)

1. **Iteration Totals**
   - `vllm:num_preemptions_total` - Cumulative preemptions from engine
   - `vllm:prompt_tokens_total` - Total prefill tokens processed
   - `vllm:generation_tokens_total` - Total generation tokens processed

2. **Request Outcomes**
   - `vllm:request_success_total{finished_reason="stop"}` - Requests completed with EOS
   - `vllm:request_success_total{finished_reason="length"}` - Requests hitting max length

#### Speculative Decoding Metrics (if enabled)

1. **Draft Model Performance** (Gauge)
   - `vllm:spec_decode_draft_acceptance_rate` - Speculative token acceptance rate
   - `vllm:spec_decode_efficiency` - Speculative decoding system efficiency

2. **Draft Model Counts** (Counter)
   - `vllm:spec_decode_num_accepted_tokens_total` - Total accepted draft tokens
   - `vllm:spec_decode_num_draft_tokens_total` - Total draft tokens proposed
   - `vllm:spec_decode_num_emitted_tokens_total` - Total tokens emitted to client

### 11.3 Metric Labels

**Common Labels:**
- `model_name`: Name of the model served by that instance
  - Example: `"meta-llama/Llama-3.1-8B-Instruct"`
- `finished_reason`: Reason for request completion
  - Values: `"stop"` (EOS token), `"length"` (max tokens reached)

**Label Usage Example:**
```
vllm:request_success_total{finished_reason="stop",model_name="meta-llama/Llama-3.1-8B-Instruct"} 1.0
vllm:request_success_total{finished_reason="length",model_name="meta-llama/Llama-3.1-8B-Instruct"} 131.0
```

### 11.4 Metrics Endpoint

**Path:** `/metrics`

**Format:** OpenMetrics (Prometheus-compatible)

**Access:** Exposed on vLLM OpenAI-compatible API server port

**Integration:**
- Scraped by Prometheus
- Visualized in Grafana
- Used by Dynamo router for routing decisions

---

## 12. Prometheus Metrics Format

### 12.1 Metric Types

1. **Counter** - Monotonically increasing value
   - Example: `vllm:prompt_tokens_total`
   - Resets to 0 on server restart

2. **Gauge** - Value that can go up or down
   - Example: `vllm:num_requests_running`
   - Represents current state

3. **Histogram** - Distribution of values with buckets
   - Example: `vllm:time_to_first_token_seconds`
   - Includes `_sum`, `_count`, and `_bucket` metrics

4. **Summary** - Similar to histogram but with quantiles
   - Example: `fakeai_ttft_seconds{quantile="0.99"}`
   - Pre-calculated percentiles

### 12.2 Metric Naming Convention

**Pattern:** `namespace:metric_name_unit`

**Examples:**
- `vllm:time_to_first_token_seconds`
- `fakeai_requests_per_second`
- `dynamo:kv_cache_hit_rate`

**Guidelines:**
- Use underscores, not hyphens
- Include unit in name (seconds, bytes, ratio)
- Namespace prefix for separation

### 12.3 Help and Type Annotations

**Format:**
```
# HELP metric_name Description of the metric
# TYPE metric_name metric_type
metric_name{label1="value1",label2="value2"} 42.0
```

**Example:**
```
# HELP vllm:time_to_first_token_seconds Time until first token generation
# TYPE vllm:time_to_first_token_seconds histogram
vllm:time_to_first_token_seconds_bucket{le="0.1",model_name="openai/gpt-oss-120b"} 10
vllm:time_to_first_token_seconds_bucket{le="0.5",model_name="openai/gpt-oss-120b"} 45
vllm:time_to_first_token_seconds_bucket{le="1.0",model_name="openai/gpt-oss-120b"} 98
vllm:time_to_first_token_seconds_bucket{le="+Inf",model_name="openai/gpt-oss-120b"} 100
vllm:time_to_first_token_seconds_sum{model_name="openai/gpt-oss-120b"} 35.7
vllm:time_to_first_token_seconds_count{model_name="openai/gpt-oss-120b"} 100
```

### 12.4 Histogram Buckets

**Common Bucket Boundaries:**

**Latency Metrics (seconds):**
```
[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, +Inf]
```

**Token Counts:**
```
[1, 10, 50, 100, 250, 500, 1000, 2000, 4000, 8000, 16000, 32000, +Inf]
```

**Rate Metrics (requests/sec):**
```
[0.1, 0.5, 1, 2, 5, 10, 25, 50, 100, 250, 500, 1000, +Inf]
```

### 12.5 Quantile Selection

**Standard Quantiles:**
- 0.5 (P50, median)
- 0.9 (P90)
- 0.95 (P95)
- 0.99 (P99)
- 0.999 (P99.9, extreme tail)

**Use Cases:**
- P50: Typical user experience
- P90: Most users experience this or better
- P99: SLO boundary (99% of requests meet this)
- P99.9: Worst-case outliers

---

## 13. Collection Methods

### 13.1 Dynamo Metrics Collection on Kubernetes

**Architecture:**
- kube-prometheus-stack for Kubernetes monitoring
- PodMonitors for custom resource-based scraping
- Prometheus for metrics storage
- Grafana for visualization

**Setup:**
1. Install kube-prometheus-stack
2. Deploy Dynamo with metrics labels
3. Create PodMonitor resources
4. Configure Prometheus scrape configs
5. Import Grafana dashboards

**PodMonitor Configuration:**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: dynamo-metrics
spec:
  selector:
    matchLabels:
      nvidia.com/metrics-enabled: "true"
  podMetricsEndpoints:
  - port: metrics
    path: /metrics
    interval: 30s
```

### 13.2 Metrics Endpoints

**Frontend Component:**
- Exposes metrics on HTTP port
- Endpoint: `/metrics`
- Format: OpenMetrics

**Worker Component:**
- Exposes metrics on system port
- Endpoint: `/metrics`
- Format: OpenMetrics

**Load Metrics:**
- Per-backend endpoint: `{model}.backend.load_metrics`
- Provides worker-specific load information
- Used by router for intelligent routing

### 13.3 Scraping Configuration

**Prometheus Scrape Config:**
```yaml
scrape_configs:
  - job_name: 'dynamo-frontend'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_nvidia_com_dynamo_component_type]
        action: keep
        regex: frontend
      - source_labels: [__meta_kubernetes_pod_label_nvidia_com_metrics_enabled]
        action: keep
        regex: true
    metrics_path: /metrics
    scrape_interval: 15s

  - job_name: 'dynamo-worker'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_nvidia_com_dynamo_component_type]
        action: keep
        regex: worker
      - source_labels: [__meta_kubernetes_pod_label_nvidia_com_metrics_enabled]
        action: keep
        regex: true
    metrics_path: /metrics
    scrape_interval: 15s
```

### 13.4 DCGM Integration

**Data Center GPU Manager (DCGM):**
- NVIDIA's monitoring tool for GPU fleets
- Exposes GPU-level metrics via dcgm-exporter
- Integrates with Prometheus

**Key DCGM Metrics:**
- GPU utilization (%)
- GPU memory usage (bytes)
- GPU temperature (°C)
- Power consumption (watts)
- SM clock frequency (MHz)
- Memory clock frequency (MHz)
- PCIe throughput (bytes/sec)

**Integration with Dynamo:**
- DCGM tracks GPU hardware metrics
- Dynamo tracks inference workload metrics
- Combined view: hardware + workload = complete observability

### 13.5 Real-Time Metrics (Dynamo 0.4+)

**Features:**
- Real-time observability for engineering teams
- Monitor system health in production
- Diagnose performance bottlenecks
- Meet strict SLOs

**Metrics Latency:**
- Scrape interval: 15-30 seconds (configurable)
- Aggregation window: 5 seconds (typical)
- Dashboard refresh: 5-60 seconds

**Alerting:**
- Prometheus AlertManager integration
- Alert on SLO violations
- Alert on error rate spikes
- Alert on capacity issues

---

## 14. Implementation Recommendations for FakeAI

### 14.1 Priority 1: Core Latency Metrics

**Implement immediately to match industry standards:**

1. **Time to First Token (TTFT)**
   ```python
   # Already partially implemented in StreamingMetrics.calculate_ttft()
   # Enhance to support non-streaming requests
   def track_ttft(self, request_id: str, ttft: float):
       self._ttft_histogram.observe(ttft)
   ```

2. **Time Per Output Token (TPOT/ITL)**
   ```python
   # New metric needed
   def track_tpot(self, request_id: str, token_latencies: list[float]):
       avg_tpot = sum(token_latencies) / len(token_latencies)
       self._tpot_histogram.observe(avg_tpot)
   ```

3. **End-to-End Latency**
   ```python
   # Already tracked as response latency
   # Add histogram with proper buckets
   LATENCY_BUCKETS = [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
   ```

### 14.2 Priority 2: Request Tracking

**Enhance existing metrics:**

1. **Queue Metrics**
   ```python
   # New gauge metrics
   self.num_requests_running = Gauge('fakeai_num_requests_running', 'Active requests')
   self.num_requests_waiting = Gauge('fakeai_num_requests_waiting', 'Queued requests')
   ```

2. **Token Counts**
   ```python
   # Already tracked, add histogram
   self.prompt_tokens = Histogram('fakeai_prompt_tokens', 'Input token count', buckets=[1, 10, 50, 100, 250, 500, 1000, 2000, 4000, 8000, 16000])
   self.generation_tokens = Histogram('fakeai_generation_tokens', 'Output token count', buckets=[1, 10, 50, 100, 250, 500, 1000, 2000, 4000])
   ```

3. **Request Success with Labels**
   ```python
   # Add finished_reason label
   self.request_success = Counter('fakeai_request_success_total', 'Successful requests', labelnames=['endpoint', 'finished_reason', 'model_name'])
   ```

### 14.3 Priority 3: KV Cache Simulation

**Simulate KV cache behavior for realism:**

1. **Cache Usage Gauge**
   ```python
   # Simulated KV cache usage
   self.gpu_cache_usage = Gauge('fakeai_gpu_cache_usage_perc', 'GPU KV cache usage', labelnames=['model_name'])

   def simulate_cache_usage(self, num_active_requests, avg_sequence_length):
       # Estimate cache usage based on active load
       estimated_usage = min(1.0, (num_active_requests * avg_sequence_length) / MAX_CACHE_BLOCKS)
       self.gpu_cache_usage.labels(model_name=model).set(estimated_usage)
   ```

2. **Prefix Cache Hit Rate**
   ```python
   # Simulated prefix caching
   self.prefix_cache_hit_rate = Gauge('fakeai_prefix_cache_hit_rate', 'Prefix cache hit rate', labelnames=['model_name'])

   def simulate_prefix_hit_rate(self, requests):
       # Simulate prefix matching (hash-based)
       # Higher hit rate for requests with similar prefixes
       hit_rate = calculate_simulated_hit_rate(requests)
       self.prefix_cache_hit_rate.labels(model_name=model).set(hit_rate)
   ```

### 14.4 Priority 4: Model-Specific Metrics

**Add model dimension to metrics:**

1. **Per-Model Counters**
   ```python
   # Add model_name label to existing metrics
   self.requests_per_model = Counter('fakeai_requests_total', 'Requests per model', labelnames=['model_name'])
   self.tokens_per_model = Counter('fakeai_tokens_total', 'Tokens per model', labelnames=['model_name', 'token_type'])
   ```

2. **Per-Model Latency**
   ```python
   # Model-specific latency tracking
   self.latency_per_model = Histogram('fakeai_latency_seconds', 'Latency per model', labelnames=['model_name'], buckets=LATENCY_BUCKETS)
   ```

### 14.5 Priority 5: Histogram Implementation

**Replace summary metrics with histograms for Prometheus compatibility:**

```python
from prometheus_client import Histogram, Counter, Gauge

class PrometheusMetrics:
    """Prometheus-compatible metrics using prometheus_client library."""

    def __init__(self):
        # Latency histograms
        self.ttft = Histogram(
            'fakeai_time_to_first_token_seconds',
            'Time to first token',
            labelnames=['model_name'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
        )

        self.tpot = Histogram(
            'fakeai_time_per_output_token_seconds',
            'Time per output token',
            labelnames=['model_name'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5]
        )

        self.e2e_latency = Histogram(
            'fakeai_e2e_request_latency_seconds',
            'End-to-end request latency',
            labelnames=['model_name'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
        )

        # Token histograms
        self.prompt_tokens = Histogram(
            'fakeai_request_prompt_tokens',
            'Prompt token count',
            labelnames=['model_name'],
            buckets=[1, 10, 50, 100, 250, 500, 1000, 2000, 4000, 8000, 16000, 32000]
        )

        self.generation_tokens = Histogram(
            'fakeai_request_generation_tokens',
            'Generation token count',
            labelnames=['model_name'],
            buckets=[1, 10, 50, 100, 250, 500, 1000, 2000, 4000]
        )

        # Counters
        self.requests_total = Counter(
            'fakeai_requests_total',
            'Total requests',
            labelnames=['model_name']
        )

        self.request_success = Counter(
            'fakeai_request_success_total',
            'Successful requests',
            labelnames=['model_name', 'finished_reason']
        )

        self.tokens_total = Counter(
            'fakeai_tokens_total',
            'Total tokens processed',
            labelnames=['model_name', 'token_type']
        )

        # Gauges
        self.num_requests_running = Gauge(
            'fakeai_num_requests_running',
            'Currently running requests',
            labelnames=['model_name']
        )

        self.num_requests_waiting = Gauge(
            'fakeai_num_requests_waiting',
            'Waiting requests',
            labelnames=['model_name']
        )

        self.gpu_cache_usage = Gauge(
            'fakeai_gpu_cache_usage_perc',
            'GPU KV cache usage percentage',
            labelnames=['model_name']
        )

        self.prefix_cache_hit_rate = Gauge(
            'fakeai_prefix_cache_hit_rate',
            'Prefix cache hit rate',
            labelnames=['model_name']
        )
```

### 14.6 Integration with Existing MetricsTracker

**Extend current implementation:**

```python
class MetricsTracker:
    """Enhanced metrics tracker with Prometheus support."""

    def __init__(self):
        # Existing initialization...

        # Add Prometheus metrics
        self.prometheus = PrometheusMetrics()

        # Simulated state for KV cache
        self.simulated_cache_state = {}
        self.request_prefixes = {}  # For prefix matching simulation

    def track_chat_completion(self, request, response, latency):
        """Track comprehensive metrics for chat completion."""
        model = request.model

        # Existing tracking...
        self.track_response(endpoint, latency)

        # New Prometheus tracking
        self.prometheus.requests_total.labels(model_name=model).inc()
        self.prometheus.e2e_latency.labels(model_name=model).observe(latency)

        # Token tracking
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens

        self.prometheus.prompt_tokens.labels(model_name=model).observe(prompt_tokens)
        self.prometheus.generation_tokens.labels(model_name=model).observe(completion_tokens)
        self.prometheus.tokens_total.labels(model_name=model, token_type='prompt').inc(prompt_tokens)
        self.prometheus.tokens_total.labels(model_name=model, token_type='completion').inc(completion_tokens)

        # Success tracking
        finish_reason = response.choices[0].finish_reason
        self.prometheus.request_success.labels(model_name=model, finished_reason=finish_reason).inc()

        # Simulate KV cache usage
        self._update_simulated_cache(model, prompt_tokens, completion_tokens)

    def track_streaming_completion(self, request, stream_id, first_token_time, completion_time, token_count):
        """Track streaming-specific metrics."""
        model = request.model

        # TTFT
        ttft = first_token_time - request_start_time
        self.prometheus.ttft.labels(model_name=model).observe(ttft)

        # TPOT
        total_generation_time = completion_time - first_token_time
        if token_count > 1:
            tpot = total_generation_time / (token_count - 1)
            self.prometheus.tpot.labels(model_name=model).observe(tpot)

        # E2E latency
        e2e_latency = completion_time - request_start_time
        self.prometheus.e2e_latency.labels(model_name=model).observe(e2e_latency)

    def _update_simulated_cache(self, model, prompt_tokens, completion_tokens):
        """Update simulated KV cache metrics."""
        # Simple simulation: track active tokens across all requests
        if model not in self.simulated_cache_state:
            self.simulated_cache_state[model] = {
                'active_tokens': 0,
                'max_capacity': 32000,  # Simulated cache capacity
                'active_requests': 0,
            }

        state = self.simulated_cache_state[model]

        # Add tokens from new request
        state['active_tokens'] += (prompt_tokens + completion_tokens)
        state['active_requests'] += 1

        # Simulate cache eviction (LRU)
        if state['active_tokens'] > state['max_capacity']:
            state['active_tokens'] = state['max_capacity']

        # Update gauge
        usage_pct = state['active_tokens'] / state['max_capacity']
        self.prometheus.gpu_cache_usage.labels(model_name=model).set(usage_pct)

        # Simulate prefix cache hit rate
        hit_rate = self._calculate_simulated_hit_rate(model, prompt_tokens)
        self.prometheus.prefix_cache_hit_rate.labels(model_name=model).set(hit_rate)

    def _calculate_simulated_hit_rate(self, model, prompt_tokens):
        """Simulate prefix cache hit rate based on request patterns."""
        # Simple simulation: higher hit rate for shorter prompts (more common prefixes)
        # In reality, would use hash-based prefix matching

        # Baseline hit rate increases with system "warmth"
        if model not in self.simulated_cache_state:
            return 0.0

        active_requests = self.simulated_cache_state[model]['active_requests']

        # More active requests → higher hit rate (more cached prefixes)
        base_hit_rate = min(0.8, active_requests * 0.05)

        # Shorter prompts → higher hit rate (more overlap)
        prompt_factor = max(0.2, 1.0 - (prompt_tokens / 2000))

        hit_rate = base_hit_rate * prompt_factor
        return min(1.0, hit_rate)
```

### 14.7 Gradana Dashboard Templates

**Recommended dashboard panels:**

1. **Request Overview**
   - Requests/second per model
   - Success rate per model
   - Error rate per model

2. **Latency Dashboard**
   - TTFT heatmap (time × latency)
   - TPOT distribution (histogram)
   - E2E latency percentiles (P50, P90, P99)
   - Latency by model (comparison)

3. **Throughput Dashboard**
   - Tokens/second per model
   - Batch size distribution
   - Active requests gauge
   - Waiting requests gauge

4. **KV Cache Dashboard**
   - Cache usage percentage
   - Prefix cache hit rate
   - Cache operations (hits, misses, evictions)

5. **System Health**
   - Error rate percentage
   - Request queue depth
   - Average latency
   - Active streams

### 14.8 Configuration Options

**Add to AppConfig:**

```python
class AppConfig(BaseSettings):
    # ... existing config ...

    # Metrics configuration
    enable_prometheus_metrics: bool = True
    metrics_port: int = 9090
    metrics_path: str = "/metrics"

    # KV cache simulation
    simulate_kv_cache: bool = True
    simulated_cache_capacity: int = 32000  # tokens
    simulate_prefix_caching: bool = True

    # Histogram bucket configuration
    latency_buckets: list[float] = field(default_factory=lambda: [
        0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0
    ])
    token_buckets: list[int] = field(default_factory=lambda: [
        1, 10, 50, 100, 250, 500, 1000, 2000, 4000, 8000, 16000, 32000
    ])
```

### 14.9 Testing Strategy

**Add tests for new metrics:**

```python
def test_ttft_metric():
    """Test TTFT metric tracking."""
    tracker = MetricsTracker()

    # Simulate request
    request = ChatCompletionRequest(model="openai/gpt-oss-120b", messages=[...])

    # Track TTFT
    ttft = 0.15  # 150ms
    tracker.prometheus.ttft.labels(model_name="openai/gpt-oss-120b").observe(ttft)

    # Verify metric recorded
    assert tracker.prometheus.ttft._child_samples()

def test_cache_simulation():
    """Test KV cache simulation."""
    tracker = MetricsTracker()

    # Simulate multiple requests
    for i in range(10):
        tracker._update_simulated_cache("openai/gpt-oss-120b", 100, 50)

    # Verify cache usage increases
    state = tracker.simulated_cache_state["openai/gpt-oss-120b"]
    assert state['active_tokens'] > 0
    assert state['active_requests'] == 10

    # Verify hit rate improves
    hit_rate = tracker._calculate_simulated_hit_rate("openai/gpt-oss-120b", 100)
    assert hit_rate > 0

def test_prometheus_export():
    """Test Prometheus metrics export."""
    tracker = MetricsTracker()

    # Track some metrics
    tracker.track_chat_completion(request, response, 0.5)

    # Export Prometheus format
    metrics_text = generate_latest(REGISTRY)

    # Verify format
    assert "fakeai_time_to_first_token_seconds" in metrics_text
    assert "fakeai_gpu_cache_usage_perc" in metrics_text
    assert 'model_name="openai/gpt-oss-120b"' in metrics_text
```

### 14.10 Migration Path

**Phase 1: Add Prometheus metrics alongside existing metrics**
- Both systems run in parallel
- No breaking changes to existing API
- Validate Prometheus metrics match existing metrics

**Phase 2: Enhance metrics with labels and histograms**
- Add model_name labels
- Add finished_reason labels
- Implement histogram buckets

**Phase 3: Add KV cache simulation**
- Implement simulated cache state tracking
- Add prefix matching simulation
- Expose cache metrics

**Phase 4: Deprecate old metrics format (optional)**
- Keep `/metrics` endpoint (Prometheus)
- Optionally remove custom JSON format (or keep both)

---

## 15. References

### Official Documentation

1. **NVIDIA Dynamo Documentation**
   - Main docs: https://docs.nvidia.com/dynamo/
   - KV Cache Routing: https://docs.nvidia.com/dynamo/latest/architecture/kv_cache_routing.html
   - Metrics Collection: https://docs.nvidia.com/dynamo/latest/guides/dynamo_deploy/k8s_metrics.html

2. **vLLM Documentation**
   - Metrics Design: https://docs.vllm.ai/en/latest/design/metrics.html
   - Production Metrics: https://docs.vllm.ai/en/v0.6.1/serving/metrics.html
   - Performance Tuning: https://docs.vllm.ai/en/latest/configuration/optimization.html

3. **NVIDIA Blog Posts**
   - Dynamo Announcement: https://developer.nvidia.com/blog/introducing-nvidia-dynamo-a-low-latency-distributed-inference-framework-for-scaling-reasoning-ai-models/
   - KV Cache Bottlenecks: https://developer.nvidia.com/blog/how-to-reduce-kv-cache-bottlenecks-with-nvidia-dynamo/
   - Dynamo 0.4 Release: https://developer.nvidia.com/blog/dynamo-0-4-delivers-4x-faster-performance-slo-based-autoscaling-and-real-time-observability/

4. **NVIDIA NIM Benchmarking**
   - Metrics Guide: https://docs.nvidia.com/nim/benchmarking/llm/latest/metrics.html

### Research Papers & Technical Blogs

5. **LLM Inference Optimization**
   - Mastering LLM Techniques: https://developer.nvidia.com/blog/mastering-llm-techniques-inference-optimization/
   - LLM Benchmarking: https://developer.nvidia.com/blog/llm-benchmarking-fundamental-concepts/

6. **Batching Strategies**
   - Continuous Batching (Anyscale): https://www.anyscale.com/blog/continuous-batching-llm-inference
   - Prefill-Decode Disaggregation: https://hao-ai-lab.github.io/blogs/distserve/
   - Chunked Prefill: https://developer.nvidia.com/blog/streamlining-ai-inference-performance-and-deployment-with-nvidia-tensorrt-llm-chunked-prefill/

7. **KV Cache Optimization**
   - KV Caching Deep Dive: https://medium.com/@plienhar/llm-inference-series-4-kv-caching-a-deeper-look-4ba9a77746c8
   - TensorRT-LLM KV Cache Reuse: https://developer.nvidia.com/blog/introducing-new-kv-cache-reuse-optimizations-in-nvidia-tensorrt-llm/
   - CPU-GPU Memory Sharing: https://developer.nvidia.com/blog/accelerate-large-scale-llm-inference-and-kv-cache-offload-with-cpu-gpu-memory-sharing/

8. **Load Balancing & Routing**
   - KV Cache Utilization-Aware Load Balancing: https://bentoml.com/llm/inference-optimization/kv-cache-utilization-aware-load-balancing
   - Consistent Hashing with Bounded Loads: https://www.kubeai.org/blog/2025/02/26/llm-load-balancing-at-scale-chwbl/
   - Inference Gateway: https://medium.com/google-cloud/inference-gateway-intelligent-load-balancing-for-llms-on-gke-6a7c1f46a59c

9. **Performance Engineering**
   - LLM Inference Performance (Databricks): https://www.databricks.com/blog/llm-inference-performance-engineering-best-practices
   - BentoML LLM Handbook: https://bentoml.com/llm/inference-optimization/llm-inference-metrics

### GitHub Repositories

10. **Open Source Projects**
    - Dynamo: https://github.com/ai-dynamo/dynamo
    - vLLM: https://github.com/vllm-project/vllm
    - Prometheus Client: https://github.com/prometheus/client_python

### Related FakeAI Documentation

11. **FakeAI Existing Docs**
    - Current Metrics: `/home/anthony/projects/fakeai/fakeai/metrics.py`
    - Streaming Metrics: `/home/anthony/projects/fakeai/examples/STREAMING_METRICS.md`
    - Claude Knowledge Base: `/home/anthony/projects/fakeai/CLAUDE.md`
    - Monitoring System: `/home/anthony/projects/fakeai/MONITORING_SYSTEM.md`

---

## Appendix A: Metric Quick Reference

### Latency Metrics
| Metric | Unit | Type | Description |
|--------|------|------|-------------|
| TTFT | seconds | Histogram | Time to first token |
| TPOT/ITL | seconds | Histogram | Time per output token |
| E2E Latency | seconds | Histogram | End-to-end request latency |
| Queue Time | seconds | Histogram | Time waiting in queue |
| Prefill Time | seconds | Histogram | Time in prefill phase |
| Decode Time | seconds | Histogram | Time in decode phase |

### Throughput Metrics
| Metric | Unit | Type | Description |
|--------|------|------|-------------|
| Requests/sec | req/s | Gauge | Request rate |
| Tokens/sec | tok/s | Gauge | Token generation rate |
| Prompt Tokens | count | Counter | Total prompt tokens |
| Generation Tokens | count | Counter | Total generated tokens |

### Resource Metrics
| Metric | Unit | Type | Description |
|--------|------|------|-------------|
| Num Running | count | Gauge | Active requests |
| Num Waiting | count | Gauge | Queued requests |
| Num Swapped | count | Gauge | Swapped requests |
| GPU Cache Usage | % | Gauge | KV cache utilization |
| CPU Cache Usage | % | Gauge | CPU cache utilization |
| Prefix Hit Rate | % | Gauge | Prefix cache hit rate |

### Success Metrics
| Metric | Unit | Type | Description |
|--------|------|------|-------------|
| Request Success | count | Counter | Successful requests |
| Preemptions | count | Counter | Cache preemptions |

---

## Appendix B: Comparison Table

### FakeAI Current vs Recommended Metrics

| Category | Current FakeAI | Recommended Addition |
|----------|---------------|---------------------|
| **Latency** | E2E latency (summary) | TTFT, TPOT (histograms) |
| **Throughput** | Tokens/sec (rate) | Per-model tokens, request counts |
| **Queue** | None | num_requests_running, num_requests_waiting |
| **KV Cache** | None | gpu_cache_usage_perc, prefix_hit_rate |
| **Labels** | endpoint only | + model_name, finished_reason |
| **Format** | Custom JSON | + Prometheus OpenMetrics |
| **Histograms** | None | All latency and token metrics |
| **Streaming** | TTFT, TPS (summary) | Keep + enhance with histograms |

---

**END OF DOCUMENT**
