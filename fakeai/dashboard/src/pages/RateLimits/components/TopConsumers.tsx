/**
 * Top Consumers Component
 * Displays top API key consumers by usage
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { TopConsumer } from '../types';

interface TopConsumersProps {
  consumers: TopConsumer[];
  loading?: boolean;
}

export const TopConsumers: React.FC<TopConsumersProps> = ({
  consumers,
  loading = false,
}) => {
  const [sortBy, setSortBy] = useState<'requests' | 'tokens' | 'utilization'>('requests');

  const sortedConsumers = React.useMemo(() => {
    return [...consumers].sort((a, b) => {
      switch (sortBy) {
        case 'requests':
          return b.total_requests - a.total_requests;
        case 'tokens':
          return b.total_tokens - a.total_tokens;
        case 'utilization':
          return b.utilization_percentage - a.utilization_percentage;
        default:
          return 0;
      }
    });
  }, [consumers, sortBy]);

  const getTierColor = (tier: string) => {
    const colors: Record<string, string> = {
      free: 'text-gray-400',
      tier1: 'text-blue-400',
      tier2: 'text-nvidia-green',
      tier3: 'text-yellow-400',
      tier4: 'text-orange-400',
      tier5: 'text-purple-400',
    };
    return colors[tier] || 'text-gray-400';
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  const formatLastActive = (timestamp: number): string => {
    const now = Date.now();
    const diff = now - timestamp;

    if (diff < 60000) return 'Active now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return `${Math.floor(diff / 86400000)}d ago`;
  };

  const getUtilizationColor = (utilization: number): string => {
    if (utilization >= 90) return 'text-red-400';
    if (utilization >= 75) return 'text-yellow-400';
    return 'text-nvidia-green';
  };

  if (loading) {
    return (
      <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
        <div className="h-6 bg-gray-700 rounded w-1/3 mb-4 animate-pulse"></div>
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-20 bg-gray-700/50 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-white mb-1">Top Consumers</h3>
          <p className="text-gray-400 text-sm">
            Highest usage API keys ranked by consumption
          </p>
        </div>
        <div className="text-2xl">🏆</div>
      </div>

      {/* Sort Controls */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setSortBy('requests')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            sortBy === 'requests'
              ? 'bg-nvidia-green/20 text-nvidia-green border border-nvidia-green/30'
              : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700'
          }`}
        >
          By Requests
        </button>
        <button
          onClick={() => setSortBy('tokens')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            sortBy === 'tokens'
              ? 'bg-nvidia-green/20 text-nvidia-green border border-nvidia-green/30'
              : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700'
          }`}
        >
          By Tokens
        </button>
        <button
          onClick={() => setSortBy('utilization')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            sortBy === 'utilization'
              ? 'bg-nvidia-green/20 text-nvidia-green border border-nvidia-green/30'
              : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700'
          }`}
        >
          By Utilization
        </button>
      </div>

      {/* Consumer List */}
      <div className="space-y-3">
        {sortedConsumers.map((consumer, index) => (
          <motion.div
            key={consumer.api_key}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: index * 0.03 }}
            className="bg-gray-900/50 border border-gray-700/50 rounded-lg p-4 hover:border-gray-600/50 transition-all hover:scale-102"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-nvidia-green/20 to-nvidia-green/5 border border-nvidia-green/30">
                  <span className="text-nvidia-green font-bold text-lg">
                    #{index + 1}
                  </span>
                </div>
                <div>
                  <div className="text-white font-semibold">
                    {consumer.api_key_name || consumer.api_key.substring(0, 20) + '...'}
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className={`font-mono ${getTierColor(consumer.tier)}`}>
                      {consumer.tier.toUpperCase()}
                    </span>
                    <span className="text-gray-600">•</span>
                    <span className="text-gray-500">
                      {formatLastActive(consumer.last_active)}
                    </span>
                  </div>
                </div>
              </div>

              {consumer.throttle_count > 0 && (
                <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs font-semibold">
                  {consumer.throttle_count} throttles
                </span>
              )}
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-4 gap-3">
              <div className="text-center">
                <div className="text-gray-400 text-xs mb-1">Requests</div>
                <div className="text-white font-bold">
                  {formatNumber(consumer.total_requests)}
                </div>
              </div>

              <div className="text-center">
                <div className="text-gray-400 text-xs mb-1">Tokens</div>
                <div className="text-white font-bold">
                  {formatNumber(consumer.total_tokens)}
                </div>
              </div>

              <div className="text-center">
                <div className="text-gray-400 text-xs mb-1">RPM</div>
                <div className="text-white font-bold">
                  {consumer.avg_requests_per_minute.toFixed(1)}
                </div>
              </div>

              <div className="text-center">
                <div className="text-gray-400 text-xs mb-1">Utilization</div>
                <div className={`font-bold ${getUtilizationColor(consumer.utilization_percentage)}`}>
                  {consumer.utilization_percentage.toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Utilization Bar */}
            <div className="mt-3 relative h-2 bg-gray-700/50 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(consumer.utilization_percentage, 100)}%` }}
                transition={{ duration: 0.5, delay: index * 0.03 }}
                className={`h-full rounded-full ${
                  consumer.utilization_percentage >= 90
                    ? 'bg-gradient-to-r from-red-500 to-red-400'
                    : consumer.utilization_percentage >= 75
                    ? 'bg-gradient-to-r from-yellow-500 to-yellow-400'
                    : 'bg-gradient-to-r from-nvidia-green to-green-400'
                }`}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
              </motion.div>
            </div>
          </motion.div>
        ))}
      </div>

      {consumers.length === 0 && (
        <div className="text-center py-12 text-gray-500">No consumer data available</div>
      )}
    </div>
  );
};
