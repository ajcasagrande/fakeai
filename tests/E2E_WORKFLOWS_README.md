# End-to-End Workflow Tests

This test suite (`test_e2e_workflows.py`) provides comprehensive end-to-end testing of the FakeAI metrics system, simulating real production usage patterns.

## Overview

The tests validate complete request lifecycles including:
- Standard request workflows (started → completed → metrics updated)
- Streaming workflows with TTFT/ITL/TPS calculations
- Error scenarios with pattern detection
- Mixed workloads with various models
- Budget exceeded scenarios
- SLO violation detection and burn rate calculation

## Test Coverage

### 1. Complete Request Lifecycle (`TestCompleteRequestLifecycle`)
- **Single request**: Validates full lifecycle from start to completion
- **Multiple requests**: Tests 10 sequential requests with varying token counts
- **Trackers validated**: MetricsTracker, CostTracker, ModelMetricsTracker, ErrorMetricsTracker

### 2. Complete Streaming Lifecycle (`TestCompleteStreamingLifecycle`)
- **Single stream**: Tests streaming with TTFT (50ms), ITL (10ms), and TPS calculations
- **Multiple parallel streams**: Simulates 5 concurrent streams with different characteristics
- **Metrics validated**: TTFT, ITL, TPS, per-model breakdown

### 3. Error Scenarios (`TestErrorScenario`)
- **Single error tracking**: Validates error recording and SLO updates
- **Pattern detection**: Tests detection of recurring error patterns (5 similar errors)
- **Mixed errors/successes**: 95 successes + 5 errors = 95% success rate
- **SLO validation**: Verifies 95% < 99.9% target triggers SLO violation

### 4. Mixed Workload (`TestMixedWorkload`)
Realistic production simulation:
- 50 successful standard requests (various models)
- 10 streaming requests
- 5 failed requests
- 3 different API keys
- 3 different models (gpt-4o, gpt-4o-mini, gpt-3.5-turbo)

### 5. Budget Exceeded Scenarios (`TestBudgetExceededScenario`)
- **Soft limit**: $10 budget with $12.50 request (warning only)
- **Alert threshold**: Tests 80% threshold triggering at $8+

### 6. SLO Violation Scenarios (`TestSLOViolationScenario`)
- **Violation detection**: 98% success < 99.9% target with 20x burn rate
- **Within target**: 99.95% success >= 99.9% target (no violation)
- **Edge case**: Exactly 99.9% success at threshold boundary

### 7. Production Realistic Workload (`TestEndToEndIntegration`)
Comprehensive integration test:
- 100 total requests over multiple API keys
- 70% standard, 30% streaming
- 2% error rate
- Budget tracking for all users
- Per-model metrics aggregation

## Running the Tests

### Run all tests
```bash
python -m pytest tests/test_e2e_workflows.py --noconftest -v
```

### Run specific test class
```bash
python -m pytest tests/test_e2e_workflows.py::TestCompleteRequestLifecycle --noconftest -v
```

### Run specific test
```bash
python -m pytest tests/test_e2e_workflows.py::TestCompleteRequestLifecycle::test_single_request_complete_lifecycle --noconftest -v
```

### Run with detailed output
```bash
python -m pytest tests/test_e2e_workflows.py --noconftest -v -s
```

**Note**: The `--noconftest` flag is required to avoid loading the global conftest.py which would initialize the full FastAPI app.

## Test Architecture

### Direct Module Loading
The tests use direct module loading to avoid triggering the FastAPI app initialization:

```python
import importlib.util

def load_module_from_file(module_name, file_path):
    """Load a module directly from a file without triggering __init__.py."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
```

This allows us to:
- Test metrics trackers independently
- Avoid async event loop issues
- Run tests faster without full app startup
- Focus purely on metrics functionality

### Fixtures
Each test class receives fresh instances of:
- `metrics_tracker`: MetricsTracker for request/response tracking
- `cost_tracker`: CostTracker for billing simulation
- `model_tracker`: ModelMetricsTracker for per-model analytics
- `error_tracker`: ErrorMetricsTracker for error analysis and SLO monitoring
- `streaming_tracker`: StreamingMetricsTracker for streaming metrics

## Key Metrics Verified

### MetricsTracker
- Requests per second (RPS)
- Responses per second
- Tokens per second
- Latency percentiles (p50, p90, p99)
- Error rates

### CostTracker
- Cost per request
- Total cost by API key
- Budget tracking and alerts
- Per-model cost breakdown

### ModelMetricsTracker
- Request count per model
- Token usage per model
- Latency statistics per model
- Error rates per model
- Cost per model

### ErrorMetricsTracker
- Error rate and success rate
- Error pattern detection
- SLO violation detection
- Error budget consumption
- Burn rate calculation

### StreamingMetricsTracker
- Time to First Token (TTFT)
- Inter-Token Latency (ITL)
- Tokens Per Second (TPS)
- Active/completed/failed stream counts
- Per-model streaming metrics

## Realistic Production Values

The tests use realistic values:
- **Latency**: 10-100ms per request
- **TTFT**: 30-50ms for first token
- **ITL**: 5-10ms between tokens
- **Token counts**: 50-300 tokens per request
- **Error rates**: 2-5% for realistic scenarios
- **Budget limits**: $10-$100 for cost tracking
- **SLO targets**: 99.9% success rate

## Assertion Strategy

Tests follow these assertion patterns:

1. **Exact matches** for counters: `assert count == expected`
2. **Tolerance** for costs: `assert abs(cost - expected) < 0.000001`
3. **Ranges** for timing: `assert 40 <= ttft_ms <= 70`
4. **Thresholds** for rates: `assert success_rate >= 0.999`

## Expected Behavior

All 14 tests should pass:
```
============================== 14 passed in ~5s ===============================
```

Typical test execution time: **4-5 seconds**

## Troubleshooting

### Import Error
If you see `RuntimeError: no running event loop`:
- Ensure you're using `--noconftest` flag
- The test file loads modules directly to avoid this

### Assertion Failures
- Check timing assertions - they use ranges to account for system variation
- Verify fixture isolation - each test should get fresh tracker instances

### Performance Issues
- Tests include `time.sleep()` calls for realistic timing
- Reduce sleep times in fixtures if tests are too slow

## Future Enhancements

Potential additions:
- [ ] Rate limiting scenarios
- [ ] Cache hit/miss tracking
- [ ] Batch processing workflows
- [ ] Multi-tenant isolation tests
- [ ] Long-running stress tests
- [ ] Memory leak detection
- [ ] Concurrent request handling

## Related Files

- `/fakeai/metrics.py` - MetricsTracker implementation
- `/fakeai/cost_tracker.py` - CostTracker implementation
- `/fakeai/model_metrics.py` - ModelMetricsTracker implementation
- `/fakeai/error_metrics_tracker.py` - ErrorMetricsTracker implementation
- `/fakeai/streaming_metrics_tracker.py` - StreamingMetricsTracker implementation
- `/fakeai/events/event_types.py` - Event type definitions

## License

Apache 2.0
