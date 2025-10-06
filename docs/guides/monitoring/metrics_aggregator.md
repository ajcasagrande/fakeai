# Metrics Aggregator

## Overview

The Metrics Aggregator (`fakeai/metrics_aggregator.py`) provides unified metrics aggregation from all FakeAI metric sources with cross-system correlation, health scoring, and time-series analysis.

## Features

### 1. Unified Metrics API

Single endpoint returning ALL metrics from:
- **MetricsTracker**: API request/response metrics, throughput, latency
- **KVCacheMetrics**: Cache hit rates, token reuse, prefix matching
- **DCGMMetricsSimulator**: GPU utilization, temperature, power, memory
- **DynamoMetricsCollector**: Inference latency, TTFT, ITL, queue depth

```python
from fakeai.metrics_aggregator import MetricsAggregator

aggregator = MetricsAggregator(
    metrics_tracker=metrics_tracker,
    kv_metrics=kv_metrics,
    dcgm_metrics=dcgm_metrics,
    dynamo_metrics=dynamo_metrics,
)

# Get all metrics
unified = aggregator.get_unified_metrics()
```

### 2. Cross-System Correlation

Automatically calculates correlations between metrics across systems:

- **GPU utilization vs Token throughput**: Compute efficiency
- **Cache hit rate vs Latency**: Cache effectiveness
- **Queue depth vs TTFT**: Queueing impact
- **Worker load vs Response time**: Batch efficiency

```python
correlated = aggregator.get_correlated_metrics()

for correlation in correlated['correlations']:
    print(f"{correlation['metric_a']} vs {correlation['metric_b']}")
    print(f"  Insight: {correlation['insight']}")
```

### 3. Derived Metrics

Calculates high-level efficiency metrics:

- **Token efficiency**: Output tokens / latency (tokens/sec)
- **Cache effectiveness**: Cache contribution to performance (%)
- **GPU efficiency**: Tokens per GPU utilization percentage
- **Cost efficiency**: Tokens per dollar (assuming $1/GPU-hour)

```python
derived = correlated['derived_metrics']

print(f"Token efficiency: {derived['token_efficiency']['value']:.2f} tokens/sec")
print(f"GPU efficiency: {derived['gpu_efficiency']['value']:.2f} tokens/sec per % GPU")
```

### 4. Health Scoring

Comprehensive health scoring with anomaly detection:

- **Overall health**: 0-100 score with status (healthy/degraded/unhealthy/critical)
- **Subsystem scores**: Individual health for API, cache, GPU, inference
- **Issues detected**: Specific problems identified
- **Recommendations**: Actionable suggestions

```python
health = aggregator.get_health_score()

print(f"Overall health: {health['overall']['score']}/100")
print(f"Status: {health['overall']['status']}")

for issue in health['overall']['issues']:
    print(f"  Issue: {issue}")

for rec in health['overall']['recommendations']:
    print(f"  Recommendation: {rec}")
```

Health thresholds:
- Error rate > 5%: Degraded
- Latency p99 > 10s: Unhealthy
- Cache hit rate < 20%: Degraded
- GPU utilization > 95%: Warning
- GPU temperature > 85°C: Warning
- ECC double-bit errors: Critical

### 5. Time-Series Aggregation

Multi-resolution time-series data with automatic downsampling:

- **1-second resolution**: Last 1 hour (3600 samples)
- **1-minute resolution**: Last 24 hours (1440 samples)
- **1-hour resolution**: Last 7 days (168 samples)

```python
# Get GPU utilization for last 60 seconds
series = aggregator.get_time_series("gpu_utilization", "1s", 60)

for point in series:
    print(f"{point['timestamp']}: {point['value']}")
```

Tracked metrics:
- GPU utilization
- Token throughput
- Cache hit rate
- Queue depth

### 6. Prometheus Export

Unified Prometheus format export for all metrics:

```python
prometheus = aggregator.get_prometheus_unified()

# Includes:
# - MetricsTracker metrics
# - DCGM GPU metrics
# - Dynamo inference metrics
# - Derived efficiency metrics
# - Health scores
```

Example output:
```
# FakeAI Unified Metrics

# MetricsTracker Metrics
fakeai_requests_per_second{endpoint="/v1/chat/completions"} 10.0

# DCGM GPU Metrics
DCGM_FI_DEV_GPU_UTIL{gpu="0"} 80

# Derived Efficiency Metrics
# TYPE fakeai_derived_token_efficiency gauge
fakeai_derived_token_efficiency 500.0

# Health Scores
# TYPE fakeai_health_score gauge
fakeai_health_score{subsystem="overall"} 95.0
```

## API

### MetricsAggregator

```python
class MetricsAggregator:
    def __init__(
        self,
        metrics_tracker=None,
        kv_metrics=None,
        dcgm_metrics=None,
        dynamo_metrics=None,
    ):
        """Initialize with metric sources."""

    def get_unified_metrics(self) -> dict:
        """Get all metrics in unified format."""

    def get_correlated_metrics(self) -> dict:
        """Get correlated metrics and insights."""

    def get_health_score(self) -> dict:
        """Calculate system health scores."""

    def get_time_series(self, metric: str, resolution: str, duration: int) -> list:
        """Get time-series data for metric."""

    def get_prometheus_unified(self) -> str:
        """Export all metrics in Prometheus format."""

    def shutdown(self):
        """Stop background aggregation."""
```

