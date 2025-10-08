# 🎨 Waterfall Chart Visualization System

## Overview

The FakeAI Waterfall System provides beautiful, real-time visualization of request timing patterns, showing:
- Request start → end timeline
- Time To First Token (TTFT) markers
- Token-by-token generation progress
- Concurrent request overlap

## Architecture

### Decoupled Modules

```
fakeai/waterfall/
├── __init__.py          # Public API exports
├── collector.py         # Request timing data collection
├── generator.py         # SVG chart generation
├── api.py              # REST API endpoints
└── subscriber.py        # Event bus integration
```

### Integration Points

1. **Event Bus**: Automatic data collection via event subscribers
2. **FastAPI**: REST endpoints for data/visualization access
3. **Metrics System**: Complementary to existing metrics
4. **Zero Dependencies**: Uses only stdlib + FastAPI

## API Endpoints

### GET /waterfall
Interactive HTML waterfall chart

**Parameters:**
- `limit` (1-1000): Max requests to display [default: 100]
- `endpoint` (string): Filter by endpoint
- `model` (string): Filter by model  
- `width` (800-3000): Chart width [default: 1200]
- `height` (400-2000): Chart height [default: 600]

**Example:**
```bash
curl http://localhost:8000/waterfall?limit=50&model=gpt-4
```

### GET /waterfall/data
JSON timing data

**Parameters:**
- `limit` (1-1000): Max requests to return
- `endpoint` (string): Filter by endpoint
- `model` (string): Filter by model

**Example:**
```bash
curl http://localhost:8000/waterfall/data?limit=20
```

**Response:**
```json
{
  "requests": [
    {
      "request_id": "req-abc123",
      "endpoint": "/v1/chat/completions",
      "model": "gpt-4",
      "start_time": 1234567890.123,
      "end_time": 1234567891.456,
      "duration_ms": 1333.0,
      "ttft_ms": 45.2,
      "is_streaming": true,
      "input_tokens": 100,
      "output_tokens": 200,
      "tokens": [...]
    }
  ],
  "stats": {
    "total_completed": 42,
    "active_requests": 3,
    "max_capacity": 1000,
    "utilization_percent": 4.2
  }
}
```

## Usage

### Quick Start

```bash
# Start FakeAI server
fakeai server

# Run demo to generate sample requests
python examples/waterfall_demo.py

# View waterfall chart
open http://localhost:8000/waterfall
```

### Programmatic Access

```python
from fakeai.waterfall import get_timing_collector

# Get collector
collector = get_timing_collector()

# Get recent requests
requests = collector.get_recent_requests(limit=50)

# Get active requests
active = collector.get_active_requests()

# Get specific request
request = collector.get_request("req-abc123")

# Get stats
stats = collector.get_stats()
```

## Features

### Real-Time Collection
- Automatic capture via event bus
- Zero configuration required
- Thread-safe operations
- Memory-efficient (configurable limit)

### Beautiful Visualizations
- SVG-based charts
- Responsive design
- Color-coded status
- Interactive tooltips
- Mobile-friendly

### Flexible Filtering
- By endpoint
- By model
- By time window
- Customizable chart size

## Performance

- **Memory:** O(n) with n = max_requests (default: 1000)
- **Collection Overhead:** < 1ms per request
- **Chart Generation:** < 100ms for 100 requests
- **Thread-Safe:** All operations protected

## Integration with Event Bus

The waterfall subscriber automatically listens to:
- `RequestStartedEvent` → Start timing
- `StreamingTokenGeneratedEvent` → Record TTFT and tokens
- `RequestCompletedEvent` → Complete timing

No manual instrumentation required!

## Use Cases

1. **Performance Analysis**: Identify slow requests and TTFT spikes
2. **Concurrency Visualization**: See request overlap patterns
3. **Model Comparison**: Compare timing across different models
4. **Debugging**: Trace individual request timelines
5. **Load Testing**: Visualize system behavior under load

## Example Workflow

```bash
# 1. Start server
fakeai server

# 2. Generate some requests (streaming recommended)
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Count to 10"}],
    "stream": true
  }'

# 3. View waterfall
open http://localhost:8000/waterfall
```

## Architecture Benefits

- ✅ **Decoupled**: Each module has single responsibility
- ✅ **Event-Driven**: Auto-collection via pub/sub
- ✅ **Thread-Safe**: Concurrent request handling
- ✅ **Zero Config**: Works out of the box
- ✅ **Extensible**: Easy to add new chart types

---

*Part of the FakeAI monitoring and visualization suite*
