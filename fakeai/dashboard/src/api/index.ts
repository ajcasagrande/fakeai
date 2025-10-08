/**
 * FakeAI Dashboard API Service Layer
 *
 * Comprehensive API client with:
 * - Axios-based HTTP client with interceptors
 * - Request retry logic with exponential backoff
 * - Response caching with TTL
 * - TypeScript type safety throughout
 * - Error handling with typed errors
 * - Auth token management
 * - React Query hooks for data fetching
 *
 * @example
 * ```typescript
 * import { apiClient, useChatCompletion, getSystemMetrics } from '@/api';
 *
 * // Use hooks in components
 * const { mutate, isLoading } = useChatCompletion();
 *
 * // Or call directly
 * const metrics = await getSystemMetrics();
 * ```
 */

// Core client and configuration
export { apiClient, createApiClient, updateBaseURL, clearCache } from './client';
export {
  initializeConfig,
  getConfig,
  updateConfig,
  resetConfig,
  isDevelopment,
  isProduction,
  getBaseURL,
  getEnvironment,
  logConfig,
} from './config';
export type { ApiConfig } from './config';

// Authentication
export {
  getAuthToken,
  setAuthToken,
  clearAuthToken,
  isAuthenticated,
  getTokenPayload,
  isTokenExpired,
  getTokenTTL,
} from './auth';

// Error handling
export {
  ApiError,
  ValidationError,
  RateLimitError,
  ApiErrorType,
  isApiError,
  isValidationError,
  isRateLimitError,
  handleApiError,
  logApiError,
} from './errors';
export type { ApiErrorResponse } from './errors';

// Caching
export { cache, createCache, cached } from './cache';

// Type definitions
export type {
  // Common types
  ModelId,
  ProjectId,
  UserId,
  OrganizationId,
  PaginationParams,
  PaginatedResponse,
  ApiResponse,
  ApiRequestConfig,

  // Chat types
  ChatMessage,
  ChatCompletionRequest,
  ChatCompletionResponse,
  ChatCompletionStreamChunk,

  // Embeddings types
  EmbeddingRequest,
  EmbeddingResponse,

  // Images types
  ImageGenerationRequest,
  ImageGenerationResponse,
  ImageEditRequest,
  ImageVariationRequest,

  // Audio types
  AudioTranscriptionRequest,
  AudioTranscriptionResponse,
  AudioTranslationRequest,
  AudioSpeechRequest,

  // Batches types
  BatchRequest,
  Batch,

  // Fine-tuning types
  FineTuningJobRequest,
  FineTuningJob,
  FineTuningEvent,

  // Vector Stores types
  VectorStoreRequest,
  VectorStore,
  VectorStoreFile,

  // Assistants types
  AssistantRequest,
  Assistant,

  // Organization types
  OrganizationUsageRequest,
  OrganizationUsageResponse,
  UsageResultItem,
  UsageBucket,

  // Metrics types
  ModelMetrics,
  SystemMetrics,
  TimeSeriesMetric,
  MetricsQuery,

  // Costs types
  CostBreakdown,
  CostEstimate,
  BudgetAlert,
} from './types';

// API endpoints
export * from './endpoints';

// React Query hooks
export * from './hooks';

// Utility functions
export * from './utils';

/**
 * API version
 */
export const API_VERSION = 'v1';

/**
 * Default configuration values
 */
export const API_CONFIG = {
  DEFAULT_TIMEOUT: 30000,
  DEFAULT_RETRY_ATTEMPTS: 3,
  DEFAULT_RETRY_DELAY: 1000,
  DEFAULT_CACHE_TTL: 60000,
} as const;
