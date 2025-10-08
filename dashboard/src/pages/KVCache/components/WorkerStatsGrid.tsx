/**
 * Worker Stats Grid Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Server, Activity, Database, Hash } from 'lucide-react';
import { WorkerStats } from '../types';

interface WorkerStatsGridProps {
  workers: Record<string, WorkerStats>;
  loading?: boolean;
}

export const WorkerStatsGrid: React.FC<WorkerStatsGridProps> = ({ workers, loading }) => {
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

  const workerEntries = Object.entries(workers).sort((a, b) => a[0].localeCompare(b[0]));

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
    return num.toFixed(0);
  };

  return (
    <motion.div
      initial={false}
      animate={{ opacity: 1, y: 0 }}
      className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
    >
      <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
        <Server className="w-5 h-5 text-blue-500" />
        Worker Statistics
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {workerEntries.map(([workerId, stats], index) => (
          <motion.div
            key={workerId}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            whileHover={{ scale: 1.03 }}
            className="p-4 bg-white/5 backdrop-blur-sm border border-white/20 rounded-lg hover:border-green-500/50 transition-all"
          >
            {/* Worker Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-blue-500/20 rounded-lg">
                  <Server className="w-4 h-4 text-blue-500" />
                </div>
                <div>
                  <div className="text-sm font-bold text-white">{workerId}</div>
                  <div className={`text-xs ${stats.active_requests > 0 ? 'text-green-500' : 'text-gray-500'}`}>
                    {stats.active_requests > 0 ? 'Active' : 'Idle'}
                  </div>
                </div>
              </div>
              {stats.active_requests > 0 && (
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              )}
            </div>

            {/* Stats */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="w-3 h-3 text-gray-400" />
                  <span className="text-xs text-gray-400">Active</span>
                </div>
                <span className="text-sm font-bold text-white">
                  {stats.active_requests}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="w-3 h-3 text-gray-400" />
                  <span className="text-xs text-gray-400">Total</span>
                </div>
                <span className="text-sm font-bold text-white">
                  {formatNumber(stats.total_requests)}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="w-3 h-3 text-gray-400" />
                  <span className="text-xs text-gray-400">Blocks</span>
                </div>
                <span className="text-sm font-bold text-green-500">
                  {formatNumber(stats.cached_blocks)}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Hash className="w-3 h-3 text-gray-400" />
                  <span className="text-xs text-gray-400">Tokens</span>
                </div>
                <span className="text-sm font-bold text-blue-500">
                  {formatNumber(stats.tokens_processed)}
                </span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};
