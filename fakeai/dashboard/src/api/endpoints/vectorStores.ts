/**
 * Vector Stores API endpoints
 */

import { apiClient } from '../client';
import type {
  VectorStoreRequest,
  VectorStore,
  VectorStoreFile,
  PaginatedResponse,
  PaginationParams,
  ApiRequestConfig,
} from '../types';

/**
 * Create a vector store
 */
export async function createVectorStore(
  request: VectorStoreRequest,
  config?: ApiRequestConfig
): Promise<VectorStore> {
  const response = await apiClient.post<VectorStore>(
    '/v1/vector_stores',
    request,
    config
  );
  return response.data;
}

/**
 * Get vector store by ID
 */
export async function getVectorStore(
  vectorStoreId: string,
  config?: ApiRequestConfig
): Promise<VectorStore> {
  const response = await apiClient.get<VectorStore>(
    `/v1/vector_stores/${vectorStoreId}`,
    config
  );
  return response.data;
}

/**
 * List vector stores
 */
export async function listVectorStores(
  params?: PaginationParams,
  config?: ApiRequestConfig
): Promise<PaginatedResponse<VectorStore>> {
  const response = await apiClient.get<PaginatedResponse<VectorStore>>(
    '/v1/vector_stores',
    {
      ...config,
      params,
    }
  );
  return response.data;
}

/**
 * Update vector store
 */
export async function updateVectorStore(
  vectorStoreId: string,
  updates: Partial<VectorStoreRequest>,
  config?: ApiRequestConfig
): Promise<VectorStore> {
  const response = await apiClient.patch<VectorStore>(
    `/v1/vector_stores/${vectorStoreId}`,
    updates,
    config
  );
  return response.data;
}

/**
 * Delete vector store
 */
export async function deleteVectorStore(
  vectorStoreId: string,
  config?: ApiRequestConfig
): Promise<{ id: string; object: string; deleted: boolean }> {
  const response = await apiClient.delete(
    `/v1/vector_stores/${vectorStoreId}`,
    config
  );
  return response.data;
}

/**
 * Add file to vector store
 */
export async function addFileToVectorStore(
  vectorStoreId: string,
  fileId: string,
  config?: ApiRequestConfig
): Promise<VectorStoreFile> {
  const response = await apiClient.post<VectorStoreFile>(
    `/v1/vector_stores/${vectorStoreId}/files`,
    { file_id: fileId },
    config
  );
  return response.data;
}

/**
 * Get vector store file
 */
export async function getVectorStoreFile(
  vectorStoreId: string,
  fileId: string,
  config?: ApiRequestConfig
): Promise<VectorStoreFile> {
  const response = await apiClient.get<VectorStoreFile>(
    `/v1/vector_stores/${vectorStoreId}/files/${fileId}`,
    config
  );
  return response.data;
}

/**
 * List vector store files
 */
export async function listVectorStoreFiles(
  vectorStoreId: string,
  params?: PaginationParams & { filter?: 'in_progress' | 'completed' | 'failed' | 'cancelled' },
  config?: ApiRequestConfig
): Promise<PaginatedResponse<VectorStoreFile>> {
  const response = await apiClient.get<PaginatedResponse<VectorStoreFile>>(
    `/v1/vector_stores/${vectorStoreId}/files`,
    {
      ...config,
      params,
    }
  );
  return response.data;
}

/**
 * Remove file from vector store
 */
export async function removeFileFromVectorStore(
  vectorStoreId: string,
  fileId: string,
  config?: ApiRequestConfig
): Promise<{ id: string; object: string; deleted: boolean }> {
  const response = await apiClient.delete(
    `/v1/vector_stores/${vectorStoreId}/files/${fileId}`,
    config
  );
  return response.data;
}

/**
 * Poll vector store status until completion
 */
export async function pollVectorStoreStatus(
  vectorStoreId: string,
  options: {
    interval?: number;
    maxAttempts?: number;
    onProgress?: (store: VectorStore) => void;
  } = {}
): Promise<VectorStore> {
  const { interval = 3000, maxAttempts = 100, onProgress } = options;

  let attempts = 0;

  while (attempts < maxAttempts) {
    const store = await getVectorStore(vectorStoreId);

    if (onProgress) {
      onProgress(store);
    }

    // Check if all files are processed
    if (store.status === 'completed' || store.file_counts.in_progress === 0) {
      return store;
    }

    attempts++;
    await new Promise(resolve => setTimeout(resolve, interval));
  }

  throw new Error(`Vector store polling timeout after ${maxAttempts} attempts`);
}

/**
 * Get vector store progress percentage
 */
export function getVectorStoreProgress(store: VectorStore): number {
  const { in_progress, completed, failed, cancelled, total } = store.file_counts;

  if (total === 0) return 0;

  const processed = completed + failed + cancelled;
  return (processed / total) * 100;
}

/**
 * Check if vector store is ready
 */
export function isVectorStoreReady(store: VectorStore): boolean {
  return store.status === 'completed' && store.file_counts.in_progress === 0;
}
