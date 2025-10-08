/**
 * Cache Metrics Overview Component
 * Displays high-level KV cache statistics in card format
 */

import React from 'react';
import { KVCacheMetrics } from '../types';

interface CacheMetricsOverviewProps {
  metrics: KVCacheMetrics;
  loading?: boolean;
}

export const CacheMetricsOverview: React.FC<CacheMetricsOverviewProps> = ({
  metrics,
  loading,
}) => {
  if (loading) {
    return (
      <div className="metrics-overview-container">
        <div className="metrics-grid">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="metric-card skeleton">
              <div className="skeleton-text"></div>
              <div className="skeleton-value"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const formatNumber = (num: number): string => {
    if (num >= 1000000000) {
      return `${(num / 1000000000).toFixed(2)}B`;
    }
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(2)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(2)}K`;
    }
    return num.toFixed(0);
  };

  const formatBytes = (bytes: number): string => {
    if (bytes >= 1073741824) {
      return `${(bytes / 1073741824).toFixed(2)} GB`;
    }
    if (bytes >= 1048576) {
      return `${(bytes / 1048576).toFixed(2)} MB`;
    }
    if (bytes >= 1024) {
      return `${(bytes / 1024).toFixed(2)} KB`;
    }
    return `${bytes} B`;
  };

  const formatCurrency = (amount: number): string => {
    return `$${amount.toFixed(2)}`;
  };

  const getHitRateStatus = (rate: number): string => {
    if (rate >= 80) return 'excellent';
    if (rate >= 60) return 'good';
    if (rate >= 40) return 'warning';
    return 'poor';
  };

  const getWarmupStatusColor = (status: string): string => {
    switch (status) {
      case 'hot':
        return 'status-hot';
      case 'warm':
        return 'status-warm';
      case 'warming':
        return 'status-warming';
      default:
        return 'status-cold';
    }
  };

  return (
    <div className="metrics-overview-container">
      <div className="metrics-grid cache-metrics">
        <div className={`metric-card hit-rate ${getHitRateStatus(metrics.cache_hit_rate)}`}>
          <div className="metric-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="metric-content">
            <div className="metric-label">Cache Hit Rate</div>
            <div className="metric-value">{metrics.cache_hit_rate.toFixed(2)}%</div>
            <div className="metric-subtitle">
              {formatNumber(metrics.total_cache_hits)} hits / {formatNumber(metrics.total_cache_misses)} misses
            </div>
          </div>
        </div>

        <div className="metric-card speedup">
          <div className="metric-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
          </div>
          <div className="metric-content">
            <div className="metric-label">Avg Speedup</div>
            <div className="metric-value">{metrics.avg_speedup_factor.toFixed(2)}x</div>
            <div className="metric-subtitle">
              {metrics.speedup_with_cache_ms.toFixed(0)}ms vs {metrics.speedup_without_cache_ms.toFixed(0)}ms
            </div>
          </div>
        </div>

        <div className="metric-card cache-size">
          <div className="metric-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
          </div>
          <div className="metric-content">
            <div className="metric-label">Cache Size</div>
            <div className="metric-value">{formatBytes(metrics.cache_size_bytes)}</div>
            <div className="metric-subtitle">
              {metrics.cache_utilization_percent.toFixed(1)}% of {formatBytes(metrics.max_cache_size_bytes)}
            </div>
          </div>
        </div>

        <div className="metric-card tokens-saved">
          <div className="metric-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="metric-content">
            <div className="metric-label">Tokens Saved</div>
            <div className="metric-value">{formatNumber(metrics.tokens_saved)}</div>
            <div className="metric-subtitle">
              {metrics.token_savings_percent.toFixed(1)}% savings
            </div>
          </div>
        </div>

        <div className="metric-card memory">
          <div className="metric-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
              />
            </svg>
          </div>
          <div className="metric-content">
            <div className="metric-label">Memory Usage</div>
            <div className="metric-value">{formatBytes(metrics.memory_used_bytes)}</div>
            <div className="metric-subtitle">
              {metrics.memory_utilization_percent.toFixed(1)}% utilized
            </div>
          </div>
        </div>

        <div className="metric-card evictions">
          <div className="metric-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </div>
          <div className="metric-content">
            <div className="metric-label">Evictions</div>
            <div className="metric-value">{formatNumber(metrics.eviction_count)}</div>
            <div className="metric-subtitle">
              {metrics.eviction_rate.toFixed(2)}/s rate
            </div>
          </div>
        </div>

        <div className={`metric-card warmup ${getWarmupStatusColor(metrics.cache_warmup_status)}`}>
          <div className="metric-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"
              />
            </svg>
          </div>
          <div className="metric-content">
            <div className="metric-label">Warmup Status</div>
            <div className="metric-value status-text">
              {metrics.cache_warmup_status.toUpperCase()}
            </div>
            <div className="metric-subtitle">
              {metrics.cache_warmup_percent.toFixed(0)}% complete
            </div>
          </div>
        </div>

        <div className="metric-card cost-savings">
          <div className="metric-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="metric-content">
            <div className="metric-label">Cost Savings</div>
            <div className="metric-value cost">{formatCurrency(metrics.cost_savings_total)}</div>
            <div className="metric-subtitle">
              {formatCurrency(metrics.cost_with_cache)} vs {formatCurrency(metrics.cost_without_cache)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
