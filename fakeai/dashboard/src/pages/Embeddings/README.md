# Embeddings Monitoring Dashboard

Comprehensive real-time monitoring dashboard for embedding operations in FakeAI.

## Features

### 1. Embedding Requests Visualization
- Real-time request rate monitoring
- Request volume trends over time
- Success/error rate tracking

### 2. Model Usage Statistics
- Usage breakdown by model
- Comparative model performance
- Request and token distribution by model

### 3. Token Consumption Tracking
- Real-time token usage monitoring
- Token consumption trends
- Average tokens per request

### 4. Average Processing Time
- Request latency metrics
- Performance trends over time
- Processing time percentiles

### 5. Batch Embedding Analytics
- Batch size distribution
- Average batch size tracking
- Batch processing efficiency

### 6. Dimension Distribution Charts
- Pie chart visualization of embedding dimensions
- Usage percentage by dimension size
- Popular dimension configurations

### 7. Recent Embeddings Table
- Latest embedding requests
- Detailed request metadata
- Status and error tracking

### 8. Usage Trends Over Time
- Multi-metric trend visualization
- Historical usage patterns
- Dual-axis charts for requests and processing time

### 9. Cost Analysis per Model
- Cost breakdown by model
- Cost per request and per 1K tokens
- Total cost tracking
- Cost optimization insights

### 10. Export Embedding Logs
- JSON export
- CSV export
- Custom date range selection
- Configurable export options

## API Endpoints Used

### Primary Endpoint
- `GET /v1/organization/usage/embeddings`
  - Query parameters:
    - `start_time`: Unix timestamp (start of range)
    - `end_time`: Unix timestamp (end of range)
    - `bucket_width`: Time bucket size ('1m', '1h', '1d')
    - `project_id`: Optional project filter
    - `model`: Optional model filter

### Secondary Endpoint
- `GET /metrics`
  - Returns general metrics including:
    - Response times
    - Error rates
    - Request rates

## Usage

### Basic Usage

```tsx
import EmbeddingsDashboard from './pages/Embeddings';

function App() {
  return <EmbeddingsDashboard />;
}
```

### Configuration

Set the API base URL via environment variable:

```bash
REACT_APP_API_BASE_URL=http://localhost:8000
```

### Time Ranges

Available time range options:
- Last Hour (1h)
- Last 6 Hours (6h)
- Last 24 Hours (24h) - default
- Last 7 Days (7d)
- Last 30 Days (30d)

### Model Filtering

Filter data by specific embedding models:
- All Models (default)
- text-embedding-ada-002
- text-embedding-3-small
- text-embedding-3-large

### Auto-Refresh

The dashboard auto-refreshes every 5 seconds by default. You can:
- Toggle auto-refresh on/off
- Manually refresh with the "Refresh Now" button

## Components

### EmbeddingStats
Displays key metrics in a card grid:
- Total Requests
- Total Tokens
- Avg Processing Time
- Requests/Second
- Tokens/Second
- Error Rate

### ModelUsageChart
Bar chart showing model usage distribution for both requests and tokens.

### TokenConsumption
Line chart with area fill showing token consumption trends over time.

### RecentEmbeddingsTable
Sortable table of recent embedding requests with:
- Timestamp
- Model
- Token count
- Dimensions
- Batch size
- Processing time
- Cost
- Status

### UsageTrends
Dual-axis line chart showing:
- Request volume (green solid line)
- Average processing time (blue dashed line)

### DimensionDistribution
Pie chart showing the distribution of embedding dimensions with legend.

### CostAnalysis
Detailed cost breakdown table by model including:
- Total cost
- Number of requests
- Cost per request
- Cost per 1K tokens
- Percentage of total cost

## Styling

The dashboard uses a custom NVIDIA green theme with:
- Primary color: `#76B900` (NVIDIA Green)
- Dark background: `#0F0F0F`
- Card background: `#1E1E1E`
- Accent colors for success, warning, and error states

### CSS Variables

All colors and spacing are defined as CSS custom properties in `styles.css`:

```css
--nvidia-green: #76B900;
--nvidia-green-light: #8FD400;
--nvidia-green-dark: #5A9100;
--nvidia-bg-gray: #0F0F0F;
--nvidia-card-bg: #1E1E1E;
```

## Data Processing

The dashboard processes raw API data into structured metrics:

1. **Aggregation**: Sums requests and tokens across buckets
2. **Rate Calculation**: Computes per-second rates
3. **Cost Calculation**: Applies model-specific cost rates
4. **Trend Generation**: Creates time-series data for charts
5. **Distribution Analysis**: Calculates dimension usage percentages

## Export Functionality

Export options:
- **JSON**: Complete data dump with all metrics
- **CSV**: Tabular format for spreadsheet analysis
- **Excel**: (Future) Formatted Excel workbook

Export includes:
- All current metrics
- Model usage statistics
- Dimension distribution
- Recent embeddings
- Usage trends
- Cost breakdown
- Export timestamp

## Browser Compatibility

Tested and supported on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance Considerations

- Canvas-based charts for efficient rendering
- Automatic cleanup of chart resources
- Debounced API calls
- Configurable refresh intervals
- Lazy loading of components

## Future Enhancements

- Real-time WebSocket updates
- Advanced filtering and search
- Custom alert configuration
- Comparison mode for time periods
- Embedding quality metrics
- Integration with external analytics tools

## License

SPDX-License-Identifier: Apache-2.0
