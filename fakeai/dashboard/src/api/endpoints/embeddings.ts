/**
 * Embeddings API endpoints
 */

import { apiClient } from '../client';
import type {
  EmbeddingRequest,
  EmbeddingResponse,
  ApiRequestConfig,
} from '../types';

/**
 * Create embeddings for input text
 */
export async function createEmbedding(
  request: EmbeddingRequest,
  config?: ApiRequestConfig
): Promise<EmbeddingResponse> {
  const response = await apiClient.post<EmbeddingResponse>(
    '/v1/embeddings',
    request,
    config
  );
  return response.data;
}

/**
 * Create embeddings with batch processing
 */
export async function createEmbeddingsBatch(
  inputs: string[],
  model: string,
  batchSize: number = 100,
  config?: ApiRequestConfig
): Promise<EmbeddingResponse> {
  const batches: string[][] = [];

  // Split into batches
  for (let i = 0; i < inputs.length; i += batchSize) {
    batches.push(inputs.slice(i, i + batchSize));
  }

  // Process batches in parallel
  const results = await Promise.all(
    batches.map(batch =>
      createEmbedding(
        {
          model,
          input: batch,
        },
        config
      )
    )
  );

  // Merge results
  const allEmbeddings = results.flatMap(result => result.data);
  const totalUsage = results.reduce(
    (acc, result) => ({
      prompt_tokens: acc.prompt_tokens + result.usage.prompt_tokens,
      total_tokens: acc.total_tokens + result.usage.total_tokens,
    }),
    { prompt_tokens: 0, total_tokens: 0 }
  );

  return {
    object: 'list',
    data: allEmbeddings,
    model,
    usage: totalUsage,
  };
}

/**
 * Calculate cosine similarity between two embeddings
 */
export function cosineSimilarity(embedding1: number[], embedding2: number[]): number {
  if (embedding1.length !== embedding2.length) {
    throw new Error('Embeddings must have the same length');
  }

  let dotProduct = 0;
  let norm1 = 0;
  let norm2 = 0;

  for (let i = 0; i < embedding1.length; i++) {
    dotProduct += embedding1[i] * embedding2[i];
    norm1 += embedding1[i] * embedding1[i];
    norm2 += embedding2[i] * embedding2[i];
  }

  return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
}

/**
 * Get available embedding models
 */
export async function getEmbeddingModels(): Promise<
  Array<{ id: string; name: string; dimensions: number; max_input: number }>
> {
  const response = await apiClient.get('/v1/models');
  return response.data.data.filter((model: any) => model.type === 'embedding');
}

/**
 * Estimate embedding cost
 */
export async function estimateEmbeddingCost(
  model: string,
  tokenCount: number
): Promise<{ estimated_cost: number }> {
  const response = await apiClient.post('/v1/embeddings/estimate', {
    model,
    token_count: tokenCount,
  });
  return response.data;
}
