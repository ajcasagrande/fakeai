/**
 * React Context for WebSocket service
 * Provides global access to WebSocket connection and methods
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { WebSocketService, createWebSocketService } from './WebSocketService';
import {
  WebSocketConfig,
  WebSocketContextValue,
  ConnectionInfo,
  ConnectionState,
  MessageType,
  MessageCallback,
  Subscription,
} from './types';

/**
 * WebSocket context
 */
const WebSocketContext = createContext<WebSocketContextValue | null>(null);

/**
 * WebSocket provider props
 */
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

/**
 * WebSocket provider component
 */
export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({
  children,
  config,
  onConnect,
  onDisconnect,
  onError,
  onReconnecting,
  onReconnected,
  onMaxReconnectAttemptsReached,
}) => {
  const [service, setService] = useState<WebSocketService | null>(null);
  const [connectionInfo, setConnectionInfo] = useState<ConnectionInfo>({
    state: ConnectionState.DISCONNECTED,
    connectedAt: null,
    disconnectedAt: null,
    reconnectAttempts: 0,
    lastError: null,
    latency: null,
    messageCount: 0,
    bytesReceived: 0,
    bytesSent: 0,
  });

  // Initialize WebSocket service
  useEffect(() => {
    const wsService = createWebSocketService(config, {
      onConnect: () => {
        setConnectionInfo(wsService.getConnectionInfo());
        if (onConnect) onConnect();
      },
      onDisconnect: (reason) => {
        setConnectionInfo(wsService.getConnectionInfo());
        if (onDisconnect) onDisconnect(reason);
      },
      onError: (error) => {
        setConnectionInfo(wsService.getConnectionInfo());
        if (onError) onError(error);
      },
      onReconnecting: (attempt) => {
        setConnectionInfo(wsService.getConnectionInfo());
        if (onReconnecting) onReconnecting(attempt);
      },
      onReconnected: () => {
        setConnectionInfo(wsService.getConnectionInfo());
        if (onReconnected) onReconnected();
      },
      onMaxReconnectAttemptsReached: () => {
        setConnectionInfo(wsService.getConnectionInfo());
        if (onMaxReconnectAttemptsReached) onMaxReconnectAttemptsReached();
      },
    });

    setService(wsService);

    // Cleanup on unmount
    return () => {
      wsService.destroy();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Poll connection info for updates (latency, message count, etc.)
  useEffect(() => {
    if (!service) return;

    const interval = setInterval(() => {
      setConnectionInfo(service.getConnectionInfo());
    }, 1000);

    return () => clearInterval(interval);
  }, [service]);

  // Subscribe method
  const subscribe = useCallback(
    <T = any>(type: MessageType, callback: MessageCallback<T>): Subscription => {
      if (!service) {
        throw new Error('WebSocket service not initialized');
      }
      return service.subscribe(type, callback);
    },
    [service]
  );

  // Send method
  const send = useCallback(
    (message: any): boolean => {
      if (!service) {
        console.warn('WebSocket service not initialized');
        return false;
      }
      return service.send(message);
    },
    [service]
  );

  // Connect method
  const connect = useCallback(() => {
    if (!service) {
      console.warn('WebSocket service not initialized');
      return;
    }
    service.connect();
  }, [service]);

  // Disconnect method
  const disconnect = useCallback(() => {
    if (!service) {
      console.warn('WebSocket service not initialized');
      return;
    }
    service.disconnect();
  }, [service]);

  const contextValue: WebSocketContextValue = {
    service,
    connectionInfo,
    subscribe,
    send,
    connect,
    disconnect,
  };

  return <WebSocketContext.Provider value={contextValue}>{children}</WebSocketContext.Provider>;
};

/**
 * Hook to access WebSocket context
 */
export function useWebSocketContext(): WebSocketContextValue {
  const context = useContext(WebSocketContext);

  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }

  return context;
}

/**
 * HOC to provide WebSocket context to a component
 */
export function withWebSocket<P extends object>(
  Component: React.ComponentType<P>
): React.FC<P & { wsConfig: WebSocketConfig }> {
  return (props) => {
    const { wsConfig, ...restProps } = props as any;

    return (
      <WebSocketProvider config={wsConfig}>
        <Component {...(restProps as P)} />
      </WebSocketProvider>
    );
  };
}
