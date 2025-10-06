# Per-Model Metrics Tracking

Comprehensive per-model metrics tracking with multi-dimensional analysis, cost estimation, model comparison, and Prometheus export.

## Overview

The `ModelMetricsTracker` provides detailed metrics for each model, enabling you to:

- Track requests, tokens, latency, and errors per model
- Compare model performance side-by-side
- Estimate costs based on token-based pricing
- Rank models by various metrics
- Export metrics in Prometheus format
- Analyze metrics across multiple dimensions (model × endpoint, model × user, model × time)

## Features

### 1. Per-Model Tracking

Track comprehensive metrics for each model:

- **Request count** - Total requests per model
- **Token usage** - Prompt, completion, and total tokens
- **Latency** - Average, min, max, p50, p90, p95, p99
- **Error rate** - Count and percentage
- **Cost estimation** - Based on OpenAI pricing
- **Uptime** - Time between first and last request

### 2. Multi-Dimensional Metrics

Analyze metrics across two dimensions:

- **Model × Endpoint** - Which endpoints are used with which models
- **Model × User** - Which users use which models
- **Model × Time** - Usage patterns over time (24h buckets)

### 3. Cost Tracking

Automatic cost estimation based on OpenAI pricing:

- Token-based pricing (per 1K tokens)
- Separate input/output pricing
- Cost per request
- Total cost per model
- Support for 50+ models

### 4. Model Comparison

Side-by-side comparison of two models:

- Request count delta and percentage change
- Latency comparison with winner determination
- Error rate comparison
- Cost comparison (total and per-request)
- Token usage comparison

### 5. Model Ranking

Rank models by any metric:

- Most used models (by request count)
- Fastest models (by latency)
- Most reliable models (by error rate)
- Most expensive models (by cost)
- Highest token usage

### 6. Prometheus Export

Export metrics in Prometheus format with model labels:

```prometheus
# Request count by model
fakeai_model_requests_total{model="gpt-4"} 150

# Token usage by model and type
fakeai_model_tokens_total{model="gpt-4",type="prompt"} 15000
fakeai_model_tokens_total{model="gpt-4",type="completion"} 7500

# Latency percentiles by model
fakeai_model_latency_milliseconds{model="gpt-4",quantile="0.5"} 250.00
fakeai_model_latency_milliseconds{model="gpt-4",quantile="0.9"} 450.00
fakeai_model_latency_milliseconds{model="gpt-4",quantile="0.99"} 800.00

# Cost by model
fakeai_model_cost_usd_total{model="gpt-4"} 0.135000

# Model-endpoint breakdown
fakeai_model_endpoint_requests_total{model="gpt-4",endpoint="/v1/chat/completions"} 145
```

## API Endpoints

### Get All Model Metrics

```bash
GET /metrics/by-model
```

Returns metrics for all models that have been used.

**Response:**
```json
{
  "gpt-4": {
    "model": "gpt-4",
    "request_count": 150,
    "tokens": {
      "prompt": 15000,
      "completion": 7500,
      "total": 22500
    },
    "latency": {
      "avg_ms": 245.5,
      "p50": 250.0,
      "p90": 450.0,
      "p95": 550.0,
      "p99": 800.0
    },
    "errors": {
      "count": 2,
      "rate_percent": 1.33
    },
    "cost": {
      "total_usd": 0.135,
      "per_request_usd": 0.0009
    },
    "endpoints": {
      "/v1/chat/completions": 145,
      "/v1/completions": 5
    },
    "users": {
      "user-1": 100,
      "user-2": 50
    },
    "uptime_seconds": 3600,
    "first_request": 1730000000.0,
    "last_request": 1730003600.0
  }
}
```

### Get Specific Model Metrics

```bash
GET /metrics/by-model/{model_id}
```

Returns metrics for a specific model.

**Example:**
```bash
curl http://localhost:8000/metrics/by-model/gpt-4
```

