/**
 * NVIDIA AI-Dynamo API Service
 *
 * Service layer for fetching AI-Dynamo LLM inference metrics
 * from the backend API endpoints.
 */

import { AIDynamoDashboardData, AIDynamoMetrics } from './types';

// Use relative URLs - dashboard is served from same server as API
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Fetch comprehensive AI-Dynamo metrics in JSON format
 */
export async function fetchAIDynamoMetrics(
  modelName?: string,
  workerId?: string,
  timeRange?: string
): Promise<AIDynamoDashboardData> {
  try {
    const params = new URLSearchParams();
    if (modelName) params.append('model_name', modelName);
    if (workerId) params.append('worker_id', workerId);
    if (timeRange) params.append('time_range', timeRange);

    const url = `/dynamo/metrics/json?${params.toString()}`;
    const response = await fetch(`${API_BASE_URL}${url}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const rawData = await response.json();
    console.log('🔍 Raw backend response:', rawData);

    // Calculate aggregate metrics from per_model data if top-level is missing
    const perModelData = rawData.per_model || {};
    const models = Object.values(perModelData) as any[];

    // Aggregate TTFT from per-model data
    const avgTTFT = models.length > 0
      ? models.reduce((sum: number, m: any) => sum + (m.avg_ttft_ms || 0), 0) / models.length
      : 0;

    // Aggregate ITL/TPOT from per-model data
    const avgITL = models.length > 0
      ? models.reduce((sum: number, m: any) => sum + (m.avg_itl_ms || 0), 0) / models.length
      : 0;

    // Transform backend response to match dashboard types
    const transformedData: AIDynamoDashboardData = {
      metrics: {
        request_count: rawData.summary?.total_requests || 0,
        success_rate: rawData.summary?.total_requests > 0
          ? (rawData.summary?.successful_requests || 0) / rawData.summary.total_requests
          : 0,
        error_count: rawData.summary?.failed_requests || 0,
        latency: {
          total: rawData.latency?.total || { avg: 0, p50: 0, p95: avgTTFT, p99: avgTTFT, min: 0, max: avgTTFT },
          queue: rawData.latency?.queue || { avg: 0, p50: 0, p95: 0, p99: 0, min: 0, max: 0 },
          prefill: rawData.latency?.prefill || { avg: 0, p50: 0, p95: 0, p99: 0, min: 0, max: 0 },
          decode: rawData.latency?.decode || { avg: 0, p50: 0, p95: 0, p99: 0, min: 0, max: 0 },
          ttft: rawData.latency?.ttft || { avg: avgTTFT, p50: avgTTFT, p95: avgTTFT, p99: avgTTFT, min: 0, max: avgTTFT },
          tpot: rawData.latency?.itl || { avg: avgITL, p50: avgITL, p95: avgITL, p99: avgITL, min: 0, max: avgITL },
          itl: rawData.latency?.itl || { avg: avgITL, p50: avgITL, p95: avgITL, p99: avgITL, min: 0, max: avgITL },
        },
        throughput: {
          requests_per_sec: rawData.throughput?.requests_per_second || 0,
          tokens_per_sec: rawData.throughput?.tokens_per_second || 0,
          input_tokens_per_sec: rawData.throughput?.input_tokens_per_second || 0,
          output_tokens_per_sec: rawData.throughput?.output_tokens_per_second || 0,
        },
        tokens: {
          total_input_tokens: 0,
          total_output_tokens: 0,
          total_cached_tokens: rawData.cache?.total_cached_tokens || 0,
          avg_input_tokens: 0,
          avg_output_tokens: 0,
          avg_cached_tokens: 0,
        },
        queue: {
          current_depth: rawData.queue?.current_depth || 0,
          max_depth: rawData.queue?.max_depth || 0,
          avg_wait_time_ms: rawData.queue?.avg_depth || 0,
          total_queued_requests: 0,
        },
        kv_cache: {
          hit_rate: rawData.cache?.hit_rate || 0,
          avg_blocks_matched: rawData.cache?.avg_blocks_matched || 0,
          avg_overlap_score: rawData.cache?.avg_overlap_score || 0,
          total_cache_hits: 0,
          total_cache_misses: 0,
        },
        workers: {
          total_workers: 0,
          active_workers: 0,
          avg_utilization: 0,
          avg_routing_cost_ms: 0,
        },
      },
      latency_breakdown: [],
      request_lifecycles: [],
      ttft_stats: {
        avg_ttft_ms: avgTTFT,
        p50_ttft_ms: avgTTFT,
        p95_ttft_ms: avgTTFT,
        p99_ttft_ms: avgTTFT,
      },
      tpot_stats: {
        avg_tpot_ms: avgITL,
        p50_tpot_ms: avgITL,
        p95_tpot_ms: avgITL,
        p99_tpot_ms: avgITL,
        avg_tokens_per_sec: rawData.throughput?.tokens_per_second || 0,
      },
      throughput_stats: {
        current_rps: rawData.throughput?.requests_per_second || 0,
        peak_rps: rawData.throughput?.requests_per_second || 0,
        avg_rps: rawData.throughput?.requests_per_second || 0,
        current_tps: rawData.throughput?.tokens_per_second || 0,
        peak_tps: rawData.throughput?.tokens_per_second || 0,
        avg_tps: rawData.throughput?.tokens_per_second || 0,
      },
      queue_stats: {
        current_depth: rawData.queue?.current_depth || 0,
        max_depth: rawData.queue?.max_depth || 0,
        avg_wait_time_ms: rawData.queue?.avg_depth || 0,
        p95_wait_time_ms: 0,
        p99_wait_time_ms: 0,
      },
      kv_cache_stats: {
        overall_hit_rate: rawData.cache?.hit_rate || 0,
        total_hits: 0,
        total_misses: 0,
        avg_blocks_matched: rawData.cache?.avg_blocks_matched || 0,
        avg_overlap_score: rawData.cache?.avg_overlap_score || 0,
        cache_size_mb: 0,
        cache_utilization: 0,
      },
      worker_stats: {
        total_workers: 0,
        active_workers: 0,
        idle_workers: 0,
        offline_workers: 0,
        workers: [],
      },
      token_stats: {
        total_input_tokens: 0,
        total_output_tokens: 0,
        total_cached_tokens: rawData.cache?.total_cached_tokens || 0,
        input_tokens_per_sec: rawData.throughput?.input_tokens_per_second || 0,
        output_tokens_per_sec: rawData.throughput?.output_tokens_per_second || 0,
        avg_input_tokens: 0,
        avg_output_tokens: 0,
        p95_input_tokens: 0,
        p95_output_tokens: 0,
        p99_input_tokens: 0,
        p99_output_tokens: 0,
      },
      per_model_stats: {
        total_models: Object.keys(rawData.per_model || {}).length,
        models: Object.entries(rawData.per_model || {}).map(([id, stats]: [string, any]) => ({
          model_id: id,
          model_name: id,
          request_count: stats.requests || 0,
          requests_per_sec: 0,
          tokens_per_sec: (stats.total_tokens || 0) / 60, // Rough estimate
          avg_ttft_ms: stats.avg_ttft_ms || 0,
          avg_tpot_ms: stats.avg_itl_ms || 0,
          total_input_tokens: 0,
          total_output_tokens: stats.total_tokens || 0,
          cache_hit_rate: 0,
          success_rate: 1.0,
        })),
      },
      historical_trends: [],
      timestamp: Date.now(),
      collection_window_seconds: 3600,
    };

    console.log('✅ Transformed data:', transformedData);
    console.log('📊 TTFT:', avgTTFT, 'ms | TPOT:', avgITL, 'ms');

    return transformedData;
  } catch (error) {
    console.error('Error fetching AI-Dynamo metrics:', error);
    throw error;
  }
}

/**
 * Fetch AI-Dynamo metrics in Prometheus format
 */
export async function fetchAIDynamoMetricsPrometheus(
  modelName?: string,
  workerId?: string
): Promise<string> {
  try {
    const params = new URLSearchParams();
    if (modelName) params.append('model_name', modelName);
    if (workerId) params.append('worker_id', workerId);

    const url = `/dynamo/metrics?${params.toString()}`;
    const response = await fetch(`${API_BASE_URL}${url}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.text();
  } catch (error) {
    console.error('Error fetching AI-Dynamo Prometheus metrics:', error);
    throw error;
  }
}

/**
 * Fetch real-time AI-Dynamo statistics
 */
export async function fetchRealtimeStats(
  modelName?: string,
  workerId?: string
): Promise<AIDynamoMetrics> {
  try {
    const params = new URLSearchParams();
    if (modelName) params.append('model_name', modelName);
    if (workerId) params.append('worker_id', workerId);

    const url = `/dynamo/stats?${params.toString()}`;
    const response = await fetch(`${API_BASE_URL}${url}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.metrics;
  } catch (error) {
    console.error('Error fetching real-time stats:', error);
    throw error;
  }
}

/**
 * Fetch available models being served
 */
export async function fetchAvailableModels(): Promise<string[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/dynamo/models`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.models || [];
  } catch (error) {
    console.error('Error fetching available models:', error);
    // Return empty array if endpoint doesn't exist
    return [];
  }
}

/**
 * Fetch available workers
 */
export async function fetchAvailableWorkers(): Promise<string[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/dynamo/workers`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.workers || [];
  } catch (error) {
    console.error('Error fetching available workers:', error);
    // Return empty array if endpoint doesn't exist
    return [];
  }
}

/**
 * Export AI-Dynamo metrics data
 */
export async function exportAIDynamoMetrics(
  format: 'json' | 'csv',
  modelName?: string,
  workerId?: string,
  timeRange?: string
): Promise<Blob> {
  try {
    const params = new URLSearchParams();
    params.append('format', format);
    if (modelName) params.append('model_name', modelName);
    if (workerId) params.append('worker_id', workerId);
    if (timeRange) params.append('time_range', timeRange);

    const url = `/dynamo/metrics/export?${params.toString()}`;
    const response = await fetch(`${API_BASE_URL}${url}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.blob();
  } catch (error) {
    console.error('Error exporting AI-Dynamo metrics:', error);
    throw error;
  }
}
