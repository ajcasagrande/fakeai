# NVIDIA TensorRT-LLM Inference Metrics Specification

**Version:** 1.0
**Date:** 2025-10-04
**Source:** NVIDIA TensorRT-LLM Official Documentation and Source Code

---

## Table of Contents

1. [Overview](#overview)
2. [Iteration Statistics](#iteration-statistics)
3. [Request Statistics](#request-statistics)
4. [Request Performance Metrics](#request-performance-metrics)
5. [KV Cache Statistics](#kv-cache-statistics)
6. [Batch Manager Statistics](#batch-manager-statistics)
7. [Speculative Decoding Statistics](#speculative-decoding-statistics)
8. [Memory Metrics](#memory-metrics)
9. [Triton Metrics Endpoint](#triton-metrics-endpoint)
10. [Benchmarking Metrics](#benchmarking-metrics)
11. [JSON Serialization](#json-serialization)

---

## Overview

TensorRT-LLM provides comprehensive metrics for monitoring and optimizing LLM inference performance. These metrics are exposed through:

1. **Executor API** - C++ and Python API for programmatic access
2. **Triton Metrics Endpoint** - Prometheus-compatible metrics (prefixed with `nv_trt_llm_`)
3. **Benchmarking Tools** - `trtllm-bench` with JSON output

All metrics are designed for production monitoring, performance tuning, and capacity planning.

---

## Iteration Statistics

### IterationStats Struct

Per-iteration statistics provide a snapshot of system state at each inference step.

**Source:** `cpp/include/tensorrt_llm/executor/types.h`

```cpp
struct IterationStats
{
    // Timing Information
    std::string timestamp;                              // ISO 8601 timestamp of iteration end
    IterationType iter;                                 // Iteration ID (sequential counter)
    double iterLatencyMS;                               // Total iteration latency (milliseconds)
    double newActiveRequestsQueueLatencyMS;             // Queue time for newly activated requests (ms)

    // Request Counts
    SizeType32 numNewActiveRequests;                    // Requests activated this iteration
    SizeType32 numActiveRequests;                       // Total active requests
    SizeType32 numQueuedRequests;                       // Requests waiting in queue
    SizeType32 numCompletedRequests;                    // Requests completed this iteration
    SizeType32 maxNumActiveRequests;                    // Maximum active requests allowed

    // Batch Size Configuration
    SizeType32 maxBatchSizeStatic;                      // Static max batch size (config)
    SizeType32 maxBatchSizeTunerRecommended;            // Dynamic tuner recommendation
    SizeType32 maxBatchSizeRuntime;                     // Actual runtime batch size limit

    // Token Configuration
    SizeType32 maxNumTokensStatic;                      // Static max tokens (config)
    SizeType32 maxNumTokensTunerRecommended;            // Dynamic tuner recommendation
    SizeType32 maxNumTokensRuntime;                     // Actual runtime token limit

    // Memory Usage (bytes)
    size_t gpuMemUsage;                                 // GPU memory consumption
    size_t cpuMemUsage;                                 // CPU memory consumption
    size_t pinnedMemUsage;                              // Pinned memory consumption

    // Optional Sub-Statistics
    std::optional<KvCacheStats> kvCacheStats;           // KV cache metrics
    std::optional<KvCacheStats> crossKvCacheStats;      // Cross-attention KV cache
    std::optional<StaticBatchingStats> staticBatchingStats;
    std::optional<InflightBatchingStats> inflightBatchingStats;
    std::optional<SpecDecodingStats> specDecodingStats;
};
```

**Key Metrics:**

- **iterLatencyMS**: Critical for SLA monitoring (prefill + decode time)
- **numActiveRequests**: Current system load
- **numQueuedRequests**: Backlog indicator
- **gpuMemUsage**: Memory pressure monitoring
- **kvCacheStats**: Cache efficiency metrics

**Access Method:**
```cpp
// C++ API
auto stats = executor.getLatestIterationStats();

// Python API
stats = executor.get_latest_iteration_stats()
```

---

## Request Statistics

### RequestStats Struct

Per-request statistics track individual request lifecycle and state.

```cpp
struct RequestStats
{
    // Identity
    IdType id;                                          // Unique request ID
    RequestStage stage;                                 // Current stage (enum)

    // Progress Tracking
    SizeType32 contextPrefillPosition;                  // Position in chunked prefill
    SizeType32 numGeneratedTokens;                      // Tokens generated so far
    float avgNumDecodedTokensPerIter;                   // Avg tokens/iteration (≥1 for spec decoding)

    // Scheduling State
    bool scheduled;                                     // Scheduled for current iteration
    bool paused;                                        // Paused due to resource constraints

    // KV Cache Metrics
    SizeType32 allocTotalBlocksPerRequest;              // Total KV cache blocks allocated
    SizeType32 allocNewBlocksPerRequest;                // Newly allocated blocks
    SizeType32 reusedBlocksPerRequest;                  // Reused blocks (cache hit)
    SizeType32 missedBlocksPerRequest;                  // Missed blocks (cache miss)
    float kvCacheHitRatePerRequest;                     // Hit rate: reused/(reused+missed)

    // Disaggregated Serving
    std::optional<DisServingRequestStats> disServingStats;
};
```

**RequestStage Enum:**
```cpp
enum class RequestStage
{
    QUEUED,            // Waiting for scheduling
    ENCODER,           // Encoder phase
    CONTEXT_INIT,      // Context initialization
    CONTEXT,           // Context/prefill phase
    GENERATION_INIT,   // Generation initialization
    GENERATION         // Token generation/decode phase
};
```

### DisServingRequestStats

Metrics specific to disaggregated serving (context/generation on separate instances).

```cpp
struct DisServingRequestStats
{
    double kvCacheTransferMS;    // KV cache transfer time (ms)
    size_t kvCacheSize;          // KV cache transfer size (bytes)
};
```

### RequestStatsPerIteration

```cpp
struct RequestStatsPerIteration
{
    IterationType iter;                         // Iteration ID
    std::vector<RequestStats> requestStats;     // All active request stats
};
```

---

## Request Performance Metrics

### RequestPerfMetrics Struct

Comprehensive end-to-end performance metrics per request.

```cpp
struct RequestPerfMetrics
{
    using TimePoint = std::chrono::time_point<std::chrono::steady_clock>;

    // Nested Structures
    struct TimingMetrics
    {
        TimePoint arrivalTime;              // Request arrival timestamp
        TimePoint firstScheduledTime;       // First scheduling timestamp
        TimePoint firstTokenTime;           // First token generation timestamp (TTFT)
        TimePoint lastTokenTime;            // Request completion timestamp
        TimePoint kvCacheTransferStart;     // DisServing: KV transfer start
        TimePoint kvCacheTransferEnd;       // DisServing: KV transfer end
        size_t kvCacheSize;                 // DisServing: KV cache size (bytes)
    };

    struct KvCacheMetrics
    {
        SizeType32 numTotalAllocatedBlocks;  // Total blocks allocated
        SizeType32 numNewAllocatedBlocks;    // Newly allocated blocks
        SizeType32 numReusedBlocks;          // Reused blocks
        SizeType32 numMissedBlocks;          // Missed blocks
        float kvCacheHitRate;                // Hit rate: reused/(reused+missed)
    };

    struct SpeculativeDecodingMetrics
    {
        float acceptanceRate;                // Draft token acceptance rate
        SizeType32 totalAcceptedDraftTokens; // Total accepted draft tokens
        SizeType32 totalDraftTokens;         // Total draft tokens proposed
    };

    // Aggregated Metrics
    TimingMetrics timingMetrics;
    KvCacheMetrics kvCacheMetrics;
    SpeculativeDecodingMetrics speculativeDecoding;

    // Iteration Tracking
    std::optional<IterationType> firstIter;  // First iteration processed
    std::optional<IterationType> lastIter;   // Last iteration with token generation
    std::optional<IterationType> iter;       // Current iteration
};
```

**Derived Metrics:**

Calculate common performance metrics from `TimingMetrics`:

```python
# Time to First Token (TTFT)
ttft_ms = (firstTokenTime - arrivalTime).total_milliseconds()

# Time Between Tokens (TBT) - average inter-token latency
total_time_ms = (lastTokenTime - firstTokenTime).total_milliseconds()
tbt_ms = total_time_ms / (num_tokens - 1)

# End-to-End Latency
e2e_latency_ms = (lastTokenTime - arrivalTime).total_milliseconds()

# Queue Time
queue_time_ms = (firstScheduledTime - arrivalTime).total_milliseconds()

# Token Throughput (tokens/second)
throughput = num_tokens / (e2e_latency_ms / 1000.0)
```

---

## KV Cache Statistics

### KvCacheStats Struct

Detailed KV cache utilization and reuse metrics.

```cpp
struct KvCacheStats
{
    // Capacity Metrics
    SizeType32 maxNumBlocks;        // Maximum blocks available
    SizeType32 freeNumBlocks;       // Free blocks (unused)
    SizeType32 usedNumBlocks;       // Used blocks (occupied)
    SizeType32 tokensPerBlock;      // Tokens per block (configuration)

    // Allocation Metrics
    SizeType32 allocTotalBlocks;    // Total allocated blocks (current iteration)
    SizeType32 allocNewBlocks;      // Newly allocated blocks (not reused)
    SizeType32 reusedBlocks;        // Reused blocks (cache hit)
    SizeType32 missedBlocks;        // Missed blocks (cache miss)

    // Efficiency Metric
    float cacheHitRate;             // reusedBlocks / (reusedBlocks + missedBlocks)
};
```

**Derived Metrics:**

```python
# KV Cache Utilization
utilization_pct = (usedNumBlocks / maxNumBlocks) * 100

# Available Capacity
available_tokens = freeNumBlocks * tokensPerBlock

# Memory Pressure
memory_pressure = 1.0 - (freeNumBlocks / maxNumBlocks)

# Reuse Efficiency
reuse_efficiency = reusedBlocks / allocTotalBlocks if allocTotalBlocks > 0 else 0
```

**Performance Impact:**

- **High cacheHitRate (>70%)**: Excellent reuse, faster TTFT
- **Low freeNumBlocks (<10%)**: Memory pressure, potential OOM
- **High missedBlocks**: Poor prompt similarity, consider cache warming

---

## Batch Manager Statistics

### InflightBatchingStats Struct

Continuous batching (inflight batching) statistics.

```cpp
struct InflightBatchingStats
{
    // Request Counts
    SizeType32 numScheduledRequests;    // Requests scheduled this iteration
    SizeType32 numContextRequests;      // Requests in context/prefill phase
    SizeType32 numGenRequests;          // Requests in generation/decode phase
    SizeType32 numPausedRequests;       // Paused requests (resource constraints)

    // Token Counts
    SizeType32 numCtxTokens;            // Total context tokens this iteration

    // Batching Metrics
    SizeType32 microBatchId;            // Micro-batch identifier
    float avgNumDecodedTokensPerIter;   // Avg tokens decoded per request per iteration
};
```

### StaticBatchingStats Struct

Traditional static batching statistics (legacy mode).

```cpp
struct StaticBatchingStats
{
    // Request Counts
    SizeType32 numScheduledRequests;    // Scheduled requests
    SizeType32 numContextRequests;      // Context phase requests

    // Token Counts
    SizeType32 numCtxTokens;            // Total context tokens
    SizeType32 numGenTokens;            // Total generation tokens

    // Efficiency Metric
    SizeType32 emptyGenSlots;           // Unused generation token slots (waste)
};
```

**Batching Efficiency:**

```python
# Inflight Batching GPU Utilization
gpu_util = (numContextRequests + numGenRequests) / maxNumActiveRequests

# Static Batching Efficiency
batch_efficiency = 1.0 - (emptyGenSlots / (numGenTokens + emptyGenSlots))

# Context/Generation Mix
ctx_ratio = numContextRequests / (numContextRequests + numGenRequests)
```

---

## Speculative Decoding Statistics

### SpecDecodingStats Struct

Metrics for speculative decoding (draft-verify approach).

```cpp
struct SpecDecodingStats
{
    SizeType64 numDraftTokens;          // Total draft tokens proposed
    SizeType64 numAcceptedTokens;       // Draft tokens accepted by target model
    SizeType64 numRequestsWithDraftTokens; // Requests using speculative decoding

    // Key Performance Metric
    double acceptanceLength;            // Avg tokens per step = numAcceptedTokens / numRequestsWithDraftTokens
};
```

**Performance Analysis:**

```python
# Acceptance Rate (higher is better)
acceptance_rate = numAcceptedTokens / numDraftTokens if numDraftTokens > 0 else 0

# Speedup Factor
# Ideal: acceptance_length ≈ draft_model_speed_ratio
# Example: draft is 5x faster, acceptance_length=2.5 → 2.5x speedup

# Speculative Decoding Efficiency
spec_efficiency = acceptance_rate * draft_model_speed_ratio
```

**Tuning Guidance:**

- **acceptanceLength < 1.5**: Draft model quality too low, consider better draft
- **acceptanceLength > 3.0**: Excellent draft quality, near-optimal speedup
- **numRequestsWithDraftTokens low**: Enable spec decoding for more requests

---

## Memory Metrics

### Memory Components

TensorRT-LLM tracks three primary memory categories:

```cpp
// From IterationStats
size_t gpuMemUsage;      // GPU DRAM (model weights + activations + KV cache)
size_t cpuMemUsage;      // CPU system memory
size_t pinnedMemUsage;   // Pinned (page-locked) host memory
```

### Memory Breakdown

**1. Weights Memory** (static)
- Model parameters in chosen precision (FP16, FP8, INT8, INT4)
- Divided across TP/PP ranks
- Formula: `weights_bytes = num_parameters * bytes_per_param / tp_size / pp_size`

**2. Activation Memory** (dynamic)
- Computed at engine build time based on max shapes
- Depends on: `max_batch_size`, `max_input_len`, `max_beam_width`, `max_num_tokens`
- Reduced by: context FMHA, packed tensors, smaller max values

**3. KV Cache Memory** (dynamic)
- Typically 90% of remaining free GPU memory (configurable)
- Formula: `kv_cache_bytes = num_blocks * tokens_per_block * num_layers * (key_size + value_size)`
- Configuration: `maxTokens` or `freeGpuMemoryFraction`

**4. I/O Tensors** (dynamic)
- Input/output buffers
- Negligible compared to KV cache

### Memory Optimization Strategies

```python
# Calculate Memory Footprint
def estimate_memory(model_params, dtype, tp_size, max_batch_size, kv_cache_pct=0.9):
    bytes_per_param = {'fp16': 2, 'fp8': 1, 'int8': 1, 'int4': 0.5}[dtype]
    weights_gb = (model_params * bytes_per_param) / (1024**3) / tp_size

    # Activation memory (rough estimate)
    activation_gb = max_batch_size * 0.5  # ~0.5GB per concurrent request

    # KV cache (remaining memory * 0.9)
    total_available_gb = 80  # Example: H100
    kv_cache_gb = (total_available_gb - weights_gb - activation_gb) * kv_cache_pct

    return weights_gb, activation_gb, kv_cache_gb
```

---

## Triton Metrics Endpoint

When using TensorRT-LLM with Triton Inference Server, metrics are exposed at `/metrics` in Prometheus format.

**Endpoint:** `http://localhost:8002/metrics`

### Metric Categories

All TensorRT-LLM metrics are prefixed with `nv_trt_llm_`.

#### 1. Request Metrics

```
nv_trt_llm_request_metrics{request_type="waiting"}
nv_trt_llm_request_metrics{request_type="context"}
nv_trt_llm_request_metrics{request_type="scheduled"}
nv_trt_llm_request_metrics{request_type="max"}
nv_trt_llm_request_metrics{request_type="active"}
```

**Description:** Number of requests in each state (gauge).

#### 2. Runtime Memory Metrics

```
nv_trt_llm_runtime_memory_metrics{memory_type="pinned"}
nv_trt_llm_runtime_memory_metrics{memory_type="gpu"}
nv_trt_llm_runtime_memory_metrics{memory_type="cpu"}
```

**Description:** Memory usage in bytes (gauge).

#### 3. KV Cache Block Metrics

```
nv_trt_llm_kv_cache_block_metrics{kv_cache_block_type="tokens_per_block"}
nv_trt_llm_kv_cache_block_metrics{kv_cache_block_type="used_blocks"}
nv_trt_llm_kv_cache_block_metrics{kv_cache_block_type="free_blocks"}
nv_trt_llm_kv_cache_block_metrics{kv_cache_block_type="max_blocks"}
nv_trt_llm_kv_cache_block_metrics{kv_cache_block_type="cache_block_fraction"}
```

**Description:** KV cache utilization metrics (gauge).

#### 4. Inflight Batcher Metrics

```
nv_trt_llm_inflight_batcher_metrics{inflight_batcher_specific_metric="micro_batch_id"}
nv_trt_llm_inflight_batcher_metrics{inflight_batcher_specific_metric="generation_requests"}
nv_trt_llm_inflight_batcher_metrics{inflight_batcher_specific_metric="total_context_tokens"}
```

**Description:** Continuous batching statistics (gauge).

#### 5. General Metrics

```
nv_trt_llm_general_metrics{general_type="iteration_counter"}
nv_trt_llm_general_metrics{general_type="timestamp"}
```

**Description:** Server-level counters (counter/gauge).

#### 6. Disaggregated Serving Metrics

```
nv_trt_llm_disaggregated_serving_metrics{disaggregated_serving_type="kv_cache_transfer_time"}
nv_trt_llm_disaggregated_serving_metrics{disaggregated_serving_type="request_count"}
```

**Description:** Context/generation split metrics (histogram/counter).

### Example Prometheus Scrape Config

```yaml
scrape_configs:
  - job_name: 'tensorrt-llm'
    static_configs:
      - targets: ['localhost:8002']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

### Grafana Dashboard Queries

```promql
# Request Throughput (req/s)
rate(nv_trt_llm_general_metrics{general_type="iteration_counter"}[1m])

# KV Cache Utilization (%)
(nv_trt_llm_kv_cache_block_metrics{kv_cache_block_type="used_blocks"} /
 nv_trt_llm_kv_cache_block_metrics{kv_cache_block_type="max_blocks"}) * 100

# GPU Memory Usage (GB)
nv_trt_llm_runtime_memory_metrics{memory_type="gpu"} / (1024^3)

# Active Request Count
nv_trt_llm_request_metrics{request_type="active"}
```

---

## Benchmarking Metrics

### trtllm-bench Tool

TensorRT-LLM provides `trtllm-bench` for performance benchmarking.

**Command:**
```bash
trtllm-bench \
  --engine_dir ./engine \
  --dataset dataset.json \
  --report_json report.json
```

### Benchmark Output Metrics

#### Performance Metrics

**1. Token Throughput**
```
Total Output Throughput: 28390.4265 tokens/sec
```
- Aggregate throughput across all requests
- Key metric for capacity planning

**2. Request Throughput**
```
Request Throughput: 221.8002 req/sec
```
- Requests completed per second
- Indicates concurrent request handling capacity

**3. Total Latency**
```
Total Latency: 13525.6862 ms
```
- Total time to complete benchmark
- Used for end-to-end performance validation

#### Latency Percentile Statistics

Reported for each latency type (TTFT, TBT, E2E):

```
Latency Percentiles (ms):
  P50:  150.23
  P90:  298.45
  P95:  367.89
  P99:  512.34
  Min:  102.11
  Max:  678.90
  Avg:  187.56
```

**Latency Types:**

- **TTFT (Time to First Token)**: `firstTokenTime - arrivalTime`
- **TBT (Time Between Tokens)**: Average inter-token latency
- **E2E (End-to-End)**: `lastTokenTime - arrivalTime`

#### Input/Output Length Statistics

```
Input Lengths (tokens):
  Average: 512
  Minimum: 128
  Maximum: 2048

Output Lengths (tokens):
  Average: 256
  Minimum: 64
  Maximum: 512
```

#### Runtime Configuration

```
Engine Details:
  Tensor Parallel (TP): 2
  Pipeline Parallel (PP): 1
  Max Runtime Batch Size: 128
  Max Runtime Tokens: 8192
  Scheduling Policy: GUARANTEED_NO_EVICT
  KV Memory Percentage: 90%
```

### JSON Report Format

**Structure:** `report.json`

```json
{
  "metadata": {
    "model": "llama-2-70b",
    "engine_path": "./engine",
    "timestamp": "2025-10-04T12:00:00Z",
    "gpu": "NVIDIA H100",
    "num_gpus": 2
  },
  "performance": {
    "token_throughput_per_sec": 28390.4265,
    "request_throughput_per_sec": 221.8002,
    "total_latency_ms": 13525.6862
  },
  "latency_stats": {
    "ttft_ms": {
      "p50": 150.23,
      "p90": 298.45,
      "p95": 367.89,
      "p99": 512.34,
      "min": 102.11,
      "max": 678.90,
      "avg": 187.56
    },
    "tbt_ms": { /* ... */ },
    "e2e_ms": { /* ... */ }
  },
  "input_output_stats": {
    "input_tokens": {
      "avg": 512,
      "min": 128,
      "max": 2048
    },
    "output_tokens": {
      "avg": 256,
      "min": 64,
      "max": 512
    }
  },
  "configuration": {
    "tp_size": 2,
    "pp_size": 1,
    "max_batch_size": 128,
    "max_num_tokens": 8192,
    "scheduler_policy": "GUARANTEED_NO_EVICT",
    "kv_memory_percentage": 0.9
  }
}
```

### Benchmark Analysis

**Calculate Key Metrics:**

```python
# Effective Batch Size
effective_batch_size = token_throughput / (1000 / avg_tbt_ms)

# GPU Utilization Estimate
theoretical_max_throughput = 100000  # tokens/sec for H100
gpu_utilization = (token_throughput / theoretical_max_throughput) * 100

# Request Processing Efficiency
avg_tokens_per_request = avg_input_tokens + avg_output_tokens
efficiency = request_throughput * avg_tokens_per_request / token_throughput
```

---

## JSON Serialization

### JsonSerialization Class

TensorRT-LLM provides utilities to serialize statistics to JSON.

**C++ API:**

```cpp
#include "tensorrt_llm/executor/executor.h"

// Serialize IterationStats to JSON string
std::string json = tensorrt_llm::executor::JsonSerialization::toJsonStr(iterationStats);

// Serialize RequestStats to JSON string
std::string json = tensorrt_llm::executor::JsonSerialization::toJsonStr(requestStats);
```

**Python API:**

```python
import json
from tensorrt_llm import bindings

# Get iteration stats
stats = executor.get_latest_iteration_stats()

# Convert to dictionary (automatic serialization)
stats_dict = {
    "timestamp": stats.timestamp,
    "iter": stats.iter,
    "iter_latency_ms": stats.iter_latency_ms,
    "num_active_requests": stats.num_active_requests,
    "num_queued_requests": stats.num_queued_requests,
    "gpu_mem_usage": stats.gpu_mem_usage,
    "cpu_mem_usage": stats.cpu_mem_usage,
    "kv_cache_stats": {
        "max_num_blocks": stats.kv_cache_stats.max_num_blocks,
        "free_num_blocks": stats.kv_cache_stats.free_num_blocks,
        "used_num_blocks": stats.kv_cache_stats.used_num_blocks,
        "cache_hit_rate": stats.kv_cache_stats.cache_hit_rate,
    } if stats.kv_cache_stats else None
}

# Serialize to JSON
json_str = json.dumps(stats_dict, indent=2)
```

### Example JSON Output

**IterationStats Example:**

```json
{
  "timestamp": "2025-10-04T12:34:56.789Z",
  "iter": 1234,
  "iter_latency_ms": 45.67,
  "new_active_requests_queue_latency_ms": 12.34,
  "num_new_active_requests": 2,
  "num_active_requests": 8,
  "num_queued_requests": 3,
  "num_completed_requests": 1,
  "max_num_active_requests": 128,
  "max_batch_size_static": 128,
  "max_batch_size_tuner_recommended": 96,
  "max_batch_size_runtime": 96,
  "max_num_tokens_static": 8192,
  "max_num_tokens_tuner_recommended": 6144,
  "max_num_tokens_runtime": 6144,
  "gpu_mem_usage": 68719476736,
  "cpu_mem_usage": 1073741824,
  "pinned_mem_usage": 268435456,
  "kv_cache_stats": {
    "max_num_blocks": 10240,
    "free_num_blocks": 2048,
    "used_num_blocks": 8192,
    "tokens_per_block": 64,
    "alloc_total_blocks": 256,
    "alloc_new_blocks": 32,
    "reused_blocks": 224,
    "missed_blocks": 32,
    "cache_hit_rate": 0.875
  },
  "inflight_batching_stats": {
    "num_scheduled_requests": 8,
    "num_context_requests": 2,
    "num_gen_requests": 6,
    "num_paused_requests": 0,
    "num_ctx_tokens": 2048,
    "micro_batch_id": 5,
    "avg_num_decoded_tokens_per_iter": 1.2
  }
}
```

**RequestPerfMetrics Example:**

```json
{
  "request_id": "req-12345",
  "timing_metrics": {
    "arrival_time": "2025-10-04T12:34:56.000Z",
    "first_scheduled_time": "2025-10-04T12:34:56.050Z",
    "first_token_time": "2025-10-04T12:34:56.200Z",
    "last_token_time": "2025-10-04T12:34:58.500Z",
    "ttft_ms": 200,
    "e2e_latency_ms": 2500,
    "queue_time_ms": 50
  },
  "kv_cache_metrics": {
    "num_total_allocated_blocks": 128,
    "num_new_allocated_blocks": 16,
    "num_reused_blocks": 112,
    "num_missed_blocks": 16,
    "kv_cache_hit_rate": 0.875
  },
  "speculative_decoding": {
    "acceptance_rate": 0.65,
    "total_accepted_draft_tokens": 130,
    "total_draft_tokens": 200
  },
  "first_iter": 1200,
  "last_iter": 1250,
  "iter": 1250
}
```

---

## Performance Tuning Guidelines

### 1. Identify Bottlenecks

**Compute-Bound (Prefill Phase)**
- Symptoms: High `numCtxTokens`, high `iterLatencyMS` with context requests
- Solutions: Increase batch size, use chunked prefill, optimize TP/PP

**Memory-Bound (Decode Phase)**
- Symptoms: Low `freeNumBlocks`, high `iterLatencyMS` with generation requests
- Solutions: Reduce `max_batch_size`, enable KV cache quantization, increase GPU memory

**Queue-Bound (Scheduler)**
- Symptoms: High `numQueuedRequests`, high `newActiveRequestsQueueLatencyMS`
- Solutions: Increase `max_num_active_requests`, optimize scheduling policy

### 2. Optimize KV Cache

**Target Metrics:**
- `cacheHitRate`: > 70% for prompt-heavy workloads
- `freeNumBlocks` / `maxNumBlocks`: > 10% (avoid OOM)
- `usedNumBlocks` / `maxNumBlocks`: > 80% (maximize utilization)

**Strategies:**
- Enable automatic prefix caching
- Use KV cache quantization (INT8/FP8)
- Adjust `tokensPerBlock` for prompt patterns
- Implement prompt pre-filling/warming

### 3. Batch Size Tuning

**Dynamic Tuning:**
- Monitor `maxBatchSizeTunerRecommended` vs `maxBatchSizeStatic`
- Enable dynamic tuner: `enable_dynamic_batch_size=true`
- Set conservative initial: `max_batch_size_static = 64`

**Optimization:**
```python
# Calculate optimal batch size
optimal_batch_size = (gpu_memory_available - weights_memory - activation_memory) / kv_cache_per_request

# Monitor efficiency
batch_efficiency = num_active_requests / max_batch_size_runtime
# Target: > 80%
```

### 4. Speculative Decoding Tuning

**Target Metrics:**
- `acceptanceLength`: > 2.0 (2x speedup)
- `acceptanceRate`: > 60%

**Strategies:**
- Use high-quality draft model (e.g., Llama-68M for Llama-70B)
- Adjust draft model size vs. acceptance trade-off
- Monitor per-request `acceptanceRate` for variability

### 5. Disaggregated Serving

**When to Use:**
- `numContextRequests` and `numGenRequests` have high variance
- Context phase latency >> generation phase latency
- GPU utilization unbalanced

**Monitor:**
- `kvCacheTransferMS`: < 10% of total latency
- `kvCacheSize`: Minimize transfer overhead

---

## Metric Collection Best Practices

### 1. Iteration Stats Polling

```python
# Configure statistics collection
executor_config.iter_stats_max_iterations = 1000  # Keep last 1000 iterations
executor_config.request_stats_max_iterations = 100  # Keep last 100 iterations per request

# Poll periodically
import time
while True:
    stats = executor.get_latest_iteration_stats()
    process_stats(stats)
    time.sleep(1)  # 1 second polling interval
```

### 2. Request Stats Callback

```python
# Enable request performance metrics
request = Request(
    input_token_ids=input_ids,
    return_perf_metrics=True  # Enable detailed metrics
)

# Access metrics in response
result = executor.generate(request)
perf_metrics = result.request_perf_metrics
```

### 3. Logging Configuration

```bash
# Enable detailed logging
export TRTLLM_LOG_LEVEL=INFO  # or DEBUG for verbose output

# Log memory usage changes
export TRTLLM_LOG_MEM_USAGE=1
```

### 4. Metrics Aggregation

```python
# Aggregate iteration stats over time window
def aggregate_metrics(stats_list, window_seconds=60):
    recent_stats = [s for s in stats_list if time.time() - s.timestamp < window_seconds]

    return {
        "avg_iter_latency_ms": sum(s.iter_latency_ms for s in recent_stats) / len(recent_stats),
        "avg_active_requests": sum(s.num_active_requests for s in recent_stats) / len(recent_stats),
        "p95_iter_latency_ms": percentile([s.iter_latency_ms for s in recent_stats], 95),
        "total_completed_requests": sum(s.num_completed_requests for s in recent_stats),
        "avg_kv_cache_hit_rate": sum(s.kv_cache_stats.cache_hit_rate for s in recent_stats if s.kv_cache_stats) / len(recent_stats),
    }
```

---

## References

### Official Documentation

- **TensorRT-LLM GitHub**: https://github.com/NVIDIA/TensorRT-LLM
- **Official Docs**: https://nvidia.github.io/TensorRT-LLM/
- **Executor API**: https://nvidia.github.io/TensorRT-LLM/advanced/executor.html
- **Benchmarking Guide**: https://nvidia.github.io/TensorRT-LLM/performance/perf-benchmarking.html
- **Memory Usage**: https://nvidia.github.io/TensorRT-LLM/reference/memory.html

### Blog Posts

- **Performance Tuning with TensorRT-LLM**: https://developer.nvidia.com/blog/llm-inference-benchmarking-performance-tuning-with-tensorrt-llm/
- **KV Cache Reuse**: https://developer.nvidia.com/blog/introducing-new-kv-cache-reuse-optimizations-in-nvidia-tensorrt-llm/
- **Chunked Prefill**: https://developer.nvidia.com/blog/streamlining-ai-inference-performance-and-deployment-with-nvidia-tensorrt-llm-chunked-prefill/
- **Speculative Decoding**: https://developer.nvidia.com/blog/boost-llama-3-3-70b-inference-throughput-3x-with-nvidia-tensorrt-llm-speculative-decoding/

### Source Code References

- **Executor Types**: `cpp/include/tensorrt_llm/executor/types.h`
- **Executor API**: `cpp/include/tensorrt_llm/executor/executor.h`
- **Python Bindings**: `cpp/tensorrt_llm/pybind/executor/bindings.cpp`

---

## Appendix: Metric Quick Reference

### Critical Performance Metrics

| Metric | Source | Unit | Description | Target |
|--------|--------|------|-------------|--------|
| `iterLatencyMS` | IterationStats | ms | Per-iteration latency | < 50ms decode, < 500ms prefill |
| `ttft_ms` | RequestPerfMetrics | ms | Time to first token | < 200ms |
| `tbt_ms` | RequestPerfMetrics | ms | Time between tokens | < 20ms |
| `token_throughput` | trtllm-bench | tokens/sec | Aggregate throughput | > 20K for H100 |
| `cacheHitRate` | KvCacheStats | ratio | KV cache reuse rate | > 0.7 |
| `gpuMemUsage` | IterationStats | bytes | GPU memory usage | < 90% capacity |
| `numQueuedRequests` | IterationStats | count | Backlog size | < 10% of max |
| `acceptanceLength` | SpecDecodingStats | count | Spec decoding efficiency | > 2.0 |

### Troubleshooting Guide

| Symptom | Likely Cause | Check Metrics | Solution |
|---------|--------------|---------------|----------|
| High latency | Memory-bound | `freeNumBlocks`, `gpuMemUsage` | Reduce batch size, enable KV quant |
| Low throughput | Under-batching | `numActiveRequests` / `maxNumActiveRequests` | Increase max batch size |
| OOM errors | KV cache exhaustion | `freeNumBlocks` < 0 | Reduce max tokens, increase GPU memory |
| Queue buildup | Insufficient capacity | `numQueuedRequests` increasing | Add GPU, optimize scheduling |
| Poor spec decoding | Bad draft quality | `acceptanceRate` < 0.5 | Use better draft model |

---

**End of TensorRT-LLM Metrics Specification**
