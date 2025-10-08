/**
 * Batch Status Badge Component
 * Displays color-coded status indicators with NVIDIA green theme
 */

import React from 'react';
import type { BatchStatus } from '../types/batch';

interface BatchStatusBadgeProps {
  status: BatchStatus;
  className?: string;
}

const statusConfig: Record<
  BatchStatus,
  { label: string; color: string; bgColor: string }
> = {
  validating: {
    label: 'Validating',
    color: 'text-blue-700',
    bgColor: 'bg-blue-100',
  },
  in_progress: {
    label: 'In Progress',
    color: 'text-green-700',
    bgColor: 'bg-green-100',
  },
  completed: {
    label: 'Completed',
    color: 'text-nvidia-green',
    bgColor: 'bg-nvidia-green/10',
  },
  failed: {
    label: 'Failed',
    color: 'text-red-700',
    bgColor: 'bg-red-100',
  },
  cancelled: {
    label: 'Cancelled',
    color: 'text-gray-700',
    bgColor: 'bg-gray-100',
  },
  cancelling: {
    label: 'Cancelling',
    color: 'text-yellow-700',
    bgColor: 'bg-yellow-100',
  },
};

export const BatchStatusBadge: React.FC<BatchStatusBadgeProps> = ({
  status,
  className = '',
}) => {
  const config = statusConfig[status];

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${config.color} ${config.bgColor} ${className}`}
    >
      <span className="w-2 h-2 mr-2 rounded-full bg-current animate-pulse" />
      {config.label}
    </span>
  );
};

export default BatchStatusBadge;
