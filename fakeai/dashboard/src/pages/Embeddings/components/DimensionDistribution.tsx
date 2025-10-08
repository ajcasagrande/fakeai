/**
 * Dimension Distribution Component
 * Visualizes the distribution of embedding dimensions
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useRef } from 'react';
import { DimensionStats } from '../types';

interface DimensionDistributionProps {
  data: DimensionStats[];
  isLoading?: boolean;
}

export const DimensionDistribution: React.FC<DimensionDistributionProps> = ({ data, isLoading }) => {
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
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const radius = Math.min(rect.width, rect.height) / 2 - 80;

    // Color palette
    const colors = [
      '#76B900', '#8FD400', '#5A9100', '#00C853', '#00B0FF',
      '#FFD600', '#FF3D00', '#3D6000', '#00E676', '#0091EA'
    ];

    // Draw pie chart
    let currentAngle = -Math.PI / 2;

    data.forEach((item, index) => {
      const sliceAngle = (item.percentage / 100) * Math.PI * 2;
      const endAngle = currentAngle + sliceAngle;

      // Draw slice
      ctx.fillStyle = colors[index % colors.length];
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, currentAngle, endAngle);
      ctx.closePath();
      ctx.fill();

      // Draw slice border
      ctx.strokeStyle = '#1E1E1E';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Draw label if slice is large enough
      if (item.percentage > 5) {
        const labelAngle = currentAngle + sliceAngle / 2;
        const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7);
        const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7);

        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 12px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(`${item.dimension}`, labelX, labelY - 8);
        ctx.font = '10px sans-serif';
        ctx.fillText(`${item.percentage.toFixed(1)}%`, labelX, labelY + 8);
      }

      currentAngle = endAngle;
    });

    // Draw legend
    const legendX = rect.width - 150;
    const legendY = 40;
    const legendItemHeight = 25;

    ctx.font = 'bold 12px sans-serif';
    ctx.fillStyle = '#FFFFFF';
    ctx.textAlign = 'left';
    ctx.fillText('Dimensions', legendX, legendY - 10);

    data.forEach((item, index) => {
      const y = legendY + index * legendItemHeight;

      // Color box
      ctx.fillStyle = colors[index % colors.length];
      ctx.fillRect(legendX, y, 15, 15);

      // Label
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '11px sans-serif';
      ctx.fillText(
        `${item.dimension}d - ${item.count} (${item.percentage.toFixed(1)}%)`,
        legendX + 20,
        y + 12
      );
    });

    // Draw title
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Embedding Dimensions Distribution', 20, 30);

  }, [data, isLoading]);

  if (isLoading) {
    return (
      <div className="chart-container">
        <div className="chart-header">
          <div>
            <h3 className="chart-title">Dimension Distribution</h3>
            <p className="chart-subtitle">Loading distribution data...</p>
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
            <h3 className="chart-title">Dimension Distribution</h3>
            <p className="chart-subtitle">No data available</p>
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">🥧</div>
          <p className="empty-state-text">No dimension distribution data to display</p>
        </div>
      </div>
    );
  }

  const totalCount = data.reduce((sum, item) => sum + item.count, 0);

  return (
    <div className="chart-container">
      <div className="chart-header">
        <div>
          <h3 className="chart-title">Dimension Distribution</h3>
          <p className="chart-subtitle">Total embeddings: {totalCount.toLocaleString()}</p>
        </div>
      </div>
      <canvas ref={canvasRef} className="chart-canvas" />
    </div>
  );
};
