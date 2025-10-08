# Embeddings Dashboard - Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Embeddings Dashboard                        │
│                      (Embeddings.tsx)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Manages State & API Calls
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐     ┌──────────────┐
│  API Layer   │      │ State Layer  │     │   UI Layer   │
└──────────────┘      └──────────────┘     └──────────────┘
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐     ┌──────────────┐
│ /v1/org/...  │      │   useState   │     │  Components  │
│  /embeddings │      │  useCallback │     │   Render     │
│   /metrics   │      │  useEffect   │     └──────────────┘
└──────────────┘      └──────────────┘
```

## Component Hierarchy

```
EmbeddingsDashboard (Main Container)
│
├── Header
│   ├── Title
│   └── Subtitle
│
├── ControlBar
│   ├── TimeRangeSelector
│   ├── ModelFilter
│   ├── AutoRefreshToggle
│   └── ExportButtons
│       ├── ExportJSON
│       └── ExportCSV
│
├── EmbeddingStats (Key Metrics)
│   ├── TotalRequests
│   ├── TotalTokens
│   ├── AvgProcessingTime
│   ├── RequestsPerSecond
│   ├── TokensPerSecond
│   └── ErrorRate
│
├── DashboardGrid (Charts)
│   ├── LeftColumn
│   │   ├── UsageTrends
│   │   └── TokenConsumption
│   └── RightColumn
│       ├── ModelUsageChart
│       └── DimensionDistribution
│
├── CostAnalysis
│   └── CostBreakdownTable
│
├── RecentEmbeddingsTable
│   └── EmbeddingsList
│
└── RefreshIndicator
    ├── Spinner
    └── LastUpdateTime
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER INTERACTION                                             │
│    - Select time range / model                                  │
│    - Click refresh / toggle auto-refresh                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. STATE UPDATE                                                 │
│    - timeRange, selectedModel, autoRefresh                      │
│    - Triggers useEffect hook                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. API CALLS                                                    │
│    - GET /v1/organization/usage/embeddings                      │
│    - GET /metrics                                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. DATA PROCESSING                                              │
│    - processUsageData()                                         │
│    - Calculate metrics, trends, costs                           │
│    - Generate chart data                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. STATE UPDATE                                                 │
│    - setMetrics(), setModelUsage(), etc.                        │
│    - Trigger re-render                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. COMPONENT RENDER                                             │
│    - Charts draw on canvas                                      │
│    - Tables populate with data                                  │
│    - Stats update with new values                               │
└─────────────────────────────────────────────────────────────────┘
```

## State Management

### Primary State Variables

```typescript
// Loading & UI State
const [isLoading, setIsLoading] = useState(true);
const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
const [autoRefresh, setAutoRefresh] = useState(true);
const [timeRange, setTimeRange] = useState('24h');
const [selectedModel, setSelectedModel] = useState('all');

// Data State
const [metrics, setMetrics] = useState<EmbeddingMetrics>({...});
const [modelUsage, setModelUsage] = useState<ModelUsageStats[]>([]);
const [dimensionStats, setDimensionStats] = useState<DimensionStats[]>([]);
const [recentEmbeddings, setRecentEmbeddings] = useState<RecentEmbedding[]>([]);
const [usageTrends, setUsageTrends] = useState<UsageTrendPoint[]>([]);
const [costBreakdown, setCostBreakdown] = useState<CostBreakdown[]>([]);
```

## Component Communication

```
┌───────────────────────────────────────────────────────────────┐
│              Props-Based Communication                         │
└───────────────────────────────────────────────────────────────┘

Parent (Embeddings.tsx)
    │
    ├──► EmbeddingStats (data: metrics, isLoading)
    │
    ├──► ModelUsageChart (data: modelUsage, isLoading)
    │
    ├──► TokenConsumption (data: usageTrends, isLoading)
    │
    ├──► RecentEmbeddingsTable (embeddings: recentEmbeddings, isLoading)
    │
    ├──► UsageTrends (data: usageTrends, isLoading)
    │
    ├──► DimensionDistribution (data: dimensionStats, isLoading)
    │
    └──► CostAnalysis (data: costBreakdown, isLoading)
```

## Canvas Chart Architecture

### Chart Rendering Pipeline

```
1. Component Mount
   └─► useEffect triggered
       └─► Canvas ref available?
           └─► Data available?
               └─► Draw chart

2. Chart Drawing Steps
   ├─► Set canvas size (with DPI scaling)
   ├─► Clear canvas
   ├─► Calculate dimensions (padding, scales)
   ├─► Draw grid
   ├─► Draw data (bars, lines, pie slices)
   ├─► Draw axes
   ├─► Draw labels
   ├─► Draw legend
   └─► Draw title

3. Cleanup
   └─► Component unmount
       └─► Canvas automatically cleaned up
```

### Chart Types

```
ModelUsageChart
├─► Type: Bar Chart
├─► X-axis: Models
├─► Y-axis: Requests/Tokens
└─► Features: Grouped bars, labels

TokenConsumption
├─► Type: Area Chart
├─► X-axis: Time
├─► Y-axis: Tokens
└─► Features: Line + fill, points

UsageTrends
├─► Type: Dual-Axis Line Chart
├─► X-axis: Time
├─► Y-axis Left: Requests
├─► Y-axis Right: Processing Time
└─► Features: Two lines, dual scale

DimensionDistribution
├─► Type: Pie Chart
├─► Data: Dimensions
├─► Values: Percentages
└─► Features: Slices, legend, labels
```

## API Integration Layer

### Endpoint: `/v1/organization/usage/embeddings`

```typescript
interface EmbeddingUsageRequest {
  start_time: number;      // Unix timestamp
  end_time: number;        // Unix timestamp
  bucket_width: string;    // '1m', '1h', '1d'
  project_id?: string;     // Optional
  model?: string;          // Optional
}

