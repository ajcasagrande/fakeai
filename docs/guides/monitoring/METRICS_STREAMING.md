# Real-Time Metrics Streaming

FakeAI provides a WebSocket-based real-time metrics streaming API for live dashboards and monitoring tools.

## Overview

The metrics streaming API allows clients to subscribe to metrics updates via WebSocket, with configurable filters and update intervals. Metrics are broadcast automatically to all connected clients based on their subscription preferences.

## Endpoint

```
WebSocket: ws://localhost:8000/metrics/stream
```

## Features

- **Real-time Updates**: Metrics are pushed to clients at configurable intervals (default: 1 second)
- **Subscription Filters**: Filter by endpoint, model, and metric type
- **Historical Data**: Clients receive current metrics immediately on connection
- **Delta Calculations**: Track changes between updates
- **Multiple Clients**: Supports concurrent connections with independent subscriptions
- **Graceful Reconnection**: Handles disconnections and reconnections automatically

## Metrics Types

### Throughput
- `requests_per_sec` - Request rate by endpoint
- `responses_per_sec` - Response rate by endpoint
- `tokens_per_sec` - Token generation rate by endpoint
- `total_requests_per_sec` - Overall request rate
- `total_tokens_per_sec` - Overall token rate

### Latency
- `avg` - Average latency (ms)
- `min` - Minimum latency (ms)
- `max` - Maximum latency (ms)
- `p50` - 50th percentile latency (ms)
- `p90` - 90th percentile latency (ms)
- `p99` - 99th percentile latency (ms)

### Cache Performance
- `hit_rate` - Percentage of requests with cache hits
- `token_reuse_rate` - Percentage of tokens reused from cache
- `avg_prefix_length` - Average prefix match length
- `total_lookups` - Total cache lookups
- `cache_hits` - Total cache hits
- `by_endpoint` - Cache stats by endpoint

### Streaming
- `active_streams` - Number of currently active streams
- `completed_streams` - Total completed streams
- `failed_streams` - Total failed streams
- `ttft` - Time to first token statistics
- `tokens_per_second` - Streaming token rate statistics

### Queue/Active Requests
- `queue_depth` - Number of queued requests
- `active_streams` - Number of active streams

### Errors
- `errors_per_sec` - Error rate by endpoint
- `total_errors_per_sec` - Overall error rate

## WebSocket Protocol

### Client Messages

#### Subscribe
```json
{
  "type": "subscribe",
  "filters": {
    "endpoint": "/v1/chat/completions",
    "model": "gpt-4",
    "metric_type": "latency",
    "interval": 1.0
  }
}
```

**Filters:**
- `endpoint` (string, optional): Filter by specific endpoint (e.g., `/v1/chat/completions`)
- `model` (string, optional): Filter by model name (e.g., `gpt-4`)
- `metric_type` (string, optional): Filter by metric type (`throughput`, `latency`, `cache`, `streaming`, `queue`, `error`, or `all`)
- `interval` (float, optional): Update interval in seconds (default: 1.0)

Multiple subscriptions can be sent to add filters. Omit filters to receive all metrics.

#### Unsubscribe
```json
{
  "type": "unsubscribe"
}
```

Resets all filters to defaults.

#### Ping
```json
{
  "type": "ping"
}
```

Keep-alive message. Server responds with `pong`.

### Server Messages

#### Historical Data
Sent immediately after connection:
```json
{
  "type": "historical_data",
  "timestamp": 1234567890.123,
  "data": {
    "throughput": { ... },
    "latency": { ... },
    "cache": { ... },
    "streaming": { ... },
    "error": { ... }
  }
}
```

#### Subscribed
Confirmation of subscription:
```json
{
  "type": "subscribed",
  "filters": {
    "endpoints": ["/v1/chat/completions"],
    "models": ["gpt-4"],
    "metric_types": ["latency"],
    "interval": 1.0
  }
}
```

