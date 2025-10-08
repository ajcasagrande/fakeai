/**
 * Throttle Analytics Component
 * Displays 429 errors over time with visualizations
 */

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
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
import { ThrottleTimeSeries } from '../types';

interface ThrottleAnalyticsProps {
  data: ThrottleTimeSeries[];
  loading?: boolean;
}

export const ThrottleAnalytics: React.FC<ThrottleAnalyticsProps> = ({
  data,
  loading = false,
}) => {
  const chartData = useMemo(() => {
    return data.map((item) => ({
      ...item,
      time: new Date(item.timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      }),
    }));
  }, [data]);

  const stats = useMemo(() => {
    const total = data.reduce((sum, d) => sum + d.total_throttles, 0);
    const rpmTotal = data.reduce((sum, d) => sum + d.rpm_throttles, 0);
    const tpmTotal = data.reduce((sum, d) => sum + d.tpm_throttles, 0);
    const rpdTotal = data.reduce((sum, d) => sum + d.rpd_throttles, 0);

    const maxThrottles = Math.max(...data.map((d) => d.total_throttles), 0);
    const avgThrottles = data.length > 0 ? total / data.length : 0;

    return {
      total,
      rpmTotal,
      tpmTotal,
      rpdTotal,
      maxThrottles,
      avgThrottles,
    };
  }, [data]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;

    return (
      <div className="bg-gray-900/95 border border-gray-700 rounded-lg p-3 shadow-xl backdrop-blur-sm">
        <p className="text-white font-semibold mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: entry.color }}
            ></div>
            <span className="text-gray-400">{entry.name}:</span>
            <span className="text-white font-semibold">{entry.value}</span>
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
        <div className="h-6 bg-gray-700 rounded w-1/3 mb-4 animate-pulse"></div>
        <div className="h-64 bg-gray-700/50 rounded animate-pulse"></div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-white mb-1">
            Throttle Analytics (429 Errors)
          </h3>
          <p className="text-gray-400 text-sm">
            Rate limit violations over time by breach type
          </p>
        </div>
        <div className="text-2xl">⚠️</div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-red-500/10 border border-red-500/30 rounded-lg p-4"
        >
          <div className="text-gray-400 text-xs mb-1">Total Throttles</div>
          <div className="text-red-400 text-2xl font-bold">{stats.total}</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4"
        >
          <div className="text-gray-400 text-xs mb-1">RPM Throttles</div>
          <div className="text-orange-400 text-2xl font-bold">{stats.rpmTotal}</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4"
        >
          <div className="text-gray-400 text-xs mb-1">TPM Throttles</div>
          <div className="text-yellow-400 text-2xl font-bold">{stats.tpmTotal}</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4"
        >
          <div className="text-gray-400 text-xs mb-1">RPD Throttles</div>
          <div className="text-blue-400 text-2xl font-bold">{stats.rpdTotal}</div>
        </motion.div>
      </div>

      {/* Area Chart */}
      <div className="mb-6">
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="rpmGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="tpmGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="rpdGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#eab308" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#eab308" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="time"
              stroke="#9ca3af"
              style={{ fontSize: '12px' }}
            />
            <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '14px' }}
              iconType="circle"
            />
            <Area
              type="monotone"
              dataKey="rpm_throttles"
              name="RPM"
              stroke="#ef4444"
              fill="url(#rpmGradient)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="tpm_throttles"
              name="TPM"
              stroke="#f97316"
              fill="url(#tpmGradient)"
              strokeWidth={2}
            />
            <Area
              type="monotone"
              dataKey="rpd_throttles"
              name="RPD"
              stroke="#eab308"
              fill="url(#rpdGradient)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Line Chart for Total */}
      <div>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="time"
              stroke="#9ca3af"
              style={{ fontSize: '12px' }}
            />
            <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '14px' }}
              iconType="circle"
            />
            <Line
              type="monotone"
              dataKey="total_throttles"
              name="Total Throttles"
              stroke="#76b900"
              strokeWidth={3}
              dot={{ r: 4, fill: '#76b900' }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Additional Metrics */}
      <div className="mt-6 grid grid-cols-2 gap-4 pt-6 border-t border-gray-700/50">
        <div>
          <span className="text-gray-400 text-sm">Peak Throttles</span>
          <div className="text-white font-bold text-lg">{stats.maxThrottles}</div>
        </div>
        <div>
          <span className="text-gray-400 text-sm">Avg Throttles/Period</span>
          <div className="text-white font-bold text-lg">
            {stats.avgThrottles.toFixed(1)}
          </div>
        </div>
      </div>

      {data.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No throttle events recorded
        </div>
      )}
    </div>
  );
};
