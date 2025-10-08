/**
 * NVIDIA AI-Dynamo Dashboard
 *
 * Real-time monitoring dashboard for NVIDIA AI-Dynamo LLM inference serving system.
 * Tracks comprehensive performance metrics including latency breakdowns, throughput,
 * KV cache efficiency, and request lifecycles.
 *
 * Updated: October 2025 - WebSocket with HTTP fallback!
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw, Activity, Clock, Wifi, WifiOff, Loader2, Zap } from 'lucide-react';
import { fetchAIDynamoMetrics } from './api';
import {
  AIDynamoDashboardData,
} from './types';
import { useGenericWebSocket, ConnectionState } from '../../services/useGenericWebSocket';

// Import components
import { MetricsOverview } from './components/MetricsOverview';
import { LatencyBreakdownChart } from './components/LatencyBreakdownChart';
import { TTFTMetrics } from './components/TTFTMetrics';
import { TPOTMetrics } from './components/TPOTMetrics';
import { RequestLifecycleTimeline } from './components/RequestLifecycleTimeline';
import { ThroughputMetrics } from './components/ThroughputMetrics';
import { QueueDepthMonitor } from './components/QueueDepthMonitor';
import { KVCacheAnalytics } from './components/KVCacheAnalytics';
import { WorkerUtilization } from './components/WorkerUtilization';
import { TokenStatistics } from './components/TokenStatistics';
import { PerModelPerformance } from './components/PerModelPerformance';

export const AIDynamoDashboard: React.FC = () => {
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [useWebSocketMode, setUseWebSocketMode] = useState(true);

  // WebSocket connection for real-time AI-Dynamo metrics
  const {
    data: wsData,
    connectionState,
    isConnected,
    error: wsError,
    latency: wsLatency,
    reconnect,
    disconnect,
  } = useGenericWebSocket<AIDynamoDashboardData>({
    url: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ai-dynamo/stream`,
    autoConnect: useWebSocketMode,
    onData: () => setLastUpdate(new Date()),
    onError: (err) => console.error('[AIDynamo] WebSocket error:', err),
  });

  // HTTP fallback
  const [httpData, setHttpData] = useState<AIDynamoDashboardData | null>(null);
  const [httpLoading, setHttpLoading] = useState(false);
  const [httpError, setHttpError] = useState<string | null>(null);

  const fetchHTTPData = useCallback(async () => {
    if (useWebSocketMode && isConnected) return; // Skip if WebSocket is working

    try {
      setHttpLoading(true);
      setHttpError(null);
      const data = await fetchAIDynamoMetrics();
      setHttpData(data);
      setLastUpdate(new Date());
    } catch (err) {
      setHttpError(err instanceof Error ? err.message : 'Failed to fetch metrics');
    } finally {
      setHttpLoading(false);
    }
  }, [useWebSocketMode, isConnected]);

  // Auto-fallback to HTTP if WebSocket fails
  useEffect(() => {
    if (useWebSocketMode && connectionState === ConnectionState.ERROR && !httpData) {
      console.log('[AIDynamo] WebSocket failed, falling back to HTTP');
      fetchHTTPData();
    }
  }, [connectionState, useWebSocketMode, httpData, fetchHTTPData]);

  // Initial HTTP load (always load once for fallback)
  useEffect(() => {
    fetchHTTPData();
  }, []);

  // Use WebSocket data if available AND connected, otherwise HTTP data
  const dashboardData = (useWebSocketMode && isConnected && wsData) ? wsData : httpData;
  const loading = (useWebSocketMode && !isConnected && connectionState === ConnectionState.CONNECTING && !httpData) || httpLoading;
  const error = (useWebSocketMode && !isConnected) ? wsError?.message : httpError;
  const data = dashboardData;

  // Show loading state
  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-black via-gray-900 to-black">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <Loader2 className="w-16 h-16 text-green-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-400 text-lg">Loading AI-Dynamo metrics...</p>
        </motion.div>
      </div>
    );
  }

  // Show error state
  if (error && !data) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-black via-gray-900 to-black">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-md"
        >
          <WifiOff className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Connection Failed</h2>
          <p className="text-gray-400 mb-6">{error}</p>
          <button
            onClick={() => {
              setUseWebSocketMode(false);
              fetchHTTPData();
            }}
            className="px-6 py-3 bg-green-500 text-black font-semibold rounded-lg hover:bg-green-400 transition-all flex items-center gap-2 mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            Use HTTP Fallback
          </button>
        </motion.div>
      </div>
    );
  }

  // Show empty state if no data at all
  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-black via-gray-900 to-black">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-md"
        >
          <Zap className="w-16 h-16 text-gray-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">No Metrics Available</h2>
          <p className="text-gray-400 mb-6">AI-Dynamo metrics are not available.</p>
          <button
            onClick={() => fetchHTTPData()}
            className="px-6 py-3 bg-green-500 text-black font-semibold rounded-lg hover:bg-green-400 transition-all"
          >
            Refresh
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-black">
      {/* Header */}
      <div className="border-b border-white/10 bg-black/50 backdrop-blur-lg sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <Zap className="w-8 h-8 text-green-500" />
              <div>
                <h1 className="text-2xl font-bold text-white">AI-Dynamo Monitor</h1>
                <p className="text-sm text-gray-400">
                  LLM Inference Performance
                  {useWebSocketMode && isConnected && wsLatency > 0 && ` • ${wsLatency}ms latency`}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Connection Mode Toggle */}
              <button
                onClick={() => {
                  setUseWebSocketMode(!useWebSocketMode);
                  if (useWebSocketMode) disconnect();
                }}
                className={`px-3 py-2 rounded-lg flex items-center gap-2 text-sm transition-all ${
                  useWebSocketMode
                    ? 'bg-green-500/20 text-green-400 border border-green-500/50'
                    : 'bg-white/10 text-white border border-white/20'
                }`}
                title={useWebSocketMode ? 'Switch to HTTP mode' : 'Switch to WebSocket mode'}
              >
                {useWebSocketMode ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
                {useWebSocketMode ? 'WebSocket' : 'HTTP'}
              </button>

              {/* Connection Status Indicator (WebSocket mode only) */}
              {useWebSocketMode && (
                <div className="flex items-center gap-2 px-3 py-2 bg-white/5 border border-white/10 rounded-lg">
                  {connectionState === ConnectionState.CONNECTED && (
                    <>
                      <Wifi className="w-4 h-4 text-green-500 animate-pulse" />
                      <span className="text-xs text-green-500 font-semibold">Live</span>
                    </>
                  )}
                  {connectionState === ConnectionState.CONNECTING && (
                    <>
                      <Loader2 className="w-4 h-4 text-yellow-500 animate-spin" />
                      <span className="text-xs text-yellow-500 font-semibold">Connecting</span>
                    </>
                  )}
                  {connectionState === ConnectionState.RECONNECTING && (
                    <>
                      <RefreshCw className="w-4 h-4 text-orange-500 animate-spin" />
                      <span className="text-xs text-orange-500 font-semibold">Reconnecting</span>
                    </>
                  )}
                  {connectionState === ConnectionState.ERROR && (
                    <>
                      <WifiOff className="w-4 h-4 text-red-500" />
                      <span className="text-xs text-red-500 font-semibold">Using HTTP</span>
                    </>
                  )}
                  {connectionState === ConnectionState.DISCONNECTED && (
                    <>
                      <WifiOff className="w-4 h-4 text-gray-500" />
                      <span className="text-xs text-gray-500 font-semibold">Disconnected</span>
                    </>
                  )}
                </div>
              )}

              {/* Manual Refresh */}
              <button
                onClick={() => {
                  if (useWebSocketMode) reconnect();
                  else fetchHTTPData();
                }}
                disabled={loading}
                className="px-4 py-2 bg-green-500 text-black font-semibold rounded-lg hover:bg-green-400 flex items-center gap-2 disabled:opacity-50 disabled:bg-gray-600 transition-all"
              >
                <RefreshCw className="w-4 h-4" />
                {useWebSocketMode ? 'Reconnect' : 'Refresh'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-red-500/10 border-l-4 border-red-500 text-red-500 px-4 py-3 mx-4 mt-4 rounded-r-lg flex items-center gap-3"
          >
            <WifiOff className="w-5 h-5" />
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Live Indicator Banner */}
      {useWebSocketMode && isConnected && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mx-4 mt-4 px-4 py-3 bg-gradient-to-r from-green-500/20 to-green-600/10 border border-green-500/30 rounded-lg flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <div className="relative">
              <Wifi className="w-5 h-5 text-green-500" />
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-ping" />
            </div>
            <div>
              <div className="text-sm font-semibold text-green-400">Live Updates Active</div>
              <div className="text-xs text-gray-400">AI-Dynamo metrics streaming via WebSocket • Updates every 1 second</div>
            </div>
          </div>
          {wsLatency > 0 && (
            <div className="text-xs text-green-400 font-mono bg-green-500/10 px-3 py-1 rounded-full">
              {wsLatency}ms latency
            </div>
          )}
        </motion.div>
      )}

      {/* Dashboard Content */}
      <div className="container mx-auto px-4 py-8">
        {/* Overview Section */}
        <MetricsOverview metrics={data.metrics} loading={loading} />

        {/* Latency Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <TTFTMetrics stats={data.ttft_stats} loading={loading} />
          <TPOTMetrics stats={data.tpot_stats} loading={loading} />
        </div>

        <div className="mb-8">
          <LatencyBreakdownChart latencyData={data.latency_breakdown} loading={loading} />
        </div>

        {/* Throughput and Queue Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <ThroughputMetrics stats={data.throughput_stats} loading={loading} />
          <QueueDepthMonitor stats={data.queue_stats} loading={loading} />
        </div>

        {/* KV Cache and Workers */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <KVCacheAnalytics stats={data.kv_cache_stats} loading={loading} />
          <WorkerUtilization workers={data.worker_stats} loading={loading} />
        </div>

        {/* Tokens and Per-Model Performance */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <TokenStatistics stats={data.token_stats} loading={loading} />
          <PerModelPerformance models={data.per_model_performance} loading={loading} />
        </div>

        {/* Request Lifecycle Timeline */}
        <RequestLifecycleTimeline lifecycles={data.request_lifecycles} loading={loading} />
      </div>

      {/* Footer Info */}
      <div className="bg-white/5 backdrop-blur-sm border-t border-white/10 py-4 mt-8">
        <div className="container mx-auto px-4">
          <div className="flex flex-wrap gap-4 items-center justify-center text-sm text-gray-400">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              <span>Last updated: {lastUpdate.toLocaleTimeString()}</span>
            </div>
            <span>•</span>
            <div className="flex items-center gap-2">
              {useWebSocketMode && isConnected ? (
                <>
                  <Wifi className="w-4 h-4 text-green-500" />
                  <span className="text-green-500 font-semibold">WebSocket Live</span>
                </>
              ) : (
                <>
                  <Activity className="w-4 h-4 text-blue-400" />
                  <span className="text-blue-400">HTTP Mode</span>
                </>
              )}
            </div>
            <span>•</span>
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-green-500 animate-pulse" />
              <span className="text-green-500">Monitoring Active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIDynamoDashboard;
