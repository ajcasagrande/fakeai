# API Integration Guide

Complete guide for integrating with the FakeAI API from the dashboard.

---

## Table of Contents

- [Overview](#overview)
- [API Client Setup](#api-client-setup)
- [Authentication](#authentication)
- [Making API Calls](#making-api-calls)
- [Error Handling](#error-handling)
- [Caching Strategy](#caching-strategy)
- [WebSocket Integration](#websocket-integration)
- [API Endpoints](#api-endpoints)
- [Type Definitions](#type-definitions)
- [Best Practices](#best-practices)

---

## Overview

The dashboard communicates with the FakeAI server through a centralized API client built on Axios. The client provides:

- **Automatic authentication** - Token injection
- **Request/response interceptors** - Logging and transformation
- **Retry logic** - Exponential backoff
- **Caching** - Configurable response caching
- **Error handling** - Unified error transformation
- **Type safety** - Full TypeScript support

---

## API Client Setup

### Configuration

**Location**: `src/api/client.ts`

```typescript
const DEFAULT_CONFIG: Required<ApiClientConfig> = {
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
  enableCache: true,
};
```

### Environment Variables

Create `.env` file:

```bash
# API Configuration
VITE_API_URL=http://localhost:8000

# Optional: WebSocket URL
VITE_WS_URL=ws://localhost:8000
```

### Custom Configuration

```typescript
import { createApiClient } from '@/api/client';

const customClient = createApiClient({
  baseURL: 'http://custom-server:8000',
  timeout: 60000,
  retryAttempts: 5,
  enableCache: false,
});
```

---

## Authentication

### Token Storage

The dashboard uses localStorage for token storage:

```typescript
// Store token
localStorage.setItem('auth_token', token);

// Retrieve token
const token = localStorage.getItem('auth_token');

// Clear token
localStorage.removeItem('auth_token');
```

### Authentication Flow

```typescript
// 1. User logs in
const response = await apiClient.post('/auth/login', {
  username: 'user@example.com',
  password: 'password123',
});

// 2. Store token
const { token } = response.data;
localStorage.setItem('auth_token', token);

// 3. Token automatically added to subsequent requests
const models = await apiClient.get('/v1/models');
// Request includes: Authorization: Bearer <token>
```

### Token Refresh

```typescript
// Automatic token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Clear invalid token
      clearAuthToken();

      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

---

## Making API Calls

### GET Requests

```typescript
import { apiClient } from '@/api/client';

// Simple GET
const response = await apiClient.get('/v1/models');
console.log(response.data);

// With query parameters
const response = await apiClient.get('/v1/chat/completions', {
  params: {
    model: 'openai/gpt-oss-120b',
    limit: 10,
  },
});

// With type safety
interface Model {
  id: string;
  name: string;
  context_length: number;
}

const response = await apiClient.get<Model[]>('/v1/models');
const models: Model[] = response.data;
```

### POST Requests

```typescript
// Create resource
const response = await apiClient.post('/v1/chat/completions', {
  model: 'openai/gpt-oss-120b',
  messages: [
    { role: 'user', content: 'Hello!' },
  ],
});

// With type safety
interface ChatResponse {
  id: string;
  choices: Array<{
    message: {
      role: string;
      content: string;
    };
  }>;
}

const response = await apiClient.post<ChatResponse>(
  '/v1/chat/completions',
  requestData
);
```

### PUT/PATCH Requests

```typescript
// Update resource
await apiClient.put('/v1/organization/users/123', {
  name: 'Updated Name',
  role: 'admin',
});

// Partial update
await apiClient.patch('/v1/organization/users/123', {
  role: 'member',
});
```

### DELETE Requests

```typescript
// Delete resource
await apiClient.delete('/v1/organization/users/123');

// With confirmation
const confirmDelete = confirm('Are you sure?');
if (confirmDelete) {
  await apiClient.delete('/v1/organization/users/123');
}
```

---

## Error Handling

### Error Types

```typescript
import { ApiError } from '@/api/errors';

try {
  await apiClient.get('/v1/models');
} catch (error) {
  if (error instanceof ApiError) {
    console.error('API Error:', {
      message: error.message,
      statusCode: error.statusCode,
      code: error.code,
      details: error.details,
    });
  } else {
    console.error('Unknown error:', error);
  }
}
```

### Status Code Handling

```typescript
try {
  const response = await apiClient.get('/v1/models');
} catch (error) {
  if (error instanceof ApiError) {
    switch (error.statusCode) {
      case 400:
        console.error('Bad request:', error.message);
        break;
      case 401:
        console.error('Unauthorized');
        // Redirect to login
        break;
      case 403:
        console.error('Forbidden');
        break;
      case 404:
        console.error('Not found');
        break;
      case 429:
        console.error('Rate limited');
        break;
      case 500:
        console.error('Server error');
        break;
      default:
        console.error('Unknown error:', error.statusCode);
    }
  }
}
```

### Retry Logic

The client automatically retries failed requests:

```typescript
// Retries on: 408, 429, 500, 502, 503, 504
// Max retries: 3 (configurable)
// Delay: Exponential backoff (1s, 2s, 4s)

// Disable retry for specific request
import { requestWithoutRetry } from '@/api/client';

const response = await requestWithoutRetry({
  method: 'POST',
  url: '/v1/chat/completions',
  data: requestData,
});
```

---

## Caching Strategy

### Automatic Caching

GET requests are cached automatically:

```typescript
// First call - hits server
const response1 = await apiClient.get('/v1/models');

// Second call within cache duration - returns cached response
const response2 = await apiClient.get('/v1/models');
// response2.headers['x-cached'] === 'true'
```

### Cache Duration

Configured per endpoint:

- **Metrics**: 5 seconds (frequently changing)
- **Models**: 30 seconds (semi-static)
- **Organization**: 5 minutes (rarely changing)
- **Default**: 1 minute

### Manual Cache Control

```typescript
import { clearCache } from '@/api/client';

// Clear all cached responses
clearCache();

// Cache is also cleared on mutations (POST, PUT, PATCH, DELETE)
```

---

## WebSocket Integration

### WebSocket Service

**Location**: `src/services/WebSocketService.ts`

```typescript
import { WebSocketService } from '@/services/WebSocketService';

const wsService = new WebSocketService('ws://localhost:8000/metrics/stream');

wsService.connect();

wsService.on('message', (data) => {
  console.log('Received:', data);
});

wsService.on('error', (error) => {
  console.error('WebSocket error:', error);
});

wsService.on('close', () => {
  console.log('WebSocket closed');
});
```

### useWebSocket Hook

```typescript
import { useWebSocket } from '@/services/hooks';

const MyComponent = () => {
  const { data, isConnected, error } = useWebSocket('/metrics/stream', {
    onMessage: (data) => {
      console.log('New data:', data);
    },
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
  });

  if (!isConnected) return <div>Connecting...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return <div>Data: {JSON.stringify(data)}</div>;
};
```

### WebSocket Context

```typescript
import { useWebSocketContext } from '@/services/WebSocketContext';

const MyComponent = () => {
  const { isConnected, lastMessage } = useWebSocketContext();

  return (
    <div>
      <div>Status: {isConnected ? 'Connected' : 'Disconnected'}</div>
      <div>Last message: {lastMessage}</div>
    </div>
  );
};
```

---

## API Endpoints

### Core Endpoints

```typescript
// Models
GET /v1/models
GET /v1/models/{id}

// Chat Completions
POST /v1/chat/completions
GET /metrics/by-model

// Embeddings
POST /v1/embeddings
GET /v1/organization/usage/embeddings

// Organization
GET /v1/organization/users
POST /v1/organization/users
GET /v1/organization/projects
POST /v1/organization/projects

// Metrics
GET /metrics
GET /metrics/by-model
GET /metrics/by-model/{model}
GET /kv-cache/metrics

// Rate Limits
GET /metrics/rate-limits
GET /metrics/rate-limits/key/{key}
GET /metrics/rate-limits/tier
```

### Example: Fetch Chat Completions Metrics

```typescript
interface ModelMetrics {
  [model: string]: {
    request_count: number;
    total_tokens: number;
    total_cost: number;
    avg_latency_ms: number;
    error_rate: number;
  };
}

const fetchChatMetrics = async (): Promise<ModelMetrics> => {
  const response = await apiClient.get<ModelMetrics>('/metrics/by-model');
  return response.data;
};
```

### Example: Create User

```typescript
interface CreateUserRequest {
  name: string;
  email: string;
  role: 'admin' | 'member';
}

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

const createUser = async (data: CreateUserRequest): Promise<User> => {
  const response = await apiClient.post<User>('/v1/organization/users', data);
  return response.data;
};
```

---

## Type Definitions

### API Types

**Location**: `src/api/types.ts`

```typescript
// Request configuration
export interface ApiClientConfig {
  baseURL?: string;
  timeout?: number;
  retryAttempts?: number;
  retryDelay?: number;
  enableCache?: boolean;
}

// Error response
export interface ApiErrorResponse {
  message: string;
  code?: string;
  details?: any;
}

// Pagination
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}
```

### Page-Specific Types

Each page defines its own types:

```typescript
// src/pages/ChatCompletions/types.ts
export interface ModelStats {
  model: string;
  request_count: number;
  total_tokens: number;
  total_cost: number;
  avg_latency_ms: number;
  error_rate: number;
}

export interface ChatRequest {
  id: string;
  model: string;
  created: number;
  prompt_tokens: number;
  completion_tokens: number;
  latency_ms: number;
  status: 'success' | 'error';
}
```

---

## Best Practices

### 1. Use Type Safety

Always define types for API responses:

```typescript
// Bad
const data: any = await apiClient.get('/v1/models');

// Good
interface Model {
  id: string;
  name: string;
}
const response = await apiClient.get<Model[]>('/v1/models');
const models: Model[] = response.data;
```

### 2. Handle Errors Gracefully

```typescript
const [data, setData] = useState<Data | null>(null);
const [error, setError] = useState<string | null>(null);
const [loading, setLoading] = useState(true);

useEffect(() => {
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<Data>('/v1/data');
      setData(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  fetchData();
}, []);
```

### 3. Use Custom Hooks

Extract data fetching logic:

```typescript
function useModelMetrics() {
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await apiClient.get<ModelMetrics>('/metrics/by-model');
        setMetrics(response.data);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  return { metrics, loading, error };
}
```

### 4. Implement Loading States

```typescript
const { data, loading, error } = useApiData();

if (loading) return <LoadingSpinner />;
if (error) return <ErrorMessage error={error} />;
if (!data) return <EmptyState />;

return <DataView data={data} />;
```

### 5. Debounce User Input

```typescript
import { debounce } from 'lodash';

const debouncedSearch = useMemo(
  () =>
    debounce(async (query: string) => {
      const results = await apiClient.get('/search', {
        params: { q: query },
      });
      setResults(results.data);
    }, 300),
  []
);

const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  debouncedSearch(e.target.value);
};
```

### 6. Cancel Requests on Unmount

```typescript
useEffect(() => {
  const abortController = new AbortController();

  const fetchData = async () => {
    try {
      const response = await apiClient.get('/data', {
        signal: abortController.signal,
      });
      setData(response.data);
    } catch (err) {
      if (err.name !== 'CanceledError') {
        console.error(err);
      }
    }
  };

  fetchData();

  return () => abortController.abort();
}, []);
```

---

## Testing API Integration

### Mock API Client

```typescript
// __mocks__/apiClient.ts
export const apiClient = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
};
```

### Test Component

```typescript
import { apiClient } from '@/api/client';

jest.mock('@/api/client');

describe('MyComponent', () => {
  it('fetches data on mount', async () => {
    const mockData = { id: '1', name: 'Test' };
    (apiClient.get as jest.Mock).mockResolvedValue({ data: mockData });

    render(<MyComponent />);

    await waitFor(() => {
      expect(screen.getByText('Test')).toBeInTheDocument();
    });

    expect(apiClient.get).toHaveBeenCalledWith('/v1/data');
  });
});
```

---

## Troubleshooting

### CORS Issues

If you encounter CORS errors:

1. Ensure FakeAI server has CORS enabled
2. Check `VITE_API_URL` in `.env`
3. Use proxy in `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/v1': 'http://localhost:8000',
      '/metrics': 'http://localhost:8000',
    },
  },
});
```

### Network Timeouts

Increase timeout for slow connections:

```typescript
const response = await apiClient.get('/data', {
  timeout: 60000, // 60 seconds
});
```

### Debug API Calls

Enable debug logging:

```bash
# .env
VITE_DEBUG_API_CALLS=true
```

---

**For more information, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)**