### Compare Two Models

```bash
GET /metrics/compare?model1=X&model2=Y
```

Compare two models side-by-side with winner determination.

**Example:**
```bash
curl "http://localhost:8000/metrics/compare?model1=gpt-4&model2=gpt-3.5-turbo"
```

**Response:**
```json
{
  "model1": "gpt-4",
  "model2": "gpt-3.5-turbo",
  "comparison": {
    "request_count": {
      "model1": 150,
      "model2": 300,
      "delta": 150,
      "percent_change": 100.0
    },
    "avg_latency_ms": {
      "model1": 245.5,
      "model2": 180.3,
      "delta": -65.2,
      "percent_change": -26.6
    },
    "total_cost_usd": {
      "model1": 0.135,
      "model2": 0.045,
      "delta": -0.09,
      "percent_change": -66.7
    }
  },
  "winner": {
    "latency": "gpt-3.5-turbo",
    "error_rate": "gpt-4",
    "cost_efficiency": "gpt-3.5-turbo"
  }
}
```

### Get Model Ranking

```bash
GET /metrics/ranking?metric=X&limit=N
```

Rank models by a specific metric.

**Supported metrics:**
- `request_count` - Most used models
- `latency` - Fastest models
- `error_rate` - Most reliable models
- `cost` - Most expensive models
- `tokens` - Highest token usage

**Example:**
```bash
curl "http://localhost:8000/metrics/ranking?metric=request_count&limit=5"
```

### Get Cost Breakdown

```bash
GET /metrics/costs
```

Get cost breakdown by model with total cost.

**Response:**
```json
{
  "costs_by_model": {
    "gpt-4": 0.135,
    "gpt-3.5-turbo": 0.045,
    "openai/gpt-oss-120b": 0.030
  },
  "total_cost_usd": 0.210
}
```

### Get Multi-Dimensional Metrics

```bash
GET /metrics/multi-dimensional
```

Get 2D metric breakdowns.

**Response:**
```json
{
  "model_by_endpoint": {
    "gpt-4": {
      "/v1/chat/completions": 145,
      "/v1/completions": 5
    },
    "gpt-3.5-turbo": {
      "/v1/chat/completions": 300
    }
  },
  "model_by_user": {
    "gpt-4": {
      "user-1": 100,
      "user-2": 50
    }
  },
  "model_by_time_24h": {
    "gpt-4": [
      {"timestamp": 1730000000, "count": 50},
      {"timestamp": 1730003600, "count": 100}
    ]
  }
}
```

### Get Prometheus Metrics

```bash
GET /metrics/by-model/prometheus
```

Export all model metrics in Prometheus format.

## Pricing Configuration

The module includes pricing for 50+ models:

### GPT-4 Family
- `gpt-4`: $0.03/$0.06 per 1K tokens (input/output)
- `gpt-4-turbo`: $0.01/$0.03 per 1K tokens
- `gpt-4o`: $0.005/$0.015 per 1K tokens
- `gpt-4o-mini`: $0.00015/$0.0006 per 1K tokens

### GPT-3.5 Family
- `gpt-3.5-turbo`: $0.0005/$0.0015 per 1K tokens
- `gpt-3.5-turbo-16k`: $0.003/$0.004 per 1K tokens

### Open-Source Models
- `openai/gpt-oss-120b`: $0.01/$0.03 per 1K tokens
- `openai/gpt-oss-20b`: $0.003/$0.009 per 1K tokens

### DeepSeek Models
- `deepseek-ai/DeepSeek-R1`: $0.014/$0.028 per 1K tokens
- `deepseek-v3`: $0.027/$0.11 per 1K tokens

### Mixtral Models
- `mixtral-8x7b`: $0.0007/$0.0007 per 1K tokens
- `mixtral-8x22b`: $0.002/$0.006 per 1K tokens

