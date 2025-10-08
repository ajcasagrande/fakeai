# Rate Limits Analytics Dashboard

A comprehensive, real-time rate limiting analytics dashboard with NVIDIA-themed design and alert-focused monitoring.

## Overview

The Rate Limits Dashboard provides detailed monitoring and analytics for API rate limits, throttling events, abuse patterns, and tier management. Built with React, TypeScript, and Framer Motion for smooth animations.

## Features

### 1. Rate Limit Status Overview
- **Total API Keys**: Count of all registered API keys
- **Total Requests**: Aggregate request count across all keys
- **Throttled Requests**: Number of requests blocked by rate limits
- **Throttle Rate**: Percentage of requests that were throttled
- **Active Breaches**: Current rate limit violations in progress
- **Abuse Patterns**: Detected suspicious usage patterns
- **Average Utilization**: Overall rate limit usage across all keys

### 2. Tier Limits Visualization
- Display all available rate limit tiers (Free, Tier 1-5)
- Show RPM (Requests Per Minute) limits
- Show TPM (Tokens Per Minute) limits
- Show RPD (Requests Per Day) limits
- Visual indicators for current and recommended tiers

### 3. Usage Progress Bars
- **Real-time monitoring** with 5-second updates
- Progress bars for RPM, TPM, and RPD usage
- Color-coded status indicators:
  - Green: Healthy (0-75%)
  - Yellow: Warning (75-90%)
  - Red: Critical (90%+)
- API key identification with throttle counts
- Animated progress bars with shimmer effects

### 4. Throttle Analytics (429 Errors)
- **Time-series visualization** of throttle events
- Breakdown by breach type (RPM, TPM, RPD)
- Area and line charts for trend analysis
- Summary statistics:
  - Total throttles
  - RPM/TPM/RPD-specific throttles
  - Peak throttles
  - Average throttles per period
- Custom tooltips with detailed information

### 5. Abuse Pattern Detection
- Automated detection of suspicious usage patterns:
  - **Burst Attacks**: Sudden spikes in request volume
  - **Sustained High Usage**: Continuous high load
  - **Distributed Patterns**: Geographic anomalies
  - **Suspicious Activity**: Unusual behavior patterns
- Severity levels: Low, Medium, High, Critical
- Detailed metrics:
  - Requests per second
  - Unique endpoints accessed
  - Error rate
  - Geographic distribution
- Recommended actions for each pattern
- Alert animations for critical patterns

### 6. Top Consumers
- Ranked list of highest-usage API keys
- Sortable by:
  - Total requests
  - Total tokens
  - Utilization percentage
- Metrics displayed:
  - Request count
  - Token count
  - Average RPM
  - Utilization percentage
  - Throttle count
- Visual utilization bars
- Last active timestamps

### 7. Rate Limit Breaches Timeline
- Chronological history of all rate limit violations
- Grouped by date
- Filterable by breach type (RPM, TPM, RPD, All)
- Interactive timeline with expandable details
- Visual indicators:
  - Timeline dots (red for active, green for resolved)
  - Color-coded breach types
  - Resolution status badges
- Detailed breach information:
  - Breach ID
  - Timestamp
  - Limit vs attempted value
  - Overage amount and percentage
  - Duration (if applicable)

### 8. Tier Distribution Pie Chart
- Visual representation of API key distribution across tiers
- Interactive pie chart with:
  - Percentage labels
  - Custom tooltips
  - Color-coded tiers
- Summary statistics:
  - Total API keys
  - Total requests
  - Total tokens
- Detailed breakdown table with:
  - Key count per tier
  - Share percentage
  - Request count
  - Token count

### 9. Tier Upgrade Recommendations
- Intelligent recommendations for tier upgrades
- Sortable by:
  - Priority (High, Medium, Low)
  - Throttle rate
  - Utilization percentage
- Detailed analysis:
  - Current vs recommended tier
  - Reasoning for recommendation
  - Key metrics (throttle rate, utilization, peak requests)
- Expected benefits:
  - Reduced throttles
  - Improved latency
- Priority indicators with alert styling
- Upgrade action buttons

### 10. Real-Time Rate Limit Monitoring
- **Live updates** every 5 seconds
- Toggle for real-time mode
- Live indicator with pulsing animation
- Auto-refresh capability (30-second intervals)
- Manual refresh option
- Last update timestamp

## Technology Stack

- **React 18**: Component framework
- **TypeScript**: Type safety
- **Framer Motion**: Smooth animations
- **Recharts**: Data visualization
- **Tailwind CSS**: Utility-first styling
- **Custom CSS**: NVIDIA-themed components

## API Endpoints

The dashboard consumes the following endpoints from `/metrics/rate-limits/*`:

