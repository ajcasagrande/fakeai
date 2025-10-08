/**
 * TypeScript type definitions for Chat Completions Dashboard
 */

export interface UsageResultItem {
  object: 'organization.usage.result';
  input_tokens: number;
  output_tokens: number;
  input_cached_tokens: number;
  num_model_requests: number;
}

export interface UsageAggregationBucket {
  object: 'bucket';
  start_time: number;
  end_time: number;
  results: UsageResultItem[];
}

export interface CompletionsUsageResponse {
  object: 'page';
  data: UsageAggregationBucket[];
  has_more: boolean;
  next_page: string | null;
}

export interface ModelStats {
  model: string;
  request_count: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_latency_ms: number;
  error_count: number;
  latency_percentiles: {
    p50: number;
    p90: number;
    p95: number;
    p99: number;
  };
  streaming_requests: number;
  non_streaming_requests: number;
  avg_latency_ms: number;
  error_rate: number;
  total_cost: number;
  avg_cost_per_request: number;
  tokens_per_second: number;
}

export interface ModelMetricsResponse {
  [model: string]: ModelStats;
}

export interface ChatRequest {
  id: string;
  model: string;
  created: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  latency_ms: number;
  streaming: boolean;
  status: 'success' | 'error';
  error_message?: string;
  cost: number;
  request_data?: any;
  response_data?: any;
}

export interface DashboardFilters {
  model: string | null;
  dateRange: {
    start: Date | null;
    end: Date | null;
  };
  status: 'all' | 'success' | 'error';
  streaming: 'all' | 'streaming' | 'non-streaming';
}

export interface MetricsOverview {
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  avg_latency_ms: number;
  error_rate: number;
  streaming_percentage: number;
  requests_per_second: number;
}

export interface ChartDataPoint {
  timestamp: number;
  value: number;
  label?: string;
}

export interface ModelUsageData {
  model: string;
  requests: number;
  percentage: number;
  color: string;
}

export interface TokenBreakdown {
  prompt_tokens: number;
  completion_tokens: number;
  cached_tokens: number;
  total_tokens: number;
}

export interface TimeSeriesData {
  timestamp: number;
  requests: number;
  latency: number;
  errors: number;
  tokens: number;
}
