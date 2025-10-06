# Reasoning Content Support (GPT-OSS & O1 Models)

FakeAI fully supports reasoning content like OpenAI's new open-source gpt-oss models and legacy deepseek-ai/DeepSeek-R1 models.

## Overview

Reasoning models include a special `reasoning_content` field that shows the model's internal thinking process before generating the final answer. This feature allows users to see how the model reasons through a problem using chain-of-thought processing.

## Supported Models

### GPT-OSS Models (Open Source - Apache 2.0, Released Aug 2025)

**Primary Models:**
- `gpt-oss-120b` - 117B parameters (5.1B active), runs on single 80GB GPU
- `gpt-oss-20b` - 21B parameters (3.6B active), optimized for low latency, runs on 16GB

**Features:**
- Open-weight models under Apache 2.0 license
- Mixture-of-experts (MoE) architecture
- Configurable reasoning effort
- Full chain-of-thought reasoning
- Agentic capabilities (function calling, web browsing, Python execution)
- MXFP4 quantization support

### O1 Models (Legacy)

- `deepseek-ai/DeepSeek-R1` - Full deepseek-ai/DeepSeek-R1 model
- `deepseek-ai/DeepSeek-R1` - Preview version
- `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` - Lightweight version

### Auto-Detection

Any model whose ID starts with `gpt-oss`, `deepseek-ai/DeepSeek-R1`, or contains "reasoning" will automatically generate reasoning content.

## API Changes

### Non-Streaming Response

**Request:**
```json
{
  "model": "gpt-oss-20b",
  "messages": [
    {"role": "user", "content": "What is 2+2?"}
  ]
}
```

**Response:**
```json
{
  "id": "chatcmpl-...",
  "model": "gpt-oss-20b",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "2+2 equals 4.",
        "reasoning_content": "Let me think about this step by step. The user asked about 'What is 2+2?'. First, I need to understand the key concepts involved..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 5,
    "completion_tokens": 97,
    "total_tokens": 102,
    "completion_tokens_details": {
      "reasoning_tokens": 49,
      "audio_tokens": 0
    }
  }
}
```

### Streaming Response

In streaming mode, reasoning tokens come **first**, followed by regular content tokens.

**Chunk Sequence:**
1. Role chunk: `{"delta": {"role": "assistant"}}`
2. Reasoning chunks: `{"delta": {"reasoning_content": "Let"}}`
3. Reasoning chunks: `{"delta": {"reasoning_content": " me"}}`
4. ... more reasoning chunks ...
5. Content chunks: `{"delta": {"content": "2+2"}}`
6. Content chunks: `{"delta": {"content": " equals"}}`
7. ... more content chunks ...
8. Final chunk: `{"delta": {}, "finish_reason": "stop"}`

## Schema Changes

### Message Model

Added optional `reasoning_content` field:

```python
class Message(BaseModel):
    role: Role
    content: str | list[ContentPart] | None = None
    reasoning_content: str | None = None  # NEW
    # ... other fields
```

### Delta Model (Streaming)

Added optional `reasoning_content` field:

```python
class Delta(BaseModel):
    role: Role | None = None
    content: str | None = None
    reasoning_content: str | None = None  # NEW
    # ... other fields
```

### CompletionTokensDetails

Already included `reasoning_tokens` field:

```python
class CompletionTokensDetails(BaseModel):
    reasoning_tokens: int = 0
    audio_tokens: int = 0
    # ... other fields
```

## Implementation Details

### Service Layer Changes

**`_is_reasoning_model(model_id: str) -> bool`**
- Checks if a model supports reasoning content
- Returns `True` for models starting with "deepseek-ai/DeepSeek-R1" or containing "reasoning"

**`_generate_simulated_reasoning(messages, max_tokens) -> str`**
- Generates simulated reasoning content
- Creates realistic step-by-step thinking text
- Takes 0.1-0.3 seconds to simulate reasoning time

**Token Counting:**
- Reasoning tokens are counted separately
- Total completion tokens = content tokens + reasoning tokens
- Reported in `completion_tokens_details.reasoning_tokens`

**Streaming:**
- Reasoning tokens streamed first as `reasoning_content` chunks
- Regular content tokens follow as `content` chunks
- Each token includes timing information

## Examples

### Python (Non-Streaming)

```python
from fakeai import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import ChatCompletionRequest, Message, Role

config = AppConfig(response_delay=0.0)
service = FakeAIService(config)

request = ChatCompletionRequest(
    model="gpt-oss-120b",
    messages=[Message(role=Role.USER, content="Solve this problem")],
)

response = await service.create_chat_completion(request)

print(f"Reasoning: {response.choices[0].message.reasoning_content}")
print(f"Answer: {response.choices[0].message.content}")
print(f"Reasoning tokens: {response.usage.completion_tokens_details.reasoning_tokens}")
```

### Python (Streaming)

```python
request = ChatCompletionRequest(
    model="gpt-oss-20b",
    messages=[Message(role=Role.USER, content="Explain AI")],
    stream=True,
)

reasoning_parts = []
content_parts = []

async for chunk in service.create_chat_completion_stream(request):
    if chunk.choices and chunk.choices[0].delta:
        delta = chunk.choices[0].delta

        if delta.reasoning_content:
            reasoning_parts.append(delta.reasoning_content)
            print(f"[REASONING] {delta.reasoning_content}", end="")

        if delta.content:
            content_parts.append(delta.content)
            print(f"[CONTENT] {delta.content}", end="")

reasoning = "".join(reasoning_parts)
content = "".join(content_parts)
```

### cURL (Non-Streaming)

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss-120b",
    "messages": [{"role": "user", "content": "What is AI?"}]
  }' | jq '.choices[0].message | {content, reasoning_content}'
```

### cURL (Streaming)

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss-20b",
    "messages": [{"role": "user", "content": "Explain quantum computing"}],
    "stream": true
  }'
```

## Testing

Run the comprehensive test example:

```bash
python examples/test_reasoning_o1.py
```

Or use the curl test script:

```bash
./examples/test_reasoning_curl.sh
```

## Regular Models vs Reasoning Models

**Reasoning Models (gpt-oss, deepseek-ai/DeepSeek-R1):**
- Include `reasoning_content` field with chain-of-thought
- Have `reasoning_tokens` > 0 in usage details
- Show internal thinking process

**Regular Models (openai/gpt-oss-120b, meta-llama/Llama-3.1-8B-Instruct, etc.):**
- Do **NOT** generate reasoning content
- `reasoning_content` field will be `None`
- `reasoning_tokens` will be `0`
- Only regular `content` is generated

## Compatibility

This implementation is fully compatible with:
- OpenAI Python SDK
- OpenAI API format
- All existing FakeAI features
- Backward compatible (reasoning fields are optional)

## Token Accounting

For reasoning models (gpt-oss and deepseek-ai/DeepSeek-R1):
- `prompt_tokens`: Input message tokens
- `completion_tokens`: Reasoning tokens + content tokens (total)
- `completion_tokens_details.reasoning_tokens`: Just the reasoning tokens
- Content tokens = `completion_tokens - reasoning_tokens`

Example:
```
prompt_tokens: 10
completion_tokens: 150  (total)
reasoning_tokens: 50
content_tokens: 100  (calculated: 150 - 50)
```

## Performance

Reasoning generation adds minimal overhead:
- ~0.1-0.3s delay for reasoning generation
- Token-by-token streaming for realistic behavior
- Proper timing metrics for both reasoning and content

## Future Enhancements

Potential improvements:
- Configurable reasoning depth
- Different reasoning templates per task type
- Chain-of-thought formatting options
- Support for custom reasoning models
