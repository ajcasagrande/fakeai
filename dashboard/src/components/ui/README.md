# UI Component Library

A comprehensive set of reusable UI components styled with NVIDIA branding, glass morphism effects, and Framer Motion animations.

## Components

### Card
Glass morphism card component with hover effects.

```tsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui'

<Card hover animated>
  <CardHeader>
    <CardTitle gradient>Performance Metrics</CardTitle>
    <CardDescription>Real-time system statistics</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Your content */}
  </CardContent>
</Card>
```

**Props:**
- `hover?: boolean` - Enable hover scale effect
- `animated?: boolean` - Use Framer Motion animations

**Style:**
- Background: `bg-white/5`
- Border: `border-white/10`
- Backdrop: `backdrop-blur-sm`
- Hover: `hover:border-nvidia-green/50`

---

### Button
Multiple variants with Framer Motion animations.

```tsx
import { Button, IconButton } from '@/components/ui'

// Primary (NVIDIA green)
<Button variant="primary">Click Me</Button>

// Secondary (gradient)
<Button variant="secondary" size="lg">Large Button</Button>

// Ghost
<Button variant="ghost">Ghost Button</Button>

// Icon button
<IconButton icon={<Zap />} variant="primary" />
```

**Variants:**
- `primary` - NVIDIA green background
- `secondary` - Gradient green
- `ghost` - Transparent with border
- `outline` - Border only
- `destructive` - Red for danger actions
- `link` - Text link style

**Sizes:** `sm`, `default`, `lg`, `icon`

---

### Badge
Status badges with colored variants.

```tsx
import { Badge, PulseBadge } from '@/components/ui'

<Badge variant="success">Active</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="error">Failed</Badge>
<Badge variant="info">Processing</Badge>

// Pulsing badge for active states
<PulseBadge variant="nvidia" pulse>Live</PulseBadge>
```

**Variants:**
- `success` - Green
- `warning` - Yellow
- `error` - Red
- `info` - Blue
- `nvidia` - NVIDIA green
- `purple` - Purple
- `default` - Gray

---

### StatCard
Metric display card with icon, value, and trend.

```tsx
import { StatCard } from '@/components/ui'
import { Zap } from 'lucide-react'

<StatCard
  icon={Zap}
  label="Throughput"
  value="1,234.56"
  unit="req/s"
  trend={{ value: 12.5, direction: "up" }}
  color="green"
  delay={0.1}
/>
```

**Props:**
- `icon: LucideIcon` - Icon component
- `label: string` - Metric label
- `value: string | number` - Main value
- `unit?: string` - Unit label
- `trend?` - Trend indicator with direction
- `color?` - Theme color
- `delay?` - Animation delay

**Colors:** `green`, `blue`, `purple`, `orange`, `pink`, `red`

---

### GradientText
Gradient text for headings and emphasis.

```tsx
import { GradientText, AnimatedGradientHeading, GradientBadge } from '@/components/ui'

<GradientText variant="nvidia" size="2xl">
  NVIDIA Performance
</GradientText>

<AnimatedGradientHeading variant="blue">
  Welcome to Dashboard
</AnimatedGradientHeading>

<GradientBadge variant="purple">New Feature</GradientBadge>
```

**Variants:**
- `nvidia` - NVIDIA green gradient
- `blue` - Blue to cyan
- `purple` - Purple to pink
- `orange` - Orange to yellow
- `pink` - Pink to rose
- `rainbow` - Multi-color

**Sizes:** `sm`, `md`, `lg`, `xl`, `2xl`, `3xl`

---

### LoadingSpinner
NVIDIA-themed loading indicators.

```tsx
import { LoadingSpinner, LoadingOverlay, ButtonSpinner } from '@/components/ui'

// Basic spinner
<LoadingSpinner size="md" variant="spinner" />

// NVIDIA activity icon spinner
<LoadingSpinner variant="nvidia" text="Loading data..." />

// Pulse animation
<LoadingSpinner variant="pulse" size="lg" />

// Dot animation
<LoadingSpinner variant="dots" />

// Full-screen overlay
<LoadingOverlay text="Processing..." variant="nvidia" />

// Button spinner
<Button disabled>
  <ButtonSpinner className="mr-2" />
  Loading...
</Button>
```

