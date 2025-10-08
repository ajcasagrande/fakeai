/**
 * Token Consumption Component
 * Tracks and visualizes token usage patterns
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useRef } from 'react';
import { UsageTrendPoint } from '../types';

interface TokenConsumptionProps {
  data: UsageTrendPoint[];
  isLoading?: boolean;
}

export const TokenConsumption: React.FC<TokenConsumptionProps> = ({ data, isLoading }) => {
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

    // Find max value
    const maxTokens = Math.max(...data.map(d => d.tokens));
    const minTime = Math.min(...data.map(d => d.timestamp));
    const maxTime = Math.max(...data.map(d => d.timestamp));

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

    // Draw line chart
    ctx.strokeStyle = '#76B900';
    ctx.lineWidth = 3;
    ctx.beginPath();

    data.forEach((point, index) => {
      const x = padding + ((point.timestamp - minTime) / (maxTime - minTime)) * chartWidth;
      const y = padding + chartHeight - (point.tokens / maxTokens) * chartHeight;

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    // Draw area fill
    ctx.fillStyle = 'rgba(118, 185, 0, 0.2)';
    ctx.beginPath();
    data.forEach((point, index) => {
      const x = padding + ((point.timestamp - minTime) / (maxTime - minTime)) * chartWidth;
      const y = padding + chartHeight - (point.tokens / maxTokens) * chartHeight;

      if (index === 0) {
        ctx.moveTo(x, padding + chartHeight);
        ctx.lineTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.lineTo(padding + chartWidth, padding + chartHeight);
    ctx.closePath();
    ctx.fill();

    // Draw points
    ctx.fillStyle = '#76B900';
    data.forEach((point) => {
      const x = padding + ((point.timestamp - minTime) / (maxTime - minTime)) * chartWidth;
      const y = padding + chartHeight - (point.tokens / maxTokens) * chartHeight;

      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fill();
    });

    // Draw Y-axis labels
    ctx.fillStyle = '#B0B0B0';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'right';
    for (let i = 0; i <= 5; i++) {
      const value = (maxTokens / 5) * (5 - i);
      const y = padding + (chartHeight / 5) * i;
      const label = value >= 1000 ? `${(value / 1000).toFixed(1)}K` : value.toFixed(0);
      ctx.fillText(label, padding - 10, y + 5);
    }

    // Draw X-axis labels (time)
    ctx.textAlign = 'center';
    const numLabels = 5;
    for (let i = 0; i <= numLabels; i++) {
      const timestamp = minTime + ((maxTime - minTime) / numLabels) * i;
      const x = padding + (chartWidth / numLabels) * i;
      const date = new Date(timestamp * 1000);
      const label = `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
      ctx.fillText(label, x, padding + chartHeight + 20);
    }

    // Draw title
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Token Consumption Over Time', padding, padding - 30);

    // Draw Y-axis label
    ctx.save();
    ctx.translate(20, padding + chartHeight / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillStyle = '#B0B0B0';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Tokens', 0, 0);
    ctx.restore();

  }, [data, isLoading]);

  if (isLoading) {
    return (
      <div className="chart-container">
        <div className="chart-header">
          <div>
            <h3 className="chart-title">Token Consumption</h3>
            <p className="chart-subtitle">Loading consumption data...</p>
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
            <h3 className="chart-title">Token Consumption</h3>
            <p className="chart-subtitle">No data available</p>
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">📈</div>
          <p className="empty-state-text">No token consumption data to display</p>
        </div>
      </div>
    );
  }

  // Calculate totals for display
  const totalTokens = data.reduce((sum, point) => sum + point.tokens, 0);
  const avgTokens = totalTokens / data.length;

  return (
    <div className="chart-container">
      <div className="chart-header">
        <div>
          <h3 className="chart-title">Token Consumption</h3>
          <p className="chart-subtitle">
            Total: {totalTokens.toLocaleString()} tokens | Avg: {avgTokens.toFixed(0)} tokens/bucket
          </p>
        </div>
      </div>
      <canvas ref={canvasRef} className="chart-canvas" />
    </div>
  );
};
