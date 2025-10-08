/**
 * Batch Progress Bar Component
 * Visual progress indicator for batch processing
 */

import React from 'react';
import type { BatchRequestCounts, BatchStatus } from '../types/batch';

interface BatchProgressBarProps {
  requestCounts: BatchRequestCounts;
  status: BatchStatus;
  className?: string;
}

export const BatchProgressBar: React.FC<BatchProgressBarProps> = ({
  requestCounts,
  status,
  className = '',
}) => {
  const { total, completed, failed } = requestCounts;
  const completedPercent = total > 0 ? (completed / total) * 100 : 0;
  const failedPercent = total > 0 ? (failed / total) * 100 : 0;
  const progressPercent = completedPercent + failedPercent;

  const getProgressColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-nvidia-green';
      case 'failed':
        return 'bg-red-500';
      case 'cancelled':
        return 'bg-gray-400';
      case 'in_progress':
        return 'bg-nvidia-green';
      case 'validating':
        return 'bg-blue-500';
      default:
        return 'bg-nvidia-green';
    }
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex justify-between text-sm text-gray-600">
        <span>
          {completed + failed} / {total} requests processed
        </span>
        <span className="font-semibold">{progressPercent.toFixed(1)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div className="h-full flex">
          {/* Completed portion */}
          <div
            className={`${getProgressColor()} transition-all duration-500 ease-out`}
            style={{ width: `${completedPercent}%` }}
          />
          {/* Failed portion */}
          {failed > 0 && (
            <div
              className="bg-red-500 transition-all duration-500 ease-out"
              style={{ width: `${failedPercent}%` }}
            />
          )}
        </div>
      </div>
      <div className="flex justify-between text-xs text-gray-500">
        <span className="text-nvidia-green">
          {completed} completed ({completedPercent.toFixed(1)}%)
        </span>
        {failed > 0 && (
          <span className="text-red-500">
            {failed} failed ({failedPercent.toFixed(1)}%)
          </span>
        )}
      </div>
    </div>
  );
};

export default BatchProgressBar;
