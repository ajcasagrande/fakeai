/**
 * Metrics Overview Component
 *
 * Beautiful glass morphism cards displaying key benchmark metrics
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Clock, Zap, Activity, TrendingUp, Users, Timer } from 'lucide-react';
import { BenchmarkRecords } from '../types';

interface MetricsOverviewProps {
  records: BenchmarkRecords;
  loading?: boolean;
}

export const MetricsOverview: React.FC<MetricsOverviewProps> = ({ records, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="h-48 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl animate-pulse"
          />
        ))}
      </div>
    );
  }

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
    return num.toFixed(2);
  };

  const getPerformanceColor = (metricType: string, value: number) => {
    // Lower is better for latency metrics
    if (metricType === 'latency') {
      if (value < 50) return { color: 'text-green-500', bg: 'bg-green-500/10', border: 'border-green-500/50' };
      if (value < 200) return { color: 'text-yellow-500', bg: 'bg-yellow-500/10', border: 'border-yellow-500/50' };
      return { color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500/50' };
    }
    // Higher is better for throughput
    if (metricType === 'throughput') {
      if (value > 5000) return { color: 'text-green-500', bg: 'bg-green-500/10', border: 'border-green-500/50' };
      if (value > 1000) return { color: 'text-yellow-500', bg: 'bg-yellow-500/10', border: 'border-yellow-500/50' };
      return { color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500/50' };
    }
    return { color: 'text-blue-500', bg: 'bg-blue-500/10', border: 'border-blue-500/50' };
  };

  const ttftColors = getPerformanceColor('latency', records.ttft.avg);
  const latencyColors = getPerformanceColor('latency', records.request_latency.avg);
  const itlColors = getPerformanceColor('latency', records.inter_token_latency.avg);
  const throughputColors = getPerformanceColor('throughput', records.output_token_throughput.avg);

  const metricCards = [
    {
      icon: Clock,
      label: 'Time to First Token (TTFT)',
      value: `${records.ttft.avg.toFixed(2)}ms`,
      stats: [
        { label: 'P50', value: `${records.ttft.p50?.toFixed(2)}ms` },
        { label: 'P95', value: `${records.ttft.p95?.toFixed(2)}ms` },
        { label: 'P99', value: `${records.ttft.p99?.toFixed(2)}ms` },
      ],
      ...ttftColors,
    },
    {
      icon: Activity,
      label: 'Request Latency',
      value: `${records.request_latency.avg.toFixed(2)}ms`,
      stats: [
        { label: 'P50', value: `${records.request_latency.p50?.toFixed(2)}ms` },
        { label: 'P95', value: `${records.request_latency.p95?.toFixed(2)}ms` },
        { label: 'P99', value: `${records.request_latency.p99?.toFixed(2)}ms` },
      ],
      ...latencyColors,
    },
    {
      icon: Timer,
      label: 'Inter Token Latency (ITL)',
      value: `${records.inter_token_latency.avg.toFixed(2)}ms`,
      stats: [
        { label: 'P50', value: `${records.inter_token_latency.p50?.toFixed(2)}ms` },
        { label: 'P95', value: `${records.inter_token_latency.p95?.toFixed(2)}ms` },
        { label: 'P99', value: `${records.inter_token_latency.p99?.toFixed(2)}ms` },
      ],
      ...itlColors,
    },
    {
      icon: TrendingUp,
      label: 'Request Throughput',
      value: `${records.request_throughput.avg.toFixed(2)}`,
      stats: [
        { label: 'Unit', value: 'req/sec' },
        { label: 'Total', value: formatNumber(records.request_count.avg) },
        { label: 'Duration', value: `${records.benchmark_duration.avg.toFixed(1)}s` },
      ],
      color: 'text-purple-500',
      bg: 'bg-purple-500/10',
      border: 'border-purple-500/50',
    },
    {
      icon: Zap,
      label: 'Output Token Throughput',
      value: `${formatNumber(records.output_token_throughput.avg)}`,
      stats: [
        { label: 'Unit', value: 'tokens/sec' },
        { label: 'Total', value: formatNumber(records.total_output_tokens.avg) },
        { label: 'Avg/Req', value: `${records.output_token_count.avg.toFixed(0)} tokens` },
      ],
      ...throughputColors,
    },
    {
      icon: Users,
      label: 'Benchmark Configuration',
      value: `${records.request_count.avg.toFixed(0)}`,
      stats: [
        { label: 'Requests', value: formatNumber(records.request_count.avg) },
        { label: 'Duration', value: `${records.benchmark_duration.avg.toFixed(2)}s` },
        { label: 'Avg Input', value: `${records.input_sequence_length.avg.toFixed(0)} tokens` },
      ],
      color: 'text-cyan-500',
      bg: 'bg-cyan-500/10',
      border: 'border-cyan-500/50',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
      {metricCards.map((card, index) => {
        const Icon = card.icon;
        return (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            whileHover={{ scale: 1.02, y: -5 }}
            className={`p-6 bg-white/5 backdrop-blur-sm border ${card.border} rounded-xl hover:shadow-2xl transition-all group`}
          >
            <div className="flex items-start gap-4 mb-4">
              <div className={`p-3 ${card.bg} rounded-lg ${card.color} group-hover:scale-110 transition-transform`}>
                <Icon className="w-6 h-6" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">
                  {card.label}
                </div>
                <div className={`text-3xl font-bold ${card.color} mb-1`}>
                  {card.value}
                </div>
              </div>
            </div>

            <div className="space-y-2 border-t border-white/5 pt-4">
              {card.stats.map((stat) => (
                <div key={stat.label} className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">{stat.label}</span>
                  <span className="text-sm text-gray-300 font-semibold">{stat.value}</span>
                </div>
              ))}
            </div>
          </motion.div>
        );
      })}
    </div>
  );
};
