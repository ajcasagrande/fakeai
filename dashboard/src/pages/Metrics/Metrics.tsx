import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  Zap,
  TrendingUp,
  Clock,
  AlertCircle,
  CheckCircle,
  Users,
  RefreshCw,
  BarChart3,
  Gauge,
  Wifi,
  WifiOff,
  Loader2,
} from 'lucide-react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import axios from 'axios';
import { useMetricsWebSocket, ConnectionState } from '../../services/useMetricsWebSocket';

interface MetricsData {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  error_rate: number;
  avg_latency: number;
  p95_latency: number;
  p99_latency: number;
  throughput: number;
  active_connections: number;
  recent_requests?: RecentRequest[];
  latency_history?: LatencyDataPoint[];
  throughput_history?: ThroughputDataPoint[];
}

interface RecentRequest {
  timestamp: string;
  endpoint: string;
  method: string;
  status: number;
  latency: number;
  model?: string;
}

interface LatencyDataPoint {
  timestamp: string;
  avg: number;
  p95: number;
  p99: number;
}

interface ThroughputDataPoint {
  timestamp: string;
  requests: number;
  tokens?: number;
}

export default function Metrics() {
  const [useWebSocket, setUseWebSocket] = useState(true);

  // WebSocket connection for real-time updates
  const {
    metrics: wsMetrics,
    connectionState,
    isConnected,
    isReconnecting,
    error: wsError,
    latency: wsLatency,
    reconnect,
    disconnect,
  } = useMetricsWebSocket({
    filters: { interval: 1.0 },
    autoConnect: useWebSocket,
  });

  // Fallback HTTP polling (when WebSocket disabled)
  const [httpMetrics, setHttpMetrics] = useState<MetricsData | null>(null);
  const [httpLoading, setHttpLoading] = useState(true);
  const [httpError, setHttpError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchMetrics = async () => {
    try {
      setHttpError(null);
      const response = await axios.get('/metrics');
      const data = response.data;

      // Generate mock latency and throughput history for visualization
      const now = Date.now();
      const latencyHistory: LatencyDataPoint[] = Array.from({ length: 20 }, (_, i) => ({
        timestamp: new Date(now - (19 - i) * 5000).toLocaleTimeString(),
        avg: data.avg_latency || Math.random() * 100 + 50,
        p95: data.p95_latency || Math.random() * 200 + 100,
        p99: data.p99_latency || Math.random() * 300 + 150,
      }));

      const throughputHistory: ThroughputDataPoint[] = Array.from({ length: 20 }, (_, i) => ({
        timestamp: new Date(now - (19 - i) * 5000).toLocaleTimeString(),
        requests: Math.floor(Math.random() * 50 + 20),
        tokens: Math.floor(Math.random() * 1000 + 500),
      }));

      setHttpMetrics({
        total_requests: data.total_requests || 0,
        successful_requests: data.successful_requests || 0,
        failed_requests: data.failed_requests || 0,
        error_rate: data.error_rate || 0,
        avg_latency: data.avg_latency || 0,
        p95_latency: data.p95_latency || 0,
        p99_latency: data.p99_latency || 0,
        throughput: data.throughput || 0,
        active_connections: data.active_connections || 0,
        recent_requests: data.recent_requests || [],
        latency_history: latencyHistory,
        throughput_history: throughputHistory,
      });

      setHttpLoading(false);
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
      setHttpError('Failed to load metrics');
      setHttpLoading(false);
    }
  };

  // HTTP polling fallback
  useEffect(() => {
    if (useWebSocket) return;
    fetchMetrics();
  }, [useWebSocket]);

  useEffect(() => {
    if (useWebSocket || !autoRefresh) return;

    const interval = setInterval(() => {
      fetchMetrics();
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh, useWebSocket]);

  // Use WebSocket metrics if available, otherwise HTTP
  const metrics = useWebSocket ? wsMetrics : httpMetrics;
  const loading = useWebSocket ? !isConnected && connectionState === ConnectionState.CONNECTING : httpLoading;
  const error = useWebSocket ? wsError?.message : httpError;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-black via-nvidia-darkGray to-black flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-nvidia-green border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-white text-xl">Loading metrics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-black via-nvidia-darkGray to-black flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <p className="text-white text-xl mb-4">{error}</p>
          <button
            onClick={fetchMetrics}
            className="px-6 py-3 bg-nvidia-green text-black font-bold rounded-lg hover:bg-nvidia-green/90 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const successRate = metrics && metrics.total_requests > 0
    ? ((metrics.successful_requests / metrics.total_requests) * 100).toFixed(1)
    : '0';

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-nvidia-darkGray to-black">
      {/* Header */}
      <div className="border-b border-white/10 bg-black/50 backdrop-blur-lg sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Gauge className="w-8 h-8 text-nvidia-green" />
              <div>
                <h1 className="text-2xl font-bold text-white">System Metrics</h1>
                <p className="text-sm text-gray-400">
                  Real-time performance monitoring
                  {useWebSocket && (
                    <span className="ml-2 text-xs">
                      • WebSocket {isConnected ? 'connected' : connectionState}
                      {isConnected && wsLatency > 0 && ` • ${wsLatency}ms latency`}
                    </span>
                  )}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Connection Status Indicator */}
              {useWebSocket && (
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
                      <span className="text-xs text-red-500 font-semibold">Error</span>
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

              {/* WebSocket Toggle */}
              <button
                onClick={() => {
                  if (useWebSocket) {
                    disconnect();
                  }
                  setUseWebSocket(!useWebSocket);
                }}
                className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                  useWebSocket
                    ? 'bg-nvidia-green text-black'
                    : 'bg-white/10 text-white hover:bg-white/20'
                }`}
              >
                {useWebSocket ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
                {useWebSocket ? 'WebSocket' : 'HTTP Polling'}
              </button>

              {/* HTTP Refresh Controls (when not using WebSocket) */}
              {!useWebSocket && (
                <>
                  <button
                    onClick={() => setAutoRefresh(!autoRefresh)}
                    className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                      autoRefresh
                        ? 'bg-nvidia-green text-black'
                        : 'bg-white/10 text-white hover:bg-white/20'
                    }`}
                  >
                    <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
                    {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
                  </button>
                  <button
                    onClick={fetchMetrics}
                    className="px-4 py-2 bg-white/10 text-white rounded-lg hover:bg-white/20 flex items-center gap-2"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                  </button>
                </>
              )}

              {/* Reconnect Button (when WebSocket error) */}
              {useWebSocket && (connectionState === ConnectionState.ERROR || connectionState === ConnectionState.DISCONNECTED) && (
                <button
                  onClick={reconnect}
                  className="px-4 py-2 bg-nvidia-green text-black rounded-lg hover:bg-nvidia-green/90 flex items-center gap-2 font-semibold"
                >
                  <RefreshCw className="w-4 h-4" />
                  Reconnect
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* WebSocket Live Indicator Banner */}
        {useWebSocket && isConnected && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 px-4 py-3 bg-gradient-to-r from-green-500/20 to-green-600/10 border border-green-500/30 rounded-lg flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <div className="relative">
                <Wifi className="w-5 h-5 text-green-500" />
                <span className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-ping" />
              </div>
              <div>
                <div className="text-sm font-semibold text-green-400">Live Updates Active</div>
                <div className="text-xs text-gray-400">Real-time metrics streaming via WebSocket • Updates every 1 second</div>
              </div>
            </div>
            {wsLatency > 0 && (
              <div className="text-xs text-green-400 font-mono bg-green-500/10 px-3 py-1 rounded-full">
                {wsLatency}ms latency
              </div>
            )}
          </motion.div>
        )}

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            icon={<Activity className="w-6 h-6" />}
            title="Total Requests"
            value={(metrics?.total_requests ?? 0).toLocaleString()}
            subtitle={`${successRate}% success rate`}
            color="green"
            trend="up"
            isLive={useWebSocket && isConnected}
          />

          <MetricCard
            icon={<Clock className="w-6 h-6" />}
            title="Avg Latency"
            value={`${Number(metrics?.avg_latency ?? 0).toFixed(0)}ms`}
            subtitle={`P95: ${Number(metrics?.p95_latency ?? 0).toFixed(0)}ms`}
            color="blue"
            isLive={useWebSocket && isConnected}
          />

          <MetricCard
            icon={<Zap className="w-6 h-6" />}
            title="Throughput"
            value={`${Number(metrics?.throughput ?? 0).toFixed(1)}`}
            subtitle="requests/sec"
            color="purple"
            trend="up"
            isLive={useWebSocket && isConnected}
          />

          <MetricCard
            icon={<Users className="w-6 h-6" />}
            title="Active Connections"
            value={(metrics?.active_connections ?? 0).toString()}
            subtitle="concurrent"
            color="cyan"
            isLive={useWebSocket && isConnected}
          />
        </div>

        {/* Secondary Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatCard
            icon={<CheckCircle className="w-5 h-5" />}
            label="Successful"
            value={(metrics?.successful_requests ?? 0).toLocaleString()}
            color="green"
          />

          <StatCard
            icon={<AlertCircle className="w-5 h-5" />}
            label="Errors"
            value={(metrics?.failed_requests ?? 0).toLocaleString()}
            color="red"
          />

          <StatCard
            icon={<BarChart3 className="w-5 h-5" />}
            label="Error Rate"
            value={`${Number(metrics?.error_rate ?? 0).toFixed(2)}%`}
            color={(metrics?.error_rate ?? 0) > 5 ? 'red' : (metrics?.error_rate ?? 0) > 1 ? 'yellow' : 'green'}
          />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Latency Chart */}
          <ChartCard title="Latency Trends" description="Response time distribution over time">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metrics?.latency_history || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis
                  dataKey="timestamp"
                  stroke="#666"
                  tick={{ fill: '#999', fontSize: 12 }}
                />
                <YAxis
                  stroke="#666"
                  tick={{ fill: '#999', fontSize: 12 }}
                  label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft', fill: '#999' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    border: '1px solid rgba(118, 185, 0, 0.3)',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="avg"
                  stroke="#76B900"
                  strokeWidth={2}
                  name="Average"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="p95"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="P95"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="p99"
                  stroke="#ef4444"
                  strokeWidth={2}
                  name="P99"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          {/* Throughput Chart */}
          <ChartCard title="Throughput Trends" description="Request volume over time">
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={metrics?.throughput_history || []}>
                <defs>
                  <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#76B900" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#76B900" stopOpacity={0.1}/>
                  </linearGradient>
                  <linearGradient id="colorTokens" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis
                  dataKey="timestamp"
                  stroke="#666"
                  tick={{ fill: '#999', fontSize: 12 }}
                />
                <YAxis
                  stroke="#666"
                  tick={{ fill: '#999', fontSize: 12 }}
                  label={{ value: 'Requests/sec', angle: -90, position: 'insideLeft', fill: '#999' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    border: '1px solid rgba(118, 185, 0, 0.3)',
                    borderRadius: '8px',
                    color: '#fff'
                  }}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="requests"
                  stroke="#76B900"
                  fillOpacity={1}
                  fill="url(#colorRequests)"
                  name="Requests/sec"
                />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>

        {/* Latency Percentiles Card */}
        <div className="mb-8">
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-4">Latency Percentiles</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <PercentileBar label="Average" value={metrics?.avg_latency ?? 0} max={metrics?.p99_latency ?? 100} color="green" />
              <PercentileBar label="P95" value={metrics?.p95_latency ?? 0} max={metrics?.p99_latency ?? 100} color="blue" />
              <PercentileBar label="P99" value={metrics?.p99_latency ?? 0} max={metrics?.p99_latency ?? 100} color="orange" />
              <PercentileBar label="Max (est)" value={(metrics?.p99_latency ?? 0) * 1.2} max={(metrics?.p99_latency ?? 0) * 1.2 || 100} color="red" />
            </div>
          </div>
        </div>

        {/* Recent Requests Table */}
        {metrics?.recent_requests && metrics.recent_requests.length > 0 && (
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
            <h3 className="text-xl font-bold text-white mb-4">Recent Requests</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-white/10">
                  <tr>
                    <th className="text-left px-4 py-3 text-gray-400">Timestamp</th>
                    <th className="text-left px-4 py-3 text-gray-400">Method</th>
                    <th className="text-left px-4 py-3 text-gray-400">Endpoint</th>
                    <th className="text-left px-4 py-3 text-gray-400">Status</th>
                    <th className="text-right px-4 py-3 text-gray-400">Latency</th>
                    {metrics.recent_requests.some(r => r.model) && (
                      <th className="text-left px-4 py-3 text-gray-400">Model</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {metrics.recent_requests.slice(0, 20).map((req, idx) => (
                    <tr key={idx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                      <td className="px-4 py-3 text-gray-300">{new Date(req.timestamp).toLocaleTimeString()}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          req.method === 'GET' ? 'bg-blue-500/20 text-blue-400' :
                          req.method === 'POST' ? 'bg-green-500/20 text-green-400' :
                          'bg-gray-500/20 text-gray-400'
                        }`}>
                          {req.method}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-300 font-mono text-xs">{req.endpoint}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          req.status >= 200 && req.status < 300 ? 'bg-green-500/20 text-green-400' :
                          req.status >= 400 && req.status < 500 ? 'bg-yellow-500/20 text-yellow-400' :
                          req.status >= 500 ? 'bg-red-500/20 text-red-400' :
                          'bg-gray-500/20 text-gray-400'
                        }`}>
                          {req.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right text-gray-300">{(req.latency ?? 0).toFixed(2)}ms</td>
                      {req.model && <td className="px-4 py-3 text-gray-300 text-xs">{req.model}</td>}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

interface MetricCardProps {
  icon: React.ReactNode;
  title: string;
  value: string;
  subtitle: string;
  color: 'green' | 'blue' | 'purple' | 'cyan' | 'orange' | 'red';
  trend?: 'up' | 'down';
  isLive?: boolean;
}

function MetricCard({ icon, title, value, subtitle, color, trend, isLive }: MetricCardProps) {
  const colorClasses = {
    green: 'text-green-400',
    blue: 'text-blue-400',
    purple: 'text-purple-400',
    cyan: 'text-cyan-400',
    orange: 'text-orange-400',
    red: 'text-red-400',
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={`bg-white/5 backdrop-blur-sm border rounded-xl p-6 hover:border-nvidia-green/50 transition-all relative ${
        isLive ? 'border-green-500/30 shadow-lg shadow-green-500/10' : 'border-white/10'
      }`}
    >
      {/* Live Indicator */}
      {isLive && (
        <div className="absolute top-3 right-3 flex items-center gap-1">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-[10px] text-green-500 font-semibold uppercase">Live</span>
        </div>
      )}

      <div className="flex items-start justify-between mb-4">
        <div className={`${colorClasses[color]}`}>
          {icon}
        </div>
        {trend && (
          <TrendingUp className={`w-5 h-5 ${trend === 'up' ? 'text-green-400' : 'text-red-400 rotate-180'}`} />
        )}
      </div>
      <div className="text-3xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-gray-400">{title}</div>
      <div className="text-xs text-gray-500 mt-1">{subtitle}</div>
    </motion.div>
  );
}

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: 'green' | 'red' | 'yellow';
}

function StatCard({ icon, label, value, color }: StatCardProps) {
  const colorClasses = {
    green: 'text-green-400 border-green-400/20',
    red: 'text-red-400 border-red-400/20',
    yellow: 'text-yellow-400 border-yellow-400/20',
  };

  return (
    <div className={`bg-white/5 backdrop-blur-sm border ${colorClasses[color]} rounded-xl p-4`}>
      <div className="flex items-center gap-3">
        <div className={colorClasses[color]}>{icon}</div>
        <div>
          <div className="text-sm text-gray-400">{label}</div>
          <div className="text-2xl font-bold text-white">{value}</div>
        </div>
      </div>
    </div>
  );
}

interface ChartCardProps {
  title: string;
  description: string;
  children: React.ReactNode;
}

function ChartCard({ title, description, children }: ChartCardProps) {
  return (
    <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
      <div className="mb-4">
        <h3 className="text-lg font-bold text-white mb-1">{title}</h3>
        <p className="text-sm text-gray-400">{description}</p>
      </div>
      {children}
    </div>
  );
}

interface PercentileBarProps {
  label: string;
  value: number;
  max: number;
  color: 'green' | 'blue' | 'orange' | 'red';
}

function PercentileBar({ label, value, max, color }: PercentileBarProps) {
  const safeValue = value ?? 0;
  const safeMax = max ?? 100;
  const percentage = safeMax > 0 ? (safeValue / safeMax) * 100 : 0;

  const colorClasses = {
    green: 'bg-green-500',
    blue: 'bg-blue-500',
    orange: 'bg-orange-500',
    red: 'bg-red-500',
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-400">{label}</span>
        <span className="text-sm font-semibold text-white">{(value ?? 0).toFixed(0)}ms</span>
      </div>
      <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full ${colorClasses[color]} transition-all duration-500`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
}
