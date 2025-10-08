# FakeAI Dashboard Testing Framework

Comprehensive testing infrastructure for the FakeAI Dashboard using 2025 best practices.

## Table of Contents

- [Overview](#overview)
- [Testing Stack](#testing-stack)
- [Getting Started](#getting-started)
- [Test Types](#test-types)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)

## Overview

This testing framework provides complete coverage for the FakeAI Dashboard, including:

- Unit tests for components and utilities
- Integration tests for API interactions
- E2E tests with Playwright
- Visual regression testing
- Performance benchmarking
- Accessibility testing
- WebSocket mocking and testing

## Testing Stack

### Core Testing Tools

- **Vitest** - Fast unit test framework with native ESM support
- **React Testing Library** - Component testing with user-centric approach
- **Playwright** - Modern E2E testing framework for cross-browser testing
- **MSW** (Mock Service Worker) - API mocking for tests
- **Happy DOM** - Lightweight DOM implementation for fast tests

### Additional Tools

- **@vitest/ui** - Interactive test UI
- **@vitest/coverage-v8** - Code coverage with V8
- **@testing-library/user-event** - Advanced user interaction simulation
- **vitest-canvas-mock** - Canvas API mocking for charts

## Getting Started

### Installation

```bash
cd fakeai/dashboard
npm install
```

### Configuration

The testing framework is configured through:

- `vitest.config.ts` - Unit test configuration
- `vitest.perf.config.ts` - Performance test configuration
- `playwright.config.ts` - E2E test configuration
- `tsconfig.json` - TypeScript configuration with test types

### Environment Setup

Create a `.env.test` file for test environment variables:

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## Test Types

### 1. Unit Tests

Test individual components and functions in isolation.

**Location:** `src/**/*.test.{ts,tsx}`

**Example:**
```typescript
import { describe, it, expect } from 'vitest';
import { renderWithProviders, screen } from '@test/utils';
import { MetricsOverview } from './MetricsOverview';

describe('MetricsOverview', () => {
  it('renders metrics correctly', () => {
    renderWithProviders(<MetricsOverview metrics={mockMetrics} />);
    expect(screen.getByText('Total Requests')).toBeInTheDocument();
  });
});
```

### 2. Integration Tests

Test component interactions with APIs and services.

**Location:** `src/**/*.test.{ts,tsx}`

**Example:**
```typescript
import { describe, it, expect } from 'vitest';
import { fetchModelMetrics } from './api';

describe('API Integration', () => {
  it('fetches model metrics', async () => {
    const metrics = await fetchModelMetrics();
    expect(metrics).toBeDefined();
  });
});
```

### 3. E2E Tests

Test complete user workflows in a real browser.

**Location:** `e2e/**/*.spec.ts`

**Example:**
```typescript
import { test, expect } from './fixtures';

test('displays dashboard metrics', async ({ dashboardPage, page }) => {
  await dashboardPage.goto();
  await expect(page.locator('[data-testid="metrics-overview"]')).toBeVisible();
});
```

### 4. Visual Regression Tests

Capture and compare screenshots to detect visual changes.

**Location:** `e2e/**/*.visual.spec.ts`

**Example:**
```typescript
test('dashboard matches baseline', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveScreenshot('dashboard.png');
});
```

### 5. Accessibility Tests

Validate WCAG compliance and accessibility best practices.

**Location:** `e2e/**/*.a11y.spec.ts`

**Example:**
```typescript
test('has proper ARIA attributes', async ({ page }) => {
  const buttons = await page.locator('button').all();
  for (const button of buttons) {
    const ariaLabel = await button.getAttribute('aria-label');
    expect(ariaLabel || await button.textContent()).toBeTruthy();
  }
});
```

### 6. Performance Tests

Measure render times, memory usage, and benchmark operations.

**Location:** `src/**/*.perf.test.{ts,tsx}`

**Example:**
```typescript
import { measureRenderTime, assertRenderTime } from '@test/performance';

it('renders within acceptable time', async () => {
  const time = await measureRenderTime(() => {
    render(<ChatCompletions />);
  });
  assertRenderTime(time, 500);
});
```

## Running Tests

### Unit Tests

```bash
# Run all unit tests
npm test

# Run in watch mode
npm run test:watch

# Run with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

### E2E Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI
npm run test:e2e:ui

# Run in debug mode
npm run test:e2e:debug

# Run visual regression tests only
npm run test:visual
```

### Performance Tests

```bash
npm run test:perf
```

### All Tests

```bash
npm run test:all
```

### Specific Test Files

```bash
# Run specific test file
npx vitest src/pages/ChatCompletions/api.test.ts

# Run specific test pattern
npx vitest --grep "MetricsOverview"
```

## Writing Tests

### Test Structure

Follow the AAA pattern: Arrange, Act, Assert

```typescript
describe('Component', () => {
  it('does something', () => {
    // Arrange - Set up test data
    const props = { value: 123 };

    // Act - Perform action
    const { getByText } = renderWithProviders(<Component {...props} />);

    // Assert - Verify outcome
    expect(getByText('123')).toBeInTheDocument();
  });
});
```

### Using Test Utilities

```typescript
import {
  renderWithProviders,
  setupUser,
  createMockResponse
} from '@test/utils';

// Render with providers
const { getByText } = renderWithProviders(<Component />);

// User interactions
const user = setupUser();
await user.click(getByText('Button'));

// Mock API responses
const response = createMockResponse({ data: 'value' });
```

### Mocking APIs

```typescript
import { server } from '@test/mocks/server';
import { http, HttpResponse } from 'msw';

// Override handler for specific test
server.use(
  http.get('/api/metrics', () => {
    return HttpResponse.json({ custom: 'data' });
  })
);
```

### Mocking WebSocket

```typescript
import { createMockWebSocket, createMetricsUpdateMessage } from '@test/mocks/websocket';

const ws = createMockWebSocket('ws://localhost:8000');
ws.simulateMessage(createMetricsUpdateMessage({ value: 123 }));
```

### Testing Async Behavior

```typescript
import { waitFor } from '@test/utils';

it('updates after data loads', async () => {
  const { getByText } = renderWithProviders(<Component />);

  await waitFor(() => {
    expect(getByText('Loaded')).toBeInTheDocument();
  });
});
```

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Push to main/develop/sagemaker branches
- Pull requests to main/develop
- Manual workflow dispatch

The workflow includes:
- Unit tests with coverage
- E2E tests on multiple browsers
- Visual regression tests
- Performance benchmarks
- Linting and type checking
- Build verification

### Coverage Reports

Coverage reports are automatically uploaded to Codecov and available as artifacts:
- HTML coverage report
- LCOV format for integration
- JSON summary

### Test Artifacts

All test runs produce artifacts:
- Test reports (HTML)
- Coverage reports
- Playwright traces
- Visual regression diffs (on failure)
- Performance benchmarks

## Best Practices

### 1. Test Naming

Use descriptive test names that explain the behavior:

```typescript
✓ GOOD: it('displays error message when API fails', () => {})
✗ BAD:  it('test error', () => {})
```

### 2. Test Independence

Each test should be independent and not rely on other tests:

```typescript
// Use beforeEach for setup
beforeEach(() => {
  localStorage.clear();
});
```

### 3. Test Data

Use mock data generators for consistent test data:

```typescript
import { generateMockChatRequest } from '@test/mocks/data';

const request = generateMockChatRequest({ model: 'gpt-4' });
```

### 4. Query Priority

Follow Testing Library's query priority:

1. `getByRole` - Most accessible
2. `getByLabelText` - Form elements
3. `getByText` - User-visible text
4. `getByTestId` - Last resort

### 5. Accessibility

Always test with accessibility in mind:

```typescript
// Use semantic queries
const button = screen.getByRole('button', { name: /submit/i });

// Check ARIA attributes
expect(button).toHaveAttribute('aria-label', 'Submit form');
```

### 6. Performance

Monitor test performance:

```typescript
// Use performance utilities
const time = await measureRenderTime(() => render(<Component />));
expect(time).toBeLessThan(100); // Assert max render time
```

### 7. Visual Tests

Keep visual tests stable:

```typescript
// Wait for animations
await page.waitForLoadState('networkidle');

// Disable animations
await expect(page).toHaveScreenshot('component.png', {
  animations: 'disabled',
});
```

### 8. Cleanup

Always clean up after tests:

```typescript
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
```

## Troubleshooting

### Tests Failing Intermittently

- Increase timeout for async operations
- Use `waitFor` instead of arbitrary delays
- Check for race conditions

### Visual Tests Failing

- Verify consistent viewport size
- Disable animations
- Check for dynamic content (timestamps, random data)

### Performance Tests Inconsistent

- Run performance tests in isolation
- Use average of multiple runs
- Account for CI environment differences

### WebSocket Tests Not Working

- Verify mock WebSocket is properly set up
- Check event listener registration
- Use `waitForOpen()` before sending messages

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)
- [MSW Documentation](https://mswjs.io/)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

## Support

For issues or questions:
1. Check this documentation
2. Review existing tests for examples
3. Check test output and error messages
4. Consult framework documentation

## License

Same as parent project.
