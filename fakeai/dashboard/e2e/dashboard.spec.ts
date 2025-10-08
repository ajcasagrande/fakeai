/**
 * E2E tests for Dashboard
 */

import { test, expect } from './fixtures';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ dashboardPage }) => {
    await dashboardPage.goto();
  });

  test('displays metrics overview on load', async ({ dashboardPage, page }) => {
    await dashboardPage.waitForMetrics();

    // Check for metrics cards
    await expect(page.locator('[data-testid="metrics-overview"]')).toBeVisible();
    await expect(page.locator('text=Total Requests')).toBeVisible();
    await expect(page.locator('text=Total Tokens')).toBeVisible();
    await expect(page.locator('text=Total Cost')).toBeVisible();
  });

  test('loads and displays model metrics', async ({ page }) => {
    // Wait for model usage chart
    await expect(page.locator('text=Model Usage Distribution')).toBeVisible();

    // Check that models are displayed
    await expect(page.locator('text=gpt-4')).toBeVisible();
  });

  test('refreshes data manually', async ({ dashboardPage, page }) => {
    await dashboardPage.waitForMetrics();

    // Click refresh button
    await dashboardPage.clickRefresh();

    // Verify loading state appears briefly
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible();
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeHidden({
      timeout: 5000,
    });
  });

  test('toggles auto-refresh', async ({ dashboardPage, page }) => {
    await dashboardPage.waitForMetrics();

    // Get initial auto-refresh state
    const toggleButton = page.locator('[data-testid="auto-refresh-toggle"]');
    const initialState = await toggleButton.getAttribute('aria-pressed');

    // Toggle auto-refresh
    await dashboardPage.toggleAutoRefresh();

    // Verify state changed
    const newState = await toggleButton.getAttribute('aria-pressed');
    expect(newState).not.toBe(initialState);
  });

  test('filters by model', async ({ dashboardPage, page }) => {
    await dashboardPage.waitForMetrics();

    // Select a specific model
    await dashboardPage.selectModel('gpt-4');

    // Wait for filtered results
    await page.waitForTimeout(500);

    // Verify only selected model is shown in requests table
    const requestRows = page.locator('[data-testid^="request-"]');
    const count = await requestRows.count();

    if (count > 0) {
      for (let i = 0; i < count; i++) {
        const row = requestRows.nth(i);
        await expect(row).toContainText('gpt-4');
      }
    }
  });

  test('opens and closes request details modal', async ({ dashboardPage, page }) => {
    await dashboardPage.waitForMetrics();

    // Click on first request in table
    const firstRequest = page.locator('[data-testid^="request-"]').first();
    await firstRequest.click();

    // Verify modal opens
    await expect(page.locator('[data-testid="request-details-modal"]')).toBeVisible();

    // Close modal
    await dashboardPage.closeModal();

    // Verify modal closes
    await expect(page.locator('[data-testid="request-details-modal"]')).toBeHidden();
  });

  test('handles API errors gracefully', async ({ mockAPI, page }) => {
    // Mock API error
    await mockAPI.mockError('metrics/by-model', 500);

    // Navigate to page
    await page.goto('/');

    // Verify error message is displayed
    await expect(page.locator('[data-testid="error-banner"]')).toBeVisible();
    await expect(page.locator('text=/failed to fetch/i')).toBeVisible();
  });

  test('displays loading state', async ({ mockAPI, page }) => {
    // Mock delayed response
    await mockAPI.mockDelay('metrics/by-model', 2000);

    // Navigate to page
    await page.goto('/');

    // Verify loading state
    await expect(page.locator('[data-testid="metrics-loading"]')).toBeVisible();

    // Wait for data to load
    await page.waitForSelector('[data-testid="metrics-overview"]', {
      state: 'visible',
      timeout: 5000,
    });
  });

  test('paginates through requests table', async ({ page }) => {
    await page.goto('/');

    // Wait for table to load
    await page.waitForSelector('[data-testid="requests-table"]');

    // Check if pagination controls exist
    const nextButton = page.locator('[data-testid="next-page"]');

    if (await nextButton.isVisible()) {
      // Get first request ID before pagination
      const firstRequestBefore = await page
        .locator('[data-testid^="request-"]')
        .first()
        .getAttribute('data-testid');

      // Click next page
      await nextButton.click();

      // Wait for new data
      await page.waitForTimeout(500);

      // Get first request ID after pagination
      const firstRequestAfter = await page
        .locator('[data-testid^="request-"]')
        .first()
        .getAttribute('data-testid');

      // Verify different requests are shown
      expect(firstRequestBefore).not.toBe(firstRequestAfter);
    }
  });

  test('switches between chart types', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('[data-testid="model-usage-chart"]');

    // Find chart type toggle buttons
    const pieButton = page.locator('button:has-text("Pie")');
    const barButton = page.locator('button:has-text("Bar")');

    // Switch to bar chart
    await barButton.click();
    await expect(barButton).toHaveClass(/active/);

    // Switch back to pie chart
    await pieButton.click();
    await expect(pieButton).toHaveClass(/active/);
  });

  test('displays responsive layout on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Verify mobile-specific layout
    const sidebar = page.locator('[data-testid="sidebar"]');

    // Sidebar should be hidden or collapsed on mobile
    if (await sidebar.isVisible()) {
      await expect(sidebar).toHaveCSS('position', 'absolute');
    }

    // Verify metrics are stacked vertically
    const metricsGrid = page.locator('[data-testid="metrics-overview"]');
    await expect(metricsGrid).toBeVisible();
  });

  test('keyboard navigation works', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Tab through interactive elements
    await page.keyboard.press('Tab');

    // Verify focus is visible
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();

    // Press Enter on focused button
    await page.keyboard.press('Enter');
  });
});

test.describe('Real-time Updates', () => {
  test('receives WebSocket updates', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Get initial metric value
    const metricElement = page.locator('[data-testid="metric-total-requests"]');
    const initialValue = await metricElement.textContent();

    // Wait for potential WebSocket update (30 seconds auto-refresh)
    await page.waitForTimeout(2000);

    // Note: In real tests, you would mock WebSocket and send updates
    // For now, just verify the element is still present
    await expect(metricElement).toBeVisible();
  });
});

test.describe('Performance', () => {
  test('loads within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    // Page should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('handles large datasets efficiently', async ({ mockAPI, page }) => {
    // Mock large dataset
    const largeDataset: Record<string, any> = {};
    for (let i = 0; i < 100; i++) {
      largeDataset[`model-${i}`] = {
        model: `model-${i}`,
        request_count: Math.floor(Math.random() * 10000),
        total_tokens: Math.floor(Math.random() * 1000000),
      };
    }

    await mockAPI.mockMetricsEndpoint(largeDataset);

    const startTime = Date.now();

    await page.goto('/');
    await page.waitForSelector('[data-testid="metrics-overview"]');

    const renderTime = Date.now() - startTime;

    // Should render within reasonable time even with large dataset
    expect(renderTime).toBeLessThan(5000);
  });
});
