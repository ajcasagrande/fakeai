/**
 * Usage Progress Bars Component
 * Displays current usage vs limits with progress bars and real-time monitoring
 */

import React from 'react';
import { motion } from 'framer-motion';
import { ApiKeyRateLimit } from '../types';

interface UsageProgressBarsProps {
  apiKeyLimits: ApiKeyRateLimit[];
  loading?: boolean;
  realTime?: boolean;
}

export const UsageProgressBars: React.FC<UsageProgressBarsProps> = ({
  apiKeyLimits,
  loading = false,
  realTime = false,
}) => {
  const getProgressColor = (percentage: number): string => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 75) return 'bg-yellow-500';
    return 'bg-nvidia-green';
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'healthy':
        return 'text-nvidia-green';
      case 'warning':
        return 'text-yellow-400';
      case 'critical':
        return 'text-orange-500';
      case 'throttled':
        return 'text-red-500';
      default:
        return 'text-gray-400';
    }
  };

  const getStatusBadge = (status: string): JSX.Element => {
    const badges: Record<string, { bg: string; text: string; icon: string }> = {
      healthy: { bg: 'bg-nvidia-green/20', text: 'text-nvidia-green', icon: '✓' },
      warning: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', icon: '⚠' },
      critical: { bg: 'bg-orange-500/20', text: 'text-orange-500', icon: '⚠' },
      throttled: { bg: 'bg-red-500/20', text: 'text-red-400', icon: '🚫' },
    };

    const badge = badges[status] || badges.healthy;

    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${badge.bg} ${badge.text}`}
      >
        <span>{badge.icon}</span>
        {status.toUpperCase()}
      </span>
    );
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  if (loading) {
    return (
      <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
        <div className="h-6 bg-gray-700 rounded w-1/3 mb-4 animate-pulse"></div>
        <div className="space-y-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-gray-700 rounded w-1/4 mb-2"></div>
              <div className="h-8 bg-gray-700 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-white mb-1">Usage vs Limits</h3>
          <p className="text-gray-400 text-sm">
            Real-time monitoring of API key rate limit utilization
          </p>
        </div>
        <div className="flex items-center gap-2">
          {realTime && (
            <span className="flex items-center gap-2 text-nvidia-green text-sm font-medium">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-nvidia-green opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-nvidia-green"></span>
              </span>
              LIVE
            </span>
          )}
          <div className="text-2xl">📊</div>
        </div>
      </div>

      <div className="space-y-6">
        {apiKeyLimits.map((apiKey, index) => (
          <motion.div
            key={apiKey.api_key}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            className="border border-gray-700/50 rounded-lg p-4 hover:border-gray-600/50 transition-colors"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-white font-semibold">
                    {apiKey.api_key_name || apiKey.api_key.substring(0, 20) + '...'}
                  </span>
                  <span className="text-gray-500 text-xs font-mono">
                    {apiKey.tier.toUpperCase()}
                  </span>
                </div>
                <div className="text-gray-400 text-xs">
                  {apiKey.throttled_requests > 0 && (
                    <span className="text-red-400">
                      {apiKey.throttled_requests} throttled requests
                    </span>
                  )}
                </div>
              </div>
              {getStatusBadge(apiKey.status)}
            </div>

            {/* RPM Progress */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">
                  Requests Per Minute (RPM)
                </span>
                <span className="text-sm font-mono text-white">
                  {formatNumber(apiKey.current_usage.rpm)} / {formatNumber(apiKey.limits.rpm)}
                </span>
              </div>
              <div className="relative h-3 bg-gray-700/50 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(apiKey.usage_percentage.rpm, 100)}%` }}
                  transition={{ duration: 0.5, delay: index * 0.05 }}
                  className={`h-full ${getProgressColor(apiKey.usage_percentage.rpm)} rounded-full`}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
                </motion.div>
              </div>
              <div className="text-right mt-1">
                <span
                  className={`text-xs font-semibold ${getStatusColor(
                    apiKey.usage_percentage.rpm >= 90 ? 'throttled' : 'healthy'
                  )}`}
                >
                  {apiKey.usage_percentage.rpm.toFixed(1)}%
                </span>
              </div>
            </div>

            {/* TPM Progress */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">
                  Tokens Per Minute (TPM)
                </span>
                <span className="text-sm font-mono text-white">
                  {formatNumber(apiKey.current_usage.tpm)} / {formatNumber(apiKey.limits.tpm)}
                </span>
              </div>
              <div className="relative h-3 bg-gray-700/50 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(apiKey.usage_percentage.tpm, 100)}%` }}
                  transition={{ duration: 0.5, delay: index * 0.05 + 0.1 }}
                  className={`h-full ${getProgressColor(apiKey.usage_percentage.tpm)} rounded-full`}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
                </motion.div>
              </div>
              <div className="text-right mt-1">
                <span
                  className={`text-xs font-semibold ${getStatusColor(
                    apiKey.usage_percentage.tpm >= 90 ? 'throttled' : 'healthy'
                  )}`}
                >
                  {apiKey.usage_percentage.tpm.toFixed(1)}%
                </span>
              </div>
            </div>

            {/* RPD Progress */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">
                  Requests Per Day (RPD)
                </span>
                <span className="text-sm font-mono text-white">
                  {formatNumber(apiKey.current_usage.rpd)} / {formatNumber(apiKey.limits.rpd)}
                </span>
              </div>
              <div className="relative h-3 bg-gray-700/50 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(apiKey.usage_percentage.rpd, 100)}%` }}
                  transition={{ duration: 0.5, delay: index * 0.05 + 0.2 }}
                  className={`h-full ${getProgressColor(apiKey.usage_percentage.rpd)} rounded-full`}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
                </motion.div>
              </div>
              <div className="text-right mt-1">
                <span
                  className={`text-xs font-semibold ${getStatusColor(
                    apiKey.usage_percentage.rpd >= 90 ? 'throttled' : 'healthy'
                  )}`}
                >
                  {apiKey.usage_percentage.rpd.toFixed(1)}%
                </span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {apiKeyLimits.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No API keys found
        </div>
      )}
    </div>
  );
};
