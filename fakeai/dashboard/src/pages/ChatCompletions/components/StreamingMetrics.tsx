/**
 * Streaming Metrics Component
 * Displays streaming vs non-streaming statistics
 */

import React from 'react';
import { ModelStats } from '../types';

interface StreamingMetricsProps {
  modelStats: Record<string, ModelStats>;
}

export const StreamingMetrics: React.FC<StreamingMetricsProps> = ({ modelStats }) => {
  const aggregateStats = React.useMemo(() => {
    let totalRequests = 0;
    let streamingRequests = 0;
    let nonStreamingRequests = 0;
    let streamingLatency = 0;
    let nonStreamingLatency = 0;

    Object.values(modelStats).forEach((stats) => {
      totalRequests += stats.request_count;
      streamingRequests += stats.streaming_requests;
      nonStreamingRequests += stats.non_streaming_requests;

      // Weighted average for latency
      if (stats.streaming_requests > 0) {
        streamingLatency += stats.avg_latency_ms * stats.streaming_requests;
      }
      if (stats.non_streaming_requests > 0) {
        nonStreamingLatency += stats.avg_latency_ms * stats.non_streaming_requests;
      }
    });

    const avgStreamingLatency = streamingRequests > 0 ? streamingLatency / streamingRequests : 0;
    const avgNonStreamingLatency = nonStreamingRequests > 0 ? nonStreamingLatency / nonStreamingRequests : 0;

    return {
      totalRequests,
      streamingRequests,
      nonStreamingRequests,
      streamingPercentage: (streamingRequests / totalRequests) * 100,
      nonStreamingPercentage: (nonStreamingRequests / totalRequests) * 100,
      avgStreamingLatency,
      avgNonStreamingLatency,
    };
  }, [modelStats]);

  return (
    <div className="streaming-metrics-container">
      <h3 className="section-title">Streaming vs Non-Streaming</h3>

      <div className="streaming-comparison">
        <div className="comparison-bar">
          <div
            className="comparison-segment streaming"
            style={{ width: `${aggregateStats.streamingPercentage}%` }}
          >
            {aggregateStats.streamingPercentage > 10 && (
              <span className="segment-label">
                {aggregateStats.streamingPercentage.toFixed(0)}%
              </span>
            )}
          </div>
          <div
            className="comparison-segment non-streaming"
            style={{ width: `${aggregateStats.nonStreamingPercentage}%` }}
          >
            {aggregateStats.nonStreamingPercentage > 10 && (
              <span className="segment-label">
                {aggregateStats.nonStreamingPercentage.toFixed(0)}%
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="streaming-stats-grid">
        <div className="streaming-stat-card streaming">
          <div className="stat-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div className="stat-content">
            <div className="stat-label">Streaming Requests</div>
            <div className="stat-value">{aggregateStats.streamingRequests.toLocaleString()}</div>
            <div className="stat-detail">
              Avg Latency: {aggregateStats.avgStreamingLatency.toFixed(0)}ms
            </div>
          </div>
        </div>

        <div className="streaming-stat-card non-streaming">
          <div className="stat-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div className="stat-content">
            <div className="stat-label">Non-Streaming Requests</div>
            <div className="stat-value">{aggregateStats.nonStreamingRequests.toLocaleString()}</div>
            <div className="stat-detail">
              Avg Latency: {aggregateStats.avgNonStreamingLatency.toFixed(0)}ms
            </div>
          </div>
        </div>
      </div>

      <div className="streaming-model-breakdown">
        <h4 className="subsection-title">Per-Model Breakdown</h4>
        <div className="model-streaming-table">
          <table>
            <thead>
              <tr>
                <th>Model</th>
                <th>Streaming</th>
                <th>Non-Streaming</th>
                <th>Streaming %</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(modelStats)
                .sort(([, a], [, b]) => b.request_count - a.request_count)
                .slice(0, 5)
                .map(([model, stats]) => {
                  const streamingPct = (stats.streaming_requests / stats.request_count) * 100;
                  return (
                    <tr key={model}>
                      <td className="model-name">{model}</td>
                      <td className="streaming-count">{stats.streaming_requests}</td>
                      <td className="non-streaming-count">{stats.non_streaming_requests}</td>
                      <td>
                        <div className="percentage-bar">
                          <div
                            className="percentage-fill streaming"
                            style={{ width: `${streamingPct}%` }}
                          ></div>
                          <span className="percentage-text">{streamingPct.toFixed(0)}%</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