### Claude Models
- `claude-3-opus`: $0.015/$0.075 per 1K tokens
- `claude-3-sonnet`: $0.003/$0.015 per 1K tokens
- `claude-3-haiku`: $0.00025/$0.00125 per 1K tokens

### Embedding Models
- `text-embedding-ada-002`: $0.0001 per 1K tokens
- `text-embedding-3-small`: $0.00002 per 1K tokens
- `text-embedding-3-large`: $0.00013 per 1K tokens

Unknown models use default pricing: $0.001/$0.002 per 1K tokens.

## Usage Examples

### Python Client

```python
import requests

# Get metrics for a specific model
response = requests.get("http://localhost:8000/metrics/by-model/gpt-4")
metrics = response.json()

print(f"Request count: {metrics['request_count']}")
print(f"Total cost: ${metrics['cost']['total_usd']:.4f}")
print(f"Average latency: {metrics['latency']['avg_ms']:.2f}ms")

# Compare two models
response = requests.get(
    "http://localhost:8000/metrics/compare",
    params={"model1": "gpt-4", "model2": "gpt-3.5-turbo"}
)
comparison = response.json()

print(f"Latency winner: {comparison['winner']['latency']}")
print(f"Cost winner: {comparison['winner']['cost_efficiency']}")

# Get top 5 most used models
response = requests.get(
    "http://localhost:8000/metrics/ranking",
    params={"metric": "request_count", "limit": 5}
)
ranking = response.json()

for i, model_stats in enumerate(ranking, 1):
    print(f"{i}. {model_stats['model']}: {model_stats['request_count']} requests")
```

### JavaScript Client

```javascript
// Get metrics for all models
fetch('http://localhost:8000/metrics/by-model')
  .then(res => res.json())
  .then(metrics => {
    for (const [model, stats] of Object.entries(metrics)) {
      console.log(`${model}: ${stats.request_count} requests, $${stats.cost.total_usd.toFixed(4)}`);
    }
  });

// Compare models
fetch('http://localhost:8000/metrics/compare?model1=gpt-4&model2=gpt-3.5-turbo')
  .then(res => res.json())
  .then(comparison => {
    console.log('Winner by latency:', comparison.winner.latency);
    console.log('Winner by cost:', comparison.winner.cost_efficiency);
  });
```

### cURL

```bash
# Get all model metrics
curl http://localhost:8000/metrics/by-model | jq

# Get specific model metrics
curl http://localhost:8000/metrics/by-model/gpt-4 | jq

# Compare two models
curl "http://localhost:8000/metrics/compare?model1=gpt-4&model2=gpt-3.5-turbo" | jq

# Get top 10 most used models
curl "http://localhost:8000/metrics/ranking?metric=request_count&limit=10" | jq

# Get cost breakdown
curl http://localhost:8000/metrics/costs | jq

# Get Prometheus metrics
curl http://localhost:8000/metrics/by-model/prometheus
```

## Programmatic Usage

### Using the ModelMetricsTracker Directly

```python
from fakeai.model_metrics import ModelMetricsTracker

# Get singleton instance
tracker = ModelMetricsTracker()

# Track a request
tracker.track_request(
    model="gpt-4",
    endpoint="/v1/chat/completions",
    prompt_tokens=100,
    completion_tokens=50,
    latency_ms=250.0,
    user="user-1",
    error=False
)

# Get stats
stats = tracker.get_model_stats("gpt-4")
print(f"Total cost: ${stats['cost']['total_usd']:.4f}")

# Compare models
comparison = tracker.compare_models("gpt-4", "gpt-3.5-turbo")
print(f"Winner: {comparison['winner']['latency']}")

# Get ranking
ranking = tracker.get_model_ranking(metric="cost", limit=5)
for i, model_stats in enumerate(ranking, 1):
    print(f"{i}. {model_stats['model']}: ${model_stats['cost']['total_usd']:.4f}")
```

## Integration

