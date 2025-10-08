# Testing Quick Reference

Quick commands and patterns for testing the FakeAI Dashboard.

## Quick Commands

```bash
# Unit Tests
npm test                    # Run all unit tests
npm run test:watch          # Watch mode
npm run test:ui             # Interactive UI
npm run test:coverage       # With coverage report

# E2E Tests
npm run test:e2e            # Run all E2E tests
npm run test:e2e:ui         # With Playwright UI
npm run test:e2e:debug      # Debug mode
npm run test:visual         # Visual regression only

# Performance Tests
npm run test:perf           # Run performance tests

# All Tests
npm run test:all            # Everything

# Other
npm run type-check          # TypeScript check
npm run lint                # ESLint
```

## Common Test Patterns

### Basic Component Test
```typescript
import { describe, it, expect } from 'vitest';
import { renderWithProviders, screen } from '@test/utils';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    renderWithProviders(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

### Testing User Interactions
```typescript
import { setupUser } from '@test/utils';

it('handles click events', async () => {
  const user = setupUser();
  const { getByRole } = renderWithProviders(<Button />);

  await user.click(getByRole('button'));

  expect(getByText('Clicked')).toBeInTheDocument();
});
```

### Testing Async Data Loading
```typescript
import { waitFor } from '@test/utils';

it('loads data', async () => {
  const { getByText } = renderWithProviders(<DataComponent />);

  await waitFor(() => {
    expect(getByText('Data loaded')).toBeInTheDocument();
  });
});
```

### Mocking API Responses
```typescript
import { server } from '@test/mocks/server';
import { http, HttpResponse } from 'msw';

it('handles API error', async () => {
  server.use(
    http.get('/api/data', () => {
      return new HttpResponse(null, { status: 500 });
    })
  );

  // Test error handling...
});
```

### Testing WebSocket
```typescript
import { createMockWebSocket } from '@test/mocks/websocket';

it('receives messages', () => {
  const ws = createMockWebSocket('ws://localhost');
  ws.simulateMessage({ type: 'update', data: { value: 123 } });

  // Verify message handling...
});
```

### E2E Test
```typescript
import { test, expect } from './fixtures';

test('user can login', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password');
  await page.click('button[type="submit"]');

  await expect(page).toHaveURL('/dashboard');
});
```

### Visual Regression Test
```typescript
test('component matches baseline', async ({ page }) => {
  await page.goto('/component');
  await page.waitForLoadState('networkidle');

  await expect(page).toHaveScreenshot('component.png', {
    fullPage: true,
    animations: 'disabled'
  });
});
```

### Performance Test
```typescript
import { measureRenderTime, assertRenderTime } from '@test/performance';

it('renders quickly', async () => {
  const time = await measureRenderTime(() => {
    renderWithProviders(<HeavyComponent />);
  });

  assertRenderTime(time, 500); // Max 500ms
});
```

## Query Priority (React Testing Library)

Use queries in this order:

1. **getByRole** - Most accessible
   ```typescript
   screen.getByRole('button', { name: /submit/i })
   ```

2. **getByLabelText** - Forms
   ```typescript
   screen.getByLabelText('Email')
   ```

3. **getByPlaceholderText** - Inputs
   ```typescript
   screen.getByPlaceholderText('Enter email')
   ```

4. **getByText** - User-visible text
   ```typescript
   screen.getByText('Hello World')
   ```

5. **getByTestId** - Last resort
   ```typescript
   screen.getByTestId('custom-element')
   ```

## Assertion Examples

```typescript
// Element presence
expect(element).toBeInTheDocument();
expect(element).not.toBeInTheDocument();

// Visibility
expect(element).toBeVisible();
expect(element).toBeHidden();

// Text content
expect(element).toHaveTextContent('Hello');
expect(element).toContainHTML('<span>Hello</span>');

// Attributes
expect(element).toHaveAttribute('href', '/link');
expect(element).toHaveClass('active');

// Form elements
expect(input).toHaveValue('test');
expect(checkbox).toBeChecked();
expect(select).toHaveDisplayValue('Option 1');

