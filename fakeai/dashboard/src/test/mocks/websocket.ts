/**
 * Mock WebSocket utilities for testing
 * Provides controllable WebSocket mock for testing real-time features
 */

import { vi } from 'vitest';
import { MessageType, WebSocketMessage } from '../../services/types';

/**
 * Mock WebSocket class with controllable behavior
 */
export class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  protocol: string = '';
  extensions: string = '';
  bufferedAmount: number = 0;
  binaryType: BinaryType = 'blob';

  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  private messageQueue: any[] = [];
  private autoConnect: boolean;
  private eventListeners: Map<string, Set<EventListener>> = new Map();

  constructor(url: string, protocols?: string | string[], autoConnect = true) {
    this.url = url;
    this.autoConnect = autoConnect;

    if (autoConnect) {
      // Simulate async connection
      setTimeout(() => this.simulateOpen(), 0);
    }
  }

  send = vi.fn((data: any) => {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
    this.messageQueue.push(data);
  });

  close = vi.fn((code?: number, reason?: string) => {
    this.readyState = MockWebSocket.CLOSING;
    setTimeout(() => this.simulateClose(code, reason), 0);
  });

  addEventListener = vi.fn((type: string, listener: EventListener) => {
    if (!this.eventListeners.has(type)) {
      this.eventListeners.set(type, new Set());
    }
    this.eventListeners.get(type)!.add(listener);
  });

  removeEventListener = vi.fn((type: string, listener: EventListener) => {
    const listeners = this.eventListeners.get(type);
    if (listeners) {
      listeners.delete(listener);
    }
  });

  dispatchEvent = vi.fn((event: Event): boolean => {
    const listeners = this.eventListeners.get(event.type);
    if (listeners) {
      listeners.forEach(listener => listener(event));
      return true;
    }
    return false;
  });

  // Test utilities

  /**
   * Simulate WebSocket opening
   */
  simulateOpen(): void {
    this.readyState = MockWebSocket.OPEN;
    const event = new Event('open');

    if (this.onopen) {
      this.onopen(event);
    }
    this.dispatchEvent(event);
  }

  /**
   * Simulate WebSocket closing
   */
  simulateClose(code = 1000, reason = 'Normal closure'): void {
    this.readyState = MockWebSocket.CLOSED;
    const event = new CloseEvent('close', { code, reason });

    if (this.onclose) {
      this.onclose(event);
    }
    this.dispatchEvent(event);
  }

  /**
   * Simulate WebSocket error
   */
  simulateError(error?: Event): void {
    const errorEvent = error || new Event('error');

    if (this.onerror) {
      this.onerror(errorEvent);
    }
    this.dispatchEvent(errorEvent);
  }

  /**
   * Simulate receiving a message
   */
  simulateMessage(data: any): void {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('Cannot send message: WebSocket is not open');
    }

    const event = new MessageEvent('message', { data: JSON.stringify(data) });

    if (this.onmessage) {
      this.onmessage(event);
    }
    this.dispatchEvent(event);
  }

  /**
   * Get messages that were sent
   */
  getSentMessages(): any[] {
    return this.messageQueue.map(msg =>
      typeof msg === 'string' ? JSON.parse(msg) : msg
    );
  }

  /**
   * Get last sent message
   */
  getLastSentMessage(): any {
    const messages = this.getSentMessages();
    return messages[messages.length - 1];
  }

  /**
   * Clear sent messages
   */
  clearSentMessages(): void {
    this.messageQueue = [];
  }

  /**
   * Wait for connection to open
   */
  async waitForOpen(timeout = 1000): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.readyState === MockWebSocket.OPEN) {
        resolve();
        return;
      }

      const timer = setTimeout(() => {
        reject(new Error('WebSocket connection timeout'));
      }, timeout);

      const openHandler = () => {
        clearTimeout(timer);
        resolve();
      };

      this.addEventListener('open', openHandler);
    });
  }
}

/**
 * Create a mock WebSocket instance
 */
export function createMockWebSocket(
  url: string,
  options?: {
    autoConnect?: boolean;
    protocols?: string | string[];
  }
): MockWebSocket {
  return new MockWebSocket(url, options?.protocols, options?.autoConnect);
}

/**
 * Mock WebSocket message factory
 */
export function createWebSocketMessage(
  type: MessageType,
  data?: any,
  overrides?: Partial<WebSocketMessage>
): WebSocketMessage {
  return {
    type,
    data: data || {},
    timestamp: Date.now(),
    ...overrides,
  };
}

/**
 * Create mock metrics update message
 */
export function createMetricsUpdateMessage(metrics: any): WebSocketMessage {
  return createWebSocketMessage(MessageType.METRICS_UPDATE, metrics);
}

/**
 * Create mock request update message
 */
export function createRequestUpdateMessage(request: any): WebSocketMessage {
  return createWebSocketMessage(MessageType.REQUEST_UPDATE, request);
}

/**
 * Create mock error message
 */
export function createErrorMessage(error: string | Error): WebSocketMessage {
  return createWebSocketMessage(MessageType.ERROR, {
    message: error instanceof Error ? error.message : error,
    timestamp: Date.now(),
  });
}

/**
 * Create mock heartbeat message
 */
export function createHeartbeatMessage(): WebSocketMessage {
  return createWebSocketMessage(MessageType.HEARTBEAT, {
    client_time: Date.now(),
  });
}

/**
 * Create mock pong message
 */
export function createPongMessage(clientTime: number): WebSocketMessage {
  return createWebSocketMessage(MessageType.PONG, {
    client_time: clientTime,
    server_time: Date.now(),
  });
}

/**
 * Mock WebSocket server for testing
 */
export class MockWebSocketServer {
  private clients: Set<MockWebSocket> = new Set();
  private messageHandlers: Map<MessageType, Function[]> = new Map();

  /**
   * Register a client connection
   */
  registerClient(client: MockWebSocket): void {
    this.clients.add(client);
  }

  /**
   * Unregister a client
   */
  unregisterClient(client: MockWebSocket): void {
    this.clients.delete(client);
  }

  /**
   * Broadcast message to all clients
   */
  broadcast(message: WebSocketMessage): void {
    this.clients.forEach(client => {
      if (client.readyState === MockWebSocket.OPEN) {
        client.simulateMessage(message);
      }
    });
  }

  /**
   * Send message to specific client
   */
  sendToClient(client: MockWebSocket, message: WebSocketMessage): void {
    if (client.readyState === MockWebSocket.OPEN) {
      client.simulateMessage(message);
    }
  }

  /**
   * Handle message from client
   */
  onMessage(type: MessageType, handler: Function): void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type)!.push(handler);
  }

  /**
   * Simulate client message
   */
  simulateClientMessage(client: MockWebSocket, message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => handler(message, client));
    }
  }

  /**
   * Close all connections
   */
  closeAll(code?: number, reason?: string): void {
    this.clients.forEach(client => client.close(code, reason));
    this.clients.clear();
  }

  /**
   * Get number of connected clients
   */
  getClientCount(): number {
    return this.clients.size;
  }
}

/**
 * Create a mock WebSocket server
 */
export function createMockWebSocketServer(): MockWebSocketServer {
  return new MockWebSocketServer();
}

/**
 * Setup global WebSocket mock
 */
export function setupWebSocketMock(): void {
  (global as any).WebSocket = MockWebSocket;
}

/**
 * Restore original WebSocket
 */
export function restoreWebSocket(): void {
  // This would restore the original WebSocket if we saved it
  // In tests, the mock is already set up in setup.ts
}
