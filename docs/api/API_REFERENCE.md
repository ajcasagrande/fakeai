# FakeAI API Reference

**Version:** 1.0.0
**Last Updated:** 2025-10-04
**Base URL:** `http://localhost:8000`

Complete API reference with request/response examples for all FakeAI endpoints.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Models](#models)
3. [Chat Completions](#chat-completions)
4. [Completions](#completions)
5. [Embeddings](#embeddings)
6. [Images](#images)
7. [Audio](#audio)
8. [Moderations](#moderations)
9. [Files](#files)
10. [Batch](#batch)
11. [Realtime](#realtime)
12. [Responses API](#responses-api)
13. [Rankings API](#rankings-api)
14. [Organization Management](#organization-management)
15. [Usage & Billing](#usage--billing)
16. [Metrics](#metrics)

---

## Authentication

All endpoints (except `/health` and `/metrics`) require authentication via the `Authorization` header.

**Header Format:**
```
Authorization: Bearer YOUR_API_KEY
```

**Default API Keys:**
- `sk-fakeai-1234567890abcdef`
- `sk-test-abcdefghijklmnop`

**Configuration:**
```bash
# Disable authentication
export FAKEAI_REQUIRE_API_KEY=false

# Custom API keys
export FAKEAI_API_KEYS="sk-custom-key1,sk-custom-key2"
```

---

## Models

### List Models

**Endpoint:** `GET /v1/models`

**Description:** Returns a list of all available models.

**cURL Example:**
```bash
curl http://localhost:8000/v1/models \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "openai/gpt-oss-120b",
      "object": "model",
      "created": 1686935002,
      "owned_by": "openai",
      "permission": [...],
      "root": null,
      "parent": null
    },
    ...
  ]
}
```

### Get Model

**Endpoint:** `GET /v1/models/{model_id}`

**Description:** Retrieves details about a specific model.

**cURL Example:**
```bash
curl http://localhost:8000/v1/models/openai/gpt-oss-120b \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

**Response:**
```json
{
  "id": "openai/gpt-oss-120b",
  "object": "model",
  "created": 1686935002,
  "owned_by": "openai",
  "permission": [...],
  "root": null,
  "parent": null
}
```

### Get Model Capabilities

**Endpoint:** `GET /v1/models/{model_id}/capabilities`

**Description:** Returns model capabilities including context window, pricing, and feature support.

**cURL Example:**
```bash
curl http://localhost:8000/v1/models/openai/gpt-oss-120b/capabilities \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

**Response:**
```json
{
  "model": "openai/gpt-oss-120b",
  "max_context_window": 8192,
  "max_output_tokens": 4096,
  "supports_tools": true,
  "supports_vision": false,
  "supports_audio_input": false,
  "supports_audio_output": false,
  "supports_reasoning": false,
  "supports_predicted_outputs": false,
  "pricing": {
    "prompt": 0.03,
    "completion": 0.06,
    "cached_prompt": 0.015,
    "image": 0.0
  }
}
```

---

## Chat Completions

### Create Chat Completion

**Endpoint:** `POST /v1/chat/completions`

**Description:** Creates a chat completion for the provided messages.

**Request Body:**
```json
{
  "model": "openai/gpt-oss-120b",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is machine learning?"}
  ],
  "temperature": 0.7,
  "max_tokens": 500
}
```

**cURL Example:**
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is machine learning?"}
    ],
    "temperature": 0.7
  }'
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "openai/gpt-oss-120b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Machine learning is a subset of artificial intelligence..."
      },
      "finish_reason": "stop",
      "logprobs": null
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 150,
    "total_tokens": 170
  },
  "system_fingerprint": "fp_44709d6fcb"
}
```

### Streaming Chat Completion

**Request Body:**
```json
{
  "model": "openai/gpt-oss-120b",
  "messages": [{"role": "user", "content": "Write a poem"}],
  "stream": true
}
```

**cURL Example:**
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "messages": [{"role": "user", "content": "Write a poem"}],
    "stream": true
  }'
```

**Response:** (Server-Sent Events)
```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"openai/gpt-oss-120b","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"openai/gpt-oss-120b","choices":[{"index":0,"delta":{"content":"Roses"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1677652288,"model":"openai/gpt-oss-120b","choices":[{"index":0,"delta":{"content":" are"},"finish_reason":null}]}

...

data: [DONE]
```

### Multi-Modal Chat Completion

**Request Body:**
```json
{
  "model": "openai/gpt-oss-120b",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "What's in this image?"},
        {
          "type": "image_url",
          "image_url": {
            "url": "https://example.com/image.jpg",
            "detail": "high"
          }
        }
      ]
    }
  ]
}
```

### Tool Calling

**Request Body:**
```json
{
  "model": "openai/gpt-oss-120b",
  "messages": [{"role": "user", "content": "What's the weather in SF?"}],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get current weather",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
          },
          "required": ["location"]
        }
      }
    }
  ],
  "tool_choice": "auto"
}
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_abc123",
            "type": "function",
            "function": {
              "name": "get_weather",
              "arguments": "{\"location\": \"San Francisco, CA\", \"unit\": \"fahrenheit\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {...}
}
```

### Structured Outputs

**Request Body:**
```json
{
  "model": "openai/gpt-oss-120b",
  "messages": [{"role": "user", "content": "Extract: John is 30 years old"}],
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "person_info",
      "strict": true,
      "schema": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "age": {"type": "number"}
        },
        "required": ["name", "age"],
        "additionalProperties": false
      }
    }
  }
}
```

**Response:**
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "{\"name\": \"John\", \"age\": 30}"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {...}
}
```

---

## Completions

### Create Completion

**Endpoint:** `POST /v1/completions`

**Description:** Creates a completion for the provided prompt (legacy endpoint).

**Request Body:**
```json
{
  "model": "meta-llama/Llama-3.1-8B-Instruct",
  "prompt": "Say this is a test",
  "max_tokens": 100,
  "temperature": 0
}
```

**cURL Example:**
```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "prompt": "Say this is a test",
    "max_tokens": 100
  }'
```

**Response:**
```json
{
  "id": "cmpl-123",
  "object": "text_completion",
  "created": 1677652288,
  "model": "meta-llama/Llama-3.1-8B-Instruct",
  "choices": [
    {
      "text": " This is a test.",
      "index": 0,
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 5,
    "completion_tokens": 10,
    "total_tokens": 15
  }
}
```

---

## Embeddings

### Create Embeddings

**Endpoint:** `POST /v1/embeddings`

**Description:** Creates an embedding vector representing the input text.

**Request Body:**
```json
{
  "model": "sentence-transformers/all-mpnet-base-v2",
  "input": "The quick brown fox jumps over the lazy dog"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "model": "sentence-transformers/all-mpnet-base-v2",
    "input": "The quick brown fox jumps over the lazy dog"
  }'
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.0023, -0.0045, 0.0189, ...],
      "index": 0
    }
  ],
  "model": "sentence-transformers/all-mpnet-base-v2",
  "usage": {
    "prompt_tokens": 10,
    "total_tokens": 10
  }
}
```

**Batch Embeddings:**
```json
{
  "model": "sentence-transformers/all-mpnet-base-v2",
  "input": ["Text 1", "Text 2", "Text 3"]
}
```

---

## Images

### Generate Images

**Endpoint:** `POST /v1/images/generations`

**Description:** Creates an image given a text prompt.

**Request Body:**
```json
{
  "model": "stabilityai/stable-diffusion-xl-base-1.0",
  "prompt": "A white siamese cat",
  "size": "1024x1024",
  "quality": "standard",
  "n": 1
}
```

**cURL Example:**
```bash
curl http://localhost:8000/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "model": "stabilityai/stable-diffusion-xl-base-1.0",
    "prompt": "A white siamese cat",
    "size": "1024x1024"
  }'
```

**Response:**
```json
{
  "created": 1677652288,
  "data": [
    {
      "url": "https://placeholder.example.com/image.png"
    }
  ]
}
```

---

## Audio

### Text-to-Speech

**Endpoint:** `POST /v1/audio/speech`

**Description:** Generates audio from the input text.

**Request Body:**
```json
{
  "model": "tts-1",
  "input": "Hello, world!",
  "voice": "alloy",
  "response_format": "mp3",
  "speed": 1.0
}
```

**cURL Example:**
```bash
curl http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "model": "tts-1",
    "input": "Hello, world!",
    "voice": "alloy"
  }' \
  --output speech.mp3
```

**Response:** Binary audio data (Content-Type: audio/mpeg)

**Available Voices:**
- `alloy`, `ash`, `ballad`, `coral`, `echo`, `fable`, `onyx`, `nova`, `sage`, `shimmer`, `verse`

**Response Formats:**
- `mp3`, `opus`, `aac`, `flac`, `wav`, `pcm`

---

## Moderations

### Create Moderation

**Endpoint:** `POST /v1/moderations`

**Description:** Classifies if text is potentially harmful.

**Request Body:**
```json
{
  "input": "I want to kill them"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/v1/moderations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "input": "I want to kill them"
  }'
```

**Response:**
```json
{
  "id": "modr-123",
  "model": "text-moderation-stable",
  "results": [
    {
      "flagged": true,
      "categories": {
        "sexual": false,
        "hate": false,
        "harassment": false,
        "self-harm": false,
        "sexual/minors": false,
        "hate/threatening": false,
        "violence/graphic": false,
        "self-harm/intent": false,
        "self-harm/instructions": false,
        "harassment/threatening": true,
        "violence": true
      },
      "category_scores": {
        "sexual": 0.01,
        "hate": 0.02,
        "harassment": 0.15,
        "self-harm": 0.01,
        "sexual/minors": 0.0,
        "hate/threatening": 0.05,
        "violence/graphic": 0.08,
        "self-harm/intent": 0.0,
        "self-harm/instructions": 0.0,
        "harassment/threatening": 0.85,
        "violence": 0.92
      }
    }
  ]
}
```

**Batch Moderation:**
```json
{
  "input": ["Text 1", "Text 2", "Text 3"]
}
```

---

## Files

### List Files

**Endpoint:** `GET /v1/files`

**cURL Example:**
```bash
curl http://localhost:8000/v1/files \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

**Response:**
```json
{
  "data": [
    {
      "id": "file-abc123",
      "object": "file",
      "bytes": 140,
      "created_at": 1677652288,
      "filename": "mydata.jsonl",
      "purpose": "fine-tune",
      "status": "uploaded"
    }
  ],
  "object": "list"
}
```

### Upload File

**Endpoint:** `POST /v1/files`

**cURL Example:**
```bash
curl http://localhost:8000/v1/files \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -F purpose="fine-tune" \
  -F file="@mydata.jsonl"
```

### Get File

**Endpoint:** `GET /v1/files/{file_id}`

**cURL Example:**
```bash
curl http://localhost:8000/v1/files/file-abc123 \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

### Delete File

**Endpoint:** `DELETE /v1/files/{file_id}`

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/v1/files/file-abc123 \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

---

## Batch

### Create Batch

**Endpoint:** `POST /v1/batches`

**Description:** Creates a batch processing job.

**Request Body:**
```json
{
  "input_file_id": "file-abc123",
  "endpoint": "/v1/chat/completions",
  "completion_window": "24h",
  "metadata": {
    "customer_id": "user_123"
  }
}
```

**cURL Example:**
```bash
curl http://localhost:8000/v1/batches \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "input_file_id": "file-abc123",
    "endpoint": "/v1/chat/completions",
    "completion_window": "24h"
  }'
```

**Response:**
```json
{
  "id": "batch_abc123",
  "object": "batch",
  "endpoint": "/v1/chat/completions",
  "input_file_id": "file-abc123",
  "completion_window": "24h",
  "status": "validating",
  "output_file_id": null,
  "error_file_id": null,
  "created_at": 1677652288,
  "in_progress_at": null,
  "expires_at": 1677738688,
  "finalizing_at": null,
  "completed_at": null,
  "failed_at": null,
  "expired_at": null,
  "cancelling_at": null,
  "cancelled_at": null,
  "request_counts": {
    "total": 100,
    "completed": 0,
    "failed": 0
  },
  "metadata": {
    "customer_id": "user_123"
  }
}
```

### Retrieve Batch

**Endpoint:** `GET /v1/batches/{batch_id}`

**cURL Example:**
```bash
curl http://localhost:8000/v1/batches/batch_abc123 \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

### Cancel Batch

**Endpoint:** `POST /v1/batches/{batch_id}/cancel`

**cURL Example:**
```bash
curl -X POST http://localhost:8000/v1/batches/batch_abc123/cancel \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

### List Batches

**Endpoint:** `GET /v1/batches`

**Query Parameters:**
- `limit` (default: 20, max: 100)
- `after` (cursor for pagination)

**cURL Example:**
```bash
curl "http://localhost:8000/v1/batches?limit=10" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

---

## Realtime

### WebSocket Connection

**Endpoint:** `ws://localhost:8000/v1/realtime?model=openai/gpt-oss-120b-realtime-preview`

**Description:** Establishes a WebSocket connection for real-time bidirectional streaming.

**JavaScript Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/v1/realtime?model=openai/gpt-oss-120b-realtime-preview');

ws.onopen = () => {
  console.log('Connected to Realtime API');

  // Update session
  ws.send(JSON.stringify({
    type: 'session.update',
    session: {
      voice: 'alloy',
      instructions: 'You are a helpful assistant.',
      turn_detection: {type: 'server_vad'}
    }
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message.type);
};

// Send audio
ws.send(JSON.stringify({
  type: 'input_audio_buffer.append',
  audio: base64AudioData
}));

// Commit audio
ws.send(JSON.stringify({
  type: 'input_audio_buffer.commit'
}));

// Create response
ws.send(JSON.stringify({
  type: 'response.create'
}));
```

**Event Types:**

**Client → Server:**
- `session.update` - Update session configuration
- `input_audio_buffer.append` - Add audio to buffer
- `input_audio_buffer.commit` - Commit audio buffer
- `input_audio_buffer.clear` - Clear audio buffer
- `conversation.item.create` - Add conversation item
- `conversation.item.delete` - Remove conversation item
- `response.create` - Generate response
- `response.cancel` - Cancel response

**Server → Client:**
- `session.created` - Session initialized
- `session.updated` - Session config changed
- `input_audio_buffer.speech_started` - VAD detected speech
- `input_audio_buffer.speech_stopped` - Speech ended
- `conversation.item.created` - Item added
- `response.created` - Response started
- `response.done` - Response completed
- `response.audio.delta` - Audio chunk
- `response.text.delta` - Text chunk
- `error` - Error occurred

---

## Responses API

### Create Response

**Endpoint:** `POST /v1/responses`

**Description:** OpenAI Responses API (March 2025 format) with stateful conversations.

**Request Body:**
```json
{
  "model": "openai/gpt-oss-120b",
  "input": "Tell me about AI",
  "instructions": "You are a helpful assistant",
  "max_output_tokens": 500,
  "temperature": 0.7,
  "store": true,
  "metadata": {
    "user_id": "123"
  }
}
```

**cURL Example:**
```bash
curl http://localhost:8000/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "input": "Tell me about AI",
    "instructions": "You are a helpful assistant"
  }'
```

**Response:**
```json
{
  "id": "resp_123",
  "object": "response",
  "created": 1677652288,
  "model": "openai/gpt-oss-120b",
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": "Artificial Intelligence is..."
    }
  ],
  "usage": {
    "input_tokens": 10,
    "output_tokens": 150,
    "total_tokens": 160
  }
}
```

**Continue Conversation:**
```json
{
  "model": "openai/gpt-oss-120b",
  "input": "Tell me more",
  "previous_response_id": "resp_123"
}
```

---

## Rankings API

### Create Ranking

**Endpoint:** `POST /v1/ranking`

**Description:** NVIDIA NIM Rankings API for reranking passages by relevance.

**Request Body:**
```json
{
  "model": "nvidia/nv-rerankqa-mistral-4b-v3",
  "query": {"text": "What is machine learning?"},
  "passages": [
    {"text": "Machine learning is a subset of AI that enables systems to learn from data."},
    {"text": "Python is a popular programming language."},
    {"text": "Deep learning uses neural networks with multiple layers."}
  ],
  "truncate": "END"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/v1/ranking \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "model": "nvidia/nv-rerankqa-mistral-4b-v3",
    "query": {"text": "What is machine learning?"},
    "passages": [
      {"text": "Machine learning is a subset of AI."},
      {"text": "Python is a programming language."}
    ]
  }'
```

**Response:**
```json
{
  "rankings": [
    {"index": 0, "logit": 8.52},
    {"index": 2, "logit": 6.18},
    {"index": 1, "logit": 1.23}
  ]
}
```

---

## Organization Management

### Organization Users

**List Users:**
```bash
curl http://localhost:8000/v1/organization/users \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

**Get User:**
```bash
curl http://localhost:8000/v1/organization/users/user-abc123 \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

**Create User:**
```bash
curl http://localhost:8000/v1/organization/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "email": "user@example.com",
    "role": "reader"
  }'
