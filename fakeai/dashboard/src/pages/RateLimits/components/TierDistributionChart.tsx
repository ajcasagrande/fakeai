/**
 * Tier Distribution Chart Component
 * Displays pie chart of API key tier distribution
 */

import React from 'react';
import { motion } from 'framer-motion';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { TierDistribution } from '../types';

interface TierDistributionChartProps {
  distribution: TierDistribution[];
  loading?: boolean;
}

export const TierDistributionChart: React.FC<TierDistributionChartProps> = ({
  distribution,
  loading = false,
}) => {
  const TIER_COLORS: Record<string, string> = {
    free: '#6b7280',
    tier1: '#3b82f6',
    tier2: '#76b900',
    tier3: '#eab308',
    tier4: '#f97316',
    tier5: '#a855f7',
  };

  const TIER_NAMES: Record<string, string> = {
    free: 'Free',
    tier1: 'Tier 1',
    tier2: 'Tier 2',
    tier3: 'Tier 3',
    tier4: 'Tier 4',
    tier5: 'Tier 5',
  };

  const chartData = distribution.map((item) => ({
    name: TIER_NAMES[item.tier] || item.tier,
    value: item.count,
    percentage: item.percentage,
    requests: item.total_requests,
    tokens: item.total_tokens,
    color: TIER_COLORS[item.tier] || '#6b7280',
  }));

  const totalApiKeys = distribution.reduce((sum, d) => sum + d.count, 0);
  const totalRequests = distribution.reduce((sum, d) => sum + d.total_requests, 0);
  const totalTokens = distribution.reduce((sum, d) => sum + d.total_tokens, 0);

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;

    const data = payload[0].payload;

    return (
      <div className="bg-gray-900/95 border border-gray-700 rounded-lg p-4 shadow-xl backdrop-blur-sm">
        <div className="flex items-center gap-2 mb-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: data.color }}
          ></div>
          <span className="text-white font-semibold">{data.name}</span>
        </div>
        <div className="space-y-1 text-sm">
          <div className="flex justify-between gap-4">
            <span className="text-gray-400">API Keys:</span>
            <span className="text-white font-semibold">{data.value}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-gray-400">Percentage:</span>
            <span className="text-white font-semibold">{data.percentage.toFixed(1)}%</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-gray-400">Requests:</span>
            <span className="text-white font-semibold">
              {data.requests.toLocaleString()}
            </span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-gray-400">Tokens:</span>
            <span className="text-white font-semibold">
              {data.tokens.toLocaleString()}
            </span>
          </div>
        </div>
      </div>
    );
  };

  const renderCustomLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
  }: any) => {
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    if (percent < 0.05) return null;

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor={x > cx ? 'start' : 'end'}
        dominantBaseline="central"
        className="font-bold text-sm"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  if (loading) {
    return (
      <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
        <div className="h-6 bg-gray-700 rounded w-1/3 mb-4 animate-pulse"></div>
        <div className="h-80 bg-gray-700/50 rounded animate-pulse"></div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-white mb-1">Tier Distribution</h3>
          <p className="text-gray-400 text-sm">
            API key distribution across rate limit tiers
          </p>
        </div>
        <div className="text-2xl">📊</div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-nvidia-green/10 border border-nvidia-green/30 rounded-lg p-4"
        >
          <div className="text-gray-400 text-xs mb-1">Total API Keys</div>
          <div className="text-nvidia-green text-2xl font-bold">{totalApiKeys}</div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4"
        >
          <div className="text-gray-400 text-xs mb-1">Total Requests</div>
          <div className="text-blue-400 text-2xl font-bold">
            {totalRequests >= 1000000
              ? `${(totalRequests / 1000000).toFixed(1)}M`
              : totalRequests >= 1000
              ? `${(totalRequests / 1000).toFixed(1)}K`
              : totalRequests}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4"
        >
          <div className="text-gray-400 text-xs mb-1">Total Tokens</div>
          <div className="text-purple-400 text-2xl font-bold">
            {totalTokens >= 1000000
              ? `${(totalTokens / 1000000).toFixed(1)}M`
              : totalTokens >= 1000
              ? `${(totalTokens / 1000).toFixed(1)}K`
              : totalTokens}
          </div>
        </motion.div>
      </div>

      {/* Pie Chart */}
      <div className="mb-6">
        <ResponsiveContainer width="100%" height={350}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderCustomLabel}
              outerRadius={120}
              fill="#8884d8"
              dataKey="value"
              animationBegin={0}
              animationDuration={800}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              wrapperStyle={{ fontSize: '14px' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Detailed Breakdown */}
      <div className="space-y-2">
        {chartData.map((tier, index) => (
          <motion.div
            key={tier.name}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg hover:bg-gray-900/70 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: tier.color }}
              ></div>
              <span className="text-white font-medium">{tier.name}</span>
            </div>

            <div className="flex items-center gap-6 text-sm">
              <div className="text-right">
                <div className="text-gray-400 text-xs">Keys</div>
                <div className="text-white font-semibold">{tier.value}</div>
              </div>
              <div className="text-right">
                <div className="text-gray-400 text-xs">Share</div>
                <div className="text-white font-semibold">
                  {tier.percentage.toFixed(1)}%
                </div>
              </div>
              <div className="text-right">
                <div className="text-gray-400 text-xs">Requests</div>
                <div className="text-white font-semibold">
                  {tier.requests >= 1000000
                    ? `${(tier.requests / 1000000).toFixed(1)}M`
                    : tier.requests >= 1000
                    ? `${(tier.requests / 1000).toFixed(0)}K`
                    : tier.requests}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {distribution.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No tier distribution data available
        </div>
      )}
    </div>
  );
};