#### Metrics Update
Periodic metrics broadcast:
```json
{
  "type": "metrics_update",
  "timestamp": 1234567890.123,
  "data": {
    "throughput": {
      "requests_per_sec": {
        "/v1/chat/completions": 10.5
      },
      "total_requests_per_sec": 15.8,
      "tokens_per_sec": {
        "/v1/chat/completions": 567.8
      },
      "total_tokens_per_sec": 750.2
    },
    "latency": {
      "/v1/chat/completions": {
        "avg": 234.5,
        "min": 100.2,
        "max": 567.8,
        "p50": 220.0,
        "p90": 450.0,
        "p99": 520.0
      }
    },
    "cache": {
      "hit_rate": 67.5,
      "token_reuse_rate": 45.2,
      "avg_prefix_length": 123.4
    },
    "streaming": {
      "active_streams": 3,
      "ttft": {
        "avg": 123.0,
        "p50": 120.0,
        "p99": 240.0
      }
    }
  },
  "deltas": {
    "throughput": {
      "total_requests_per_sec": 2.5,
      "total_tokens_per_sec": 50.0
    },
    "streaming": {
      "active_streams_delta": 1
    }
  }
}
```

#### Pong
Response to ping:
```json
{
  "type": "pong",
  "timestamp": 1234567890.123
}
```

#### Error
Error message:
```json
{
  "type": "error",
  "timestamp": 1234567890.123,
  "message": "Invalid JSON: ..."
}
```

## Usage Examples

### Python Client

```python
import asyncio
import json
import websockets

async def stream_metrics():
    uri = "ws://localhost:8000/metrics/stream"

    async with websockets.connect(uri) as websocket:
        # Receive historical data
        message = await websocket.recv()
        data = json.loads(message)
        print(f"Historical data: {data}")

        # Subscribe to specific metrics
        await websocket.send(json.dumps({
            "type": "subscribe",
            "filters": {
                "endpoint": "/v1/chat/completions",
                "interval": 2.0
            }
        }))

        # Receive metrics updates
        async for message in websocket:
            data = json.loads(message)
            if data["type"] == "metrics_update":
                print(f"Throughput: {data['data']['throughput']}")
                print(f"Latency: {data['data']['latency']}")

asyncio.run(stream_metrics())
```

See `examples/metrics_streaming_client.py` for a complete example.

### JavaScript Client

```javascript
const ws = new WebSocket('ws://localhost:8000/metrics/stream');

ws.onopen = () => {
    console.log('Connected');

    // Subscribe to metrics
    ws.send(JSON.stringify({
        type: 'subscribe',
        filters: {
            endpoint: '/v1/chat/completions',
            interval: 1.0
        }
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'metrics_update') {
        console.log('Throughput:', data.data.throughput);
        console.log('Latency:', data.data.latency);
    }
};
```

See `examples/metrics_streaming_dashboard.html` for a complete HTML dashboard.

### cURL Example

Test the WebSocket endpoint using `websocat`:

```bash
# Install websocat
cargo install websocat

# Connect and subscribe
echo '{"type":"subscribe","filters":{"endpoint":"/v1/chat/completions","interval":2.0}}' | \
    websocat ws://localhost:8000/metrics/stream
```

## Architecture

### Components

1. **MetricsStreamer**: Main streaming service that manages WebSocket connections
2. **ClientConnection**: Represents individual client connections with subscription filters
3. **MetricSnapshot**: Immutable snapshot of metrics at a point in time
4. **SubscriptionFilter**: Client filter configuration (endpoints, models, metric types, interval)

### Data Flow

```
MetricsTracker → MetricsStreamer → Snapshot Builder → Filter → Broadcast → Clients
                        ↑                                          ↓
                         Background Loop (0.5s) 
```

