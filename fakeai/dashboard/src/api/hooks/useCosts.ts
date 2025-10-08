/**
 * React Query hooks for Costs API
 */

import { useQuery, useMutation, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import {
  getCostBreakdown,
  getCostByModel,
  getCostByService,
  getCostEstimate,
  getCurrentMonthCost,
  getCurrentDayCost,
  getBudgetAlerts,
  createBudgetAlert,
  updateBudgetAlert,
  deleteBudgetAlert,
  getCostTrends,
  compareCosts,
  getTopCostDrivers,
  getCacheSavings,
} from '../endpoints/costs';
import type { CostBreakdown, CostEstimate, BudgetAlert } from '../types';

/**
 * Hook to get cost breakdown
 */
export function useCostBreakdown(
  startTime: number,
  endTime: number,
  period: 'hour' | 'day' | 'week' | 'month' | 'year' = 'day',
  options?: UseQueryOptions<CostBreakdown, Error>
) {
  return useQuery({
    queryKey: ['costs', 'breakdown', startTime, endTime, period],
    queryFn: () => getCostBreakdown(startTime, endTime, period),
    staleTime: 60000, // 1 minute
    ...options,
  });
}

/**
 * Hook to get cost by model
 */
export function useCostByModel(
  startTime: number,
  endTime: number,
  options?: UseQueryOptions<Record<string, number>, Error>
) {
  return useQuery({
    queryKey: ['costs', 'by-model', startTime, endTime],
    queryFn: () => getCostByModel(startTime, endTime),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to get cost by service
 */
export function useCostByService(
  startTime: number,
  endTime: number,
  options?: UseQueryOptions<Record<string, number>, Error>
) {
  return useQuery({
    queryKey: ['costs', 'by-service', startTime, endTime],
    queryFn: () => getCostByService(startTime, endTime),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to get cost estimate
 */
export function useCostEstimate(
  basedOnDays: number = 7,
  options?: UseQueryOptions<CostEstimate, Error>
) {
  return useQuery({
    queryKey: ['costs', 'estimate', basedOnDays],
    queryFn: () => getCostEstimate(basedOnDays),
    staleTime: 300000, // 5 minutes
    ...options,
  });
}

/**
 * Hook to get current month cost
 */
export function useCurrentMonthCost(
  options?: UseQueryOptions<number, Error>
) {
  return useQuery({
    queryKey: ['costs', 'current-month'],
    queryFn: () => getCurrentMonthCost(),
    staleTime: 60000,
    refetchInterval: 300000, // Refetch every 5 minutes
    ...options,
  });
}

/**
 * Hook to get current day cost
 */
export function useCurrentDayCost(
  options?: UseQueryOptions<number, Error>
) {
  return useQuery({
    queryKey: ['costs', 'current-day'],
    queryFn: () => getCurrentDayCost(),
    staleTime: 30000,
    refetchInterval: 60000, // Refetch every minute
    ...options,
  });
}

/**
 * Hook to get budget alerts
 */
export function useBudgetAlerts(
  options?: UseQueryOptions<BudgetAlert[], Error>
) {
  return useQuery({
    queryKey: ['costs', 'alerts'],
    queryFn: () => getBudgetAlerts(),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to create budget alert
 */
export function useCreateBudgetAlert(
  options?: UseMutationOptions<
    BudgetAlert,
    Error,
    { threshold: number; period: 'day' | 'week' | 'month' }
  >
) {
  return useMutation({
    mutationFn: ({ threshold, period }) => createBudgetAlert(threshold, period),
    ...options,
  });
}

/**
 * Hook to update budget alert
 */
export function useUpdateBudgetAlert(
  options?: UseMutationOptions<
    BudgetAlert,
    Error,
    { alertId: string; updates: Partial<{ threshold: number; period: 'day' | 'week' | 'month' }> }
  >
) {
  return useMutation({
    mutationFn: ({ alertId, updates }) => updateBudgetAlert(alertId, updates),
    ...options,
  });
}

/**
 * Hook to delete budget alert
 */
export function useDeleteBudgetAlert(
  options?: UseMutationOptions<{ id: string; deleted: boolean }, Error, string>
) {
  return useMutation({
    mutationFn: (alertId: string) => deleteBudgetAlert(alertId),
    ...options,
  });
}

/**
 * Hook to get cost trends
 */
export function useCostTrends(
  days: number = 30,
  options?: UseQueryOptions<Array<{ date: string; cost: number }>, Error>
) {
  return useQuery({
    queryKey: ['costs', 'trends', days],
    queryFn: () => getCostTrends(days),
    staleTime: 300000,
    ...options,
  });
}

/**
 * Hook to compare costs
 */
export function useCompareCosts(
  currentStart: number,
  currentEnd: number,
  previousStart: number,
  previousEnd: number,
  options?: UseQueryOptions<
    {
      current_cost: number;
      previous_cost: number;
      delta: number;
      delta_percentage: number;
    },
    Error
  >
) {
  return useQuery({
    queryKey: ['costs', 'compare', currentStart, currentEnd, previousStart, previousEnd],
    queryFn: () => compareCosts(currentStart, currentEnd, previousStart, previousEnd),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to get top cost drivers
 */
export function useTopCostDrivers(
  startTime: number,
  endTime: number,
  limit: number = 10,
  options?: UseQueryOptions<Array<{ name: string; cost: number; percentage: number }>, Error>
) {
  return useQuery({
    queryKey: ['costs', 'drivers', startTime, endTime, limit],
    queryFn: () => getTopCostDrivers(startTime, endTime, limit),
    staleTime: 60000,
    ...options,
  });
}

/**
 * Hook to get cache savings
 */
export function useCacheSavings(
  startTime: number,
  endTime: number,
  options?: UseQueryOptions<
    {
      total_savings: number;
      cache_hit_rate: number;
      cached_tokens: number;
      estimated_monthly_savings: number;
    },
    Error
  >
) {
  return useQuery({
    queryKey: ['costs', 'cache-savings', startTime, endTime],
    queryFn: () => getCacheSavings(startTime, endTime),
    staleTime: 60000,
    ...options,
  });
}
