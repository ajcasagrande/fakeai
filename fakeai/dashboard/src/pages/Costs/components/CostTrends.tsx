/**
 * Cost Trends Component
 * Displays daily/weekly/monthly cost trends with line chart
 */

import React, { useState } from 'react';
import { DailyCost } from '../types';

interface CostTrendsProps {
  dailyCosts: DailyCost[];
  loading: boolean;
}

export const CostTrends: React.FC<CostTrendsProps> = ({ dailyCosts, loading }) => {
  const [viewMode, setViewMode] = useState<'daily' | 'weekly' | 'monthly'>('daily');
  const [hoveredPoint, setHoveredPoint] = useState<number | null>(null);

  const formatCost = (cost: number): string => {
    if (cost >= 1) return `$${cost.toFixed(2)}`;
    if (cost >= 0.01) return `$${cost.toFixed(4)}`;
    return `$${cost.toFixed(6)}`;
  };

  const aggregateData = (data: DailyCost[], mode: 'daily' | 'weekly' | 'monthly') => {
    if (mode === 'daily') return data;

    const aggregated: DailyCost[] = [];
    if (mode === 'weekly') {
      for (let i = 0; i < data.length; i += 7) {
        const week = data.slice(i, i + 7);
        aggregated.push({
          date: week[0].date,
          timestamp: week[0].timestamp,
          total_cost: week.reduce((sum, d) => sum + d.total_cost, 0),
          costs_by_service: {},
          request_count: week.reduce((sum, d) => sum + d.request_count, 0),
        });
      }
    } else if (mode === 'monthly') {
      const months = new Map<string, DailyCost[]>();
      data.forEach(day => {
        const month = day.date.substring(0, 7);
        if (!months.has(month)) months.set(month, []);
        months.get(month)!.push(day);
      });
      months.forEach((days, month) => {
        aggregated.push({
          date: month,
          timestamp: days[0].timestamp,
          total_cost: days.reduce((sum, d) => sum + d.total_cost, 0),
          costs_by_service: {},
          request_count: days.reduce((sum, d) => sum + d.request_count, 0),
        });
      });
    }
    return aggregated;
  };

  if (loading) {
    return (
      <div className="cost-trends-container">
        <div className="skeleton-chart"></div>
      </div>
    );
  }

  if (!dailyCosts || dailyCosts.length === 0) {
    return (
      <div className="cost-trends-container">
        <p className="no-data">No cost trend data available</p>
      </div>
    );
  }

  const data = aggregateData(dailyCosts, viewMode);
  const maxCost = Math.max(...data.map(d => d.total_cost));
  const minCost = Math.min(...data.map(d => d.total_cost));

  // SVG chart dimensions
  const width = 800;
  const height = 300;
  const padding = { top: 20, right: 20, bottom: 40, left: 60 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Create line path
  const points = data.map((d, i) => {
    const x = padding.left + (i / (data.length - 1)) * chartWidth;
    const y = padding.top + chartHeight - ((d.total_cost - minCost) / (maxCost - minCost)) * chartHeight;
    return { x, y, cost: d.total_cost, date: d.date };
  });

  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${height - padding.bottom} L ${padding.left} ${height - padding.bottom} Z`;

  return (
    <div className="cost-trends-container">
      <div className="trends-header">
        <h3 className="section-title">Cost Trends</h3>
        <div className="view-mode-toggle">
          <button
            className={`toggle-btn ${viewMode === 'daily' ? 'active' : ''}`}
            onClick={() => setViewMode('daily')}
          >
            Daily
          </button>
          <button
            className={`toggle-btn ${viewMode === 'weekly' ? 'active' : ''}`}
            onClick={() => setViewMode('weekly')}
          >
            Weekly
          </button>
          <button
            className={`toggle-btn ${viewMode === 'monthly' ? 'active' : ''}`}
            onClick={() => setViewMode('monthly')}
          >
            Monthly
          </button>
        </div>
      </div>

      <div className="chart-area">
        <svg viewBox={`0 0 ${width} ${height}`} className="trend-chart">
          {/* Grid lines */}
          <g className="grid-lines">
            {[0, 0.25, 0.5, 0.75, 1].map((percent, i) => {
              const y = padding.top + chartHeight * (1 - percent);
              const value = minCost + (maxCost - minCost) * percent;
              return (
                <g key={i}>
                  <line
                    x1={padding.left}
                    y1={y}
                    x2={width - padding.right}
                    y2={y}
                    stroke="#333"
                    strokeDasharray="4"
                    opacity="0.5"
                  />
                  <text x={padding.left - 10} y={y + 4} textAnchor="end" fill="#999" fontSize="12">
                    {formatCost(value)}
                  </text>
                </g>
              );
            })}
          </g>

          {/* Area fill */}
          <path d={areaPath} fill="url(#areaGradient)" opacity="0.3" />

          {/* Line */}
          <path
            d={linePath}
            fill="none"
            stroke="#76B900"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Points */}
          {points.map((point, i) => (
            <circle
              key={i}
              cx={point.x}
              cy={point.y}
              r={hoveredPoint === i ? 6 : 4}
              fill="#76B900"
              stroke="#000"
              strokeWidth="2"
              className="chart-point"
              onMouseEnter={() => setHoveredPoint(i)}
              onMouseLeave={() => setHoveredPoint(null)}
            />
          ))}

          {/* X-axis labels */}
          <g className="x-axis-labels">
            {points.map((point, i) => {
              if (i % Math.ceil(points.length / 7) !== 0 && i !== points.length - 1) return null;
              return (
                <text
                  key={i}
                  x={point.x}
                  y={height - padding.bottom + 20}
                  textAnchor="middle"
                  fill="#999"
                  fontSize="11"
                >
                  {new Date(data[i].date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </text>
              );
            })}
          </g>

          {/* Gradient definition */}
          <defs>
            <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#76B900" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#76B900" stopOpacity="0.1" />
            </linearGradient>
          </defs>
        </svg>

        {/* Tooltip */}
        {hoveredPoint !== null && (
          <div
            className="chart-tooltip"
            style={{
              left: `${(points[hoveredPoint].x / width) * 100}%`,
              top: `${(points[hoveredPoint].y / height) * 100}%`,
            }}
          >
            <div className="tooltip-date">{data[hoveredPoint].date}</div>
            <div className="tooltip-cost">{formatCost(data[hoveredPoint].total_cost)}</div>
            <div className="tooltip-requests">{data[hoveredPoint].request_count.toLocaleString()} requests</div>
          </div>
        )}
      </div>

      <div className="trends-summary">
        <div className="summary-item">
          <span className="summary-label">Average {viewMode} cost:</span>
          <span className="summary-value">{formatCost(data.reduce((sum, d) => sum + d.total_cost, 0) / data.length)}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Peak cost:</span>
          <span className="summary-value">{formatCost(maxCost)}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Lowest cost:</span>
          <span className="summary-value">{formatCost(minCost)}</span>
        </div>
      </div>
    </div>
  );
};
