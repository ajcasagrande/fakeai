/**
 * API client functions for Chat Completions Dashboard
 */

import {
  CompletionsUsageResponse,
  ModelMetricsResponse,
  ChatRequest,
} from './types';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Fetch model metrics from /metrics/by-model endpoint
 */
export async function fetchModelMetrics(): Promise<ModelMetricsResponse> {
  const response = await fetch(`${BASE_URL}/metrics/by-model`);
  if (!response.ok) {
    throw new Error(`Failed to fetch model metrics: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch specific model metrics
 */
export async function fetchModelMetricsById(modelId: string): Promise<any> {
  const response = await fetch(`${BASE_URL}/metrics/by-model/${encodeURIComponent(modelId)}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch metrics for model ${modelId}: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch completions usage data from /v1/organization/usage/completions
 */
export async function fetchCompletionsUsage(
  startTime: number,
  endTime: number,
  bucketWidth: string = '1h',
  projectId?: string,
  model?: string
): Promise<CompletionsUsageResponse> {
  const params = new URLSearchParams({
    start_time: startTime.toString(),
    end_time: endTime.toString(),
    bucket_width: bucketWidth,
  });

  if (projectId) {
    params.append('project_id', projectId);
  }

  if (model) {
    params.append('model', model);
  }

  const response = await fetch(
    `${BASE_URL}/v1/organization/usage/completions?${params.toString()}`,
    {
      headers: {
        'Authorization': `Bearer ${getApiKey()}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch completions usage: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Fetch general metrics endpoint
 */
export async function fetchGeneralMetrics(): Promise<any> {
  const response = await fetch(`${BASE_URL}/metrics`);
  if (!response.ok) {
    throw new Error(`Failed to fetch general metrics: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Mock function to simulate fetching individual chat requests
 * In a real implementation, this would connect to a database or logging system
 */
export async function fetchChatRequests(
  limit: number = 100,
  offset: number = 0,
  filters?: {
    model?: string;
    status?: string;
    streaming?: string;
    startTime?: number;
    endTime?: number;
  }
): Promise<{ requests: ChatRequest[]; total: number }> {
  // This is a mock implementation
  // In production, you would fetch from a real endpoint that stores request logs

  const modelMetrics = await fetchModelMetrics();
  const requests: ChatRequest[] = [];

  let id = offset;
  for (const [model, stats] of Object.entries(modelMetrics)) {
    const count = Math.min(stats.request_count, limit);

    for (let i = 0; i < count; i++) {
      const streaming = Math.random() < (stats.streaming_requests / stats.request_count);
      const isError = Math.random() < stats.error_rate;

      requests.push({
        id: `req_${id++}`,
        model,
        created: Date.now() - Math.floor(Math.random() * 86400000), // Random time in last 24h
        prompt_tokens: Math.floor(Math.random() * 1000) + 100,
        completion_tokens: Math.floor(Math.random() * 500) + 50,
        total_tokens: 0, // Will be calculated
        latency_ms: stats.avg_latency_ms + (Math.random() - 0.5) * 100,
        streaming,
        status: isError ? 'error' : 'success',
        error_message: isError ? 'Sample error message' : undefined,
        cost: stats.avg_cost_per_request,
      });
    }

    if (requests.length >= limit) break;
  }

  // Calculate total_tokens
  requests.forEach(req => {
    req.total_tokens = req.prompt_tokens + req.completion_tokens;
  });

  // Apply filters
  let filteredRequests = requests;
  if (filters?.model) {
    filteredRequests = filteredRequests.filter(r => r.model === filters.model);
  }
  if (filters?.status && filters.status !== 'all') {
    filteredRequests = filteredRequests.filter(r => r.status === filters.status);
  }
  if (filters?.streaming && filters.streaming !== 'all') {
    const isStreaming = filters.streaming === 'streaming';
    filteredRequests = filteredRequests.filter(r => r.streaming === isStreaming);
  }
  if (filters?.startTime) {
    filteredRequests = filteredRequests.filter(r => r.created >= filters.startTime!);
  }
  if (filters?.endTime) {
    filteredRequests = filteredRequests.filter(r => r.created <= filters.endTime!);
  }

  return {
    requests: filteredRequests.slice(0, limit),
    total: filteredRequests.length,
  };
}

/**
 * Get API key from localStorage or environment
 */
function getApiKey(): string {
  return localStorage.getItem('apiKey') || process.env.REACT_APP_API_KEY || 'fake-api-key';
}

/**
 * Set API key in localStorage
 */
export function setApiKey(key: string): void {
  localStorage.setItem('apiKey', key);
}

/**
 * Clear API key from localStorage
 */
export function clearApiKey(): void {
  localStorage.removeItem('apiKey');
}
