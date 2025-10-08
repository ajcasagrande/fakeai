/**
 * Production-ready WebSocket service with reconnection logic,
 * heartbeat mechanism, and event dispatching
 */

import {
  ConnectionState,
  MessageType,
  WebSocketMessage,
  WebSocketConfig,
  ConnectionInfo,
  WebSocketEventHandlers,
  MessageCallback,
  Subscription,
  IWebSocketService,
} from './types';

/**
 * Default configuration values
 */
const DEFAULT_CONFIG: Partial<WebSocketConfig> = {
  reconnectInterval: 1000,
  maxReconnectInterval: 30000,
  reconnectDecay: 1.5,
  maxReconnectAttempts: Infinity,
  heartbeatInterval: 30000,
  heartbeatTimeout: 5000,
  debug: false,
  autoConnect: true,
};

/**
 * WebSocket service class with robust error handling and reconnection
 */
export class WebSocketService implements IWebSocketService {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private state: ConnectionState = ConnectionState.DISCONNECTED;
  private eventHandlers: WebSocketEventHandlers = {};

  // Subscription management
  private subscriptions: Map<string, { type: MessageType; callback: MessageCallback }> = new Map();
  private subscriptionCounter = 0;

  // Reconnection logic
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private shouldReconnect = true;

  // Heartbeat mechanism
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private heartbeatTimeoutTimer: NodeJS.Timeout | null = null;
  private lastHeartbeatTime: number | null = null;

  // Connection info
  private connectionInfo: ConnectionInfo = {
    state: ConnectionState.DISCONNECTED,
    connectedAt: null,
    disconnectedAt: null,
    reconnectAttempts: 0,
    lastError: null,
    latency: null,
    messageCount: 0,
    bytesReceived: 0,
    bytesSent: 0,
  };

  // Message queue for offline messages
  private messageQueue: any[] = [];
  private maxQueueSize = 100;

  // Sequence tracking for message ordering
  private lastSequence = 0;

  constructor(config: WebSocketConfig, handlers?: WebSocketEventHandlers) {
    this.config = { ...DEFAULT_CONFIG, ...config } as Required<WebSocketConfig>;
    this.eventHandlers = handlers || {};

    if (this.config.autoConnect) {
      this.connect();
    }
  }

