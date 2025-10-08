/**
 * Metrics WebSocket Service
 *
 * Fully-featured WebSocket client for real-time metrics streaming.
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Heartbeat/ping-pong for connection health
 * - Subscription management
 * - Type-safe message handling
 * - Connection state management
 * - Error handling and recovery
 *
 * Updated: October 2025
 */

export enum ConnectionState {
  DISCONNECTED = 'disconnected',
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  RECONNECTING = 'reconnecting',
  ERROR = 'error',
}

export interface MetricsUpdate {
  type: 'metrics_update';
  timestamp: number;
  data: {
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
  };
}

export interface SubscribeMessage {
  type: 'subscribe';
  filters?: {
    endpoint?: string;
    model?: string;
    metric_type?: string;
    interval?: number;
  };
}

export interface PingMessage {
  type: 'ping';
}

export interface PongMessage {
  type: 'pong';
  timestamp: number;
}

export interface ErrorMessage {
  type: 'error';
  message: string;
}

export interface SubscribedMessage {
  type: 'subscribed';
  filters: any;
}

export type WebSocketMessage =
  | MetricsUpdate
  | PongMessage
  | ErrorMessage
  | SubscribedMessage;

export interface MetricsWebSocketConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
  heartbeatInterval?: number;
  reconnectAttempts?: number;
  onStateChange?: (state: ConnectionState) => void;
  onMetricsUpdate?: (data: MetricsUpdate['data']) => void;
  onError?: (error: Error) => void;
}

export class MetricsWebSocketService {
  private ws: WebSocket | null = null;
  private config: Required<MetricsWebSocketConfig>;
  private state: ConnectionState = ConnectionState.DISCONNECTED;
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private lastPingTime = 0;
  private latency = 0;

  constructor(config: MetricsWebSocketConfig) {
    this.config = {
      reconnectInterval: 1000,
      maxReconnectInterval: 30000,
      heartbeatInterval: 10000,
      reconnectAttempts: -1, // Infinite
      onStateChange: () => {},
      onMetricsUpdate: () => {},
      onError: () => {},
      ...config,
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN || this.ws?.readyState === WebSocket.CONNECTING) {
      return;
    }

    this.updateState(ConnectionState.CONNECTING);

    try {
      this.ws = new WebSocket(this.config.url);

      this.ws.onopen = () => this.handleOpen();
      this.ws.onmessage = (event) => this.handleMessage(event);
      this.ws.onerror = (error) => this.handleError(error);
      this.ws.onclose = () => this.handleClose();
    } catch (error) {
      this.handleError(error instanceof Error ? error : new Error('Failed to create WebSocket'));
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.stopHeartbeat();
    this.cancelReconnect();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.updateState(ConnectionState.DISCONNECTED);
  }

  /**
   * Subscribe to metrics with optional filters
   */
  subscribe(filters?: SubscribeMessage['filters']): void {
    const message: SubscribeMessage = {
      type: 'subscribe',
      filters,
    };

    this.send(message);
  }

  /**
   * Get current connection state
   */
  getState(): ConnectionState {
    return this.state;
  }

  /**
   * Get current WebSocket latency
   */
  getLatency(): number {
    return this.latency;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.state === ConnectionState.CONNECTED;
  }

  /**
   * Send message to server
   */
  private send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not ready, message not sent:', message);
    }
  }

  /**
   * Handle WebSocket open event
   */
  private handleOpen(): void {
    console.log('[MetricsWS] Connected');
    this.updateState(ConnectionState.CONNECTED);
    this.reconnectAttempt = 0;

    // Subscribe to all metrics with 1 second interval
    this.subscribe({ interval: 1.0 });

    // Start heartbeat
    this.startHeartbeat();
  }

  /**
   * Handle incoming messages
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);

      switch (message.type) {
        case 'metrics_update':
          this.config.onMetricsUpdate(message.data);
          break;

        case 'pong':
          this.latency = Date.now() - this.lastPingTime;
          break;

        case 'subscribed':
          console.log('[MetricsWS] Subscribed successfully:', message.filters);
          break;

        case 'error':
          console.error('[MetricsWS] Server error:', message.message);
          this.config.onError(new Error(message.message));
          break;

        default:
          console.warn('[MetricsWS] Unknown message type:', message);
      }
    } catch (error) {
      console.error('[MetricsWS] Failed to parse message:', error);
      this.config.onError(
        error instanceof Error ? error : new Error('Failed to parse message')
      );
    }
  }

  /**
   * Handle WebSocket error
   */
  private handleError(error: Event | Error): void {
    console.error('[MetricsWS] WebSocket error:', error);
    this.updateState(ConnectionState.ERROR);

    const errorObj = error instanceof Error ? error : new Error('WebSocket error');
    this.config.onError(errorObj);
  }

  /**
   * Handle WebSocket close event
   */
  private handleClose(): void {
    console.log('[MetricsWS] Connection closed');
    this.stopHeartbeat();

    if (this.state !== ConnectionState.DISCONNECTED) {
      this.attemptReconnect();
    }
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  private attemptReconnect(): void {
    if (
      this.config.reconnectAttempts !== -1 &&
      this.reconnectAttempt >= this.config.reconnectAttempts
    ) {
      console.log('[MetricsWS] Max reconnect attempts reached');
      this.updateState(ConnectionState.ERROR);
      return;
    }

    const delay = Math.min(
      this.config.reconnectInterval * Math.pow(2, this.reconnectAttempt),
      this.config.maxReconnectInterval
    );

    console.log(`[MetricsWS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempt + 1})`);
    this.updateState(ConnectionState.RECONNECTING);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempt++;
      this.connect();
    }, delay);
  }

  /**
   * Cancel pending reconnect
   */
  private cancelReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Start heartbeat ping/pong
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();

    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.lastPingTime = Date.now();
        this.send({ type: 'ping' });
      }
    }, this.config.heartbeatInterval);
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * Update connection state and notify listeners
   */
  private updateState(newState: ConnectionState): void {
    if (this.state !== newState) {
      this.state = newState;
      this.config.onStateChange(newState);
    }
  }
}

export default MetricsWebSocketService;
