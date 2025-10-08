/**
 * TypeScript type definitions for all API endpoints
 */

/**
 * Common types
 */
export type ModelId = string;
export type ProjectId = string;
export type UserId = string;
export type OrganizationId = string;

/**
 * Pagination types
 */
export interface PaginationParams {
  limit?: number;
  offset?: number;
  after?: string;
  before?: string;
}

export interface PaginatedResponse<T> {
  object: 'list';
  data: T[];
  has_more: boolean;
  first_id?: string;
  last_id?: string;
}

/**
 * Chat Completions types
 */
export interface ChatMessage {
  role: 'system' | 'user' | 'assistant' | 'function';
  content: string;
  name?: string;
  function_call?: {
    name: string;
    arguments: string;
  };
}

export interface ChatCompletionRequest {
  model: ModelId;
  messages: ChatMessage[];
  temperature?: number;
  top_p?: number;
  n?: number;
  stream?: boolean;
  stop?: string | string[];
  max_tokens?: number;
  presence_penalty?: number;
  frequency_penalty?: number;
  logit_bias?: Record<string, number>;
  user?: string;
}

export interface ChatCompletionResponse {
  id: string;
  object: 'chat.completion';
  created: number;
  model: ModelId;
  choices: Array<{
    index: number;
    message: ChatMessage;
    finish_reason: 'stop' | 'length' | 'function_call' | 'content_filter' | null;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface ChatCompletionStreamChunk {
  id: string;
  object: 'chat.completion.chunk';
  created: number;
  model: ModelId;
  choices: Array<{
    index: number;
    delta: Partial<ChatMessage>;
    finish_reason: 'stop' | 'length' | 'function_call' | 'content_filter' | null;
  }>;
}

/**
 * Embeddings types
 */
export interface EmbeddingRequest {
  model: ModelId;
  input: string | string[];
  user?: string;
  encoding_format?: 'float' | 'base64';
}

export interface EmbeddingResponse {
  object: 'list';
  data: Array<{
    object: 'embedding';
    embedding: number[];
    index: number;
  }>;
  model: ModelId;
  usage: {
    prompt_tokens: number;
    total_tokens: number;
  };
}

/**
 * Images types
 */
export interface ImageGenerationRequest {
  prompt: string;
  model?: ModelId;
  n?: number;
  size?: '256x256' | '512x512' | '1024x1024' | '1792x1024' | '1024x1792';
  quality?: 'standard' | 'hd';
  response_format?: 'url' | 'b64_json';
  style?: 'vivid' | 'natural';
  user?: string;
}

export interface ImageGenerationResponse {
  created: number;
  data: Array<{
    url?: string;
    b64_json?: string;
    revised_prompt?: string;
  }>;
}

export interface ImageEditRequest {
  image: File | Blob;
  prompt: string;
  mask?: File | Blob;
  model?: ModelId;
  n?: number;
  size?: '256x256' | '512x512' | '1024x1024';
  response_format?: 'url' | 'b64_json';
  user?: string;
}

export interface ImageVariationRequest {
  image: File | Blob;
  model?: ModelId;
  n?: number;
  size?: '256x256' | '512x512' | '1024x1024';
  response_format?: 'url' | 'b64_json';
  user?: string;
}

/**
 * Audio types
 */
export interface AudioTranscriptionRequest {
  file: File | Blob;
  model: ModelId;
  language?: string;
  prompt?: string;
  response_format?: 'json' | 'text' | 'srt' | 'verbose_json' | 'vtt';
  temperature?: number;
}

export interface AudioTranscriptionResponse {
  text: string;
  language?: string;
  duration?: number;
  segments?: Array<{
    id: number;
    seek: number;
    start: number;
    end: number;
    text: string;
    tokens: number[];
    temperature: number;
    avg_logprob: number;
    compression_ratio: number;
    no_speech_prob: number;
  }>;
}

export interface AudioTranslationRequest {
  file: File | Blob;
  model: ModelId;
  prompt?: string;
  response_format?: 'json' | 'text' | 'srt' | 'verbose_json' | 'vtt';
  temperature?: number;
}

export interface AudioSpeechRequest {
  model: ModelId;
  input: string;
  voice: 'alloy' | 'echo' | 'fable' | 'onyx' | 'nova' | 'shimmer';
  response_format?: 'mp3' | 'opus' | 'aac' | 'flac';
  speed?: number;
}

/**
 * Batches types
 */
export interface BatchRequest {
  input_file_id: string;
  endpoint: '/v1/chat/completions' | '/v1/embeddings';
  completion_window: '24h';
  metadata?: Record<string, string>;
}

export interface Batch {
  id: string;
  object: 'batch';
  endpoint: string;
  errors?: {
    object: string;
    data: Array<{
      code: string;
      message: string;
      param: string | null;
      line: number | null;
    }>;
  };
  input_file_id: string;
  completion_window: string;
  status: 'validating' | 'failed' | 'in_progress' | 'finalizing' | 'completed' | 'expired' | 'cancelling' | 'cancelled';
  output_file_id?: string;
  error_file_id?: string;
  created_at: number;
  in_progress_at?: number;
  expires_at?: number;
  finalizing_at?: number;
  completed_at?: number;
  failed_at?: number;
  expired_at?: number;
  cancelling_at?: number;
  cancelled_at?: number;
  request_counts: {
    total: number;
    completed: number;
    failed: number;
  };
  metadata?: Record<string, string>;
}

/**
 * Fine-tuning types
 */
export interface FineTuningJobRequest {
  model: ModelId;
  training_file: string;
  validation_file?: string;
  hyperparameters?: {
    n_epochs?: number;
    batch_size?: number;
    learning_rate_multiplier?: number;
  };
  suffix?: string;
  integrations?: Array<{
    type: 'wandb';
    wandb: {
      project: string;
      name?: string;
      entity?: string;
      tags?: string[];
    };
  }>;
}

export interface FineTuningJob {
  id: string;
  object: 'fine_tuning.job';
  created_at: number;
  error?: {
    code: string;
    message: string;
    param: string | null;
  };
  fine_tuned_model: string | null;
  finished_at: number | null;
  hyperparameters: {
    n_epochs: number;
    batch_size: number;
    learning_rate_multiplier: number;
  };
  model: ModelId;
  organization_id: OrganizationId;
  result_files: string[];
  status: 'validating_files' | 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled';
  trained_tokens: number | null;
  training_file: string;
  validation_file: string | null;
  integrations?: any[];
}

export interface FineTuningEvent {
  object: 'fine_tuning.job.event';
  id: string;
  created_at: number;
  level: 'info' | 'warning' | 'error';
  message: string;
  type: string;
}

/**
 * Vector Stores types
 */
export interface VectorStoreRequest {
  name?: string;
  file_ids?: string[];
  metadata?: Record<string, string>;
  expires_after?: {
    anchor: 'last_active_at';
    days: number;
  };
}

export interface VectorStore {
  id: string;
  object: 'vector_store';
  created_at: number;
  name: string;
  usage_bytes: number;
  file_counts: {
    in_progress: number;
    completed: number;
    failed: number;
    cancelled: number;
    total: number;
  };
  status: 'expired' | 'in_progress' | 'completed';
  expires_after?: {
    anchor: 'last_active_at';
    days: number;
  };
  expires_at?: number;
  last_active_at: number;
  metadata: Record<string, string>;
}

export interface VectorStoreFile {
  id: string;
  object: 'vector_store.file';
  usage_bytes: number;
  created_at: number;
  vector_store_id: string;
  status: 'in_progress' | 'completed' | 'cancelled' | 'failed';
  last_error?: {
    code: string;
    message: string;
  };
}

/**
 * Assistants types
 */
export interface AssistantRequest {
  model: ModelId;
  name?: string;
  description?: string;
  instructions?: string;
  tools?: Array<{
    type: 'code_interpreter' | 'file_search' | 'function';
    function?: {
      name: string;
      description?: string;
      parameters?: Record<string, any>;
    };
  }>;
  tool_resources?: {
    code_interpreter?: {
      file_ids?: string[];
    };
    file_search?: {
      vector_store_ids?: string[];
    };
  };
  metadata?: Record<string, string>;
  temperature?: number;
  top_p?: number;
  response_format?: 'auto' | { type: 'json_object' };
}

export interface Assistant {
  id: string;
  object: 'assistant';
  created_at: number;
  name: string | null;
  description: string | null;
  model: ModelId;
  instructions: string | null;
  tools: Array<any>;
  tool_resources?: Record<string, any>;
  metadata: Record<string, string>;
  temperature?: number;
  top_p?: number;
  response_format?: string | { type: string };
}

/**
 * Organization and Usage types
 */
export interface OrganizationUsageRequest {
  start_time: number;
  end_time: number;
  bucket_width?: '1m' | '1h' | '1d';
  project_ids?: string[];
  user_ids?: string[];
  api_key_ids?: string[];
  models?: string[];
  group_by?: Array<'project_id' | 'user_id' | 'api_key_id' | 'model'>;
}

export interface UsageResultItem {
  object: 'organization.usage.result';
  input_tokens: number;
  output_tokens: number;
  input_cached_tokens: number;
  num_model_requests: number;
  project_id?: string;
  user_id?: string;
  api_key_id?: string;
  model?: string;
}

export interface UsageBucket {
  object: 'bucket';
  start_time: number;
  end_time: number;
  results: UsageResultItem[];
}

export interface OrganizationUsageResponse {
  object: 'page';
  data: UsageBucket[];
  has_more: boolean;
  next_page: string | null;
}

/**
 * Metrics types
 */
export interface ModelMetrics {
  model: ModelId;
  request_count: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_latency_ms: number;
  error_count: number;
  latency_percentiles: {
    p50: number;
    p90: number;
    p95: number;
    p99: number;
  };
  streaming_requests: number;
  non_streaming_requests: number;
  avg_latency_ms: number;
  error_rate: number;
  total_cost: number;
  avg_cost_per_request: number;
  tokens_per_second: number;
}

export interface SystemMetrics {
  total_requests: number;
  total_tokens: number;
  total_cost: number;
  avg_latency_ms: number;
  error_rate: number;
  streaming_percentage: number;
  requests_per_second: number;
  tokens_per_second: number;
  active_connections: number;
  cache_hit_rate: number;
  uptime_seconds: number;
}

export interface TimeSeriesMetric {
  timestamp: number;
  value: number;
  metadata?: Record<string, any>;
}

export interface MetricsQuery {
  start_time?: number;
  end_time?: number;
  interval?: '1m' | '5m' | '15m' | '1h' | '1d';
  models?: ModelId[];
  metric_types?: string[];
}

/**
 * Cost types
 */
export interface CostBreakdown {
  period: 'hour' | 'day' | 'week' | 'month' | 'year';
  start_time: number;
  end_time: number;
  total_cost: number;
  by_model: Record<ModelId, number>;
  by_service: Record<string, number>;
  by_project?: Record<ProjectId, number>;
  by_user?: Record<UserId, number>;
}

export interface CostEstimate {
  estimated_monthly_cost: number;
  estimated_daily_cost: number;
  projection_confidence: number;
  based_on_days: number;
}

export interface BudgetAlert {
  id: string;
  threshold: number;
  current_spend: number;
  period: 'day' | 'week' | 'month';
  triggered: boolean;
  triggered_at?: number;
}

/**
 * Request/Response wrapper types
 */
export interface ApiResponse<T> {
  data: T;
  status: number;
  statusText: string;
  headers: Record<string, string>;
}

export interface ApiRequestConfig {
  params?: Record<string, any>;
  headers?: Record<string, string>;
  timeout?: number;
  skipRetry?: boolean;
  skipCache?: boolean;
}
