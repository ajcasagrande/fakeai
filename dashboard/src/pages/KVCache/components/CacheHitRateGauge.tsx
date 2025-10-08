/**
 * Cache Hit Rate Gauge Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Target, TrendingUp } from 'lucide-react';

interface CacheHitRateGaugeProps {
  hitRate: number;
  totalHits: number;
  totalMisses: number;
  loading?: boolean;
}

export const CacheHitRateGauge: React.FC<CacheHitRateGaugeProps> = ({
  hitRate,
  totalHits,
  totalMisses,
  loading,
}) => {
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

  const getGaugeColor = (rate: number) => {
    if (rate >= 95) return { color: 'text-green-500', gradient: 'from-green-400 to-green-600' };
    if (rate >= 85) return { color: 'text-yellow-500', gradient: 'from-yellow-400 to-yellow-600' };
    if (rate >= 70) return { color: 'text-orange-500', gradient: 'from-orange-400 to-orange-600' };
    return { color: 'text-red-500', gradient: 'from-red-400 to-red-600' };
  };

  const gaugeStyle = getGaugeColor(hitRate);
  const rotation = (hitRate / 100) * 180 - 90; // -90 to 90 degrees

  const formatNumber = (num?: number): string => {
    const value = num ?? 0;
    if (value >= 1000000) return `${(value / 1000000).toFixed(2)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(2)}K`;
    return value.toLocaleString();
  };

  return (
    <motion.div
      initial={false}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01 }}
      className={`p-6 bg-white/5 backdrop-blur-sm border border-green-500/30 rounded-xl hover:border-green-500/50 transition-all`}
    >
      <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
        <Target className="w-5 h-5 text-green-500" />
        Cache Hit Rate Performance
      </h3>

      {/* Circular Gauge */}
      <div className="relative w-64 h-64 mx-auto mb-6">
        {/* Background Arc */}
        <svg className="w-full h-full" viewBox="0 0 200 200">
          <defs>
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" className="text-green-400" stopColor="currentColor" />
              <stop offset="100%" className="text-green-600" stopColor="currentColor" />
            </linearGradient>
          </defs>

          {/* Background circle */}
          <circle
            cx="100"
            cy="100"
            r="80"
            fill="none"
            stroke="rgba(255, 255, 255, 0.1)"
            strokeWidth="20"
            strokeDasharray="251.2 251.2"
            strokeDashoffset="62.8"
            transform="rotate(180 100 100)"
          />

          {/* Progress circle */}
          <motion.circle
            cx="100"
            cy="100"
            r="80"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth="20"
            strokeLinecap="round"
            strokeDasharray="251.2 251.2"
            initial={{ strokeDashoffset: 251.2 }}
            animate={{ strokeDashoffset: 251.2 - (251.2 * hitRate / 100) / 2 }}
            transition={{ duration: 1.5, ease: 'easeOut' }}
            transform="rotate(180 100 100)"
          />
        </svg>

        {/* Center Content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.5, type: 'spring', stiffness: 200 }}
            className={`text-6xl font-bold ${gaugeStyle.color}`}
          >
            {(hitRate ?? 0).toFixed(1)}%
          </motion.div>
          <div className="text-sm text-gray-400 mt-2">Hit Rate</div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-green-500" />
            <span className="text-xs text-gray-400 uppercase">Cache Hits</span>
          </div>
          <div className="text-2xl font-bold text-green-500">
            {formatNumber(totalHits)}
          </div>
        </div>

        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs text-gray-400 uppercase">Cache Misses</span>
          </div>
          <div className="text-2xl font-bold text-red-500">
            {formatNumber(totalMisses)}
          </div>
        </div>
      </div>

      {/* Performance Indicator */}
      <div className="mt-4 p-3 bg-white/5 rounded-lg">
        <div className="text-xs text-gray-400 mb-2">Performance Status</div>
        <div className={`text-sm font-bold ${gaugeStyle.color}`}>
          {hitRate >= 95 && 'Excellent - Optimal cache performance'}
          {hitRate >= 85 && hitRate < 95 && 'Good - Cache performing well'}
          {hitRate >= 70 && hitRate < 85 && 'Fair - Room for improvement'}
          {hitRate < 70 && 'Poor - Cache optimization needed'}
        </div>
      </div>
    </motion.div>
  );
};
