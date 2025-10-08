/**
 * Connection status indicator component with NVIDIA theme
 * Shows real-time WebSocket connection status
 */

import React, { useState, useEffect } from 'react';
import { ConnectionState } from '../types';
import { useConnectionStatus } from '../hooks';

/**
 * Component props
 */
interface ConnectionStatusProps {
  className?: string;
  showDetails?: boolean;
  showLatency?: boolean;
  compact?: boolean;
  position?: 'inline' | 'fixed';
}

/**
 * Connection status indicator component
 */
export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  className = '',
  showDetails = true,
  showLatency = true,
  compact = false,
  position = 'inline',
}) => {
  const { state, isConnected, reconnectAttempts, latency } = useConnectionStatus();
  const [isExpanded, setIsExpanded] = useState(!compact);

  // Auto-collapse after successful connection in compact mode
  useEffect(() => {
    if (compact && isConnected && reconnectAttempts === 0) {
      const timer = setTimeout(() => setIsExpanded(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [compact, isConnected, reconnectAttempts]);

  // Get status info based on connection state
  const getStatusInfo = () => {
    switch (state) {
      case ConnectionState.CONNECTED:
        return {
          color: 'bg-green-500',
          borderColor: 'border-green-500',
          textColor: 'text-green-500',
          bgColor: 'bg-green-500/10',
          label: 'Connected',
          icon: '●',
          pulse: false,
        };
      case ConnectionState.CONNECTING:
        return {
          color: 'bg-yellow-500',
          borderColor: 'border-yellow-500',
          textColor: 'text-yellow-500',
          bgColor: 'bg-yellow-500/10',
          label: 'Connecting',
          icon: '◐',
          pulse: true,
        };
      case ConnectionState.RECONNECTING:
        return {
          color: 'bg-orange-500',
          borderColor: 'border-orange-500',
          textColor: 'text-orange-500',
          bgColor: 'bg-orange-500/10',
          label: `Reconnecting (${reconnectAttempts})`,
          icon: '◐',
          pulse: true,
        };
      case ConnectionState.DISCONNECTED:
        return {
          color: 'bg-gray-500',
          borderColor: 'border-gray-500',
          textColor: 'text-gray-500',
          bgColor: 'bg-gray-500/10',
          label: 'Disconnected',
          icon: '○',
          pulse: false,
        };
      case ConnectionState.ERROR:
        return {
          color: 'bg-red-500',
          borderColor: 'border-red-500',
          textColor: 'text-red-500',
          bgColor: 'bg-red-500/10',
          label: 'Error',
          icon: '✕',
          pulse: false,
        };
      default:
        return {
          color: 'bg-gray-500',
          borderColor: 'border-gray-500',
          textColor: 'text-gray-500',
          bgColor: 'bg-gray-500/10',
          label: 'Unknown',
          icon: '?',
          pulse: false,
        };
    }
  };

  const statusInfo = getStatusInfo();

  // Format latency
  const formatLatency = (ms: number | null): string => {
    if (ms === null) return 'N/A';
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  // Compact view
  if (compact && !isExpanded) {
    return (
      <button
        className={`
          inline-flex items-center gap-2 px-3 py-1.5 rounded-lg
          ${statusInfo.bgColor} ${statusInfo.borderColor} border
          transition-all duration-200 hover:scale-105
          ${className}
        `}
        onClick={() => setIsExpanded(true)}
        title={`Connection status: ${statusInfo.label}`}
      >
        <span
          className={`
            w-2 h-2 rounded-full ${statusInfo.color}
            ${statusInfo.pulse ? 'animate-pulse' : ''}
          `}
        />
        {showLatency && isConnected && latency !== null && (
          <span className="text-xs text-gray-400">{formatLatency(latency)}</span>
        )}
      </button>
    );
  }

  // Full view
  const containerClass =
    position === 'fixed'
      ? 'fixed top-4 right-4 z-50'
      : 'inline-flex';

  return (
    <div
      className={`
        ${containerClass}
        items-center gap-3 px-4 py-2.5 rounded-lg
        ${statusInfo.bgColor} ${statusInfo.borderColor} border
        backdrop-blur-sm shadow-lg
        transition-all duration-200
        ${className}
      `}
    >
      {/* Status Indicator */}
      <div className="flex items-center gap-2">
        <div className="relative">
          <span
            className={`
              inline-block w-3 h-3 rounded-full ${statusInfo.color}
              ${statusInfo.pulse ? 'animate-pulse' : ''}
            `}
          />
          {statusInfo.pulse && (
            <span
              className={`
                absolute inset-0 w-3 h-3 rounded-full ${statusInfo.color}
                animate-ping opacity-75
              `}
            />
          )}
        </div>

        <span className={`text-sm font-medium ${statusInfo.textColor}`}>
          {statusInfo.label}
        </span>
      </div>

      {/* Details */}
      {showDetails && (
        <div className="flex items-center gap-4 text-xs text-gray-400 border-l border-gray-700 pl-3">
          {/* Latency */}
          {showLatency && isConnected && (
            <div className="flex items-center gap-1.5">
              <svg
                className="w-3 h-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
              <span className={latency && latency < 100 ? 'text-green-400' : ''}>
                {formatLatency(latency)}
              </span>
            </div>
          )}

          {/* Reconnect Attempts */}
          {reconnectAttempts > 0 && (
            <div className="flex items-center gap-1.5">
              <svg
                className="w-3 h-3 animate-spin"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              <span>Attempt {reconnectAttempts}</span>
            </div>
          )}
        </div>
      )}

      {/* Collapse button for compact mode */}
      {compact && (
        <button
          onClick={() => setIsExpanded(false)}
          className="ml-2 text-gray-400 hover:text-gray-300 transition-colors"
          title="Collapse"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      )}
    </div>
  );
};

/**
 * Detailed connection stats component
 */
interface ConnectionStatsProps {
  className?: string;
}

export const ConnectionStats: React.FC<ConnectionStatsProps> = ({ className = '' }) => {
  const { state, isConnected, reconnectAttempts, latency } = useConnectionStatus();

  const stats = [
    {
      label: 'Status',
      value: state,
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      ),
    },
    {
      label: 'Latency',
      value: latency !== null ? `${latency}ms` : 'N/A',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M13 10V3L4 14h7v7l9-11h-7z"
          />
        </svg>
      ),
    },
    {
      label: 'Reconnects',
      value: reconnectAttempts,
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>
      ),
    },
  ];

  return (
    <div className={`grid grid-cols-3 gap-4 ${className}`}>
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="bg-gray-800/50 border border-gray-700 rounded-lg p-4"
        >
          <div className="flex items-center gap-2 text-gray-400 text-xs mb-2">
            {stat.icon}
            <span>{stat.label}</span>
          </div>
          <div className="text-lg font-bold text-white">{stat.value}</div>
        </div>
      ))}
    </div>
  );
};

/**
 * Connection status badge (minimal version)
 */
interface ConnectionBadgeProps {
  className?: string;
}

export const ConnectionBadge: React.FC<ConnectionBadgeProps> = ({ className = '' }) => {
  const { state, isConnected } = useConnectionStatus();

  const getColor = () => {
    if (isConnected) return 'bg-green-500';
    if (state === ConnectionState.CONNECTING || state === ConnectionState.RECONNECTING) {
      return 'bg-yellow-500 animate-pulse';
    }
    if (state === ConnectionState.ERROR) return 'bg-red-500';
    return 'bg-gray-500';
  };

  return (
    <div
      className={`w-2 h-2 rounded-full ${getColor()} ${className}`}
      title={`Connection: ${state}`}
    />
  );
};

export default ConnectionStatus;
