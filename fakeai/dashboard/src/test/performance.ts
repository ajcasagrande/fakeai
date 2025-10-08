/**
 * Performance testing utilities
 * Provides tools for measuring and asserting performance metrics
 */

import { vi } from 'vitest';

/**
 * Performance metrics interface
 */
export interface PerformanceMetrics {
  renderTime: number;
  totalTime: number;
  memoryUsed?: number;
  reRenderCount: number;
}

/**
 * Performance profiler for React components
 */
export class PerformanceProfiler {
  private startTime: number = 0;
  private renderCount: number = 0;
  private metrics: Map<string, number[]> = new Map();

  /**
   * Start profiling
   */
  start(): void {
    this.startTime = performance.now();
    this.renderCount = 0;
  }

  /**
   * Record a render
   */
  recordRender(componentName: string): void {
    this.renderCount++;
    const renderTime = performance.now() - this.startTime;

    if (!this.metrics.has(componentName)) {
      this.metrics.set(componentName, []);
    }

    this.metrics.get(componentName)!.push(renderTime);
  }

  /**
   * Get metrics for a component
   */
  getMetrics(componentName: string): {
    count: number;
    average: number;
    min: number;
    max: number;
  } {
    const times = this.metrics.get(componentName) || [];

    if (times.length === 0) {
      return { count: 0, average: 0, min: 0, max: 0 };
    }

    const sum = times.reduce((a, b) => a + b, 0);
    const average = sum / times.length;
    const min = Math.min(...times);
    const max = Math.max(...times);

    return { count: times.length, average, min, max };
  }

  /**
   * Get total render count
   */
  getTotalRenderCount(): number {
    return this.renderCount;
  }

  /**
   * Stop profiling and get results
   */
  stop(): PerformanceMetrics {
    const totalTime = performance.now() - this.startTime;

    return {
      renderTime: totalTime,
      totalTime,
      reRenderCount: this.renderCount,
      memoryUsed: this.getMemoryUsage(),
    };
  }

  /**
   * Get memory usage (if available)
   */
  private getMemoryUsage(): number | undefined {
    if (performance.memory) {
      return performance.memory.usedJSHeapSize / 1024 / 1024; // MB
    }
    return undefined;
  }

  /**
   * Reset profiler
   */
  reset(): void {
    this.startTime = 0;
    this.renderCount = 0;
    this.metrics.clear();
  }
}

/**
 * Measure render time of a function
 */
export async function measureRenderTime(
  fn: () => void | Promise<void>
): Promise<number> {
  const startTime = performance.now();
  await fn();
  return performance.now() - startTime;
}

/**
 * Measure multiple renders and get statistics
 */
export async function measureMultipleRenders(
  fn: () => void | Promise<void>,
  iterations: number = 10
): Promise<{
  average: number;
  min: number;
  max: number;
  median: number;
  p95: number;
  p99: number;
}> {
  const times: number[] = [];

  for (let i = 0; i < iterations; i++) {
    const time = await measureRenderTime(fn);
    times.push(time);
  }

  times.sort((a, b) => a - b);

  const sum = times.reduce((a, b) => a + b, 0);
  const average = sum / times.length;
  const min = times[0];
  const max = times[times.length - 1];
  const median = times[Math.floor(times.length / 2)];
  const p95 = times[Math.floor(times.length * 0.95)];
  const p99 = times[Math.floor(times.length * 0.99)];

  return { average, min, max, median, p95, p99 };
}

/**
 * Assert render time is within threshold
 */
export function assertRenderTime(
  actualTime: number,
  maxTime: number,
  message?: string
): void {
  if (actualTime > maxTime) {
    throw new Error(
      message ||
        `Render time ${actualTime.toFixed(2)}ms exceeds maximum ${maxTime}ms`
    );
  }
}

/**
 * Assert re-render count is within threshold
 */
export function assertReRenderCount(
  actualCount: number,
  maxCount: number,
  message?: string
): void {
  if (actualCount > maxCount) {
    throw new Error(
      message ||
        `Re-render count ${actualCount} exceeds maximum ${maxCount}`
    );
  }
}

/**
 * Mock performance API for testing
 */
