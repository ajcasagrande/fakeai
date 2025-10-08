# WebSocket Integration Guide

Quick guide to integrate the WebSocket real-time updates system into your dashboard.

## Step 1: Setup Provider in App Root

Edit your main App component to wrap everything with `WebSocketProvider`:

```tsx
// src/App.tsx or src/main.tsx
import { WebSocketProvider } from '@/services';

function App() {
  return (
    <WebSocketProvider
      config={{
        url: process.env.REACT_APP_WS_URL || 'ws://localhost:8000/metrics/stream',
        debug: process.env.NODE_ENV === 'development',
        reconnectInterval: 1000,
        maxReconnectInterval: 30000,
        reconnectDecay: 1.5,
        heartbeatInterval: 30000,
        maxReconnectAttempts: Infinity,
      }}
      onConnect={() => console.log('WebSocket connected')}
      onDisconnect={(reason) => console.warn('WebSocket disconnected:', reason)}
      onError={(error) => console.error('WebSocket error:', error)}
      onReconnecting={(attempt) => console.log(`Reconnecting... attempt ${attempt}`)}
    >
      <Router>
        <Layout>
          <Routes />
        </Layout>
      </Router>
    </WebSocketProvider>
  );
}
```

## Step 2: Add Connection Status to Layout

Add the connection status indicator to your main layout header:

```tsx
// src/components/Layout.tsx
import { ConnectionStatus } from '@/services';

function Layout({ children }) {
  return (
    <div className="min-h-screen bg-gray-900">
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <ConnectionStatus showDetails showLatency />
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
```

## Step 3: Use Real-time Metrics in Pages

Update your dashboard pages to use real-time data:

```tsx
// src/pages/Dashboard.tsx
import { useRealtimeMetrics, ConnectionBadge } from '@/services';

function Dashboard() {
  const {
    metrics,
    models,
    recentRequests,
    isConnected,
    connectionState,
  } = useRealtimeMetrics();

  if (!isConnected) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <ConnectionBadge className="mx-auto mb-2" />
          <p className="text-gray-400">Connecting to real-time updates...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Metrics Overview */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          label="Total Requests"
          value={metrics?.total_requests.toLocaleString() || '0'}
        />
        <MetricCard
          label="Avg Latency"
          value={`${Math.round(metrics?.avg_latency_ms || 0)}ms`}
        />
        <MetricCard
          label="Error Rate"
          value={`${((metrics?.error_rate || 0) * 100).toFixed(2)}%`}
        />
        <MetricCard
          label="RPS"
          value={(metrics?.requests_per_second || 0).toFixed(1)}
        />
      </div>

      {/* Model Performance */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Model Performance</h2>
        <div className="space-y-2">
          {Array.from(models.entries()).map(([modelName, stats]) => (
            <div key={modelName} className="bg-gray-900 rounded p-4">
              <h3 className="text-white font-medium">{modelName}</h3>
              <div className="grid grid-cols-4 gap-4 mt-2 text-sm">
                <div>
                  <div className="text-gray-400">Requests</div>
                  <div className="text-white">{stats.request_count}</div>
                </div>
                <div>
                  <div className="text-gray-400">Latency</div>
                  <div className="text-white">{Math.round(stats.avg_latency_ms)}ms</div>
                </div>
                <div>
                  <div className="text-gray-400">Tokens</div>
                  <div className="text-white">{stats.total_tokens.toLocaleString()}</div>
                </div>
                <div>
                  <div className="text-gray-400">Cost</div>
                  <div className="text-green-400">${stats.total_cost.toFixed(2)}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Requests */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">
          Recent Requests ({recentRequests.length})
        </h2>
        <RequestsTable requests={recentRequests.slice(0, 10)} />
      </div>
    </div>
  );
}
```

## Step 4: Custom Subscriptions (Advanced)

For custom message handling:

```tsx
import { useWebSocketSubscription, MessageType } from '@/services';

function CustomComponent() {
  const [data, setData] = useState(null);

  useWebSocketSubscription(
    MessageType.METRICS_UPDATE,
    (data, message) => {
      // Custom processing
      console.log('Received metrics:', data);
      setData(data);
    }
  );

  return <div>{/* Render data */}</div>;
}
```

## Step 5: Model-Specific Monitoring

Monitor specific models:

```tsx
import { useModelMetrics } from '@/services';

function ModelMonitor({ modelName }: { modelName: string }) {
  const metrics = useModelMetrics(modelName);

  if (!metrics) {
    return <div>No data for {modelName}</div>;
  }

  return (
    <div>
      <h3>{modelName}</h3>
      <div>Requests: {metrics.request_count}</div>
      <div>Latency: {metrics.avg_latency_ms}ms</div>
      <div>Cost: ${metrics.total_cost.toFixed(2)}</div>
    </div>
  );
}
```

## Step 6: Error Monitoring

Add error monitoring:

```tsx
import { useErrorMonitor } from '@/services';

function ErrorMonitor() {
  const { errors, errorCount, clearErrors } = useErrorMonitor({
    maxSize: 50,
    onError: (error) => {
      if (error.severity === 'critical') {
        // Trigger alert
        alert(`Critical error: ${error.error_message}`);
      }
    },
  });

  return (
    <div>
      <h3>Errors ({errorCount})</h3>
      <button onClick={clearErrors}>Clear</button>
      {errors.map((error, idx) => (
        <div key={idx}>
          <div>{error.error_type}</div>
          <div>{error.error_message}</div>
        </div>
      ))}
    </div>
  );
}
```