  /**
   * Establish WebSocket connection
   */
  public connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN || this.ws?.readyState === WebSocket.CONNECTING) {
      this.log('WebSocket already connected or connecting');
      return;
    }

    try {
      this.log(`Connecting to ${this.config.url}`);
      this.setState(ConnectionState.CONNECTING);

      const protocols = this.config.protocols;
      this.ws = protocols
        ? new WebSocket(this.config.url, protocols)
        : new WebSocket(this.config.url);

      this.setupEventListeners();
    } catch (error) {
      this.handleError(error as Error);
      this.scheduleReconnect();
    }
  }

  /**
   * Close WebSocket connection
   */
  public disconnect(): void {
    this.log('Disconnecting WebSocket');
    this.shouldReconnect = false;
    this.clearTimers();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
      this.ws = null;
    }

    this.setState(ConnectionState.DISCONNECTED);
    this.connectionInfo.disconnectedAt = Date.now();
  }

  /**
   * Send message through WebSocket
   */
  public send(message: any): boolean {
    if (!this.isConnected()) {
      this.log('WebSocket not connected, queuing message');

      if (this.messageQueue.length < this.maxQueueSize) {
        this.messageQueue.push(message);
        return false;
      } else {
        this.log('Message queue full, dropping message');
        return false;
      }
    }

    try {
      const payload = typeof message === 'string' ? message : JSON.stringify(message);
      this.ws!.send(payload);
      this.connectionInfo.bytesSent += payload.length;
      this.log(`Sent message: ${payload.substring(0, 100)}...`);
      return true;
    } catch (error) {
      this.handleError(error as Error);
      return false;
    }
  }

  /**
   * Subscribe to specific message types
   */
  public subscribe<T = any>(type: MessageType, callback: MessageCallback<T>): Subscription {
    const id = `sub_${this.subscriptionCounter++}`;
    this.subscriptions.set(id, { type, callback: callback as MessageCallback });

    this.log(`Subscribed to ${type} with id ${id}`);

    return {
      id,
      type,
      unsubscribe: () => this.unsubscribe(id),
    };
  }

  /**
   * Unsubscribe from messages
   */
  public unsubscribe(subscriptionId: string): void {
    if (this.subscriptions.delete(subscriptionId)) {
      this.log(`Unsubscribed ${subscriptionId}`);
    }
  }

  /**
   * Get current connection info
   */
  public getConnectionInfo(): ConnectionInfo {
    return { ...this.connectionInfo, state: this.state };
  }

  /**
   * Check if connected
   */
  public isConnected(): boolean {
    return this.state === ConnectionState.CONNECTED && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get current connection state
   */
  public getState(): ConnectionState {
    return this.state;
  }

  /**
   * Set connection state and notify handlers
   */
  private setState(state: ConnectionState): void {
    if (this.state !== state) {
      this.log(`State transition: ${this.state} -> ${state}`);
      this.state = state;
      this.connectionInfo.state = state;
    }
  }

  /**
   * Setup WebSocket event listeners
   */
  private setupEventListeners(): void {
    if (!this.ws) return;

    this.ws.onopen = this.handleOpen.bind(this);
    this.ws.onclose = this.handleClose.bind(this);
    this.ws.onerror = this.handleWebSocketError.bind(this);
    this.ws.onmessage = this.handleMessage.bind(this);
  }

  /**
   * Handle WebSocket open event
   */
  private handleOpen(): void {
    this.log('WebSocket connected');
    this.setState(ConnectionState.CONNECTED);
    this.reconnectAttempts = 0;
    this.connectionInfo.connectedAt = Date.now();
    this.connectionInfo.reconnectAttempts = 0;
    this.connectionInfo.lastError = null;

    // Start heartbeat
    this.startHeartbeat();

    // Process queued messages
    this.processMessageQueue();

    // Notify handlers
    if (this.eventHandlers.onConnect) {
      this.eventHandlers.onConnect();
    }

    if (this.reconnectAttempts > 0 && this.eventHandlers.onReconnected) {
      this.eventHandlers.onReconnected();
    }
  }

  /**
   * Handle WebSocket close event
   */
  private handleClose(event: CloseEvent): void {
    this.log(`WebSocket closed: ${event.code} - ${event.reason}`);
    this.setState(ConnectionState.DISCONNECTED);
    this.connectionInfo.disconnectedAt = Date.now();
    this.clearTimers();

    // Notify handlers
    if (this.eventHandlers.onDisconnect) {
      this.eventHandlers.onDisconnect(event.reason || 'Connection closed');
    }

    // Attempt reconnection if not intentionally closed
    if (this.shouldReconnect && event.code !== 1000) {
      this.scheduleReconnect();
    }
  }

  /**
   * Handle WebSocket error event
   */
  private handleWebSocketError(event: Event): void {
    const error = new Error('WebSocket error occurred');
    this.handleError(error);
  }

  /**
   * Handle WebSocket message event
   */
  private handleMessage(event: MessageEvent): void {
    try {
      this.connectionInfo.messageCount++;
      this.connectionInfo.bytesReceived += event.data.length;

      const message: WebSocketMessage = JSON.parse(event.data);
      this.log(`Received message: ${message.type}`);

      // Update sequence tracking
      if (message.sequence !== undefined) {
        if (message.sequence <= this.lastSequence) {
          this.log(`Out of order message detected: ${message.sequence} <= ${this.lastSequence}`);
        }
        this.lastSequence = message.sequence;
      }

      // Handle special message types
      switch (message.type) {
        case MessageType.HEARTBEAT:
          this.handleHeartbeat();
          break;
        case MessageType.PONG:
          this.handlePong(message);
          break;
        default:
          // Dispatch to subscribers
          this.dispatchMessage(message);
      }

      // Notify global message handler
      if (this.eventHandlers.onMessage) {
        this.eventHandlers.onMessage(message);
      }
    } catch (error) {
      this.log(`Failed to parse message: ${error}`);
      this.handleError(error as Error);
    }
  }

  /**
   * Dispatch message to subscribers
   */
  private dispatchMessage(message: WebSocketMessage): void {
    this.subscriptions.forEach((subscription) => {
      if (subscription.type === message.type) {
        try {
          subscription.callback(message.data, message);
        } catch (error) {
          this.log(`Error in subscription callback: ${error}`);
        }
      }
    });
  }

  /**
   * Handle error
   */
  private handleError(error: Error): void {
    this.log(`Error: ${error.message}`);
    this.setState(ConnectionState.ERROR);
    this.connectionInfo.lastError = error;

    if (this.eventHandlers.onError) {
      this.eventHandlers.onError(error);
    }
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(): void {
    if (!this.shouldReconnect) {
      return;
    }

    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      this.log('Max reconnect attempts reached');
      this.shouldReconnect = false;

      if (this.eventHandlers.onMaxReconnectAttemptsReached) {
        this.eventHandlers.onMaxReconnectAttemptsReached();
      }
      return;
    }

    this.setState(ConnectionState.RECONNECTING);
    this.reconnectAttempts++;
    this.connectionInfo.reconnectAttempts = this.reconnectAttempts;

    // Calculate backoff delay with exponential growth
    const baseDelay = this.config.reconnectInterval;
    const maxDelay = this.config.maxReconnectInterval;
    const delay = Math.min(
      baseDelay * Math.pow(this.config.reconnectDecay, this.reconnectAttempts - 1),
      maxDelay
    );

    this.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    if (this.eventHandlers.onReconnecting) {
      this.eventHandlers.onReconnecting(this.reconnectAttempts);
    }

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Start heartbeat mechanism
   */
  private startHeartbeat(): void {
    this.clearHeartbeatTimers();

    this.heartbeatTimer = setInterval(() => {
      this.sendHeartbeat();
    }, this.config.heartbeatInterval);

    // Send initial heartbeat
    this.sendHeartbeat();
  }

  /**
   * Send heartbeat/ping message
   */
  private sendHeartbeat(): void {
    if (!this.isConnected()) {
      return;
    }

    this.lastHeartbeatTime = Date.now();

    const pingMessage = {
      type: MessageType.HEARTBEAT,
      timestamp: this.lastHeartbeatTime,
      data: { client_time: this.lastHeartbeatTime },
    };

    this.send(pingMessage);

    // Set timeout for heartbeat response
    this.heartbeatTimeoutTimer = setTimeout(() => {
      this.log('Heartbeat timeout - connection may be dead');
      this.handleError(new Error('Heartbeat timeout'));
      this.ws?.close();
    }, this.config.heartbeatTimeout);
  }

  /**
   * Handle heartbeat response
   */
  private handleHeartbeat(): void {
    this.clearHeartbeatTimeout();
  }

  /**
   * Handle pong message and calculate latency
   */
  private handlePong(message: WebSocketMessage): void {
    this.clearHeartbeatTimeout();

    if (this.lastHeartbeatTime) {
      const latency = Date.now() - this.lastHeartbeatTime;
      this.connectionInfo.latency = latency;
      this.log(`Latency: ${latency}ms`);
    }
  }

  /**
   * Process queued messages
   */
  private processMessageQueue(): void {
    if (this.messageQueue.length === 0) {
      return;
    }

    this.log(`Processing ${this.messageQueue.length} queued messages`);

    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      this.send(message);
    }
  }

  /**
   * Clear all timers
   */
  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.clearHeartbeatTimers();
  }

  /**
   * Clear heartbeat timers
   */
  private clearHeartbeatTimers(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    this.clearHeartbeatTimeout();
  }

  /**
   * Clear heartbeat timeout
   */
  private clearHeartbeatTimeout(): void {
    if (this.heartbeatTimeoutTimer) {
      clearTimeout(this.heartbeatTimeoutTimer);
      this.heartbeatTimeoutTimer = null;
    }
  }

  /**
   * Log debug messages
   */
  private log(message: string): void {
    if (this.config.debug) {
      console.log(`[WebSocketService] ${message}`);
    }
  }

  /**
   * Destroy service and cleanup
   */
  public destroy(): void {
    this.log('Destroying WebSocket service');
    this.disconnect();
    this.subscriptions.clear();
    this.messageQueue = [];
  }
}

/**
 * Create WebSocket service instance
 */
export function createWebSocketService(
  config: WebSocketConfig,
  handlers?: WebSocketEventHandlers
): WebSocketService {
  return new WebSocketService(config, handlers);
}