```

**Modify User:**
```bash
curl -X POST http://localhost:8000/v1/organization/users/user-abc123 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "role": "owner"
  }'
```

**Delete User:**
```bash
curl -X DELETE http://localhost:8000/v1/organization/users/user-abc123 \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

### Projects

**List Projects:**
```bash
curl "http://localhost:8000/v1/organization/projects?include_archived=false" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

**Create Project:**
```bash
curl http://localhost:8000/v1/organization/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "name": "Production Project"
  }'
```

**Archive Project:**
```bash
curl -X POST http://localhost:8000/v1/organization/projects/proj-abc123/archive \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

---

## Usage & Billing

### Completions Usage

**Endpoint:** `GET /v1/organization/usage/completions`

**Query Parameters:**
- `start_time` (required): Unix timestamp
- `end_time` (required): Unix timestamp
- `bucket_width`: `1m`, `1h`, or `1d` (default: `1d`)
- `project_id` (optional): Filter by project
- `model` (optional): Filter by model

**cURL Example:**
```bash
curl "http://localhost:8000/v1/organization/usage/completions?start_time=1700000000&end_time=1700086400&bucket_width=1d" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "start_time": 1700000000,
      "end_time": 1700086400,
      "total_requests": 100,
      "total_tokens": 50000,
      "input_tokens": 30000,
      "output_tokens": 20000,
      "cached_tokens": 5000
    }
  ],
  "has_more": false
}
```

