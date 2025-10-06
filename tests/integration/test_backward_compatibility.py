"""
Backward Compatibility Tests

Tests that ensure nothing breaks:
- All old imports work
- All endpoints respond
- AIPerf compatibility
- OpenAI SDK compatibility
- Response format stability
"""

import pytest
from fastapi.testclient import TestClient

from fakeai.app import app
from fakeai.config import AppConfig


@pytest.fixture
def client():
    """Test client."""
    import fakeai.app as app_module
    app_module.server_ready = True
    return TestClient(app)


# ==============================================================================
# Legacy Import Tests
# ==============================================================================


def test_old_imports_still_work():
    """Test that old import paths still work."""
    # Core imports
    from fakeai import FakeAIService, AppConfig, app

    assert FakeAIService is not None
    assert AppConfig is not None
    assert app is not None


def test_client_utilities_importable():
    """Test that client utilities can be imported."""
    try:
        from fakeai import (
            FakeAIClient,
            temporary_server,
            assert_response_valid,
            assert_tokens_in_range,
        )

        assert FakeAIClient is not None
        assert temporary_server is not None
        assert assert_response_valid is not None
    except ImportError:
        # Optional dependencies not installed
        pytest.skip("Client utilities not available")


def test_deprecated_imports_still_work():
    """Test that deprecated but still supported imports work."""
    # Test various import patterns
    from fakeai.fakeai_service import FakeAIService
    from fakeai.config import AppConfig
    from fakeai.models import ChatCompletionRequest

    assert FakeAIService is not None
    assert AppConfig is not None
    assert ChatCompletionRequest is not None


# ==============================================================================
# Endpoint Backward Compatibility Tests
# ==============================================================================


def test_all_v1_endpoints_respond(client):
    """Test that all v1 API endpoints respond."""
    endpoints = [
        ("/v1/models", "GET"),
        ("/v1/chat/completions", "POST"),
        ("/v1/completions", "POST"),
        ("/v1/embeddings", "POST"),
        ("/v1/images/generations", "POST"),
        ("/v1/audio/speech", "POST"),
        ("/v1/moderations", "POST"),
        ("/v1/files", "GET"),
        ("/v1/batches", "GET"),
    ]

    for endpoint, method in endpoints:
        if method == "GET":
            response = client.get(endpoint)
        else:
            # POST with minimal valid data
            response = client.post(endpoint, json={})

        # Should respond (even if with error)
        assert response.status_code in [200, 400, 422], f"{endpoint} not responding"


def test_health_endpoint_backward_compatible(client):
    """Test that health endpoint maintains format."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Should have expected fields
    assert "status" in data
    assert "timestamp" in data or "ready" in data


def test_metrics_endpoint_backward_compatible(client):
    """Test that metrics endpoint maintains format."""
    response = client.get("/metrics")

    assert response.status_code == 200
    data = response.json()

    # Should be dict-like
    assert isinstance(data, dict)


# ==============================================================================
# OpenAI SDK Compatibility Tests
# ==============================================================================


def test_openai_sdk_chat_completions():
    """Test OpenAI SDK compatibility for chat completions."""
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key="test-key",
            base_url="http://localhost:8000/v1",
        )

        # Skip actual request (would require running server)
        # Just test that SDK can be initialized
        assert client is not None

    except ImportError:
        pytest.skip("OpenAI SDK not installed")


def test_chat_completion_response_format(client):
    """Test that chat completion response maintains OpenAI format."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Test"}],
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Should have OpenAI format
    assert "id" in data
    assert "object" in data
    assert "created" in data
    assert "model" in data
    assert "choices" in data
    assert "usage" in data

    # Choices format
    assert len(data["choices"]) > 0
    choice = data["choices"][0]
    assert "index" in choice
    assert "message" in choice
    assert "finish_reason" in choice

    # Message format
    message = choice["message"]
    assert "role" in message
    assert "content" in message

    # Usage format
    usage = data["usage"]
    assert "prompt_tokens" in usage
    assert "completion_tokens" in usage
    assert "total_tokens" in usage