// Async
await waitFor(() => {
  expect(element).toBeInTheDocument();
});

// Numbers
expect(value).toBeGreaterThan(10);
expect(value).toBeLessThan(100);
expect(value).toBeCloseTo(3.14, 2);

// Arrays
expect(array).toHaveLength(5);
expect(array).toContain('item');
expect(array).toEqual([1, 2, 3]);

// Objects
expect(obj).toHaveProperty('key');
expect(obj).toMatchObject({ key: 'value' });
```

## Mocking Examples

### Mock Function
```typescript
import { vi } from 'vitest';

const mockFn = vi.fn();
mockFn.mockReturnValue(42);
mockFn.mockResolvedValue({ data: 'async' });

expect(mockFn).toHaveBeenCalled();
expect(mockFn).toHaveBeenCalledWith('arg');
expect(mockFn).toHaveBeenCalledTimes(2);
```

### Mock Module
```typescript
vi.mock('./api', () => ({
  fetchData: vi.fn().mockResolvedValue({ id: 1 }),
}));
```

### Mock Timer
```typescript
vi.useFakeTimers();

// Advance by time
vi.advanceTimersByTime(1000);

// Run all timers
vi.runAllTimers();

// Restore
vi.useRealTimers();
```

## Test Data Generators

```typescript
import {
  generateMockChatRequest,
  generateMockModelStats,
} from '@test/mocks/data';

// Generate single item
const request = generateMockChatRequest({
  model: 'gpt-4',
  status: 'success'
});

// Generate multiple items
const requests = Array.from({ length: 10 }, () =>
  generateMockChatRequest()
);

// Use predefined mocks
import { mockModelStats, mockChatRequests } from '@test/mocks/data';
```

## Debugging Tests

### Console Output
```typescript
screen.debug(); // Print entire DOM
screen.debug(element); // Print specific element
```

### Playwright Debug
```bash
# Debug mode
npm run test:e2e:debug

# Headed mode
npx playwright test --headed

# Specific test
npx playwright test --grep "test name"

# Trace viewer
npx playwright show-trace trace.zip
```

### Vitest Debug
```bash
# Run single test file
npx vitest src/path/to/test.ts

# Run with pattern
npx vitest --grep "test pattern"

# Update snapshots
npx vitest -u
```

## Common Pitfalls

### Don't
```typescript
// ❌ Arbitrary waits
await new Promise(r => setTimeout(r, 1000));

// ❌ Query by implementation details
container.querySelector('.css-class');

// ❌ Testing implementation
expect(component.state).toBe('loading');

// ❌ Multiple assertions without waiting
expect(element).toBeInTheDocument();
expect(element).toHaveTextContent('text'); // Might fail
```

### Do
```typescript
// ✅ Wait for conditions
await waitFor(() => {
  expect(element).toBeInTheDocument();
});

// ✅ Query by accessibility
screen.getByRole('button', { name: /submit/i });

// ✅ Test behavior
expect(screen.getByText('Success')).toBeInTheDocument();

// ✅ Wait between checks
await waitFor(() => {
  expect(element).toBeInTheDocument();
});
expect(element).toHaveTextContent('text');
```

## File Locations

```
Component test:     src/path/to/Component.test.tsx
API test:          src/path/to/api.test.ts
Service test:      src/services/Service.test.ts
Performance test:  src/path/to/Component.perf.test.tsx

E2E test:          e2e/feature.spec.ts
Visual test:       e2e/feature.visual.spec.ts
A11y test:         e2e/feature.a11y.spec.ts

Mock data:         src/test/mocks/data.ts
Mock handlers:     src/test/mocks/handlers.ts
Test utils:        src/test/utils.tsx
```

## Resources

- Full Guide: [TESTING.md](./TESTING.md)
- Summary: [TEST_SUMMARY.md](./TEST_SUMMARY.md)
- Vitest: https://vitest.dev
- Playwright: https://playwright.dev
- Testing Library: https://testing-library.com
