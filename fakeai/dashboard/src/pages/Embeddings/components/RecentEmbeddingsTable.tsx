/**
 * Recent Embeddings Table Component
 * Displays recent embedding requests with details
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { RecentEmbedding } from '../types';

interface RecentEmbeddingsTableProps {
  embeddings: RecentEmbedding[];
  isLoading?: boolean;
}

export const RecentEmbeddingsTable: React.FC<RecentEmbeddingsTableProps> = ({ embeddings, isLoading }) => {
  const formatTimestamp = (timestamp: number): string => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
  };

  const formatCost = (cost: number): string => {
    return `$${cost.toFixed(6)}`;
  };

  const formatDuration = (ms: number): string => {
    if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`;
    return `${ms.toFixed(0)}ms`;
  };

  if (isLoading) {
    return (
      <div className="table-container">
        <div className="chart-header">
          <h3 className="chart-title">Recent Embeddings</h3>
        </div>
        <div className="empty-state">
          <div className="loading-spinner" />
          <p className="empty-state-text">Loading recent embeddings...</p>
        </div>
      </div>
    );
  }

  if (embeddings.length === 0) {
    return (
      <div className="table-container">
        <div className="chart-header">
          <h3 className="chart-title">Recent Embeddings</h3>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <p className="empty-state-text">No recent embeddings to display</p>
        </div>
      </div>
    );
  }

  return (
    <div className="table-container">
      <div className="chart-header">
        <div>
          <h3 className="chart-title">Recent Embeddings</h3>
          <p className="chart-subtitle">Latest {embeddings.length} embedding requests</p>
        </div>
        <button className="btn btn-secondary btn-export">
          <span>📥</span>
          <span>Export CSV</span>
        </button>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Model</th>
            <th>Tokens</th>
            <th>Dimensions</th>
            <th>Batch Size</th>
            <th>Processing Time</th>
            <th>Cost</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {embeddings.map((embedding) => (
            <tr key={embedding.id}>
              <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                {formatTimestamp(embedding.timestamp)}
              </td>
              <td>
                <span className="model-badge">{embedding.model}</span>
              </td>
              <td>{embedding.input_tokens.toLocaleString()}</td>
              <td>{embedding.dimensions}</td>
              <td>{embedding.batch_size}</td>
              <td>{formatDuration(embedding.processing_time)}</td>
              <td className="cost-value">{formatCost(embedding.cost)}</td>
              <td>
                <span className={`status-badge status-${embedding.status}`}>
                  {embedding.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
