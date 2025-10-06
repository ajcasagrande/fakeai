# GPU Architecture-Specific Metrics Catalog

**Version:** 1.0.0
**Last Updated:** 2025-10-04
**Purpose:** Comprehensive catalog of GPU architecture-specific metrics for Ampere, Hopper, and Blackwell architectures

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [NVIDIA Ampere Architecture (A100, A30)](#2-nvidia-ampere-architecture-a100-a30)
3. [NVIDIA Hopper Architecture (H100, H200)](#3-nvidia-hopper-architecture-h100-h200)
4. [NVIDIA Blackwell Architecture (B100, B200, GB200)](#4-nvidia-blackwell-architecture-b100-b200-gb200)
5. [Multi-Instance GPU (MIG) Metrics](#5-multi-instance-gpu-mig-metrics)
6. [NVSwitch and NVLink Metrics](#6-nvswitch-and-nvlink-metrics)
7. [Memory Hierarchy Metrics](#7-memory-hierarchy-metrics)
8. [DCGM Field Identifiers](#8-dcgm-field-identifiers)
9. [Cross-Architecture Comparison](#9-cross-architecture-comparison)
10. [Implementation Considerations](#10-implementation-considerations)

---

## 1. Executive Summary

### Key Findings

This document catalogs GPU architecture-specific metrics across three NVIDIA datacenter GPU generations: Ampere, Hopper, and Blackwell. Key architectural innovations include:

- **Ampere**: Multi-Instance GPU (MIG), third-generation Tensor Cores, HBM2e memory
- **Hopper**: Fourth-generation Tensor Cores with FP8, Transformer Engine, HBM3, NVLink 4.0
- **Blackwell**: Fifth-generation Tensor Cores with FP4, second-generation Transformer Engine, dual-die design, HBM3e, NVLink 5.0

### DCGM Limitations

**Critical Note**: As of 2025, DCGM has limited support for newer precision formats:
-  Supported: FP64, FP32, FP16, TF32, Tensor Core activity
-  Not Supported: FP8 (Hopper), FP4 (Blackwell), Transformer Engine-specific metrics
-  Limited: Architecture-specific profiling on older DCGM versions

### Architecture Evolution Timeline

```
2020: Ampere A100  → MIG, 3rd Gen Tensor Cores, HBM2e
2022: Hopper H100  → FP8, Transformer Engine, HBM3, NVLink 4.0
2024: Blackwell B200 → FP4, 2nd Gen Transformer Engine, HBM3e, NVLink 5.0
```

---

## 2. NVIDIA Ampere Architecture (A100, A30)

### 2.1 Architecture Overview

**Release**: 2020
**Process**: TSMC 7nm
**Transistors**: 54.2 billion
**Die Size**: 826 mm²

### 2.2 Compute Resources

#### A100 SXM4-80GB Specifications

| Component | Specification |
|-----------|--------------|
| **Streaming Multiprocessors (SMs)** | 108 SMs (full GH100 has 128) |
| **CUDA Cores** | 6,912 FP32 cores |
| **Tensor Cores** | 432 (third generation) |
| **FP64 Performance** | 9.7 TFLOPS |
| **FP32 Performance** | 19.5 TFLOPS |
| **FP16 Performance** | 312 TFLOPS (Tensor Core) |
| **TF32 Performance** | 156 TFLOPS (Tensor Core) |

#### A30-24GB Specifications

| Component | Specification |
|-----------|--------------|
| **Streaming Multiprocessors (SMs)** | 56 SMs |
| **CUDA Cores** | 3,584 FP32 cores |
| **Tensor Cores** | 224 (third generation) |
| **FP32 Performance** | 10.3 TFLOPS |
| **FP16 Performance** | 165 TFLOPS (Tensor Core) |

### 2.3 Memory System

#### A100 Memory Specifications

| Component | Specification |
|-----------|--------------|
| **Memory Type** | HBM2e |
| **Memory Capacity** | 40GB (SXM4-40GB) / 80GB (SXM4-80GB) |
| **Memory Bandwidth** | 1,555 GB/s (40GB) / 2,039 GB/s (80GB) |
| **Memory Bus Width** | 5,120-bit |
| **L2 Cache Size** | 40 MB |
| **Memory Controllers** | 10 × 512-bit controllers |

#### Memory Architecture

- **8×5GB memory slices** (40GB model) or **8×10GB slices** (80GB model)
- **7 SM slices** for MIG partitioning
- Each MIG instance gets isolated memory controllers and L2 cache banks

### 2.4 Interconnect

#### NVLink 3.0

| Metric | Value |
|--------|-------|
| **NVLink Generation** | 3.0 |
| **Links per GPU** | 12 |
| **Bandwidth per Link** | 50 GB/s bidirectional |
| **Total GPU Bandwidth** | 600 GB/s |
| **NVSwitch Version** | 2.0 (36 ports × 50 GB/s) |

#### PCIe

| Metric | Value |
|--------|-------|
| **PCIe Generation** | Gen 4 |
| **PCIe Lanes** | x16 |
| **PCIe Bandwidth** | 64 GB/s bidirectional |

### 2.5 Multi-Instance GPU (MIG)

#### MIG Overview

- Partition GPU into up to **7 isolated instances**
- Each instance: isolated memory, cache, SMs
- Hardware-level QoS and isolation

#### A100-40GB MIG Profiles

| Profile | GPU Slices | Memory | SMs | L2 Cache | Memory BW |
|---------|------------|--------|-----|----------|-----------|
| **1g.5gb** | 1/7 | 5 GB | 14 | 5.7 MB | ~194 GB/s |
| **2g.10gb** | 2/7 | 10 GB | 28 | 11.4 MB | ~388 GB/s |
| **3g.20gb** | 3/7 | 20 GB | 42 | 17.1 MB | ~776 GB/s |
| **4g.20gb** | 4/7 | 20 GB | 56 | 22.9 MB | ~776 GB/s |
| **7g.40gb** | 7/7 | 40 GB | 98 | 40 MB | 1,555 GB/s |

#### A100-80GB MIG Profiles

| Profile | GPU Slices | Memory | SMs | L2 Cache | Memory BW |
|---------|------------|--------|-----|----------|-----------|
| **1g.10gb** | 1/7 | 10 GB | 14 | 5.7 MB | ~291 GB/s |
| **2g.20gb** | 2/7 | 20 GB | 28 | 11.4 MB | ~582 GB/s |
| **3g.40gb** | 3/7 | 40 GB | 42 | 17.1 MB | ~1,164 GB/s |
| **4g.40gb** | 4/7 | 40 GB | 56 | 22.9 MB | ~1,164 GB/s |
| **7g.80gb** | 7/7 | 80 GB | 98 | 40 MB | 2,039 GB/s |

#### A30-24GB MIG Profiles

| Profile | GPU Slices | Memory | SMs |
|---------|------------|--------|-----|
| **1g.6gb** | 1/4 | 6 GB | 14 |
| **2g.12gb** | 2/4 | 12 GB | 28 |
| **4g.24gb** | 4/4 | 24 GB | 56 |

### 2.6 Power and Thermal

| Metric | A100 SXM4-80GB | A100 PCIe-80GB | A30-24GB |
|--------|----------------|----------------|----------|
| **TDP** | 400W | 300W | 165W |
| **Max Temperature** | 83°C | 83°C | 83°C |
| **Idle Power** | ~40W | ~30W | ~25W |

### 2.7 DCGM Metrics for Ampere

#### Supported Metrics

 **Compute Metrics**:
- `DCGM_FI_PROF_SM_ACTIVE` - SM active ratio
- `DCGM_FI_PROF_SM_OCCUPANCY` - SM occupancy
- `DCGM_FI_PROF_PIPE_FP16_ACTIVE` - FP16 pipeline activity
- `DCGM_FI_PROF_PIPE_FP32_ACTIVE` - FP32 pipeline activity
- `DCGM_FI_PROF_PIPE_FP64_ACTIVE` - FP64 pipeline activity
- `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` - Tensor Core activity

 **Memory Metrics**:
- `DCGM_FI_PROF_DRAM_ACTIVE` - DRAM active percentage
- `DCGM_FI_DEV_FB_FREE` - Framebuffer memory free
- `DCGM_FI_DEV_FB_USED` - Framebuffer memory used
- `DCGM_FI_DEV_MEM_CLOCK` - Memory clock frequency

 **Interconnect Metrics**:
- `DCGM_FI_PROF_NVLINK_RX_BYTES` - NVLink receive bytes
- `DCGM_FI_PROF_NVLINK_TX_BYTES` - NVLink transmit bytes
- `DCGM_FI_PROF_PCIE_RX_BYTES` - PCIe receive bytes
- `DCGM_FI_PROF_PCIE_TX_BYTES` - PCIe transmit bytes

#### MIG Monitoring Limitations

**IMPORTANT**: On Ampere GPUs, NVML/nvidia-smi does NOT support attribution of utilization metrics to MIG devices.

**Recommended Solution**: Use **DCGM v2.0.13 or later** for MIG device monitoring with proper metric attribution.

---

## 3. NVIDIA Hopper Architecture (H100, H200)

### 3.1 Architecture Overview

**Release**: 2022 (H100), 2023 (H200)
**Process**: TSMC 4N (Custom 5nm-class)
**Transistors**: 80 billion
**Die Size**: 814 mm²

### 3.2 Compute Resources

#### H100 SXM5-80GB Specifications

| Component | Specification |
|-----------|--------------|
| **Streaming Multiprocessors (SMs)** | 132 SMs (full GH100 has 144) |
| **CUDA Cores** | 16,896 FP32 cores |
| **Tensor Cores** | 528 (fourth generation) |
| **FP64 Performance** | 34 TFLOPS (67 TFLOPS with sparsity) |
| **FP32 Performance** | 67 TFLOPS |
| **TF32 Performance** | 989 TFLOPS (1,979 TFLOPS with sparsity) |
| **FP16 Performance** | 1,979 TFLOPS (3,958 TFLOPS with sparsity) |
| **FP8 Performance** | 3,958 TFLOPS (7,916 TFLOPS with sparsity) |

#### H100 PCIe-80GB Specifications

| Component | Specification |
|-----------|--------------|
| **Streaming Multiprocessors (SMs)** | 114 SMs |
| **CUDA Cores** | 14,592 FP32 cores |
| **Tensor Cores** | 456 (fourth generation) |
| **TF32 Performance** | 756 TFLOPS |
| **FP16 Performance** | 1,513 TFLOPS |
| **FP8 Performance** | 3,026 TFLOPS |

#### H200 SXM-141GB Specifications

| Component | Specification |
|-----------|--------------|
| **Streaming Multiprocessors (SMs)** | 132 SMs (same as H100) |
| **Performance** | Same as H100 SXM5 |
| **Key Difference** | 141GB HBM3e memory |

### 3.3 Memory System

#### H100 Memory Specifications

| Component | H100 SXM5-80GB | H100 PCIe-80GB |
|-----------|----------------|----------------|
| **Memory Type** | HBM3 | HBM3 |
| **Memory Capacity** | 80 GB | 80 GB |
| **Memory Bandwidth** | 3,350 GB/s | 2,000 GB/s |
| **Memory Bus Width** | 5,120-bit | 5,120-bit |
| **Memory Stacks** | 5 stacks | 5 stacks |
| **Memory Speed** | 6.4 Gb/s (819 GB/s per stack) | ~4.8 Gb/s |
| **L2 Cache Size** | 50 MB (60 MB in full GH100) | 50 MB |
| **Memory Controllers** | 10 × 512-bit controllers | 10 × 512-bit controllers |

#### H200 Memory Specifications

| Component | H200 SXM-141GB |
|-----------|----------------|
| **Memory Type** | HBM3e (enhanced) |
| **Memory Capacity** | 141 GB |
| **Memory Bandwidth** | 4,800 GB/s |
| **Memory Speed** | 8 GT/s (1 TB/s per stack) |
| **Performance Improvement** | 1.64× vs H100 |

#### Memory Hierarchy

```
Registers (per SM)
    ↓
Shared Memory (per SM) - 228 KB
    ↓
L1 Cache (per SM) - 256 KB
    ↓
L2 Cache (shared) - 50 MB (1.25× larger than A100)
    ↓
HBM3/HBM3e - 80-141 GB (3.35-4.8 TB/s)
```

### 3.4 Fourth-Generation Tensor Cores

#### Key Innovations

1. **FP8 Support**: New 8-bit floating-point format
   - 2× computational throughput vs FP16
   - 4× computational throughput vs FP16 on A100

2. **Transformer Engine**:
   - Per-layer statistical analysis
   - Dynamic precision selection (FP8 vs FP16)
   - Software + hardware integration
   - Up to 6× faster inference vs A100
   - Up to 9× faster training vs A100

3. **Supported Precision Formats**:
   - FP64 (double precision)
   - FP32 (single precision)
   - TF32 (TensorFloat-32, 19-bit)
   - FP16 (half precision)
   - BF16 (Brain Float-16)
   - **FP8** (new in Hopper)
   - INT8 (integer)

#### Performance Comparison: A100 vs H100

| Precision | A100 (TFLOPS) | H100 (TFLOPS) | Speedup |
|-----------|---------------|---------------|---------|
| **FP64** | 9.7 | 34 | 3.5× |
| **FP32** | 19.5 | 67 | 3.4× |
| **TF32** | 156 | 989 | 6.3× |
| **FP16** | 312 | 1,979 | 6.3× |
| **FP8** | N/A | 3,958 | New |

### 3.5 Interconnect

#### NVLink 4.0

| Metric | Value |
|--------|-------|
| **NVLink Generation** | 4.0 |
| **Links per GPU** | 18 |
| **Bandwidth per Link** | 50 GB/s bidirectional |
| **Total GPU Bandwidth** | 900 GB/s |
| **NVSwitch Version** | 3.0 (64 ports) |
| **NVSwitch Bandwidth** | 14.4 TB/s (per switch) |
| **SerDes Speed** | 112 Gbps per lane |
| **Speedup vs NVLink 3.0** | 1.5× bandwidth |

#### PCIe

| Metric | Value |
|--------|-------|
| **PCIe Generation** | Gen 5 |
| **PCIe Lanes** | x16 |
| **PCIe Bandwidth** | 128 GB/s bidirectional |
| **Speedup vs Gen 4** | 2× bandwidth |

#### DGX H100 Topology

- **8 H100 GPUs** per node
- **4 NVSwitch 3.0** chips per node
- Full GPU-to-GPU connectivity at 900 GB/s
- Hybrid cube-mesh topology

### 3.6 MIG on Hopper

#### H100 MIG Profiles

| Profile | GPU Slices | Memory | SMs | Tensor Cores |
|---------|------------|--------|-----|--------------|
| **1g.10gb** | 1/7 | 10 GB | 18 | ~72 |
| **1g.20gb** | 1/7 | 20 GB | 18 | ~72 |
| **2g.20gb** | 2/7 | 20 GB | 36 | ~144 |
| **3g.40gb** | 3/7 | 40 GB | 54 | ~216 |
| **4g.40gb** | 4/7 | 40 GB | 72 | ~288 |
| **7g.80gb** | 7/7 | 80 GB | 132 | 528 |

**Note**: H100 supports more flexible MIG profiles than A100, including dual memory configurations (1g.10gb and 1g.20gb).

### 3.7 Power and Thermal

| Metric | H100 SXM5 | H100 PCIe | H200 SXM |
|--------|-----------|-----------|----------|
| **TDP** | 700W | 350W | 700W |
| **Max Temperature** | 89°C | 83°C | 89°C |
| **Idle Power** | ~50W | ~35W | ~50W |
| **TDP Increase vs A100** | 75% | 17% | 75% |

### 3.8 DCGM Metrics for Hopper

#### Supported Metrics

 **All Ampere metrics** (see section 2.7)

 **Enhanced Profiling** (GKE 1.32.0+ or DCGM 3.0+):
- Full profiling metrics for H100
- Better MIG attribution
- Improved NVLink bandwidth monitoring

 **Missing Metrics** (as of 2025):
- `DCGM_FI_PROF_PIPE_FP8_ACTIVE` - Not available
- Transformer Engine utilization - Not available
- Per-layer precision tracking - Not available

**GitHub Issue**: [NVIDIA/dcgm-exporter#173](https://github.com/NVIDIA/dcgm-exporter/issues/173) - Support for FP8 and Transformer Engine usage

#### Workaround for FP8 Monitoring

Currently, you must infer FP8 usage from:
1. Application-level instrumentation
2. Tensor Core activity (`DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`)
3. Memory bandwidth utilization
4. CUDA kernel names (via profiling tools)

---

## 4. NVIDIA Blackwell Architecture (B100, B200, GB200)

### 4.1 Architecture Overview

**Release**: 2024
**Process**: TSMC 4NP (Custom 4nm)
**Transistors**: 208 billion (dual-die)
**Die Configuration**: 2× reticle-limited dies connected via NV-HBI

### 4.2 Dual-Die Design

#### Key Innovation: NV-High Bandwidth Interface (NV-HBI)

| Metric | Value |
|--------|-------|
| **Interface Type** | Chip-to-chip interconnect |
| **Bandwidth** | 10 TB/s |
| **Protocol** | NVLink 7 protocol |
| **Connection** | Two GB100 dies in single package |
| **Transparency** | Appears as single unified GPU |

### 4.3 Compute Resources

#### B200 SXM-192GB Specifications

| Component | Specification |
|-----------|--------------|
| **Streaming Multiprocessors (SMs)** | 256 SMs (total across both dies) |
| **CUDA Cores** | ~32,768 FP32 cores |
| **Tensor Cores** | 1,024 (fifth generation) |
| **FP64 Performance** | ~68 TFLOPS |
| **FP32 Performance** | ~134 TFLOPS |
| **TF32 Performance** | ~2,250 TFLOPS |
| **FP16/BF16 Performance** | 2,250 TFLOPS |
| **FP8 Performance** | 9,000 TFLOPS |
| **FP4 Performance** | 18,000 TFLOPS (new) |

#### B100 Air-Cooled-192GB Specifications

| Component | Specification |
|-----------|--------------|
| **TDP** | 700W (vs B200's higher TDP) |
| **FP16/BF16 Performance** | 1,750 TFLOPS |
| **Clock Speed** | Lower than B200 |
| **Cooling** | Air-cooled (vs liquid-cooled B200) |

#### GB200 NVL72 Superchip

| Component | Specification |
|-----------|--------------|
| **Configuration** | 36× GB200 nodes |
| **GPUs** | 72× B200 GPUs |
| **CPUs** | 36× Grace CPUs |
| **Total GPU Memory** | 13.5 TB (72 × 192GB) |
| **GPU-GPU Bandwidth** | 130 TB/s (via NVLink 5.0) |
| **Memory Instances** | 2× 95GB, 4× 45GB, or 7× 23GB per GPU |

### 4.4 Memory System

#### B200 Memory Specifications

| Component | Specification |
|-----------|--------------|
| **Memory Type** | HBM3e |
| **Memory Capacity** | 192 GB |
| **Memory Bandwidth** | 8 TB/s |
| **Memory Stacks** | 8 stacks |
| **Memory Speed** | 8+ GT/s |
| **Bandwidth per Stack** | 1 TB/s |
| **L2 Cache Size** | ~100 MB (estimated, dual-die) |

#### Memory Improvements

| Metric | H100 | H200 | B200 | Improvement (H100→B200) |
|--------|------|------|------|------------------------|
| **Capacity** | 80 GB | 141 GB | 192 GB | 2.4× |
| **Bandwidth** | 3.35 TB/s | 4.8 TB/s | 8 TB/s | 2.4× |
| **Memory Type** | HBM3 | HBM3e | HBM3e | - |

### 4.5 Fifth-Generation Tensor Cores

#### Second-Generation Transformer Engine

**Key Innovations**:

1. **FP4 Support**:
   - 4-bit floating-point precision
   - 2× performance vs FP8
   - 4× performance vs FP16
   - Maintains high accuracy with micro-tensor scaling

2. **Micro-Tensor Scaling**:
   - Fine-grain scaling at "tens of elements" level
   - Hardware-accelerated FP4 operations
   - Dynamic per-block scaling factors
   - Superior to per-tensor or per-channel scaling

3. **Performance Metrics**:
   - Up to 4× faster training than H100
   - Up to 15× faster inference than H100 (on GPT-MoE-1.8T)
   - Doubles model size capacity in memory

#### MLPerf Benchmark Results

| Workload | H100 (tokens/sec) | B200 (tokens/sec) | Speedup |
|----------|-------------------|-------------------|---------|
| **Single GPU Inference** | ~2,900 | ~10,755 | 3.7× |
| **Offline Reference** | ~3,000 | ~11,264 | 3.75× |

#### Supported Precision Formats

| Format | Bits | Use Case | Performance (TFLOPS) |
|--------|------|----------|---------------------|
| **FP64** | 64 | Scientific computing | ~68 |
| **FP32** | 32 | General compute | ~134 |
| **TF32** | 19 | Deep learning | ~2,250 |
| **FP16** | 16 | Training | 2,250 |
| **BF16** | 16 | Training | 2,250 |
| **FP8** | 8 | Inference/training | 9,000 |
| **FP4** | 4 | Inference (new) | 18,000 |
| **INT8** | 8 | Quantized inference | ~18,000 |

### 4.6 Interconnect

#### NVLink 5.0

| Metric | Value |
|--------|-------|
| **NVLink Generation** | 5.0 |
| **Links per GPU** | 18 |
| **Bandwidth per Link** | 100 GB/s bidirectional |
| **Total GPU Bandwidth** | 1,800 GB/s (1.8 TB/s) |
| **SerDes Speed** | 224 Gbps per lane |
| **Speedup vs NVLink 4.0** | 2× bandwidth |
| **Speedup vs PCIe Gen5** | 14× bandwidth |

#### NVSwitch 5.0

| Metric | Value |
|--------|-------|
| **Switch Ports** | 144 NVLink ports |
| **Switch Bandwidth** | 14.4 TB/s (non-blocking) |
| **Total Bidirectional BW** | 25.6 Tbps (per switch) |

#### GB200 NVL72 Topology

- **72 B200 GPUs** + **36 Grace CPUs**
- **18 NVSwitch 5.0** chips (2 per tray, 9 trays)
- Each B200 has 18 NVLink ports → one per NVSwitch
- **130 TB/s** total GPU-to-GPU bandwidth
- Full all-to-all GPU connectivity

### 4.7 Power and Thermal

| Metric | B100 | B200 | GB200 NVL72 |
|--------|------|------|-------------|
| **TDP per GPU** | 700W | ~1,000W | ~72 kW (total) |
| **Cooling** | Air | Liquid | Liquid |
| **Max Temperature** | ~85°C | ~90°C | - |
| **Power Efficiency** | High | Ultra-high | Optimized |

### 4.8 DCGM Metrics for Blackwell

#### Expected Support (Based on Architecture)

 **Likely Supported** (Standard Metrics):
- All Hopper profiling metrics
- Enhanced NVLink 5.0 bandwidth monitoring
- Dual-die memory metrics
- MIG support (similar profiles to Hopper)

 **Not Yet Supported** (as of 2025-10):
- `DCGM_FI_PROF_PIPE_FP4_ACTIVE` - Not available
- Second-generation Transformer Engine metrics
- Micro-tensor scaling statistics
- FP4 utilization tracking
- Per-die metrics (dual-die monitoring)

 **Status**: Blackwell production began in 2024-2025, DCGM support may be limited initially

#### Monitoring Considerations

1. **Dual-Die Metrics**: Need new DCGM fields to track per-die utilization
2. **NV-HBI Monitoring**: 10 TB/s chip-to-chip link bandwidth
3. **FP4 Precision**: Application-level tracking required until DCGM support
4. **GB200 Specific**: Grace CPU + B200 GPU metrics coordination

---

## 5. Multi-Instance GPU (MIG) Metrics

### 5.1 MIG Architecture Overview

**Purpose**: Partition single physical GPU into multiple isolated instances

**Key Features**:
- Hardware-level isolation
- Dedicated memory, cache, SMs
- Predictable QoS
- Up to 7 instances per GPU

### 5.2 MIG Profile Naming Convention

**Format**: `{SM_slices}g.{memory_size}gb`

**Examples**:
- `1g.5gb` = 1 SM slice, 5GB memory
- `3g.40gb` = 3 SM slices, 40GB memory
- `7g.80gb` = Full GPU (all 7 slices, 80GB)

### 5.3 Compute Instances (CI)

Each GPU Instance (GI) can be further subdivided into Compute Instances:
- **GI**: GPU Instance (memory + SMs + L2 cache)
- **CI**: Compute Instance (subset of GI's SMs, shares memory)

**Use Case**: Multiple workloads sharing same memory pool but with SM isolation

### 5.4 Cross-Architecture MIG Comparison

| Feature | A100-80GB | H100-80GB | B200-192GB |
|---------|-----------|-----------|------------|
| **Max Instances** | 7 | 7 | 7 (estimated) |
| **SM Slices** | 7 fractions | 7 fractions | 7 fractions |
| **Memory Slices** | 8 fractions | 8 fractions | 8 fractions |
| **Smallest Profile** | 1g.10gb | 1g.10gb | ~1g.23gb |
| **Flexible Configs** | Limited | Enhanced | Advanced |

### 5.5 MIG Metrics via DCGM

#### Standard GPU Metrics (per MIG instance)

 **Available**:
- `DCGM_FI_DEV_GPU_UTIL` - GPU utilization
- `DCGM_FI_DEV_MEM_COPY_UTIL` - Memory copy utilization
- `DCGM_FI_DEV_FB_FREE` - Free framebuffer memory
- `DCGM_FI_DEV_FB_USED` - Used framebuffer memory
- `DCGM_FI_DEV_POWER_USAGE` - Power consumption
- `DCGM_FI_DEV_GPU_TEMP` - GPU temperature

#### Profiling Metrics (per MIG instance)

 **Available** (DCGM v2.0.13+):
- `DCGM_FI_PROF_SM_ACTIVE` - SM activity ratio
- `DCGM_FI_PROF_SM_OCCUPANCY` - SM occupancy
- `DCGM_FI_PROF_DRAM_ACTIVE` - Memory bandwidth utilization
- `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` - Tensor Core activity
- `DCGM_FI_PROF_PIPE_FP16_ACTIVE` - FP16 pipeline activity
- `DCGM_FI_PROF_PIPE_FP32_ACTIVE` - FP32 pipeline activity
- `DCGM_FI_PROF_PIPE_FP64_ACTIVE` - FP64 pipeline activity

#### MIG Identification

```bash
# List MIG devices
nvidia-smi mig -lgi

# Query MIG device metrics via DCGM
dcgmi dmon -e 150,155,203,204 -i <mig_device_id>
```

#### MIG Limitations

 **Not Available on Ampere via nvidia-smi**:
- Utilization metrics attribution
- Per-instance profiling

 **Solution**: Use DCGM v2.0.13+ for full MIG monitoring

### 5.6 MIG Use Cases

| Use Case | Recommended Profile | Rationale |
|----------|-------------------|-----------|
| **Inference (small models)** | 1g.5gb / 1g.10gb | Minimize resource waste |
| **Inference (medium models)** | 2g.20gb / 3g.40gb | Balance throughput & latency |
| **Training (small batch)** | 3g.40gb | Adequate memory + compute |
| **Training (large batch)** | 7g.80gb | Full GPU for max throughput |
| **Multi-tenant** | Mix of 1g/2g/3g | Flexible resource allocation |

---

## 6. NVSwitch and NVLink Metrics

### 6.1 NVLink Evolution

| Generation | Bandwidth per Link | Links per GPU | Total BW per GPU | GPU Architecture | Year |
|------------|-------------------|---------------|------------------|------------------|------|
| **NVLink 1.0** | 20 GB/s | 4-6 | 80-120 GB/s | Pascal (P100) | 2016 |
| **NVLink 2.0** | 25 GB/s | 6-12 | 150-300 GB/s | Volta (V100) | 2017 |
| **NVLink 3.0** | 50 GB/s | 12 | 600 GB/s | Ampere (A100) | 2020 |
| **NVLink 4.0** | 50 GB/s | 18 | 900 GB/s | Hopper (H100) | 2022 |
| **NVLink 5.0** | 100 GB/s | 18 | 1,800 GB/s | Blackwell (B200) | 2024 |

### 6.2 NVSwitch Evolution

| Version | Ports | Bandwidth per Port | Total Switch BW | GPU Support |
|---------|-------|-------------------|-----------------|-------------|
| **NVSwitch 1.0** | 18 | 50 GB/s | 900 GB/s | V100 (DGX-2) |
| **NVSwitch 2.0** | 36 | 50 GB/s | 1,800 GB/s | A100 (DGX A100) |
| **NVSwitch 3.0** | 64 | 50 GB/s | 3,200 GB/s | H100 (DGX H100) |
| **NVSwitch 5.0** | 144 | 100 GB/s | 14,400 GB/s | B200 (GB200 NVL72) |

**Note**: Total bidirectional bandwidth per NVSwitch 3.0 = **25.6 Tbps**

### 6.3 Topology Architectures

#### DGX-1 (Pascal P100)
- **8 GPUs** in hybrid cube-mesh topology
- **NVLink 1.0** (6 links per GPU)
- Direct GPU-to-GPU connections

#### DGX-2 (Volta V100)
- **16 GPUs** fully connected
- **6 NVSwitch 1.0** chips
- First system with NVSwitch

#### DGX A100 (Ampere)
- **8 GPUs** fully connected
- **6 NVSwitch 2.0** chips
- Each GPU → 12 NVLink → 6 NVSwitch (2 links per switch)

#### DGX H100 (Hopper)
- **8 GPUs** fully connected
- **4 NVSwitch 3.0** chips
- Each GPU → 18 NVLink connections

#### GB200 NVL72 (Blackwell)
- **72 GPUs** + **36 Grace CPUs**
- **18 NVSwitch 5.0** chips (9 switch trays)
- Each GPU → 18 NVLink → 18 NVSwitch (1 per switch)
- **130 TB/s** total GPU bandwidth

### 6.4 NVLink Metrics via DCGM

#### Available Metrics

 **Bandwidth Metrics**:
- `DCGM_FI_PROF_NVLINK_RX_BYTES` - NVLink receive bytes
- `DCGM_FI_PROF_NVLINK_TX_BYTES` - NVLink transmit bytes

**Note**: TX = GPU transmitting, RX = GPU receiving

#### Per-Link Metrics

```bash
# Query NVLink status
nvidia-smi nvlink --status

# Query NVLink bandwidth counters
nvidia-smi nvlink --capabilities

# DCGM NVLink monitoring
dcgmi dmon -e 1002,1003 -i 0
```

#### Derived Metrics

Calculate from raw counters:
- **NVLink Utilization** = `(TX_BYTES + RX_BYTES) / (LINK_BANDWIDTH × TIME × NUM_LINKS)`
- **Effective Bandwidth** = `(TX_BYTES + RX_BYTES) / TIME`
- **Link Imbalance** = Variance across links

### 6.5 NVLink Topology Discovery

#### nvidia-smi Topology Commands

```bash
# Show GPU interconnect topology
nvidia-smi topo -m

# Show NVLink connections
nvidia-smi topo -p2p r

# Show NVSwitch topology
nvidia-smi topo --nvswitch
```

#### Example Output (DGX H100)

```
     GPU0  GPU1  GPU2  GPU3  GPU4  GPU5  GPU6  GPU7
GPU0  X    NV18  NV18  NV18  NV18  NV18  NV18  NV18
GPU1 NV18   X    NV18  NV18  NV18  NV18  NV18  NV18
GPU2 NV18  NV18   X    NV18  NV18  NV18  NV18  NV18
...
```

**NV18** = NVLink 4.0 (18 links × 50 GB/s = 900 GB/s)

### 6.6 PCIe vs NVLink Performance

| Interconnect | Bandwidth | Latency | Use Case |
|--------------|-----------|---------|----------|
| **PCIe Gen3 x16** | 32 GB/s | ~1-2 μs | CPU-GPU, storage |
| **PCIe Gen4 x16** | 64 GB/s | ~1 μs | CPU-GPU, storage |
| **PCIe Gen5 x16** | 128 GB/s | ~800 ns | CPU-GPU, NVMe |
| **NVLink 3.0** | 600 GB/s | ~500 ns | GPU-GPU (A100) |
| **NVLink 4.0** | 900 GB/s | ~400 ns | GPU-GPU (H100) |
| **NVLink 5.0** | 1,800 GB/s | ~300 ns | GPU-GPU (B200) |

**Speedup**: NVLink 5.0 is **14× faster** than PCIe Gen5

### 6.7 NVLink Error Metrics

#### Available Error Counters

- `DCGM_FI_DEV_NVLINK_CRC_FLIT_ERROR_COUNT_*` - CRC errors per link
- `DCGM_FI_DEV_NVLINK_CRC_DATA_ERROR_COUNT_*` - Data errors per link
- `DCGM_FI_DEV_NVLINK_REPLAY_ERROR_COUNT_*` - Replay errors per link
- `DCGM_FI_DEV_NVLINK_RECOVERY_ERROR_COUNT_*` - Recovery errors per link

**Critical**: Monitor for hardware faults in production systems

---

## 7. Memory Hierarchy Metrics

### 7.1 Memory Hierarchy Overview

```
Fastest, Smallest
    ↓

 Registers (per thread)   ~64 KB per SM

 Shared Memory (per SM)   96-228 KB per SM

 L1 Cache (per SM)        128-256 KB per SM

 L2 Cache (shared)        40-60 MB

 HBM (global memory)      40-192 GB, 1.5-8 TB/s

    ↓
Slowest, Largest
```

### 7.2 L2 Cache Specifications

| Architecture | L2 Cache Size | L2 Bandwidth | Cache Line Size |
|--------------|---------------|--------------|-----------------|
| **Ampere A100** | 40 MB | ~7 TB/s | 128 bytes |
| **Hopper H100** | 50 MB | ~9 TB/s | 128 bytes |
| **Hopper H200** | 50 MB | ~9 TB/s | 128 bytes |
| **Blackwell B200** | ~100 MB (est) | ~18 TB/s (est) | 128 bytes |

### 7.3 HBM Memory Specifications

#### HBM2e (Ampere)

| Specification | A100-40GB | A100-80GB |
|---------------|-----------|-----------|
| **Memory Type** | HBM2e | HBM2e |
| **Capacity** | 40 GB | 80 GB |
| **Stacks** | 5 | 5 |
| **Bandwidth per Stack** | ~311 GB/s | ~408 GB/s |
| **Total Bandwidth** | 1,555 GB/s | 2,039 GB/s |
| **Memory Speed** | 2.4 Gbps | 3.2 Gbps |
| **Bus Width** | 5,120-bit | 5,120-bit |

#### HBM3 (Hopper H100)

| Specification | H100 SXM5 | H100 PCIe |
|---------------|-----------|-----------|
| **Memory Type** | HBM3 | HBM3 |
| **Capacity** | 80 GB | 80 GB |
| **Stacks** | 5 | 5 |
| **Bandwidth per Stack** | 819 GB/s | ~400 GB/s |
| **Total Bandwidth** | 3,350 GB/s | 2,000 GB/s |
| **Memory Speed** | 6.4 Gbps | ~4.8 Gbps |
| **Bus Width** | 5,120-bit | 5,120-bit |

#### HBM3e (Hopper H200, Blackwell B200)

| Specification | H200 | B200 |
|---------------|------|------|
| **Memory Type** | HBM3e | HBM3e |
| **Capacity** | 141 GB | 192 GB |
| **Stacks** | 5-6 (est) | 8 |
| **Bandwidth per Stack** | ~800-960 GB/s | 1,000 GB/s |
| **Total Bandwidth** | 4,800 GB/s | 8,000 GB/s |
| **Memory Speed** | 8 GT/s | 8+ GT/s |
| **Bus Width** | ~7,168-bit | ~8,192-bit |

### 7.4 Memory Bandwidth Evolution

| Generation | Memory Type | Bandwidth | Improvement |
|------------|-------------|-----------|-------------|
| **Ampere A100-80GB** | HBM2e | 2,039 GB/s | Baseline |
| **Hopper H100** | HBM3 | 3,350 GB/s | 1.64× |
| **Hopper H200** | HBM3e | 4,800 GB/s | 2.35× |
| **Blackwell B200** | HBM3e | 8,000 GB/s | 3.92× |

### 7.5 Memory Metrics via DCGM

#### Available Metrics

 **Memory Utilization**:
- `DCGM_FI_DEV_FB_FREE` - Free framebuffer memory (MB)
- `DCGM_FI_DEV_FB_USED` - Used framebuffer memory (MB)
- `DCGM_FI_DEV_FB_TOTAL` - Total framebuffer memory (MB)

 **Memory Bandwidth**:
- `DCGM_FI_PROF_DRAM_ACTIVE` - Percentage of cycles DRAM is active
  - **HBM Note**: Memory clock fixed, so this is accurate for bandwidth
- `DCGM_FI_DEV_MEM_CLOCK` - Memory clock frequency (MHz)

 **Memory Temperature**:
- `DCGM_FI_DEV_MEMORY_TEMP` - Memory temperature (°C)

#### Derived Metrics

**Effective Memory Bandwidth**:
```
Effective_BW = DRAM_ACTIVE × Peak_BW
```

**Example (H100)**:
- Peak BW = 3,350 GB/s
- DRAM_ACTIVE = 65%
- Effective BW = 0.65 × 3,350 = 2,177 GB/s

### 7.6 Memory Hierarchy Performance

#### Access Latency (Approximate)

| Memory Type | Latency | Bandwidth (per SM) |
|-------------|---------|-------------------|
| **Registers** | 1 cycle | ~10 TB/s |
| **Shared Memory** | ~30 cycles | ~19 TB/s (Hopper) |
| **L1 Cache Hit** | ~30 cycles | ~19 TB/s |
| **L2 Cache Hit** | ~200 cycles | ~9 TB/s (Hopper) |
| **HBM (L2 miss)** | ~400-600 cycles | 3.35 TB/s (H100) |

#### Cache Hit Rates (Typical)

| Workload | L1 Hit Rate | L2 Hit Rate | HBM Access |
|----------|-------------|-------------|------------|
| **Well-optimized** | 85-95% | 70-85% | 5-15% |
| **Memory-bound** | 50-70% | 40-60% | 30-50% |
| **Compute-bound** | 95-99% | 85-95% | <5% |

### 7.7 Memory Capacity vs Bandwidth Trade-offs

| Model Size | Memory Needed | Bandwidth Needed | Recommended GPU |
|------------|---------------|------------------|-----------------|
| **<20B params** | <40 GB | 1-2 TB/s | A100-40GB |
| **20-70B params** | 40-140 GB | 2-3 TB/s | A100-80GB, H100 |
| **70-175B params** | 140-350 GB | 3-5 TB/s | H200, 2×H100 |
| **175B+ params** | >350 GB | >5 TB/s | 4×H100, GB200 NVL72 |

---

## 8. DCGM Field Identifiers

### 8.1 DCGM Overview

**DCGM** = Data Center GPU Manager
**Purpose**: Monitoring, diagnostics, and management for NVIDIA datacenter GPUs

**Documentation**: [NVIDIA DCGM Field IDs](https://docs.nvidia.com/datacenter/dcgm/latest/dcgm-api/dcgm-api-field-ids.html)

### 8.2 Field ID Categories

| Category | Prefix | Count | Examples |
|----------|--------|-------|----------|
| **Device Info** | `DCGM_FI_DEV_` | ~50 | Model, UUID, serial |
| **Profiling** | `DCGM_FI_PROF_` | ~30 | SM active, pipe utilization |
| **Driver** | `DCGM_FI_DRIVER_` | ~10 | Version, CUDA version |
| **Process** | `DCGM_FI_PROCESS_` | ~5 | Process utilization |
| **NVLink** | `DCGM_FI_DEV_NVLINK_` | ~40 | Errors, throughput |

### 8.3 Essential DCGM Fields for Monitoring

#### Compute Utilization (Field IDs 150-169)

| Field ID | Name | Description | Unit |
|----------|------|-------------|------|
| **150** | `DCGM_FI_DEV_GPU_UTIL` | GPU utilization | % |
| **155** | `DCGM_FI_DEV_MEM_COPY_UTIL` | Memory copy utilization | % |
| **1001** | `DCGM_FI_PROF_GR_ENGINE_ACTIVE` | Graphics/compute engine active | % |
| **1002** | `DCGM_FI_PROF_SM_ACTIVE` | SM has ≥1 warp assigned | % |
| **1003** | `DCGM_FI_PROF_SM_OCCUPANCY` | Warps resident on SM | % |

#### Pipeline Utilization (Field IDs 1004-1007)

| Field ID | Name | Description | Unit |
|----------|------|-------------|------|
| **1004** | `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` | Tensor Core pipeline active | % |
| **1005** | `DCGM_FI_PROF_PIPE_FP64_ACTIVE` | FP64 pipeline active | % |
| **1006** | `DCGM_FI_PROF_PIPE_FP32_ACTIVE` | FP32 pipeline active | % |
| **1007** | `DCGM_FI_PROF_PIPE_FP16_ACTIVE` | FP16 pipeline active | % |

**Missing (as of 2025)**:
- `DCGM_FI_PROF_PIPE_FP8_ACTIVE` - Not yet available
- `DCGM_FI_PROF_PIPE_FP4_ACTIVE` - Not yet available

#### Memory Metrics (Field IDs 200-230)

| Field ID | Name | Description | Unit |
|----------|------|-------------|------|
| **203** | `DCGM_FI_DEV_FB_FREE` | Framebuffer memory free | MiB |
| **204** | `DCGM_FI_DEV_FB_USED` | Framebuffer memory used | MiB |
| **209** | `DCGM_FI_DEV_MEM_CLOCK` | Memory clock | MHz |
| **1008** | `DCGM_FI_PROF_DRAM_ACTIVE` | DRAM active (bandwidth %) | % |

#### NVLink Metrics (Field IDs 1010-1013)

| Field ID | Name | Description | Unit |
|----------|------|-------------|------|
| **1010** | `DCGM_FI_PROF_NVLINK_TX_BYTES` | NVLink transmit bytes | bytes |
| **1011** | `DCGM_FI_PROF_NVLINK_RX_BYTES` | NVLink receive bytes | bytes |

#### PCIe Metrics (Field IDs 1012-1013)

| Field ID | Name | Description | Unit |
|----------|------|-------------|------|
| **1012** | `DCGM_FI_PROF_PCIE_TX_BYTES` | PCIe transmit bytes | bytes |
| **1013** | `DCGM_FI_PROF_PCIE_RX_BYTES` | PCIe receive bytes | bytes |

#### Power and Thermal (Field IDs 140-180)

| Field ID | Name | Description | Unit |
|----------|------|-------------|------|
| **140** | `DCGM_FI_DEV_POWER_USAGE` | Power draw | W |
| **141** | `DCGM_FI_DEV_TOTAL_ENERGY_CONSUMPTION` | Total energy | mJ |
| **150** | `DCGM_FI_DEV_GPU_TEMP` | GPU temperature | °C |
| **156** | `DCGM_FI_DEV_MEMORY_TEMP` | Memory temperature | °C |

#### Clock Frequencies (Field IDs 200-210)

| Field ID | Name | Description | Unit |
|----------|------|-------------|------|
| **200** | `DCGM_FI_DEV_SM_CLOCK` | SM clock | MHz |
| **209** | `DCGM_FI_DEV_MEM_CLOCK` | Memory clock | MHz |

### 8.4 DCGM Profiling Limitations

#### Parallel Query Restrictions

**IMPORTANT**: Not all fields can be queried in parallel. This particularly applies to `*_PROF_*` fields.

**Recommendation**: Query profiling fields in separate DCGM groups or with staggered intervals.

#### Sampling Rate Limits

| Metric Type | Min Interval | Recommended Interval |
|-------------|--------------|---------------------|
| **Standard fields** | 1 ms | 100 ms |
| **Profiling fields** | 10 ms | 1000 ms |
| **Energy fields** | 100 ms | 1000 ms |

### 8.5 DCGM Exporter Configuration

#### Default Metrics CSV

DCGM Exporter uses CSV files to define metrics:

```csv
# Format: DCGM_FI field, Prometheus metric type, help string
DCGM_FI_DEV_GPU_UTIL, gauge, GPU utilization (in %).
DCGM_FI_DEV_FB_FREE, gauge, Framebuffer memory free (in MiB).
DCGM_FI_DEV_POWER_USAGE, gauge, Power draw (in W).
DCGM_FI_PROF_SM_ACTIVE, gauge, SM active ratio (in %).
DCGM_FI_PROF_DRAM_ACTIVE, gauge, DRAM active ratio (in %).
DCGM_FI_PROF_NVLINK_TX_BYTES, counter, NVLink TX bytes.
DCGM_FI_PROF_NVLINK_RX_BYTES, counter, NVLink RX bytes.
```

#### Custom Metrics Example

Create custom CSV for architecture-specific monitoring:

```csv
# Hopper-specific profiling
DCGM_FI_PROF_GR_ENGINE_ACTIVE, gauge, Graphics engine active (%).
DCGM_FI_PROF_SM_OCCUPANCY, gauge, SM occupancy (%).
DCGM_FI_PROF_PIPE_TENSOR_ACTIVE, gauge, Tensor Core active (%).
DCGM_FI_PROF_PIPE_FP16_ACTIVE, gauge, FP16 pipeline active (%).
DCGM_FI_PROF_PIPE_FP32_ACTIVE, gauge, FP32 pipeline active (%).
DCGM_FI_PROF_DRAM_ACTIVE, gauge, DRAM active (%).
DCGM_FI_PROF_NVLINK_TX_BYTES, counter, NVLink transmit bytes.
DCGM_FI_PROF_NVLINK_RX_BYTES, counter, NVLink receive bytes.
DCGM_FI_DEV_MEMORY_TEMP, gauge, Memory temperature (C).
```

### 8.6 DCGM API Reference

**Complete Field List**: [NVIDIA DCGM Documentation](https://docs.nvidia.com/datacenter/dcgm/latest/dcgm-api/dcgm-api-field-ids.html)

**Source Code**: [DCGM GitHub - dcgm_fields.h](https://github.com/NVIDIA/DCGM/blob/master/dcgmlib/dcgm_fields.h)

---

## 9. Cross-Architecture Comparison

### 9.1 Compute Performance Summary

| Metric | A100 | H100 | B200 | A→H Speedup | H→B Speedup |
|--------|------|------|------|-------------|-------------|
| **FP64** | 9.7 TF | 34 TF | 68 TF | 3.5× | 2× |
| **FP32** | 19.5 TF | 67 TF | 134 TF | 3.4× | 2× |
| **TF32** | 156 TF | 989 TF | 2,250 TF | 6.3× | 2.3× |
| **FP16** | 312 TF | 1,979 TF | 2,250 TF | 6.3× | 1.1× |
| **FP8** | - | 3,958 TF | 9,000 TF | N/A | 2.3× |
| **FP4** | - | - | 18,000 TF | N/A | N/A |

### 9.2 Memory System Comparison

| Metric | A100-80GB | H100-80GB | H200-141GB | B200-192GB |
|--------|-----------|-----------|------------|------------|
| **Memory Type** | HBM2e | HBM3 | HBM3e | HBM3e |
| **Capacity** | 80 GB | 80 GB | 141 GB | 192 GB |
| **Bandwidth** | 2,039 GB/s | 3,350 GB/s | 4,800 GB/s | 8,000 GB/s |
| **L2 Cache** | 40 MB | 50 MB | 50 MB | ~100 MB |

### 9.3 Interconnect Comparison

| Metric | A100 | H100 | B200 |
|--------|------|------|------|
| **NVLink Generation** | 3.0 | 4.0 | 5.0 |
| **NVLink Bandwidth** | 600 GB/s | 900 GB/s | 1,800 GB/s |
| **NVSwitch Version** | 2.0 | 3.0 | 5.0 |
| **NVSwitch Bandwidth** | 1,800 GB/s | 3,200 GB/s | 14,400 GB/s |
| **PCIe Generation** | Gen 4 | Gen 5 | Gen 5 |

### 9.4 Power Efficiency Comparison

| Metric | A100 | H100 | B200 |
|--------|------|------|------|
| **TDP** | 400W | 700W | ~1,000W |
| **FP16 TFLOPS** | 312 | 1,979 | 2,250 |
| **TFLOPS/Watt (FP16)** | 0.78 | 2.83 | 2.25 |
| **TDP Increase** | Baseline | +75% | +150% |
| **Perf/Watt Improvement** | Baseline | 3.6× | 2.9× |

**Note**: B200 TFLOPS/Watt appears lower than H100 due to dual-die design; FP8/FP4 efficiency is significantly better.

### 9.5 Architecture Feature Matrix

| Feature | Ampere | Hopper | Blackwell |
|---------|--------|--------|-----------|
| **MIG Support** |  Up to 7 instances |  Up to 7 instances |  Up to 7 instances |
| **Tensor Core Gen** | 3rd | 4th | 5th |
| **FP64 Support** |  |  |  |
| **TF32 Support** |  |  |  |
| **FP16/BF16** |  |  |  |
| **FP8 Support** |  |  |  |
| **FP4 Support** |  |  |  |
| **Transformer Engine** |  |  Gen 1 |  Gen 2 |
| **Micro-Tensor Scaling** |  |  |  |
| **Dual-Die Design** |  |  |  |

### 9.6 Optimal Use Cases by Architecture

#### Ampere (A100, A30)

**Best For**:
- General-purpose AI training
- FP16/TF32 workloads
- Multi-tenant environments (MIG)
- Inference for small-medium models
- Cost-optimized deployments

**Limitations**:
- No FP8 support
- Lower memory bandwidth than Hopper/Blackwell
- Smaller L2 cache

#### Hopper (H100, H200)

**Best For**:
- Large language model training (GPT, LLaMA)
- Transformer architectures (Transformer Engine)
- FP8 inference
- High-bandwidth memory workloads
- Multi-GPU scaling (NVLink 4.0)

**Limitations**:
- No FP4 support
- Higher power consumption than Ampere
- More expensive

#### Blackwell (B200, GB200)

**Best For**:
- Ultra-large models (>100B parameters)
- FP4 inference for maximum throughput
- Multi-modal AI (vision + language)
- Extreme-scale deployments (GB200 NVL72)
- Cutting-edge research

**Limitations**:
- Highest power consumption
- Most expensive
- Liquid cooling required (B200)
- Limited availability (2025 production sold out)

---

## 10. Implementation Considerations

### 10.1 Metrics Collection Strategy

#### Polling Intervals

| Metric Category | Interval | Rationale |
|-----------------|----------|-----------|
| **GPU Utilization** | 1-5 seconds | Capture workload patterns |
| **Memory Stats** | 5-10 seconds | Relatively stable |
| **Temperature** | 10-30 seconds | Slow-changing |
| **NVLink Bandwidth** | 1-5 seconds | Capture burst traffic |
| **Profiling Metrics** | 1-10 seconds | Expensive to collect |
| **Error Counters** | 60 seconds | Rare events |

#### Metric Grouping

**Group 1: Real-Time Metrics** (1s interval)
- `DCGM_FI_DEV_GPU_UTIL`
- `DCGM_FI_PROF_SM_ACTIVE`
- `DCGM_FI_PROF_DRAM_ACTIVE`
- `DCGM_FI_PROF_NVLINK_TX_BYTES`
- `DCGM_FI_PROF_NVLINK_RX_BYTES`

**Group 2: Resource Metrics** (5s interval)
- `DCGM_FI_DEV_FB_FREE`
- `DCGM_FI_DEV_FB_USED`
- `DCGM_FI_DEV_POWER_USAGE`
- `DCGM_FI_DEV_GPU_TEMP`

**Group 3: Detailed Profiling** (10s interval)
- `DCGM_FI_PROF_SM_OCCUPANCY`
- `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`
- `DCGM_FI_PROF_PIPE_FP16_ACTIVE`
- `DCGM_FI_PROF_PIPE_FP32_ACTIVE`

### 10.2 Architecture Detection

#### Detecting GPU Architecture

```python
import pynvml

pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)
name = pynvml.nvmlDeviceGetName(handle)

if "A100" in name or "A30" in name:
    architecture = "Ampere"
elif "H100" in name or "H200" in name:
    architecture = "Hopper"
elif "B100" in name or "B200" in name or "GB200" in name:
    architecture = "Blackwell"
```

#### Architecture-Specific Feature Flags

```python
features = {
    "Ampere": {
        "mig": True,
        "fp8": False,
        "fp4": False,
        "transformer_engine": False,
        "max_nvlink_bw": 600_000_000_000,  # 600 GB/s
    },
    "Hopper": {
        "mig": True,
        "fp8": True,
        "fp4": False,
        "transformer_engine": True,
        "max_nvlink_bw": 900_000_000_000,  # 900 GB/s
    },
    "Blackwell": {
        "mig": True,
        "fp8": True,
        "fp4": True,
        "transformer_engine": True,
        "max_nvlink_bw": 1_800_000_000_000,  # 1.8 TB/s
    },
}
```

### 10.3 FP8/FP4 Monitoring Workarounds

Since DCGM doesn't yet support FP8/FP4 metrics, use these approaches:

#### Application-Level Instrumentation

```python
# Using PyTorch with Transformer Engine
import transformer_engine.pytorch as te

# Track FP8 usage
fp8_enabled = te.fp8_autocast.is_enabled()
fp8_recipe = te.fp8_autocast.get_fp8_recipe()

# Export metrics
metrics = {
    "fp8_enabled": int(fp8_enabled),
    "fp8_recipe": str(fp8_recipe),
}
```

#### CUDA Kernel Name Tracking

```bash
# Use nsys to track FP8 kernel launches
nsys profile --cuda-graph-trace=node \
             --cuda-memory-usage=true \
             --force-overwrite=true \
             python train.py

# Parse output for FP8 kernel names
grep -i "fp8" nsys_report.txt | wc -l
```

#### Inference from Tensor Core Utilization

```python
# High Tensor Core activity + low FP16 activity = likely FP8/FP4
tensor_active = get_dcgm_metric("DCGM_FI_PROF_PIPE_TENSOR_ACTIVE")
fp16_active = get_dcgm_metric("DCGM_FI_PROF_PIPE_FP16_ACTIVE")

if tensor_active > 50 and fp16_active < 20:
    likely_fp8_or_fp4 = True
```

### 10.4 MIG Monitoring Best Practices

#### MIG Device Enumeration

```python
import pynvml

pynvml.nvmlInit()
device_count = pynvml.nvmlDeviceGetCount()

mig_devices = []
for i in range(device_count):
    handle = pynvml.nvmlDeviceGetHandleByIndex(i)

    # Check if MIG is enabled
    try:
        mig_mode = pynvml.nvmlDeviceGetMigMode(handle)
        if mig_mode[0] == pynvml.NVML_DEVICE_MIG_ENABLE:
            # Enumerate MIG instances
            for gi_id in range(8):  # Max 7 instances + 1
                try:
                    gi_info = pynvml.nvmlDeviceGetGpuInstanceById(handle, gi_id)
                    mig_devices.append({
                        "parent_gpu": i,
                        "gi_id": gi_id,
                        "profile": gi_info.profileId,
                    })
                except:
                    continue
    except:
        pass

print(f"Found {len(mig_devices)} MIG instances")
```

#### MIG Metrics via DCGM

```python
import dcgm_agent
import dcgm_fields

# Connect to DCGM
dcgm_handle = dcgm_agent.dcgmInit()
dcgm_system = dcgm_agent.dcgmSystemDiscovery(dcgm_handle)

# Get all MIG entities
mig_hierarchy = dcgm_system.GetGpuInstanceHierarchy()

for entity in mig_hierarchy.entities:
    if entity.entity_type == dcgm_fields.DCGM_FE_GPU_I:
        # Monitor MIG instance
        group_id = dcgm_agent.dcgmGroupCreate(dcgm_handle, entity.entity_id)

        # Watch metrics
        field_ids = [
            dcgm_fields.DCGM_FI_DEV_GPU_UTIL,
            dcgm_fields.DCGM_FI_DEV_FB_USED,
            dcgm_fields.DCGM_FI_PROF_SM_ACTIVE,
        ]
        dcgm_agent.dcgmWatchFields(dcgm_handle, group_id, field_ids, 1000)
```

### 10.5 NVLink Bandwidth Calculation

```python
import time

# Read initial counters
tx_bytes_0 = get_dcgm_metric("DCGM_FI_PROF_NVLINK_TX_BYTES")
rx_bytes_0 = get_dcgm_metric("DCGM_FI_PROF_NVLINK_RX_BYTES")
time_0 = time.time()

# Wait for interval
time.sleep(5)

# Read final counters
tx_bytes_1 = get_dcgm_metric("DCGM_FI_PROF_NVLINK_TX_BYTES")
rx_bytes_1 = get_dcgm_metric("DCGM_FI_PROF_NVLINK_RX_BYTES")
time_1 = time.time()

# Calculate bandwidth
elapsed = time_1 - time_0
tx_bandwidth = (tx_bytes_1 - tx_bytes_0) / elapsed  # bytes/sec
rx_bandwidth = (rx_bytes_1 - rx_bytes_0) / elapsed  # bytes/sec
total_bandwidth = tx_bandwidth + rx_bandwidth

# Calculate utilization (for H100 with 900 GB/s)
max_bandwidth = 900_000_000_000  # 900 GB/s
utilization = total_bandwidth / max_bandwidth * 100

print(f"NVLink Utilization: {utilization:.2f}%")
print(f"Bandwidth: {total_bandwidth / 1e9:.2f} GB/s")
```

### 10.6 Memory Bandwidth Utilization

```python
# Get DRAM active percentage (on HBM memory)
dram_active = get_dcgm_metric("DCGM_FI_PROF_DRAM_ACTIVE")  # Percentage

# Get peak bandwidth based on GPU model
peak_bandwidth = {
    "A100-80GB": 2039e9,    # 2,039 GB/s
    "H100-80GB": 3350e9,    # 3,350 GB/s
    "H200-141GB": 4800e9,   # 4,800 GB/s
    "B200-192GB": 8000e9,   # 8,000 GB/s
}

# Calculate effective bandwidth
gpu_model = detect_gpu_model()
peak_bw = peak_bandwidth[gpu_model]
effective_bw = (dram_active / 100) * peak_bw

print(f"Effective Memory Bandwidth: {effective_bw / 1e9:.2f} GB/s")
print(f"Memory Utilization: {dram_active:.2f}%")
```

### 10.7 Alerting Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| **GPU Utilization** | <20% | <5% | Check for idle GPUs |
| **Memory Utilization** | >85% | >95% | Scale memory or optimize |
| **GPU Temperature** | >80°C | >85°C | Check cooling |
| **Memory Temperature** | >85°C | >90°C | Check cooling, throttling likely |
| **NVLink CRC Errors** | >10/hour | >100/hour | Hardware fault |
| **Power Draw** | >90% TDP | >95% TDP | Check for power throttling |
| **DRAM Active** | >90% | >95% | Memory-bound workload |

### 10.8 Performance Optimization Guidelines

#### Identify Bottlenecks

```python
# Collect metrics
metrics = {
    "sm_active": get_dcgm_metric("DCGM_FI_PROF_SM_ACTIVE"),
    "sm_occupancy": get_dcgm_metric("DCGM_FI_PROF_SM_OCCUPANCY"),
    "dram_active": get_dcgm_metric("DCGM_FI_PROF_DRAM_ACTIVE"),
    "tensor_active": get_dcgm_metric("DCGM_FI_PROF_PIPE_TENSOR_ACTIVE"),
}

# Diagnose bottleneck
if metrics["dram_active"] > 80 and metrics["sm_occupancy"] < 50:
    bottleneck = "Memory-bound"
    recommendation = "Increase data reuse, use larger batch sizes"

elif metrics["sm_active"] < 30:
    bottleneck = "Underutilized"
    recommendation = "Increase parallelism, check for CPU bottlenecks"

elif metrics["sm_occupancy"] > 80 and metrics["sm_active"] > 80:
    bottleneck = "Compute-bound"
    recommendation = "Well-optimized or inherently compute-intensive"

elif metrics["tensor_active"] < 10 and model_uses_tensorcores:
    bottleneck = "Not using Tensor Cores"
    recommendation = "Enable TF32/FP16/FP8, check data types"
```

---

## Appendix A: Quick Reference Tables

### A.1 Architecture Summary Table

| Architecture | Year | Process | SMs | Memory | BW | NVLink | TDP |
|--------------|------|---------|-----|--------|----|----|-----|
| **A100-80GB** | 2020 | 7nm | 108 | 80GB HBM2e | 2 TB/s | 600 GB/s | 400W |
| **H100-80GB** | 2022 | 4N | 132 | 80GB HBM3 | 3.35 TB/s | 900 GB/s | 700W |
| **H200-141GB** | 2023 | 4N | 132 | 141GB HBM3e | 4.8 TB/s | 900 GB/s | 700W |
| **B200-192GB** | 2024 | 4NP | 256 | 192GB HBM3e | 8 TB/s | 1.8 TB/s | 1000W |

### A.2 Precision Format Comparison

| Format | Bits | Mantissa | Exponent | Range | Ampere | Hopper | Blackwell |
|--------|------|----------|----------|-------|--------|--------|-----------|
| **FP64** | 64 | 52 | 11 | ±10^308 |  |  |  |
| **FP32** | 32 | 23 | 8 | ±10^38 |  |  |  |
| **TF32** | 19 | 10 | 8 | ±10^38 |  |  |  |
| **FP16** | 16 | 10 | 5 | ±65,504 |  |  |  |
| **BF16** | 16 | 7 | 8 | ±10^38 |  |  |  |
| **FP8** | 8 | 3-4 | 4-5 | ±448 |  |  |  |
| **FP4** | 4 | 2 | 2 | ±6 |  |  |  |

### A.3 DCGM Quick Reference

```bash
# List GPUs
dcgmi discovery -l

# List MIG instances
dcgmi discovery -l --mig

# Monitor key metrics
dcgmi dmon -e 150,155,203,204,1002,1008

# Watch profiling metrics
dcgmi dmon -e 1002,1003,1004,1008,1010,1011

# Set up field group
dcgmi group -c my_group
dcgmi fieldgroup -c perf_group -f 150,155,1002,1003,1004,1008
dcgmi policy -g my_group --set 1000,perf_group
```

---

## Appendix B: Additional Resources

### Official Documentation

- **NVIDIA Ampere Architecture**: [https://www.nvidia.com/en-us/data-center/ampere-architecture/](https://www.nvidia.com/en-us/data-center/ampere-architecture/)
- **NVIDIA Hopper Architecture**: [https://www.nvidia.com/en-us/data-center/technologies/hopper-architecture/](https://www.nvidia.com/en-us/data-center/technologies/hopper-architecture/)
- **NVIDIA Blackwell Architecture**: [https://www.nvidia.com/en-us/data-center/technologies/blackwell-architecture/](https://www.nvidia.com/en-us/data-center/technologies/blackwell-architecture/)
- **DCGM Documentation**: [https://docs.nvidia.com/datacenter/dcgm/latest/](https://docs.nvidia.com/datacenter/dcgm/latest/)
- **MIG User Guide**: [https://docs.nvidia.com/datacenter/tesla/mig-user-guide/](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/)

### White Papers

- **Hopper Architecture Whitepaper**: [NVIDIA H100 Tensor Core GPU Architecture](https://resources.nvidia.com/en-us-tensor-core)
- **Transformer Engine**: [H100 Transformer Engine Technical Brief](https://developer.nvidia.com/blog/h100-transformer-engine/)
- **NVLink and NVSwitch**: [NVLink Technical Overview](https://www.nvidia.com/en-us/data-center/nvlink/)

### GitHub Repositories

- **DCGM**: [https://github.com/NVIDIA/DCGM](https://github.com/NVIDIA/DCGM)
- **DCGM Exporter**: [https://github.com/NVIDIA/dcgm-exporter](https://github.com/NVIDIA/dcgm-exporter)
- **Transformer Engine**: [https://github.com/NVIDIA/TransformerEngine](https://github.com/NVIDIA/TransformerEngine)

### Community Resources

- **NVIDIA Developer Forums**: [https://forums.developer.nvidia.com/](https://forums.developer.nvidia.com/)
- **DCGM Issues**: [https://github.com/NVIDIA/DCGM/issues](https://github.com/NVIDIA/DCGM/issues)
- **MLPerf Results**: [https://mlcommons.org/benchmarks/inference/](https://mlcommons.org/benchmarks/inference/)

---

**End of GPU Architecture-Specific Metrics Catalog**

This document will be updated as new NVIDIA GPU architectures are released and as DCGM support expands for newer features like FP8 and FP4 metrics.
