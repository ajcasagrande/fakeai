/**
 * Costs and Billing API endpoints
 */

import { apiClient } from '../client';
import type {
  CostBreakdown,
  CostEstimate,
  BudgetAlert,
  ApiRequestConfig,
} from '../types';

/**
 * Get cost breakdown for a time period
 */
export async function getCostBreakdown(
  startTime: number,
  endTime: number,
  period: 'hour' | 'day' | 'week' | 'month' | 'year' = 'day',
  config?: ApiRequestConfig
): Promise<CostBreakdown> {
  const response = await apiClient.get<CostBreakdown>('/costs/breakdown', {
    ...config,
    params: {
      start_time: startTime,
      end_time: endTime,
      period,
    },
  });
  return response.data;
}

/**
 * Get cost by model for a time period
 */
export async function getCostByModel(
  startTime: number,
  endTime: number,
  config?: ApiRequestConfig
): Promise<Record<string, number>> {
  const breakdown = await getCostBreakdown(startTime, endTime, 'day', config);
  return breakdown.by_model;
}

/**
 * Get cost by service for a time period
 */
export async function getCostByService(
  startTime: number,
  endTime: number,
  config?: ApiRequestConfig
): Promise<Record<string, number>> {
  const breakdown = await getCostBreakdown(startTime, endTime, 'day', config);
  return breakdown.by_service;
}

/**
 * Get cost by project for a time period
 */
export async function getCostByProject(
  startTime: number,
  endTime: number,
  config?: ApiRequestConfig
): Promise<Record<string, number>> {
  const breakdown = await getCostBreakdown(startTime, endTime, 'day', config);
  return breakdown.by_project || {};
}

/**
 * Get cost estimate and projections
 */
export async function getCostEstimate(
  basedOnDays: number = 7,
  config?: ApiRequestConfig
): Promise<CostEstimate> {
  const response = await apiClient.get<CostEstimate>('/costs/estimate', {
    ...config,
    params: {
      based_on_days: basedOnDays,
    },
  });
  return response.data;
}

/**
 * Get current month cost
 */
export async function getCurrentMonthCost(
  config?: ApiRequestConfig
): Promise<number> {
  const now = new Date();
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
  const startTime = Math.floor(monthStart.getTime() / 1000);
  const endTime = Math.floor(Date.now() / 1000);

  const breakdown = await getCostBreakdown(startTime, endTime, 'month', config);
  return breakdown.total_cost;
}

/**
 * Get current day cost
 */
export async function getCurrentDayCost(
  config?: ApiRequestConfig
): Promise<number> {
  const now = new Date();
  const dayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startTime = Math.floor(dayStart.getTime() / 1000);
  const endTime = Math.floor(Date.now() / 1000);

  const breakdown = await getCostBreakdown(startTime, endTime, 'day', config);
  return breakdown.total_cost;
}

/**
 * Get budget alerts
 */
export async function getBudgetAlerts(
  config?: ApiRequestConfig
): Promise<BudgetAlert[]> {
  const response = await apiClient.get<{ alerts: BudgetAlert[] }>(
    '/costs/alerts',
    config
  );
  return response.data.alerts;
}

/**
 * Create budget alert
 */
export async function createBudgetAlert(
  threshold: number,
  period: 'day' | 'week' | 'month',
  config?: ApiRequestConfig
): Promise<BudgetAlert> {
  const response = await apiClient.post<BudgetAlert>(
    '/costs/alerts',
    {
      threshold,
      period,
    },
    config
  );
  return response.data;
}

/**
 * Update budget alert
 */
export async function updateBudgetAlert(
  alertId: string,
  updates: Partial<{ threshold: number; period: 'day' | 'week' | 'month' }>,
  config?: ApiRequestConfig
): Promise<BudgetAlert> {
  const response = await apiClient.patch<BudgetAlert>(
    `/costs/alerts/${alertId}`,
    updates,
    config
  );
  return response.data;
}

/**
 * Delete budget alert
 */
export async function deleteBudgetAlert(
  alertId: string,
  config?: ApiRequestConfig
): Promise<{ id: string; deleted: boolean }> {
  const response = await apiClient.delete(`/costs/alerts/${alertId}`, config);
  return response.data;
}

/**
 * Get cost trends over time
 */
export async function getCostTrends(
  days: number = 30,
  config?: ApiRequestConfig
): Promise<Array<{ date: string; cost: number }>> {
  const now = new Date();
  const startDate = new Date(now);
  startDate.setDate(startDate.getDate() - days);

  const startTime = Math.floor(startDate.getTime() / 1000);
  const endTime = Math.floor(Date.now() / 1000);

  const breakdown = await getCostBreakdown(startTime, endTime, 'day', config);

  // Convert to daily trend data
  const trends: Array<{ date: string; cost: number }> = [];
  const dailyCost = breakdown.total_cost / days;

  for (let i = 0; i < days; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    trends.push({
      date: date.toISOString().split('T')[0],
      cost: dailyCost,
    });
  }

  return trends;
}

/**
 * Compare costs between time periods
 */
export async function compareCosts(
  currentStart: number,
  currentEnd: number,
  previousStart: number,
  previousEnd: number,
  config?: ApiRequestConfig
): Promise<{
  current_cost: number;
  previous_cost: number;
  delta: number;
  delta_percentage: number;
}> {
  const [currentBreakdown, previousBreakdown] = await Promise.all([
    getCostBreakdown(currentStart, currentEnd, 'day', config),
    getCostBreakdown(previousStart, previousEnd, 'day', config),
  ]);

  const delta = currentBreakdown.total_cost - previousBreakdown.total_cost;
  const deltaPercentage =
    previousBreakdown.total_cost > 0
      ? (delta / previousBreakdown.total_cost) * 100
      : 0;

  return {
    current_cost: currentBreakdown.total_cost,
    previous_cost: previousBreakdown.total_cost,
    delta,
    delta_percentage: deltaPercentage,
  };
}

/**
 * Get top cost drivers
 */
export async function getTopCostDrivers(
  startTime: number,
  endTime: number,
  limit: number = 10,
  config?: ApiRequestConfig
): Promise<Array<{ name: string; cost: number; percentage: number }>> {
  const breakdown = await getCostBreakdown(startTime, endTime, 'day', config);

  const drivers = Object.entries(breakdown.by_model).map(([name, cost]) => ({
    name,
    cost,
    percentage: (cost / breakdown.total_cost) * 100,
  }));

  drivers.sort((a, b) => b.cost - a.cost);
  return drivers.slice(0, limit);
}

/**
 * Calculate estimated savings from caching
 */
export async function getCacheSavings(
  startTime: number,
  endTime: number,
  config?: ApiRequestConfig
): Promise<{
  total_savings: number;
  cache_hit_rate: number;
  cached_tokens: number;
  estimated_monthly_savings: number;
}> {
  const response = await apiClient.get('/costs/cache-savings', {
    ...config,
    params: {
      start_time: startTime,
      end_time: endTime,
    },
  });
  return response.data;
}

/**
 * Format cost for display
 */
export function formatCost(cost: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(cost);
}
