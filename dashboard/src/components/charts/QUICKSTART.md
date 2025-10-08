# Chart Components - Quick Start Guide

## Import

```tsx
import {
  LineChart,
  BarChart,
  MetricCard,
  StatsGrid,
  PerformanceGauge
} from '@/components/charts'
```

## 1. Display Key Metrics (5 min)

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
      trendLabel: 'vs last hour',
      color: 'green',
    },
    {
      id: 'latency',
      icon: Clock,
      label: 'Latency',
      value: 45.2,
      unit: 'ms',
      trend: -5.3,
      color: 'blue',
    },
  ]}
  columns={4}
/>
```

## 2. Show Time Series (5 min)

```tsx
import { LineChart } from '@/components/charts'

const data = [
  { time: '00:00', throughput: 100, latency: 50 },
  { time: '01:00', throughput: 150, latency: 45 },
  { time: '02:00', throughput: 180, latency: 42 },
]

<LineChart
  data={data}
  xKey="time"
  yKeys={['throughput', 'latency']}
  xLabel="Time"
  yLabel="Value"
  height={400}
/>
```

## 3. Compare Models (5 min)

```tsx
import { BarChart } from '@/components/charts'

const data = [
  { model: 'Llama-2-7B', throughput: 150 },
  { model: 'Llama-2-13B', throughput: 120 },
  { model: 'Llama-2-70B', throughput: 80 },
]

<BarChart
  data={data}
  xKey="model"
  yKeys={['throughput']}
  yLabel="Throughput (req/s)"
  showValues
/>
```

## 4. Show Performance Score (5 min)

```tsx
import { PerformanceGauge } from '@/components/charts'

<PerformanceGauge
  value={85}
  label="Performance Score"
  description="Overall system performance"
  size="lg"
/>
```

## Color Options

```tsx
// MetricCard colors
color="green"   // NVIDIA green (default)
color="blue"    // Blue accent
color="yellow"  // Yellow accent
color="red"     // Red accent
color="purple"  // Purple accent
color="gray"    // Neutral
```

## Common Patterns

### Dashboard Page
```tsx
export default function DashboardPage() {
  return (
    <div className="space-y-8 p-8">
      {/* Top metrics */}
      <StatsGrid stats={topMetrics} columns={4} />

      {/* Time series chart */}
      <LineChart data={timeSeries} xKey="time" yKeys={['value']} />

      {/* Performance gauge */}
      <div className="flex justify-center">
        <PerformanceGauge value={score} label="Score" size="lg" />
      </div>
    </div>
  )
}
```

### Comparison Page
```tsx
export default function ComparisonPage() {
  return (
    <div className="space-y-8 p-8">
      {/* Bar chart comparison */}
      <BarChart
        data={modelData}
        xKey="model"
        yKeys={['throughput', 'latency']}
        showValues
      />
    </div>
  )
}
```

### Loading States
```tsx
<MetricCard icon={Zap} label="Loading..." value={0} loading />
<LineChart data={[]} xKey="x" yKeys={['y']} loading />
<PerformanceGauge value={0} label="Loading..." loading />
```

### Empty States
```tsx
// Automatically handled - just pass empty data
<LineChart data={[]} xKey="x" yKeys={['y']} />
<BarChart data={[]} xKey="x" yKeys={['y']} />
<StatsGrid stats={[]} />
```

## Files

- **LineChart.tsx** - Time series line charts
- **BarChart.tsx** - Bar charts (vertical/horizontal)
- **MetricCard.tsx** - Single metric displays
- **StatsGrid.tsx** - Grid of metrics
- **PerformanceGauge.tsx** - Circular progress gauge
- **ChartExamples.tsx** - Complete usage examples
- **README.md** - Full documentation
- **index.ts** - Export file

## Next Steps

1. Copy examples from `ChartExamples.tsx`
2. Read full documentation in `README.md`
3. Check component comparison in `COMPARISON.md`
4. See implementation details in `SUMMARY.md`

## Tips

- All components are responsive by default
- Dark theme optimized (black backgrounds)
- NVIDIA green (#76B900) is the primary color
- Use Lucide React icons for consistency
- All animations are automatic (Framer Motion)
- Glass morphism is built-in
- Loading and empty states are handled automatically

## Support

See the example file for working code:
```bash
/home/anthony/projects/fakeai/dashboard/src/components/charts/ChartExamples.tsx
```
