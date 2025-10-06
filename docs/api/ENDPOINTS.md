# API Endpoint Reference

This document provides a comprehensive reference for all API endpoints supported by FakeAI.

## Table of Contents

- [Authentication](#authentication)
- [Models](#models)
- [Chat Completions](#chat-completions)
- [Text Completions](#text-completions)
- [Embeddings](#embeddings)
- [Image Generation](#image-generation)
- [Files](#files)
- [Text Generation (Azure)](#text-generation-azure)
- [Responses API](#responses-api)
- [Rankings API (NVIDIA NIM)](#rankings-api-nvidia-nim)
- [Health Check](#health-check)
- [Metrics](#metrics)

---

## Authentication

All API endpoints (except `/health` and `/metrics`) require authentication using an API key.

**Header Format:**
```
Authorization: Bearer YOUR_API_KEY
```

**Default API Keys:**
- `sk-fakeai-1234567890abcdef`
- `sk-test-abcdefghijklmnop`

**Configuration:**
- Set `FAKEAI_REQUIRE_API_KEY=false` to disable authentication
- Add custom keys via `FAKEAI_API_KEYS=key1,key2,key3`

---

## Models

### List Models

**Endpoint:** `GET /v1/models`

Lists all available models.

**Response Schema:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "openai/gpt-oss-120b",
      "object": "model",
      "created": 1234567890,
      "owned_by": "openai",
      "permission": [...],
      "root": null,
      "parent": null
    }
  ]
}
```

**Example curl:**
```bash
curl http://localhost:8000/v1/models \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

**Example Python:**
```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1"
)

models = client.models.list()
for model in models.data:
    print(f"{model.id} - {model.owned_by}")
```

### Get Model

**Endpoint:** `GET /v1/models/{model_id}`

Retrieves details about a specific model.

**Path Parameters:**
- `model_id` (string, required): The ID of the model

**Response Schema:**
```json
{
  "id": "openai/gpt-oss-120b",
  "object": "model",
  "created": 1234567890,
  "owned_by": "openai",
  "permission": [...],
  "root": null,
  "parent": null
}
```

**Example curl:**
```bash
curl http://localhost:8000/v1/models/openai/gpt-oss-120b \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

**Example Python:**
```python
model = client.models.retrieve("openai/gpt-oss-120b")
print(f"Model: {model.id}, Owner: {model.owned_by}")
```

---

## Chat Completions

### Create Chat Completion

**Endpoint:** `POST /v1/chat/completions`

Creates a chat completion response (streaming or non-streaming).

**Request Schema:**
```json
{
  "model": "openai/gpt-oss-120b",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Hello!"
    }
  ],
  "temperature": 1.0,
  "top_p": 1.0,
  "n": 1,
  "stream": false,
  "stop": null,
  "max_tokens": 100,
  "presence_penalty": 0,
  "frequency_penalty": 0,
  "logit_bias": null,
  "user": "user-123",
  "response_format": {"type": "text"},
  "seed": null,
  "tools": null,
  "tool_choice": "auto",
  "parallel_tool_calls": true,
  "logprobs": false,
  "top_logprobs": null,
  "stream_options": null,
  "max_completion_tokens": null,
  "service_tier": null,
  "modalities": null,
  "audio": null,
  "store": false,
  "metadata": null
}
```

**Response Schema (Non-Streaming):**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "openai/gpt-oss-120b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop",
      "logprobs": null
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30,
    "prompt_tokens_details": {
      "cached_tokens": 0,
      "audio_tokens": 0
    },
    "completion_tokens_details": {
      "reasoning_tokens": 0,
      "audio_tokens": 0,
      "accepted_prediction_tokens": 0,
      "rejected_prediction_tokens": 0
    }
  },
  "system_fingerprint": "fp_abc123"
}
```

**Response Format (Streaming):**
When `stream: true`, the response is sent as Server-Sent Events (SSE):

```
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1234567890,"model":"openai/gpt-oss-120b","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1234567890,"model":"openai/gpt-oss-120b","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1234567890,"model":"openai/gpt-oss-120b","choices":[{"index":0,"delta":{"content":"!"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1234567890,"model":"openai/gpt-oss-120b","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

**Example curl (Non-Streaming):**
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

**Example curl (Streaming):**
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "messages": [{"role": "user", "content": "Write a haiku about AI"}],
    "stream": true
  }'
```

**Example Python (Non-Streaming):**
```python
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me about AI."}
    ],
    temperature=0.7,
    max_tokens=150
)

print(response.choices[0].message.content)
print(f"Tokens used: {response.usage.total_tokens}")
```

**Example Python (Streaming):**
```python
stream = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Write a poem"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## Text Completions

### Create Text Completion

**Endpoint:** `POST /v1/completions`

Creates a text completion (legacy endpoint).

**Request Schema:**
```json
{
  "model": "meta-llama/Llama-3.1-8B-Instruct",
  "prompt": "Once upon a time",
  "suffix": null,
  "max_tokens": 16,
  "temperature": 1.0,
  "top_p": 1.0,
  "n": 1,
  "stream": false,
  "logprobs": null,
  "echo": false,
  "stop": null,
  "presence_penalty": 0,
  "frequency_penalty": 0,
  "best_of": 1,
  "logit_bias": null,
  "user": null
}
```

**Response Schema:**
```json
{
  "id": "cmpl-abc123",
  "object": "text_completion",
  "created": 1234567890,
  "model": "meta-llama/Llama-3.1-8B-Instruct",
  "choices": [
    {
      "text": " in a faraway land...",
      "index": 0,
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 4,
    "completion_tokens": 6,
    "total_tokens": 10
  }
}
```

**Example curl:**
```bash
curl http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "prompt": "Say hello in 3 languages:",
    "max_tokens": 50
  }'
```

**Example Python:**
```python
response = client.completions.create(
    model="meta-llama/Llama-3.1-8B-Instruct",
    prompt="Once upon a time,",
    max_tokens=30
)

print(response.choices[0].text)
```

---

## Embeddings

### Create Embeddings

**Endpoint:** `POST /v1/embeddings`

Creates embeddings for input text.

**Request Schema:**
```json
{
  "model": "sentence-transformers/all-mpnet-base-v2",
  "input": "The quick brown fox",
  "encoding_format": "float",
  "dimensions": null,
  "user": null
}
```

**Response Schema:**
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [0.0023, -0.0145, 0.0089, ...],
      "index": 0
    }
  ],
  "model": "sentence-transformers/all-mpnet-base-v2",
  "usage": {
    "prompt_tokens": 5,
    "total_tokens": 5
  }
}
```

**Example curl:**
```bash
curl http://localhost:8000/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "model": "sentence-transformers/all-mpnet-base-v2",
    "input": "The quick brown fox jumps over the lazy dog"
  }'
```

**Example Python:**
```python
response = client.embeddings.create(
    model="sentence-transformers/all-mpnet-base-v2",
    input="The quick brown fox jumps over the lazy dog"
)

embedding = response.data[0].embedding
print(f"Embedding vector with {len(embedding)} dimensions")
print(f"First 5 values: {embedding[:5]}")
```

**Batch Embeddings:**
```python
# Multiple texts at once
response = client.embeddings.create(
    model="sentence-transformers/all-mpnet-base-v2",
    input=["Text 1", "Text 2", "Text 3"]
)

for i, item in enumerate(response.data):
    print(f"Embedding {i}: {len(item.embedding)} dimensions")
```

---

## Image Generation

### Generate Images

**Endpoint:** `POST /v1/images/generations`

Generates images using DALL-E.

**Request Schema:**
```json
{
  "prompt": "A futuristic city with flying cars",
  "model": "stabilityai/stable-diffusion-xl-base-1.0",
  "n": 1,
  "quality": "standard",
  "response_format": "url",
  "size": "1024x1024",
  "style": "vivid",
  "user": null
}
```

**Response Schema:**
```json
{
  "created": 1234567890,
  "data": [
    {
      "url": "https://simulated-openai-images.example.com/abc123.png",
      "b64_json": null,
      "revised_prompt": null
    }
  ]
}
```

**Example curl:**
```bash
curl http://localhost:8000/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "prompt": "A beautiful sunset over mountains",
    "model": "stabilityai/stable-diffusion-xl-base-1.0",
    "size": "1024x1024",
    "quality": "hd"
  }'
```

**Example Python:**
```python
response = client.images.generate(
    model="stabilityai/stable-diffusion-xl-base-1.0",
    prompt="A futuristic city with flying cars",
    size="1024x1024",
    quality="hd",
    n=1
)

print(f"Image URL: {response.data[0].url}")
```

---

## Files

### List Files

**Endpoint:** `GET /v1/files`

Lists uploaded files.

**Response Schema:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "file-abc123",
      "object": "file",
      "bytes": 123456,
      "created_at": 1234567890,
      "filename": "training_data.jsonl",
      "purpose": "fine-tune",
      "status": "processed",
      "status_details": null
    }
  ]
}
```

**Example curl:**
```bash
curl http://localhost:8000/v1/files \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

### Get File

**Endpoint:** `GET /v1/files/{file_id}`

Retrieves details about a specific file.

**Example curl:**
```bash
curl http://localhost:8000/v1/files/file-abc123 \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

### Delete File

**Endpoint:** `DELETE /v1/files/{file_id}`

Deletes a file.

**Response Schema:**
```json
{
  "id": "file-abc123",
  "object": "file",
  "deleted": true
}
```

**Example curl:**
```bash
curl -X DELETE http://localhost:8000/v1/files/file-abc123 \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef"
```

---

## Text Generation (Azure)

### Create Text Generation

**Endpoint:** `POST /v1/text/generation`

Azure-compatible text generation endpoint.

**Request Schema:**
```json
{
  "input": "Tell me about AI",
  "model": "openai/gpt-oss-120b",
  "max_output_tokens": 100,
  "temperature": 1.0,
  "top_p": 0.95,
  "stop": null,
  "user": null
}
```

**Response Schema:**
```json
{
  "id": "txtgen-abc123",
  "created": 1234567890,
  "output": "Artificial Intelligence...",
  "model": "openai/gpt-oss-120b",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
```

**Example curl:**
```bash
curl http://localhost:8000/v1/text/generation \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "input": "Explain quantum computing",
    "model": "openai/gpt-oss-120b",
    "max_output_tokens": 200
  }'
```

---

## Responses API

### Create Response

**Endpoint:** `POST /v1/responses`

OpenAI Responses API (March 2025 format).

**Request Schema:**
```json
{
  "model": "openai/gpt-oss-120b",
  "input": "Tell me about AI",
  "instructions": "You are a helpful assistant",
  "tools": null,
  "previous_response_id": null,
  "max_output_tokens": 1000,
  "temperature": 1.0,
  "top_p": 1.0,
  "stream": false,
  "store": false,
  "metadata": {},
  "parallel_tool_calls": true,
  "tool_choice": "auto",
  "response_format": null,
  "background": false
}
```

**Response Schema:**
```json
{
  "id": "resp-abc123",
  "object": "response",
  "created_at": 1234567890,
  "model": "openai/gpt-oss-120b",
  "status": "completed",
  "error": null,
  "incomplete_details": null,
  "instructions": "You are a helpful assistant",
  "max_output_tokens": 1000,
  "metadata": {},
  "previous_response_id": null,
  "temperature": 1.0,
  "top_p": 1.0,
  "parallel_tool_calls": true,
  "tool_choice": "auto",
  "tools": [],
  "output": [
    {
      "type": "message",
      "id": "msg-abc123",
      "role": "assistant",
      "status": "completed",
      "content": [
        {
          "type": "text",
          "text": "Artificial Intelligence..."
        }
      ]
    }
  ],
  "usage": {
    "input_tokens": 10,
    "output_tokens": 50,
    "total_tokens": 60
  }
}
```

**Example curl:**
```bash
curl http://localhost:8000/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "model": "openai/gpt-oss-120b",
    "input": "What is machine learning?",
    "instructions": "Be concise"
  }'
```

**Example Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/v1/responses",
    headers={"Authorization": "Bearer sk-fakeai-1234567890abcdef"},
    json={
        "model": "openai/gpt-oss-120b",
        "input": "Explain neural networks",
        "max_output_tokens": 200
    }
)

data = response.json()
print(f"Status: {data['status']}")
print(f"Output: {data['output'][0]['content'][0]['text']}")
```

---

## Rankings API (NVIDIA NIM)

### Create Ranking

**Endpoint:** `POST /v1/ranking`

NVIDIA NIM-compatible ranking/reranking endpoint.

**Request Schema:**
```json
{
  "model": "nvidia/nv-rerankqa-mistral-4b-v3",
  "query": {
    "text": "What is machine learning?"
  },
  "passages": [
    {"text": "Machine learning is a subset of AI..."},
    {"text": "Deep learning uses neural networks..."},
    {"text": "AI can solve complex problems..."}
  ],
  "truncate": "NONE"
}
```

**Response Schema:**
```json
{
  "rankings": [
    {"index": 0, "logit": 8.5},
    {"index": 2, "logit": 6.2},
    {"index": 1, "logit": 4.8}
  ]
}
```

**Example curl:**
```bash
curl http://localhost:8000/v1/ranking \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-fakeai-1234567890abcdef" \
  -d '{
    "model": "nvidia/nv-rerankqa-mistral-4b-v3",
    "query": {"text": "best programming language"},
    "passages": [
      {"text": "Python is versatile"},
      {"text": "JavaScript runs in browsers"},
      {"text": "Rust is memory safe"}
    ]
  }'
```

**Example Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/v1/ranking",
    headers={"Authorization": "Bearer sk-fakeai-1234567890abcdef"},
    json={
        "model": "nvidia/nv-rerankqa-mistral-4b-v3",
        "query": {"text": "machine learning frameworks"},
        "passages": [
            {"text": "TensorFlow is developed by Google"},
            {"text": "PyTorch is popular in research"},
            {"text": "Scikit-learn is for classical ML"}
        ]
    }
)

rankings = response.json()["rankings"]
for rank in rankings:
    print(f"Passage {rank['index']}: score {rank['logit']:.2f}")
```

---

## Health Check

### Health Check

**Endpoint:** `GET /health`

Returns server health status (no authentication required).

**Response Schema:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-04T12:00:00.000000"
}
```

**Example curl:**
```bash
curl http://localhost:8000/health
```

---

## Metrics

### Get Metrics

**Endpoint:** `GET /metrics`

Returns server metrics (no authentication required).

**Response Schema:**
```json
{
  "requests": {
    "/v1/chat/completions": 42,
    "/v1/embeddings": 15
  },
  "response_times": {
    "/v1/chat/completions": [0.5, 0.6, 0.7],
    "/v1/embeddings": [0.2, 0.3]
  },
  "errors": {
    "/v1/chat/completions": 1
  },
  "tokens_generated": {
    "/v1/chat/completions": 5000
  }
}
```

**Example curl:**
```bash
curl http://localhost:8000/metrics
```

**Example Python:**
```python
import requests

metrics = requests.get("http://localhost:8000/metrics").json()
print(f"Total requests: {sum(metrics['requests'].values())}")
```
