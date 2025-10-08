/**
 * Chat Completions Dashboard
 * Main dashboard component for monitoring chat completions
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  fetchModelMetrics,
  fetchCompletionsUsage,
  fetchChatRequests,
} from './api';
import {
  ModelStats,
  ChatRequest,
  DashboardFilters,
  MetricsOverview as MetricsOverviewType,
  TokenBreakdown,
} from './types';
import { MetricsOverview } from './components/MetricsOverview';
import { ModelUsageChart } from './components/ModelUsageChart';
import { TokenStats } from './components/TokenStats';
import { StreamingMetrics } from './components/StreamingMetrics';
import { ResponseTimeChart } from './components/ResponseTimeChart';
import { ErrorRateChart } from './components/ErrorRateChart';
import { RequestsTable } from './components/RequestsTable';
import { RequestDetailsModal } from './components/RequestDetailsModal';
import { FilterPanel } from './components/FilterPanel';
import { CostVisualization } from './components/CostVisualization';
import './styles.css';

export const ChatCompletions: React.FC = () => {
  // State management
  const [modelStats, setModelStats] = useState<Record<string, ModelStats>>({});
  const [requests, setRequests] = useState<ChatRequest[]>([]);
  const [totalRequests, setTotalRequests] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRequest, setSelectedRequest] = useState<ChatRequest | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [chartType, setChartType] = useState<'pie' | 'bar'>('pie');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [filters, setFilters] = useState<DashboardFilters>({
    model: null,
    dateRange: {
      start: null,
      end: null,
    },
    status: 'all',
    streaming: 'all',
  });

  const pageSize = 20;

  // Calculate aggregated metrics
  const metricsOverview: MetricsOverviewType = React.useMemo(() => {
    const stats = Object.values(modelStats);

    const totalRequests = stats.reduce((sum, s) => sum + s.request_count, 0);
    const totalTokens = stats.reduce((sum, s) => sum + s.total_tokens, 0);
    const totalCost = stats.reduce((sum, s) => sum + s.total_cost, 0);
    const totalLatency = stats.reduce((sum, s) => sum + s.total_latency_ms, 0);
    const totalErrors = stats.reduce((sum, s) => sum + s.error_count, 0);
    const totalStreaming = stats.reduce((sum, s) => sum + s.streaming_requests, 0);

    return {
      total_requests: totalRequests,
      total_tokens: totalTokens,
      total_cost: totalCost,
      avg_latency_ms: totalRequests > 0 ? totalLatency / totalRequests : 0,
      error_rate: totalRequests > 0 ? (totalErrors / totalRequests) * 100 : 0,
      streaming_percentage: totalRequests > 0 ? (totalStreaming / totalRequests) * 100 : 0,
      requests_per_second: totalRequests / 3600, // Assuming 1 hour window
    };
  }, [modelStats]);

  const tokenBreakdown: TokenBreakdown = React.useMemo(() => {
    const stats = Object.values(modelStats);

    return {
      prompt_tokens: stats.reduce((sum, s) => sum + s.total_prompt_tokens, 0),
      completion_tokens: stats.reduce((sum, s) => sum + s.total_completion_tokens, 0),
      cached_tokens: 0, // This would come from the API if available
      total_tokens: stats.reduce((sum, s) => sum + s.total_tokens, 0),
    };
  }, [modelStats]);

  const availableModels = React.useMemo(() => {
    return Object.keys(modelStats).sort();
  }, [modelStats]);

  // Fetch data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch model metrics
      const metrics = await fetchModelMetrics();
      setModelStats(metrics);

      // Fetch requests with filters
      const startTime = filters.dateRange.start?.getTime() || undefined;
      const endTime = filters.dateRange.end?.getTime() || undefined;

      const { requests: fetchedRequests, total } = await fetchChatRequests(
        pageSize,
        currentPage * pageSize,
        {
          model: filters.model || undefined,
          status: filters.status !== 'all' ? filters.status : undefined,
          streaming: filters.streaming !== 'all' ? filters.streaming : undefined,
          startTime,
          endTime,
        }
      );

      setRequests(fetchedRequests);
      setTotalRequests(total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, [currentPage, filters]);

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchData();
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh, fetchData]);

  // Handle page change
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  // Handle request click
  const handleRequestClick = (request: ChatRequest) => {
    setSelectedRequest(request);
  };

  // Handle filters change
  const handleFiltersChange = (newFilters: DashboardFilters) => {
    setFilters(newFilters);
    setCurrentPage(0); // Reset to first page when filters change
  };

  return (
    <div className="chat-completions-dashboard">
      <div className="dashboard-header">
        <div className="header-content">
          <h1 className="dashboard-title">Chat Completions Monitoring</h1>
          <p className="dashboard-subtitle">
            Real-time monitoring and analytics for chat completion requests
          </p>
        </div>
        <div className="header-actions">
          <button
            className={`refresh-toggle ${autoRefresh ? 'active' : ''}`}
            onClick={() => setAutoRefresh(!autoRefresh)}
            title={autoRefresh ? 'Disable auto-refresh' : 'Enable auto-refresh'}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          </button>
          <button
            className="manual-refresh-btn"
            onClick={fetchData}
            disabled={loading}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}

      <div className="dashboard-content">
        <div className="main-section">
          <MetricsOverview metrics={metricsOverview} loading={loading} />

          <div className="grid-2-col">
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Model Usage Distribution</h3>
                <div className="chart-type-toggle">
                  <button
                    className={`toggle-btn ${chartType === 'pie' ? 'active' : ''}`}
                    onClick={() => setChartType('pie')}
                  >
                    Pie
                  </button>
                  <button
                    className={`toggle-btn ${chartType === 'bar' ? 'active' : ''}`}
                    onClick={() => setChartType('bar')}
                  >
                    Bar
                  </button>
                </div>
              </div>
              <ModelUsageChart modelStats={modelStats} chartType={chartType} />
            </div>

            <div className="card">
              <TokenStats tokenBreakdown={tokenBreakdown} />
            </div>
          </div>

          <div className="card">
            <StreamingMetrics modelStats={modelStats} />
          </div>

          <div className="grid-2-col">
            <div className="card">
              <ResponseTimeChart modelStats={modelStats} />
            </div>

            <div className="card">
              <ErrorRateChart modelStats={modelStats} />
            </div>
          </div>

          <div className="card">
            <CostVisualization modelStats={modelStats} />
          </div>

          <div className="card">
            <RequestsTable
              requests={requests}
              total={totalRequests}
              page={currentPage}
              pageSize={pageSize}
              onPageChange={handlePageChange}
              onRequestClick={handleRequestClick}
              loading={loading}
            />
          </div>
        </div>

        <div className="sidebar-section">
          <div className="card">
            <FilterPanel
              filters={filters}
              availableModels={availableModels}
              onFiltersChange={handleFiltersChange}
            />
          </div>

          <div className="card info-card">
            <h3 className="card-title">Dashboard Info</h3>
            <div className="info-content">
              <div className="info-item">
                <span className="info-label">Last Updated</span>
                <span className="info-value">{new Date().toLocaleTimeString()}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Total Models</span>
                <span className="info-value">{Object.keys(modelStats).length}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Refresh Rate</span>
                <span className="info-value">{autoRefresh ? '30s' : 'Manual'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <RequestDetailsModal
        request={selectedRequest}
        onClose={() => setSelectedRequest(null)}
      />
    </div>
  );
};

export default ChatCompletions;
