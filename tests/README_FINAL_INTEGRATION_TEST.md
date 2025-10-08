# Final Integration Test - Production Validation

## Overview

`FINAL_INTEGRATION_TEST.py` is a comprehensive, production-quality integration test that validates the complete FakeAI server system. This test is designed for CI/CD pipelines, pre-release validation, and production readiness checks.

## What It Tests

### 1. Server Health Check (30s timeout)
- Port availability on 8765
- Health endpoint response
- Server ready state

### 2. Mixed Request Load (20 requests)
- **10 Non-Streaming Requests**
  - Various models (gpt-4, gpt-4-turbo, gpt-3.5-turbo, claude-3-opus, claude-3-sonnet)
  - Token counting
  - Response validation

- **10 Streaming Requests**
  - Same model variety
  - SSE stream consumption
  - Chunk counting
  - Stream completion

### 3. Metrics Endpoints Validation
Checks that all 5 metrics endpoints respond:
- `/metrics` - Dashboard format metrics
- `/metrics/events` - Event bus statistics
- `/metrics/errors` - Error tracking
- `/metrics/streaming` - Streaming performance
- `/metrics/slo` - SLO status

### 4. Data Validation
For each endpoint, validates expected data structure:

**`/metrics`**
- `total_requests` > 0
- `requests_per_second` exists
- `avg_response_time` exists

**`/metrics/events`**
- `events_published` (numeric)
- `events_processed` (numeric)
- `queue_depth` (numeric)

**`/metrics/errors`**
- `total_requests` > 0
- `total_errors` (numeric)
- `error_rate` (numeric)

**`/metrics/streaming`**
- `total_streams` (numeric)
- `successful_streams` (numeric)
- `ttft_percentiles` (dict or null)

**`/metrics/slo`**
- `success_rate` (numeric)
- `error_budget_remaining` (numeric)
- `slo_target` (numeric)

### 5. Data Consistency Checks

**Request Count Consistency**
- `/metrics` `total_requests` should match `/metrics/errors` `total_requests` (±2 tolerance)

**Streaming Count Consistency**
- `total_streams` = `successful_streams` + `failed_streams`

**SLO Rate Consistency**
- `success_rate` ≈ 1.0 - `error_rate` (±2% tolerance)

**Event Bus Activity**
- `events_published` > 0 (events are flowing)

### 6. Exception Monitoring
- Checks for exceptions in logs (placeholder in current version)
- Ready for integration with logging systems

## Usage

### Prerequisites
```bash
# Server must be running
python -m fakeai --port 8765
```

### Run Test
```bash
# From repository root
python tests/FINAL_INTEGRATION_TEST.py

# Or from tests directory
./FINAL_INTEGRATION_TEST.py
```

