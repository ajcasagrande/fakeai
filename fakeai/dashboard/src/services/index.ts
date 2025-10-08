/**
 * WebSocket Real-time Updates System
 *
 * Production-ready WebSocket client with:
 * - Automatic reconnection with exponential backoff
 * - Heartbeat/ping mechanism
 * - Message parsing and event dispatching
 * - TypeScript interfaces for type safety
 * - React hooks for easy integration
 * - Context API for global state management
 * - Connection status indicators with NVIDIA theme
 * - Comprehensive error handling and logging
 *
 * @example Basic usage
 * ```tsx
 * import { WebSocketProvider, useRealtimeMetrics, ConnectionStatus } from '@/services';
 *
 * function App() {
 *   return (
 *     <WebSocketProvider config={{ url: 'ws://localhost:8000/metrics/stream' }}>
 *       <Dashboard />
 *     </WebSocketProvider>
 *   );
 * }
 *
 * function Dashboard() {
 *   const metrics = useRealtimeMetrics();
 *   return (
 *     <div>
 *       <ConnectionStatus />
 *       <MetricsDisplay data={metrics} />
 *     </div>
 *   );
 * }
 * ```
 */

// Core service
export { WebSocketService, createWebSocketService } from './WebSocketService';

// Context
export { WebSocketProvider, useWebSocketContext, withWebSocket } from './WebSocketContext';

// Hooks
export {
  useWebSocket,
  useWebSocketSubscription,
  useConnectionStatus,
  useRealtimeMetrics,
  useWebSocketSend,
  useWebSocketConnection,
  useMetric,
  useRequestHistory,
  useErrorMonitor,
  useModelMetrics,
  useSystemHealth,
  useAggregateStats,
} from './hooks';

// Components
export { ConnectionStatus, ConnectionStats, ConnectionBadge } from './components';

// Types
export type {
  // Enums
  ConnectionState,
  MessageType,

  // Messages
  WebSocketMessage,
  MetricsUpdatePayload,
  ModelUpdatePayload,
  RequestUpdatePayload,
  ErrorUpdatePayload,
  SystemUpdatePayload,
  RateLimitUpdatePayload,
  CostUpdatePayload,
  KVCacheUpdatePayload,
  HeartbeatPayload,

  // Configuration
  WebSocketConfig,
  ConnectionInfo,
  WebSocketEventHandlers,

  // Subscriptions
  MessageCallback,
  Subscription,

  // Service interface
  IWebSocketService,

  // State
  RealtimeMetricsState,
  WebSocketContextValue,
} from './types';

// Re-export enums for convenience
export { ConnectionState, MessageType } from './types';
