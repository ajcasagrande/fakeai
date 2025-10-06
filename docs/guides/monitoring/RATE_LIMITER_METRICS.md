# Rate Limiter Metrics Module

## Overview

The rate limiter metrics module (`fakeai/rate_limiter_metrics.py`) provides comprehensive tracking and analytics for rate limiting behavior and patterns. It integrates seamlessly with the existing rate limiter to offer detailed insights into API usage, throttling patterns, and potential abuse detection.

## Features

### 1. Per-Key Metrics

Track detailed statistics for each API key:

- **Request Tracking**
  - Total requests attempted vs allowed
  - Throttled request count
  - Success rate and throttle rate
  - Request timing and patterns

- **Token Tracking**
  - Tokens consumed vs requested
  - Token efficiency metrics
  - Peak token usage rates

- **Throttling Analytics**
  - Total throttle time
  - Average retry-after duration
  - Retry attempt counts
  - Time spent throttled

- **Usage Patterns**
  - Burst detection (requests per second)
  - Peak RPM tracking
  - Last request timestamp
  - Steady state vs burst behavior

### 2. Quota Tracking

Monitor quota consumption and availability:

- Remaining quota by key (RPM and TPM)
- Quota refill rate tracking
- Peak usage time identification
- Average utilization percentage
- Quota exhaustion events

### 3. Throttling Analytics

Detailed throttle behavior analysis:

- **Duration Histogram**
  - Bucketed distribution of throttle durations
  - Time ranges: <100ms, <500ms, <1s, <5s, <10s, <30s, <60s, >60s

- **Retry-After Distribution**
  - Min, max, average, median
  - P90, P95, P99 percentiles
  - Statistical analysis of retry patterns

- **RPM vs TPM Analysis**
  - RPM-only exceeded events
  - TPM-only exceeded events
  - Both limits exceeded simultaneously

- **Client Retry Patterns**
  - Retry compliance tracking
  - Excessive retry detection

### 4. Tier Statistics

Aggregate metrics by rate limit tier:

- **Per-Tier Aggregations**
  - Total keys in tier
  - Total requests and tokens
  - Average throttle rates
  - Peak burst behavior

- **Upgrade Opportunity Detection**
  - Keys with high throttle rates (>50%)
  - Keys hitting quota exhaustion
  - Recommended tier upgrades

- **Tier Comparison**
  - Usage patterns across tiers
  - Efficiency metrics by tier
  - Tier exhaustion events

### 5. Abuse Pattern Detection

Identify potential abuse or misconfiguration:

- **High Throttle Rate** (>50% of requests throttled)
- **Excessive Retries** (>10 retries in 60 seconds)
- **Burst Behavior** (>20 requests in 1 second)
- **Quota Exhaustion** (>95% quota consumed frequently)
- **Severity Classification** (high/medium based on issue count)

## API Endpoints

### `GET /metrics/rate-limits`
Get comprehensive rate limiting metrics including all categories.

**Response:**
```json
{
  "summary": {
    "total_keys": 3,
    "total_throttle_events": 90,
    "tiers": ["tier-1", "free"]
  },
  "tier_stats": { ... },
  "throttle_analytics": { ... },
  "abuse_patterns": [ ... ]
}
```

### `GET /metrics/rate-limits/key/{api_key}`
Get detailed statistics for a specific API key.

**Response:**
```json
{
  "api_key": "user-alice",
  "tier": "tier-1",
  "time_in_service_seconds": 120.5,
  "requests": {
    "total_attempted": 100,
    "total_allowed": 95,
    "total_throttled": 5,
    "throttle_rate": 0.05,
    "success_rate": 0.95
  },
  "tokens": {
    "total_requested": 10000,
    "total_consumed": 9500,
    "efficiency": 0.95
  },
  "throttling": {
    "total_throttle_time_ms": 25000,
    "avg_retry_after_ms": 5000,
    "throttle_event_count": 5,
    "recent_retry_count": 3
  },
  "usage_patterns": {
    "current_burst_requests": 8,
    "peak_rpm": 1200.5,
    "peak_tpm": 120000.0,
    "last_request_time": 1696512345.678
  },
  "quota_utilization": {
    "rpm_utilization": 0.75,
    "tpm_utilization": 0.68
  }
}
```

