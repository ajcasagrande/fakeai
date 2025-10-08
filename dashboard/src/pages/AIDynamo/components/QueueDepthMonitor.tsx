/**
 * Queue Depth Monitor Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Layers, Clock } from 'lucide-react';
import { QueueStats } from '../types';

interface QueueDepthMonitorProps {
  queueStats: QueueStats;
  loading?: boolean;
}

export const QueueDepthMonitor: React.FC<QueueDepthMonitorProps> = ({ queueStats, loading }) => {
  if (loading || !queueStats) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
      >
        <h3 className="text-lg font-bold text-white mb-2">Queue Depth Monitor</h3>
        <div className="text-center py-8 text-gray-400">
          {loading ? 'Loading...' : 'No queue data available'}
        </div>
      </motion.div>
    );
  }

  const currentDepth = queueStats.current_depth || 0;
  const maxDepth = queueStats.max_depth || 100;
  const fillPercentage = Math.min((currentDepth / maxDepth) * 100, 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01 }}
      className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:border-green-500/50 transition-all"
    >
      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
        <Layers className="w-5 h-5 text-orange-500" />
        Queue Depth Monitor
      </h3>

      <div className="flex gap-6 items-center mb-6">
        <div className="flex-shrink-0">
          <div className="w-32 h-48 bg-gray-900 rounded-lg relative overflow-hidden border border-white/10">
            <div
              className="absolute bottom-0 w-full bg-gradient-to-t from-orange-500 to-orange-400 transition-all duration-500"
              style={{ height: `${fillPercentage}%` }}
            ></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-3xl font-bold text-white drop-shadow-lg">{currentDepth}</div>
            </div>
          </div>
          <div className="text-xs text-gray-400 text-center mt-2">Current Depth</div>
        </div>

        <div className="flex-1 grid grid-cols-2 gap-4">
          <div className="p-4 bg-white/5 rounded-lg border border-white/10">
            <div className="text-xs text-gray-400 uppercase mb-2">Max Depth</div>
            <div className="text-2xl font-bold text-white">{maxDepth}</div>
          </div>

          <div className="p-4 bg-white/5 rounded-lg border border-white/10">
            <div className="text-xs text-gray-400 uppercase mb-2">Avg Depth</div>
            <div className="text-2xl font-bold text-white">{queueStats.avg_depth?.toFixed(1) || '0'}</div>
          </div>

          <div className="p-4 bg-white/5 rounded-lg border border-white/10">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-4 h-4 text-orange-500" />
              <span className="text-xs text-gray-400 uppercase">Avg Wait</span>
            </div>
            <div className="text-xl font-bold text-white">{queueStats.avg_wait_time_ms?.toFixed(1) || '0'}ms</div>
          </div>

          <div className="p-4 bg-white/5 rounded-lg border border-white/10">
            <div className="text-xs text-gray-400 uppercase mb-2">Total Queued</div>
            <div className="text-xl font-bold text-white">{queueStats.total_queued || '0'}</div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
