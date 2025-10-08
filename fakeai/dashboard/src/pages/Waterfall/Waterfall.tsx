import React, { useEffect, useState } from 'react';
import './Waterfall.css';

interface TokenTiming {
  token_index: number;
  timestamp_ms: number;
  latency_ms: number | null;
}

interface RequestTiming {
  request_id: string;
  endpoint: string;
  model: string;
  start_time: number;
  end_time: number | null;
  duration_ms: number;
  ttft_ms: number | null;
  is_streaming: boolean;
  input_tokens: number;
  output_tokens: number;
  tokens: TokenTiming[];
  is_complete: boolean;
}

interface WaterfallData {
  requests: RequestTiming[];
  stats: {
    total_completed: number;
    active_requests: number;
    max_capacity: number;
    utilization_percent: number;
  };
}

const Waterfall: React.FC = () => {
  const [data, setData] = useState<WaterfallData | null>(null);
  const [loading, setLoading] = useState(true);
  const [limit, setLimit] = useState(50);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchWaterfallData = async () => {
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/waterfall/data?limit=${limit}`);
      const jsonData = await response.json();
      setData(jsonData);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch waterfall data:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWaterfallData();

    if (autoRefresh) {
      const interval = setInterval(fetchWaterfallData, 2000);
      return () => clearInterval(interval);
    }
  }, [limit, autoRefresh]);

  if (loading) {
    return (
      <div className="waterfall-container">
        <div className="loading">Loading waterfall data...</div>
      </div>
    );
  }

  if (!data || data.requests.length === 0) {
    return (
      <div className="waterfall-container">
        <h1>🎨 Request Waterfall</h1>
        <div className="empty-state">
          <p>No request data available yet.</p>
          <p>Make some requests to see the waterfall visualization!</p>
        </div>
      </div>
    );
  }

  // Calculate chart dimensions
  const earliestTime = Math.min(...data.requests.map(r => r.start_time));
  const latestTime = Math.max(
    ...data.requests.map(r => r.end_time || r.start_time)
  );
  const totalDurationMs = (latestTime - earliestTime) * 1000;

  const chartWidth = 1000;
  const rowHeight = 40;
  const chartHeight = data.requests.length * rowHeight;
  const timeScale = totalDurationMs > 0 ? chartWidth / totalDurationMs : 1;

  return (
    <div className="waterfall-container">
      <div className="waterfall-header">
        <h1>🎨 Request Waterfall</h1>
        <div className="controls">
          <label>
            Requests:
            <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
              <option value="20">20</option>
              <option value="50">50</option>
              <option value="100">100</option>
              <option value="200">200</option>
            </select>
          </label>
          <label>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh
          </label>
          <button onClick={fetchWaterfallData} className="refresh-btn">
            🔄 Refresh
          </button>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{data.stats.total_completed}</div>
          <div className="stat-label">Total Requests</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{data.stats.active_requests}</div>
          <div className="stat-label">Active Now</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{totalDurationMs.toFixed(0)}ms</div>
          <div className="stat-label">Time Window</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {data.requests.reduce((sum, r) => sum + r.output_tokens, 0)}
          </div>
          <div className="stat-label">Total Tokens</div>
        </div>
      </div>

      <div className="legend">
        <div className="legend-item">
          <div className="legend-color" style={{ background: '#4CAF50', opacity: 0.6 }} />
          <span>Request Duration</span>
        </div>
        <div className="legend-item">
          <div className="legend-color ttft-marker" />
          <span>TTFT Marker</span>
        </div>
      </div>

      <div className="chart-scroll">
        <svg width={chartWidth + 200} height={chartHeight + 60}>
          <g transform="translate(180, 30)">
            {data.requests.map((req, i) => {
              const y = i * rowHeight;
              const startOffsetMs = (req.start_time - earliestTime) * 1000;
              const xStart = startOffsetMs * timeScale;
              const barWidth = req.duration_ms * timeScale;

              return (
                <g key={req.request_id}>
                  {/* Request bar */}
                  <rect
                    x={xStart}
                    y={y}
                    width={barWidth}
                    height={rowHeight - 5}
                    fill={req.is_complete ? '#4CAF50' : '#FFA500'}
                    opacity="0.7"
                    rx="3"
                    className="request-bar"
                  />

                  {/* TTFT marker */}
                  {req.ttft_ms !== null && (
                    <line
                      x1={xStart + req.ttft_ms * timeScale}
                      y1={y}
                      x2={xStart + req.ttft_ms * timeScale}
                      y2={y + rowHeight - 5}
                      stroke="#FF5722"
                      strokeWidth="2"
                      strokeDasharray="4,2"
                    />
                  )}

                  {/* Request label */}
                  <text
                    x={-5}
                    y={y + rowHeight / 2}
                    textAnchor="end"
                    fontSize="11"
                    fill="#333"
                    dominantBaseline="middle"
                  >
                    {req.model.substring(0, 25)}
                  </text>

                  {/* Duration label */}
                  <text
                    x={xStart + barWidth + 5}
                    y={y + rowHeight / 2}
                    fontSize="10"
                    fill="#666"
                    dominantBaseline="middle"
                  >
                    {req.duration_ms.toFixed(0)}ms
                    {req.ttft_ms && ` (TTFT: ${req.ttft_ms.toFixed(0)}ms)`}
                  </text>
                </g>
              );
            })}

            {/* Time axis */}
            <line
              x1="0"
              y1={chartHeight}
              x2={chartWidth}
              y2={chartHeight}
              stroke="#999"
              strokeWidth="1"
            />

            {/* Time labels */}
            {[0, 0.25, 0.5, 0.75, 1].map((fraction) => {
              const x = chartWidth * fraction;
              const timeMs = totalDurationMs * fraction;
              return (
                <text
                  key={fraction}
                  x={x}
                  y={chartHeight + 20}
                  textAnchor="middle"
                  fontSize="11"
                  fill="#666"
                >
                  {timeMs.toFixed(0)}ms
                </text>
              );
            })}
          </g>
        </svg>
      </div>

      <div className="info-panel">
        <h3>💡 How to Read This Chart</h3>
        <ul>
          <li><strong>Horizontal bars</strong> show request duration from start to completion</li>
          <li><strong>Orange dashed lines</strong> mark Time To First Token (TTFT)</li>
          <li><strong>Bar length</strong> indicates total request latency</li>
          <li><strong>Overlapping bars</strong> show concurrent requests</li>
        </ul>
      </div>
    </div>
  );
};

export default Waterfall;
