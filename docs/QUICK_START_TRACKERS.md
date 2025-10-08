# Quick Start: New Metrics Trackers

## TL;DR

Three production-ready trackers implemented with 2025 best practices:

| Tracker | Purpose | Lines | Status |
|---------|---------|-------|--------|
| **StreamingMetricsTracker** | Streaming response metrics | 1,046 | ✅ NEW |
| **ErrorMetricsTracker** | Error tracking + SLO monitoring | 946 | ✅ NEW |
| **CostTracker** | Cost tracking + budgets | 946 | ✅ EXISTING |

---

## Quick Usage Examples

### StreamingMetricsTracker

```python
from fakeai.streaming_metrics_tracker import StreamingMetricsTracker

tracker = StreamingMetricsTracker()

# Track a stream
tracker.start_stream("stream-1", "gpt-4", prompt_tokens=100)
tracker.record_token("stream-1", "Hello", chunk_size_bytes=20)
tracker.complete_stream("stream-1", "stop")

# Get metrics
metrics = tracker.get_metrics()
print(f"P95 TTFT: {metrics.p95_ttft:.2f}ms")
print(f"Avg TPS: {metrics.avg_tokens_per_second:.2f}")
```

### ErrorMetricsTracker

```python
from fakeai.error_metrics_tracker import ErrorMetricsTracker

tracker = ErrorMetricsTracker(error_budget_slo=0.999)  # 99.9%

# Track errors and successes
tracker.record_error(
    endpoint="/v1/chat/completions",
    status_code=500,
    error_type="TimeoutError",
    error_message="Database timeout",
    model="gpt-4"
)
tracker.record_success("/v1/chat/completions", "gpt-4")

# Check SLO
slo = tracker.get_slo_status()
if slo.slo_violated:
    print(f"⚠️ SLO VIOLATED! Burn rate: {slo.burn_rate:.2f}x")

# Get error patterns
patterns = tracker.get_error_patterns()
for p in patterns:
    print(f"Pattern {p.fingerprint}: {p.count} occurrences")
```

### CostTracker

```python
from fakeai.cost_tracker import CostTracker

tracker = CostTracker()

# Track usage
cost = tracker.record_usage(
    api_key="sk-abc123",
    model="gpt-4",
    endpoint="/v1/chat/completions",
    prompt_tokens=150,
    completion_tokens=50
)

# Set budget
tracker.set_budget("sk-abc123", limit=100.0, period=BudgetPeriod.MONTHLY)

# Check budget
used, remaining, exceeded = tracker.check_budget("sk-abc123")
print(f"Used: ${used:.2f}, Remaining: ${remaining:.2f}")

# Get suggestions
suggestions = tracker.get_optimization_suggestions("sk-abc123")
for s in suggestions:
    print(f"💡 {s.description}")
    print(f"   Savings: ${s.potential_savings:.2f}/month")
```

---

## Key Metrics at a Glance

### Streaming Metrics

| Metric | What It Measures |
|--------|------------------|
| **TTFT** | Time to first token (latency felt by user) |
| **ITL** | Inter-token latency (token generation smoothness) |
| **TPS** | Tokens per second (throughput) |
| **Success Rate** | % of streams completed successfully |
| **Backpressure** | Network congestion events |

### Error Metrics

| Metric | What It Measures |
|--------|------------------|
| **Error Rate** | % of requests that fail |
| **SLO Status** | Whether error budget is exceeded |
| **Burn Rate** | How fast error budget is consumed |
| **Error Budget** | Remaining allowed errors |
| **Patterns** | Detected recurring error signatures |

### Cost Metrics

| Metric | What It Measures |
|--------|------------------|
| **Total Cost** | Cumulative spending |
| **By Model** | Cost breakdown per model |
| **By Endpoint** | Cost breakdown per API endpoint |
| **Projected** | Forecasted monthly cost |
| **Cache Savings** | Savings from prompt caching |

---

## Percentiles Explained

