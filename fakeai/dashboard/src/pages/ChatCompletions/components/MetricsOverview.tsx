/**
 * Metrics Overview Component
 * Displays high-level statistics in card format
 */

import React from 'react';
import { MetricsOverview as MetricsOverviewType } from '../types';

interface MetricsOverviewProps {
  metrics: MetricsOverviewType;
  loading?: boolean;
}

export const MetricsOverview: React.FC<MetricsOverviewProps> = ({ metrics, loading }) => {
  if (loading) {
    return (
      <div className="metrics-overview-container">
        <div className="metrics-grid">
          {[...Array(6)].map((_, i) => (
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
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(2)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(2)}K`;
    }
    return num.toFixed(0);
  };

  const formatCurrency = (amount: number): string => {
    return `$${amount.toFixed(4)}`;
  };

  return (
    <div className="metrics-overview-container">
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Total Requests</div>
          <div className="metric-value">{formatNumber(metrics.total_requests)}</div>
          <div className="metric-subtitle">
            {metrics.requests_per_second.toFixed(2)} req/s
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Total Tokens</div>
          <div className="metric-value">{formatNumber(metrics.total_tokens)}</div>
          <div className="metric-subtitle">Prompt + Completion</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Total Cost</div>
          <div className="metric-value cost">{formatCurrency(metrics.total_cost)}</div>
          <div className="metric-subtitle">All requests</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Avg Latency</div>
          <div className="metric-value latency">
            {metrics.avg_latency_ms.toFixed(0)}
            <span className="metric-unit">ms</span>
          </div>
          <div className="metric-subtitle">Response time</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Error Rate</div>
          <div className={`metric-value ${metrics.error_rate > 5 ? 'error' : metrics.error_rate > 2 ? 'warning' : 'success'}`}>
            {metrics.error_rate.toFixed(2)}%
          </div>
          <div className="metric-subtitle">Failed requests</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Streaming</div>
          <div className="metric-value streaming">
            {metrics.streaming_percentage.toFixed(1)}%
          </div>
          <div className="metric-subtitle">of requests</div>
        </div>
      </div>
    </div>
  );
};