### `GET /metrics/rate-limits/tier`
Get statistics aggregated by tier.

**Response:**
```json
{
  "tier-1": {
    "key_count": 2,
    "total_requests_attempted": 200,
    "total_requests_allowed": 190,
    "total_requests_throttled": 10,
    "total_tokens_consumed": 19000,
    "avg_throttle_rate": 0.05,
    "keys_with_high_throttle": 0,
    "keys_with_exhaustion": 0,
    "upgrade_opportunities": 0,
    "peak_burst_requests": 15
  }
}
```

### `GET /metrics/rate-limits/throttle-analytics`
Get detailed throttling analytics.

**Response:**
```json
{
  "total_throttle_events": 90,
  "duration_histogram": {
    "<100ms": 0,
    "<500ms": 0,
    "<1000ms": 10,
    "<5000ms": 45,
    "<10000ms": 90,
    "<30000ms": 90,
    "<60000ms": 90,
    ">60000ms": 0
  },
  "retry_after_distribution": {
    "min": 500.0,
    "max": 10000.0,
    "avg": 5245.5,
    "median": 5000.0,
    "p90": 8500.0,
    "p95": 9200.0,
    "p99": 9800.0
  },
  "rpm_vs_tpm_exceeded": {
    "rpm_only": 30,
    "tpm_only": 50,
    "both": 10
  }
}
```

### `GET /metrics/rate-limits/abuse-patterns`
Detect potential abuse patterns.

**Response:**
```json
[
  {
    "api_key": "user-charlie",
    "tier": "free",
    "severity": "high",
    "total_requests": 1000,
    "throttle_rate": 0.75,
    "issues": [
      "High throttle rate: 75.0% (threshold: 50.0%)",
      "Excessive retries: 45 in last 60s (threshold: 10)",
      "Burst behavior: 35 requests/sec (threshold: 20)"
    ]
  }
]
```

## Integration

### With Rate Limiter

The metrics module is automatically integrated with the rate limiter:

```python
from fakeai.rate_limiter import RateLimiter

rate_limiter = RateLimiter()
rate_limiter.configure(tier="tier-1")

# Metrics are automatically recorded during rate limit checks
allowed, retry_after, headers = rate_limiter.check_rate_limit("api-key-123", tokens=100)

# Access metrics
stats = rate_limiter.metrics.get_key_stats("api-key-123")
```

### Manual Recording

You can also manually record metrics:

```python
from fakeai.rate_limiter_metrics import RateLimiterMetrics

metrics = RateLimiterMetrics()

# Assign tier
metrics.assign_tier("user-123", "tier-2")

# Record request attempt
metrics.record_request_attempt(
    api_key="user-123",
    allowed=True,
    tokens=100,
    rpm_limit=5000,
    tpm_limit=450000
)

# Record throttle event
metrics.record_throttle(
    api_key="user-123",
    retry_after_ms=5000.0,
    requested_tokens=100,
    rpm_exceeded=False,
    tpm_exceeded=True
)

# Record retry
metrics.record_retry("user-123")

# Update quota snapshot
metrics.update_quota_snapshot(
    api_key="user-123",
    rpm_remaining=4500,
    tpm_remaining=400000
)
```

## Testing

The module includes comprehensive tests covering all features:

```bash
# Run all rate limiter metrics tests (26 tests)
pytest tests/test_rate_limiter_metrics.py -v

# Run specific test categories
pytest tests/test_rate_limiter_metrics.py -v -k "throttle"
pytest tests/test_rate_limiter_metrics.py -v -k "abuse"
pytest tests/test_rate_limiter_metrics.py -v -k "tier"
```

## Demo

Run the interactive demo to see metrics in action:

```bash
python examples/rate_limiter_metrics_demo.py
```

The demo simulates:
1. Normal usage patterns (tier-1)
2. Burst behavior (tier-1)
3. Heavy usage on free tier
4. Per-key metrics display
5. Tier statistics
6. Throttle analytics
7. Abuse pattern detection

