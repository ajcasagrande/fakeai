/**
 * Organization and Usage API endpoints
 */

import { apiClient } from '../client';
import type {
  OrganizationUsageRequest,
  OrganizationUsageResponse,
  ApiRequestConfig,
} from '../types';

/**
 * Get organization usage for completions
 */
export async function getCompletionsUsage(
  request: OrganizationUsageRequest,
  config?: ApiRequestConfig
): Promise<OrganizationUsageResponse> {
  const response = await apiClient.get<OrganizationUsageResponse>(
    '/v1/organization/usage/completions',
    {
      ...config,
      params: {
        start_time: request.start_time,
        end_time: request.end_time,
        bucket_width: request.bucket_width,
        project_ids: request.project_ids?.join(','),
        user_ids: request.user_ids?.join(','),
        api_key_ids: request.api_key_ids?.join(','),
        models: request.models?.join(','),
        group_by: request.group_by?.join(','),
      },
    }
  );
  return response.data;
}

/**
 * Get organization usage for embeddings
 */
export async function getEmbeddingsUsage(
  request: OrganizationUsageRequest,
  config?: ApiRequestConfig
): Promise<OrganizationUsageResponse> {
  const response = await apiClient.get<OrganizationUsageResponse>(
    '/v1/organization/usage/embeddings',
    {
      ...config,
      params: {
        start_time: request.start_time,
        end_time: request.end_time,
        bucket_width: request.bucket_width,
        project_ids: request.project_ids?.join(','),
        user_ids: request.user_ids?.join(','),
        api_key_ids: request.api_key_ids?.join(','),
        models: request.models?.join(','),
        group_by: request.group_by?.join(','),
      },
    }
  );
  return response.data;
}

/**
 * Get organization usage for images
 */
export async function getImagesUsage(
  request: OrganizationUsageRequest,
  config?: ApiRequestConfig
): Promise<OrganizationUsageResponse> {
  const response = await apiClient.get<OrganizationUsageResponse>(
    '/v1/organization/usage/images',
    {
      ...config,
      params: {
        start_time: request.start_time,
        end_time: request.end_time,
        bucket_width: request.bucket_width,
        project_ids: request.project_ids?.join(','),
        user_ids: request.user_ids?.join(','),
        api_key_ids: request.api_key_ids?.join(','),
        models: request.models?.join(','),
        group_by: request.group_by?.join(','),
      },
    }
  );
  return response.data;
}

/**
 * Get organization usage for audio
 */
export async function getAudioUsage(
  request: OrganizationUsageRequest,
  config?: ApiRequestConfig
): Promise<OrganizationUsageResponse> {
  const response = await apiClient.get<OrganizationUsageResponse>(
    '/v1/organization/usage/audio',
    {
      ...config,
      params: {
        start_time: request.start_time,
        end_time: request.end_time,
        bucket_width: request.bucket_width,
        project_ids: request.project_ids?.join(','),
        user_ids: request.user_ids?.join(','),
        api_key_ids: request.api_key_ids?.join(','),
        models: request.models?.join(','),
        group_by: request.group_by?.join(','),
      },
    }
  );
  return response.data;
}

/**
 * Get aggregated organization usage across all services
 */
export async function getAggregatedUsage(
  request: OrganizationUsageRequest,
  config?: ApiRequestConfig
): Promise<{
  completions: OrganizationUsageResponse;
  embeddings: OrganizationUsageResponse;
  images: OrganizationUsageResponse;
  audio: OrganizationUsageResponse;
}> {
  const [completions, embeddings, images, audio] = await Promise.all([
    getCompletionsUsage(request, config),
    getEmbeddingsUsage(request, config),
    getImagesUsage(request, config),
    getAudioUsage(request, config),
  ]);

  return {
    completions,
    embeddings,
    images,
    audio,
  };
}

/**
 * Get usage summary for a time period
 */
export async function getUsageSummary(
  startTime: number,
  endTime: number,
  config?: ApiRequestConfig
): Promise<{
  total_input_tokens: number;
  total_output_tokens: number;
  total_cached_tokens: number;
  total_requests: number;
  by_service: Record<string, number>;
}> {
  const request: OrganizationUsageRequest = {
    start_time: startTime,
    end_time: endTime,
    bucket_width: '1d',
  };

  const usage = await getAggregatedUsage(request, config);

  let totalInputTokens = 0;
  let totalOutputTokens = 0;
  let totalCachedTokens = 0;
  let totalRequests = 0;

  const byService: Record<string, number> = {
    completions: 0,
    embeddings: 0,
    images: 0,
    audio: 0,
  };

  // Aggregate completions
  for (const bucket of usage.completions.data) {
    for (const result of bucket.results) {
      totalInputTokens += result.input_tokens;
      totalOutputTokens += result.output_tokens;
      totalCachedTokens += result.input_cached_tokens;
      totalRequests += result.num_model_requests;
      byService.completions += result.num_model_requests;
    }
  }

  // Aggregate embeddings
  for (const bucket of usage.embeddings.data) {
    for (const result of bucket.results) {
      totalInputTokens += result.input_tokens;
      totalRequests += result.num_model_requests;
      byService.embeddings += result.num_model_requests;
    }
  }

  // Aggregate images
  for (const bucket of usage.images.data) {
    for (const result of bucket.results) {
      totalRequests += result.num_model_requests;
      byService.images += result.num_model_requests;
    }
  }

  // Aggregate audio
  for (const bucket of usage.audio.data) {
    for (const result of bucket.results) {
      totalRequests += result.num_model_requests;
      byService.audio += result.num_model_requests;
    }
  }

  return {
    total_input_tokens: totalInputTokens,
    total_output_tokens: totalOutputTokens,
    total_cached_tokens: totalCachedTokens,
    total_requests: totalRequests,
    by_service: byService,
  };
}

/**
 * Helper to create time range for common periods
 */
export function createTimeRange(period: 'today' | 'yesterday' | 'last7days' | 'last30days' | 'thisMonth'): {
  start_time: number;
  end_time: number;
} {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  switch (period) {
    case 'today':
      return {
        start_time: Math.floor(today.getTime() / 1000),
        end_time: Math.floor(Date.now() / 1000),
      };

    case 'yesterday': {
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      return {
        start_time: Math.floor(yesterday.getTime() / 1000),
        end_time: Math.floor(today.getTime() / 1000),
      };
    }

    case 'last7days': {
      const last7days = new Date(today);
      last7days.setDate(last7days.getDate() - 7);
      return {
        start_time: Math.floor(last7days.getTime() / 1000),
        end_time: Math.floor(Date.now() / 1000),
      };
    }

    case 'last30days': {
      const last30days = new Date(today);
      last30days.setDate(last30days.getDate() - 30);
      return {
        start_time: Math.floor(last30days.getTime() / 1000),
        end_time: Math.floor(Date.now() / 1000),
      };
    }

    case 'thisMonth': {
      const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
      return {
        start_time: Math.floor(monthStart.getTime() / 1000),
        end_time: Math.floor(Date.now() / 1000),
      };
    }

    default:
      return {
        start_time: Math.floor(today.getTime() / 1000),
        end_time: Math.floor(Date.now() / 1000),
      };
  }
}
