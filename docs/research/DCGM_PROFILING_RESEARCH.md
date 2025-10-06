# NVIDIA DCGM Profiling and Performance Metrics Research

**Version:** 1.0
**Date:** 2025-10-04
**Purpose:** Comprehensive research on NVIDIA DCGM profiling mode, performance metrics, and implementation patterns for GPU monitoring

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [DCGM Overview](#dcgm-overview)
3. [Profiling vs Monitoring Modes](#profiling-vs-monitoring-modes)
4. [Complete Profiling Metrics Reference](#complete-profiling-metrics-reference)
5. [Metric Groups and Multiplexing](#metric-groups-and-multiplexing)
6. [Performance Counter Details](#performance-counter-details)
7. [Calculating Derived Metrics](#calculating-derived-metrics)
8. [API Implementation Patterns](#api-implementation-patterns)
9. [LLM Inference Best Practices](#llm-inference-best-practices)
10. [Implementation Recommendations](#implementation-recommendations)

---

## 1. Executive Summary

NVIDIA Data Center GPU Manager (DCGM) provides two distinct modes for GPU monitoring:

1. **Monitoring Mode (Default)**: Basic GPU health and utilization metrics with low overhead
2. **Profiling Mode**: Fine-grained performance counters for detailed analysis with higher overhead

This document focuses on **profiling mode**, which provides detailed metrics for:
- SM (Streaming Multiprocessor) occupancy and efficiency
- Tensor Core utilization
- Memory bandwidth utilization
- PCIe and NVLink bandwidth
- Instruction throughput and FLOPS
- Pipeline activity across different data types

**Key Findings:**
- Profiling metrics use field IDs 1001-1012 with `DCGM_FI_PROF_` prefix
- Metrics are organized into groups (A, B, C, D, E) with multiplexing requirements
- DCGM automatically handles multiplexing through statistical sampling
- Some metric combinations cannot be collected simultaneously without multiplexing
- Profiling mode conflicts with Nsight tools on A100 and earlier GPUs

---

## 2. DCGM Overview

### 2.1 What is DCGM?

NVIDIA DCGM is a low-overhead, production-grade tool for:
- Active health monitoring of GPUs
- Performance diagnostics and validation
- Policy-based power and clock management
- Accounting and telemetry collection

### 2.2 Key Characteristics

- **Low Overhead**: Designed for continuous monitoring without impacting workloads
- **Production Ready**: Used in data centers for 24/7 monitoring
- **Non-Invasive**: Does not interfere with application behavior
- **Flexible**: Supports C, Python, and Go APIs
- **Scalable**: Can monitor single GPUs or entire clusters

### 2.3 Architecture

```

       Application / Client              
   (dcgmi CLI, Python, Go, C API)       

                   

          DCGM Service Layer             
  (Field Groups, Metrics Collection)     

                   

        NVIDIA Driver / NVML             
   (Performance Counters, Telemetry)     

                   

           GPU Hardware                  
   (Performance Monitoring Units)        

```

### 2.4 Version Compatibility

- **DCGM 3.1 - 3.3.9**: Compatible with most integrations
- **Field ID Format**: Numeric (1001-1012) or symbolic (`DCGM_FI_PROF_*`)
- **GPU Support**: Profiling not available on P100 and P4
- **Enhanced Support**: H100 and newer GPUs support all profiling features

---

## 3. Profiling vs Monitoring Modes

### 3.1 Monitoring Mode (Version 2 Receiver)

**Purpose**: Continuous health and utilization monitoring

**Metrics Include**:
- GPU utilization percentage
- Memory usage (used/free/total)
- Power consumption
- Temperature
- Clock speeds (SM, memory)
- PCIe replay counter
- ECC errors
- Throttling reasons

**Characteristics**:
- Very low overhead (< 1% CPU)
- Safe for production use
- Default sampling rate: 1Hz (1000ms)
- No conflicts with other tools
- Can run 24/7

**Field ID Range**: 1-999 (non-profiling fields)

### 3.2 Profiling Mode (Version 1 Receiver)

**Purpose**: Fine-grained performance analysis

**Metrics Include**:
- SM occupancy and active ratios
- Tensor Core utilization
- FP64, FP32, FP16 pipeline activity
- DRAM active ratio
- Graphics engine activity
- PCIe TX/RX bandwidth
- NVLink TX/RX bandwidth

**Characteristics**:
- Higher overhead (1-5% CPU depending on metrics)
- Recommended for analysis/debugging
- Default sampling rate: 1Hz (minimum 100ms)
- May conflict with Nsight tools (A100 and earlier)
- Requires multiplexing for some metric combinations

**Field ID Range**: 1001-1012 (profiling fields)

### 3.3 Key Differences

| Aspect | Monitoring Mode | Profiling Mode |
|--------|----------------|----------------|
| **Overhead** | < 1% | 1-5% |
| **Granularity** | Coarse (GPU-level) | Fine (SM/pipe-level) |
| **Sampling Rate** | 1Hz default | 1Hz default, 100ms min |
| **Production Use** | Always safe | Use cautiously |
| **Tool Conflicts** | None | Nsight (A100 and earlier) |
| **Multiplexing** | Not required | May be required |
| **GPU Support** | All GPUs | Not on P100/P4 |
| **Use Case** | Health monitoring | Performance tuning |

### 3.4 When to Use Each Mode

**Use Monitoring Mode When**:
- Monitoring production workloads
- Tracking GPU health 24/7
- Detecting hardware issues
- Resource utilization tracking
- Power/thermal management

**Use Profiling Mode When**:
- Analyzing workload performance
- Identifying bottlenecks
- Optimizing kernel efficiency
- Measuring Tensor Core usage
- Debugging performance issues
- Benchmarking inference/training

---

## 4. Complete Profiling Metrics Reference

### 4.1 All DCGM Profiling Field IDs (1001-1012)

| Field ID | Symbolic Name | Description | Data Type | Unit |
|----------|--------------|-------------|-----------|------|
| 1001 | DCGM_FI_PROF_GR_ENGINE_ACTIVE | Graphics engine active ratio | Double | % |
| 1002 | DCGM_FI_PROF_SM_ACTIVE | SM active ratio | Double | % |
| 1003 | DCGM_FI_PROF_SM_OCCUPANCY | SM occupancy ratio | Double | % |
| 1004 | DCGM_FI_PROF_PIPE_TENSOR_ACTIVE | Tensor pipe active ratio | Double | % |
| 1005 | DCGM_FI_PROF_DRAM_ACTIVE | DRAM active ratio | Double | % |
| 1006 | DCGM_FI_PROF_PIPE_FP64_ACTIVE | FP64 pipe active ratio | Double | % |
| 1007 | DCGM_FI_PROF_PIPE_FP32_ACTIVE | FP32 pipe active ratio | Double | % |
| 1008 | DCGM_FI_PROF_PIPE_FP16_ACTIVE | FP16 pipe active ratio | Double | % |
| 1009 | DCGM_FI_PROF_PCIE_TX_BYTES | PCIe TX bytes | Int64 | bytes |
| 1010 | DCGM_FI_PROF_PCIE_RX_BYTES | PCIe RX bytes | Int64 | bytes |
| 1011 | DCGM_FI_PROF_NVLINK_TX_BYTES | NVLink TX bytes | Int64 | bytes |
| 1012 | DCGM_FI_PROF_NVLINK_RX_BYTES | NVLink RX bytes | Int64 | bytes |

### 4.2 Detailed Metric Descriptions

#### 4.2.1 SM Metrics

**DCGM_FI_PROF_SM_ACTIVE (1002)**
- **Description**: The ratio of cycles an SM has at least 1 warp assigned
- **Interpretation**: Percentage of time at least one warp was active on an SM, averaged over all SMs
- **Example**: If GPU has 80 SMs and 16 were executing a warp, sm_active = 16/80 = 20%
- **Range**: 0-100%
- **Use Case**: Measure overall SM utilization

**DCGM_FI_PROF_SM_OCCUPANCY (1003)**
- **Description**: The ratio of number of warps resident on an SM
- **Interpretation**: Ratio of resident warps to theoretical maximum warps per elapsed cycle
- **Formula**: (Active Warps) / (Max Warps per SM × Number of SMs)
- **Range**: 0-100%
- **Use Case**: Identify if kernels achieve sufficient occupancy
- **Note**: High occupancy doesn't always mean high performance

#### 4.2.2 Tensor Core Metrics

**DCGM_FI_PROF_PIPE_TENSOR_ACTIVE (1004)**
- **Description**: Ratio of cycles the tensor (HMMA) pipe is active
- **Interpretation**: Percentage of time Tensor Cores are performing matrix operations
- **Range**: 0-100%
- **Use Case**: Critical for ML/AI workloads, measures Tensor Core efficiency
- **Note**: Modern LLM inference should show high tensor activity (> 80%)
- **Important**: Cannot be collected simultaneously with SM_ACTIVE/SM_OCCUPANCY on some GPUs

#### 4.2.3 Floating Point Pipeline Metrics

**DCGM_FI_PROF_PIPE_FP64_ACTIVE (1006)**
- **Description**: Ratio of cycles the FP64 (double precision) pipe is active
- **Range**: 0-100%
- **Use Case**: Scientific computing, high-precision simulations
- **Typical Workloads**: CFD, molecular dynamics, weather simulation

**DCGM_FI_PROF_PIPE_FP32_ACTIVE (1007)**
- **Description**: Ratio of cycles the FP32 (single precision) pipe is active
- **Range**: 0-100%
- **Use Case**: General computing, graphics, some ML training
- **Typical Workloads**: Rendering, traditional ML models

**DCGM_FI_PROF_PIPE_FP16_ACTIVE (1008)**
- **Description**: Ratio of cycles the FP16 (half precision) pipe is active
- **Note**: Does NOT include HMMA (Tensor Core) operations
- **Range**: 0-100%
- **Use Case**: Mixed precision training, inference optimization
- **Typical Workloads**: Modern ML training with automatic mixed precision

#### 4.2.4 Memory Metrics

**DCGM_FI_PROF_DRAM_ACTIVE (1005)**
- **Description**: The ratio of cycles the device memory interface is active sending or receiving data
- **Range**: 0-100%
- **Use Case**: Identify memory bandwidth bottlenecks
- **Interpretation**:
  - High DRAM activity + low SM activity = memory bound
  - Low DRAM activity + high SM activity = compute bound
- **Critical for**: LLM inference decoding phase (typically memory bound)

**DCGM_FI_PROF_GR_ENGINE_ACTIVE (1001)**
- **Description**: Ratio of time the graphics engine is active
- **Details**: Graphics engine is active if a graphics/compute context is bound and graphics pipe or compute pipe is busy
- **Range**: 0-100%
- **Use Case**: Overall GPU activity indicator

#### 4.2.5 Interconnect Bandwidth Metrics

**DCGM_FI_PROF_PCIE_TX_BYTES (1009)**
- **Description**: Number of bytes of active PCIe TX (transmit) data including header and payload
- **Perspective**: From GPU's perspective (GPU → Host)
- **Data Type**: Counter (cumulative)
- **Use Case**: Measure CPU-to-GPU bandwidth usage
- **Convert to Bandwidth**: (bytes_delta / time_delta) to get bytes/sec

**DCGM_FI_PROF_PCIE_RX_BYTES (1010)**
- **Description**: Number of bytes of active PCIe RX (receive) data including header and payload
- **Perspective**: From GPU's perspective (Host → GPU)
- **Example**: Copying data from host to device (HtoD) increases this metric
- **Data Type**: Counter (cumulative)
- **Use Case**: Identify data transfer bottlenecks

**DCGM_FI_PROF_NVLINK_TX_BYTES (1011)**
- **Description**: Number of bytes of active NVLink TX data including header and payload
- **Perspective**: GPU transmitting to other GPUs
- **Data Type**: Counter (cumulative)
- **Use Case**: Multi-GPU bandwidth utilization
- **Critical for**: Model parallelism, tensor parallelism

**DCGM_FI_PROF_NVLINK_RX_BYTES (1012)**
- **Description**: Number of bytes of active NVLink RX data including header and payload
- **Perspective**: GPU receiving from other GPUs
- **Data Type**: Counter (cumulative)
- **Use Case**: Multi-GPU communication patterns

---

## 5. Metric Groups and Multiplexing

### 5.1 What is Multiplexing?

**Definition**: Due to hardware limitations, not all profiling metrics can be collected simultaneously. Multiplexing is the process of time-sharing performance counters to collect multiple metrics.

**How DCGM Handles It**: DCGM automatically multiplexes metrics by statistically sampling requested metrics and performing groupings internally.

**Impact**: Metrics collected via multiplexing are averaged over multiple sampling periods, which may reduce precision but allows comprehensive monitoring.

### 5.2 Metric Groups by GPU Architecture

#### 5.2.1 NVIDIA T4 Metric Groups

```
Group A.1: sm_active, sm_occupancy, tensor_active, fp32_active
Group A.2: fp64_active
Group A.3: fp16_active
Group B.0: dram_active
Group C.0: pcie_tx_bytes, pcie_rx_bytes
Group D.0: gr_engine_active
Group E.0: nvlink_tx_bytes, nvlink_rx_bytes
```

**Collection Rules for T4**:
- Metrics from each letter group (A, B, C, D, E) can be collected together WITHOUT multiplexing
- Metrics within the same subgroup (e.g., A.1) can be collected together WITHOUT multiplexing
- Metrics from different subgroups within same letter (e.g., A.1 and A.2) REQUIRE multiplexing
- Example: `sm_active + dram_active + pcie_tx_bytes` = No multiplexing needed
- Example: `sm_active + fp64_active` = Multiplexing required (both in group A)

#### 5.2.2 NVIDIA V100 Metric Groups

```
Group A.1: sm_active, sm_occupancy
Group A.2: tensor_active
Group A.3: fp64_active
Group A.4: fp32_active
Group A.5: fp16_active
Group B.0: dram_active
Group C.0: pcie_tx_bytes, pcie_rx_bytes
Group D.0: gr_engine_active
Group E.0: nvlink_tx_bytes, nvlink_rx_bytes
```

**Key Difference from T4**:
- V100 CANNOT collect `sm_active`/`sm_occupancy` together with `tensor_active` without multiplexing
- T4 CAN collect them together (all in group A.1)

#### 5.2.3 NVIDIA A100 Metric Groups

Similar to V100 but with some refinements. Check specific GPU using:
```bash
dcgmi profile -l -i 0
```

### 5.3 Discovering Metric Groups

**Using dcgmi CLI**:
```bash
# List all profiling metrics and their groups for GPU 0
dcgmi profile --list --gpuid 0

# Example output shows groupings like:
# Group A.1: DCGM_FI_PROF_SM_ACTIVE, DCGM_FI_PROF_SM_OCCUPANCY
# Group A.2: DCGM_FI_PROF_PIPE_TENSOR_ACTIVE
```

**Using API**:
```c
// C API
dcgmReturn_t dcgmProfGetSupportedMetricGroups(
    dcgmHandle_t dcgmHandle,
    dcgmGpuGrp_t groupId,
    dcgmProfGetMetricGroups_t *metricGroups
);
```

### 5.4 Best Practices for Metric Collection

1. **Minimize Multiplexing**: Choose metrics from different letter groups when possible
2. **Common Combinations**:
   - LLM Inference: `tensor_active + dram_active + sm_active` (may require multiplexing)
   - Multi-GPU: Add `nvlink_tx_bytes + nvlink_rx_bytes`
   - CPU Transfer: Add `pcie_tx_bytes + pcie_rx_bytes`
3. **Accept Trade-offs**: If you need incompatible metrics, accept multiplexing overhead
4. **Sample Rate**: Increase sampling interval when multiplexing (e.g., 1Hz → 2Hz)

---

## 6. Performance Counter Details

### 6.1 SM Occupancy and Efficiency

#### 6.1.1 Understanding SM Architecture

**Streaming Multiprocessor (SM)**: The fundamental processing unit in NVIDIA GPUs
- Modern GPUs have 40-140+ SMs depending on model
- Each SM can execute multiple warps concurrently
- Each warp contains 32 threads

**Key Metrics**:
- **SM Active**: At least one warp executing
- **SM Occupancy**: How many warps are resident vs maximum possible

#### 6.1.2 Interpreting SM Metrics

**Scenario 1: High SM Active, Low Occupancy**
```
SM Active: 95%
SM Occupancy: 30%
```
- **Interpretation**: SMs are busy but with few warps
- **Likely Cause**: Low parallelism, small batch size
- **Action**: Increase batch size or use batching techniques

**Scenario 2: Low SM Active, High Occupancy**
```
SM Active: 40%
SM Occupancy: 80%
```
- **Interpretation**: Many warps resident but not executing
- **Likely Cause**: Memory latency, dependencies, synchronization
- **Action**: Optimize memory access patterns, reduce dependencies

**Scenario 3: High SM Active, High Occupancy**
```
SM Active: 90%
SM Occupancy: 85%
```
- **Interpretation**: Optimal GPU utilization
- **Result**: Good compute efficiency

**Scenario 4: Low SM Active, Low Occupancy**
```
SM Active: 20%
SM Occupancy: 25%
```
- **Interpretation**: Underutilized GPU
- **Likely Cause**: Small workload, CPU bottleneck, insufficient batching
- **Action**: Increase workload, optimize data pipeline

### 6.2 Tensor Core Utilization

#### 6.2.1 When Tensor Cores Are Used

Tensor Cores accelerate:
- Matrix multiplication (GEMM operations)
- Convolutions (via im2col + GEMM)
- Attention mechanisms (Q × K^T, score × V)
- Mixed precision operations (FP16 compute with FP32 accumulation)

#### 6.2.2 Tensor Core Activity Targets

**LLM Inference Prefill Phase** (compute bound):
- **Target**: 70-90% tensor active
- **Typical**: Highly parallel matrix multiplications
- **Bottleneck**: Usually compute bound

**LLM Inference Decoding Phase** (memory bound):
- **Target**: 30-60% tensor active
- **Typical**: Sequential token generation
- **Bottleneck**: Usually memory bandwidth bound
- **Note**: Low tensor activity is EXPECTED here

**Training with Mixed Precision**:
- **Target**: 80-95% tensor active
- **Typical**: Large batch sizes, efficient data loading
- **Bottleneck**: Usually compute or I/O bound

#### 6.2.3 Improving Tensor Core Utilization

1. **Use Supported Data Types**: FP16, BF16, INT8, TF32
2. **Matrix Dimensions**: Align to multiples of 16 (FP16) or 8 (INT8)
3. **Enable Tensor Cores**: Use appropriate cuBLAS/cuDNN settings
4. **Batch Operations**: Group operations to increase parallelism
5. **Mixed Precision**: Use automatic mixed precision (AMP)

### 6.3 Memory Bandwidth Utilization

#### 6.3.1 DRAM Active Interpretation

**High DRAM Activity (> 80%)**:
- Memory subsystem is working hard
- May indicate memory bound workload
- Check if compute utilization is low

**Low DRAM Activity (< 30%)**:
- Memory subsystem is idle
- Workload is compute bound or underutilized
- May indicate optimization opportunity

**Balanced Activity (50-70%)**:
- Mixed compute and memory operations
- Typical for balanced kernels

#### 6.3.2 Memory Bandwidth Formula

```
Memory Bandwidth (GB/s) = (DRAM Active %) × (Peak Memory Bandwidth)

Example for A100 (peak 1.6 TB/s):
DRAM Active = 75%
Actual Bandwidth = 0.75 × 1600 GB/s = 1200 GB/s
```

**Note**: This is an approximation. Actual bandwidth depends on access patterns.

### 6.4 PCIe Bandwidth Utilization

#### 6.4.1 PCIe Bandwidth Calculation

```python
def calculate_pcie_bandwidth(tx_bytes, rx_bytes, time_delta):
    """Calculate PCIe bandwidth utilization."""
    tx_bandwidth = tx_bytes / time_delta  # bytes/sec
    rx_bandwidth = rx_bytes / time_delta  # bytes/sec
    total_bandwidth = tx_bandwidth + rx_bandwidth

    # Convert to GB/s
    tx_gbps = tx_bandwidth / (1024**3)
    rx_gbps = rx_bandwidth / (1024**3)

    return {
        "tx_gbps": tx_gbps,
        "rx_gbps": rx_gbps,
        "total_gbps": tx_gbps + rx_gbps
    }
```

#### 6.4.2 PCIe Generations and Bandwidth

| PCIe Gen | x16 Bandwidth | x8 Bandwidth | Typical GPUs |
|----------|--------------|--------------|--------------|
| PCIe 3.0 | 15.75 GB/s | 7.88 GB/s | V100, P100 |
| PCIe 4.0 | 31.5 GB/s | 15.75 GB/s | A100, A30 |
| PCIe 5.0 | 63 GB/s | 31.5 GB/s | H100, H200 |

#### 6.4.3 Identifying PCIe Bottlenecks

**Signs of PCIe Bottleneck**:
- PCIe bandwidth close to peak (> 90%)
- Low GPU utilization (< 50%)
- High host-to-device or device-to-host transfers

**Solutions**:
- Minimize CPU-GPU data transfers
- Use pinned memory for transfers
- Overlap compute with transfers
- Increase batch size to amortize transfer cost

### 6.5 NVLink Bandwidth Utilization

#### 6.5.1 NVLink Bandwidth Calculation

```python
def calculate_nvlink_bandwidth(tx_bytes, rx_bytes, time_delta, num_links):
    """Calculate NVLink bandwidth utilization."""
    tx_bandwidth = tx_bytes / time_delta
    rx_bandwidth = rx_bytes / time_delta

    # Convert to GB/s
    tx_gbps = tx_bandwidth / (1024**3)
    rx_gbps = rx_bandwidth / (1024**3)

    # Calculate per-link bandwidth
    tx_per_link = tx_gbps / num_links if num_links > 0 else 0
    rx_per_link = rx_gbps / num_links if num_links > 0 else 0

    return {
        "tx_gbps": tx_gbps,
        "rx_gbps": rx_gbps,
        "total_gbps": tx_gbps + rx_gbps,
        "tx_per_link_gbps": tx_per_link,
        "rx_per_link_gbps": rx_per_link
    }
```

#### 6.5.2 NVLink Generations and Bandwidth

| NVLink Gen | Per-Link BW | Typical Config | Total BW | GPUs |
|------------|-------------|----------------|----------|------|
| NVLink 2.0 | 25 GB/s | 6 links | 300 GB/s | V100 |
| NVLink 3.0 | 50 GB/s | 12 links | 600 GB/s | A100 |
| NVLink 4.0 | 50 GB/s | 18 links | 900 GB/s | H100 |

#### 6.5.3 Multi-GPU Communication Patterns

**All-Reduce (Data Parallelism)**:
- High bidirectional NVLink traffic
- All GPUs communicate with all other GPUs
- Typical in distributed training

**Point-to-Point (Pipeline Parallelism)**:
- Sequential communication between adjacent GPUs
- Lower NVLink utilization
- Typical in pipeline parallel training

**All-to-All (Tensor Parallelism)**:
- Each GPU communicates with every other GPU
- Very high NVLink utilization
- Typical in Megatron-style tensor parallelism

---

## 7. Calculating Derived Metrics

### 7.1 FLOPS Calculation

#### 7.1.1 Formula

```
Actual FLOPS = (Pipe Active %) × (Peak Theoretical FLOPS)
```

#### 7.1.2 Example: A100 GPU

**Peak Performance**:
- FP64: 9.7 TFLOPS (19.5 with FP64 Tensor Cores)
- FP32: 19.5 TFLOPS (156 with TF32 Tensor Cores)
- FP16: 312 TFLOPS (Tensor Cores)
- INT8: 624 TOPS (Tensor Cores)

**Calculation Example**:
```
Measured Metrics:
- DCGM_FI_PROF_PIPE_FP16_ACTIVE = 65%
- DCGM_FI_PROF_PIPE_TENSOR_ACTIVE = 75%

FP16 FLOPS (non-Tensor):
= 0.65 × (312 TFLOPS × 0.25)  # Assume 25% is non-Tensor FP16
= ~50 TFLOPS

Tensor Core FLOPS (FP16):
= 0.75 × 312 TFLOPS
= 234 TFLOPS

Total Effective FLOPS:
= 50 + 234 = 284 TFLOPS
```

#### 7.1.3 Python Implementation

```python
def calculate_flops(pipe_active_percent, peak_flops_teraflops):
    """
    Calculate actual FLOPS from pipe active percentage.

    Args:
        pipe_active_percent: Percentage (0-100) from DCGM_FI_PROF_PIPE_*
        peak_flops_teraflops: Peak theoretical FLOPS for the GPU

    Returns:
        Actual FLOPS in TFLOPS
    """
    return (pipe_active_percent / 100.0) * peak_flops_teraflops


def calculate_gpu_flops(gpu_model, profiling_metrics):
    """
    Calculate FLOPS for various precision types.

    Args:
        gpu_model: GPU model name (e.g., "A100", "H100")
        profiling_metrics: Dict with DCGM profiling metrics

    Returns:
        Dict with FLOPS calculations
    """
    # Peak FLOPS lookup table
    peak_flops = {
        "A100": {
            "fp64": 19.5,  # With Tensor Cores
            "fp32": 156,   # With TF32 Tensor Cores
            "fp16": 312,   # With Tensor Cores
            "int8": 624,   # TOPS with Tensor Cores
        },
        "H100": {
            "fp64": 67,    # With Tensor Cores
            "fp32": 267,   # With TF32 Tensor Cores
            "fp16": 989,   # With Tensor Cores
            "int8": 1979,  # TOPS with Tensor Cores
        },
    }

    if gpu_model not in peak_flops:
        raise ValueError(f"Unknown GPU model: {gpu_model}")

    results = {}
    peak = peak_flops[gpu_model]

    # Calculate FLOPS for each precision
    if "pipe_fp64_active" in profiling_metrics:
        results["fp64_tflops"] = calculate_flops(
            profiling_metrics["pipe_fp64_active"],
            peak["fp64"]
        )

    if "pipe_fp32_active" in profiling_metrics:
        results["fp32_tflops"] = calculate_flops(
            profiling_metrics["pipe_fp32_active"],
            peak["fp32"]
        )

    if "pipe_fp16_active" in profiling_metrics:
        results["fp16_tflops"] = calculate_flops(
            profiling_metrics["pipe_fp16_active"],
            peak["fp16"]
        )

    # Tensor Core FLOPS
    if "pipe_tensor_active" in profiling_metrics:
        # Use highest precision Tensor Core capability
        results["tensor_tflops"] = calculate_flops(
            profiling_metrics["pipe_tensor_active"],
            peak["fp16"]  # Assume FP16 Tensor Cores
        )

    return results
```

### 7.2 Model FLOPS Utilization (MFU)

#### 7.2.1 Definition

**MFU**: The ratio of actual FLOPS achieved to peak theoretical FLOPS

```
MFU = (Actual FLOPS) / (Peak FLOPS)
```

#### 7.2.2 Target MFU Values

| Workload Type | Target MFU | Notes |
|--------------|------------|-------|
| Large Batch Training | 0.40 - 0.70 | Compute bound, well optimized |
| Small Batch Training | 0.20 - 0.40 | Less parallelism |
| Inference Prefill | 0.30 - 0.60 | Parallel phase |
| Inference Decoding | 0.05 - 0.15 | Memory bound |
| Scientific Computing | 0.50 - 0.90 | Highly optimized kernels |

#### 7.2.3 Python Implementation

```python
def calculate_mfu(actual_flops_tflops, peak_flops_tflops):
    """
    Calculate Model FLOPS Utilization.

    Args:
        actual_flops_tflops: Actual FLOPS achieved
        peak_flops_tflops: Peak theoretical FLOPS

    Returns:
        MFU as a decimal (0.0 to 1.0)
    """
    if peak_flops_tflops == 0:
        return 0.0
    return actual_flops_tflops / peak_flops_tflops


def interpret_mfu(mfu, workload_type):
    """
    Interpret MFU value and provide recommendations.

    Args:
        mfu: Model FLOPS Utilization (0.0 to 1.0)
        workload_type: Type of workload (training, inference_prefill, etc.)

    Returns:
        Dict with interpretation and recommendations
    """
    targets = {
        "training_large_batch": (0.40, 0.70),
        "training_small_batch": (0.20, 0.40),
        "inference_prefill": (0.30, 0.60),
        "inference_decoding": (0.05, 0.15),
    }

    if workload_type not in targets:
        return {"error": "Unknown workload type"}

    target_min, target_max = targets[workload_type]

    if mfu < target_min:
        status = "below_target"
        recommendations = [
            "Increase batch size",
            "Optimize data loading pipeline",
            "Check for CPU bottlenecks",
            "Enable Tensor Cores if not already",
            "Profile for memory bottlenecks"
        ]
    elif mfu > target_max:
        status = "above_target"
        recommendations = [
            "Excellent performance",
            "Current configuration is well optimized"
        ]
    else:
        status = "within_target"
        recommendations = [
            "Performance is within expected range",
            "Fine-tune if seeking marginal improvements"
        ]

    return {
        "mfu": mfu,
        "mfu_percent": mfu * 100,
        "target_range": (target_min, target_max),
        "status": status,
        "recommendations": recommendations
    }
```

### 7.3 Memory Bandwidth Utilization (MBU)

#### 7.3.1 Formula

```
MBU = (Actual Memory Bandwidth) / (Peak Memory Bandwidth)

Actual Memory Bandwidth ≈ (DRAM Active %) × (Peak Bandwidth)
```

#### 7.3.2 Target MBU Values

| Workload Type | Target MBU | Notes |
|--------------|------------|-------|
| Memory Bound Kernels | 0.70 - 0.95 | Well optimized |
| Inference Decoding | 0.60 - 0.85 | Memory bound phase |
| Balanced Workloads | 0.40 - 0.60 | Mix of compute and memory |
| Compute Bound | 0.10 - 0.30 | Low memory usage expected |

#### 7.3.3 Python Implementation

```python
def calculate_mbu(dram_active_percent, peak_bandwidth_gbps):
    """
    Calculate Memory Bandwidth Utilization.

    Args:
        dram_active_percent: DRAM active percentage from DCGM
        peak_bandwidth_gbps: Peak memory bandwidth in GB/s

    Returns:
        Dict with MBU and actual bandwidth
    """
    actual_bandwidth = (dram_active_percent / 100.0) * peak_bandwidth_gbps
    mbu = dram_active_percent / 100.0

    return {
        "mbu": mbu,
        "mbu_percent": mbu * 100,
        "actual_bandwidth_gbps": actual_bandwidth,
        "peak_bandwidth_gbps": peak_bandwidth_gbps
    }


def analyze_memory_bound(mbu, mfu):
    """
    Analyze if workload is memory bound or compute bound.

    Args:
        mbu: Memory Bandwidth Utilization
        mfu: Model FLOPS Utilization

    Returns:
        Dict with analysis
    """
    if mbu > 0.7 and mfu < 0.3:
        return {
            "classification": "memory_bound",
            "confidence": "high",
            "recommendations": [
                "Optimize memory access patterns",
                "Use kernel fusion to reduce memory traffic",
                "Consider compute optimizations secondary",
                "Profile memory access patterns"
            ]
        }
    elif mfu > 0.6 and mbu < 0.4:
        return {
            "classification": "compute_bound",
            "confidence": "high",
            "recommendations": [
                "Optimize compute kernels",
                "Increase arithmetic intensity",
                "Memory bandwidth is not the bottleneck",
                "Focus on algorithmic optimizations"
            ]
        }
    elif mbu > 0.5 and mfu > 0.5:
        return {
            "classification": "balanced",
            "confidence": "medium",
            "recommendations": [
                "Well balanced workload",
                "Both compute and memory are utilized",
                "Look for other bottlenecks (I/O, synchronization)"
            ]
        }
    else:
        return {
            "classification": "underutilized",
            "confidence": "high",
            "recommendations": [
                "GPU is underutilized",
                "Check for CPU bottlenecks",
                "Increase batch size",
                "Improve data loading pipeline",
                "Profile end-to-end pipeline"
            ]
        }
```

### 7.4 Instruction Throughput

#### 7.4.1 Calculating Instructions Per Second

```python
def calculate_instruction_throughput(sm_active_percent, num_sms, clock_speed_mhz):
    """
    Estimate instruction throughput.

    Args:
        sm_active_percent: SM active percentage from DCGM
        num_sms: Number of SMs on the GPU
        clock_speed_mhz: SM clock speed in MHz

    Returns:
        Estimated instructions per second
    """
    # Each SM can issue up to 4 instructions per cycle (typical)
    instructions_per_cycle = 4

    # Calculate active SMs
    active_sms = (sm_active_percent / 100.0) * num_sms

    # Calculate cycles per second
    cycles_per_second = clock_speed_mhz * 1e6

    # Total instruction throughput
    instructions_per_second = (
        active_sms * instructions_per_cycle * cycles_per_second
    )

    return {
        "instructions_per_second": instructions_per_second,
        "giga_instructions_per_second": instructions_per_second / 1e9,
        "active_sms": active_sms,
        "total_sms": num_sms,
        "sm_utilization": sm_active_percent / 100.0
    }
```

---

## 8. API Implementation Patterns

### 8.1 C API Usage

#### 8.1.1 Basic Profiling Setup

```c
#include <dcgm_agent.h>
#include <dcgm_structs.h>

// Initialize DCGM
dcgmHandle_t dcgmHandle;
dcgmReturn_t result;

result = dcgmInit();
if (result != DCGM_ST_OK) {
    fprintf(stderr, "Failed to initialize DCGM: %d\n", result);
    return 1;
}

result = dcgmConnect("127.0.0.1", &dcgmHandle);
if (result != DCGM_ST_OK) {
    fprintf(stderr, "Failed to connect to DCGM: %d\n", result);
    dcgmShutdown();
    return 1;
}

// Create GPU group for all GPUs
dcgmGpuGrp_t groupId;
result = dcgmGroupCreate(dcgmHandle, DCGM_GROUP_DEFAULT, "all_gpus", &groupId);

// Get supported metric groups
dcgmProfGetMetricGroups_v3 metricGroups;
memset(&metricGroups, 0, sizeof(metricGroups));
metricGroups.version = dcgmProfGetMetricGroups_version3;

result = dcgmProfGetSupportedMetricGroups(dcgmHandle, groupId, &metricGroups);
if (result != DCGM_ST_OK) {
    fprintf(stderr, "Failed to get metric groups: %d\n", result);
}

// Watch profiling fields
unsigned short fieldIds[] = {
    DCGM_FI_PROF_SM_ACTIVE,
    DCGM_FI_PROF_SM_OCCUPANCY,
    DCGM_FI_PROF_PIPE_TENSOR_ACTIVE,
    DCGM_FI_PROF_DRAM_ACTIVE,
    DCGM_FI_PROF_PCIE_TX_BYTES,
    DCGM_FI_PROF_PCIE_RX_BYTES
};
int numFields = sizeof(fieldIds) / sizeof(fieldIds[0]);

result = dcgmWatchFields(
    dcgmHandle,
    groupId,
    fieldIds,
    numFields,
    1000000,  // 1 second update interval (microseconds)
    1.0,      // Max keep age (seconds)
    0         // Max keep samples (0 = unlimited)
);

// Get latest values
dcgmFieldValue_v2 values[numFields];
for (int i = 0; i < numFields; i++) {
    result = dcgmGetLatestValuesForFields(
        dcgmHandle,
        0,  // GPU ID
        fieldIds + i,
        1,
        values + i
    );

    if (result == DCGM_ST_OK && values[i].status == DCGM_ST_OK) {
        if (values[i].fieldType == DCGM_FT_DOUBLE) {
            printf("Field %d: %.2f%%\n", fieldIds[i], values[i].value.dbl);
        } else if (values[i].fieldType == DCGM_FT_INT64) {
            printf("Field %d: %lld bytes\n", fieldIds[i], values[i].value.i64);
        }
    }
}

// Cleanup
dcgmGroupDestroy(dcgmHandle, groupId);
dcgmDisconnect(dcgmHandle);
dcgmShutdown();
```

#### 8.1.2 Pausing and Resuming Profiling

```c
// Pause profiling (for use with Nsight tools)
result = dcgmProfPause(dcgmHandle);
if (result != DCGM_ST_OK) {
    fprintf(stderr, "Failed to pause profiling: %d\n", result);
}

// Run Nsight profiling here...

// Resume profiling
result = dcgmProfResume(dcgmHandle);
if (result != DCGM_ST_OK) {
    fprintf(stderr, "Failed to resume profiling: %d\n", result);
}
```

### 8.2 Python API Usage

#### 8.2.1 Basic Profiling with pydcgm

```python
import pydcgm
import time

# Initialize DCGM
pydcgm.Init()
dcgm_handle = pydcgm.DcgmHandle()

# Get system information
system_info = dcgm_handle.GetSystem()
gpus = system_info.gpuIdList

print(f"Found {len(gpus)} GPUs")

# Create group for all GPUs
group_id = dcgm_handle.GetGroupAllGpus()

# Define profiling field IDs
field_ids = [
    pydcgm.DCGM_FI_PROF_SM_ACTIVE,
    pydcgm.DCGM_FI_PROF_SM_OCCUPANCY,
    pydcgm.DCGM_FI_PROF_PIPE_TENSOR_ACTIVE,
    pydcgm.DCGM_FI_PROF_DRAM_ACTIVE,
    pydcgm.DCGM_FI_PROF_PCIE_TX_BYTES,
    pydcgm.DCGM_FI_PROF_PCIE_RX_BYTES,
    pydcgm.DCGM_FI_PROF_NVLINK_TX_BYTES,
    pydcgm.DCGM_FI_PROF_NVLINK_RX_BYTES,
]

# Watch fields with 1 second interval
update_freq = 1000000  # microseconds
max_keep_age = 10.0  # seconds
max_keep_samples = 0  # unlimited

dcgm_handle.WatchFields(
    group_id,
    field_ids,
    update_freq,
    max_keep_age,
    max_keep_samples
)

# Collect metrics
print("Collecting metrics for 10 seconds...")
for _ in range(10):
    time.sleep(1)

    for gpu_id in gpus:
        values = dcgm_handle.GetLatestValuesForFields(gpu_id, field_ids)

        print(f"\nGPU {gpu_id} Metrics:")
        for field_id, value in zip(field_ids, values):
            field_name = pydcgm.DcgmFieldGetById(field_id).name
            if value.status == pydcgm.DCGM_ST_OK:
                if isinstance(value.value, float):
                    print(f"  {field_name}: {value.value:.2f}%")
                else:
                    print(f"  {field_name}: {value.value}")

# Cleanup
dcgm_handle.UnwatchFields(group_id, field_ids)
dcgm_handle.Shutdown()
```

#### 8.2.2 Calculating Derived Metrics

```python
import pydcgm
import time

class DCGMProfiler:
    """Profiler using DCGM for GPU metrics."""

    def __init__(self, gpu_id=0):
        self.gpu_id = gpu_id
        pydcgm.Init()
        self.handle = pydcgm.DcgmHandle()
        self.group_id = self.handle.GetGroupAllGpus()

        # Define fields to watch
        self.field_ids = [
            pydcgm.DCGM_FI_PROF_SM_ACTIVE,
            pydcgm.DCGM_FI_PROF_SM_OCCUPANCY,
            pydcgm.DCGM_FI_PROF_PIPE_TENSOR_ACTIVE,
            pydcgm.DCGM_FI_PROF_DRAM_ACTIVE,
            pydcgm.DCGM_FI_PROF_PIPE_FP16_ACTIVE,
            pydcgm.DCGM_FI_PROF_PIPE_FP32_ACTIVE,
            pydcgm.DCGM_FI_PROF_PCIE_TX_BYTES,
            pydcgm.DCGM_FI_PROF_PCIE_RX_BYTES,
        ]

        # Start watching
        self.handle.WatchFields(
            self.group_id,
            self.field_ids,
            1000000,  # 1 second
            10.0,
            0
        )

        # GPU specs (example for A100)
        self.gpu_specs = {
            "peak_fp16_tflops": 312,
            "peak_fp32_tflops": 19.5,
            "peak_memory_bandwidth_gbps": 1600,
            "num_sms": 108,
        }

        # Previous byte counters for bandwidth calculation
        self.prev_pcie_tx = None
        self.prev_pcie_rx = None
        self.prev_timestamp = None

    def get_metrics(self):
        """Get current profiling metrics."""
        values = self.handle.GetLatestValuesForFields(
            self.gpu_id,
            self.field_ids
        )

        metrics = {}
        for field_id, value in zip(self.field_ids, values):
            if value.status == pydcgm.DCGM_ST_OK:
                field_name = pydcgm.DcgmFieldGetById(field_id).name
                metrics[field_name] = value.value

        return metrics

    def calculate_derived_metrics(self, metrics):
        """Calculate derived metrics from raw profiling data."""
        derived = {}

        # FLOPS calculations
        if "DCGM_FI_PROF_PIPE_FP16_ACTIVE" in metrics:
            fp16_active = metrics["DCGM_FI_PROF_PIPE_FP16_ACTIVE"]
            derived["fp16_tflops"] = (
                fp16_active / 100.0
            ) * self.gpu_specs["peak_fp16_tflops"]

        if "DCGM_FI_PROF_PIPE_FP32_ACTIVE" in metrics:
            fp32_active = metrics["DCGM_FI_PROF_PIPE_FP32_ACTIVE"]
            derived["fp32_tflops"] = (
                fp32_active / 100.0
            ) * self.gpu_specs["peak_fp32_tflops"]

        # Memory bandwidth
        if "DCGM_FI_PROF_DRAM_ACTIVE" in metrics:
            dram_active = metrics["DCGM_FI_PROF_DRAM_ACTIVE"]
            derived["memory_bandwidth_gbps"] = (
                dram_active / 100.0
            ) * self.gpu_specs["peak_memory_bandwidth_gbps"]
            derived["mbu"] = dram_active / 100.0

        # PCIe bandwidth
        current_time = time.time()
        if "DCGM_FI_PROF_PCIE_TX_BYTES" in metrics:
            pcie_tx = metrics["DCGM_FI_PROF_PCIE_TX_BYTES"]

            if self.prev_pcie_tx is not None:
                time_delta = current_time - self.prev_timestamp
                tx_bytes_delta = pcie_tx - self.prev_pcie_tx
                derived["pcie_tx_gbps"] = (
                    tx_bytes_delta / time_delta / (1024**3)
                )

            self.prev_pcie_tx = pcie_tx

        if "DCGM_FI_PROF_PCIE_RX_BYTES" in metrics:
            pcie_rx = metrics["DCGM_FI_PROF_PCIE_RX_BYTES"]

            if self.prev_pcie_rx is not None:
                time_delta = current_time - self.prev_timestamp
                rx_bytes_delta = pcie_rx - self.prev_pcie_rx
                derived["pcie_rx_gbps"] = (
                    rx_bytes_delta / time_delta / (1024**3)
                )

            self.prev_pcie_rx = pcie_rx

        self.prev_timestamp = current_time

        # SM utilization
        if "DCGM_FI_PROF_SM_ACTIVE" in metrics:
            derived["sm_utilization"] = (
                metrics["DCGM_FI_PROF_SM_ACTIVE"] / 100.0
            )

        # Workload classification
        if "DCGM_FI_PROF_DRAM_ACTIVE" in metrics and \
           "DCGM_FI_PROF_PIPE_TENSOR_ACTIVE" in metrics:
            dram = metrics["DCGM_FI_PROF_DRAM_ACTIVE"]
            tensor = metrics["DCGM_FI_PROF_PIPE_TENSOR_ACTIVE"]

            if dram > 70 and tensor < 30:
                derived["workload_classification"] = "memory_bound"
            elif tensor > 60 and dram < 40:
                derived["workload_classification"] = "compute_bound"
            elif tensor > 50 and dram > 50:
                derived["workload_classification"] = "balanced"
            else:
                derived["workload_classification"] = "underutilized"

        return derived

    def profile_for_duration(self, duration_seconds=10):
        """Profile GPU for specified duration."""
        print(f"Profiling GPU {self.gpu_id} for {duration_seconds} seconds...")

        all_metrics = []
        for _ in range(duration_seconds):
            time.sleep(1)
            metrics = self.get_metrics()
            derived = self.calculate_derived_metrics(metrics)

            combined = {**metrics, **derived}
            all_metrics.append(combined)

            # Print current metrics
            print(f"\nTimestamp: {time.time()}")
            print(f"  SM Active: {metrics.get('DCGM_FI_PROF_SM_ACTIVE', 0):.2f}%")
            print(f"  SM Occupancy: {metrics.get('DCGM_FI_PROF_SM_OCCUPANCY', 0):.2f}%")
            print(f"  Tensor Active: {metrics.get('DCGM_FI_PROF_PIPE_TENSOR_ACTIVE', 0):.2f}%")
            print(f"  DRAM Active: {metrics.get('DCGM_FI_PROF_DRAM_ACTIVE', 0):.2f}%")
            if "fp16_tflops" in derived:
                print(f"  FP16 TFLOPS: {derived['fp16_tflops']:.2f}")
            if "memory_bandwidth_gbps" in derived:
                print(f"  Memory BW: {derived['memory_bandwidth_gbps']:.2f} GB/s")
            if "workload_classification" in derived:
                print(f"  Classification: {derived['workload_classification']}")

        return all_metrics

    def cleanup(self):
        """Clean up DCGM resources."""
        self.handle.UnwatchFields(self.group_id, self.field_ids)
        self.handle.Shutdown()


# Usage example
if __name__ == "__main__":
    profiler = DCGMProfiler(gpu_id=0)

    try:
        metrics = profiler.profile_for_duration(duration_seconds=10)

        # Calculate averages
        avg_sm_active = sum(
            m.get("DCGM_FI_PROF_SM_ACTIVE", 0) for m in metrics
        ) / len(metrics)
        avg_tensor_active = sum(
            m.get("DCGM_FI_PROF_PIPE_TENSOR_ACTIVE", 0) for m in metrics
        ) / len(metrics)

        print(f"\n=== Summary ===")
        print(f"Average SM Active: {avg_sm_active:.2f}%")
        print(f"Average Tensor Active: {avg_tensor_active:.2f}%")

    finally:
        profiler.cleanup()
```

### 8.3 Go API Usage

#### 8.3.1 Basic Go Implementation

```go
package main

import (
    "fmt"
    "time"

    "github.com/NVIDIA/go-dcgm/pkg/dcgm"
)

func main() {
    // Initialize DCGM
    cleanup, err := dcgm.Init(dcgm.Embedded)
    if err != nil {
        panic(err)
    }
    defer cleanup()

    // Get all GPUs
    gpus, err := dcgm.GetSupportedDevices()
    if err != nil {
        panic(err)
    }

    fmt.Printf("Found %d GPUs\n", len(gpus))

    // Create field group for profiling metrics
    fieldIds := []dcgm.Short{
        dcgm.DCGM_FI_PROF_SM_ACTIVE,
        dcgm.DCGM_FI_PROF_SM_OCCUPANCY,
        dcgm.DCGM_FI_PROF_PIPE_TENSOR_ACTIVE,
        dcgm.DCGM_FI_PROF_DRAM_ACTIVE,
    }

    fieldGroup, err := dcgm.FieldGroupCreate("profiling_fields", fieldIds)
    if err != nil {
        panic(err)
    }
    defer dcgm.FieldGroupDestroy(fieldGroup)

    // Create GPU group
    gpuGroup, err := dcgm.CreateGroup("all_gpus")
    if err != nil {
        panic(err)
    }
    defer dcgm.DestroyGroup(gpuGroup)

    for _, gpu := range gpus {
        err = dcgm.AddToGroup(gpuGroup, gpu)
        if err != nil {
            fmt.Printf("Failed to add GPU %d to group: %v\n", gpu, err)
        }
    }

    // Watch fields
    err = dcgm.WatchFieldGroup(
        gpuGroup,
        fieldGroup,
        1000000, // 1 second update interval (microseconds)
        10.0,    // max keep age
        0,       // max keep samples
    )
    if err != nil {
        panic(err)
    }
    defer dcgm.UnwatchFieldGroup(gpuGroup, fieldGroup)

    // Collect metrics for 10 seconds
    fmt.Println("Collecting metrics...")
    for i := 0; i < 10; i++ {
        time.Sleep(1 * time.Second)

        for _, gpuId := range gpus {
            values, err := dcgm.GetLatestValuesForFields(gpuId, fieldIds)
            if err != nil {
                fmt.Printf("Error getting values for GPU %d: %v\n", gpuId, err)
                continue
            }

            fmt.Printf("\nGPU %d:\n", gpuId)
            for j, value := range values {
                fieldMeta, _ := dcgm.GetFieldById(fieldIds[j])
                if value.Status == dcgm.Healthy {
                    if fieldMeta.FieldType == dcgm.DCGM_FT_DOUBLE {
                        fmt.Printf("  %s: %.2f%%\n", fieldMeta.Tag, value.Float64())
                    }
                }
            }
        }
    }
}
```

---

## 9. LLM Inference Best Practices

### 9.1 Understanding LLM Inference Phases

#### 9.1.1 Prefill Phase (Prompt Processing)

**Characteristics**:
- Processes entire input prompt at once
- Highly parallel matrix multiplications
- **Compute bound** on most hardware
- High Tensor Core utilization expected

**Expected Metrics**:
```
SM Active: 70-95%
SM Occupancy: 60-85%
Tensor Active: 70-90%
DRAM Active: 30-50%
Classification: Compute bound
```

**Optimization Targets**:
- **MFU**: 0.4-0.7 (40-70% of peak FLOPS)
- **Tensor Utilization**: > 70%
- **Memory Bandwidth**: 30-50% (secondary importance)

#### 9.1.2 Decoding Phase (Token Generation)

**Characteristics**:
- Generates one token at a time (auto-regressive)
- Sequential by nature
- **Memory bandwidth bound**
- Low parallelism per request

**Expected Metrics**:
```
SM Active: 30-60%
SM Occupancy: 20-50%
Tensor Active: 20-40%
DRAM Active: 60-85%
Classification: Memory bound
```

**Optimization Targets**:
- **MBU**: 0.6-0.9 (60-90% of peak memory bandwidth)
- **Tensor Utilization**: 20-40% (low is EXPECTED)
- **MFU**: 0.05-0.15 (low is EXPECTED)

**Key Insight**: Low tensor/compute utilization during decoding is NORMAL and EXPECTED. Focus on memory bandwidth optimization.

### 9.2 Monitoring LLM Inference

#### 9.2.1 Key Metrics to Track

1. **Throughput Metrics**:
   - Tokens per second (TPS)
   - Requests per second (RPS)
   - Time to first token (TTFT)
   - Inter-token latency (ITL)

2. **GPU Utilization Metrics**:
   - SM active %
   - Tensor Core active %
   - Memory bandwidth utilization

3. **Quality Metrics**:
   - P50, P90, P99 latencies
   - Error rate
   - Timeout rate

#### 9.2.2 Continuous Batching Metrics

**Continuous batching** (e.g., vLLM, TensorRT-LLM) provides 10-20x better throughput than dynamic batching.

**Monitor**:
- Batch size distribution
- KV cache utilization
- Request queuing time
- Preemption rate (if supported)

**DCGM Metrics**:
```python
# Good continuous batching performance indicators
sm_active > 70%           # High SM utilization
tensor_active > 60%       # Tensor Cores busy
dram_active > 50%         # Memory subsystem utilized
batch_size_avg > 16       # Reasonable batch sizes
```

### 9.3 Identifying Bottlenecks

#### 9.3.1 Common Bottleneck Patterns

**Pattern 1: Low GPU Utilization**
```
SM Active: 20%
Tensor Active: 15%
DRAM Active: 25%

Diagnosis: GPU is idle most of the time
Causes:
  - CPU bottleneck (preprocessing, postprocessing)
  - I/O bottleneck (data loading)
  - Small batch size
  - Insufficient request rate

Solutions:
  - Profile CPU usage
  - Optimize data pipeline
  - Increase batch size
  - Use continuous batching
```

**Pattern 2: PCIe Bottleneck**
```
SM Active: 30%
PCIe Bandwidth: 90% of peak
DRAM Active: 20%

Diagnosis: CPU-GPU data transfer is the bottleneck
Causes:
  - Large input/output sizes
  - Frequent host-device transfers
  - Slow PCIe generation (e.g., PCIe 3.0)

Solutions:
  - Minimize CPU-GPU transfers
  - Use pinned memory
  - Consider model compression
  - Upgrade to faster PCIe
```

**Pattern 3: Memory Bandwidth Bound (Expected for Decoding)**
```
SM Active: 50%
Tensor Active: 25%
DRAM Active: 85%

Diagnosis: Memory bandwidth is the bottleneck
Context: Normal for LLM decoding phase
Solutions:
  - This is expected behavior
  - Focus on memory access patterns
  - Use quantization (INT8, FP8) to reduce memory traffic
  - Consider Flash Attention
```

**Pattern 4: Multi-GPU Imbalance**
```
GPU 0 - Tensor Active: 80%, NVLink TX: High
GPU 1 - Tensor Active: 60%, NVLink TX: Low

Diagnosis: Unbalanced load across GPUs
Causes:
  - Improper sharding
  - Pipeline bubble
  - Communication overhead

Solutions:
  - Review parallelism strategy
  - Profile inter-GPU communication
  - Optimize pipeline stages
```

### 9.4 Optimization Strategies

#### 9.4.1 Batching Strategies

**1. Continuous Batching (Recommended)**
- Dynamically group requests
- Maximizes GPU utilization
- Handles variable sequence lengths
- Implemented by vLLM, TensorRT-LLM

**Monitoring**:
```python
# Target metrics with continuous batching
tokens_per_second > 1000     # High throughput
average_batch_size > 16      # Good batching
p99_latency < 2000ms        # Acceptable latency
tensor_active > 60%          # Good utilization
```

**2. Static Batching**
- Fixed batch size
- Simpler implementation
- May waste computation on padding
- Suitable for homogeneous workloads

**3. Dynamic Batching**
- Batch requests with timeout
- Better than static but worse than continuous
- Can lead to head-of-line blocking

#### 9.4.2 Memory Optimizations

**1. Quantization**
- INT8: 4x memory reduction, 2-3x speedup
- FP8: 2x memory reduction (H100+)
- Quantization-aware training for accuracy

**Expected Impact on DCGM Metrics**:
```
INT8 Quantization:
  - Memory bandwidth reduced by ~4x
  - DRAM Active: 85% → 65%
  - Tensor Active: May increase (faster ops)
  - Throughput: 2-3x improvement
```

**2. Flash Attention**
- Reduces memory usage for attention computation
- Kernel fusion for efficiency

**Expected Impact**:
```
  - DRAM Active: Slight decrease
  - SM Occupancy: May increase
  - TTFT: 10-30% improvement
```

**3. KV Cache Optimization**
- PagedAttention (vLLM)
- Efficient memory management
- Reduces memory waste

#### 9.4.3 Compute Optimizations

**1. Kernel Fusion**
- Fuse multiple operations
- Reduces memory traffic
- Increases arithmetic intensity

**2. Mixed Precision**
- FP16/BF16 for compute
- FP32 for accumulation
- Maintains accuracy while improving speed

**Expected Metrics**:
```
Mixed Precision Training:
  - Tensor Active: 70-90%
  - FP16 Active: 60-80%
  - Memory bandwidth: Reduced vs FP32
  - Training speed: 2-3x faster
```

### 9.5 Profiling Workflow for LLM Inference

#### 9.5.1 Step-by-Step Profiling

**Step 1: Establish Baseline**
```bash
# Run inference with DCGM monitoring
dcgmi profile --pause  # Pause if using Nsight
# Run your inference workload
dcgmi profile --resume
dcgmi dmon -e 1002,1003,1004,1005,1009,1010 -c 10
```

**Step 2: Identify Phase**
```python
# Determine if in prefill or decode phase
if tensor_active > 60 and sm_active > 70:
    phase = "prefill"
    expected_mfu = 0.4 - 0.7
elif dram_active > 60 and tensor_active < 40:
    phase = "decode"
    expected_mbu = 0.6 - 0.9
```

**Step 3: Check Against Targets**
```python
def check_performance(metrics, phase):
    if phase == "prefill":
        if metrics["tensor_active"] < 60:
            print("WARNING: Low Tensor Core utilization in prefill")
            print("Consider: Increase batch size, check for CPU bottleneck")

        if metrics["sm_active"] < 60:
            print("WARNING: Low SM utilization")
            print("Consider: Optimize data loading pipeline")

    elif phase == "decode":
        if metrics["dram_active"] < 50:
            print("INFO: Low memory bandwidth usage")
            print("GPU is underutilized - increase request rate or batch size")

        if metrics["dram_active"] > 85:
            print("INFO: Memory bandwidth saturated (expected for decode)")
            print("Consider: Quantization to reduce memory traffic")
```

**Step 4: Profile End-to-End**
```python
def profile_llm_inference(duration=60):
    profiler = DCGMProfiler()

    metrics_over_time = []
    for _ in range(duration):
        time.sleep(1)
        m = profiler.get_metrics()
        metrics_over_time.append(m)

    # Analyze metrics
    avg_tensor = sum(m.get("DCGM_FI_PROF_PIPE_TENSOR_ACTIVE", 0)
                     for m in metrics_over_time) / len(metrics_over_time)
    avg_dram = sum(m.get("DCGM_FI_PROF_DRAM_ACTIVE", 0)
                   for m in metrics_over_time) / len(metrics_over_time)

    print(f"Average Tensor Active: {avg_tensor:.2f}%")
    print(f"Average DRAM Active: {avg_dram:.2f}%")

    # Determine predominant phase
    if avg_tensor > 50:
        print("Workload is compute-heavy (likely prefill-dominant)")
    else:
        print("Workload is memory-heavy (likely decode-dominant)")

    profiler.cleanup()
    return metrics_over_time
```

---

## 10. Implementation Recommendations

### 10.1 For FakeAI Integration

#### 10.1.1 Simulated GPU Metrics

Since FakeAI is a simulation server, we can provide **realistic simulated GPU metrics** based on workload characteristics.

**Approach**:
1. Detect request type (chat completion, embeddings, etc.)
2. Estimate compute vs memory bound based on:
   - Batch size
   - Sequence length
   - Model size (if specified)
3. Generate realistic profiling metrics

#### 10.1.2 Metric Generation Logic

```python
def simulate_gpu_metrics(request_type, batch_size, seq_length):
    """Generate realistic GPU profiling metrics."""

    if request_type == "chat_completion":
        # LLM inference patterns
        if seq_length < 128:
            # Prefill-like: short prompts
            return {
                "sm_active": random.uniform(70, 90),
                "sm_occupancy": random.uniform(60, 80),
                "tensor_active": random.uniform(70, 85),
                "dram_active": random.uniform(30, 50),
                "pcie_tx_bytes": random.randint(1000000, 5000000),
                "pcie_rx_bytes": random.randint(500000, 2000000),
            }
        else:
            # Decode-like: long sequences
            return {
                "sm_active": random.uniform(30, 60),
                "sm_occupancy": random.uniform(20, 50),
                "tensor_active": random.uniform(20, 40),
                "dram_active": random.uniform(60, 85),
                "pcie_tx_bytes": random.randint(500000, 2000000),
                "pcie_rx_bytes": random.randint(200000, 1000000),
            }

    elif request_type == "embeddings":
        # Embedding generation: compute bound
        return {
            "sm_active": random.uniform(75, 95),
            "sm_occupancy": random.uniform(70, 90),
            "tensor_active": random.uniform(60, 80),
            "dram_active": random.uniform(40, 60),
            "pcie_tx_bytes": random.randint(2000000, 8000000),
            "pcie_rx_bytes": random.randint(1000000, 4000000),
        }

    # Default: balanced workload
    return {
        "sm_active": random.uniform(50, 70),
        "sm_occupancy": random.uniform(50, 70),
        "tensor_active": random.uniform(50, 70),
        "dram_active": random.uniform(50, 70),
        "pcie_tx_bytes": random.randint(1000000, 5000000),
        "pcie_rx_bytes": random.randint(500000, 2000000),
    }
```

#### 10.1.3 New Metrics Endpoint

```python
# In app.py
@app.get("/v1/gpu_metrics")
async def get_gpu_metrics():
    """Get simulated GPU profiling metrics."""
    metrics = {
        "timestamp": time.time(),
        "gpu_id": 0,
        "profiling_metrics": {
            "sm_active_percent": random.uniform(50, 90),
            "sm_occupancy_percent": random.uniform(50, 80),
            "tensor_active_percent": random.uniform(40, 85),
            "dram_active_percent": random.uniform(40, 80),
            "fp16_active_percent": random.uniform(30, 70),
            "fp32_active_percent": random.uniform(10, 30),
            "pcie_tx_bytes": random.randint(1000000, 10000000),
            "pcie_rx_bytes": random.randint(500000, 5000000),
        },
        "derived_metrics": {
            "estimated_tflops": random.uniform(50, 200),
            "memory_bandwidth_gbps": random.uniform(400, 1200),
            "pcie_bandwidth_gbps": random.uniform(5, 25),
            "workload_classification": random.choice([
                "compute_bound",
                "memory_bound",
                "balanced"
            ]),
        }
    }
    return metrics
```

### 10.2 Integration with Existing Metrics

#### 10.2.1 Extend MetricsTracker

```python
# In metrics.py
class MetricsTracker:
    def __init__(self):
        # ... existing code ...

        # Add GPU profiling metrics
        self._gpu_metrics = {
            "sm_active": deque(maxlen=100),
            "tensor_active": deque(maxlen=100),
            "dram_active": deque(maxlen=100),
        }

    def track_gpu_metrics(self, endpoint: str, request_type: str,
                         batch_size: int, seq_length: int):
        """Track simulated GPU metrics for a request."""
        metrics = simulate_gpu_metrics(request_type, batch_size, seq_length)

        self._gpu_metrics["sm_active"].append(metrics["sm_active"])
        self._gpu_metrics["tensor_active"].append(metrics["tensor_active"])
        self._gpu_metrics["dram_active"].append(metrics["dram_active"])

    def get_gpu_metrics(self) -> Dict[str, float]:
        """Get averaged GPU metrics."""
        return {
            "avg_sm_active": (
                sum(self._gpu_metrics["sm_active"]) /
                len(self._gpu_metrics["sm_active"])
                if self._gpu_metrics["sm_active"] else 0
            ),
            "avg_tensor_active": (
                sum(self._gpu_metrics["tensor_active"]) /
                len(self._gpu_metrics["tensor_active"])
                if self._gpu_metrics["tensor_active"] else 0
            ),
            "avg_dram_active": (
                sum(self._gpu_metrics["dram_active"]) /
                len(self._gpu_metrics["dram_active"])
                if self._gpu_metrics["dram_active"] else 0
            ),
        }
```

### 10.3 Documentation Updates

#### 10.3.1 Add to README.md

```markdown
## GPU Metrics (Simulated)

FakeAI provides simulated GPU profiling metrics that mimic real NVIDIA DCGM behavior.

### Available Metrics

- **SM Active**: Streaming Multiprocessor utilization
- **SM Occupancy**: Warp occupancy ratio
- **Tensor Active**: Tensor Core utilization
- **DRAM Active**: Memory bandwidth utilization
- **PCIe Bandwidth**: CPU-GPU transfer bandwidth
- **FLOPS**: Estimated floating point operations per second

### Accessing GPU Metrics

```bash
curl http://localhost:8000/v1/gpu_metrics
```

### Metrics Endpoint

**GET /v1/gpu_metrics**

Returns simulated GPU profiling metrics based on current workload.
```

---

## 11. References and Resources

### 11.1 Official Documentation

1. **NVIDIA DCGM Documentation**
   - https://docs.nvidia.com/datacenter/dcgm/latest/
   - Comprehensive API reference and user guide

2. **DCGM Field Identifiers**
   - https://docs.nvidia.com/datacenter/dcgm/latest/dcgm-api/dcgm-api-field-ids.html
   - Complete list of all field IDs and descriptions

3. **DCGM Profiling API**
   - https://docs.nvidia.com/datacenter/dcgm/latest/dcgm-api/dcgm-api-profiling.html
   - Profiling-specific API documentation

4. **DCGM GitHub Repository**
   - https://github.com/NVIDIA/DCGM
   - Source code and examples

### 11.2 Related Tools

1. **nvidia-smi**: Basic GPU monitoring tool
2. **Nsight Systems**: System-wide profiling
3. **Nsight Compute**: Kernel-level profiling
4. **dcgmi**: Command-line interface for DCGM
5. **dcgm-exporter**: Prometheus exporter for DCGM metrics

### 11.3 Performance Analysis Resources

1. **NVIDIA Technical Blog: Monitoring GPUs in Kubernetes with DCGM**
   - https://developer.nvidia.com/blog/monitoring-gpus-in-kubernetes-with-dcgm/

2. **LLM Inference Performance Engineering Best Practices**
   - Detailed guide on optimizing LLM inference

3. **Understanding GPU Performance Counters**
   - NVIDIA GTC talks and presentations

---

## 12. Conclusion

NVIDIA DCGM profiling provides comprehensive, fine-grained GPU performance metrics essential for:
- Understanding workload characteristics
- Identifying performance bottlenecks
- Optimizing GPU utilization
- Monitoring production deployments

**Key Takeaways**:

1. **Two Modes**: Monitoring (low overhead) vs Profiling (detailed metrics)
2. **12 Core Metrics**: Field IDs 1001-1012 cover all major GPU subsystems
3. **Multiplexing**: Some metrics cannot be collected simultaneously
4. **LLM Inference**: Different patterns for prefill (compute bound) vs decode (memory bound)
5. **Derived Metrics**: Calculate FLOPS, MFU, MBU from profiling data
6. **Best Practices**: Match metrics to workload type, accept trade-offs

**For FakeAI Integration**:
- Simulate realistic GPU metrics based on request characteristics
- Provide metrics endpoint for observability
- Help users understand GPU behavior without real hardware

This research provides a foundation for implementing GPU metrics in FakeAI or understanding real GPU profiling in production environments.