**Variants:**
- `spinner` - Classic spinning circle
- `nvidia` - Rotating Activity icon
- `pulse` - Pulsing circle
- `dots` - Three bouncing dots

**Sizes:** `sm`, `md`, `lg`, `xl`

---

### EmptyState
Empty state displays with actions.

```tsx
import { EmptyState, SimpleEmptyState, NoResultsState } from '@/components/ui'
import { Database } from 'lucide-react'

// Full empty state
<EmptyState
  icon={Database}
  title="No Data Available"
  description="Upload your first benchmark to get started"
  action={{
    label: "Upload Benchmark",
    onClick: handleUpload,
    variant: "primary"
  }}
  secondaryAction={{
    label: "Learn More",
    onClick: handleLearnMore
  }}
  size="md"
/>

// Simple version
<SimpleEmptyState
  icon={Database}
  message="No items found"
/>

// Search results
<NoResultsState
  searchQuery="my query"
  onClear={handleClear}
/>
```

**Sizes:** `sm`, `md`, `lg`

---

## Design Tokens

### Colors
```css
/* NVIDIA Brand */
--nvidia-green: #76b900
--nvidia-black: #000000
--nvidia-dark-gray: #1a1a1a

/* Glass Morphism */
background: white/5
border: white/10
backdrop-blur: sm

/* Hover States */
border-color: nvidia-green/50
```

### Animations
- Scale on hover: `hover:scale-105`
- Framer Motion: `whileHover`, `whileTap`
- Pulse: `animate-pulse-slow`
- Shimmer: `animate-shimmer`
- Glow: `animate-glow`

### Shadows
- `shadow-nvidia-green`: NVIDIA green glow
- `shadow-nvidia-green-lg`: Large NVIDIA green glow

---

## Usage Example

```tsx
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  StatCard,
  GradientText,
  LoadingSpinner,
  EmptyState,
} from '@/components/ui'
import { Zap, Activity, Database } from 'lucide-react'

function Dashboard() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-nvidia-darkGray to-black p-8">
      {/* Header */}
      <GradientText variant="nvidia" size="3xl" className="mb-8">
        Performance Dashboard
      </GradientText>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard
          icon={Zap}
          label="Throughput"
          value="1,234"
          unit="req/s"
          color="green"
          trend={{ value: 12.5, direction: "up" }}
        />
        <StatCard
          icon={Activity}
          label="Latency"
          value="45"
          unit="ms"
          color="blue"
          trend={{ value: 8.3, direction: "down" }}
        />
        <StatCard
          icon={Database}
          label="Data Processed"
          value="2.4"
          unit="TB"
          color="purple"
        />
      </div>

      {/* Content Card */}
      <Card hover animated>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Recent Activity</CardTitle>
            <Badge variant="success">Live</Badge>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <LoadingSpinner variant="nvidia" text="Loading..." centered />
          ) : data?.length === 0 ? (
            <EmptyState
              icon={Database}
              title="No Activity"
              description="Start a benchmark to see activity"
              action={{ label: "Start Now", onClick: handleStart }}
            />
          ) : (
            // Your content
          )}
        </CardContent>
      </Card>
    </div>
  )
}
```

---

## Dependencies

- **Tailwind CSS** - Utility classes
- **Framer Motion** - Animations
- **Lucide React** - Icons
- **class-variance-authority** - Variant management
- **Radix UI** - Accessible primitives

## Best Practices

1. **Always use Tailwind classes** - No inline styles
2. **Leverage Framer Motion** - Smooth, performant animations
3. **Type safety** - All components are fully typed
4. **Accessibility** - Built on Radix UI primitives
5. **Consistency** - Match reference dashboard styling
6. **Glass morphism** - `bg-white/5 backdrop-blur-sm border-white/10`
7. **NVIDIA branding** - Use nvidia-green for primary actions

## Color Reference

| Variant | Background | Text | Border |
|---------|-----------|------|--------|
| Success | `bg-green-500/20` | `text-green-400` | `border-green-500/30` |
| Warning | `bg-yellow-500/20` | `text-yellow-400` | `border-yellow-500/30` |
| Error | `bg-red-500/20` | `text-red-400` | `border-red-500/30` |
| Info | `bg-blue-500/20` | `text-blue-400` | `border-blue-500/30` |
| NVIDIA | `bg-nvidia-green/20` | `text-nvidia-green` | `border-nvidia-green/30` |