## Step 7: System Health Monitoring

Monitor system health:

```tsx
import { useSystemHealth } from '@/services';

function SystemHealth() {
  const { health, isHealthy } = useSystemHealth();

  if (!health) return null;

  return (
    <div>
      <div className={isHealthy ? 'text-green-500' : 'text-red-500'}>
        System {isHealthy ? 'Healthy' : 'Unhealthy'}
      </div>
      <div>CPU: {health.cpu_usage.toFixed(1)}%</div>
      <div>Memory: {health.memory_usage.toFixed(1)}%</div>
      {health.gpu_usage !== undefined && (
        <div>GPU: {health.gpu_usage.toFixed(1)}%</div>
      )}
      <div>Queue: {health.queue_size}</div>
    </div>
  );
}
```

## Environment Variables

Add to your `.env` file:

```bash
# WebSocket Configuration
REACT_APP_WS_URL=ws://localhost:8000/metrics/stream
REACT_APP_WS_DEBUG=true
```

## TypeScript Configuration

Ensure your `tsconfig.json` includes:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/services": ["src/services"],
      "@/services/*": ["src/services/*"]
    }
  }
}
```

## Backend Server Setup

The WebSocket expects a `/metrics/stream` endpoint. Example FastAPI implementation:

```python
from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect
import asyncio
import json
import time

app = FastAPI()

@app.websocket("/metrics/stream")
async def metrics_stream(websocket: WebSocket):
    await websocket.accept()
    sequence = 0

    try:
        while True:
            # Send metrics update
            message = {
                "type": "metrics_update",
                "timestamp": int(time.time() * 1000),
                "sequence": sequence,
                "data": {
                    "total_requests": get_total_requests(),
                    "total_tokens": get_total_tokens(),
                    "total_cost": get_total_cost(),
                    "avg_latency_ms": get_avg_latency(),
                    "error_rate": get_error_rate(),
                    "streaming_percentage": get_streaming_percentage(),
                    "requests_per_second": get_rps(),
                    "tokens_per_second": get_tps(),
                    "active_connections": get_active_connections(),
                }
            }

            await websocket.send_json(message)
            sequence += 1

            # Send every second
            await asyncio.sleep(1)

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()
```

## Testing

Test the WebSocket connection:

```tsx
import { WebSocketProvider } from '@/services';

function TestApp() {
  return (
    <WebSocketProvider
      config={{
        url: 'ws://localhost:8000/metrics/stream',
        debug: true, // Enable detailed logs
      }}
      onConnect={() => console.log('✓ Connected')}
      onDisconnect={(reason) => console.log('✗ Disconnected:', reason)}
      onError={(error) => console.error('✗ Error:', error)}
      onReconnecting={(attempt) => console.log(`⟳ Reconnecting (attempt ${attempt})`)}
    >
      <div>Check console for connection logs</div>
    </WebSocketProvider>
  );
}
```

## Troubleshooting

### Connection Issues

1. Check WebSocket URL is correct
2. Verify server is running and accessible
3. Check for CORS issues (WebSocket uses different protocol)
4. Enable debug mode: `debug: true`
5. Check browser console for detailed logs

### No Data Received

1. Verify server is sending correct message format
2. Check message type matches subscription
3. Enable debug mode to see raw messages
4. Check browser network tab for WebSocket frames

### Performance Issues

1. Reduce `maxRecentRequests` and `maxRecentErrors` in `useRealtimeMetrics()`
2. Use `useWebSocketSubscription` for specific message types only
3. Implement pagination for large datasets
4. Clear history periodically with `clearHistory()`

### Memory Leaks

1. Ensure components properly unmount
2. Don't create subscriptions outside of hooks
3. Use cleanup functions in `useEffect`
4. Monitor browser memory usage

## Best Practices

1. **Use Provider Once**: Wrap app root with `WebSocketProvider` once
2. **Selective Subscriptions**: Only subscribe to needed message types
3. **Handle Offline State**: Always check `isConnected` before showing data
4. **Error Boundaries**: Wrap WebSocket components in error boundaries
5. **Loading States**: Show loading UI while connecting
6. **Graceful Degradation**: Fall back to polling if WebSocket fails
7. **Debug Mode**: Enable in development, disable in production
8. **Monitor Performance**: Use React DevTools Profiler
9. **Clean Up**: Hooks handle cleanup automatically
10. **Type Safety**: Use TypeScript types for all messages

## Production Checklist

- [ ] Environment variables configured
- [ ] Debug mode disabled in production
- [ ] Error boundaries implemented
- [ ] Loading states handled
- [ ] Offline state handled
- [ ] Connection status indicator visible
- [ ] Server WebSocket endpoint tested
- [ ] CORS configured correctly
- [ ] SSL/TLS for production (wss://)
- [ ] Monitoring and logging configured
- [ ] Performance tested under load
- [ ] Memory leaks checked
- [ ] Error handling tested
- [ ] Reconnection logic tested
- [ ] Documentation updated

## Next Steps

1. Integrate into existing dashboard pages
2. Add custom message types as needed
3. Implement notification system for alerts
4. Add data export functionality
5. Create custom visualizations
6. Implement historical data comparison
7. Add user preferences for metrics display
8. Create mobile-responsive views
9. Add keyboard shortcuts
10. Implement advanced filtering

## Support

For issues or questions:
- Check README.md for detailed documentation
- Review examples.tsx for implementation patterns
- Enable debug mode for detailed logs
- Check browser console and network tab
- Review WebSocket frames in browser DevTools

Happy monitoring!
