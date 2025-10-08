# Shared Chart Components

Beautiful, reusable chart components matching the ultimate_dashboard_v3 style.

## Components

### 1. LineChart
Time-series line chart with NVIDIA green gradient fill.

```tsx
import { LineChart } from '@/components/charts'

<LineChart
  data={[
    { time: '00:00', throughput: 100, latency: 50 },
    { time: '01:00', throughput: 150, latency: 45 },
  ]}
  xKey="time"
  yKeys={['throughput', 'latency']}
  xLabel="Time"
  yLabel="Value"
  height={400}
/>
```

**Props:**
- `data`: Array of data points
- `xKey`: Key for x-axis values
- `yKeys`: Array of keys for y-axis values (multiple lines)
- `colors`: Optional array of colors (defaults to NVIDIA green, blue, yellow, red)
- `xLabel`, `yLabel`: Optional axis labels
- `loading`: Show loading state
- `height`: Chart height in pixels
- `showLegend`: Show/hide legend
- `smooth`: Smooth or linear lines

### 2. BarChart
Horizontal/vertical bar charts with NVIDIA green bars.

```tsx
import { BarChart } from '@/components/charts'

<BarChart
  data={[
    { model: 'Model A', throughput: 100, latency: 50 },
    { model: 'Model B', throughput: 150, latency: 45 },
  ]}
  xKey="model"
  yKeys={['throughput', 'latency']}
  xLabel="Model"
  yLabel="Performance"
  showValues
/>
```

**Props:**
- `data`: Array of data points
- `xKey`: Key for x-axis/category values
- `yKeys`: Array of keys for bar values
- `colors`: Optional array of colors
- `xLabel`, `yLabel`: Optional axis labels
- `loading`: Show loading state
- `height`: Chart height in pixels
- `showLegend`: Show/hide legend
- `horizontal`: Horizontal or vertical bars
- `showValues`: Display value labels on bars

### 3. MetricCard
Single metric display with icon, value, and trend indicator.

```tsx
import { MetricCard } from '@/components/charts'
import { Zap } from 'lucide-react'

<MetricCard
  icon={Zap}
  label="Throughput"
  value={1250.5}
  unit="req/s"
  trend={12.5}
  trendLabel="vs last hour"
  color="green"
/>
```

**Props:**
- `icon`: Lucide icon component
- `label`: Metric label
- `value`: Metric value (string or number)
- `unit`: Optional unit string
- `trend`: Optional trend percentage (positive/negative)
- `trendLabel`: Optional trend description
- `loading`: Show loading state
- `color`: Color theme ('green', 'blue', 'yellow', 'red', 'purple', 'gray')
- `delay`: Animation delay in seconds

**Colors:**
- `green`: NVIDIA green (default)
- `blue`: Blue accent
- `yellow`: Yellow accent
- `red`: Red accent
- `purple`: Purple accent
- `gray`: Neutral gray

### 4. StatsGrid
Responsive grid of stat cards with staggered animations.

```tsx
import { StatsGrid } from '@/components/charts'
import { Zap, Clock, Target, TrendingUp } from 'lucide-react'

<StatsGrid
  stats={[
    {
      id: 'throughput',
      icon: Zap,
      label: 'Throughput',
      value: 1250.5,
      unit: 'req/s',
      trend: 12.5,
      color: 'green',
    },
    {
      id: 'latency',
      icon: Clock,
      label: 'Avg Latency',
      value: 45.2,
      unit: 'ms',
      trend: -5.3,
      color: 'blue',
    },
  ]}
  columns={4}
  gap={6}
/>
```

**Props:**
- `stats`: Array of stat objects (same structure as MetricCard props)
- `loading`: Show loading state for all cards
- `columns`: Grid columns (1, 2, 3, or 4)
- `gap`: Gap size between cards (2, 4, 6, or 8)

### 5. PerformanceGauge
Circular progress gauge with color-coded performance indicator.

```tsx
import { PerformanceGauge } from '@/components/charts'

<PerformanceGauge
  value={85}
  maxValue={100}
  label="Performance Score"
  description="Overall system performance"
  size="lg"
/>
```

**Props:**
- `value`: Current value
- `maxValue`: Maximum value (defaults to 100)
- `label`: Gauge label
- `description`: Optional description text
- `size`: Gauge size ('sm', 'md', 'lg', 'xl')
- `loading`: Show loading state
- `showPercentage`: Display percentage in center (default: true)

**Color Thresholds:**
- 90-100%: NVIDIA Green (excellent)
- 70-89%: Blue (good)
- 50-69%: Yellow (fair)
- 30-49%: Orange (poor)
- 0-29%: Red (critical)

## Design Features

All components include:
- **Glass Morphism**: Transparent backgrounds with blur effects
- **Framer Motion**: Smooth entrance and hover animations
- **NVIDIA Color Theme**: NVIDIA green (#76B900) as primary color
- **Dark Theme**: Optimized for dark backgrounds
- **Responsive**: Auto-sizing and mobile-friendly
- **Loading States**: Skeleton loaders and spinners
- **Empty States**: Graceful handling of missing data
- **TypeScript**: Full type safety

## Example Usage

```tsx
'use client'

import { LineChart, StatsGrid, PerformanceGauge } from '@/components/charts'
import { Zap, Clock, Target, TrendingUp } from 'lucide-react'

export function DashboardView() {
  return (
    <div className="space-y-8">
      {/* Stats Grid */}
      <StatsGrid
        stats={[
          {
            id: 'throughput',
            icon: Zap,
            label: 'Throughput',
            value: 1250.5,
            unit: 'req/s',
            trend: 12.5,
            color: 'green',
          },
          {
            id: 'latency',
            icon: Clock,
            label: 'Avg Latency',
            value: 45.2,
            unit: 'ms',
            trend: -5.3,
            color: 'blue',
          },
        ]}
        columns={4}
      />

      {/* Line Chart */}
      <LineChart
        data={timeSeriesData}
        xKey="timestamp"
        yKeys={['throughput', 'latency']}
        xLabel="Time"
        yLabel="Value"
      />

      {/* Performance Gauge */}
      <div className="flex justify-center">
        <PerformanceGauge
          value={85}
          label="Performance Score"
          size="lg"
        />
      </div>
    </div>
  )
}
```

## Color Palette

```tsx
// NVIDIA Colors
const colors = {
  nvidia: {
    green: '#76B900',
    greenDark: '#5a9000',
    greenLight: '#90d920',
  },
  accent: {
    blue: '#3b82f6',
    yellow: '#f59e0b',
    red: '#ef4444',
    purple: '#a855f7',
    orange: '#f97316',
  },
  neutral: {
    black: '#000000',
    gray900: '#111827',
    gray800: '#1f2937',
    gray700: '#374151',
    gray600: '#4b5563',
    gray500: '#6b7280',
    gray400: '#9ca3af',
  },
}
```
