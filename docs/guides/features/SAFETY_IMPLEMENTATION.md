# Safety Refusal Mechanism Implementation

This document describes the safety refusal mechanism implementation for FakeAI.

## Components Implemented

### 1. Configuration (config.py) -  COMPLETE

Added safety configuration fields:
- `enable_safety_features: bool = True` - Enable/disable safety refusal mechanism
- `enable_jailbreak_detection: bool = True` - Enable/disable jailbreak detection
- `prepend_safety_message: bool = False` - Prepend safety guidelines as system message

### 2. Safety Patterns and Methods (fakeai_service.py) -  COMPLETE

Added to `FakeAIService` class:

**Harmful Content Patterns:**
```python
HARMFUL_PATTERNS = {
    "violence": ["how to kill", "how to murder", "make a bomb", ...],
    "illegal": ["how to hack", "how to steal", "how to rob", ...],
    "self_harm": ["how to commit suicide", "ways to kill myself", ...],
    "sexual_minors": ["child abuse", "child exploitation", ...],
    "hate": ["hate speech against", "genocide", "ethnic cleansing", ...],
    "harassment": ["doxx", "doxing", "swat", "threaten to kill", ...],
}
```

**Jailbreak Detection Patterns:**
```python
JAILBREAK_PATTERNS = [
    "ignore previous instructions",
    "forget your training",
    "you are now",
    "dan mode",
    "developer mode",
    "jailbreak mode",
    "do anything now",
    "grandma exploit",
    ...
]
```

**Safety System Message:**
```python
SAFETY_SYSTEM_MESSAGE = (
    "You are a helpful, harmless, and honest AI assistant. "
    "You will not provide information that could be used to harm people, "
    "break laws, or violate ethical guidelines. "
    "You will refuse requests for illegal activities, violence, self-harm, "
    "child exploitation, hate speech, or harassment."
)
```

**Methods:**

1. `should_refuse_request(messages: list[Message]) -> tuple[bool, str | None]`
   - Checks if request contains harmful content
   - Returns (should_refuse: bool, refusal_message: str | None)
   - Handles both string and multi-modal content
   - Uses DRY extract_text_content pattern from CLAUDE.md

2. `is_jailbreak_attempt(messages: list[Message]) -> bool`
   - Detects prompt injection/jailbreak attempts
   - Returns True if jailbreak detected, False otherwise
   - Logs warnings when jailbreaks are detected

3. `_prepend_safety_message(messages: list[Message]) -> list[Message]`
   - Prepends safety guidelines as system message
   - Only if no system message exists
   - Only if `prepend_safety_message=True` in config

### 3. Integration Points -   NEEDS MANUAL INTEGRATION

Due to file linter conflicts, the following integration needs to be added manually to the `create_chat_completion` and `create_chat_completion_stream` methods in `fakeai_service.py`:

#### For `create_chat_completion` (line ~1384):

Add after `self._ensure_model_exists(request.model)`:

```python
        # Prepend safety message if configured
        request.messages = self._prepend_safety_message(request.messages)

        # Check for harmful content and jailbreak attempts
        should_refuse, refusal_message = self.should_refuse_request(request.messages)
        is_jailbreak = self.is_jailbreak_attempt(request.messages)

        # Handle refusals
        if should_refuse or is_jailbreak:
            if is_jailbreak and not should_refuse:
                refusal_message = (
                    "I cannot assist with requests that attempt to bypass safety guidelines "
                    "or manipulate my behavior. Please rephrase your request appropriately."
                )

            # Return response with refusal
            return ChatCompletionResponse(
                id=f"chatcmpl-{uuid.uuid4().hex}",
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatCompletionChoice(
                        index=i,
                        message=Message(
                            role=Role.ASSISTANT,
                            content=None,
                            refusal=refusal_message,
                        ),
                        finish_reason="stop",
                    )
                    for i in range(request.n or 1)
                ],
                usage=Usage(
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                ),
                system_fingerprint="fp_" + uuid.uuid4().hex[:16],
            )
```

#### For `create_chat_completion_stream` (line ~1578):

Add after `self._ensure_model_exists(request.model)`:

