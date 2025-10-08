/**
 * Rate Limits Dashboard
 * Main dashboard component for monitoring rate limits and API key usage
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  fetchRateLimitsOverview,
  fetchApiKeyRateLimits,
  fetchRateLimitBreaches,
  fetchThrottleAnalytics,
  fetchAbusePatterns,
  fetchTopConsumers,
  fetchTierDistribution,
  fetchTierUpgradeRecommendations,
  fetchRealTimeRateLimitData,
} from './api';
import {
  RateLimitsOverview as RateLimitsOverviewType,
  ApiKeyRateLimit,
  RateLimitBreach,
  ThrottleTimeSeries,
  AbusePattern,
  TopConsumer,
  TierDistribution,
  TierUpgradeRecommendation,
  RateLimitFilters,
} from './types';
import { RateLimitOverview } from './components/RateLimitOverview';
import { TierLimitsVisualization } from './components/TierLimitsVisualization';
import { UsageProgressBars } from './components/UsageProgressBars';
import { ThrottleAnalytics } from './components/ThrottleAnalytics';
import { AbusePatternDetection } from './components/AbusePatternDetection';
import { TopConsumers } from './components/TopConsumers';
import { RateLimitBreachesTimeline } from './components/RateLimitBreachesTimeline';
import { TierDistributionChart } from './components/TierDistributionChart';
import { TierUpgradeRecommendations } from './components/TierUpgradeRecommendations';
import './styles.css';

export const RateLimits: React.FC = () => {
  // State management
  const [overview, setOverview] = useState<RateLimitsOverviewType | null>(null);
  const [apiKeyLimits, setApiKeyLimits] = useState<ApiKeyRateLimit[]>([]);
  const [breaches, setBreaches] = useState<RateLimitBreach[]>([]);
  const [throttleData, setThrottleData] = useState<ThrottleTimeSeries[]>([]);
  const [abusePatterns, setAbusePatterns] = useState<AbusePattern[]>([]);
  const [topConsumers, setTopConsumers] = useState<TopConsumer[]>([]);
  const [tierDistribution, setTierDistribution] = useState<TierDistribution[]>([]);
  const [recommendations, setRecommendations] = useState<TierUpgradeRecommendation[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [realTimeMode, setRealTimeMode] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const [filters, setFilters] = useState<RateLimitFilters>({
    dateRange: {
      start: null,
      end: null,
    },
  });

  // Fetch all data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [
        overviewData,
        apiKeysData,
        breachesData,
        throttleAnalytics,
        patternsData,
        consumersData,
        distributionData,
        recommendationsData,
      ] = await Promise.all([
        fetchRateLimitsOverview(),
        fetchApiKeyRateLimits(filters),
        fetchRateLimitBreaches(100, filters),
        fetchThrottleAnalytics(
          Date.now() - 3600000, // Last hour
          Date.now(),
          '5m'
        ),
        fetchAbusePatterns(),
        fetchTopConsumers(10),
        fetchTierDistribution(),
        fetchTierUpgradeRecommendations(),
      ]);

      setOverview(overviewData);
      setApiKeyLimits(apiKeysData);
      setBreaches(breachesData);
      setThrottleData(throttleAnalytics);
      setAbusePatterns(patternsData);
      setTopConsumers(consumersData);
      setTierDistribution(distributionData);
      setRecommendations(recommendationsData);
      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
      console.error('Error fetching rate limits data:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Fetch real-time data (more frequent updates)
  const fetchRealTimeData = useCallback(async () => {
    if (!realTimeMode) return;

    try {
      const realTimeData = await fetchRealTimeRateLimitData();
      setApiKeyLimits(realTimeData.api_keys);
      setBreaches(realTimeData.active_breaches);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Error fetching real-time data:', err);
    }
  }, [realTimeMode]);

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchData();
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh, fetchData]);

  // Real-time updates every 5 seconds
  useEffect(() => {
    if (!realTimeMode) return;

    const interval = setInterval(() => {
      fetchRealTimeData();
    }, 5000);

    return () => clearInterval(interval);
  }, [realTimeMode, fetchRealTimeData]);

  const handleRefresh = () => {
    fetchData();
  };

  return (
    <div className="rate-limits-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-content">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="dashboard-title">
              <span className="title-icon">⚡</span>
              Rate Limits Analytics
            </h1>
            <p className="dashboard-subtitle">
              Real-time monitoring and analytics for API rate limits and throttling
            </p>
          </motion.div>
        </div>

        <div className="header-actions">
          <button
            className={`toggle-btn ${realTimeMode ? 'active' : ''}`}
            onClick={() => setRealTimeMode(!realTimeMode)}
            title={realTimeMode ? 'Disable real-time mode' : 'Enable real-time mode'}
          >
            {realTimeMode && (
              <span className="live-indicator">
                <span className="live-dot"></span>
              </span>
            )}
            {realTimeMode ? 'LIVE' : 'PAUSED'}
          </button>

          <button
            className={`toggle-btn ${autoRefresh ? 'active' : ''}`}
            onClick={() => setAutoRefresh(!autoRefresh)}
            title={autoRefresh ? 'Disable auto-refresh' : 'Enable auto-refresh'}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          </button>

          <button
            className="refresh-btn"
            onClick={handleRefresh}
            disabled={loading}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="error-banner"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </motion.div>
      )}

      {/* Main Content */}
      <div className="dashboard-content">
        {/* Overview Section */}
        {overview && (
          <RateLimitOverview overview={overview} loading={loading} />
        )}

        {/* Critical Alerts Section */}
        {(abusePatterns.length > 0 || (overview && overview.active_breaches > 0)) && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="alert-section"
          >
            <div className="alert-header">
              <span className="alert-icon">🚨</span>
              <span className="alert-title">Critical Alerts</span>
              <span className="alert-count">
                {abusePatterns.length + (overview?.active_breaches || 0)}
              </span>
            </div>
          </motion.div>
        )}

        {/* Tier Limits Visualization */}
        <TierLimitsVisualization />

        {/* Usage Progress Bars */}
        <UsageProgressBars
          apiKeyLimits={apiKeyLimits}
          loading={loading}
          realTime={realTimeMode}
        />

        {/* Two Column Layout */}
        <div className="grid-2-col">
          {/* Throttle Analytics */}
          <ThrottleAnalytics data={throttleData} loading={loading} />

          {/* Tier Distribution Chart */}
          <TierDistributionChart distribution={tierDistribution} loading={loading} />
        </div>

        {/* Abuse Pattern Detection */}
        <AbusePatternDetection patterns={abusePatterns} loading={loading} />

        {/* Top Consumers */}
        <TopConsumers consumers={topConsumers} loading={loading} />

        {/* Breaches Timeline */}
        <RateLimitBreachesTimeline breaches={breaches} loading={loading} />

        {/* Tier Upgrade Recommendations */}
        <TierUpgradeRecommendations recommendations={recommendations} loading={loading} />

        {/* Info Panel */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="info-panel"
        >
          <div className="info-card">
            <h3 className="info-title">Dashboard Information</h3>
            <div className="info-content">
              <div className="info-item">
                <span className="info-label">Last Updated</span>
                <span className="info-value">{lastUpdate.toLocaleTimeString()}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Refresh Rate</span>
                <span className="info-value">
                  {autoRefresh ? '30s' : 'Manual'}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Real-Time Mode</span>
                <span className="info-value">
                  {realTimeMode ? 'Active (5s)' : 'Disabled'}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">Total API Keys</span>
                <span className="info-value">{overview?.total_api_keys || 0}</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default RateLimits;
