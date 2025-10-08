/**
 * Mock data for testing
 * Provides realistic test data for all dashboard components
 */

import {
  ModelStats,
  ChatRequest,
  CompletionsUsageResponse,
  UsageAggregationBucket,
  ModelMetricsResponse,
} from '../../pages/ChatCompletions/types';

/**
 * Mock model statistics
 */
export const mockModelStats: Record<string, ModelStats> = {
  'gpt-4': {
    model: 'gpt-4',
    request_count: 1523,
    total_prompt_tokens: 245678,
    total_completion_tokens: 156432,
    total_tokens: 402110,
    total_latency_ms: 2345678,
    error_count: 12,
    latency_percentiles: {
      p50: 1200,
      p90: 2500,
      p95: 3200,
      p99: 5000,
    },
    streaming_requests: 856,
    non_streaming_requests: 667,
    avg_latency_ms: 1540,
    error_rate: 0.00788,
    total_cost: 45.67,
    avg_cost_per_request: 0.03,
    tokens_per_second: 261.3,
  },
  'gpt-3.5-turbo': {
    model: 'gpt-3.5-turbo',
    request_count: 4567,
    total_prompt_tokens: 567890,
    total_completion_tokens: 234567,
    total_tokens: 802457,
    total_latency_ms: 1234567,
    error_count: 23,
    latency_percentiles: {
      p50: 450,
      p90: 890,
      p95: 1200,
      p99: 2000,
    },
    streaming_requests: 2345,
    non_streaming_requests: 2222,
    avg_latency_ms: 270,
    error_rate: 0.00504,
    total_cost: 12.34,
    avg_cost_per_request: 0.0027,
    tokens_per_second: 650.2,
  },
  'claude-3-opus': {
    model: 'claude-3-opus',
    request_count: 892,
    total_prompt_tokens: 123456,
    total_completion_tokens: 98765,
    total_tokens: 222221,
    total_latency_ms: 1567890,
    error_count: 5,
    latency_percentiles: {
      p50: 1800,
      p90: 3200,
      p95: 4100,
      p99: 6500,
    },
    streaming_requests: 567,
    non_streaming_requests: 325,
    avg_latency_ms: 1757,
    error_rate: 0.00561,
    total_cost: 34.56,
    avg_cost_per_request: 0.0387,
    tokens_per_second: 141.7,
  },
};

/**
 * Mock chat requests
 */
export const mockChatRequests: ChatRequest[] = [
  {
    id: 'req_001',
    model: 'gpt-4',
    created: Date.now() - 1000 * 60 * 5, // 5 minutes ago
    prompt_tokens: 150,
    completion_tokens: 200,
    total_tokens: 350,
    latency_ms: 1250,
    streaming: true,
    status: 'success',
    cost: 0.0105,
  },
  {
    id: 'req_002',
    model: 'gpt-3.5-turbo',
    created: Date.now() - 1000 * 60 * 10,
    prompt_tokens: 120,
    completion_tokens: 80,
    total_tokens: 200,
    latency_ms: 340,
    streaming: false,
    status: 'success',
    cost: 0.0006,
  },
  {
    id: 'req_003',
    model: 'gpt-4',
    created: Date.now() - 1000 * 60 * 15,
    prompt_tokens: 200,
    completion_tokens: 0,
    total_tokens: 200,
    latency_ms: 450,
    streaming: true,
    status: 'error',
    error_message: 'Rate limit exceeded',
    cost: 0,
  },
  {
    id: 'req_004',
    model: 'claude-3-opus',
    created: Date.now() - 1000 * 60 * 20,
    prompt_tokens: 300,
    completion_tokens: 400,
    total_tokens: 700,
    latency_ms: 1850,
    streaming: true,
    status: 'success',
    cost: 0.042,
  },
  {
    id: 'req_005',
    model: 'gpt-3.5-turbo',
    created: Date.now() - 1000 * 60 * 25,
    prompt_tokens: 80,
    completion_tokens: 120,
    total_tokens: 200,
    latency_ms: 280,
    streaming: false,
    status: 'success',
    cost: 0.00054,
  },
];

/**
 * Mock usage aggregation buckets
 */
