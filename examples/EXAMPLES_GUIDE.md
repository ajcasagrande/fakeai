# FakeAI Examples Guide

Complete example applications demonstrating all FakeAI features with production-ready patterns.

## Overview

This directory contains comprehensive, runnable examples that demonstrate:
- Best practices for using FakeAI
- Production-ready implementation patterns
- Performance optimization techniques
- Error handling and reliability
- Complete feature coverage

All examples are **interactive** and **well-documented** with step-by-step demonstrations.

## Prerequisites

1. **Start FakeAI server:**
   ```bash
   python run_server.py
   # or
   fakeai-server
   ```

2. **Install OpenAI client:**
   ```bash
   pip install openai
   ```

3. **Optional dependencies for load testing:**
   ```bash
   pip install httpx
   ```

## Examples

### 1. KV Cache Demo (`example_kv_cache_demo.py`)

**What it demonstrates:**
- KV cache hits vs misses
- Token reuse metrics
- Latency improvements with caching
- Cache benefits in conversations
- Streaming with cache

**Key features:**
- Basic cache demonstration
- Multi-turn conversation caching
- Cache performance metrics
- Cache comparison (with vs without)
- Streaming cache benefits

**Run it:**
```bash
python examples/example_kv_cache_demo.py
```

**Perfect for:**
- Understanding cache behavior
- Optimizing multi-turn conversations
- Reducing latency with common prefixes
- RAG systems with fixed templates

---

### 2. Reasoning Workflow (`example_reasoning_workflow.py`)

**What it demonstrates:**
- GPT-OSS reasoning models
- O1 model family
- Reasoning content (internal thinking)
- Reasoning tokens tracking
- Streaming reasoning vs content

**Key features:**
- Basic reasoning model usage
- Comparison with regular models
- Streaming reasoning demonstration
- O1 model family support
- Complex multi-step reasoning
- Reasoning in conversations
- Reasoning with tool calling

**Run it:**
```bash
python examples/example_reasoning_workflow.py
```

**Perfect for:**
- Complex problem solving
- Multi-step logical reasoning
- Math and planning tasks
- Understanding model thinking process

---

### 3. Moderation Pipeline (`example_moderation_pipeline.py`)

**What it demonstrates:**
- Content moderation before LLM
- Safe chat pipeline
- Category-specific handling
- Batch moderation
- Custom thresholds

**Key features:**
- Basic text moderation
- Safe chat pipeline with blocking
- Category-specific user messages
- Multimodal moderation (text + image)
- Batch processing
- Conversation moderation
- Custom score thresholds

**Run it:**
```bash
python examples/example_moderation_pipeline.py
```

**Perfect for:**
- Building safe applications
- Filtering harmful content
- Compliance with content policies
- Child-safe applications

---

### 4. Multimodal Content (`example_multimodal.py`)

**What it demonstrates:**
- Vision models (text + image)
- Audio models (text + audio)
- Token calculation for images/audio
- Multiple images per request
- Base64 vs URL images

**Key features:**
- Basic vision model usage
- Image detail levels (low/high/auto)
- Multiple images in one request
- Base64-encoded images
- Vision with streaming
- Audio input processing
- Audio output generation
- Vision in conversations
- Mixed modalities (text + image + audio)

**Run it:**
```bash
python examples/example_multimodal.py
```

**Perfect for:**
- Vision applications
- Audio transcription/generation
- Multimodal AI systems
- Understanding token costs

---

### 5. Production Workflow (`example_production_workflow.py`)

**What it demonstrates:**
- Complete production-ready implementation
- Combines ALL features
- Error handling and retries
- Metrics collection
- Best practices

**Key features:**
- Content moderation (safety)
- KV cache optimization (performance)
- Reasoning models (accuracy)
- Streaming responses (UX)
- Error handling with retries (reliability)
- Metrics tracking (observability)
- Tool calling (functionality)
- Production service class

**Run it:**
```bash
python examples/example_production_workflow.py
```

**Perfect for:**
- Production deployments
- Reference implementation
- Learning best practices
- Building robust applications

**This is the MOST IMPORTANT example** - it shows how to combine everything correctly.

---

### 6. Load Testing (`example_load_testing.py`)

**What it demonstrates:**
- Concurrent request handling
- Performance benchmarking
- Throughput measurement
- Latency percentiles
- Cache performance under load

