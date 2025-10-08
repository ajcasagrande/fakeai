/**
 * Chat Completions API endpoints
 */

import { apiClient } from '../client';
import type {
  ChatCompletionRequest,
  ChatCompletionResponse,
  ChatCompletionStreamChunk,
  ApiRequestConfig,
} from '../types';

/**
 * Create a chat completion
 */
export async function createChatCompletion(
  request: ChatCompletionRequest,
  config?: ApiRequestConfig
): Promise<ChatCompletionResponse> {
  const response = await apiClient.post<ChatCompletionResponse>(
    '/v1/chat/completions',
    request,
    config
  );
  return response.data;
}

/**
 * Create a streaming chat completion
 */
export async function* streamChatCompletion(
  request: ChatCompletionRequest,
  config?: ApiRequestConfig
): AsyncGenerator<ChatCompletionStreamChunk, void, undefined> {
  const streamRequest = { ...request, stream: true };

  const response = await apiClient.post('/v1/chat/completions', streamRequest, {
    ...config,
    responseType: 'stream',
    headers: {
      ...config?.headers,
      Accept: 'text/event-stream',
    },
  });

  const stream = response.data;

  // Process server-sent events
  let buffer = '';

  for await (const chunk of stream) {
    buffer += chunk.toString();

    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      const trimmed = line.trim();

      if (!trimmed || trimmed === 'data: [DONE]') {
        continue;
      }

      if (trimmed.startsWith('data: ')) {
        try {
          const jsonStr = trimmed.slice(6);
          const data = JSON.parse(jsonStr) as ChatCompletionStreamChunk;
          yield data;
        } catch (e) {
          console.error('Failed to parse SSE data:', e);
        }
      }
    }
  }
}

/**
 * Create chat completion with abort support
 */
export async function createChatCompletionWithAbort(
  request: ChatCompletionRequest,
  signal?: AbortSignal,
  config?: ApiRequestConfig
): Promise<ChatCompletionResponse> {
  const response = await apiClient.post<ChatCompletionResponse>(
    '/v1/chat/completions',
    request,
    {
      ...config,
      signal,
    }
  );
  return response.data;
}

/**
 * Estimate chat completion cost
 */
export async function estimateChatCompletionCost(
  request: Omit<ChatCompletionRequest, 'messages'> & { estimated_tokens: number }
): Promise<{ estimated_cost: number; breakdown: Record<string, number> }> {
  const response = await apiClient.post('/v1/chat/completions/estimate', request);
  return response.data;
}

/**
 * Get available chat models
 */
export async function getChatModels(): Promise<Array<{ id: string; name: string; context_length: number }>> {
  const response = await apiClient.get('/v1/models');
  return response.data.data.filter((model: any) => model.type === 'chat');
}
