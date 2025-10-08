/**
 * Example implementations of WebSocket real-time updates system
 * These examples demonstrate various use cases and best practices
 */

import React, { useState } from 'react';
import {
  WebSocketProvider,
  useRealtimeMetrics,
  useConnectionStatus,
  useWebSocketSubscription,
  useModelMetrics,
  useRequestHistory,
  useErrorMonitor,
  useSystemHealth,
  useAggregateStats,
  ConnectionStatus,
  ConnectionStats,
  ConnectionBadge,
  MessageType,
  MetricsUpdatePayload,
  RequestUpdatePayload,
} from './index';

/**
 * Example 1: Basic Dashboard with Real-time Metrics
 */
export function BasicDashboard() {
  return (
    <WebSocketProvider
      config={{
        url: 'ws://localhost:8000/metrics/stream',
        debug: true,
      }}
      onConnect={() => console.log('Dashboard connected')}
    >
      <div className="p-6 space-y-6">
        <ConnectionStatus showDetails showLatency />
        <MetricsOverview />
        <ModelsList />
        <RecentRequests />
      </div>
    </WebSocketProvider>
  );
}

/**
 * Example 2: Metrics Overview Component
 */
function MetricsOverview() {
  const { metrics, isConnected } = useRealtimeMetrics();

  if (!isConnected) {
    return <div className="text-gray-400">Connecting to metrics stream...</div>;
  }

  if (!metrics) {
    return <div className="text-gray-400">Waiting for metrics data...</div>;
  }

  return (
    <div className="grid grid-cols-4 gap-4">
      <MetricCard
        label="Total Requests"
        value={metrics.total_requests.toLocaleString()}
        icon="📊"
      />
      <MetricCard
        label="Avg Latency"
        value={`${Math.round(metrics.avg_latency_ms)}ms`}
        icon="⚡"
      />
      <MetricCard
        label="Error Rate"
        value={`${(metrics.error_rate * 100).toFixed(2)}%`}
        icon="⚠️"
        alert={metrics.error_rate > 0.05}
      />
      <MetricCard
        label="RPS"
        value={metrics.requests_per_second.toFixed(1)}
        icon="🔥"
      />
    </div>
  );
}

/**
 * Example 3: Models List with Real-time Updates
 */
function ModelsList() {
  const { models } = useRealtimeMetrics();

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h2 className="text-xl font-bold text-white mb-4">Model Performance</h2>
      <div className="space-y-2">
        {Array.from(models.entries()).map(([modelName, stats]) => (
          <ModelCard key={modelName} modelName={modelName} stats={stats} />
        ))}
      </div>
    </div>
  );
}

