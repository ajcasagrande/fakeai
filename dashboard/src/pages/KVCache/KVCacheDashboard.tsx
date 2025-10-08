/**
 * KV Cache Monitoring Dashboard
 *
 * Real-time monitoring dashboard for KV cache performance metrics.
 * Tracks cache hit rates, speedup ratios, worker statistics, and radix tree structure.
 *
 * Updated: October 2025 - Now with WebSocket streaming!
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw, Activity, Clock, Database, Wifi, WifiOff, Loader2 } from 'lucide-react';
import { KVCacheData } from './types';
import { fetchKVCacheMetrics } from './api';
import { useGenericWebSocket, ConnectionState } from '../../services/useGenericWebSocket';

// Import components
import { CachePerformanceOverview } from './components/CachePerformanceOverview';
import { SpeedupMetrics } from './components/SpeedupMetrics';
import { WorkerStatsGrid } from './components/WorkerStatsGrid';
import { RadixTreeStats } from './components/RadixTreeStats';
import { CacheHitRateGauge } from './components/CacheHitRateGauge';

export const KVCacheDashboard: React.FC = () => {
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [useWebSocketMode, setUseWebSocketMode] = useState(true);

  // WebSocket connection for real-time KV cache metrics
  const {
    data: wsData,
    connectionState,
    isConnected,
    error: wsError,
    latency: wsLatency,
    reconnect,
    disconnect,
  } = useGenericWebSocket<KVCacheData>({
    url: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/kv-cache/stream`,
    autoConnect: useWebSocketMode,
    onData: () => setLastUpdate(new Date()),
    onError: (err) => console.error('[KVCache] WebSocket error:', err),
  });

  // HTTP fallback
  const [httpData, setHttpData] = useState<KVCacheData | null>(null);
  const [httpLoading, setHttpLoading] = useState(false);
  const [httpError, setHttpError] = useState<string | null>(null);

  const fetchHTTPData = useCallback(async () => {
    if (useWebSocketMode && isConnected) return; // Skip if WebSocket is working

    try {
      setHttpLoading(true);
      setHttpError(null);
      const data = await fetchKVCacheMetrics();
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
      console.log('[KVCache] WebSocket failed, falling back to HTTP');
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

  // Show loading state
  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-black via-gray-900 to-black">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <Loader2 className="w-16 h-16 text-green-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-400 text-lg">Connecting to KV cache metrics stream...</p>
        </motion.div>
      </div>
    );
  }

  // Show error state
  if (error && !dashboardData) {
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
            onClick={reconnect}
            className="px-6 py-3 bg-green-500 text-black font-semibold rounded-lg hover:bg-green-400 transition-all flex items-center gap-2 mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            Reconnect
          </button>
        </motion.div>
      </div>
    );
  }

  // Show empty state if no data
  if (!dashboardData) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-black via-gray-900 to-black">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-md"
        >
          <Database className="w-16 h-16 text-gray-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">No Metrics Available</h2>
          <p className="text-gray-400 mb-6">KV cache metrics are not available.</p>
          <button
            onClick={reconnect}
            className="px-6 py-3 bg-green-500 text-black font-semibold rounded-lg hover:bg-green-400 transition-all"
          >
            Refresh
          </button>
        </motion.div>
      </div>
    );
  }

  const { cache_performance, smart_router } = dashboardData;

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-black" key="kv-cache-dashboard">
      {/* Header */}
      <div className="border-b border-white/10 bg-black/50 backdrop-blur-lg sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <Database className="w-8 h-8 text-green-500" />
              <div>
                <h1 className="text-2xl font-bold text-white">KV Cache Monitor</h1>
                <p className="text-sm text-gray-400">
                  Real-time Cache Performance via WebSocket
                  {isConnected && wsLatency > 0 && ` • ${wsLatency}ms latency`}
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
                      <span className="text-xs text-red-500 font-semibold">Fallback to HTTP</span>
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

              {/* Manual Refresh (HTTP mode or WebSocket retry) */}
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
              <div className="text-xs text-gray-400">KV cache metrics streaming via WebSocket • Updates every 1 second</div>
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
        {/* Cache Performance Overview */}
        <CachePerformanceOverview
          performance={cache_performance}
          loading={loading}
        />

        {/* Main Metrics Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <CacheHitRateGauge
            hitRate={cache_performance.cache_hit_rate}
            totalHits={cache_performance.total_cache_hits}
            totalMisses={cache_performance.total_cache_misses}
            loading={loading}
          />
          <SpeedupMetrics
            speedupStats={cache_performance.speedup_stats}
            loading={loading}
          />
        </div>

        {/* Worker and Radix Tree Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <WorkerStatsGrid
            workers={smart_router.workers}
            loading={loading}
          />
          <RadixTreeStats
            radixTree={smart_router.radix_tree}
            loading={loading}
          />
        </div>
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
              {isConnected ? (
                <>
                  <Wifi className="w-4 h-4 text-green-500" />
                  <span className="text-green-500 font-semibold">WebSocket Connected</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-4 h-4 text-orange-500" />
                  <span className="text-orange-500">{connectionState}</span>
                </>
              )}
            </div>
            <span>•</span>
            <span>{Object.keys(smart_router.workers).length} workers active</span>
            <span>•</span>
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-green-500 animate-pulse" />
              <span className="text-green-500">Live Monitoring</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KVCacheDashboard;
