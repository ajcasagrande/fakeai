/**
 * Rate Limit Breaches Timeline Component
 * Displays rate limit breach events over time
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RateLimitBreach } from '../types';

interface RateLimitBreachesTimelineProps {
  breaches: RateLimitBreach[];
  loading?: boolean;
}

export const RateLimitBreachesTimeline: React.FC<RateLimitBreachesTimelineProps> = ({
  breaches,
  loading = false,
}) => {
  const [filter, setFilter] = useState<'all' | 'rpm' | 'tpm' | 'rpd'>('all');
  const [expandedBreach, setExpandedBreach] = useState<string | null>(null);

  const filteredBreaches = React.useMemo(() => {
    if (filter === 'all') return breaches;
    return breaches.filter((b) => b.breach_type === filter);
  }, [breaches, filter]);

  const getBreachTypeColor = (type: string) => {
    switch (type) {
      case 'rpm':
        return {
          bg: 'bg-red-500/10',
          border: 'border-red-500/30',
          text: 'text-red-400',
          badge: 'bg-red-500/20 text-red-300',
          icon: '🔴',
        };
      case 'tpm':
        return {
          bg: 'bg-orange-500/10',
          border: 'border-orange-500/30',
          text: 'text-orange-400',
          badge: 'bg-orange-500/20 text-orange-300',
          icon: '🟠',
        };
      case 'rpd':
        return {
          bg: 'bg-yellow-500/10',
          border: 'border-yellow-500/30',
          text: 'text-yellow-400',
          badge: 'bg-yellow-500/20 text-yellow-300',
          icon: '🟡',
        };
      default:
        return {
          bg: 'bg-gray-500/10',
          border: 'border-gray-500/30',
          text: 'text-gray-400',
          badge: 'bg-gray-500/20 text-gray-300',
          icon: '⚪',
        };
    }
  };

  const formatTimestamp = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const formatDuration = (ms: number): string => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const groupByDate = (breaches: RateLimitBreach[]) => {
    const groups: Record<string, RateLimitBreach[]> = {};

    breaches.forEach((breach) => {
      const date = new Date(breach.timestamp).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });

      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(breach);
    });

    return groups;
  };

  const groupedBreaches = React.useMemo(() => {
    return groupByDate(filteredBreaches);
  }, [filteredBreaches]);

  if (loading) {
    return (
      <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
        <div className="h-6 bg-gray-700 rounded w-1/3 mb-4 animate-pulse"></div>
        <div className="space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-24 bg-gray-700/50 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-white mb-1">
            Rate Limit Breaches Timeline
          </h3>
          <p className="text-gray-400 text-sm">
            Chronological history of rate limit violations
          </p>
        </div>
        <div className="text-2xl">⏱️</div>
      </div>

      {/* Filter Controls */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            filter === 'all'
              ? 'bg-nvidia-green/20 text-nvidia-green border border-nvidia-green/30'
              : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700'
          }`}
        >
          All ({breaches.length})
        </button>
        <button
          onClick={() => setFilter('rpm')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            filter === 'rpm'
              ? 'bg-red-500/20 text-red-400 border border-red-500/30'
              : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700'
          }`}
        >
          RPM ({breaches.filter((b) => b.breach_type === 'rpm').length})
        </button>
        <button
          onClick={() => setFilter('tpm')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            filter === 'tpm'
              ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
              : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700'
          }`}
        >
          TPM ({breaches.filter((b) => b.breach_type === 'tpm').length})
        </button>
        <button
          onClick={() => setFilter('rpd')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            filter === 'rpd'
              ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
              : 'bg-gray-700/50 text-gray-400 hover:bg-gray-700'
          }`}
        >
          RPD ({breaches.filter((b) => b.breach_type === 'rpd').length})
        </button>
      </div>

      {/* Timeline */}
      <div className="space-y-6">
        {Object.entries(groupedBreaches).map(([date, dateBreaches]) => (
          <div key={date}>
            <div className="flex items-center gap-3 mb-4">
              <div className="text-nvidia-green font-semibold text-sm">{date}</div>
              <div className="flex-1 h-px bg-gray-700/50"></div>
              <span className="text-gray-500 text-xs">
                {dateBreaches.length} breach{dateBreaches.length !== 1 ? 'es' : ''}
              </span>
            </div>

            <div className="space-y-3 pl-4 border-l-2 border-gray-700/50">
              {dateBreaches.map((breach, index) => {
                const colors = getBreachTypeColor(breach.breach_type);
                const isExpanded = expandedBreach === breach.id;

                return (
                  <motion.div
                    key={breach.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.03 }}
                    className="relative"
                  >
                    {/* Timeline Dot */}
                    <div
                      className={`absolute -left-[21px] top-3 w-3 h-3 rounded-full ${
                        breach.resolved ? 'bg-nvidia-green' : 'bg-red-500'
                      } ring-4 ring-gray-800`}
                    ></div>

                    <div
                      onClick={() => setExpandedBreach(isExpanded ? null : breach.id)}
                      className={`
                        ${colors.bg} ${colors.border}
                        border rounded-lg p-4
                        cursor-pointer
                        hover:border-opacity-60 transition-all
                      `}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <div className="text-2xl">{colors.icon}</div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className={`${colors.text} font-bold text-sm`}>
                                {breach.breach_type.toUpperCase()} Breach
                              </span>
                              {breach.resolved && (
                                <span className="px-2 py-0.5 bg-nvidia-green/20 text-nvidia-green rounded-full text-xs font-semibold">
                                  RESOLVED
                                </span>
                              )}
                            </div>
                            <div className="text-gray-400 text-xs font-mono mt-1">
                              {breach.api_key_name || breach.api_key.substring(0, 20) + '...'}
                            </div>
                          </div>
                        </div>
                        <span className="text-gray-500 text-xs whitespace-nowrap">
                          {formatTimestamp(breach.timestamp)}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span className="text-gray-400">Limit:</span>
                          <span className="text-white font-semibold ml-2">
                            {breach.limit.toLocaleString()}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-400">Attempted:</span>
                          <span className={`${colors.text} font-semibold ml-2`}>
                            {breach.attempted_value.toLocaleString()}
                          </span>
                        </div>
                      </div>

                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.2 }}
                            className="mt-3 pt-3 border-t border-gray-700/50"
                          >
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span className="text-gray-400">Breach ID:</span>
                                <span className="text-white font-mono text-xs">{breach.id}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-400">Overage:</span>
                                <span className={`${colors.text} font-semibold`}>
                                  +{(breach.attempted_value - breach.limit).toLocaleString()}
                                </span>
                              </div>
                              {breach.duration_ms && (
                                <div className="flex justify-between">
                                  <span className="text-gray-400">Duration:</span>
                                  <span className="text-white font-semibold">
                                    {formatDuration(breach.duration_ms)}
                                  </span>
                                </div>
                              )}
                              <div className="flex justify-between">
                                <span className="text-gray-400">Percentage over limit:</span>
                                <span className={`${colors.text} font-semibold`}>
                                  {(((breach.attempted_value - breach.limit) / breach.limit) * 100).toFixed(1)}%
                                </span>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {filteredBreaches.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">✅</div>
          <div className="text-nvidia-green font-semibold mb-2">No Breaches Found</div>
          <div className="text-gray-500 text-sm">
            {filter === 'all'
              ? 'No rate limit breaches detected'
              : `No ${filter.toUpperCase()} breaches detected`}
          </div>
        </div>
      )}
    </div>
  );
};
