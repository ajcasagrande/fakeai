# Chat Completions Monitoring Dashboard

A comprehensive, real-time monitoring dashboard for OpenAI-compatible chat completion endpoints with NVIDIA theme styling.

## Features

### 1. Real-time Chat Request Monitoring
- Live metrics updates every 30 seconds (configurable)
- Manual refresh capability
- Auto-refresh toggle

### 2. Model Usage Breakdown
- **Pie Chart View**: Visual distribution of requests across models
- **Bar Chart View**: Comparative request counts with percentages
- Interactive visualizations with NVIDIA color palette

### 3. Token Usage Statistics
- Prompt tokens vs completion tokens breakdown
- Cached tokens tracking
- Visual token distribution bars
- Total and average token metrics

### 4. Streaming vs Non-Streaming Metrics
- Aggregate streaming percentage
- Per-model streaming breakdown
- Comparative latency analysis
- Request type distribution

### 5. Average Response Time by Model
- Multi-percentile visualization (P50, P90, P95, P99, Avg)
- Fastest and slowest model identification
- Interactive latency bars
- Color-coded performance indicators

### 6. Error Rate Tracking
- Overall error rate with status indicator
- Per-model error analysis
- Healthy models highlighting
- Critical models alerting
- Error rate trends

### 7. Recent Requests Table
- **Pagination**: 20 requests per page
- **Sorting**: Click column headers to sort
- **Real-time updates**: Auto-refreshes with main dashboard
- **Columns**:
  - Timestamp
  - Request ID
  - Model
  - Token usage (prompt + completion)
  - Latency
  - Cost
  - Type (streaming/standard)
  - Status (success/error)
  - Actions (view details)

### 8. Request Details Modal
- **Overview Tab**: Complete request metadata
- **Request Data Tab**: Full request payload with JSON formatting
- **Response Data Tab**: Full response payload with JSON formatting
- Copy-to-clipboard functionality
- Token distribution visualization
- Error message display

### 9. Filtering Capabilities
- **Model Filter**: Select specific models
- **Date Range Filter**:
  - Quick ranges (Last Hour, 24h, 7d, 30d, All Time)
  - Custom date range picker
- **Status Filter**: All, Success, Error
- **Request Type Filter**: All, Streaming, Non-Streaming
- Reset all filters functionality

### 10. Cost Per Request Visualization
- Total cost tracking
- Average cost per request
- Per-model cost breakdown with bar charts
- Cost efficiency rankings (top 10)
- Cost per 1K tokens analysis
- Projected costs (daily, monthly, annual)
- Medal rankings for most cost-efficient models

## Architecture

### Components

```
ChatCompletions/
├── ChatCompletions.tsx          # Main dashboard component
├── types.ts                     # TypeScript type definitions
├── api.ts                       # API client functions
├── styles.css                   # NVIDIA-themed styles
├── components/
│   ├── MetricsOverview.tsx      # High-level metrics cards
│   ├── ModelUsageChart.tsx      # Pie/Bar charts for model usage
│   ├── TokenStats.tsx           # Token usage breakdown
│   ├── StreamingMetrics.tsx     # Streaming analysis
│   ├── ResponseTimeChart.tsx    # Latency visualization
│   ├── ErrorRateChart.tsx       # Error tracking
│   ├── RequestsTable.tsx        # Paginated requests table
│   ├── RequestDetailsModal.tsx  # Request detail modal
│   ├── FilterPanel.tsx          # Filtering controls
│   └── CostVisualization.tsx    # Cost analysis
└── README.md                    # This file
```

### API Endpoints

The dashboard integrates with the following FakeAI endpoints:

1. **`GET /metrics/by-model`**
   - Returns metrics for all models
   - Used for: Model stats, latency, errors, costs

2. **`GET /v1/organization/usage/completions`**
   - Returns usage data by time buckets
   - Used for: Historical usage analysis
   - Query params: start_time, end_time, bucket_width, project_id, model

### Data Flow

```
┌─────────────────────────────────────────┐
│     ChatCompletions Component           │
│  (Main orchestrator & state manager)    │
└────────────┬────────────────────────────┘
             │
             ├──→ fetchModelMetrics()
             │    └─→ /metrics/by-model
             │
             ├──→ fetchCompletionsUsage()
             │    └─→ /v1/organization/usage/completions
             │
             └──→ fetchChatRequests()
                  └─→ Simulated (would be real endpoint)
```

