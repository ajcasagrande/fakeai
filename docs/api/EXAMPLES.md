# FakeAI Usage Examples

This document provides comprehensive, copy-paste ready examples for using the FakeAI server. All examples assume the server is running at `http://localhost:8000`.

## Table of Contents

- [Starting the Server](#starting-the-server)
- [Basic Usage](#basic-usage)
  - [Simple Chat Completion](#simple-chat-completion)
  - [Simple Embedding](#simple-embedding)
  - [Simple Image Generation](#simple-image-generation)
- [Advanced Chat Completions](#advanced-chat-completions)
  - [Multi-turn Conversations](#multi-turn-conversations)
  - [Streaming Responses](#streaming-responses)
  - [Tool/Function Calling](#toolfunction-calling)
  - [Structured Outputs with JSON Schema](#structured-outputs-with-json-schema)
  - [Log Probabilities](#log-probabilities)
  - [Multi-modal Content (Images + Text)](#multi-modal-content-images--text)
  - [Audio Content](#audio-content)
- [Responses API Usage](#responses-api-usage)
  - [Basic Response Creation](#basic-response-creation)
  - [Continuing Conversations](#continuing-conversations-with-previous_response_id)
  - [Using Tools](#using-tools)
  - [Background Processing](#background-processing)
- [NIM Rankings Usage](#nim-rankings-usage)
  - [Basic Reranking](#basic-reranking)
  - [Multiple Passages](#multiple-passages)
  - [Interpreting Logit Scores](#interpreting-logit-scores)
- [Python Client Examples](#python-client-examples)
  - [Using with OpenAI SDK](#using-with-openai-sdk)
  - [Async Operations](#async-operations)
  - [Error Handling](#error-handling)
  - [Best Practices](#best-practices)

---

## Starting the Server

### Option 1: Using the Command-Line Tool

```bash
fakeai-server
```

### Option 2: Using Python Module

```bash
python -m fakeai.run_server
```

### Option 3: Custom Configuration

```python
#!/usr/bin/env python3
"""Custom server configuration."""

import uvicorn
from fakeai import app
from fakeai.config import AppConfig

# Create custom configuration
config = AppConfig(
    host="0.0.0.0",           # Allow external connections
    port=9000,                # Custom port
    debug=True,               # Enable debug mode
    require_api_key=False,    # Disable API key requirement
    response_delay=0.2,       # Faster responses
    random_delay=True,        # Add variability
    max_variance=0.5          # Higher variance
)

if __name__ == "__main__":
    uvicorn.run(
        "fakeai:app",
        host=config.host,
        port=config.port,
        reload=config.debug
    )
```

---

## Basic Usage

### Simple Chat Completion

```python
#!/usr/bin/env python3
"""Simple chat completion example."""

from openai import OpenAI

# Initialize client
client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1",
)

# Create a simple chat completion
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me about artificial intelligence."}
    ]
)

print(f"Response: {response.choices[0].message.content}")
print(f"Usage: {response.usage.prompt_tokens} prompt + {response.usage.completion_tokens} completion = {response.usage.total_tokens} total tokens")
```

### Simple Embedding

```python
#!/usr/bin/env python3
"""Simple embedding example."""

from openai import OpenAI

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1",
)

# Create embeddings for a single text
response = client.embeddings.create(
    model="sentence-transformers/all-mpnet-base-v2",
    input="The quick brown fox jumps over the lazy dog."
)

embedding = response.data[0].embedding
print(f"Embedding dimensions: {len(embedding)}")
print(f"First 5 values: {embedding[:5]}")
print(f"Usage: {response.usage.total_tokens} tokens")

# Create embeddings for multiple texts
response = client.embeddings.create(
    model="sentence-transformers/all-mpnet-base-v2",
    input=[
        "Machine learning is fascinating.",
        "Natural language processing powers chatbots.",
        "Computer vision enables image recognition."
    ]
)

for i, data in enumerate(response.data):
    print(f"Text {i+1}: {len(data.embedding)} dimensions")
```

### Simple Image Generation

```python
#!/usr/bin/env python3
"""Simple image generation example."""

from openai import OpenAI

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1",
)

# Generate a single image
response = client.images.generate(
    model="stabilityai/stable-diffusion-xl-base-1.0",
    prompt="A futuristic city with flying cars and tall skyscrapers",
    n=1,
    size="1024x1024",
    quality="hd",
    style="vivid"
)

print(f"Generated image URL: {response.data[0].url}")
if response.data[0].revised_prompt:
    print(f"Revised prompt: {response.data[0].revised_prompt}")

# Generate multiple images with DALL-E 2
response = client.images.generate(
    model="stabilityai/stable-diffusion-2-1",
    prompt="A serene mountain landscape at sunset",
    n=3,
    size="512x512"
)

for i, image in enumerate(response.data):
    print(f"Image {i+1}: {image.url}")
```

---

## Advanced Chat Completions

### Multi-turn Conversations

```python
#!/usr/bin/env python3
"""Multi-turn conversation example."""

from openai import OpenAI

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1",
)

# Maintain conversation history
conversation = [
    {"role": "system", "content": "You are a helpful coding assistant."}
]

# First turn
conversation.append({
    "role": "user",
    "content": "How do I read a file in Python?"
})

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=conversation
)

assistant_message = response.choices[0].message.content
conversation.append({
    "role": "assistant",
    "content": assistant_message
})

print(f"Assistant: {assistant_message}\n")

# Second turn - context is maintained
conversation.append({
    "role": "user",
    "content": "What about writing to a file?"
})

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=conversation
)

assistant_message = response.choices[0].message.content
print(f"Assistant: {assistant_message}")
```

### Streaming Responses

```python
#!/usr/bin/env python3
"""Streaming chat completion example."""

from openai import OpenAI

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1",
)

print("Response: ", end="", flush=True)

# Stream the response
stream = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "user", "content": "Write a short story about a robot learning to paint."}
    ],
    stream=True,
    max_tokens=300
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)

print("\n")
```

### Async Streaming

```python
#!/usr/bin/env python3
"""Async streaming example."""

import asyncio
from openai import AsyncOpenAI

async def main():
    client = AsyncOpenAI(
        api_key="sk-fakeai-1234567890abcdef",
        base_url="http://localhost:8000/v1",
    )

    print("Streaming response: ", end="", flush=True)

    stream = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "user", "content": "Explain quantum computing in simple terms"}
        ],
        stream=True
    )

    async for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)

    print("\n")

if __name__ == "__main__":
    asyncio.run(main())
```

### Tool/Function Calling

```python
#!/usr/bin/env python3
"""Tool calling example."""

import json
from openai import OpenAI

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1",
)

# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "The temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get the current stock price for a given ticker symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "The stock ticker symbol, e.g. AAPL"
                    }
                },
                "required": ["symbol"]
            }
        }
    }
]

# Make a request that should trigger a tool call
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "user", "content": "What's the weather like in San Francisco?"}
    ],
    tools=tools,
    tool_choice="auto"
)

# Check if the model wants to call a tool
message = response.choices[0].message
if message.tool_calls:
    print("Tool calls requested:")
    for tool_call in message.tool_calls:
        print(f"  Function: {tool_call.function.name}")
        print(f"  Arguments: {tool_call.function.arguments}")

        # Simulate executing the function
        if tool_call.function.name == "get_current_weather":
            function_response = json.dumps({
                "location": "San Francisco, CA",
                "temperature": "72",
                "unit": "fahrenheit",
                "conditions": "Sunny"
            })
        else:
            function_response = json.dumps({"error": "Unknown function"})

        # Continue the conversation with the function response
        messages = [
            {"role": "user", "content": "What's the weather like in San Francisco?"},
            message,
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": function_response
            }
        ]

        # Get the final response
        final_response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=tools
        )

        print(f"\nFinal response: {final_response.choices[0].message.content}")
else:
    print(f"Direct response: {message.content}")
```

### Parallel Tool Calls

```python
#!/usr/bin/env python3
"""Parallel tool calling example."""

import json
from openai import OpenAI

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1",
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }
    }
]

# Request that should trigger multiple tool calls
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "user", "content": "What's the weather in New York, London, and Tokyo?"}
    ],
    tools=tools,
    parallel_tool_calls=True  # Enable parallel tool execution
)

message = response.choices[0].message
if message.tool_calls:
    print(f"Model requested {len(message.tool_calls)} parallel tool calls:")
    for tool_call in message.tool_calls:
        args = json.loads(tool_call.function.arguments)
        print(f"  - get_weather({args['location']})")
```

### Structured Outputs with JSON Schema

```python
#!/usr/bin/env python3
"""Structured output with JSON schema example."""

from openai import OpenAI

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1",
)

# Define a JSON schema for the response
response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "PersonInfo",
        "description": "Information about a person",
        "schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The person's full name"
                },
                "age": {
                    "type": "integer",
                    "description": "The person's age in years"
                },
                "occupation": {
                    "type": "string",
                    "description": "The person's current job"
                },
                "skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of the person's skills"
                }
            },
            "required": ["name", "age", "occupation"],
            "additionalProperties": False
        },
        "strict": True
    }
}

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "user", "content": "Tell me about a software engineer named Alice who is 28 years old."}
    ],
    response_format=response_format
)

import json
structured_data = json.loads(response.choices[0].message.content)
print("Structured response:")
print(json.dumps(structured_data, indent=2))
```

### Log Probabilities

```python
#!/usr/bin/env python3
"""Log probabilities example."""

from openai import OpenAI

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1",
)

# Request with log probabilities
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "user", "content": "Say 'Hello, World!'"}
    ],
    logprobs=True,
    top_logprobs=3  # Get top 3 alternative tokens at each position
)

choice = response.choices[0]
if choice.logprobs and choice.logprobs.content:
    print("Token log probabilities:")
    for token_info in choice.logprobs.content:
        print(f"\nToken: '{token_info.token}'")
        print(f"  Log probability: {token_info.logprob:.4f}")
        if token_info.top_logprobs:
            print("  Top alternatives:")
            for alt in token_info.top_logprobs:
                print(f"    '{alt.token}': {alt.logprob:.4f}")
```

### Multi-modal Content (Images + Text)

```python
#!/usr/bin/env python3
"""Multi-modal content example with images."""

from openai import OpenAI

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1",
)

# Using an image URL
response = client.chat.completions.create(
    model="openai/gpt-oss-120b-vision-preview",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What's in this image?"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/image.jpg",
                        "detail": "high"  # Options: "auto", "low", "high"
                    }
                }
            ]
        }
    ],
    max_tokens=300
)

print(f"Response: {response.choices[0].message.content}")

# Using base64 encoded image
import base64

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Example with base64 (assuming you have an image file)
# base64_image = encode_image("path/to/your/image.jpg")

response = client.chat.completions.create(
    model="openai/gpt-oss-120b-vision-preview",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Describe this image in detail"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."  # Your base64 string
                    }
                }
            ]
        }
    ]
)

print(f"Response: {response.choices[0].message.content}")

# Multiple images in one request
response = client.chat.completions.create(
    model="openai/gpt-oss-120b-vision-preview",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Compare these two images"
                },
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/image1.jpg"}
                },
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/image2.jpg"}
                }
            ]
        }
    ]
)

print(f"Comparison: {response.choices[0].message.content}")
```

### Audio Content

```python
#!/usr/bin/env python3
"""Audio input and output example."""

import base64
from openai import OpenAI

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1",
)

def encode_audio(audio_path):
    """Encode audio file to base64."""
    with open(audio_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode('utf-8')

# Audio input example
# audio_data = encode_audio("path/to/audio.wav")

response = client.chat.completions.create(
    model="openai/gpt-oss-120b-audio-preview",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Transcribe this audio"
                },
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": "base64_encoded_audio_data_here",
                        "format": "wav"  # Options: "wav", "mp3"
                    }
                }
            ]
        }
    ]
)

print(f"Transcription: {response.choices[0].message.content}")

# Audio output configuration
response = client.chat.completions.create(
    model="openai/gpt-oss-120b-audio-preview",
    modalities=["text", "audio"],
    audio={
        "voice": "alloy",  # Options: alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer, verse
        "format": "mp3"    # Options: mp3, opus, aac, flac, wav, pcm16
    },
    messages=[
        {
            "role": "user",
            "content": "Tell me a short joke"
        }
    ]
)

print(f"Text response: {response.choices[0].message.content}")
# Audio response would be in response.choices[0].message.audio if available
```

---

## Responses API Usage

The Responses API is OpenAI's newer API format (March 2025) that provides a simplified interface for text generation.

### Basic Response Creation

```python
#!/usr/bin/env python3
"""Basic Responses API example."""

import requests

API_KEY = "sk-fakeai-1234567890abcdef"
BASE_URL = "http://localhost:8000/v1"

# Simple text input
response = requests.post(
    f"{BASE_URL}/responses",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "openai/gpt-oss-120b",
        "input": "Explain the theory of relativity in simple terms"
    }
)

data = response.json()
print(f"Response ID: {data['id']}")
print(f"Status: {data['status']}")
print(f"Output: {data['output'][0]['content'][0]['text']}")
print(f"Usage: {data['usage']}")

# With system instructions
response = requests.post(
    f"{BASE_URL}/responses",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "openai/gpt-oss-120b",
        "input": "Write a haiku about programming",
        "instructions": "You are a creative poet who loves technology",
        "max_output_tokens": 100,
        "temperature": 0.8
    }
)

data = response.json()
print(f"\n{data['output'][0]['content'][0]['text']}")
```

### Continuing Conversations with previous_response_id

```python
#!/usr/bin/env python3
"""Responses API conversation continuation example."""

import requests

API_KEY = "sk-fakeai-1234567890abcdef"
BASE_URL = "http://localhost:8000/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# First message
response = requests.post(
    f"{BASE_URL}/responses",
    headers=headers,
    json={
        "model": "openai/gpt-oss-120b",
        "input": "What is machine learning?",
        "instructions": "You are a helpful teacher",
        "store": True  # Important: store the response for continuation
    }
)

data = response.json()
response_id = data['id']
print(f"First response: {data['output'][0]['content'][0]['text']}\n")

# Continue the conversation
response = requests.post(
    f"{BASE_URL}/responses",
    headers=headers,
    json={
        "model": "openai/gpt-oss-120b",
        "input": "Can you give me a simple example?",
        "previous_response_id": response_id,  # Reference the previous response
        "store": True
    }
)

data = response.json()
print(f"Follow-up response: {data['output'][0]['content'][0]['text']}")
print(f"Previous response ID: {data['previous_response_id']}")
```

### Using Tools

```python
#!/usr/bin/env python3
"""Responses API with tools example."""

import requests
import json

API_KEY = "sk-fakeai-1234567890abcdef"
BASE_URL = "http://localhost:8000/v1"

tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate_bmi",
            "description": "Calculate Body Mass Index",
            "parameters": {
                "type": "object",
                "properties": {
                    "weight_kg": {
                        "type": "number",
                        "description": "Weight in kilograms"
                    },
                    "height_m": {
                        "type": "number",
                        "description": "Height in meters"
                    }
                },
                "required": ["weight_kg", "height_m"]
            }
        }
    }
]

response = requests.post(
    f"{BASE_URL}/responses",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "openai/gpt-oss-120b",
        "input": "Calculate BMI for someone who is 1.75m tall and weighs 70kg",
        "tools": tools,
        "tool_choice": "auto"
    }
)

data = response.json()
print(f"Response: {json.dumps(data, indent=2)}")

# Check if tools were called
if data['output']:
    for item in data['output']:
        if item['type'] == 'function_call':
            print(f"\nFunction called: {item['name']}")
            print(f"Arguments: {item['arguments']}")
```

### Background Processing

```python
#!/usr/bin/env python3
"""Responses API background processing example."""

import requests
import time

API_KEY = "sk-fakeai-1234567890abcdef"
BASE_URL = "http://localhost:8000/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Submit a request for background processing
response = requests.post(
    f"{BASE_URL}/responses",
    headers=headers,
    json={
        "model": "openai/gpt-oss-120b",
        "input": "Write a detailed essay about artificial intelligence",
        "max_output_tokens": 2000,
        "background": True  # Process in background
    }
)

data = response.json()
response_id = data['id']
print(f"Background task submitted: {response_id}")
print(f"Initial status: {data['status']}")

# Poll for completion (in a real scenario)
# Note: FakeAI simulates immediate completion, but in real usage you'd poll
while data['status'] in ['queued', 'in_progress']:
    time.sleep(1)
    # In a real implementation, you would fetch the response status
    # response = requests.get(f"{BASE_URL}/responses/{response_id}", headers=headers)
    # data = response.json()
    print(f"Status: {data['status']}")

if data['status'] == 'completed':
    print(f"\nCompleted! Output: {data['output'][0]['content'][0]['text']}")
elif data['status'] == 'failed':
    print(f"\nFailed: {data['error']}")
```

---

## NIM Rankings Usage

The NIM Rankings API provides passage reranking capabilities for search and retrieval tasks.

### Basic Reranking

```python
#!/usr/bin/env python3
"""Basic NIM Rankings example."""

import requests

API_KEY = "sk-fakeai-1234567890abcdef"
BASE_URL = "http://localhost:8000/v1"

response = requests.post(
    f"{BASE_URL}/ranking",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "nvidia/nv-rerankqa-mistral-4b-v3",
        "query": {
            "text": "What is machine learning?"
        },
        "passages": [
            {"text": "Machine learning is a subset of artificial intelligence."},
            {"text": "The weather today is sunny and warm."},
            {"text": "Machine learning algorithms learn from data to make predictions."}
        ]
    }
)

data = response.json()
print("Rankings (sorted by relevance):")
for rank in data['rankings']:
    print(f"  Index {rank['index']}: logit score = {rank['logit']:.4f}")
```

### Multiple Passages

```python
#!/usr/bin/env python3
"""NIM Rankings with multiple passages example."""

import requests

API_KEY = "sk-fakeai-1234567890abcdef"
BASE_URL = "http://localhost:8000/v1"

# Search query
query = "best practices for Python programming"

# Documents to rerank
passages = [
    {"text": "Python uses indentation to define code blocks instead of braces."},
    {"text": "Use list comprehensions for concise and readable code."},
    {"text": "JavaScript is a popular programming language for web development."},
    {"text": "Follow PEP 8 style guide for consistent Python code formatting."},
    {"text": "Virtual environments help isolate project dependencies in Python."},
    {"text": "Type hints improve code documentation and catch errors early."},
    {"text": "The capital of France is Paris."},
    {"text": "Use meaningful variable names to make code self-documenting."}
]

response = requests.post(
    f"{BASE_URL}/ranking",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "nvidia/nv-rerankqa-mistral-4b-v3",
        "query": {"text": query},
        "passages": passages,
        "truncate": "END"  # Options: "NONE", "END"
    }
)

data = response.json()

print(f"Query: {query}\n")
print("Top 5 most relevant passages:")
for i, rank in enumerate(data['rankings'][:5], 1):
    passage_text = passages[rank['index']]['text']
    print(f"{i}. [Score: {rank['logit']:.4f}] {passage_text}")
```

### Interpreting Logit Scores

```python
#!/usr/bin/env python3
"""Understanding NIM Rankings logit scores."""

import requests
import math

API_KEY = "sk-fakeai-1234567890abcdef"
BASE_URL = "http://localhost:8000/v1"

def sigmoid(x):
    """Convert logit to probability."""
    return 1 / (1 + math.exp(-x))

response = requests.post(
    f"{BASE_URL}/ranking",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "nvidia/nv-rerankqa-mistral-4b-v3",
        "query": {"text": "deep learning frameworks"},
        "passages": [
            {"text": "PyTorch is a popular deep learning framework developed by Facebook."},
            {"text": "TensorFlow is Google's open-source machine learning framework."},
            {"text": "Keras provides a high-level API for building neural networks."},
            {"text": "NumPy is used for numerical computing in Python."},
            {"text": "Pandas is a data manipulation library."}
        ]
    }
)

data = response.json()

print("Rankings with interpretations:\n")
for rank in data['rankings']:
    logit = rank['logit']
    probability = sigmoid(logit)

    # Interpret relevance
    if logit > 2.0:
        relevance = "Highly relevant"
    elif logit > 0:
        relevance = "Somewhat relevant"
    elif logit > -2.0:
        relevance = "Low relevance"
    else:
        relevance = "Not relevant"

    print(f"Index {rank['index']}:")
    print(f"  Logit: {logit:.4f}")
    print(f"  Probability: {probability:.4f}")
    print(f"  Relevance: {relevance}\n")
```

---

## Python Client Examples

### Using with OpenAI SDK

```python
#!/usr/bin/env python3
"""Complete OpenAI SDK example with FakeAI."""

from openai import OpenAI
import os

# Best practice: use environment variables
# export OPENAI_API_KEY="sk-fakeai-1234567890abcdef"
# export OPENAI_BASE_URL="http://localhost:8000/v1"

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "sk-fakeai-1234567890abcdef"),
    base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1"),
)

def list_models():
    """List available models."""
    models = client.models.list()
    print("Available models:")
    for model in models.data:
        print(f"  - {model.id}")
    return models.data

def chat_completion(model="openai/gpt-oss-120b", message="Hello!"):
    """Create a chat completion."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": message}]
    )
    return response.choices[0].message.content

def stream_completion(model="openai/gpt-oss-120b", message="Tell me a story"):
    """Stream a chat completion."""
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": message}],
        stream=True
    )

    full_response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            full_response += content
            print(content, end="", flush=True)

    print()
    return full_response

def create_embedding(text):
    """Create an embedding."""
    response = client.embeddings.create(
        model="sentence-transformers/all-mpnet-base-v2",
        input=text
    )
    return response.data[0].embedding

if __name__ == "__main__":
    # List models
    list_models()

    # Chat completion
    print("\nChat completion:")
    response = chat_completion(message="What is Python?")
    print(response)

    # Streaming
    print("\nStreaming completion:")
    stream_completion(message="Write a haiku about coding")

    # Embedding
    print("\nEmbedding:")
    embedding = create_embedding("Hello, world!")
    print(f"Embedding dimension: {len(embedding)}")
```

### Async Operations

```python
#!/usr/bin/env python3
"""Async operations with OpenAI SDK and FakeAI."""

import asyncio
from openai import AsyncOpenAI

async def main():
    client = AsyncOpenAI(
        api_key="sk-fakeai-1234567890abcdef",
        base_url="http://localhost:8000/v1",
    )

    # Concurrent requests
    tasks = [
        client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": f"Tell me about {topic}"}]
        )
        for topic in ["Python", "JavaScript", "Go", "Rust"]
    ]

    print("Making concurrent requests...")
    responses = await asyncio.gather(*tasks)

    for i, response in enumerate(responses):
        topic = ["Python", "JavaScript", "Go", "Rust"][i]
        print(f"\n{topic}:")
        print(response.choices[0].message.content[:100] + "...")

    # Async streaming
    print("\n\nAsync streaming:")
    stream = await client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Count to 10"}],
        stream=True
    )

    async for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print()

if __name__ == "__main__":
    asyncio.run(main())
```

### Error Handling

```python
#!/usr/bin/env python3
"""Error handling examples with OpenAI SDK and FakeAI."""

from openai import OpenAI, OpenAIError, APIError, APIConnectionError, RateLimitError
import sys

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1",
)

def safe_completion(message, max_retries=3):
    """Create a completion with error handling and retries."""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": message}],
                timeout=30.0  # Set timeout
            )
            return response.choices[0].message.content

        except APIConnectionError as e:
            print(f"Connection error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

        except RateLimitError as e:
            print(f"Rate limit exceeded: {e}")
            raise

        except APIError as e:
            print(f"API error: {e}")
            raise

        except OpenAIError as e:
            print(f"OpenAI error: {e}")
            raise

        except Exception as e:
            print(f"Unexpected error: {e}")
            raise

def validate_model(model_id):
    """Validate that a model exists."""
    try:
        model = client.models.retrieve(model_id)
        print(f"Model {model_id} is available")
        return True
    except Exception as e:
        print(f"Model {model_id} not found: {e}")
        return False

def test_authentication():
    """Test API key authentication."""
    # Test with valid key
    try:
        response = client.models.list()
        print("Authentication successful")
        return True
    except Exception as e:
        print(f"Authentication failed: {e}")
        return False

if __name__ == "__main__":
    # Test authentication
    print("Testing authentication...")
    test_authentication()

    # Validate model
    print("\nValidating model...")
    validate_model("openai/gpt-oss-120b")

    # Safe completion with retries
    print("\nTesting completion with error handling...")
    try:
        result = safe_completion("What is artificial intelligence?")
        print(f"Success: {result[:100]}...")
    except Exception as e:
        print(f"Failed after retries: {e}")
        sys.exit(1)
```

### Best Practices

```python
#!/usr/bin/env python3
"""Best practices for using OpenAI SDK with FakeAI."""

from openai import OpenAI
import os
import logging
from functools import wraps
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment
class Config:
    API_KEY = os.getenv("OPENAI_API_KEY", "sk-fakeai-1234567890abcdef")
    BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1")
    DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-oss-120b")
    TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))
    MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "3"))

# Initialize client with best practices
client = OpenAI(
    api_key=Config.API_KEY,
    base_url=Config.BASE_URL,
    timeout=Config.TIMEOUT,
    max_retries=Config.MAX_RETRIES
)

def log_api_call(func):
    """Decorator to log API calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Calling {func.__name__} with model={kwargs.get('model', Config.DEFAULT_MODEL)}")
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"{func.__name__} completed in {elapsed:.2f}s")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}")
            raise

    return wrapper

@log_api_call
def create_completion(
    message: str,
    model: str = Config.DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 500,
    system_prompt: str = "You are a helpful assistant."
) -> str:
    """
    Create a chat completion with best practices.

    Args:
        message: User message
        model: Model to use
        temperature: Sampling temperature (0-2)
        max_tokens: Maximum tokens to generate
        system_prompt: System instruction

    Returns:
        The assistant's response text
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        temperature=temperature,
        max_tokens=max_tokens
    )

    # Log usage
    usage = response.usage
    logger.info(f"Token usage: {usage.prompt_tokens} prompt + {usage.completion_tokens} completion = {usage.total_tokens} total")

    return response.choices[0].message.content

@log_api_call
def batch_embeddings(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    """
    Create embeddings in batches for efficiency.

    Args:
        texts: List of texts to embed
        batch_size: Number of texts per batch

    Returns:
        List of embedding vectors
    """
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        logger.info(f"Processing batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}")

        response = client.embeddings.create(
            model="sentence-transformers/all-mpnet-base-v2",
            input=batch
        )

        embeddings = [data.embedding for data in response.data]
        all_embeddings.extend(embeddings)

    return all_embeddings

class ConversationManager:
    """Manage multi-turn conversations with context."""

    def __init__(self, system_prompt: str = "You are a helpful assistant.", max_history: int = 10):
        self.messages = [{"role": "system", "content": system_prompt}]
        self.max_history = max_history

    def add_message(self, role: str, content: str):
        """Add a message to the conversation."""
        self.messages.append({"role": role, "content": content})

        # Keep only recent messages (plus system message)
        if len(self.messages) > self.max_history + 1:
            self.messages = [self.messages[0]] + self.messages[-(self.max_history):]

    @log_api_call
    def send(self, message: str, model: str = Config.DEFAULT_MODEL) -> str:
        """Send a message and get a response."""
        self.add_message("user", message)

        response = client.chat.completions.create(
            model=model,
            messages=self.messages
        )

        assistant_message = response.choices[0].message.content
        self.add_message("assistant", assistant_message)

        return assistant_message

    def reset(self):
        """Reset the conversation, keeping only the system message."""
        self.messages = [self.messages[0]]

# Example usage
if __name__ == "__main__":
    # Simple completion
    print("=== Simple Completion ===")
    response = create_completion(
        "What is machine learning?",
        temperature=0.7,
        max_tokens=200
    )
    print(response)

    # Batch embeddings
    print("\n=== Batch Embeddings ===")
    texts = [
        "Machine learning is a subset of AI",
        "Deep learning uses neural networks",
        "Natural language processing enables text understanding",
        "Computer vision allows machines to see"
    ]
    embeddings = batch_embeddings(texts)
    print(f"Created {len(embeddings)} embeddings, each with {len(embeddings[0])} dimensions")

    # Conversation management
    print("\n=== Conversation Manager ===")
    conversation = ConversationManager(
        system_prompt="You are a helpful Python programming assistant.",
        max_history=5
    )

    print("User: How do I read a file in Python?")
    response = conversation.send("How do I read a file in Python?")
    print(f"Assistant: {response}\n")

    print("User: What about writing to a file?")
    response = conversation.send("What about writing to a file?")
    print(f"Assistant: {response}")
```

---

## Additional Examples

### Rate Limiting and Throttling

```python
#!/usr/bin/env python3
"""Rate limiting example."""

import time
from openai import OpenAI
from collections import deque

class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, max_requests: int, time_window: float):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()

    def acquire(self):
        """Wait if necessary to respect rate limit."""
        now = time.time()

        # Remove old requests outside the time window
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()

        # If at limit, wait
        if len(self.requests) >= self.max_requests:
            sleep_time = self.requests[0] + self.time_window - now
            if sleep_time > 0:
                print(f"Rate limit reached, waiting {sleep_time:.2f}s...")
                time.sleep(sleep_time)
                return self.acquire()

        self.requests.append(now)

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1",
)

# Allow 3 requests per 5 seconds
rate_limiter = RateLimiter(max_requests=3, time_window=5.0)

# Make requests with rate limiting
for i in range(10):
    rate_limiter.acquire()
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": f"Request {i+1}"}]
    )
    print(f"Request {i+1} completed")
```

### Caching Responses

```python
#!/usr/bin/env python3
"""Response caching example."""

import hashlib
import json
from functools import lru_cache
from openai import OpenAI

client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",
    base_url="http://localhost:8000/v1",
)

def cache_key(model: str, messages: list) -> str:
    """Generate a cache key for a request."""
    content = json.dumps({"model": model, "messages": messages}, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()

# Simple in-memory cache
_cache = {}

def cached_completion(model: str, messages: list) -> str:
    """Create a completion with caching."""
    key = cache_key(model, messages)

    if key in _cache:
        print("Cache hit!")
        return _cache[key]

    print("Cache miss, calling API...")
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )

    result = response.choices[0].message.content
    _cache[key] = result
    return result

# Test caching
print("First call:")
result1 = cached_completion("openai/gpt-oss-120b", [{"role": "user", "content": "What is AI?"}])
print(result1[:100])

print("\nSecond call (same request):")
result2 = cached_completion("openai/gpt-oss-120b", [{"role": "user", "content": "What is AI?"}])
print(result2[:100])

print("\nThird call (different request):")
result3 = cached_completion("openai/gpt-oss-120b", [{"role": "user", "content": "What is ML?"}])
print(result3[:100])
```

---

## Testing and Development

### Using FakeAI for Unit Tests

```python
#!/usr/bin/env python3
"""Unit testing example with FakeAI."""

import unittest
from openai import OpenAI

class TestChatbot(unittest.TestCase):
    """Test cases for a chatbot using FakeAI."""

    @classmethod
    def setUpClass(cls):
        """Set up the test client."""
        cls.client = OpenAI(
            api_key="sk-fakeai-test",
            base_url="http://localhost:8000/v1",
        )

    def test_basic_completion(self):
        """Test basic chat completion."""
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Hello"}]
        )

        self.assertIsNotNone(response)
        self.assertEqual(len(response.choices), 1)
        self.assertIsNotNone(response.choices[0].message.content)

    def test_streaming(self):
        """Test streaming completion."""
        stream = self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Test"}],
            stream=True
        )

        chunks = list(stream)
        self.assertGreater(len(chunks), 0)

    def test_embeddings(self):
        """Test embedding creation."""
        response = self.client.embeddings.create(
            model="sentence-transformers/all-mpnet-base-v2",
            input="Test text"
        )

        self.assertEqual(len(response.data), 1)
        self.assertGreater(len(response.data[0].embedding), 0)

    def test_model_list(self):
        """Test listing models."""
        models = self.client.models.list()
        self.assertGreater(len(models.data), 0)

if __name__ == "__main__":
    unittest.main()
```

---

## Summary

This guide covered:

1. **Basic Usage**: Simple examples for chat, embeddings, and images
2. **Advanced Features**: Streaming, tools, structured outputs, multi-modal content
3. **Responses API**: New simplified API format with conversation continuation
4. **NIM Rankings**: Passage reranking for search applications
5. **Best Practices**: Error handling, async operations, rate limiting, caching

For more information:
- See the main [README.md](../README.md) for installation and setup
- Check [CLI_USAGE.md](../CLI_USAGE.md) for command-line options
- Review [API_KEY_GUIDE.md](../API_KEY_GUIDE.md) for authentication details

All examples are functional and ready to use with your FakeAI server!