interface EmbeddingUsageResponse {
  object: "organization.usage.result";
  data: EmbeddingBucket[];
  has_more: boolean;
}

interface EmbeddingBucket {
  aggregation_timestamp: number;
  num_model_requests: number;
  operation: string;
  snapshot_id: string;
  num_input_tokens: number;
  num_cached_tokens?: number;
  project_id?: string;
  model?: string;
}
```

### Endpoint: `/metrics`

```typescript
interface MetricsResponse {
  requests: {
    [endpoint: string]: {
      rate: number;
    };
  };
  responses: {
    [endpoint: string]: {
      avg: number;
      p50: number;
      p90: number;
      p99: number;
      min: number;
      max: number;
      rate: number;
    };
  };
  errors: {
    [endpoint: string]: {
      rate: number;
    };
  };
  tokens: {
    [endpoint: string]: {
      rate: number;
    };
  };
}
```

## Data Processing Pipeline

### Step 1: Fetch Data
```typescript
const { start, end } = getTimeRange();
const response = await fetch(`${API_BASE_URL}/v1/organization/usage/embeddings?...`);
const data = await response.json();
```

### Step 2: Aggregate Metrics
```typescript
const totalRequests = data.data.reduce((sum, bucket) =>
  sum + bucket.num_model_requests, 0
);

const totalTokens = data.data.reduce((sum, bucket) =>
  sum + bucket.num_input_tokens, 0
);
```

### Step 3: Calculate Rates
```typescript
const timeSpan = data.data.length > 0
  ? (data.data[data.data.length - 1].timestamp - data.data[0].timestamp)
  : 3600;

const requestsPerSecond = totalRequests / timeSpan;
const tokensPerSecond = totalTokens / timeSpan;
```

### Step 4: Process Model Stats
```typescript
const modelMap = new Map<string, ModelUsageStats>();

data.data.forEach(bucket => {
  const model = bucket.model || 'unknown';
  // Aggregate by model
  // Calculate costs
});

setModelUsage(Array.from(modelMap.values()));
```

### Step 5: Generate Trends
```typescript
const trends = data.data.map(bucket => ({
  timestamp: bucket.aggregation_timestamp,
  requests: bucket.num_model_requests,
  tokens: bucket.num_input_tokens,
  avg_processing_time: avgProcessingTime,
}));

setUsageTrends(trends);
```

## Performance Optimizations

### 1. Memoization
```typescript
const getTimeRange = useCallback(() => {
  // Memoized calculation
}, [timeRange]);

const fetchEmbeddingsData = useCallback(async () => {
  // Memoized API call
}, [getTimeRange, selectedModel]);
```

### 2. Canvas Efficiency
```typescript
// High DPI scaling
canvas.width = rect.width * window.devicePixelRatio;
canvas.height = rect.height * window.devicePixelRatio;
ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

// Single-pass rendering
// No unnecessary redraws
```

### 3. Auto-Refresh Control
```typescript
useEffect(() => {
  fetchEmbeddingsData();

  if (autoRefresh) {
    const interval = setInterval(fetchEmbeddingsData, REFRESH_INTERVAL);
    return () => clearInterval(interval); // Cleanup
  }
}, [autoRefresh, fetchEmbeddingsData]);
```

## Error Handling

```typescript
try {
  // API call
  const response = await fetch(...);
  const data = await response.json();
  processUsageData(data);
} catch (error) {
  console.error('Error fetching embeddings data:', error);
  setIsLoading(false);
  // Display error state in UI
}
```

## Type Safety

All data structures are strictly typed:

```typescript
// No 'any' types (except for external API data)
// All props interfaces defined
// Compile-time type checking
// IntelliSense support
```

## Responsive Design Strategy

### Breakpoints

```css
/* Mobile: < 768px */
.embeddings-dashboard {
  padding: var(--spacing-md);
}

/* Tablet: 768px - 1024px */
@media (min-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Desktop: >= 1024px */
@media (min-width: 1024px) {
  .dashboard-grid {
    grid-template-columns: 2fr 1fr;
  }
}
```

## Security Considerations

1. **API Authentication**: Requires API key in headers
2. **CORS**: Configured for allowed origins
3. **Input Validation**: Time ranges, model names validated
4. **XSS Prevention**: React's built-in escaping
5. **No Sensitive Data**: No credentials in code

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                         │
└─────────────────────────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼                             ▼
┌──────────────────┐          ┌──────────────────┐
│  React App       │          │  React App       │
│  (Dashboard)     │          │  (Dashboard)     │
└──────────────────┘          └──────────────────┘
          │                             │
          └──────────────┬──────────────┘
                         │
                         ▼
          ┌─────────────────────────────┐
          │      FakeAI API Server      │
          │  (/v1/organization/usage)   │
          │        (/metrics)           │
          └─────────────────────────────┘
                         │
                         ▼
          ┌─────────────────────────────┐
          │      Database / Storage     │
          │    (Metrics & Usage Data)   │
          └─────────────────────────────┘
```

## Testing Strategy

### Unit Tests
- Component rendering
- Data transformation functions
- State management
- Export functionality

### Integration Tests
- API mocking
- Full data flow
- Component interaction
- Chart rendering

### E2E Tests
- User workflows
- Time range selection
- Export operations
- Auto-refresh

## Monitoring & Observability

```
Application Metrics:
├─► API Response Times
├─► Chart Render Times
├─► User Interactions
├─► Error Rates
└─► Resource Usage

User Analytics:
├─► Page Views
├─► Feature Usage
├─► Export Frequency
└─► Time Range Preferences
```

---

**Last Updated**: 2025-10-06
**Architecture Version**: 1.0
**Status**: Production Ready
