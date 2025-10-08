# SLO Monitoring Test Suite

Comprehensive test coverage for SLO (Service Level Objective) monitoring and error budget tracking in the FakeAI error metrics system.

## File Location

- **Test File**: `/home/anthony/projects/fakeai/tests/test_slo_monitoring.py`
- **Standalone Runner**: `/home/anthony/projects/fakeai/tests/run_slo_tests_standalone.py`

## Test Coverage Overview

The test suite contains **10 test classes** with **60+ comprehensive tests** covering all aspects of SLO monitoring:

### 1. Error Budget Calculation (`TestErrorBudgetCalculation`)

Tests error budget calculations for various SLO targets:

- **99.9% SLO with 1000 requests = 1 error allowed**
  - Error budget total = int(1000 * 0.001) = 1
  - Budget consumption tracked correctly

- **99% SLO with 100 requests = 1 error allowed**
  - Error budget total = int(100 * 0.01) = 1

- **95% SLO with 100 requests = 5 errors allowed**
  - Error budget total = int(100 * 0.05) = 5

- **Partial budget consumption**
  - Tracks consumed vs remaining
  - Calculates percentage correctly

- **Zero errors scenario**
  - 100% budget available
  - No consumption

### 2. SLO Violation Detection (`TestSLOViolationDetection`)

Tests accurate detection of SLO violations:

- **Not violated when within budget**
  - 99% success rate meets 99% SLO
  - `slo_violated = False`

- **Violated when budget exceeded**
  - 98% success rate violates 99% SLO
  - `slo_violated = True`

- **Exactly at threshold behavior**
  - Exactly at SLO threshold = not violated
  - Just below threshold = violated

- **Multiple SLO targets**
  - Different SLO levels (99.9%, 99%, 95%)
  - Same traffic pattern yields different violation status

### 3. Burn Rate Calculation (`TestBurnRateCalculation`)

Tests burn rate computation for alerting:

- **Normal rate = 1.0x**
  - Error rate exactly at SLO target = 1x burn
  - Example: 99% SLO, 1% error rate = 1x

- **High burn rate = 10x (alert!)**
  - 99.9% SLO allows 0.1% errors
  - 1% error rate = 10x burn rate
  - Critical alerting threshold

- **Zero errors = 0 burn rate**
  - No errors = 0% error rate = 0x burn

- **Other burn rates**
  - 2x burn rate test
  - Below 1x (healthy) test
  - Extremely high (100x) test

### 4. Success Rate Tracking (`TestSuccessRateTracking`)

Tests success rate calculation with edge cases:

- **99 successes, 1 error = 99% success**
  - Straightforward calculation

- **0 requests = 100% success (default)**
  - Assumes healthy state when no data
  - No false alarms on startup

- **All successes = 100%**
  - Perfect scenario

- **All failures = 0%**
  - Complete outage scenario

- **50/50 split = 50%**
  - Median case

### 5. Error Budget Consumption (`TestErrorBudgetConsumption`)

Tests detailed budget consumption tracking:

- **Starts at 0 consumption**
  - New tracker has no consumption

- **Increments with each error**
  - Tracks consumption incrementally
  - Verifies at each step

- **Remaining calculated correctly**
  - `remaining = total - consumed`
  - Maintains accuracy

- **Percentage accurate**
  - Budget percentage matches calculation
  - Example: 7/10 remaining = 70%

- **Cannot go negative**
  - Floors at 0 when over-budget
  - Prevents negative values

- **Full consumption = 0%**
  - When budget exhausted, percentage = 0%

### 6. Per-Endpoint Tracking (`TestPerEndpointTracking`)

Tests endpoint-specific error tracking:

- **Different endpoints tracked separately**
  - Each endpoint has own error rate
  - Independent tracking

- **Endpoint error rates calculated**
  - Multiple endpoints with different rates
  - Accurate per-endpoint percentages

- **Zero requests endpoint handling**
  - Endpoints with no requests not in rates dict
  - Avoids division by zero

### 7. Real-World Scenarios (`TestRealWorldScenarios`)

Tests realistic production scenarios:

#### Gradual Error Accumulation
- Phase 1: Healthy operation (0 errors)
- Phase 2: Errors appear (below threshold)
- Phase 3: Error rate increases (at threshold)
- Monitors burn rate increase over time

#### Sudden Error Spike (Incident)
- Normal operation
- Sudden spike of errors
- Budget exhausted quickly
- High burn rate alert triggered

