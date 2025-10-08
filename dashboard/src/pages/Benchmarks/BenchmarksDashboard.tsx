/**
 * Benchmarks Dashboard
 *
 * Beautiful benchmark results viewer for AIPerf data
 * Features glass morphism design, framer motion animations,
 * and comprehensive performance metrics visualization
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw, BarChart3, Clock, AlertCircle } from 'lucide-react';
import { fetchBenchmarkList, fetchBenchmarkData } from './api';
import { BenchmarkData, BenchmarkFile } from './types';

// Import components
import { BenchmarkSelector } from './components/BenchmarkSelector';
import { MetricsOverview } from './components/MetricsOverview';
import { TTFTDistribution } from './components/TTFTDistribution';
import { LatencyChart } from './components/LatencyChart';
import { ThroughputChart } from './components/ThroughputChart';
import { ITLDistribution } from './components/ITLDistribution';

export const BenchmarksDashboard: React.FC = () => {
  // State management
  const [benchmarkList, setBenchmarkList] = useState<BenchmarkFile[]>([]);
  const [selectedBenchmark, setSelectedBenchmark] = useState<BenchmarkFile | null>(null);
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Load benchmark list
  const loadBenchmarkList = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const list = await fetchBenchmarkList();
      setBenchmarkList(list);

      // Auto-select first benchmark if available
      if (list.length > 0 && !selectedBenchmark) {
        setSelectedBenchmark(list[0]);
      }

      console.log('Benchmark list loaded:', list);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch benchmark list');
      console.error('Error fetching benchmark list:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedBenchmark]);

  // Load benchmark data
  const loadBenchmarkData = useCallback(async (benchmark: BenchmarkFile) => {
    try {
      setLoading(true);
      setError(null);

      const data = await fetchBenchmarkData(benchmark.path);
      setBenchmarkData(data);
      setLastUpdate(new Date());

      console.log('Benchmark data loaded:', data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch benchmark data');
      console.error('Error fetching benchmark data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadBenchmarkList();
  }, [loadBenchmarkList]);

  // Load data when benchmark is selected
  useEffect(() => {
    if (selectedBenchmark) {
      loadBenchmarkData(selectedBenchmark);
    }
  }, [selectedBenchmark, loadBenchmarkData]);

  // Handle benchmark selection
  const handleBenchmarkSelect = (benchmark: BenchmarkFile) => {
    setSelectedBenchmark(benchmark);
  };

  // Handle refresh
  const handleRefresh = () => {
    if (selectedBenchmark) {
      loadBenchmarkData(selectedBenchmark);
    } else {
      loadBenchmarkList();
    }
  };

  // Show loading state
  if (loading && !benchmarkData && benchmarkList.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-black via-gray-900 to-black">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="w-16 h-16 border-4 border-nvidia-green border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400 text-lg">Loading benchmark data...</p>
        </motion.div>
      </div>
    );
  }

  // Show error state (no data available)
  if (error && !benchmarkData && benchmarkList.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-black via-gray-900 to-black">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center max-w-md"
        >
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Failed to Load</h2>
          <p className="text-gray-400 mb-6">{error}</p>
          <button
            onClick={handleRefresh}
            className="px-6 py-3 bg-nvidia-green text-black font-semibold rounded-lg hover:bg-nvidia-green/90 transition-all"
          >
            Retry
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
              <BarChart3 className="w-8 h-8 text-nvidia-green" />
              <div>
                <h1 className="text-2xl font-bold text-white">AIPerf Benchmarks</h1>
                <p className="text-sm text-gray-400">Performance Metrics Visualization</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleRefresh}
                disabled={loading}
                className="px-4 py-2 bg-white/10 text-white rounded-lg hover:bg-white/20 flex items-center gap-2 border border-white/20 disabled:opacity-50 transition-all"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
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
            <AlertCircle className="w-5 h-5" />
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Dashboard Content */}
      <div className="container mx-auto px-4 py-8">
        {/* Benchmark Selector */}
        <BenchmarkSelector
          benchmarks={benchmarkList}
          selectedBenchmark={selectedBenchmark}
          onSelect={handleBenchmarkSelect}
          loading={loading}
        />

        {loading && !benchmarkData ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-12 h-12 border-4 border-nvidia-green border-t-transparent rounded-full animate-spin" />
          </div>
        ) : benchmarkData ? (
          <>
            {/* Metrics Overview */}
            <MetricsOverview records={benchmarkData.records} loading={loading} />

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <TTFTDistribution ttft={benchmarkData.records.ttft} loading={loading} />
              <LatencyChart latency={benchmarkData.records.request_latency} loading={loading} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <ThroughputChart
                requestThroughput={benchmarkData.records.request_throughput}
                outputTokenThroughput={benchmarkData.records.output_token_throughput}
                duration={benchmarkData.records.benchmark_duration}
                requestCount={benchmarkData.records.request_count}
                loading={loading}
              />
              <ITLDistribution itl={benchmarkData.records.inter_token_latency} loading={loading} />
            </div>

            {/* Benchmark Info */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
            >
              <h3 className="text-lg font-bold text-white mb-4">Benchmark Configuration</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <div className="text-xs text-gray-500 mb-1">Model</div>
                  <div className="text-sm text-white font-semibold">
                    {benchmarkData.input_config.endpoint.model_names.join(', ')}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-1">Concurrency</div>
                  <div className="text-sm text-white font-semibold">
                    {benchmarkData.input_config.loadgen.concurrency}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-1">Endpoint Type</div>
                  <div className="text-sm text-white font-semibold">
                    {benchmarkData.input_config.endpoint.type}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-1">Streaming</div>
                  <div className="text-sm text-white font-semibold">
                    {benchmarkData.input_config.endpoint.streaming ? 'Enabled' : 'Disabled'}
                  </div>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-white/5">
                <div className="text-xs text-gray-500 mb-1">CLI Command</div>
                <div className="text-xs text-gray-400 font-mono bg-black/30 p-3 rounded-lg overflow-x-auto">
                  {benchmarkData.input_config.cli_command}
                </div>
              </div>
            </motion.div>
          </>
        ) : (
          <div className="text-center py-20">
            <p className="text-gray-400 text-lg">No benchmark data available</p>
          </div>
        )}
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
            <span>{benchmarkList.length} benchmark runs available</span>
            {benchmarkData && (
              <>
                <span>•</span>
                <span>
                  {benchmarkData.records.request_count.avg.toFixed(0)} total requests
                </span>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BenchmarksDashboard;
