/**
 * Cost Overview Component
 * Displays high-level cost metrics and trends
 */

import React from 'react';
import { CostData, CostTrend } from '../types';

interface CostOverviewProps {
  costData: CostData | null;
  loading: boolean;
}

export const CostOverview: React.FC<CostOverviewProps> = ({ costData, loading }) => {
  const formatCost = (cost: number): string => {
    if (cost >= 1000) {
      return `$${(cost / 1000).toFixed(2)}K`;
    }
    if (cost >= 1) {
      return `$${cost.toFixed(2)}`;
    }
    if (cost >= 0.01) {
      return `$${cost.toFixed(4)}`;
    }
    return `$${cost.toFixed(6)}`;
  };

  const formatTrend = (trend: CostTrend) => {
    const isPositive = trend.change_percentage > 0;
    const absChange = Math.abs(trend.change_percentage);
    return {
      sign: isPositive ? '+' : '-',
      value: absChange.toFixed(1),
      color: isPositive ? '#FF6B6B' : '#76B900',
      icon: isPositive ? '↑' : '↓',
    };
  };

  if (loading) {
    return (
      <div className="cost-overview-grid">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="overview-card loading">
            <div className="skeleton-icon"></div>
            <div className="skeleton-text"></div>
            <div className="skeleton-value"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!costData) {
    return (
      <div className="cost-overview-grid">
        <div className="overview-card">
          <p className="no-data">No cost data available</p>
        </div>
      </div>
    );
  }

  const trend = formatTrend(costData.cost_trend);
  const avgDailyCost = costData.daily_costs.length > 0
    ? costData.total_cost / costData.daily_costs.length
    : 0;

  const totalRequests = costData.daily_costs.reduce((sum, day) => sum + day.request_count, 0);
  const avgCostPerRequest = totalRequests > 0 ? costData.total_cost / totalRequests : 0;

  return (
    <div className="cost-overview-grid">
      {/* Total Cost Card */}
      <div className="overview-card primary">
        <div className="card-header">
          <div className="card-icon total-cost">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="card-info">
            <h3 className="card-title">Total Cost</h3>
            <p className="card-subtitle">Period total</p>
          </div>
        </div>
        <div className="card-value-section">
          <div className="card-value">{formatCost(costData.total_cost)}</div>
          <div className={`card-trend ${costData.cost_trend.trend}`}>
            <span className="trend-icon" style={{ color: trend.color }}>{trend.icon}</span>
            <span className="trend-value" style={{ color: trend.color }}>
              {trend.sign}{trend.value}%
            </span>
            <span className="trend-label">vs previous period</span>
          </div>
        </div>
      </div>

      {/* Average Daily Cost Card */}
      <div className="overview-card">
        <div className="card-header">
          <div className="card-icon daily-cost">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <div className="card-info">
            <h3 className="card-title">Avg Daily Cost</h3>
            <p className="card-subtitle">Average per day</p>
          </div>
        </div>
        <div className="card-value-section">
          <div className="card-value">{formatCost(avgDailyCost)}</div>
          <div className="card-detail">
            Based on {costData.daily_costs.length} days
          </div>
        </div>
      </div>

      {/* Cost per Request Card */}
      <div className="overview-card">
        <div className="card-header">
          <div className="card-icon per-request">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <div className="card-info">
            <h3 className="card-title">Avg Cost/Request</h3>
            <p className="card-subtitle">Per API request</p>
          </div>
        </div>
        <div className="card-value-section">
          <div className="card-value">{formatCost(avgCostPerRequest)}</div>
          <div className="card-detail">
            {totalRequests.toLocaleString()} total requests
          </div>
        </div>
      </div>

      {/* Active Services Card */}
      <div className="overview-card">
        <div className="card-header">
          <div className="card-icon services">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
          </div>
          <div className="card-info">
            <h3 className="card-title">Active Services</h3>
            <p className="card-subtitle">With costs</p>
          </div>
        </div>
        <div className="card-value-section">
          <div className="card-value">{costData.costs_by_service.length}</div>
          <div className="card-detail">
            {costData.costs_by_model.length} models
          </div>
        </div>
      </div>
    </div>
  );
};
