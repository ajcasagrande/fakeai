/**
 * Assistants API endpoints
 */

import { apiClient } from '../client';
import type {
  AssistantRequest,
  Assistant,
  PaginatedResponse,
  PaginationParams,
  ApiRequestConfig,
} from '../types';

/**
 * Create an assistant
 */
export async function createAssistant(
  request: AssistantRequest,
  config?: ApiRequestConfig
): Promise<Assistant> {
  const response = await apiClient.post<Assistant>('/v1/assistants', request, config);
  return response.data;
}

/**
 * Get assistant by ID
 */
export async function getAssistant(
  assistantId: string,
  config?: ApiRequestConfig
): Promise<Assistant> {
  const response = await apiClient.get<Assistant>(
    `/v1/assistants/${assistantId}`,
    config
  );
  return response.data;
}

/**
 * List assistants
 */
export async function listAssistants(
  params?: PaginationParams & { order?: 'asc' | 'desc' },
  config?: ApiRequestConfig
): Promise<PaginatedResponse<Assistant>> {
  const response = await apiClient.get<PaginatedResponse<Assistant>>('/v1/assistants', {
    ...config,
    params,
  });
  return response.data;
}

/**
 * Update assistant
 */
export async function updateAssistant(
  assistantId: string,
  updates: Partial<AssistantRequest>,
  config?: ApiRequestConfig
): Promise<Assistant> {
  const response = await apiClient.patch<Assistant>(
    `/v1/assistants/${assistantId}`,
    updates,
    config
  );
  return response.data;
}

/**
 * Delete assistant
 */
export async function deleteAssistant(
  assistantId: string,
  config?: ApiRequestConfig
): Promise<{ id: string; object: string; deleted: boolean }> {
  const response = await apiClient.delete(`/v1/assistants/${assistantId}`, config);
  return response.data;
}

/**
 * Clone an assistant
 */
export async function cloneAssistant(
  assistantId: string,
  overrides?: Partial<AssistantRequest>,
  config?: ApiRequestConfig
): Promise<Assistant> {
  const original = await getAssistant(assistantId);

  const cloneRequest: AssistantRequest = {
    model: original.model,
    name: overrides?.name || `${original.name} (Copy)`,
    description: overrides?.description || original.description || undefined,
    instructions: overrides?.instructions || original.instructions || undefined,
    tools: overrides?.tools || original.tools || undefined,
    tool_resources: overrides?.tool_resources || original.tool_resources,
    metadata: overrides?.metadata || { ...original.metadata, cloned_from: assistantId },
    temperature: overrides?.temperature ?? original.temperature,
    top_p: overrides?.top_p ?? original.top_p,
    response_format: overrides?.response_format ?? original.response_format,
  };

  return createAssistant(cloneRequest, config);
}

/**
 * Search assistants by name
 */
export async function searchAssistants(
  query: string,
  config?: ApiRequestConfig
): Promise<Assistant[]> {
  const response = await listAssistants({ limit: 100 }, config);

  // Filter by name (case-insensitive)
  const lowerQuery = query.toLowerCase();
  return response.data.filter(assistant =>
    assistant.name?.toLowerCase().includes(lowerQuery)
  );
}

/**
 * Get assistants by model
 */
export async function getAssistantsByModel(
  model: string,
  config?: ApiRequestConfig
): Promise<Assistant[]> {
  const response = await listAssistants({ limit: 100 }, config);
  return response.data.filter(assistant => assistant.model === model);
}

/**
 * Validate assistant configuration
 */
export function validateAssistantRequest(
  request: AssistantRequest
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!request.model) {
    errors.push('Model is required');
  }

  if (request.name && request.name.length > 256) {
    errors.push('Name must be 256 characters or less');
  }

  if (request.description && request.description.length > 512) {
    errors.push('Description must be 512 characters or less');
  }

  if (request.instructions && request.instructions.length > 32768) {
    errors.push('Instructions must be 32,768 characters or less');
  }

  if (request.tools && request.tools.length > 128) {
    errors.push('Maximum 128 tools allowed');
  }

  if (request.temperature !== undefined && (request.temperature < 0 || request.temperature > 2)) {
    errors.push('Temperature must be between 0 and 2');
  }

  if (request.top_p !== undefined && (request.top_p < 0 || request.top_p > 1)) {
    errors.push('Top P must be between 0 and 1');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}
