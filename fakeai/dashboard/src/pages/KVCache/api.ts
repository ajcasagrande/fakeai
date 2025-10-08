/**
 * API client functions for KV Cache Analytics Dashboard
 */

import { KVCacheResponse } from './types';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Fetch KV cache metrics from /kv-cache/metrics endpoint
 */
export async function fetchKVCacheMetrics(
  startTime?: number,
  endTime?: number,
  model?: string,
  granularity: string = '1h'
): Promise<KVCacheResponse> {
  const params = new URLSearchParams();

  if (startTime) {
    params.append('start_time', startTime.toString());
  }

  if (endTime) {
    params.append('end_time', endTime.toString());
  }

  if (model) {
    params.append('model', model);
  }

  params.append('granularity', granularity);

  const response = await fetch(`${BASE_URL}/kv-cache/metrics?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch KV cache metrics: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch available models with KV cache enabled
 */
export async function fetchCacheEnabledModels(): Promise<string[]> {
  try {
    const response = await fetch(`${BASE_URL}/kv-cache/models`);

    if (!response.ok) {
      throw new Error(`Failed to fetch cache-enabled models: ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    // Fallback to empty array if endpoint doesn't exist
    console.warn('Failed to fetch cache-enabled models:', error);
    return [];
  }
}

/**
 * Trigger cache warmup for a specific model
 */
export async function triggerCacheWarmup(model: string): Promise<void> {
  const response = await fetch(`${BASE_URL}/kv-cache/warmup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ model }),
  });

  if (!response.ok) {
    throw new Error(`Failed to trigger cache warmup: ${response.statusText}`);
  }
}

/**
 * Clear cache for a specific model or all models
 */
export async function clearCache(model?: string): Promise<void> {
  const params = model ? `?model=${encodeURIComponent(model)}` : '';
  const response = await fetch(`${BASE_URL}/kv-cache/clear${params}`, {
    method: 'POST',
  });

  if (!response.ok) {
    throw new Error(`Failed to clear cache: ${response.statusText}`);
  }
}
