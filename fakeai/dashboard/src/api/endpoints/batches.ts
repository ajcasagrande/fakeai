/**
 * Batches API endpoints
 */

import { apiClient } from '../client';
import type {
  BatchRequest,
  Batch,
  PaginatedResponse,
  PaginationParams,
  ApiRequestConfig,
} from '../types';

/**
 * Create a new batch
 */
export async function createBatch(
  request: BatchRequest,
  config?: ApiRequestConfig
): Promise<Batch> {
  const response = await apiClient.post<Batch>('/v1/batches', request, config);
  return response.data;
}

/**
 * Get batch by ID
 */
export async function getBatch(
  batchId: string,
  config?: ApiRequestConfig
): Promise<Batch> {
  const response = await apiClient.get<Batch>(`/v1/batches/${batchId}`, config);
  return response.data;
}

/**
 * List batches with pagination
 */
export async function listBatches(
  params?: PaginationParams,
  config?: ApiRequestConfig
): Promise<PaginatedResponse<Batch>> {
  const response = await apiClient.get<PaginatedResponse<Batch>>('/v1/batches', {
    ...config,
    params,
  });
  return response.data;
}

/**
 * Cancel a batch
 */
export async function cancelBatch(
  batchId: string,
  config?: ApiRequestConfig
): Promise<Batch> {
  const response = await apiClient.post<Batch>(
    `/v1/batches/${batchId}/cancel`,
    {},
    config
  );
  return response.data;
}

/**
 * Poll batch status until completion
 */
export async function pollBatchStatus(
  batchId: string,
  options: {
    interval?: number;
    maxAttempts?: number;
    onProgress?: (batch: Batch) => void;
  } = {}
): Promise<Batch> {
  const { interval = 5000, maxAttempts = 120, onProgress } = options;

  let attempts = 0;

  while (attempts < maxAttempts) {
    const batch = await getBatch(batchId);

    if (onProgress) {
      onProgress(batch);
    }

    // Check if batch is in terminal state
    if (['completed', 'failed', 'expired', 'cancelled'].includes(batch.status)) {
      return batch;
    }

    attempts++;
    await new Promise(resolve => setTimeout(resolve, interval));
  }

  throw new Error(`Batch polling timeout after ${maxAttempts} attempts`);
}

/**
 * Get batch progress percentage
 */
export function getBatchProgress(batch: Batch): number {
  const { total, completed, failed } = batch.request_counts;
  if (total === 0) return 0;
  return ((completed + failed) / total) * 100;
}

/**
 * Check if batch is in terminal state
 */
export function isBatchComplete(batch: Batch): boolean {
  return ['completed', 'failed', 'expired', 'cancelled'].includes(batch.status);
}

/**
 * Get batch status display text
 */
export function getBatchStatusText(status: Batch['status']): string {
  const statusMap: Record<Batch['status'], string> = {
    validating: 'Validating',
    failed: 'Failed',
    in_progress: 'In Progress',
    finalizing: 'Finalizing',
    completed: 'Completed',
    expired: 'Expired',
    cancelling: 'Cancelling',
    cancelled: 'Cancelled',
  };
  return statusMap[status] || status;
}
