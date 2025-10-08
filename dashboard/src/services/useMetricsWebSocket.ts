/**
 * useMetricsWebSocket Hook
 *
 * React hook for consuming real-time metrics via WebSocket.
 * Provides automatic connection management, state tracking, and error handling.
 *
 * Updated: October 2025
 */

import { useEffect, useState, useRef, useCallback } from 'react';
import MetricsWebSocketService, {
  ConnectionState,
  MetricsUpdate,
} from './MetricsWebSocketService';

// Re-export ConnectionState for convenience
export { ConnectionState } from './MetricsWebSocketService';

export interface MetricsData {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  error_rate: number;
  avg_latency: number;
  p95_latency: number;
  p99_latency: number;
  throughput: number;
  active_connections: number;
  recent_requests?: Array<{
    timestamp: string;
    endpoint: string;
    method: string;
    status: number;
    latency: number;
    model?: string;
  }>;
  latency_history?: Array<{
    timestamp: string;
    avg: number;
    p95: number;
    p99: number;
  }>;
  throughput_history?: Array<{
    timestamp: string;
    requests: number;
    tokens?: number;
  }>;
}

export interface UseMetricsWebSocketResult {
  metrics: MetricsData | null;
  connectionState: ConnectionState;
  isConnected: boolean;
  isReconnecting: boolean;
  error: Error | null;
  latency: number;
  reconnect: () => void;
  disconnect: () => void;
}

export interface UseMetricsWebSocketOptions {
  url?: string;
  filters?: {
    endpoint?: string;
    model?: string;
    metric_type?: string;
    interval?: number;
  };
  autoConnect?: boolean;
}

const DEFAULT_WS_URL =
  import.meta.env.VITE_WS_URL ||
  `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/metrics/stream`;

/**
 * Hook for consuming real-time metrics via WebSocket
 *
 * @param options Configuration options
 * @returns Metrics data, connection state, and control functions
 *
 * @example
 * ```tsx
 * function MetricsComponent() {
 *   const { metrics, isConnected, connectionState } = useMetricsWebSocket({
 *     filters: { interval: 1.0 }
 *   });
 *
 *   return (
 *     <div>
 *       <div>Status: {connectionState}</div>
 *       <div>Requests: {metrics?.total_requests}</div>
 *       <div>Latency: {metrics?.avg_latency}ms</div>
 *     </div>
 *   );
 * }
 * ```
 */
export function useMetricsWebSocket(
  options: UseMetricsWebSocketOptions = {}
): UseMetricsWebSocketResult {
  const {
    url = DEFAULT_WS_URL,
    filters,
    autoConnect = true,
  } = options;

  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>(
    ConnectionState.DISCONNECTED
  );
  const [error, setError] = useState<Error | null>(null);
  const [latency, setLatency] = useState(0);

  const serviceRef = useRef<MetricsWebSocketService | null>(null);
  const latencyIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Initialize service
  useEffect(() => {
    const service = new MetricsWebSocketService({
      url,
      onStateChange: (state) => {
        setConnectionState(state);
        if (state === ConnectionState.CONNECTED) {
          setError(null);
        }
      },
      onMetricsUpdate: (data) => {
        setMetrics(data as MetricsData);
        setError(null);
      },
      onError: (err) => {
        setError(err);
        console.error('[useMetricsWS] Error:', err);
      },
    });

    serviceRef.current = service;

    // Start latency tracking
    latencyIntervalRef.current = setInterval(() => {
      if (service.isConnected()) {
        setLatency(service.getLatency());
      }
    }, 1000);

    // Auto-connect if enabled
    if (autoConnect) {
      service.connect();
    }

    // Cleanup on unmount
    return () => {
      if (latencyIntervalRef.current) {
        clearInterval(latencyIntervalRef.current);
      }
      service.disconnect();
    };
  }, [url, autoConnect]);

  // Update subscription filters when they change
  useEffect(() => {
    if (filters && serviceRef.current?.isConnected()) {
      serviceRef.current.subscribe(filters);
    }
  }, [filters]);

  // Reconnect function
  const reconnect = useCallback(() => {
    if (serviceRef.current) {
      serviceRef.current.disconnect();
      setTimeout(() => {
        serviceRef.current?.connect();
      }, 100);
    }
  }, []);

  // Disconnect function
  const disconnect = useCallback(() => {
    serviceRef.current?.disconnect();
  }, []);

  return {
    metrics,
    connectionState,
    isConnected: connectionState === ConnectionState.CONNECTED,
    isReconnecting: connectionState === ConnectionState.RECONNECTING,
    error,
    latency,
    reconnect,
    disconnect,
  };
}

export default useMetricsWebSocket;