## Architecture

### Singleton Pattern

The `RateLimiterMetrics` class follows the singleton pattern to ensure a single instance tracks all metrics across the application:

```python
metrics1 = RateLimiterMetrics()
metrics2 = RateLimiterMetrics()
assert metrics1 is metrics2  # Same instance
```

### Thread Safety

All metric operations are thread-safe using `threading.Lock()`:

- Per-key metrics protected by `_key_metrics_lock`
- Throttle history protected by `_throttle_lock`
- Concurrent requests from multiple threads are safely handled

### Efficient Storage

- **NumPy arrays** for fast percentile calculations in throttle analytics
- **Deques with maxlen** for bounded memory usage (100-1000 items)
- **Sliding windows** (60 seconds) for time-series data
- **Automatic cleanup** of old data to prevent memory growth

### Data Structures

- `KeyMetrics` - Per-key metrics dataclass
- `ThrottleEvent` - Individual throttle event record
- Deques for recent events (bounded, efficient)
- NumPy arrays for statistical analysis

## Performance

### Memory Usage

- Per-key overhead: ~1-2 KB (with bounded deques)
- Throttle history: ~40-80 KB (1000 events max)
- NumPy arrays: ~16-32 KB (60-second windows)
- Total overhead: ~100-200 KB for typical usage

### CPU Usage

- Request recording: ~5-10 μs (microseconds)
- Throttle recording: ~10-20 μs
- Metrics retrieval: ~100-500 μs
- Analytics calculation: ~1-5 ms (with NumPy)

## Configuration

### Abuse Detection Thresholds

Customize abuse detection thresholds:

```python
metrics = RateLimiterMetrics()
metrics._abuse_thresholds = {
    "high_throttle_rate": 0.6,      # 60% throttled
    "excessive_retries": 15,         # 15 retries in 60s
    "burst_threshold": 30,           # 30 requests/sec
    "quota_exhaustion_rate": 0.90,  # 90% quota consumed
}
```

### Window Size

Adjust the time window for analytics:

```python
metrics._window_size = 120.0  # 2 minutes instead of 60 seconds
```

## Best Practices

1. **Monitor Regularly**: Check `/metrics/rate-limits` periodically
2. **Set Alerts**: Alert on high throttle rates or abuse patterns
3. **Track Trends**: Use tier stats to identify upgrade opportunities
4. **Investigate Bursts**: Look into burst behavior to optimize client code
5. **Review Throttling**: Use analytics to tune rate limit configurations
6. **Detect Abuse Early**: Monitor abuse patterns endpoint for security

## Use Cases

### 1. Capacity Planning

Monitor tier statistics to understand when users need tier upgrades:

```python
tier_stats = metrics.get_tier_stats()
if tier_stats["free"]["upgrade_opportunities"] > 5:
    # Alert: Many free-tier users hitting limits
    notify_sales_team()
```

### 2. Security Monitoring

Detect potential abuse or DDoS attempts:

```python
patterns = metrics.detect_abuse_patterns()
for pattern in patterns:
    if pattern["severity"] == "high":
        # Block or rate limit more aggressively
        apply_additional_restrictions(pattern["api_key"])
```

### 3. Performance Optimization

Identify clients with inefficient request patterns:

```python
stats = metrics.get_key_stats(api_key)
if stats["usage_patterns"]["peak_rpm"] > 10000:
    # Suggest batch API or caching to client
    recommend_optimization(api_key)
```

### 4. Billing and Analytics

Track actual usage for billing or analytics:

```python
stats = metrics.get_key_stats(api_key)
monthly_requests = stats["requests"]["total_allowed"]
monthly_tokens = stats["tokens"]["total_consumed"]
calculate_invoice(api_key, monthly_requests, monthly_tokens)
```

## Future Enhancements

Potential additions:

1. Prometheus metrics export for rate limiter metrics
2. Historical data persistence (time-series database)
3. Anomaly detection using ML
4. Automatic tier recommendations
5. Cost estimation based on usage
6. Geographic usage patterns
7. Endpoint-specific rate limiting metrics

## License

Apache License 2.0
