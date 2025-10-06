# Validation Framework

A comprehensive, composable validation pipeline framework for FakeAI API requests.

## Overview

The validation framework provides a flexible, extensible system for validating API requests through a pipeline of validators. It supports both synchronous and asynchronous validation, fail-fast and collect-all error modes, and includes pre-configured pipelines for all FakeAI endpoints.

## Architecture

### Core Components

```
validation/
 base.py              # Base classes and protocols
 pipeline.py          # Pipeline orchestration
 factory.py           # Pre-configured pipelines
 validators/          # Individual validators
     schema.py        # Pydantic schema validation
     context_length.py    # Context window validation
     parameters.py    # Parameter range validation
     rate_limit.py    # Rate limiting
     auth.py          # Authentication
     content_policy.py    # Content policy compliance
     multimodal.py    # Multi-modal content validation
     model_availability.py    # Model existence check
```

## Quick Start

### Using Pre-configured Pipelines

```python
from fakeai.validation import create_validators_for_endpoint

# Create a chat completion validation pipeline
pipeline = create_validators_for_endpoint(
    "chat",
    require_auth=True,
    check_rate_limits=True,
    check_content_policy=True,
    fail_fast=True
)

# Validate a request
request = {
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
}

context = {
    "api_key": "test-key",
    "model": "gpt-4",
    "prompt_tokens": 10,
    "max_tokens": 100,
}

result = pipeline.validate(request, context)

if result.valid:
    print("Request is valid!")
else:
    error_response = result.to_error_response()
    print(error_response)
```

### Building Custom Pipelines

```python
from fakeai.validation import ValidationPipeline
from fakeai.validation.validators import (
    SchemaValidator,
    ParameterValidator,
    ContextLengthValidator,
)

# Create custom pipeline
pipeline = ValidationPipeline(fail_fast=True, name="CustomPipeline")
pipeline.add_validator(SchemaValidator(schema=MyRequestSchema))
pipeline.add_validator(ParameterValidator())
pipeline.add_validator(ContextLengthValidator())

# Validate
result = pipeline.validate(request, context)
```

## Key Features

### 1. Composable Validators

Each validator is independent and can be composed into pipelines:

```python
from fakeai.validation import ValidationPipeline
from fakeai.validation.validators import *

pipeline = ValidationPipeline()
pipeline.add_validators([
    SchemaValidator(schema=MySchema),
    AuthValidator(require_api_key=True),
    ParameterValidator(),
    ContextLengthValidator(),
    RateLimitValidator(),
])
```

### 2. Fail-Fast or Collect-All

Control error handling behavior:

```python
# Stop at first error (fail-fast)
pipeline = ValidationPipeline(fail_fast=True)

# Collect all errors
pipeline = ValidationPipeline(fail_fast=False)
```

### 3. Async Support

Validators can be synchronous or asynchronous:

```python
# Async validation
result = await pipeline.validate_async(request, context)

# Sync validation (will raise if pipeline has async validators)
result = pipeline.validate(request, context)
```

### 4. Parallel Execution

For independent validators, run in parallel:

```python
from fakeai.validation.pipeline import ParallelValidationPipeline

pipeline = ParallelValidationPipeline()
pipeline.add_validator(AsyncValidator1())
pipeline.add_validator(AsyncValidator2())

# Runs all validators in parallel
result = await pipeline.validate_async(request, context)
```

### 5. Rich Error Information

Validation results include detailed error and warning information:

```python
result = pipeline.validate(request, context)

# Check validity
if not result.valid:
    # Get all errors
    for error in result.errors:
        print(f"{error.message} [{error.code}] (param: {error.param})")

    # Get warnings (don't affect validity)
    for warning in result.warnings:
        print(f"Warning: {warning.message}")

    # Convert to OpenAI-compatible error response
    error_response = result.to_error_response()
```

## Available Validators

### SchemaValidator

Validates request structure using Pydantic models:

```python
from fakeai.validation.validators import SchemaValidator
from pydantic import BaseModel

class MyRequest(BaseModel):
    model: str
    temperature: float = 1.0

validator = SchemaValidator(schema=MyRequest)
```

