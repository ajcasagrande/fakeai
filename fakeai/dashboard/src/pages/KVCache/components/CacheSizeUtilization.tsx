/**
 * Cache Size and Utilization Component
 * Displays cache size metrics and memory usage
 */

import React from 'react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { CacheTimeSeriesData } from '../types';

interface CacheSizeUtilizationProps {
  data: CacheTimeSeriesData[];
  loading?: boolean;
}

export const CacheSizeUtilization: React.FC<CacheSizeUtilizationProps> = ({
  data,
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

  const chartData = data.map((item) => ({
    timestamp: item.timestamp,
    time: formatTimestamp(item.timestamp),
    cacheSize: item.cache_size_mb,
    memoryUsage: item.memory_usage_mb,
  }));

  return (
    <div className="cache-size-utilization">
      <div className="card-header">
        <h3 className="card-title">Cache Size & Memory Utilization</h3>
        <div className="chart-legend">
          <div className="legend-item">
            <span className="legend-color cache-size"></span>
            <span className="legend-label">Cache Size (MB)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color memory-usage"></span>
            <span className="legend-label">Memory Usage (MB)</span>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={350}>
        <AreaChart
          data={chartData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="colorCacheSize" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00bfff" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#00bfff" stopOpacity={0.1} />
            </linearGradient>
            <linearGradient id="colorMemoryUsage" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ff9900" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#ff9900" stopOpacity={0.1} />
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
            tickFormatter={(value) => `${value} MB`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a1a1a',
              border: '1px solid #333',
              borderRadius: '8px',
            }}
            formatter={(value: number) => `${value.toFixed(2)} MB`}
          />
          <Area
            type="monotone"
            dataKey="cacheSize"
            stroke="#00bfff"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorCacheSize)"
            name="Cache Size"
          />
          <Area
            type="monotone"
            dataKey="memoryUsage"
            stroke="#ff9900"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#colorMemoryUsage)"
            name="Memory Usage"
          />
        </AreaChart>
      </ResponsiveContainer>

      <div className="utilization-stats">
        <div className="stat-item">
          <div className="stat-label">Current Cache Size</div>
          <div className="stat-value cache-color">
            {chartData[chartData.length - 1]?.cacheSize.toFixed(2) || '0.00'} MB
          </div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Current Memory Usage</div>
          <div className="stat-value memory-color">
            {chartData[chartData.length - 1]?.memoryUsage.toFixed(2) || '0.00'} MB
          </div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Utilization Ratio</div>
          <div className="stat-value">
            {chartData[chartData.length - 1]
              ? ((chartData[chartData.length - 1].cacheSize / chartData[chartData.length - 1].memoryUsage) * 100).toFixed(1)
              : '0.0'}%
          </div>
        </div>
      </div>
    </div>
  );
};