**Key features:**
- Basic load testing
- Concurrency scaling tests
- Streaming vs non-streaming performance
- Cache performance under load
- Rate limiting behavior
- Server metrics collection
- Comprehensive benchmark suite

**Run it:**
```bash
python examples/example_load_testing.py
```

**Perfect for:**
- Performance testing
- Capacity planning
- Validating error handling
- Testing before production

---

## Quick Start

### Run a single example:
```bash
python examples/example_kv_cache_demo.py
```

### Run all examples (requires server):
```bash
# Terminal 1: Start server
python run_server.py

# Terminal 2: Run examples
python examples/example_kv_cache_demo.py
python examples/example_reasoning_workflow.py
python examples/example_moderation_pipeline.py
python examples/example_multimodal.py
python examples/example_production_workflow.py
python examples/example_load_testing.py
```

## Example Usage Patterns

### Pattern 1: Safe Chat Application

```python
from example_production_workflow import ProductionChatService

service = ProductionChatService(enable_moderation=True)

messages = [
    {"role": "user", "content": "User input here"}
]

response, metrics = await service.chat_completion(messages)
```

### Pattern 2: Optimized with Cache

```python
# Use consistent system messages for cache hits
system_msg = "You are a helpful assistant."

messages = [
    {"role": "system", "content": system_msg},
    {"role": "user", "content": "Question 1"}
]

response = await client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=messages,
)

# Next request reuses cached system message
print(f"Cached tokens: {response.usage.prompt_tokens_details.cached_tokens}")
```

### Pattern 3: Reasoning for Complex Problems

```python
# Use reasoning model for complex tasks
response = await client.chat.completions.create(
    model="gpt-oss-120b",
    messages=[
        {"role": "user", "content": "Complex math problem"}
    ],
)

print("Reasoning:", response.choices[0].message.reasoning_content)
print("Answer:", response.choices[0].message.content)
```

### Pattern 4: Vision Processing

```python
# Send image for analysis
response = await client.chat.completions.create(
    model="openai/gpt-oss-120b-vision-preview",
    messages=[
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
    ],
)
```

## Features Coverage

| Feature | Example File | Description |
|---------|-------------|-------------|
| KV Cache | kv_cache_demo.py | Cache reuse, token savings |
| Reasoning Models | reasoning_workflow.py | GPT-OSS, O1, reasoning content |
| Content Moderation | moderation_pipeline.py | Safety, policy compliance |
| Vision/Audio | multimodal.py | Images, audio, token calculation |
| Production Patterns | production_workflow.py | Complete implementation |
| Load Testing | load_testing.py | Performance, benchmarking |
| Streaming | All examples | Streaming responses |
| Tool Calling | production_workflow.py | Function calling |
| Error Handling | production_workflow.py | Retries, reliability |
| Metrics | All examples | Usage tracking |

## Tips

1. **Start with production_workflow.py** - it shows best practices combining all features
2. **Use KV cache** - Significant latency improvements for repeated prefixes
3. **Always moderate user input** - Before sending to LLM
4. **Track metrics** - Monitor cache hit rates, token usage, latency
5. **Test under load** - Use load_testing.py to validate behavior
6. **Handle errors** - Implement retries with exponential backoff
7. **Choose right model** - Reasoning for complex tasks, regular for simple ones

## Common Issues

### Server not running
```
Error: Connection refused

Solution: Start the server first:
  python run_server.py
```

### Import errors
```
ModuleNotFoundError: No module named 'openai'

Solution: Install the OpenAI client:
  pip install openai
```

### Rate limiting
```
Rate limit exceeded

Solution: FakeAI has no rate limits by default. If enabled:
  FAKEAI_RATE_LIMIT_ENABLED=false python run_server.py
```

## Next Steps

1. **Read the code** - Each example is heavily commented
2. **Modify and experiment** - Change parameters, models, messages
3. **Build your application** - Use production_workflow.py as template
4. **Test thoroughly** - Use load_testing.py before production
5. **Monitor in production** - Track same metrics you see in examples

## Additional Resources

- **Main README**: `/home/anthony/projects/fakeai/README.md`
- **CLAUDE.md**: Comprehensive technical documentation
- **Existing Examples**: Other example files in this directory
- **Server Metrics**: `http://localhost:8000/metrics`
- **API Docs**: `http://localhost:8000/docs`

## Contributing

Found a bug or want to add more examples? Contributions welcome!

---

**Last Updated**: 2025-10-04
**FakeAI Version**: 0.0.4+
