# Architecture Documentation

This document explains the architectural decisions, design patterns, and technical implementation details of the FakeAI Dashboard.

---

## Table of Contents

- [Overview](#overview)
- [Architecture Principles](#architecture-principles)
- [System Architecture](#system-architecture)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [State Management](#state-management)
- [API Layer](#api-layer)
- [WebSocket Integration](#websocket-integration)
- [Performance Optimization](#performance-optimization)
- [Security Considerations](#security-considerations)
- [Scalability](#scalability)
- [Technology Choices](#technology-choices)

---

## Overview

The FakeAI Dashboard is a production-grade React application built with TypeScript, designed for monitoring and managing the FakeAI API service. The architecture emphasizes:

- **Modularity** - Independent, reusable components
- **Type Safety** - Comprehensive TypeScript coverage
- **Performance** - Optimized rendering and data fetching
- **Maintainability** - Clear structure and documentation
- **Scalability** - Easy to extend and modify

---

## Architecture Principles

### 1. Separation of Concerns

The application is organized into distinct layers:

```
Presentation Layer (UI Components)
        ↓
Business Logic Layer (Services & Hooks)
        ↓
Data Access Layer (API Client)
        ↓
External Services (FakeAI Server)
```

### 2. Single Responsibility Principle

Each module has a single, well-defined purpose:

- **Components** - Render UI and handle user interactions
- **Services** - Business logic and data processing
- **API Client** - HTTP communication and error handling
- **Hooks** - Reusable stateful logic
- **Types** - Type definitions and interfaces

### 3. Dependency Inversion

Higher-level modules don't depend on lower-level modules. Both depend on abstractions:

```typescript
// Abstraction
interface DataService {
  fetchData(): Promise<Data>;
}

// Component depends on abstraction, not implementation
const Component = ({ service }: { service: DataService }) => {
  // Use service
};
```

### 4. Open/Closed Principle

The system is open for extension but closed for modification:

- New pages can be added without modifying existing code
- Components accept configuration props for customization
- API client supports middleware for extending functionality

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Browser                           │
│  ┌───────────────────────────────────────────────┐ │
│  │         React Application (SPA)                │ │
│  │                                                │ │
│  │  ┌──────────────────────────────────────────┐ │ │
│  │  │         Pages (Routes)                   │ │ │
│  │  │  - ChatCompletions                       │ │ │
│  │  │  - Embeddings                            │ │ │
│  │  │  - RateLimits                            │ │ │
│  │  │  - Organization                          │ │ │
│  │  └──────────────────────────────────────────┘ │ │
│  │                                                │ │
│  │  ┌──────────────────────────────────────────┐ │ │
│  │  │    Services & Hooks                      │ │ │
│  │  │  - WebSocketService                      │ │ │
│  │  │  - Custom Hooks                          │ │ │
│  │  └──────────────────────────────────────────┘ │ │
│  │                                                │ │
│  │  ┌──────────────────────────────────────────┐ │ │
│  │  │       API Client                         │ │ │
│  │  │  - Axios Instance                        │ │ │
│  │  │  - Interceptors                          │ │ │
│  │  │  - Cache                                 │ │ │
│  │  └──────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                      ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────┐
│              FakeAI Server (Python)                 │
│  - REST API Endpoints                               │
│  - WebSocket Streaming                              │
│  - Metrics Collection                               │
└─────────────────────────────────────────────────────┘
```

### Module Architecture

```
dashboard/
├── src/
│   ├── api/              # Data Access Layer
│   │   ├── client.ts     # HTTP client configuration
│   │   ├── auth.ts       # Authentication
│   │   ├── cache.ts      # Response caching
│   │   ├── errors.ts     # Error handling
│   │   └── endpoints/    # API endpoints
│   │
│   ├── services/         # Business Logic Layer
│   │   ├── WebSocketService.ts
│   │   ├── hooks.ts
│   │   └── components/
│   │
│   └── pages/            # Presentation Layer
│       ├── ChatCompletions/
│       ├── Embeddings/
│       └── ...
```

---

## Component Architecture

### Component Hierarchy

```
App
├── Router
│   ├── ChatCompletionsPage
│   │   ├── MetricsOverview
│   │   ├── ModelUsageChart
│   │   ├── TokenStats
│   │   ├── StreamingMetrics
│   │   ├── ResponseTimeChart
│   │   ├── ErrorRateChart
│   │   ├── RequestsTable
│   │   ├── FilterPanel
│   │   └── CostVisualization
│   │
│   ├── EmbeddingsPage
│   │   ├── EmbeddingStats
│   │   ├── ModelUsageChart
│   │   ├── TokenConsumption
│   │   └── ...
│   │
│   ├── RateLimitsPage
│   │   ├── RateLimitOverview
│   │   ├── TierLimitsVisualization
│   │   └── ...
│   │
│   └── ...
```

### Component Types

#### 1. Page Components

**Responsibility**: Orchestrate page layout and data fetching

```typescript
export const ChatCompletions: React.FC = () => {
  // Data fetching
  const { data, loading, error } = useChatCompletionsData();

  // Layout and composition
  return (
    <div className="page">
      <Header />
      <MetricsOverview data={data} />
      <Charts data={data} />
      <Table data={data} />
    </div>
  );
};
```

#### 2. Container Components

**Responsibility**: Manage state and business logic

```typescript
export const MetricsContainer: React.FC = () => {
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const metrics = useMetrics(filters);

  return <MetricsView metrics={metrics} onFilterChange={setFilters} />;
};
```

#### 3. Presentation Components

**Responsibility**: Pure UI rendering

```typescript
interface MetricsViewProps {
  metrics: Metrics;
  onFilterChange: (filters: Filters) => void;
}

export const MetricsView: React.FC<MetricsViewProps> = ({ metrics, onFilterChange }) => {
  return (
    <div>
      <MetricCard value={metrics.total} label="Total" />
      <FilterPanel onChange={onFilterChange} />
    </div>
  );
};
```

---

## Data Flow

### Unidirectional Data Flow

```
User Action
    ↓
Event Handler
    ↓
State Update / API Call
    ↓
Component Re-render
    ↓
UI Update
```

### Data Fetching Flow

```
Component Mount
    ↓
useEffect Hook
    ↓
API Client Request
    ↓
Server Response
    ↓
State Update
    ↓
Component Re-render
```

### Example: Fetching Chat Completions Data

```typescript
// 1. Component mounts
export const ChatCompletions: React.FC = () => {
  // 2. Initialize state
  const [data, setData] = useState<Data | null>(null);
  const [loading, setLoading] = useState(true);

  // 3. Fetch data on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        // 4. API call
        const response = await apiClient.get('/metrics/by-model');

        // 5. Update state
        setData(response.data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // 6. Render based on state
  if (loading) return <Loading />;
  if (!data) return <Error />;
  return <DataView data={data} />;
};
```

---

## State Management

### State Management Strategy

The dashboard uses a hybrid approach:

1. **Local State** (useState) - Component-specific state
2. **Context API** - Shared state (theme, auth, WebSocket)
3. **URL State** - Filters and pagination

### Local State

Used for component-specific state that doesn't need to be shared:

```typescript
const [selectedModel, setSelectedModel] = useState<string | null>(null);
const [chartType, setChartType] = useState<'pie' | 'bar'>('pie');
```

### Context API

Used for application-wide state:

```typescript
// WebSocket Context
const WebSocketContext = createContext<WebSocketContextValue>(null!);

export const WebSocketProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [data, setData] = useState<any>(null);

  // WebSocket logic
  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    ws.onopen = () => setIsConnected(true);
    ws.onmessage = (event) => setData(JSON.parse(event.data));
    return () => ws.close();
  }, []);

  return (
    <WebSocketContext.Provider value={{ isConnected, data }}>
      {children}
    </WebSocketContext.Provider>
  );
};
```

### URL State

Used for filters and navigation state:

```typescript
const [searchParams, setSearchParams] = useSearchParams();

// Read from URL
const model = searchParams.get('model');
const page = parseInt(searchParams.get('page') || '0');

// Update URL
const updateFilters = (model: string) => {
  setSearchParams({ model, page: '0' });
};
```

---

## API Layer

### API Client Architecture

```
┌─────────────────────────────────────────┐
│         API Client (Axios)              │
├─────────────────────────────────────────┤
│  Request Interceptors:                  │
│  - Add auth token                       │
│  - Check cache                          │
│  - Add request timestamp                │
├─────────────────────────────────────────┤
│         HTTP Request                    │
├─────────────────────────────────────────┤
│  Response Interceptors:                 │
│  - Calculate latency                    │
│  - Cache response                       │
│  - Handle errors                        │
│  - Retry failed requests                │
└─────────────────────────────────────────┘
```

### Request Lifecycle

```typescript
// 1. Request initiated
apiClient.get('/v1/models')

// 2. Request interceptor
// - Add Authorization header
// - Add timestamp
// - Check cache

// 3. HTTP request sent to server

// 4. Response received

// 5. Response interceptor
// - Calculate latency
// - Cache response
// - Transform data

// 6. Return to caller
```

### Error Handling Strategy

```typescript
try {
  const response = await apiClient.get('/v1/models');
  return response.data;
} catch (error) {
  if (error instanceof ApiError) {
    // Handle API errors
    switch (error.statusCode) {
      case 401:
        // Redirect to login
        break;
      case 429:
        // Show rate limit message
        break;
      case 500:
        // Show server error
        break;
    }
  } else {
    // Handle network errors
    console.error('Network error:', error);
  }
}
```

### Caching Strategy

Cache duration based on endpoint type:

- **Metrics** - 5 seconds (frequently changing)
- **Models** - 30 seconds (semi-static)
- **Organization** - 5 minutes (rarely changing)

```typescript
function getCacheDuration(url: string): number {
  if (url.includes('/metrics')) return 5000;
  if (url.includes('/models')) return 30000;
  if (url.includes('/organization')) return 300000;
  return 60000; // Default: 1 minute
}
```

---

## WebSocket Integration

### WebSocket Architecture

```
┌──────────────────────────────────────────┐
│      WebSocketService                    │
│  - Connection management                 │
│  - Reconnection logic                    │
│  - Message parsing                       │
│  - Event distribution                    │
└──────────────────────────────────────────┘
                ↓
┌──────────────────────────────────────────┐
│      WebSocketContext                    │
│  - Global state                          │
│  - Connection status                     │
│  - Latest data                           │
└──────────────────────────────────────────┘
                ↓
┌──────────────────────────────────────────┐
│      useWebSocket Hook                   │
│  - Subscribe to data                     │
│  - Handle updates                        │
│  - Error handling                        │
└──────────────────────────────────────────┘
```

### Connection Management

```typescript
class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;

  connect(url: string) {
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      this.handleDisconnect();
    };
  }

  private handleDisconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      setTimeout(() => {
        this.reconnectAttempts++;
        this.connect(this.url);
      }, delay);
    }
  }
}
```

---

## Performance Optimization

### 1. Code Splitting

Split code by route for faster initial load:

```typescript
// Lazy load pages
const ChatCompletions = lazy(() => import('./pages/ChatCompletions'));
const Embeddings = lazy(() => import('./pages/Embeddings'));

// Use Suspense
<Suspense fallback={<Loading />}>
  <Routes>
    <Route path="/chat" element={<ChatCompletions />} />
    <Route path="/embeddings" element={<Embeddings />} />
  </Routes>
</Suspense>
```

### 2. Memoization

Prevent unnecessary re-renders:

```typescript
// Memoize expensive computations
const metrics = useMemo(() => {
  return calculateMetrics(data);
}, [data]);

// Memoize components
const MetricsCard = React.memo<MetricsCardProps>(({ value, label }) => {
  return <div>{label}: {value}</div>;
});
```

### 3. Virtualization

Render only visible items in large lists:

```typescript
// For tables with 1000+ rows
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={items.length}
  itemSize={50}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>
      {items[index].name}
    </div>
  )}
</FixedSizeList>
```

### 4. Debouncing

Reduce API calls for user input:

```typescript
const debouncedSearch = useMemo(
  () =>
    debounce((query: string) => {
      fetchSearchResults(query);
    }, 300),
  []
);
```

### 5. Response Caching

Cache API responses to reduce server load:

- In-memory cache with TTL
- Cache invalidation on mutations
- Cache warming for frequently accessed data

---

## Security Considerations

### 1. Authentication

```typescript
// Store token securely
localStorage.setItem('auth_token', token);

// Add to all requests
axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

// Clear on logout
localStorage.removeItem('auth_token');
```

### 2. XSS Prevention

- Use React's built-in XSS protection (escapes user input)
- Sanitize HTML if using dangerouslySetInnerHTML
- Validate user input before rendering

### 3. CORS Configuration

```typescript
// API client respects CORS headers
// Server must configure:
// Access-Control-Allow-Origin
// Access-Control-Allow-Methods
// Access-Control-Allow-Headers
```

### 4. API Key Management

- Never commit API keys to source control
- Use environment variables
- Rotate keys regularly
- Use different keys for dev/prod

---

## Scalability

### Horizontal Scalability

The dashboard is stateless and can be deployed to multiple instances:

```
Load Balancer
    ↓
┌─────────┬─────────┬─────────┐
│ Instance│ Instance│ Instance│
│    1    │    2    │    3    │
└─────────┴─────────┴─────────┘
```

### Vertical Scalability

The application is optimized for performance:

- Lazy loading reduces initial bundle size
- Code splitting improves load times
- Memoization reduces re-renders
- Caching reduces API calls

### Future Scalability Considerations

- **State Management**: Consider Redux for complex state
- **GraphQL**: Consider GraphQL for flexible data fetching
- **Service Workers**: Add offline support
- **PWA**: Make it installable

---

## Technology Choices

### Why React?

- **Popular** - Large ecosystem and community
- **Component-based** - Reusable UI components
- **Virtual DOM** - Efficient rendering
- **Hooks** - Clean state management
- **TypeScript support** - First-class type safety

### Why TypeScript?

- **Type Safety** - Catch errors at compile time
- **Better IDE support** - Autocomplete and refactoring
- **Self-documenting** - Types serve as documentation
- **Refactoring confidence** - Safe to change code

### Why Vite?

- **Fast** - Instant dev server startup
- **Modern** - Native ES modules
- **HMR** - Fast hot module replacement
- **Optimized builds** - Tree shaking and code splitting

### Why Axios?

- **Interceptors** - Request/response transformation
- **Automatic transformations** - JSON parsing
- **Timeout support** - Request timeouts
- **Cancel requests** - AbortController support
- **TypeScript support** - Full type definitions

### Why Recharts?

- **React-based** - Native React components
- **Composable** - Build custom charts
- **Responsive** - Works on all screen sizes
- **Customizable** - Full styling control

---

## Future Architectural Improvements

### Short-term

1. **Add unit tests** - Jest + React Testing Library
2. **Add E2E tests** - Playwright or Cypress
3. **Error boundaries** - Better error handling
4. **Loading states** - Skeleton screens

### Medium-term

1. **Service workers** - Offline support
2. **Performance monitoring** - Real user monitoring
3. **Analytics** - Usage tracking
4. **A/B testing** - Feature flags

### Long-term

1. **Micro-frontends** - Split into smaller apps
2. **GraphQL** - Replace REST API
3. **Server-side rendering** - Next.js migration
4. **Real-time collaboration** - Multi-user support

---

## Conclusion

The FakeAI Dashboard architecture is designed for:

- **Developer experience** - Easy to understand and modify
- **Performance** - Fast load times and smooth interactions
- **Maintainability** - Clear structure and documentation
- **Scalability** - Ready to grow with the application

The architecture follows industry best practices and modern web development standards, ensuring a solid foundation for future development.

---

**For questions or suggestions, please open an issue on GitHub.**
