export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  isStreaming?: boolean;
  error?: string;
  reasoning_content?: string;
  oneOffModel?: string; // Model used for this specific response (overrides conversation default)
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
  model: string;
  systemPrompt?: string;
}

export interface ChatSettings {
  model: string;
  temperature: number;
  maxTokens: number;
  systemPrompt: string;
}

export interface ChatCompletionRequest {
  model: string;
  messages: Array<{
    role: 'system' | 'user' | 'assistant';
    content: string;
  }>;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

export interface ChatCompletionResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: string;
      content: string;
    };
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface ChatCompletionChunk {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    delta: {
      role?: string;
      content?: string;
    };
    finish_reason: string | null;
  }>;
}

export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  estimatedCost: number;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  contextWindow: number;
  costPer1kPrompt: number;
  costPer1kCompletion: number;
  description?: string;
  tags?: string[];
}

// Updated October 2025 - All major providers and models
export const AVAILABLE_MODELS: ModelInfo[] = [
  // === OPENAI ===
  { id: 'gpt-5', name: 'GPT-5', provider: 'OpenAI', contextWindow: 400000, costPer1kPrompt: 0.00125, costPer1kCompletion: 0.01, description: 'Latest flagship with 400K context', tags: ['latest', 'reasoning', 'multimodal'] },
  { id: 'gpt-5-mini', name: 'GPT-5 Mini', provider: 'OpenAI', contextWindow: 256000, costPer1kPrompt: 0.0005, costPer1kCompletion: 0.0025, description: 'Efficient GPT-5 variant', tags: ['efficient', 'fast'] },
  { id: 'gpt-5-nano', name: 'GPT-5 Nano', provider: 'OpenAI', contextWindow: 128000, costPer1kPrompt: 0.0002, costPer1kCompletion: 0.0008, description: 'Ultra-efficient GPT-5', tags: ['budget', 'fast'] },
  { id: 'gpt-4.1', name: 'GPT-4.1', provider: 'OpenAI', contextWindow: 1000000, costPer1kPrompt: 0.002, costPer1kCompletion: 0.008, description: '1M context, excellent coding', tags: ['coding', 'long-context'] },
  { id: 'gpt-4.1-mini', name: 'GPT-4.1 Mini', provider: 'OpenAI', contextWindow: 512000, costPer1kPrompt: 0.0004, costPer1kCompletion: 0.0016, description: 'Efficient with 512K context', tags: ['efficient'] },
  { id: 'gpt-4.1-nano', name: 'GPT-4.1 Nano', provider: 'OpenAI', contextWindow: 128000, costPer1kPrompt: 0.0001, costPer1kCompletion: 0.0004, description: 'Budget GPT-4.1', tags: ['budget'] },
  { id: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI', contextWindow: 128000, costPer1kPrompt: 0.0025, costPer1kCompletion: 0.01, description: 'Multimodal flagship', tags: ['multimodal', 'vision'] },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI', contextWindow: 128000, costPer1kPrompt: 0.00015, costPer1kCompletion: 0.0006, description: 'Efficient multimodal', tags: ['efficient', 'vision'] },
  { id: 'gpt-4-turbo', name: 'GPT-4 Turbo', provider: 'OpenAI', contextWindow: 128000, costPer1kPrompt: 0.01, costPer1kCompletion: 0.03, description: 'Legacy GPT-4', tags: ['legacy'] },
  { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', provider: 'OpenAI', contextWindow: 16385, costPer1kPrompt: 0.0005, costPer1kCompletion: 0.0015, description: 'Legacy efficient model', tags: ['legacy', 'budget'] },

  // === ANTHROPIC ===
  { id: 'claude-sonnet-4-5', name: 'Claude Sonnet 4.5', provider: 'Anthropic', contextWindow: 200000, costPer1kPrompt: 0.003, costPer1kCompletion: 0.015, description: 'Latest! 82% SWE-bench, 64K output', tags: ['latest', 'coding', 'flagship'] },
  { id: 'claude-sonnet-4', name: 'Claude Sonnet 4', provider: 'Anthropic', contextWindow: 200000, costPer1kPrompt: 0.003, costPer1kCompletion: 0.015, description: 'Balanced Claude 4', tags: ['balanced'] },
  { id: 'claude-opus-4', name: 'Claude Opus 4', provider: 'Anthropic', contextWindow: 200000, costPer1kPrompt: 0.015, costPer1kCompletion: 0.075, description: 'Most powerful Claude', tags: ['powerful', 'premium'] },
  { id: 'claude-haiku-4', name: 'Claude Haiku 4', provider: 'Anthropic', contextWindow: 200000, costPer1kPrompt: 0.0008, costPer1kCompletion: 0.004, description: 'Fast Claude 4', tags: ['fast', 'efficient'] },
  { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet', provider: 'Anthropic', contextWindow: 200000, costPer1kPrompt: 0.003, costPer1kCompletion: 0.015, description: 'Claude 3.5 (legacy)', tags: ['legacy'] },
  { id: 'claude-3-opus-20240229', name: 'Claude 3 Opus', provider: 'Anthropic', contextWindow: 200000, costPer1kPrompt: 0.015, costPer1kCompletion: 0.075, description: 'Claude 3 powerful', tags: ['legacy'] },
  { id: 'claude-3-sonnet-20240229', name: 'Claude 3 Sonnet', provider: 'Anthropic', contextWindow: 200000, costPer1kPrompt: 0.003, costPer1kCompletion: 0.015, description: 'Claude 3 balanced', tags: ['legacy'] },
  { id: 'claude-3-haiku-20240307', name: 'Claude 3 Haiku', provider: 'Anthropic', contextWindow: 200000, costPer1kPrompt: 0.00025, costPer1kCompletion: 0.00125, description: 'Claude 3 fast', tags: ['legacy', 'efficient'] },

  // === META LLAMA ===
  { id: 'meta-llama/Llama-4-Scout', name: 'Llama 4 Scout', provider: 'Meta', contextWindow: 10000000, costPer1kPrompt: 0.00019, costPer1kCompletion: 0.00019, description: '🚀 10M context! Revolutionary', tags: ['revolutionary', 'ultra-long-context'] },
  { id: 'meta-llama/Llama-4-Maverick', name: 'Llama 4 Maverick', provider: 'Meta', contextWindow: 1000000, costPer1kPrompt: 0.00019, costPer1kCompletion: 0.00019, description: '1M context, 400B MoE', tags: ['powerful', 'long-context'] },
  { id: 'meta-llama/Llama-3.1-405B-Instruct', name: 'Llama 3.1 405B', provider: 'Meta', contextWindow: 128000, costPer1kPrompt: 0.005, costPer1kCompletion: 0.015, description: 'Flagship Llama 3.1', tags: ['large'] },
  { id: 'meta-llama/Llama-3.1-70B-Instruct', name: 'Llama 3.1 70B', provider: 'Meta', contextWindow: 128000, costPer1kPrompt: 0.00088, costPer1kCompletion: 0.00088, description: 'Balanced Llama 3.1', tags: ['balanced'] },
  { id: 'meta-llama/Llama-3.1-8B-Instruct', name: 'Llama 3.1 8B', provider: 'Meta', contextWindow: 128000, costPer1kPrompt: 0.00018, costPer1kCompletion: 0.00018, description: 'Efficient Llama 3.1', tags: ['efficient', 'budget'] },

  // === GOOGLE ===
  { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro', provider: 'Google', contextWindow: 2000000, costPer1kPrompt: 0.00125, costPer1kCompletion: 0.005, description: '2M context with thinking', tags: ['reasoning', 'ultra-long-context'] },
  { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', provider: 'Google', contextWindow: 1000000, costPer1kPrompt: 0.000075, costPer1kCompletion: 0.0003, description: '1M context, excellent value', tags: ['efficient', 'fast', 'best-value'] },
  { id: 'gemini-2.5-flash-lite', name: 'Gemini 2.5 Flash-Lite', provider: 'Google', contextWindow: 1000000, costPer1kPrompt: 0.0000375, costPer1kCompletion: 0.00015, description: 'Ultra-fast! 544 tok/s', tags: ['ultra-fast', 'budget'] },
  { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash', provider: 'Google', contextWindow: 1000000, costPer1kPrompt: 0.0001, costPer1kCompletion: 0.0004, description: 'Previous gen fast', tags: ['efficient'] },
  { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro', provider: 'Google', contextWindow: 2000000, costPer1kPrompt: 0.00125, costPer1kCompletion: 0.005, description: 'Legacy 2M context', tags: ['legacy'] },
  { id: 'gemma-3n-e4b', name: 'Gemma 3n E4B', provider: 'Google', contextWindow: 8192, costPer1kPrompt: 0.00003, costPer1kCompletion: 0.00003, description: 'Cheapest! Edge model', tags: ['budget', 'edge', 'cheapest'] },

  // === DEEPSEEK ===
  { id: 'deepseek-v3.1', name: 'DeepSeek V3.1', provider: 'DeepSeek', contextWindow: 128000, costPer1kPrompt: 0.00014, costPer1kCompletion: 0.00028, description: 'Hybrid thinking! 671B MoE', tags: ['reasoning', 'efficient', 'hybrid'] },
  { id: 'deepseek-v3', name: 'DeepSeek V3', provider: 'DeepSeek', contextWindow: 128000, costPer1kPrompt: 0.00027, costPer1kCompletion: 0.0011, description: '671B MoE flagship', tags: ['powerful'] },
  { id: 'deepseek-ai/DeepSeek-R1', name: 'DeepSeek-R1', provider: 'DeepSeek', contextWindow: 200000, costPer1kPrompt: 0.00055, costPer1kCompletion: 0.00219, description: 'Reasoning specialist', tags: ['reasoning'] },
  { id: 'deepseek-ai/DeepSeek-R1-Distill-Qwen-32B', name: 'DeepSeek-R1 Qwen-32B', provider: 'DeepSeek', contextWindow: 128000, costPer1kPrompt: 0.00014, costPer1kCompletion: 0.00028, description: 'Efficient reasoning', tags: ['reasoning', 'efficient'] },
  { id: 'deepseek-coder', name: 'DeepSeek Coder', provider: 'DeepSeek', contextWindow: 128000, costPer1kPrompt: 0.00014, costPer1kCompletion: 0.00028, description: 'Code specialist', tags: ['coding', 'efficient'] },

  // === MISTRAL ===
  { id: 'mistral-large-2411', name: 'Mistral Large 2.1', provider: 'Mistral', contextWindow: 128000, costPer1kPrompt: 0.002, costPer1kCompletion: 0.006, description: '123B flagship', tags: ['flagship'] },
  { id: 'mistral-medium-3', name: 'Mistral Medium 3', provider: 'Mistral', contextWindow: 128000, costPer1kPrompt: 0.0027, costPer1kCompletion: 0.0081, description: 'Balanced performance', tags: ['balanced'] },
  { id: 'mistralai/Mixtral-8x22B-Instruct-v0.1', name: 'Mixtral 8x22B', provider: 'Mistral', contextWindow: 65536, costPer1kPrompt: 0.002, costPer1kCompletion: 0.006, description: '141B MoE', tags: ['powerful', 'moe'] },
  { id: 'mistralai/Mixtral-8x7B-Instruct-v0.1', name: 'Mixtral 8x7B', provider: 'Mistral', contextWindow: 32768, costPer1kPrompt: 0.0007, costPer1kCompletion: 0.0007, description: '47B MoE', tags: ['balanced', 'moe'] },
  { id: 'ministral-3b', name: 'Ministral 3B', provider: 'Mistral', contextWindow: 128000, costPer1kPrompt: 0.00004, costPer1kCompletion: 0.00004, description: 'Ultra-efficient', tags: ['budget', 'edge'] },

  // === COHERE ===
  { id: 'command-a-vision', name: 'Command A Vision', provider: 'Cohere', contextWindow: 256000, costPer1kPrompt: 0.0025, costPer1kCompletion: 0.01, description: '256K context, multimodal', tags: ['multimodal', 'vision', 'enterprise'] },
  { id: 'command-a', name: 'Command A', provider: 'Cohere', contextWindow: 256000, costPer1kPrompt: 0.0025, costPer1kCompletion: 0.01, description: '111B enterprise flagship', tags: ['enterprise', 'flagship'] },
  { id: 'command-r-plus', name: 'Command R+', provider: 'Cohere', contextWindow: 128000, costPer1kPrompt: 0.0025, costPer1kCompletion: 0.01, description: '104B RAG optimized', tags: ['rag'] },
  { id: 'command-r', name: 'Command R', provider: 'Cohere', contextWindow: 128000, costPer1kPrompt: 0.00015, costPer1kCompletion: 0.0006, description: 'Lowest latency! 0.12s TTFT', tags: ['ultra-fast', 'rag', 'efficient'] },
  { id: 'command-r7b', name: 'Command R7B', provider: 'Cohere', contextWindow: 128000, costPer1kPrompt: 0.0000375, costPer1kCompletion: 0.00015, description: 'Small efficient', tags: ['budget', 'efficient'] },
  { id: 'aya-expanse-32b', name: 'Aya Expanse 32B', provider: 'Cohere', contextWindow: 128000, costPer1kPrompt: 0.0006, costPer1kCompletion: 0.0024, description: '23+ languages', tags: ['multilingual', 'efficient'] },

  // === NVIDIA ===
  { id: 'nvidia/cosmos-vision', name: 'NVIDIA Cosmos Vision', provider: 'NVIDIA', contextWindow: 32768, costPer1kPrompt: 0.001, costPer1kCompletion: 0.003, description: 'Video understanding', tags: ['multimodal', 'video'] },
  { id: 'nvidia/llama-3.1-nemotron-70b-instruct', name: 'Llama 3.1 NeMo 70B', provider: 'NVIDIA', contextWindow: 128000, costPer1kPrompt: 0.00088, costPer1kCompletion: 0.00088, description: 'NVIDIA optimized', tags: ['optimized'] },
];

export const DEFAULT_SETTINGS: ChatSettings = {
  model: 'claude-sonnet-4-5', // Latest and best for coding!
  temperature: 0.7,
  maxTokens: 4096,
  systemPrompt: 'You are a helpful AI assistant.',
};

// Helper function to check if a model is a reasoning model
export const isReasoningModel = (modelId: string): boolean => {
  const lowerModel = modelId.toLowerCase();
  return lowerModel.includes('o1') ||
         lowerModel.includes('o3') ||
         lowerModel.includes('deepseek-r1') ||
         lowerModel.includes('reasoning');
};

// Get model display name
export const getModelDisplayName = (modelId: string): string => {
  const model = AVAILABLE_MODELS.find(m => m.id === modelId);
  return model?.name || modelId;
};

// Group models by category for ChatGPT-style selector
export const getModelGroups = () => {
  const groups: Record<string, ModelInfo[]> = {
    'Reasoning Models': [],
    'GPT Models': [],
    'Claude Models': [],
    'Other Models': [],
  };

  AVAILABLE_MODELS.forEach(model => {
    if (isReasoningModel(model.id)) {
      groups['Reasoning Models'].push(model);
    } else if (model.provider === 'OpenAI') {
      groups['GPT Models'].push(model);
    } else if (model.provider === 'Anthropic') {
      groups['Claude Models'].push(model);
    } else {
      groups['Other Models'].push(model);
    }
  });

  // Remove empty groups
  Object.keys(groups).forEach(key => {
    if (groups[key].length === 0) delete groups[key];
  });

  return groups;
};
