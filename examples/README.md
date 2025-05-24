# FakeAI Examples

This directory contains example clients that demonstrate how to use the FakeAI server with the OpenAI Python client library.

## Overview

FakeAI is an OpenAI-compatible API server that simulates AI model responses. These examples show how to interact with the FakeAI server using the official OpenAI client libraries. They demonstrate various features including basic API calls, streaming functionality, and more complex interaction patterns.

## Getting Started

Before running the examples, make sure:

1. The FakeAI server is running on your machine
2. You have the OpenAI Python client installed

To start the FakeAI server:

```bash
# Install FakeAI if you haven't already
pip install fakeai

# Start the server
fakeai-server
```

## Available Examples

### 1. Example Client (`example_client.py`)

A comprehensive example that demonstrates various FakeAI features:

- Listing available models
- Basic chat completions
- Streaming chat completions
- Text completions
- Embeddings generation
- Image generation

**Usage:**
```bash
python example_client.py
```
or
```bash
./example_client.py
```

### 2. Streaming Client (`streaming_client.py`)

A specialized example focusing on streaming capabilities with more advanced use cases:

- Simple streaming chat: Basic token-by-token output
- Collecting full responses: Accumulating streamed tokens
- Interactive streaming: Real-time token processing with timing information
- Multi-message conversations: Managing context in streaming conversations
- Multiple concurrent completions: Running multiple streaming requests in parallel
- Advanced stream processing: Detailed event handling with a custom handler

**Usage:**
```bash
python streaming_client.py
```
or
```bash
./streaming_client.py
```

## Example Details

### Example Client

The `example_client.py` script demonstrates:

1. **Model Listing**: Shows how to retrieve the list of available models from the FakeAI server.

2. **Chat Completion**: Demonstrates a basic chat completion request with system and user messages.

3. **Streaming Chat Completion**: Shows how to handle streaming responses for more responsive user interfaces.

4. **Text Completion**: Demonstrates the older-style completion API.

5. **Embedding Generation**: Shows how to generate embeddings for text, useful for semantic search and other vector operations.

6. **Image Generation**: Demonstrates how to generate images using the DALL-E compatible endpoint.

### Streaming Client

The `streaming_client.py` script provides in-depth examples of streaming functionality:

1. **Simple Streaming Chat**: The most basic streaming example that prints tokens as they arrive.

2. **Collecting Full Response**: Shows how to accumulate streamed tokens into a complete response while showing progress indicators.

3. **Interactive Streaming**: Demonstrates real-time processing of tokens with timing information - useful for creating responsive interfaces or analyzing token generation speed.

4. **Multi-message Conversation**: Shows how to maintain conversation context while streaming responses, simulating a chatbot interaction.

5. **Multiple Concurrent Completions**: Demonstrates how to manage multiple streaming completions simultaneously using asyncio - useful for batch processing or parallel operations.

6. **Advanced Stream Processing**: Shows detailed handling of streaming events including metadata, finish reasons, and comprehensive token analytics.

## API Configuration

Both examples connect to the FakeAI server with these default settings:

```python
client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",  # Any key from the allowed list
    base_url="http://localhost:8000/v1",
)
```

You can modify these settings if you've configured your FakeAI server differently.

## Customization

These examples can be used as starting points for your own applications. You can:

- Modify the prompts to test different response patterns
- Adjust model parameters (temperature, max_tokens, etc.) to see how they affect responses
- Build upon the conversation examples to create more complex dialogue flows
- Integrate the streaming examples into your own user interfaces

## Error Handling

Both examples include basic error handling. If you encounter errors:

1. Ensure the FakeAI server is running and accessible
2. Check that you're using the correct API key format
3. Verify the base URL matches your FakeAI server configuration

## Additional Resources

For more information, refer to:

- [FakeAI Documentation](https://github.com/ajcasagrande/fakeai#readme)
- [OpenAI Python Library Documentation](https://github.com/openai/openai-python)

## License

These examples are provided under the Apache-2.0 license.
