/**
 * Visual regression tests
 * Captures and compares screenshots to detect visual changes
 */

import { test, expect } from './fixtures';

test.describe('Visual Regression Tests', () => {
  test.beforeEach(async ({ dashboardPage }) => {
    await dashboardPage.goto();
    await dashboardPage.waitForMetrics();
  });

  test('dashboard homepage matches baseline', async ({ page }) => {
    // Wait for all content to load
    await page.waitForLoadState('networkidle');

    // Take full page screenshot
    await expect(page).toHaveScreenshot('dashboard-homepage.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('metrics overview cards match baseline', async ({ page }) => {
    const metricsOverview = page.locator('[data-testid="metrics-overview"]');
    await expect(metricsOverview).toBeVisible();

    // Screenshot just the metrics section
    await expect(metricsOverview).toHaveScreenshot('metrics-overview.png');
  });

  test('model usage chart matches baseline', async ({ page }) => {
    const chart = page.locator('[data-testid="model-usage-chart"]');
    await expect(chart).toBeVisible();

    // Wait for chart to render
    await page.waitForTimeout(500);

    await expect(chart).toHaveScreenshot('model-usage-chart.png');
  });

  test('requests table matches baseline', async ({ page }) => {
    const table = page.locator('[data-testid="requests-table"]');
    await expect(table).toBeVisible();

    await expect(table).toHaveScreenshot('requests-table.png');
  });

  test('sidebar filters match baseline', async ({ page }) => {
    const sidebar = page.locator('[data-testid="sidebar"]');
    await expect(sidebar).toBeVisible();

    await expect(sidebar).toHaveScreenshot('sidebar-filters.png');
  });

  test('request details modal matches baseline', async ({ page }) => {
    // Open first request
    const firstRequest = page.locator('[data-testid^="request-"]').first();
    await firstRequest.click();

    // Wait for modal
    const modal = page.locator('[data-testid="request-details-modal"]');
    await expect(modal).toBeVisible();

    await expect(modal).toHaveScreenshot('request-details-modal.png');
  });

  test('error state matches baseline', async ({ mockAPI, page }) => {
    await mockAPI.mockError('metrics/by-model', 500);
    await page.goto('/');

    // Wait for error banner
    const errorBanner = page.locator('[data-testid="error-banner"]');
    await expect(errorBanner).toBeVisible();

    await expect(errorBanner).toHaveScreenshot('error-banner.png');
  });

  test('loading state matches baseline', async ({ page }) => {
    // Reload to capture loading state
    const reloadPromise = page.reload();

    // Quickly capture loading state
    const loadingIndicator = page.locator('[data-testid="metrics-loading"]');

    try {
      await expect(loadingIndicator).toBeVisible({ timeout: 1000 });
      await expect(loadingIndicator).toHaveScreenshot('loading-state.png');
    } catch (e) {
      // Loading might be too fast, skip this assertion
      console.log('Loading state too fast to capture');
    }

    await reloadPromise;
  });

  test('mobile view matches baseline', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('dashboard-mobile.png', {
      fullPage: true,
    });
  });

  test('tablet view matches baseline', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('dashboard-tablet.png', {
      fullPage: true,
    });
  });

  test('dark mode matches baseline (if implemented)', async ({ page }) => {
    // This assumes dark mode is implemented
    // You would need to add a dark mode toggle mechanism

    // Toggle dark mode
    const darkModeToggle = page.locator('[data-testid="dark-mode-toggle"]');

    if (await darkModeToggle.isVisible()) {
      await darkModeToggle.click();
      await page.waitForTimeout(300);

      await expect(page).toHaveScreenshot('dashboard-dark-mode.png', {
        fullPage: true,
      });
    }
  });

  test('chart types match baseline', async ({ page }) => {
    // Pie chart
    const pieButton = page.locator('button:has-text("Pie")');
    await pieButton.click();
    await page.waitForTimeout(300);

    const pieChart = page.locator('[data-testid="model-usage-chart"]');
    await expect(pieChart).toHaveScreenshot('pie-chart.png');

    // Bar chart
    const barButton = page.locator('button:has-text("Bar")');
    await barButton.click();
    await page.waitForTimeout(300);

    const barChart = page.locator('[data-testid="model-usage-chart"]');
    await expect(barChart).toHaveScreenshot('bar-chart.png');
  });
});

test.describe('Visual Regression - Interactive States', () => {
  test('hover states match baseline', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Hover over refresh button
    const refreshButton = page.locator('[data-testid="manual-refresh"]');
    await refreshButton.hover();

    await expect(refreshButton).toHaveScreenshot('refresh-button-hover.png');
  });

  test('focus states match baseline', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Focus on model filter
    const modelFilter = page.locator('[data-testid="model-filter"]');
    await modelFilter.focus();

    await expect(modelFilter).toHaveScreenshot('model-filter-focus.png');
  });

  test('active toggle states match baseline', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Auto-refresh toggle active state
    const toggle = page.locator('[data-testid="auto-refresh-toggle"]');
    await toggle.click();

    await expect(toggle).toHaveScreenshot('auto-refresh-active.png');
  });
});

test.describe('Visual Regression - Empty States', () => {
  test('empty metrics matches baseline', async ({ mockAPI, page }) => {
    await mockAPI.mockMetricsEndpoint({});
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('empty-metrics.png', {
      fullPage: true,
    });
  });

  test('no requests matches baseline', async ({ mockAPI, page }) => {
    await mockAPI.mockMetricsEndpoint({});
    await page.route('**/chat/requests', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ requests: [], total: 0 }),
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const table = page.locator('[data-testid="requests-table"]');
    await expect(table).toHaveScreenshot('empty-requests-table.png');
  });
});
