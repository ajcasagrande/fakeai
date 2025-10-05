# FakeAI: OpenAI Compatible API Server

[![PyPI version](https://badge.fury.io/py/fakeai.svg)](https://badge.fury.io/py/fakeai)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

This is a fully-featured FastAPI implementation that mimics the OpenAI API. It supports all endpoints and features of the official OpenAI API while returning simulated responses instead of performing actual inference.

## Features

- **Complete API Compatibility**: Implements all endpoints of the OpenAI API with the same request/response formats
- **Simulated Responses**: Generates realistic responses with appropriate delays to simulate real workloads
- **Streaming Support**: Supports streaming for both chat completions and text completions
- **Authentication**: Simulates API key authentication
- **Configurable**: Easy configuration options for response time, randomness, etc.

## Supported Endpoints

The server implements all major OpenAI API endpoints:

- `/v1/models` - List and retrieve models
- `/v1/chat/completions` - Chat completions (GPT-3.5, GPT-4, etc.)
- `/v1/completions` - Text completions
- `/v1/embeddings` - Text embeddings
- `/v1/images/generations` - DALL-E image generation
- `/v1/files` - File management
- `/v1/responses` - Text generation (Azure OpenAI compatibility)

## Requirements

- Python 3.10+
- FastAPI
- Uvicorn
- Pydantic
- Pydantic-Settings
- NumPy
- Faker
- Python-Multipart

## Installation

### Option 1: Install from PyPI (recommended)

```bash
pip install fakeai
```

### Option 2: Install from source

1. Clone the repository:

```bash
git clone https://github.com/ajcasagrande/fakeai.git
cd fakeai
```

2. Install the package in development mode:

```bash
pip install -e .
```

## Quick Start

### Option 1: Using the command-line tool

After installation, you can start the server using the provided command-line tool:

```bash
fakeai-server
```

### Option 2: Running the Python module

You can also run the server as a Python module:

```bash
python -m fakeai.run_server
```

### Option 3: For development

During development, you can run the server directly from the source directory:

```bash
python run_server.py
```

The server will be running at `http://localhost:8000` by default, and you can access the FastAPI documentation at `http://localhost:8000/docs`

## Configuration

The server can be configured using environment variables:

- `FAKEAI_HOST`: Host to bind the server (default: `127.0.0.1`)
- `FAKEAI_PORT`: Port to bind the server (default: `8000`)
- `FAKEAI_DEBUG`: Enable debug mode (`true` or `false`, default: `false`)
- `FAKEAI_RESPONSE_DELAY`: Base delay for responses in seconds (default: `0.5`)
- `FAKEAI_RANDOM_DELAY`: Add random variation to response delays (`true` or `false`, default: `true`)
- `FAKEAI_MAX_VARIANCE`: Maximum variance for random delays as a factor (default: `0.3`)
- `FAKEAI_API_KEYS`: Comma-separated list of valid API keys (default: `sk-fakeai-1234567890abcdef,sk-test-abcdefghijklmnop`)
- `FAKEAI_REQUIRE_API_KEY`: Whether to require API key authentication (`true` or `false`, default: `true`)

## Example Usage with OpenAI Python Client

Once the server is running, you can use it with the official OpenAI Python client:

```python
from openai import OpenAI

# Initialize the client with the FakeAI server URL
client = OpenAI(
    api_key="sk-fakeai-1234567890abcdef",  # Any key from the allowed list
    base_url="http://localhost:8000",
)

# Example: Chat completion
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me about artificial intelligence."}
    ]
)
print(response.choices[0].message.content)

# Example: Streaming chat completion
for chunk in client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Write a short poem about technology."}
    ],
    stream=True
):
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
    
# Example: Embeddings
response = client.embeddings.create(
    model="text-embedding-ada-002",
    input="The quick brown fox jumps over the lazy dog."
)
print(f"Embedding dimensions: {len(response.data[0].embedding)}")
```

## Using FakeAI as a Library

You can also use FakeAI programmatically in your Python code:

```python
from fakeai import app, AppConfig

# Create a custom configuration
config = AppConfig(
    host="0.0.0.0",  # Allow external connections
    port=9000,       # Use a different port
    debug=True,      # Enable debug mode
    require_api_key=False  # Disable API key requirement
)

# Access the FastAPI app
app_instance = app  # Use this for more advanced FastAPI configuration

# Run the server programmatically
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fakeai:app", host=config.host, port=config.port, reload=config.debug)
```

## Advanced Usage

### Custom Response Generation

The server uses a `SimulatedGenerator` class to generate responses based on the input. You can customize the response generation logic in `fakeai_service.py` to better suit your needs.

### Response Timing Simulation

The server simulates realistic response times based on factors like:

- Model complexity (e.g., GPT-4 is slower than GPT-3.5)
- Input length
- Output length
- Temperature setting

These timings can be adjusted in the `FakeAIService` class.

### Key Components

The main components of FakeAI are:

- `FakeAIService` - The core service that simulates the OpenAI API endpoints
- `SimulatedGenerator` - A utility for generating realistic responses
- `AppConfig` - Configuration settings with environment variable support (via `FAKEAI_` prefix)

### Error Simulation

You can test error handling by:

- Using an invalid API key (e.g., "invalid")
- Requesting a non-existent model
- Using an invalid file ID

## Comparing with the Real API

This server aims to be a drop-in replacement for the real OpenAI API in development and testing environments. The key differences are:

1. **Response Quality**: Generated responses are simplistic compared to actual AI models
2. **Performance**: Simulated responses are generated much faster than actual inference
3. **Cost**: No tokens are consumed, making it ideal for development and testing

## Use Cases

- Development and testing of applications that use the OpenAI API
- CI/CD pipelines where you want to avoid actual API calls
- Demos and presentations that don't require actual AI responses
- Testing error handling and edge cases
- Performance testing with controlled response times

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## Development

### Setup development environment

1. Clone the repository:
```bash
git clone https://github.com/ajcasagrande/fakeai.git
cd fakeai
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install in development mode:
```bash
pip install -e ".[dev]"
```

### Running tests

```bash
pytest
```

### Code formatting

```bash
black .
isort .
```

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
