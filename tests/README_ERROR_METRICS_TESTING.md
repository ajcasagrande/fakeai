# Error Metrics Live Testing

## Overview

`verify_error_metrics_live.py` is a comprehensive testing script that validates the error metrics tracking system through live API interactions.

## What It Tests

The script performs a complete end-to-end validation of error metrics:

### 1. Request Generation (Step 1)
- Sends **20 successful requests** to `/v1/chat/completions`
- Verifies requests complete successfully
- Builds baseline metrics

### 2. Error Triggering (Step 2)
- **Invalid Model Error**: Attempts to use a non-existent model
- **Auth Failure Error**: Sends request with invalid API key
- Verifies errors are properly triggered (4xx status codes)

### 3. Error Metrics Validation (Step 3)
Checks `/metrics/errors` endpoint for:
- ✓ `total_requests` = 22 (20 success + 2 errors)
- ✓ `total_errors` = 2
- ✓ `success_rate` ≈ 91% (20/22)
- ✓ Error distribution by endpoint
- ✓ Error classification by type

### 4. SLO Monitoring (Step 4)
Checks `/metrics/slo` endpoint for:
- ✓ `current_success_rate` calculated correctly
- ✓ `error_budget` tracked (consumed vs remaining)
- ✓ `slo_violated` status (with 99.9% SLO target)
- ✓ `availability` percentage
- ✓ SLO targets configuration (0.999 = 99.9%)

### 5. Error Pattern Detection (Step 5)
Checks `/metrics/error-patterns` endpoint for:
- ✓ Pattern fingerprinting (SHA256-based)
- ✓ Occurrence counting
- ✓ Affected endpoints and models
- ✓ Example request IDs

### 6. Additional Validation (Step 6)
- ✓ `/metrics` endpoint responsive
- ✓ `/health` endpoint responsive
- ✓ `/metrics/prometheus` endpoint responsive

## Usage

### Prerequisites

1. **Start the FakeAI server:**
   ```bash
   python -m fakeai.app
   ```

2. **Ensure server is running:**
   ```bash
   curl http://localhost:8765/health
   ```

### Run the Test

**Basic usage (default localhost:8765):**
```bash
python tests/verify_error_metrics_live.py
```

**Custom server URL:**
```bash
python tests/verify_error_metrics_live.py --url http://localhost:8000
```

**Make it executable and run directly:**
```bash
chmod +x tests/verify_error_metrics_live.py
./tests/verify_error_metrics_live.py
```

## Expected Output

The script provides **color-coded output** for easy interpretation:

```
================================================================================
              ERROR METRICS LIVE TESTING
================================================================================

Step 1: Sending 20 Successful Requests
---------------------------------------
ℹ Sent 5/20 requests...
ℹ Sent 10/20 requests...
ℹ Sent 15/20 requests...
ℹ Sent 20/20 requests...
✓ Sent 20/20 successful requests (expected >= 18)

Step 2: Triggering 2 Error Conditions
--------------------------------------
ℹ Triggering invalid model error...
✓ Invalid model error triggered successfully
ℹ Triggering auth failure error...
✓ Auth failure error triggered successfully

Step 3: Validating /metrics/errors Endpoint
--------------------------------------------
✓ Error metrics has expected structure
✓ Total requests tracked: 22 (expected >= 20)
✓ Total errors tracked: 2 (expected >= 2)
✓ Success rate: 90.91% (expected ~91%)

Step 4: Validating /metrics/slo Endpoint
-----------------------------------------
✓ SLO status has expected structure
✓ Current availability: 90.91%
✓ Error budget tracking is active
✓ SLO violation tracking present
✓ SLO target: 99.9% (expected 99.9%)

Step 5: Validating /metrics/error-patterns Endpoint
----------------------------------------------------
ℹ Found 2 error patterns
✓ Error patterns have fingerprints/identifiers
✓ Error patterns track occurrence counts

Step 6: Additional Validation
------------------------------
✓ Endpoint /metrics is responsive
✓ Endpoint /health is responsive
✓ Endpoint /metrics/prometheus is responsive

================================================================================
                            TEST SUMMARY
================================================================================

Total Tests: 20
Passed: 20
Failed: 0
Success Rate: 100.0%

✓ ALL TESTS PASSED - Error metrics system is working correctly!
```

