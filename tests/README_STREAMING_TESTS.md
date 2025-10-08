# Comprehensive Streaming Tests

## Overview

`test_streaming_complete.py` is a comprehensive test suite for validating all aspects of streaming functionality in FakeAI.

## Features Tested

1. **Chat Completions Streaming** (`/v1/chat/completions`)
   - SSE event parsing
   - Token-by-token streaming
   - TTFT measurement
   - Token count accuracy
   - Finish reason detection
   - Usage reporting

2. **Completions Streaming** (`/v1/completions`)
   - Text completion streaming
   - Real-time token delivery
   - Performance metrics

3. **Multiple Concurrent Streams**
   - Sequential stream execution
   - Aggregate statistics
   - Success rate tracking

4. **Streaming Metrics Validation**
   - StreamingMetricsTracker data integrity
   - TTFT (Time to First Token) calculation
   - ITL (Inter-Token Latency) tracking
   - TPS (Tokens Per Second) measurement

5. **Error Detection**
   - NameError exception checking
   - Connection error handling
   - Timeout management

6. **Comprehensive Reporting**
   - Detailed statistics
   - Percentile calculations
   - Visual validation indicators

## Usage

### Prerequisites

1. Start the FakeAI server:
```bash
python -m fakeai.app
```

2. Ensure required packages are installed:
```bash
pip install requests
```

### Running the Tests

```bash
# Run from project root
python tests/test_streaming_complete.py
```

### Configuration

Edit the following constants at the top of the file to customize:

```python
BASE_URL = "http://localhost:8000"  # Server URL
API_KEY = "test-key"                # API key
```

## Test Execution Flow

```
1. Single Chat Completions Stream
   ↓
2. Single Completions Stream
   ↓
3. 10 Sequential Streams (alternating endpoints)
   ↓
4. Validate Streaming Tracker Metrics
   ↓
5. Validate General Metrics
   ↓
6. Generate Comprehensive Report
```

## Output

The test provides detailed, color-coded output:

- ✓ Success indicators
- ❌ Error indicators
- ⚠ Warning indicators

### Sample Output

```
================================================================================
COMPREHENSIVE STREAMING TEST REPORT
================================================================================

1. STREAMING REQUEST TESTS
   ────────────────────────────────────────────────────────────────────────────
   Total streams tested: 10
   Successful streams: 10
   Failed streams: 0
   Success rate: 100.0%

2. TIME TO FIRST TOKEN (TTFT)
   ────────────────────────────────────────────────────────────────────────────
   Measurements: 10
   Mean: 15.34ms
   Median: 14.82ms
   Min: 12.10ms
   Max: 19.87ms

3. TOKEN COUNTS
   ────────────────────────────────────────────────────────────────────────────
   Total streams: 10
   Mean tokens/stream: 42.3
   Total tokens: 423
   Min tokens: 38
   Max tokens: 50

...
```

## What Gets Validated

### ✓ Stream Completion
- All streams complete successfully
- No dropped connections
- Proper [DONE] markers

### ✓ Token Accuracy
- Token counts match expectations
- All tokens properly delivered
- No missing or duplicate tokens

### ✓ Performance Metrics
- TTFT is measured for all streams
- TTFT < Total Duration (sanity check)
- TPS calculations are accurate

### ✓ Tracker Integration
- StreamingMetricsTracker has data
- Metrics are properly aggregated
- Percentiles are calculated

### ✓ No Exceptions
- Server responds to health checks
- No NameError exceptions
- No internal server errors

## Advanced Usage

### Custom Test Scenarios

```python
# Test specific model
result = test_chat_completions_streaming(
    model="openai/gpt-oss-120b",
    max_tokens=100
)

# Test multiple streams
results = test_multiple_streams(count=50)

# Check specific metrics
streaming_metrics = check_streaming_tracker()
```

### Integration with CI/CD

```bash
# Run as part of CI pipeline
python tests/test_streaming_complete.py || exit 1
```

## Troubleshooting

### Connection Refused
- Ensure server is running on the correct port
- Check `BASE_URL` matches server configuration

### Timeout Errors
- Increase timeout values in the code
- Check server performance

### Missing Metrics
- Ensure StreamingMetricsTracker is initialized
- Check `/metrics/streaming` endpoint is enabled

## Metrics Endpoints

The test validates the following endpoints:

1. `/v1/chat/completions` - Chat streaming
2. `/v1/completions` - Text completion streaming
3. `/metrics/streaming` - Streaming-specific metrics
4. `/metrics` - General system metrics
5. `/health` - Server health check

## Implementation Details

### SSE Parsing
```python
def parse_sse_event(line: str) -> Dict[str, Any]:
    """Parse Server-Sent Events format."""
    if line.startswith("data: "):
        data_str = line[6:].strip()
        if data_str == "[DONE]":
            return {"type": "done"}
        return {"type": "data", "data": json.loads(data_str)}
```

### TTFT Measurement
```python
start_time = time.time()
# ... wait for first token ...
first_token_time = time.time()
ttft_ms = (first_token_time - start_time) * 1000
```

### Token Counting
```python
for chunk in stream:
    if "content" in chunk["delta"]:
        token_count += 1
        tokens.append(chunk["delta"]["content"])
```

## Future Enhancements

- [ ] Parallel stream testing
- [ ] WebSocket streaming tests
- [ ] Error injection scenarios
- [ ] Load testing integration
- [ ] Automated regression detection

## Related Files

- `/fakeai/streaming_metrics_tracker.py` - Metrics tracking
- `/fakeai/metrics.py` - General metrics
- `/tests/integration/test_streaming_metrics.py` - Unit tests
- `/fakeai/app.py` - Server implementation

## License

Apache-2.0
