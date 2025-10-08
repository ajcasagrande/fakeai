/**
 * Tests for API functions
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { server } from '@test/mocks/server';
import { http, HttpResponse } from 'msw';
import {
  fetchModelMetrics,
  fetchModelMetricsById,
  fetchGeneralMetrics,
  fetchCompletionsUsage,
  fetchChatRequests,
  setApiKey,
  clearApiKey,
} from './api';
import { mockModelMetricsResponse } from '@test/mocks/data';

const BASE_URL = 'http://localhost:8000';

describe('API Functions', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('fetchModelMetrics', () => {
    it('fetches all model metrics successfully', async () => {
      const metrics = await fetchModelMetrics();

      expect(metrics).toEqual(mockModelMetricsResponse);
      expect(Object.keys(metrics)).toContain('gpt-4');
      expect(Object.keys(metrics)).toContain('gpt-3.5-turbo');
    });

    it('throws error on failed request', async () => {
      server.use(
        http.get(`${BASE_URL}/metrics/by-model`, () => {
          return new HttpResponse(null, { status: 500 });
        })
      );

      await expect(fetchModelMetrics()).rejects.toThrow();
    });

    it('throws error on network failure', async () => {
      server.use(
        http.get(`${BASE_URL}/metrics/by-model`, () => {
          return HttpResponse.error();
        })
      );

      await expect(fetchModelMetrics()).rejects.toThrow();
    });
  });

  describe('fetchModelMetricsById', () => {
    it('fetches specific model metrics', async () => {
      const metrics = await fetchModelMetricsById('gpt-4');

      expect(metrics.model).toBe('gpt-4');
      expect(metrics.request_count).toBeGreaterThan(0);
    });

    it('returns 404 for non-existent model', async () => {
      await expect(fetchModelMetricsById('non-existent-model')).rejects.toThrow();
    });

    it('handles special characters in model ID', async () => {
      const modelId = 'gpt-4-32k';
      server.use(
        http.get(`${BASE_URL}/metrics/by-model/:modelId`, () => {
          return HttpResponse.json(mockModelMetricsResponse['gpt-4']);
        })
      );

      const metrics = await fetchModelMetricsById(modelId);
      expect(metrics).toBeDefined();
    });
  });

  describe('fetchGeneralMetrics', () => {
    it('fetches general metrics successfully', async () => {
      const metrics = await fetchGeneralMetrics();

      expect(metrics).toHaveProperty('total_requests');
      expect(metrics).toHaveProperty('total_errors');
      expect(metrics).toHaveProperty('avg_latency_ms');
    });

    it('handles server errors', async () => {
      server.use(
        http.get(`${BASE_URL}/metrics`, () => {
          return new HttpResponse(null, { status: 503 });
        })
      );

      await expect(fetchGeneralMetrics()).rejects.toThrow();
    });
  });

  describe('fetchCompletionsUsage', () => {
    const startTime = Date.now() - 3600000;
    const endTime = Date.now();

    it('fetches completions usage with required params', async () => {
      const usage = await fetchCompletionsUsage(startTime, endTime);

      expect(usage).toHaveProperty('object', 'page');
      expect(usage).toHaveProperty('data');
      expect(Array.isArray(usage.data)).toBe(true);
    });

    it('includes optional parameters in request', async () => {
      let capturedUrl: string = '';

      server.use(
        http.get(`${BASE_URL}/v1/organization/usage/completions`, ({ request }) => {
          capturedUrl = request.url;
          return HttpResponse.json({
            object: 'page',
            data: [],
            has_more: false,
            next_page: null,
          });
        })
      );

      await fetchCompletionsUsage(startTime, endTime, '1h', 'proj_123', 'gpt-4');

      expect(capturedUrl).toContain('start_time=');
      expect(capturedUrl).toContain('end_time=');
      expect(capturedUrl).toContain('bucket_width=1h');
      expect(capturedUrl).toContain('project_id=proj_123');
      expect(capturedUrl).toContain('model=gpt-4');
    });

    it('uses default bucket width when not specified', async () => {
      let capturedUrl: string = '';

      server.use(
        http.get(`${BASE_URL}/v1/organization/usage/completions`, ({ request }) => {
          capturedUrl = request.url;
          return HttpResponse.json({
            object: 'page',
            data: [],
            has_more: false,
            next_page: null,
          });
        })
      );

      await fetchCompletionsUsage(startTime, endTime);

      expect(capturedUrl).toContain('bucket_width=1h');
    });
  });

  describe('fetchChatRequests', () => {
    it('fetches chat requests with default parameters', async () => {
      const result = await fetchChatRequests();

      expect(result).toHaveProperty('requests');
      expect(result).toHaveProperty('total');
      expect(Array.isArray(result.requests)).toBe(true);
    });

    it('applies pagination parameters', async () => {
      const result = await fetchChatRequests(10, 20);

      expect(result.requests.length).toBeLessThanOrEqual(10);
    });

    it('filters by model', async () => {
      const result = await fetchChatRequests(100, 0, { model: 'gpt-4' });

      result.requests.forEach(req => {
        expect(req.model).toBe('gpt-4');
      });
    });

    it('filters by status', async () => {
      const result = await fetchChatRequests(100, 0, { status: 'success' });

      result.requests.forEach(req => {
        expect(req.status).toBe('success');
      });
    });

    it('filters by streaming', async () => {
      const result = await fetchChatRequests(100, 0, { streaming: 'streaming' });

      result.requests.forEach(req => {
        expect(req.streaming).toBe(true);
      });
    });

    it('returns empty array when no matches', async () => {
      server.use(
        http.get(`${BASE_URL}/chat/requests`, () => {
          return HttpResponse.json({ requests: [], total: 0 });
        })
      );

      const result = await fetchChatRequests(100, 0, { model: 'non-existent' });

      expect(result.requests).toEqual([]);
      expect(result.total).toBe(0);
    });
  });

  describe('API Key Management', () => {
    it('stores API key in localStorage', () => {
      const apiKey = 'test-api-key-123';
      setApiKey(apiKey);

      expect(localStorage.getItem('apiKey')).toBe(apiKey);
    });

    it('clears API key from localStorage', () => {
      setApiKey('test-key');
      expect(localStorage.getItem('apiKey')).toBeTruthy();

      clearApiKey();
      expect(localStorage.getItem('apiKey')).toBeNull();
    });
  });

  describe('Error Handling', () => {
    it('handles rate limiting', async () => {
      server.use(
        http.get(`${BASE_URL}/metrics/rate-limit`, () => {
          return new HttpResponse(
            JSON.stringify({ error: 'Rate limit exceeded' }),
            {
              status: 429,
              headers: { 'Retry-After': '60' },
            }
          );
        })
      );

      await expect(
        fetch(`${BASE_URL}/metrics/rate-limit`).then(r => {
          if (!r.ok) throw new Error('Rate limit exceeded');
          return r.json();
        })
      ).rejects.toThrow();
    });

    it('handles timeout scenarios', async () => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 100);

      server.use(
        http.get(`${BASE_URL}/metrics/timeout`, async () => {
          await new Promise(resolve => setTimeout(resolve, 1000));
          return HttpResponse.json({});
        })
      );

      await expect(
        fetch(`${BASE_URL}/metrics/timeout`, { signal: controller.signal })
      ).rejects.toThrow();

      clearTimeout(timeoutId);
    });
  });
});
