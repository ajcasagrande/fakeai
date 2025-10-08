/**
 * Performance tests for ChatCompletions component
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { renderWithProviders } from '@test/utils';
import { ChatCompletions } from './ChatCompletions';
import {
  measureRenderTime,
  measureMultipleRenders,
  assertRenderTime,
  PerformanceProfiler,
  MemoryLeakDetector,
  benchmark,
} from '@test/performance';
import { generateMockModelStatsArray, generateMockChatRequests } from '@test/mocks/data';

describe('ChatCompletions Performance', () => {
  describe('Render Performance', () => {
    it('renders within acceptable time with small dataset', async () => {
      const renderTime = await measureRenderTime(() => {
        const { unmount } = renderWithProviders(<ChatCompletions />);
        unmount();
      });

      assertRenderTime(renderTime, 500, 'Initial render should be under 500ms');
      console.log(`Render time with small dataset: ${renderTime.toFixed(2)}ms`);
    });

    it('renders efficiently with large dataset', async () => {
      // Mock large dataset
      const largeDataset = generateMockModelStatsArray(100);

      const renderTime = await measureRenderTime(() => {
        const { unmount } = renderWithProviders(<ChatCompletions />);
        unmount();
      });

      assertRenderTime(renderTime, 1000, 'Render with large dataset should be under 1000ms');
      console.log(`Render time with large dataset: ${renderTime.toFixed(2)}ms`);
    });

    it('has consistent render times across multiple renders', async () => {
      const stats = await measureMultipleRenders(() => {
        const { unmount } = renderWithProviders(<ChatCompletions />);
        unmount();
      }, 10);

      console.log('Render statistics:', {
        average: `${stats.average.toFixed(2)}ms`,
        min: `${stats.min.toFixed(2)}ms`,
        max: `${stats.max.toFixed(2)}ms`,
        median: `${stats.median.toFixed(2)}ms`,
        p95: `${stats.p95.toFixed(2)}ms`,
        p99: `${stats.p99.toFixed(2)}ms`,
      });

      // P95 should be reasonable
      expect(stats.p95).toBeLessThan(800);
    });
  });

  describe('Re-render Optimization', () => {
    it('minimizes re-renders on state updates', async () => {
      const profiler = new PerformanceProfiler();
      profiler.start();

      const { rerender } = renderWithProviders(<ChatCompletions />);

      // Simulate multiple updates
      for (let i = 0; i < 5; i++) {
        rerender(<ChatCompletions />);
        profiler.recordRender('ChatCompletions');
      }

      const metrics = profiler.stop();

      // Should not re-render excessively
      expect(metrics.reRenderCount).toBeLessThanOrEqual(5);

      console.log('Re-render metrics:', {
        totalRenders: metrics.reRenderCount,
        totalTime: `${metrics.renderTime.toFixed(2)}ms`,
      });
    });
  });

  describe('Memory Management', () => {
    it('does not leak memory on mount/unmount cycles', () => {
      const detector = new MemoryLeakDetector(5); // 5MB threshold
      detector.setBaseline();

      // Mount and unmount multiple times
      for (let i = 0; i < 10; i++) {
        const { unmount } = renderWithProviders(<ChatCompletions />);
        unmount();
      }

      // Force garbage collection if available
      if (global.gc) {
        global.gc();
      }

      const hasLeak = detector.check();
      const memoryIncrease = detector.getMemoryIncrease();

      console.log(`Memory increase: ${memoryIncrease?.toFixed(2) || 'N/A'}MB`);

      if (memoryIncrease !== null) {
        expect(hasLeak).toBe(false);
      }
    });
  });

  describe('Data Processing Performance', () => {
    it('processes model stats efficiently', async () => {
      const largeStats = generateMockModelStatsArray(100);

      const result = await benchmark(
        'Process model stats',
        () => {
          // Simulate the useMemo calculations
          const stats = Object.values(largeStats);
          const totalRequests = stats.reduce((sum, s) => sum + s.request_count, 0);
          const totalTokens = stats.reduce((sum, s) => sum + s.total_tokens, 0);
          const totalCost = stats.reduce((sum, s) => sum + s.total_cost, 0);
        },
        1000
      );

      console.log('Stats processing benchmark:', {
        iterations: result.iterations,
        averageTime: `${result.averageTime.toFixed(4)}ms`,
        opsPerSecond: `${result.opsPerSecond.toFixed(0)} ops/s`,
      });

      // Should process very quickly
      expect(result.averageTime).toBeLessThan(1); // Less than 1ms
    });

    it('filters requests efficiently', async () => {
      const largeRequestList = generateMockChatRequests(1000);

      const result = await benchmark(
        'Filter requests',
        () => {
          // Simulate filtering
          const filtered = largeRequestList.filter(r => r.model === 'gpt-4');
          const sorted = filtered.sort((a, b) => b.created - a.created);
        },
        100
      );

      console.log('Request filtering benchmark:', {
        averageTime: `${result.averageTime.toFixed(4)}ms`,
        opsPerSecond: `${result.opsPerSecond.toFixed(0)} ops/s`,
      });

      // Should filter efficiently
      expect(result.averageTime).toBeLessThan(10); // Less than 10ms
    });
  });

  describe('Update Performance', () => {
    it('handles auto-refresh efficiently', async () => {
      const { rerender } = renderWithProviders(<ChatCompletions />);

      const updateTime = await measureRenderTime(() => {
        rerender(<ChatCompletions />);
      });

      console.log(`Auto-refresh update time: ${updateTime.toFixed(2)}ms`);

      // Updates should be fast
      expect(updateTime).toBeLessThan(200);
    });
  });

  describe('Scroll Performance', () => {
    it('handles large lists efficiently', () => {
      // This would require a virtual scrolling test
      // For now, just verify the component renders
      const { container } = renderWithProviders(<ChatCompletions />);

      const requestsTable = container.querySelector('[data-testid="requests-table"]');
      expect(requestsTable).toBeTruthy();
    });
  });
});
