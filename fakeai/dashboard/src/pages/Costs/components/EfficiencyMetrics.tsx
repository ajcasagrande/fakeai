/**
 * Efficiency Metrics Component
 * Displays cost efficiency metrics
 */

import React from 'react';
import { ModelCost } from '../types';

interface EfficiencyMetricsProps {
  models: ModelCost[];
  totalCost: number;
  totalRequests: number;
  loading: boolean;
}

export const EfficiencyMetrics: React.FC<EfficiencyMetricsProps> = ({
  models,
  totalCost,
  totalRequests,
  loading,
}) => {
  const formatCost = (cost: number): string => {
    if (cost >= 1) return `$${cost.toFixed(2)}`;
    return `$${cost.toFixed(6)}`;
  };

  if (loading) {
    return <div className="efficiency-metrics-container"><div className="skeleton-metrics"></div></div>;
  }

  const totalTokens = models.reduce((sum, m) => sum + m.input_tokens + m.output_tokens, 0);
  const avgCostPerRequest = totalRequests > 0 ? totalCost / totalRequests : 0;
  const avgCostPer1kTokens = totalTokens > 0 ? (totalCost / totalTokens) * 1000 : 0;

  const mostEfficientModel = [...models]
    .filter(m => m.request_count > 0)
    .sort((a, b) => a.cost_per_1k_tokens - b.cost_per_1k_tokens)[0];

  const leastEfficientModel = [...models]
    .filter(m => m.request_count > 0)
    .sort((a, b) => b.cost_per_1k_tokens - a.cost_per_1k_tokens)[0];

  const metrics = [
    {
      title: 'Avg Cost per Request',
      value: formatCost(avgCostPerRequest),
      icon: 'M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z',
      description: 'Average cost across all API requests',
    },
    {
      title: 'Cost per 1K Tokens',
      value: formatCost(avgCostPer1kTokens),
      icon: 'M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z',
      description: 'Average cost per 1,000 tokens processed',
    },
    {
      title: 'Most Efficient Model',
      value: mostEfficientModel?.model || 'N/A',
      subtitle: mostEfficientModel ? formatCost(mostEfficientModel.cost_per_1k_tokens) + '/1K' : '',
      icon: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
      description: 'Model with lowest cost per token',
    },
    {
      title: 'Least Efficient Model',
      value: leastEfficientModel?.model || 'N/A',
      subtitle: leastEfficientModel ? formatCost(leastEfficientModel.cost_per_1k_tokens) + '/1K' : '',
      icon: 'M13 17h8m0 0V9m0 8l-8-8-4 4-6-6',
      description: 'Model with highest cost per token',
    },
  ];

  return (
    <div className="efficiency-metrics-container">
      <h3 className="section-title">Efficiency Metrics</h3>

      <div className="metrics-grid">
        {metrics.map((metric, index) => (
          <div key={index} className="efficiency-card">
            <div className="efficiency-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={metric.icon} />
              </svg>
            </div>
            <div className="efficiency-content">
              <h4 className="efficiency-title">{metric.title}</h4>
              <div className="efficiency-value">{metric.value}</div>
              {metric.subtitle && <div className="efficiency-subtitle">{metric.subtitle}</div>}
              <p className="efficiency-description">{metric.description}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="efficiency-comparison">
        <h4 className="subsection-title">Model Efficiency Ranking</h4>
        <div className="efficiency-table">
          <div className="table-header">
            <span>Model</span>
            <span>Cost/1K Tokens</span>
            <span>Efficiency Score</span>
          </div>
          {[...models]
            .filter(m => m.request_count > 0)
            .sort((a, b) => a.cost_per_1k_tokens - b.cost_per_1k_tokens)
            .slice(0, 5)
            .map((model, index) => {
              const score = mostEfficientModel
                ? Math.max(0, 100 - ((model.cost_per_1k_tokens / mostEfficientModel.cost_per_1k_tokens - 1) * 100))
                : 100;

              return (
                <div key={model.model} className="table-row">
                  <span className="model-name">
                    <span className="rank-badge">#{index + 1}</span>
                    {model.model}
                  </span>
                  <span className="cost-value">{formatCost(model.cost_per_1k_tokens)}</span>
                  <div className="score-bar">
                    <div className="score-fill" style={{ width: `${score}%` }}></div>
                    <span className="score-label">{score.toFixed(0)}</span>
                  </div>
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
};
