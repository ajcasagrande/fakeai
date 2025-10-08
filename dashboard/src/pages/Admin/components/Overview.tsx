/**
 * Admin Overview Panel
 * Display current system metrics and status
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Activity, Zap, Database, Cpu, Clock, TrendingUp } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { AdminMetrics } from '../types';

interface OverviewProps {
  metrics: AdminMetrics;
  loading?: boolean;
}

export const Overview: React.FC<OverviewProps> = ({ metrics, loading = false }) => {
  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const metrics_data = [
    {
      icon: Activity,
      label: 'Total Requests',
      value: (metrics?.total_requests ?? 0).toLocaleString(),
      color: 'text-nvidia-green',
      bgColor: 'bg-nvidia-green/10',
    },
    {
      icon: Zap,
      label: 'Active Workers',
      value: (metrics?.active_workers ?? 0).toString(),
      color: 'text-blue-400',
      bgColor: 'bg-blue-400/10',
    },
    {
      icon: Database,
      label: 'Cache Hit Rate',
      value: `${Number(metrics?.cache_hit_rate ?? 0).toFixed(1)}%`,
      color: 'text-purple-400',
      bgColor: 'bg-purple-400/10',
    },
    {
      icon: Clock,
      label: 'Avg TTFT',
      value: `${Number(metrics?.avg_ttft_ms ?? 0).toFixed(1)}ms`,
      color: 'text-yellow-400',
      bgColor: 'bg-yellow-400/10',
    },
    {
      icon: TrendingUp,
      label: 'Avg TPOT',
      value: `${Number(metrics?.avg_tpot_ms ?? 0).toFixed(1)}ms`,
      color: 'text-orange-400',
      bgColor: 'bg-orange-400/10',
    },
    {
      icon: Cpu,
      label: 'GPU Utilization',
      value: `${Number(metrics?.gpu_utilization ?? 0).toFixed(0)}%`,
      color: 'text-green-400',
      bgColor: 'bg-green-400/10',
    },
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardContent>
              <div className="h-24 bg-nvidia-green/10 rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* System Status Header */}
      <Card className="border-nvidia-green/30 bg-gradient-to-br from-nvidia-green/5 to-transparent">
        <CardContent className="py-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">System Status</h2>
              <p className="text-gray-400">Real-time metrics and performance indicators</p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-400 mb-1">System Uptime</div>
              <div className="text-2xl font-bold text-nvidia-green">
                {formatUptime(metrics?.uptime_seconds ?? 0)}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {metrics_data.map((metric, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card hover className="border-nvidia-green/20 h-full">
              <CardContent className="py-6">
                <div className="flex items-start gap-4">
                  <div className={`p-3 ${metric.bgColor} border border-${metric.color}/20 rounded-lg`}>
                    <metric.icon className={`w-6 h-6 ${metric.color}`} />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-400 mb-1">{metric.label}</p>
                    <p className={`text-3xl font-bold ${metric.color}`}>{metric.value}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Queue Depth Indicator */}
      <Card className="border-nvidia-green/30">
        <CardHeader>
          <CardTitle className="text-nvidia-green">Queue Depth Monitor</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Current Queue Depth</span>
              <span className="text-white font-bold">{metrics?.queue_depth ?? 0}</span>
            </div>
            <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(((metrics?.queue_depth ?? 0) / 100) * 100, 100)}%` }}
                transition={{ duration: 0.5 }}
                className={`h-full rounded-full ${
                  (metrics?.queue_depth ?? 0) < 30
                    ? 'bg-green-500'
                    : (metrics?.queue_depth ?? 0) < 70
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
              />
            </div>
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>0</span>
              <span>50</span>
              <span>100</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