```python
        # Prepend safety message if configured
        request.messages = self._prepend_safety_message(request.messages)

        # Check for harmful content and jailbreak attempts
        should_refuse, refusal_message = self.should_refuse_request(request.messages)
        is_jailbreak = self.is_jailbreak_attempt(request.messages)

        # Handle refusals in streaming
        if should_refuse or is_jailbreak:
            if is_jailbreak and not should_refuse:
                refusal_message = (
                    "I cannot assist with requests that attempt to bypass safety guidelines "
                    "or manipulate my behavior. Please rephrase your request appropriately."
                )

            stream_id = f"chatcmpl-{uuid.uuid4().hex}"
            system_fingerprint = "fp_" + uuid.uuid4().hex[:16]

            # First chunk with role
            yield ChatCompletionChunk(
                id=stream_id,
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatCompletionChunkChoice(
                        index=i,
                        delta=Delta(role=Role.ASSISTANT),
                        finish_reason=None,
                    )
                    for i in range(request.n or 1)
                ],
                system_fingerprint=system_fingerprint,
            )

            # Chunk with refusal
            yield ChatCompletionChunk(
                id=stream_id,
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatCompletionChunkChoice(
                        index=i,
                        delta=Delta(refusal=refusal_message),
                        finish_reason=None,
                    )
                    for i in range(request.n or 1)
                ],
                system_fingerprint=system_fingerprint,
            )

            # Final chunk
            yield ChatCompletionChunk(
                id=stream_id,
                created=int(time.time()),
                model=request.model,
                choices=[
                    ChatCompletionChunkChoice(
                        index=i,
                        delta=Delta(),
                        finish_reason="stop",
                    )
                    for i in range(request.n or 1)
                ],
                system_fingerprint=system_fingerprint,
            )
            return
```

### 4. Tests (tests/test_safety.py) -  COMPLETE

Comprehensive test suite created covering:
- Violent content refusal
- Illegal activity refusal
- Self-harm content refusal (with mental health message)
- Child exploitation refusal
- Hate speech refusal
- Harassment content refusal
- Jailbreak detection (multiple patterns)
- Safe content passes through
- Safety features can be disabled
- Refusal field format validation
- Multimodal content safety
- Safety message prepending
- Streaming refusals
- Multiple choices (n > 1) refusals

## Usage Examples

### Enable Safety Features

```python
config = AppConfig(
    enable_safety_features=True,
    enable_jailbreak_detection=True,
    prepend_safety_message=False,  # Optional
)
service = FakeAIService(config)
```

### Environment Variables

```bash
export FAKEAI_ENABLE_SAFETY_FEATURES=true
export FAKEAI_ENABLE_JAILBREAK_DETECTION=true
export FAKEAI_PREPEND_SAFETY_MESSAGE=false
```

### Disable for Testing

```python
config = AppConfig(
    enable_safety_features=False,
    enable_jailbreak_detection=False,
)
```

## Response Format

When content is refused, the response looks like:

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
        "content": null,
        "refusal": "I cannot provide assistance with requests related to violence. This type of content could cause harm and violates ethical guidelines..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  }
}
```

## Testing

Run tests:

```bash
pytest tests/test_safety.py -v
```

Expected output: All tests should pass once integration is complete.

## Next Steps

1. **Manual Integration**: Add the safety check code to `create_chat_completion` and `create_chat_completion_stream` methods as shown above
2. **Run Tests**: Execute `pytest tests/test_safety.py -v` to verify implementation
3. **Documentation**: Update README.md with safety features documentation
4. **Examples**: Create example scripts demonstrating safety features

## Design Decisions

### Why Simple Pattern Matching?

- **Good Enough**: For a testing/simulation server, simple keyword matching is sufficient
- **Fast**: No ML models or complex analysis needed
- **Maintainable**: Easy to add/remove patterns
- **Transparent**: Clear what triggers refusals

### Why Configurable?

- **Testing Flexibility**: Developers can disable for certain test scenarios
- **Development**: Can test edge cases without safety blocks
- **Production Ready**: Can be enabled by default in production deployments

### Why DRY Content Extraction?

- Follows CLAUDE.md principles
- Handles multi-modal content (text + images)
- Handles both dict and Pydantic model instances
- Reusable pattern used throughout codebase

### Why Both Harmful and Jailbreak?

- **Harmful**: Detects actual harmful content requests
- **Jailbreak**: Detects attempts to bypass safety
- **Combined**: Comprehensive protection

## Compliance

This implementation simulates OpenAI's refusal mechanism:
- Uses `refusal` field in Message model (OpenAI spec)
- Sets `content` to `null` when refusing
- Returns `finish_reason="stop"`
- Works in both streaming and non-streaming modes

## Limitations

This is a simulation, not actual content moderation:
- Pattern matching can have false positives/negatives
- No ML-based detection
- English-focused patterns
- No context understanding

For production use cases requiring real content moderation, use actual moderation APIs.
