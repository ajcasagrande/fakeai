/**
 * Playwright test fixtures
 * Provides reusable test setup and utilities
 */

import { test as base, Page } from '@playwright/test';

/**
 * Custom fixtures for dashboard tests
 */
type DashboardFixtures = {
  dashboardPage: DashboardPage;
  mockAPI: MockAPIHelper;
};

/**
 * Dashboard page object
 */
class DashboardPage {
  constructor(public readonly page: Page) {}

  async goto() {
    await this.page.goto('/');
    await this.page.waitForLoadState('networkidle');
  }

  async waitForMetrics() {
    await this.page.waitForSelector('[data-testid="metrics-overview"]', {
      state: 'visible',
    });
  }

  async getMetricValue(metricName: string) {
    const selector = `[data-testid="metric-${metricName}"]`;
    return await this.page.textContent(selector);
  }

  async selectModel(modelName: string) {
    await this.page.selectOption('[data-testid="model-filter"]', modelName);
  }

  async toggleAutoRefresh() {
    await this.page.click('[data-testid="auto-refresh-toggle"]');
  }

  async clickRefresh() {
    await this.page.click('[data-testid="manual-refresh"]');
  }

  async openRequestDetails(requestId: string) {
    await this.page.click(`[data-testid="request-${requestId}"]`);
  }

  async closeModal() {
    await this.page.click('[data-testid="close-modal"]');
  }
}

/**
 * Mock API helper
 */
class MockAPIHelper {
  constructor(public readonly page: Page) {}

  async mockMetricsEndpoint(data: any) {
    await this.page.route('**/metrics/by-model', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(data),
      });
    });
  }

  async mockError(endpoint: string, status: number = 500) {
    await this.page.route(`**/${endpoint}`, route => {
      route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal Server Error' }),
      });
    });
  }

  async mockDelay(endpoint: string, delayMs: number) {
    await this.page.route(`**/${endpoint}`, async route => {
      await new Promise(resolve => setTimeout(resolve, delayMs));
      route.continue();
    });
  }

  async clearMocks() {
    await this.page.unrouteAll();
  }
}

/**
 * Extend base test with custom fixtures
 */
export const test = base.extend<DashboardFixtures>({
  dashboardPage: async ({ page }, use) => {
    const dashboardPage = new DashboardPage(page);
    await use(dashboardPage);
  },

  mockAPI: async ({ page }, use) => {
    const mockAPI = new MockAPIHelper(page);
    await use(mockAPI);
  },
});

export { expect } from '@playwright/test';
