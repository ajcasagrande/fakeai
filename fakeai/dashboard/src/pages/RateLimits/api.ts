/**
 * API client functions for Rate Limits Dashboard
 */

import {
  RateLimitsOverview,
  ApiKeyRateLimit,
  RateLimitBreach,
  ThrottleTimeSeries,
  AbusePattern,
  TopConsumer,
  TierDistribution,
  TierUpgradeRecommendation,
  RealTimeRateLimitData,
  RateLimitFilters,
} from './types';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Get API key from localStorage or environment
 */
function getApiKey(): string {
  return localStorage.getItem('apiKey') || process.env.REACT_APP_API_KEY || 'fake-api-key';
}

/**
 * Fetch rate limits overview
 */
export async function fetchRateLimitsOverview(): Promise<RateLimitsOverview> {
  const response = await fetch(`${BASE_URL}/metrics/rate-limits/overview`, {
    headers: {
      'Authorization': `Bearer ${getApiKey()}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch rate limits overview: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch rate limit status by API keys
 */
export async function fetchApiKeyRateLimits(
  filters?: RateLimitFilters
): Promise<ApiKeyRateLimit[]> {
  const params = new URLSearchParams();

  if (filters?.api_key) {
    params.append('api_key', filters.api_key);
  }
  if (filters?.tier) {
    params.append('tier', filters.tier);
  }
  if (filters?.status && filters.status !== 'all') {
    params.append('status', filters.status);
  }
  if (filters?.dateRange.start) {
    params.append('start_time', filters.dateRange.start.getTime().toString());
  }
  if (filters?.dateRange.end) {
    params.append('end_time', filters.dateRange.end.getTime().toString());
  }

  const response = await fetch(
    `${BASE_URL}/metrics/rate-limits/by-api-key?${params.toString()}`,
    {
      headers: {
        'Authorization': `Bearer ${getApiKey()}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch API key rate limits: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch specific API key rate limit status
 */
export async function fetchApiKeyRateLimit(apiKey: string): Promise<ApiKeyRateLimit> {
  const response = await fetch(
    `${BASE_URL}/metrics/rate-limits/by-api-key/${encodeURIComponent(apiKey)}`,
    {
      headers: {
        'Authorization': `Bearer ${getApiKey()}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch rate limit for API key: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch rate limit breaches
 */
export async function fetchRateLimitBreaches(
  limit: number = 100,
  filters?: RateLimitFilters
): Promise<RateLimitBreach[]> {
  const params = new URLSearchParams({
    limit: limit.toString(),
  });

  if (filters?.api_key) {
    params.append('api_key', filters.api_key);
  }
  if (filters?.breach_type && filters.breach_type !== 'all') {
    params.append('breach_type', filters.breach_type);
  }
  if (filters?.dateRange.start) {
    params.append('start_time', filters.dateRange.start.getTime().toString());
  }
  if (filters?.dateRange.end) {
    params.append('end_time', filters.dateRange.end.getTime().toString());
  }

  const response = await fetch(
    `${BASE_URL}/metrics/rate-limits/breaches?${params.toString()}`,
    {
      headers: {
        'Authorization': `Bearer ${getApiKey()}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch rate limit breaches: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch throttle analytics (429 errors over time)
 */
export async function fetchThrottleAnalytics(
  startTime?: number,
  endTime?: number,
  bucketWidth: string = '5m'
): Promise<ThrottleTimeSeries[]> {
  const params = new URLSearchParams({
    bucket_width: bucketWidth,
  });

  if (startTime) {
    params.append('start_time', startTime.toString());
  }
  if (endTime) {
    params.append('end_time', endTime.toString());
  }

  const response = await fetch(
    `${BASE_URL}/metrics/rate-limits/throttles?${params.toString()}`,
    {
      headers: {
        'Authorization': `Bearer ${getApiKey()}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch throttle analytics: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch abuse patterns
 */
export async function fetchAbusePatterns(): Promise<AbusePattern[]> {
  const response = await fetch(`${BASE_URL}/metrics/rate-limits/abuse-patterns`, {
    headers: {
      'Authorization': `Bearer ${getApiKey()}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch abuse patterns: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch top consumers by API key
 */
export async function fetchTopConsumers(limit: number = 10): Promise<TopConsumer[]> {
  const response = await fetch(
    `${BASE_URL}/metrics/rate-limits/top-consumers?limit=${limit}`,
    {
      headers: {
        'Authorization': `Bearer ${getApiKey()}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch top consumers: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch tier distribution
 */
export async function fetchTierDistribution(): Promise<TierDistribution[]> {
  const response = await fetch(`${BASE_URL}/metrics/rate-limits/tier-distribution`, {
    headers: {
      'Authorization': `Bearer ${getApiKey()}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch tier distribution: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch tier upgrade recommendations
 */
export async function fetchTierUpgradeRecommendations(): Promise<TierUpgradeRecommendation[]> {
  const response = await fetch(`${BASE_URL}/metrics/rate-limits/upgrade-recommendations`, {
    headers: {
      'Authorization': `Bearer ${getApiKey()}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch tier upgrade recommendations: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch real-time rate limit data
 */
export async function fetchRealTimeRateLimitData(): Promise<RealTimeRateLimitData> {
  const response = await fetch(`${BASE_URL}/metrics/rate-limits/real-time`, {
    headers: {
      'Authorization': `Bearer ${getApiKey()}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch real-time rate limit data: ${response.statusText}`);
  }

  return response.json();
}
