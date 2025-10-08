/**
 * Global setup for Playwright tests
 * Runs once before all tests
 */

import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('Starting global setup...');

  // Launch browser for setup tasks
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Wait for dev server to be ready
  const baseURL = config.use?.baseURL || 'http://localhost:5173';
  console.log(`Waiting for dev server at ${baseURL}...`);

  let retries = 30;
  while (retries > 0) {
    try {
      await page.goto(baseURL, { timeout: 2000 });
      console.log('Dev server is ready!');
      break;
    } catch (error) {
      retries--;
      if (retries === 0) {
        throw new Error(`Dev server not ready at ${baseURL}`);
      }
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  // Optional: Set up test data, authentication, etc.
  // Example: await setupTestDatabase();
  // Example: await seedTestData();

  await browser.close();
  console.log('Global setup completed!');
}

export default globalSetup;
