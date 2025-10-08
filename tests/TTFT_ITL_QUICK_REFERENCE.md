# TTFT & ITL Quick Reference Guide

## Formulas

### TTFT (Time to First Token)
```python
TTFT = (first_token_time - start_time) * 1000  # milliseconds
```

**When**: Measured from request start to first token generation
**Unit**: Milliseconds (ms)
**Captured**: Once, on first token only

### ITL (Inter-Token Latency)
```python
ITL[i] = (token_timestamp[i] - token_timestamp[i-1]) * 1000  # milliseconds
```

**When**: Measured between consecutive tokens
**Unit**: Milliseconds (ms)
**Array Size**: n tokens → (n-1) ITL measurements

### Average ITL
```python
avg_itl = mean([ITL[0], ITL[1], ..., ITL[n-2]])
```

## Implementation Code

### StreamState Class
```python
class StreamState:
    start_time: float              # Request start (seconds)
    first_token_time: float        # First token arrival (seconds)
    token_timestamps: list[float]  # All token timestamps (seconds)

    def get_ttft(self) -> Optional[float]:
        """Get TTFT in milliseconds."""
        if self.first_token_time:
            return (self.first_token_time - self.start_time) * 1000
        return None

    def get_inter_token_latencies(self) -> list[float]:
        """Get ITL array in milliseconds."""
        if len(self.token_timestamps) < 2:
            return []

        latencies = []
        for i in range(1, len(self.token_timestamps)):
            latency_ms = (self.token_timestamps[i] - self.token_timestamps[i-1]) * 1000
            latencies.append(latency_ms)

        return latencies

    def get_average_itl(self) -> Optional[float]:
        """Get average ITL in milliseconds."""
        latencies = self.get_inter_token_latencies()
        if latencies:
            return statistics.mean(latencies)
        return None
```

## Percentile Calculations

### p50 (Median)
```python
p50 = statistics.median(values)
```

### p95
```python
if len(values) >= 20:
    p95 = statistics.quantiles(values, n=20)[18]  # 19th of 20 quantiles
else:
    p95 = max(values)  # Use max for small samples
```

### p99
```python
if len(values) >= 100:
    p99 = statistics.quantiles(values, n=100)[98]  # 99th of 100 quantiles
else:
    p99 = max(values)  # Use max for small samples
```

## Edge Cases

| Scenario | TTFT | ITL Array | Avg ITL |
|----------|------|-----------|---------|
| 0 tokens | `None` | `[]` | `None` |
| 1 token | `150ms` | `[]` | `None` |
| 2 tokens | `150ms` | `[50ms]` | `50ms` |
| n tokens | `150ms` | `[...] (n-1 items)` | `mean(ITLs)` |

## Typical Model Profiles

### GPT-4
```
TTFT: ~500ms (450-550ms)
ITL:  ~30ms (consistent)
Profile: Slow start, steady generation
```

### GPT-4o
```
TTFT: ~100ms (80-120ms)
ITL:  15-45ms (variable)
Profile: Fast start, variable generation
```

### With Network Issues
```
TTFT: Base + network delay (e.g., 200ms + 100ms = 300ms)
ITL:  Normal + spikes (e.g., 20ms with 200ms spikes)
Profile: Inconsistent due to network
```

## Test Examples

### Basic TTFT Test
```python
tracker = StreamingMetricsTracker()
tracker.start_stream("stream-1", "gpt-4", 50)

stream = tracker._active_streams["stream-1"]
stream.start_time = 1000.0
stream.first_token_time = 1000.150  # 150ms later

ttft = stream.get_ttft()
assert abs(ttft - 150.0) < 0.001  # ≈150ms
```

### Basic ITL Test
```python
stream.token_timestamps = [
    1000.0,      # Token 0
    1000.05,     # Token 1 (50ms later)
    1000.15,     # Token 2 (100ms later)
]

itls = stream.get_inter_token_latencies()
assert itls == [50.0, 100.0]  # Two ITL measurements
```

### Percentile Test
```python
# Create 100 streams with TTFT 1-100ms
for ttft_ms in range(1, 101):
    # ... create and complete stream with this TTFT
    pass

metrics = tracker.get_metrics()
assert metrics.p50_ttft ≈ 50.5  # Median
assert metrics.p95_ttft ≈ 96.0  # 95th percentile
assert metrics.p99_ttft ≈ 100.0 # 99th percentile
```

## Common Pitfalls

### ❌ Wrong: Exact equality with floats
```python
assert ttft == 150.0  # Fails due to floating point
```

### ✓ Right: Tolerance-based comparison
```python
assert abs(ttft - 150.0) < 0.001  # Passes
```

### ❌ Wrong: Wrong time units
```python
ttft = first_token_time - start_time  # In seconds!
```

### ✓ Right: Convert to milliseconds
```python
ttft = (first_token_time - start_time) * 1000  # ms
```

### ❌ Wrong: Assuming ITL exists for 1 token
```python
stream.tokens = [token1]
avg_itl = mean(stream.get_inter_token_latencies())  # ERROR!
```

### ✓ Right: Check for empty array
```python
itls = stream.get_inter_token_latencies()
avg_itl = mean(itls) if itls else None  # Safe
```

## Validation

Run comprehensive validation:
```bash
python validate_streaming_metrics.py
```

Expected output:
```
======================================================================
STREAMING LATENCY METRICS VALIDATION
======================================================================

1. TTFT Basic Calculation...
   ✓ TTFT = 150.000ms (expected 150ms)
2. TTFT Millisecond Precision...
   ✓ Tested 1ms, 10ms, 100ms, 250ms, 1500ms
...
======================================================================
RESULTS: 10 passed, 0 failed
======================================================================
```

## File Locations

- **Implementation**: `/home/anthony/projects/fakeai/fakeai/streaming_metrics_tracker.py`
- **Tests**: `/home/anthony/projects/fakeai/tests/test_streaming_latency_metrics.py`
- **Validation**: `/home/anthony/projects/fakeai/validate_streaming_metrics.py`
- **Documentation**: `/home/anthony/projects/fakeai/tests/STREAMING_LATENCY_TESTS.md`

## Quick Stats

- **Test Coverage**: 40+ test cases
- **Lines of Test Code**: 800+
- **Categories**: 8 major areas
- **Edge Cases**: 10+ scenarios
- **Real-World Sims**: 3 models
- **Execution Time**: < 1 second

## Key Metrics

| Metric | Description | Unit | Formula |
|--------|-------------|------|---------|
| TTFT | Time to first token | ms | `(first - start) * 1000` |
| ITL | Inter-token latency | ms | `(token[i] - token[i-1]) * 1000` |
| Avg ITL | Mean ITL | ms | `mean(ITLs)` |
| TPS | Tokens per second | tok/s | `token_count / duration` |
| p50 | Median | ms | `median(values)` |
| p95 | 95th percentile | ms | `quantiles(values, 20)[18]` |
| p99 | 99th percentile | ms | `quantiles(values, 100)[98]` |