### Costs

**Endpoint:** `GET /v1/organization/costs`

**cURL Example:**
```bash
curl "http://localhost:8000/v1/organization/costs?start_time=1700000000&end_time=1700086400" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

**Response:**
```json
{
  "object": "list",
  "data": [
    {
      "start_time": 1700000000,
      "end_time": 1700086400,
      "results": [
        {
          "object": "cost.result",
          "line_item": "chat_completions",
          "project_id": "proj-abc123",
          "amount": {
            "value": 15.50,
            "currency": "usd"
          }
        }
      ]
    }
  ]
}
```

---

## Metrics

### Server Metrics

**Endpoint:** `GET /metrics`

**Description:** Returns server performance metrics (no authentication required).

**cURL Example:**
```bash
curl http://localhost:8000/metrics
```

**Response:**
```json
{
  "requests": {
    "/v1/chat/completions": {
      "rate": 10.5,
      "avg": 0,
      "min": 0,
      "max": 0,
      "p50": 0,
      "p90": 0,
      "p99": 0
    }
  },
  "responses": {
    "/v1/chat/completions": {
      "rate": 10.4,
      "avg": 0.15,
      "min": 0.12,
      "max": 0.18,
      "p50": 0.15,
      "p90": 0.17,
      "p99": 0.18
    }
  },
  "tokens": {
    "/v1/chat/completions": {
      "rate": 520.3
    }
  },
  "errors": {}
}
```

### KV Cache Metrics

**Endpoint:** `GET /kv-cache-metrics`

**Description:** Returns KV cache performance and smart routing metrics.

**cURL Example:**
```bash
curl http://localhost:8000/kv-cache-metrics
```

**Response:**
```json
{
  "cache_performance": {
    "cache_hit_rate": 65.3,
    "token_reuse_rate": 42.8,
    "total_cache_hits": 1250,
    "total_cache_misses": 665,
    "total_tokens_processed": 150000,
    "cached_tokens_reused": 64200,
    "avg_prefix_length": 128.5,
    "by_endpoint": {
      "/v1/chat/completions": {
        "hits": 1200,
        "misses": 600
      }
    }
  },
  "smart_router": {
    "workers": {
      "worker-0": {
        "active_requests": 2,
        "total_requests": 500,
        "cached_blocks": 1250,
        "tokens_processed": 50000
      },
      "worker-1": {...}
    },
    "radix_tree": {
      "total_nodes": 5000,
      "total_cached_blocks": 4800
    },
    "config": {
      "kv_overlap_weight": 1.0,
      "load_balance_weight": 0.5,
      "block_size": 16,
      "num_workers": 4
    }
  }
}
```

---

## Error Responses

All errors follow the OpenAI error format:

```json
{
  "error": {
    "code": "invalid_request_error",
    "message": "The model `gpt-invalid` does not exist",
    "param": "model",
    "type": "invalid_request_error"
  }
}
```

**Common Error Codes:**
- `invalid_request_error` (400) - Invalid request parameters
- `authentication_error` (401) - Invalid API key
- `rate_limit_exceeded` (429) - Rate limit hit
- `server_error` (500) - Internal server error

---

## Rate Limiting

**Headers in Response:**
```
X-RateLimit-Limit-Requests: 10000
X-RateLimit-Limit-Tokens: 2000000
X-RateLimit-Remaining-Requests: 9999
X-RateLimit-Remaining-Tokens: 1999500
X-RateLimit-Reset-Requests: 60s
X-RateLimit-Reset-Tokens: 60s
```

**429 Response:**
```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Please retry after the specified time.",
    "type": "rate_limit_error"
  }
}
```

**Headers:**
```
Retry-After: 30
```

---

## Python SDK Examples

### Using OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000"
)

# Chat completion
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Hello"}]
)

# Streaming
for chunk in client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Hello"}],
    stream=True
):
    print(chunk.choices[0].delta.content, end="")

# Embeddings
response = client.embeddings.create(
    model="sentence-transformers/all-mpnet-base-v2",
    input="Hello world"
)

# Moderation
response = client.moderations.create(
    input="Violent content here"
)

# Batch
batch = client.batches.create(
    input_file_id="file-abc123",
    endpoint="/v1/chat/completions",
    completion_window="24h"
)
```

---

**Last Updated:** 2025-10-04
**Version:** 1.0.0
