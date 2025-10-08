/**
 * Vector Stores Types
 * Based on /v1/vector_stores API endpoints
 */

export type VectorStoreStatus = 'in_progress' | 'completed' | 'failed' | 'expired';

export type FileStatus = 'in_progress' | 'completed' | 'failed' | 'cancelled';

export interface VectorStoreFileCounts {
  in_progress: number;
  completed: number;
  failed: number;
  cancelled: number;
  total: number;
}

export interface VectorStoreExpirationPolicy {
  anchor: 'last_active_at';
  days: number;
}

export interface VectorStore {
  id: string;
  object: 'vector_store';
  created_at: number;
  name: string;
  usage_bytes: number;
  file_counts: VectorStoreFileCounts;
  status: VectorStoreStatus;
  expires_at?: number;
  expires_after?: VectorStoreExpirationPolicy;
  last_active_at?: number;
  metadata?: Record<string, any>;
}

export interface VectorStoreListResponse {
  object: 'list';
  data: VectorStore[];
  first_id?: string;
  last_id?: string;
  has_more: boolean;
}

export interface CreateVectorStoreRequest {
  name?: string;
  file_ids?: string[];
  expires_after?: VectorStoreExpirationPolicy;
  metadata?: Record<string, any>;
}

export interface ModifyVectorStoreRequest {
  name?: string;
  expires_after?: VectorStoreExpirationPolicy;
  metadata?: Record<string, any>;
}

export interface VectorStoreFile {
  id: string;
  object: 'vector_store.file';
  usage_bytes: number;
  created_at: number;
  vector_store_id: string;
  status: FileStatus;
  last_error?: {
    code: string;
    message: string;
  };
}

export interface VectorStoreFileListResponse {
  object: 'list';
  data: VectorStoreFile[];
  first_id?: string;
  last_id?: string;
  has_more: boolean;
}

export interface VectorStoreFileBatch {
  id: string;
  object: 'vector_store.files_batch';
  created_at: number;
  vector_store_id: string;
  status: 'in_progress' | 'completed' | 'cancelled' | 'failed';
  file_counts: VectorStoreFileCounts;
}

export interface CreateVectorStoreFileBatchRequest {
  file_ids: string[];
}

export interface UploadFileRequest {
  file: File;
  purpose: 'assistants';
}

export interface UploadedFile {
  id: string;
  object: 'file';
  bytes: number;
  created_at: number;
  filename: string;
  purpose: string;
}

export interface FileListResponse {
  object: 'list';
  data: UploadedFile[];
  has_more: boolean;
}

export interface VectorStoreStats {
  totalStores: number;
  totalFiles: number;
  totalStorageBytes: number;
  avgFilesPerStore: number;
  storesByStatus: Record<VectorStoreStatus, number>;
}

export interface VectorSearchMetrics {
  avgQueryLatencyMs: number;
  queriesPerSecond: number;
  successRate: number;
  totalQueries: number;
  cacheHitRate: number;
}

export interface StorageUsageData {
  vectorStoreId: string;
  name: string;
  usageBytes: number;
  fileCount: number;
  lastActive?: number;
}

export interface VectorStoreFilterOptions {
  status?: VectorStoreStatus[];
  searchQuery?: string;
  sortBy?: 'created_at' | 'name' | 'usage_bytes' | 'file_count';
  sortOrder?: 'asc' | 'desc';
}
