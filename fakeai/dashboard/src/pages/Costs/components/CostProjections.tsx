/**
 * Cost Projections Component
 * Shows projected costs for various time periods
 */

import React from 'react';
import { DailyCost } from '../types';

interface CostProjectionsProps {
  dailyCosts: DailyCost[];
  loading: boolean;
}

export const CostProjections: React.FC<CostProjectionsProps> = ({ dailyCosts, loading }) => {
  const formatCost = (cost: number): string => {
    if (cost >= 1000) return `$${(cost / 1000).toFixed(2)}K`;
    if (cost >= 1) return `$${cost.toFixed(2)}`;
    return `$${cost.toFixed(4)}`;
  };

  if (loading || !dailyCosts || dailyCosts.length === 0) {
    return <div className="cost-projections-container"><div className="skeleton-cards"></div></div>;
  }

  const avgDailyCost = dailyCosts.reduce((sum, d) => sum + d.total_cost, 0) / dailyCosts.length;
  const last7Days = dailyCosts.slice(-7);
  const recentAvg = last7Days.reduce((sum, d) => sum + d.total_cost, 0) / last7Days.length;

  // Calculate trend
  const firstHalf = dailyCosts.slice(0, Math.floor(dailyCosts.length / 2));
  const secondHalf = dailyCosts.slice(Math.floor(dailyCosts.length / 2));
  const firstAvg = firstHalf.reduce((sum, d) => sum + d.total_cost, 0) / firstHalf.length;
  const secondAvg = secondHalf.reduce((sum, d) => sum + d.total_cost, 0) / secondHalf.length;
  const growthRate = (secondAvg - firstAvg) / firstAvg;

  const projections = [
    {
      period: 'Next 7 Days',
      cost: recentAvg * 7,
      based_on: 'Last 7 days average',
      confidence: 95,
    },
    {
      period: 'Next 30 Days',
      cost: recentAvg * 30,
      based_on: 'Current trend',
      confidence: 85,
    },
    {
      period: 'Next 90 Days',
      cost: recentAvg * 90 * (1 + growthRate / 2),
      based_on: 'Growth adjusted',
      confidence: 70,
    },
    {
      period: 'Annual',
      cost: recentAvg * 365 * (1 + growthRate),
      based_on: 'Growth projection',
      confidence: 60,
    },
  ];

  return (
    <div className="cost-projections-container">
      <h3 className="section-title">Cost Projections</h3>

      <div className="projections-grid">
        {projections.map((proj, index) => (
          <div key={index} className="projection-card">
            <div className="projection-header">
              <h4 className="projection-period">{proj.period}</h4>
              <div className="confidence-badge">
                {proj.confidence}% confidence
              </div>
            </div>
            <div className="projection-value">{formatCost(proj.cost)}</div>
            <div className="projection-meta">
              <div className="projection-note">{proj.based_on}</div>
              <div className="projection-daily">
                ~{formatCost(proj.cost / (proj.period.includes('7') ? 7 : proj.period.includes('30') ? 30 : proj.period.includes('90') ? 90 : 365))}/day
              </div>
            </div>
            <div className="projection-bar">
              <div
                className="projection-fill"
                style={{ width: `${proj.confidence}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>

      <div className="projection-disclaimer">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>Projections are estimates based on historical data and may vary with actual usage.</span>
      </div>
    </div>
  );
};
