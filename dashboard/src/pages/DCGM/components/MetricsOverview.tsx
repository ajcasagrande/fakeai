/**
 * DCGM Metrics Overview Cards Component
 *
 * Displays 4 key metrics cards: GPU Utilization, Temperature, Power, Memory
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Activity, Thermometer, Zap, HardDrive, Loader2 } from 'lucide-react';
import { GPUMetrics } from '../types';

interface MetricsOverviewProps {
  gpuMetrics: GPUMetrics[];
  loading?: boolean;
}

const getUtilizationColor = (value: number): string => {
  if (value >= 90) return 'text-red-400';
  if (value >= 70) return 'text-yellow-400';
  if (value >= 40) return 'text-green-400';
  return 'text-blue-400';
};

const getTempColor = (value: number): string => {
  if (value >= 80) return 'text-red-400';
  if (value >= 70) return 'text-orange-400';
  if (value >= 60) return 'text-yellow-400';
  return 'text-green-400';
};

const getPowerColor = (value: number, max: number): string => {
  const percentage = (value / max) * 100;
  if (percentage >= 95) return 'text-red-400';
  if (percentage >= 85) return 'text-orange-400';
  if (percentage >= 70) return 'text-yellow-400';
  return 'text-green-400';
};

export const MetricsOverview: React.FC<MetricsOverviewProps> = ({ gpuMetrics, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6">
            <Loader2 className="w-8 h-8 text-gray-400 animate-spin mx-auto" />
          </div>
        ))}
      </div>
    );
  }

  if (!gpuMetrics || gpuMetrics.length === 0) {
    return null;
  }

  // Calculate aggregate metrics across all GPUs
  const avgUtilization = gpuMetrics.reduce((sum, gpu) => sum + gpu.gpu_utilization_pct, 0) / gpuMetrics.length;
  const avgTemp = gpuMetrics.reduce((sum, gpu) => sum + gpu.temperature_c, 0) / gpuMetrics.length;
  const totalPower = gpuMetrics.reduce((sum, gpu) => sum + gpu.power_usage_w, 0);
  const maxPowerLimit = gpuMetrics.length * 700; // Assuming H100 power limit
  const totalMemoryUsed = gpuMetrics.reduce((sum, gpu) => sum + gpu.memory_used_mib, 0);
  const totalMemory = gpuMetrics.reduce((sum, gpu) => sum + gpu.memory_total_mib, 0);
  const memoryPct = (totalMemoryUsed / totalMemory) * 100;

  const maxTemp = Math.max(...gpuMetrics.map(g => g.temperature_c));
  const maxUtil = Math.max(...gpuMetrics.map(g => g.gpu_utilization_pct));

  const cards = [
    {
      title: 'GPU Utilization',
      value: avgUtilization.toFixed(1),
      unit: '%',
      max: maxUtil.toFixed(0),
      icon: Activity,
      color: getUtilizationColor(avgUtilization),
      bgGradient: 'from-green-500/20 to-green-600/5',
      borderColor: 'border-green-500/30',
      percentage: avgUtilization,
    },
    {
      title: 'Temperature',
      value: avgTemp.toFixed(1),
      unit: '°C',
      max: `${maxTemp.toFixed(0)}°C max`,
      icon: Thermometer,
      color: getTempColor(avgTemp),
      bgGradient: 'from-orange-500/20 to-orange-600/5',
      borderColor: 'border-orange-500/30',
      percentage: (avgTemp / 90) * 100, // 90°C max
    },
    {
      title: 'Power Usage',
      value: totalPower.toFixed(0),
      unit: 'W',
      max: `${maxPowerLimit}W limit`,
      icon: Zap,
      color: getPowerColor(totalPower, maxPowerLimit),
      bgGradient: 'from-yellow-500/20 to-yellow-600/5',
      borderColor: 'border-yellow-500/30',
      percentage: (totalPower / maxPowerLimit) * 100,
    },
    {
      title: 'Memory Usage',
      value: (totalMemoryUsed / 1024).toFixed(1),
      unit: 'GB',
      max: `${(totalMemory / 1024).toFixed(0)}GB total`,
      icon: HardDrive,
      color: getUtilizationColor(memoryPct),
      bgGradient: 'from-blue-500/20 to-blue-600/5',
      borderColor: 'border-blue-500/30',
      percentage: memoryPct,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {cards.map((card, index) => (
        <motion.div
          key={card.title}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          className={`bg-gradient-to-br ${card.bgGradient} backdrop-blur-sm border ${card.borderColor} rounded-lg p-6`}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <card.icon className={`w-5 h-5 ${card.color}`} />
              <h3 className="text-sm font-medium text-gray-300">{card.title}</h3>
            </div>
          </div>

          <div className="mb-3">
            <div className="flex items-baseline gap-2">
              <span className={`text-3xl font-bold ${card.color}`}>{card.value}</span>
              <span className="text-lg text-gray-400">{card.unit}</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">{card.max}</p>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(card.percentage, 100)}%` }}
              transition={{ duration: 1, ease: 'easeOut' }}
              className={`h-full rounded-full ${
                card.percentage >= 90
                  ? 'bg-red-500'
                  : card.percentage >= 70
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
              }`}
            />
          </div>

          <p className="text-xs text-gray-400 mt-2 text-center">
            {gpuMetrics.length} GPU{gpuMetrics.length > 1 ? 's' : ''} monitored
          </p>
        </motion.div>
      ))}
    </div>
  );
};