### Expected Output
```
================================================================================
                    FakeAI Final Integration Test
================================================================================

Production-Quality System Validation
This test validates the complete system including:
  - Server health and availability
  - Request processing (streaming & non-streaming)
  - All metrics endpoints
  - Data consistency
  - Exception monitoring

--------------------------------------------------------------------------------
Server Health Check
--------------------------------------------------------------------------------

ℹ Waiting for server at 127.0.0.1:8765 (timeout: 45s)
✓ Server ready after 0.15s (3 attempts)
  Status: healthy
  Ready: True

--------------------------------------------------------------------------------
Executing Test Load (20 Requests)
--------------------------------------------------------------------------------

ℹ Sending 20 requests...
ℹ Mix: 10 non-streaming + 10 streaming
ℹ Models: gpt-4, gpt-4-turbo, gpt-3.5-turbo, claude-3-opus, claude-3-sonnet

  [ 1/20] NORMAL | gpt-4                ... OK (0.123s)
  [ 2/20] NORMAL | gpt-4-turbo          ... OK (0.098s)
  [ 3/20] NORMAL | gpt-3.5-turbo        ... OK (0.087s)
  ...
  [20/20] STREAM | claude-3-sonnet      ... OK (0.234s)

ℹ Completed 20 requests in 3.42s
ℹ Success: 20/20 (100.0%)

ℹ Waiting 1s for event processing...

--------------------------------------------------------------------------------
Validating Metrics Endpoints
--------------------------------------------------------------------------------

  /metrics                       ... OK (0.003s)
  /metrics/events                ... OK (0.002s)
  /metrics/errors                ... OK (0.002s)
  /metrics/streaming             ... OK (0.003s)
  /metrics/slo                   ... OK (0.002s)

ℹ Endpoints: 5/5 responding

--------------------------------------------------------------------------------
Validating Metrics Data
--------------------------------------------------------------------------------

/metrics
  ✓ total_requests: 20
  ✓ requests_per_second: 5.85
  ✓ avg_response_time: 0.171

/metrics/events
  ✓ events_published: 40
  ✓ events_processed: 40
  ✓ queue_depth: 0

/metrics/errors
  ✓ total_requests: 20
  ✓ total_errors: 0
  ✓ error_rate: 0.0

/metrics/streaming
  ✓ total_streams: 10
  ✓ successful_streams: 10
  ✓ ttft_percentiles: 3 metrics

/metrics/slo
  ✓ success_rate: 1.0
  ✓ error_budget_remaining: 1.0
  ✓ slo_target: 0.99

--------------------------------------------------------------------------------
Validating Data Consistency
--------------------------------------------------------------------------------

Request Count Consistency:
  total_requests (/metrics): 20
  total_requests (/metrics/errors): 20
  ✓ Request counts are consistent

Streaming Stats Validation:
  total_streams: 10
  successful_streams: 10
  failed_streams: 0
  ✓ Streaming counts are consistent

SLO Consistency:
  error_rate: 0.00%
  success_rate: 100.00%
  ✓ SLO rates are consistent with error metrics

Event Bus Activity:
  events_published: 40
  events_processed: 40
  ✓ Events are being published

--------------------------------------------------------------------------------
Checking for Exceptions
--------------------------------------------------------------------------------

ℹ Log checking not implemented in this version
ℹ In production, this would:
  - Parse server log files
  - Connect to logging aggregation service
  - Check for ERROR/CRITICAL level logs
  - Validate no uncaught exceptions occurred

================================================================================
                              FINAL TEST REPORT
================================================================================

Test Summary
  Total Tests: 45
  Passed: 45
  Failed: 0
  Pass Rate: 100.0%
  Duration: 5.67s

Request Summary
  Total Requests: 20
  Successful: 20
  Failed: 0
  Avg Duration: 0.171s
  Streaming: 10
  Non-Streaming: 10

Metrics Endpoints
  /metrics                       OK
  /metrics/events                OK
  /metrics/errors                OK
  /metrics/streaming             OK
  /metrics/slo                   OK

✓ ALL TESTS PASSED (45/45)

System is operating correctly!
```

## Exit Codes

- **0** - All tests passed (100% success rate)
- **1** - Some tests failed or server not available

## Pass/Fail Criteria

### Pass (Exit Code 0)
- Server responds to health check
- All 20 requests complete successfully
- All 5 metrics endpoints respond
- All data validation checks pass
- Data consistency checks pass

### Partial Pass (Exit Code 1)
- 90-99% of tests pass
- Minor inconsistencies detected
- Some requests failed but system mostly operational

### Fail (Exit Code 1)
- Server not available
- <90% of tests pass
- Critical metrics endpoints not responding
- Major data inconsistencies

## Integration with CI/CD

### GitHub Actions
```yaml
- name: Run Integration Tests
  run: |
    python -m fakeai --port 8765 &
    SERVER_PID=$!
    sleep 5
    python tests/FINAL_INTEGRATION_TEST.py
    TEST_RESULT=$?
    kill $SERVER_PID
    exit $TEST_RESULT
```

### GitLab CI
```yaml
integration_test:
  script:
    - python -m fakeai --port 8765 &
    - sleep 5
    - python tests/FINAL_INTEGRATION_TEST.py
  after_script:
    - killall python
```

