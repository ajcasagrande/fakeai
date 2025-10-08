/**
 * Service Breakdown Component
 * Displays cost breakdown by service with pie/donut chart
 */

import React, { useState } from 'react';
import { ServiceCost } from '../types';

interface ServiceBreakdownProps {
  services: ServiceCost[];
  loading: boolean;
}

const SERVICE_ICONS: Record<string, string> = {
  chat: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
  embeddings: 'M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4',
  images: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z',
  audio: 'M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z',
  'fine-tuning': 'M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4',
  assistants: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
  batch: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10',
  other: 'M12 6v6m0 0v6m0-6h6m-6 0H6',
};

const SERVICE_COLORS = [
  '#76B900', // NVIDIA Green
  '#00FFFF', // Cyan
  '#9D00FF', // Purple
  '#FFA500', // Orange
  '#0080FF', // Blue
  '#00CC99', // Teal
  '#FF3388', // Pink
  '#FFD700', // Gold
];

export const ServiceBreakdown: React.FC<ServiceBreakdownProps> = ({ services, loading }) => {
  const [chartType, setChartType] = useState<'pie' | 'donut'>('donut');
  const [hoveredService, setHoveredService] = useState<string | null>(null);

  const formatCost = (cost: number): string => {
    if (cost >= 1) return `$${cost.toFixed(2)}`;
    if (cost >= 0.01) return `$${cost.toFixed(4)}`;
    return `$${cost.toFixed(6)}`;
  };

  if (loading) {
    return (
      <div className="service-breakdown-container">
        <div className="skeleton-chart"></div>
        <div className="skeleton-legend"></div>
      </div>
    );
  }

  if (!services || services.length === 0) {
    return (
      <div className="service-breakdown-container">
        <p className="no-data">No service data available</p>
      </div>
    );
  }

  const totalCost = services.reduce((sum, s) => sum + s.total_cost, 0);

  // Calculate SVG pie chart
  const createPieChart = () => {
    const size = 200;
    const center = size / 2;
    const radius = chartType === 'donut' ? 70 : 80;
    const innerRadius = chartType === 'donut' ? 40 : 0;

    let currentAngle = -90;
    const slices = services.map((service, index) => {
      const percentage = (service.total_cost / totalCost) * 100;
      const angle = (percentage / 100) * 360;
      const startAngle = currentAngle;
      const endAngle = currentAngle + angle;

      currentAngle = endAngle;

      const x1 = center + radius * Math.cos((startAngle * Math.PI) / 180);
      const y1 = center + radius * Math.sin((startAngle * Math.PI) / 180);
      const x2 = center + radius * Math.cos((endAngle * Math.PI) / 180);
      const y2 = center + radius * Math.sin((endAngle * Math.PI) / 180);

      const largeArc = angle > 180 ? 1 : 0;

      let path: string;
      if (chartType === 'donut') {
        const innerX1 = center + innerRadius * Math.cos((startAngle * Math.PI) / 180);
        const innerY1 = center + innerRadius * Math.sin((startAngle * Math.PI) / 180);
        const innerX2 = center + innerRadius * Math.cos((endAngle * Math.PI) / 180);
        const innerY2 = center + innerRadius * Math.sin((endAngle * Math.PI) / 180);

        path = `
          M ${x1} ${y1}
          A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}
          L ${innerX2} ${innerY2}
          A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${innerX1} ${innerY1}
          Z
        `;
      } else {
        path = `
          M ${center} ${center}
          L ${x1} ${y1}
          A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}
          Z
        `;
      }

      return {
        path,
        color: SERVICE_COLORS[index % SERVICE_COLORS.length],
        service: service.service,
        percentage,
      };
    });

    return slices;
  };

  const slices = createPieChart();

  return (
    <div className="service-breakdown-container">
      <div className="breakdown-header">
        <h3 className="section-title">Cost by Service</h3>
        <div className="chart-type-toggle">
          <button
            className={`toggle-btn ${chartType === 'pie' ? 'active' : ''}`}
            onClick={() => setChartType('pie')}
          >
            Pie
          </button>
          <button
            className={`toggle-btn ${chartType === 'donut' ? 'active' : ''}`}
            onClick={() => setChartType('donut')}
          >
            Donut
          </button>
        </div>
      </div>

      <div className="breakdown-content">
        <div className="chart-container">
          <svg viewBox="0 0 200 200" className="pie-chart">
            {slices.map((slice, index) => (
              <path
                key={index}
                d={slice.path}
                fill={slice.color}
                className={`pie-slice ${hoveredService === slice.service ? 'hovered' : ''}`}
                onMouseEnter={() => setHoveredService(slice.service)}
                onMouseLeave={() => setHoveredService(null)}
              />
            ))}
          </svg>
          {chartType === 'donut' && (
            <div className="donut-center">
              <div className="donut-label">Total</div>
              <div className="donut-value">{formatCost(totalCost)}</div>
            </div>
          )}
        </div>

        <div className="service-legend">
          {services.map((service, index) => {
            const color = SERVICE_COLORS[index % SERVICE_COLORS.length];
            const iconPath = SERVICE_ICONS[service.service] || SERVICE_ICONS.other;
            const isHovered = hoveredService === service.service;

            return (
              <div
                key={service.service}
                className={`legend-item ${isHovered ? 'hovered' : ''}`}
                onMouseEnter={() => setHoveredService(service.service)}
                onMouseLeave={() => setHoveredService(null)}
              >
                <div className="legend-indicator">
                  <div className="color-dot" style={{ backgroundColor: color }}></div>
                  <div className="service-icon" style={{ color }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={iconPath} />
                    </svg>
                  </div>
                </div>
                <div className="legend-content">
                  <div className="legend-header">
                    <span className="service-name">{service.service}</span>
                    <span className="service-cost">{formatCost(service.total_cost)}</span>
                  </div>
                  <div className="legend-details">
                    <span className="service-percentage">{service.percentage.toFixed(1)}%</span>
                    <span className="service-requests">{service.request_count.toLocaleString()} requests</span>
                  </div>
                  <div className="cost-breakdown-bar">
                    <div
                      className="breakdown-segment input"
                      style={{ width: `${(service.cost_breakdown.input_cost / service.total_cost) * 100}%` }}
                      title={`Input: ${formatCost(service.cost_breakdown.input_cost)}`}
                    ></div>
                    <div
                      className="breakdown-segment output"
                      style={{ width: `${(service.cost_breakdown.output_cost / service.total_cost) * 100}%` }}
                      title={`Output: ${formatCost(service.cost_breakdown.output_cost)}`}
                    ></div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
