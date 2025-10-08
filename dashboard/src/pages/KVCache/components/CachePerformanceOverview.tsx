/**
 * Cache Performance Overview Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Gauge, TrendingUp, CheckCircle, Zap } from 'lucide-react';
import { CachePerformance } from '../types';

interface CachePerformanceOverviewProps {
  performance: CachePerformance;
  loading?: boolean;
}

export const CachePerformanceOverview: React.FC<CachePerformanceOverviewProps> = ({
  performance,
  loading,
}) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-40 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
    return num.toFixed(0);
  };

  const metricCards = [
    {
      icon: Gauge,
      label: 'Cache Hit Rate',
      value: `${performance.cache_hit_rate.toFixed(2)}%`,
      subtext: `${formatNumber(performance.total_cache_hits)} hits`,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500/50',
    },
    {
      icon: TrendingUp,
      label: 'Token Reuse Rate',
      value: `${performance.token_reuse_rate.toFixed(2)}%`,
      subtext: `${formatNumber(performance.cached_tokens_reused)} reused`,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500/50',
    },
    {
      icon: CheckCircle,
      label: 'Tokens Processed',
      value: formatNumber(performance.total_tokens_processed),
      subtext: `Avg prefix: ${performance.average_prefix_length.toFixed(0)}`,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
      borderColor: 'border-blue-500/50',
    },
    {
      icon: Zap,
      label: 'Speedup Ratio',
      value: `${performance.speedup_stats.avg_speedup_ratio.toFixed(1)}x`,
      subtext: `${formatNumber(performance.speedup_stats.total_speedup_records)} records`,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500/50',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {metricCards.map((card, index) => {
        const Icon = card.icon;
        return (
          <motion.div
            key={card.label}
            initial={false}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            whileHover={{ scale: 1.02 }}
            className={`p-6 bg-white/5 backdrop-blur-sm border ${card.borderColor} rounded-xl hover:shadow-lg transition-all`}
          >
            <div className="flex items-start gap-4">
              <div className={`p-3 ${card.bgColor} rounded-lg ${card.color}`}>
                <Icon className="w-6 h-6" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">
                  {card.label}
                </div>
                <div className="text-2xl font-bold text-white mb-1 truncate">
                  {card.value}
                </div>
                <div className="text-xs text-gray-500">
                  {card.subtext}
                </div>
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
};
