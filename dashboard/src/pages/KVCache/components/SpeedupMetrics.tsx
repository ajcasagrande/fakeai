/**
 * Speedup Metrics Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Zap, Clock, TrendingUp } from 'lucide-react';
import { SpeedupStats } from '../types';

interface SpeedupMetricsProps {
  speedupStats: SpeedupStats;
  loading?: boolean;
}

export const SpeedupMetrics: React.FC<SpeedupMetricsProps> = ({ speedupStats, loading }) => {
  if (loading) {
    return (
      <motion.div
        initial={false}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
      >
        <div className="h-64 flex items-center justify-center">
          <div className="w-12 h-12 border-4 border-green-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </motion.div>
    );
  }

  const improvementPercent = speedupStats.avg_baseline_ttft_ms > 0
    ? ((speedupStats.avg_baseline_ttft_ms - speedupStats.avg_actual_ttft_ms) / speedupStats.avg_baseline_ttft_ms * 100)
    : 0;

  return (
    <motion.div
      initial={false}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01 }}
      className="p-6 bg-white/5 backdrop-blur-sm border border-green-500/30 rounded-xl hover:border-green-500/50 transition-all"
    >
      <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
        <Zap className="w-5 h-5 text-green-500" />
        TTFT Speedup Analysis
      </h3>

      {/* Speedup Ratio Gauge */}
      <div className="mb-6 text-center">
        <div className="text-6xl font-bold text-green-500 mb-2">
          {(speedupStats.avg_speedup_ratio ?? 0).toFixed(1)}x
        </div>
        <div className="text-sm text-gray-400">Average Speedup Ratio</div>
        <div className="text-xs text-green-500 mt-1">
          {improvementPercent.toFixed(0)}% faster
        </div>
      </div>

      {/* Comparison Bars */}
      <div className="space-y-4 mb-6">
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-red-400" />
              <span className="text-sm text-gray-400">Baseline TTFT</span>
            </div>
            <span className="text-sm font-bold text-white">
              {(speedupStats.avg_baseline_ttft_ms ?? 0).toFixed(1)}ms
            </span>
          </div>
          <div className="h-8 bg-gray-900 rounded-lg overflow-hidden relative">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: '100%' }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
              className="h-full bg-gradient-to-r from-red-500 to-red-600 flex items-center justify-end pr-3"
            >
              <span className="text-xs font-bold text-white">
                {(speedupStats.avg_baseline_ttft_ms ?? 0).toFixed(1)}ms
              </span>
            </motion.div>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-green-500" />
              <span className="text-sm text-gray-400">With KV Cache</span>
            </div>
            <span className="text-sm font-bold text-green-500">
              {(speedupStats.avg_actual_ttft_ms ?? 0).toFixed(1)}ms
            </span>
          </div>
          <div className="h-8 bg-gray-900 rounded-lg overflow-hidden relative">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(speedupStats.avg_baseline_ttft_ms ?? 0) > 0 ? ((speedupStats.avg_actual_ttft_ms ?? 0) / (speedupStats.avg_baseline_ttft_ms ?? 1)) * 100 : 0}%` }}
              transition={{ duration: 0.8, delay: 0.2, ease: 'easeOut' }}
              className="h-full bg-gradient-to-r from-green-500 to-green-600 flex items-center justify-end pr-3"
            >
              <span className="text-xs font-bold text-white">
                {(speedupStats.avg_actual_ttft_ms ?? 0).toFixed(1)}ms
              </span>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Time Saved */}
      <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
        <div className="text-xs text-gray-400 uppercase mb-1">Time Saved Per Request</div>
        <div className="text-2xl font-bold text-green-500">
          {((speedupStats.avg_baseline_ttft_ms ?? 0) - (speedupStats.avg_actual_ttft_ms ?? 0)).toFixed(1)}ms
        </div>
        <div className="text-xs text-gray-500 mt-1">
          Based on {(speedupStats.total_speedup_records ?? 0).toLocaleString()} measurements
        </div>
      </div>
    </motion.div>
  );
};
