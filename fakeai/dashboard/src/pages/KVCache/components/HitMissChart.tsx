/**
 * Cache Hit/Miss Rate Visualization Component
 * Displays cache hit and miss rates over time
 */

import React from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { CacheTimeSeriesData } from '../types';

interface HitMissChartProps {
  data: CacheTimeSeriesData[];
  loading?: boolean;
}

export const HitMissChart: React.FC<HitMissChartProps> = ({ data, loading }) => {
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

  const chartData = data.map((item) => ({
    timestamp: item.timestamp,
    time: formatTimestamp(item.timestamp),
    hitRate: item.hit_rate,
    missRate: item.miss_rate,
  }));

  return (
    <div className="cache-hit-miss-chart">
      <div className="card-header">
        <h3 className="card-title">Cache Hit/Miss Rate Over Time</h3>
        <div className="chart-legend">
          <div className="legend-item">
            <span className="legend-color hit-rate"></span>
            <span className="legend-label">Hit Rate</span>
          </div>
          <div className="legend-item">
            <span className="legend-color miss-rate"></span>
            <span className="legend-label">Miss Rate</span>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={350}>
        <AreaChart
          data={chartData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="colorHitRate" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#76b900" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#76b900" stopOpacity={0.1} />
            </linearGradient>
            <linearGradient id="colorMissRate" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ff6b6b" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#ff6b6b" stopOpacity={0.1} />
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
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a1a1a',
              border: '1px solid #333',
              borderRadius: '8px',
            }}
            formatter={(value: number) => `${value.toFixed(2)}%`}
          />
          <Area
            type="monotone"
            dataKey="hitRate"
            stroke="#76b900"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorHitRate)"
            name="Hit Rate"
          />
          <Area
            type="monotone"
            dataKey="missRate"
            stroke="#ff6b6b"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorMissRate)"
            name="Miss Rate"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