### ContextLengthValidator

Ensures requests don't exceed model context windows:

```python
from fakeai.validation.validators import ContextLengthValidator

validator = ContextLengthValidator()

# Requires context with: model, prompt_tokens, max_tokens
result = validator.validate(request, context={
    "model": "gpt-4",
    "prompt_tokens": 100,
    "max_tokens": 500,
    "image_tokens": 85,  # Optional
    "audio_tokens": 0,   # Optional
    "video_tokens": 0,   # Optional
})
```

### ParameterValidator

Validates parameter values and ranges:

```python
from fakeai.validation.validators import ParameterValidator

validator = ParameterValidator()

# Validates: temperature, top_p, frequency_penalty, presence_penalty,
# max_tokens, n, best_of, logprobs, top_logprobs, seed, timeout
```

### RateLimitValidator

Enforces rate limits using the rate limiter:

```python
from fakeai.validation.validators import RateLimitValidator

validator = RateLimitValidator()

# Requires context with: api_key, tokens
result = validator.validate(request, context={
    "api_key": "test-key",
    "tokens": 100,
})
```

### AuthValidator

Validates API authentication:

```python
from fakeai.validation.validators import AuthValidator

# Require any API key
validator = AuthValidator(require_api_key=True)

# Require specific API keys
validator = AuthValidator(
    valid_api_keys=["key1", "key2", "key3"],
    require_api_key=True
)
```

### ContentPolicyValidator

Checks content against usage policies:

```python
from fakeai.validation.validators import ContentPolicyValidator

# Non-strict mode (warnings only)
validator = ContentPolicyValidator(strict_mode=False)

# Strict mode (errors)
validator = ContentPolicyValidator(strict_mode=True)
```

### MultiModalValidator

Validates multi-modal content (images, audio, video):

```python
from fakeai.validation.validators import MultiModalValidator

validator = MultiModalValidator()

# Checks that model supports requested modalities
result = validator.validate(request, context={
    "model": "gpt-4-vision-preview",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {"type": "image_url", "image_url": {"url": "..."}},
            ]
        }
    ]
})
```

### ModelAvailabilityValidator

Validates model existence and format:

```python
from fakeai.validation.validators import ModelAvailabilityValidator

# Allow any model (auto-create)
validator = ModelAvailabilityValidator(allow_auto_create=True)

# Restrict to specific models
validator = ModelAvailabilityValidator(
    available_models={"gpt-4", "gpt-3.5-turbo"},
    allow_auto_create=False
)
```

## Pre-configured Pipelines

The factory module provides pre-configured pipelines for common endpoints:

### Chat Completions

```python
from fakeai.validation import create_chat_validators

pipeline = create_chat_validators(
    schema=ChatCompletionRequest,  # Optional
    require_auth=True,
    check_rate_limits=True,
    check_content_policy=False,
    fail_fast=True
)
```

### Completions (Legacy)

```python
from fakeai.validation import create_completion_validators

pipeline = create_completion_validators(...)
```

### Embeddings

```python
from fakeai.validation import create_embedding_validators

pipeline = create_embedding_validators(...)
```

### Image Generation

```python
from fakeai.validation import create_image_validators

pipeline = create_image_validators(...)
```

### Audio (Speech, Transcription)

```python
from fakeai.validation import create_audio_validators

pipeline = create_audio_validators(...)
```

### Moderation

```python
from fakeai.validation import create_moderation_validators

pipeline = create_moderation_validators(...)
```

### Batch Processing

```python
from fakeai.validation import create_batch_validators

pipeline = create_batch_validators(...)
```

### Generic Endpoint Factory

```python
from fakeai.validation import create_validators_for_endpoint

# Automatically selects the right pipeline
pipeline = create_validators_for_endpoint(
    endpoint="chat",  # or "completion", "embedding", etc.
    schema=MySchema,
    require_auth=True,
    check_rate_limits=True,
    check_content_policy=False,
    fail_fast=True
)
```