## Color Legend

- 🟢 **Green (✓)**: Test passed
- 🔴 **Red (✗)**: Test failed
- 🟡 **Yellow (⚠)**: Warning or partial success
- 🔵 **Blue**: Section headers
- 🟣 **Magenta (ℹ)**: Informational message

## Exit Codes

- **0**: All tests passed
- **1**: Some tests failed or error occurred
- **130**: User interrupted (Ctrl+C)

## Interpreting Results

### Success Rate Thresholds

- **≥90%**: ✓ All tests passed (Green)
- **70-89%**: ⚠ Some tests failed (Yellow)
- **<70%**: ✗ Many tests failed (Red)

### Common Issues

**Server not running:**
```
✗ Cannot connect to server: Connection refused
ℹ Please ensure the FakeAI server is running:
ℹ   python -m fakeai.app
```

**Metrics not updating:**
- Wait longer between requests (increase sleep time)
- Check server logs for errors
- Verify metrics endpoints are registered

**SLO always violated:**
- This is expected! With 20 success / 22 total = 90.91%
- 90.91% < 99.9% SLO target
- The test validates that violation detection works

## Integration with CI/CD

Add to your test suite:

```bash
# Start server in background
python -m fakeai.app &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Run the test
python tests/verify_error_metrics_live.py
TEST_EXIT_CODE=$?

# Cleanup
kill $SERVER_PID

# Exit with test result
exit $TEST_EXIT_CODE
```

## Advanced Usage

### Testing Different Error Scenarios

Modify the script to test additional error types:

```python
def trigger_rate_limit_error(self) -> bool:
    """Trigger a rate limit error."""
    for _ in range(100):
        response = requests.post(...)
    return response.status_code == 429

def trigger_timeout_error(self) -> bool:
    """Trigger a timeout error."""
    response = requests.post(..., timeout=0.001)
```

### Custom Validation Rules

Add custom checks in `run_test_sequence()`:

```python
# Check error rates by model
if "by_model" in error_metrics.get("distribution", {}):
    model_errors = error_metrics["distribution"]["by_model"]
    self.check(
        "gpt-3.5-turbo" in model_errors,
        "Errors tracked per model"
    )
```

### Load Testing

Increase request counts for load testing:

```python
# Send 1000 successful requests
for i in range(1000):
    self.send_successful_request()
```

## Related Files

- **Error Tracker Implementation**: `fakeai/error_metrics_tracker.py`
- **Error Metrics Handler**: `fakeai/handlers/metrics.py`
- **API Endpoints**: `fakeai/app.py` (lines 833-878)
- **Unit Tests**: `tests/test_error_metrics.py`

## Troubleshooting

### Tests Fail Intermittently

**Cause**: Race condition - metrics not updated yet

**Solution**: Increase sleep time in script:
```python
time.sleep(1.0)  # Increase from 0.5
```

### Error Patterns Not Detected

**Cause**: Minimum occurrence threshold not met

**Solution**: Lower threshold in API call:
```python
params={"min_count": 1, "recent_only": True}
```

### Success Rate Calculation Off

**Cause**: Different request counting methods

**Solution**: Check if server counts:
- Only successful requests
- Both successful and failed requests
- Adjust expectations accordingly

## Contributing

When adding new test cases:

1. Add descriptive section headers
2. Use color-coded output consistently
3. Record results with `self.check()`
4. Update this README with new test descriptions

## License

SPDX-License-Identifier: Apache-2.0
