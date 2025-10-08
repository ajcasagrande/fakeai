/**
 * Per-Model Performance Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Cpu, CheckCircle, XCircle } from 'lucide-react';
import { PerModelStats } from '../types';

interface PerModelPerformanceProps {
  perModelStats: PerModelStats;
  loading?: boolean;
}

export const PerModelPerformance: React.FC<PerModelPerformanceProps> = ({ perModelStats, loading }) => {
  if (loading || !perModelStats) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
      >
        <h3 className="text-lg font-bold text-white mb-2">Per-Model Performance</h3>
        <div className="text-center py-8 text-gray-400">
          {loading ? 'Loading...' : 'No model data available'}
        </div>
      </motion.div>
    );
  }

  if (!perModelStats.models || perModelStats.models.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
      >
        <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
          <Cpu className="w-5 h-5" />
          Per-Model Performance
        </h3>
        <div className="text-center py-8 text-gray-400">No model data available</div>
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
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <Cpu className="w-5 h-5 text-purple-500" />
          Per-Model Performance
        </h3>
        <div className="text-sm text-gray-400">
          {perModelStats.total_models} model(s) tracked
        </div>
      </div>

      <div className="space-y-4">
        {perModelStats.models.map((model) => (
          <div
            key={model.model_name}
            className="p-5 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-all"
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <h4 className="text-lg font-semibold text-white">{model.model_name}</h4>
                <div className="flex items-center gap-4 mt-1 text-sm">
                  <span className="flex items-center gap-1 text-green-500">
                    <CheckCircle className="w-4 h-4" />
                    {model.successful_requests}
                  </span>
                  <span className="flex items-center gap-1 text-red-500">
                    <XCircle className="w-4 h-4" />
                    {model.failed_requests}
                  </span>
                  <span className="text-gray-400">
                    Success Rate: {(model.success_rate * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
              <div className="p-3 bg-white/5 rounded">
                <div className="text-xs text-gray-400 mb-1">Requests</div>
                <div className="text-lg font-bold text-white">{model.total_requests}</div>
              </div>

              <div className="p-3 bg-white/5 rounded">
                <div className="text-xs text-gray-400 mb-1">Avg TTFT</div>
                <div className="text-lg font-bold text-blue-500">{model.avg_ttft_ms?.toFixed(1) || '0'}ms</div>
              </div>

              <div className="p-3 bg-white/5 rounded">
                <div className="text-xs text-gray-400 mb-1">Avg TPOT</div>
                <div className="text-lg font-bold text-green-500">{model.avg_tpot_ms?.toFixed(1) || '0'}ms</div>
              </div>

              <div className="p-3 bg-white/5 rounded">
                <div className="text-xs text-gray-400 mb-1">RPS</div>
                <div className="text-lg font-bold text-white">{model.requests_per_sec?.toFixed(1) || '0'}</div>
              </div>

              <div className="p-3 bg-white/5 rounded">
                <div className="text-xs text-gray-400 mb-1">TPS</div>
                <div className="text-lg font-bold text-white">{model.tokens_per_sec?.toFixed(0) || '0'}</div>
              </div>

              <div className="p-3 bg-white/5 rounded">
                <div className="text-xs text-gray-400 mb-1">Cache Hit</div>
                <div className="text-lg font-bold text-orange-500">
                  {((model.kv_cache_hit_rate || 0) * 100).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
};
