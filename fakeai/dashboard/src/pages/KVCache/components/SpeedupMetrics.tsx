/**
 * Speedup Metrics Component
 * Displays performance improvements from cache usage
 */

import React from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import { CacheTimeSeriesData, CachePerformanceImpact } from '../types';

interface SpeedupMetricsProps {
  timeSeries: CacheTimeSeriesData[];
  performanceImpact: CachePerformanceImpact;
  loading?: boolean;
}

export const SpeedupMetrics: React.FC<SpeedupMetricsProps> = ({
  timeSeries,
  performanceImpact,
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

  const chartData = timeSeries.map((item) => ({
    timestamp: item.timestamp,
    time: formatTimestamp(item.timestamp),
    speedupFactor: item.speedup_factor,
  }));

  return (
    <div className="speedup-metrics">
      <div className="card-header">
        <h3 className="card-title">Performance Speedup Metrics</h3>
        <div className="speedup-badge">
          <span className="badge-label">Avg Speedup:</span>
          <span className="badge-value">
            {(timeSeries.reduce((sum, d) => sum + d.speedup_factor, 0) / timeSeries.length).toFixed(2)}x
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={chartData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="speedupGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#76b900" />
              <stop offset="100%" stopColor="#00ff88" />
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
            tickFormatter={(value) => `${value}x`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a1a1a',
              border: '1px solid #333',
              borderRadius: '8px',
            }}
            formatter={(value: number) => [`${value.toFixed(2)}x`, 'Speedup Factor']}
          />
          <Line
            type="monotone"
            dataKey="speedupFactor"
            stroke="url(#speedupGradient)"
            strokeWidth={3}
            dot={{ fill: '#76b900', r: 4 }}
            activeDot={{ r: 6 }}
            name="Speedup Factor"
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="performance-impact-grid">
        <div className="impact-card">
          <div className="impact-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="impact-content">
            <div className="impact-label">Latency Reduction</div>
            <div className="impact-value">
              {performanceImpact.latency_reduction_ms.toFixed(0)} ms
            </div>
            <div className="impact-subtitle">
              {performanceImpact.latency_reduction_percent.toFixed(1)}% faster
            </div>
          </div>
        </div>

        <div className="impact-card">
          <div className="impact-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
              />
            </svg>
          </div>
          <div className="impact-content">
            <div className="impact-label">Throughput Increase</div>
            <div className="impact-value">
              {performanceImpact.throughput_increase_percent.toFixed(1)}%
            </div>
            <div className="impact-subtitle">
              {performanceImpact.requests_per_second_with_cache.toFixed(2)} req/s
            </div>
          </div>
        </div>

        <div className="impact-card">
          <div className="impact-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="impact-content">
            <div className="impact-label">Time Saved (Total)</div>
            <div className="impact-value">
              {(performanceImpact.time_saved_total_ms / 1000).toFixed(2)} s
            </div>
            <div className="impact-subtitle">
              {performanceImpact.time_saved_per_request_ms.toFixed(2)} ms/req
            </div>
          </div>
        </div>

        <div className="impact-card comparison">
          <div className="comparison-row">
            <div className="comparison-item">
              <div className="comparison-label">With Cache</div>
              <div className="comparison-value with-cache">
                {performanceImpact.requests_per_second_with_cache.toFixed(2)} req/s
              </div>
            </div>
            <div className="comparison-divider">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M14 5l7 7m0 0l-7 7m7-7H3"
                />
              </svg>
            </div>
            <div className="comparison-item">
              <div className="comparison-label">Without Cache</div>
              <div className="comparison-value without-cache">
                {performanceImpact.requests_per_second_without_cache.toFixed(2)} req/s
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
