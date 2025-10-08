/**
 * TypeScript type definitions for WebSocket real-time updates
 */

/**
 * WebSocket connection states
 */
export enum ConnectionState {
  CONNECTING = 'CONNECTING',
  CONNECTED = 'CONNECTED',
  DISCONNECTED = 'DISCONNECTED',
  RECONNECTING = 'RECONNECTING',
  ERROR = 'ERROR',
  CLOSED = 'CLOSED',
}

/**
 * WebSocket message types
 */
export enum MessageType {
  METRICS_UPDATE = 'metrics_update',
  MODEL_UPDATE = 'model_update',
  REQUEST_UPDATE = 'request_update',
  ERROR_UPDATE = 'error_update',
  SYSTEM_UPDATE = 'system_update',
  HEARTBEAT = 'heartbeat',
  PONG = 'pong',
  INIT = 'init',
  RATE_LIMIT_UPDATE = 'rate_limit_update',
  COST_UPDATE = 'cost_update',
  KV_CACHE_UPDATE = 'kv_cache_update',
}

/**
 * Base WebSocket message structure
 */
export interface WebSocketMessage<T = any> {
  type: MessageType;
  timestamp: number;
  data: T;
  sequence?: number;
  metadata?: Record<string, any>;
}

/**
 * Metrics update payload
 */
export interface MetricsUpdatePayload {
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  avg_latency_ms: number;
  error_rate: number;
  streaming_percentage: number;
  requests_per_second: number;
  tokens_per_second: number;
  active_connections: number;
}

/**
 * Model update payload
 */
export interface ModelUpdatePayload {
  model: string;
  request_count: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_latency_ms: number;
  error_count: number;
  avg_latency_ms: number;
  error_rate: number;
  total_cost: number;
  tokens_per_second: number;
}

/**
 * Request update payload
 */
export interface RequestUpdatePayload {
  id: string;
  model: string;
  created: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  latency_ms: number;
  streaming: boolean;
  status: 'success' | 'error' | 'in_progress';
  error_message?: string;
  cost: number;
  user_id?: string;
  organization_id?: string;
}

/**
 * Error update payload
 */
export interface ErrorUpdatePayload {
  error_type: string;
  error_message: string;
  model?: string;
  timestamp: number;
  stack_trace?: string;
  request_id?: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

/**
 * System update payload
 */
export interface SystemUpdatePayload {
  cpu_usage: number;
  memory_usage: number;
  gpu_usage?: number;
  gpu_memory_usage?: number;
  disk_usage: number;
  network_in_bytes: number;
  network_out_bytes: number;
  active_workers: number;
  queue_size: number;
}

/**
 * Rate limit update payload
 */
export interface RateLimitUpdatePayload {
  endpoint: string;
  limit: number;
  remaining: number;
  reset_time: number;
  percentage_used: number;
}

/**
 * Cost update payload
 */
export interface CostUpdatePayload {
  period: 'hour' | 'day' | 'week' | 'month';
  total_cost: number;
  breakdown_by_model: Record<string, number>;
  breakdown_by_service: Record<string, number>;
  projected_monthly_cost: number;
}

/**
 * KV Cache update payload
 */
export interface KVCacheUpdatePayload {
  cache_hits: number;
  cache_misses: number;
  hit_rate: number;
  cache_size_bytes: number;
  cache_entries: number;
  evictions: number;
  avg_lookup_time_ms: number;
}

/**
 * Heartbeat payload
 */
export interface HeartbeatPayload {
  server_time: number;
  uptime_seconds: number;
}

/**
 * WebSocket configuration options
 */
export interface WebSocketConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectInterval?: number;
  reconnectDecay?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  heartbeatTimeout?: number;
  debug?: boolean;
  protocols?: string | string[];
  autoConnect?: boolean;
}

/**
 * WebSocket connection info
 */
export interface ConnectionInfo {
  state: ConnectionState;
  connectedAt: number | null;
  disconnectedAt: number | null;
  reconnectAttempts: number;
  lastError: Error | null;
  latency: number | null;
  messageCount: number;
  bytesReceived: number;
  bytesSent: number;
}

/**
 * WebSocket event handlers
 */
export interface WebSocketEventHandlers {
  onConnect?: () => void;
  onDisconnect?: (reason: string) => void;
  onError?: (error: Error) => void;
  onMessage?: (message: WebSocketMessage) => void;
  onReconnecting?: (attempt: number) => void;
  onReconnected?: () => void;
  onMaxReconnectAttemptsReached?: () => void;
}

/**
 * Message subscription callback
 */
export type MessageCallback<T = any> = (data: T, message: WebSocketMessage<T>) => void;

/**
 * Subscription handle for unsubscribing
 */
export interface Subscription {
  id: string;
  type: MessageType;
  unsubscribe: () => void;
}

/**
 * WebSocket service interface
 */
export interface IWebSocketService {
  connect(): void;
  disconnect(): void;
  send(message: any): boolean;
  subscribe<T = any>(type: MessageType, callback: MessageCallback<T>): Subscription;
  unsubscribe(subscriptionId: string): void;
  getConnectionInfo(): ConnectionInfo;
  isConnected(): boolean;
  getState(): ConnectionState;
}

/**
 * Real-time metrics hook state
 */
export interface RealtimeMetricsState {
  metrics: MetricsUpdatePayload | null;
  models: Map<string, ModelUpdatePayload>;
  recentRequests: RequestUpdatePayload[];
  recentErrors: ErrorUpdatePayload[];
  systemStats: SystemUpdatePayload | null;
  rateLimits: Map<string, RateLimitUpdatePayload>;
  costs: CostUpdatePayload | null;
  kvCache: KVCacheUpdatePayload | null;
  isConnected: boolean;
  connectionState: ConnectionState;
  lastUpdate: number | null;
}

/**
 * WebSocket context value
 */
export interface WebSocketContextValue {
  service: IWebSocketService | null;
  connectionInfo: ConnectionInfo;
  subscribe: <T = any>(type: MessageType, callback: MessageCallback<T>) => Subscription;
  send: (message: any) => boolean;
  connect: () => void;
  disconnect: () => void;
}
