# Metrics Streaming Quick Start

## 5-Minute Guide to Real-Time Metrics

### 1. Start the Server
```bash
python -m fakeai server
```

### 2. Connect via WebSocket

**Python:**
```python
import asyncio
import websockets
import json

async def main():
    async with websockets.connect("ws://localhost:8000/metrics/stream") as ws:
        async for message in ws:
            print(json.loads(message))

asyncio.run(main())
```

**JavaScript:**
```javascript
const ws = new WebSocket('ws://localhost:8000/metrics/stream');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

### 3. Subscribe to Specific Metrics

```json
{
  "type": "subscribe",
  "filters": {
    "endpoint": "/v1/chat/completions",
    "interval": 2.0
  }
}
```

### 4. Message Types

**From Server:**
- `historical_data` - Initial metrics on connect
- `subscribed` - Subscription confirmation
- `metrics_update` - Real-time metrics (periodic)
- `pong` - Response to ping

**To Server:**
- `subscribe` - Update subscription filters
- `unsubscribe` - Reset filters
- `ping` - Keep-alive

### 5. Metric Categories

- **throughput**: Requests/sec, tokens/sec
- **latency**: Avg, p50, p99 (milliseconds)
- **cache**: Hit rate, token reuse
- **streaming**: Active streams, TTFT
- **error**: Error rates

### 6. Try the Examples

**Python Client:**
```bash
python examples/metrics_streaming_client.py
```

**HTML Dashboard:**
```bash
# Open in browser
open examples/metrics_streaming_dashboard.html
```

**Integration Test:**
```bash
python examples/test_websocket_metrics.py
```

## Common Use Cases

### Monitor Latency
```json
{
  "type": "subscribe",
  "filters": {
    "metric_type": "latency",
    "interval": 1.0
  }
}
```

### Track Cache Performance
```json
{
  "type": "subscribe",
  "filters": {
    "metric_type": "cache",
    "interval": 5.0
  }
}
```

### Watch Specific Endpoint
```json
{
  "type": "subscribe",
  "filters": {
    "endpoint": "/v1/chat/completions",
    "metric_type": "all",
    "interval": 1.0
  }
}
```

## Tips

- Keep intervals ≥ 0.5 seconds
- Filter by endpoint to reduce data
- Send ping every 30-60 seconds
- Handle reconnections gracefully
- Process updates asynchronously

## Full Documentation

See `docs/METRICS_STREAMING.md` for complete API reference, examples, and troubleshooting.
