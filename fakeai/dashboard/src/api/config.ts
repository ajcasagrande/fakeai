/**
 * API Configuration and Environment Management
 */

/**
 * API configuration interface
 */
export interface ApiConfig {
  baseURL: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
  enableCache: boolean;
  enableLogging: boolean;
  environment: 'development' | 'staging' | 'production';
}

/**
 * Default API configuration
 */
const DEFAULT_CONFIG: ApiConfig = {
  baseURL: 'http://localhost:8000',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
  enableCache: true,
  enableLogging: true,
  environment: 'development',
};

/**
 * Environment-specific configurations
 */
const ENV_CONFIGS: Record<string, Partial<ApiConfig>> = {
  development: {
    baseURL: 'http://localhost:8000',
    enableLogging: true,
    enableCache: true,
  },
  staging: {
    baseURL: 'https://staging-api.fakeai.com',
    enableLogging: true,
    enableCache: true,
  },
  production: {
    baseURL: 'https://api.fakeai.com',
    enableLogging: false,
    enableCache: true,
    retryAttempts: 5,
    timeout: 60000,
  },
};

/**
 * Current API configuration
 */
let currentConfig: ApiConfig = { ...DEFAULT_CONFIG };

/**
 * Initialize API configuration from environment variables
 */
export function initializeConfig(): ApiConfig {
  const env = (import.meta.env.MODE as ApiConfig['environment']) || 'development';
  const envConfig = ENV_CONFIGS[env] || {};

  currentConfig = {
    ...DEFAULT_CONFIG,
    ...envConfig,
    baseURL: import.meta.env.VITE_API_URL || envConfig.baseURL || DEFAULT_CONFIG.baseURL,
    environment: env,
  };

  return currentConfig;
}

/**
 * Get current API configuration
 */
export function getConfig(): ApiConfig {
  return { ...currentConfig };
}

/**
 * Update API configuration
 */
export function updateConfig(updates: Partial<ApiConfig>): ApiConfig {
  currentConfig = {
    ...currentConfig,
    ...updates,
  };
  return currentConfig;
}

/**
 * Reset configuration to defaults
 */
export function resetConfig(): ApiConfig {
  currentConfig = { ...DEFAULT_CONFIG };
  return currentConfig;
}

/**
 * Check if running in development mode
 */
export function isDevelopment(): boolean {
  return currentConfig.environment === 'development';
}

/**
 * Check if running in production mode
 */
export function isProduction(): boolean {
  return currentConfig.environment === 'production';
}

/**
 * Get API base URL
 */
export function getBaseURL(): string {
  return currentConfig.baseURL;
}

/**
 * Get environment name
 */
export function getEnvironment(): string {
  return currentConfig.environment;
}

/**
 * Log API configuration (development only)
 */
export function logConfig(): void {
  if (isDevelopment()) {
    console.group('API Configuration');
    console.table(currentConfig);
    console.groupEnd();
  }
}

// Initialize configuration on module load
initializeConfig();
