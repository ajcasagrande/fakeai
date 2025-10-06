# Testing Guide

This document explains how to test FakeAI and write new tests.

## Table of Contents

- [Overview](#overview)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Writing New Tests](#writing-new-tests)
- [Test Patterns](#test-patterns)
- [Testing Endpoints](#testing-endpoints)
- [Testing Schemas](#testing-schemas)
- [Testing Services](#testing-services)
- [Continuous Integration](#continuous-integration)

---

## Overview

FakeAI includes a comprehensive test suite that validates:
- Schema compliance for all Pydantic models
- Service method implementations
- API endpoint integration
- Multi-modal content handling
- Tool calling functionality
- Structured outputs
- Streaming responses
- Token usage tracking

The test suite is designed to ensure 100% compatibility with OpenAI API specifications.

---

## Running Tests

### Using the Test Script

The project includes a comprehensive test script that validates all implementations:

```bash
# Run the complete test suite
python test_complete_implementation.py
```

This script runs three test suites:
1. **Schema Compliance Tests** - Validates all Pydantic models
2. **Service Method Tests** - Tests service implementations
3. **API Endpoint Tests** - Tests HTTP endpoints

### Using pytest

If you have pytest installed, you can run tests using pytest:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest test_complete_implementation.py

# Run specific test function
pytest test_complete_implementation.py::test_schema_compliance
```

### Running Individual Test Files

You can also run individual test files directly:

```bash
# API key system tests
python test_api_key_system.py

# CLI tests
python test_cli.py

# Complete implementation tests
python test_complete_implementation.py
```

---

## Test Structure

### Test Organization

The test suite is organized into three main categories:

```
test_complete_implementation.py
 test_schema_compliance()      # Schema validation tests
 test_service_methods()         # Service logic tests
 test_api_endpoints()           # HTTP endpoint tests
```

### Test Files

- **test_complete_implementation.py** - Main test suite for schema and API compliance
- **test_api_key_system.py** - API key authentication tests
- **test_cli.py** - Command-line interface tests

---

## Writing New Tests

### Test Function Template

```python
def test_new_feature():
    """Test description."""
    # Arrange - Set up test data
    from fakeai.models import SomeModel

    test_data = {...}

    # Act - Execute the code being tested
    result = SomeModel(**test_data)

    # Assert - Verify the results
    assert result.field == expected_value
    assert result.is_valid()
```

### Schema Compliance Test Template

```python
def test_new_schema_model():
    """Test new Pydantic model schema."""
    from fakeai.models import NewModel, NestedModel

    tests_passed = 0
    tests_total = 1

    try:
        # Create instance with all fields
        model = NewModel(
            field1="value1",
            field2=42,
            nested=NestedModel(
                nested_field="nested_value"
            )
        )

        # Validate fields
        assert model.field1 == "value1"
        assert model.field2 == 42
        assert model.nested.nested_field == "nested_value"

        # Validate model dump
        data = model.model_dump()
        assert "field1" in data
        assert "field2" in data

        print("[PASS] Test: NewModel validation")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] Test: NewModel validation - {e}")

    return tests_passed == tests_total
```

### Service Method Test Template

```python
def test_new_service_method():
    """Test service method implementation."""
    import asyncio
    from fakeai.fakeai_service import FakeAIService
    from fakeai.config import AppConfig
    from fakeai.models import RequestModel

    config = AppConfig()
    service = FakeAIService(config)

    async def test():
        # Create request
        request = RequestModel(
            field1="value1",
            field2=42
        )

        # Call service method
        response = await service.new_method(request)

        # Validate response
        assert response.result is not None
        assert response.status == "success"
        return True

    result = asyncio.run(test())
    assert result
    print("[PASS] Test: new_service_method")
```

### API Endpoint Test Template

```python
def test_new_api_endpoint():
    """Test HTTP endpoint."""
    from fastapi.testclient import TestClient
    from fakeai.app import app
    import os

    # Disable auth for testing
    os.environ["FAKEAI_REQUIRE_API_KEY"] = "false"
    client = TestClient(app)

    # Make request
    response = client.post("/v1/new/endpoint", json={
        "field1": "value1",
        "field2": 42
    })

    # Validate response
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["status"] == "success"

    print("[PASS] Test: POST /v1/new/endpoint")
```

---

## Test Patterns

### Pattern 1: Testing Pydantic Models

```python
def test_pydantic_model():
    """Test Pydantic model validation."""
    from fakeai.models import ChatCompletionRequest, Message, Role

    # Test valid input
    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[
            Message(role=Role.USER, content="Hello")
        ]
    )
    assert request.model == "openai/gpt-oss-120b"
    assert len(request.messages) == 1

    # Test default values
    assert request.temperature == 1.0
    assert request.stream == False

    # Test validation
    try:
        invalid_request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[],  # Empty messages should fail
            temperature=3.0  # Out of range
        )
        assert False, "Should have raised validation error"
    except Exception:
        pass  # Expected
```

### Pattern 2: Testing Async Functions

```python
def test_async_service_method():
    """Test asynchronous service method."""
    import asyncio
    from fakeai.fakeai_service import FakeAIService
    from fakeai.config import AppConfig

    config = AppConfig()
    service = FakeAIService(config)

    async def run_test():
        # Test async method
        response = await service.list_models()
        assert response.object == "list"
        assert len(response.data) > 0
        return True

    result = asyncio.run(run_test())
    assert result
```

### Pattern 3: Testing Streaming Responses

```python
def test_streaming_response():
    """Test streaming endpoint."""
    from fastapi.testclient import TestClient
    from fakeai.app import app

    client = TestClient(app)

    with client.stream("POST", "/v1/chat/completions", json={
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": True
    }) as response:
        assert response.status_code == 200

        chunks = []
        for line in response.iter_lines():
            if line.startswith("data: "):
                data = line[6:]  # Remove "data: " prefix
                if data != "[DONE]":
                    chunks.append(data)

        assert len(chunks) > 0
```

### Pattern 4: Testing Error Conditions

```python
def test_error_handling():
    """Test error responses."""
    from fastapi.testclient import TestClient
    from fakeai.app import app
    import os

    os.environ["FAKEAI_REQUIRE_API_KEY"] = "true"
    client = TestClient(app)

    # Test missing API key
    response = client.get("/v1/models")
    assert response.status_code == 401

    # Test invalid API key
    response = client.get(
        "/v1/models",
        headers={"Authorization": "Bearer invalid-key"}
    )
    assert response.status_code == 401

    # Test invalid model
    os.environ["FAKEAI_REQUIRE_API_KEY"] = "false"
    response = client.post("/v1/chat/completions", json={
        "model": "invalid-model",
        "messages": [{"role": "user", "content": "Hi"}]
    })
    # Should still work (FakeAI creates models dynamically)
    assert response.status_code == 200
```

### Pattern 5: Testing Multi-Modal Content

```python
def test_multimodal_content():
    """Test multi-modal message content."""
    from fakeai.models import (
        Message, Role, TextContent, ImageContent, ImageUrl
    )

    # Create multi-modal message
    message = Message(
        role=Role.USER,
        content=[
            TextContent(text="What's in this image?"),
            ImageContent(
                image_url=ImageUrl(
                    url="https://example.com/image.jpg",
                    detail="high"
                )
            )
        ]
    )

    # Validate
    assert len(message.content) == 2
    assert message.content[0].type == "text"
    assert message.content[1].type == "image_url"
    assert message.content[1].image_url.detail == "high"
```

---

## Testing Endpoints

### Testing with FastAPI TestClient

FastAPI provides a test client that doesn't require running the server:

```python
from fastapi.testclient import TestClient
from fakeai.app import app

def test_endpoint():
    client = TestClient(app)

    # Test GET request
    response = client.get("/v1/models")
    assert response.status_code == 200

    # Test POST request
    response = client.post("/v1/chat/completions", json={
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": "Hello"}]
    })
    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
```

### Testing with Real HTTP Client

You can also test with actual HTTP requests (requires running server):

```python
import httpx

def test_with_httpx():
    """Test with real HTTP client."""
    # Assumes server is running on localhost:8000
    response = httpx.get("http://localhost:8000/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Testing Authentication

```python
def test_authentication():
    """Test API key authentication."""
    from fastapi.testclient import TestClient
    from fakeai.app import app
    import os

    os.environ["FAKEAI_REQUIRE_API_KEY"] = "true"
    os.environ["FAKEAI_API_KEYS"] = "test-key-1,test-key-2"

    client = TestClient(app)

    # Test without key
    response = client.get("/v1/models")
    assert response.status_code == 401

    # Test with valid key
    response = client.get(
        "/v1/models",
        headers={"Authorization": "Bearer test-key-1"}
    )
    assert response.status_code == 200

    # Test with invalid key
    response = client.get(
        "/v1/models",
        headers={"Authorization": "Bearer invalid-key"}
    )
    assert response.status_code == 401
```

---

## Testing Schemas

### Validating Required Fields

```python
def test_required_fields():
    """Test required field validation."""
    from fakeai.models import ChatCompletionRequest, Message
    from pydantic import ValidationError

    # Should fail without required fields
    try:
        request = ChatCompletionRequest()
        assert False, "Should raise ValidationError"
    except ValidationError as e:
        assert "model" in str(e)
        assert "messages" in str(e)
```

### Validating Field Types

```python
def test_field_types():
    """Test field type validation."""
    from fakeai.models import ChatCompletionRequest, Message, Role
    from pydantic import ValidationError

    # Valid types
    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[Message(role=Role.USER, content="Hi")],
        temperature=0.7,
        max_tokens=100
    )
    assert isinstance(request.temperature, float)
    assert isinstance(request.max_tokens, int)

    # Invalid types
    try:
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hi")],
            temperature="invalid"  # Should be float
        )
        assert False, "Should raise ValidationError"
    except ValidationError:
        pass  # Expected
```

### Validating Field Constraints

```python
def test_field_constraints():
    """Test field constraint validation."""
    from fakeai.models import ChatCompletionRequest, Message, Role
    from pydantic import ValidationError

    # Temperature out of range
    try:
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hi")],
            temperature=3.0  # Max is 2.0
        )
        assert False, "Should raise ValidationError"
    except ValidationError:
        pass  # Expected

    # Valid range
    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[Message(role=Role.USER, content="Hi")],
        temperature=1.5
    )
    assert request.temperature == 1.5
```

---

## Testing Services

### Testing Model Listing

```python
def test_list_models():
    """Test model listing service method."""
    import asyncio
    from fakeai.fakeai_service import FakeAIService
    from fakeai.config import AppConfig

    config = AppConfig()
    service = FakeAIService(config)

    async def test():
        response = await service.list_models()
        assert response.object == "list"
        assert len(response.data) > 0
        assert any(m.id == "openai/gpt-oss-120b" for m in response.data)
        return True

    assert asyncio.run(test())
```

### Testing Chat Completions

```python
def test_chat_completion():
    """Test chat completion service method."""
    import asyncio
    from fakeai.fakeai_service import FakeAIService
    from fakeai.config import AppConfig
    from fakeai.models import ChatCompletionRequest, Message, Role

    config = AppConfig()
    service = FakeAIService(config)

    async def test():
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                Message(role=Role.USER, content="Hello")
            ]
        )

        response = await service.create_chat_completion(request)
        assert response.id is not None
        assert response.model == "openai/gpt-oss-120b"
        assert len(response.choices) > 0
        assert response.choices[0].message.role == Role.ASSISTANT
        assert response.choices[0].message.content is not None
        assert response.usage.total_tokens > 0
        return True

    assert asyncio.run(test())
```

### Testing Embeddings

```python
def test_embeddings():
    """Test embeddings service method."""
    import asyncio
    from fakeai.fakeai_service import FakeAIService
    from fakeai.config import AppConfig
    from fakeai.models import EmbeddingRequest

    config = AppConfig()
    service = FakeAIService(config)

    async def test():
        request = EmbeddingRequest(
            model="sentence-transformers/all-mpnet-base-v2",
            input="Hello world"
        )

        response = await service.create_embedding(request)
        assert response.object == "list"
        assert len(response.data) == 1
        assert len(response.data[0].embedding) > 0
        assert response.usage.prompt_tokens > 0
        return True

    assert asyncio.run(test())
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests
        run: |
          python test_complete_implementation.py
          pytest -v

      - name: Check code formatting
        run: |
          black --check .
          isort --check-only .
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.10

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

---

## Best Practices

1. **Test Coverage**: Aim for high test coverage of critical paths
2. **Isolated Tests**: Each test should be independent
3. **Clear Names**: Use descriptive test function names
4. **Arrange-Act-Assert**: Follow the AAA pattern
5. **Error Cases**: Test both success and failure scenarios
6. **Mock External Dependencies**: Use mocks for external services
7. **Fast Tests**: Keep tests fast by avoiding unnecessary delays
8. **Documentation**: Document complex test setups
9. **Continuous Integration**: Run tests automatically on commits
10. **Regular Updates**: Update tests when adding new features

---

## Running Tests in Development

### Quick Test Command

```bash
# Run all tests quickly
python test_complete_implementation.py
```

### Watch Mode (with pytest-watch)

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests on file changes
ptw
```

### Testing Specific Features

```bash
# Test only schemas
pytest -k "schema"

# Test only API endpoints
pytest -k "endpoint"

# Test only service methods
pytest -k "service"
```

---

## Troubleshooting Tests

### Tests Failing Due to Environment

**Problem**: Tests fail because of environment configuration.

**Solution**: Reset environment variables before tests:

```python
import os

def setup_test_environment():
    os.environ["FAKEAI_REQUIRE_API_KEY"] = "false"
    os.environ["FAKEAI_DEBUG"] = "false"
```

### Async Tests Not Running

**Problem**: Async test functions not executing properly.

**Solution**: Use `asyncio.run()` or pytest-asyncio:

```python
import asyncio

def test_async_function():
    async def run():
        result = await async_function()
        assert result is not None

    asyncio.run(run())
```

### Import Errors

**Problem**: Cannot import fakeai modules.

**Solution**: Install in development mode:

```bash
pip install -e .
```

---

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validation/)
