/**
 * Token Statistics Component
 * Displays token usage breakdown and statistics
 */

import React from 'react';
import { TokenBreakdown } from '../types';

interface TokenStatsProps {
  tokenBreakdown: TokenBreakdown;
}

export const TokenStats: React.FC<TokenStatsProps> = ({ tokenBreakdown }) => {
  const { prompt_tokens, completion_tokens, cached_tokens, total_tokens } = tokenBreakdown;

  const formatNumber = (num: number): string => {
    if (num >= 1000000000) {
      return `${(num / 1000000000).toFixed(2)}B`;
    }
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(2)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(2)}K`;
    }
    return num.toFixed(0);
  };

  const promptPercentage = (prompt_tokens / total_tokens) * 100;
  const completionPercentage = (completion_tokens / total_tokens) * 100;
  const cachedPercentage = (cached_tokens / total_tokens) * 100;

  return (
    <div className="token-stats-container">
      <h3 className="section-title">Token Usage Breakdown</h3>

      <div className="token-visualization">
        <div className="token-bar">
          <div
            className="token-segment prompt"
            style={{ width: `${promptPercentage}%` }}
            title={`Prompt: ${formatNumber(prompt_tokens)} (${promptPercentage.toFixed(1)}%)`}
          ></div>
          <div
            className="token-segment completion"
            style={{ width: `${completionPercentage}%` }}
            title={`Completion: ${formatNumber(completion_tokens)} (${completionPercentage.toFixed(1)}%)`}
          ></div>
          {cached_tokens > 0 && (
            <div
              className="token-segment cached"
              style={{ width: `${cachedPercentage}%` }}
              title={`Cached: ${formatNumber(cached_tokens)} (${cachedPercentage.toFixed(1)}%)`}
            ></div>
          )}
        </div>

        <div className="token-legend">
          <div className="token-legend-item">
            <div className="legend-indicator prompt"></div>
            <div className="legend-text">
              <span className="legend-label">Prompt Tokens</span>
              <span className="legend-value">{formatNumber(prompt_tokens)}</span>
              <span className="legend-percentage">{promptPercentage.toFixed(1)}%</span>
            </div>
          </div>

          <div className="token-legend-item">
            <div className="legend-indicator completion"></div>
            <div className="legend-text">
              <span className="legend-label">Completion Tokens</span>
              <span className="legend-value">{formatNumber(completion_tokens)}</span>
              <span className="legend-percentage">{completionPercentage.toFixed(1)}%</span>
            </div>
          </div>

          {cached_tokens > 0 && (
            <div className="token-legend-item">
              <div className="legend-indicator cached"></div>
              <div className="legend-text">
                <span className="legend-label">Cached Tokens</span>
                <span className="legend-value">{formatNumber(cached_tokens)}</span>
                <span className="legend-percentage">{cachedPercentage.toFixed(1)}%</span>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="token-summary">
        <div className="summary-item">
          <span className="summary-label">Total Tokens</span>
          <span className="summary-value total">{formatNumber(total_tokens)}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Avg per Request</span>
          <span className="summary-value">
            {formatNumber(total_tokens / Math.max(1, prompt_tokens + completion_tokens))}
          </span>
        </div>
        {cached_tokens > 0 && (
          <div className="summary-item">
            <span className="summary-label">Cache Efficiency</span>
            <span className="summary-value success">
              {((cached_tokens / total_tokens) * 100).toFixed(1)}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
