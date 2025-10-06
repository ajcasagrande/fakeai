# NVIDIA Triton Inference Server Metrics Research

**Research Date:** 2025-10-04
**Triton Version Researched:** Latest (2025), with references to archived versions
**Purpose:** Comprehensive catalog of Triton metrics for potential FakeAI integration

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Triton Metrics Architecture](#triton-metrics-architecture)
3. [Complete Metric Catalog](#complete-metric-catalog)
4. [Backend-Specific Metrics](#backend-specific-metrics)
5. [Integration Patterns](#integration-patterns)
6. [Production Deployment Patterns](#production-deployment-patterns)
7. [Comparison with FakeAI Metrics](#comparison-with-fakeai-metrics)
8. [Implementation Recommendations](#implementation-recommendations)

---

## 1. Executive Summary

### What is Triton Inference Server?

NVIDIA Triton Inference Server (recently renamed to NVIDIA Dynamo Triton as of March 18, 2025) is a production-grade, high-performance inference serving solution that supports multiple deep learning frameworks including TensorFlow, PyTorch, TensorRT, ONNX, and custom backends.

### Metrics Overview

Triton provides comprehensive Prometheus-formatted metrics at **http://localhost:8002/metrics** covering:

- **Inference Request Metrics**: Request counts, latencies, queue times, compute times
- **GPU Metrics**: Power usage, utilization, memory via DCGM integration
- **CPU Metrics**: Utilization and memory from `/proc` filesystem
- **Batch Metrics**: Batch sizes, execution counts, dynamic batching effectiveness
- **Cache Metrics**: Response cache hit/miss rates and latencies
- **Custom Backend Metrics**: TensorRT-LLM, vLLM, and user-defined metrics via C API

### Key Features

1. **Per-Model Granularity**: All inference metrics include `model` and `version` labels
2. **Multiple Metric Types**: Counters, Gauges, Histograms, and Summaries
3. **Custom Metrics API**: C API for backends to expose specialized metrics
4. **Prometheus Compatible**: Standard exposition format for scraping
5. **Configurable**: Control metrics endpoint, polling intervals, quantiles, and buckets

---

## 2. Triton Metrics Architecture

### 2.1 Metrics Endpoint Configuration

**Default Endpoint:**
```
http://localhost:8002/metrics
```

**CLI Configuration Options:**
```bash
tritonserver \
  --metrics-address=0.0.0.0 \
  --metrics-port=8002 \
  --metrics-interval-ms=2000 \
  --allow-metrics=true
```

### 2.2 Metric Collection Architecture

```

                   Triton Server Core                    

  Request Handler → Metrics Collector → Prometheus      
                         ↓                                
     
   Inference Metrics (per-model, per-version)         
    - Request counts                                   
    - Latency breakdowns                               
    - Queue times                                      
    - Batch sizes                                      
     
                                                          
     
   System Metrics                                      
    - GPU (via DCGM)                                   
    - CPU (via /proc)                                  
    - Memory (pinned, GPU, system)                     
     
                                                          
     
   Backend Custom Metrics (via C API)                 
    - TensorRT-LLM metrics                             
    - vLLM metrics                                     
    - User-defined metrics                             
     

                            ↓
            HTTP GET /metrics → Prometheus scrape
```

### 2.3 Metric Types Used

| Type | Usage | Example |
|------|-------|---------|
| **Counter** | Cumulative values that only increase | `nv_inference_request_success` |
| **Gauge** | Values that can go up or down | `nv_gpu_utilization` |
| **Histogram** | Distribution of observations | `nv_inference_first_response_histogram_ms` |
| **Summary** | Quantiles over sliding time window | `nv_inference_request_duration_us` |

---

## 3. Complete Metric Catalog

### 3.1 Inference Request Count Metrics

#### 3.1.1 nv_inference_request_success
- **Type**: Counter
- **Description**: Number of successful inference requests received by Triton
- **Labels**: `model`, `version`
- **Use Case**: Track successful request volume per model

**Example:**
```prometheus
nv_inference_request_success{model="resnet50",version="1"} 45231
```

#### 3.1.2 nv_inference_request_failure
- **Type**: Counter
- **Description**: Number of failed inference requests received by Triton
- **Labels**: `model`, `version`
- **Use Case**: Monitor error rates and model health

**Example:**
```prometheus
nv_inference_request_failure{model="bert-base",version="2"} 12
```

#### 3.1.3 nv_inference_count
- **Type**: Counter
- **Description**: Number of inferences performed (batch of "n" counted as "n" inferences)
- **Labels**: `model`, `version`
- **Use Case**: Track actual inference volume accounting for batching

**Formula for Batch Size:**
```
Average Batch Size = nv_inference_count / nv_inference_exec_count
```

**Example:**
```prometheus
nv_inference_count{model="gpt-neo",version="1"} 128450
```

#### 3.1.4 nv_inference_exec_count
- **Type**: Counter
- **Description**: Number of inference batch executions performed
- **Labels**: `model`, `version`
- **Use Case**: Monitor batch execution efficiency

**Example:**
```prometheus
nv_inference_exec_count{model="gpt-neo",version="1"} 8530
# Average batch size = 128450 / 8530 = 15.05
```

#### 3.1.5 nv_inference_pending_request_count
- **Type**: Gauge
- **Description**: Number of inference requests currently awaiting execution
- **Labels**: `model`, `version`
- **Use Case**: Monitor queue depth and potential bottlenecks

**Example:**
```prometheus
nv_inference_pending_request_count{model="stable-diffusion",version="1"} 23
```

### 3.2 Inference Latency Metrics

#### 3.2.1 nv_inference_request_duration_us
- **Type**: Counter (cumulative microseconds) and Summary
- **Description**: Cumulative end-to-end request handling time
- **Labels**: `model`, `version`
- **Breakdown**: Total time from request arrival to response completion
- **Use Case**: Track overall request latency

**Components (sum equals total):**
```
nv_inference_request_duration_us =
    nv_inference_queue_duration_us +
    nv_inference_compute_input_duration_us +
    nv_inference_compute_infer_duration_us +
    nv_inference_compute_output_duration_us
```

**Summary Quantiles (when enabled):**
```prometheus
nv_inference_request_duration_us{model="bert",version="1",quantile="0.5"} 12500
nv_inference_request_duration_us{model="bert",version="1",quantile="0.9"} 25000
nv_inference_request_duration_us{model="bert",version="1",quantile="0.99"} 45000
```

#### 3.2.2 nv_inference_queue_duration_us
- **Type**: Counter (cumulative microseconds)
- **Description**: Cumulative time requests spend in the scheduling queue waiting for model instance
- **Labels**: `model`, `version`
- **Use Case**: Identify scheduling bottlenecks and insufficient model instances

**High queue time indicates:**
- Insufficient model instances
- Need for dynamic batching tuning
- Resource constraints

**Example:**
```prometheus
nv_inference_queue_duration_us{model="llama-2-70b",version="1"} 45620000
# Average per request = 45620000 / num_requests
```

#### 3.2.3 nv_inference_compute_input_duration_us
- **Type**: Counter (cumulative microseconds)
- **Description**: Cumulative time processing inference inputs (e.g., copying data to GPU)
- **Labels**: `model`, `version`
- **Use Case**: Monitor input preprocessing and data transfer overhead

**Example:**
```prometheus
nv_inference_compute_input_duration_us{model="resnet50",version="1"} 1250000
```

#### 3.2.4 nv_inference_compute_infer_duration_us
- **Type**: Counter (cumulative microseconds)
- **Description**: Cumulative time executing the actual inference model (core compute)
- **Labels**: `model`, `version`
- **Use Case**: Track pure model execution time

**This is the "real" inference time:**
- Excludes queue wait
- Excludes data transfer
- Pure model execution

**Example:**
```prometheus
nv_inference_compute_infer_duration_us{model="yolov8",version="1"} 8940000
```

#### 3.2.5 nv_inference_compute_output_duration_us
- **Type**: Counter (cumulative microseconds)
- **Description**: Cumulative time processing inference outputs (e.g., copying data from GPU)
- **Labels**: `model`, `version`
- **Use Case**: Monitor output postprocessing and data transfer overhead

**Example:**
```prometheus
nv_inference_compute_output_duration_us{model="openai/gpt-oss-120b",version="1"} 2340000
```

#### 3.2.6 nv_inference_first_response_histogram_ms
- **Type**: Histogram
- **Description**: Time to first response for decoupled models (milliseconds)
- **Labels**: `model`, `version`
- **Buckets**: Configurable (default: [1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000])
- **Use Case**: Track streaming/decoupled model TTFT (Time To First Token)

**For LLM/Streaming Models:**
- Critical metric for user experience
- Measures time until first token appears

**Example:**
```prometheus
nv_inference_first_response_histogram_ms_bucket{model="meta-llama/Llama-3.1-8B-Instruct",version="1",le="50"} 245
nv_inference_first_response_histogram_ms_bucket{model="meta-llama/Llama-3.1-8B-Instruct",version="1",le="100"} 892
nv_inference_first_response_histogram_ms_bucket{model="meta-llama/Llama-3.1-8B-Instruct",version="1",le="250"} 1450
nv_inference_first_response_histogram_ms_bucket{model="meta-llama/Llama-3.1-8B-Instruct",version="1",le="+Inf"} 1523
nv_inference_first_response_histogram_ms_sum{model="meta-llama/Llama-3.1-8B-Instruct",version="1"} 125400
nv_inference_first_response_histogram_ms_count{model="meta-llama/Llama-3.1-8B-Instruct",version="1"} 1523
```

### 3.3 GPU Metrics (via DCGM)

#### 3.3.1 nv_gpu_power_usage
- **Type**: Gauge
- **Description**: Instantaneous GPU power usage in watts
- **Labels**: `gpu_uuid`
- **Collection**: Via NVIDIA DCGM (Data Center GPU Manager)
- **Use Case**: Monitor power consumption and thermal management

**Example:**
```prometheus
nv_gpu_power_usage{gpu_uuid="GPU-12345678-1234-1234-1234-123456789012"} 285.4
```

#### 3.3.2 nv_gpu_power_limit
- **Type**: Gauge
- **Description**: Maximum GPU power limit in watts
- **Labels**: `gpu_uuid`
- **Use Case**: Track power budget and throttling thresholds

**Example:**
```prometheus
nv_gpu_power_limit{gpu_uuid="GPU-12345678-1234-1234-1234-123456789012"} 350.0
```

#### 3.3.3 nv_energy_consumption
- **Type**: Counter
- **Description**: Cumulative GPU energy consumption in joules
- **Labels**: `gpu_uuid`
- **Use Case**: Calculate total energy usage over time

**Example:**
```prometheus
nv_energy_consumption{gpu_uuid="GPU-12345678-1234-1234-1234-123456789012"} 125678900
```

#### 3.3.4 nv_gpu_utilization
- **Type**: Gauge
- **Description**: GPU utilization rate (0.0 to 1.0)
- **Labels**: `gpu_uuid`
- **Use Case**: Monitor GPU compute saturation

**Example:**
```prometheus
nv_gpu_utilization{gpu_uuid="GPU-12345678-1234-1234-1234-123456789012"} 0.87
# 87% GPU utilization
```

#### 3.3.5 nv_gpu_memory_total_bytes
- **Type**: Gauge
- **Description**: Total GPU memory available in bytes
- **Labels**: `gpu_uuid`
- **Use Case**: Capacity planning

**Example:**
```prometheus
nv_gpu_memory_total_bytes{gpu_uuid="GPU-12345678-1234-1234-1234-123456789012"} 85899345920
# 80 GB GPU (A100)
```

#### 3.3.6 nv_gpu_memory_used_bytes
- **Type**: Gauge
- **Description**: Currently used GPU memory in bytes
- **Labels**: `gpu_uuid`
- **Use Case**: Monitor memory pressure and OOM risks

**Formula:**
```
GPU Memory Utilization % = (nv_gpu_memory_used_bytes / nv_gpu_memory_total_bytes) * 100
```

**Example:**
```prometheus
nv_gpu_memory_used_bytes{gpu_uuid="GPU-12345678-1234-1234-1234-123456789012"} 72635523072
# 67.5 GB used out of 80 GB (84.4% utilization)
```

### 3.4 CPU Metrics (Linux /proc)

#### 3.4.1 nv_cpu_utilization
- **Type**: Gauge
- **Description**: Total CPU utilization rate (0.0 to 1.0)
- **Labels**: None (system-wide)
- **Collection**: Linux `/proc/stat`
- **Use Case**: Monitor CPU preprocessing/postprocessing overhead

**Example:**
```prometheus
nv_cpu_utilization 0.42
# 42% total CPU utilization across all cores
```

#### 3.4.2 nv_cpu_memory_total_bytes
- **Type**: Gauge
- **Description**: Total system memory in bytes
- **Labels**: None
- **Collection**: Linux `/proc/meminfo`
- **Use Case**: Capacity planning

**Example:**
```prometheus
nv_cpu_memory_total_bytes 540431384576
# 503 GB system RAM
```

#### 3.4.3 nv_cpu_memory_used_bytes
- **Type**: Gauge
- **Description**: Currently used system memory in bytes
- **Labels**: None
- **Use Case**: Monitor system memory pressure

**Example:**
```prometheus
nv_cpu_memory_used_bytes 245678931456
# 228 GB used out of 503 GB
```

### 3.5 Pinned Memory Metrics (Available since 24.01)

#### 3.5.1 nv_pinned_memory_pool_total_bytes
- **Type**: Gauge
- **Description**: Total pinned memory pool size in bytes
- **Labels**: None
- **Use Case**: Monitor pinned memory capacity for GPU transfers

**Pinned Memory:**
- Page-locked host memory
- Faster GPU-CPU transfers via DMA
- Limited resource

**Example:**
```prometheus
nv_pinned_memory_pool_total_bytes 8589934592
# 8 GB pinned memory pool
```

#### 3.5.2 nv_pinned_memory_pool_used_bytes
- **Type**: Gauge
- **Description**: Currently used pinned memory in bytes
- **Labels**: None
- **Use Case**: Monitor pinned memory utilization

**Example:**
```prometheus
nv_pinned_memory_pool_used_bytes 6442450944
# 6 GB used out of 8 GB (75%)
```

### 3.6 Response Cache Metrics (Available since 23.03)

#### 3.6.1 nv_cache_num_hits_per_model
- **Type**: Counter
- **Description**: Number of cache hits for model responses
- **Labels**: `model`, `version`
- **Use Case**: Monitor cache effectiveness

**Example:**
```prometheus
nv_cache_num_hits_per_model{model="bert-base",version="1"} 8450
```

#### 3.6.2 nv_cache_num_misses_per_model
- **Type**: Counter
- **Description**: Number of cache misses for model responses
- **Labels**: `model`, `version`
- **Use Case**: Calculate cache hit rate

**Formula:**
```
Cache Hit Rate % = (hits / (hits + misses)) * 100
```

**Example:**
```prometheus
nv_cache_num_misses_per_model{model="bert-base",version="1"} 1550
# Hit rate = 8450 / (8450 + 1550) = 84.5%
```

#### 3.6.3 nv_cache_hit_duration_per_model_us
- **Type**: Counter
- **Description**: Cumulative cache hit lookup time in microseconds
- **Labels**: `model`, `version`
- **Use Case**: Monitor cache performance

**Example:**
```prometheus
nv_cache_hit_duration_per_model_us{model="bert-base",version="1"} 42500
# Average hit latency = 42500 / 8450 = 5.03 µs per hit
```

#### 3.6.4 nv_cache_miss_duration_per_model_us
- **Type**: Counter
- **Description**: Cumulative cache miss lookup time in microseconds
- **Labels**: `model`, `version`
- **Use Case**: Track cache lookup overhead

**Example:**
```prometheus
nv_cache_miss_duration_per_model_us{model="bert-base",version="1"} 15500
```

#### 3.6.5 Custom Cache Metrics
- **Available**: Depends on cache implementation
- **Examples**: Cache size, eviction counts, memory usage
- **Use Case**: Implementation-specific monitoring

---

## 4. Backend-Specific Metrics

### 4.1 TensorRT-LLM Backend Metrics

**Introduced:** Triton 23.11+
**Prefix:** `nv_trt_llm_`
**Source:** TensorRT-LLM Batch Manager statistics

#### 4.1.1 nv_trt_llm_request_metrics
- **Type**: Gauge
- **Description**: TRT LLM request metrics by request state
- **Labels**: `model`, `version`, `request_type`

**Request Types:**
- `waiting`: Requests in queue awaiting processing
- `context`: Requests in context (prefill) phase
- `scheduled`: Requests scheduled for generation
- `max`: Maximum concurrent requests capacity
- `active`: Currently active requests

**Example:**
```prometheus
nv_trt_llm_request_metrics{model="llama-2-7b",version="1",request_type="waiting"} 3
nv_trt_llm_request_metrics{model="llama-2-7b",version="1",request_type="context"} 2
nv_trt_llm_request_metrics{model="llama-2-7b",version="1",request_type="scheduled"} 8
nv_trt_llm_request_metrics{model="llama-2-7b",version="1",request_type="max"} 64
nv_trt_llm_request_metrics{model="llama-2-7b",version="1",request_type="active"} 13
```

#### 4.1.2 nv_trt_llm_runtime_memory_metrics
- **Type**: Gauge
- **Description**: TRT LLM runtime memory usage in bytes
- **Labels**: `model`, `version`, `memory_type`

**Memory Types:**
- `gpu`: GPU device memory
- `cpu`: Host CPU memory
- `pinned`: Pinned (page-locked) host memory

**Example:**
```prometheus
nv_trt_llm_runtime_memory_metrics{model="llama-2-70b",version="1",memory_type="gpu"} 142345678912
nv_trt_llm_runtime_memory_metrics{model="llama-2-70b",version="1",memory_type="cpu"} 8589934592
nv_trt_llm_runtime_memory_metrics{model="llama-2-70b",version="1",memory_type="pinned"} 4294967296
# 132 GB GPU, 8 GB CPU, 4 GB pinned
```

#### 4.1.3 nv_trt_llm_kv_cache_block_metrics
- **Type**: Gauge
- **Description**: TRT LLM KV cache block utilization metrics
- **Labels**: `model`, `version`, `kv_cache_block_type`

**KV Cache Block Types:**
- `max_blocks`: Maximum available KV cache blocks
- `free_blocks`: Currently free KV cache blocks
- `used_blocks`: Currently used KV cache blocks
- `tokens_per_block`: Number of tokens per cache block
- `free_num_blocks`: Alternative naming for free blocks
- `used_num_blocks`: Alternative naming for used blocks
- `max_num_blocks`: Alternative naming for max blocks

**Example:**
```prometheus
nv_trt_llm_kv_cache_block_metrics{model="gpt-neo-2.7b",version="1",kv_cache_block_type="max_blocks"} 2048
nv_trt_llm_kv_cache_block_metrics{model="gpt-neo-2.7b",version="1",kv_cache_block_type="free_blocks"} 1523
nv_trt_llm_kv_cache_block_metrics{model="gpt-neo-2.7b",version="1",kv_cache_block_type="used_blocks"} 525
nv_trt_llm_kv_cache_block_metrics{model="gpt-neo-2.7b",version="1",kv_cache_block_type="tokens_per_block"} 64
# KV cache utilization = 525 / 2048 = 25.6%
```

**Critical for LLM Performance:**
- Running out of KV cache blocks → requests rejected
- Monitor `free_blocks` to prevent OOM
- Tune `max_blocks` based on workload

#### 4.1.4 nv_trt_llm_inflight_batcher_metrics
- **Type**: Gauge
- **Description**: TRT LLM inflight batching metrics
- **Labels**: `model`, `version`, `inflight_batcher_specific_metric`

**Metric Types:**
- `micro_batch_id`: Current micro-batch identifier
- `generation_requests`: Number of active generation requests
- `total_context_tokens`: Total tokens in context phase
- `total_generation_tokens`: Total tokens being generated
- `empty_generation_slots`: Available generation slots

**Example:**
```prometheus
nv_trt_llm_inflight_batcher_metrics{model="llama-2-13b",version="1",inflight_batcher_specific_metric="generation_requests"} 12
nv_trt_llm_inflight_batcher_metrics{model="llama-2-13b",version="1",inflight_batcher_specific_metric="total_context_tokens"} 8456
nv_trt_llm_inflight_batcher_metrics{model="llama-2-13b",version="1",inflight_batcher_specific_metric="total_generation_tokens"} 15234
nv_trt_llm_inflight_batcher_metrics{model="llama-2-13b",version="1",inflight_batcher_specific_metric="empty_generation_slots"} 52
```

**Inflight Batching:**
- Continuous batching technique for LLMs
- Allows joining/leaving batch mid-generation
- Maximizes GPU utilization for variable-length outputs

#### 4.1.5 nv_trt_llm_general_metrics
- **Type**: Gauge
- **Description**: General TRT LLM metrics
- **Labels**: `model`, `version`, `general_type`

**General Types:**
- `iteration_counter`: Number of batch iterations completed
- `timestamp`: Current timestamp

**Example:**
```prometheus
nv_trt_llm_general_metrics{model="falcon-40b",version="1",general_type="iteration_counter"} 15678
nv_trt_llm_general_metrics{model="falcon-40b",version="1",general_type="timestamp"} 1730678400
```

#### 4.1.6 nv_trt_llm_disaggregated_serving_metrics
- **Type**: Gauge
- **Description**: Metrics for disaggregated serving architecture
- **Labels**: `model`, `version`, `disaggregated_serving_type`

**Disaggregated Serving:**
- Separate context (prefill) and generation nodes
- KV cache transfer between nodes

**Metric Types:**
- `kv_cache_transfer_time_ms`: Time to transfer KV cache
- `request_count`: Requests in disaggregated mode

**Example:**
```prometheus
nv_trt_llm_disaggregated_serving_metrics{model="llama-2-70b",version="1",disaggregated_serving_type="kv_cache_transfer_time_ms"} 45.3
nv_trt_llm_disaggregated_serving_metrics{model="llama-2-70b",version="1",disaggregated_serving_type="request_count"} 234
```

### 4.2 vLLM Backend Metrics

**Status:** Uses custom metrics API
**Prefix:** Likely `nv_vllm_` (specific metrics not fully documented in search results)
**Note:** vLLM backend exposes LLM-specific metrics similar to TensorRT-LLM but with vLLM's architecture

**Expected Metrics (based on vLLM architecture):**
- Request queue depth
- KV cache utilization (PagedAttention blocks)
- Batch size metrics
- Token generation rate
- Context phase vs. generation phase timing

**Documentation:** https://github.com/triton-inference-server/vllm_backend#triton-metrics

### 4.3 Custom Metrics via C API

Triton exposes a **C API** for backends and users to register custom metrics:

**API Functions (conceptual):**
```c
// Register a new metric family
void TRITONSERVER_MetricFamilyNew(
    TRITONSERVER_MetricFamily** family,
    enum TRITONSERVER_MetricKind kind,  // GAUGE, COUNTER, HISTOGRAM, SUMMARY
    const char* name,
    const char* description
);

// Create a metric instance with labels
void TRITONSERVER_MetricNew(
    TRITONSERVER_Metric** metric,
    TRITONSERVER_MetricFamily* family,
    const char** label_keys,
    const char** label_values
);

// Update metric value
void TRITONSERVER_MetricIncrement(TRITONSERVER_Metric* metric, double value);
void TRITONSERVER_MetricSet(TRITONSERVER_Metric* metric, double value);
```

**Use Cases:**
- Backend-specific metrics (TensorRT-LLM, vLLM)
- Model-specific performance counters
- Custom business logic metrics
- Framework-specific profiling data

---

## 5. Integration Patterns

### 5.1 Prometheus Integration

#### Basic Scrape Configuration

**prometheus.yml:**
```yaml
scrape_configs:
  - job_name: 'triton'
    scrape_interval: 15s
    static_configs:
      - targets: ['triton-server:8002']
    metric_relabel_configs:
      # Keep only Triton metrics
      - source_labels: [__name__]
        regex: 'nv_.*'
        action: keep
```

#### Kubernetes PodMonitor

**For Kubernetes deployments:**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: triton-metrics
  namespace: inference
spec:
  selector:
    matchLabels:
      app: triton-inference-server
  podMetricsEndpoints:
    - port: metrics
      path: /metrics
      interval: 30s
      scrapeTimeout: 10s
```

### 5.2 Grafana Dashboard Patterns

#### Key Panel Queries

**Request Rate per Model:**
```promql
rate(nv_inference_request_success{model=~"$model"}[5m])
```

**Error Rate Percentage:**
```promql
(
  rate(nv_inference_request_failure{model=~"$model"}[5m]) /
  (rate(nv_inference_request_success{model=~"$model"}[5m]) +
   rate(nv_inference_request_failure{model=~"$model"}[5m]))
) * 100
```

**Average Request Latency:**
```promql
rate(nv_inference_request_duration_us{model=~"$model"}[5m]) /
rate(nv_inference_request_success{model=~"$model"}[5m]) / 1000
```

**Average Batch Size:**
```promql
rate(nv_inference_count{model=~"$model"}[5m]) /
rate(nv_inference_exec_count{model=~"$model"}[5m])
```

**Queue Time Ratio:**
```promql
rate(nv_inference_queue_duration_us{model=~"$model"}[5m]) /
rate(nv_inference_request_duration_us{model=~"$model"}[5m])
```

**GPU Memory Utilization:**
```promql
(nv_gpu_memory_used_bytes / nv_gpu_memory_total_bytes) * 100
```

**KV Cache Utilization (TensorRT-LLM):**
```promql
(
  nv_trt_llm_kv_cache_block_metrics{kv_cache_block_type="used_blocks"} /
  nv_trt_llm_kv_cache_block_metrics{kv_cache_block_type="max_blocks"}
) * 100
```

### 5.3 Alerting Rules

**High Error Rate:**
```yaml
- alert: TritonHighErrorRate
  expr: |
    (
      rate(nv_inference_request_failure[5m]) /
      (rate(nv_inference_request_success[5m]) + rate(nv_inference_request_failure[5m]))
    ) > 0.05
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High error rate on Triton model {{ $labels.model }}"
    description: "Error rate is {{ $value | humanizePercentage }} on model {{ $labels.model }}"
```

**High Queue Time:**
```yaml
- alert: TritonHighQueueTime
  expr: |
    (
      rate(nv_inference_queue_duration_us[5m]) /
      rate(nv_inference_request_success[5m])
    ) > 100000  # 100ms average queue time
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High queue time for model {{ $labels.model }}"
    description: "Average queue time is {{ $value | humanize }}µs"
```

**GPU Memory Pressure:**
```yaml
- alert: TritonGPUMemoryPressure
  expr: |
    (nv_gpu_memory_used_bytes / nv_gpu_memory_total_bytes) > 0.90
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "GPU memory usage above 90% on {{ $labels.gpu_uuid }}"
```

**KV Cache Exhaustion (TensorRT-LLM):**
```yaml
- alert: TritonKVCacheExhaustion
  expr: |
    (
      nv_trt_llm_kv_cache_block_metrics{kv_cache_block_type="free_blocks"} /
      nv_trt_llm_kv_cache_block_metrics{kv_cache_block_type="max_blocks"}
    ) < 0.10
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "KV cache nearly exhausted for model {{ $labels.model }}"
    description: "Only {{ $value | humanizePercentage }} free KV cache blocks remaining"
```

### 5.4 Autoscaling Integration

#### Horizontal Pod Autoscaler (HPA)

**Custom Metric: Queue-to-Compute Ratio**

This metric is commonly used for autoscaling decisions:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: triton-hpa
  namespace: inference
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: triton-inference-server
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Pods
      pods:
        metric:
          name: triton_queue_compute_ratio
        target:
          type: AverageValue
          averageValue: "100m"  # Scale when ratio > 0.1
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
```

**Queue-to-Compute Ratio Calculation:**
```promql
sum(rate(nv_inference_queue_duration_us{model="$model"}[2m])) /
sum(rate(nv_inference_compute_infer_duration_us{model="$model"}[2m]))
```

**Interpretation:**
- `ratio < 0.1`: Underutilized, can scale down
- `ratio = 0.1-0.5`: Optimal utilization
- `ratio > 0.5`: Overloaded, scale up

#### KEDA (Kubernetes Event-Driven Autoscaling)

**Prometheus-based KEDA ScaledObject:**
```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: triton-scaledobject
  namespace: inference
spec:
  scaleTargetRef:
    name: triton-inference-server
  minReplicaCount: 1
  maxReplicaCount: 50
  triggers:
    - type: prometheus
      metadata:
        serverAddress: http://prometheus:9090
        metricName: triton_pending_requests
        query: |
          sum(nv_inference_pending_request_count{model="llama-2-70b"})
        threshold: "10"
```

---

## 6. Production Deployment Patterns

### 6.1 Multi-GPU Monitoring

**Challenge:** Multiple GPUs require aggregation strategies

**Pattern 1: Sum Across GPUs**
```promql
# Total GPU memory used across all GPUs
sum(nv_gpu_memory_used_bytes)

# Average GPU utilization
avg(nv_gpu_utilization)
```

**Pattern 2: Per-GPU Tracking**
```promql
# Memory usage by GPU
nv_gpu_memory_used_bytes{gpu_uuid=~".*"}

# Identify hotspots
topk(3, nv_gpu_utilization)
```

### 6.2 Multi-Model Monitoring

**Dashboard Variables:**
```
$model = label_values(nv_inference_request_success, model)
$version = label_values(nv_inference_request_success{model="$model"}, version)
```

**Model Comparison:**
```promql
# Latency comparison across models
avg by (model) (
  rate(nv_inference_request_duration_us[5m]) /
  rate(nv_inference_request_success[5m])
)
```

### 6.3 Dynamic Batching Monitoring

**Key Metrics:**
- `nv_inference_count` / `nv_inference_exec_count` → Average batch size
- `nv_inference_queue_duration_us` → Queue wait time
- `nv_inference_pending_request_count` → Current queue depth

**Optimal Batching Dashboard:**
```promql
# Actual average batch size
rate(nv_inference_count{model="$model"}[5m]) /
rate(nv_inference_exec_count{model="$model"}[5m])

# Queue depth
nv_inference_pending_request_count{model="$model"}

# Time spent waiting vs. computing
sum(rate(nv_inference_queue_duration_us{model="$model"}[5m])) /
sum(rate(nv_inference_compute_infer_duration_us{model="$model"}[5m]))
```

**Tuning Guide:**
- **High queue time, low batch size** → Increase `max_batch_size` or `preferred_batch_size`
- **Low queue time, low batch size** → Decrease `max_queue_delay_microseconds`
- **High queue time, high batch size** → Add more model instances or GPU resources

### 6.4 LLM-Specific Monitoring

**Critical Metrics for LLMs (TensorRT-LLM):**

1. **Time to First Token (TTFT)**
   ```promql
   histogram_quantile(0.95,
     rate(nv_inference_first_response_histogram_ms_bucket{model="$llm"}[5m])
   )
   ```

2. **KV Cache Utilization**
   ```promql
   (
     nv_trt_llm_kv_cache_block_metrics{kv_cache_block_type="used_blocks"} /
     nv_trt_llm_kv_cache_block_metrics{kv_cache_block_type="max_blocks"}
   ) * 100
   ```

3. **Active vs. Waiting Requests**
   ```promql
   # Active
   nv_trt_llm_request_metrics{request_type="active"}

   # Waiting
   nv_trt_llm_request_metrics{request_type="waiting"}

   # Capacity
   nv_trt_llm_request_metrics{request_type="max"}
   ```

4. **Token Generation Rate**
   ```promql
   nv_trt_llm_inflight_batcher_metrics{inflight_batcher_specific_metric="total_generation_tokens"}
   ```

5. **Context vs. Generation Phase Ratio**
   ```promql
   nv_trt_llm_request_metrics{request_type="context"} /
   nv_trt_llm_request_metrics{request_type="scheduled"}
   ```

### 6.5 Cost Optimization Monitoring

**Metrics for Cost Analysis:**

1. **Inference per Dollar (GPU efficiency)**
   ```promql
   # Inferences per watt-hour
   rate(nv_inference_count[1h]) /
   (rate(nv_energy_consumption[1h]) / 3600)
   ```

2. **Idle GPU Detection**
   ```promql
   # GPUs with <10% utilization for >5 minutes
   nv_gpu_utilization < 0.1 for 5m
   ```

3. **Batch Efficiency**
   ```promql
   # Higher is better (more batching = more efficient)
   rate(nv_inference_count[5m]) /
   rate(nv_inference_exec_count[5m])
   ```

4. **Resource Waste (High Queue + Low Utilization)**
   ```promql
   # Detect configuration issues
   (nv_inference_pending_request_count > 10) and
   (nv_gpu_utilization < 0.5)
   ```

---

## 7. Comparison with FakeAI Metrics

### 7.1 Current FakeAI Metrics

**FakeAI Prefix:** `fakeai_`

**Existing Metrics:**
1. `fakeai_requests_per_second` - Request rate per endpoint
2. `fakeai_responses_per_second` - Response rate per endpoint
3. `fakeai_latency_seconds` - Response latency (summary with quantiles)
4. `fakeai_tokens_per_second` - Token generation rate
5. `fakeai_errors_per_second` - Error rate per endpoint
6. `fakeai_active_streams` - Active streaming connections
7. `fakeai_completed_streams` - Total completed streams
8. `fakeai_failed_streams` - Total failed streams
9. `fakeai_ttft_seconds` - Time to first token (summary)
10. `fakeai_stream_tokens_per_second` - Streaming token rate (summary)

**Labels:**
- `endpoint` - API endpoint path
- `quantile` - For summary metrics (0.5, 0.9, 0.99)

### 7.2 Triton vs. FakeAI Metric Comparison

| Feature | Triton | FakeAI | Gap |
|---------|--------|--------|-----|
| **Request Metrics** | Per-model, per-version | Per-endpoint | FakeAI lacks model/version labels |
| **Latency Breakdown** | Queue, Input, Compute, Output | Single total latency | FakeAI lacks component breakdown |
| **Batch Metrics** | Inference count, exec count, batch size | N/A | FakeAI doesn't track batching |
| **GPU Metrics** | Power, utilization, memory (via DCGM) | N/A | FakeAI is CPU-only |
| **Cache Metrics** | Hit/miss rates, durations | N/A | FakeAI doesn't simulate caching |
| **Streaming Metrics** | TTFT histogram, first response time | TTFT summary, active streams | Similar coverage |
| **Backend Metrics** | TensorRT-LLM, vLLM specifics | N/A | FakeAI lacks backend concept |
| **Custom Metrics** | C API for extensions | Python singleton | Different patterns |

### 7.3 Compatibility Assessment

**Can FakeAI Emit Triton-Compatible Metrics?**

**YES - With Modifications:**

1. **Easy Additions:**
   - Add `model` and `version` labels to existing metrics
   - Rename metrics to use `nv_inference_` prefix
   - Add batch size tracking (inferences vs. executions)
   - Add latency breakdown (queue, compute input/output)

2. **Medium Complexity:**
   - Implement response cache simulation with hit/miss metrics
   - Add pending request count gauge
   - Create histogram for TTFT (currently summary)

3. **Not Applicable (Simulation Limitations):**
   - Real GPU metrics (power, memory, utilization) - FakeAI is CPU-based
   - Backend-specific metrics (TensorRT-LLM, vLLM) - No real backends
   - DCGM integration - Requires NVIDIA hardware

### 7.4 Proposed Triton-Compatible Mode for FakeAI

**New Configuration Option:**
```python
class AppConfig(BaseSettings):
    # ... existing fields

    # Triton compatibility mode
    triton_metrics_mode: bool = False
    triton_metrics_prefix: str = "nv_inference_"

    # Model/version support
    default_model_name: str = "fakeai-model"
    default_model_version: str = "1"
```

**Metric Mapping in Triton Mode:**

| Triton Metric | FakeAI Equivalent | Implementation |
|---------------|-------------------|----------------|
| `nv_inference_request_success` | `fakeai_requests_per_second` | Counter, add model/version labels |
| `nv_inference_request_failure` | `fakeai_errors_per_second` | Counter, add model/version labels |
| `nv_inference_count` | New | Track individual inferences in batch |
| `nv_inference_exec_count` | New | Track batch executions |
| `nv_inference_pending_request_count` | New | Track queue depth |
| `nv_inference_request_duration_us` | `fakeai_latency_seconds * 1e6` | Convert to microseconds |
| `nv_inference_queue_duration_us` | New | Track queue component |
| `nv_inference_compute_infer_duration_us` | New | Track compute component |
| `nv_inference_first_response_histogram_ms` | `fakeai_ttft_seconds * 1000` | Convert to histogram |
| `nv_cache_num_hits_per_model` | New | Simulate cache |
| `nv_cache_num_misses_per_model` | New | Simulate cache |

**GPU Metrics Simulation Strategy:**

Since FakeAI runs on CPU, simulate realistic GPU metrics:

```python
# Simulate GPU metrics based on model complexity
nv_gpu_utilization = min(0.95, request_rate * avg_compute_time / gpu_capacity)
nv_gpu_memory_used_bytes = loaded_models_memory + active_kv_cache_memory
nv_gpu_power_usage = base_power + (peak_power - base_power) * nv_gpu_utilization
```

---

## 8. Implementation Recommendations

### 8.1 Immediate Opportunities

**High Value, Low Effort:**

1. **Add Model/Version Labels**
   - Extend metrics to include `model` and `version` labels
   - Extract from request parameters
   - Enable per-model tracking

2. **Implement Latency Breakdown**
   - Split total latency into queue, compute, and overhead
   - Track queue depth as gauge
   - Provides insight into bottlenecks

3. **Add Batch Metrics**
   - Track `inference_count` (individual inferences)
   - Track `exec_count` (batch executions)
   - Calculate average batch size

4. **Rename Metrics in Triton Mode**
   - Configurable prefix (`fakeai_` or `nv_inference_`)
   - Maintain backward compatibility
   - Enable Triton dashboard compatibility

### 8.2 Medium-Term Enhancements

**Moderate Effort, High Value:**

1. **Response Cache Simulation**
   - Implement in-memory LRU cache for responses
   - Track hit/miss rates
   - Add cache-specific latency metrics

2. **TTFT Histogram**
   - Convert TTFT from summary to histogram
   - Configurable buckets
   - Better Prometheus compatibility

3. **Simulated GPU Metrics**
   - Calculate "virtual GPU" utilization based on load
   - Simulate memory usage based on model sizes
   - Provide realistic power metrics

4. **Backend-Specific Metrics (Optional)**
   - Simulate TensorRT-LLM-like metrics
   - KV cache block tracking (simulated)
   - Inflight batching metrics

### 8.3 Advanced Features

**High Effort, Niche Value:**

1. **Full Triton Metrics API Compatibility**
   - Implement all Triton metric types
   - Match label schemas exactly
   - Enable drop-in Grafana dashboard compatibility

2. **Custom Metrics API**
   - Python decorator for custom metrics
   - Allow users to register metrics programmatically
   - Similar to Triton C API pattern

3. **Multi-Model Instance Simulation**
   - Simulate multiple model versions
   - Instance-level metrics
   - Model repository simulation

### 8.4 Recommended Implementation Order

**Phase 1: Basic Triton Compatibility (1-2 days)**
- Add `triton_metrics_mode` config flag
- Add `model` and `version` labels to existing metrics
- Rename metrics to `nv_inference_*` prefix in Triton mode
- Add `nv_inference_pending_request_count` gauge

**Phase 2: Latency and Batch Metrics (2-3 days)**
- Split latency into components (queue, compute, overhead)
- Add `nv_inference_count` and `nv_inference_exec_count`
- Implement batch size tracking
- Add latency breakdown metrics

**Phase 3: Advanced Features (1 week)**
- Implement response cache simulation
- Convert TTFT to histogram
- Add simulated GPU metrics
- Create Grafana dashboard examples

**Phase 4: Optional Enhancements (1-2 weeks)**
- Backend-specific metric simulation (TensorRT-LLM, vLLM)
- Custom metrics API
- Multi-model instance support
- Full documentation and examples

### 8.5 Code Example: Triton Mode Metric

**Example implementation for `MetricsTracker` class:**

```python
class MetricsTracker:
    def __init__(self, config: AppConfig):
        self.config = config
        self.triton_mode = config.triton_metrics_mode

        if self.triton_mode:
            self.metric_prefix = config.triton_metrics_prefix
            # Track additional Triton-specific metrics
            self._pending_requests = defaultdict(int)
            self._inference_counts = defaultdict(lambda: {"inferences": 0, "executions": 0})
        else:
            self.metric_prefix = "fakeai_"

    def track_request(self, endpoint: str, model: str = None, version: str = None):
        """Track request with optional model/version labels."""
        if self.triton_mode and model:
            # Track in Triton format
            self._pending_requests[(model, version)] += 1
            self._metrics[MetricType.REQUESTS][(endpoint, model, version)].add()
        else:
            # Track in FakeAI format
            self._metrics[MetricType.REQUESTS][endpoint].add()

    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []

        if self.triton_mode:
            # Export Triton-style metrics
            lines.append(f"# HELP {self.metric_prefix}request_success Number of successful inference requests")
            lines.append(f"# TYPE {self.metric_prefix}request_success counter")

            for (endpoint, model, version), window in self._metrics[MetricType.REQUESTS].items():
                count = window.get_stats()["rate"] * 5  # Convert rate to count
                lines.append(
                    f'{self.metric_prefix}request_success{{model="{model}",version="{version}"}} {count:.0f}'
                )

            # Pending requests gauge
            lines.append(f"# HELP {self.metric_prefix}pending_request_count Pending requests")
            lines.append(f"# TYPE {self.metric_prefix}pending_request_count gauge")
            for (model, version), count in self._pending_requests.items():
                lines.append(
                    f'{self.metric_prefix}pending_request_count{{model="{model}",version="{version}"}} {count}'
                )
        else:
            # Export FakeAI-style metrics (existing implementation)
            lines.append(f"# HELP {self.metric_prefix}requests_per_second Request rate per endpoint")
            # ... existing code

        return "\n".join(lines) + "\n"
```

### 8.6 Testing Strategy

**Unit Tests:**
```python
def test_triton_metrics_mode():
    """Test Triton-compatible metrics output."""
    config = AppConfig(triton_metrics_mode=True)
    tracker = MetricsTracker(config)

    # Track request with model/version
    tracker.track_request("/v1/models/test/infer", model="bert-base", version="1")

    # Get Prometheus output
    metrics = tracker.get_prometheus_metrics()

    # Assert Triton format
    assert 'nv_inference_request_success{model="bert-base",version="1"}' in metrics
    assert 'nv_inference_pending_request_count{model="bert-base",version="1"}' in metrics

def test_latency_breakdown():
    """Test latency component tracking."""
    tracker = MetricsTracker(config)

    request_id = tracker.start_request_timer(endpoint, model="openai/gpt-oss-120b", version="1")

    # Simulate queue time
    time.sleep(0.01)
    tracker.track_queue_exit(request_id)

    # Simulate compute time
    time.sleep(0.05)
    tracker.end_request_timer(endpoint, request_id)

    # Assert breakdown
    metrics = tracker.get_metrics()
    assert metrics["queue_latency"]["openai/gpt-oss-120b"]["avg"] > 0
    assert metrics["compute_latency"]["openai/gpt-oss-120b"]["avg"] > 0
```

**Integration Tests:**
```python
@pytest.mark.asyncio
async def test_triton_compatible_endpoint():
    """Test API with Triton-style model inference."""
    app = create_app(config=AppConfig(triton_metrics_mode=True))
    client = TestClient(app)

    # Make inference request
    response = client.post(
        "/v1/models/bert-base/versions/1/infer",
        json={"inputs": [{"name": "text", "data": ["test"]}]}
    )

    assert response.status_code == 200

    # Check metrics endpoint
    metrics_response = client.get("/metrics")
    assert 'nv_inference_request_success{model="bert-base",version="1"}' in metrics_response.text
```

---

## Appendix A: Metric Quick Reference

### Core Inference Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `nv_inference_request_success` | Counter | model, version | Successful requests |
| `nv_inference_request_failure` | Counter | model, version | Failed requests |
| `nv_inference_count` | Counter | model, version | Individual inferences |
| `nv_inference_exec_count` | Counter | model, version | Batch executions |
| `nv_inference_pending_request_count` | Gauge | model, version | Queue depth |
| `nv_inference_request_duration_us` | Counter/Summary | model, version | Total latency (µs) |
| `nv_inference_queue_duration_us` | Counter | model, version | Queue time (µs) |
| `nv_inference_compute_input_duration_us` | Counter | model, version | Input processing (µs) |
| `nv_inference_compute_infer_duration_us` | Counter | model, version | Model execution (µs) |
| `nv_inference_compute_output_duration_us` | Counter | model, version | Output processing (µs) |
| `nv_inference_first_response_histogram_ms` | Histogram | model, version | TTFT (ms) |

### GPU Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `nv_gpu_utilization` | Gauge | gpu_uuid | GPU utilization (0-1) |
| `nv_gpu_memory_total_bytes` | Gauge | gpu_uuid | Total GPU memory |
| `nv_gpu_memory_used_bytes` | Gauge | gpu_uuid | Used GPU memory |
| `nv_gpu_power_usage` | Gauge | gpu_uuid | Power usage (watts) |
| `nv_gpu_power_limit` | Gauge | gpu_uuid | Power limit (watts) |
| `nv_energy_consumption` | Counter | gpu_uuid | Energy consumed (joules) |

### TensorRT-LLM Metrics

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `nv_trt_llm_request_metrics` | Gauge | model, version, request_type | Request states |
| `nv_trt_llm_runtime_memory_metrics` | Gauge | model, version, memory_type | Memory usage |
| `nv_trt_llm_kv_cache_block_metrics` | Gauge | model, version, kv_cache_block_type | KV cache blocks |
| `nv_trt_llm_inflight_batcher_metrics` | Gauge | model, version, inflight_batcher_specific_metric | Batching stats |

---

## Appendix B: Useful PromQL Queries

### Performance Analysis

**Average Request Latency by Model:**
```promql
rate(nv_inference_request_duration_us[5m]) /
rate(nv_inference_request_success[5m]) / 1000
```

**P95 Queue Time:**
```promql
histogram_quantile(0.95, rate(nv_inference_queue_duration_us_bucket[5m]))
```

**Batch Size Over Time:**
```promql
rate(nv_inference_count{model="openai/gpt-oss-120b"}[5m]) /
rate(nv_inference_exec_count{model="openai/gpt-oss-120b"}[5m])
```

### Capacity Planning

**Requests per GPU:**
```promql
sum(rate(nv_inference_request_success[5m])) /
count(nv_gpu_utilization)
```

**Memory Headroom:**
```promql
(nv_gpu_memory_total_bytes - nv_gpu_memory_used_bytes) / 1024 / 1024 / 1024
```

**KV Cache Remaining:**
```promql
nv_trt_llm_kv_cache_block_metrics{kv_cache_block_type="free_blocks"}
```

### Cost Optimization

**Inferences per Watt-Hour:**
```promql
rate(nv_inference_count[1h]) /
(rate(nv_energy_consumption[1h]) / 3600)
```

**Cost per 1M Inferences (assuming $0.10/kWh):**
```promql
(
  (rate(nv_energy_consumption[1h]) / 3600 / 1000) * 0.10
) / (rate(nv_inference_count[1h]) / 1000000)
```

---

## Appendix C: References

### Official Documentation

- **Triton Metrics Documentation**: https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/metrics.html
- **TensorRT-LLM Backend**: https://github.com/triton-inference-server/tensorrtllm_backend
- **vLLM Backend**: https://github.com/triton-inference-server/vllm_backend
- **Triton Server GitHub**: https://github.com/triton-inference-server/server

### Community Resources

- **AWS Hyperscale Triton Guide**: https://aws.amazon.com/blogs/machine-learning/achieve-hyperscale-performance-for-model-serving-using-nvidia-triton-inference-server-on-amazon-sagemaker/
- **Google Cloud Triton Monitoring**: https://medium.com/google-cloud/use-google-managed-prometheus-and-triton-inference-server-to-simplify-llm-observability-and-b93fb42342c2
- **SoftwareMill Triton Tutorial**: https://softwaremill.com/triton-inference-server/

### Related Tools

- **Prometheus**: https://prometheus.io/
- **Grafana**: https://grafana.com/
- **NVIDIA DCGM**: https://developer.nvidia.com/dcgm
- **KEDA**: https://keda.sh/

---

**Document Version:** 1.0
**Last Updated:** 2025-10-04
**Author:** AI Research Assistant
**Status:** Complete - Ready for FakeAI Integration Planning
