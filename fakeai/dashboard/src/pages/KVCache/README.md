# KV Cache Analytics Dashboard

A comprehensive, performance-optimized analytics dashboard for monitoring and analyzing Key-Value (KV) cache performance in AI/ML workloads. Built with React, TypeScript, and Recharts, featuring an NVIDIA-themed design optimized for high-performance computing environments.

## Overview

The KV Cache Analytics Dashboard provides real-time insights into cache performance, efficiency metrics, cost savings, and optimization opportunities. It's designed for AI/ML engineers, DevOps teams, and system administrators who need to monitor and optimize caching strategies for large language models and AI inference workloads.

## Features

### 1. Cache Hit/Miss Rate Visualization
- **Real-time tracking** of cache hit and miss rates over time
- **Area charts** showing trends and patterns
- **Color-coded metrics** for quick performance assessment
- Hit/miss ratio calculations and historical trends

### 2. Cache Size and Utilization
- **Memory usage monitoring** with visual indicators
- **Cache size tracking** over time
- **Utilization percentage** calculations
- **Capacity planning** insights

### 3. Speedup Metrics
- **Performance comparison** between cached and non-cached requests
- **Latency reduction** measurements in milliseconds
- **Throughput improvements** displayed as percentage gains
- **Request rate comparisons** (req/s with vs without cache)
- **Time savings** calculations per request and total

### 4. Token Savings from Cache
- **Cumulative token savings** visualization
- **Token distribution** pie charts
- **Savings percentage** tracking
- **Efficiency ratio** calculations (tokens per hit vs miss)

### 5. Cache Efficiency by Model
- **Per-model performance** breakdown
- **Sortable metrics** (hit rate, speedup, cost savings)
- **Interactive model selection** for detailed analysis
- **Comparative visualizations** across models
- **Detailed model statistics** including latency, evictions, and memory usage

### 6. Memory Usage Tracking
- **Real-time memory monitoring**
- **Memory allocation** visualization
- **Utilization trends** over time
- **Memory pressure** indicators

### 7. Eviction Statistics
- **Eviction count tracking** with rate calculations
- **Eviction reasons breakdown** (pie chart visualization)
- **Eviction timeline** (bar chart over time)
- **Average cache age** on eviction
- **Evicted data size** tracking

### 8. Cache Warm-up Status
- **Visual status indicators** (Cold, Warming, Warm, Hot)
- **Progress bar** with percentage complete
- **Entries loaded** vs total entries
- **Warmup time** measurements
- **Last warmup timestamp**
- **Manual warmup trigger** button
- **Status explanations** and meanings

### 9. Performance Impact Charts
- **Speedup factor** line charts over time
- **Performance metrics grid** with multiple indicators
- **Latency reduction** visualizations
- **Throughput increase** percentages
- **Comparative analysis** tools

### 10. Cost Savings from Caching
- **Total savings** calculations
- **Cost per token comparison** (with vs without cache)
- **Projected savings** (monthly and yearly)
- **Savings percentage** tracking
- **ROI calculations** and visualizations
- **Cost efficiency** metrics

## API Integration

The dashboard integrates with the `/kv-cache/metrics` endpoint to fetch real-time data:

```typescript
GET /kv-cache/metrics
Query Parameters:
  - start_time: number (Unix timestamp)
  - end_time: number (Unix timestamp)
  - model: string (optional, filter by specific model)
  - granularity: '1m' | '5m' | '15m' | '1h' | '1d'

Response: KVCacheResponse {
  metrics: KVCacheMetrics
  model_efficiency: ModelCacheEfficiency[]
  time_series: CacheTimeSeriesData[]
  eviction_stats: CacheEvictionStats
  warmup_status: CacheWarmupStatus
  performance_impact: CachePerformanceImpact
  cost_savings: CacheCostSavings
}
```

Additional endpoints:
- `GET /kv-cache/models` - Fetch available models with cache enabled
- `POST /kv-cache/warmup` - Trigger cache warmup for a model
- `POST /kv-cache/clear` - Clear cache (all or specific model)

## Component Structure

```
KVCache/
├── KVCache.tsx                    # Main dashboard component
├── types.ts                       # TypeScript type definitions
├── api.ts                         # API client functions
├── styles.css                     # NVIDIA-themed styles
├── index.ts                       # Export file
├── README.md                      # Documentation
└── components/
    ├── CacheMetricsOverview.tsx   # High-level metrics cards
    ├── HitMissChart.tsx          # Hit/miss rate visualization
    ├── CacheSizeUtilization.tsx  # Size and memory tracking
    ├── SpeedupMetrics.tsx        # Performance improvements
    ├── TokenSavings.tsx          # Token savings analytics
    ├── ModelEfficiency.tsx       # Per-model breakdown
    ├── EvictionStats.tsx         # Eviction analytics
    ├── WarmupStatus.tsx          # Warmup progress tracking
    └── CostSavings.tsx           # Cost analysis
```

