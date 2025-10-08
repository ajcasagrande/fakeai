# Test Index - Quick Navigation

## Integration Tests (E2E)

### **FINAL_INTEGRATION_TEST.py** ⭐ RECOMMENDED
**The comprehensive production-quality integration test**

- **Purpose**: Complete system validation in one script
- **Tests**: 45+ automated checks
- **Duration**: ~5-10 seconds
- **Features**:
  - Server health check
  - 20 mixed requests (streaming + non-streaming)
  - All 5 metrics endpoints
  - Data validation & consistency checks
  - Beautiful colored output
  - CLI arguments support
  - CI/CD ready

**Usage**:
```bash
python tests/FINAL_INTEGRATION_TEST.py
python tests/FINAL_INTEGRATION_TEST.py --help
```

**Documentation**:
- `README_FINAL_INTEGRATION_TEST.md` - Full documentation
- `QUICK_START_FINAL_TEST.md` - Quick reference
- `FINAL_INTEGRATION_TEST_SUMMARY.md` - Overview

**Exit Codes**: 0 = pass, 1 = fail

---

### verify_event_flow.py
**Event system validation**

- **Purpose**: Verify events flow through the system
- **Tests**: Event bus, error metrics, streaming metrics
- **Duration**: ~5 seconds
- **Focus**: Event publishing and processing

**Usage**:
```bash
python tests/verify_event_flow.py
```

---

### verify_error_metrics_live.py
**Error tracking validation**

- **Purpose**: Validate error metrics and SLO tracking
- **Tests**: Error counting, SLO status, error patterns
- **Duration**: ~10 seconds
- **Focus**: Error handling and monitoring

**Usage**:
```bash
python tests/verify_error_metrics_live.py
```

---

### verify_streaming_metrics_live.py
**Streaming performance validation**

- **Purpose**: Validate streaming metrics collection
- **Tests**: TTFT, ITL, TPS metrics
- **Duration**: ~8 seconds
- **Focus**: Streaming performance tracking

**Usage**:
```bash
python tests/verify_streaming_metrics_live.py
```

---

### verify_prometheus_complete.py
**Prometheus metrics validation**

- **Purpose**: Validate Prometheus metrics export
- **Tests**: Prometheus format, metrics accuracy
- **Duration**: ~5 seconds
- **Focus**: Prometheus integration

**Usage**:
```bash
python tests/verify_prometheus_complete.py
```

---

### verify_cost_tracking_live.py
**Cost tracking validation**

- **Purpose**: Validate cost calculation and tracking
- **Tests**: Token costs, billing accuracy
- **Duration**: ~8 seconds
- **Focus**: Cost and billing

**Usage**:
```bash
python tests/verify_cost_tracking_live.py
```

---

## Unit Tests (Component-Level)

### Metrics Tests
- `test_metrics.py` - Basic metrics functionality
- `test_metrics_direct.py` - Direct metrics API tests
- `test_metrics_dashboard.py` - Dashboard metrics tests
- `test_metrics_integration_complete.py` - Full metrics integration
- `test_metrics_streaming.py` - Streaming metrics
- `test_metrics_stress.py` - Stress testing

### Event Bus Tests
- `test_event_bus.py` - Event bus core functionality
- `test_event_bus_factory.py` - Event bus creation
- `test_event_emitter.py` - Event emission
- `test_event_types.py` - Event type validation

### Tracker Tests
- `test_error_metrics_tracker.py` - Error tracking
- `test_streaming_metrics_tracker.py` - Streaming tracking
- `test_streaming_latency_metrics.py` - Latency tracking
- `test_slo_monitoring.py` - SLO monitoring

### Performance Tests
- `test_10k_concurrent.py` - Concurrent request handling
- `test_thread_safety.py` - Thread safety validation
- `test_memory_bounds.py` - Memory usage validation

---

## Test Runners

### run_all_metrics_tests.py
**Run all metrics tests**

```bash
python tests/run_all_metrics_tests.py
```

### run_metrics_tests_simple.py
**Run basic metrics tests**

```bash
python tests/run_metrics_tests_simple.py
```

### run_slo_tests_standalone.py
**Run SLO monitoring tests**

```bash
python tests/run_slo_tests_standalone.py
```

---

## Documentation

### Quick References
- `QUICK_START_FINAL_TEST.md` - Integration test quick start
- `QUICK_START_TRACKERS.md` - Metrics trackers guide
- `TTFT_ITL_QUICK_REFERENCE.md` - Streaming metrics reference

### Full Guides
- `README_FINAL_INTEGRATION_TEST.md` - Integration test documentation
- `README_ERROR_METRICS_TESTING.md` - Error metrics guide
- `VERIFY_COST_TRACKING_README.md` - Cost tracking guide
- `README.md` - General testing overview

