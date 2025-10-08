/**
 * GPU Health and Throttling Monitor Component
 *
 * Displays throttling status, ECC errors, fan speed, and health indicators
 */

import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Fan, ShieldAlert, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { GPUMetrics } from '../types';

interface HealthMonitorProps {
  gpuMetrics: GPUMetrics[];
  loading?: boolean;
}

export const HealthMonitor: React.FC<HealthMonitorProps> = ({ gpuMetrics, loading }) => {
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

  // Calculate health metrics
  const thermalThrottleCount = gpuMetrics.filter((gpu) => gpu.thermal_throttle > 0).length;
  const powerThrottleCount = gpuMetrics.filter((gpu) => gpu.power_throttle > 0).length;
  const totalEccSbe = gpuMetrics.reduce((sum, gpu) => sum + gpu.ecc_sbe_total, 0);
  const totalEccDbe = gpuMetrics.reduce((sum, gpu) => sum + gpu.ecc_dbe_total, 0);
  const avgFanSpeed = gpuMetrics.reduce((sum, gpu) => sum + gpu.fan_speed_pct, 0) / gpuMetrics.length;

  const hasThrottling = thermalThrottleCount > 0 || powerThrottleCount > 0;
  const hasEccErrors = totalEccDbe > 0;
  const hasWarnings = totalEccSbe > 100 || avgFanSpeed > 85;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-lg p-6"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-blue-500/20 rounded-lg">
          <ShieldAlert className="w-6 h-6 text-blue-400" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Health & Throttling</h2>
          <p className="text-sm text-gray-400">GPU health status and thermal management</p>
        </div>
      </div>

      {/* Overall Health Status */}
      <div className="mb-6 p-4 rounded-lg border border-white/10 bg-white/5">
        <div className="flex items-center gap-3">
          {!hasThrottling && !hasEccErrors && !hasWarnings ? (
            <>
              <CheckCircle className="w-6 h-6 text-green-400" />
              <div>
                <div className="text-sm font-semibold text-green-400">All Systems Normal</div>
                <div className="text-xs text-gray-400">No throttling or critical errors detected</div>
              </div>
            </>
          ) : hasEccErrors ? (
            <>
              <AlertCircle className="w-6 h-6 text-red-400 animate-pulse" />
              <div>
                <div className="text-sm font-semibold text-red-400">Critical: ECC Errors Detected</div>
                <div className="text-xs text-gray-400">{totalEccDbe} uncorrectable errors</div>
              </div>
            </>
          ) : hasThrottling ? (
            <>
              <AlertTriangle className="w-6 h-6 text-orange-400 animate-pulse" />
              <div>
                <div className="text-sm font-semibold text-orange-400">Warning: Throttling Active</div>
                <div className="text-xs text-gray-400">
                  {thermalThrottleCount > 0 && `${thermalThrottleCount} GPU(s) thermal throttling`}
                  {powerThrottleCount > 0 && ` | ${powerThrottleCount} GPU(s) power throttling`}
                </div>
              </div>
            </>
          ) : (
            <>
              <AlertTriangle className="w-6 h-6 text-yellow-400" />
              <div>
                <div className="text-sm font-semibold text-yellow-400">Advisory: Minor Issues</div>
                <div className="text-xs text-gray-400">Check metrics below</div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Throttling Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Thermal Throttle */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`p-4 rounded-lg border ${
            thermalThrottleCount > 0
              ? 'bg-red-500/10 border-red-500/50'
              : 'bg-white/5 border-white/10'
          }`}
        >
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle
              className={`w-5 h-5 ${thermalThrottleCount > 0 ? 'text-red-400 animate-pulse' : 'text-gray-400'}`}
            />
            <span className="text-sm font-semibold text-white">Thermal Throttle</span>
          </div>
          <div className="text-2xl font-bold">
            <span className={thermalThrottleCount > 0 ? 'text-red-400' : 'text-green-400'}>
              {thermalThrottleCount > 0 ? 'ACTIVE' : 'Normal'}
            </span>
          </div>
          {thermalThrottleCount > 0 && (
            <p className="text-xs text-red-400 mt-1">{thermalThrottleCount} GPU(s) affected</p>
          )}
        </motion.div>

        {/* Power Throttle */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className={`p-4 rounded-lg border ${
            powerThrottleCount > 0
              ? 'bg-orange-500/10 border-orange-500/50'
              : 'bg-white/5 border-white/10'
          }`}
        >
          <div className="flex items-center gap-3 mb-2">
            <AlertTriangle
              className={`w-5 h-5 ${powerThrottleCount > 0 ? 'text-orange-400 animate-pulse' : 'text-gray-400'}`}
            />
            <span className="text-sm font-semibold text-white">Power Throttle</span>
          </div>
          <div className="text-2xl font-bold">
            <span className={powerThrottleCount > 0 ? 'text-orange-400' : 'text-green-400'}>
              {powerThrottleCount > 0 ? 'ACTIVE' : 'Normal'}
            </span>
          </div>
          {powerThrottleCount > 0 && (
            <p className="text-xs text-orange-400 mt-1">{powerThrottleCount} GPU(s) affected</p>
          )}
        </motion.div>
      </div>

      {/* ECC Errors and Fan Speed */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* ECC Errors */}
        <div className="p-4 rounded-lg border border-white/10 bg-white/5">
          <div className="flex items-center gap-3 mb-3">
            <ShieldAlert className="w-5 h-5 text-purple-400" />
            <span className="text-sm font-semibold text-white">ECC Errors</span>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-400">Single-bit (correctable)</span>
              <span
                className={`text-sm font-semibold ${totalEccSbe > 100 ? 'text-yellow-400' : 'text-green-400'}`}
              >
                {totalEccSbe}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-400">Double-bit (uncorrectable)</span>
              <span className={`text-sm font-semibold ${totalEccDbe > 0 ? 'text-red-400' : 'text-green-400'}`}>
                {totalEccDbe}
              </span>
            </div>
          </div>
        </div>

        {/* Fan Speed */}
        <div className="p-4 rounded-lg border border-white/10 bg-white/5">
          <div className="flex items-center gap-3 mb-3">
            <Fan className={`w-5 h-5 text-cyan-400 ${avgFanSpeed > 70 ? 'animate-spin' : ''}`} />
            <span className="text-sm font-semibold text-white">Fan Speed</span>
          </div>
          <div className="flex items-baseline gap-2 mb-2">
            <span className={`text-2xl font-bold ${avgFanSpeed > 85 ? 'text-red-400' : 'text-cyan-400'}`}>
              {avgFanSpeed.toFixed(0)}
            </span>
            <span className="text-sm text-gray-400">%</span>
          </div>
          <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${avgFanSpeed}%` }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
              className={`h-full rounded-full ${
                avgFanSpeed > 85 ? 'bg-red-500' : avgFanSpeed > 70 ? 'bg-yellow-500' : 'bg-cyan-500'
              }`}
            />
          </div>
        </div>
      </div>
    </motion.div>
  );
};
