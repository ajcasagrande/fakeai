/**
 * Cache Warmup Status Component
 * Displays cache warmup progress and status
 */

import React from 'react';
import { CacheWarmupStatus } from '../types';

interface WarmupStatusProps {
  warmupStatus: CacheWarmupStatus;
  onTriggerWarmup?: () => void;
  loading?: boolean;
}

export const WarmupStatus: React.FC<WarmupStatusProps> = ({
  warmupStatus,
  onTriggerWarmup,
  loading,
}) => {
  if (loading) {
    return (
      <div className="warmup-status-container">
        <div className="skeleton-card"></div>
      </div>
    );
  }

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'hot':
        return '#76b900';
      case 'warm':
        return '#00bfff';
      case 'warming':
        return '#ff9900';
      default:
        return '#999';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'hot':
        return (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.879 16.121A3 3 0 1012.015 11L11 14H9c0 .768.293 1.536.879 2.121z"
            />
          </svg>
        );
      case 'warm':
        return (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"
            />
          </svg>
        );
      case 'warming':
        return (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="warming-icon">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
        );
      default:
        return (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        );
    }
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(2)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(2)}K`;
    }
    return num.toFixed(0);
  };

  const formatTime = (ms: number): string => {
    if (ms >= 60000) {
      return `${(ms / 60000).toFixed(2)} min`;
    }
    if (ms >= 1000) {
      return `${(ms / 1000).toFixed(2)} s`;
    }
    return `${ms.toFixed(0)} ms`;
  };

  const formatTimestamp = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  return (
    <div className="warmup-status">
      <div className="card-header">
        <h3 className="card-title">Cache Warmup Status</h3>
        {onTriggerWarmup && (
          <button
            className="warmup-trigger-btn"
            onClick={onTriggerWarmup}
            disabled={warmupStatus.status === 'warming'}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            {warmupStatus.status === 'warming' ? 'Warming...' : 'Trigger Warmup'}
          </button>
        )}
      </div>

      <div className="warmup-content">
        <div className="status-indicator" style={{ borderColor: getStatusColor(warmupStatus.status) }}>
          <div className="status-icon" style={{ color: getStatusColor(warmupStatus.status) }}>
            {getStatusIcon(warmupStatus.status)}
          </div>
          <div className="status-info">
            <div className="status-label">Current Status</div>
            <div className="status-value" style={{ color: getStatusColor(warmupStatus.status) }}>
              {warmupStatus.status.toUpperCase()}
            </div>
          </div>
        </div>

        <div className="progress-section">
          <div className="progress-header">
            <span className="progress-label">Warmup Progress</span>
            <span className="progress-percentage">
              {warmupStatus.warmup_progress_percent.toFixed(1)}%
            </span>
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{
                width: `${warmupStatus.warmup_progress_percent}%`,
                backgroundColor: getStatusColor(warmupStatus.status),
              }}
            >
              <div className="progress-shine"></div>
            </div>
          </div>
          <div className="progress-details">
            <span className="progress-detail">
              {formatNumber(warmupStatus.entries_loaded)} / {formatNumber(warmupStatus.total_entries)} entries loaded
            </span>
          </div>
        </div>

        <div className="warmup-stats">
          <div className="stat-row">
            <div className="stat-item">
              <div className="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div className="stat-content">
                <div className="stat-label">Warmup Time</div>
                <div className="stat-value">{formatTime(warmupStatus.warmup_time_ms)}</div>
              </div>
            </div>

            <div className="stat-item">
              <div className="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <div className="stat-content">
                <div className="stat-label">Last Warmup</div>
                <div className="stat-value timestamp">
                  {warmupStatus.last_warmup_timestamp
                    ? formatTimestamp(warmupStatus.last_warmup_timestamp)
                    : 'Never'}
                </div>
              </div>
            </div>
          </div>

          <div className="stat-row">
            <div className="stat-item">
              <div className="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <div className="stat-content">
                <div className="stat-label">Entries Loaded</div>
                <div className="stat-value">{formatNumber(warmupStatus.entries_loaded)}</div>
              </div>
            </div>

            <div className="stat-item">
              <div className="stat-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  />
                </svg>
              </div>
              <div className="stat-content">
                <div className="stat-label">Total Entries</div>
                <div className="stat-value">{formatNumber(warmupStatus.total_entries)}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="warmup-info">
          <div className="info-section">
            <h4 className="info-title">What is Cache Warmup?</h4>
            <p className="info-text">
              Cache warmup preloads frequently accessed data into the cache to improve initial
              response times and hit rates. A "hot" cache provides optimal performance.
            </p>
          </div>

          <div className="status-meanings">
            <div className="meaning-item">
              <span className="meaning-badge cold">COLD</span>
              <span className="meaning-text">Cache is empty or minimally populated</span>
            </div>
            <div className="meaning-item">
              <span className="meaning-badge warming">WARMING</span>
              <span className="meaning-text">Cache is actively being preloaded</span>
            </div>
            <div className="meaning-item">
              <span className="meaning-badge warm">WARM</span>
              <span className="meaning-text">Cache is partially populated and improving</span>
            </div>
            <div className="meaning-item">
              <span className="meaning-badge hot">HOT</span>
              <span className="meaning-text">Cache is fully optimized for peak performance</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
