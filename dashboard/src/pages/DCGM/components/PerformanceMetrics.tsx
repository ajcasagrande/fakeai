/**
 * Performance Metrics Component
 *
 * Displays SM Clock, SM Active %, Tensor Core %, Memory Bandwidth, Performance State
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Cpu, Gauge, MemoryStick, Zap, Loader2 } from 'lucide-react';
import { GPUMetrics } from '../types';

interface PerformanceMetricsProps {
  gpuMetrics: GPUMetrics[];
  loading?: boolean;
}

export const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ gpuMetrics, loading }) => {
  if (loading) {
    return (
      <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
        <Loader2 className="w-8 h-8 text-gray-400 animate-spin mx-auto" />
      </div>
    );
  }

  if (!gpuMetrics || gpuMetrics.length === 0) {
    return null;
  }

  // Calculate aggregate performance metrics
  const avgSmClock = gpuMetrics.reduce((sum, gpu) => sum + gpu.sm_clock_mhz, 0) / gpuMetrics.length;
  const avgSmActive = gpuMetrics.reduce((sum, gpu) => sum + gpu.sm_active_pct, 0) / gpuMetrics.length;
  const avgTensorActive = gpuMetrics.reduce((sum, gpu) => sum + gpu.tensor_active_pct, 0) / gpuMetrics.length;
  const avgDramActive = gpuMetrics.reduce((sum, gpu) => sum + gpu.dram_active_pct, 0) / gpuMetrics.length;
  const avgPState = gpuMetrics.reduce((sum, gpu) => sum + gpu.performance_state, 0) / gpuMetrics.length;

  const metrics = [
    {
      label: 'SM Clock',
      value: avgSmClock.toFixed(0),
      unit: 'MHz',
      icon: Cpu,
      color: 'text-green-400',
      progress: null,
    },
    {
      label: 'SM Active',
      value: avgSmActive.toFixed(1),
      unit: '%',
      icon: Gauge,
      color: 'text-blue-400',
      progress: avgSmActive,
    },
    {
      label: 'Tensor Core Active',
      value: avgTensorActive.toFixed(1),
      unit: '%',
      icon: Zap,
      color: 'text-purple-400',
      progress: avgTensorActive,
    },
    {
      label: 'Memory Bandwidth (DRAM Active)',
      value: avgDramActive.toFixed(1),
      unit: '%',
      icon: MemoryStick,
      color: 'text-cyan-400',
      progress: avgDramActive,
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-green-500/20 rounded-lg">
          <Cpu className="w-6 h-6 text-green-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Performance Metrics</h2>
          <p className="text-sm text-gray-400">
            Compute and memory performance across {gpuMetrics.length} GPU{gpuMetrics.length > 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* Performance State Badge */}
      <div className="mb-6 flex items-center gap-3">
        <span className="text-sm text-gray-400">Performance State:</span>
        <span
          className={`px-3 py-1 rounded-full text-sm font-semibold ${
            avgPState === 0
              ? 'bg-green-500/20 text-green-400 border border-green-500/50'
              : avgPState <= 4
              ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/50'
              : 'bg-orange-500/20 text-orange-400 border border-orange-500/50'
          }`}
        >
          P{avgPState.toFixed(0)} {avgPState === 0 ? '(Max Performance)' : ''}
        </span>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white/5 rounded-lg p-4 border border-white/10"
          >
            <div className="flex items-center gap-3 mb-3">
              <metric.icon className={`w-5 h-5 ${metric.color}`} />
              <span className="text-sm text-gray-300">{metric.label}</span>
            </div>

            <div className="flex items-baseline gap-2 mb-2">
              <span className={`text-2xl font-bold ${metric.color}`}>{metric.value}</span>
              <span className="text-sm text-gray-400">{metric.unit}</span>
            </div>

            {metric.progress !== null && (
              <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(metric.progress, 100)}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                  className={`h-full rounded-full ${
                    metric.progress >= 90
                      ? 'bg-red-500'
                      : metric.progress >= 70
                      ? 'bg-yellow-500'
                      : 'bg-green-500'
                  }`}
                />
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Per-GPU breakdown (collapsed by default, show summary) */}
      <div className="mt-6 pt-6 border-t border-white/10">
        <h3 className="text-sm font-semibold text-gray-400 mb-3">Per-GPU Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {gpuMetrics.slice(0, 4).map((gpu) => (
            <div key={gpu.gpu_id} className="bg-white/5 rounded-lg p-3">
              <div className="text-xs text-gray-500 mb-1">GPU {gpu.gpu_id}</div>
              <div className="text-sm font-semibold text-green-400">{gpu.sm_clock_mhz} MHz</div>
              <div className="text-xs text-gray-400">P{gpu.performance_state}</div>
            </div>
          ))}
        </div>
        {gpuMetrics.length > 4 && (
          <p className="text-xs text-gray-500 mt-2 text-center">
            +{gpuMetrics.length - 4} more GPU{gpuMetrics.length - 4 > 1 ? 's' : ''}
          </p>
        )}
      </div>
    </motion.div>
  );
};
