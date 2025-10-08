/**
 * Batch Analytics Charts Component
 * Success/failure rate and processing time visualizations
 */

import React from 'react';
import type { Batch } from '../types/batch';

interface BatchChartsProps {
  batches: Batch[];
  className?: string;
}

export const BatchCharts: React.FC<BatchChartsProps> = ({
  batches,
  className = '',
}) => {
  // Calculate statistics
  const totalRequests = batches.reduce(
    (sum, b) => sum + b.request_counts.total,
    0
  );
  const completedRequests = batches.reduce(
    (sum, b) => sum + b.request_counts.completed,
    0
  );
  const failedRequests = batches.reduce(
    (sum, b) => sum + b.request_counts.failed,
    0
  );

  const successRate =
    totalRequests > 0 ? (completedRequests / totalRequests) * 100 : 0;
  const failureRate =
    totalRequests > 0 ? (failedRequests / totalRequests) * 100 : 0;

  // Calculate average processing times
  const completedBatches = batches.filter(
    b => b.status === 'completed' && b.completed_at && b.created_at
  );

  const processingTimes = completedBatches.map(b => ({
    id: b.id,
    time: (b.completed_at! - b.created_at) / 1000 / 60, // minutes
  }));

  const avgProcessingTime =
    processingTimes.length > 0
      ? processingTimes.reduce((sum, pt) => sum + pt.time, 0) /
        processingTimes.length
      : 0;

  // Status distribution
  const statusCounts = batches.reduce((acc, batch) => {
    acc[batch.status] = (acc[batch.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 gap-6 ${className}`}>
      {/* Success/Failure Rate Pie Chart */}
      <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          Success/Failure Rate
        </h3>
        <div className="flex items-center justify-center space-x-8">
          {/* Simple pie representation */}
          <div className="relative w-48 h-48">
            <svg viewBox="0 0 100 100" className="transform -rotate-90">
              {/* Success segment */}
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#76B900"
                strokeWidth="20"
                strokeDasharray={`${successRate * 2.51327} 251.327`}
                className="transition-all duration-1000"
              />
              {/* Failure segment */}
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#EF4444"
                strokeWidth="20"
                strokeDasharray={`${failureRate * 2.51327} 251.327`}
                strokeDashoffset={`-${successRate * 2.51327}`}
                className="transition-all duration-1000"
              />
              {/* Background */}
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#E5E7EB"
                strokeWidth="20"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="text-2xl font-bold text-nvidia-green">
                  {successRate.toFixed(1)}%
                </div>
                <div className="text-xs text-gray-500">Success</div>
              </div>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded bg-nvidia-green" />
              <div>
                <div className="text-sm font-medium text-gray-700">Success</div>
                <div className="text-xs text-gray-500">
                  {(completedRequests ?? 0).toLocaleString()} requests
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 rounded bg-red-500" />
              <div>
                <div className="text-sm font-medium text-gray-700">Failed</div>
                <div className="text-xs text-gray-500">
                  {(failedRequests ?? 0).toLocaleString()} requests
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Processing Time Analytics */}
      <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          Processing Time Analytics
        </h3>
        <div className="space-y-4">
          <div className="bg-nvidia-green/5 rounded-lg p-4 border border-nvidia-green/20">
            <div className="text-sm text-gray-600 mb-1">
              Average Processing Time
            </div>
            <div className="text-3xl font-bold text-nvidia-green">
              {avgProcessingTime.toFixed(1)} min
            </div>
          </div>
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700">
              Recent Batches
            </div>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {processingTimes.slice(-5).map((pt, idx) => (
                <div
                  key={pt.id}
                  className="flex justify-between text-xs text-gray-600 py-1"
                >
                  <span className="truncate">Batch {idx + 1}</span>
                  <span className="font-medium">{pt.time.toFixed(1)} min</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Status Distribution */}
      <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          Status Distribution
        </h3>
        <div className="space-y-3">
          {Object.entries(statusCounts).map(([status, count]) => {
            const percent = (count / batches.length) * 100;
            return (
              <div key={status}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="capitalize text-gray-700">{status}</span>
                  <span className="font-medium text-gray-900">
                    {count} ({percent.toFixed(0)}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-nvidia-green h-2 rounded-full transition-all duration-500"
                    style={{ width: `${percent}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Cost Overview */}
      <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          Cost Overview
        </h3>
        <div className="space-y-4">
          <div className="bg-gradient-to-br from-nvidia-green/10 to-nvidia-green/5 rounded-lg p-4 border border-nvidia-green/20">
            <div className="text-sm text-gray-600 mb-1">Total Cost</div>
            <div className="text-3xl font-bold text-nvidia-green">
              ${(totalRequests * 0.001).toFixed(2)}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 rounded p-3">
              <div className="text-xs text-gray-500">Total Requests</div>
              <div className="text-lg font-semibold text-gray-800">
                {(totalRequests ?? 0).toLocaleString()}
              </div>
            </div>
            <div className="bg-gray-50 rounded p-3">
              <div className="text-xs text-gray-500">Cost per Request</div>
              <div className="text-lg font-semibold text-gray-800">$0.001</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BatchCharts;
