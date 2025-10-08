/**
 * Images API endpoints
 */

import { apiClient } from '../client';
import type {
  ImageGenerationRequest,
  ImageGenerationResponse,
  ImageEditRequest,
  ImageVariationRequest,
  ApiRequestConfig,
} from '../types';

/**
 * Generate images from text prompt
 */
export async function generateImage(
  request: ImageGenerationRequest,
  config?: ApiRequestConfig
): Promise<ImageGenerationResponse> {
  const response = await apiClient.post<ImageGenerationResponse>(
    '/v1/images/generations',
    request,
    config
  );
  return response.data;
}

/**
 * Edit an existing image with a prompt
 */
export async function editImage(
  request: ImageEditRequest,
  config?: ApiRequestConfig
): Promise<ImageGenerationResponse> {
  const formData = new FormData();
  formData.append('image', request.image);
  formData.append('prompt', request.prompt);

  if (request.mask) {
    formData.append('mask', request.mask);
  }
  if (request.model) {
    formData.append('model', request.model);
  }
  if (request.n) {
    formData.append('n', request.n.toString());
  }
  if (request.size) {
    formData.append('size', request.size);
  }
  if (request.response_format) {
    formData.append('response_format', request.response_format);
  }
  if (request.user) {
    formData.append('user', request.user);
  }

  const response = await apiClient.post<ImageGenerationResponse>(
    '/v1/images/edits',
    formData,
    {
      ...config,
      headers: {
        ...config?.headers,
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
}

/**
 * Create variations of an image
 */
export async function createImageVariation(
  request: ImageVariationRequest,
  config?: ApiRequestConfig
): Promise<ImageGenerationResponse> {
  const formData = new FormData();
  formData.append('image', request.image);

  if (request.model) {
    formData.append('model', request.model);
  }
  if (request.n) {
    formData.append('n', request.n.toString());
  }
  if (request.size) {
    formData.append('size', request.size);
  }
  if (request.response_format) {
    formData.append('response_format', request.response_format);
  }
  if (request.user) {
    formData.append('user', request.user);
  }

  const response = await apiClient.post<ImageGenerationResponse>(
    '/v1/images/variations',
    formData,
    {
      ...config,
      headers: {
        ...config?.headers,
        'Content-Type': 'multipart/form-data',
      },
    }
  );
  return response.data;
}

/**
 * Download image from URL
 */
export async function downloadImage(url: string): Promise<Blob> {
  const response = await apiClient.get(url, {
    responseType: 'blob',
  });
  return response.data;
}

/**
 * Convert base64 image to Blob
 */
export function base64ToBlob(base64: string, mimeType: string = 'image/png'): Blob {
  const byteString = atob(base64);
  const arrayBuffer = new ArrayBuffer(byteString.length);
  const uint8Array = new Uint8Array(arrayBuffer);

  for (let i = 0; i < byteString.length; i++) {
    uint8Array[i] = byteString.charCodeAt(i);
  }

  return new Blob([arrayBuffer], { type: mimeType });
}

/**
 * Estimate image generation cost
 */
export async function estimateImageCost(
  model: string,
  size: string,
  quality: string,
  n: number = 1
): Promise<{ estimated_cost: number }> {
  const response = await apiClient.post('/v1/images/estimate', {
    model,
    size,
    quality,
    n,
  });
  return response.data;
}
