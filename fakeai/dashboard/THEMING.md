# Theming and Customization Guide

Complete guide for customizing the appearance and behavior of the FakeAI Dashboard.

---

## Table of Contents

- [Overview](#overview)
- [CSS Variables](#css-variables)
- [Color Schemes](#color-schemes)
- [Typography](#typography)
- [Spacing System](#spacing-system)
- [Component Styling](#component-styling)
- [Dark Mode](#dark-mode)
- [Custom Themes](#custom-themes)
- [Responsive Design](#responsive-design)
- [Animation and Transitions](#animation-and-transitions)

---

## Overview

The dashboard uses CSS variables for theming, making it easy to customize colors, spacing, typography, and more without modifying component code.

### Theming Benefits

- **Consistency** - Centralized design tokens
- **Maintainability** - Easy to update global styles
- **Customization** - Override variables for custom themes
- **Runtime Changes** - Change themes dynamically
- **No Rebuild Required** - Modify CSS without recompiling

---

## CSS Variables

### Base Variables

**Location**: `src/styles/variables.css` (or inline in HTML)

```css
:root {
  /* Colors */
  --primary-color: #3b82f6;
  --primary-hover: #2563eb;
  --primary-light: #eff6ff;
  --secondary-color: #8b5cf6;
  --accent-color: #06b6d4;

  /* Status Colors */
  --success-color: #10b981;
  --success-light: #d1fae5;
  --warning-color: #f59e0b;
  --warning-light: #fef3c7;
  --error-color: #ef4444;
  --error-light: #fee2e2;
  --info-color: #3b82f6;
  --info-light: #dbeafe;

  /* Neutral Colors */
  --background-color: #ffffff;
  --surface-color: #f9fafb;
  --border-color: #e5e7eb;
  --text-color: #1f2937;
  --text-secondary: #6b7280;
  --text-muted: #9ca3af;

  /* Spacing */
  --spacing-xs: 0.25rem;    /* 4px */
  --spacing-sm: 0.5rem;     /* 8px */
  --spacing-md: 1rem;       /* 16px */
  --spacing-lg: 1.5rem;     /* 24px */
  --spacing-xl: 2rem;       /* 32px */
  --spacing-2xl: 3rem;      /* 48px */

  /* Typography */
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
  --font-family-mono: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;

  --font-size-xs: 0.75rem;   /* 12px */
  --font-size-sm: 0.875rem;  /* 14px */
  --font-size-md: 1rem;      /* 16px */
  --font-size-lg: 1.125rem;  /* 18px */
  --font-size-xl: 1.25rem;   /* 20px */
  --font-size-2xl: 1.5rem;   /* 24px */
  --font-size-3xl: 1.875rem; /* 30px */

  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;

  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);

  /* Transitions */
  --transition-fast: 150ms;
  --transition-normal: 300ms;
  --transition-slow: 500ms;

  /* Z-index */
  --z-dropdown: 1000;
  --z-modal: 2000;
  --z-tooltip: 3000;
  --z-notification: 4000;
}
```

---

## Color Schemes

### Light Theme (Default)

```css
:root {
  --background-color: #ffffff;
  --surface-color: #f9fafb;
  --border-color: #e5e7eb;
  --text-color: #1f2937;
  --text-secondary: #6b7280;
  --primary-color: #3b82f6;
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --error-color: #ef4444;
}
```

### Dark Theme

```css
[data-theme="dark"] {
  --background-color: #111827;
  --surface-color: #1f2937;
  --border-color: #374151;
  --text-color: #f9fafb;
  --text-secondary: #d1d5db;
  --primary-color: #60a5fa;
  --success-color: #34d399;
  --warning-color: #fbbf24;
  --error-color: #f87171;
}
```

### Blue Theme

```css
[data-theme="blue"] {
  --primary-color: #0ea5e9;
  --primary-hover: #0284c7;
  --primary-light: #e0f2fe;
  --accent-color: #06b6d4;
}
```

### Purple Theme

```css
[data-theme="purple"] {
  --primary-color: #a855f7;
  --primary-hover: #9333ea;
  --primary-light: #f3e8ff;
  --accent-color: #d946ef;
}
```

---

## Typography

### Font Families

```css
/* Default sans-serif */
.text-sans {
  font-family: var(--font-family);
}

/* Monospace for code */
.text-mono {
  font-family: var(--font-family-mono);
}
```

### Font Sizes

```css
.text-xs   { font-size: var(--font-size-xs); }   /* 12px */
.text-sm   { font-size: var(--font-size-sm); }   /* 14px */
.text-md   { font-size: var(--font-size-md); }   /* 16px */
.text-lg   { font-size: var(--font-size-lg); }   /* 18px */
.text-xl   { font-size: var(--font-size-xl); }   /* 20px */
.text-2xl  { font-size: var(--font-size-2xl); }  /* 24px */
.text-3xl  { font-size: var(--font-size-3xl); }  /* 30px */
```

### Font Weights

```css
.font-normal    { font-weight: var(--font-weight-normal); }    /* 400 */
.font-medium    { font-weight: var(--font-weight-medium); }    /* 500 */
.font-semibold  { font-weight: var(--font-weight-semibold); }  /* 600 */
.font-bold      { font-weight: var(--font-weight-bold); }      /* 700 */
```

### Line Heights

```css
.leading-tight    { line-height: var(--line-height-tight); }    /* 1.25 */
.leading-normal   { line-height: var(--line-height-normal); }   /* 1.5 */
.leading-relaxed  { line-height: var(--line-height-relaxed); }  /* 1.75 */
```

---

## Spacing System

### Padding

```css
.p-xs   { padding: var(--spacing-xs); }   /* 4px */
.p-sm   { padding: var(--spacing-sm); }   /* 8px */
.p-md   { padding: var(--spacing-md); }   /* 16px */
.p-lg   { padding: var(--spacing-lg); }   /* 24px */
.p-xl   { padding: var(--spacing-xl); }   /* 32px */
.p-2xl  { padding: var(--spacing-2xl); }  /* 48px */
```

### Margin

```css
.m-xs   { margin: var(--spacing-xs); }
.m-sm   { margin: var(--spacing-sm); }
.m-md   { margin: var(--spacing-md); }
.m-lg   { margin: var(--spacing-lg); }
.m-xl   { margin: var(--spacing-xl); }
```

### Gap (Flexbox/Grid)

```css
.gap-xs   { gap: var(--spacing-xs); }
.gap-sm   { gap: var(--spacing-sm); }
.gap-md   { gap: var(--spacing-md); }
.gap-lg   { gap: var(--spacing-lg); }
.gap-xl   { gap: var(--spacing-xl); }
```

---

## Component Styling

### Cards

```css
.card {
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--transition-normal);
}

.card:hover {
  box-shadow: var(--shadow-md);
}
```

### Buttons

```css
.button {
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  cursor: pointer;
}

.button-primary {
  background: var(--primary-color);
  color: white;
  border: none;
}

.button-primary:hover {
  background: var(--primary-hover);
}

.button-secondary {
  background: transparent;
  color: var(--text-color);
  border: 1px solid var(--border-color);
}
```

### Inputs

```css
.input {
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: var(--font-size-md);
  background: var(--background-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  transition: border-color var(--transition-fast);
}

.input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--primary-light);
}
```

---

## Dark Mode

### Implementation

```typescript
// Toggle dark mode
const toggleDarkMode = () => {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';

  if (isDark) {
    html.removeAttribute('data-theme');
    localStorage.setItem('theme', 'light');
  } else {
    html.setAttribute('data-theme', 'dark');
    localStorage.setItem('theme', 'dark');
  }
};

// Initialize from localStorage
const initTheme = () => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
};

// Call on page load
initTheme();
```

### Dark Mode Toggle Component

```typescript
export const DarkModeToggle: React.FC = () => {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const theme = localStorage.getItem('theme');
    setIsDark(theme === 'dark');
  }, []);

  const toggle = () => {
    const html = document.documentElement;
    const newIsDark = !isDark;

    if (newIsDark) {
      html.setAttribute('data-theme', 'dark');
      localStorage.setItem('theme', 'dark');
    } else {
      html.removeAttribute('data-theme');
      localStorage.setItem('theme', 'light');
    }

    setIsDark(newIsDark);
  };

  return (
    <button onClick={toggle}>
      {isDark ? '☀️ Light Mode' : '🌙 Dark Mode'}
    </button>
  );
};
```

---

## Custom Themes

### Creating a Custom Theme

1. Define theme variables:

```css
[data-theme="custom"] {
  /* Brand colors */
  --primary-color: #ff6b6b;
  --primary-hover: #ee5a52;
  --primary-light: #ffe0e0;

  /* Background */
  --background-color: #fafafa;
  --surface-color: #ffffff;

  /* Text */
  --text-color: #2c3e50;
  --text-secondary: #546e7a;
}
```

2. Apply theme:

```typescript
document.documentElement.setAttribute('data-theme', 'custom');
```

### Theme Switcher

```typescript
export const ThemeSwitcher: React.FC = () => {
  const [theme, setTheme] = useState('light');

  const themes = ['light', 'dark', 'blue', 'purple', 'custom'];

  const changeTheme = (newTheme: string) => {
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    setTheme(newTheme);
  };

  return (
    <select value={theme} onChange={(e) => changeTheme(e.target.value)}>
      {themes.map(t => (
        <option key={t} value={t}>{t}</option>
      ))}
    </select>
  );
};
```

---

## Responsive Design

### Breakpoints

```css
/* Mobile first approach */
:root {
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
  --breakpoint-2xl: 1536px;
}
```

### Media Queries

```css
/* Mobile (default) */
.container {
  padding: var(--spacing-md);
}

/* Tablet and up */
@media (min-width: 768px) {
  .container {
    padding: var(--spacing-lg);
  }
}

/* Desktop and up */
@media (min-width: 1024px) {
  .container {
    padding: var(--spacing-xl);
    max-width: 1200px;
    margin: 0 auto;
  }
}
```

### Responsive Grid

```css
.grid {
  display: grid;
  gap: var(--spacing-md);
}

/* Mobile: 1 column */
.grid {
  grid-template-columns: 1fr;
}

/* Tablet: 2 columns */
@media (min-width: 768px) {
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Desktop: 3 columns */
@media (min-width: 1024px) {
  .grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

---

## Animation and Transitions

### Transitions

```css
.transition-all {
  transition: all var(--transition-normal);
}

.transition-fast {
  transition: all var(--transition-fast);
}

.transition-slow {
  transition: all var(--transition-slow);
}
```

### Animations

```css
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideIn {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.animate-fade-in {
  animation: fadeIn var(--transition-normal);
}

.animate-slide-in {
  animation: slideIn var(--transition-normal);
}
```

### Loading Spinner

```css
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--border-color);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
```

---

## Best Practices

### 1. Use CSS Variables Consistently

```css
/* Bad */
.component {
  color: #3b82f6;
  padding: 16px;
}

/* Good */
.component {
  color: var(--primary-color);
  padding: var(--spacing-md);
}
```

### 2. Follow the Spacing System

```css
/* Bad */
.component {
  margin: 13px;
  padding: 19px;
}

/* Good */
.component {
  margin: var(--spacing-md);
  padding: var(--spacing-lg);
}
```

### 3. Use Semantic Color Names

```css
/* Bad */
.button {
  background: var(--color-blue-500);
}

/* Good */
.button {
  background: var(--primary-color);
}
```

### 4. Maintain Contrast Ratios

Ensure text is readable:
- Normal text: 4.5:1 minimum
- Large text: 3:1 minimum

### 5. Test Across Themes

Always test your components in both light and dark modes.

---

## Resources

- **CSS Variables**: https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties
- **Color Contrast Checker**: https://webaim.org/resources/contrastchecker/
- **Material Design Colors**: https://material.io/design/color/
- **Tailwind CSS**: https://tailwindcss.com/docs (inspiration)

---

**For questions about theming, open an issue on GitHub.**
