/**
 * Cost Analysis Component
 * Displays cost breakdown and analysis by model
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { CostBreakdown } from '../types';

interface CostAnalysisProps {
  data: CostBreakdown[];
  isLoading?: boolean;
}

export const CostAnalysis: React.FC<CostAnalysisProps> = ({ data, isLoading }) => {
  const formatCost = (cost: number): string => {
    return `$${cost.toFixed(4)}`;
  };

  const formatCostSmall = (cost: number): string => {
    return `$${cost.toFixed(6)}`;
  };

  if (isLoading) {
    return (
      <div className="table-container">
        <div className="chart-header">
          <div>
            <h3 className="chart-title">Cost Analysis</h3>
            <p className="chart-subtitle">Loading cost data...</p>
          </div>
        </div>
        <div className="empty-state">
          <div className="loading-spinner" />
          <p className="empty-state-text">Calculating costs...</p>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="table-container">
        <div className="chart-header">
          <div>
            <h3 className="chart-title">Cost Analysis</h3>
            <p className="chart-subtitle">No data available</p>
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">💰</div>
          <p className="empty-state-text">No cost data to display</p>
        </div>
      </div>
    );
  }

  // Calculate totals
  const totalCost = data.reduce((sum, item) => sum + item.total_cost, 0);
  const totalRequests = data.reduce((sum, item) => sum + item.total_requests, 0);
  const avgCostPerRequest = totalCost / totalRequests;

  return (
    <div className="table-container">
      <div className="chart-header">
        <div>
          <h3 className="chart-title">Cost Analysis by Model</h3>
          <p className="chart-subtitle">
            Total Cost: <span className="cost-value">{formatCost(totalCost)}</span> |
            Avg per Request: <span className="cost-value">{formatCostSmall(avgCostPerRequest)}</span>
          </p>
        </div>
        <button className="btn btn-export">
          <span>📊</span>
          <span>Export Report</span>
        </button>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>Model</th>
            <th>Total Cost</th>
            <th>Requests</th>
            <th>Cost/Request</th>
            <th>Cost/1K Tokens</th>
            <th>% of Total</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item, index) => {
            const percentOfTotal = (item.total_cost / totalCost) * 100;

            return (
              <tr key={index}>
                <td>
                  <span className="model-badge">{item.model}</span>
                </td>
                <td className="cost-value" style={{ fontWeight: 600, fontSize: '1.1rem' }}>
                  {formatCost(item.total_cost)}
                </td>
                <td>{item.total_requests.toLocaleString()}</td>
                <td className="cost-value">{formatCostSmall(item.cost_per_request)}</td>
                <td className="cost-value">{formatCostSmall(item.cost_per_1k_tokens)}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{
                      flex: 1,
                      height: '8px',
                      background: 'var(--nvidia-dark-gray)',
                      borderRadius: '4px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        width: `${percentOfTotal}%`,
                        height: '100%',
                        background: 'var(--nvidia-green)',
                        transition: 'width 0.3s ease'
                      }} />
                    </div>
                    <span style={{ minWidth: '50px', textAlign: 'right' }}>
                      {percentOfTotal.toFixed(1)}%
                    </span>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
        <tfoot>
          <tr style={{ fontWeight: 'bold', borderTop: '2px solid var(--nvidia-green)' }}>
            <td>Total</td>
            <td className="cost-value" style={{ fontSize: '1.2rem' }}>
              {formatCost(totalCost)}
            </td>
            <td>{totalRequests.toLocaleString()}</td>
            <td className="cost-value">{formatCostSmall(avgCostPerRequest)}</td>
            <td>-</td>
            <td>100%</td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
};
