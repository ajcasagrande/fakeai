/**
 * TPOT (Time per Output Token) Metrics Component
 *
 * Decode throughput metric
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Activity, Zap, BarChart3 } from 'lucide-react';
import { TPOTStats } from '../types';

interface TPOTMetricsProps {
  tpotStats: TPOTStats;
  loading?: boolean;
}

export const TPOTMetrics: React.FC<TPOTMetricsProps> = ({ tpotStats, loading }) => {
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

  if (!tpotStats) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
      >
        <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
          <Activity className="w-5 h-5" />
          TPOT - Time per Output Token
        </h3>
        <div className="text-center py-8 text-gray-400">No TPOT data available</div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01 }}
      className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:border-green-500/50 transition-all"
    >
      <div className="mb-6">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <Activity className="w-5 h-5 text-green-500" />
          TPOT - Time per Output Token
        </h3>
        <p className="text-sm text-gray-400 mt-1">Decode throughput - tokens/second generation</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-4 h-4 text-green-500" />
            <span className="text-xs text-gray-400 uppercase">Average</span>
          </div>
          <div className="text-2xl font-bold text-green-500">{tpotStats.avg_tpot_ms.toFixed(1)}</div>
          <div className="text-xs text-gray-500">ms/token</div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <span className="text-xs text-gray-400 uppercase block mb-2">P50</span>
          <div className="text-2xl font-bold text-white">{tpotStats.p50_tpot_ms.toFixed(1)}</div>
          <div className="text-xs text-gray-500">ms/token</div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <span className="text-xs text-gray-400 uppercase block mb-2">P95</span>
          <div className="text-2xl font-bold text-white">{tpotStats.p95_tpot_ms.toFixed(1)}</div>
          <div className="text-xs text-gray-500">ms/token</div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <span className="text-xs text-gray-400 uppercase block mb-2">P99</span>
          <div className="text-2xl font-bold text-white">{tpotStats.p99_tpot_ms.toFixed(1)}</div>
          <div className="text-xs text-gray-500">ms/token</div>
        </div>
      </div>

      <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg flex items-center gap-3">
        <BarChart3 className="w-5 h-5 text-green-500" />
        <div>
          <div className="text-white font-medium">
            {(1000 / tpotStats.avg_tpot_ms).toFixed(1)} tokens/sec
          </div>
          <div className="text-xs text-gray-400">Average generation speed</div>
        </div>
      </div>

      <div className="mt-4 text-xs text-gray-500 text-center">
        {tpotStats.samples_count} samples analyzed
      </div>
    </motion.div>
  );
};
