# FakeAI Client SDK

Comprehensive Python client SDK and testing utilities for FakeAI server.

## Overview

The FakeAI Client SDK provides a convenient wrapper around the OpenAI Python client with additional testing utilities, automatic server management, and validation helpers.

## Features

- **FakeAIClient**: OpenAI client wrapper with convenience methods
- **Auto-start/stop server**: Context managers for automatic lifecycle management
- **Testing utilities**: Assertions and validators for responses
- **Pytest fixtures**: Ready-to-use fixtures for testing
- **Timing measurements**: Performance metrics for streaming
- **Type-safe**: Full type hints for IDE support

## Installation

```bash
pip install fakeai
```

## Quick Start

### Basic Usage

```python
from fakeai import FakeAIClient, assert_response_valid

# Auto-start server and test
with FakeAIClient(auto_start=True) as client:
    response = client.chat("Hello, how are you?")
    assert_response_valid(response)
    print(response.choices[0].message.content)
```

### Using with Existing Server

```python
from fakeai import FakeAIClient

# Connect to already-running server
client = FakeAIClient(
    api_key="your-key",
    base_url="http://localhost:8000/v1"
)

response = client.chat("Tell me a joke")
print(response.choices[0].message.content)
```

## FakeAIClient Class

### Initialization

```python
FakeAIClient(
    api_key: str = "test-key",
    base_url: str = "http://localhost:8000/v1",
    config: AppConfig | None = None,
    auto_start: bool = False,
    port: int = 8000,
    host: str = "127.0.0.1",
)
```

**Parameters:**
- `api_key`: API key for authentication
- `base_url`: Server base URL
- `config`: AppConfig for server (if auto_start=True)
- `auto_start`: Whether to automatically start/stop server
- `port`: Port for server (if auto_start=True)
- `host`: Host for server (if auto_start=True)

### Convenience Methods

#### Chat Completion

```python
response = client.chat(
    message="Hello!",
    model="openai/gpt-oss-120b",
    system="You are a helpful assistant.",
    temperature=0.7,
    max_tokens=100,
)
```

#### Streaming Chat

```python
stream = client.stream_chat(
    message="Count from 1 to 10",
    model="meta-llama/Llama-3.1-8B-Instruct",
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

#### Embeddings

```python
# Single text
response = client.embed("Hello world!")
embedding = response.data[0].embedding

# Multiple texts
response = client.embed(["Text 1", "Text 2", "Text 3"])
```

#### Moderation

```python
result = client.moderate("Check this text for violations")
if result.results[0].flagged:
    print("Content was flagged!")
```

#### Model Operations

```python
# List models
models = client.list_models()
for model in models.data:
    print(model.id)

# Get specific model
model = client.get_model("openai/gpt-oss-120b")
print(f"Context window: {model.context_window}")
```

## Testing Utilities

### Response Validation

```python
from fakeai import assert_response_valid

response = client.chat("Hello!")
assert_response_valid(response)  # Validates schema
```

**Checks:**
- Response has valid ID format
- Model and timestamp are present
- Choices array is not empty
- Message has correct role
- Finish reason is set
- Usage tokens are valid

### Token Range Validation

```python
from fakeai import assert_tokens_in_range

assert_tokens_in_range(
    response.usage,
    min_prompt=5,
    max_prompt=20,
    min_completion=10,
    max_completion=100,
)
```

### Cache Hit Validation

```python
from fakeai import assert_cache_hit

response = client.chat("Same prompt as before...")
assert_cache_hit(response)  # Validates cached_tokens > 0
```

### Moderation Validation

```python
from fakeai import assert_moderation_flagged

result = client.moderate("harmful content here")
assert_moderation_flagged(result, category="violence")
```

### Streaming Validation

```python
from fakeai import assert_streaming_valid

stream = client.stream_chat("Hello!")
assert_streaming_valid(stream)  # Validates stream structure
```

**Checks:**
- Stream produces chunks
- Chunks have content
- Stream ends with finish_reason

### Collect Stream Content

```python
from fakeai import collect_stream_content

