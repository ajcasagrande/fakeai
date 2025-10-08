# FakeAI Dashboard

> A comprehensive, production-grade React dashboard for monitoring and managing FakeAI API services with real-time metrics, advanced analytics, and intuitive visualizations.

![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)
![React](https://img.shields.io/badge/React-18+-blue.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5+-blue.svg)

---

## Overview

The FakeAI Dashboard is a sophisticated web application providing real-time monitoring, analytics, and management capabilities for the FakeAI API service. Built with modern web technologies, it offers comprehensive insights into API usage, performance metrics, cost analytics, and organizational management.

### Key Features

- **Real-time Monitoring** - Live metrics with WebSocket streaming and auto-refresh
- **Chat Completions Analytics** - Comprehensive tracking of chat API usage with model-specific insights
- **Embeddings Monitoring** - Track embedding generation, token consumption, and cost analysis
- **Rate Limit Management** - Visual representation of rate limits, tier usage, and throttling analytics
- **KV Cache Metrics** - Monitor cache hit rates, block matching, and smart routing efficiency
- **Cost Analytics** - Detailed cost breakdowns by model, endpoint, and time period
- **Organization Management** - User management, project administration, and service accounts
- **Customizable Filters** - Date ranges, model selection, status filtering
- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile devices
- **Dark/Light Themes** - Customizable theming with CSS variables

---

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- FakeAI server running (default: http://localhost:8000)

### Installation & Setup

```bash
# Navigate to dashboard directory
cd fakeai/dashboard

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Access the Dashboard

- **Development**: http://localhost:5173
- **Production**: http://localhost:8000/dashboard (served by FakeAI server)

### Quick Configuration

Create a `.env` file in the dashboard directory:

```bash
# API Configuration
VITE_API_URL=http://localhost:8000

# Feature Flags
VITE_ENABLE_WEBSOCKETS=true
VITE_ENABLE_STREAMING_METRICS=true
```

---

## Dashboard Pages

### 1. Chat Completions

Monitor chat completion API usage with real-time metrics and detailed analytics.

**Features:**
- Total requests, tokens, costs, and latency metrics
- Model usage distribution (pie/bar charts)
- Token breakdown (prompt/completion/cached)
- Streaming vs non-streaming statistics
- Response time analysis by model
- Error rate tracking and visualization
- Cost visualization and trends
- Request details table with filtering
- Individual request inspection modal

**Location:** `/src/pages/ChatCompletions/`

### 2. Embeddings

Track embedding generation, token consumption, and model usage patterns.

**Features:**
- Embedding statistics overview
- Model usage distribution
- Token consumption tracking
- Recent embeddings table
- Usage trends over time
- Dimension distribution analysis
- Cost analysis and projections

**Location:** `/src/pages/Embeddings/`

### 3. Rate Limits

Comprehensive rate limiting management and analytics.

**Features:**
- Rate limit overview (RPM, TPM, RPD, TPD)
- Tier limits visualization
- Usage progress bars
- Throttle analytics
- Abuse pattern detection
- Top consumers identification
- Rate limit breaches timeline
- Tier distribution charts
- Tier upgrade recommendations

**Location:** `/src/pages/RateLimits/`

### 4. KV Cache

Monitor KV cache performance and smart routing efficiency.

**Features:**
- Cache hit rate tracking
- Block matching statistics
- Worker distribution analysis
- Cache overlap metrics
- Routing cost visualization
- Performance optimization insights

**Location:** `/src/pages/KVCache/`

### 5. Costs

Detailed cost analytics and breakdowns across all services.

**Features:**
- Total cost overview
- Cost breakdown by model
- Cost breakdown by endpoint
- Time-based cost trends
- Budget tracking
- Cost projections
- Export capabilities

**Location:** `/src/pages/Costs/`

### 6. Organization

Manage users, projects, invites, and service accounts.

**Features:**
- User management (create, edit, delete)
- Project management with role assignments
- Invitation system
- Project-specific user management
- Service account administration
- API key management

**Location:** `/src/pages/Organization/`

---

## Technology Stack

### Core Technologies

- **React 18** - Modern React with hooks and concurrent features
- **TypeScript 5** - Type-safe development with strict mode
- **Vite** - Fast build tool and development server
- **CSS Modules** - Component-scoped styling

### Key Libraries

- **Axios** - HTTP client with interceptors and retry logic
- **Recharts** - Composable charting library for React
- **Date-fns** - Modern JavaScript date utility library

### Architecture Patterns

- **Component-based Architecture** - Modular, reusable components
- **Custom Hooks** - Shared logic extraction
- **Context API** - Global state management
- **WebSocket Integration** - Real-time data streaming
- **API Client Layer** - Centralized API communication
- **Error Boundaries** - Graceful error handling

---

## Project Structure

```
fakeai/dashboard/
├── src/
│   ├── api/                    # API client and configuration
│   │   ├── auth.ts            # Authentication utilities
│   │   ├── cache.ts           # Response caching
│   │   ├── client.ts          # Axios instance with interceptors
│   │   ├── errors.ts          # Error handling
│   │   ├── types.ts           # API type definitions
│   │   └── endpoints/         # API endpoint modules
│   │
│   ├── services/              # Business logic and utilities
│   │   ├── WebSocketService.ts    # WebSocket management
│   │   ├── WebSocketContext.tsx   # WebSocket context provider
│   │   ├── hooks.ts               # Custom React hooks
│   │   ├── types.ts               # Service type definitions
│   │   └── components/            # Shared service components
│   │
│   └── pages/                 # Dashboard pages
│       ├── ChatCompletions/   # Chat completions monitoring
│       │   ├── ChatCompletions.tsx
│       │   ├── types.ts       # Page-specific types
│       │   ├── api.ts         # Page-specific API calls
│       │   ├── styles.css     # Page styles
│       │   └── components/    # Page components
│       │       ├── MetricsOverview.tsx
│       │       ├── ModelUsageChart.tsx
│       │       ├── TokenStats.tsx
│       │       ├── StreamingMetrics.tsx
│       │       ├── ResponseTimeChart.tsx
│       │       ├── ErrorRateChart.tsx
│       │       ├── RequestsTable.tsx
│       │       ├── RequestDetailsModal.tsx
│       │       ├── FilterPanel.tsx
│       │       └── CostVisualization.tsx
│       │
│       ├── Embeddings/        # Embeddings monitoring
│       ├── RateLimits/        # Rate limit management
│       ├── KVCache/           # KV cache metrics
│       ├── Costs/             # Cost analytics
│       └── Organization/      # Organization management
│
├── build.py                   # Build script for production
├── package.json              # Dependencies and scripts
├── tsconfig.json             # TypeScript configuration
├── vite.config.ts            # Vite configuration
└── README.md                 # This file
```

---

## Development Workflow

### Local Development

```bash
# Install dependencies
npm install

# Start development server with hot reload
npm run dev

# The dashboard will be available at http://localhost:5173
```

### Building for Production

```bash
# Build the dashboard
npm run build

# The built files will be in the dist/ directory

# Preview production build
npm run preview
```

### Integrating with FakeAI

The dashboard is designed to be served by the FakeAI server:

```bash
# Build and copy to static directory
python -m fakeai.dashboard.build

# Or use the CLI
cd fakeai/dashboard
python build.py

# Start FakeAI server (serves dashboard at /dashboard)
fakeai server
```

---

## API Integration

### API Client Configuration

The dashboard uses a centralized API client with:

- **Base URL Configuration** - Via environment variable `VITE_API_URL`
- **Authentication** - Bearer token from local storage
- **Request/Response Interceptors** - Automatic token injection and error handling
- **Retry Logic** - Exponential backoff for failed requests
- **Caching** - Configurable cache duration per endpoint
- **Error Transformation** - Unified error handling

### WebSocket Integration

Real-time metrics streaming via WebSocket:

```typescript
import { useWebSocket } from '@/services/hooks';

const { data, isConnected, error } = useWebSocket('/metrics/stream', {
  onMessage: (data) => console.log('Received:', data),
  reconnectInterval: 5000,
  maxReconnectAttempts: 10
});
```

---

## Customization

### Theming

The dashboard supports theming via CSS variables:

```css
:root {
  --primary-color: #3b82f6;
  --secondary-color: #8b5cf6;
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --error-color: #ef4444;
  --background-color: #ffffff;
  --text-color: #1f2937;
  --border-color: #e5e7eb;
}
```

### Environment Variables

Configure the dashboard via `.env`:

```bash
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Feature Flags
VITE_ENABLE_WEBSOCKETS=true
VITE_ENABLE_STREAMING_METRICS=true
VITE_AUTO_REFRESH_INTERVAL=30000

# UI Configuration
VITE_DEFAULT_PAGE_SIZE=20
VITE_DEFAULT_CHART_TYPE=pie
VITE_ENABLE_ANIMATIONS=true
```

---

## Performance Optimization

### Built-in Optimizations

- **Code Splitting** - Lazy loading of pages and components
- **Response Caching** - Intelligent cache with TTL
- **Memoization** - React.memo and useMemo for expensive computations
- **Debouncing** - Input debouncing for filters
- **Virtual Scrolling** - Efficient rendering of large tables
- **WebSocket Throttling** - Rate limiting for real-time updates

### Performance Monitoring

The dashboard tracks its own performance:

- Request latency tracking
- Component render times
- Memory usage monitoring
- Network waterfall analysis

---

## Browser Support

- **Chrome/Edge** - Latest 2 versions
- **Firefox** - Latest 2 versions
- **Safari** - Latest 2 versions

---

## Troubleshooting

### Common Issues

**Dashboard not loading:**
```bash
# Check if FakeAI server is running
curl http://localhost:8000/health

# Verify API URL in .env
echo $VITE_API_URL
```

**WebSocket connection failing:**
```bash
# Enable WebSocket debugging
VITE_DEBUG_WEBSOCKETS=true npm run dev
```

**Build errors:**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed guidelines on:

- Code style and conventions
- Component development guidelines
- Testing requirements
- Pull request process
- Documentation standards

---

## Documentation

- [DEVELOPMENT.md](./DEVELOPMENT.md) - Development setup and workflow
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Architecture and design decisions
- [COMPONENTS.md](./COMPONENTS.md) - Component documentation
- [API_INTEGRATION.md](./API_INTEGRATION.md) - API integration guide
- [THEMING.md](./THEMING.md) - Theming and customization
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment guide
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Troubleshooting guide

---

## License

Apache-2.0

---

## Support

- **Issues:** https://github.com/ajcasagrande/fakeai/issues
- **Discussions:** https://github.com/ajcasagrande/fakeai/discussions

---

**Built with React, TypeScript, and modern web technologies for world-class monitoring and analytics.**
