/**
 * KV Cache API Client
 */

import { KVCacheData } from './types';

// Use relative URLs - dashboard is served from same server as API
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const fetchKVCacheMetrics = async (): Promise<KVCacheData> => {
  const response = await fetch(`${API_BASE_URL}/kv-cache/metrics`);

  if (!response.ok) {
    throw new Error(`Failed to fetch KV cache metrics: ${response.statusText}`);
  }

  return response.json();
};
