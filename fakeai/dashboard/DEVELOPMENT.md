# Development Guide

This guide covers everything you need to know to develop, test, and contribute to the FakeAI Dashboard.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Development Server](#development-server)
- [Project Configuration](#project-configuration)
- [Development Workflow](#development-workflow)
- [Code Organization](#code-organization)
- [TypeScript Guidelines](#typescript-guidelines)
- [Component Development](#component-development)
- [API Integration](#api-integration)
- [State Management](#state-management)
- [Styling Guidelines](#styling-guidelines)
- [Testing](#testing)
- [Debugging](#debugging)
- [Build Process](#build-process)
- [Git Workflow](#git-workflow)

---

## Prerequisites

### Required Software

- **Node.js** 18.0.0 or higher
- **npm** 9.0.0 or higher (comes with Node.js)
- **Git** 2.30.0 or higher
- **Python** 3.10+ (for FakeAI server)

### Recommended Tools

- **VS Code** with extensions:
  - ESLint
  - Prettier
  - TypeScript and JavaScript Language Features
  - Volar (Vue Language Features)
- **React Developer Tools** (browser extension)
- **Redux DevTools** (if using Redux)
- **Postman** or **Insomnia** for API testing

### Verify Installation

```bash
# Check Node.js version
node --version
# Expected: v18.0.0 or higher

# Check npm version
npm --version
# Expected: 9.0.0 or higher

# Check Python version
python --version
# Expected: Python 3.10.0 or higher
```

---

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/ajcasagrande/fakeai.git
cd fakeai/fakeai/dashboard
```

### 2. Install Dependencies

```bash
# Install all npm dependencies
npm install

# This will install:
# - React 18
# - TypeScript 5
# - Vite
# - Axios
# - Recharts
# - Date-fns
# - And all development dependencies
```

### 3. Configure Environment

Create a `.env` file in the dashboard directory:

```bash
# Copy the example environment file
cp .env.example .env

# Edit the file with your settings
nano .env
```

Example `.env` configuration:

```bash
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Feature Flags
VITE_ENABLE_WEBSOCKETS=true
VITE_ENABLE_STREAMING_METRICS=true
VITE_ENABLE_DEBUG_MODE=false

# UI Configuration
VITE_DEFAULT_PAGE_SIZE=20
VITE_AUTO_REFRESH_INTERVAL=30000
VITE_DEFAULT_CHART_TYPE=pie

# Development
VITE_DEBUG_API_CALLS=false
VITE_MOCK_API=false
```

### 4. Start FakeAI Server

The dashboard requires the FakeAI server to be running:

```bash
# In a separate terminal, navigate to the project root
cd /path/to/fakeai

# Install FakeAI (if not already installed)
pip install -e .

# Start the server
fakeai server --port 8000
```

### 5. Verify Setup

```bash
# Check if FakeAI server is running
curl http://localhost:8000/health

# Expected response:
# {"status": "ok", "version": "x.x.x"}
```

---

## Development Server

### Start Development Server

```bash
# Start Vite development server with hot reload
npm run dev

# Server will start at http://localhost:5173
# Open your browser to http://localhost:5173
```

### Development Server Features

- **Hot Module Replacement (HMR)** - Instant updates without full page reload
- **Fast Refresh** - Preserves component state during updates
- **TypeScript Checking** - Real-time type checking
- **Error Overlay** - In-browser error display
- **Network Inspection** - Built-in proxy for API calls

### Alternative Commands

```bash
# Start with custom port
npm run dev -- --port 3000

# Start with host binding (for network access)
npm run dev -- --host

# Start with HTTPS
npm run dev -- --https
```

---

## Project Configuration

### Vite Configuration

`vite.config.ts` controls the build and development server:

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/pages': path.resolve(__dirname, './src/pages'),
      '@/api': path.resolve(__dirname, './src/api'),
      '@/services': path.resolve(__dirname, './src/services'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/v1': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/metrics': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          charts: ['recharts'],
        },
      },
    },
  },
});
```

### TypeScript Configuration

`tsconfig.json` defines TypeScript compiler options:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

---

## Development Workflow

### Typical Development Cycle

1. **Create a feature branch**
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make changes**
   - Edit files in `src/`
   - Save to see hot reload in browser

3. **Test changes**
   - Manually test in browser
   - Run automated tests (when available)

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/my-new-feature
   ```

### Development Best Practices

- **Small, focused commits** - One logical change per commit
- **Descriptive commit messages** - Follow conventional commits format
- **Test as you go** - Don't wait until the end to test
- **Keep dependencies up to date** - Regularly check for updates
- **Document complex logic** - Add comments for non-obvious code
- **Use TypeScript strictly** - No `any` types unless absolutely necessary

---

## Code Organization

### Directory Structure

```
src/
├── api/                    # API client and configuration
│   ├── client.ts          # Axios instance with interceptors
│   ├── auth.ts            # Authentication utilities
│   ├── cache.ts           # Response caching
│   ├── errors.ts          # Error handling
│   ├── types.ts           # API type definitions
│   └── endpoints/         # Endpoint-specific modules
│
├── services/              # Business logic and utilities
│   ├── WebSocketService.ts   # WebSocket management
│   ├── WebSocketContext.tsx  # Context provider
│   ├── hooks.ts              # Custom hooks
│   ├── types.ts              # Service types
│   └── components/           # Shared service components
│
├── pages/                 # Page components
│   ├── ChatCompletions/   # Each page has its own directory
│   │   ├── ChatCompletions.tsx    # Main page component
│   │   ├── types.ts              # Page-specific types
│   │   ├── api.ts                # Page-specific API calls
│   │   ├── styles.css            # Page styles
│   │   ├── index.ts              # Public exports
│   │   └── components/           # Page components
│   │       ├── MetricsOverview.tsx
│   │       ├── ModelUsageChart.tsx
│   │       └── ...
│   └── ...
│
├── types/                 # Shared type definitions
├── utils/                 # Utility functions
└── constants/             # Constants and configuration
```

### File Naming Conventions

- **Components**: PascalCase - `MetricsOverview.tsx`
- **Utilities**: camelCase - `formatDate.ts`
- **Types**: PascalCase - `types.ts`
- **Styles**: kebab-case - `metrics-overview.css`
- **Tests**: Same as source file + `.test` - `MetricsOverview.test.tsx`

### Module Organization

Each page follows this structure:

```
PageName/
├── PageName.tsx           # Main page component
├── types.ts               # Type definitions
├── api.ts                 # API calls
├── styles.css             # Styles
├── index.ts               # Public exports
└── components/            # Page-specific components
    ├── Component1.tsx
    ├── Component2.tsx
    └── ...
```

---

## TypeScript Guidelines

### Type Safety

Always prefer type safety over `any`:

```typescript
// Bad
const data: any = await fetchData();

// Good
interface DataResponse {
  id: string;
  name: string;
  value: number;
}
const data: DataResponse = await fetchData();
```

### Interface vs Type

Use interfaces for object shapes, types for unions/intersections:

```typescript
// Interfaces for objects
interface User {
  id: string;
  name: string;
  email: string;
}

// Types for unions
type Status = 'success' | 'error' | 'pending';

// Types for intersections
type UserWithRole = User & { role: string };
```

### Generic Types

Use generics for reusable components:

```typescript
interface ApiResponse<T> {
  data: T;
  status: number;
  message: string;
}

function fetchData<T>(url: string): Promise<ApiResponse<T>> {
  // Implementation
}
```

### Enum vs Union Types

Prefer union types over enums:

```typescript
// Prefer this
type ChartType = 'pie' | 'bar' | 'line';

// Over this
enum ChartType {
  Pie = 'pie',
  Bar = 'bar',
  Line = 'line',
}
```

---

## Component Development

### Component Template

```typescript
/**
 * ComponentName - Brief description
 *
 * Longer description if needed
 */

import React, { useState, useEffect } from 'react';
import './styles.css';

interface ComponentNameProps {
  // Props with JSDoc comments
  /** Description of prop */
  propName: string;
  /** Optional prop */
  optionalProp?: number;
  /** Callback function */
  onAction?: (value: string) => void;
}

export const ComponentName: React.FC<ComponentNameProps> = ({
  propName,
  optionalProp = 0,
  onAction,
}) => {
  // State
  const [state, setState] = useState<string>('');

  // Effects
  useEffect(() => {
    // Effect logic
  }, [propName]);

  // Handlers
  const handleClick = () => {
    if (onAction) {
      onAction(state);
    }
  };

  // Render
  return (
    <div className="component-name">
      <h2>{propName}</h2>
      <button onClick={handleClick}>Action</button>
    </div>
  );
};

export default ComponentName;
```

### Custom Hooks

Extract reusable logic into custom hooks:

```typescript
/**
 * useApiData - Fetch and manage API data
 */
function useApiData<T>(url: string) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get<T>(url);
        setData(response.data);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [url]);

  return { data, loading, error };
}
```

### Component Best Practices

- **Single Responsibility** - One component, one purpose
- **Props Interface** - Always define prop types
- **Default Props** - Use destructuring defaults
- **Memoization** - Use React.memo for expensive components
- **Event Handlers** - Prefix with `handle` (e.g., `handleClick`)
- **CSS Scoping** - Use CSS modules or BEM naming

---

## API Integration

### Making API Calls

Use the centralized API client:

```typescript
import { apiClient } from '@/api/client';

// GET request
const response = await apiClient.get('/v1/models');

// POST request
const response = await apiClient.post('/v1/chat/completions', {
  model: 'openai/gpt-oss-120b',
  messages: [{ role: 'user', content: 'Hello' }],
});

// With type safety
interface ModelResponse {
  id: string;
  name: string;
}
const response = await apiClient.get<ModelResponse[]>('/v1/models');
```

### Error Handling

```typescript
import { ApiError } from '@/api/errors';

try {
  const response = await apiClient.get('/v1/models');
  return response.data;
} catch (error) {
  if (error instanceof ApiError) {
    console.error('API Error:', error.message, error.statusCode);
    // Handle specific error codes
    if (error.statusCode === 401) {
      // Redirect to login
    }
  } else {
    console.error('Unknown error:', error);
  }
}
```

### Caching

The API client includes automatic caching:

```typescript
// Cached for 30 seconds (configured in client.ts)
const response = await apiClient.get('/v1/models');

// Clear cache manually
import { clearCache } from '@/api/client';
clearCache();
```

---

## State Management

### Local State

Use `useState` for component-local state:

```typescript
const [count, setCount] = useState(0);
const [user, setUser] = useState<User | null>(null);
```

### Context API

For shared state across components:

```typescript
// Create context
const ThemeContext = React.createContext<{
  theme: string;
  setTheme: (theme: string) => void;
}>({ theme: 'light', setTheme: () => {} });

// Provider
export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState('light');
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

// Consumer hook
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};
```

---

## Styling Guidelines

### CSS Organization

```css
/* Component styles follow BEM naming */
.component-name {
  /* Layout */
  display: flex;
  flex-direction: column;
  gap: 1rem;

  /* Visual */
  background: var(--background-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1.5rem;
}

.component-name__header {
  /* Nested element */
}

.component-name--loading {
  /* Modifier */
  opacity: 0.5;
}
```

### CSS Variables

Use CSS variables for theming:

```css
:root {
  /* Colors */
  --primary-color: #3b82f6;
  --secondary-color: #8b5cf6;
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --error-color: #ef4444;

  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;

  /* Typography */
  --font-size-sm: 0.875rem;
  --font-size-md: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
}
```

---

## Testing

### Unit Testing (Future)

When testing is added:

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage
```

### Manual Testing Checklist

- [ ] Component renders without errors
- [ ] All interactive elements work
- [ ] API calls succeed
- [ ] Error states display correctly
- [ ] Loading states work
- [ ] Responsive design works on mobile
- [ ] Accessibility features work
- [ ] No console errors or warnings

---

## Debugging

### Browser DevTools

```javascript
// Console logging
console.log('Data:', data);
console.error('Error:', error);
console.table(arrayData);

// React DevTools
// - Inspect component props and state
// - Profile component performance
// - Debug hooks

// Network tab
// - Inspect API requests/responses
// - Check request timing
// - View response payloads
```

### VS Code Debugging

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "chrome",
      "request": "launch",
      "name": "Launch Chrome",
      "url": "http://localhost:5173",
      "webRoot": "${workspaceFolder}/src",
      "sourceMapPathOverrides": {
        "webpack:///./src/*": "${webRoot}/*"
      }
    }
  ]
}
```

---

## Build Process

### Production Build

```bash
# Build the dashboard
npm run build

# Output directory: dist/
# - index.html
# - assets/ (JS, CSS, images)
```

### Build Optimization

The build process includes:

- **Code Splitting** - Separate vendor and app bundles
- **Minification** - Smaller file sizes
- **Tree Shaking** - Remove unused code
- **Source Maps** - For debugging production issues
- **Asset Optimization** - Compress images and fonts

### Preview Production Build

```bash
# Build and preview
npm run build
npm run preview

# Opens preview server at http://localhost:4173
```

---

## Git Workflow

### Commit Message Format

Follow conventional commits:

```bash
# Format: <type>(<scope>): <subject>

# Types:
# - feat: New feature
# - fix: Bug fix
# - docs: Documentation
# - style: Code style (formatting)
# - refactor: Code refactoring
# - test: Tests
# - chore: Build process, dependencies

# Examples:
git commit -m "feat(chat): add streaming metrics component"
git commit -m "fix(api): handle network timeout errors"
git commit -m "docs(readme): update installation instructions"
```

### Branch Naming

```bash
# Format: <type>/<description>

# Examples:
feature/add-dark-mode
fix/api-connection-error
docs/update-development-guide
refactor/simplify-state-management
```

---

## Common Commands Reference

```bash
# Development
npm run dev                 # Start development server
npm run build              # Build for production
npm run preview            # Preview production build

# Maintenance
npm install                # Install dependencies
npm update                 # Update dependencies
npm outdated              # Check for outdated packages

# Cleaning
rm -rf node_modules dist   # Clean dependencies and build
npm install               # Reinstall
```

---

## Getting Help

- **Documentation**: Check other markdown files in this directory
- **FakeAI Issues**: https://github.com/ajcasagrande/fakeai/issues
- **Stack Overflow**: Tag questions with `fakeai` and `react`

---

**Happy coding!**
