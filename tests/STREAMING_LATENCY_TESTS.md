# Streaming Latency Metrics Tests

Comprehensive test suite for validating Time to First Token (TTFT) and Inter-Token Latency (ITL) metrics in streaming responses.

## Test File

**Location**: `/home/anthony/projects/fakeai/tests/test_streaming_latency_metrics.py`

## Coverage

This test suite provides complete coverage of streaming latency metrics with 800+ lines of tests covering:

### 1. TTFT (Time to First Token) Tests

Time to First Token measures the latency from when a request starts until the first token is generated.

**Formula**: `TTFT = (first_token_time - start_time) * 1000` (milliseconds)

#### Tests:
- **Basic Calculation** (`test_ttft_basic_calculation`)
  - Validates formula: TTFT = first_token_time - start_time
  - Ensures conversion to milliseconds

- **Millisecond Accuracy** (`test_ttft_millisecond_accuracy`)
  - Tests precision across different time scales: 1ms, 10ms, 100ms, 250ms, 1500ms
  - Verifies sub-millisecond accuracy

- **First Token Only** (`test_ttft_captured_on_first_token_only`)
  - Ensures TTFT is captured on first token
  - Verifies TTFT doesn't change with subsequent tokens

- **None When No Tokens** (`test_ttft_none_when_no_tokens`)
  - Returns None when no tokens generated

- **Very Fast Tokens** (`test_ttft_with_very_fast_token`)
  - Tests < 1ms TTFT (0.5ms)

- **Very Slow Tokens** (`test_ttft_with_very_slow_token`)
  - Tests > 1s TTFT (5000ms)

### 2. ITL (Inter-Token Latency) Tests

Inter-Token Latency measures the time between consecutive tokens in a stream.

**Formula**: `ITL[i] = (token_timestamp[i] - token_timestamp[i-1]) * 1000` (milliseconds)

#### Tests:
- **Basic Calculation** (`test_itl_basic_calculation`)
  - Validates calculation between consecutive tokens
  - Tests array of latencies: [50ms, 100ms, 50ms]

- **Array Generation** (`test_itl_array_generation`)
  - Verifies correct array size (n tokens → n-1 ITLs)
  - Tests consistent ITL values

- **Average Calculation** (`test_itl_average_calculation`)
  - Tests mean ITL across all inter-token latencies
  - Validates: (10 + 20 + 30 + 40 + 50) / 5 = 30ms

- **Single Token** (`test_itl_with_single_token`)
  - Returns empty array for 1 token (no ITL possible)
  - Average ITL returns None

- **No Tokens** (`test_itl_with_no_tokens`)
  - Returns empty array and None average

- **Very Fast Tokens** (`test_itl_very_fast_tokens`)
  - Tests < 1ms ITL (0.1ms)

- **Very Slow Tokens** (`test_itl_very_slow_tokens`)
  - Tests > 1s ITL (2000ms)

### 3. Percentile Accuracy Tests

Statistical calculations for p50 (median), p95, and p99 percentiles.

#### Tests:
- **Median Calculation** (`test_ttft_median_calculation`)
  - 5 streams with TTFT [100, 150, 200, 250, 300]
  - Validates p50 = 200ms (middle value)

- **P95 with Small Sample** (`test_ttft_p95_with_small_sample`)
  - < 20 samples uses max value as p95
  - Tests 10 streams: p95 = 100ms (max)

- **P95 with Large Sample** (`test_ttft_p95_with_large_sample`)
  - >= 20 samples uses `statistics.quantiles(n=20)[18]`
  - Tests 100 streams: validates accurate p95

- **P99 with Large Dataset** (`test_ttft_p99_with_large_dataset`)
  - 200 samples using `statistics.quantiles(n=100)[98]`
  - Ensures accurate 99th percentile

- **ITL Percentiles** (`test_itl_percentiles_with_varying_data`)
  - Tests p50, p95, p99 for ITL metrics
  - Validates ordering: p99 >= p95 >= p50

### 4. Real-World Scenarios

Simulations of actual model behaviors with realistic timing profiles.

#### GPT-4 Simulation (`test_gpt4_slow_ttft_consistent_itl`)
- **TTFT**: ~500ms (450-550ms range)
- **ITL**: Consistent ~30ms
- Simulates slower but steady token generation
- 10 streams × 20 tokens each

#### GPT-4o Simulation (`test_gpt4o_fast_ttft_variable_itl`)
- **TTFT**: ~100ms (80-120ms range)
- **ITL**: Variable 15-45ms
- Simulates faster but less consistent generation
- 10 streams × 20 tokens each

#### Network Delay Simulation (`test_network_delay_simulation`)
- **TTFT**: 300ms (includes 100ms network delay)
- **ITL**: 20ms normal, 200ms spikes every 5th token
- Simulates real-world network conditions
- 5 streams × 21 tokens each

### 5. Edge Cases

Boundary conditions and unusual scenarios.

#### Tests:
- **Zero Tokens** (`test_stream_with_zero_tokens`)
  - Stream completes without generating tokens
  - Metrics handle empty data gracefully

- **Simultaneous Streams** (`test_simultaneous_streams`)
  - 5 concurrent streams
  - All tracked independently

