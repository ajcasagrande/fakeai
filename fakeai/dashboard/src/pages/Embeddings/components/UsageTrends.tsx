/**
 * Usage Trends Component
 * Displays usage trends over time with multiple metrics
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useRef } from 'react';
import { UsageTrendPoint } from '../types';

interface UsageTrendsProps {
  data: UsageTrendPoint[];
  isLoading?: boolean;
}

export const UsageTrends: React.FC<UsageTrendsProps> = ({ data, isLoading }) => {
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

    // Normalize data for dual-axis
    const maxRequests = Math.max(...data.map(d => d.requests));
    const maxProcessingTime = Math.max(...data.map(d => d.avg_processing_time));
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

    // Draw requests line (green)
    ctx.strokeStyle = '#76B900';
    ctx.lineWidth = 3;
    ctx.beginPath();

    data.forEach((point, index) => {
      const x = padding + ((point.timestamp - minTime) / (maxTime - minTime)) * chartWidth;
      const y = padding + chartHeight - (point.requests / maxRequests) * chartHeight;

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    // Draw processing time line (blue)
    ctx.strokeStyle = '#00B0FF';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();

    data.forEach((point, index) => {
      const x = padding + ((point.timestamp - minTime) / (maxTime - minTime)) * chartWidth;
      const y = padding + chartHeight - (point.avg_processing_time / maxProcessingTime) * chartHeight;

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();
    ctx.setLineDash([]);

    // Draw points for requests
    ctx.fillStyle = '#76B900';
    data.forEach((point) => {
      const x = padding + ((point.timestamp - minTime) / (maxTime - minTime)) * chartWidth;
      const y = padding + chartHeight - (point.requests / maxRequests) * chartHeight;

      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fill();
    });

    // Draw points for processing time
    ctx.fillStyle = '#00B0FF';
    data.forEach((point) => {
      const x = padding + ((point.timestamp - minTime) / (maxTime - minTime)) * chartWidth;
      const y = padding + chartHeight - (point.avg_processing_time / maxProcessingTime) * chartHeight;

      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    });

    // Draw Y-axis labels (requests)
    ctx.fillStyle = '#76B900';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'right';
    for (let i = 0; i <= 5; i++) {
      const value = (maxRequests / 5) * (5 - i);
      const y = padding + (chartHeight / 5) * i;
      ctx.fillText(value.toFixed(0), padding - 10, y + 5);
    }

    // Draw Y-axis labels (processing time) on right side
    ctx.fillStyle = '#00B0FF';
    ctx.textAlign = 'left';
    for (let i = 0; i <= 5; i++) {
      const value = (maxProcessingTime / 5) * (5 - i);
      const y = padding + (chartHeight / 5) * i;
      ctx.fillText(`${value.toFixed(0)}ms`, padding + chartWidth + 10, y + 5);
    }

    // Draw X-axis labels (time)
    ctx.fillStyle = '#B0B0B0';
    ctx.textAlign = 'center';
    const numLabels = 6;
    for (let i = 0; i <= numLabels; i++) {
      const timestamp = minTime + ((maxTime - minTime) / numLabels) * i;
      const x = padding + (chartWidth / numLabels) * i;
      const date = new Date(timestamp * 1000);
      const label = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      ctx.fillText(label, x, padding + chartHeight + 20);
    }

    // Draw title
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Usage Trends Over Time', padding, padding - 30);

    // Draw legend
    ctx.fillStyle = '#76B900';
    ctx.fillRect(padding, padding - 20, 15, 3);
    ctx.fillStyle = '#76B900';
    ctx.font = '12px sans-serif';
    ctx.fillText('Requests', padding + 20, padding - 14);

    ctx.strokeStyle = '#00B0FF';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(padding + 100, padding - 18);
    ctx.lineTo(padding + 115, padding - 18);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#00B0FF';
    ctx.fillText('Avg Processing Time', padding + 120, padding - 14);

  }, [data, isLoading]);

  if (isLoading) {
    return (
      <div className="chart-container">
        <div className="chart-header">
          <div>
            <h3 className="chart-title">Usage Trends</h3>
            <p className="chart-subtitle">Loading trend data...</p>
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
            <h3 className="chart-title">Usage Trends</h3>
            <p className="chart-subtitle">No data available</p>
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">📉</div>
          <p className="empty-state-text">No usage trend data to display</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chart-container">
      <div className="chart-header">
        <div>
          <h3 className="chart-title">Usage Trends</h3>
          <p className="chart-subtitle">Requests and processing time trends</p>
        </div>
      </div>
      <canvas ref={canvasRef} className="chart-canvas" />
    </div>
  );
};
