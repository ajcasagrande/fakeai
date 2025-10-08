/**
 * Model Cost Chart Component
 * Displays cost breakdown by model with horizontal bar chart
 */

import React, { useState } from 'react';
import { ModelCost } from '../types';

interface ModelCostChartProps {
  models: ModelCost[];
  loading: boolean;
}

export const ModelCostChart: React.FC<ModelCostChartProps> = ({ models, loading }) => {
  const [sortBy, setSortBy] = useState<'cost' | 'efficiency'>('cost');
  const [showCount, setShowCount] = useState(10);

  const formatCost = (cost: number): string => {
    if (cost >= 1) return `$${cost.toFixed(2)}`;
    if (cost >= 0.01) return `$${cost.toFixed(4)}`;
    return `$${cost.toFixed(6)}`;
  };

  if (loading) {
    return (
      <div className="model-cost-chart-container">
        <div className="skeleton-bars"></div>
      </div>
    );
  }

  if (!models || models.length === 0) {
    return (
      <div className="model-cost-chart-container">
        <p className="no-data">No model data available</p>
      </div>
    );
  }

  const sortedModels = [...models].sort((a, b) => {
    if (sortBy === 'cost') {
      return b.total_cost - a.total_cost;
    } else {
      return a.cost_per_1k_tokens - b.cost_per_1k_tokens;
    }
  });

  const displayedModels = sortedModels.slice(0, showCount);
  const maxCost = Math.max(...displayedModels.map(m => m.total_cost));

  const MODEL_COLORS = [
    '#76B900', '#00FFFF', '#9D00FF', '#FFA500', '#0080FF',
    '#00CC99', '#FF3388', '#FFD700', '#7AB928', '#00A9E0',
  ];

  return (
    <div className="model-cost-chart-container">
      <div className="chart-header">
        <h3 className="section-title">Cost by Model</h3>
        <div className="chart-controls">
          <div className="sort-controls">
            <label>Sort by:</label>
            <select value={sortBy} onChange={(e) => setSortBy(e.target.value as 'cost' | 'efficiency')}>
              <option value="cost">Total Cost</option>
              <option value="efficiency">Efficiency (Cost/1K tokens)</option>
            </select>
          </div>
          <div className="display-controls">
            <label>Show:</label>
            <select value={showCount} onChange={(e) => setShowCount(Number(e.target.value))}>
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
              <option value={15}>Top 15</option>
              <option value={20}>Top 20</option>
              <option value={models.length}>All ({models.length})</option>
            </select>
          </div>
        </div>
      </div>

      <div className="model-chart-bars">
        {displayedModels.map((model, index) => {
          const barWidth = (model.total_cost / maxCost) * 100;
          const color = MODEL_COLORS[index % MODEL_COLORS.length];

          return (
            <div key={model.model} className="model-bar-item">
              <div className="model-bar-header">
                <div className="model-info">
                  <span className="model-rank">#{index + 1}</span>
                  <span className="model-name">{model.model}</span>
                  <span className="model-service-badge">{model.service}</span>
                </div>
                <div className="model-cost-value">{formatCost(model.total_cost)}</div>
              </div>

              <div className="model-bar-wrapper">
                <div
                  className="model-bar-fill"
                  style={{
                    width: `${barWidth}%`,
                    backgroundColor: color,
                  }}
                >
                  <span className="percentage-label">{model.percentage.toFixed(1)}%</span>
                </div>
              </div>

              <div className="model-bar-stats">
                <div className="stat-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                  </svg>
                  <span>{model.request_count.toLocaleString()} requests</span>
                </div>
                <div className="stat-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  <span>{formatCost(model.avg_cost_per_request)}/req</span>
                </div>
                <div className="stat-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                  <span>{formatCost(model.cost_per_1k_tokens)}/1K tokens</span>
                </div>
                <div className="stat-item">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                  </svg>
                  <span>{((model.input_tokens + model.output_tokens) / 1000).toFixed(1)}K tokens</span>
                </div>
              </div>

              <div className="token-breakdown">
                <div className="token-bar">
                  <div
                    className="token-segment input-tokens"
                    style={{
                      width: `${(model.input_tokens / (model.input_tokens + model.output_tokens)) * 100}%`,
                    }}
                    title={`Input: ${model.input_tokens.toLocaleString()} tokens`}
                  ></div>
                  <div
                    className="token-segment output-tokens"
                    style={{
                      width: `${(model.output_tokens / (model.input_tokens + model.output_tokens)) * 100}%`,
                    }}
                    title={`Output: ${model.output_tokens.toLocaleString()} tokens`}
                  ></div>
                </div>
                <div className="token-labels">
                  <span className="token-label input">Input: {model.input_tokens.toLocaleString()}</span>
                  <span className="token-label output">Output: {model.output_tokens.toLocaleString()}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {models.length > showCount && (
        <div className="chart-footer">
          <button
            className="show-more-btn"
            onClick={() => setShowCount(Math.min(showCount + 10, models.length))}
          >
            Show More Models ({models.length - showCount} remaining)
          </button>
        </div>
      )}
    </div>
  );
};
