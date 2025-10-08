/**
 * KV Cache Analytics Dashboard
 * Main dashboard component for monitoring KV cache performance and efficiency
 */

import React, { useState, useEffect, useCallback } from 'react';
import { fetchKVCacheMetrics, fetchCacheEnabledModels, triggerCacheWarmup, clearCache } from './api';
import {
  KVCacheMetrics,
  ModelCacheEfficiency,
  CacheTimeSeriesData,
  CacheEvictionStats,
  CacheWarmupStatus,
  CachePerformanceImpact,
  CacheCostSavings,
  DashboardFilters,
} from './types';
import { CacheMetricsOverview } from './components/CacheMetricsOverview';
import { HitMissChart } from './components/HitMissChart';
import { CacheSizeUtilization } from './components/CacheSizeUtilization';
import { SpeedupMetrics } from './components/SpeedupMetrics';
import { TokenSavings } from './components/TokenSavings';
import { ModelEfficiency } from './components/ModelEfficiency';
import { EvictionStats } from './components/EvictionStats';
import { WarmupStatus } from './components/WarmupStatus';
import { CostSavings } from './components/CostSavings';
import './styles.css';

export const KVCache: React.FC = () => {
  // State management
  const [metrics, setMetrics] = useState<KVCacheMetrics | null>(null);
  const [modelEfficiency, setModelEfficiency] = useState<ModelCacheEfficiency[]>([]);
  const [timeSeries, setTimeSeries] = useState<CacheTimeSeriesData[]>([]);
  const [evictionStats, setEvictionStats] = useState<CacheEvictionStats | null>(null);
  const [warmupStatus, setWarmupStatus] = useState<CacheWarmupStatus | null>(null);
  const [performanceImpact, setPerformanceImpact] = useState<CachePerformanceImpact | null>(null);
  const [costSavings, setCostSavings] = useState<CacheCostSavings | null>(null);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [filters, setFilters] = useState<DashboardFilters>({
    model: null,
    dateRange: {
      start: null,
      end: null,
    },
    timeGranularity: '1h',
  });

  // Fetch data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const startTime = filters.dateRange.start?.getTime();
      const endTime = filters.dateRange.end?.getTime();

      const data = await fetchKVCacheMetrics(
        startTime,
        endTime,
        filters.model || undefined,
        filters.timeGranularity
      );

      setMetrics(data.metrics);
      setModelEfficiency(data.model_efficiency);
      setTimeSeries(data.time_series);
      setEvictionStats(data.eviction_stats);
      setWarmupStatus(data.warmup_status);
      setPerformanceImpact(data.performance_impact);
      setCostSavings(data.cost_savings);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch KV cache metrics');
      console.error('Error fetching KV cache data:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Fetch available models
  const fetchModels = useCallback(async () => {
    try {
      const models = await fetchCacheEnabledModels();
      setAvailableModels(models);
    } catch (err) {
      console.error('Error fetching available models:', err);
    }
  }, []);

  // Handle cache warmup trigger
  const handleTriggerWarmup = useCallback(async () => {
    if (!filters.model) {
      alert('Please select a model first');
      return;
    }

    try {
      await triggerCacheWarmup(filters.model);
      // Refresh data after triggering warmup
      await fetchData();
    } catch (err) {
      alert(`Failed to trigger cache warmup: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }, [filters.model, fetchData]);

  // Handle cache clear
  const handleClearCache = useCallback(async () => {
    const confirmMessage = filters.model
      ? `Are you sure you want to clear the cache for ${filters.model}?`
      : 'Are you sure you want to clear ALL caches?';

    if (!confirm(confirmMessage)) {
      return;
    }

    try {
      await clearCache(filters.model || undefined);
      // Refresh data after clearing cache
      await fetchData();
    } catch (err) {
      alert(`Failed to clear cache: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }, [filters.model, fetchData]);

  // Initial data fetch
  useEffect(() => {
    fetchData();
    fetchModels();
  }, [fetchData, fetchModels]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchData();
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh, fetchData]);

  return (
    <div className="kv-cache-dashboard">
      <div className="dashboard-header">
        <div className="header-content">
          <h1 className="dashboard-title">KV Cache Analytics</h1>
          <p className="dashboard-subtitle">
            Real-time monitoring and performance analysis for KV cache optimization
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
          <button className="clear-cache-btn" onClick={handleClearCache} disabled={loading}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
            Clear Cache
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
          {metrics && <CacheMetricsOverview metrics={metrics} loading={loading} />}

          <div className="grid-2-col">
            <div className="card">
              {timeSeries && <HitMissChart data={timeSeries} loading={loading} />}
            </div>

            <div className="card">
              {timeSeries && <CacheSizeUtilization data={timeSeries} loading={loading} />}
            </div>
          </div>

          <div className="card">
            {timeSeries && performanceImpact && (
              <SpeedupMetrics
                timeSeries={timeSeries}
                performanceImpact={performanceImpact}
                loading={loading}
              />
            )}
          </div>

          <div className="card">
            {timeSeries && metrics && (
              <TokenSavings timeSeries={timeSeries} metrics={metrics} loading={loading} />
            )}
          </div>

          <div className="card">
            <ModelEfficiency models={modelEfficiency} loading={loading} />
          </div>

          <div className="grid-2-col">
            <div className="card">
              {evictionStats && timeSeries && (
                <EvictionStats
                  evictionStats={evictionStats}
                  timeSeries={timeSeries}
                  loading={loading}
                />
              )}
            </div>

            <div className="card">
              {warmupStatus && (
                <WarmupStatus
                  warmupStatus={warmupStatus}
                  onTriggerWarmup={handleTriggerWarmup}
                  loading={loading}
                />
              )}
            </div>
          </div>

          <div className="card">
            {costSavings && <CostSavings costSavings={costSavings} loading={loading} />}
          </div>
        </div>

        <div className="sidebar-section">
          <div className="card filter-panel">
            <h3 className="card-title">Filters</h3>
            <div className="filter-content">
              <div className="filter-group">
                <label className="filter-label">Model</label>
                <select
                  className="filter-select"
                  value={filters.model || ''}
                  onChange={(e) =>
                    setFilters({ ...filters, model: e.target.value || null })
                  }
                >
                  <option value="">All Models</option>
                  {availableModels.map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
              </div>

              <div className="filter-group">
                <label className="filter-label">Time Granularity</label>
                <select
                  className="filter-select"
                  value={filters.timeGranularity}
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      timeGranularity: e.target.value as any,
                    })
                  }
                >
                  <option value="1m">1 Minute</option>
                  <option value="5m">5 Minutes</option>
                  <option value="15m">15 Minutes</option>
                  <option value="1h">1 Hour</option>
                  <option value="1d">1 Day</option>
                </select>
              </div>

              <div className="filter-group">
                <label className="filter-label">Date Range</label>
                <input
                  type="datetime-local"
                  className="filter-input"
                  value={
                    filters.dateRange.start
                      ? filters.dateRange.start.toISOString().slice(0, 16)
                      : ''
                  }
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      dateRange: {
                        ...filters.dateRange,
                        start: e.target.value ? new Date(e.target.value) : null,
                      },
                    })
                  }
                  placeholder="Start date"
                />
                <input
                  type="datetime-local"
                  className="filter-input"
                  value={
                    filters.dateRange.end
                      ? filters.dateRange.end.toISOString().slice(0, 16)
                      : ''
                  }
                  onChange={(e) =>
                    setFilters({
                      ...filters,
                      dateRange: {
                        ...filters.dateRange,
                        end: e.target.value ? new Date(e.target.value) : null,
                      },
                    })
                  }
                  placeholder="End date"
                />
              </div>

              <button className="apply-filters-btn" onClick={fetchData}>
                Apply Filters
              </button>
            </div>
          </div>

          <div className="card info-card">
            <h3 className="card-title">Dashboard Info</h3>
            <div className="info-content">
              <div className="info-item">
                <span className="info-label">Last Updated</span>
                <span className="info-value">{new Date().toLocaleTimeString()}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Refresh Rate</span>
                <span className="info-value">{autoRefresh ? '30s' : 'Manual'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Active Models</span>
                <span className="info-value">{modelEfficiency.length}</span>
              </div>
              {metrics && (
                <>
                  <div className="info-item">
                    <span className="info-label">Hit Rate</span>
                    <span className="info-value">{metrics.cache_hit_rate.toFixed(2)}%</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Cache Status</span>
                    <span className="info-value status">
                      {warmupStatus?.status.toUpperCase() || 'UNKNOWN'}
                    </span>
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="card legend-card">
            <h3 className="card-title">Performance Indicators</h3>
            <div className="legend-content">
              <div className="legend-item">
                <span className="legend-color excellent"></span>
                <span className="legend-text">Excellent (80%+)</span>
              </div>
              <div className="legend-item">
                <span className="legend-color good"></span>
                <span className="legend-text">Good (60-80%)</span>
              </div>
              <div className="legend-item">
                <span className="legend-color warning"></span>
                <span className="legend-text">Warning (40-60%)</span>
              </div>
              <div className="legend-item">
                <span className="legend-color poor"></span>
                <span className="legend-text">Poor (&lt;40%)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KVCache;
