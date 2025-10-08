import axios, { AxiosInstance } from 'axios';
import type { ChatCompletionRequest, ChatCompletionResponse } from './types';

class ChatAPI {
  private client: AxiosInstance;

  constructor(baseURL: string = '/v1') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async createCompletion(request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    const response = await this.client.post<ChatCompletionResponse>(
      '/chat/completions',
      request
    );
    return response.data;
  }

  async *createStreamingCompletion(request: ChatCompletionRequest): AsyncGenerator<string | { reasoning_content?: string; content?: string }> {
    const response = await fetch('/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ...request, stream: true }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is null');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine || trimmedLine === 'data: [DONE]') continue;

          if (trimmedLine.startsWith('data: ')) {
            try {
              const jsonStr = trimmedLine.slice(6);
              const data = JSON.parse(jsonStr);
              const delta = data.choices?.[0]?.delta;

              // Check for reasoning content (for reasoning models)
              if (delta?.reasoning_content) {
                yield { reasoning_content: delta.reasoning_content };
              }

              // Check for regular content
              if (delta?.content) {
                // Preserve newlines in content
                const content = delta.content;
                console.log('Chunk received:', JSON.stringify(content).substring(0, 100));
                yield content;
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  createEventSource(request: ChatCompletionRequest): EventSource {
    const params = new URLSearchParams({
      model: request.model,
      temperature: request.temperature?.toString() || '0.7',
      max_tokens: request.max_tokens?.toString() || '2048',
      messages: JSON.stringify(request.messages),
    });
    return new EventSource(`/v1/chat/completions?${params.toString()}`);
  }
}

export const chatAPI = new ChatAPI();
export default chatAPI;