## Validation Context

Most validators rely on a context dictionary for additional information:

```python
context = {
    # Authentication
    "api_key": "test-key",

    # Model information
    "model": "gpt-4",

    # Token counts
    "prompt_tokens": 100,
    "max_tokens": 500,
    "image_tokens": 85,
    "audio_tokens": 0,
    "video_tokens": 0,
    "tokens": 185,  # Total for rate limiting

    # Content
    "messages": [...],
    "content": "...",
}

result = pipeline.validate(request, context)
```

## Error Response Format

Validation errors are converted to OpenAI-compatible error responses:

```python
result = pipeline.validate(request, context)

if not result.valid:
    error_response = result.to_error_response()
    # {
    #     "error": {
    #         "message": "temperature must be between 0 and 2",
    #         "type": "invalid_request_error",
    #         "code": "invalid_value",
    #         "param": "temperature",
    #         "additional_errors": [...]  # If multiple errors
    #     }
    # }
```

## Testing

The framework includes comprehensive tests (125 tests):

```bash
# Run all validation tests
pytest tests/validation/ -v

# Run specific test file
pytest tests/validation/test_base.py -v
pytest tests/validation/test_pipeline.py -v
pytest tests/validation/test_validators.py -v
pytest tests/validation/test_factory.py -v
pytest tests/validation/test_integration.py -v
```

## Creating Custom Validators

Implement the `Validator` or `AsyncValidator` protocol:

```python
from fakeai.validation.base import ValidationResult

class MyCustomValidator:
    @property
    def name(self) -> str:
        return "MyCustomValidator"

    def validate(self, request, context=None):
        # Perform validation
        if some_condition:
            return ValidationResult.success()
        else:
            return ValidationResult.failure(
                message="Validation failed",
                code="custom_error",
                param="field_name"
            )

# Async validator
class MyAsyncValidator:
    @property
    def name(self) -> str:
        return "MyAsyncValidator"

    async def validate(self, request, context=None):
        # Perform async validation
        result = await some_async_check()
        if result:
            return ValidationResult.success()
        else:
            return ValidationResult.failure(...)
```

## Best Practices

1. **Order Matters**: Place validators in logical order (schema first, rate limit last)
2. **Use Context**: Pass relevant information in context dict
3. **Fail-Fast for APIs**: Use `fail_fast=True` for API endpoints to respond quickly
4. **Collect-All for Testing**: Use `fail_fast=False` for testing to see all issues
5. **Async When Needed**: Use async validators only for I/O operations
6. **Parallel for Independent**: Use `ParallelValidationPipeline` for independent validators
7. **Warnings vs Errors**: Use warnings for non-blocking issues, errors for blocking issues

## Integration Example

Here's a complete example integrating with a FastAPI endpoint:

```python
from fastapi import HTTPException
from fakeai.validation import create_chat_validators
from fakeai.models import ChatCompletionRequest

# Create pipeline once at startup
chat_pipeline = create_chat_validators(
    schema=ChatCompletionRequest,
    require_auth=True,
    check_rate_limits=True,
    check_content_policy=True,
    fail_fast=True
)

@app.post("/v1/chat/completions")
async def create_chat_completion(request: ChatCompletionRequest):
    # Build validation context
    context = {
        "api_key": get_api_key_from_header(),
        "model": request.model,
        "prompt_tokens": calculate_prompt_tokens(request),
        "max_tokens": request.max_tokens,
        "messages": request.messages,
    }

    # Validate
    result = await chat_pipeline.validate_async(request, context)

    if not result.valid:
        error_response = result.to_error_response()
        raise HTTPException(status_code=400, detail=error_response)

    # Process valid request
    return await process_chat_completion(request)
```

## Performance

The validation framework is designed for high performance:

- Minimal overhead per validator (~10μs)
- Fail-fast mode stops at first error
- Parallel execution for independent validators
- No database or network calls (except rate limiter)
- 100 validations complete in < 10ms

## License

SPDX-License-Identifier: Apache-2.0
