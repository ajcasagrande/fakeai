/**
 * DCGM GPU Metrics API Client
 */

import { DCGMData } from './types';

// Use relative URLs - dashboard is served from same server as API
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export const fetchDCGMMetrics = async (): Promise<DCGMData> => {
  const response = await fetch(`${API_BASE_URL}/dcgm/metrics/json`);

  if (!response.ok) {
    throw new Error(`Failed to fetch DCGM metrics: ${response.statusText}`);
  }

  return response.json();
};