## Usage Example

```python
from fakeai.metrics_aggregator import MetricsAggregator
from fakeai.metrics import MetricsTracker
from fakeai.kv_cache import KVCacheMetrics
from fakeai.dcgm_metrics import DCGMMetricsSimulator
from fakeai.dynamo_metrics import DynamoMetricsCollector

# Initialize all sources
metrics_tracker = MetricsTracker()
kv_metrics = KVCacheMetrics()
dcgm_metrics = DCGMMetricsSimulator(num_gpus=4)
dynamo_metrics = DynamoMetricsCollector()

# Create aggregator
aggregator = MetricsAggregator(
    metrics_tracker=metrics_tracker,
    kv_metrics=kv_metrics,
    dcgm_metrics=dcgm_metrics,
    dynamo_metrics=dynamo_metrics,
)

# Get unified view
unified = aggregator.get_unified_metrics()
print("Sources:", list(unified['sources'].keys()))

# Get correlations
correlated = aggregator.get_correlated_metrics()
for correlation in correlated['correlations']:
    print(f"{correlation['insight']}")

# Check health
health = aggregator.get_health_score()
if health['overall']['status'] != 'healthy':
    print("Issues detected:")
    for issue in health['overall']['issues']:
        print(f"  - {issue}")

# Export to Prometheus
prometheus = aggregator.get_prometheus_unified()

# Cleanup
aggregator.shutdown()
```

## Endpoint Integration

Add to `app.py`:

```python
from fakeai.metrics_aggregator import MetricsAggregator

# Initialize aggregator
aggregator = MetricsAggregator(
    metrics_tracker=fakeai_service.metrics_tracker,
    kv_metrics=fakeai_service.kv_cache_metrics,
    dcgm_metrics=fakeai_service.dcgm_metrics,
    dynamo_metrics=fakeai_service.dynamo_metrics,
)

@app.get("/metrics/unified")
async def get_unified_metrics():
    """Get unified metrics from all sources."""
    return aggregator.get_unified_metrics()

@app.get("/metrics/correlated")
async def get_correlated_metrics():
    """Get correlated metrics with insights."""
    return aggregator.get_correlated_metrics()

@app.get("/metrics/health")
async def get_health_score():
    """Get system health scores."""
    return aggregator.get_health_score()

@app.get("/metrics/time-series/{metric}")
async def get_time_series(
    metric: str,
    resolution: str = "1s",
    duration: int = 60,
):
    """Get time-series data for metric."""
    return aggregator.get_time_series(metric, resolution, duration)

@app.get("/metrics/prometheus/unified")
async def get_prometheus_unified():
    """Get unified Prometheus export."""
    return Response(
        content=aggregator.get_prometheus_unified(),
        media_type="text/plain",
    )
```

## Testing

Run comprehensive tests:

```bash
pytest tests/test_metrics_aggregator.py -v
```

Test coverage:
- Unified metrics API (5 tests)
- Correlated metrics (4 tests)
- Derived metrics (4 tests)
- Health scoring (9 tests)
- Time-series aggregation (5 tests)
- Prometheus export (5 tests)
- Lifecycle management (3 tests)
- Edge cases (4 tests)

**Total: 40 tests**

## Demo

Run the interactive demo:

```bash
python examples/metrics_aggregation_demo.py
```

The demo shows:
1. Initialization of all metric sources
2. Workload simulation
3. Unified metrics display
4. Cross-system correlations
5. System health scoring
6. Time-series data collection
7. Prometheus export

## Background Aggregation

The aggregator runs a background thread that:
- Samples metrics at 1-second intervals
- Aggregates to 1-minute resolution every 60 seconds
- Aggregates to 1-hour resolution every 3600 seconds
- Automatically manages memory with fixed-size deques

## Performance

- Lock-free reads from metric sources
- Atomic snapshot updates
- Minimal memory footprint (fixed-size deques)
- Non-blocking background aggregation
- Efficient correlation calculations

## Architecture

```

                  MetricsAggregator                      

                                                         
        
     Unified      Correlated       Health       
     Metrics        Metrics        Scoring      
        
                                                         
        
   Time-Series     Derived        Prometheus    
  Aggregation      Metrics          Export      
        
                                                         

                   Metric Sources                        

  MetricsTracker  KVCacheMetrics  DCGM  Dynamo       

```

## References

- Source: `fakeai/metrics_aggregator.py`
- Tests: `tests/test_metrics_aggregator.py`
- Demo: `examples/metrics_aggregation_demo.py`
- Related: `fakeai/metrics.py`, `fakeai/kv_cache.py`, `fakeai/dcgm_metrics.py`, `fakeai/dynamo_metrics.py`
