/**
 * Test utilities and helper functions
 * Provides custom render methods and common test helpers
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions, RenderResult } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

/**
 * Custom render function with common providers
 */
export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
): RenderResult {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <>{children}</>;
  }

  return render(ui, { wrapper: Wrapper, ...options });
}

/**
 * Setup user event for testing interactions
 */
export function setupUser() {
  return userEvent.setup();
}

/**
 * Wait for async operations with timeout
 */
export async function waitFor(
  callback: () => void | Promise<void>,
  options: { timeout?: number; interval?: number } = {}
): Promise<void> {
  const { timeout = 5000, interval = 50 } = options;
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    try {
      await callback();
      return;
    } catch (error) {
      await new Promise((resolve) => setTimeout(resolve, interval));
    }
  }

  throw new Error(`Timeout after ${timeout}ms`);
}

/**
 * Mock fetch response helper
 */
export function createMockResponse<T>(
  data: T,
  options: { status?: number; statusText?: string; headers?: HeadersInit } = {}
): Response {
  const { status = 200, statusText = 'OK', headers = {} } = options;

  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    headers: new Headers(headers),
    json: async () => data,
    text: async () => JSON.stringify(data),
    blob: async () => new Blob([JSON.stringify(data)]),
    arrayBuffer: async () => new ArrayBuffer(0),
    formData: async () => new FormData(),
    clone: () => createMockResponse(data, options),
    body: null,
    bodyUsed: false,
    redirected: false,
    type: 'basic',
    url: '',
  } as Response;
}

/**
 * Create a delayed promise for testing async behavior
 */
export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Generate mock data with customization
 */
export function createMockData<T>(
  defaults: T,
  overrides?: Partial<T>
): T {
  return { ...defaults, ...overrides };
}

/**
 * Spy on console methods
 */
export function spyOnConsole() {
  const originalError = console.error;
  const originalWarn = console.warn;
  const originalLog = console.log;

  const errors: any[] = [];
  const warnings: any[] = [];
  const logs: any[] = [];

  console.error = (...args: any[]) => errors.push(args);
  console.warn = (...args: any[]) => warnings.push(args);
  console.log = (...args: any[]) => logs.push(args);

  return {
    errors,
    warnings,
    logs,
    restore: () => {
      console.error = originalError;
      console.warn = originalWarn;
      console.log = originalLog;
    },
  };
}

/**
 * Assert that element is visible and has text
 */
export function assertElementWithText(
  element: HTMLElement | null,
  text: string
): void {
  if (!element) {
    throw new Error('Element not found');
  }
  if (!element.textContent?.includes(text)) {
    throw new Error(`Expected element to contain "${text}", but got "${element.textContent}"`);
  }
}

/**
 * Fire custom event
 */
export function fireCustomEvent(
  element: Element,
  eventType: string,
  detail?: any
): void {
  const event = new CustomEvent(eventType, { detail });
  element.dispatchEvent(event);
}

/**
 * Mock timer utilities
 */
export function createTimerUtils() {
  let timers: NodeJS.Timeout[] = [];

  return {
    setTimeout: (callback: () => void, delay: number) => {
      const timer = setTimeout(callback, delay);
      timers.push(timer);
      return timer;
    },
    setInterval: (callback: () => void, delay: number) => {
      const timer = setInterval(callback, delay);
      timers.push(timer);
      return timer;
    },
    clearAll: () => {
      timers.forEach((timer) => clearTimeout(timer));
      timers = [];
    },
  };
}

/**
 * Measure render performance
 */
export async function measureRenderTime(
  component: () => ReactElement
): Promise<number> {
  const startTime = performance.now();
  const { unmount } = renderWithProviders(component());
  const endTime = performance.now();
  unmount();
  return endTime - startTime;
}

/**
 * Create mock file for file upload tests
 */
export function createMockFile(
  name: string,
  size: number,
  type: string
): File {
  const blob = new Blob(['a'.repeat(size)], { type });
  return new File([blob], name, { type });
}

/**
 * Assert accessibility
 */
export async function assertAccessibility(
  container: HTMLElement
): Promise<void> {
  // Check for basic accessibility requirements
  const images = container.querySelectorAll('img');
  images.forEach((img) => {
    if (!img.hasAttribute('alt')) {
      throw new Error(`Image missing alt attribute: ${img.src}`);
    }
  });

  const buttons = container.querySelectorAll('button');
  buttons.forEach((button) => {
    if (!button.textContent?.trim() && !button.hasAttribute('aria-label')) {
      throw new Error('Button missing accessible name');
    }
  });
}

/**
 * Re-export commonly used testing library utilities
 */
export * from '@testing-library/react';
export { userEvent };
