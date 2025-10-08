/**
 * TTFT Distribution Chart Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { BarChart3 } from 'lucide-react';
import { BenchmarkMetric } from '../types';

interface TTFTDistributionProps {
  ttft: BenchmarkMetric;
  loading?: boolean;
}

export const TTFTDistribution: React.FC<TTFTDistributionProps> = ({ ttft, loading }) => {
  if (loading) {
    return (
      <div className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl animate-pulse">
        <div className="h-64"></div>
      </div>
    );
  }

  const percentiles = [
    { label: 'Min', value: ttft.min || 0, color: 'bg-green-500' },
    { label: 'P1', value: ttft.p1 || 0, color: 'bg-green-400' },
    { label: 'P25', value: ttft.p25 || 0, color: 'bg-blue-500' },
    { label: 'P50', value: ttft.p50 || 0, color: 'bg-purple-500' },
    { label: 'P75', value: ttft.p75 || 0, color: 'bg-yellow-500' },
    { label: 'P95', value: ttft.p95 || 0, color: 'bg-orange-500' },
    { label: 'P99', value: ttft.p99 || 0, color: 'bg-red-500' },
    { label: 'Max', value: ttft.max || 0, color: 'bg-red-700' },
  ];

  const maxValue = Math.max(...percentiles.map((p) => p.value));

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:border-nvidia-green/50 transition-all"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-nvidia-green/10 rounded-lg">
          <BarChart3 className="w-5 h-5 text-nvidia-green" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-white">TTFT Distribution</h3>
          <p className="text-xs text-gray-400">Time to First Token Percentiles</p>
        </div>
      </div>

      <div className="space-y-3 mb-6">
        {percentiles.map((percentile, index) => (
          <motion.div
            key={percentile.label}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="group"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm text-gray-400">{percentile.label}</span>
              <span className="text-sm font-semibold text-white">
                {percentile.value.toFixed(2)}ms
              </span>
            </div>
            <div className="relative h-8 bg-white/5 rounded-lg overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(percentile.value / maxValue) * 100}%` }}
                transition={{ delay: index * 0.05 + 0.2, duration: 0.5 }}
                className={`h-full ${percentile.color} group-hover:brightness-110 transition-all`}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent to-white/10"></div>
              </motion.div>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/5">
        <div className="text-center">
          <div className="text-xs text-gray-500 mb-1">Average</div>
          <div className="text-lg font-bold text-nvidia-green">{ttft.avg.toFixed(2)}ms</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 mb-1">Std Dev</div>
          <div className="text-lg font-bold text-blue-400">
            {ttft.std?.toFixed(2) || 'N/A'}ms
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 mb-1">Count</div>
          <div className="text-lg font-bold text-purple-400">{ttft.count}</div>
        </div>
      </div>
    </motion.div>
  );
};
