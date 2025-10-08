/**
 * TTFT (Time to First Token) Metrics Component
 *
 * Critical metric for streaming user experience
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Zap, Clock, TrendingUp, AlertCircle } from 'lucide-react';
import { TTFTStats } from '../types';

interface TTFTMetricsProps {
  ttftStats: TTFTStats;
  loading?: boolean;
}

export const TTFTMetrics: React.FC<TTFTMetricsProps> = ({ ttftStats, loading }) => {
  console.log('🔴 TTFTMetrics component - ttftStats:', ttftStats, 'loading:', loading);

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
      >
        <div className="animate-pulse">
          <div className="h-6 bg-white/10 rounded w-1/3 mb-4"></div>
          <div className="h-32 bg-white/10 rounded"></div>
        </div>
      </motion.div>
    );
  }

  if (!ttftStats) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
      >
        <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
          <Clock className="w-5 h-5" />
          TTFT - Time to First Token
        </h3>
        <div className="text-center py-8 text-gray-400">No TTFT data available</div>
      </motion.div>
    );
  }

  const getPerformanceStatus = () => {
    if (ttftStats.avg_ttft_ms < 100) {
      return { level: 'excellent', color: 'text-green-500', bg: 'bg-green-500/10', border: 'border-green-500/50', message: 'Excellent - Sub-100ms TTFT' };
    } else if (ttftStats.avg_ttft_ms < 200) {
      return { level: 'good', color: 'text-blue-500', bg: 'bg-blue-500/10', border: 'border-blue-500/50', message: 'Good - Acceptable for most use cases' };
    } else {
      return { level: 'warning', color: 'text-orange-500', bg: 'bg-orange-500/10', border: 'border-orange-500/50', message: 'Needs Optimization - High TTFT impacts UX' };
    }
  };

  const status = getPerformanceStatus();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01 }}
      className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:border-green-500/50 transition-all"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-500" />
            TTFT - Time to First Token
            <span className="text-xs px-2 py-1 bg-red-500 text-white rounded font-bold">CRITICAL</span>
          </h3>
          <p className="text-sm text-gray-400 mt-1">First token latency - impacts streaming UX</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-4 h-4 text-green-500" />
            <span className="text-xs text-gray-400 uppercase">Average</span>
          </div>
          <div className="text-2xl font-bold text-green-500">{ttftStats.avg_ttft_ms.toFixed(1)}</div>
          <div className="text-xs text-gray-500">ms</div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <span className="text-xs text-gray-400 uppercase block mb-2">P50</span>
          <div className="text-2xl font-bold text-white">{ttftStats.p50_ttft_ms.toFixed(1)}</div>
          <div className="text-xs text-gray-500">ms</div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <span className="text-xs text-gray-400 uppercase block mb-2">P95</span>
          <div className="text-2xl font-bold text-white">{ttftStats.p95_ttft_ms.toFixed(1)}</div>
          <div className="text-xs text-gray-500">ms</div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <span className="text-xs text-gray-400 uppercase block mb-2">P99</span>
          <div className="text-2xl font-bold text-white">{ttftStats.p99_ttft_ms.toFixed(1)}</div>
          <div className="text-xs text-gray-500">ms</div>
        </div>
      </div>

      <div className={`p-4 rounded-lg border-l-4 ${status.border} ${status.bg} flex items-center gap-3`}>
        <div className={`w-2 h-2 rounded-full ${status.color}`}></div>
        <span className={`${status.color} font-medium text-sm`}>{status.message}</span>
      </div>

      <div className="mt-4 text-xs text-gray-500 text-center">
        {ttftStats.samples_count} samples analyzed
      </div>
    </motion.div>
  );
};
