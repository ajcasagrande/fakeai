/**
 * Cost Visualization Component
 * Displays cost per request and total cost analysis
 */

import React from 'react';
import { ModelStats } from '../types';

interface CostVisualizationProps {
  modelStats: Record<string, ModelStats>;
}

export const CostVisualization: React.FC<CostVisualizationProps> = ({ modelStats }) => {
  const costData = React.useMemo(() => {
    const data = Object.entries(modelStats)
      .map(([model, stats]) => ({
        model,
        totalCost: stats.total_cost,
        avgCostPerRequest: stats.avg_cost_per_request,
        requestCount: stats.request_count,
        costPerToken: stats.total_tokens > 0 ? stats.total_cost / stats.total_tokens : 0,
      }))
      .filter(d => d.totalCost > 0)
      .sort((a, b) => b.totalCost - a.totalCost);

    const totalCost = data.reduce((sum, d) => sum + d.totalCost, 0);

    return {
      models: data,
      totalCost,
      avgCostPerRequest:
        data.reduce((sum, d) => sum + d.avgCostPerRequest * d.requestCount, 0) /
        Math.max(data.reduce((sum, d) => sum + d.requestCount, 0), 1),
    };
  }, [modelStats]);

  const formatCost = (cost: number): string => {
    if (cost >= 1) {
      return `$${cost.toFixed(2)}`;
    }
    if (cost >= 0.01) {
      return `$${cost.toFixed(4)}`;
    }
    return `$${cost.toFixed(6)}`;
  };

  const maxCost = Math.max(...costData.models.map(d => d.totalCost));

  const nvidiaColors = [
    '#76B900', // NVIDIA Green
    '#1A1A1A', // Dark Gray
    '#00A9E0', // Cyan
    '#FF6B00', // Orange
    '#9D5CC9', // Purple
    '#FFD700', // Gold
    '#00CED1', // Dark Turquoise
    '#FF69B4', // Hot Pink
  ];

  return (
    <div className="cost-visualization-container">
      <h3 className="section-title">Cost Analysis</h3>

      <div className="cost-summary-cards">
        <div className="cost-summary-card total">
          <div className="card-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div className="card-content">
            <div className="card-label">Total Cost</div>
            <div className="card-value">{formatCost(costData.totalCost)}</div>
            <div className="card-detail">All models combined</div>
          </div>
        </div>

        <div className="cost-summary-card average">
          <div className="card-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
          </div>
          <div className="card-content">
            <div className="card-label">Avg Cost / Request</div>
            <div className="card-value">{formatCost(costData.avgCostPerRequest)}</div>
            <div className="card-detail">Across all requests</div>
          </div>
        </div>

        <div className="cost-summary-card models">
          <div className="card-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <div className="card-content">
            <div className="card-label">Active Models</div>
            <div className="card-value">{costData.models.length}</div>
            <div className="card-detail">With tracked costs</div>
          </div>
        </div>
      </div>

      <div className="cost-breakdown">
        <h4 className="subsection-title">Cost Breakdown by Model</h4>

        <div className="cost-chart">
          {costData.models.slice(0, 10).map((model, index) => {
            const percentage = (model.totalCost / costData.totalCost) * 100;
            const barWidth = (model.totalCost / maxCost) * 100;
            const color = nvidiaColors[index % nvidiaColors.length];

            return (
              <div key={model.model} className="cost-bar-item">
                <div className="cost-bar-header">
                  <span className="model-name">{model.model}</span>
                  <span className="cost-value">{formatCost(model.totalCost)}</span>
                </div>
                <div className="cost-bar-wrapper">
                  <div
                    className="cost-bar-fill"
                    style={{
                      width: `${barWidth}%`,
                      backgroundColor: color,
                    }}
                  >
                    <span className="percentage-label">{percentage.toFixed(1)}%</span>
                  </div>
                </div>
                <div className="cost-bar-details">
                  <span className="detail-item">
                    {model.requestCount} requests
                  </span>
                  <span className="detail-item">
                    {formatCost(model.avgCostPerRequest)} avg/req
                  </span>
                  <span className="detail-item">
                    {formatCost(model.costPerToken * 1000)} per 1K tokens
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="cost-comparison-table">
        <h4 className="subsection-title">Cost Efficiency Rankings</h4>
        <table className="comparison-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Model</th>
              <th>Total Cost</th>
              <th>Avg / Request</th>
              <th>Cost / 1K Tokens</th>
              <th>Requests</th>
            </tr>
          </thead>
          <tbody>
            {costData.models
              .sort((a, b) => a.avgCostPerRequest - b.avgCostPerRequest)
              .slice(0, 10)
              .map((model, index) => (
                <tr key={model.model}>
                  <td className="rank">
                    {index === 0 ? (
                      <span className="rank-badge gold">1</span>
                    ) : index === 1 ? (
                      <span className="rank-badge silver">2</span>
                    ) : index === 2 ? (
                      <span className="rank-badge bronze">3</span>
                    ) : (
                      <span className="rank-number">{index + 1}</span>
                    )}
                  </td>
                  <td className="model-name">{model.model}</td>
                  <td className="total-cost">{formatCost(model.totalCost)}</td>
                  <td className="avg-cost">{formatCost(model.avgCostPerRequest)}</td>
                  <td className="token-cost">{formatCost(model.costPerToken * 1000)}</td>
                  <td className="request-count">{model.requestCount.toLocaleString()}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <div className="cost-projections">
        <h4 className="subsection-title">Cost Projections</h4>
        <div className="projection-cards">
          <div className="projection-card">
            <div className="projection-label">Projected Daily Cost</div>
            <div className="projection-value">{formatCost(costData.totalCost)}</div>
            <div className="projection-note">Based on current usage</div>
          </div>
          <div className="projection-card">
            <div className="projection-label">Projected Monthly Cost</div>
            <div className="projection-value">{formatCost(costData.totalCost * 30)}</div>
            <div className="projection-note">Estimated for 30 days</div>
          </div>
          <div className="projection-card">
            <div className="projection-label">Projected Annual Cost</div>
            <div className="projection-value">{formatCost(costData.totalCost * 365)}</div>
            <div className="projection-note">Estimated for 365 days</div>
          </div>
        </div>
      </div>
    </div>
  );
};
