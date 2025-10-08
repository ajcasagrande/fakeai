/**
 * Throughput Metrics Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Zap } from 'lucide-react';
import { ThroughputStats } from '../types';

interface ThroughputMetricsProps {
  throughputStats: ThroughputStats;
  loading?: boolean;
}

export const ThroughputMetrics: React.FC<ThroughputMetricsProps> = ({ throughputStats, loading }) => {
  if (loading || !throughputStats) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
      >
        <h3 className="text-lg font-bold text-white mb-2">Throughput Metrics</h3>
        <div className="text-center py-8 text-gray-400">
          {loading ? 'Loading...' : 'No throughput data available'}
        </div>
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
      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
        <TrendingUp className="w-5 h-5 text-orange-500" />
        Throughput Metrics
      </h3>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-4 h-4 text-green-500" />
            <span className="text-xs text-gray-400 uppercase">Current RPS</span>
          </div>
          <div className="text-2xl font-bold text-green-500">{throughputStats.current_rps?.toFixed(1) || '0'}</div>
          <div className="text-xs text-gray-400 mt-1">Peak: {throughputStats.peak_rps?.toFixed(1) || '0'}</div>
        </div>

        <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-4 h-4 text-blue-500" />
            <span className="text-xs text-gray-400 uppercase">Current TPS</span>
          </div>
          <div className="text-2xl font-bold text-blue-500">{throughputStats.current_tps?.toFixed(0) || '0'}</div>
          <div className="text-xs text-gray-400 mt-1">Peak: {throughputStats.peak_tps?.toFixed(0) || '0'}</div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="text-xs text-gray-400 uppercase mb-2">Avg Requests/sec</div>
          <div className="text-xl font-bold text-white">{throughputStats.avg_rps?.toFixed(2) || '0'}</div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="text-xs text-gray-400 uppercase mb-2">Avg Tokens/sec</div>
          <div className="text-xl font-bold text-white">{throughputStats.avg_tps?.toFixed(0) || '0'}</div>
        </div>
      </div>
    </motion.div>
  );
};