stream = client.stream_chat("Tell me a story")
full_content = collect_stream_content(stream)
print(full_content)
```

### Measure Stream Timing

```python
from fakeai import measure_stream_timing

stream = client.stream_chat("Count to 10")
timing = measure_stream_timing(stream)

print(f"Time to first token: {timing['time_to_first_token']*1000:.2f}ms")
print(f"Total time: {timing['total_time']:.2f}s")
print(f"Chunks: {timing['chunks_count']}")
print(f"Avg ITL: {timing['avg_inter_token_latency']*1000:.2f}ms")
```

**Returns:**
```python
{
    "time_to_first_token": float,  # Seconds to first content
    "total_time": float,            # Total stream duration
    "chunks_count": int,            # Number of chunks
    "avg_inter_token_latency": float,  # Avg time between chunks
}
```

## Context Managers

### temporary_server

```python
from fakeai import temporary_server, AppConfig

config = AppConfig(
    response_delay=0.0,
    enable_audio=True,
)

with temporary_server(config=config) as client:
    response = client.chat("Hello!")
    print(response.choices[0].message.content)
# Server automatically stops
```

**Parameters:**
- `config`: AppConfig for the server
- `port`: Port to bind to (default: 8000)
- `host`: Host to bind to (default: 127.0.0.1)
- `timeout`: Startup timeout in seconds (default: 10.0)

### FakeAIClient as Context Manager

```python
with FakeAIClient(auto_start=True) as client:
    response = client.chat("Hello!")
    assert_response_valid(response)
# Server automatically stopped
```

## Pytest Fixtures

### fakeai_client

Basic client fixture with auto-started server.

```python
def test_chat(fakeai_client):
    response = fakeai_client.chat("Hello!")
    assert_response_valid(response)
```

### fakeai_client_with_auth

Client fixture with authentication enabled.

```python
def test_authenticated(fakeai_client_with_auth):
    response = fakeai_client_with_auth.chat("Hello!")
    assert_response_valid(response)
```

### fakeai_running_server

Fixture providing server connection info.

```python
def test_with_openai_client(fakeai_running_server):
    from openai import OpenAI

    client = OpenAI(
        api_key="test",
        base_url=fakeai_running_server["url"],
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Hello!"}],
    )

    assert response.choices[0].message.content
```

**Provides:**
```python
{
    "url": "http://127.0.0.1:8000/v1",
    "host": "127.0.0.1",
    "port": 8000,
    "config": AppConfig(...),
    "client": FakeAIClient(...),
}
```

## Custom Configuration

### Zero Delay for Fast Tests

```python
from fakeai import FakeAIClient, AppConfig

config = AppConfig(
    response_delay=0.0,  # No artificial delay
    random_delay=False,  # Predictable timing
)

with FakeAIClient(config=config, auto_start=True) as client:
    response = client.chat("Hello!")
    # Very fast response
```

### With Authentication

```python
config = AppConfig(
    require_api_key=True,
    api_keys=["sk-test-key-1", "sk-test-key-2"],
)

with FakeAIClient(config=config, auto_start=True, api_key="sk-test-key-1") as client:
    response = client.chat("Hello!")
```

### Advanced Features

```python
config = AppConfig(
    response_delay=0.1,
    enable_audio=True,
    enable_moderation=True,
    enable_kv_cache=True,
    kv_cache_workers=8,
    moderation_threshold=0.5,
)

with FakeAIClient(config=config, auto_start=True) as client:
    # All features enabled
    response = client.chat("Hello!")
```

## Examples

### Complete Test Suite

```python
import pytest
from fakeai import (
    FakeAIClient,
    assert_response_valid,
    assert_tokens_in_range,
    assert_streaming_valid,
    collect_stream_content,
    measure_stream_timing,
)


def test_basic_chat(fakeai_client):
    """Test basic chat completion."""
    response = fakeai_client.chat("What is 2+2?")
    assert_response_valid(response)
    assert response.choices[0].message.content


