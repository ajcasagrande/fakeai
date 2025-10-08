/**
 * Axios client configuration with interceptors and retry logic
 */

import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { ApiError, ApiErrorResponse } from './errors';
import { getAuthToken, clearAuthToken } from './auth';
import { cache } from './cache';

/**
 * API client configuration options
 */
export interface ApiClientConfig {
  baseURL?: string;
  timeout?: number;
  retryAttempts?: number;
  retryDelay?: number;
  enableCache?: boolean;
}

/**
 * Default configuration
 */
const DEFAULT_CONFIG: Required<ApiClientConfig> = {
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
  enableCache: true,
};

/**
 * Request retry configuration
 */
interface RetryConfig extends AxiosRequestConfig {
  __retryCount?: number;
  __skipRetry?: boolean;
}

/**
 * Create configured axios instance
 */
function createAxiosInstance(config: ApiClientConfig = {}): AxiosInstance {
  const mergedConfig = { ...DEFAULT_CONFIG, ...config };

  const instance = axios.create({
    baseURL: mergedConfig.baseURL,
    timeout: mergedConfig.timeout,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor
  instance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      // Add auth token if available
      const token = getAuthToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      // Add request timestamp for latency tracking
      (config as any).__requestTime = Date.now();

      // Check cache for GET requests
      if (mergedConfig.enableCache && config.method === 'get') {
        const cacheKey = generateCacheKey(config);
        const cachedData = cache.get(cacheKey);
        if (cachedData) {
          // Return cached response (axios will handle this as a resolved promise)
          return Promise.reject({
            __cached: true,
            data: cachedData,
            config,
          });
        }
      }

      return config;
    },
    (error: AxiosError) => {
      return Promise.reject(new ApiError('Request configuration failed', 500, error));
    }
  );

  // Response interceptor
  instance.interceptors.response.use(
    (response: AxiosResponse) => {
      // Calculate request latency
      const requestTime = (response.config as any).__requestTime;
      if (requestTime) {
        const latency = Date.now() - requestTime;
        response.headers['x-response-time'] = latency.toString();
      }

      // Cache successful GET responses
      if (mergedConfig.enableCache && response.config.method === 'get') {
        const cacheKey = generateCacheKey(response.config);
        const cacheDuration = getCacheDuration(response.config.url || '');
        cache.set(cacheKey, response.data, cacheDuration);
      }

      return response;
    },
    async (error: any) => {
      // Handle cached responses
      if (error.__cached) {
        return Promise.resolve({
          data: error.data,
          status: 200,
          statusText: 'OK',
          headers: { 'x-cached': 'true' },
          config: error.config,
        });
      }

      // Handle network errors
      if (!error.response) {
        if (error.code === 'ECONNABORTED') {
          return Promise.reject(new ApiError('Request timeout', 408, error));
        }
        return Promise.reject(new ApiError('Network error', 0, error));
      }

      const axiosError = error as AxiosError<ApiErrorResponse>;
      const config = axiosError.config as RetryConfig;

      // Handle authentication errors
      if (axiosError.response?.status === 401) {
        clearAuthToken();
        return Promise.reject(new ApiError('Unauthorized', 401, axiosError));
      }

      // Retry logic for specific errors
      if (shouldRetry(axiosError) && !config.__skipRetry) {
        const retryCount = config.__retryCount || 0;

        if (retryCount < mergedConfig.retryAttempts) {
          config.__retryCount = retryCount + 1;

          // Exponential backoff
          const delay = mergedConfig.retryDelay * Math.pow(2, retryCount);
          await new Promise(resolve => setTimeout(resolve, delay));

          return instance.request(config);
        }
      }

      // Convert to ApiError
      const apiError = new ApiError(
        axiosError.response?.data?.message || axiosError.message,
        axiosError.response?.status || 500,
        axiosError,
        axiosError.response?.data?.code,
        axiosError.response?.data?.details
      );

      return Promise.reject(apiError);
    }
  );

  return instance;
}

/**
 * Determine if request should be retried
 */
function shouldRetry(error: AxiosError): boolean {
  // Retry on network errors
  if (!error.response) {
    return true;
  }

  // Retry on specific status codes
  const retryableStatuses = [408, 429, 500, 502, 503, 504];
  return retryableStatuses.includes(error.response.status);
}

/**
 * Generate cache key from request config
 */
function generateCacheKey(config: AxiosRequestConfig): string {
  const { url, params } = config;
  const paramString = params ? JSON.stringify(params) : '';
  return `${url}:${paramString}`;
}

/**
 * Get cache duration based on endpoint
 */
function getCacheDuration(url: string): number {
  // Short cache for frequently changing data
  if (url.includes('/metrics') || url.includes('/requests')) {
    return 5000; // 5 seconds
  }

  // Medium cache for model data
  if (url.includes('/models')) {
    return 30000; // 30 seconds
  }

  // Long cache for static data
  if (url.includes('/organization') || url.includes('/costs')) {
    return 300000; // 5 minutes
  }

  // Default cache duration
  return 60000; // 1 minute
}

/**
 * Global API client instance
 */
export const apiClient = createAxiosInstance();

/**
 * Create a new API client with custom configuration
 */
export function createApiClient(config: ApiClientConfig = {}): AxiosInstance {
  return createAxiosInstance(config);
}

/**
 * Update base URL for API client
 */
export function updateBaseURL(baseURL: string): void {
  apiClient.defaults.baseURL = baseURL;
}

/**
 * Clear all cached responses
 */
export function clearCache(): void {
  cache.clear();
}

/**
 * Make a request without retry logic
 */
export function requestWithoutRetry<T = any>(
  config: AxiosRequestConfig
): Promise<AxiosResponse<T>> {
  const configWithSkip: RetryConfig = {
    ...config,
    __skipRetry: true,
  };
  return apiClient.request<T>(configWithSkip);
}
