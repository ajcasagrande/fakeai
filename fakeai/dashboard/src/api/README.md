# FakeAI Dashboard API Service Layer

Comprehensive, type-safe API client for the FakeAI Dashboard following 2025 best practices.

## Features

- **Axios-based HTTP client** with request/response interceptors
- **Automatic retry logic** with exponential backoff
- **Response caching** with TTL support
- **TypeScript-first** with complete type definitions
- **Typed error handling** with custom error classes
- **Auth token management** with automatic injection
- **React Query integration** with custom hooks
- **Request cancellation** via AbortController
- **Streaming support** for chat completions
- **Loading states** managed through React Query

## Directory Structure

```
api/
├── client.ts              # Axios client configuration
├── auth.ts                # Authentication token management
├── errors.ts              # Typed error classes
├── cache.ts               # Response caching system
├── types.ts               # TypeScript type definitions
├── endpoints/             # API endpoint modules
│   ├── chat.ts
│   ├── embeddings.ts
│   ├── images.ts
│   ├── audio.ts
│   ├── batches.ts
│   ├── fineTuning.ts
│   ├── vectorStores.ts
│   ├── assistants.ts
│   ├── organization.ts
│   ├── metrics.ts
│   ├── costs.ts
│   └── index.ts
├── hooks/                 # React Query hooks
│   ├── useChat.ts
│   ├── useMetrics.ts
│   ├── useCosts.ts
│   ├── useOrganization.ts
│   └── index.ts
├── index.ts               # Main export file
└── README.md              # This file
```

## Quick Start

### Installation

The API layer uses axios and @tanstack/react-query. Make sure they're installed:

```bash
npm install axios @tanstack/react-query
```

### Basic Usage

#### 1. Direct API Calls

```typescript
import { getSystemMetrics, createChatCompletion } from '@/api';

// Fetch metrics
const metrics = await getSystemMetrics();

// Create chat completion
const response = await createChatCompletion({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'Hello!' }],
});
```

#### 2. Using React Query Hooks

```typescript
import { useSystemMetrics, useChatCompletion } from '@/api';

function MyComponent() {
  // Fetch data with automatic caching and refetching
  const { data: metrics, isLoading, error } = useSystemMetrics();

  // Mutations with loading states
  const { mutate: sendChat, isLoading: isSending } = useChatCompletion({
    onSuccess: (response) => {
      console.log('Chat response:', response);
    },
  });

  return (
    <div>
      {isLoading && <p>Loading...</p>}
      {error && <p>Error: {error.message}</p>}
      {metrics && <pre>{JSON.stringify(metrics, null, 2)}</pre>}
    </div>
  );
}
```

#### 3. Streaming Chat Completions

```typescript
import { useStreamingChat } from '@/api';

function ChatComponent() {
  const { isStreaming, streamedContent, startStream, stopStream } = useStreamingChat();

  const handleSend = () => {
    startStream({
      model: 'gpt-4',
      messages: [{ role: 'user', content: 'Tell me a story' }],
    });
  };

  return (
    <div>
      <button onClick={handleSend} disabled={isStreaming}>
        Send
      </button>
      {isStreaming && <button onClick={stopStream}>Stop</button>}
      <div>{streamedContent}</div>
    </div>
  );
}
```

## Authentication

The API layer automatically manages authentication tokens:

```typescript
import { setAuthToken, clearAuthToken, isAuthenticated } from '@/api';

// Set token (automatically added to all requests)
setAuthToken('your-api-key', 3600); // 3600 seconds expiry

// Check authentication status
if (isAuthenticated()) {
  console.log('User is authenticated');
}

// Clear token
clearAuthToken();
```

## Error Handling

All API errors are typed and include helpful context:

```typescript
import { ApiError, isApiError, ApiErrorType } from '@/api';

try {
  await createChatCompletion(request);
} catch (error) {
  if (isApiError(error)) {
    console.log('Error type:', error.type);
    console.log('Status code:', error.status);
    console.log('User message:', error.getUserMessage());

    if (error.is(ApiErrorType.RATE_LIMIT_ERROR)) {
      console.log('Rate limited, retry after:', error.details?.retryAfter);
    }
  }
}
```