## Key Metrics Tracked

### Performance Metrics
- Cache hit rate (%)
- Cache miss rate (%)
- Average speedup factor (x)
- Latency reduction (ms, %)
- Throughput increase (%)
- Requests per second (with/without cache)

### Resource Metrics
- Cache size (bytes, MB, GB)
- Memory usage (bytes, MB, GB)
- Cache utilization (%)
- Memory utilization (%)
- Eviction count and rate

### Efficiency Metrics
- Tokens saved (total count)
- Token savings percentage (%)
- Average tokens per hit
- Average tokens per miss
- Efficiency ratio

### Cost Metrics
- Total cost savings ($)
- Cost per token (with/without cache)
- Savings percentage (%)
- Projected monthly savings ($)
- Projected yearly savings ($)
- ROI calculations

## Design System

### NVIDIA Theme Colors
- **Primary Green**: `#76b900` - Main brand color
- **Speedup Green**: `#00ff88` - Performance improvements
- **Cache Blue**: `#00bfff` - Cache-related metrics
- **Warning Orange**: `#ff9900` - Warnings and alerts
- **Error Red**: `#ff6b6b` - Errors and poor performance
- **Background Black**: `#000000` - Primary background
- **Dark Gray**: `#1a1a1a` - Card backgrounds
- **Medium Gray**: `#2d2d2d` - Secondary backgrounds

### Status Indicators
- **Excellent**: `#76b900` (≥80% hit rate)
- **Good**: `#00bfff` (60-80% hit rate)
- **Warning**: `#ff9900` (40-60% hit rate)
- **Poor**: `#ff6b6b` (<40% hit rate)

### Warmup Status Colors
- **Hot**: `#ff4500` - Optimal performance
- **Warm**: `#00bfff` - Good performance
- **Warming**: `#ff9900` - In progress
- **Cold**: `#999999` - Not optimized

## Features in Detail

### Interactive Charts
All charts are built with Recharts and feature:
- Responsive design
- Interactive tooltips
- Smooth animations
- NVIDIA-themed gradients
- Real-time updates (30s auto-refresh)

### Filtering Capabilities
- **Model filtering**: View data for specific models
- **Time range selection**: Custom date/time ranges
- **Time granularity**: 1m, 5m, 15m, 1h, 1d intervals
- **Real-time filtering**: Instant updates on filter changes

### Auto-refresh
- Toggle auto-refresh on/off
- 30-second refresh interval
- Manual refresh button
- Last updated timestamp

### Cache Management
- **Clear cache**: Remove all or model-specific cache entries
- **Trigger warmup**: Pre-load cache for optimal performance
- **Status monitoring**: Track warmup progress in real-time

## Usage

### Basic Integration

```typescript
import { KVCache } from './pages/KVCache';

function App() {
  return (
    <div className="app">
      <KVCache />
    </div>
  );
}
```

### With Router

```typescript
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { KVCache } from './pages/KVCache';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/kv-cache" element={<KVCache />} />
      </Routes>
    </BrowserRouter>
  );
}
```

## Performance Optimization

The dashboard is built with performance in mind:

1. **Memoization**: Heavy computations are memoized using `React.useMemo`
2. **Lazy loading**: Components load data on demand
3. **Efficient re-renders**: Only update when data changes
4. **Debounced filters**: Filter changes are optimized
5. **Skeleton loaders**: Smooth loading states
6. **Responsive design**: Optimized for all screen sizes

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Dependencies

- React 18+
- TypeScript 4.5+
- Recharts 2.5+
- Modern browser with ES6+ support

## Accessibility

The dashboard includes:
- ARIA labels for screen readers
- Keyboard navigation support
- High contrast colors
- Focus indicators
- Semantic HTML structure

## Future Enhancements

Potential additions for future versions:
- Export data to CSV/JSON
- Custom alert thresholds
- Comparison mode (multiple time periods)
- Advanced filtering (regex, multi-select)
- Dashboard customization (drag-drop widgets)
- Cache prediction analytics
- ML-based optimization suggestions

## Contributing

When contributing to this dashboard:
1. Follow the existing code style
2. Add TypeScript types for all new features
3. Update this README with new features
4. Test on multiple screen sizes
5. Ensure NVIDIA theme consistency

## License

Part of the FakeAI project.

## Support

For issues, questions, or contributions, please refer to the main FakeAI repository.

---

**Built with performance in mind for NVIDIA-powered AI workloads.**
