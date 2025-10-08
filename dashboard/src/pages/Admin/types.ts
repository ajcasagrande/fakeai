/**
 * Admin Dashboard Types
 * Type definitions for admin configuration and settings
 */

export interface AdminConfig {
  kv_cache: KVCacheConfig;
  dynamo: DynamoConfig;
  token_generation: TokenGenerationConfig;
  gpu_dcgm: GPUConfig;
  model_integrations: ModelIntegrationsConfig;
}

export interface KVCacheConfig {
  block_size: number;
  num_workers: number;
  overlap_weight: number;
  enable_prefix_caching: boolean;
  cache_size_mb: number;
}

export interface DynamoConfig {
  num_workers: number;
  max_queue_depth: number;
  batch_size: number;
  enable_dynamic_batching: boolean;
  worker_timeout_ms: number;
}

export interface TokenGenerationConfig {
  ttft_range_ms: [number, number];
  tpot_range_ms: [number, number];
  itl_range_ms: [number, number];
  variance_percentage: number;
  realistic_timing: boolean;
}

export interface GPUConfig {
  num_gpus: number;
  gpu_models: string[];
  utilization_range: [number, number];
  memory_range_gb: [number, number];
  enable_dcgm: boolean;
}

export interface ModelIntegrationsConfig {
  enable_vlm: boolean;
  enable_triton: boolean;
  enable_trt_llm: boolean;
  vlm_models: string[];
  triton_backend: string;
  trt_llm_engines: string[];
}

export interface AdminMetrics {
  total_requests: number;
  active_workers: number;
  cache_hit_rate: number;
  avg_ttft_ms: number;
  avg_tpot_ms: number;
  gpu_utilization: number;
  queue_depth: number;
  uptime_seconds: number;
}

export interface AdminUser {
  username: string;
  role: string;
  logged_in: boolean;
  session_token?: string;
}
