# WebSocket Real-time Updates System

Production-ready WebSocket client for real-time metrics streaming with automatic reconnection, heartbeat monitoring, and React integration.

## Features

- **Automatic Reconnection**: Exponential backoff strategy for resilient connections
- **Heartbeat Mechanism**: Ping/pong to detect dead connections
- **Message Dispatching**: Type-safe event system for different message types
- **React Hooks**: Easy integration with React components
- **Context API**: Global state management for WebSocket connection
- **Connection Status**: Visual indicators with NVIDIA-themed components
- **Error Handling**: Comprehensive error logging and recovery
- **TypeScript**: Full type safety for all messages and events
- **Message Queue**: Offline message buffering
- **Sequence Tracking**: Message ordering and duplicate detection

## Installation

The WebSocket system is located in `src/services/` and can be imported directly:

```typescript
import {
  WebSocketProvider,
  useRealtimeMetrics,
  ConnectionStatus,
  MessageType,
} from '@/services';
```

## Quick Start

### 1. Wrap your app with WebSocketProvider

```tsx
import { WebSocketProvider } from '@/services';

function App() {
  return (
    <WebSocketProvider
      config={{
        url: 'ws://localhost:8000/metrics/stream',
        reconnectInterval: 1000,
        maxReconnectInterval: 30000,
        reconnectDecay: 1.5,
        heartbeatInterval: 30000,
        debug: true,
      }}
      onConnect={() => console.log('Connected!')}
      onDisconnect={(reason) => console.log('Disconnected:', reason)}
    >
      <Dashboard />
    </WebSocketProvider>
  );
}
```

### 2. Use hooks to access real-time data

```tsx
import { useRealtimeMetrics, ConnectionStatus } from '@/services';

function Dashboard() {
  const {
    metrics,
    models,
    recentRequests,
    isConnected,
    connectionState,
  } = useRealtimeMetrics();

  return (
    <div>
      <ConnectionStatus showDetails showLatency />

      {metrics && (
        <div>
          <h2>Metrics Overview</h2>
          <p>Total Requests: {metrics.total_requests}</p>
          <p>Avg Latency: {metrics.avg_latency_ms}ms</p>
          <p>Error Rate: {metrics.error_rate}%</p>
        </div>
      )}

      <h3>Model Performance</h3>
      {Array.from(models.entries()).map(([modelName, stats]) => (
        <div key={modelName}>
          <h4>{modelName}</h4>
          <p>Requests: {stats.request_count}</p>
          <p>Latency: {stats.avg_latency_ms}ms</p>
          <p>Error Rate: {stats.error_rate}%</p>
        </div>
      ))}
    </div>
  );
}
```

## API Reference

### WebSocketProvider

Provider component that initializes and manages WebSocket connection.

**Props:**

```typescript
interface WebSocketProviderProps {
  children: React.ReactNode;
  config: WebSocketConfig;
  onConnect?: () => void;
  onDisconnect?: (reason: string) => void;
  onError?: (error: Error) => void;
  onReconnecting?: (attempt: number) => void;
  onReconnected?: () => void;
  onMaxReconnectAttemptsReached?: () => void;
}
```

**Config Options:**

```typescript
interface WebSocketConfig {
  url: string; // WebSocket URL
  reconnectInterval?: number; // Initial reconnect delay (default: 1000ms)
  maxReconnectInterval?: number; // Max reconnect delay (default: 30000ms)
  reconnectDecay?: number; // Exponential backoff multiplier (default: 1.5)
  maxReconnectAttempts?: number; // Max attempts (default: Infinity)
  heartbeatInterval?: number; // Ping interval (default: 30000ms)
  heartbeatTimeout?: number; // Pong timeout (default: 5000ms)
  debug?: boolean; // Enable logging (default: false)
  protocols?: string | string[]; // WebSocket protocols
  autoConnect?: boolean; // Auto-connect on init (default: true)
}
```

### Hooks

#### useRealtimeMetrics

Main hook for accessing all real-time metrics data.