def test_streaming(fakeai_client):
    """Test streaming response."""
    stream = fakeai_client.stream_chat("Count to 5")
    assert_streaming_valid(stream)


def test_token_validation(fakeai_client):
    """Test token usage is within expected range."""
    response = fakeai_client.chat("Short message", max_tokens=20)
    assert_tokens_in_range(
        response.usage,
        min_prompt=2,
        max_prompt=10,
        min_completion=1,
        max_completion=25,
    )


def test_performance(fakeai_client):
    """Test streaming performance metrics."""
    stream = fakeai_client.stream_chat("Hello!")
    timing = measure_stream_timing(stream)

    assert timing["time_to_first_token"] > 0
    assert timing["chunks_count"] > 0
```

### Integration Test

```python
from fakeai import temporary_server, AppConfig


def test_full_workflow():
    """Test complete workflow with custom config."""
    config = AppConfig(
        response_delay=0.0,
        enable_audio=True,
        enable_moderation=True,
    )

    with temporary_server(config=config) as client:
        # Test chat
        chat_response = client.chat("Hello!")
        assert_response_valid(chat_response)

        # Test streaming
        stream = client.stream_chat("Count to 5")
        content = collect_stream_content(stream)
        assert len(content) > 0

        # Test embeddings
        embed_response = client.embed("Test text")
        assert len(embed_response.data[0].embedding) > 0

        # Test moderation
        mod_response = client.moderate("Check this")
        assert len(mod_response.results) > 0

        # Test models
        models = client.list_models()
        assert len(models.data) > 0
```

### Performance Testing

```python
import time
from fakeai import FakeAIClient, AppConfig


def test_throughput():
    """Test request throughput."""
    config = AppConfig(response_delay=0.0, random_delay=False)

    with FakeAIClient(config=config, auto_start=True) as client:
        num_requests = 100
        start = time.time()

        for i in range(num_requests):
            response = client.chat(f"Request {i}")
            assert_response_valid(response)

        elapsed = time.time() - start
        rps = num_requests / elapsed

        print(f"Requests per second: {rps:.2f}")
        assert rps > 10  # Should handle at least 10 RPS
```

### Load Testing

```python
import concurrent.futures
from fakeai import FakeAIClient, AppConfig


def test_concurrent_requests():
    """Test concurrent request handling."""
    config = AppConfig(response_delay=0.1)

    with FakeAIClient(config=config, auto_start=True) as client:
        def make_request(i):
            response = client.chat(f"Request {i}")
            assert_response_valid(response)
            return response

        # Send 50 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(50)]
            results = [f.result() for f in futures]

        assert len(results) == 50
```

## Advanced Usage

### Multiple Servers

```python
from fakeai import FakeAIClient, AppConfig


# Run two servers on different ports
config1 = AppConfig(response_delay=0.0, port=8001)
config2 = AppConfig(response_delay=0.5, port=8002)

with FakeAIClient(config=config1, auto_start=True, port=8001) as client1:
    with FakeAIClient(config=config2, auto_start=True, port=8002) as client2:
        # Fast server
        response1 = client1.chat("Hello!")

        # Slow server
        response2 = client2.chat("Hello!")
```

### Custom Validation

```python
def assert_response_contains_keyword(response, keyword):
    """Custom assertion for response content."""
    content = response.choices[0].message.content.lower()
    assert keyword.lower() in content, f"Response missing keyword: {keyword}"


# Use in tests
response = client.chat("Tell me about Python programming")
assert_response_contains_keyword(response, "python")
```

### Timing Comparisons

```python
from fakeai import measure_stream_timing


def compare_streaming_performance(client, prompts):
    """Compare streaming performance across prompts."""
    results = []

    for prompt in prompts:
        stream = client.stream_chat(prompt)
        timing = measure_stream_timing(stream)
        results.append({
            "prompt": prompt,
            "ttft": timing["time_to_first_token"],
            "total_time": timing["total_time"],
            "chunks": timing["chunks_count"],
        })

    return results


