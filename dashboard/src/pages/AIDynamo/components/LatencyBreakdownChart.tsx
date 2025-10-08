/**
 * Latency Breakdown Chart Component
 *
 * Visualizes the breakdown of latency phases: Queue, Prefill, Decode
 */

import React from 'react';
import { motion } from 'framer-motion';
import { BarChart3 } from 'lucide-react';
import { LatencyBreakdownData } from '../types';

interface LatencyBreakdownChartProps {
  latencyData: LatencyBreakdownData[];
  loading?: boolean;
}

export const LatencyBreakdownChart: React.FC<LatencyBreakdownChartProps> = ({ latencyData, loading }) => {
  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
      >
        <div className="animate-pulse h-64"></div>
      </motion.div>
    );
  }

  if (!latencyData || latencyData.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
      >
        <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Latency Breakdown
        </h3>
        <div className="text-center py-8 text-gray-400">No latency data available</div>
      </motion.div>
    );
  }

  // Calculate averages
  const avgQueue = latencyData.reduce((sum, d) => sum + (d.queue_time_ms || 0), 0) / latencyData.length;
  const avgPrefill = latencyData.reduce((sum, d) => sum + (d.prefill_time_ms || 0), 0) / latencyData.length;
  const avgDecode = latencyData.reduce((sum, d) => sum + (d.decode_time_ms || 0), 0) / latencyData.length;
  const avgTotal = avgQueue + avgPrefill + avgDecode;

  const queuePct = avgTotal > 0 ? (avgQueue / avgTotal) * 100 : 0;
  const prefillPct = avgTotal > 0 ? (avgPrefill / avgTotal) * 100 : 0;
  const decodePct = avgTotal > 0 ? (avgDecode / avgTotal) * 100 : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.01 }}
      className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:border-green-500/50 transition-all"
    >
      <div className="mb-6">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-purple-500" />
          Latency Breakdown
        </h3>
        <p className="text-sm text-gray-400 mt-1">Average request latency across phases</p>
      </div>

      {/* Visual Bar */}
      <div className="mb-6">
        <div className="h-16 flex rounded-lg overflow-hidden bg-gray-900">
          {queuePct > 0 && (
            <div
              className="bg-orange-500 flex items-center justify-center text-white font-semibold text-sm transition-all hover:brightness-110"
              style={{ width: `${queuePct}%` }}
            >
              {queuePct > 10 && 'Queue'}
            </div>
          )}
          {prefillPct > 0 && (
            <div
              className="bg-blue-500 flex items-center justify-center text-white font-semibold text-sm transition-all hover:brightness-110"
              style={{ width: `${prefillPct}%` }}
            >
              {prefillPct > 10 && 'Prefill'}
            </div>
          )}
          {decodePct > 0 && (
            <div
              className="bg-green-500 flex items-center justify-center text-white font-semibold text-sm transition-all hover:brightness-110"
              style={{ width: `${decodePct}%` }}
            >
              {decodePct > 10 && 'Decode'}
            </div>
          )}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-white/5 rounded-lg border-l-4 border-orange-500">
          <div className="text-xs text-gray-400 uppercase mb-1">Queue Time</div>
          <div className="text-xl font-bold text-white">{avgQueue.toFixed(1)}ms</div>
          <div className="text-xs text-gray-500">{queuePct.toFixed(1)}%</div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border-l-4 border-blue-500">
          <div className="text-xs text-gray-400 uppercase mb-1">Prefill Time</div>
          <div className="text-xl font-bold text-white">{avgPrefill.toFixed(1)}ms</div>
          <div className="text-xs text-gray-500">{prefillPct.toFixed(1)}%</div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border-l-4 border-green-500">
          <div className="text-xs text-gray-400 uppercase mb-1">Decode Time</div>
          <div className="text-xl font-bold text-white">{avgDecode.toFixed(1)}ms</div>
          <div className="text-xs text-gray-500">{decodePct.toFixed(1)}%</div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border-l-4 border-green-500">
          <div className="text-xs text-gray-400 uppercase mb-1">Total Time</div>
          <div className="text-xl font-bold text-green-500">{avgTotal.toFixed(1)}ms</div>
          <div className="text-xs text-gray-500">100%</div>
        </div>
      </div>

      <div className="mt-4 text-xs text-gray-500 text-center">
        Based on {latencyData.length} requests
      </div>
    </motion.div>
  );
};
