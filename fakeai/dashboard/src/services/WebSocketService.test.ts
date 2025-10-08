/**
 * Tests for WebSocketService
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { WebSocketService } from './WebSocketService';
import { ConnectionState, MessageType } from './types';
import {
  MockWebSocket,
  createWebSocketMessage,
  createMetricsUpdateMessage,
} from '@test/mocks/websocket';

// Replace global WebSocket with mock
global.WebSocket = MockWebSocket as any;

describe('WebSocketService', () => {
  let service: WebSocketService;
  const wsUrl = 'ws://localhost:8000/ws';

  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    if (service) {
      service.destroy();
    }
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  describe('Connection Management', () => {
    it('connects automatically when autoConnect is true', () => {
      service = new WebSocketService({
        url: wsUrl,
        autoConnect: true,
      });

      expect(service.getState()).toBe(ConnectionState.CONNECTING);
    });

    it('does not connect automatically when autoConnect is false', () => {
      service = new WebSocketService({
        url: wsUrl,
        autoConnect: false,
      });

      expect(service.getState()).toBe(ConnectionState.DISCONNECTED);
    });

    it('transitions to connected state after opening', async () => {
      const onConnect = vi.fn();

      service = new WebSocketService(
        {
          url: wsUrl,
          autoConnect: true,
        },
        { onConnect }
      );

      // Fast-forward timers to simulate connection
      await vi.runAllTimersAsync();

      expect(service.getState()).toBe(ConnectionState.CONNECTED);
      expect(onConnect).toHaveBeenCalled();
    });

    it('handles manual connection', () => {
      service = new WebSocketService({
        url: wsUrl,
        autoConnect: false,
      });

      service.connect();

      expect(service.getState()).toBe(ConnectionState.CONNECTING);
    });

    it('handles disconnection', async () => {
      const onDisconnect = vi.fn();

      service = new WebSocketService(
        {
          url: wsUrl,
          autoConnect: true,
        },
        { onDisconnect }
      );

      await vi.runAllTimersAsync();

      service.disconnect();

      expect(service.getState()).toBe(ConnectionState.DISCONNECTED);
      expect(onDisconnect).toHaveBeenCalled();
    });

    it('prevents multiple simultaneous connections', async () => {
      service = new WebSocketService({
        url: wsUrl,
        autoConnect: true,
      });

      await vi.runAllTimersAsync();

      // Try to connect again
      service.connect();

      // Should still be in connected state, not reconnecting
      expect(service.getState()).toBe(ConnectionState.CONNECTED);
    });
  });

  describe('Message Handling', () => {
    beforeEach(async () => {
      service = new WebSocketService({
        url: wsUrl,
        autoConnect: true,
      });

      await vi.runAllTimersAsync();
    });

    it('sends messages when connected', () => {
      const message = { type: 'test', data: { value: 123 } };
      const result = service.send(message);

      expect(result).toBe(true);
    });

    it('queues messages when disconnected', () => {
      service.disconnect();

      const message = { type: 'test', data: { value: 123 } };
      const result = service.send(message);

      expect(result).toBe(false);
    });

    it('processes queued messages after reconnection', async () => {
      service.disconnect();

      // Queue messages while disconnected
      service.send({ type: 'msg1' });
      service.send({ type: 'msg2' });

      // Reconnect
      service.connect();
      await vi.runAllTimersAsync();

      // Messages should be sent
      const info = service.getConnectionInfo();
      expect(info.bytesSent).toBeGreaterThan(0);
    });

    it('subscribes to specific message types', async () => {
      const callback = vi.fn();

      const subscription = service.subscribe(MessageType.METRICS_UPDATE, callback);

      expect(subscription).toHaveProperty('id');
      expect(subscription).toHaveProperty('unsubscribe');
    });

    it('calls subscription callback when message received', async () => {
      const callback = vi.fn();

      service.subscribe(MessageType.METRICS_UPDATE, callback);

      // Simulate receiving a message
      const message = createMetricsUpdateMessage({ test: 'data' });
      (service as any).handleMessage({
        data: JSON.stringify(message),
      });

      expect(callback).toHaveBeenCalledWith(
        message.data,
        expect.objectContaining({ type: MessageType.METRICS_UPDATE })
      );
    });

    it('unsubscribes from messages', async () => {
      const callback = vi.fn();

      const subscription = service.subscribe(MessageType.METRICS_UPDATE, callback);
      subscription.unsubscribe();

      // Simulate receiving a message
      const message = createMetricsUpdateMessage({ test: 'data' });
      (service as any).handleMessage({
        data: JSON.stringify(message),
      });

      expect(callback).not.toHaveBeenCalled();
    });
  });

  describe('Reconnection Logic', () => {
    it('attempts reconnection after connection loss', async () => {
      const onReconnecting = vi.fn();

      service = new WebSocketService(
        {
          url: wsUrl,
          autoConnect: true,
          reconnectInterval: 1000,
        },
        { onReconnecting }
      );

      await vi.runAllTimersAsync();

      // Simulate connection loss
      (service as any).handleClose({ code: 1006, reason: 'Connection lost' });

      // Fast-forward to reconnection attempt
      await vi.advanceTimersByTimeAsync(1000);

      expect(onReconnecting).toHaveBeenCalled();
      expect(service.getState()).toBe(ConnectionState.RECONNECTING);
    });

    it('uses exponential backoff for reconnection', async () => {
      service = new WebSocketService({
        url: wsUrl,
        autoConnect: true,
        reconnectInterval: 1000,
        reconnectDecay: 2,
      });

      await vi.runAllTimersAsync();

      // Simulate multiple connection failures
      for (let i = 0; i < 3; i++) {
        (service as any).handleClose({ code: 1006, reason: 'Connection lost' });
        await vi.runAllTimersAsync();
      }

      const info = service.getConnectionInfo();
      expect(info.reconnectAttempts).toBe(3);
    });

    it('stops reconnecting after max attempts', async () => {
      const onMaxReconnectAttemptsReached = vi.fn();

      service = new WebSocketService(
        {
          url: wsUrl,
          autoConnect: true,
          reconnectInterval: 100,
          maxReconnectAttempts: 3,
        },
        { onMaxReconnectAttemptsReached }
      );

      await vi.runAllTimersAsync();

      // Simulate connection failures
      for (let i = 0; i < 4; i++) {
        (service as any).handleClose({ code: 1006, reason: 'Connection lost' });
        await vi.runAllTimersAsync();
      }

      expect(onMaxReconnectAttemptsReached).toHaveBeenCalled();
    });

    it('does not reconnect after intentional disconnect', async () => {
      service = new WebSocketService({
        url: wsUrl,
        autoConnect: true,
      });

      await vi.runAllTimersAsync();

      service.disconnect();
      await vi.runAllTimersAsync();

      expect(service.getState()).toBe(ConnectionState.DISCONNECTED);
    });
  });

  describe('Heartbeat Mechanism', () => {
    it('sends heartbeat messages periodically', async () => {
      service = new WebSocketService({
        url: wsUrl,
        autoConnect: true,
        heartbeatInterval: 1000,
      });

      await vi.runAllTimersAsync();

      // Advance time to trigger heartbeat
      await vi.advanceTimersByTimeAsync(1000);

      const info = service.getConnectionInfo();
      expect(info.bytesSent).toBeGreaterThan(0);
    });

    it('detects connection timeout when heartbeat fails', async () => {
      const onError = vi.fn();

      service = new WebSocketService(
        {
          url: wsUrl,
          autoConnect: true,
          heartbeatInterval: 1000,
          heartbeatTimeout: 500,
        },
        { onError }
      );

      await vi.runAllTimersAsync();

      // Trigger heartbeat but don't respond
      await vi.advanceTimersByTimeAsync(1000);
      await vi.advanceTimersByTimeAsync(500);

      expect(onError).toHaveBeenCalled();
    });

    it('calculates latency from heartbeat response', async () => {
      service = new WebSocketService({
        url: wsUrl,
        autoConnect: true,
        heartbeatInterval: 1000,
      });

      await vi.runAllTimersAsync();

      // Simulate heartbeat/pong exchange
      const pongMessage = createWebSocketMessage(MessageType.PONG, {
        client_time: Date.now() - 50,
        server_time: Date.now(),
      });

      (service as any).handleMessage({
        data: JSON.stringify(pongMessage),
      });

      const info = service.getConnectionInfo();
      expect(info.latency).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Error Handling', () => {
    it('handles connection errors', async () => {
      const onError = vi.fn();

      service = new WebSocketService(
        {
          url: wsUrl,
          autoConnect: true,
        },
        { onError }
      );

      await vi.runAllTimersAsync();

      // Simulate error
      const error = new Error('Connection failed');
      (service as any).handleError(error);

      expect(onError).toHaveBeenCalledWith(error);
      expect(service.getState()).toBe(ConnectionState.ERROR);
    });

    it('handles malformed messages', async () => {
      const onError = vi.fn();

      service = new WebSocketService(
        {
          url: wsUrl,
          autoConnect: true,
        },
        { onError }
      );

      await vi.runAllTimersAsync();

      // Simulate malformed message
      (service as any).handleMessage({
        data: 'invalid json',
      });

      expect(onError).toHaveBeenCalled();
    });
  });

  describe('Connection Info', () => {
    it('tracks connection statistics', async () => {
      service = new WebSocketService({
        url: wsUrl,
        autoConnect: true,
      });

      await vi.runAllTimersAsync();

      const info = service.getConnectionInfo();

      expect(info).toHaveProperty('state');
      expect(info).toHaveProperty('connectedAt');
      expect(info).toHaveProperty('messageCount');
      expect(info).toHaveProperty('bytesReceived');
      expect(info).toHaveProperty('bytesSent');
    });

    it('updates message count on received messages', async () => {
      service = new WebSocketService({
        url: wsUrl,
        autoConnect: true,
      });

      await vi.runAllTimersAsync();

      // Simulate receiving messages
      const message = createWebSocketMessage(MessageType.METRICS_UPDATE, {});
      (service as any).handleMessage({
        data: JSON.stringify(message),
      });

      const info = service.getConnectionInfo();
      expect(info.messageCount).toBe(1);
    });
  });

  describe('Cleanup', () => {
    it('cleans up resources on destroy', async () => {
      service = new WebSocketService({
        url: wsUrl,
        autoConnect: true,
      });

      await vi.runAllTimersAsync();

      service.destroy();

      expect(service.getState()).toBe(ConnectionState.DISCONNECTED);
    });

    it('clears all subscriptions on destroy', async () => {
      service = new WebSocketService({
        url: wsUrl,
        autoConnect: true,
      });

      await vi.runAllTimersAsync();

      const callback = vi.fn();
      service.subscribe(MessageType.METRICS_UPDATE, callback);

      service.destroy();

      // Try to send message after destroy
      const message = createMetricsUpdateMessage({ test: 'data' });
      (service as any).handleMessage({
        data: JSON.stringify(message),
      });

      expect(callback).not.toHaveBeenCalled();
    });
  });
});
