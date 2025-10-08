/**
 * Token Savings Component
 * Displays token savings from cache usage
 */

import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { CacheTimeSeriesData, KVCacheMetrics } from '../types';

interface TokenSavingsProps {
  timeSeries: CacheTimeSeriesData[];
  metrics: KVCacheMetrics;
  loading?: boolean;
}

export const TokenSavings: React.FC<TokenSavingsProps> = ({
  timeSeries,
  metrics,
  loading,
}) => {
  if (loading) {
    return (
      <div className="chart-container">
        <div className="chart-skeleton"></div>
      </div>
    );
  }

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

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

  const chartData = timeSeries.map((item) => ({
    timestamp: item.timestamp,
    time: formatTimestamp(item.timestamp),
    tokensSaved: item.tokens_saved,
  }));

  const pieData = [
    {
      name: 'Tokens Saved',
      value: metrics.tokens_saved,
      color: '#76b900',
    },
    {
      name: 'Tokens Processed',
      value: metrics.total_tokens_processed - metrics.tokens_saved,
      color: '#555',
    },
  ];

  return (
    <div className="token-savings">
      <div className="card-header">
        <h3 className="card-title">Token Savings from Cache</h3>
        <div className="savings-badge">
          <span className="badge-label">Total Saved:</span>
          <span className="badge-value">{formatNumber(metrics.tokens_saved)}</span>
        </div>
      </div>

      <div className="token-savings-content">
        <div className="chart-section">
          <h4 className="section-title">Cumulative Token Savings</h4>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart
              data={chartData}
              margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="tokenSavingsGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#76b900" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#76b900" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="time"
                stroke="#999"
                style={{ fontSize: '12px' }}
              />
              <YAxis
                stroke="#999"
                style={{ fontSize: '12px' }}
                tickFormatter={(value) => formatNumber(value)}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1a1a',
                  border: '1px solid #333',
                  borderRadius: '8px',
                }}
                formatter={(value: number) => [formatNumber(value), 'Tokens Saved']}
              />
              <Area
                type="monotone"
                dataKey="tokensSaved"
                stroke="#76b900"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#tokenSavingsGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="pie-section">
          <h4 className="section-title">Token Distribution</h4>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1a1a1a',
                  border: '1px solid #333',
                  borderRadius: '8px',
                }}
                formatter={(value: number) => formatNumber(value)}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="token-stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Tokens Processed</div>
          <div className="stat-value">{formatNumber(metrics.total_tokens_processed)}</div>
        </div>

        <div className="stat-card highlight">
          <div className="stat-label">Tokens Saved</div>
          <div className="stat-value">{formatNumber(metrics.tokens_saved)}</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Savings Percentage</div>
          <div className="stat-value">{metrics.token_savings_percent.toFixed(2)}%</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Avg Tokens per Hit</div>
          <div className="stat-value">{formatNumber(metrics.avg_tokens_per_hit)}</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Avg Tokens per Miss</div>
          <div className="stat-value">{formatNumber(metrics.avg_tokens_per_miss)}</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Efficiency Ratio</div>
          <div className="stat-value">
            {(metrics.avg_tokens_per_hit / metrics.avg_tokens_per_miss).toFixed(2)}x
          </div>
        </div>
      </div>
    </div>
  );
};