- **Extremely Long Stream** (`test_extremely_long_stream`)
  - 1000 tokens with 5ms ITL
  - 999 ITL measurements
  - Tests scalability

- **Instant Tokens** (`test_instant_tokens`)
  - Tokens at exact same timestamp (0ms ITL)
  - Tests zero-duration edge case

- **Backwards Time** (`test_backwards_time`)
  - Clock adjustment causing negative ITL
  - Handles time going backwards

### 6. Metrics Aggregation

Cross-stream statistical aggregation.

#### Tests:
- **Min/Max TTFT** (`test_min_max_ttft`)
  - Tracks minimum and maximum TTFT
  - Tests with values [50, 100, 25, 200, 75]
  - Validates min=25ms, max=200ms

- **Mixed Models** (`test_mixed_models_statistics`)
  - Tracks per-model statistics
  - 2 gpt-4, 2 gpt-3.5-turbo, 1 claude-3

- **Success Rate** (`test_success_rate_calculation`)
  - 7 successful + 3 failed streams
  - Validates 70% success rate

### 7. Memory Management

Bounded storage and cache management.

#### Tests:
- **Max Completed Streams** (`test_max_completed_streams_limit`)
  - 50 streams created, only 10 retained
  - Validates bounded queue behavior

- **Cache Invalidation** (`test_cache_invalidation`)
  - Cache cleared on stream completion
  - Fresh metrics recalculated

### 8. Tokens Per Second

Throughput calculations.

#### Tests:
- **Basic TPS** (`test_tps_basic_calculation`)
  - 20 tokens over 1.1 seconds = ~18 tokens/sec

- **TPS Percentiles** (`test_tps_percentiles`)
  - p50, p95 calculations for throughput
  - 20 streams with varying TPS

## Running the Tests

### Option 1: Validation Script (Recommended)

```bash
python validate_streaming_metrics.py
```

This standalone script validates all core functionality without pytest dependencies.

**Output Example**:
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

### Option 2: Direct Test File

Due to conftest import issues, use the standalone runner:

```bash
python run_streaming_latency_tests.py
```

## Implementation Details

### Floating Point Tolerance

All assertions use tolerance for floating point comparisons:

```python
assert abs(actual - expected) < 0.001  # 0.001ms tolerance
```

This handles floating point arithmetic precision issues.

### Time Units

- **Internal Storage**: Seconds (float)
- **Calculations**: Convert to milliseconds (× 1000)
- **Display**: Milliseconds with 1-3 decimal places

### Statistical Methods

- **p50 (Median)**: `statistics.median(values)`
- **p95**:
  - `<20 samples`: Use `max(values)`
  - `>=20 samples`: Use `statistics.quantiles(values, n=20)[18]`
- **p99**:
  - `<20 samples`: Use `max(values)`
  - `>=100 samples`: Use `statistics.quantiles(values, n=100)[98]`

## Test Metrics

- **Total Tests**: 40+ comprehensive test cases
- **Lines of Code**: 800+
- **Coverage Areas**: 8 major categories
- **Edge Cases**: 10+ boundary conditions
- **Real-World Scenarios**: 3 model simulations

## Key Assertions

### TTFT Validations
```python
# Basic calculation
ttft = (first_token_time - start_time) * 1000  # milliseconds

# Captured once
assert first_token_time is set on token 1
assert first_token_time unchanged on tokens 2+

# Percentiles
assert p50 = median(ttft_values)
assert p95 >= p50
assert p99 >= p95
```

### ITL Validations
```python
# Array size
assert len(itls) == len(tokens) - 1

# Calculation
itl[i] = (timestamp[i+1] - timestamp[i]) * 1000

# Average
avg_itl = mean(itls)

# Edge cases
assert single_token → itls = []
assert single_token → avg_itl = None
```

## Performance Characteristics

- **Setup Time**: < 1ms per test
- **Execution Time**: < 10ms per test
- **Memory Usage**: Bounded by `max_completed_streams`
- **Scalability**: Tested up to 1000 tokens per stream

## Related Files

- **Implementation**: `/home/anthony/projects/fakeai/fakeai/streaming_metrics_tracker.py`
- **Test File**: `/home/anthony/projects/fakeai/tests/test_streaming_latency_metrics.py`
- **Validation Script**: `/home/anthony/projects/fakeai/validate_streaming_metrics.py`
- **Test Runner**: `/home/anthony/projects/fakeai/run_streaming_latency_tests.py`

## Maintenance Notes

### Adding New Tests

1. Follow existing test class structure
2. Use descriptive docstrings
3. Add floating point tolerance for assertions
4. Document expected values in comments
5. Update this README with new test description

### Common Issues

1. **Floating Point Precision**: Always use `abs(actual - expected) < tolerance`
2. **Time Units**: Ensure consistent ms conversion
3. **Empty Data**: Handle None returns for edge cases
4. **Cache**: Remember to invalidate on updates

## Future Enhancements

- [ ] Multi-threaded streaming tests
- [ ] Performance benchmarks
- [ ] Percentile accuracy with different algorithms
- [ ] Time zone handling for distributed systems
- [ ] Prometheus metrics export validation
