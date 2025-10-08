/**
 * Audio API endpoints
 */

import { apiClient } from '../client';
import type {
  AudioTranscriptionRequest,
  AudioTranscriptionResponse,
  AudioTranslationRequest,
  AudioSpeechRequest,
  ApiRequestConfig,
} from '../types';

/**
 * Transcribe audio to text
 */
export async function createTranscription(
  request: AudioTranscriptionRequest,
  config?: ApiRequestConfig
): Promise<AudioTranscriptionResponse> {
  const formData = new FormData();
  formData.append('file', request.file);
  formData.append('model', request.model);

  if (request.language) {
    formData.append('language', request.language);
  }
  if (request.prompt) {
    formData.append('prompt', request.prompt);
  }
  if (request.response_format) {
    formData.append('response_format', request.response_format);
  }
  if (request.temperature !== undefined) {
    formData.append('temperature', request.temperature.toString());
  }

  const response = await apiClient.post<AudioTranscriptionResponse>(
    '/v1/audio/transcriptions',
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
 * Translate audio to English text
 */
export async function createTranslation(
  request: AudioTranslationRequest,
  config?: ApiRequestConfig
): Promise<AudioTranscriptionResponse> {
  const formData = new FormData();
  formData.append('file', request.file);
  formData.append('model', request.model);

  if (request.prompt) {
    formData.append('prompt', request.prompt);
  }
  if (request.response_format) {
    formData.append('response_format', request.response_format);
  }
  if (request.temperature !== undefined) {
    formData.append('temperature', request.temperature.toString());
  }

  const response = await apiClient.post<AudioTranscriptionResponse>(
    '/v1/audio/translations',
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
 * Generate speech from text
 */
export async function createSpeech(
  request: AudioSpeechRequest,
  config?: ApiRequestConfig
): Promise<Blob> {
  const response = await apiClient.post<Blob>(
    '/v1/audio/speech',
    request,
    {
      ...config,
      responseType: 'blob',
    }
  );
  return response.data;
}

/**
 * Create speech and get audio URL
 */
export async function createSpeechURL(
  request: AudioSpeechRequest,
  config?: ApiRequestConfig
): Promise<string> {
  const audioBlob = await createSpeech(request, config);
  return URL.createObjectURL(audioBlob);
}

/**
 * Download audio file from URL
 */
export async function downloadAudio(url: string): Promise<Blob> {
  const response = await apiClient.get(url, {
    responseType: 'blob',
  });
  return response.data;
}

/**
 * Validate audio file format
 */
export function validateAudioFile(file: File): { valid: boolean; error?: string } {
  const supportedFormats = ['audio/mp3', 'audio/mp4', 'audio/mpeg', 'audio/mpga', 'audio/m4a', 'audio/wav', 'audio/webm'];
  const maxSize = 25 * 1024 * 1024; // 25MB

  if (!supportedFormats.includes(file.type)) {
    return {
      valid: false,
      error: `Unsupported audio format: ${file.type}. Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm`,
    };
  }

  if (file.size > maxSize) {
    return {
      valid: false,
      error: `File size exceeds maximum of 25MB. Current size: ${(file.size / 1024 / 1024).toFixed(2)}MB`,
    };
  }

  return { valid: true };
}

/**
 * Estimate transcription cost
 */
export async function estimateTranscriptionCost(
  durationSeconds: number,
  model: string
): Promise<{ estimated_cost: number }> {
  const response = await apiClient.post('/v1/audio/transcriptions/estimate', {
    duration_seconds: durationSeconds,
    model,
  });
  return response.data;
}