function ModelCard({ modelName, stats }: any) {
  return (
    <div className="bg-gray-900 rounded p-3 border border-gray-700">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-white font-medium">{modelName}</h3>
          <div className="flex gap-4 text-sm text-gray-400 mt-1">
            <span>Requests: {stats.request_count}</span>
            <span>Latency: {Math.round(stats.avg_latency_ms)}ms</span>
            <span>Tokens: {stats.total_tokens.toLocaleString()}</span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-green-400 font-bold">
            ${stats.total_cost.toFixed(2)}
          </div>
          <div className="text-xs text-gray-400">
            {stats.tokens_per_second.toFixed(0)} tok/s
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Example 4: Recent Requests Table
 */
function RecentRequests() {
  const { recentRequests } = useRealtimeMetrics();

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h2 className="text-xl font-bold text-white mb-4">Recent Requests</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-gray-400 border-b border-gray-700">
            <tr>
              <th className="text-left py-2">ID</th>
              <th className="text-left py-2">Model</th>
              <th className="text-left py-2">Tokens</th>
              <th className="text-left py-2">Latency</th>
              <th className="text-left py-2">Status</th>
              <th className="text-left py-2">Cost</th>
            </tr>
          </thead>
          <tbody className="text-gray-300">
            {recentRequests.slice(0, 10).map((req) => (
              <tr key={req.id} className="border-b border-gray-700/50">
                <td className="py-2">{req.id.slice(0, 8)}...</td>
                <td className="py-2">{req.model}</td>
                <td className="py-2">{req.total_tokens}</td>
                <td className="py-2">{req.latency_ms}ms</td>
                <td className="py-2">
                  <StatusBadge status={req.status} />
                </td>
                <td className="py-2">${req.cost.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * Example 5: Connection Status in Header
 */
export function DashboardHeader() {
  return (
    <header className="bg-gray-900 border-b border-gray-800 px-6 py-4">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white">FakeAI Dashboard</h1>
          <p className="text-gray-400 text-sm">Real-time metrics monitoring</p>
        </div>
        <div className="flex items-center gap-4">
          <ConnectionStats />
          <ConnectionStatus compact showLatency />
        </div>
      </div>
    </header>
  );
}

/**
 * Example 6: Specific Model Monitoring
 */
export function ModelMonitor({ modelName }: { modelName: string }) {
  const metrics = useModelMetrics(modelName);

  if (!metrics) {
    return <div>No data for {modelName}</div>;
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-xl font-bold text-white mb-4">{modelName}</h2>
      <div className="grid grid-cols-3 gap-4">
        <div>
          <div className="text-gray-400 text-sm">Requests</div>
          <div className="text-2xl font-bold text-white">
            {metrics.request_count.toLocaleString()}
          </div>
        </div>
        <div>
          <div className="text-gray-400 text-sm">Avg Latency</div>
          <div className="text-2xl font-bold text-white">
            {Math.round(metrics.avg_latency_ms)}ms
          </div>
        </div>
        <div>
          <div className="text-gray-400 text-sm">Error Rate</div>
          <div className="text-2xl font-bold text-red-400">
            {(metrics.error_rate * 100).toFixed(2)}%
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Example 7: Error Monitor with Alerts
 */
export function ErrorMonitorPanel() {
  const [showAlert, setShowAlert] = useState(false);

  const { errors, errorCount, clearErrors } = useErrorMonitor({
    maxSize: 20,
    onError: (error) => {
      if (error.severity === 'critical') {
        setShowAlert(true);
        // Could trigger notification system here
      }
    },
  });

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-white">
          Errors ({errorCount})
        </h2>
        <button
          onClick={clearErrors}
          className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm"
        >
          Clear
        </button>
      </div>

      {showAlert && (
        <div className="bg-red-900/50 border border-red-600 rounded p-3 mb-4">
          <div className="flex justify-between">
            <span className="text-red-400">Critical error detected!</span>
            <button onClick={() => setShowAlert(false)}>✕</button>
          </div>
        </div>
      )}

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {errors.map((error, idx) => (
          <div
            key={idx}
            className="bg-gray-900 rounded p-3 border border-red-800/50"
          >
            <div className="flex justify-between items-start">
              <div>
                <div className="text-red-400 font-medium">
                  {error.error_type}
                </div>
                <div className="text-gray-400 text-sm mt-1">
                  {error.error_message}
                </div>
              </div>
              <SeverityBadge severity={error.severity} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Example 8: System Health Dashboard
 */
export function SystemHealthDashboard() {
  const { health, isHealthy } = useSystemHealth();

  if (!health) {
    return <div>Loading system health...</div>;
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center gap-2 mb-4">
        <h2 className="text-xl font-bold text-white">System Health</h2>
        <div
          className={`w-3 h-3 rounded-full ${
            isHealthy ? 'bg-green-500' : 'bg-red-500'
          }`}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <ResourceUsage label="CPU" usage={health.cpu_usage} />
        <ResourceUsage label="Memory" usage={health.memory_usage} />
        {health.gpu_usage !== undefined && (
          <ResourceUsage label="GPU" usage={health.gpu_usage} />
        )}
        {health.gpu_memory_usage !== undefined && (
          <ResourceUsage label="GPU Memory" usage={health.gpu_memory_usage} />
        )}
        <div className="col-span-2">
          <div className="text-gray-400 text-sm">Queue Size</div>
          <div className="text-2xl font-bold text-white">
            {health.queue_size}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Example 9: Custom Message Subscription
 */
export function CustomMetricsSubscriber() {
  const [customData, setCustomData] = useState<any>(null);

  useWebSocketSubscription<MetricsUpdatePayload>(
    MessageType.METRICS_UPDATE,
    (data, message) => {
      // Custom processing
      const processedData = {
        ...data,
        timestamp: new Date(message.timestamp).toLocaleString(),
        health: data.error_rate < 0.05 ? 'healthy' : 'warning',
      };
      setCustomData(processedData);
    }
  );

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="text-white font-bold mb-2">Custom Metrics</h3>
      <pre className="text-xs text-gray-400">
        {JSON.stringify(customData, null, 2)}
      </pre>
    </div>
  );
}

/**
 * Example 10: Request History with Filtering
 */
export function FilteredRequestHistory() {
  const [filterModel, setFilterModel] = useState<string>('');

  const { requests, clearHistory } = useRequestHistory({
    maxSize: 100,
    filterFn: (request) =>
      !filterModel || request.model.includes(filterModel),
  });

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-white">Request History</h2>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Filter by model..."
            value={filterModel}
            onChange={(e) => setFilterModel(e.target.value)}
            className="px-3 py-1 bg-gray-900 border border-gray-700 rounded text-white"
          />
          <button
            onClick={clearHistory}
            className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded"
          >
            Clear
          </button>
        </div>
      </div>
      <div className="text-gray-400">
        Showing {requests.length} requests
      </div>
    </div>
  );
}

/**
 * Example 11: Aggregate Statistics
 */
export function AggregateStatsPanel() {
  const stats = useAggregateStats();

  return (
    <div className="grid grid-cols-5 gap-4">
      <StatCard label="Models" value={stats.totalModels} />
      <StatCard label="Requests" value={stats.totalRequests.toLocaleString()} />
      <StatCard label="Tokens" value={stats.totalTokens.toLocaleString()} />
      <StatCard label="Cost" value={`$${stats.totalCost.toFixed(2)}`} />
      <StatCard label="RPS" value={stats.requestsPerSecond.toFixed(1)} />
    </div>
  );
}

/**
 * Example 12: Manual Connection Control
 */
export function ConnectionControls() {
  const status = useConnectionStatus();

  return (
    <div className="flex items-center gap-4">
      <ConnectionBadge />
      <span className="text-gray-400">{status.state}</span>
      {status.latency && (
        <span className="text-green-400">{status.latency}ms</span>
      )}
    </div>
  );
}

// Helper Components

function MetricCard({
  label,
  value,
  icon,
  alert = false,
}: {
  label: string;
  value: string;
  icon: string;
  alert?: boolean;
}) {
  return (
    <div
      className={`bg-gray-900 rounded-lg p-4 border ${
        alert ? 'border-red-600' : 'border-gray-700'
      }`}
    >
      <div className="flex justify-between items-start mb-2">
        <span className="text-gray-400 text-sm">{label}</span>
        <span className="text-2xl">{icon}</span>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors = {
    success: 'bg-green-500/20 text-green-400',
    error: 'bg-red-500/20 text-red-400',
    in_progress: 'bg-yellow-500/20 text-yellow-400',
  };

  return (
    <span
      className={`px-2 py-0.5 rounded text-xs ${
        colors[status as keyof typeof colors]
      }`}
    >
      {status}
    </span>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const colors = {
    low: 'bg-blue-500/20 text-blue-400',
    medium: 'bg-yellow-500/20 text-yellow-400',
    high: 'bg-orange-500/20 text-orange-400',
    critical: 'bg-red-500/20 text-red-400',
  };

  return (
    <span
      className={`px-2 py-0.5 rounded text-xs ${
        colors[severity as keyof typeof colors]
      }`}
    >
      {severity}
    </span>
  );
}

function ResourceUsage({ label, usage }: { label: string; usage: number }) {
  const getColor = () => {
    if (usage < 70) return 'bg-green-500';
    if (usage < 85) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-400">{label}</span>
        <span className="text-white">{usage.toFixed(1)}%</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${getColor()}`}
          style={{ width: `${usage}%` }}
        />
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
      <div className="text-gray-400 text-sm mb-1">{label}</div>
      <div className="text-xl font-bold text-white">{value}</div>
    </div>
  );
}
