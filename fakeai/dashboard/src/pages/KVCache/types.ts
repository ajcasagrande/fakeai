/**
 * TypeScript type definitions for KV Cache Analytics Dashboard
 */

export interface KVCacheMetrics {
  cache_hit_rate: number;
  cache_miss_rate: number;
  total_cache_hits: number;
  total_cache_misses: number;
  cache_size_bytes: number;
  cache_utilization_percent: number;
  max_cache_size_bytes: number;
  avg_speedup_factor: number;
  speedup_with_cache_ms: number;
  speedup_without_cache_ms: number;
  tokens_saved: number;
  total_tokens_processed: number;
  token_savings_percent: number;
  memory_used_bytes: number;
  memory_available_bytes: number;
  memory_utilization_percent: number;
  eviction_count: number;
  eviction_rate: number;
  cache_warmup_status: 'cold' | 'warming' | 'warm' | 'hot';
  cache_warmup_percent: number;
  cost_savings_total: number;
  cost_with_cache: number;
  cost_without_cache: number;
  requests_with_cache: number;
  requests_without_cache: number;
  avg_tokens_per_hit: number;
  avg_tokens_per_miss: number;
}

export interface ModelCacheEfficiency {
  model: string;
  hit_rate: number;
  miss_rate: number;
  total_hits: number;
  total_misses: number;
  speedup_factor: number;
  tokens_saved: number;
  cost_savings: number;
  avg_latency_with_cache: number;
  avg_latency_without_cache: number;
  cache_size_mb: number;
  memory_usage_mb: number;
  evictions: number;
}

export interface CacheTimeSeriesData {
  timestamp: number;
  hit_rate: number;
  miss_rate: number;
  cache_size_mb: number;
  memory_usage_mb: number;
  speedup_factor: number;
  tokens_saved: number;
  evictions: number;
}

export interface CacheEvictionStats {
  total_evictions: number;
  eviction_reasons: {
    [reason: string]: number;
  };
  avg_cache_age_on_eviction_ms: number;
  evicted_entries_size_bytes: number;
}

export interface CacheWarmupStatus {
  status: 'cold' | 'warming' | 'warm' | 'hot';
  warmup_progress_percent: number;
  entries_loaded: number;
  total_entries: number;
  warmup_time_ms: number;
  last_warmup_timestamp: number;
}

export interface CachePerformanceImpact {
  latency_reduction_ms: number;
  latency_reduction_percent: number;
  throughput_increase_percent: number;
  requests_per_second_with_cache: number;
  requests_per_second_without_cache: number;
  time_saved_total_ms: number;
  time_saved_per_request_ms: number;
}

export interface CacheCostSavings {
  total_savings: number;
  savings_percent: number;
  cost_per_token_with_cache: number;
  cost_per_token_without_cache: number;
  projected_monthly_savings: number;
  projected_yearly_savings: number;
}

export interface DashboardFilters {
  model: string | null;
  dateRange: {
    start: Date | null;
    end: Date | null;
  };
  timeGranularity: '1m' | '5m' | '15m' | '1h' | '1d';
}

export interface KVCacheResponse {
  metrics: KVCacheMetrics;
  model_efficiency: ModelCacheEfficiency[];
  time_series: CacheTimeSeriesData[];
  eviction_stats: CacheEvictionStats;
  warmup_status: CacheWarmupStatus;
  performance_impact: CachePerformanceImpact;
  cost_savings: CacheCostSavings;
}
