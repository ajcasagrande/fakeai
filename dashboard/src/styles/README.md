# NVIDIA-Themed Design System for FakeAI Dashboard

A comprehensive design system built with NVIDIA's iconic green brand colors and optimized for AI/ML performance monitoring dashboards.

## Overview

This design system provides a complete theming solution for the FakeAI dashboard, featuring:

- **NVIDIA Brand Colors**: Primary green (#76B900, #7AB928) with a dark theme aesthetic
- **TailwindCSS Integration**: Full Tailwind configuration with custom NVIDIA utilities
- **CSS Variables**: Consistent theming using CSS custom properties
- **Component Library**: Pre-built styles for cards, buttons, badges, charts, and more
- **Responsive Design**: Mobile-first breakpoints and adaptive layouts
- **Smooth Animations**: Custom transitions and keyframe animations
- **Performance Optimized**: JIT mode for smaller bundle sizes

## File Structure

```
fakeai/dashboard/src/styles/
├── theme.ts              # TypeScript theme constants and type definitions
├── globals.css           # Global styles, CSS variables, and base utilities
├── tailwind.config.js    # TailwindCSS configuration with NVIDIA theme
├── components.css        # Component-specific styles
└── README.md            # This file
```

## Getting Started

### 1. Installation

Make sure you have TailwindCSS installed in your project:

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 2. Import Styles

Import the global styles in your main application file:

```tsx
// app/layout.tsx or pages/_app.tsx
import '@/styles/globals.css';
import '@/styles/components.css';
```

### 3. Use Theme Constants

Import theme constants in your TypeScript/JavaScript files:

```tsx
import { THEME, NVIDIA_COLORS, DARK_THEME } from '@/styles/theme';

// Use colors
const primaryGreen = NVIDIA_COLORS.green.DEFAULT; // #76B900

// Use gradients
const gradient = THEME.gradients.nvidiaGreen;
```

## Color Palette

### NVIDIA Green (Primary)

```
#76B900  - Base NVIDIA green (nvidia-500)
#7AB928  - Light variant (nvidia-light)
#5F9400  - Dark variant (nvidia-dark)
```

### Dark Theme Colors

```
Background:
- #000000  - Primary background (bg-primary)
- #111111  - Secondary background (bg-secondary)
- #1A1A1A  - Tertiary background (bg-tertiary)
- #222222  - Elevated surfaces (bg-elevated)

Text:
- #FFFFFF  - Primary text (text-primary)
- #B3B3B3  - Secondary text (text-secondary)
- #808080  - Tertiary text (text-tertiary)

Borders:
- #333333  - Default border (border-default)
- #76B900  - Focus border (border-focus)
```

### Semantic Colors

```
Success: #76B900 (NVIDIA green)
Warning: #FFA500 (Orange)
Error:   #FF3333 (Red)
Info:    #0080FF (Blue)
```

### Chart Colors

8 distinct colors for data visualization:
1. #76B900 (NVIDIA green)
2. #00FFFF (Cyan)
3. #9D00FF (Purple)
4. #FFA500 (Orange)
5. #0080FF (Blue)
6. #00CC99 (Teal)
7. #FF3388 (Pink)
8. #FFD700 (Gold)

## Usage Examples

### Using Tailwind Classes

```tsx
// Card with NVIDIA styling
<div className="bg-surface-base border border-border-default rounded-lg p-6 shadow-md hover:shadow-nvidia-glow">
  <h3 className="text-xl font-semibold text-primary mb-2">GPU Metrics</h3>
  <p className="text-text-secondary">Real-time performance data</p>
</div>

// NVIDIA gradient button
<button className="bg-gradient-nvidia text-black font-semibold px-6 py-3 rounded-md hover:shadow-nvidia-glow transition-all">
  Start Training
</button>

// Badge with status
<span className="badge-nvidia">Active</span>
```

### Using CSS Classes

```tsx
// Dashboard card
<div className="card-dashboard">
  <h3>Performance Metrics</h3>
  <div className="metric-value">98.5%</div>
</div>

// Primary button
<button className="btn-nvidia-primary">
  Deploy Model
</button>

// Status badge
<span className="status-badge running">Running</span>
```

### Using CSS Variables

```css
.custom-component {
  background: var(--bg-secondary);
  border: 1px solid var(--border-default);
  color: var(--text-primary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-base);
}

.custom-component:hover {
  box-shadow: var(--shadow-green-glow);
}
```

### Using TypeScript Theme

```tsx
import { THEME } from '@/styles/theme';

const ChartComponent = () => {
  const chartConfig = {
    colors: THEME.colors.chart.series,
    backgroundColor: THEME.colors.dark.background.secondary,
    textColor: THEME.colors.dark.text.primary,
  };

  return <Chart config={chartConfig} />;
};
```

## Components

### Cards

```tsx
// Basic card
<div className="card">Content</div>

// Elevated card
<div className="card card-elevated">Content</div>

// NVIDIA accent card
<div className="card card-nvidia">Content</div>

// Metric card
<div className="card-metric">
  <div className="card-metric-header">
    <span className="card-metric-title">GPU Utilization</span>
  </div>
  <div className="card-metric-value">87%</div>
  <div className="card-metric-trend positive">+5.2%</div>
</div>
```

### Buttons

```tsx
// Primary button
<button className="btn btn-primary">Primary</button>

// NVIDIA branded button
<button className="btn-nvidia-primary">NVIDIA Action</button>

// Outline button
<button className="btn-outline-nvidia">Secondary</button>

// Icon button
<button className="btn-icon">
  <IconComponent />
</button>
```

### Badges

```tsx
// Status badges
<span className="status-badge running">Running</span>
<span className="status-badge stopped">Stopped</span>
<span className="status-badge pending">Pending</span>

// Performance badges
<span className="performance-badge excellent">Excellent</span>
<span className="performance-badge good">Good</span>
<span className="performance-badge moderate">Moderate</span>

// NVIDIA badge
<span className="badge-nvidia">NVIDIA</span>
```

### Form Elements

```tsx
// Input field
<div className="form-group">
  <label className="label">Model Name</label>
  <input type="text" className="input-field" placeholder="Enter model name" />
</div>

// Select dropdown
<select className="select-field">
  <option>Option 1</option>
  <option>Option 2</option>
</select>

// Checkbox
<label className="checkbox-wrapper">
  <input type="checkbox" className="checkbox-input" />
  <span>Enable GPU acceleration</span>
</label>
```

### Charts

```tsx
<div className="chart-wrapper">
  <div className="chart-header">
    <div>
      <h3 className="chart-title">Performance Over Time</h3>
      <p className="chart-subtitle">Last 24 hours</p>
    </div>
  </div>
  <div className="chart-content">
    {/* Your chart component */}
  </div>
  <div className="chart-legend">
    <div className="legend-item">
      <span className="legend-color" style={{ background: '#76B900' }}></span>
      <span>GPU 0</span>
    </div>
    <div className="legend-item">
      <span className="legend-color" style={{ background: '#00FFFF' }}></span>
      <span>GPU 1</span>
    </div>
  </div>
</div>
```

### Progress Indicators

```tsx
// Progress bar
<div className="progress-bar">
  <div className="progress-fill" style={{ width: '75%' }}></div>
</div>

// Circular progress
<div className="progress-circle">
  <span className="progress-circle-value">75%</span>
</div>

// Loading spinner
<div className="loading"></div>
```

## Animations

### Available Animations

```css
.animate-fade-in      /* Fade in with slight upward movement */
.animate-slide-in-right  /* Slide in from right */
.animate-slide-in-left   /* Slide in from left */
.animate-pulse        /* Continuous pulse */
.animate-glow         /* NVIDIA green glow pulse */
.animate-shimmer      /* Shimmer effect for loading */
.animate-spin         /* Rotation spinner */
```

### Custom Animations

```tsx
// Apply animation class
<div className="animate-fade-in">
  Content appears with fade in effect
</div>

// NVIDIA glow effect
<div className="card glow-nvidia">
  Card with green glow
</div>

// Hover glow effect
<div className="card glow-nvidia-hover">
  Glows on hover
</div>
```

## Responsive Design

### Breakpoints

```
xs:  480px  (Extra small devices)
sm:  640px  (Small devices - landscape phones)
md:  768px  (Medium devices - tablets)
lg:  1024px (Large devices - desktops)
xl:  1280px (Extra large devices)
2xl: 1536px (2X large devices)
3xl: 1920px (Ultra-wide monitors)
```

### Usage

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {/* Responsive grid: 1 column mobile, 2 tablet, 3 desktop */}
</div>

<div className="text-sm md:text-base lg:text-lg">
  {/* Responsive text sizing */}
</div>
```

## Utility Classes

### Layout

```css
.flex-center      /* Flexbox with centered content */
.flex-between     /* Flexbox with space-between */
.container        /* Centered container with max-width */
```

### Text

```css
.text-nvidia         /* NVIDIA green text */
.text-nvidia-light   /* Light NVIDIA green text */
.text-gradient-nvidia /* Gradient text effect */
```

### Effects

```css
.glow-nvidia         /* NVIDIA green glow shadow */
.backdrop-blur       /* Blur backdrop effect */
.nvidia-gradient     /* NVIDIA gradient background */
```

## Best Practices

### 1. Use Semantic Colors

Use semantic color names for status and actions:
```tsx
// Good
<span className="text-success">Active</span>
<span className="text-error">Failed</span>

// Avoid
<span style={{ color: '#76B900' }}>Active</span>
```

### 2. Maintain Contrast

Ensure sufficient contrast for readability:
- Use `text-primary` for important content
- Use `text-secondary` for supporting text
- Use `text-tertiary` for subtle hints

### 3. Layer Elevation

Use consistent shadow levels to indicate hierarchy:
```tsx
<div className="shadow-base">    {/* Base level */}
<div className="shadow-md">      {/* Slightly elevated */}
<div className="shadow-lg">      {/* More elevated */}
<div className="shadow-xl">      {/* Highest elevation */}
```

### 4. Animation Performance

Use GPU-accelerated properties for smooth animations:
- `transform` instead of `top/left`
- `opacity` for fade effects
- Avoid animating `width/height` directly

### 5. Responsive First

Design mobile-first and enhance for larger screens:
```tsx
<div className="p-4 md:p-6 lg:p-8">
  {/* Padding increases with screen size */}
</div>
```

## Integration with Chart Libraries

### Recharts

```tsx
import { THEME } from '@/styles/theme';

const chartColors = THEME.colors.chart.series;

<LineChart data={data}>
  <Line
    dataKey="value"
    stroke={chartColors[0]}
    strokeWidth={2}
  />
</LineChart>
```

### Chart.js

```tsx
import { THEME } from '@/styles/theme';

const chartOptions = {
  plugins: {
    legend: {
      labels: {
        color: THEME.colors.dark.text.secondary,
      },
    },
  },
  scales: {
    y: {
      ticks: {
        color: THEME.colors.dark.text.tertiary,
      },
      grid: {
        color: THEME.colors.dark.border.subtle,
      },
    },
  },
};
```

## Performance Optimization

### 1. JIT Mode

TailwindCSS JIT mode is enabled for optimal performance:
- Only generates CSS for used classes
- Smaller bundle sizes
- Faster build times

### 2. CSS Variables

Use CSS variables for runtime theme switching:
```tsx
// Switch to alternate theme
document.documentElement.style.setProperty('--nvidia-green', '#8FCC33');
```

### 3. Purge Unused Styles

The Tailwind config automatically purges unused styles in production.

## Customization

### Extending the Theme

Edit `tailwind.config.js` to add custom values:

```js
module.exports = {
  theme: {
    extend: {
      colors: {
        'custom-blue': '#0080FF',
      },
      spacing: {
        '128': '32rem',
      },
    },
  },
};
```

### Adding Custom Components

Add new component styles to `components.css`:

```css
.custom-component {
  background: var(--surface-base);
  padding: var(--spacing-lg);
  border-radius: var(--radius-md);
}
```

## Troubleshooting

### Colors Not Applying

1. Make sure `globals.css` is imported in your app
2. Check that Tailwind directives are present in CSS
3. Verify content paths in `tailwind.config.js`

### CSS Variables Not Working

1. Ensure variables are defined in `:root` selector
2. Check for typos in variable names
3. Verify browser support for CSS variables

### Animations Not Smooth

1. Use GPU-accelerated properties (`transform`, `opacity`)
2. Add `will-change` for complex animations
3. Check for conflicting CSS properties

## Browser Support

- Chrome/Edge: 88+
- Firefox: 85+
- Safari: 14+
- Opera: 74+

CSS Variables, Grid, and Flexbox are required.

## License

This design system is part of the FakeAI project.

## Contributing

To contribute to the design system:

1. Follow the existing naming conventions
2. Document new components in this README
3. Test across different screen sizes
4. Ensure accessibility standards are met

## Resources

- [TailwindCSS Documentation](https://tailwindcss.com/docs)
- [NVIDIA Brand Guidelines](https://www.nvidia.com/en-us/about-nvidia/brand-guidelines/)
- [CSS Custom Properties](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
