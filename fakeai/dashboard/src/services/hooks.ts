/**
 * React hooks for WebSocket integration
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  ConnectionState,
  MessageType,
  MessageCallback,
  Subscription,
  WebSocketMessage,
  MetricsUpdatePayload,
  ModelUpdatePayload,
  RequestUpdatePayload,
  ErrorUpdatePayload,
  SystemUpdatePayload,
  RateLimitUpdatePayload,
  CostUpdatePayload,
  KVCacheUpdatePayload,
  RealtimeMetricsState,
} from './types';
import { useWebSocketContext } from './WebSocketContext';

/**
 * Hook for accessing WebSocket service
 */
export function useWebSocket() {
  const context = useWebSocketContext();

  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }

  return context;
}

/**
 * Hook for subscribing to specific message types
 */
export function useWebSocketSubscription<T = any>(
  messageType: MessageType,
  callback: MessageCallback<T>,
  deps: React.DependencyList = []
): void {
  const { subscribe } = useWebSocket();
  const callbackRef = useRef(callback);

  // Update callback ref when it changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    const subscription = subscribe<T>(messageType, (data, message) => {
      callbackRef.current(data, message);
    });

    return () => {
      subscription.unsubscribe();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messageType, subscribe, ...deps]);
}

/**
 * Hook for connection status
 */
export function useConnectionStatus() {
  const { connectionInfo } = useWebSocket();
  const [status, setStatus] = useState({
    state: connectionInfo.state,
    isConnected: connectionInfo.state === ConnectionState.CONNECTED,
    reconnectAttempts: connectionInfo.reconnectAttempts,
    latency: connectionInfo.latency,
  });

  useEffect(() => {
    setStatus({
      state: connectionInfo.state,
      isConnected: connectionInfo.state === ConnectionState.CONNECTED,
      reconnectAttempts: connectionInfo.reconnectAttempts,
      latency: connectionInfo.latency,
    });
  }, [connectionInfo]);

  return status;
}

/**
 * Hook for real-time metrics with automatic state management
 */
export function useRealtimeMetrics(options?: {
  maxRecentRequests?: number;
  maxRecentErrors?: number;
}): RealtimeMetricsState {
  const maxRecentRequests = options?.maxRecentRequests || 50;
  const maxRecentErrors = options?.maxRecentErrors || 20;

  const { connectionInfo } = useWebSocket();
  const [state, setState] = useState<RealtimeMetricsState>({
    metrics: null,
    models: new Map(),
    recentRequests: [],
    recentErrors: [],
    systemStats: null,
    rateLimits: new Map(),
    costs: null,
    kvCache: null,
    isConnected: connectionInfo.state === ConnectionState.CONNECTED,
    connectionState: connectionInfo.state,
    lastUpdate: null,
  });

  // Subscribe to metrics updates
  useWebSocketSubscription<MetricsUpdatePayload>(
    MessageType.METRICS_UPDATE,
    useCallback((data) => {
      setState((prev) => ({
        ...prev,
        metrics: data,
        lastUpdate: Date.now(),
      }));
    }, [])
  );

  // Subscribe to model updates
  useWebSocketSubscription<ModelUpdatePayload>(
    MessageType.MODEL_UPDATE,
    useCallback((data) => {
      setState((prev) => {
        const newModels = new Map(prev.models);
        newModels.set(data.model, data);
        return {
          ...prev,
          models: newModels,
          lastUpdate: Date.now(),
        };
      });
    }, [])
  );

  // Subscribe to request updates
  useWebSocketSubscription<RequestUpdatePayload>(
    MessageType.REQUEST_UPDATE,
    useCallback(
      (data) => {
        setState((prev) => {
          const newRequests = [data, ...prev.recentRequests].slice(0, maxRecentRequests);
          return {
            ...prev,
            recentRequests: newRequests,
            lastUpdate: Date.now(),
          };
        });
      },
      [maxRecentRequests]
    )
  );

  // Subscribe to error updates
  useWebSocketSubscription<ErrorUpdatePayload>(
    MessageType.ERROR_UPDATE,
    useCallback(
      (data) => {
        setState((prev) => {
          const newErrors = [data, ...prev.recentErrors].slice(0, maxRecentErrors);
          return {
            ...prev,
            recentErrors: newErrors,
            lastUpdate: Date.now(),
          };
        });
      },
      [maxRecentErrors]
    )
  );

  // Subscribe to system updates
  useWebSocketSubscription<SystemUpdatePayload>(
    MessageType.SYSTEM_UPDATE,
    useCallback((data) => {
      setState((prev) => ({
        ...prev,
        systemStats: data,
        lastUpdate: Date.now(),
      }));
    }, [])
  );

  // Subscribe to rate limit updates
  useWebSocketSubscription<RateLimitUpdatePayload>(
    MessageType.RATE_LIMIT_UPDATE,
    useCallback((data) => {
      setState((prev) => {
        const newRateLimits = new Map(prev.rateLimits);
        newRateLimits.set(data.endpoint, data);
        return {
          ...prev,
          rateLimits: newRateLimits,
          lastUpdate: Date.now(),
        };
      });
    }, [])
  );

  // Subscribe to cost updates
  useWebSocketSubscription<CostUpdatePayload>(
    MessageType.COST_UPDATE,
    useCallback((data) => {
      setState((prev) => ({
        ...prev,
        costs: data,
        lastUpdate: Date.now(),
      }));
    }, [])
  );

  // Subscribe to KV cache updates
  useWebSocketSubscription<KVCacheUpdatePayload>(
    MessageType.KV_CACHE_UPDATE,
    useCallback((data) => {
      setState((prev) => ({
        ...prev,
        kvCache: data,
        lastUpdate: Date.now(),
      }));
    }, [])
  );

  // Update connection state
  useEffect(() => {
    setState((prev) => ({
      ...prev,
      isConnected: connectionInfo.state === ConnectionState.CONNECTED,
      connectionState: connectionInfo.state,
    }));
  }, [connectionInfo.state]);

  return state;
}