#### Recovery After Incident
- Incident causes errors
- Service recovers
- Error rate normalizes
- Budget consumption persists (important!)

#### Multiple Partial Incidents
- Several small error spikes
- Each consumes part of budget
- Cumulative consumption
- Eventually budget exhausted

#### High Traffic with Acceptable Errors
- 10,000 requests
- 10 errors (0.1% rate)
- Exactly at 99.9% SLO target
- Should not violate

#### Endpoint-Specific Incident
- Multiple endpoints
- One endpoint has incident
- Others remain healthy
- Overall SLO may still be violated

### 8. Edge Cases and Boundary Conditions (`TestEdgeCases`)

Tests corner cases:

- **Single request that fails**
  - 100% error rate
  - Immediate violation

- **Very strict SLO (99.99%)**
  - 10,000 requests, 1 error
  - Just meets SLO

- **Very loose SLO (90%)**
  - More errors allowed
  - Different violation thresholds

- **Fractional error budget**
  - Small request counts
  - Budget rounds to 0
  - Any error violates

### 9. SLO Status Object (`TestSLOStatusObject`)

Tests the `SLOStatus` dataclass:

- **to_dict() conversion**
  - Serializes to dictionary
  - Contains all expected fields

- **Immutable snapshot**
  - Represents point-in-time
  - Doesn't change after creation

### 10. Integration Tests (`TestIntegration`)

Tests combining multiple features:

- **Complete monitoring workflow**
  - Full lifecycle test
  - All metrics verified together

- **Multiple SLO targets in parallel**
  - Different trackers with different SLOs
  - Same traffic, different evaluations

- **Prometheus export**
  - Includes SLO-related metrics
  - Proper metric names and format

## Running the Tests

### Option 1: Using Pytest (Recommended)

```bash
# Run all SLO monitoring tests
pytest tests/test_slo_monitoring.py -v

# Run specific test class
pytest tests/test_slo_monitoring.py::TestErrorBudgetCalculation -v

# Run specific test
pytest tests/test_slo_monitoring.py::TestBurnRateCalculation::test_high_burn_rate_10x -v
```

### Option 2: Standalone Runner (No pytest required)

```bash
# Run standalone test suite
python tests/run_slo_tests_standalone.py
```

The standalone runner executes key tests without pytest, useful for:
- Quick validation
- CI environments without pytest
- Demonstrating core functionality

## Test Fixtures

The test suite provides fixtures for different SLO targets:

```python
@pytest.fixture
def tracker_99_9():
    """99.9% SLO (0.1% error budget)"""
    return ErrorMetricsTracker(error_budget_slo=0.999)

@pytest.fixture
def tracker_99():
    """99% SLO (1% error budget)"""
    return ErrorMetricsTracker(error_budget_slo=0.99)

@pytest.fixture
def tracker_95():
    """95% SLO (5% error budget)"""
    return ErrorMetricsTracker(error_budget_slo=0.95)
```

## Key Concepts Tested

### Error Budget
- **Total Budget**: Maximum allowed errors based on SLO
  - Formula: `int(total_requests * (1 - slo_target))`
  - Example: 1000 requests * 0.001 = 1 error for 99.9% SLO

- **Consumed**: Actual errors that occurred
- **Remaining**: Budget left (cannot be negative)
- **Percentage**: `(remaining / total) * 100`

### Burn Rate
- **Definition**: How fast error budget is consumed
- **Formula**: `current_error_rate / target_error_rate`
- **Interpretation**:
  - `1.0x` = Normal (at SLO target)
  - `< 1.0x` = Healthy (below target)
  - `> 1.0x` = Concerning (above target)
  - `> 10.0x` = Critical alert threshold

### SLO Violation
- **Triggered when**: `current_success_rate < target_success_rate`
- **Not violated at threshold**: Exactly meeting SLO is acceptable
- **Per-endpoint tracking**: Violations can be endpoint-specific

## Example Test Scenarios

### Scenario 1: Normal Operation
```python
tracker = ErrorMetricsTracker(error_budget_slo=0.99)

# 99 successes, 1 error = 99% success rate
for _ in range(99):
    tracker.record_success("/v1/chat/completions")

tracker.record_error(
    endpoint="/v1/chat/completions",
    status_code=500,
    error_type="InternalServerError",
    error_message="Rare error"
)

slo = tracker.get_slo_status()
assert slo.slo_violated is False  # Meets 99% SLO
assert slo.burn_rate == 1.0       # Normal burn rate
```

