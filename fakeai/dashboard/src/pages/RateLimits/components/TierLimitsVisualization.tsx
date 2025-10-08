/**
 * Tier Limits Visualization Component
 * Displays rate limit tiers and their configurations
 */

import React from 'react';
import { motion } from 'framer-motion';
import { RateLimitTier } from '../types';

interface TierConfig {
  tier: RateLimitTier;
  name: string;
  rpm: number;
  tpm: number;
  rpd: number;
  color: string;
  description: string;
}

const TIER_CONFIGS: TierConfig[] = [
  {
    tier: 'free',
    name: 'Free',
    rpm: 3,
    tpm: 40000,
    rpd: 200,
    color: 'gray',
    description: 'Basic access for testing',
  },
  {
    tier: 'tier1',
    name: 'Tier 1',
    rpm: 10,
    tpm: 200000,
    rpd: 1000,
    color: 'blue',
    description: 'Low-volume production',
  },
  {
    tier: 'tier2',
    name: 'Tier 2',
    rpm: 50,
    tpm: 500000,
    rpd: 5000,
    color: 'green',
    description: 'Medium-volume production',
  },
  {
    tier: 'tier3',
    name: 'Tier 3',
    rpm: 200,
    tpm: 1000000,
    rpd: 10000,
    color: 'yellow',
    description: 'High-volume production',
  },
  {
    tier: 'tier4',
    name: 'Tier 4',
    rpm: 500,
    tpm: 2000000,
    rpd: 50000,
    color: 'orange',
    description: 'Enterprise',
  },
  {
    tier: 'tier5',
    name: 'Tier 5',
    rpm: 10000,
    tpm: 10000000,
    rpd: 100000,
    color: 'purple',
    description: 'Premium enterprise',
  },
];

interface TierLimitsVisualizationProps {
  currentTier?: RateLimitTier;
  highlightTier?: RateLimitTier;
}

export const TierLimitsVisualization: React.FC<TierLimitsVisualizationProps> = ({
  currentTier,
  highlightTier,
}) => {
  const colorClasses: Record<string, any> = {
    gray: {
      bg: 'bg-gray-500/10',
      border: 'border-gray-500/30',
      text: 'text-gray-400',
      badge: 'bg-gray-500/20 text-gray-300',
    },
    blue: {
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/30',
      text: 'text-blue-400',
      badge: 'bg-blue-500/20 text-blue-300',
    },
    green: {
      bg: 'bg-nvidia-green/10',
      border: 'border-nvidia-green/30',
      text: 'text-nvidia-green',
      badge: 'bg-nvidia-green/20 text-nvidia-green',
    },
    yellow: {
      bg: 'bg-yellow-500/10',
      border: 'border-yellow-500/30',
      text: 'text-yellow-400',
      badge: 'bg-yellow-500/20 text-yellow-300',
    },
    orange: {
      bg: 'bg-orange-500/10',
      border: 'border-orange-500/30',
      text: 'text-orange-400',
      badge: 'bg-orange-500/20 text-orange-300',
    },
    purple: {
      bg: 'bg-purple-500/10',
      border: 'border-purple-500/30',
      text: 'text-purple-400',
      badge: 'bg-purple-500/20 text-purple-300',
    },
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(0)}K`;
    return num.toString();
  };

  return (
    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-white mb-1">Rate Limit Tiers</h3>
          <p className="text-gray-400 text-sm">
            Available rate limit configurations for API keys
          </p>
        </div>
        <div className="text-3xl">⚡</div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {TIER_CONFIGS.map((tier, index) => {
          const colors = colorClasses[tier.color];
          const isCurrent = currentTier === tier.tier;
          const isHighlighted = highlightTier === tier.tier;

          return (
            <motion.div
              key={tier.tier}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
              className={`
                ${colors.bg} ${colors.border}
                border-2 rounded-xl p-5
                backdrop-blur-sm
                transition-all duration-300
                ${isCurrent ? 'ring-2 ring-nvidia-green/50 shadow-lg shadow-nvidia-green/20' : ''}
                ${isHighlighted ? 'ring-2 ring-yellow-500/50 shadow-lg shadow-yellow-500/20' : ''}
                hover:scale-105
              `}
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className={`${colors.text} text-lg font-bold mb-1`}>
                    {tier.name}
                  </h4>
                  {isCurrent && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-nvidia-green/20 text-nvidia-green">
                      CURRENT
                    </span>
                  )}
                  {isHighlighted && !isCurrent && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-yellow-500/20 text-yellow-400">
                      RECOMMENDED
                    </span>
                  )}
                </div>
              </div>

              <p className="text-gray-400 text-sm mb-4">{tier.description}</p>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400 text-sm">RPM</span>
                  <span className={`${colors.text} font-bold`}>
                    {formatNumber(tier.rpm)}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-gray-400 text-sm">TPM</span>
                  <span className={`${colors.text} font-bold`}>
                    {formatNumber(tier.tpm)}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-gray-400 text-sm">RPD</span>
                  <span className={`${colors.text} font-bold`}>
                    {formatNumber(tier.rpd)}
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-700/50">
                <div className="text-xs text-gray-500 space-y-1">
                  <div>Requests Per Minute (RPM)</div>
                  <div>Tokens Per Minute (TPM)</div>
                  <div>Requests Per Day (RPD)</div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
