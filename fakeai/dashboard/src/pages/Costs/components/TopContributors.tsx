/**
 * Top Contributors Component
 * Shows top cost contributors (models and services)
 */

import React from 'react';
import { ModelCost, ServiceCost } from '../types';

interface TopContributorsProps {
  models: ModelCost[];
  services: ServiceCost[];
  loading: boolean;
}

export const TopContributors: React.FC<TopContributorsProps> = ({ models, services, loading }) => {
  const formatCost = (cost: number): string => {
    if (cost >= 1) return `$${cost.toFixed(2)}`;
    return `$${cost.toFixed(6)}`;
  };

  if (loading) {
    return <div className="top-contributors-container"><div className="skeleton-list"></div></div>;
  }

  const topModels = [...models].sort((a, b) => b.total_cost - a.total_cost).slice(0, 5);
  const topServices = [...services].sort((a, b) => b.total_cost - a.total_cost).slice(0, 3);

  return (
    <div className="top-contributors-container">
      <h3 className="section-title">Top Cost Contributors</h3>

      <div className="contributors-section">
        <h4 className="subsection-title">Top 5 Models</h4>
        <div className="contributors-list">
          {topModels.map((model, index) => (
            <div key={model.model} className="contributor-item">
              <div className="contributor-rank">#{index + 1}</div>
              <div className="contributor-info">
                <div className="contributor-name">{model.model}</div>
                <div className="contributor-meta">
                  {model.request_count.toLocaleString()} requests • {formatCost(model.cost_per_1k_tokens)}/1K tokens
                </div>
              </div>
              <div className="contributor-cost">{formatCost(model.total_cost)}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="contributors-section">
        <h4 className="subsection-title">Top Services</h4>
        <div className="contributors-list">
          {topServices.map((service, index) => (
            <div key={service.service} className="contributor-item">
              <div className="contributor-rank">#{index + 1}</div>
              <div className="contributor-info">
                <div className="contributor-name">{service.service}</div>
                <div className="contributor-meta">
                  {service.percentage.toFixed(1)}% of total
                </div>
              </div>
              <div className="contributor-cost">{formatCost(service.total_cost)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
