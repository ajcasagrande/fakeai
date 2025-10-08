# Cost Tracking Dashboard

A comprehensive financial analytics dashboard for tracking and analyzing AI API costs with real-time monitoring, budget alerts, and detailed cost breakdowns.

## Features

### 1. Total Cost Overview with Trend
- **High-level metrics**: Total cost, average daily cost, cost per request, active services
- **Trend indicators**: Visual up/down/stable indicators with percentage changes
- **Period comparison**: Current vs previous period cost analysis
- **NVIDIA-themed cards**: Financial-focused design with green accents

### 2. Cost Breakdown by Service
- **Service-level analysis**: Chat, embeddings, images, audio, fine-tuning, assistants, batch
- **Pie/Donut charts**: Interactive visualizations with hover effects
- **Cost composition**: Input/output cost breakdown for each service
- **Percentage breakdown**: Shows each service's contribution to total cost

### 3. Cost by Model with Charts
- **Model rankings**: Sortable by total cost or efficiency
- **Horizontal bar charts**: Visual comparison with color-coded bars
- **Token breakdown**: Input/output token distribution per model
- **Detailed metrics**: Cost per request, cost per 1K tokens, request counts
- **Top N display**: Configurable to show top 5, 10, 15, 20, or all models

### 4. Daily/Weekly/Monthly Cost Trends
- **Time series charts**: Line charts with area fills
- **View modes**: Toggle between daily, weekly, and monthly aggregations
- **Interactive tooltips**: Hover to see exact costs and request counts
- **Trend statistics**: Average, peak, and lowest costs displayed
- **Grid lines**: Clear y-axis labels with formatted cost values

### 5. Top Cost Contributors
- **Model rankings**: Top 5 models by total cost
- **Service rankings**: Top services by percentage
- **Quick metrics**: Request counts and efficiency metrics
- **Ranked display**: #1-5 with visual rank badges

### 6. Budget Alerts and Thresholds
- **Configurable budgets**: Set daily and monthly budget limits
- **Real-time alerts**: Visual warnings at 75% and critical alerts at 90%
- **Progress bars**: Color-coded (green/yellow/red) based on usage
- **Projected monthly costs**: Automatic calculation based on daily average
- **Alert messages**: Actionable notifications when thresholds are exceeded

### 7. Cost Projections
- **Multiple time periods**: 7-day, 30-day, 90-day, and annual projections
- **Confidence levels**: Percentage-based confidence indicators (95% to 60%)
- **Growth-adjusted**: Incorporates historical growth trends
- **Daily averages**: Shows projected daily cost for each period
- **Disclaimer**: Clear indication that projections are estimates

### 8. Export Cost Reports
- **Multiple formats**: CSV, JSON, and PDF export options
- **Comprehensive data**: Includes all cost breakdowns and analytics
- **Date range export**: Exports data for selected time period
- **One-click download**: Simple download button with format selection
- **Export info**: Shows period and format details

### 9. Filter by Date Range, Service, Model
- **Date presets**: Today, Yesterday, Last 7/30 days, This/Last month
- **Custom date range**: Manual start and end date selection
- **Service filter**: Filter by specific service type
- **Model filter**: Filter by specific model
- **Group by**: Aggregate by day, week, or month
- **Reset filters**: Quick reset to default view

### 10. Cost Efficiency Metrics
- **Average cost per request**: Overall efficiency metric
- **Cost per 1K tokens**: Token-based efficiency comparison
- **Most/Least efficient models**: Identifies best and worst performers
- **Efficiency rankings**: Top 5 models ranked by cost per token
- **Efficiency scores**: 0-100 score based on relative performance
- **Visual comparison**: Score bars and rankings

## API Endpoints Used

### `/v1/organization/costs`
- Fetches cost data grouped by time buckets
- Supports filtering by project, date range, and grouping
- Returns cost results with line items and amounts

### `/metrics/costs`
- Provides aggregated cost metrics
- Returns cost by service and model
- Includes time period information

## Technology Stack

- **React**: Component-based UI
- **TypeScript**: Type-safe development
- **CSS3**: Custom styling with NVIDIA theme
- **SVG**: Custom charts and visualizations
- **Date API**: Native JavaScript date handling

## File Structure

```
/pages/Costs/
├── Costs.tsx                      # Main dashboard component
├── types.ts                       # TypeScript type definitions
├── api.ts                         # API client functions
├── styles.css                     # Dashboard styles
├── index.ts                       # Module exports
├── README.md                      # Documentation
└── components/
    ├── CostOverview.tsx           # Overview cards
    ├── ServiceBreakdown.tsx       # Service pie/donut chart
    ├── ModelCostChart.tsx         # Model horizontal bar chart
    ├── CostTrends.tsx             # Time series line chart
    ├── TopContributors.tsx        # Top models and services
    ├── BudgetAlerts.tsx           # Budget monitoring
    ├── CostProjections.tsx        # Cost projections
    ├── ExportReports.tsx          # Export functionality
    ├── CostFilters.tsx            # Filter controls
    ├── EfficiencyMetrics.tsx      # Efficiency analysis
    └── index.ts                   # Component exports
```

## Usage

### Import and Use

```typescript
import { Costs } from './pages/Costs';

// In your app
<Costs />
```

### Access Components Individually

```typescript
import {
  CostOverview,
  ServiceBreakdown,
  ModelCostChart,
  CostTrends,
  BudgetAlerts,
} from './pages/Costs';

// Use components separately
<CostOverview costData={data} loading={false} />
```

### Export Cost Data

```typescript
import { exportCostData, downloadBlob } from './pages/Costs';

// Export as CSV
const blob = await exportCostData('csv', startTime, endTime);
downloadBlob(blob, 'cost-report.csv');
```

## Features Highlights

### Financial-Focused Design
- Professional dark theme with NVIDIA green accents
- High contrast for readability
- Hover effects and smooth transitions
- Responsive grid layouts

### Real-Time Monitoring
- Auto-refresh toggle (5-minute intervals)
- Manual refresh button
- Loading states with skeletons
- Error handling with user-friendly messages

### Interactive Visualizations
- Hover tooltips on charts
- Click interactions on chart elements
- Sortable tables and lists
- Expandable sections

### Budget Management
- Configurable daily and monthly budgets
- Visual progress bars
- Color-coded alerts (green/yellow/red)
- Animated pulse effect for critical alerts

### Data Export
- CSV for spreadsheet analysis
- JSON for programmatic processing
- PDF for reports and documentation
- Includes all metrics and breakdowns

## Color Scheme (NVIDIA Theme)

- **Primary Green**: #76B900 (NVIDIA signature)
- **Dark Background**: #000000, #111111, #1A1A1A
- **Borders**: #333333, #444444
- **Text**: #FFFFFF (primary), #B3B3B3 (secondary), #808080 (tertiary)
- **Accents**: #00FFFF (cyan), #9D00FF (purple), #FFA500 (orange)
- **Alerts**: #FF3333 (critical), #FFA500 (warning), #76B900 (success)

## Responsive Design

- Desktop: Full grid layout with sidebar
- Tablet: Stacked grid with adjusted columns
- Mobile: Single column with optimized spacing

## Performance Considerations

- Lazy loading for large datasets
- Memoized calculations
- Efficient rendering with React.memo
- Debounced filter changes
- Optimized chart rendering

## Future Enhancements

- Real-time WebSocket updates
- Custom alert webhooks
- Team/user cost attribution
- Cost optimization recommendations
- Historical trend comparison
- Cost anomaly detection
- Budget forecasting with ML
- Multi-currency support