### Status Reports
- `FINAL_INTEGRATION_TEST_SUMMARY.md` - Integration test details
- `E2E_WORKFLOWS_README.md` - End-to-end workflows
- `TEST_COST_TRACKER.md` - Cost tracking status
- `TEST_SLO_MONITORING_README.md` - SLO monitoring status

---

## Which Test Should I Run?

### For Production Validation
✅ **Use: `FINAL_INTEGRATION_TEST.py`**
- Most comprehensive
- Fast (~5-10s)
- Clear pass/fail
- CI/CD ready

### For Event System Debugging
✅ **Use: `verify_event_flow.py`**
- Focused on events
- Shows event counts
- Quick validation

### For Error Tracking Debugging
✅ **Use: `verify_error_metrics_live.py`**
- Error-specific
- SLO status
- Error patterns

### For Streaming Issues
✅ **Use: `verify_streaming_metrics_live.py`**
- Streaming-specific
- TTFT/ITL metrics
- Performance data

### For Development (Unit Tests)
✅ **Use: `pytest tests/test_*.py`**
- Component-level
- Faster feedback
- Isolated testing

### For CI/CD Pipeline
✅ **Use: `FINAL_INTEGRATION_TEST.py`**
- Single command
- Exit code support
- Comprehensive coverage

---

## Test Hierarchy

```
Production Validation
└── FINAL_INTEGRATION_TEST.py (⭐ RECOMMENDED)
    ├── Server Health
    ├── Request Processing
    ├── Metrics Endpoints
    ├── Data Validation
    └── Consistency Checks

System Verification
├── verify_event_flow.py
├── verify_error_metrics_live.py
├── verify_streaming_metrics_live.py
├── verify_prometheus_complete.py
└── verify_cost_tracking_live.py

Component Testing
├── Metrics Tests (test_metrics*.py)
├── Event Tests (test_event*.py)
├── Tracker Tests (test_*_tracker.py)
└── Performance Tests (test_*_concurrent.py)

Test Runners
├── run_all_metrics_tests.py
├── run_metrics_tests_simple.py
└── run_slo_tests_standalone.py
```

---

## Common Commands

```bash
# Run comprehensive integration test
python tests/FINAL_INTEGRATION_TEST.py

# Run with custom port
python tests/FINAL_INTEGRATION_TEST.py --port 8080

# Run specific verification
python tests/verify_event_flow.py

# Run unit tests with pytest
pytest tests/test_metrics.py -v

# Run all unit tests
pytest tests/ -v

# Run all metrics tests
python tests/run_all_metrics_tests.py

# Start server for manual testing
python -m fakeai --port 8765
```

---

## CI/CD Integration

### Recommended Setup

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Start server
        run: python -m fakeai --port 8765 &

      - name: Wait for server
        run: sleep 5

      - name: Run integration tests
        run: python tests/FINAL_INTEGRATION_TEST.py

      - name: Run unit tests
        run: pytest tests/ -v --maxfail=5

  verification:
    runs-on: ubuntu-latest
    needs: integration
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Start server
        run: python -m fakeai --port 8765 &

      - name: Verify event flow
        run: python tests/verify_event_flow.py

      - name: Verify error metrics
        run: python tests/verify_error_metrics_live.py

      - name: Verify streaming
        run: python tests/verify_streaming_metrics_live.py
```

---

## Test Coverage Summary

| Category | Tests | Coverage |
|----------|-------|----------|
| Integration | 1 | Complete system |
| Verification | 5 | Subsystems |
| Unit | 100+ | Components |
| Performance | 3 | Load/stress |
| Total | 109+ | Comprehensive |

---

## Quick Decision Tree

```
Need to validate production?
  └─> FINAL_INTEGRATION_TEST.py ⭐

Events not working?
  └─> verify_event_flow.py

Errors not tracked?
  └─> verify_error_metrics_live.py

Streaming issues?
  └─> verify_streaming_metrics_live.py

Developing new feature?
  └─> pytest tests/test_*.py

Setting up CI/CD?
  └─> FINAL_INTEGRATION_TEST.py ⭐

Testing specific component?
  └─> pytest tests/test_[component].py

Need comprehensive validation?
  └─> FINAL_INTEGRATION_TEST.py ⭐
```

---

## Support

For test issues or questions:

1. Check test documentation (README files)
2. Run with `--help` for options
3. Verify server is running: `curl http://localhost:8765/health`
4. Check server logs
5. Review test output for specific failures

---

## License

Apache-2.0

---

**Last Updated**: 2025-10-07

**Maintained By**: FakeAI Development Team
