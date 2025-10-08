/**
 * Worker Utilization Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Server, Circle } from 'lucide-react';
import { WorkerStats } from '../types';

interface WorkerUtilizationProps {
  workerStats: WorkerStats;
  loading?: boolean;
}

export const WorkerUtilization: React.FC<WorkerUtilizationProps> = ({ workerStats, loading }) => {
  if (loading || !workerStats) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
      >
        <h3 className="text-lg font-bold text-white mb-2">Worker Utilization</h3>
        <div className="text-center py-8 text-gray-400">
          {loading ? 'Loading...' : 'No worker data available'}
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.005 }}
      className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:border-green-500/50 transition-all"
    >
      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
        <Server className="w-5 h-5 text-green-500" />
        Worker Utilization
      </h3>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
          <div className="text-xs text-gray-400 uppercase mb-2">Total Workers</div>
          <div className="text-3xl font-bold text-white">{workerStats.total_workers || 0}</div>
        </div>

        <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
          <div className="text-xs text-gray-400 uppercase mb-2">Active</div>
          <div className="text-3xl font-bold text-green-500">{workerStats.active_workers || 0}</div>
        </div>

        <div className="p-4 bg-white/5 border border-white/10 rounded-lg">
          <div className="text-xs text-gray-400 uppercase mb-2">Avg Utilization</div>
          <div className="text-3xl font-bold text-white">{((workerStats.avg_utilization || 0) * 100).toFixed(0)}%</div>
        </div>
      </div>

      {workerStats.workers && workerStats.workers.length > 0 && (
        <div className="space-y-3">
          {workerStats.workers.map((worker) => (
            <div
              key={worker.worker_id}
              className="p-4 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-all"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Circle
                    className={`w-3 h-3 ${
                      worker.status === 'active' ? 'text-green-500 fill-green-500' :
                      worker.status === 'idle' ? 'text-orange-500 fill-orange-500' :
                      'text-gray-500 fill-gray-500'
                    }`}
                  />
                  <span className="font-mono text-sm text-white">{worker.worker_id}</span>
                  <span className="text-xs text-gray-400">{worker.status}</span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-sm text-gray-400">
                    {worker.current_requests} req
                  </div>
                  <div className="w-32 bg-gray-900 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full bg-green-500 transition-all"
                      style={{ width: `${(worker.utilization || 0) * 100}%` }}
                    ></div>
                  </div>
                  <div className="text-sm text-white w-12 text-right">
                    {((worker.utilization || 0) * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
};
