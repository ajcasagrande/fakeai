/**
 * Throughput Visualization Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, Zap } from 'lucide-react';
import { BenchmarkMetric } from '../types';

interface ThroughputChartProps {
  requestThroughput: BenchmarkMetric;
  outputTokenThroughput: BenchmarkMetric;
  duration: BenchmarkMetric;
  requestCount: BenchmarkMetric;
  loading?: boolean;
}

export const ThroughputChart: React.FC<ThroughputChartProps> = ({
  requestThroughput,
  outputTokenThroughput,
  duration,
  requestCount,
  loading,
}) => {
  if (loading) {
    return (
      <div className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl animate-pulse">
        <div className="h-64"></div>
      </div>
    );
  }

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
    return num.toFixed(2);
  };

  const requestThroughputValue = requestThroughput.avg;
  const tokenThroughputValue = outputTokenThroughput.avg;
  const maxThroughput = Math.max(requestThroughputValue, tokenThroughputValue / 40); // Normalize for visualization

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:border-nvidia-green/50 transition-all"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-nvidia-green/10 rounded-lg">
          <TrendingUp className="w-5 h-5 text-nvidia-green" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-white">Throughput Metrics</h3>
          <p className="text-xs text-gray-400">Request and Token Processing Rates</p>
        </div>
      </div>

      {/* Request Throughput */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-purple-500" />
            <span className="text-sm text-gray-400">Request Throughput</span>
          </div>
          <span className="text-lg font-bold text-purple-400">
            {requestThroughputValue.toFixed(2)} req/sec
          </span>
        </div>
        <div className="relative h-12 bg-white/5 rounded-lg overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: '100%' }}
            transition={{ duration: 0.8 }}
            className="h-full bg-gradient-to-r from-purple-600 to-purple-400 relative overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
          </motion.div>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-sm font-bold text-white drop-shadow-lg">
              {requestCount.avg.toFixed(0)} requests in {duration.avg.toFixed(1)}s
            </span>
          </div>
        </div>
      </div>

      {/* Token Throughput */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-nvidia-green" />
            <span className="text-sm text-gray-400">Output Token Throughput</span>
          </div>
          <span className="text-lg font-bold text-nvidia-green">
            {formatNumber(tokenThroughputValue)} tokens/sec
          </span>
        </div>
        <div className="relative h-12 bg-white/5 rounded-lg overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: '100%' }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="h-full bg-gradient-to-r from-nvidia-green to-emerald-400 relative overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
          </motion.div>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-sm font-bold text-black drop-shadow-lg">
              High Performance Token Generation
            </span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5">
        <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/30">
          <div className="text-xs text-purple-400 mb-1">Requests/Second</div>
          <div className="text-2xl font-bold text-purple-300">
            {requestThroughputValue.toFixed(2)}
          </div>
        </div>
        <div className="p-3 bg-nvidia-green/10 rounded-lg border border-nvidia-green/30">
          <div className="text-xs text-nvidia-green mb-1">Tokens/Second</div>
          <div className="text-2xl font-bold text-nvidia-green">
            {formatNumber(tokenThroughputValue)}
          </div>
        </div>
        <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/30">
          <div className="text-xs text-blue-400 mb-1">Total Duration</div>
          <div className="text-2xl font-bold text-blue-300">
            {duration.avg.toFixed(2)}s
          </div>
        </div>
        <div className="p-3 bg-cyan-500/10 rounded-lg border border-cyan-500/30">
          <div className="text-xs text-cyan-400 mb-1">Total Requests</div>
          <div className="text-2xl font-bold text-cyan-300">
            {formatNumber(requestCount.avg)}
          </div>
        </div>
      </div>
    </motion.div>
  );
};
