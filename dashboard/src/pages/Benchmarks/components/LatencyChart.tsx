/**
 * Request Latency Chart Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Activity } from 'lucide-react';
import { BenchmarkMetric } from '../types';

interface LatencyChartProps {
  latency: BenchmarkMetric;
  loading?: boolean;
}

export const LatencyChart: React.FC<LatencyChartProps> = ({ latency, loading }) => {
  if (loading) {
    return (
      <div className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl animate-pulse">
        <div className="h-64"></div>
      </div>
    );
  }

  const percentiles = [
    { label: 'Min', value: latency.min || 0, color: 'bg-emerald-500', height: 0.2 },
    { label: 'P25', value: latency.p25 || 0, color: 'bg-blue-500', height: 0.4 },
    { label: 'P50', value: latency.p50 || 0, color: 'bg-purple-500', height: 0.6 },
    { label: 'P75', value: latency.p75 || 0, color: 'bg-yellow-500', height: 0.75 },
    { label: 'P90', value: latency.p90 || 0, color: 'bg-orange-500', height: 0.85 },
    { label: 'P95', value: latency.p95 || 0, color: 'bg-red-500', height: 0.9 },
    { label: 'P99', value: latency.p99 || 0, color: 'bg-red-600', height: 0.95 },
    { label: 'Max', value: latency.max || 0, color: 'bg-red-700', height: 1.0 },
  ];

  const maxValue = Math.max(...percentiles.map((p) => p.value));

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:border-purple-500/50 transition-all"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-purple-500/10 rounded-lg">
          <Activity className="w-5 h-5 text-purple-500" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-white">Request Latency Distribution</h3>
          <p className="text-xs text-gray-400">End-to-End Request Latency</p>
        </div>
      </div>

      {/* Visual Bar Chart */}
      <div className="flex items-end justify-between gap-2 h-48 mb-6">
        {percentiles.map((percentile, index) => (
          <motion.div
            key={percentile.label}
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: `${percentile.height * 100}%`, opacity: 1 }}
            transition={{ delay: index * 0.08, duration: 0.5 }}
            className="flex-1 flex flex-col items-center group"
          >
            <div className="relative w-full h-full flex flex-col justify-end">
              <motion.div
                whileHover={{ scale: 1.05 }}
                className={`w-full ${percentile.color} rounded-t-lg relative overflow-hidden group-hover:brightness-125 transition-all cursor-pointer`}
                style={{ height: '100%' }}
              >
                <div className="absolute inset-0 bg-gradient-to-t from-transparent to-white/20"></div>
                <div className="absolute top-2 left-0 right-0 text-center">
                  <div className="text-xs font-bold text-white/90">
                    {percentile.value.toFixed(0)}
                  </div>
                </div>
              </motion.div>
            </div>
            <div className="text-xs text-gray-400 mt-2">{percentile.label}</div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/5">
        <div className="text-center">
          <div className="text-xs text-gray-500 mb-1">Average</div>
          <div className="text-lg font-bold text-purple-400">{latency.avg.toFixed(2)}ms</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 mb-1">Median (P50)</div>
          <div className="text-lg font-bold text-blue-400">
            {latency.p50?.toFixed(2) || 'N/A'}ms
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 mb-1">Std Dev</div>
          <div className="text-lg font-bold text-cyan-400">
            {latency.std?.toFixed(2) || 'N/A'}ms
          </div>
        </div>
      </div>
    </motion.div>
  );
};
