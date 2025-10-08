# Component Documentation

Comprehensive documentation for all components in the FakeAI Dashboard.

---

## Table of Contents

- [Overview](#overview)
- [Shared Components](#shared-components)
- [Chat Completions Components](#chat-completions-components)
- [Embeddings Components](#embeddings-components)
- [Rate Limits Components](#rate-limits-components)
- [KV Cache Components](#kv-cache-components)
- [Costs Components](#costs-components)
- [Organization Components](#organization-components)
- [Component Development Guide](#component-development-guide)

---

## Overview

The dashboard contains 100+ TypeScript components organized by feature area. Each component follows React best practices with TypeScript for type safety.

### Component Categories

- **Page Components** - Top-level route components
- **Feature Components** - Domain-specific functionality
- **Shared Components** - Reusable UI elements
- **Service Components** - Business logic wrappers

---

## Shared Components

### LoadingSpinner

Displays a loading indicator.

**Location**: `src/services/components/LoadingSpinner.tsx`

```typescript
interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  message?: string;
}

<LoadingSpinner size="medium" message="Loading data..." />
```

### ErrorBanner

Displays error messages with optional retry action.

**Location**: `src/services/components/ErrorBanner.tsx`

```typescript
interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
  dismissible?: boolean;
}

<ErrorBanner
  message="Failed to load data"
  onRetry={fetchData}
  dismissible
/>
```

---

## Chat Completions Components

### ChatCompletions

Main page component for chat completions monitoring.

**Location**: `src/pages/ChatCompletions/ChatCompletions.tsx`

**Features**:
- Real-time metrics display
- Auto-refresh with configurable interval
- Comprehensive filtering
- Request details inspection

**State Management**:
```typescript
interface ChatCompletionsState {
  modelStats: Record<string, ModelStats>;
  requests: ChatRequest[];
  totalRequests: number;
  loading: boolean;
  error: string | null;
  filters: DashboardFilters;
  currentPage: number;
  autoRefresh: boolean;
}
```

### MetricsOverview

Displays key metrics at a glance.

**Location**: `src/pages/ChatCompletions/components/MetricsOverview.tsx`

**Props**:
```typescript
interface MetricsOverviewProps {
  metrics: MetricsOverview;
  loading?: boolean;
}

interface MetricsOverview {
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  avg_latency_ms: number;
  error_rate: number;
  streaming_percentage: number;
  requests_per_second: number;
}
```

**Example**:
```typescript
<MetricsOverview
  metrics={{
    total_requests: 10000,
    total_tokens: 5000000,
    total_cost: 125.50,
    avg_latency_ms: 234,
    error_rate: 0.5,
    streaming_percentage: 75.0,
    requests_per_second: 2.5
  }}
/>
```

### ModelUsageChart

Visualizes model usage distribution.

**Location**: `src/pages/ChatCompletions/components/ModelUsageChart.tsx`

**Props**:
```typescript
interface ModelUsageChartProps {
  modelStats: Record<string, ModelStats>;
  chartType: 'pie' | 'bar';
}
```

**Features**:
- Pie chart or bar chart view
- Percentage calculations
- Color-coded models
- Interactive tooltips

### TokenStats

Displays token breakdown statistics.

**Location**: `src/pages/ChatCompletions/components/TokenStats.tsx`

**Props**:
```typescript
interface TokenStatsProps {
  tokenBreakdown: TokenBreakdown;
}

interface TokenBreakdown {
  prompt_tokens: number;
  completion_tokens: number;
  cached_tokens: number;
  total_tokens: number;
}
```

**Features**:
- Visual breakdown with progress bars
- Percentage calculations
- Token type indicators

### StreamingMetrics

Shows streaming vs non-streaming statistics.

**Location**: `src/pages/ChatCompletions/components/StreamingMetrics.tsx`

**Props**:
```typescript
interface StreamingMetricsProps {
  modelStats: Record<string, ModelStats>;
}
```

**Displays**:
- Total streaming requests
- Total non-streaming requests
- Percentage breakdown
- Per-model streaming stats

### ResponseTimeChart

Visualizes response time by model.

**Location**: `src/pages/ChatCompletions/components/ResponseTimeChart.tsx`

**Props**:
```typescript
interface ResponseTimeChartProps {
  modelStats: Record<string, ModelStats>;
}
```

**Features**:
- Bar chart of average latency
- Percentile indicators (p50, p90, p95, p99)
- Model comparison

### ErrorRateChart

Displays error rates by model.

**Location**: `src/pages/ChatCompletions/components/ErrorRateChart.tsx`

**Props**:
```typescript
interface ErrorRateChartProps {
  modelStats: Record<string, ModelStats>;
}
```

**Features**:
- Error rate percentage
- Error count visualization
- Model-specific error tracking

### RequestsTable

Paginated table of chat completion requests.

**Location**: `src/pages/ChatCompletions/components/RequestsTable.tsx`

**Props**:
```typescript
interface RequestsTableProps {
  requests: ChatRequest[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onRequestClick: (request: ChatRequest) => void;
  loading?: boolean;
}
```

**Features**:
- Pagination controls
- Sortable columns
- Row click to view details
- Status indicators
- Timestamp formatting

### RequestDetailsModal

Modal for viewing detailed request information.

**Location**: `src/pages/ChatCompletions/components/RequestDetailsModal.tsx`

**Props**:
```typescript
interface RequestDetailsModalProps {
  request: ChatRequest | null;
  onClose: () => void;
}
```

**Displays**:
- Request metadata
- Full request payload
- Response data
- Token counts
- Latency breakdown
- Cost information

### FilterPanel

Sidebar component for filtering data.

**Location**: `src/pages/ChatCompletions/components/FilterPanel.tsx`

**Props**:
```typescript
interface FilterPanelProps {
  filters: DashboardFilters;
  availableModels: string[];
  onFiltersChange: (filters: DashboardFilters) => void;
}

interface DashboardFilters {
  model: string | null;
  dateRange: {
    start: Date | null;
    end: Date | null;
  };
  status: 'all' | 'success' | 'error';
  streaming: 'all' | 'streaming' | 'non-streaming';
}
```

**Features**:
- Model selector dropdown
- Date range picker
- Status filter
- Streaming filter
- Reset filters button

### CostVisualization

Visualizes cost breakdown and trends.

**Location**: `src/pages/ChatCompletions/components/CostVisualization.tsx`

**Props**:
```typescript
interface CostVisualizationProps {
  modelStats: Record<string, ModelStats>;
}
```

**Features**:
- Total cost display
- Cost per model
- Cost trends over time
- Cost per request average

---

## Embeddings Components

### Embeddings

Main page component for embeddings monitoring.

**Location**: `src/pages/Embeddings/Embeddings.tsx`

### EmbeddingStats

Overview statistics for embeddings.

**Location**: `src/pages/Embeddings/components/EmbeddingStats.tsx`

**Displays**:
- Total embeddings generated
- Total tokens consumed
- Average dimension
- Cost analytics

### ModelUsageChart

Model usage distribution for embeddings.

**Location**: `src/pages/Embeddings/components/ModelUsageChart.tsx`

### TokenConsumption

Token consumption tracking over time.

**Location**: `src/pages/Embeddings/components/TokenConsumption.tsx`

### RecentEmbeddingsTable

Table of recent embedding requests.

**Location**: `src/pages/Embeddings/components/RecentEmbeddingsTable.tsx`

### UsageTrends

Visualizes usage trends over time.

**Location**: `src/pages/Embeddings/components/UsageTrends.tsx`

### DimensionDistribution

Shows distribution of embedding dimensions.

**Location**: `src/pages/Embeddings/components/DimensionDistribution.tsx`

### CostAnalysis

Detailed cost analysis for embeddings.

**Location**: `src/pages/Embeddings/components/CostAnalysis.tsx`

---

## Rate Limits Components

### RateLimits

Main page component for rate limit management.

**Location**: `src/pages/RateLimits/RateLimits.tsx`

### RateLimitOverview

High-level rate limit statistics.

**Location**: `src/pages/RateLimits/components/RateLimitOverview.tsx`

**Displays**:
- RPM (Requests Per Minute)
- TPM (Tokens Per Minute)
- RPD (Requests Per Day)
- TPD (Tokens Per Day)

### TierLimitsVisualization

Visualizes limits by tier.

**Location**: `src/pages/RateLimits/components/TierLimitsVisualization.tsx`

**Features**:
- Tier comparison
- Limit visualization
- Current tier indicator

### UsageProgressBars

Progress bars showing usage vs limits.

**Location**: `src/pages/RateLimits/components/UsageProgressBars.tsx`

**Features**:
- Visual progress bars
- Percentage indicators
- Warning thresholds

### ThrottleAnalytics

Analytics for throttling events.

**Location**: `src/pages/RateLimits/components/ThrottleAnalytics.tsx`

### AbusePatternDetection

Displays detected abuse patterns.

**Location**: `src/pages/RateLimits/components/AbusePatternDetection.tsx`

### TopConsumers

Lists top API consumers.

**Location**: `src/pages/RateLimits/components/TopConsumers.tsx`

### RateLimitBreachesTimeline

Timeline of rate limit breaches.

**Location**: `src/pages/RateLimits/components/RateLimitBreachesTimeline.tsx`

### TierDistributionChart

Chart showing tier distribution.

**Location**: `src/pages/RateLimits/components/TierDistributionChart.tsx`

### TierUpgradeRecommendations

Suggestions for tier upgrades.

**Location**: `src/pages/RateLimits/components/TierUpgradeRecommendations.tsx`

---

## KV Cache Components

### KVCache

Main page component for KV cache monitoring.

**Location**: `src/pages/KVCache/KVCache.tsx`

Components include cache hit rate visualization, block matching statistics, worker distribution, and routing efficiency metrics.

---

## Costs Components

### Costs

Main page component for cost analytics.

**Location**: `src/pages/Costs/Costs.tsx`

Components include cost overview, breakdown by model, breakdown by endpoint, time-based trends, and budget tracking.

---

## Organization Components

### Organization

Main page component for organization management.

**Location**: `src/pages/Organization/Organization.tsx`

### UsersManagement

User management interface.

**Location**: `src/pages/Organization/components/UsersManagement.tsx`

**Features**:
- List all users
- Create new users
- Edit user roles
- Delete users

### InvitesManagement

Invitation management interface.

**Location**: `src/pages/Organization/components/InvitesManagement.tsx`

**Features**:
- Send invitations
- View pending invites
- Cancel invitations
- Resend invitations

### ProjectsManagement

Project management interface.

**Location**: `src/pages/Organization/components/ProjectsManagement.tsx`

**Features**:
- Create projects
- Edit project details
- Archive projects
- View project statistics

### ProjectUsersManagement

Manage users within projects.

**Location**: `src/pages/Organization/components/ProjectUsersManagement.tsx`

### ServiceAccountsManagement

Service account administration.

**Location**: `src/pages/Organization/components/ServiceAccountsManagement.tsx`

**Features**:
- Create service accounts
- Generate API keys
- Revoke access
- View usage statistics

---

## Component Development Guide

### Creating a New Component

1. **Create component file**:
```typescript
// src/pages/MyPage/components/MyComponent.tsx
import React from 'react';
import './MyComponent.css';

interface MyComponentProps {
  data: MyData;
  onAction?: () => void;
}

export const MyComponent: React.FC<MyComponentProps> = ({ data, onAction }) => {
  return (
    <div className="my-component">
      {/* Component content */}
    </div>
  );
};
```

2. **Add types**:
```typescript
// src/pages/MyPage/types.ts
export interface MyData {
  id: string;
  name: string;
  value: number;
}
```

3. **Add styles**:
```css
/* src/pages/MyPage/components/MyComponent.css */
.my-component {
  padding: 1rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
}
```

4. **Export component**:
```typescript
// src/pages/MyPage/components/index.ts
export { MyComponent } from './MyComponent';
```

### Component Best Practices

- **Type all props** - No `any` types
- **Document with JSDoc** - Explain complex logic
- **Keep components small** - Single responsibility
- **Use semantic HTML** - Proper element selection
- **Handle loading states** - Show loading indicators
- **Handle error states** - Display error messages
- **Make accessible** - ARIA labels and keyboard navigation

### Testing Components

```typescript
import { render, screen } from '@testing-library/react';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent data={mockData} />);
    expect(screen.getByText('Expected Text')).toBeInTheDocument();
  });

  it('calls onAction when button clicked', () => {
    const handleAction = jest.fn();
    render(<MyComponent data={mockData} onAction={handleAction} />);

    fireEvent.click(screen.getByRole('button'));
    expect(handleAction).toHaveBeenCalled();
  });
});
```

---

## Storybook Setup (Future)

To add Storybook for component documentation:

```bash
# Install Storybook
npx storybook@latest init

# Run Storybook
npm run storybook
```

Example story:

```typescript
// MyComponent.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { MyComponent } from './MyComponent';

const meta: Meta<typeof MyComponent> = {
  title: 'Components/MyComponent',
  component: MyComponent,
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof MyComponent>;

export const Default: Story = {
  args: {
    data: {
      id: '1',
      name: 'Example',
      value: 100,
    },
  },
};

export const WithAction: Story = {
  args: {
    data: {
      id: '2',
      name: 'Interactive',
      value: 200,
    },
    onAction: () => console.log('Action clicked'),
  },
};
```

---

## Component Library

For a visual component library, see the running dashboard:

- **Development**: http://localhost:5173
- **Production**: http://localhost:8000/dashboard

---

**For component contributions, see [CONTRIBUTING.md](./CONTRIBUTING.md)**
