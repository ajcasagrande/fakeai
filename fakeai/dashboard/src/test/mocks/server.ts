/**
 * MSW server setup for testing
 * Configures mock service worker for API request interception
 */

import { setupServer } from 'msw/node';
import { handlers } from './handlers';

/**
 * Create MSW server instance with default handlers
 */
export const server = setupServer(...handlers);

/**
 * Setup server for tests
 */
export function setupServer() {
  return server;
}

/**
 * Reset handlers to defaults
 */
export function resetHandlers() {
  server.resetHandlers();
}

/**
 * Use custom handlers for specific tests
 */
export function useHandlers(...customHandlers: Parameters<typeof server.use>) {
  server.use(...customHandlers);
}

export default server;
