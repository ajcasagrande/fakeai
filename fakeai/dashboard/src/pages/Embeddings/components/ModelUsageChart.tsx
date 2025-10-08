/**
 * Model Usage Chart Component
 * Visualizes model usage statistics and distribution
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useRef } from 'react';
import { ModelUsageStats } from '../types';

interface ModelUsageChartProps {
  data: ModelUsageStats[];
  isLoading?: boolean;
}

export const ModelUsageChart: React.FC<ModelUsageChartProps> = ({ data, isLoading }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || isLoading || data.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    // Clear canvas
    ctx.clearRect(0, 0, rect.width, rect.height);

    // Chart dimensions
    const padding = 60;
    const chartWidth = rect.width - padding * 2;
    const chartHeight = rect.height - padding * 2;

    // Find max values
    const maxRequests = Math.max(...data.map(d => d.requests));
    const maxTokens = Math.max(...data.map(d => d.tokens));

    // Draw grid
    ctx.strokeStyle = '#333333';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const y = padding + (chartHeight / 5) * i;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(padding + chartWidth, y);
      ctx.stroke();
    }

    // Draw bars
    const barWidth = chartWidth / data.length - 10;
    data.forEach((item, index) => {
      const x = padding + (chartWidth / data.length) * index + 5;

      // Requests bar (green)
      const requestHeight = (item.requests / maxRequests) * chartHeight;
      ctx.fillStyle = '#76B900';
      ctx.fillRect(x, padding + chartHeight - requestHeight, barWidth / 2 - 2, requestHeight);

      // Tokens bar (light green)
      const tokenHeight = (item.tokens / maxTokens) * chartHeight;
      ctx.fillStyle = '#8FD400';
      ctx.fillRect(x + barWidth / 2, padding + chartHeight - tokenHeight, barWidth / 2 - 2, tokenHeight);

      // Model label
      ctx.fillStyle = '#B0B0B0';
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(
        item.model.substring(0, 15) + (item.model.length > 15 ? '...' : ''),
        x + barWidth / 2,
        padding + chartHeight + 20
      );
    });

    // Draw Y-axis labels
    ctx.fillStyle = '#B0B0B0';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'right';
    for (let i = 0; i <= 5; i++) {
      const value = (maxRequests / 5) * (5 - i);
      const y = padding + (chartHeight / 5) * i;
      ctx.fillText(value.toFixed(0), padding - 10, y + 5);
    }

    // Draw title
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Model Usage Distribution', padding, padding - 30);

    // Draw legend
    ctx.fillStyle = '#76B900';
    ctx.fillRect(padding, padding - 20, 15, 10);
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '12px sans-serif';
    ctx.fillText('Requests', padding + 20, padding - 11);

    ctx.fillStyle = '#8FD400';
    ctx.fillRect(padding + 100, padding - 20, 15, 10);
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText('Tokens', padding + 120, padding - 11);

  }, [data, isLoading]);

  if (isLoading) {
    return (
      <div className="chart-container">
        <div className="chart-header">
          <div>
            <h3 className="chart-title">Model Usage Distribution</h3>
            <p className="chart-subtitle">Loading chart data...</p>
          </div>
        </div>
        <div className="chart-canvas" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="loading-spinner" />
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="chart-container">
        <div className="chart-header">
          <div>
            <h3 className="chart-title">Model Usage Distribution</h3>
            <p className="chart-subtitle">No data available</p>
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <p className="empty-state-text">No model usage data to display</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chart-container">
      <div className="chart-header">
        <div>
          <h3 className="chart-title">Model Usage Distribution</h3>
          <p className="chart-subtitle">Requests and token usage by model</p>
        </div>
      </div>
      <canvas ref={canvasRef} className="chart-canvas" />
    </div>
  );
};