# Use in tests
with FakeAIClient(auto_start=True) as client:
    prompts = ["Short", "Medium length prompt", "Very long prompt " * 10]
    results = compare_streaming_performance(client, prompts)

    for result in results:
        print(f"{result['prompt'][:30]}: TTFT={result['ttft']*1000:.2f}ms")
```

## API Reference

### FakeAIClient Methods

| Method | Description |
|--------|-------------|
| `chat(message, model, system, **kwargs)` | Simple chat completion |
| `stream_chat(message, model, system, **kwargs)` | Streaming chat |
| `embed(text, model)` | Create embeddings |
| `moderate(text)` | Content moderation |
| `list_models()` | List available models |
| `get_model(model_id)` | Get model details |
| `start_server(timeout)` | Manually start server |
| `stop_server()` | Manually stop server |

### Assertion Functions

| Function | Purpose |
|----------|---------|
| `assert_response_valid(response)` | Validate response schema |
| `assert_tokens_in_range(usage, ...)` | Validate token counts |
| `assert_cache_hit(response)` | Validate cache was used |
| `assert_moderation_flagged(result, category)` | Validate content flagged |
| `assert_streaming_valid(stream)` | Validate stream structure |

### Utility Functions

| Function | Returns |
|----------|---------|
| `collect_stream_content(stream)` | Complete text from stream |
| `measure_stream_timing(stream)` | Timing metrics dict |

### Context Managers

| Context Manager | Purpose |
|----------------|---------|
| `temporary_server(config, port, host)` | Auto-managed server |
| `FakeAIClient(auto_start=True)` | Client with server lifecycle |

### Pytest Fixtures

| Fixture | Provides |
|---------|----------|
| `fakeai_client` | Basic client |
| `fakeai_client_with_auth` | Authenticated client |
| `fakeai_running_server` | Server connection info |

## Best Practices

### 1. Use Zero Delay for Unit Tests

```python
config = AppConfig(response_delay=0.0, random_delay=False)
with FakeAIClient(config=config, auto_start=True) as client:
    # Fast tests
    pass
```

### 2. Validate All Responses

```python
response = client.chat("Hello!")
assert_response_valid(response)  # Always validate
assert_tokens_in_range(response.usage, min_prompt=1, min_completion=1)
```

### 3. Use Context Managers

```python
# Good - automatic cleanup
with FakeAIClient(auto_start=True) as client:
    response = client.chat("Hello!")

# Avoid - manual cleanup needed
client = FakeAIClient(auto_start=True)
client.start_server()
# ... use client ...
client.stop_server()
```

### 4. Use Fixtures for Tests

```python
# Good - reusable fixture
def test_feature(fakeai_client):
    response = fakeai_client.chat("Hello!")

# Avoid - creating client in each test
def test_feature():
    with FakeAIClient(auto_start=True) as client:
        response = client.chat("Hello!")
```

### 5. Measure Performance

```python
stream = client.stream_chat("Hello!")
timing = measure_stream_timing(stream)
assert timing["time_to_first_token"] < 1.0  # Performance assertion
```

## Troubleshooting

### Server Won't Start

```python
# Increase timeout
with FakeAIClient(auto_start=True) as client:
    client.start_server(timeout=30.0)  # Wait longer
```

### Port Already in Use

```python
# Use different port
config = AppConfig(port=8001)
with FakeAIClient(config=config, auto_start=True, port=8001) as client:
    response = client.chat("Hello!")
```

### Authentication Errors

```python
# Ensure API key matches config
config = AppConfig(require_api_key=True, api_keys=["my-key"])
client = FakeAIClient(config=config, auto_start=True, api_key="my-key")
```

### Timeout Errors

```python
# Reduce delay for faster responses
config = AppConfig(response_delay=0.1)
with FakeAIClient(config=config, auto_start=True) as client:
    response = client.chat("Hello!")
```

## Contributing

Contributions are welcome! Please see the main README for guidelines.

## License

Apache-2.0