### Core Endpoints
- `GET /metrics/rate-limits/overview` - Overall rate limits metrics
- `GET /metrics/rate-limits/by-api-key` - API key rate limit status
- `GET /metrics/rate-limits/by-api-key/:key` - Specific API key status
- `GET /metrics/rate-limits/breaches` - Rate limit breach history
- `GET /metrics/rate-limits/throttles` - Throttle analytics time series
- `GET /metrics/rate-limits/abuse-patterns` - Detected abuse patterns
- `GET /metrics/rate-limits/top-consumers` - Top API key consumers
- `GET /metrics/rate-limits/tier-distribution` - Tier distribution data
- `GET /metrics/rate-limits/upgrade-recommendations` - Tier upgrade suggestions
- `GET /metrics/rate-limits/real-time` - Real-time monitoring data

### Query Parameters

**Filtering (by-api-key endpoint)**:
- `api_key`: Filter by specific API key
- `tier`: Filter by tier (free, tier1-5)
- `status`: Filter by status (healthy, warning, critical, throttled)
- `start_time`: Start timestamp for date range
- `end_time`: End timestamp for date range

**Throttles endpoint**:
- `start_time`: Start timestamp
- `end_time`: End timestamp
- `bucket_width`: Time bucket width (e.g., "5m", "1h")

**Top consumers endpoint**:
- `limit`: Number of top consumers to return (default: 10)

## Components

### Main Dashboard
- `RateLimits.tsx`: Main dashboard container with state management

### Child Components
- `RateLimitOverview.tsx`: Overview metrics cards
- `TierLimitsVisualization.tsx`: Tier limits display
- `UsageProgressBars.tsx`: Real-time usage progress bars
- `ThrottleAnalytics.tsx`: Throttle event charts
- `AbusePatternDetection.tsx`: Abuse pattern alerts
- `TopConsumers.tsx`: Top consumers leaderboard
- `RateLimitBreachesTimeline.tsx`: Breach history timeline
- `TierDistributionChart.tsx`: Tier distribution pie chart
- `TierUpgradeRecommendations.tsx`: Upgrade recommendations

## Styling

### NVIDIA Theme
- **Primary Color**: NVIDIA Green (#76b900)
- **Background**: Dark gradients (#0a0a0a to #1a1a1a)
- **Accent Colors**:
  - Blue: #3b82f6
  - Yellow: #eab308
  - Orange: #f97316
  - Red: #ef4444
  - Purple: #a855f7

### Alert-Focused Design
- Pulsing borders for critical alerts
- Animated status indicators
- Color-coded severity levels
- Prominent alert banners
- Live update indicators

### Animations
- Framer Motion for smooth transitions
- Shimmer effects on progress bars
- Pulse animations for live data
- Fade and slide transitions
- Scale on hover

## Usage

### Installation

```bash
cd fakeai/dashboard
npm install
```

### Development

```bash
npm run dev
```

### Production Build

```bash
npm run build
```

### Environment Variables

Create a `.env` file:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_KEY=your-api-key-here
```

## Features by Component

### Auto-Refresh
- Configurable refresh intervals
- Manual refresh button
- Visual indicators for refresh status
- Efficient state management to prevent unnecessary re-renders

### Real-Time Monitoring
- WebSocket-ready architecture
- 5-second update intervals for critical data
- Optimistic UI updates
- Graceful degradation if real-time unavailable

### Filtering and Sorting
- Multiple filter options per component
- Sort by various metrics
- Persistent filter state
- URL query parameter support (future enhancement)

### Responsive Design
- Mobile-first approach
- Breakpoints for tablet and desktop
- Collapsible sections on mobile
- Touch-friendly controls

## Data Flow

1. **Initial Load**: Fetch all dashboard data on mount
2. **Auto-Refresh**: Update all data every 30 seconds
3. **Real-Time Mode**: Update critical data every 5 seconds
4. **Manual Refresh**: User-triggered full data refresh
5. **Filter Changes**: Re-fetch filtered data immediately

## Performance Optimization

- Memoized calculations for derived data
- Lazy loading for large datasets
- Debounced filter updates
- Virtualization for long lists (future enhancement)
- Code splitting by route

## Error Handling

- Graceful error messages
- Retry logic for failed requests
- Loading states for all async operations
- Error boundaries for component failures

## Accessibility

- Semantic HTML structure
- ARIA labels for interactive elements
- Keyboard navigation support
- Color contrast compliance
- Screen reader friendly

## Future Enhancements

1. **Export Functionality**: Export data to CSV/PDF
2. **Custom Alerts**: User-defined alert thresholds
3. **Historical Analysis**: Long-term trend analysis
4. **Predictive Analytics**: ML-based usage predictions
5. **WebSocket Support**: True real-time updates
6. **Custom Dashboards**: User-configurable layouts
7. **API Key Management**: Inline tier upgrades
8. **Notification System**: Email/Slack alerts

## Contributing

When adding new features:
1. Follow existing component patterns
2. Add TypeScript types for all data
3. Include loading and error states
4. Add animations for smooth transitions
5. Update this README

## License

Part of the FakeAI project.
