/**
 * Fine-tuning API endpoints
 */

import { apiClient } from '../client';
import type {
  FineTuningJobRequest,
  FineTuningJob,
  FineTuningEvent,
  PaginatedResponse,
  PaginationParams,
  ApiRequestConfig,
} from '../types';

/**
 * Create a fine-tuning job
 */
export async function createFineTuningJob(
  request: FineTuningJobRequest,
  config?: ApiRequestConfig
): Promise<FineTuningJob> {
  const response = await apiClient.post<FineTuningJob>(
    '/v1/fine_tuning/jobs',
    request,
    config
  );
  return response.data;
}

/**
 * Get fine-tuning job by ID
 */
export async function getFineTuningJob(
  jobId: string,
  config?: ApiRequestConfig
): Promise<FineTuningJob> {
  const response = await apiClient.get<FineTuningJob>(
    `/v1/fine_tuning/jobs/${jobId}`,
    config
  );
  return response.data;
}

/**
 * List fine-tuning jobs
 */
export async function listFineTuningJobs(
  params?: PaginationParams,
  config?: ApiRequestConfig
): Promise<PaginatedResponse<FineTuningJob>> {
  const response = await apiClient.get<PaginatedResponse<FineTuningJob>>(
    '/v1/fine_tuning/jobs',
    {
      ...config,
      params,
    }
  );
  return response.data;
}

/**
 * Cancel a fine-tuning job
 */
export async function cancelFineTuningJob(
  jobId: string,
  config?: ApiRequestConfig
): Promise<FineTuningJob> {
  const response = await apiClient.post<FineTuningJob>(
    `/v1/fine_tuning/jobs/${jobId}/cancel`,
    {},
    config
  );
  return response.data;
}

/**
 * List fine-tuning events
 */
export async function listFineTuningEvents(
  jobId: string,
  params?: PaginationParams,
  config?: ApiRequestConfig
): Promise<PaginatedResponse<FineTuningEvent>> {
  const response = await apiClient.get<PaginatedResponse<FineTuningEvent>>(
    `/v1/fine_tuning/jobs/${jobId}/events`,
    {
      ...config,
      params,
    }
  );
  return response.data;
}

/**
 * Poll fine-tuning job status until completion
 */
export async function pollFineTuningJob(
  jobId: string,
  options: {
    interval?: number;
    maxAttempts?: number;
    onProgress?: (job: FineTuningJob) => void;
  } = {}
): Promise<FineTuningJob> {
  const { interval = 10000, maxAttempts = 360, onProgress } = options;

  let attempts = 0;

  while (attempts < maxAttempts) {
    const job = await getFineTuningJob(jobId);

    if (onProgress) {
      onProgress(job);
    }

    // Check if job is in terminal state
    if (['succeeded', 'failed', 'cancelled'].includes(job.status)) {
      return job;
    }

    attempts++;
    await new Promise(resolve => setTimeout(resolve, interval));
  }

  throw new Error(`Fine-tuning job polling timeout after ${maxAttempts} attempts`);
}

/**
 * Stream fine-tuning events
 */
export async function* streamFineTuningEvents(
  jobId: string,
  options: {
    interval?: number;
    includeHistorical?: boolean;
  } = {}
): AsyncGenerator<FineTuningEvent, void, undefined> {
  const { interval = 5000, includeHistorical = true } = options;
  const seenEventIds = new Set<string>();

  // Fetch historical events first
  if (includeHistorical) {
    const events = await listFineTuningEvents(jobId);
    for (const event of events.data) {
      seenEventIds.add(event.id);
      yield event;
    }
  }

  // Poll for new events
  let job = await getFineTuningJob(jobId);

  while (!['succeeded', 'failed', 'cancelled'].includes(job.status)) {
    await new Promise(resolve => setTimeout(resolve, interval));

    const events = await listFineTuningEvents(jobId);

    for (const event of events.data) {
      if (!seenEventIds.has(event.id)) {
        seenEventIds.add(event.id);
        yield event;
      }
    }

    job = await getFineTuningJob(jobId);
  }
}

/**
 * Get fine-tuning job progress percentage
 */
export function getFineTuningProgress(job: FineTuningJob): number {
  // Approximate progress based on status
  const progressMap: Record<FineTuningJob['status'], number> = {
    validating_files: 10,
    queued: 20,
    running: 50,
    succeeded: 100,
    failed: 0,
    cancelled: 0,
  };

  return progressMap[job.status] || 0;
}

/**
 * Check if job is in terminal state
 */
export function isFineTuningComplete(job: FineTuningJob): boolean {
  return ['succeeded', 'failed', 'cancelled'].includes(job.status);
}

/**
 * Get job status display text
 */
export function getFineTuningStatusText(status: FineTuningJob['status']): string {
  const statusMap: Record<FineTuningJob['status'], string> = {
    validating_files: 'Validating Files',
    queued: 'Queued',
    running: 'Running',
    succeeded: 'Succeeded',
    failed: 'Failed',
    cancelled: 'Cancelled',
  };
  return statusMap[status] || status;
}
