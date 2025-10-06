# FakeAI Client SDK - Quick Reference

## Installation

```bash
pip install fakeai
```

## Imports

```python
from fakeai import (
    FakeAIClient,                # Main client class
    temporary_server,            # Context manager
    assert_response_valid,       # Validation
    assert_tokens_in_range,      # Token validation
    assert_cache_hit,            # Cache validation
    assert_moderation_flagged,   # Moderation validation
    assert_streaming_valid,      # Stream validation
    collect_stream_content,      # Utility
    measure_stream_timing,       # Utility
    AppConfig,                   # Configuration
)
```

## Quick Start

```python
# Auto-start server and chat
with FakeAIClient(auto_start=True) as client:
    response = client.chat("Hello!")
    print(response.choices[0].message.content)
```

## FakeAIClient Methods

```python
# Chat
response = client.chat("Hello!", model="openai/gpt-oss-120b", system="You are helpful")

# Streaming
stream = client.stream_chat("Count to 5")
for chunk in stream:
    print(chunk.choices[0].delta.content, end="")

# Embeddings
response = client.embed("Text to embed")
response = client.embed(["Text 1", "Text 2"])  # Batch

# Moderation
result = client.moderate("Check this text")

# Models
models = client.list_models()
model = client.get_model("openai/gpt-oss-120b")
```

## Validation Functions

```python
# Response validation
assert_response_valid(response)

# Token validation
assert_tokens_in_range(
    response.usage,
    min_prompt=5,
    max_prompt=20,
    min_completion=10,
    max_completion=100,
)

# Cache validation
assert_cache_hit(response)

# Moderation validation
assert_moderation_flagged(result, category="violence")

# Streaming validation
assert_streaming_valid(stream)
```

## Utility Functions

```python
# Collect stream content
content = collect_stream_content(stream)

# Measure timing
timing = measure_stream_timing(stream)
print(f"TTFT: {timing['time_to_first_token']*1000:.2f}ms")
print(f"Total: {timing['total_time']:.2f}s")
print(f"Chunks: {timing['chunks_count']}")
print(f"ITL: {timing['avg_inter_token_latency']*1000:.2f}ms")
```

## Context Managers

```python
# Temporary server
with temporary_server() as client:
    response = client.chat("Hello!")

# Custom config
config = AppConfig(response_delay=0.0, enable_audio=True)
with temporary_server(config=config) as client:
    response = client.chat("Hello!")

# FakeAIClient context manager
with FakeAIClient(auto_start=True) as client:
    response = client.chat("Hello!")
```

## Pytest Fixtures

```python
# Basic fixture
def test_chat(fakeai_client):
    response = fakeai_client.chat("Hello!")
    assert_response_valid(response)

# Auth fixture
def test_auth(fakeai_client_with_auth):
    response = fakeai_client_with_auth.chat("Hello!")

# Server info fixture
def test_openai_client(fakeai_running_server):
    from openai import OpenAI
    client = OpenAI(
        api_key="test",
        base_url=fakeai_running_server["url"]
    )
    response = client.chat.completions.create(...)
```

## Configuration

```python
from fakeai import AppConfig

config = AppConfig(
    response_delay=0.0,         # No delay
    random_delay=False,         # Predictable
    require_api_key=False,      # No auth
    enable_audio=True,          # Audio support
    enable_moderation=True,     # Moderation
    enable_kv_cache=True,       # KV cache
    kv_cache_workers=8,         # Workers
)

with FakeAIClient(config=config, auto_start=True) as client:
    # Use client...
    pass
```

## Common Patterns

### Fast Tests

```python
config = AppConfig(response_delay=0.0, random_delay=False)
with FakeAIClient(config=config, auto_start=True) as client:
    response = client.chat("Hello!")  # Very fast
```

### Performance Testing

```python
import time

stream = client.stream_chat("Hello!")
timing = measure_stream_timing(stream)
assert timing["time_to_first_token"] < 0.5  # < 500ms
```

### Batch Processing

```python
with FakeAIClient(auto_start=True) as client:
    for i in range(100):
        response = client.chat(f"Request {i}")
        assert_response_valid(response)
```

### Multiple Models

```python
models = ["meta-llama/Llama-3.1-8B-Instruct", "openai/gpt-oss-120b", "openai/gpt-oss-120b"]
with FakeAIClient(auto_start=True) as client:
    for model in models:
        response = client.chat("Hello!", model=model)
        assert response.model == model
```

### Error Handling

```python
with FakeAIClient(auto_start=True) as client:
    try:
        response = client.chat("Hello!", max_tokens=10)
        assert_response_valid(response)
        assert_tokens_in_range(response.usage, min_prompt=1)
    except AssertionError as e:
        print(f"Validation failed: {e}")
```

## Examples

### Complete Test

```python
def test_complete_workflow(fakeai_client):
    # Chat
    response = fakeai_client.chat("Hello!")
    assert_response_valid(response)
    assert_tokens_in_range(response.usage, min_prompt=1, min_completion=1)

    # Streaming
    stream = fakeai_client.stream_chat("Count to 5")
    assert_streaming_valid(stream)

    # Embeddings
    embed = fakeai_client.embed("Test")
    assert len(embed.data[0].embedding) > 0

    # Models
    models = fakeai_client.list_models()
    assert len(models.data) > 0
```

### Integration Test

```python
def test_integration():
    config = AppConfig(response_delay=0.0)
    with temporary_server(config=config) as client:
        # Test multiple endpoints
        chat = client.chat("Hello!")
        stream = client.stream_chat("Hi!")
        embed = client.embed("Test")
        models = client.list_models()

        # Validate all
        assert_response_valid(chat)
        assert_streaming_valid(stream)
        assert len(embed.data) > 0
        assert len(models.data) > 0
```

## Troubleshooting

### Server won't start
```python
# Increase timeout
client.start_server(timeout=30.0)
```

### Port in use
```python
config = AppConfig(port=8001)
with FakeAIClient(config=config, auto_start=True, port=8001) as client:
    pass
```

### Auth errors
```python
config = AppConfig(require_api_key=True, api_keys=["my-key"])
client = FakeAIClient(config=config, auto_start=True, api_key="my-key")
```

### Slow responses
```python
config = AppConfig(response_delay=0.0)  # Zero delay
```

## Files

- **SDK**: `fakeai/client.py` (560 lines)
- **Examples**: `examples/example_client_sdk.py` (400 lines)
- **Tests**: `tests/test_client_sdk.py` (500 lines)
- **Docs**: `CLIENT_SDK.md` (600 lines)

## Run Examples

```bash
# Simple example
python examples/example_client_simple.py

# Comprehensive example
python examples/example_client_sdk.py

# Run tests
pytest tests/test_client_sdk.py -v
```

## Type Hints

All functions have full type hints for IDE support:

```python
def chat(
    self,
    message: str,
    model: str = "openai/gpt-oss-120b",
    system: str | None = None,
    **kwargs,
) -> ChatCompletion:
    ...
```

## Best Practices

1.  Use `auto_start=True` for tests
2.  Use `response_delay=0.0` for speed
3.  Always validate responses
4.  Use context managers
5.  Use pytest fixtures
6.  Measure performance
7.  Handle errors
8.  Clean up resources

## Links

- Full docs: `CLIENT_SDK.md`
- Summary: `CLIENT_SDK_SUMMARY.md`
- Examples: `examples/example_client_sdk.py`
- Tests: `tests/test_client_sdk.py`
