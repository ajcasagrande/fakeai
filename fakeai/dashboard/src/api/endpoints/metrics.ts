/**
 * Metrics API endpoints
 */

import { apiClient } from '../client';
import type {
  ModelMetrics,
  SystemMetrics,
  TimeSeriesMetric,
  MetricsQuery,
  ApiRequestConfig,
} from '../types';

/**
 * Get system-wide metrics
 */
export async function getSystemMetrics(
  config?: ApiRequestConfig
): Promise<SystemMetrics> {
  const response = await apiClient.get<SystemMetrics>('/metrics', config);
  return response.data;
}

/**
 * Get metrics for all models
 */
export async function getModelMetrics(
  config?: ApiRequestConfig
): Promise<Record<string, ModelMetrics>> {
  const response = await apiClient.get<Record<string, ModelMetrics>>(
    '/metrics/by-model',
    config
  );
  return response.data;
}

/**
 * Get metrics for a specific model
 */
export async function getModelMetricsById(
  modelId: string,
  config?: ApiRequestConfig
): Promise<ModelMetrics> {
  const response = await apiClient.get<ModelMetrics>(
    `/metrics/by-model/${encodeURIComponent(modelId)}`,
    config
  );
  return response.data;
}

/**
 * Get time series metrics
 */
export async function getTimeSeriesMetrics(
  query: MetricsQuery,
  config?: ApiRequestConfig
): Promise<Record<string, TimeSeriesMetric[]>> {
  const response = await apiClient.get<Record<string, TimeSeriesMetric[]>>(
    '/metrics/timeseries',
    {
      ...config,
      params: {
        start_time: query.start_time,
        end_time: query.end_time,
        interval: query.interval,
        models: query.models?.join(','),
        metric_types: query.metric_types?.join(','),
      },
    }
  );
  return response.data;
}

/**
 * Get request count metrics over time
 */
export async function getRequestCountMetrics(
  startTime: number,
  endTime: number,
  interval: '1m' | '5m' | '15m' | '1h' | '1d' = '1h',
  models?: string[],
  config?: ApiRequestConfig
): Promise<TimeSeriesMetric[]> {
  const response = await getTimeSeriesMetrics(
    {
      start_time: startTime,
      end_time: endTime,
      interval,
      models,
      metric_types: ['request_count'],
    },
    config
  );
  return response.request_count || [];
}

/**
 * Get latency metrics over time
 */
export async function getLatencyMetrics(
  startTime: number,
  endTime: number,
  interval: '1m' | '5m' | '15m' | '1h' | '1d' = '1h',
  models?: string[],
  config?: ApiRequestConfig
): Promise<TimeSeriesMetric[]> {
  const response = await getTimeSeriesMetrics(
    {
      start_time: startTime,
      end_time: endTime,
      interval,
      models,
      metric_types: ['latency'],
    },
    config
  );
  return response.latency || [];
}

/**
 * Get error rate metrics over time
 */
export async function getErrorRateMetrics(
  startTime: number,
  endTime: number,
  interval: '1m' | '5m' | '15m' | '1h' | '1d' = '1h',
  models?: string[],
  config?: ApiRequestConfig
): Promise<TimeSeriesMetric[]> {
  const response = await getTimeSeriesMetrics(
    {
      start_time: startTime,
      end_time: endTime,
      interval,
      models,
      metric_types: ['error_rate'],
    },
    config
  );
  return response.error_rate || [];
}

/**
 * Get token usage metrics over time
 */
export async function getTokenUsageMetrics(
  startTime: number,
  endTime: number,
  interval: '1m' | '5m' | '15m' | '1h' | '1d' = '1h',
  models?: string[],
  config?: ApiRequestConfig
): Promise<{
  input_tokens: TimeSeriesMetric[];
  output_tokens: TimeSeriesMetric[];
  total_tokens: TimeSeriesMetric[];
}> {
  const response = await getTimeSeriesMetrics(
    {
      start_time: startTime,
      end_time: endTime,
      interval,
      models,
      metric_types: ['input_tokens', 'output_tokens', 'total_tokens'],
    },
    config
  );

  return {
    input_tokens: response.input_tokens || [],
    output_tokens: response.output_tokens || [],
    total_tokens: response.total_tokens || [],
  };
}

/**
 * Get cache hit rate metrics
 */
