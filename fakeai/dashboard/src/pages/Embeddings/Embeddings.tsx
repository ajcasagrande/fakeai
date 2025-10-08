/**
 * Embeddings Monitoring Dashboard
 *
 * Comprehensive dashboard for monitoring embedding operations, token usage,
 * model statistics, cost analysis, and performance metrics.
 *
 * Features:
 * 1. Embedding requests visualization
 * 2. Model usage statistics
 * 3. Token consumption tracking
 * 4. Average processing time
 * 5. Batch embedding analytics
 * 6. Dimension distribution charts
 * 7. Recent embeddings table
 * 8. Usage trends over time
 * 9. Cost analysis per model
 * 10. Export embedding logs
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect, useCallback } from 'react';
import './styles.css';
import {
  EmbeddingMetrics,
  ModelUsageStats,
  DimensionStats,
  RecentEmbedding,
  UsageTrendPoint,
  CostBreakdown,
  EmbeddingUsageData,
  ExportOptions,
} from './types';

// Import components
import { EmbeddingStats } from './components/EmbeddingStats';
import { ModelUsageChart } from './components/ModelUsageChart';
import { TokenConsumption } from './components/TokenConsumption';
import { RecentEmbeddingsTable } from './components/RecentEmbeddingsTable';
import { UsageTrends } from './components/UsageTrends';
import { DimensionDistribution } from './components/DimensionDistribution';
import { CostAnalysis } from './components/CostAnalysis';

// Configuration
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
const REFRESH_INTERVAL = 5000; // 5 seconds
const DEFAULT_BUCKET_WIDTH = '1h';

export const EmbeddingsDashboard: React.FC = () => {
  // State
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [timeRange, setTimeRange] = useState('24h');
  const [selectedModel, setSelectedModel] = useState<string>('all');

  // Data state
  const [metrics, setMetrics] = useState<EmbeddingMetrics>({
    total_requests: 0,
    total_tokens: 0,
    avg_processing_time: 0,
    requests_per_second: 0,
    tokens_per_second: 0,
    error_rate: 0,
  });

  const [modelUsage, setModelUsage] = useState<ModelUsageStats[]>([]);
  const [dimensionStats, setDimensionStats] = useState<DimensionStats[]>([]);
  const [recentEmbeddings, setRecentEmbeddings] = useState<RecentEmbedding[]>([]);
  const [usageTrends, setUsageTrends] = useState<UsageTrendPoint[]>([]);
  const [costBreakdown, setCostBreakdown] = useState<CostBreakdown[]>([]);

  // Calculate time range timestamps
  const getTimeRange = useCallback(() => {
    const end = Math.floor(Date.now() / 1000);
    let start = end;

    switch (timeRange) {
      case '1h':
        start = end - 3600;
        break;
      case '6h':
        start = end - 6 * 3600;
        break;
      case '24h':
        start = end - 24 * 3600;
        break;
      case '7d':
        start = end - 7 * 24 * 3600;
        break;
      case '30d':
        start = end - 30 * 24 * 3600;
        break;
      default:
        start = end - 24 * 3600;
    }

    return { start, end };
  }, [timeRange]);

  // Fetch embeddings usage data
  const fetchEmbeddingsData = useCallback(async () => {
    try {
      const { start, end } = getTimeRange();
      const modelParam = selectedModel !== 'all' ? `&model=${selectedModel}` : '';

      // Fetch usage data
      const usageResponse = await fetch(
        `${API_BASE_URL}/v1/organization/usage/embeddings?start_time=${start}&end_time=${end}&bucket_width=${DEFAULT_BUCKET_WIDTH}${modelParam}`
      );
      const usageData: EmbeddingUsageData = await usageResponse.json();

      // Fetch metrics
      const metricsResponse = await fetch(`${API_BASE_URL}/metrics`);
      const metricsData = await metricsResponse.json();

      // Process data
      processUsageData(usageData, metricsData);

      setLastUpdate(new Date());
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching embeddings data:', error);
      setIsLoading(false);
    }
  }, [getTimeRange, selectedModel]);

  // Process usage data into dashboard metrics
  const processUsageData = (usageData: EmbeddingUsageData, metricsData: any) => {
    // Calculate aggregate metrics
    const totalRequests = usageData.data.reduce((sum, bucket) => sum + bucket.num_model_requests, 0);
    const totalTokens = usageData.data.reduce((sum, bucket) => sum + bucket.num_input_tokens, 0);

    // Extract from metrics endpoint
    const embeddingsMetrics = metricsData.responses?.['/v1/embeddings'] || {};
    const avgProcessingTime = (embeddingsMetrics.avg || 0) * 1000; // Convert to ms

    // Calculate rates
    const timeSpan = usageData.data.length > 0
      ? (usageData.data[usageData.data.length - 1].aggregation_timestamp - usageData.data[0].aggregation_timestamp) || 3600
      : 3600;
    const requestsPerSecond = totalRequests / timeSpan;
    const tokensPerSecond = totalTokens / timeSpan;

    setMetrics({
      total_requests: totalRequests,
      total_tokens: totalTokens,
      avg_processing_time: avgProcessingTime,
      requests_per_second: requestsPerSecond,
      tokens_per_second: tokensPerSecond,
      error_rate: (metricsData.errors?.['/v1/embeddings']?.rate || 0) * 100,
    });

    // Process model usage stats
    const modelMap = new Map<string, ModelUsageStats>();
    usageData.data.forEach((bucket) => {
      const model = bucket.model || 'unknown';
      if (!modelMap.has(model)) {
        modelMap.set(model, {
          model,
          requests: 0,
          tokens: 0,
          avg_dimensions: 1536, // Default
          avg_batch_size: 1,
          total_cost: 0,
        });
      }
      const stats = modelMap.get(model)!;
      stats.requests += bucket.num_model_requests;
      stats.tokens += bucket.num_input_tokens;
    });

    // Calculate costs (example rates)
    const costRates: { [key: string]: number } = {
      'text-embedding-ada-002': 0.0001,
      'text-embedding-3-small': 0.00002,
      'text-embedding-3-large': 0.00013,
      'default': 0.00001,
    };

    modelMap.forEach((stats) => {
      const rate = costRates[stats.model] || costRates.default;
      stats.total_cost = (stats.tokens / 1000) * rate;
    });

    setModelUsage(Array.from(modelMap.values()));

    // Generate usage trends
    const trends: UsageTrendPoint[] = usageData.data.map((bucket) => ({
      timestamp: bucket.aggregation_timestamp,
      requests: bucket.num_model_requests,
      tokens: bucket.num_input_tokens,
      avg_processing_time: avgProcessingTime,
    }));
    setUsageTrends(trends);

    // Generate dimension distribution (simulated)
    const dimensions = [256, 512, 768, 1024, 1536, 2048, 3072];
    const dimStats: DimensionStats[] = dimensions.map((dim, index) => {
      const count = Math.floor(totalRequests * (0.5 - index * 0.08));
      return {
        dimension: dim,
        count: Math.max(0, count),
        percentage: 0,
      };
    });
    const totalDimCount = dimStats.reduce((sum, s) => sum + s.count, 0);
    dimStats.forEach(s => s.percentage = totalDimCount > 0 ? (s.count / totalDimCount) * 100 : 0);
    setDimensionStats(dimStats.filter(s => s.count > 0));

    // Generate recent embeddings (simulated)
    const recent: RecentEmbedding[] = usageData.data.slice(-10).map((bucket, index) => ({
      id: `emb-${bucket.snapshot_id}-${index}`,
      timestamp: bucket.aggregation_timestamp,
      model: bucket.model || 'text-embedding-ada-002',
      input_tokens: Math.floor(bucket.num_input_tokens / bucket.num_model_requests) || 100,
      dimensions: 1536,
      batch_size: 1,
      processing_time: avgProcessingTime,
      cost: 0.0001 * (bucket.num_input_tokens / 1000),
      status: 'success',
    }));
    setRecentEmbeddings(recent);

    // Generate cost breakdown
    const costs: CostBreakdown[] = Array.from(modelMap.values()).map((stats) => ({
      model: stats.model,
      total_cost: stats.total_cost,
      total_requests: stats.requests,
      cost_per_request: stats.total_cost / stats.requests,
      cost_per_1k_tokens: (stats.total_cost / stats.tokens) * 1000,
    }));
    setCostBreakdown(costs);
  };

  // Export functionality
  const handleExport = async (format: 'json' | 'csv' | 'excel') => {
    try {
      const { start, end } = getTimeRange();
      const exportData: ExportOptions = {
        format,
        dateRange: { start, end },
        includeMetrics: true,
        includeCosts: true,
      };

      // In a real implementation, this would call an export API endpoint
      console.log('Exporting data:', exportData);

      // For now, create a JSON download
      const dataToExport = {
        metrics,
        modelUsage,
        dimensionStats,
        recentEmbeddings,
        usageTrends,
        costBreakdown,
        exportedAt: new Date().toISOString(),
      };

      const blob = new Blob([JSON.stringify(dataToExport, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `embeddings-export-${Date.now()}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  };

  // Auto-refresh effect
  useEffect(() => {
    fetchEmbeddingsData();

    if (autoRefresh) {
      const interval = setInterval(fetchEmbeddingsData, REFRESH_INTERVAL);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, fetchEmbeddingsData]);

  return (
    <div className="embeddings-dashboard">
      {/* Header */}
      <header className="embeddings-header">
        <h1 className="embeddings-title">Embeddings Monitoring Dashboard</h1>
        <p className="embeddings-subtitle">
          Real-time monitoring of embedding operations, token usage, and performance metrics
        </p>
      </header>

      {/* Control Bar */}
      <div className="control-bar">
        <div className="control-group">
          <label className="control-label">Time Range:</label>
          <select
            className="control-select"
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
          >
            <option value="1h">Last Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>

        <div className="control-group">
          <label className="control-label">Model:</label>
          <select
            className="control-select"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
          >
            <option value="all">All Models</option>
            <option value="text-embedding-ada-002">text-embedding-ada-002</option>
            <option value="text-embedding-3-small">text-embedding-3-small</option>
            <option value="text-embedding-3-large">text-embedding-3-large</option>
          </select>
        </div>

        <div className="control-group">
          <label className="control-label">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              style={{ marginRight: '8px' }}
            />
            Auto-refresh
          </label>
        </div>

        <div className="control-group" style={{ marginLeft: 'auto' }}>
          <button className="btn btn-export" onClick={() => handleExport('json')}>
            <span>📥</span>
            <span>Export JSON</span>
          </button>
          <button className="btn btn-export" onClick={() => handleExport('csv')}>
            <span>📊</span>
            <span>Export CSV</span>
          </button>
          <button className="btn btn-primary" onClick={fetchEmbeddingsData}>
            <span>🔄</span>
            <span>Refresh Now</span>
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <EmbeddingStats metrics={metrics} isLoading={isLoading} />

      {/* Charts Grid */}
      <div className="dashboard-grid">
        <div>
          <UsageTrends data={usageTrends} isLoading={isLoading} />
          <TokenConsumption data={usageTrends} isLoading={isLoading} />
        </div>
        <div>
          <ModelUsageChart data={modelUsage} isLoading={isLoading} />
          <DimensionDistribution data={dimensionStats} isLoading={isLoading} />
        </div>
      </div>

      {/* Cost Analysis */}
      <CostAnalysis data={costBreakdown} isLoading={isLoading} />

      {/* Recent Embeddings Table */}
      <RecentEmbeddingsTable embeddings={recentEmbeddings} isLoading={isLoading} />

      {/* Refresh Indicator */}
      {autoRefresh && (
        <div className="refresh-indicator">
          <div className="loading-spinner" />
          <span className="refresh-indicator-text">
            Last updated: <span className="refresh-indicator-time">{lastUpdate.toLocaleTimeString()}</span>
          </span>
        </div>
      )}
    </div>
  );
};

export default EmbeddingsDashboard;
