# Context Validator Module

A comprehensive context length validation module for FakeAI that ensures prompt + max_tokens doesn't exceed model context windows, with full OpenAI API compatibility.

## Quick Start

```python
from fakeai.context_validator import validate_context_length, create_context_length_error
from fastapi import HTTPException

# Validate request
is_valid, error_message = validate_context_length(
    model="gpt-4",
    prompt_tokens=4000,
    max_tokens=2000,
)

if not is_valid:
    error_response = create_context_length_error(error_message)
    raise HTTPException(status_code=400, detail=error_response)
```

## Features

-  **17 Model Support** - GPT, Claude, LLaMA, DeepSeek, Mistral, Gemini, and more
-  **Multi-Modal** - Validates text, image, audio, and video tokens separately
-  **Fine-Tuned Models** - Automatic base model detection (ft:base:org::id)
-  **OpenAI Compatible** - Exact error format matching OpenAI API
-  **Type Safe** - Full Python 3.10+ type hints
-  **Well Tested** - 33 tests, 100% pass rate
-  **Fast** - O(1) lookups, minimal overhead
-  **Zero Dependencies** - Pure Python

## Installation

Already included in FakeAI. No additional installation needed.

```python
from fakeai.context_validator import (
    validate_context_length,
    get_model_context_window,
    calculate_remaining_budget,
    create_context_length_error,
)
```

## API Reference

### validate_context_length()

Validates that prompt + max_tokens doesn't exceed model context window.

```python
def validate_context_length(
    model: str,
    prompt_tokens: int,
    max_tokens: int | None,
    image_tokens: int = 0,
    audio_tokens: int = 0,
    video_tokens: int = 0
) -> tuple[bool, str | None]:
    """
    Returns (is_valid, error_message).
    error_message is None if valid.
    """
```

**Example:**

```python
is_valid, error = validate_context_length(
    model="gpt-4",
    prompt_tokens=4000,
    max_tokens=2000,
    image_tokens=1000,
)

if not is_valid:
    print(f"Error: {error}")
```

### get_model_context_window()

Get context window size for a model.

```python
def get_model_context_window(model: str) -> int:
    """Get context window for model."""
```

**Example:**

```python
window = get_model_context_window("gpt-4")  # Returns: 8192
window = get_model_context_window("meta-llama/Llama-3.1-70B-Instruct")  # Returns: 131072
window = get_model_context_window("ft:gpt-oss-120b:org::id")  # Returns: 128000
```

### calculate_remaining_budget()

Calculate how many tokens can be generated.

```python
def calculate_remaining_budget(
    model: str,
    prompt_tokens: int,
    reserved_tokens: int = 1000
) -> int:
    """Calculate remaining token budget."""
```

**Example:**

```python
remaining = calculate_remaining_budget(
    model="gpt-4",
    prompt_tokens=5000,
    reserved_tokens=1000,
)
# Returns: 2192 (8192 - 5000 - 1000)
```

### create_context_length_error()

Create OpenAI-compatible error response.

```python
def create_context_length_error(error_message: str) -> dict[str, Any]:
    """Create error response dict."""
```

**Example:**

```python
error_response = create_context_length_error(error_message)
# Returns:
# {
#   "error": {
#     "message": "...",
#     "type": "invalid_request_error",
#     "param": "messages",
#     "code": "context_length_exceeded"
#   }
# }
```

## Supported Models

| Model | Context Window |
|-------|---------------|
| gpt-4 | 8,192 |
| gpt-4-32k | 32,768 |
| gpt-4-turbo | 128,000 |
| gpt-oss-120b | 128,000 |
| gpt-oss-20b | 32,768 |
| gpt-3.5-turbo | 16,385 |
| gpt-3.5-turbo-16k | 16,385 |
| claude-3-opus | 200,000 |
| claude-3-sonnet | 200,000 |
| gemini-pro | 32,768 |
| meta-llama/Llama-3.1-8B-Instruct | 131,072 |
| meta-llama/Llama-3.1-70B-Instruct | 131,072 |
| meta-llama/Llama-3.1-405B-Instruct | 131,072 |
| deepseek-ai/DeepSeek-R1 | 64,000 |
| mistral-7b | 32,768 |
| mixtral-8x7b | 32,768 |
| **default** (unknown) | 8,192 |

## Usage Examples

### Basic Validation

