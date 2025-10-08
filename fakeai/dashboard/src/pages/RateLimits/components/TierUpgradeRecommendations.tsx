/**
 * Tier Upgrade Recommendations Component
 * Provides intelligent recommendations for tier upgrades
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { TierUpgradeRecommendation } from '../types';

interface TierUpgradeRecommendationsProps {
  recommendations: TierUpgradeRecommendation[];
  loading?: boolean;
}

export const TierUpgradeRecommendations: React.FC<TierUpgradeRecommendationsProps> = ({
  recommendations,
  loading = false,
}) => {
  const [sortBy, setSortBy] = useState<'priority' | 'throttles' | 'utilization'>('priority');

  const sortedRecommendations = React.useMemo(() => {
    return [...recommendations].sort((a, b) => {
      switch (sortBy) {
        case 'priority':
          const priorityOrder = { high: 3, medium: 2, low: 1 };
          return priorityOrder[b.priority] - priorityOrder[a.priority];
        case 'throttles':
          return b.metrics.throttle_rate - a.metrics.throttle_rate;
        case 'utilization':
          return b.metrics.avg_utilization - a.metrics.avg_utilization;
        default:
          return 0;
      }
    });
  }, [recommendations, sortBy]);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return {
          bg: 'bg-red-500/10',
          border: 'border-red-500/30',
          text: 'text-red-400',
          badge: 'bg-red-500/20 text-red-300',
          icon: '🔴',
        };
      case 'medium':
        return {
          bg: 'bg-yellow-500/10',
          border: 'border-yellow-500/30',
          text: 'text-yellow-400',
          badge: 'bg-yellow-500/20 text-yellow-300',
          icon: '🟡',
        };
      case 'low':
        return {
          bg: 'bg-blue-500/10',
          border: 'border-blue-500/30',
          text: 'text-blue-400',
          badge: 'bg-blue-500/20 text-blue-300',
          icon: '🔵',
        };
      default:
        return {
          bg: 'bg-gray-500/10',
          border: 'border-gray-500/30',
          text: 'text-gray-400',
          badge: 'bg-gray-500/20 text-gray-300',
          icon: '⚪',
        };
    }
  };

  const getTierLabel = (tier: string): string => {
    const labels: Record<string, string> = {
      free: 'Free',
      tier1: 'Tier 1',
      tier2: 'Tier 2',
      tier3: 'Tier 3',
      tier4: 'Tier 4',
      tier5: 'Tier 5',
    };
    return labels[tier] || tier.toUpperCase();
  };

  const getTierColor = (tier: string): string => {
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

  if (loading) {
    return (
      <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
        <div className="h-6 bg-gray-700 rounded w-1/3 mb-4 animate-pulse"></div>
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-40 bg-gray-700/50 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-white mb-1">
            Tier Upgrade Recommendations
          </h3>
          <p className="text-gray-400 text-sm">
            Intelligent suggestions to optimize API key performance
          </p>
        </div>
        <div className="flex items-center gap-2">
          {recommendations.length > 0 && (
            <span className="px-3 py-1 bg-nvidia-green/20 text-nvidia-green rounded-full text-sm font-semibold">
              {recommendations.length} Recommended
            </span>
          )}
          <div className="text-2xl">💡</div>
        </div>
      </div>

      {/* Sort Controls */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setSortBy('priority')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            sortBy === 'priority'
              ? 'bg-nvidia-green/20 text-nvidia-green border border-nvidia-green/30'
              : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700'
          }`}
        >
          By Priority
        </button>
        <button
          onClick={() => setSortBy('throttles')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            sortBy === 'throttles'
              ? 'bg-nvidia-green/20 text-nvidia-green border border-nvidia-green/30'
              : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700'
          }`}
        >
          By Throttles
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

      {/* Recommendations List */}
      <div className="space-y-4">
        {sortedRecommendations.map((rec, index) => {
          const colors = getPriorityColor(rec.priority);

          return (
            <motion.div
              key={rec.api_key}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
              className={`
                ${colors.bg} ${colors.border}
                border-2 rounded-lg p-5
                backdrop-blur-sm
                hover:scale-102 transition-all duration-300
              `}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="text-3xl">{colors.icon}</div>
                  <div>
                    <h4 className="text-white font-bold text-lg mb-1">
                      {rec.api_key_name || rec.api_key.substring(0, 20) + '...'}
                    </h4>
                    <div className="flex items-center gap-2">
                      <span className={`font-mono text-sm ${getTierColor(rec.current_tier)}`}>
                        {getTierLabel(rec.current_tier)}
                      </span>
                      <span className="text-gray-500">→</span>
                      <span className={`font-mono text-sm ${getTierColor(rec.recommended_tier)}`}>
                        {getTierLabel(rec.recommended_tier)}
                      </span>
                    </div>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-bold ${colors.badge}`}>
                  {rec.priority.toUpperCase()} PRIORITY
                </span>
              </div>

              {/* Reason */}
              <div className="mb-4">
                <div className="text-gray-300 text-sm leading-relaxed">{rec.reason}</div>
              </div>

              {/* Metrics */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-gray-900/30 rounded-lg p-3">
                  <div className="text-gray-400 text-xs mb-1">Throttle Rate</div>
                  <div className={`${colors.text} font-bold text-lg`}>
                    {rec.metrics.throttle_rate.toFixed(1)}%
                  </div>
                </div>

                <div className="bg-gray-900/30 rounded-lg p-3">
                  <div className="text-gray-400 text-xs mb-1">Avg Utilization</div>
                  <div className={`${colors.text} font-bold text-lg`}>
                    {rec.metrics.avg_utilization.toFixed(1)}%
                  </div>
                </div>

                <div className="bg-gray-900/30 rounded-lg p-3">
                  <div className="text-gray-400 text-xs mb-1">Peak Requests</div>
                  <div className={`${colors.text} font-bold text-lg`}>
                    {rec.metrics.peak_requests.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Potential Savings */}
              <div className="border-t border-gray-700/50 pt-4">
                <div className="text-nvidia-green text-sm font-semibold mb-3">
                  Expected Benefits
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-start gap-2">
                    <div className="text-nvidia-green mt-0.5">✓</div>
                    <div>
                      <div className="text-gray-400 text-xs">Reduced Throttles</div>
                      <div className="text-white font-bold">
                        -{rec.potential_savings.reduced_throttles}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-start gap-2">
                    <div className="text-nvidia-green mt-0.5">✓</div>
                    <div>
                      <div className="text-gray-400 text-xs">Improved Latency</div>
                      <div className="text-white font-bold">
                        -{rec.potential_savings.improved_latency_ms}ms
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="mt-4">
                <button
                  className={`
                    w-full py-3 px-4 rounded-lg font-semibold
                    bg-gradient-to-r from-nvidia-green to-green-500
                    hover:from-nvidia-green/90 hover:to-green-500/90
                    text-black
                    transition-all duration-300
                    hover:shadow-lg hover:shadow-nvidia-green/50
                  `}
                >
                  Upgrade to {getTierLabel(rec.recommended_tier)}
                </button>
              </div>
            </motion.div>
          );
        })}
      </div>

      {recommendations.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">✅</div>
          <div className="text-nvidia-green font-semibold mb-2">
            All Tiers Optimized
          </div>
          <div className="text-gray-500 text-sm">
            No tier upgrade recommendations at this time
          </div>
        </div>
      )}
    </div>
  );
};