/**
 * Hook for sending messages
 */
export function useWebSocketSend() {
  const { send } = useWebSocket();

  return useCallback(
    (message: any) => {
      return send(message);
    },
    [send]
  );
}

/**
 * Hook for manual connection control
 */
export function useWebSocketConnection() {
  const { connect, disconnect, connectionInfo } = useWebSocket();

  return {
    connect,
    disconnect,
    isConnected: connectionInfo.state === ConnectionState.CONNECTED,
    state: connectionInfo.state,
    reconnectAttempts: connectionInfo.reconnectAttempts,
    latency: connectionInfo.latency,
  };
}

/**
 * Hook for specific metric type
 */
export function useMetric<T = any>(
  messageType: MessageType
): { data: T | null; lastUpdate: number | null } {
  const [data, setData] = useState<T | null>(null);
  const [lastUpdate, setLastUpdate] = useState<number | null>(null);

  useWebSocketSubscription<T>(
    messageType,
    useCallback((receivedData) => {
      setData(receivedData);
      setLastUpdate(Date.now());
    }, [])
  );

  return { data, lastUpdate };
}

/**
 * Hook for request history with filtering
 */
export function useRequestHistory(options?: {
  maxSize?: number;
  filterFn?: (request: RequestUpdatePayload) => boolean;
}) {
  const maxSize = options?.maxSize || 100;
  const filterFn = options?.filterFn;

  const [requests, setRequests] = useState<RequestUpdatePayload[]>([]);

  useWebSocketSubscription<RequestUpdatePayload>(
    MessageType.REQUEST_UPDATE,
    useCallback(
      (data) => {
        setRequests((prev) => {
          const shouldInclude = filterFn ? filterFn(data) : true;
          if (!shouldInclude) return prev;

          const newRequests = [data, ...prev].slice(0, maxSize);
          return newRequests;
        });
      },
      [maxSize, filterFn]
    )
  );

  const clearHistory = useCallback(() => {
    setRequests([]);
  }, []);

  return { requests, clearHistory };
}

/**
 * Hook for error monitoring
 */
export function useErrorMonitor(options?: {
  maxSize?: number;
  onError?: (error: ErrorUpdatePayload) => void;
}) {
  const maxSize = options?.maxSize || 50;
  const onError = options?.onError;

  const [errors, setErrors] = useState<ErrorUpdatePayload[]>([]);
  const [errorCount, setErrorCount] = useState(0);

  useWebSocketSubscription<ErrorUpdatePayload>(
    MessageType.ERROR_UPDATE,
    useCallback(
      (data) => {
        setErrors((prev) => [data, ...prev].slice(0, maxSize));
        setErrorCount((count) => count + 1);

        if (onError) {
          onError(data);
        }
      },
      [maxSize, onError]
    )
  );

  const clearErrors = useCallback(() => {
    setErrors([]);
  }, []);

  return { errors, errorCount, clearErrors };
}

/**
 * Hook for model-specific metrics
 */
export function useModelMetrics(modelName?: string) {
  const [metrics, setMetrics] = useState<ModelUpdatePayload | null>(null);

  useWebSocketSubscription<ModelUpdatePayload>(
    MessageType.MODEL_UPDATE,
    useCallback(
      (data) => {
        if (!modelName || data.model === modelName) {
          setMetrics(data);
        }
      },
      [modelName]
    )
  );

  return metrics;
}

/**
 * Hook for system health monitoring
 */
export function useSystemHealth() {
  const [health, setHealth] = useState<SystemUpdatePayload | null>(null);
  const [isHealthy, setIsHealthy] = useState(true);

  useWebSocketSubscription<SystemUpdatePayload>(
    MessageType.SYSTEM_UPDATE,
    useCallback((data) => {
      setHealth(data);

      // Determine health status based on thresholds
      const healthy =
        data.cpu_usage < 90 &&
        data.memory_usage < 90 &&
        (data.gpu_usage === undefined || data.gpu_usage < 95) &&
        data.queue_size < 1000;

      setIsHealthy(healthy);
    }, [])
  );

  return { health, isHealthy };
}

/**
 * Hook for aggregate statistics
 */
export function useAggregateStats() {
  const { metrics, models, recentRequests, recentErrors } = useRealtimeMetrics();

  const stats = {
    totalModels: models.size,
    totalRequests: metrics?.total_requests || 0,
    totalTokens: metrics?.total_tokens || 0,
    totalCost: metrics?.total_cost || 0,
    avgLatency: metrics?.avg_latency_ms || 0,
    errorRate: metrics?.error_rate || 0,
    recentRequestCount: recentRequests.length,
    recentErrorCount: recentErrors.length,
    requestsPerSecond: metrics?.requests_per_second || 0,
    tokensPerSecond: metrics?.tokens_per_second || 0,
  };

  return stats;
}
