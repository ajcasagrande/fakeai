/**
 * KV Cache Dashboard Types
 */

export interface SpeedupStats {
  avg_baseline_ttft_ms: number;
  avg_actual_ttft_ms: number;
  avg_speedup_ratio: number;
  total_speedup_records: number;
}

export interface CachePerformance {
  cache_hit_rate: number;
  token_reuse_rate: number;
  total_cache_hits: number;
  total_cache_misses: number;
  total_tokens_processed: number;
  cached_tokens_reused: number;
  average_prefix_length: number;
  speedup_stats: SpeedupStats;
}

export interface WorkerStats {
  active_requests: number;
  total_requests: number;
  cached_blocks: number;
  tokens_processed: number;
}

export interface RadixTreeStats {
  total_nodes: number;
  total_cached_blocks: number;
}

export interface SmartRouter {
  workers: Record<string, WorkerStats>;
  radix_tree: RadixTreeStats;
}

export interface KVCacheData {
  cache_performance: CachePerformance;
  smart_router: SmartRouter;
}
