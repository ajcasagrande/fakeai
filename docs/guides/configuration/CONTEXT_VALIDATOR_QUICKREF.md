# Context Validator Quick Reference

## Basic Usage

```python
from fakeai.context_validator import validate_context_length, create_context_length_error

# Validate context length
is_valid, error = validate_context_length(
    model="gpt-4",
    prompt_tokens=4000,
    max_tokens=2000,
)

if not is_valid:
    # Raise error
    from fastapi import HTTPException
    error_response = create_context_length_error(error)
    raise HTTPException(status_code=400, detail=error_response)
```

## Multi-Modal Support

```python
is_valid, error = validate_context_length(
    model="gpt-4",
    prompt_tokens=3000,
    max_tokens=2000,
    image_tokens=1500,
    audio_tokens=500,
    video_tokens=1000,
)
```

## Get Context Window

```python
from fakeai.context_validator import get_model_context_window

# Get context window size
window = get_model_context_window("gpt-4")  # Returns: 8192
window = get_model_context_window("meta-llama/Llama-3.1-70B-Instruct")  # Returns: 131072
window = get_model_context_window("ft:gpt-oss-120b:org::id")  # Returns: 128000
```

## Calculate Remaining Budget

```python
from fakeai.context_validator import calculate_remaining_budget

# Calculate available tokens
remaining = calculate_remaining_budget(
    model="gpt-4",
    prompt_tokens=5000,
    reserved_tokens=1000,  # Safety buffer
)
# Returns: 2192 (8192 - 5000 - 1000)
```

## Integration Points

### Chat Completions (Non-Streaming)

**Location:** `fakeai_service.py`, line ~1571

```python
# After: prompt_tokens = text_tokens + input_image_tokens + input_video_tokens + input_audio_tokens
is_valid, error_message = validate_context_length(
    model=request.model,
    prompt_tokens=text_tokens,
    max_tokens=request.max_tokens,
    image_tokens=input_image_tokens,
    audio_tokens=input_audio_tokens,
    video_tokens=input_video_tokens,
)

if not is_valid:
    from fastapi import HTTPException
    error_response = create_context_length_error(error_message)
    raise HTTPException(status_code=400, detail=error_response)
```

### Chat Completions (Streaming)

**Location:** `fakeai_service.py`, line ~1817

```python
# Calculate tokens first
text_tokens = calculate_token_count(prompt_text)
input_image_tokens = sum(calculate_message_image_tokens(msg.content, request.model)
                         for msg in request.messages if msg.content)
input_video_tokens = sum(calculate_message_video_tokens(msg.content, request.model)
                         for msg in request.messages if msg.content)
input_audio_tokens, _ = self._process_audio_input(request.messages)

# Validate
is_valid, error_message = validate_context_length(
    model=request.model,
    prompt_tokens=text_tokens,
    max_tokens=request.max_tokens,
    image_tokens=input_image_tokens,
    audio_tokens=input_audio_tokens,
    video_tokens=input_video_tokens,
)

if not is_valid:
    from fastapi import HTTPException
    error_response = create_context_length_error(error_message)
    raise HTTPException(status_code=400, detail=error_response)
```

### Text Completions (Non-Streaming)

**Location:** `fakeai_service.py`, line ~2177

```python
# After: prompt_tokens = calculate_token_count(prompt_text)
is_valid, error_message = validate_context_length(
    model=request.model,
    prompt_tokens=prompt_tokens,
    max_tokens=request.max_tokens,
)

if not is_valid:
    from fastapi import HTTPException
    error_response = create_context_length_error(error_message)
    raise HTTPException(status_code=400, detail=error_response)
```

### Text Completions (Streaming)

**Location:** `fakeai_service.py`, line ~2232

```python
# After: prompt_text = self._process_prompt(request.prompt)
prompt_tokens = calculate_token_count(prompt_text)

is_valid, error_message = validate_context_length(
    model=request.model,
    prompt_tokens=prompt_tokens,
    max_tokens=request.max_tokens,
)

if not is_valid:
    from fastapi import HTTPException
    error_response = create_context_length_error(error_message)
    raise HTTPException(status_code=400, detail=error_response)
```

## Error Response

```json
{
  "error": {
    "message": "This model's maximum context length is 8192 tokens. However, your messages resulted in 9000 tokens (7000 in the messages, 2000 in the completion). Please reduce the length of the messages or completion.",
    "type": "invalid_request_error",
    "param": "messages",
    "code": "context_length_exceeded"
  }
}
```

## Model Context Windows

| Model Family | Models | Context Window |
|--------------|--------|----------------|
| GPT-4 | gpt-4 | 8,192 |
| GPT-4 | gpt-4-32k | 32,768 |
| GPT-4 | gpt-4-turbo | 128,000 |
| GPT-OSS | gpt-oss-120b | 128,000 |
| GPT-OSS | gpt-oss-20b | 32,768 |
| GPT-3.5 | gpt-3.5-turbo, gpt-3.5-turbo-16k | 16,385 |
| Claude | claude-3-opus, claude-3-sonnet | 200,000 |
| LLaMA 3.1 | Llama-3.1-8B/70B/405B-Instruct | 131,072 |
| DeepSeek | deepseek-ai/DeepSeek-R1 | 64,000 |
| Mistral | mistral-7b, mixtral-8x7b | 32,768 |
| Gemini | gemini-pro | 32,768 |
| Default | (unknown models) | 8,192 |

## Special Model Formats

### Fine-Tuned Models

```python
# Format: ft:base_model:org::id
model = "ft:gpt-oss-120b:my-org::abc123"
window = get_model_context_window(model)  # Returns base model window: 128,000
```

### Provider Prefixes

```python
# Both formats work:
get_model_context_window("gpt-oss-120b")           # 128,000
get_model_context_window("openai/gpt-oss-120b")   # 128,000
```

## Testing

```bash
# Run tests
python -m pytest tests/test_context_validator.py -v

# Run examples
python examples/context_validation_example.py
python examples/integration_snippet.py
```

## Files

- **Module:** `/home/anthony/projects/fakeai/fakeai/context_validator.py`
- **Tests:** `/home/anthony/projects/fakeai/tests/test_context_validator.py`
- **Integration Guide:** `/home/anthony/projects/fakeai/CONTEXT_VALIDATOR_INTEGRATION.md`
- **Examples:** `/home/anthony/projects/fakeai/examples/context_validation_example.py`
- **Integration Snippet:** `/home/anthony/projects/fakeai/examples/integration_snippet.py`

## API Reference

```python
def validate_context_length(
    model: str,
    prompt_tokens: int,
    max_tokens: int | None,
    image_tokens: int = 0,
    audio_tokens: int = 0,
    video_tokens: int = 0
) -> tuple[bool, str | None]

def get_model_context_window(model: str) -> int

def calculate_remaining_budget(
    model: str,
    prompt_tokens: int,
    reserved_tokens: int = 1000
) -> int

def create_context_length_error(error_message: str) -> dict[str, Any]
```
