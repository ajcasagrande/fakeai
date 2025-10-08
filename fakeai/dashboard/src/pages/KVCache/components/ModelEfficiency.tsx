/**
 * Model Cache Efficiency Component
 * Displays cache efficiency metrics broken down by model
 */

import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { ModelCacheEfficiency } from '../types';

interface ModelEfficiencyProps {
  models: ModelCacheEfficiency[];
  loading?: boolean;
}

export const ModelEfficiency: React.FC<ModelEfficiencyProps> = ({
  models,
  loading,
}) => {
  const [sortBy, setSortBy] = useState<'hit_rate' | 'speedup' | 'savings'>('hit_rate');
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="chart-container">
        <div className="chart-skeleton"></div>
      </div>
    );
  }

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(2)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(2)}K`;
    }
    return num.toFixed(0);
  };

  const sortedModels = [...models].sort((a, b) => {
    switch (sortBy) {
      case 'hit_rate':
        return b.hit_rate - a.hit_rate;
      case 'speedup':
        return b.speedup_factor - a.speedup_factor;
      case 'savings':
        return b.cost_savings - a.cost_savings;
      default:
        return 0;
    }
  });

  const chartData = sortedModels.map((model) => ({
    model: model.model.length > 20 ? model.model.substring(0, 20) + '...' : model.model,
    fullModel: model.model,
    hitRate: model.hit_rate,
    speedup: model.speedup_factor,
    savings: model.cost_savings,
  }));

  const getBarColor = (value: number, max: number) => {
    const ratio = value / max;
    if (ratio >= 0.8) return '#76b900';
    if (ratio >= 0.6) return '#00bfff';
    if (ratio >= 0.4) return '#ff9900';
    return '#ff6b6b';
  };

  const selectedModelData = selectedModel
    ? models.find((m) => m.model === selectedModel)
    : null;

  return (
    <div className="model-efficiency">
      <div className="card-header">
        <h3 className="card-title">Cache Efficiency by Model</h3>
        <div className="sort-controls">
          <label>Sort by:</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="sort-select"
          >
            <option value="hit_rate">Hit Rate</option>
            <option value="speedup">Speedup Factor</option>
            <option value="savings">Cost Savings</option>
          </select>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={chartData}
          margin={{ top: 10, right: 30, left: 0, bottom: 60 }}
          onClick={(data) => {
            if (data && data.activePayload) {
              setSelectedModel(data.activePayload[0].payload.fullModel);
            }
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis
            dataKey="model"
            stroke="#999"
            angle={-45}
            textAnchor="end"
            height={100}
            style={{ fontSize: '11px' }}
          />
          <YAxis
            stroke="#999"
            style={{ fontSize: '12px' }}
            tickFormatter={(value) =>
              sortBy === 'hit_rate' ? `${value}%` : sortBy === 'speedup' ? `${value}x` : `$${value}`
            }
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a1a1a',
              border: '1px solid #333',
              borderRadius: '8px',
            }}
            formatter={(value: number) => {
              if (sortBy === 'hit_rate') return `${value.toFixed(2)}%`;
              if (sortBy === 'speedup') return `${value.toFixed(2)}x`;
              return `$${value.toFixed(2)}`;
            }}
          />
          <Bar
            dataKey={sortBy === 'hit_rate' ? 'hitRate' : sortBy === 'speedup' ? 'speedup' : 'savings'}
            radius={[8, 8, 0, 0]}
          >
            {chartData.map((entry, index) => {
              const maxValue = Math.max(
                ...chartData.map((d) =>
                  sortBy === 'hit_rate' ? d.hitRate : sortBy === 'speedup' ? d.speedup : d.savings
                )
              );
              const value =
                sortBy === 'hit_rate' ? entry.hitRate : sortBy === 'speedup' ? entry.speedup : entry.savings;
              return (
                <Cell
                  key={`cell-${index}`}
                  fill={getBarColor(value, maxValue)}
                  opacity={selectedModel === entry.fullModel ? 1 : 0.8}
                />
              );
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {selectedModelData && (
        <div className="model-details">
          <div className="details-header">
            <h4 className="details-title">{selectedModelData.model}</h4>
            <button
              className="close-details"
              onClick={() => setSelectedModel(null)}
            >
              ×
            </button>
          </div>

          <div className="details-grid">
            <div className="detail-item">
              <span className="detail-label">Hit Rate</span>
              <span className="detail-value">{selectedModelData.hit_rate.toFixed(2)}%</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Miss Rate</span>
              <span className="detail-value">{selectedModelData.miss_rate.toFixed(2)}%</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Total Hits</span>
              <span className="detail-value">{formatNumber(selectedModelData.total_hits)}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Total Misses</span>
              <span className="detail-value">{formatNumber(selectedModelData.total_misses)}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Speedup Factor</span>
              <span className="detail-value">{selectedModelData.speedup_factor.toFixed(2)}x</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Tokens Saved</span>
              <span className="detail-value">{formatNumber(selectedModelData.tokens_saved)}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Cost Savings</span>
              <span className="detail-value">${selectedModelData.cost_savings.toFixed(2)}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Cache Size</span>
              <span className="detail-value">{selectedModelData.cache_size_mb.toFixed(2)} MB</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Memory Usage</span>
              <span className="detail-value">{selectedModelData.memory_usage_mb.toFixed(2)} MB</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Evictions</span>
              <span className="detail-value">{formatNumber(selectedModelData.evictions)}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Avg Latency (Cached)</span>
              <span className="detail-value">{selectedModelData.avg_latency_with_cache.toFixed(0)} ms</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Avg Latency (Uncached)</span>
              <span className="detail-value">{selectedModelData.avg_latency_without_cache.toFixed(0)} ms</span>
            </div>
          </div>
        </div>
      )}

      <div className="models-table">
        <table>
          <thead>
            <tr>
              <th>Model</th>
              <th>Hit Rate</th>
              <th>Speedup</th>
              <th>Tokens Saved</th>
              <th>Cost Savings</th>
              <th>Cache Size</th>
            </tr>
          </thead>
          <tbody>
            {sortedModels.map((model) => (
              <tr
                key={model.model}
                onClick={() => setSelectedModel(model.model)}
                className={selectedModel === model.model ? 'selected' : ''}
              >
                <td className="model-name">{model.model}</td>
                <td>
                  <span className={`hit-rate-badge ${model.hit_rate >= 70 ? 'good' : model.hit_rate >= 50 ? 'medium' : 'poor'}`}>
                    {model.hit_rate.toFixed(1)}%
                  </span>
                </td>
                <td>{model.speedup_factor.toFixed(2)}x</td>
                <td>{formatNumber(model.tokens_saved)}</td>
                <td>${model.cost_savings.toFixed(2)}</td>
                <td>{model.cache_size_mb.toFixed(2)} MB</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
