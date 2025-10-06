# Research Documentation

This directory contains background research and technical analysis documents that informed the design and implementation of FakeAI features.

## Purpose

These documents serve as:
- **Technical references** for understanding design decisions
- **Metrics catalogs** documenting available telemetry
- **API research** analyzing third-party services
- **Implementation guides** for complex features

## Documents

### GPU & Performance Monitoring

- **[DCGM Health Metrics](DCGM_HEALTH_METRICS_RESEARCH.md)** - DCGM health monitoring metrics and alerts
- **[DCGM Profiling](DCGM_PROFILING_RESEARCH.md)** - GPU profiling capabilities with DCGM
- **[GPU Architecture Metrics Catalog](GPU_ARCHITECTURE_METRICS_CATALOG.md)** - Comprehensive catalog of GPU telemetry across A100, H100, H200, Blackwell
- **[TensorRT-LLM Metrics](TENSORRT_LLM_METRICS.md)** - TensorRT-LLM performance metrics and profiling
- **[Triton Metrics](TRITON_METRICS_RESEARCH.md)** - NVIDIA Triton Inference Server metrics

### Inference Systems

- **[Dynamo Inference Metrics](DYNAMO_INFERENCE_METRICS_RESEARCH.md)** - AI-Dynamo KV cache and routing metrics
- **[gRPC HTTP/2](GRPC_HTTP2_RESEARCH.md)** - gRPC and HTTP/2 protocol analysis and implementation decisions

### OpenAI API Features

- **[Fine-tuning](FINE_TUNING_RESEARCH.md)** - OpenAI fine-tuning API research and implementation
- **[Realtime API](REALTIME_API_RESEARCH.md)** - OpenAI Realtime API (WebSocket) research
- **[Usage Billing API](USAGE_BILLING_API_RESEARCH.md)** - OpenAI usage tracking and billing API

## How to Use

These documents are primarily for:

1. **Understanding implementation** - See why certain features were built the way they are
2. **Extending functionality** - Use metric catalogs to add new telemetry
3. **Reference material** - Look up available metrics and API capabilities
4. **Historical context** - Understand the evolution of features

## Note

These are research documents, not user guides. For user-facing documentation, see:
- [Getting Started](../getting-started/)
- [API Reference](../api/)
- [Features Guide](../guides/features/)