```typescript
function useRealtimeMetrics(options?: {
  maxRecentRequests?: number;
  maxRecentErrors?: number;
}): RealtimeMetricsState;
```

**Returns:**

```typescript
interface RealtimeMetricsState {
  metrics: MetricsUpdatePayload | null;
  models: Map<string, ModelUpdatePayload>;
  recentRequests: RequestUpdatePayload[];
  recentErrors: ErrorUpdatePayload[];
  systemStats: SystemUpdatePayload | null;
  rateLimits: Map<string, RateLimitUpdatePayload>;
  costs: CostUpdatePayload | null;
  kvCache: KVCacheUpdatePayload | null;
  isConnected: boolean;
  connectionState: ConnectionState;
  lastUpdate: number | null;
}
```

#### useConnectionStatus

Get current connection status.

```typescript
function useConnectionStatus(): {
  state: ConnectionState;
  isConnected: boolean;
  reconnectAttempts: number;
  latency: number | null;
}
```

#### useWebSocketSubscription

Subscribe to specific message types.

```typescript
function useWebSocketSubscription<T>(
  messageType: MessageType,
  callback: (data: T, message: WebSocketMessage<T>) => void,
  deps?: React.DependencyList
): void;
```

**Example:**

```typescript
useWebSocketSubscription<MetricsUpdatePayload>(
  MessageType.METRICS_UPDATE,
  (data) => {
    console.log('New metrics:', data);
  }
);
```

#### useModelMetrics

Get metrics for a specific model.

```typescript
function useModelMetrics(modelName?: string): ModelUpdatePayload | null;
```

#### useSystemHealth

Monitor system health.

```typescript
function useSystemHealth(): {
  health: SystemUpdatePayload | null;
  isHealthy: boolean;
}
```

#### useRequestHistory

Track request history with filtering.

```typescript
function useRequestHistory(options?: {
  maxSize?: number;
  filterFn?: (request: RequestUpdatePayload) => boolean;
}): {
  requests: RequestUpdatePayload[];
  clearHistory: () => void;
}
```

#### useErrorMonitor

Monitor errors in real-time.

```typescript
function useErrorMonitor(options?: {
  maxSize?: number;
  onError?: (error: ErrorUpdatePayload) => void;
}): {
  errors: ErrorUpdatePayload[];
  errorCount: number;
  clearErrors: () => void;
}
```

#### useAggregateStats

Get aggregate statistics across all metrics.

```typescript
function useAggregateStats(): {
  totalModels: number;
  totalRequests: number;
  totalTokens: number;
  totalCost: number;
  avgLatency: number;
  errorRate: number;
  recentRequestCount: number;
  recentErrorCount: number;
  requestsPerSecond: number;
  tokensPerSecond: number;
}
```

### Components

#### ConnectionStatus

Visual indicator of connection status with NVIDIA theme.

```tsx
<ConnectionStatus
  showDetails={true}
  showLatency={true}
  compact={false}
  position="inline" // or "fixed"
/>
```

**Features:**
- Green dot: Connected
- Yellow dot: Connecting/Reconnecting (animated)
- Red dot: Error
- Gray dot: Disconnected
- Shows latency when connected
- Shows reconnect attempts
- Compact mode with auto-collapse

#### ConnectionStats

Detailed connection statistics card.

```tsx
<ConnectionStats className="my-4" />
```

#### ConnectionBadge

Minimal connection indicator (just a colored dot).

```tsx
<ConnectionBadge className="ml-2" />
```

### Message Types

All available message types:

```typescript
enum MessageType {
  METRICS_UPDATE = 'metrics_update',
  MODEL_UPDATE = 'model_update',
  REQUEST_UPDATE = 'request_update',
  ERROR_UPDATE = 'error_update',
  SYSTEM_UPDATE = 'system_update',
  HEARTBEAT = 'heartbeat',
  PONG = 'pong',
  INIT = 'init',
  RATE_LIMIT_UPDATE = 'rate_limit_update',
  COST_UPDATE = 'cost_update',
  KV_CACHE_UPDATE = 'kv_cache_update',
}
```

