/**
 * Token Statistics Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Hash, ArrowUpCircle, ArrowDownCircle, Database } from 'lucide-react';
import { TokenStats } from '../types';

interface TokenStatisticsProps {
  tokenStats: TokenStats;
  loading?: boolean;
}

export const TokenStatistics: React.FC<TokenStatisticsProps> = ({ tokenStats, loading }) => {
  if (loading || !tokenStats) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
      >
        <h3 className="text-lg font-bold text-white mb-2">Token Statistics</h3>
        <div className="text-center py-8 text-gray-400">
          {loading ? 'Loading...' : 'No token data available'}
        </div>
      </motion.div>
    );
  }

  const formatNumber = (num: number | undefined): string => {
    if (num === undefined || num === null) return '0';
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
    return num.toFixed(0);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.005 }}
      className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:border-green-500/50 transition-all"
    >
      <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
        <Hash className="w-5 h-5 text-pink-500" />
        Token Statistics
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="p-5 bg-blue-500/10 border border-blue-500/20 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <ArrowDownCircle className="w-5 h-5 text-blue-500" />
            <span className="text-xs text-gray-400 uppercase">Input Tokens</span>
          </div>
          <div className="text-3xl font-bold text-blue-500">{formatNumber(tokenStats.total_input_tokens)}</div>
          <div className="text-xs text-gray-400 mt-1">Avg: {tokenStats.avg_input_tokens?.toFixed(0) || '0'} per req</div>
        </div>

        <div className="p-5 bg-green-500/10 border border-green-500/20 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <ArrowUpCircle className="w-5 h-5 text-green-500" />
            <span className="text-xs text-gray-400 uppercase">Output Tokens</span>
          </div>
          <div className="text-3xl font-bold text-green-500">{formatNumber(tokenStats.total_output_tokens)}</div>
          <div className="text-xs text-gray-400 mt-1">Avg: {tokenStats.avg_output_tokens?.toFixed(0) || '0'} per req</div>
        </div>

        <div className="p-5 bg-orange-500/10 border border-orange-500/20 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Database className="w-5 h-5 text-orange-500" />
            <span className="text-xs text-gray-400 uppercase">Cached Tokens</span>
          </div>
          <div className="text-3xl font-bold text-orange-500">{formatNumber(tokenStats.total_cached_tokens)}</div>
          <div className="text-xs text-gray-400 mt-1">Avg: {tokenStats.avg_cached_tokens?.toFixed(0) || '0'} per req</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="text-xs text-gray-400 uppercase mb-2">Input Rate</div>
          <div className="text-xl font-bold text-white">{formatNumber(tokenStats.input_tokens_per_sec)}/s</div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="text-xs text-gray-400 uppercase mb-2">Output Rate</div>
          <div className="text-xl font-bold text-white">{formatNumber(tokenStats.output_tokens_per_sec)}/s</div>
        </div>
      </div>
    </motion.div>
  );
};