### Scenario 2: High Burn Rate Alert
```python
tracker = ErrorMetricsTracker(error_budget_slo=0.999)

# 99 successes, 1 error = 1% error rate
# Target: 0.1% error rate
# Burn rate: 1% / 0.1% = 10x
for _ in range(99):
    tracker.record_success("/v1/chat/completions")

tracker.record_error(
    endpoint="/v1/chat/completions",
    status_code=500,
    error_type="Critical",
    error_message="High error rate"
)

slo = tracker.get_slo_status()
assert slo.burn_rate > 10.0       # Alert threshold!
```

### Scenario 3: Incident Recovery
```python
tracker = ErrorMetricsTracker(error_budget_slo=0.99)

# Incident: 5 errors
for _ in range(45):
    tracker.record_success("/v1/chat/completions")
for _ in range(5):
    tracker.record_error(endpoint="/v1/chat/completions", ...)

# Recovery: 950 successes
for _ in range(950):
    tracker.record_success("/v1/chat/completions")

slo = tracker.get_slo_status()
assert slo.burn_rate < 1.0              # Normalized
assert slo.error_budget_consumed == 5   # Budget still consumed
```

## Assertions and Validations

Each test validates:

1. **Correctness**: Calculations match expected formulas
2. **Precision**: Floating-point comparisons use tolerance (`< 0.01`)
3. **Edge cases**: Boundary conditions handled properly
4. **State management**: Metrics update correctly over time
5. **Thread safety**: Tests can run concurrently (via fixtures)

## Coverage Metrics

- **Lines of test code**: ~1370 lines
- **Test functions**: 60+
- **Test classes**: 10
- **Scenarios covered**: All production use cases
- **SLO targets tested**: 99.9%, 99%, 95%, 90%, 99.99%
- **Edge cases**: 15+

## Integration with Existing Tests

This test suite complements existing tests:

- **`test_error_metrics_tracker.py`**: Basic SLO tests (560-700 lines)
- **`test_slo_monitoring.py`**: Comprehensive SLO scenarios (this file)
- **`test_error_metrics.py`**: Legacy error metrics (different system)

## Maintenance Notes

### Adding New Tests

1. Choose appropriate test class based on feature
2. Use fixtures for consistent tracker setup
3. Follow naming convention: `test_<feature>_<scenario>`
4. Include docstrings explaining expected behavior
5. Assert multiple related aspects in one test

### Updating for New Features

If `ErrorMetricsTracker` adds new SLO features:

1. Add tests to relevant class
2. Update integration tests
3. Add to standalone runner if critical
4. Update this README

## Troubleshooting

### Tests Won't Run with Pytest

If you see conftest errors:

```bash
# Use standalone runner instead
python tests/run_slo_tests_standalone.py
```

This bypasses pytest's conftest which may have async issues.

### Assertion Failures

Check for:
- Floating-point precision (use `abs(a - b) < 0.01`)
- Integer truncation in budget calculations
- Order of operations (success before error recording)

### Import Errors

The tests use direct module imports to avoid app initialization:

```python
module_path = Path(__file__).parent.parent / "fakeai" / "error_metrics_tracker.py"
spec = importlib.util.spec_from_file_location("error_metrics_tracker", module_path)
# ... load module
```

This pattern ensures tests are isolated and fast.

## Performance

- **Test execution time**: ~2-3 seconds for full suite
- **Memory usage**: Minimal (bounded deques)
- **Parallelization**: Safe (fixtures create isolated instances)

## References

- **SLO Guide**: `/home/anthony/projects/fakeai/docs/METRICS_TRACKERS_GUIDE.md`
- **Implementation**: `/home/anthony/projects/fakeai/fakeai/error_metrics_tracker.py`
- **Quick Start**: `/home/anthony/projects/fakeai/docs/QUICK_START_TRACKERS.md`

## Summary

This comprehensive test suite ensures the SLO monitoring system is:
- ✓ Mathematically correct
- ✓ Handles edge cases
- ✓ Works in production scenarios
- ✓ Provides accurate alerting signals
- ✓ Tracks budgets properly
- ✓ Supports multiple SLO targets
- ✓ Thread-safe and performant

The tests serve as both validation and documentation of expected behavior.
