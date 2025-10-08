/**
 * React Query hooks for Metrics API
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import {
  getSystemMetrics,
  getModelMetrics,
  getModelMetricsById,
  getTimeSeriesMetrics,
  getRequestCountMetrics,
  getLatencyMetrics,
  getErrorRateMetrics,
  getTokenUsageMetrics,
  getStreamingMetrics,
  compareModelMetrics,
  getTopModelsByMetric,
  getHealthStatus,
} from '../endpoints/metrics';
import type {
  ModelMetrics,
  SystemMetrics,
  TimeSeriesMetric,
  MetricsQuery,
} from '../types';

/**
 * Hook to get system metrics
 */
export function useSystemMetrics(
  options?: UseQueryOptions<SystemMetrics, Error>
) {
  return useQuery({
    queryKey: ['metrics', 'system'],
    queryFn: () => getSystemMetrics(),
    staleTime: 5000, // 5 seconds
    refetchInterval: 10000, // Refetch every 10 seconds
    ...options,
  });
}

/**
 * Hook to get all model metrics
 */
export function useModelMetrics(
  options?: UseQueryOptions<Record<string, ModelMetrics>, Error>
) {
  return useQuery({
    queryKey: ['metrics', 'models'],
    queryFn: () => getModelMetrics(),
    staleTime: 10000, // 10 seconds
    refetchInterval: 30000, // Refetch every 30 seconds
    ...options,
  });
}

/**
 * Hook to get metrics for a specific model
 */
export function useModelMetricsById(
  modelId: string,
  options?: UseQueryOptions<ModelMetrics, Error>
) {
  return useQuery({
    queryKey: ['metrics', 'model', modelId],
    queryFn: () => getModelMetricsById(modelId),
    enabled: !!modelId,
    staleTime: 10000,
    refetchInterval: 30000,
    ...options,
  });
}

/**
 * Hook to get time series metrics
 */
export function useTimeSeriesMetrics(
  query: MetricsQuery,
  options?: UseQueryOptions<Record<string, TimeSeriesMetric[]>, Error>
) {
  return useQuery({
    queryKey: ['metrics', 'timeseries', query],
    queryFn: () => getTimeSeriesMetrics(query),
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to get request count metrics
 */
export function useRequestCountMetrics(
  startTime: number,
  endTime: number,
  interval: '1m' | '5m' | '15m' | '1h' | '1d' = '1h',
  models?: string[],
  options?: UseQueryOptions<TimeSeriesMetric[], Error>
) {
  return useQuery({
    queryKey: ['metrics', 'requests', startTime, endTime, interval, models],
    queryFn: () => getRequestCountMetrics(startTime, endTime, interval, models),
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to get latency metrics
 */
export function useLatencyMetrics(
  startTime: number,
  endTime: number,
  interval: '1m' | '5m' | '15m' | '1h' | '1d' = '1h',
  models?: string[],
  options?: UseQueryOptions<TimeSeriesMetric[], Error>
) {
  return useQuery({
    queryKey: ['metrics', 'latency', startTime, endTime, interval, models],
    queryFn: () => getLatencyMetrics(startTime, endTime, interval, models),
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to get error rate metrics
 */
export function useErrorRateMetrics(
  startTime: number,
  endTime: number,
  interval: '1m' | '5m' | '15m' | '1h' | '1d' = '1h',
  models?: string[],
  options?: UseQueryOptions<TimeSeriesMetric[], Error>
) {
  return useQuery({
    queryKey: ['metrics', 'errorRate', startTime, endTime, interval, models],
    queryFn: () => getErrorRateMetrics(startTime, endTime, interval, models),
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to get token usage metrics
 */
export function useTokenUsageMetrics(
  startTime: number,
  endTime: number,
  interval: '1m' | '5m' | '15m' | '1h' | '1d' = '1h',
  models?: string[],
  options?: UseQueryOptions<
    {
      input_tokens: TimeSeriesMetric[];
      output_tokens: TimeSeriesMetric[];
      total_tokens: TimeSeriesMetric[];
    },
    Error
  >
) {
  return useQuery({
    queryKey: ['metrics', 'tokens', startTime, endTime, interval, models],
    queryFn: () => getTokenUsageMetrics(startTime, endTime, interval, models),
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to get streaming metrics
 */
export function useStreamingMetrics(
  options?: UseQueryOptions<
    {
      streaming_requests: number;
      non_streaming_requests: number;
      streaming_percentage: number;
      avg_streaming_latency: number;
      avg_non_streaming_latency: number;
    },
    Error
  >
) {
  return useQuery({
    queryKey: ['metrics', 'streaming'],
    queryFn: () => getStreamingMetrics(),
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to compare metrics between models
 */
export function useCompareModelMetrics(
  modelIds: string[],
  options?: UseQueryOptions<Record<string, ModelMetrics>, Error>
) {
  return useQuery({
    queryKey: ['metrics', 'compare', modelIds],
    queryFn: () => compareModelMetrics(modelIds),
    enabled: modelIds.length > 0,
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to get top models by metric
 */
export function useTopModelsByMetric(
  metric: 'request_count' | 'total_tokens' | 'total_cost' | 'error_rate',
  limit: number = 10,
  options?: UseQueryOptions<Array<{ model: string; value: number }>, Error>
) {
  return useQuery({
    queryKey: ['metrics', 'top', metric, limit],
    queryFn: () => getTopModelsByMetric(metric, limit),
    staleTime: 30000,
    ...options,
  });
}

/**
 * Hook to get health status
 */
export function useHealthStatus(
  options?: UseQueryOptions<
    {
      status: 'healthy' | 'degraded' | 'unhealthy';
      issues: string[];
      metrics: SystemMetrics;
    },
    Error
  >
) {
  return useQuery({
    queryKey: ['metrics', 'health'],
    queryFn: () => getHealthStatus(),
    staleTime: 10000,
    refetchInterval: 30000,
    ...options,
  });
}
