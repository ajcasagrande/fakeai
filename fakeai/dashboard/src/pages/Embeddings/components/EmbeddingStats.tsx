/**
 * Embedding Statistics Component
 * Displays key metrics for embedding operations
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { EmbeddingMetrics } from '../types';

interface EmbeddingStatsProps {
  metrics: EmbeddingMetrics;
  isLoading?: boolean;
}

export const EmbeddingStats: React.FC<EmbeddingStatsProps> = ({ metrics, isLoading }) => {
  if (isLoading) {
    return (
      <div className="stats-grid">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="stat-card">
            <div className="stat-label">Loading...</div>
            <div className="stat-value">
              <div className="loading-spinner" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
    return num.toFixed(0);
  };

  const formatRate = (rate: number): string => {
    return rate.toFixed(2);
  };

  const formatTime = (ms: number): string => {
    if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`;
    return `${ms.toFixed(0)}ms`;
  };

  return (
    <div className="stats-grid">
      <div className="stat-card">
        <div className="stat-label">Total Requests</div>
        <div className="stat-value">{formatNumber(metrics.total_requests)}</div>
        <div className="stat-change positive">
          <span>↑</span>
          <span>24h trend</span>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-label">Total Tokens</div>
        <div className="stat-value">{formatNumber(metrics.total_tokens)}</div>
        <div className="stat-change positive">
          <span>↑</span>
          <span>Token usage</span>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-label">Avg Processing Time</div>
        <div className="stat-value">{formatTime(metrics.avg_processing_time)}</div>
        <div className="stat-change negative">
          <span>↓</span>
          <span>Faster than avg</span>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-label">Requests/Second</div>
        <div className="stat-value">{formatRate(metrics.requests_per_second)}</div>
        <div className="stat-change positive">
          <span>↑</span>
          <span>Current rate</span>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-label">Tokens/Second</div>
        <div className="stat-value">{formatRate(metrics.tokens_per_second)}</div>
        <div className="stat-change positive">
          <span>↑</span>
          <span>Throughput</span>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-label">Error Rate</div>
        <div className="stat-value" style={{ color: metrics.error_rate > 5 ? 'var(--error-red)' : 'var(--success-green)' }}>
          {metrics.error_rate.toFixed(2)}%
        </div>
        <div className={`stat-change ${metrics.error_rate < 1 ? 'positive' : 'negative'}`}>
          <span>{metrics.error_rate < 1 ? '✓' : '⚠'}</span>
          <span>{metrics.error_rate < 1 ? 'Healthy' : 'Monitor'}</span>
        </div>
      </div>
    </div>
  );
};