### WebSocket Service

Direct access to the WebSocket service (advanced usage).

```typescript
import { WebSocketService, createWebSocketService } from '@/services';

const service = createWebSocketService(
  {
    url: 'ws://localhost:8000/metrics/stream',
    debug: true,
  },
  {
    onConnect: () => console.log('Connected'),
    onError: (error) => console.error('Error:', error),
  }
);

// Connect
service.connect();

// Subscribe to messages
const subscription = service.subscribe(
  MessageType.METRICS_UPDATE,
  (data, message) => {
    console.log('Metrics:', data);
  }
);

// Send message
service.send({ type: 'custom', data: { foo: 'bar' } });

// Disconnect
service.disconnect();

// Cleanup
subscription.unsubscribe();
service.destroy();
```

## Connection States

```typescript
enum ConnectionState {
  CONNECTING = 'CONNECTING',
  CONNECTED = 'CONNECTED',
  DISCONNECTED = 'DISCONNECTED',
  RECONNECTING = 'RECONNECTING',
  ERROR = 'ERROR',
  CLOSED = 'CLOSED',
}
```

## Message Format

All WebSocket messages follow this format:

```typescript
interface WebSocketMessage<T = any> {
  type: MessageType;
  timestamp: number;
  data: T;
  sequence?: number;
  metadata?: Record<string, any>;
}
```

## Server Integration

The WebSocket client expects messages from `/metrics/stream` endpoint in this format:

```json
{
  "type": "metrics_update",
  "timestamp": 1234567890,
  "sequence": 42,
  "data": {
    "total_requests": 1000,
    "total_tokens": 50000,
    "avg_latency_ms": 150,
    "error_rate": 0.05
  }
}
```

### Example Server (FastAPI)

```python
from fastapi import FastAPI, WebSocket
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
                    "total_requests": 1000,
                    "total_tokens": 50000,
                    "total_cost": 25.50,
                    "avg_latency_ms": 150,
                    "error_rate": 0.05,
                    "streaming_percentage": 0.75,
                    "requests_per_second": 10,
                    "tokens_per_second": 500,
                    "active_connections": 5,
                }
            }

            await websocket.send_json(message)
            sequence += 1
            await asyncio.sleep(1)

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
```

## Error Handling

The WebSocket service handles errors gracefully:

1. **Connection Errors**: Automatic reconnection with exponential backoff
2. **Message Parsing Errors**: Logged and skipped, connection stays alive
3. **Heartbeat Timeout**: Closes connection and reconnects
4. **Max Reconnect Attempts**: Notifies via `onMaxReconnectAttemptsReached` callback

## Best Practices

1. **Use Provider at Top Level**: Wrap your app with `WebSocketProvider` once
2. **Subscribe in Components**: Use hooks in components that need specific data
3. **Clean Up Subscriptions**: Hooks handle cleanup automatically
4. **Handle Offline State**: Check `isConnected` before showing real-time data
5. **Monitor Latency**: Use connection status component to show health
6. **Error Boundaries**: Wrap components in error boundaries for robustness
7. **Debug Mode**: Enable debug logging during development

## Performance

- **Memory Efficient**: Bounded queues for recent data (configurable)
- **No Props Drilling**: Context API for clean component tree
- **Selective Updates**: Only subscribed components re-render
- **Message Queue**: Buffers messages when offline (max 100)
- **Optimized Re-renders**: Uses React best practices for minimal updates

## Troubleshooting

### Connection keeps disconnecting

- Check server WebSocket implementation
- Verify heartbeat interval matches server timeout
- Enable debug mode to see detailed logs

### Messages not received

- Check message type matches subscription
- Verify message format from server
- Enable debug mode to see raw messages

### High memory usage

- Reduce `maxRecentRequests` and `maxRecentErrors` options
- Clear history periodically with `clearHistory()`
- Check for memory leaks in subscription callbacks

### Latency issues

- Check network connection
- Verify server performance
- Consider adjusting heartbeat interval

## License

Part of the FakeAI dashboard system.
