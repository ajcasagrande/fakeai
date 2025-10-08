/**
 * Cost Tracking Dashboard
 * Comprehensive cost tracking and analytics dashboard
 */

import React, { useState, useEffect, useCallback } from 'react';
import { fetchComprehensiveCostData } from './api';
import { CostData, CostFilters as CostFiltersType } from './types';
import { CostOverview } from './components/CostOverview';
import { ServiceBreakdown } from './components/ServiceBreakdown';
import { ModelCostChart } from './components/ModelCostChart';
import { CostTrends } from './components/CostTrends';
import { TopContributors } from './components/TopContributors';
import { BudgetAlerts } from './components/BudgetAlerts';
import { CostProjections } from './components/CostProjections';
import { ExportReports } from './components/ExportReports';
import { CostFilters } from './components/CostFilters';
import { EfficiencyMetrics } from './components/EfficiencyMetrics';
import './styles.css';

export const Costs: React.FC = () => {
  // State management
  const [costData, setCostData] = useState<CostData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [filters, setFilters] = useState<CostFiltersType>({
    dateRange: {
      start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // Last 30 days
      end: new Date(),
      preset: 'last30days',
    },
    service: null,
    model: null,
    groupBy: 'day',
  });

  // Fetch cost data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const startTime = filters.dateRange.start
        ? Math.floor(filters.dateRange.start.getTime() / 1000)
        : Math.floor((Date.now() - 30 * 24 * 60 * 60 * 1000) / 1000);

      const endTime = filters.dateRange.end
        ? Math.floor(filters.dateRange.end.getTime() / 1000)
        : Math.floor(Date.now() / 1000);

      const data = await fetchComprehensiveCostData(
        startTime,
        endTime,
        filters.groupBy === 'day' ? '1d' : filters.groupBy === 'week' ? '1w' : '1mo'
      );

      // Apply filters
      let filteredData = { ...data };

      if (filters.service) {
        filteredData.costs_by_service = data.costs_by_service.filter(
          (s) => s.service === filters.service
        );
        filteredData.costs_by_model = data.costs_by_model.filter(
          (m) => m.service === filters.service
        );
      }

      if (filters.model) {
        filteredData.costs_by_model = data.costs_by_model.filter(
          (m) => m.model === filters.model
        );
      }

      setCostData(filteredData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch cost data');
      console.error('Error fetching cost data:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh every 5 minutes
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchData();
    }, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, fetchData]);

  // Extract available services and models for filters
  const availableServices = React.useMemo(() => {
    if (!costData) return [];
    return costData.costs_by_service.map((s) => s.service);
  }, [costData]);

  const availableModels = React.useMemo(() => {
    if (!costData) return [];
    return costData.costs_by_model.map((m) => m.model);
  }, [costData]);

  // Calculate metrics
  const totalRequests = React.useMemo(() => {
    if (!costData) return 0;
    return costData.daily_costs.reduce((sum, d) => sum + d.request_count, 0);
  }, [costData]);

  const avgDailyCost = React.useMemo(() => {
    if (!costData || costData.daily_costs.length === 0) return 0;
    return costData.total_cost / costData.daily_costs.length;
  }, [costData]);

  return (
    <div className="costs-dashboard">
      <div className="dashboard-header">
        <div className="header-content">
          <h1 className="dashboard-title">Cost Tracking Dashboard</h1>
          <p className="dashboard-subtitle">
            Comprehensive cost analytics and budget monitoring
          </p>
        </div>
        <div className="header-actions">
          <button
            className={`refresh-toggle ${autoRefresh ? 'active' : ''}`}
            onClick={() => setAutoRefresh(!autoRefresh)}
            title={autoRefresh ? 'Disable auto-refresh' : 'Enable auto-refresh'}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          </button>
          <button className="manual-refresh-btn" onClick={fetchData} disabled={loading}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          {error}
        </div>
      )}

      <div className="dashboard-content">
        <div className="main-section">
          {/* Cost Overview Cards */}
          <CostOverview costData={costData} loading={loading} />

          {/* Budget Alerts */}
          <div className="card">
            <BudgetAlerts
              totalCost={costData?.total_cost || 0}
              dailyAverage={avgDailyCost}
            />
          </div>

          {/* Cost Trends Chart */}
          <div className="card">
            <CostTrends dailyCosts={costData?.daily_costs || []} loading={loading} />
          </div>

          {/* Service and Model Breakdown */}
          <div className="grid-2-col">
            <div className="card">
              <ServiceBreakdown
                services={costData?.costs_by_service || []}
                loading={loading}
              />
            </div>
            <div className="card">
              <TopContributors
                models={costData?.costs_by_model || []}
                services={costData?.costs_by_service || []}
                loading={loading}
              />
            </div>
          </div>

          {/* Model Cost Chart */}
          <div className="card">
            <ModelCostChart models={costData?.costs_by_model || []} loading={loading} />
          </div>

          {/* Efficiency Metrics */}
          <div className="card">
            <EfficiencyMetrics
              models={costData?.costs_by_model || []}
              totalCost={costData?.total_cost || 0}
              totalRequests={totalRequests}
              loading={loading}
            />
          </div>

          {/* Cost Projections */}
          <div className="card">
            <CostProjections dailyCosts={costData?.daily_costs || []} loading={loading} />
          </div>

          {/* Export Reports */}
          <div className="card">
            <ExportReports
              startTime={
                filters.dateRange.start
                  ? Math.floor(filters.dateRange.start.getTime() / 1000)
                  : Math.floor((Date.now() - 30 * 24 * 60 * 60 * 1000) / 1000)
              }
              endTime={
                filters.dateRange.end
                  ? Math.floor(filters.dateRange.end.getTime() / 1000)
                  : Math.floor(Date.now() / 1000)
              }
            />
          </div>
        </div>

        <div className="sidebar-section">
          <div className="card">
            <CostFilters
              filters={filters}
              availableServices={availableServices}
              availableModels={availableModels}
              onFiltersChange={setFilters}
            />
          </div>

          <div className="card info-card">
            <h3 className="card-title">Dashboard Info</h3>
            <div className="info-content">
              <div className="info-item">
                <span className="info-label">Last Updated</span>
                <span className="info-value">{new Date().toLocaleTimeString()}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Date Range</span>
                <span className="info-value">
                  {filters.dateRange.start?.toLocaleDateString() || 'N/A'} -{' '}
                  {filters.dateRange.end?.toLocaleDateString() || 'N/A'}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Total Days</span>
                <span className="info-value">{costData?.daily_costs.length || 0}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Refresh Rate</span>
                <span className="info-value">{autoRefresh ? '5 min' : 'Manual'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Costs;