### Automatic Tracking

Model metrics are automatically tracked for:

- `POST /v1/chat/completions` (non-streaming)
- `POST /v1/completions` (non-streaming)
- `POST /v1/embeddings`

The tracking includes:
- Model ID
- Endpoint
- Token usage (prompt + completion)
- Request latency
- User/API key (first 20 chars)
- Error status

### Manual Tracking

To add tracking to other endpoints:

```python
from fakeai.app import model_metrics_tracker
import time

@app.post("/your/endpoint")
async def your_endpoint(request: YourRequest):
    start_time = time.time()

    response = await your_service.process(request)

    # Track metrics
    latency_ms = (time.time() - start_time) * 1000
    model_metrics_tracker.track_request(
        model=request.model,
        endpoint="/your/endpoint",
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        latency_ms=latency_ms,
        user=get_user_id(),
        error=False
    )

    return response
```

## Architecture

### Thread Safety

The `ModelMetricsTracker` is a thread-safe singleton that uses:
- `threading.Lock` for synchronized access
- `defaultdict` for automatic initialization
- Atomic operations for counter updates

### Memory Management

- Metrics are stored in-memory
- No automatic cleanup (use `reset_stats()` if needed)
- Latency samples kept in arrays (unbounded)
- Time buckets pruned to 24 hours

### Performance

- O(1) metric updates
- O(n) percentile calculations
- O(n log n) model ranking
- Minimal overhead per request (~1-2ms)

## Monitoring

### Grafana Dashboard

Use the Prometheus export to create Grafana dashboards:

```promql
# Request rate by model
rate(fakeai_model_requests_total[5m])

# Average latency by model
fakeai_model_latency_milliseconds{quantile="0.5"}

# Cost over time
increase(fakeai_model_cost_usd_total[1h])

# Error rate by model
rate(fakeai_model_errors_total[5m])
```

### Alerts

Set up alerts for cost and performance:

```yaml
# High cost alert
- alert: HighModelCost
  expr: fakeai_model_cost_usd_total > 10
  annotations:
    summary: "Model {{ $labels.model }} has exceeded $10"

# High latency alert
- alert: HighModelLatency
  expr: fakeai_model_latency_milliseconds{quantile="0.99"} > 1000
  annotations:
    summary: "Model {{ $labels.model }} p99 latency > 1s"
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest tests/test_model_metrics.py -v

# Run specific test classes
pytest tests/test_model_metrics.py::TestBasicTracking -v
pytest tests/test_model_metrics.py::TestCostTracking -v
pytest tests/test_model_metrics.py::TestPrometheusExport -v

# Run with coverage
pytest tests/test_model_metrics.py --cov=fakeai.model_metrics --cov-report=html
```

The test suite includes 36+ tests covering:
- Basic tracking functionality
- Multi-dimensional metrics
- Cost calculation
- Model comparison
- Latency percentiles
- Prometheus export
- Thread safety
- Edge cases

## Demo

Run the interactive demo:

```bash
# Start the server
python -m fakeai server

# Run the demo (in another terminal)
python examples/model_metrics_demo.py
```

The demo will:
1. Make requests to multiple models
2. Display per-model metrics
3. Compare models
4. Show rankings
5. Display cost breakdown
6. Show Prometheus format sample

## Limitations

- **Streaming not tracked**: Streaming requests (`stream=True`) are not currently tracked
- **Memory**: All metrics stored in-memory (no persistence)
- **Latency array**: Unbounded growth for latency samples
- **Time buckets**: Only last 24 hours retained
- **Single server**: No distributed tracking across multiple servers

## Future Enhancements

Potential improvements:
- Add streaming support
- Persist metrics to database/Redis
- Add TTL for old metrics
- Support distributed tracking
- Add more cost models
- Add budget alerts
- Add A/B testing support
- Add custom pricing overrides
- Add metric aggregation API

## License

Apache 2.0
