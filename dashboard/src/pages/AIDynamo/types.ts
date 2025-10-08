/**
 * NVIDIA AI-Dynamo Dashboard Types
 *
 * Type definitions for NVIDIA AI-Dynamo LLM inference serving system.
 * AI-Dynamo tracks comprehensive performance metrics for LLM inference workloads
 * including latency breakdowns, throughput, KV cache efficiency, and request lifecycles.
 */

// ============================================================================
// Core Metrics Overview
// ============================================================================

export interface AIDynamoMetrics {
  // Request metrics
  request_count: number;
  success_rate: number;
  error_count: number;

  // Latency statistics (in milliseconds)
  latency: {
    total: LatencyPercentiles;
    queue: LatencyPercentiles;
    prefill: LatencyPercentiles;
    decode: LatencyPercentiles;
    ttft: LatencyPercentiles;  // Time to First Token
    tpot: LatencyPercentiles;  // Time per Output Token
    itl: LatencyPercentiles;   // Inter-Token Latency (same as TPOT)
  };

  // Throughput metrics
  throughput: {
    requests_per_sec: number;
    tokens_per_sec: number;
    input_tokens_per_sec: number;
    output_tokens_per_sec: number;
  };

  // Token statistics
  tokens: {
    total_input_tokens: number;
    total_output_tokens: number;
    total_cached_tokens: number;
    avg_input_tokens: number;
    avg_output_tokens: number;
    avg_cached_tokens: number;
  };

  // Queue metrics
  queue: {
    current_depth: number;
    max_depth: number;
    avg_wait_time_ms: number;
    total_queued_requests: number;
  };

  // KV Cache metrics
  kv_cache: {
    hit_rate: number;
    avg_blocks_matched: number;
    avg_overlap_score: number;
    total_cache_hits: number;
    total_cache_misses: number;
  };

  // Worker metrics
  workers: {
    total_workers: number;
    active_workers: number;
    avg_utilization: number;
    avg_routing_cost_ms: number;
  };
}

export interface LatencyPercentiles {
  p50: number;
  p95: number;
  p99: number;
  avg: number;
  min: number;
  max: number;
}

// ============================================================================
// Latency Breakdown
// ============================================================================

export interface LatencyBreakdownData {
  timestamp: number;
  queue_time_ms: number;
  prefill_time_ms: number;
  decode_time_ms: number;
  total_time_ms: number;
  request_id?: string;
}

export interface LatencyPhase {
  phase: 'queue' | 'prefill' | 'decode';
  duration_ms: number;
  percentage: number;
  color: string;
}

// ============================================================================
// Request Lifecycle
// ============================================================================

export interface RequestLifecycle {
  request_id: string;
  model: string;
  timestamp: number;

  // Lifecycle stages
  arrival_time: number;
  queue_entry_time: number;
  prefill_start_time: number;
  prefill_end_time: number;
  decode_start_time: number;
  decode_end_time: number;
  completion_time: number;

  // Durations
  queue_wait_ms: number;
  prefill_duration_ms: number;
  decode_duration_ms: number;
  total_duration_ms: number;

  // Token metrics
  input_tokens: number;
  output_tokens: number;
  cached_tokens: number;

  // Worker assignment
  worker_id: string;
  routing_cost_ms: number;

  // Status
  status: 'completed' | 'failed' | 'in_progress' | 'queued';
  error_message?: string;
}

// ============================================================================
// TTFT (Time to First Token) Metrics
// ============================================================================

export interface TTFTMetrics {
  timestamp: number;
  ttft_ms: number;
  request_id: string;
  model: string;
  input_tokens: number;
  cached_tokens: number;
}

export interface TTFTStats {
  avg_ttft_ms: number;
  p50_ttft_ms: number;
  p95_ttft_ms: number;
  p99_ttft_ms: number;
  samples_count: number;
  time_series: TTFTMetrics[];
}

// ============================================================================
// TPOT/ITL (Time per Output Token) Metrics
// ============================================================================

export interface TPOTMetrics {
  timestamp: number;
  tpot_ms: number;
  itl_ms: number;  // Same as TPOT
  request_id: string;
  model: string;
  output_tokens: number;
  decode_duration_ms: number;
}

export interface TPOTStats {
  avg_tpot_ms: number;
  p50_tpot_ms: number;
  p95_tpot_ms: number;
  p99_tpot_ms: number;
  samples_count: number;
  time_series: TPOTMetrics[];
}

// ============================================================================
// Throughput Metrics
// ============================================================================

export interface ThroughputData {
  timestamp: number;
  requests_per_sec: number;
  tokens_per_sec: number;
  input_tokens_per_sec: number;
  output_tokens_per_sec: number;
}

export interface ThroughputStats {
  current_rps: number;
  current_tps: number;
  peak_rps: number;
  peak_tps: number;
  avg_rps: number;
  avg_tps: number;
  time_series: ThroughputData[];
}

// ============================================================================
// Queue Metrics
// ============================================================================

export interface QueueSnapshot {
  timestamp: number;
  queue_depth: number;
  requests_waiting: number;
  avg_wait_time_ms: number;
  max_wait_time_ms: number;
}

export interface QueueStats {
  current_depth: number;
  max_depth: number;
  avg_depth: number;
  avg_wait_time_ms: number;
  p95_wait_time_ms: number;
  p99_wait_time_ms: number;
  total_queued: number;
  time_series: QueueSnapshot[];
}

