# Quick Reference Guide

## Import Statement
```tsx
import {
  Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter,
  Button, IconButton,
  Badge, PulseBadge,
  StatCard, SimpleStatCard,
  GradientText, AnimatedGradientHeading, GradientBadge,
  LoadingSpinner, LoadingOverlay, ButtonSpinner, LoadingSkeleton,
  EmptyState, SimpleEmptyState, NoResultsState,
} from '@/components/ui'
```

## Quick Examples

### Card
```tsx
<Card hover animated>
  <CardHeader>
    <CardTitle gradient>Title</CardTitle>
    <CardDescription>Description</CardDescription>
  </CardHeader>
  <CardContent>Content here</CardContent>
</Card>
```

### Button
```tsx
<Button variant="primary">Primary</Button>
<Button variant="secondary" size="lg">Large Secondary</Button>
<Button variant="ghost">Ghost</Button>
<IconButton icon={<Settings />} variant="primary" />
```

### Badge
```tsx
<Badge variant="success">Active</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="error">Failed</Badge>
<PulseBadge variant="nvidia" pulse>Live</PulseBadge>
```

### StatCard
```tsx
<StatCard
  icon={Zap}
  label="Throughput"
  value="1,234"
  unit="req/s"
  trend={{ value: 12.5, direction: "up" }}
  color="green"
/>
```

### GradientText
```tsx
<GradientText variant="nvidia" size="2xl">Heading</GradientText>
<AnimatedGradientHeading>Hero Text</AnimatedGradientHeading>
<GradientBadge variant="purple">New</GradientBadge>
```

### Loading
```tsx
<LoadingSpinner variant="nvidia" text="Loading..." />
<LoadingOverlay text="Processing..." />
<ButtonSpinner />
<LoadingSkeleton className="h-8 w-full" count={3} />
```

### EmptyState
```tsx
<EmptyState
  icon={Database}
  title="No Data"
  description="Upload to get started"
  action={{ label: "Upload", onClick: handleUpload }}
/>
```

## Color Variants

| Variant | Use Case | Color |
|---------|----------|-------|
| `success` | Active, Complete | Green |
| `warning` | Pending, Caution | Yellow |
| `error` | Failed, Error | Red |
| `info` | Information | Blue |
| `nvidia` | Brand, Primary | NVIDIA Green |
| `purple` | Accent | Purple |

## Common Patterns

### Dashboard Layout
```tsx
<div className="bg-gradient-to-br from-black via-nvidia-darkGray to-black p-8">
  <GradientText variant="nvidia" size="3xl">Dashboard</GradientText>
  <div className="grid grid-cols-3 gap-6">
    <StatCard {...} />
  </div>
</div>
```

### Loading State
```tsx
{isLoading ? (
  <LoadingSpinner variant="nvidia" centered />
) : data ? (
  <Content />
) : (
  <EmptyState {...} />
)}
```

### Action Buttons
```tsx
<div className="flex gap-3">
  <Button variant="primary">Save</Button>
  <Button variant="ghost">Cancel</Button>
</div>
```

## Tailwind Classes Reference

### Glass Morphism
- `bg-white/5` - Semi-transparent white background
- `backdrop-blur-sm` - Blur effect
- `border-white/10` - Semi-transparent border

### NVIDIA Colors
- `text-nvidia-green` - NVIDIA green text
- `bg-nvidia-green` - NVIDIA green background
- `border-nvidia-green` - NVIDIA green border
- `hover:border-nvidia-green/50` - Hover state

### Animations
- `hover:scale-105` - Scale on hover
- `animate-pulse` - Pulse animation
- `animate-spin` - Spin animation

## Icons
Use Lucide React:
```tsx
import { Zap, Activity, Database, Clock, TrendingUp } from 'lucide-react'
```

## File Locations
- Components: `/home/anthony/projects/fakeai/dashboard/src/components/ui/`
- Full docs: `README.md`
- Demo: `ComponentShowcase.tsx`
- Summary: `COMPONENT_SUMMARY.md`
