/**
 * React Query hooks for Chat Completions API
 */

import React from 'react';
import { useMutation, useQuery, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import {
  createChatCompletion,
  createChatCompletionWithAbort,
  estimateChatCompletionCost,
  getChatModels,
} from '../endpoints/chat';
import type {
  ChatCompletionRequest,
  ChatCompletionResponse,
  ApiRequestConfig,
} from '../types';
import { handleApiError } from '../errors';

/**
 * Hook to create chat completion
 */
export function useChatCompletion(
  options?: UseMutationOptions<ChatCompletionResponse, Error, ChatCompletionRequest>
) {
  return useMutation({
    mutationFn: (request: ChatCompletionRequest) => createChatCompletion(request),
    onError: (error) => {
      handleApiError(error);
    },
    ...options,
  });
}

/**
 * Hook to create chat completion with abort controller
 */
export function useChatCompletionWithAbort(
  options?: UseMutationOptions<
    ChatCompletionResponse,
    Error,
    { request: ChatCompletionRequest; signal?: AbortSignal }
  >
) {
  return useMutation({
    mutationFn: ({ request, signal }) => createChatCompletionWithAbort(request, signal),
    onError: (error) => {
      handleApiError(error);
    },
    ...options,
  });
}

/**
 * Hook to estimate chat completion cost
 */
export function useEstimateChatCost(
  options?: UseMutationOptions<
    { estimated_cost: number; breakdown: Record<string, number> },
    Error,
    Omit<ChatCompletionRequest, 'messages'> & { estimated_tokens: number }
  >
) {
  return useMutation({
    mutationFn: (request) => estimateChatCompletionCost(request),
    ...options,
  });
}

/**
 * Hook to get available chat models
 */
export function useChatModels(
  options?: UseQueryOptions<Array<{ id: string; name: string; context_length: number }>, Error>
) {
  return useQuery({
    queryKey: ['chat', 'models'],
    queryFn: () => getChatModels(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    ...options,
  });
}

/**
 * Hook for streaming chat completion
 */
export function useStreamingChat() {
  const [isStreaming, setIsStreaming] = React.useState(false);
  const [streamedContent, setStreamedContent] = React.useState('');
  const [error, setError] = React.useState<Error | null>(null);
  const abortControllerRef = React.useRef<AbortController | null>(null);

  const startStream = React.useCallback(
    async (request: ChatCompletionRequest, onChunk?: (content: string) => void) => {
      setIsStreaming(true);
      setStreamedContent('');
      setError(null);

      abortControllerRef.current = new AbortController();

      try {
        const { streamChatCompletion } = await import('../endpoints/chat');
        const stream = streamChatCompletion(request, {
          signal: abortControllerRef.current.signal,
        });

        let fullContent = '';

        for await (const chunk of stream) {
          const content = chunk.choices[0]?.delta?.content || '';
          fullContent += content;
          setStreamedContent(fullContent);

          if (onChunk) {
            onChunk(content);
          }
        }
      } catch (err) {
        const apiError = handleApiError(err);
        setError(apiError);
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    []
  );

  const stopStream = React.useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsStreaming(false);
    }
  }, []);

  const reset = React.useCallback(() => {
    setStreamedContent('');
    setError(null);
  }, []);

  return {
    isStreaming,
    streamedContent,
    error,
    startStream,
    stopStream,
    reset,
  };
}
