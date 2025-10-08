/**
 * React Query hooks for Organization and Usage API
 */

import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import {
  getCompletionsUsage,
  getEmbeddingsUsage,
  getImagesUsage,
  getAudioUsage,
  getAggregatedUsage,
  getUsageSummary,
} from '../endpoints/organization';
import type { OrganizationUsageRequest, OrganizationUsageResponse } from '../types';

/**
 * Hook to get completions usage
 */
export function useCompletionsUsage(
  request: OrganizationUsageRequest,
  options?: UseQueryOptions<OrganizationUsageResponse, Error>
) {
  return useQuery({
    queryKey: ['organization', 'usage', 'completions', request],
    queryFn: () => getCompletionsUsage(request),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to get embeddings usage
 */
export function useEmbeddingsUsage(
  request: OrganizationUsageRequest,
  options?: UseQueryOptions<OrganizationUsageResponse, Error>
) {
  return useQuery({
    queryKey: ['organization', 'usage', 'embeddings', request],
    queryFn: () => getEmbeddingsUsage(request),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to get images usage
 */
export function useImagesUsage(
  request: OrganizationUsageRequest,
  options?: UseQueryOptions<OrganizationUsageResponse, Error>
) {
  return useQuery({
    queryKey: ['organization', 'usage', 'images', request],
    queryFn: () => getImagesUsage(request),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to get audio usage
 */
export function useAudioUsage(
  request: OrganizationUsageRequest,
  options?: UseQueryOptions<OrganizationUsageResponse, Error>
) {
  return useQuery({
    queryKey: ['organization', 'usage', 'audio', request],
    queryFn: () => getAudioUsage(request),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to get aggregated usage across all services
 */
export function useAggregatedUsage(
  request: OrganizationUsageRequest,
  options?: UseQueryOptions<
    {
      completions: OrganizationUsageResponse;
      embeddings: OrganizationUsageResponse;
      images: OrganizationUsageResponse;
      audio: OrganizationUsageResponse;
    },
    Error
  >
) {
  return useQuery({
    queryKey: ['organization', 'usage', 'aggregated', request],
    queryFn: () => getAggregatedUsage(request),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to get usage summary
 */
export function useUsageSummary(
  startTime: number,
  endTime: number,
  options?: UseQueryOptions<
    {
      total_input_tokens: number;
      total_output_tokens: number;
      total_cached_tokens: number;
      total_requests: number;
      by_service: Record<string, number>;
    },
    Error
  >
) {
  return useQuery({
    queryKey: ['organization', 'usage', 'summary', startTime, endTime],
    queryFn: () => getUsageSummary(startTime, endTime),
    staleTime: 60000,
    ...options,
  });
}
