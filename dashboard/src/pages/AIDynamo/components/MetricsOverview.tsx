/**
 * AI-Dynamo Metrics Overview Component
 *
 * Displays key LLM inference performance metrics at a glance
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Activity, Clock, Zap, Database, Layers, Server, Hash, TrendingUp } from 'lucide-react';
import { AIDynamoMetrics } from '../types';

interface MetricsOverviewProps {
  metrics: AIDynamoMetrics;
  loading?: boolean;
}

export const MetricsOverview: React.FC<MetricsOverviewProps> = ({ metrics, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="h-32 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  const formatNumber = (num: number | undefined): string => {
    if (num === undefined || num === null) return 'N/A';
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
    return num.toFixed(0);
  };

  const formatLatency = (ms: number | undefined): string => {
    if (ms === undefined || ms === null) return 'N/A';
    return `${ms.toFixed(1)}ms`;
  };

  const formatPercentage = (value: number | undefined): string => {
    if (value === undefined || value === null) return 'N/A';
    return `${(value * 100).toFixed(1)}%`;
  };

  const metricCards = [
    {
      icon: Activity,
      label: 'Total Requests',
      value: formatNumber(metrics?.request_count),
      subtext: `Success: ${formatPercentage(metrics?.success_rate)}`,
      color: 'text-green-500',
    },
    {
      icon: Clock,
      label: 'TTFT (P95)',
      value: formatLatency(metrics?.latency?.ttft?.p95),
      subtext: `Avg: ${formatLatency(metrics?.latency?.ttft?.avg)}`,
      color: 'text-blue-500',
    },
    {
      icon: Zap,
      label: 'TPOT (P95)',
      value: formatLatency(metrics?.latency?.tpot?.p95),
      subtext: `Avg: ${formatLatency(metrics?.latency?.tpot?.avg)}`,
      color: 'text-green-500',
    },
    {
      icon: TrendingUp,
      label: 'Throughput',
      value: metrics?.throughput?.requests_per_sec?.toFixed(1) || 'N/A',
      subtext: 'req/s',
      color: 'text-orange-500',
    },
    {
      icon: Hash,
      label: 'Token Throughput',
      value: formatNumber(metrics?.throughput?.tokens_per_sec),
      subtext: 'tokens/s',
      color: 'text-pink-500',
    },
    {
      icon: Layers,
      label: 'Queue Depth',
      value: metrics?.queue?.current_depth?.toString() || 'N/A',
      subtext: `Wait: ${formatLatency(metrics?.queue?.avg_wait_time_ms)}`,
      color: 'text-orange-500',
    },
    {
      icon: Database,
      label: 'KV Cache Hit Rate',
      value: formatPercentage(metrics?.kv_cache?.hit_rate),
      subtext: `Blocks: ${metrics?.kv_cache?.avg_blocks_matched?.toFixed(1) || 'N/A'}`,
      color: 'text-blue-500',
    },
    {
      icon: Server,
      label: 'Active Workers',
      value: `${metrics?.workers?.active_workers || 0}/${metrics?.workers?.total_workers || 0}`,
      subtext: `Util: ${formatPercentage(metrics?.workers?.avg_utilization)}`,
      color: 'text-green-500',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {metricCards.map((card, index) => {
        const Icon = card.icon;
        return (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            whileHover={{ scale: 1.02, borderColor: 'rgba(118, 185, 0, 0.5)' }}
            className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:shadow-lg transition-all"
          >
            <div className="flex items-start gap-4">
              <div className={`p-3 bg-white/5 rounded-lg ${card.color}`}>
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
