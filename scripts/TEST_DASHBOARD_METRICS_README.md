# Dashboard Metrics Test Script

## Overview

`test_dashboard_metrics.py` is a comprehensive test script that validates all dashboard metrics endpoints are working correctly.

## What It Does

1. **Sends 100 streaming requests** to the backend server (configurable)
2. **Checks `/dynamo/metrics/json`** endpoint and validates:
   - `summary.total_requests` >= 100
   - `latency.ttft.avg` > 0
   - `throughput.requests_per_second` > 0
   - `latency_breakdown` array has items
   - `request_lifecycles` array has items
   - `per_model` has entries
   - `worker_stats.total_workers` == 4

3. **Checks `/kv-cache/metrics`** endpoint and validates:
   - `cache_hit_rate` >= 0
   - `total_cache_hits` >= 0
   - All 4 workers present in worker stats

4. **Prints a beautiful report** showing all metrics with color-coded results
5. **Returns exit code 0** if all critical tests pass, **1** if any fail

## Usage

### Basic Usage

```bash
# Run with defaults (localhost:8000, 100 requests)
python scripts/test_dashboard_metrics.py
```

### Custom Server URL

```bash
# Test against a different server
python scripts/test_dashboard_metrics.py --url http://remote-server:8000
```

### Custom Number of Requests

```bash
# Send 50 requests instead of 100
python scripts/test_dashboard_metrics.py --requests 50
```

### Combined Options

```bash
python scripts/test_dashboard_metrics.py --url http://localhost:9000 --requests 200
```

## Requirements

The script requires the following Python packages:

```bash
pip install aiohttp openai
```

These are already included in the FakeAI project dependencies.

## Exit Codes

- **0**: All critical tests passed
- **1**: Some tests failed or error occurred

## Output

The script provides colorful, detailed output showing:

- **Progress bar** during request sending
- **Validation results** for each metric field
- **Summary statistics** including:
  - Request success rate
  - Average duration, TTFT, tokens per request
  - Dynamo metrics validation pass rate
  - KV-Cache metrics validation pass rate
- **Final verdict** with specific failure reasons if applicable

## Example Output

```
================================================================================
                    COMPREHENSIVE DASHBOARD METRICS TEST                    
================================================================================

ℹ Target URL: http://localhost:8000
ℹ Test Requests: 100
ℹ Started at: 2025-10-06 20:30:00

================================================================================
                         SENDING STREAMING REQUESTS                         
================================================================================

ℹ Sending 100 streaming requests to http://localhost:8000
ℹ Started at: 2025-10-06 20:30:00

Progress: [██████████████████████████████████████████████████] 100.00% (100/100)

✓ All 100 requests completed successfully!

================================================================================
                         VALIDATING DYNAMO METRICS                          
================================================================================

✓ Successfully fetched /dynamo/metrics/json

ℹ Validating summary section...
✓   total_requests: 150 (>= 100)
✓   successful_requests: 150
✓   failed_requests: 0
✓   active_requests: 0

ℹ Validating latency section...
✓   ttft.avg: 45.23ms
✓   itl.avg: 12.34ms
✓   total.avg: 234.56ms
✓   prefill.avg: 38.90ms
✓   decode.avg: 195.66ms

ℹ Validating throughput section...
✓   requests_per_second: 12.45
✓   tokens_per_second: 456.78

ℹ Validating latency_breakdown array...
✓   latency_breakdown: 150 items

ℹ Validating request_lifecycles array...
✓   request_lifecycles: 150 items

ℹ Validating per_model section...
✓   per_model: 1 models
ℹ     openai/gpt-oss-120b: 150 requests

ℹ Validating worker_stats section...
✓   total_workers: 4
✓   workers array: 4 workers
ℹ     worker-0: 38 requests
ℹ     worker-1: 37 requests
ℹ     worker-2: 38 requests

================================================================================
                        VALIDATING KV-CACHE METRICS                         
================================================================================

✓ Successfully fetched /kv-cache/metrics

ℹ Validating cache_performance section...
✓   cache_hit_rate: 15.50%
✓   total_cache_hits: 23
✓   total_requests: 150
✓   cache_misses: 127
✓   tokens_saved: 1234

ℹ Validating smart_router section...
✓   workers: 4 workers found
✓   All 4 workers present
ℹ     worker-0: 38 requests
ℹ     worker-1: 37 requests
ℹ     worker-2: 38 requests
ℹ     worker-3: 37 requests
✓   total_routed: 150

================================================================================
                            FINAL TEST REPORT                            
================================================================================

Request Summary:
  Total Requests:     100
  Successful:         100
  Failed:             0
  Success Rate:       100.00%

Average Metrics:
  Duration:           2.345s
  TTFT:               45.23ms
  Tokens/Request:     45.6

Dynamo Metrics Validation:
  Passed:             18/18
  Pass Rate:          100.00%

KV-Cache Metrics Validation:
  Passed:             12/12
  Pass Rate:          100.00%

Overall Result:
✓ ALL CRITICAL TESTS PASSED!
```

## Integration with CI/CD

You can use this script in CI/CD pipelines:

```bash
#!/bin/bash
# Start server
fakeai-server &
SERVER_PID=$!

# Wait for server to be ready
sleep 5

# Run tests
python scripts/test_dashboard_metrics.py
TEST_RESULT=$?

# Cleanup
kill $SERVER_PID

# Exit with test result
exit $TEST_RESULT
```

## Troubleshooting

### "Connection refused" error

Make sure the FakeAI server is running:

```bash
fakeai-server
```

### Metrics not updating

The script waits 2 seconds after sending requests for metrics to update. If you still see issues:

1. Check that metrics collection is enabled in the server
2. Try increasing the wait time in the script
3. Verify the endpoints are accessible: `curl http://localhost:8000/dynamo/metrics/json`

### Some validations failing

- **worker_stats missing**: This is expected if worker pool is not enabled
- **latency_breakdown empty**: May happen if no recent requests
- **cache_hit_rate = 0**: Normal if no cache hits occurred

## Development

To modify the script:

1. Edit validation criteria in `check_dynamo_metrics()` and `check_kv_cache_metrics()`
2. Adjust critical metrics list in `print_final_report()`
3. Customize request prompts in `send_streaming_request()`

## License

Same as FakeAI project (Apache 2.0)
