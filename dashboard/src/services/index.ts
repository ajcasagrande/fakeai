/**
 * Services Module
 *
 * Centralized export for all service modules including WebSocket services,
 * API clients, and related hooks.
 *
 * Updated: October 2025
 */

// Generic WebSocket hook (reusable)
export { useGenericWebSocket, ConnectionState } from './useGenericWebSocket';
export type {
  WebSocketHookOptions,
  WebSocketHookResult,
} from './useGenericWebSocket';

// Metrics-specific WebSocket
export { default as MetricsWebSocketService } from './MetricsWebSocketService';
export type {
  MetricsUpdate,
  SubscribeMessage,
  WebSocketMessage,
  MetricsWebSocketConfig,
} from './MetricsWebSocketService';

export { default as useMetricsWebSocket } from './useMetricsWebSocket';
export type {
  MetricsData,
  UseMetricsWebSocketResult,
  UseMetricsWebSocketOptions,
} from './useMetricsWebSocket';
