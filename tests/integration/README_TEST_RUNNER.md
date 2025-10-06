# Intelligent Master Test Runner

## Overview

`RUN_ALL_TESTS.py` is a comprehensive test orchestration tool that systematically runs all test files, provides beautiful reporting, intelligent failure analysis, and actionable recommendations.

## Features

### Core Capabilities
- **Individual File Testing** - Tests each file separately with configurable timeout (default: 60s)
- **Real-time Progress** - Live updates showing test execution status
- **Beautiful Reporting** - ASCII table with color-coded results
- **Intelligent Analysis** - Automatically detects common failure patterns
- **Actionable Recommendations** - Suggests specific fixes based on failure types
- **Parallel Execution** - Run tests concurrently with configurable worker count
- **Result Filtering** - Filter by status (passed/failed/error/timeout)
- **JSON Export** - Export results for CI/CD integration
- **Comprehensive Metrics** - Track pass rates, durations, test counts

### Test Status Types
- `PASSED` ✓ - All tests in file passed (green)
- `FAILED` ✗ - Some tests failed (red)
- `ERROR` ⚠ - Test execution error (yellow)
- `TIMEOUT` ⏱ - Test exceeded time limit (magenta)

### Failure Pattern Detection
Automatically identifies:
- `import_error` - Missing modules or import issues
- `attribute_error` - Missing attributes or methods
- `assertion_error` - Test assertion failures
- `type_error` - Type mismatch errors
- `value_error` - Invalid values
- `connection_error` - Network/connection issues
- `timeout` - Long-running tests
- `fixture_error` - Pytest fixture problems
- `async_error` - Async/event loop issues
- `deprecation` - Deprecation warnings

## Usage

### Basic Usage

```bash
# Run all tests sequentially
python tests/integration/RUN_ALL_TESTS.py

# Run with custom timeout (120 seconds per file)
python tests/integration/RUN_ALL_TESTS.py --timeout 120

# Run with verbose output
python tests/integration/RUN_ALL_TESTS.py --verbose
```

### Parallel Execution

```bash
# Run in parallel with default 4 workers
python tests/integration/RUN_ALL_TESTS.py --parallel

# Run with 8 workers
python tests/integration/RUN_ALL_TESTS.py --parallel 8

# Recommended for fast execution on multi-core systems
python tests/integration/RUN_ALL_TESTS.py --parallel 8 --timeout 30
```

### Filtering Results

```bash
# Show only failed tests
python tests/integration/RUN_ALL_TESTS.py --filter failed

# Show only passed tests
python tests/integration/RUN_ALL_TESTS.py --filter passed

# Show only errors
python tests/integration/RUN_ALL_TESTS.py --filter error

# Show only timeouts
python tests/integration/RUN_ALL_TESTS.py --filter timeout
```

### Testing Specific Directories

```bash
# Test only service layer
python tests/integration/RUN_ALL_TESTS.py --dir tests/services

# Test only handlers
python tests/integration/RUN_ALL_TESTS.py --dir tests/handlers

# Test only streaming
python tests/integration/RUN_ALL_TESTS.py --dir tests/streaming
```

### Exporting Results

```bash
# Export to JSON
python tests/integration/RUN_ALL_TESTS.py --export results.json

# Export with filtering (only failed tests)
python tests/integration/RUN_ALL_TESTS.py --filter failed --export failed_tests.json

# Export for CI/CD pipeline
python tests/integration/RUN_ALL_TESTS.py --no-color --export ci_results.json
```

### Combined Options

```bash
# Fast parallel execution with export
python tests/integration/RUN_ALL_TESTS.py --parallel 8 --timeout 30 --export results.json

# Debug failed tests only
python tests/integration/RUN_ALL_TESTS.py --filter failed --verbose

# Quick check of specific directory
python tests/integration/RUN_ALL_TESTS.py --dir tests/services --parallel 4 --timeout 20
```

## Output Report Structure

### Summary Section
```
SUMMARY:
  Total Test Files:     142
  ✓ Passed Files:      120 (84.5%)
  ✗ Failed Files:      15
  ⚠ Error Files:       5
  ⏱ Timeout Files:     2
  Total Duration:       450.32s (7.5m)

TEST COUNTS:
  Tests Passed:         1,350
  Tests Failed:         45
  Tests Skipped:        12
  Test Errors:          8
```

### Detailed Results Table
```
FILE                                               STATUS       PASS   FAIL   SKIP   ERR    RATE     TIME
------------------------------------------------------------------------------------------------------------------------
test_audio.py                                      PASSED       28     0      0      0      100.0%   5.23   s
test_batch_service.py                              FAILED       15     8      0      52     20.0%    11.43  s
test_moderation_service.py                         FAILED       20     1      0      0      95.2%    0.98   s
test_image_generation.py                           TIMEOUT      0      0      0      1      0.0%     60.01  s
```

### Failure Analysis
```
FAILURE ANALYSIS:

Common Failure Patterns:
  • assertion_error      (15 occurrences)
  • import_error         (5 occurrences)
  • timeout              (2 occurrences)

Failed Files Details:

  ✗ test_batch_service.py
    Status: failed
    Exit Code: 1
    Patterns: assertion_error
    test_batch_service.py::test_cancel_completed_batch FAILED
    test_batch_service.py::test_list_batches_multiple FAILED
```

### Recommendations
```
RECOMMENDATIONS:

  ⚠ Good progress (84.5%), but needs attention.
  • Focus on common failure patterns
  • Run individual failed tests with -vv for details
  • Fix assertion errors (verify test expectations)
  • Fix import errors (check dependencies and module paths)
  • Investigate timeouts (increase --timeout or optimize tests)
```