export function mockPerformanceAPI() {
  const originalNow = performance.now;
  let mockTime = 0;

  const mock = {
    now: vi.fn(() => mockTime),
    advance: (ms: number) => {
      mockTime += ms;
    },
    reset: () => {
      mockTime = 0;
    },
    restore: () => {
      performance.now = originalNow;
    },
  };

  performance.now = mock.now as any;

  return mock;
}

/**
 * Measure memory usage
 */
export function getMemoryUsage(): number | null {
  if (performance.memory) {
    return performance.memory.usedJSHeapSize / 1024 / 1024; // MB
  }
  return null;
}

/**
 * Monitor for memory leaks
 */
export class MemoryLeakDetector {
  private baseline: number | null = null;
  private threshold: number;

  constructor(thresholdMB: number = 10) {
    this.threshold = thresholdMB;
  }

  /**
   * Set baseline memory usage
   */
  setBaseline(): void {
    this.baseline = getMemoryUsage();
  }

  /**
   * Check for memory leak
   */
  check(): boolean {
    if (this.baseline === null) {
      throw new Error('Baseline not set. Call setBaseline() first.');
    }

    const current = getMemoryUsage();
    if (current === null) {
      return false; // Can't detect without memory API
    }

    const increase = current - this.baseline;
    return increase > this.threshold;
  }

  /**
   * Get memory increase since baseline
   */
  getMemoryIncrease(): number | null {
    if (this.baseline === null) {
      return null;
    }

    const current = getMemoryUsage();
    if (current === null) {
      return null;
    }

    return current - this.baseline;
  }
}

/**
 * Benchmark a function
 */
export async function benchmark(
  name: string,
  fn: () => void | Promise<void>,
  iterations: number = 1000
): Promise<{
  name: string;
  iterations: number;
  totalTime: number;
  averageTime: number;
  opsPerSecond: number;
}> {
  const startTime = performance.now();

  for (let i = 0; i < iterations; i++) {
    await fn();
  }

  const totalTime = performance.now() - startTime;
  const averageTime = totalTime / iterations;
  const opsPerSecond = (iterations / totalTime) * 1000;

  return {
    name,
    iterations,
    totalTime,
    averageTime,
    opsPerSecond,
  };
}

/**
 * Compare benchmark results
 */
export function compareBenchmarks(
  baseline: { averageTime: number },
  current: { averageTime: number }
): {
  percentChange: number;
  isRegression: boolean;
  isFaster: boolean;
} {
  const percentChange =
    ((current.averageTime - baseline.averageTime) / baseline.averageTime) * 100;

  return {
    percentChange,
    isRegression: percentChange > 10, // More than 10% slower
    isFaster: percentChange < -5, // More than 5% faster
  };
}

/**
 * Create a performance observer
 */
export function createPerformanceObserver(
  callback: (entries: PerformanceEntry[]) => void
): PerformanceObserver | null {
  if (typeof PerformanceObserver === 'undefined') {
    return null;
  }

  const observer = new PerformanceObserver(list => {
    const entries = list.getEntries();
    callback(entries);
  });

  return observer;
}

/**
 * Measure long tasks (tasks > 50ms)
 */
export async function measureLongTasks(
  fn: () => void | Promise<void>
): Promise<PerformanceEntry[]> {
  const longTasks: PerformanceEntry[] = [];

  const observer = createPerformanceObserver(entries => {
    entries.forEach(entry => {
      if (entry.duration > 50) {
        longTasks.push(entry);
      }
    });
  });

  if (observer) {
    observer.observe({ entryTypes: ['measure', 'mark'] });
  }

  await fn();

  if (observer) {
    observer.disconnect();
  }

  return longTasks;
}

/**
 * Wait for idle time
 */
export async function waitForIdle(timeout: number = 5000): Promise<void> {
  return new Promise((resolve, reject) => {
    if (typeof requestIdleCallback === 'undefined') {
      setTimeout(resolve, 0);
      return;
    }

    const timeoutId = setTimeout(() => {
      reject(new Error('Idle timeout exceeded'));
    }, timeout);

    requestIdleCallback(() => {
      clearTimeout(timeoutId);
      resolve();
    });
  });
}
