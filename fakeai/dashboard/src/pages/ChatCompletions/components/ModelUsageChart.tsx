/**
 * Model Usage Chart Component
 * Displays model usage distribution with pie and bar charts
 */

import React, { useMemo } from 'react';
import { ModelStats } from '../types';

interface ModelUsageChartProps {
  modelStats: Record<string, ModelStats>;
  chartType: 'pie' | 'bar';
}

export const ModelUsageChart: React.FC<ModelUsageChartProps> = ({ modelStats, chartType }) => {
  const modelUsageData = useMemo(() => {
    const total = Object.values(modelStats).reduce(
      (sum, stats) => sum + stats.request_count,
      0
    );

    const nvidiaColors = [
      '#76B900', // NVIDIA Green
      '#1A1A1A', // Dark Gray
      '#00A9E0', // Cyan
      '#FF6B00', // Orange
      '#9D5CC9', // Purple
      '#FFD700', // Gold
      '#00CED1', // Dark Turquoise
      '#FF69B4', // Hot Pink
    ];

    return Object.entries(modelStats)
      .map(([model, stats], index) => ({
        model,
        requests: stats.request_count,
        percentage: (stats.request_count / total) * 100,
        color: nvidiaColors[index % nvidiaColors.length],
      }))
      .sort((a, b) => b.requests - a.requests);
  }, [modelStats]);

  if (chartType === 'pie') {
    return <PieChart data={modelUsageData} />;
  }

  return <BarChart data={modelUsageData} />;
};

const PieChart: React.FC<{ data: any[] }> = ({ data }) => {
  const total = data.reduce((sum, d) => sum + d.requests, 0);

  // Calculate SVG path for pie slices
  const generatePiePath = (percentage: number, startAngle: number): string => {
    const angle = (percentage / 100) * 360;
    const endAngle = startAngle + angle;

    const startRadians = (startAngle - 90) * (Math.PI / 180);
    const endRadians = (endAngle - 90) * (Math.PI / 180);

    const x1 = 50 + 40 * Math.cos(startRadians);
    const y1 = 50 + 40 * Math.sin(startRadians);
    const x2 = 50 + 40 * Math.cos(endRadians);
    const y2 = 50 + 40 * Math.sin(endRadians);

    const largeArc = angle > 180 ? 1 : 0;

    return `M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2} Z`;
  };

  let currentAngle = 0;

  return (
    <div className="chart-container pie-chart">
      <svg viewBox="0 0 100 100" className="pie-svg">
        {data.map((item, index) => {
          const path = generatePiePath(item.percentage, currentAngle);
          currentAngle += (item.percentage / 100) * 360;

          return (
            <g key={item.model}>
              <path
                d={path}
                fill={item.color}
                stroke="#fff"
                strokeWidth="0.5"
                className="pie-slice"
              >
                <title>{`${item.model}: ${item.requests} (${item.percentage.toFixed(1)}%)`}</title>
              </path>
            </g>
          );
        })}
      </svg>

      <div className="chart-legend">
        {data.map((item) => (
          <div key={item.model} className="legend-item">
            <div className="legend-color" style={{ backgroundColor: item.color }}></div>
            <div className="legend-label">
              <span className="legend-model">{item.model}</span>
              <span className="legend-stats">
                {item.requests} ({item.percentage.toFixed(1)}%)
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const BarChart: React.FC<{ data: any[] }> = ({ data }) => {
  const maxRequests = Math.max(...data.map(d => d.requests));

  return (
    <div className="chart-container bar-chart">
      <div className="bar-chart-content">
        {data.map((item) => (
          <div key={item.model} className="bar-item">
            <div className="bar-label">{item.model}</div>
            <div className="bar-wrapper">
              <div
                className="bar-fill"
                style={{
                  width: `${(item.requests / maxRequests) * 100}%`,
                  backgroundColor: item.color,
                }}
              >
                <span className="bar-value">{item.requests}</span>
              </div>
            </div>
            <div className="bar-percentage">{item.percentage.toFixed(1)}%</div>
          </div>
        ))}
      </div>
    </div>
  );
};