```python
from fakeai.context_validator import validate_context_length

is_valid, error = validate_context_length(
    model="gpt-4",
    prompt_tokens=4000,
    max_tokens=2000,
)

if is_valid:
    print(" Request is valid")
else:
    print(f" {error}")
```

### Multi-Modal Content

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

### Fine-Tuned Models

```python
# Automatically extracts base model context window
window = get_model_context_window("ft:gpt-oss-120b:my-org::abc123")
# Returns: 128,000 (from base model gpt-oss-120b)
```

### Calculate Remaining Budget

```python
from fakeai.context_validator import calculate_remaining_budget

remaining = calculate_remaining_budget(
    model="gpt-4-turbo",
    prompt_tokens=50000,
    reserved_tokens=1000,
)
print(f"Can generate up to {remaining:,} tokens")
# Output: Can generate up to 77,000 tokens
```

### Integration with FastAPI

```python
from fakeai.context_validator import validate_context_length, create_context_length_error
from fastapi import HTTPException

async def create_chat_completion(request):
    # Calculate tokens
    prompt_tokens = calculate_token_count(prompt_text)

    # Validate
    is_valid, error_message = validate_context_length(
        model=request.model,
        prompt_tokens=prompt_tokens,
        max_tokens=request.max_tokens,
    )

    if not is_valid:
        error_response = create_context_length_error(error_message)
        raise HTTPException(status_code=400, detail=error_response)

    # Continue with request...
```

## Integration

To integrate into FakeAI:

1. Import the validator:
```python
from fakeai.context_validator import validate_context_length, create_context_length_error
```

2. Add validation after calculating tokens:
```python
is_valid, error_message = validate_context_length(
    model=request.model,
    prompt_tokens=prompt_tokens,
    max_tokens=request.max_tokens,
    image_tokens=image_tokens,
    audio_tokens=audio_tokens,
    video_tokens=video_tokens,
)

if not is_valid:
    from fastapi import HTTPException
    error_response = create_context_length_error(error_message)
    raise HTTPException(status_code=400, detail=error_response)
```

See `CONTEXT_VALIDATOR_INTEGRATION.md` for detailed integration instructions.

## Error Response Format

Matches OpenAI API exactly:

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

## Testing

Run the test suite:

```bash
python -m pytest tests/test_context_validator.py -v
```

Run examples:

```bash
python examples/context_validation_example.py
python examples/integration_snippet.py
```

Run verification:

```bash
python verify_context_validator.py
```

## Test Coverage

- **33 tests** covering all functionality
- **100% pass rate**
- **0.02s execution time**

Test categories:
- Model context window lookup (5 tests)
- Context length validation (13 tests)
- Remaining budget calculation (7 tests)
- Error response creation (2 tests)
- Edge cases (6 tests)

## Documentation

- **Quick Reference:** `CONTEXT_VALIDATOR_QUICKREF.md` - Copy-paste snippets
- **Integration Guide:** `CONTEXT_VALIDATOR_INTEGRATION.md` - Step-by-step integration
- **Summary:** `CONTEXT_VALIDATOR_SUMMARY.md` - High-level overview
- **Deliverables:** `DELIVERABLES.md` - Complete feature checklist

## Design Principles

Following FakeAI project standards:

- **Schema-first** - OpenAI-compatible error responses
- **Type hints** - Full Python 3.10+ annotations
- **Pythonic** - Simple, clear, DRY code
- **No abstractions** - Direct, practical implementation
- **Well tested** - Comprehensive test coverage
- **Well documented** - Multiple guides and examples

## Performance

- **Fast lookups** - O(1) dictionary operations
- **Minimal overhead** - Simple arithmetic validation
- **No external deps** - Pure Python
- **Thread-safe** - Stateless functions

## Contributing

When adding new models, update `MODEL_CONTEXT_WINDOWS` in `context_validator.py`:

```python
MODEL_CONTEXT_WINDOWS = {
    # ... existing models ...
    "new-model-name": 64000,  # context window in tokens
}
```

Add tests for new models in `tests/test_context_validator.py`.

## License

Apache 2.0 (same as FakeAI)

## Support

- See examples: `examples/context_validation_example.py`
- Read integration guide: `CONTEXT_VALIDATOR_INTEGRATION.md`
- Check quick reference: `CONTEXT_VALIDATOR_QUICKREF.md`
- Run verification: `python verify_context_validator.py`

## Version

**Version:** 1.0.0
**Status:** Production Ready
**Last Updated:** 2025-10-05
