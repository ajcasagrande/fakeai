/**
 * Rate Limit Overview Component
 * Displays high-level metrics and status cards
 */

import React from 'react';
import { motion } from 'framer-motion';
import { RateLimitsOverview } from '../types';

interface RateLimitOverviewProps {
  overview: RateLimitsOverview;
  loading?: boolean;
}

export const RateLimitOverview: React.FC<RateLimitOverviewProps> = ({
  overview,
  loading = false,
}) => {
  const metrics = [
    {
      title: 'Total API Keys',
      value: overview.total_api_keys,
      icon: '🔑',
      color: 'blue',
      suffix: '',
    },
    {
      title: 'Total Requests',
      value: overview.total_requests.toLocaleString(),
      icon: '📊',
      color: 'green',
      suffix: '',
    },
    {
      title: 'Throttled Requests',
      value: overview.total_throttled.toLocaleString(),
      icon: '⚠️',
      color: overview.throttle_rate > 5 ? 'red' : 'yellow',
      suffix: '',
      alert: overview.throttle_rate > 5,
    },
    {
      title: 'Throttle Rate',
      value: overview.throttle_rate.toFixed(2),
      icon: '📉',
      color: overview.throttle_rate > 5 ? 'red' : overview.throttle_rate > 2 ? 'yellow' : 'green',
      suffix: '%',
      alert: overview.throttle_rate > 5,
    },
    {
      title: 'Active Breaches',
      value: overview.active_breaches,
      icon: '🚨',
      color: overview.active_breaches > 0 ? 'red' : 'green',
      suffix: '',
      alert: overview.active_breaches > 0,
    },
    {
      title: 'Abuse Patterns',
      value: overview.detected_abuse_patterns,
      icon: '🛡️',
      color: overview.detected_abuse_patterns > 0 ? 'red' : 'green',
      suffix: '',
      alert: overview.detected_abuse_patterns > 0,
    },
    {
      title: 'Avg Utilization',
      value: overview.avg_utilization.toFixed(1),
      icon: '📈',
      color: overview.avg_utilization > 80 ? 'yellow' : 'green',
      suffix: '%',
    },
  ];

  const colorClasses = {
    green: {
      bg: 'bg-gradient-to-br from-nvidia-green/10 to-nvidia-green/5',
      border: 'border-nvidia-green/30',
      text: 'text-nvidia-green',
      glow: 'shadow-lg shadow-nvidia-green/20',
    },
    blue: {
      bg: 'bg-gradient-to-br from-blue-500/10 to-blue-500/5',
      border: 'border-blue-500/30',
      text: 'text-blue-400',
      glow: 'shadow-lg shadow-blue-500/20',
    },
    yellow: {
      bg: 'bg-gradient-to-br from-yellow-500/10 to-yellow-500/5',
      border: 'border-yellow-500/30',
      text: 'text-yellow-400',
      glow: 'shadow-lg shadow-yellow-500/20',
    },
    red: {
      bg: 'bg-gradient-to-br from-red-500/10 to-red-500/5',
      border: 'border-red-500/30',
      text: 'text-red-400',
      glow: 'shadow-lg shadow-red-500/20',
    },
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {Array.from({ length: 7 }).map((_, i) => (
          <div
            key={i}
            className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 animate-pulse"
          >
            <div className="h-4 bg-gray-700 rounded w-1/2 mb-4"></div>
            <div className="h-8 bg-gray-700 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {metrics.map((metric, index) => {
        const colors = colorClasses[metric.color as keyof typeof colorClasses];

        return (
          <motion.div
            key={metric.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: index * 0.05 }}
            className={`
              ${colors.bg} ${colors.border} ${colors.glow}
              border rounded-xl p-6
              backdrop-blur-sm
              hover:scale-105 transition-all duration-300
              ${metric.alert ? 'ring-2 ring-red-500/50 animate-pulse' : ''}
            `}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-gray-400 text-sm font-medium mb-1">
                  {metric.title}
                </h3>
                {metric.alert && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-red-500/20 text-red-400">
                    ALERT
                  </span>
                )}
              </div>
              <div className="text-2xl opacity-60">{metric.icon}</div>
            </div>

            <div className="flex items-baseline gap-1">
              <span className={`${colors.text} text-3xl font-bold`}>
                {metric.value}
              </span>
              {metric.suffix && (
                <span className="text-gray-500 text-lg">{metric.suffix}</span>
              )}
            </div>
          </motion.div>
        );
      })}
    </div>
  );
};
