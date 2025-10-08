/**
 * Radix Tree Stats Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { GitBranch, Database, Layers } from 'lucide-react';
import { RadixTreeStats as RadixTreeStatsType } from '../types';

interface RadixTreeStatsProps {
  radixTree: RadixTreeStatsType;
  loading?: boolean;
}

export const RadixTreeStats: React.FC<RadixTreeStatsProps> = ({ radixTree, loading }) => {
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

  const formatNumber = (num?: number): string => {
    const value = num ?? 0;
    if (value >= 1000000) return `${(value / 1000000).toFixed(2)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(2)}K`;
    return value.toLocaleString();
  };

  const avgBlocksPerNode = (radixTree.total_nodes ?? 0) > 0
    ? ((radixTree.total_cached_blocks ?? 0) / (radixTree.total_nodes ?? 1)).toFixed(2)
    : '0';

  return (
    <motion.div
      initial={false}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01 }}
      className="p-6 bg-white/5 backdrop-blur-sm border border-purple-500/30 rounded-xl hover:border-purple-500/50 transition-all"
    >
      <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
        <GitBranch className="w-5 h-5 text-purple-500" />
        Radix Tree Cache Structure
      </h3>

      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Total Nodes */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.1 }}
          className="p-6 bg-white/5 backdrop-blur-sm border border-purple-500/30 rounded-lg text-center"
        >
          <div className="flex justify-center mb-3">
            <div className="p-3 bg-purple-500/20 rounded-lg">
              <Layers className="w-8 h-8 text-purple-500" />
            </div>
          </div>
          <div className="text-xs text-gray-400 uppercase mb-2">Total Nodes</div>
          <div className="text-3xl font-bold text-purple-500">
            {formatNumber(radixTree?.total_nodes)}
          </div>
        </motion.div>

        {/* Cached Blocks */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="p-6 bg-white/5 backdrop-blur-sm border border-green-500/30 rounded-lg text-center"
        >
          <div className="flex justify-center mb-3">
            <div className="p-3 bg-green-500/20 rounded-lg">
              <Database className="w-8 h-8 text-green-500" />
            </div>
          </div>
          <div className="text-xs text-gray-400 uppercase mb-2">Cached Blocks</div>
          <div className="text-3xl font-bold text-green-500">
            {formatNumber(radixTree?.total_cached_blocks)}
          </div>
        </motion.div>
      </div>

      {/* Efficiency Metric */}
      <motion.div
        initial={false}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="p-4 bg-gradient-to-r from-purple-500/10 to-green-500/10 border border-white/10 rounded-lg"
      >
        <div className="text-xs text-gray-400 uppercase mb-2">
          Average Blocks per Node
        </div>
        <div className="flex items-center justify-between">
          <div className="text-2xl font-bold text-white">
            {avgBlocksPerNode}
          </div>
          <div className="text-xs text-gray-500">
            Cache efficiency metric
          </div>
        </div>
      </motion.div>

      {/* Info Text */}
      <div className="mt-4 p-3 bg-white/5 rounded-lg">
        <div className="text-xs text-gray-400">
          The radix tree efficiently organizes cached content for fast prefix matching and block reuse across requests.
        </div>
      </div>
    </motion.div>
  );
};