## JSON Export Format

```json
{
  "summary": {
    "total_files": 142,
    "passed_files": 120,
    "failed_files": 15,
    "error_files": 5,
    "timeout_files": 2,
    "total_duration": 450.32,
    "total_tests_passed": 1350,
    "total_tests_failed": 45,
    "total_tests_skipped": 12,
    "total_tests_errors": 8
  },
  "results": [
    {
      "file_path": "tests/test_audio.py",
      "file_name": "test_audio.py",
      "status": "passed",
      "passed": 28,
      "failed": 0,
      "skipped": 0,
      "errors": 0,
      "warnings": 0,
      "duration": 5.23,
      "exit_code": 0,
      "error_message": null,
      "failure_patterns": []
    }
  ]
}
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run Test Suite
  run: |
    python tests/integration/RUN_ALL_TESTS.py \
      --parallel 4 \
      --timeout 60 \
      --export test_results.json \
      --no-color

- name: Upload Test Results
  uses: actions/upload-artifact@v3
  with:
    name: test-results
    path: test_results.json
```

### GitLab CI Example

```yaml
test:
  script:
    - python tests/integration/RUN_ALL_TESTS.py --parallel 4 --export results.json --no-color
  artifacts:
    reports:
      junit: results.json
```

## Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed, errored, or timed out

## Performance Tips

### For Fast Feedback
```bash
# Run with high parallelism and short timeout
python tests/integration/RUN_ALL_TESTS.py --parallel 8 --timeout 20
```

### For Comprehensive Testing
```bash
# Run sequentially with long timeout for stability
python tests/integration/RUN_ALL_TESTS.py --timeout 120
```

### For Debugging
```bash
# Run failed tests only with verbose output
python tests/integration/RUN_ALL_TESTS.py --filter failed --verbose --timeout 120
```

### For Specific Areas
```bash
# Test only critical paths
python tests/integration/RUN_ALL_TESTS.py --dir tests/services --parallel 4
```

## Troubleshooting

### High Timeout Rate
- Increase timeout: `--timeout 120`
- Check for hanging tests (infinite loops, deadlocks)
- Review async test implementations
- Consider breaking up long tests

### Import Errors
- Verify dependencies installed: `pip install -e .`
- Check Python path configuration
- Ensure `__init__.py` files exist
- Review relative import paths

### Fixture Errors
- Check `conftest.py` setup
- Verify fixture names match usage
- Ensure fixture scope is correct
- Review fixture dependencies

### Parallel Execution Issues
- Reduce worker count: `--parallel 2`
- Check for race conditions
- Review shared resource usage (files, ports)
- Consider sequential execution for debugging

## Advanced Usage

### Custom Test Discovery
```python
# Modify find_test_files() to customize discovery
def find_test_files(self) -> List[Path]:
    # Add custom patterns
    test_files = []
    for pattern in ['test_*.py', '*_test.py', 'integration_*.py']:
        test_files.extend(self.tests_dir.rglob(pattern))
    return sorted(test_files)
```

### Custom Failure Patterns
```python
# Extend pattern_checks in _identify_failure_patterns()
pattern_checks = {
    'custom_error': r'YourCustomError',
    'database_error': r'DatabaseError|IntegrityError',
    # Add more patterns
}
```

### Custom Report Format
```python
# Modify generate_report() for custom formatting
# Add sections, change colors, adjust layout
```

## Best Practices

1. **Run Regularly** - Execute test runner frequently during development
2. **Use Filters** - Focus on failed tests when fixing issues
3. **Export Results** - Keep historical data for trend analysis
4. **Parallel for Speed** - Use parallel mode for quick feedback
5. **Sequential for Debug** - Use sequential mode when debugging
6. **Set Appropriate Timeouts** - Balance speed vs completeness
7. **Review Patterns** - Focus on common failure patterns first
8. **Track Metrics** - Monitor pass rates and test counts over time

## Examples

### Quick Health Check
```bash
# Fast check of all tests
python tests/integration/RUN_ALL_TESTS.py --parallel 8 --timeout 20
```

### Full Test Suite Run
```bash
# Comprehensive test with export
python tests/integration/RUN_ALL_TESTS.py --timeout 120 --export full_results.json
```

### Debug Failed Tests
```bash
# Detailed output for failures only
python tests/integration/RUN_ALL_TESTS.py --filter failed --verbose --timeout 180
```

### Pre-commit Hook
```bash
# Run services and handlers before commit
python tests/integration/RUN_ALL_TESTS.py --dir tests/services --parallel 4
python tests/integration/RUN_ALL_TESTS.py --dir tests/handlers --parallel 4
```

### Continuous Integration
```bash
# CI-friendly execution with JSON export
python tests/integration/RUN_ALL_TESTS.py \
  --parallel $(nproc) \
  --timeout 60 \
  --no-color \
  --export ci_results.json
```

## Support

For issues or questions:
1. Check the failure analysis section in output
2. Review recommendations for actionable fixes
3. Run individual test files with `pytest -vv`
4. Examine error patterns in JSON export
5. Use `--verbose` flag for detailed execution logs

## Version History

- **v1.0** (2025-10-06) - Initial release
  - Individual file testing with timeout
  - Beautiful ASCII table reporting
  - Parallel and sequential execution
  - Failure pattern detection
  - JSON export
  - Result filtering
  - Comprehensive metrics

## License

Part of the FakeAI project - see main project LICENSE.