// ============================================================================
// KV Cache Analytics
// ============================================================================

export interface KVCacheMetrics {
  timestamp: number;
  hit_rate: number;
  blocks_matched: number;
  overlap_score: number;
  cache_hits: number;
  cache_misses: number;
}

export interface KVCacheStats {
  overall_hit_rate: number;
  avg_blocks_matched: number;
  avg_overlap_score: number;
  total_hits: number;
  total_misses: number;
  cache_size_mb: number;
  cache_utilization: number;
  time_series: KVCacheMetrics[];
}

// ============================================================================
// Worker Metrics
// ============================================================================

export interface WorkerMetrics {
  worker_id: string;
  status: 'active' | 'idle' | 'offline';
  current_requests: number;
  total_requests_processed: number;
  utilization: number;
  avg_request_duration_ms: number;
  error_count: number;
  last_heartbeat: number;
}

export interface WorkerStats {
  total_workers: number;
  active_workers: number;
  idle_workers: number;
  avg_utilization: number;
  workers: WorkerMetrics[];
  routing_costs: {
    timestamp: number;
    worker_id: string;
    routing_cost_ms: number;
  }[];
}

// ============================================================================
// Token Statistics
// ============================================================================

export interface TokenStats {
  // Totals
  total_input_tokens: number;
  total_output_tokens: number;
  total_cached_tokens: number;
  total_tokens_processed: number;

  // Averages per request
  avg_input_tokens: number;
  avg_output_tokens: number;
  avg_cached_tokens: number;

  // Rates
  input_tokens_per_sec: number;
  output_tokens_per_sec: number;

  // Distribution
  input_token_distribution: {
    min: number;
    max: number;
    p50: number;
    p95: number;
    p99: number;
  };

  output_token_distribution: {
    min: number;
    max: number;
    p50: number;
    p95: number;
    p99: number;
  };

  // Time series
  time_series: {
    timestamp: number;
    input_tokens: number;
    output_tokens: number;
    cached_tokens: number;
  }[];
}

// ============================================================================
// Per-Model Performance
// ============================================================================

export interface ModelPerformance {
  model_name: string;

  // Request counts
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  success_rate: number;

  // Latency
  avg_total_latency_ms: number;
  avg_ttft_ms: number;
  avg_tpot_ms: number;
  avg_queue_time_ms: number;
  avg_prefill_time_ms: number;
  avg_decode_time_ms: number;

  // Throughput
  requests_per_sec: number;
  tokens_per_sec: number;

  // Tokens
  total_input_tokens: number;
  total_output_tokens: number;
  avg_input_tokens: number;
  avg_output_tokens: number;

  // KV Cache
  kv_cache_hit_rate: number;
  avg_cached_tokens: number;

  // Resource usage
  avg_worker_utilization: number;
  workers_assigned: number;
}

export interface PerModelStats {
  models: ModelPerformance[];
  total_models: number;
  most_used_model: string;
  best_performing_model: string;  // By latency
  highest_throughput_model: string;
}

// ============================================================================
// Historical Trends
// ============================================================================

export interface HistoricalTrend {
  timestamp: number;

  // Requests
  total_requests: number;
  successful_requests: number;
  failed_requests: number;

  // Latency
  avg_total_latency_ms: number;
  avg_ttft_ms: number;
  avg_tpot_ms: number;
  p95_total_latency_ms: number;

  // Throughput
  requests_per_sec: number;
  tokens_per_sec: number;

  // Queue
  avg_queue_depth: number;
  avg_queue_wait_ms: number;

  // KV Cache
  kv_cache_hit_rate: number;

  // Workers
  active_workers: number;
  avg_worker_utilization: number;
}

// ============================================================================
// Dashboard Data Container
// ============================================================================

export interface AIDynamoDashboardData {
  // Overview metrics
  metrics: AIDynamoMetrics;

  // Detailed breakdowns
  latency_breakdown: LatencyBreakdownData[];
  request_lifecycles: RequestLifecycle[];
  ttft_stats: TTFTStats;
  tpot_stats: TPOTStats;
  throughput_stats: ThroughputStats;
  queue_stats: QueueStats;
  kv_cache_stats: KVCacheStats;
  worker_stats: WorkerStats;
  token_stats: TokenStats;
  per_model_stats: PerModelStats;
  historical_trends: HistoricalTrend[];

  // Metadata
  timestamp: number;
  collection_window_seconds: number;
}

// ============================================================================
// Dashboard Filters
// ============================================================================

export interface DashboardFilters {
  model_name: string | null;
  worker_id: string | null;
  time_range: '5m' | '15m' | '1h' | '6h' | '24h' | '7d';
  aggregation: 'second' | 'minute' | 'hour' | 'day';
  status_filter: 'all' | 'success' | 'failed' | 'in_progress';
}

// ============================================================================
// Performance Alerts
// ============================================================================

export interface PerformanceAlert {
  id: string;
  severity: 'info' | 'warning' | 'critical';
  type: 'latency' | 'throughput' | 'queue' | 'error' | 'cache' | 'worker';
  message: string;
  timestamp: number;
  metric_name: string;
  current_value: number;
  threshold_value: number;
  recommendation: string;
}

// ============================================================================
// System Status
// ============================================================================

export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'critical' | 'offline';
  uptime_seconds: number;
  version: string;
  total_requests_served: number;
  active_alerts: PerformanceAlert[];
  last_health_check: number;
}
