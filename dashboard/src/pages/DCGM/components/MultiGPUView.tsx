/**
 * Multi-GPU View Component
 *
 * Side-by-side comparison cards for each GPU
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, Thermometer, Zap, HardDrive, Activity, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { GPUMetrics } from '../types';

interface MultiGPUViewProps {
  gpuMetrics: GPUMetrics[];
  loading?: boolean;
}

export const MultiGPUView: React.FC<MultiGPUViewProps> = ({ gpuMetrics, loading }) => {
  const [expandedGPU, setExpandedGPU] = useState<number | null>(null);

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

  const toggleExpand = (gpuId: number) => {
    setExpandedGPU(expandedGPU === gpuId ? null : gpuId);
  };

  const getStatusColor = (gpu: GPUMetrics): string => {
    if (gpu.thermal_throttle > 0 || gpu.power_throttle > 0) return 'border-red-500/50 bg-red-500/5';
    if (gpu.temperature_c > 75 || gpu.power_usage_w > 650) return 'border-orange-500/50 bg-orange-500/5';
    if (gpu.gpu_utilization_pct > 80) return 'border-green-500/50 bg-green-500/5';
    return 'border-white/10 bg-white/5';
  };

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
          <h2 className="text-xl font-bold text-white">Multi-GPU Overview</h2>
          <p className="text-sm text-gray-400">Individual GPU metrics and comparison</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {gpuMetrics.map((gpu, index) => (
          <motion.div
            key={gpu.gpu_id}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            className={`rounded-lg border ${getStatusColor(gpu)} backdrop-blur-sm overflow-hidden`}
          >
            {/* GPU Header */}
            <div
              className="p-4 cursor-pointer hover:bg-white/5 transition-colors"
              onClick={() => toggleExpand(gpu.gpu_id)}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-green-400" />
                  <span className="font-bold text-white">GPU {gpu.gpu_id}</span>
                </div>
                <button className="text-gray-400 hover:text-white transition-colors">
                  {expandedGPU === gpu.gpu_id ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                </button>
              </div>

              {/* Quick Stats */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">Utilization</span>
                  <span className="text-sm font-semibold text-green-400">{gpu.gpu_utilization_pct.toFixed(0)}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">Temperature</span>
                  <span
                    className={`text-sm font-semibold ${
                      gpu.temperature_c > 80 ? 'text-red-400' : gpu.temperature_c > 70 ? 'text-orange-400' : 'text-green-400'
                    }`}
                  >
                    {gpu.temperature_c.toFixed(0)}°C
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">Power</span>
                  <span className="text-sm font-semibold text-yellow-400">{gpu.power_usage_w.toFixed(0)}W</span>
                </div>
              </div>

              {/* Status Badges */}
              <div className="mt-3 flex flex-wrap gap-1">
                {gpu.thermal_throttle > 0 && (
                  <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs rounded-full border border-red-500/50">
                    Thermal
                  </span>
                )}
                {gpu.power_throttle > 0 && (
                  <span className="px-2 py-0.5 bg-orange-500/20 text-orange-400 text-xs rounded-full border border-orange-500/50">
                    Power
                  </span>
                )}
                <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded-full border border-blue-500/50">
                  P{gpu.performance_state}
                </span>
              </div>
            </div>

            {/* Expanded Details */}
            <AnimatePresence>
              {expandedGPU === gpu.gpu_id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="border-t border-white/10 bg-white/5"
                >
                  <div className="p-4 space-y-3">
                    {/* Memory */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <HardDrive className="w-4 h-4 text-blue-400" />
                        <span className="text-xs font-semibold text-white">Memory</span>
                      </div>
                      <div className="text-xs text-gray-400 space-y-1">
                        <div className="flex justify-between">
                          <span>Used</span>
                          <span className="text-white">{(gpu.memory_used_mib / 1024).toFixed(1)} GB</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Total</span>
                          <span className="text-white">{(gpu.memory_total_mib / 1024).toFixed(0)} GB</span>
                        </div>
                        <div className="w-full bg-white/10 rounded-full h-1.5 mt-2">
                          <div
                            className="bg-blue-500 h-full rounded-full"
                            style={{ width: `${(gpu.memory_used_mib / gpu.memory_total_mib) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Clocks */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Activity className="w-4 h-4 text-cyan-400" />
                        <span className="text-xs font-semibold text-white">Clocks</span>
                      </div>
                      <div className="text-xs text-gray-400 space-y-1">
                        <div className="flex justify-between">
                          <span>SM Clock</span>
                          <span className="text-white">{gpu.sm_clock_mhz} MHz</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Memory Clock</span>
                          <span className="text-white">{gpu.memory_clock_mhz} MHz</span>
                        </div>
                      </div>
                    </div>

                    {/* Compute */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Zap className="w-4 h-4 text-purple-400" />
                        <span className="text-xs font-semibold text-white">Compute</span>
                      </div>
                      <div className="text-xs text-gray-400 space-y-1">
                        <div className="flex justify-between">
                          <span>SM Active</span>
                          <span className="text-white">{gpu.sm_active_pct.toFixed(1)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Tensor Core</span>
                          <span className="text-white">{gpu.tensor_active_pct.toFixed(1)}%</span>
                        </div>
                      </div>
                    </div>

                    {/* Temperatures */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <Thermometer className="w-4 h-4 text-orange-400" />
                        <span className="text-xs font-semibold text-white">Temperatures</span>
                      </div>
                      <div className="text-xs text-gray-400 space-y-1">
                        <div className="flex justify-between">
                          <span>GPU</span>
                          <span className="text-white">{gpu.temperature_c.toFixed(0)}°C</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Memory</span>
                          <span className="text-white">{gpu.memory_temp_c.toFixed(0)}°C</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Hotspot</span>
                          <span className="text-white">{gpu.hotspot_temp_c.toFixed(0)}°C</span>
                        </div>
                      </div>
                    </div>

                    {/* ECC Errors */}
                    {(gpu.ecc_sbe_total > 0 || gpu.ecc_dbe_total > 0) && (
                      <div className="pt-3 border-t border-white/10">
                        <div className="text-xs font-semibold text-red-400 mb-1">ECC Errors</div>
                        <div className="text-xs text-gray-400 space-y-1">
                          {gpu.ecc_sbe_total > 0 && (
                            <div className="flex justify-between">
                              <span>Single-bit</span>
                              <span className="text-yellow-400">{gpu.ecc_sbe_total}</span>
                            </div>
                          )}
                          {gpu.ecc_dbe_total > 0 && (
                            <div className="flex justify-between">
                              <span>Double-bit</span>
                              <span className="text-red-400">{gpu.ecc_dbe_total}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};
