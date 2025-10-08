/**
 * Generic WebSocket Hook
 *
 * Reusable WebSocket hook for any real-time data streaming.
 * Supports automatic reconnection, heartbeat, and type-safe data handling.
 *
 * Updated: October 2025
 */

import { useEffect, useState, useRef, useCallback } from 'react';

export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error',
}

export interface WebSocketHookOptions<T> {
  url: string;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
  heartbeatInterval?: number;
  onData?: (data: T) => void;
  onError?: (error: Error) => void;
  onStateChange?: (state: ConnectionState) => void;
}

export interface WebSocketHookResult<T> {
  data: T | null;
  connectionState: ConnectionState;
  isConnected: boolean;
  isReconnecting: boolean;
  error: Error | null;
  latency: number;
  reconnect: () => void;
  disconnect: () => void;
  send: (message: any) => void;
}

/**
 * Generic WebSocket hook for real-time data streaming
 *
 * @template T - Type of data being streamed
 * @param options - Configuration options
 * @returns WebSocket state and control functions
 */
export function useGenericWebSocket<T = any>(
  options: WebSocketHookOptions<T>
): WebSocketHookResult<T> {
  const {
    url,
    autoConnect = true,
    reconnectInterval = 1000,
    maxReconnectInterval = 30000,
    heartbeatInterval = 10000,
    onData,
    onError,
    onStateChange,
  } = options;

  const [data, setData] = useState<T | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>(
    ConnectionState.DISCONNECTED
  );
  const [error, setError] = useState<Error | null>(null);
  const [latency, setLatency] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastPingTimeRef = useRef(0);

  const updateState = useCallback(
    (newState: ConnectionState) => {
      setConnectionState(newState);
      onStateChange?.(newState);
    },
    [onStateChange]
  );

  const send = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const startHeartbeat = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
    }

    heartbeatTimerRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        lastPingTimeRef.current = Date.now();
        send({ type: 'ping' });
      }
    }, heartbeatInterval);
  }, [heartbeatInterval, send]);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatTimerRef.current) {
      clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    updateState(ConnectionState.CONNECTING);

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log(`[WebSocket] Connected to ${url}`);
        updateState(ConnectionState.CONNECTED);
        reconnectAttemptRef.current = 0;
        setError(null);
        startHeartbeat();
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          switch (message.type) {
            case 'pong':
              setLatency(Date.now() - lastPingTimeRef.current);
              break;

            case 'connected':
              console.log(`[WebSocket] Connection acknowledged`);
              break;

            case 'error':
              const err = new Error(message.message || 'Server error');
              setError(err);
              onError?.(err);
              break;

            default:
              // Handle data updates (kv_cache_update, ai_dynamo_update, etc.)
              if (message.data) {
                setData(message.data);
                onData?.(message.data);
              }
          }
        } catch (err) {
          console.error('[WebSocket] Failed to parse message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('[WebSocket] Error:', event);
        updateState(ConnectionState.ERROR);
        const err = new Error('WebSocket error');
        setError(err);
        onError?.(err);
      };

      ws.onclose = () => {
        console.log('[WebSocket] Connection closed');
        stopHeartbeat();

        if (connectionState !== ConnectionState.DISCONNECTED) {
          attemptReconnect();
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('[WebSocket] Failed to create connection:', err);
      const error = err instanceof Error ? err : new Error('Failed to create WebSocket');
      setError(error);
      onError?.(error);
      updateState(ConnectionState.ERROR);
    }
  }, [url, connectionState, updateState, onData, onError, startHeartbeat, stopHeartbeat]);

  const attemptReconnect = useCallback(() => {
    const delay = Math.min(
      reconnectInterval * Math.pow(2, reconnectAttemptRef.current),
      maxReconnectInterval
    );

    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttemptRef.current + 1})`);
    updateState(ConnectionState.RECONNECTING);

    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
    }

    reconnectTimerRef.current = setTimeout(() => {
      reconnectAttemptRef.current++;
      connect();
    }, delay);
  }, [reconnectInterval, maxReconnectInterval, updateState, connect]);

  const disconnect = useCallback(() => {
    stopHeartbeat();

    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    updateState(ConnectionState.DISCONNECTED);
  }, [stopHeartbeat, updateState]);

  const reconnect = useCallback(() => {
    disconnect();
    setTimeout(() => connect(), 100);
  }, [disconnect, connect]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect]); // Only run on mount/unmount

  return {
    data,
    connectionState,
    isConnected: connectionState === ConnectionState.CONNECTED,
    isReconnecting: connectionState === ConnectionState.RECONNECTING,
    error,
    latency,
    reconnect,
    disconnect,
    send,
  };
}

export default useGenericWebSocket;
