/**
 * Response Time Chart Component
 * Displays average response time by model with trend visualization
 */

import React from 'react';
import { ModelStats } from '../types';

interface ResponseTimeChartProps {
  modelStats: Record<string, ModelStats>;
}

export const ResponseTimeChart: React.FC<ResponseTimeChartProps> = ({ modelStats }) => {
  const chartData = React.useMemo(() => {
    return Object.entries(modelStats)
      .map(([model, stats]) => ({
        model,
        avgLatency: stats.avg_latency_ms,
        p50: stats.latency_percentiles.p50,
        p90: stats.latency_percentiles.p90,
        p95: stats.latency_percentiles.p95,
        p99: stats.latency_percentiles.p99,
        requestCount: stats.request_count,
      }))
      .sort((a, b) => b.requestCount - a.requestCount)
      .slice(0, 10);
  }, [modelStats]);

  const maxLatency = Math.max(...chartData.map(d => d.p99));

  return (
    <div className="response-time-chart-container">
      <h3 className="section-title">Response Time by Model</h3>

      <div className="chart-content">
        <div className="latency-chart">
          {chartData.map((data, index) => {
            const avgHeight = (data.avgLatency / maxLatency) * 100;
            const p50Height = (data.p50 / maxLatency) * 100;
            const p90Height = (data.p90 / maxLatency) * 100;
            const p95Height = (data.p95 / maxLatency) * 100;
            const p99Height = (data.p99 / maxLatency) * 100;

            return (
              <div key={data.model} className="latency-bar-group">
                <div className="latency-bars">
                  <div
                    className="latency-bar p99"
                    style={{ height: `${p99Height}%` }}
                    title={`P99: ${data.p99.toFixed(1)}ms`}
                  ></div>
                  <div
                    className="latency-bar p95"
                    style={{ height: `${p95Height}%` }}
                    title={`P95: ${data.p95.toFixed(1)}ms`}
                  ></div>
                  <div
                    className="latency-bar p90"
                    style={{ height: `${p90Height}%` }}
                    title={`P90: ${data.p90.toFixed(1)}ms`}
                  ></div>
                  <div
                    className="latency-bar p50"
                    style={{ height: `${p50Height}%` }}
                    title={`P50: ${data.p50.toFixed(1)}ms`}
                  ></div>
                  <div
                    className="latency-bar avg"
                    style={{ height: `${avgHeight}%` }}
                    title={`Avg: ${data.avgLatency.toFixed(1)}ms`}
                  >
                    <span className="bar-label">{data.avgLatency.toFixed(0)}</span>
                  </div>
                </div>
                <div className="bar-group-label" title={data.model}>
                  {data.model.length > 20 ? data.model.substring(0, 17) + '...' : data.model}
                </div>
              </div>
            );
          })}
        </div>

        <div className="chart-legend-horizontal">
          <div className="legend-item">
            <div className="legend-indicator avg"></div>
            <span>Average</span>
          </div>
          <div className="legend-item">
            <div className="legend-indicator p50"></div>
            <span>P50</span>
          </div>
          <div className="legend-item">
            <div className="legend-indicator p90"></div>
            <span>P90</span>
          </div>
          <div className="legend-item">
            <div className="legend-indicator p95"></div>
            <span>P95</span>
          </div>
          <div className="legend-item">
            <div className="legend-indicator p99"></div>
            <span>P99</span>
          </div>
        </div>
      </div>

      <div className="latency-summary">
        <div className="summary-card">
          <div className="summary-title">Fastest Model</div>
          <div className="summary-value">
            {chartData.length > 0 && chartData.reduce((min, curr) =>
              curr.avgLatency < min.avgLatency ? curr : min
            ).model}
          </div>
          <div className="summary-detail">
            {chartData.length > 0 && chartData.reduce((min, curr) =>
              curr.avgLatency < min.avgLatency ? curr : min
            ).avgLatency.toFixed(1)}ms avg
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-title">Slowest Model</div>
          <div className="summary-value">
            {chartData.length > 0 && chartData.reduce((max, curr) =>
              curr.avgLatency > max.avgLatency ? curr : max
            ).model}
          </div>
          <div className="summary-detail">
            {chartData.length > 0 && chartData.reduce((max, curr) =>
              curr.avgLatency > max.avgLatency ? curr : max
            ).avgLatency.toFixed(1)}ms avg
          </div>
        </div>

        <div className="summary-card">
          <div className="summary-title">Overall P95</div>
          <div className="summary-value">
            {chartData.length > 0 && (
              chartData.reduce((sum, d) => sum + d.p95, 0) / chartData.length
            ).toFixed(1)}ms
          </div>
          <div className="summary-detail">Across all models</div>
        </div>
      </div>
    </div>
  );
};
