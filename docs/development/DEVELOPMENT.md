# Development Guide

This guide provides information for developers who want to contribute to or extend FakeAI.

## Table of Contents

- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Architecture Overview](#architecture-overview)
- [Key Components](#key-components)
- [Adding New Features](#adding-new-features)
- [Code Organization](#code-organization)
- [Best Practices](#best-practices)
- [Development Workflow](#development-workflow)
- [Contributing](#contributing)

---

## Project Structure

```
fakeai/
 fakeai/                      # Main package directory
    __init__.py             # Package initialization
    app.py                  # FastAPI application and endpoints
    models.py               # Pydantic models and schemas
    fakeai_service.py       # Core service implementation
    config.py               # Configuration management
    utils.py                # Utility functions
    metrics.py              # Metrics tracking
    cli.py                  # Command-line interface

 examples/                    # Example scripts
    example_client.py       # Basic client usage
    streaming_client.py     # Streaming examples
    test_metrics.py         # Metrics examples

 tests/                       # Test files
    test_complete_implementation.py
    test_api_key_system.py
    test_cli.py

 docs/                        # Documentation
    ENDPOINTS.md            # API endpoint reference
    SCHEMAS.md              # Schema documentation
    MULTIMODAL.md           # Multi-modal guide
    TOOL_CALLING.md         # Tool calling guide
    TESTING.md              # Testing guide
    DEVELOPMENT.md          # This file

 pyproject.toml              # Project configuration
 README.md                   # Main documentation
 LICENSE                     # Apache 2.0 license
 run_server.py               # Development server script
```

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Virtual environment tool (venv, virtualenv, or conda)

### Setting Up Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ajcasagrande/fakeai.git
   cd fakeai
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install in development mode:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify installation:**
   ```bash
   python -c "import fakeai; print(fakeai.__version__)"
   ```

5. **Run tests:**
   ```bash
   python test_complete_implementation.py
   ```

6. **Start development server:**
   ```bash
   python run_server.py
   ```

---

## Architecture Overview

### High-Level Architecture

```

   FastAPI App   
    (app.py)     

         
         > Authentication Middleware
         
         > Request Logging Middleware
         
         
                                      
                                      
          
  FakeAI Service             Metrics Tracker 
 (fakeai_service)             (metrics.py)   
          
         
         > SimulatedGenerator (utils.py)
         
         > AsyncExecutor (utils.py)
```

### Request Flow

1. **Client Request** → FastAPI endpoint
2. **Authentication** → API key verification
3. **Request Logging** → Metrics tracking
4. **Service Method** → Business logic execution
5. **Response Generation** → Simulated AI response
6. **Response Return** → JSON or streaming response

---

## Key Components

### 1. FastAPI Application (app.py)

**Purpose**: Defines HTTP endpoints and handles requests.

**Key Responsibilities**:
- Endpoint routing
- Request/response handling
- Authentication middleware
- CORS configuration
- Error handling

**Example - Adding a new endpoint**:
```python
@app.post("/v1/custom/endpoint")
async def custom_endpoint(
    request: CustomRequest,
    api_key: str = Depends(verify_api_key)
):
    """Custom endpoint implementation."""
    return await fakeai_service.handle_custom_request(request)
```

### 2. Models (models.py)

**Purpose**: Define Pydantic models for request/response validation.

**Key Responsibilities**:
- Schema validation
- Type checking
- Default values
- Field constraints

**Example - Adding a new model**:
```python
class CustomRequest(BaseModel):
    """Custom request model."""

    model: str = Field(description="Model identifier")
    input: str = Field(description="Input text")
    max_tokens: int | None = Field(
        default=100,
        ge=1,
        le=4096,
        description="Maximum tokens"
    )
```

### 3. FakeAI Service (fakeai_service.py)

**Purpose**: Core business logic for generating simulated responses.

**Key Responsibilities**:
- Model management
- Response generation
- Token calculation
- Delay simulation

**Example - Adding a new service method**:
```python
async def handle_custom_request(
    self, request: CustomRequest
) -> CustomResponse:
    """Handle custom request."""
    # Ensure model exists
    self._ensure_model_exists(request.model)

    # Generate response
    output = await self._generate_simulated_completion(
        messages=[Message(role=Role.USER, content=request.input)],
        max_tokens=request.max_tokens or 100,
        temperature=1.0
    )

    # Calculate tokens
    input_tokens = calculate_token_count(request.input)
    output_tokens = calculate_token_count(output)

    # Return response
    return CustomResponse(
        id=f"custom-{uuid.uuid4().hex}",
        output=output,
        usage=Usage(
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens
        )
    )
```

### 4. Configuration (config.py)

**Purpose**: Manage application configuration via environment variables.

**Key Responsibilities**:
- Environment variable loading
- Configuration validation
- Default values

**Example - Adding a new config option**:
```python
class AppConfig(BaseSettings):
    """Application configuration."""

    # Existing fields...

    custom_feature_enabled: bool = Field(
        default=False,
        description="Enable custom feature"
    )

    custom_timeout: float = Field(
        default=5.0,
        description="Timeout for custom operations"
    )

    class Config:
        env_prefix = "FAKEAI_"
```

### 5. Utilities (utils.py)

**Purpose**: Helper functions and utility classes.

**Key Components**:
- **SimulatedGenerator**: Generates realistic text responses
- **AsyncExecutor**: Handles async operations with delays
- **Token calculation**: Estimates token counts
- **Embedding generation**: Creates random embeddings

**Example - Adding a utility function**:
```python
def validate_custom_input(input_text: str) -> bool:
    """Validate custom input format."""
    if not input_text or len(input_text) > 10000:
        return False
    return True
```

### 6. Metrics (metrics.py)

**Purpose**: Track and report server metrics.

**Key Responsibilities**:
- Request counting
- Response time tracking
- Error tracking
- Token usage tracking

**Example - Adding a new metric**:
```python
class MetricsTracker:
    """Track server metrics."""

    def __init__(self):
        # Existing metrics...
        self.custom_metric: dict[str, int] = defaultdict(int)

    def track_custom_event(self, event_type: str):
        """Track custom event."""
        self.custom_metric[event_type] += 1
```

---

## Adding New Features

### Adding a New Endpoint

**Step 1: Define Request/Response Models** (models.py)

```python
class NewFeatureRequest(BaseModel):
    """Request for new feature."""
    model: str = Field(description="Model to use")
    input_data: str = Field(description="Input data")
    option: bool = Field(default=False, description="Feature option")


class NewFeatureResponse(BaseModel):
    """Response from new feature."""
    id: str = Field(description="Unique identifier")
    output: str = Field(description="Generated output")
    usage: Usage = Field(description="Token usage")
```

**Step 2: Implement Service Method** (fakeai_service.py)

```python
async def process_new_feature(
    self, request: NewFeatureRequest
) -> NewFeatureResponse:
    """Process new feature request."""
    # Ensure model exists
    self._ensure_model_exists(request.model)

    # Generate response
    output = await self._generate_simulated_completion(
        messages=[Message(role=Role.USER, content=request.input_data)],
        max_tokens=100,
        temperature=1.0
    )

    # Calculate tokens
    input_tokens = calculate_token_count(request.input_data)
    output_tokens = calculate_token_count(output)

    return NewFeatureResponse(
        id=f"feat-{uuid.uuid4().hex}",
        output=output,
        usage=Usage(
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens
        )
    )
```

**Step 3: Add Endpoint** (app.py)

```python
@app.post("/v1/new-feature", dependencies=[Depends(verify_api_key)])
async def new_feature_endpoint(
    request: NewFeatureRequest
) -> NewFeatureResponse:
    """New feature endpoint."""
    return await fakeai_service.process_new_feature(request)
```

**Step 4: Add Tests** (test_complete_implementation.py)

```python
def test_new_feature_endpoint():
    """Test new feature endpoint."""
    from fastapi.testclient import TestClient
    from fakeai.app import app
    import os

    os.environ["FAKEAI_REQUIRE_API_KEY"] = "false"
    client = TestClient(app)

    response = client.post("/v1/new-feature", json={
        "model": "openai/gpt-oss-120b",
        "input_data": "Test input",
        "option": True
    })

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "output" in data
    assert "usage" in data
    print("[PASS] Test: new_feature_endpoint")
```

**Step 5: Update Documentation**

Add endpoint documentation to `docs/ENDPOINTS.md`.

### Adding a New Pydantic Model

**Step 1: Define Model** (models.py)

```python
class NewModel(BaseModel):
    """Description of new model."""

    field1: str = Field(description="First field")
    field2: int = Field(ge=0, le=100, description="Second field")
    optional_field: str | None = Field(
        default=None,
        description="Optional field"
    )
```

**Step 2: Add Validation**

```python
from pydantic import field_validator

class NewModel(BaseModel):
    """Description of new model."""

    field1: str = Field(description="First field")
    field2: int = Field(ge=0, le=100, description="Second field")

    @field_validator("field1")
    def validate_field1(cls, v: str) -> str:
        """Validate field1."""
        if not v.strip():
            raise ValueError("field1 cannot be empty")
        return v
```

**Step 3: Add Tests**

```python
def test_new_model():
    """Test new model validation."""
    from fakeai.models import NewModel
    from pydantic import ValidationError

    # Valid model
    model = NewModel(field1="value", field2=50)
    assert model.field1 == "value"
    assert model.field2 == 50

    # Invalid model
    try:
        invalid = NewModel(field1="", field2=150)
        assert False, "Should raise ValidationError"
    except ValidationError:
        pass  # Expected
```

---

## Code Organization

### Import Structure

```python
# Standard library imports
import asyncio
import json
import time
from typing import Any

# Third-party imports
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Local imports
from fakeai.config import AppConfig
from fakeai.models import ChatCompletionRequest
from fakeai.utils import calculate_token_count
```

### Module Organization

Each module should have:
1. Module docstring
2. License information
3. Imports (grouped as shown above)
4. Constants
5. Classes
6. Functions

**Example**:
```python
"""
Module description.

This module provides functionality for...
"""
#  SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3


class MyClass:
    """Class description."""
    pass


def my_function() -> None:
    """Function description."""
    pass
```

### Naming Conventions

- **Classes**: PascalCase (e.g., `ChatCompletionRequest`)
- **Functions**: snake_case (e.g., `create_chat_completion`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_PORT`)
- **Private methods**: Leading underscore (e.g., `_ensure_model_exists`)
- **Type hints**: Always use type hints

---

## Best Practices

### 1. Type Hints

Always use type hints for function parameters and return values:

```python
def calculate_tokens(text: str, model: str = "openai/gpt-oss-120b") -> int:
    """Calculate token count."""
    return len(text.split())

async def fetch_data(url: str) -> dict[str, Any]:
    """Fetch data from URL."""
    pass
```

### 2. Docstrings

Use Google-style docstrings:

```python
def process_request(request: Request, timeout: float = 30.0) -> Response:
    """Process incoming request.

    Args:
        request: The incoming request object
        timeout: Maximum time to wait in seconds

    Returns:
        Response object with processed data

    Raises:
        TimeoutError: If processing exceeds timeout
        ValueError: If request is invalid
    """
    pass
```

### 3. Error Handling

Handle errors gracefully:

```python
async def process_data(data: dict) -> dict:
    """Process data with error handling."""
    try:
        result = await perform_operation(data)
        return result
    except KeyError as e:
        logger.error(f"Missing required key: {e}")
        raise ValueError(f"Invalid data structure: missing {e}")
    except Exception as e:
        logger.exception("Unexpected error during processing")
        raise
```

### 4. Async/Await

Use async/await for I/O operations:

```python
async def fetch_multiple_resources(urls: list[str]) -> list[dict]:
    """Fetch multiple resources concurrently."""
    tasks = [fetch_resource(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return results
```

### 5. Pydantic Models

Use Pydantic for data validation:

```python
class RequestModel(BaseModel):
    """Request model with validation."""

    field1: str = Field(min_length=1, max_length=100)
    field2: int = Field(ge=0, le=1000)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"field1": "example", "field2": 42}
            ]
        }
    }
```

### 6. Logging

Use appropriate logging levels:

```python
import logging

logger = logging.getLogger(__name__)

def process_item(item: dict) -> None:
    """Process item with logging."""
    logger.debug(f"Processing item: {item['id']}")

    try:
        result = perform_operation(item)
        logger.info(f"Successfully processed item {item['id']}")
    except Exception as e:
        logger.error(f"Failed to process item {item['id']}: {e}")
        raise
```

### 7. Configuration

Use environment variables for configuration:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""

    api_key: str
    timeout: float = 30.0
    debug: bool = False

    class Config:
        env_prefix = "MYAPP_"
```

### 8. Testing

Write tests for all new features:

```python
def test_new_feature():
    """Test new feature."""
    # Arrange
    input_data = {"key": "value"}

    # Act
    result = process_feature(input_data)

    # Assert
    assert result["status"] == "success"
    assert "output" in result
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/my-new-feature
```

### 2. Make Changes

Edit files, add features, fix bugs.

### 3. Run Tests

```bash
# Run all tests
python test_complete_implementation.py

# Run pytest
pytest -v

# Run specific test
pytest test_complete_implementation.py::test_schema_compliance
```

### 4. Format Code

```bash
# Format with black
black .

# Sort imports with isort
isort .

# Check formatting
black --check .
isort --check-only .
```

### 5. Commit Changes

```bash
git add .
git commit -m "Add new feature: description"
```

### 6. Push and Create PR

```bash
git push origin feature/my-new-feature
```

Then create a pull request on GitHub.

---

## Contributing

### Contribution Guidelines

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests** for new functionality
5. **Update documentation**
6. **Run tests** to ensure nothing broke
7. **Format code** with black and isort
8. **Commit with clear messages**
9. **Push to your fork**
10. **Create a pull request**

### Code Review Process

1. All changes require review
2. Tests must pass
3. Code must be formatted
4. Documentation must be updated
5. Maintain backward compatibility

### Commit Message Format

```
type: short description

Longer description if needed.

Fixes #123
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

---

## Additional Resources

### Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)

### OpenAI API Reference

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [OpenAI Chat Completions](https://platform.openai.com/docs/guides/chat-completions)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)

### Project Links

- [GitHub Repository](https://github.com/ajcasagrande/fakeai)
- [PyPI Package](https://pypi.org/project/fakeai/)
- [Issue Tracker](https://github.com/ajcasagrande/fakeai/issues)

---

## Questions and Support

For questions or support:

1. Check existing documentation
2. Search [GitHub Issues](https://github.com/ajcasagrande/fakeai/issues)
3. Create a new issue if needed
4. Join community discussions

---

## License

FakeAI is licensed under the Apache License 2.0. See the [LICENSE](../LICENSE) file for details.