export const mockUsageBuckets: UsageAggregationBucket[] = [
  {
    object: 'bucket',
    start_time: Date.now() - 1000 * 60 * 60, // 1 hour ago
    end_time: Date.now(),
    results: [
      {
        object: 'organization.usage.result',
        input_tokens: 123456,
        output_tokens: 98765,
        input_cached_tokens: 12345,
        num_model_requests: 500,
      },
    ],
  },
  {
    object: 'bucket',
    start_time: Date.now() - 1000 * 60 * 60 * 2,
    end_time: Date.now() - 1000 * 60 * 60,
    results: [
      {
        object: 'organization.usage.result',
        input_tokens: 98765,
        output_tokens: 76543,
        input_cached_tokens: 9876,
        num_model_requests: 423,
      },
    ],
  },
];

/**
 * Mock completions usage response
 */
export const mockCompletionsUsageResponse: CompletionsUsageResponse = {
  object: 'page',
  data: mockUsageBuckets,
  has_more: false,
  next_page: null,
};

/**
 * Mock model metrics response
 */
export const mockModelMetricsResponse: ModelMetricsResponse = mockModelStats;

/**
 * Generate random mock model stats
 */
export function generateMockModelStats(overrides?: Partial<ModelStats>): ModelStats {
  const requestCount = Math.floor(Math.random() * 5000) + 100;
  const promptTokens = Math.floor(Math.random() * 500000) + 10000;
  const completionTokens = Math.floor(Math.random() * 300000) + 5000;
  const errorCount = Math.floor(Math.random() * 50);
  const streamingRequests = Math.floor(requestCount * (Math.random() * 0.4 + 0.3)); // 30-70% streaming

  return {
    model: overrides?.model || `model-${Math.random().toString(36).substr(2, 9)}`,
    request_count: requestCount,
    total_prompt_tokens: promptTokens,
    total_completion_tokens: completionTokens,
    total_tokens: promptTokens + completionTokens,
    total_latency_ms: requestCount * (Math.random() * 2000 + 500),
    error_count: errorCount,
    latency_percentiles: {
      p50: Math.random() * 1000 + 200,
      p90: Math.random() * 2000 + 800,
      p95: Math.random() * 3000 + 1500,
      p99: Math.random() * 5000 + 3000,
    },
    streaming_requests: streamingRequests,
    non_streaming_requests: requestCount - streamingRequests,
    avg_latency_ms: Math.random() * 2000 + 500,
    error_rate: errorCount / requestCount,
    total_cost: Math.random() * 100 + 10,
    avg_cost_per_request: Math.random() * 0.05 + 0.001,
    tokens_per_second: Math.random() * 500 + 100,
    ...overrides,
  };
}

/**
 * Generate random mock chat request
 */
export function generateMockChatRequest(overrides?: Partial<ChatRequest>): ChatRequest {
  const models = ['gpt-4', 'gpt-3.5-turbo', 'claude-3-opus', 'claude-3-sonnet'];
  const promptTokens = Math.floor(Math.random() * 500) + 50;
  const completionTokens = Math.floor(Math.random() * 300) + 50;
  const isError = Math.random() < 0.05;

  return {
    id: `req_${Math.random().toString(36).substr(2, 9)}`,
    model: models[Math.floor(Math.random() * models.length)],
    created: Date.now() - Math.floor(Math.random() * 86400000),
    prompt_tokens: promptTokens,
    completion_tokens: isError ? 0 : completionTokens,
    total_tokens: isError ? promptTokens : promptTokens + completionTokens,
    latency_ms: Math.random() * 3000 + 200,
    streaming: Math.random() > 0.5,
    status: isError ? 'error' : 'success',
    error_message: isError ? 'Sample error message' : undefined,
    cost: isError ? 0 : Math.random() * 0.05 + 0.001,
    ...overrides,
  };
}

/**
 * Generate array of mock requests
 */
export function generateMockChatRequests(count: number): ChatRequest[] {
  return Array.from({ length: count }, () => generateMockChatRequest());
}

/**
 * Generate array of mock model stats
 */
export function generateMockModelStatsArray(count: number): Record<string, ModelStats> {
  const stats: Record<string, ModelStats> = {};
  for (let i = 0; i < count; i++) {
    const model = `model-${i}`;
    stats[model] = generateMockModelStats({ model });
  }
  return stats;
}
