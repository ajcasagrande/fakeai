/**
 * TypeScript type definitions for Embeddings Dashboard
 *
 * SPDX-License-Identifier: Apache-2.0
 */

export interface EmbeddingUsageData {
  object: string;
  data: EmbeddingBucket[];
  ftTokensData?: any[];
  has_more: boolean;
}

export interface EmbeddingBucket {
  aggregation_timestamp: number;
  num_model_requests: number;
  operation: string;
  snapshot_id: string;
  num_input_tokens: number;
  num_cached_tokens?: number;
  project_id?: string;
  model?: string;
}

export interface EmbeddingMetrics {
  total_requests: number;
  total_tokens: number;
  avg_processing_time: number;
  requests_per_second: number;
  tokens_per_second: number;
  error_rate: number;
}

export interface ModelUsageStats {
  model: string;
  requests: number;
  tokens: number;
  avg_dimensions: number;
  avg_batch_size: number;
  total_cost: number;
}

export interface DimensionStats {
  dimension: number;
  count: number;
  percentage: number;
}

export interface RecentEmbedding {
  id: string;
  timestamp: number;
  model: string;
  input_tokens: number;
  dimensions: number;
  batch_size: number;
  processing_time: number;
  cost: number;
  status: 'success' | 'error';
}

export interface UsageTrendPoint {
  timestamp: number;
  requests: number;
  tokens: number;
  avg_processing_time: number;
}

export interface CostBreakdown {
  model: string;
  total_cost: number;
  total_requests: number;
  cost_per_request: number;
  cost_per_1k_tokens: number;
}

export interface BatchAnalytics {
  total_batches: number;
  avg_batch_size: number;
  max_batch_size: number;
  min_batch_size: number;
  batch_size_distribution: { size: number; count: number }[];
}

export interface ExportOptions {
  format: 'json' | 'csv' | 'excel';
  dateRange: {
    start: number;
    end: number;
  };
  includeMetrics?: boolean;
  includeCosts?: boolean;
}
