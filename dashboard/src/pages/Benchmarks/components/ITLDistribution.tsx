/**
 * Inter Token Latency Distribution Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Timer } from 'lucide-react';
import { BenchmarkMetric } from '../types';

interface ITLDistributionProps {
  itl: BenchmarkMetric;
  loading?: boolean;
}

export const ITLDistribution: React.FC<ITLDistributionProps> = ({ itl, loading }) => {
  if (loading) {
    return (
      <div className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl animate-pulse">
        <div className="h-64"></div>
      </div>
    );
  }

  const getColorForValue = (value: number, max: number) => {
    const ratio = value / max;
    if (ratio < 0.3) return 'from-green-600 to-green-400';
    if (ratio < 0.6) return 'from-blue-600 to-blue-400';
    if (ratio < 0.8) return 'from-yellow-600 to-yellow-400';
    return 'from-red-600 to-red-400';
  };

  const dataPoints = [
    { label: 'P1', value: itl.p1 || 0 },
    { label: 'P25', value: itl.p25 || 0 },
    { label: 'P50', value: itl.p50 || 0 },
    { label: 'P75', value: itl.p75 || 0 },
    { label: 'P90', value: itl.p90 || 0 },
    { label: 'P95', value: itl.p95 || 0 },
    { label: 'P99', value: itl.p99 || 0 },
  ];

  const maxValue = Math.max(...dataPoints.map((d) => d.value));

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:border-blue-500/50 transition-all"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-blue-500/10 rounded-lg">
          <Timer className="w-5 h-5 text-blue-500" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-white">Inter Token Latency (ITL)</h3>
          <p className="text-xs text-gray-400">Token Generation Speed Distribution</p>
        </div>
      </div>

      {/* Visual representation */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm text-gray-400">Distribution</span>
          <span className="text-sm text-gray-400">0ms → {maxValue.toFixed(2)}ms</span>
        </div>

        {/* Gradient bar showing distribution */}
        <div className="relative h-16 bg-white/5 rounded-lg overflow-hidden mb-4">
          <div className="absolute inset-0 bg-gradient-to-r from-green-500 via-blue-500 via-yellow-500 to-red-500 opacity-30"></div>
          {dataPoints.map((point, index) => {
            const position = (point.value / maxValue) * 100;
            return (
              <motion.div
                key={point.label}
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                className="absolute top-1/2 -translate-y-1/2"
                style={{ left: `${position}%` }}
              >
                <div className="relative group">
                  <div className="w-3 h-3 bg-white rounded-full shadow-lg border-2 border-blue-500 group-hover:scale-150 transition-transform cursor-pointer"></div>
                  <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="bg-black/90 text-white text-xs py-1 px-2 rounded whitespace-nowrap">
                      {point.label}: {point.value.toFixed(2)}ms
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Detailed breakdown */}
        <div className="grid grid-cols-2 gap-3">
          {dataPoints.map((point, index) => (
            <motion.div
              key={point.label}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="flex items-center justify-between p-3 bg-white/5 rounded-lg hover:bg-white/10 transition-all group"
            >
              <span className="text-sm text-gray-400 group-hover:text-white transition-colors">
                {point.label}
              </span>
              <div className="flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full bg-gradient-to-r ${getColorForValue(
                    point.value,
                    maxValue
                  )}`}
                ></div>
                <span className="text-sm font-semibold text-white">
                  {point.value.toFixed(2)}ms
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-white/5">
        <div className="text-center">
          <div className="text-xs text-gray-500 mb-1">Average</div>
          <div className="text-lg font-bold text-blue-400">{itl.avg.toFixed(2)}ms</div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 mb-1">Median</div>
          <div className="text-lg font-bold text-green-400">
            {itl.p50?.toFixed(2) || 'N/A'}ms
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-gray-500 mb-1">Std Dev</div>
          <div className="text-lg font-bold text-purple-400">
            {itl.std?.toFixed(2) || 'N/A'}ms
          </div>
        </div>
      </div>
    </motion.div>
  );
};