## Caching

The API client automatically caches GET requests:

```typescript
import { clearCache, cache } from '@/api';

// Clear all cached responses
clearCache();

// Check cache manually
const cached = cache.get('some-key');

// Disable cache for specific request
await getSystemMetrics({ skipCache: true });
```

## Request Configuration

All API functions accept an optional configuration object:

```typescript
import { createChatCompletion } from '@/api';

const response = await createChatCompletion(request, {
  timeout: 60000,        // Custom timeout
  skipRetry: true,       // Disable retry logic
  skipCache: true,       // Disable caching
  headers: {             // Additional headers
    'X-Custom': 'value',
  },
});
```

## React Query Setup

Wrap your app with QueryClientProvider:

```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60000,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <YourApp />
    </QueryClientProvider>
  );
}
```

## Available Endpoints

### Chat Completions
- `createChatCompletion(request)` - Create chat completion
- `streamChatCompletion(request)` - Stream chat completion
- `estimateChatCompletionCost(request)` - Estimate cost

### Embeddings
- `createEmbedding(request)` - Create embeddings
- `createEmbeddingsBatch(inputs, model, batchSize)` - Batch embeddings

### Images
- `generateImage(request)` - Generate images
- `editImage(request)` - Edit images
- `createImageVariation(request)` - Create variations

### Audio
- `createTranscription(request)` - Transcribe audio
- `createTranslation(request)` - Translate audio
- `createSpeech(request)` - Generate speech

### Batches
- `createBatch(request)` - Create batch
- `getBatch(id)` - Get batch status
- `listBatches()` - List batches
- `cancelBatch(id)` - Cancel batch

### Fine-tuning
- `createFineTuningJob(request)` - Create fine-tuning job
- `getFineTuningJob(id)` - Get job status
- `listFineTuningJobs()` - List jobs
- `cancelFineTuningJob(id)` - Cancel job

### Vector Stores
- `createVectorStore(request)` - Create vector store
- `getVectorStore(id)` - Get vector store
- `addFileToVectorStore(id, fileId)` - Add file

### Assistants
- `createAssistant(request)` - Create assistant
- `getAssistant(id)` - Get assistant
- `updateAssistant(id, updates)` - Update assistant
- `deleteAssistant(id)` - Delete assistant

### Organization & Usage
- `getCompletionsUsage(request)` - Get completions usage
- `getEmbeddingsUsage(request)` - Get embeddings usage
- `getUsageSummary(start, end)` - Get usage summary

### Metrics
- `getSystemMetrics()` - Get system-wide metrics
- `getModelMetrics()` - Get all model metrics
- `getModelMetricsById(id)` - Get specific model metrics
- `getTimeSeriesMetrics(query)` - Get time series data

### Costs
- `getCostBreakdown(start, end, period)` - Get cost breakdown
- `getCostEstimate(days)` - Get cost estimate
- `getCurrentMonthCost()` - Get current month cost
- `getBudgetAlerts()` - Get budget alerts

## Environment Variables

Configure the API base URL:

```env
VITE_API_URL=http://localhost:8000
```

## Best Practices

1. **Use hooks in components** - Leverage React Query for automatic caching and refetching
2. **Handle errors gracefully** - Use typed errors to provide user-friendly messages
3. **Leverage caching** - Let the API client cache responses to reduce server load
4. **Use TypeScript** - Take advantage of complete type safety
5. **Monitor health** - Use `useHealthStatus()` hook to monitor system health

## TypeScript Support

All types are exported from the main index:

```typescript
import type {
  ChatCompletionRequest,
  ChatCompletionResponse,
  SystemMetrics,
  ModelMetrics,
  CostBreakdown,
} from '@/api';
```

## License

Part of the FakeAI project.
