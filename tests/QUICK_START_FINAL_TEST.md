# Quick Start - Final Integration Test

## One-Line Commands

### Run Test (Server Already Running)
```bash
python tests/FINAL_INTEGRATION_TEST.py
```

### Start Server & Run Test
```bash
# Terminal 1: Start server
python -m fakeai --port 8765

# Terminal 2: Run test
python tests/FINAL_INTEGRATION_TEST.py
```

### All-in-One (Background Server)
```bash
# Start server in background, run test, cleanup
python -m fakeai --port 8765 > /tmp/fakeai.log 2>&1 &
SERVER_PID=$!
sleep 3
python tests/FINAL_INTEGRATION_TEST.py
TEST_RESULT=$?
kill $SERVER_PID
exit $TEST_RESULT
```

## What It Does (Summary)

1. **Waits** for server on port 8765 (45s timeout)
2. **Sends** 20 requests:
   - 10 non-streaming (gpt-4, claude-3, etc.)
   - 10 streaming
3. **Checks** all 5 metrics endpoints:
   - `/metrics` (dashboard)
   - `/metrics/events` (event bus)
   - `/metrics/errors` (errors)
   - `/metrics/streaming` (streaming)
   - `/metrics/slo` (SLO status)
4. **Validates** data in each endpoint
5. **Verifies** consistency across endpoints
6. **Prints** comprehensive PASS/FAIL report

## Expected Output (Success)

```
================================================================================
                    FakeAI Final Integration Test
================================================================================

✓ Server ready after 0.15s
✓ 20/20 requests successful
✓ 5/5 metrics endpoints responding
✓ All data validation passed
✓ Data consistency verified

✓ ALL TESTS PASSED (45/45)
System is operating correctly!
```

## Exit Codes

- **0** = All tests passed
- **1** = Some tests failed

## Requirements

```bash
# Install dependencies
pip install requests

# Or from requirements
pip install -r requirements.txt
```

## Troubleshooting

### "Server did not respond"
```bash
# Start the server first
python -m fakeai --port 8765
```

### "Connection refused"
```bash
# Check if port is already in use
netstat -an | grep 8765

# Use a different port
# (Edit DEFAULT_PORT in script)
```

### "Metrics endpoint failed"
```bash
# Verify endpoints manually
curl http://localhost:8765/metrics
curl http://localhost:8765/metrics/events
curl http://localhost:8765/metrics/errors
curl http://localhost:8765/metrics/streaming
curl http://localhost:8765/metrics/slo
```

## CI/CD Integration

### GitHub Actions
```yaml
name: Integration Test
on: [push, pull_request]

jobs:
  test:
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
      - name: Run integration test
        run: python tests/FINAL_INTEGRATION_TEST.py
```

### GitLab CI
```yaml
integration_test:
  stage: test
  script:
    - pip install -r requirements.txt
    - python -m fakeai --port 8765 &
    - sleep 5
    - python tests/FINAL_INTEGRATION_TEST.py
```

## Key Features

### Comprehensive Coverage
- Tests all major system components in one run
- Validates both functionality and data consistency
- Checks multiple model types and request modes

### Production-Quality
- Clear pass/fail criteria
- Detailed error reporting
- Suitable for CI/CD pipelines
- Fast execution (~5-10 seconds)

### Beautiful Output
- Color-coded results
- Section headers
- Progress indicators
- Summary statistics

### Robust Validation
- Server health check
- Request success tracking
- Endpoint availability
- Data structure validation
- Cross-endpoint consistency
- Event flow verification

## What Gets Tested

| Category | Tests | What's Validated |
|----------|-------|-----------------|
| Server | 1 | Health endpoint, ready state |
| Requests | 20 | 10 normal + 10 streaming across 5 models |
| Endpoints | 5 | All metrics endpoints respond |
| Data | 15+ | Structure and content of each endpoint |
| Consistency | 4 | Cross-endpoint data matches |
| Total | **45+** | Comprehensive system validation |

## Sample Results

### Perfect Run
```
Test Summary
  Total Tests: 45
  Passed: 45
  Failed: 0
  Pass Rate: 100.0%
  Duration: 5.67s

✓ ALL TESTS PASSED
```

### With Issues
```
Test Summary
  Total Tests: 45
  Passed: 42
  Failed: 3
  Pass Rate: 93.3%
  Duration: 6.12s

Failed Tests:
  ✗ /metrics/streaming - total_streams: missing or invalid
  ✗ Consistency - Streaming Counts: Invalid: 8 ≠ 7 + 0
  ✗ Consistency - Event Bus Activity: No events published

⚠ MOSTLY PASSED (42/45)
```

## See Also

- **Full Documentation**: `README_FINAL_INTEGRATION_TEST.md`
- **Event Flow Test**: `verify_event_flow.py`
- **Error Metrics Test**: `verify_error_metrics_live.py`
- **Streaming Test**: `verify_streaming_metrics_live.py`

## Support

```bash
# View help
python tests/FINAL_INTEGRATION_TEST.py --help

# Check server status
curl http://localhost:8765/health

# View metrics manually
curl http://localhost:8765/metrics | jq
```