### Jenkins
```groovy
stage('Integration Test') {
    steps {
        sh '''
            python -m fakeai --port 8765 &
            SERVER_PID=$!
            sleep 5
            python tests/FINAL_INTEGRATION_TEST.py
            TEST_RESULT=$?
            kill $SERVER_PID
            exit $TEST_RESULT
        '''
    }
}
```

## Configuration

### Environment Variables
```bash
# Override defaults
export FAKEAI_HOST="127.0.0.1"
export FAKEAI_PORT="8765"
export SERVER_TIMEOUT="60"
export REQUEST_TIMEOUT="20"
```

### Modifying Test Configuration
Edit constants in `FINAL_INTEGRATION_TEST.py`:
```python
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
SERVER_TIMEOUT = 45  # seconds
REQUEST_TIMEOUT = 15  # seconds

TEST_MODELS = [
    "gpt-4",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
    "claude-3-opus",
    "claude-3-sonnet",
]
```

## Extending the Test

### Adding New Endpoints
```python
METRICS_ENDPOINTS = [
    "/metrics",
    "/metrics/events",
    "/metrics/errors",
    "/metrics/streaming",
    "/metrics/slo",
    "/metrics/custom",  # Add here
]
```

### Adding Custom Validations
```python
def validate_custom_endpoint(data: Dict[str, Any]) -> List[TestResult]:
    """Add custom validation logic."""
    results = []

    # Your validation logic
    if data.get("custom_metric") > 0:
        results.append(TestResult(
            name="Custom Check",
            passed=True,
            message="Custom metric valid"
        ))

    return results
```

### Adding Log Monitoring
Replace placeholder in `check_for_exceptions()`:
```python
def check_for_exceptions(report: TestReport) -> None:
    """Check server logs for exceptions."""
    log_file = "/var/log/fakeai/server.log"

    with open(log_file, 'r') as f:
        for line in f:
            if "ERROR" in line or "EXCEPTION" in line:
                report.exceptions_found.append(line.strip())

    if report.exceptions_found:
        report.add_result(TestResult(
            name="Exception Monitoring",
            passed=False,
            message=f"Found {len(report.exceptions_found)} exceptions",
            details={"exceptions": report.exceptions_found[:5]}
        ))
```

## Troubleshooting

### Server Not Responding
```bash
# Check if server is running
curl http://localhost:8765/health

# Check port availability
netstat -an | grep 8765

# Start server manually
python -m fakeai --port 8765
```

### Metrics Endpoints Not Found
```bash
# Verify endpoints exist
curl http://localhost:8765/metrics
curl http://localhost:8765/metrics/events
curl http://localhost:8765/metrics/errors
curl http://localhost:8765/metrics/streaming
curl http://localhost:8765/metrics/slo
```

### Request Failures
- Check server logs for errors
- Verify model names are valid
- Increase `REQUEST_TIMEOUT` if needed
- Check network connectivity

### Data Consistency Failures
- Allow time for event processing (increase sleep time)
- Check event bus configuration
- Verify metrics trackers are properly initialized

## Test Philosophy

This test follows production-quality testing principles:

1. **Comprehensive** - Tests all major system components
2. **Realistic** - Uses real requests and actual API calls
3. **Deterministic** - Same inputs produce same results
4. **Fast** - Completes in ~5-10 seconds
5. **Informative** - Clear output with actionable errors
6. **Automated** - Zero manual intervention required
7. **Reliable** - Minimal false positives/negatives

## Related Tests

- `verify_event_flow.py` - Event system validation
- `verify_error_metrics_live.py` - Error metrics validation
- `verify_streaming_metrics_live.py` - Streaming metrics validation
- `test_metrics_integration_complete.py` - Unit-level metrics tests

## Support

For issues or questions:
- Check server logs: `tail -f /var/log/fakeai/server.log`
- Review test output for specific failures
- Verify server configuration
- Ensure all dependencies are installed

## License

Apache-2.0