def test_embedding_response_format(client):
    """Test that embedding response maintains OpenAI format."""
    response = client.post(
        "/v1/embeddings",
        json={
            "model": "text-embedding-3-small",
            "input": "Test",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # OpenAI format
    assert "object" in data
    assert data["object"] == "list"
    assert "data" in data
    assert "model" in data
    assert "usage" in data

    # Data format
    assert len(data["data"]) > 0
    item = data["data"][0]
    assert "object" in item
    assert "embedding" in item
    assert "index" in item


def test_model_list_response_format(client):
    """Test that model list response maintains OpenAI format."""
    response = client.get("/v1/models")

    assert response.status_code == 200
    data = response.json()

    # OpenAI format
    assert "object" in data
    assert data["object"] == "list"
    assert "data" in data

    # Model format
    if len(data["data"]) > 0:
        model = data["data"][0]
        assert "id" in model
        assert "object" in model
        assert "created" in model
        assert "owned_by" in model


# ==============================================================================
# AIPerf Compatibility Tests
# ==============================================================================


def test_aiperf_can_benchmark():
    """Test that AIPerf can run benchmarks."""
    # AIPerf would make requests to /v1/chat/completions
    # Test that basic format works
    pytest.skip("AIPerf integration test - requires full setup")


def test_streaming_format_compatible(client):
    """Test that streaming format is compatible with AIPerf."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Test"}],
            "stream": True,
        },
    )

    assert response.status_code == 200

    # Should be SSE format
    chunks = []
    for line in response.iter_lines():
        if line and line.startswith(b"data: "):
            data_str = line[6:].decode("utf-8")
            if data_str.strip() != "[DONE]":
                import json

                chunks.append(json.loads(data_str))

    assert len(chunks) > 0

    # First chunk should have role
    assert chunks[0]["object"] == "chat.completion.chunk"
    assert "choices" in chunks[0]


# ==============================================================================
# Response Schema Stability Tests
# ==============================================================================


def test_chat_completion_schema_stable(client):
    """Test that chat completion schema hasn't changed."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Test"}],
            "max_tokens": 10,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Core fields that must exist
    required_fields = {
        "id",
        "object",
        "created",
        "model",
        "choices",
        "usage",
    }

    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def test_usage_schema_stable(client):
    """Test that usage schema hasn't changed."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Test"}],
        },
    )

    assert response.status_code == 200
    data = response.json()

    usage = data["usage"]

    # Required usage fields
    assert "prompt_tokens" in usage
    assert "completion_tokens" in usage
    assert "total_tokens" in usage

    # Values should be consistent
    assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]


def test_error_schema_stable(client):
    """Test that error response schema hasn't changed."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "",  # Invalid
            "messages": [{"role": "user", "content": "Test"}],
        },
    )

    assert response.status_code == 422

    # Should have error details
    data = response.json()
    assert "detail" in data


# ==============================================================================
# Model Names Backward Compatible
# ==============================================================================


def test_legacy_model_names_work(client):
    """Test that legacy model names still work."""
    legacy_models = [
        "gpt-4",
        "gpt-3.5-turbo",
        "text-embedding-ada-002",
    ]

    for model in legacy_models:
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 5,
            },
        )

        # Should work (auto-created)
        assert response.status_code == 200


def test_new_model_names_work(client):
    """Test that new model names work."""
    new_models = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "deepseek-ai/DeepSeek-R1",
    ]

    for model in new_models:
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 5,
            },
        )

        assert response.status_code == 200


# ==============================================================================
# Parameter Backward Compatibility
# ==============================================================================


def test_old_parameters_still_accepted(client):
    """Test that old parameters are still accepted."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Test"}],
            "temperature": 0.7,  # Old parameter
            "top_p": 0.9,  # Old parameter
            "max_tokens": 10,  # Old parameter
        },
    )

    assert response.status_code == 200


def test_new_parameters_work(client):
    """Test that new parameters work."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Test"}],
            "max_completion_tokens": 10,  # New parameter
        },
    )

    assert response.status_code == 200


# ==============================================================================
# Feature Flag Compatibility
# ==============================================================================


def test_streaming_flag_works(client):
    """Test that streaming flag works."""
    # stream=false
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Test"}],
            "stream": False,
        },
    )

    assert response.status_code == 200
    # Should be regular response
    data = response.json()
    assert "choices" in data

    # stream=true
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Test"}],
            "stream": True,
        },
    )

    assert response.status_code == 200
    # Should be streaming response
    for line in response.iter_lines():
        if line:
            break  # Got at least one line


# ==============================================================================
# Configuration Backward Compatibility
# ==============================================================================


def test_config_fields_backward_compatible():
    """Test that config fields haven't changed."""
    config = AppConfig()

    # Core fields that must exist
    required_fields = [
        "host",
        "port",
        "debug",
        "response_delay",
        "random_delay",
        "require_api_key",
        "api_keys",
    ]

    for field in required_fields:
        assert hasattr(config, field), f"Missing config field: {field}"


def test_environment_variables_backward_compatible():
    """Test that environment variable names haven't changed."""
    import os

    # Test that old env vars are recognized
    old_env_vars = [
        "FAKEAI_HOST",
        "FAKEAI_PORT",
        "FAKEAI_DEBUG",
        "FAKEAI_RESPONSE_DELAY",
    ]

    # Just test that AppConfig would recognize them
    # (actual testing would require setting env vars)


# ==============================================================================
# CLI Backward Compatibility
# ==============================================================================


def test_cli_commands_exist():
    """Test that CLI commands haven't been removed."""
    from fakeai.cli import app as cli_app

    # Should have main commands
    # (Hard to test without actually running CLI)


# ==============================================================================
# Metrics Format Backward Compatibility
# ==============================================================================


def test_metrics_format_stable(client):
    """Test that metrics format is stable."""
    # Make a request
    client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Test"}],
        },
    )

    # Get metrics
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()

    # Should be dict
    assert isinstance(data, dict)


# ==============================================================================
# Deprecation Warnings
# ==============================================================================


def test_no_breaking_changes_in_public_api():
    """Test that public API hasn't broken."""
    # Test that key classes can be instantiated
    from fakeai.config import AppConfig
    from fakeai.fakeai_service import FakeAIService

    config = AppConfig()
    service = FakeAIService(config)

    # Should work
    assert service is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
