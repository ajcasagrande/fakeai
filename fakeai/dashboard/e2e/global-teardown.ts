/**
 * Global teardown for Playwright tests
 * Runs once after all tests
 */

import { FullConfig } from '@playwright/test';

async function globalTeardown(config: FullConfig) {
  console.log('Starting global teardown...');

  // Optional: Clean up test data, close connections, etc.
  // Example: await cleanupTestDatabase();
  // Example: await closeConnections();

  console.log('Global teardown completed!');
}

export default globalTeardown;
