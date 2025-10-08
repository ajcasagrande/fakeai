/**
 * Admin Service
 * API service for admin dashboard configuration and management
 */

import axios, { AxiosInstance } from 'axios';
import {
  AdminConfig,
  AdminMetrics,
  KVCacheConfig,
  DynamoConfig,
  TokenGenerationConfig,
  GPUConfig,
  ModelIntegrationsConfig,
} from '../pages/Admin/types';

class AdminService {
  private client: AxiosInstance;

  constructor(baseURL: string = '/admin') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests if available
    this.client.interceptors.request.use((config) => {
      const session = localStorage.getItem('fakeai_admin_session');
      if (session) {
        try {
          const { session_token } = JSON.parse(session);
          if (session_token) {
            config.headers.Authorization = `Bearer ${session_token}`;
          }
        } catch (e) {
          console.error('Failed to parse admin session:', e);
        }
      }
      return config;
    });
  }

  // Get full admin configuration
  async getConfig(): Promise<AdminConfig> {
    const response = await this.client.get<AdminConfig>('/config');
    return response.data;
  }

  // Get current metrics
  async getMetrics(): Promise<AdminMetrics> {
    const response = await this.client.get<AdminMetrics>('/metrics');
    return response.data;
  }

  // Update KV Cache configuration
  async updateKVCacheConfig(config: KVCacheConfig): Promise<void> {
    await this.client.post('/config/kv-cache', config);
  }

  // Update Dynamo configuration
  async updateDynamoConfig(config: DynamoConfig): Promise<void> {
    await this.client.post('/config/dynamo', config);
  }

  // Update Token Generation configuration
  async updateTokenConfig(config: TokenGenerationConfig): Promise<void> {
    await this.client.post('/config/token-generation', config);
  }

  // Update GPU configuration
  async updateGPUConfig(config: GPUConfig): Promise<void> {
    await this.client.post('/config/gpu', config);
  }

  // Update Model Integrations configuration
  async updateModelIntegrations(config: ModelIntegrationsConfig): Promise<void> {
    await this.client.post('/config/model-integrations', config);
  }

  // Update full configuration at once
  async updateFullConfig(config: AdminConfig): Promise<void> {
    await this.client.post('/config', config);
  }

  // Reset configuration to defaults
  async resetConfig(): Promise<AdminConfig> {
    const response = await this.client.post<AdminConfig>('/config/reset');
    return response.data;
  }

  // Verify admin session
  async verifySession(): Promise<boolean> {
    try {
      await this.client.get('/verify');
      return true;
    } catch {
      return false;
    }
  }

  // Export configuration
  async exportConfig(): Promise<Blob> {
    const response = await this.client.get('/config/export', {
      responseType: 'blob',
    });
    return response.data;
  }

  // Import configuration
  async importConfig(file: File): Promise<AdminConfig> {
    const formData = new FormData();
    formData.append('config', file);

    const response = await this.client.post<AdminConfig>('/config/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
}

export const adminService = new AdminService();
export default adminService;
