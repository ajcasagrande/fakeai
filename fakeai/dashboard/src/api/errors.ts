/**
 * Typed error handling for API operations
 */

/**
 * Standard API error response structure
 */
export interface ApiErrorResponse {
  message: string;
  code?: string;
  details?: Record<string, any>;
  status?: number;
}

/**
 * Error types for different API failures
 */
export enum ApiErrorType {
  NETWORK_ERROR = 'NETWORK_ERROR',
  TIMEOUT_ERROR = 'TIMEOUT_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  AUTHENTICATION_ERROR = 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR = 'AUTHORIZATION_ERROR',
  NOT_FOUND_ERROR = 'NOT_FOUND_ERROR',
  RATE_LIMIT_ERROR = 'RATE_LIMIT_ERROR',
  SERVER_ERROR = 'SERVER_ERROR',
  UNKNOWN_ERROR = 'UNKNOWN_ERROR',
}

/**
 * Custom API Error class with enhanced context
 */
export class ApiError extends Error {
  public readonly type: ApiErrorType;
  public readonly status: number;
  public readonly code?: string;
  public readonly details?: Record<string, any>;
  public readonly timestamp: number;
  public readonly originalError?: Error;

  constructor(
    message: string,
    status: number,
    originalError?: Error,
    code?: string,
    details?: Record<string, any>
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
    this.timestamp = Date.now();
    this.originalError = originalError;
    this.type = this.determineErrorType(status);

    // Maintains proper stack trace for where error was thrown
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiError);
    }
  }

  /**
   * Determine error type from status code
   */
  private determineErrorType(status: number): ApiErrorType {
    if (status === 0) {
      return ApiErrorType.NETWORK_ERROR;
    }
    if (status === 400) {
      return ApiErrorType.VALIDATION_ERROR;
    }
    if (status === 401) {
      return ApiErrorType.AUTHENTICATION_ERROR;
    }
    if (status === 403) {
      return ApiErrorType.AUTHORIZATION_ERROR;
    }
    if (status === 404) {
      return ApiErrorType.NOT_FOUND_ERROR;
    }
    if (status === 408) {
      return ApiErrorType.TIMEOUT_ERROR;
    }
    if (status === 429) {
      return ApiErrorType.RATE_LIMIT_ERROR;
    }
    if (status >= 500) {
      return ApiErrorType.SERVER_ERROR;
    }
    return ApiErrorType.UNKNOWN_ERROR;
  }

  /**
   * Check if error is a specific type
   */
  public is(type: ApiErrorType): boolean {
    return this.type === type;
  }

  /**
   * Check if error is retryable
   */
  public isRetryable(): boolean {
    return [
      ApiErrorType.NETWORK_ERROR,
      ApiErrorType.TIMEOUT_ERROR,
      ApiErrorType.RATE_LIMIT_ERROR,
      ApiErrorType.SERVER_ERROR,
    ].includes(this.type);
  }

  /**
   * Get user-friendly error message
   */
  public getUserMessage(): string {
    switch (this.type) {
      case ApiErrorType.NETWORK_ERROR:
        return 'Unable to connect to the server. Please check your internet connection.';
      case ApiErrorType.TIMEOUT_ERROR:
        return 'Request timed out. Please try again.';
      case ApiErrorType.AUTHENTICATION_ERROR:
        return 'Authentication failed. Please log in again.';
      case ApiErrorType.AUTHORIZATION_ERROR:
        return 'You do not have permission to access this resource.';
      case ApiErrorType.NOT_FOUND_ERROR:
        return 'The requested resource was not found.';
      case ApiErrorType.RATE_LIMIT_ERROR:
        return 'Too many requests. Please try again later.';
      case ApiErrorType.VALIDATION_ERROR:
        return this.message || 'Invalid request data.';
      case ApiErrorType.SERVER_ERROR:
        return 'Server error occurred. Please try again later.';
      default:
        return this.message || 'An unexpected error occurred.';
    }
  }

  /**
   * Convert error to JSON for logging
   */
  public toJSON(): Record<string, any> {
    return {
      name: this.name,
      type: this.type,
      message: this.message,
      status: this.status,
      code: this.code,
      details: this.details,
      timestamp: this.timestamp,
      stack: this.stack,
    };
  }
}

/**
 * Validation error for invalid request data
 */
export class ValidationError extends ApiError {
  public readonly fieldErrors: Record<string, string[]>;

  constructor(
    message: string,
    fieldErrors: Record<string, string[]> = {},
    details?: Record<string, any>
  ) {
    super(message, 400, undefined, 'VALIDATION_ERROR', details);
    this.name = 'ValidationError';
    this.fieldErrors = fieldErrors;
  }

  /**
   * Get errors for a specific field
   */
  public getFieldErrors(field: string): string[] {
    return this.fieldErrors[field] || [];
  }

  /**
   * Check if a field has errors
   */
  public hasFieldError(field: string): boolean {
    return field in this.fieldErrors;
  }
}

/**
 * Rate limit error with retry information
 */
export class RateLimitError extends ApiError {
  public readonly retryAfter?: number;
  public readonly limit?: number;
  public readonly remaining?: number;

  constructor(
    message: string,
    retryAfter?: number,
    limit?: number,
    remaining?: number
  ) {
    super(message, 429, undefined, 'RATE_LIMIT_ERROR', {
      retryAfter,
      limit,
      remaining,
    });
    this.name = 'RateLimitError';
    this.retryAfter = retryAfter;
    this.limit = limit;
    this.remaining = remaining;
  }

  /**
   * Get time until retry in milliseconds
   */
  public getRetryAfterMs(): number {
    return (this.retryAfter || 60) * 1000;
  }
}

/**
 * Check if error is an ApiError
 */
export function isApiError(error: any): error is ApiError {
  return error instanceof ApiError;
}

/**
 * Check if error is a ValidationError
 */
export function isValidationError(error: any): error is ValidationError {
  return error instanceof ValidationError;
}

/**
 * Check if error is a RateLimitError
 */
export function isRateLimitError(error: any): error is RateLimitError {
  return error instanceof RateLimitError;
}

/**
 * Handle and format API errors
 */
export function handleApiError(error: any): ApiError {
  if (isApiError(error)) {
    return error;
  }

  // Convert unknown errors to ApiError
  if (error instanceof Error) {
    return new ApiError(error.message, 500, error);
  }

  // Handle non-Error objects
  return new ApiError(
    typeof error === 'string' ? error : 'An unknown error occurred',
    500
  );
}

/**
 * Log API error with context
 */
export function logApiError(error: ApiError, context?: Record<string, any>): void {
  const errorLog = {
    ...error.toJSON(),
    context,
  };

  if (error.status >= 500) {
    console.error('[API Error]', errorLog);
  } else if (error.status >= 400) {
    console.warn('[API Warning]', errorLog);
  } else {
    console.info('[API Info]', errorLog);
  }
}