| Percentile | Meaning | Use Case |
|------------|---------|----------|
| **p50 (median)** | 50% of values below | Typical experience |
| **p95** | 95% of values below | Good user experience |
| **p99** | 99% of values below | SLA/SLO threshold |

Example: `p95_ttft = 500ms` means 95% of users get first token within 500ms.

---

## Alert Thresholds (Recommended)

### Streaming Performance

```python
metrics = streaming_tracker.get_metrics()

if metrics.p95_ttft > 2000:  # 2 seconds
    alert("High TTFT detected")

if metrics.avg_tokens_per_second < 10:
    alert("Low token generation rate")

if metrics.success_rate < 0.95:
    alert("High stream failure rate")
```

### Error Monitoring

```python
slo = error_tracker.get_slo_status()

if slo.slo_violated:
    page("SLO VIOLATED - Error budget exhausted")

if slo.burn_rate > 10.0:
    page("CRITICAL: Error burn rate 10x normal")

if slo.error_budget_percentage < 10:
    alert("Error budget < 10% remaining")
```

### Cost Management

```python
budget = cost_tracker.get_budget_status(api_key)

if budget and budget.get_usage_percentage() > 90:
    alert(f"Budget 90% used for {api_key}")

projected = cost_tracker.get_projected_monthly_cost()
if projected > 10000:
    alert(f"Projected monthly cost: ${projected:.2f}")
```

---

## Prometheus Queries

### Streaming

```promql
# High TTFT alerts
streaming_ttft_milliseconds{quantile="0.95"} > 2000

# Low throughput
streaming_tokens_per_second{quantile="0.50"} < 10

# Stream failure rate
rate(streaming_failed_streams[5m]) / rate(streaming_total_streams[5m]) > 0.05
```

### Errors

```promql
# SLO violations
error_slo_violated == 1

# High burn rate
error_burn_rate > 10

# Error rate spike
rate(error_total_errors[5m]) > 0.01
```

### Costs

```promql
# Daily cost rate
rate(cost_total_usd[1d])

# Budget alerts
cost_budget_usage_percentage > 90

# Model cost distribution
topk(5, cost_by_model_usd)
```

---

## Files Created

```
fakeai/
├── streaming_metrics_tracker.py (1,046 lines) ✅ NEW
├── error_metrics_tracker.py (946 lines)       ✅ NEW
└── cost_tracker.py (946 lines)                ✅ EXISTING

docs/
├── METRICS_TRACKERS_GUIDE.md          - Complete integration guide
├── TRACKERS_IMPLEMENTATION_SUMMARY.md  - Architecture details
└── QUICK_START_TRACKERS.md            - This file
```

---

## Next: Enable in Production

1. **Update subscribers** (`fakeai/events/subscribers.py`)
2. **Initialize trackers** (`fakeai/app.py`)
3. **Add metrics endpoints** (`/metrics/streaming`, `/metrics/errors`)
4. **Update Prometheus export**
5. **Configure alerts** in your monitoring system
6. **Add to dashboard**

See `METRICS_TRACKERS_GUIDE.md` for step-by-step integration.

---

## Testing

```bash
# Test imports
python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('sm', 'fakeai/streaming_metrics_tracker.py')
sm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sm)
tracker = sm.StreamingMetricsTracker()
print(f'✅ Max streams: {tracker.max_active_streams}')
"

# Run tests
pytest tests/test_streaming_metrics_tracker.py
pytest tests/test_error_metrics_tracker.py
```

---

## Support

- **Full Guide**: `docs/METRICS_TRACKERS_GUIDE.md`
- **Architecture**: `docs/TRACKERS_IMPLEMENTATION_SUMMARY.md`
- **Code**: `fakeai/streaming_metrics_tracker.py` (1,046 lines of docs + code)
- **Code**: `fakeai/error_metrics_tracker.py` (946 lines of docs + code)

All trackers are production-ready with comprehensive docstrings, type hints, thread safety, and 2025 best practices! 🎉
