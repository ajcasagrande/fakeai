/**
 * Error Rate Chart Component
 * Displays error rates and tracking across models
 */

import React from 'react';
import { ModelStats } from '../types';

interface ErrorRateChartProps {
  modelStats: Record<string, ModelStats>;
}

export const ErrorRateChart: React.FC<ErrorRateChartProps> = ({ modelStats }) => {
  const errorData = React.useMemo(() => {
    return Object.entries(modelStats)
      .map(([model, stats]) => ({
        model,
        errorRate: stats.error_rate,
        errorCount: stats.error_count,
        totalRequests: stats.request_count,
        successRate: 100 - stats.error_rate,
      }))
      .sort((a, b) => b.errorRate - a.errorRate);
  }, [modelStats]);

  const overallErrorRate =
    errorData.reduce((sum, d) => sum + d.errorCount, 0) /
    Math.max(errorData.reduce((sum, d) => sum + d.totalRequests, 0), 1) *
    100;

  const getStatusClass = (errorRate: number): string => {
    if (errorRate === 0) return 'success';
    if (errorRate < 1) return 'warning';
    if (errorRate < 5) return 'error';
    return 'critical';
  };

  const modelsWithErrors = errorData.filter(d => d.errorCount > 0);
  const healthyModels = errorData.filter(d => d.errorCount === 0);

  return (
    <div className="error-rate-chart-container">
      <h3 className="section-title">Error Rate Tracking</h3>

      <div className="error-overview">
        <div className={`error-overview-card ${getStatusClass(overallErrorRate)}`}>
          <div className="overview-icon">
            {overallErrorRate === 0 ? (
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ) : overallErrorRate < 5 ? (
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            ) : (
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
          </div>
          <div className="overview-content">
            <div className="overview-label">Overall Error Rate</div>
            <div className="overview-value">{overallErrorRate.toFixed(2)}%</div>
            <div className="overview-detail">
              {errorData.reduce((sum, d) => sum + d.errorCount, 0)} errors out of{' '}
              {errorData.reduce((sum, d) => sum + d.totalRequests, 0)} requests
            </div>
          </div>
        </div>

        <div className="error-stats-grid">
          <div className="error-stat">
            <div className="stat-value success">{healthyModels.length}</div>
            <div className="stat-label">Healthy Models</div>
          </div>
          <div className="error-stat">
            <div className="stat-value warning">{modelsWithErrors.length}</div>
            <div className="stat-label">Models with Errors</div>
          </div>
          <div className="error-stat">
            <div className="stat-value error">
              {modelsWithErrors.filter(d => d.errorRate >= 5).length}
            </div>
            <div className="stat-label">Critical Models</div>
          </div>
        </div>
      </div>

      {modelsWithErrors.length > 0 && (
        <div className="error-models-list">
          <h4 className="subsection-title">Models with Errors</h4>
          <div className="error-table">
            <table>
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Error Rate</th>
                  <th>Errors</th>
                  <th>Total Requests</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {modelsWithErrors.map((data) => (
                  <tr key={data.model} className={getStatusClass(data.errorRate)}>
                    <td className="model-name">{data.model}</td>
                    <td className="error-rate">
                      <div className="rate-bar-container">
                        <div
                          className={`rate-bar ${getStatusClass(data.errorRate)}`}
                          style={{ width: `${Math.min(data.errorRate, 100)}%` }}
                        ></div>
                        <span className="rate-text">{data.errorRate.toFixed(2)}%</span>
                      </div>
                    </td>
                    <td className="error-count">{data.errorCount}</td>
                    <td className="total-requests">{data.totalRequests}</td>
                    <td>
                      <span className={`status-badge ${getStatusClass(data.errorRate)}`}>
                        {data.errorRate === 0
                          ? 'Healthy'
                          : data.errorRate < 1
                          ? 'Good'
                          : data.errorRate < 5
                          ? 'Warning'
                          : 'Critical'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {healthyModels.length > 0 && (
        <div className="healthy-models">
          <h4 className="subsection-title">Healthy Models (0% Error Rate)</h4>
          <div className="healthy-models-grid">
            {healthyModels.map((data) => (
              <div key={data.model} className="healthy-model-card">
                <div className="healthy-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div className="healthy-model-info">
                  <div className="model-name">{data.model}</div>
                  <div className="model-requests">{data.totalRequests} requests</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