## NVIDIA Theme

### Color Palette

- **Primary Green**: `#76B900` - NVIDIA brand color
- **Dark Gray**: `#1A1A1A` - Main backgrounds
- **Cyan**: `#00A9E0` - Accent color for data
- **Orange**: `#FF6B00` - Warnings
- **Purple**: `#9D5CC9` - Secondary accent
- **Black**: `#000000` - Deep backgrounds

### Design Principles

1. **Dark Theme**: Optimal for monitoring dashboards
2. **High Contrast**: Easy readability of metrics
3. **Color-Coded Status**: Instant visual feedback
4. **Smooth Animations**: Professional feel
5. **Responsive Design**: Works on all screen sizes

## Usage

### Basic Integration

```tsx
import { ChatCompletions } from './pages/ChatCompletions';

function App() {
  return <ChatCompletions />;
}
```

### With React Router

```tsx
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { ChatCompletions } from './pages/ChatCompletions';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/chat-completions" element={<ChatCompletions />} />
      </Routes>
    </BrowserRouter>
  );
}
```

### Environment Configuration

Create a `.env` file:

```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_KEY=your-api-key-here
```

## State Management

The dashboard uses React hooks for state management:

- `useState`: Component-level state
- `useEffect`: Data fetching and auto-refresh
- `useMemo`: Computed metrics and derived data
- `useCallback`: Memoized fetch functions

## Performance Optimizations

1. **Memoization**: Expensive calculations are memoized
2. **Virtual Scrolling**: Large tables use pagination
3. **Debounced Filters**: Filter changes are debounced
4. **Conditional Rendering**: Components only render when visible
5. **Code Splitting**: Lazy loading for modal components

## Customization

### Changing Refresh Interval

In `ChatCompletions.tsx`:

```tsx
const interval = setInterval(() => {
  fetchData();
}, 30000); // Change from 30000ms (30s) to desired interval
```

### Modifying Color Scheme

In `styles.css`, update CSS variables:

```css
:root {
  --nvidia-green: #76B900;      /* Change primary color */
  --nvidia-cyan: #00A9E0;       /* Change accent color */
  --bg-primary: #0A0A0A;        /* Change background */
}
```

### Adding Custom Metrics

1. Add type to `types.ts`
2. Fetch data in `api.ts`
3. Create component in `components/`
4. Import and use in `ChatCompletions.tsx`

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Dependencies

### Required

- React 18+
- TypeScript 4.5+

### Optional (for enhanced features)

- Chart.js or D3.js for advanced visualizations
- React Query for better data fetching
- Zustand/Redux for global state management

## Testing

### Unit Tests (Jest + React Testing Library)

```bash
npm test
```

### E2E Tests (Cypress)

```bash
npm run cypress:open
```

## Accessibility

- WCAG 2.1 AA compliant
- Keyboard navigation supported
- Screen reader friendly
- High contrast mode
- Focus indicators

## Known Limitations

1. **Request History**: Currently uses mock data. In production, connect to a real logging/database system.
2. **Real-time Updates**: WebSocket support would enable true real-time updates instead of polling.
3. **Large Datasets**: Consider implementing virtual scrolling for very large tables.

## Future Enhancements

- [ ] WebSocket integration for real-time updates
- [ ] Export functionality (CSV, PDF)
- [ ] Custom dashboard layouts (drag & drop)
- [ ] Alert configuration and notifications
- [ ] Dark/Light theme toggle
- [ ] Multi-language support
- [ ] Advanced filtering with query builder
- [ ] Time-series graphs for trends
- [ ] Comparison mode for multiple time periods
- [ ] Custom metric definitions

## Contributing

When contributing to this dashboard:

1. Follow the existing code style
2. Add TypeScript types for all new data structures
3. Update this README with new features
4. Maintain NVIDIA theme consistency
5. Test on multiple screen sizes
6. Ensure accessibility standards

## License

Apache-2.0

## Support

For issues or questions:
- Check the FakeAI documentation
- Review the API endpoints in `/home/anthony/projects/fakeai/fakeai/app.py`
- Examine existing components for patterns

---

**Built with React + TypeScript | Styled with NVIDIA Theme | Powered by FakeAI**
