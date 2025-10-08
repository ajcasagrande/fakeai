/**
 * Historical Charts Component
 *
 * Displays line charts for temperature, power, and utilization history
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, Loader2 } from 'lucide-react';
import { GPUMetrics } from '../types';

interface HistoricalChartsProps {
  gpuMetrics: GPUMetrics[];
  loading?: boolean;
}

interface HistoricalDataPoint {
  timestamp: string;
  [key: string]: number | string;
}

export const HistoricalCharts: React.FC<HistoricalChartsProps> = ({ gpuMetrics, loading }) => {
  const [temperatureHistory, setTemperatureHistory] = useState<HistoricalDataPoint[]>([]);
  const [powerHistory, setPowerHistory] = useState<HistoricalDataPoint[]>([]);
  const [utilizationHistory, setUtilizationHistory] = useState<HistoricalDataPoint[]>([]);

  useEffect(() => {
    if (!gpuMetrics || gpuMetrics.length === 0) return;

    const now = new Date();
    const timestamp = now.toLocaleTimeString();

    // Update temperature history
    setTemperatureHistory((prev) => {
      const newPoint: HistoricalDataPoint = { timestamp };
      gpuMetrics.forEach((gpu) => {
        newPoint[`GPU${gpu.gpu_id}`] = gpu.temperature_c;
      });
      const updated = [...prev, newPoint].slice(-30); // Keep last 30 points
      return updated;
    });

    // Update power history
    setPowerHistory((prev) => {
      const newPoint: HistoricalDataPoint = { timestamp };
      gpuMetrics.forEach((gpu) => {
        newPoint[`GPU${gpu.gpu_id}`] = gpu.power_usage_w;
      });
      const updated = [...prev, newPoint].slice(-30);
      return updated;
    });

    // Update utilization history
    setUtilizationHistory((prev) => {
      const newPoint: HistoricalDataPoint = { timestamp };
      gpuMetrics.forEach((gpu) => {
        newPoint[`GPU${gpu.gpu_id}`] = gpu.gpu_utilization_pct;
      });
      const updated = [...prev, newPoint].slice(-30);
      return updated;
    });
  }, [gpuMetrics]);

  if (loading) {
    return (
      <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
        <Loader2 className="w-8 h-8 text-gray-400 animate-spin mx-auto" />
      </div>
    );
  }

  if (!gpuMetrics || gpuMetrics.length === 0) {
    return null;
  }

  const colors = ['#76B900', '#00D9FF', '#FF6B6B', '#FFA500', '#9B59B6', '#3498DB', '#E74C3C', '#F39C12'];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload) return null;

    return (
      <div className="bg-black/90 border border-white/20 rounded-lg p-3 shadow-xl">
        <p className="text-xs text-gray-400 mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2 mb-1">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-xs text-white font-semibold">{entry.name}:</span>
            <span className="text-xs text-gray-300">{entry.value.toFixed(1)}</span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Temperature Chart */}
      <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-orange-500/20 rounded-lg">
            <TrendingUp className="w-6 h-6 text-orange-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Temperature History</h2>
            <p className="text-sm text-gray-400">Real-time temperature monitoring (°C)</p>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={temperatureHistory}>
            <defs>
              {gpuMetrics.map((gpu, index) => (
                <linearGradient key={gpu.gpu_id} id={`tempGradient${gpu.gpu_id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={colors[index % colors.length]} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={colors[index % colors.length]} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
            <XAxis dataKey="timestamp" stroke="#888" tick={{ fontSize: 12 }} />
            <YAxis stroke="#888" tick={{ fontSize: 12 }} domain={[30, 90]} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            {gpuMetrics.map((gpu, index) => (
              <Area
                key={gpu.gpu_id}
                type="monotone"
                dataKey={`GPU${gpu.gpu_id}`}
                stroke={colors[index % colors.length]}
                fill={`url(#tempGradient${gpu.gpu_id})`}
                strokeWidth={2}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Power Chart */}
      <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-yellow-500/20 rounded-lg">
            <TrendingUp className="w-6 h-6 text-yellow-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Power Usage History</h2>
            <p className="text-sm text-gray-400">Real-time power consumption (W)</p>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={powerHistory}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
            <XAxis dataKey="timestamp" stroke="#888" tick={{ fontSize: 12 }} />
            <YAxis stroke="#888" tick={{ fontSize: 12 }} domain={[0, 750]} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            {gpuMetrics.map((gpu, index) => (
              <Line
                key={gpu.gpu_id}
                type="monotone"
                dataKey={`GPU${gpu.gpu_id}`}
                stroke={colors[index % colors.length]}
                strokeWidth={2}
                dot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Utilization Chart */}
      <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-green-500/20 rounded-lg">
            <TrendingUp className="w-6 h-6 text-green-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">GPU Utilization History</h2>
            <p className="text-sm text-gray-400">Real-time compute utilization (%)</p>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={utilizationHistory}>
            <defs>
              {gpuMetrics.map((gpu, index) => (
                <linearGradient key={gpu.gpu_id} id={`utilGradient${gpu.gpu_id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={colors[index % colors.length]} stopOpacity={0.4} />
                  <stop offset="95%" stopColor={colors[index % colors.length]} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
            <XAxis dataKey="timestamp" stroke="#888" tick={{ fontSize: 12 }} />
            <YAxis stroke="#888" tick={{ fontSize: 12 }} domain={[0, 100]} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            {gpuMetrics.map((gpu, index) => (
              <Area
                key={gpu.gpu_id}
                type="monotone"
                dataKey={`GPU${gpu.gpu_id}`}
                stroke={colors[index % colors.length]}
                fill={`url(#utilGradient${gpu.gpu_id})`}
                strokeWidth={2}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
};
