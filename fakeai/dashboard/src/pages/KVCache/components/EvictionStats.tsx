/**
 * Eviction Statistics Component
 * Displays cache eviction metrics and reasons
 */

import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { CacheEvictionStats, CacheTimeSeriesData } from '../types';

interface EvictionStatsProps {
  evictionStats: CacheEvictionStats;
  timeSeries: CacheTimeSeriesData[];
  loading?: boolean;
}

const COLORS = ['#76b900', '#00bfff', '#ff9900', '#ff6b6b', '#9d4edd', '#06ffa5'];

export const EvictionStats: React.FC<EvictionStatsProps> = ({
  evictionStats,
  timeSeries,
  loading,
}) => {
  if (loading) {
    return (
      <div className="chart-container">
        <div className="chart-skeleton"></div>
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

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Prepare data for eviction reasons pie chart
  const evictionReasonData = Object.entries(evictionStats.eviction_reasons).map(
    ([reason, count]) => ({
      name: reason.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
      value: count,
      percentage: (count / evictionStats.total_evictions) * 100,
    })
  );

  // Prepare data for evictions over time
  const evictionTimelineData = timeSeries.map((item) => ({
    time: formatTimestamp(item.timestamp),
    evictions: item.evictions,
  }));

  return (
    <div className="eviction-stats">
      <div className="card-header">
        <h3 className="card-title">Cache Eviction Statistics</h3>
        <div className="eviction-badge">
          <span className="badge-label">Total Evictions:</span>
          <span className="badge-value">{formatNumber(evictionStats.total_evictions)}</span>
        </div>
      </div>

      <div className="eviction-content">
        <div className="eviction-overview">
          <div className="overview-card">
            <div className="overview-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </div>
            <div className="overview-content">
              <div className="overview-label">Total Evictions</div>
              <div className="overview-value">{formatNumber(evictionStats.total_evictions)}</div>
            </div>
          </div>

          <div className="overview-card">
            <div className="overview-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div className="overview-content">
              <div className="overview-label">Avg Cache Age on Eviction</div>
              <div className="overview-value">
                {(evictionStats.avg_cache_age_on_eviction_ms / 1000).toFixed(2)} s
              </div>
            </div>
          </div>

          <div className="overview-card">
            <div className="overview-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"
                />
              </svg>
            </div>
            <div className="overview-content">
              <div className="overview-label">Evicted Data Size</div>
              <div className="overview-value">
                {formatBytes(evictionStats.evicted_entries_size_bytes)}
              </div>
            </div>
          </div>
        </div>

        <div className="charts-row">
          <div className="chart-section">
            <h4 className="section-title">Eviction Reasons</h4>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={evictionReasonData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {evictionReasonData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
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

            <div className="reasons-legend">
              {evictionReasonData.map((reason, index) => (
                <div key={reason.name} className="legend-item">
                  <span
                    className="legend-color"
                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                  ></span>
                  <span className="legend-name">{reason.name}</span>
                  <span className="legend-value">
                    {formatNumber(reason.value)} ({reason.percentage.toFixed(1)}%)
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="chart-section">
            <h4 className="section-title">Evictions Over Time</h4>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart
                data={evictionTimelineData}
                margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="evictionGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#ff6b6b" stopOpacity={0.8} />
                    <stop offset="100%" stopColor="#ff6b6b" stopOpacity={0.3} />
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
                  formatter={(value: number) => [formatNumber(value), 'Evictions']}
                />
                <Bar
                  dataKey="evictions"
                  fill="url(#evictionGradient)"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