export async function getCacheHitRateMetrics(
  startTime: number,
  endTime: number,
  interval: '1m' | '5m' | '15m' | '1h' | '1d' = '1h',
  config?: ApiRequestConfig
): Promise<TimeSeriesMetric[]> {
  const response = await getTimeSeriesMetrics(
    {
      start_time: startTime,
      end_time: endTime,
      interval,
      metric_types: ['cache_hit_rate'],
    },
    config
  );
  return response.cache_hit_rate || [];
}

/**
 * Get streaming metrics
 */
export async function getStreamingMetrics(
  config?: ApiRequestConfig
): Promise<{
  streaming_requests: number;
  non_streaming_requests: number;
  streaming_percentage: number;
  avg_streaming_latency: number;
  avg_non_streaming_latency: number;
}> {
  const response = await apiClient.get('/metrics/streaming', config);
  return response.data;
}

/**
 * Compare metrics between models
 */
export async function compareModelMetrics(
  modelIds: string[],
  config?: ApiRequestConfig
): Promise<Record<string, ModelMetrics>> {
  const metrics = await getModelMetrics(config);

  const comparison: Record<string, ModelMetrics> = {};
  for (const modelId of modelIds) {
    if (metrics[modelId]) {
      comparison[modelId] = metrics[modelId];
    }
  }

  return comparison;
}

/**
 * Get top models by metric
 */
export async function getTopModelsByMetric(
  metric: 'request_count' | 'total_tokens' | 'total_cost' | 'error_rate',
  limit: number = 10,
  config?: ApiRequestConfig
): Promise<Array<{ model: string; value: number }>> {
  const metrics = await getModelMetrics(config);

  const modelData = Object.entries(metrics).map(([model, data]) => ({
    model,
    value: data[metric],
  }));

  // Sort by metric value (descending for counts, ascending for error rate)
  modelData.sort((a, b) => {
    if (metric === 'error_rate') {
      return a.value - b.value; // Lower error rate is better
    }
    return b.value - a.value; // Higher is better for other metrics
  });

  return modelData.slice(0, limit);
}

/**
 * Calculate metrics delta between two time periods
 */
export async function getMetricsDelta(
  currentStart: number,
  currentEnd: number,
  previousStart: number,
  previousEnd: number,
  config?: ApiRequestConfig
): Promise<{
  requests_delta: number;
  tokens_delta: number;
  cost_delta: number;
  latency_delta: number;
  error_rate_delta: number;
}> {
  const [currentMetrics, previousMetrics] = await Promise.all([
    getSystemMetrics(config),
    getSystemMetrics(config),
  ]);

  return {
    requests_delta: currentMetrics.total_requests - previousMetrics.total_requests,
    tokens_delta: currentMetrics.total_tokens - previousMetrics.total_tokens,
    cost_delta: currentMetrics.total_cost - previousMetrics.total_cost,
    latency_delta: currentMetrics.avg_latency_ms - previousMetrics.avg_latency_ms,
    error_rate_delta: currentMetrics.error_rate - previousMetrics.error_rate,
  };
}

/**
 * Get health status based on metrics
 */
export async function getHealthStatus(
  config?: ApiRequestConfig
): Promise<{
  status: 'healthy' | 'degraded' | 'unhealthy';
  issues: string[];
  metrics: SystemMetrics;
}> {
  const metrics = await getSystemMetrics(config);
  const issues: string[] = [];

  // Check error rate
  if (metrics.error_rate > 0.05) {
    issues.push(`High error rate: ${(metrics.error_rate * 100).toFixed(2)}%`);
  }

  // Check latency
  if (metrics.avg_latency_ms > 5000) {
    issues.push(`High latency: ${metrics.avg_latency_ms.toFixed(0)}ms`);
  }

  // Check cache hit rate
  if (metrics.cache_hit_rate < 0.5) {
    issues.push(`Low cache hit rate: ${(metrics.cache_hit_rate * 100).toFixed(2)}%`);
  }

  // Determine overall status
  let status: 'healthy' | 'degraded' | 'unhealthy';
  if (issues.length === 0) {
    status = 'healthy';
  } else if (issues.length === 1 || metrics.error_rate < 0.1) {
    status = 'degraded';
  } else {
    status = 'unhealthy';
  }

  return {
    status,
    issues,
    metrics,
  };
}
