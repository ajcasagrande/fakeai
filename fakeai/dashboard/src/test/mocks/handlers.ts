/**
 * MSW (Mock Service Worker) request handlers
 * Provides mock API responses for testing
 */

import { http, HttpResponse } from 'msw';
import {
  mockModelMetricsResponse,
  mockChatRequests,
  mockCompletionsUsageResponse,
  generateMockChatRequest,
} from './data';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Request handlers for API endpoints
 */
export const handlers = [
  // GET /metrics/by-model - Get all model metrics
  http.get(`${BASE_URL}/metrics/by-model`, () => {
    return HttpResponse.json(mockModelMetricsResponse);
  }),

  // GET /metrics/by-model/:modelId - Get specific model metrics
  http.get(`${BASE_URL}/metrics/by-model/:modelId`, ({ params }) => {
    const { modelId } = params;
    const stats = mockModelMetricsResponse[modelId as string];

    if (!stats) {
      return new HttpResponse(null, { status: 404 });
    }

    return HttpResponse.json(stats);
  }),

  // GET /metrics - Get general metrics
  http.get(`${BASE_URL}/metrics`, () => {
    return HttpResponse.json({
      total_requests: 6982,
      total_errors: 40,
      avg_latency_ms: 872,
      total_cost: 92.57,
      uptime_seconds: 86400,
    });
  }),

  // GET /v1/organization/usage/completions - Get completions usage
  http.get(`${BASE_URL}/v1/organization/usage/completions`, ({ request }) => {
    const url = new URL(request.url);
    const startTime = url.searchParams.get('start_time');
    const endTime = url.searchParams.get('end_time');
    const model = url.searchParams.get('model');

    // Filter by model if specified
    let response = mockCompletionsUsageResponse;
    if (model) {
      // In real implementation, filter by model
    }

    return HttpResponse.json(response);
  }),

  // Mock endpoint for chat requests (not part of real API)
  http.get(`${BASE_URL}/chat/requests`, ({ request }) => {
    const url = new URL(request.url);
    const limit = parseInt(url.searchParams.get('limit') || '20');
    const offset = parseInt(url.searchParams.get('offset') || '0');
    const model = url.searchParams.get('model');
    const status = url.searchParams.get('status');

    let filteredRequests = [...mockChatRequests];

    // Apply filters
    if (model) {
      filteredRequests = filteredRequests.filter(r => r.model === model);
    }
    if (status && status !== 'all') {
      filteredRequests = filteredRequests.filter(r => r.status === status);
    }

    const paginatedRequests = filteredRequests.slice(offset, offset + limit);

    return HttpResponse.json({
      requests: paginatedRequests,
      total: filteredRequests.length,
    });
  }),

  // Error simulation handlers
  http.get(`${BASE_URL}/metrics/error`, () => {
    return new HttpResponse(null, { status: 500, statusText: 'Internal Server Error' });
  }),

  http.get(`${BASE_URL}/metrics/timeout`, () => {
    return new Promise(() => {
      // Never resolves - simulates timeout
    });
  }),

  http.get(`${BASE_URL}/metrics/not-found`, () => {
    return new HttpResponse(null, { status: 404, statusText: 'Not Found' });
  }),

  // Rate limit simulation
  http.get(`${BASE_URL}/metrics/rate-limit`, () => {
    return new HttpResponse(
      JSON.stringify({ error: 'Rate limit exceeded' }),
      {
        status: 429,
        headers: {
          'Retry-After': '60',
        },
      }
    );
  }),
];

/**
 * Error handlers for testing error scenarios
 */
export const errorHandlers = [
  http.get(`${BASE_URL}/metrics/by-model`, () => {
    return new HttpResponse(null, { status: 500 });
  }),
];

/**
 * Delay handlers for testing loading states
 */
export const delayedHandlers = [
  http.get(`${BASE_URL}/metrics/by-model`, async () => {
    await new Promise(resolve => setTimeout(resolve, 2000));
    return HttpResponse.json(mockModelMetricsResponse);
  }),
];

/**
 * Empty data handlers for testing empty states
 */
export const emptyHandlers = [
  http.get(`${BASE_URL}/metrics/by-model`, () => {
    return HttpResponse.json({});
  }),

  http.get(`${BASE_URL}/chat/requests`, () => {
    return HttpResponse.json({
      requests: [],
      total: 0,
    });
  }),
];
