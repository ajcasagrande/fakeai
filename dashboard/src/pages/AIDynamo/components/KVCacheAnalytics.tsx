/**
 * KV Cache Analytics Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Database, CheckCircle, XCircle } from 'lucide-react';
import { KVCacheStats } from '../types';

interface KVCacheAnalyticsProps {
  kvCacheStats: KVCacheStats;
  loading?: boolean;
}

export const KVCacheAnalytics: React.FC<KVCacheAnalyticsProps> = ({ kvCacheStats, loading }) => {
  if (loading || !kvCacheStats) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
      >
        <h3 className="text-lg font-bold text-white mb-2">KV Cache Analytics</h3>
        <div className="text-center py-8 text-gray-400">
          {loading ? 'Loading...' : 'No cache data available'}
        </div>
      </motion.div>
    );
  }

  const hitRate = (kvCacheStats.overall_hit_rate || 0) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01 }}
      className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:border-green-500/50 transition-all"
    >
      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
        <Database className="w-5 h-5 text-blue-500" />
        KV Cache Analytics
      </h3>

      <div className="mb-6">
        <div className="text-sm text-gray-400 mb-2">Hit Rate</div>
        <div className="h-4 bg-gray-900 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-green-500 transition-all duration-500"
            style={{ width: `${hitRate}%` }}
          ></div>
        </div>
        <div className="text-3xl font-bold text-green-500 mt-2">{hitRate.toFixed(1)}%</div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span className="text-xs text-gray-400 uppercase">Hits</span>
          </div>
          <div className="text-xl font-bold text-green-500">{kvCacheStats.total_hits || 0}</div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <XCircle className="w-4 h-4 text-red-500" />
            <span className="text-xs text-gray-400 uppercase">Misses</span>
          </div>
          <div className="text-xl font-bold text-red-500">{kvCacheStats.total_misses || 0}</div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="text-xs text-gray-400 uppercase mb-2">Avg Blocks</div>
          <div className="text-xl font-bold text-white">{kvCacheStats.avg_blocks_matched?.toFixed(1) || '0'}</div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="text-xs text-gray-400 uppercase mb-2">Cache Size</div>
          <div className="text-xl font-bold text-white">{kvCacheStats.cache_size_mb?.toFixed(0) || '0'} MB</div>
        </div>
      </div>
    </motion.div>
  );
};
