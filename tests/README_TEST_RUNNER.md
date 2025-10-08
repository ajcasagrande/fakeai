# FakeAI Metrics Test Runner

## Overview

This directory contains a comprehensive test runner for FakeAI's metrics system. The test runner discovers, executes, and generates coverage reports for all metrics-related tests.

## Quick Start

```bash
# Run all metrics tests with coverage
python tests/run_all_metrics_tests.py --metrics-only

# Run with custom coverage threshold
python tests/run_all_metrics_tests.py --metrics-only --coverage-threshold 80

# Run with verbose output
python tests/run_all_metrics_tests.py --metrics-only --verbose

# Run without HTML report
python tests/run_all_metrics_tests.py --metrics-only --no-html
```

## Files

### Main Test Runner
- **`run_all_metrics_tests.py`** - Full-featured test runner with:
  - Automatic test discovery
  - Coverage reporting (term, JSON, HTML)
  - Test counting and categorization
  - Import verification
  - CI/CD ready (proper exit codes)

### Coverage Configuration
- **`pyproject.toml`** - Contains pytest and coverage configuration:
  - Source paths
  - Exclusions
  - Branch coverage enabled
  - Output formats

## Test Organization

### Metrics Tests (42 files, 1410+ tests)
The runner automatically detects these test categories:
- `test_batch_metrics.py` - Batch processing metrics
- `test_cost_*` - Cost tracking and calculations
- `test_error_*` - Error tracking and pattern detection
- `test_event_*` - Event bus and emitter tests
- `test_streaming_*` - Streaming metrics tracking
- `test_metrics_*` - General metrics tests
- `test_prometheus_export.py` - Prometheus format export
- `test_slo_monitoring.py` - SLO monitoring
- And more...

## Key Modules Covered

The test suite provides comprehensive coverage for:

### Event System
- `fakeai/events/subscribers.py`
- `fakeai/events/emitter.py`
- `fakeai/events/event_types.py`
- `fakeai/events/bus.py`
- `fakeai/events/base.py`

### Metrics Trackers
- `fakeai/streaming_metrics_tracker.py`
- `fakeai/error_metrics_tracker.py`
- `fakeai/cost_tracker.py`

## Coverage Reporting

### Terminal Report
Shows line-by-line coverage with missing lines highlighted.

### HTML Report
```bash
# Open in browser after running tests
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### JSON Report
Machine-readable coverage data in `coverage.json` for CI/CD integration.

## CI/CD Integration

The test runner is designed for CI/CD pipelines:

### Exit Codes
- `0` - All tests passed AND coverage meets threshold
- `1` - Tests failed OR coverage below threshold

### Example GitHub Actions
```yaml
- name: Run Metrics Tests
  run: |
    python tests/run_all_metrics_tests.py --metrics-only --coverage-threshold 80
```

### Example GitLab CI
```yaml
test:metrics:
  script:
    - python tests/run_all_metrics_tests.py --metrics-only --coverage-threshold 80
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

## Advanced Usage

### Run Specific Test Patterns
```bash
# Use pytest directly for more control
pytest tests/test_streaming_metrics_tracker.py -v --cov=fakeai/streaming_metrics_tracker.py
```

### Debug Failing Tests
```bash
# Run with full traceback
python tests/run_all_metrics_tests.py --metrics-only --verbose

# Or use pytest directly
pytest tests/ -k "streaming" -vv --tb=long
```

### Update Coverage Threshold
Edit `run_all_metrics_tests.py`:
```python
parser.add_argument(
    '--coverage-threshold',
    type=int,
    default=80,  # Change this value
    help='Minimum coverage percentage required'
)
```

## Troubleshooting

### Import Errors
The runner uses `--noconftest` flag to avoid event loop issues with the main app initialization. If you see import warnings, this is expected and won't affect test execution.

### Coverage Not Collected
Some tests use direct module imports (via `importlib.util`) to avoid app initialization overhead. This is intentional and doesn't affect test quality.

### Slow Tests
Metrics tests include performance tests. Skip them with:
```bash
pytest tests/ -k "not performance" --metrics-only
```

## Test Statistics

- **Total test files**: 163
- **Metrics test files**: 42
- **Total metrics tests**: 1410+
- **Average tests per file**: 33
- **Test categories**: 9 (streaming, error, cost, event, etc.)

## Contributing

When adding new metrics functionality:

1. Create corresponding test file with `test_` prefix
2. Include metrics-related keywords in filename
3. Aim for 80%+ coverage
4. Run the test runner before committing:
   ```bash
   python tests/run_all_metrics_tests.py --metrics-only
   ```

## See Also

- `pyproject.toml` - Pytest configuration
- `conftest.py` - Shared fixtures (skipped by metrics tests)
- Individual test files for specific module documentation
