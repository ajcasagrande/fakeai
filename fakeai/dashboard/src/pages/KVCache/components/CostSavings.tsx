/**
 * Cost Savings Component
 * Displays cost savings from cache usage
 */

import React from 'react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import { CacheCostSavings } from '../types';

interface CostSavingsProps {
  costSavings: CacheCostSavings;
  loading?: boolean;
}

export const CostSavings: React.FC<CostSavingsProps> = ({
  costSavings,
  loading,
}) => {
  if (loading) {
    return (
      <div className="chart-container">
        <div className="chart-skeleton"></div>
      </div>
    );
  }

  const formatCurrency = (amount: number): string => {
    return `$${amount.toFixed(2)}`;
  };

  const comparisonData = [
    {
      category: 'Cost per Token',
      withCache: costSavings.cost_per_token_with_cache * 1000,
      withoutCache: costSavings.cost_per_token_without_cache * 1000,
    },
  ];

  const savingsData = [
    { period: 'Total', amount: costSavings.total_savings },
    { period: 'Monthly', amount: costSavings.projected_monthly_savings },
    { period: 'Yearly', amount: costSavings.projected_yearly_savings },
  ];

  return (
    <div className="cost-savings">
      <div className="card-header">
        <h3 className="card-title">Cost Savings from Caching</h3>
        <div className="savings-badge-large">
          <span className="badge-label">Total Savings:</span>
          <span className="badge-value">{formatCurrency(costSavings.total_savings)}</span>
        </div>
      </div>

      <div className="cost-content">
        <div className="savings-overview">
          <div className="savings-card primary">
            <div className="savings-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div className="savings-content">
              <div className="savings-label">Total Savings</div>
              <div className="savings-value">{formatCurrency(costSavings.total_savings)}</div>
              <div className="savings-subtitle">
                {costSavings.savings_percent.toFixed(1)}% reduction
              </div>
            </div>
          </div>

          <div className="savings-card">
            <div className="savings-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            </div>
            <div className="savings-content">
              <div className="savings-label">Projected Monthly</div>
              <div className="savings-value">{formatCurrency(costSavings.projected_monthly_savings)}</div>
              <div className="savings-subtitle">Based on current usage</div>
            </div>
          </div>

          <div className="savings-card">
            <div className="savings-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
            </div>
            <div className="savings-content">
              <div className="savings-label">Projected Yearly</div>
              <div className="savings-value">{formatCurrency(costSavings.projected_yearly_savings)}</div>
              <div className="savings-subtitle">Annual projection</div>
            </div>
          </div>

          <div className="savings-card percentage">
            <div className="savings-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                />
              </svg>
            </div>
            <div className="savings-content">
              <div className="savings-label">Savings Percentage</div>
              <div className="savings-value percentage-value">
                {costSavings.savings_percent.toFixed(2)}%
              </div>
              <div className="savings-subtitle">Cost reduction</div>
            </div>
          </div>
        </div>

        <div className="charts-section">
          <div className="chart-container">
            <h4 className="chart-title">Projected Savings Timeline</h4>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart
                data={savingsData}
                margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="savingsGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#76b900" stopOpacity={0.9} />
                    <stop offset="100%" stopColor="#76b900" stopOpacity={0.6} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis
                  dataKey="period"
                  stroke="#999"
                  style={{ fontSize: '12px' }}
                />
                <YAxis
                  stroke="#999"
                  style={{ fontSize: '12px' }}
                  tickFormatter={(value) => `$${value}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1a1a1a',
                    border: '1px solid #333',
                    borderRadius: '8px',
                  }}
                  formatter={(value: number) => [formatCurrency(value), 'Savings']}
                />
                <Bar
                  dataKey="amount"
                  fill="url(#savingsGradient)"
                  radius={[8, 8, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="cost-comparison">
            <h4 className="chart-title">Cost per 1000 Tokens Comparison</h4>
            <div className="comparison-bars">
              <div className="comparison-item">
                <div className="comparison-label">Without Cache</div>
                <div className="comparison-bar-container">
                  <div
                    className="comparison-bar without-cache"
                    style={{
                      width: '100%',
                    }}
                  >
                    <span className="comparison-value">
                      {formatCurrency(costSavings.cost_per_token_without_cache * 1000)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="comparison-item">
                <div className="comparison-label">With Cache</div>
                <div className="comparison-bar-container">
                  <div
                    className="comparison-bar with-cache"
                    style={{
                      width: `${(costSavings.cost_per_token_with_cache / costSavings.cost_per_token_without_cache) * 100}%`,
                    }}
                  >
                    <span className="comparison-value">
                      {formatCurrency(costSavings.cost_per_token_with_cache * 1000)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="savings-indicator">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                  />
                </svg>
                <span>
                  {costSavings.savings_percent.toFixed(1)}% savings per 1000 tokens
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="roi-section">
          <div className="roi-card">
            <h4 className="roi-title">Return on Investment (ROI)</h4>
            <div className="roi-content">
              <div className="roi-stat">
                <div className="roi-label">Monthly ROI</div>
                <div className="roi-value">
                  {formatCurrency(costSavings.projected_monthly_savings)}
                </div>
              </div>
              <div className="roi-divider"></div>
              <div className="roi-stat">
                <div className="roi-label">Annual ROI</div>
                <div className="roi-value">
                  {formatCurrency(costSavings.projected_yearly_savings)}
                </div>
              </div>
              <div className="roi-divider"></div>
              <div className="roi-stat">
                <div className="roi-label">Cost Efficiency</div>
                <div className="roi-value">{costSavings.savings_percent.toFixed(1)}%</div>
              </div>
            </div>
            <div className="roi-description">
              By implementing KV cache, you're reducing token processing costs by{' '}
              {costSavings.savings_percent.toFixed(1)}%, resulting in significant cost savings over time.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