1. **Collection**: MetricsTracker collects metrics from FakeAI service
2. **Snapshotting**: MetricsStreamer builds snapshots from current metrics
3. **Filtering**: Each client's subscription filters are applied
4. **Broadcasting**: Filtered data is sent to clients at their requested interval
5. **Delta Calculation**: Changes since previous snapshot are included

### Thread Safety

- All WebSocket operations are async
- Client list is managed by asyncio event loop (thread-safe)
- MetricsTracker uses threading.Lock for numpy operations

### Performance

- Broadcast rate: 2Hz (every 0.5 seconds)
- Client update intervals: Configurable per-client (0.5s - 60s recommended)
- Overhead: ~10-20ms per broadcast cycle
- Memory: ~1KB per client connection

## Best Practices

### For Clients

1. **Set appropriate intervals**: Use 1-5 second intervals for dashboards, 0.5s for debugging
2. **Filter aggressively**: Subscribe only to metrics you need
3. **Handle disconnections**: Implement reconnection logic with exponential backoff
4. **Process updates asynchronously**: Don't block on message handling
5. **Send periodic pings**: Keep connection alive (every 30-60 seconds)

### For Production

1. **Monitor connection count**: Track active WebSocket connections
2. **Set connection limits**: Limit concurrent connections if needed
3. **Use HTTPS/WSS**: Encrypt WebSocket traffic in production
4. **Rate limit subscriptions**: Prevent abuse with aggressive update intervals
5. **Log errors**: Monitor WebSocket errors and disconnections

## Configuration

No specific configuration is required. The metrics streamer starts automatically with the FakeAI server.

To disable metrics streaming:
```python
# In app.py, comment out the streamer initialization
# metrics_streamer = MetricsStreamer(metrics_tracker)
```

## Testing

Run the metrics streaming tests:

```bash
pytest tests/test_metrics_streaming.py -v
```

Test categories:
- WebSocket connection handling
- Subscription management
- Filtering logic
- Broadcasting behavior
- Delta calculations
- Error handling

## Troubleshooting

### Connection Refused
- Ensure FakeAI server is running
- Check firewall settings
- Verify WebSocket port (default: 8000)

### No Metrics Updates
- Check subscription filters (may be too restrictive)
- Verify interval setting (must be > 0)
- Ensure metrics are being generated (send test requests)

### High CPU Usage
- Reduce number of connected clients
- Increase update intervals
- Filter metrics more aggressively

### Disconnections
- Check network stability
- Implement reconnection logic
- Send periodic ping messages

## API Reference

### MetricsStreamer

```python
class MetricsStreamer:
    def __init__(self, metrics_tracker: MetricsTracker):
        """Initialize metrics streamer with tracker."""

    async def start(self):
        """Start background broadcast task."""

    async def stop(self):
        """Stop background broadcast task."""

    async def handle_websocket(self, websocket: WebSocket):
        """Handle WebSocket connection."""

    def get_active_connections(self) -> int:
        """Get number of active connections."""

    def get_client_info(self) -> List[dict]:
        """Get information about connected clients."""
```

### SubscriptionFilter

```python
@dataclass
class SubscriptionFilter:
    endpoints: Set[str] = field(default_factory=set)
    models: Set[str] = field(default_factory=set)
    metric_types: Set[MetricType] = field(default_factory=lambda: {MetricType.ALL})
    interval: float = 1.0
```

### MetricType

```python
class MetricType(Enum):
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    CACHE = "cache"
    QUEUE = "queue"
    STREAMING = "streaming"
    ERROR = "error"
    ALL = "all"
```

## Related Documentation

- [Metrics API](METRICS.md) - REST API for metrics
- [KV Cache Metrics](KV_CACHE.md) - Cache performance tracking
- [WebSocket API](WEBSOCKETS.md) - General WebSocket documentation

## Changelog

### Version 0.0.5
- Initial implementation of metrics streaming
- WebSocket endpoint: `/metrics/stream`
- Subscription-based filtering
- Delta calculations
- Historical data on connect
- Graceful reconnection support
