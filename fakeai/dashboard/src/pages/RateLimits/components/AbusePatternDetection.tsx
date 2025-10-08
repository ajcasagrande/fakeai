/**
 * Abuse Pattern Detection Component
 * Displays detected abuse patterns and suspicious activity
 */

import React from 'react';
import { motion } from 'framer-motion';
import { AbusePattern } from '../types';

interface AbusePatternDetectionProps {
  patterns: AbusePattern[];
  loading?: boolean;
}

export const AbusePatternDetection: React.FC<AbusePatternDetectionProps> = ({
  patterns,
  loading = false,
}) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return {
          bg: 'bg-red-500/10',
          border: 'border-red-500/30',
          text: 'text-red-400',
          badge: 'bg-red-500/20 text-red-300',
        };
      case 'high':
        return {
          bg: 'bg-orange-500/10',
          border: 'border-orange-500/30',
          text: 'text-orange-400',
          badge: 'bg-orange-500/20 text-orange-300',
        };
      case 'medium':
        return {
          bg: 'bg-yellow-500/10',
          border: 'border-yellow-500/30',
          text: 'text-yellow-400',
          badge: 'bg-yellow-500/20 text-yellow-300',
        };
      case 'low':
        return {
          bg: 'bg-blue-500/10',
          border: 'border-blue-500/30',
          text: 'text-blue-400',
          badge: 'bg-blue-500/20 text-blue-300',
        };
      default:
        return {
          bg: 'bg-gray-500/10',
          border: 'border-gray-500/30',
          text: 'text-gray-400',
          badge: 'bg-gray-500/20 text-gray-300',
        };
    }
  };

  const getPatternIcon = (patternType: string) => {
    switch (patternType) {
      case 'burst':
        return '💥';
      case 'sustained':
        return '📈';
      case 'distributed':
        return '🌐';
      case 'suspicious':
        return '🔍';
      default:
        return '⚠️';
    }
  };

  const getPatternLabel = (patternType: string) => {
    switch (patternType) {
      case 'burst':
        return 'Burst Attack';
      case 'sustained':
        return 'Sustained High Usage';
      case 'distributed':
        return 'Distributed Pattern';
      case 'suspicious':
        return 'Suspicious Activity';
      default:
        return 'Unknown Pattern';
    }
  };

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = Date.now();
    const diff = now - timestamp;

    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
        <div className="h-6 bg-gray-700 rounded w-1/3 mb-4 animate-pulse"></div>
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-32 bg-gray-700/50 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  const sortedPatterns = [...patterns].sort((a, b) => {
    const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
    return (
      severityOrder[b.severity] - severityOrder[a.severity] ||
      b.detected_at - a.detected_at
    );
  });

  return (
    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-white mb-1">
            Abuse Pattern Detection
          </h3>
          <p className="text-gray-400 text-sm">
            Automated detection of suspicious usage patterns
          </p>
        </div>
        <div className="flex items-center gap-2">
          {patterns.length > 0 && (
            <span className="px-3 py-1 bg-red-500/20 text-red-400 rounded-full text-sm font-semibold">
              {patterns.length} Active
            </span>
          )}
          <div className="text-2xl">🛡️</div>
        </div>
      </div>

      <div className="space-y-4">
        {sortedPatterns.map((pattern, index) => {
          const colors = getSeverityColor(pattern.severity);

          return (
            <motion.div
              key={`${pattern.api_key}-${pattern.detected_at}`}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
              className={`
                ${colors.bg} ${colors.border}
                border-2 rounded-lg p-5
                backdrop-blur-sm
                hover:scale-102 transition-all duration-300
                ${pattern.severity === 'critical' ? 'ring-2 ring-red-500/30 animate-pulse-slow' : ''}
              `}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="text-3xl">{getPatternIcon(pattern.pattern_type)}</div>
                  <div>
                    <h4 className={`${colors.text} font-bold text-lg mb-1`}>
                      {getPatternLabel(pattern.pattern_type)}
                    </h4>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400 text-sm font-mono">
                        {pattern.api_key_name || pattern.api_key.substring(0, 20) + '...'}
                      </span>
                      <span className="text-gray-600">•</span>
                      <span className="text-gray-500 text-xs">
                        {formatTimestamp(pattern.detected_at)}
                      </span>
                    </div>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-bold ${colors.badge}`}>
                  {pattern.severity.toUpperCase()}
                </span>
              </div>

              <p className="text-gray-300 text-sm mb-4">{pattern.description}</p>

              {/* Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
                <div className="bg-gray-900/30 rounded-lg p-3">
                  <div className="text-gray-400 text-xs mb-1">Requests/sec</div>
                  <div className={`${colors.text} font-bold text-lg`}>
                    {pattern.metrics.requests_per_second.toFixed(2)}
                  </div>
                </div>

                <div className="bg-gray-900/30 rounded-lg p-3">
                  <div className="text-gray-400 text-xs mb-1">Unique Endpoints</div>
                  <div className={`${colors.text} font-bold text-lg`}>
                    {pattern.metrics.unique_endpoints}
                  </div>
                </div>

                <div className="bg-gray-900/30 rounded-lg p-3">
                  <div className="text-gray-400 text-xs mb-1">Error Rate</div>
                  <div className={`${colors.text} font-bold text-lg`}>
                    {pattern.metrics.error_rate.toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* Geographic Distribution */}
              {pattern.metrics.geographic_distribution && pattern.metrics.geographic_distribution.length > 0 && (
                <div className="mb-4">
                  <div className="text-gray-400 text-xs mb-2">Geographic Distribution</div>
                  <div className="flex flex-wrap gap-2">
                    {pattern.metrics.geographic_distribution.map((location) => (
                      <span
                        key={location}
                        className="px-2 py-1 bg-gray-900/50 text-gray-300 rounded text-xs"
                      >
                        {location}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Action */}
              <div className="pt-4 border-t border-gray-700/50">
                <div className="flex items-start gap-2">
                  <div className="text-yellow-400 mt-0.5">💡</div>
                  <div>
                    <div className="text-gray-400 text-xs mb-1">
                      Recommended Action
                    </div>
                    <div className="text-white text-sm font-medium">
                      {pattern.recommended_action}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {patterns.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">✅</div>
          <div className="text-nvidia-green font-semibold mb-2">
            No Abuse Patterns Detected
          </div>
          <div className="text-gray-500 text-sm">
            All API keys are operating within normal parameters
          </div>
        </div>
      )}
    </div>
  );
};
