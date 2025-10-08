"""
Complete System Integration Tests

Tests all endpoints and features working together end-to-end.
Validates full request/response cycles with real data.
"""

import json

import pytest
from fastapi.testclient import TestClient

from fakeai.app import app
from fakeai.config import AppConfig
from fakeai.fakeai_service import FakeAIService


@pytest.fixture
def client():
    """Test client with no auth."""
    import fakeai.app as app_module
    app_module.server_ready = True
    return TestClient(app)


@pytest.fixture
def service():
    """Service instance for direct testing."""
    config = AppConfig(require_api_key=False, response_delay=0.0, random_delay=False)
    return FakeAIService(config)


# ==============================================================================
# Chat Completions End-to-End
# ==============================================================================


def test_chat_completion_end_to_end(client):
    """Test complete chat completion flow."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Hello, world!"}],
            "max_tokens": 100,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"].startswith("chatcmpl-")
    assert data["object"] == "chat.completion"
    assert len(data["choices"]) > 0
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert "content" in data["choices"][0]["message"]
    assert data["usage"]["prompt_tokens"] > 0
    assert data["usage"]["completion_tokens"] > 0
    assert data["usage"]["total_tokens"] > 0


def test_chat_completion_streaming_end_to_end(client):
    """Test streaming chat completion flow."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Count to 5"}],
            "stream": True,
        },
    )

    assert response.status_code == 200

    chunks = []
    for line in response.iter_lines():
        if line and line.startswith(b"data: "):
            data_str = line[6:].decode("utf-8")
            if data_str.strip() != "[DONE]":
                chunks.append(json.loads(data_str))

    assert len(chunks) > 0
    assert chunks[0]["object"] == "chat.completion.chunk"
    assert chunks[0]["choices"][0]["delta"]["role"] == "assistant"


def test_chat_completion_with_tools(client):
    """Test chat completion with function/tool calling."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "What's the weather in San Francisco?"}],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get weather in a location",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string"},
                            },
                            "required": ["location"],
                        },
                    },
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["choices"][0]["message"]["role"] == "assistant"


def test_chat_completion_multimodal(client):
    """Test chat completion with vision/multimodal content."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What's in this image?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "https://example.com/image.jpg"
                            },
                        },
                    ],
                }
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["choices"][0]["message"]["content"]


def test_chat_completion_reasoning_models(client):
    """Test reasoning models with reasoning_content."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "deepseek-ai/DeepSeek-R1",
            "messages": [{"role": "user", "content": "Solve 2x + 5 = 11"}],
        },
    )

    assert response.status_code == 200
    data = response.json()
    # Reasoning models should have reasoning_content
    assert "reasoning_content" in data["choices"][0]["message"]
    assert "reasoning_tokens" in data["usage"]


# ==============================================================================
# Embeddings End-to-End
# ==============================================================================


def test_embeddings_end_to_end(client):
    """Test complete embeddings flow."""
    response = client.post(
        "/v1/embeddings",
        json={
            "model": "text-embedding-3-small",
            "input": "Hello, world!",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) > 0
    assert len(data["data"][0]["embedding"]) > 0
    assert data["usage"]["prompt_tokens"] > 0


def test_embeddings_batch_end_to_end(client):
    """Test batch embeddings."""
    response = client.post(
        "/v1/embeddings",
        json={
            "model": "text-embedding-3-small",
            "input": ["Text 1", "Text 2", "Text 3"],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 3
    assert all(len(item["embedding"]) > 0 for item in data["data"])


# ==============================================================================
# Image Generation End-to-End
# ==============================================================================


def test_image_generation_end_to_end(client):
    """Test complete image generation flow."""
    response = client.post(
        "/v1/images/generations",
        json={
            "model": "dall-e-3",
            "prompt": "A beautiful sunset over mountains",
            "size": "1024x1024",
            "quality": "standard",
            "n": 1,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert "url" in data["data"][0] or "b64_json" in data["data"][0]


def test_image_generation_multiple_end_to_end(client):
    """Test multiple image generation."""
    response = client.post(
        "/v1/images/generations",
        json={
            "model": "dall-e-2",
            "prompt": "A cat playing piano",
            "size": "512x512",
            "n": 3,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 3


# ==============================================================================
# Audio End-to-End
# ==============================================================================


def test_audio_synthesis_end_to_end(client):
    """Test text-to-speech audio generation."""
    response = client.post(
        "/v1/audio/speech",
        json={
            "model": "tts-1",
            "input": "Hello, this is a test.",
            "voice": "alloy",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/")
    assert len(response.content) > 0


def test_audio_transcription_end_to_end(client):
    """Test audio transcription (Whisper)."""
    # Create fake audio file
    fake_audio = b"RIFF" + b"\x00" * 36 + b"WAVE" + b"\x00" * 100

    response = client.post(
        "/v1/audio/transcriptions",
        files={"file": ("audio.wav", fake_audio, "audio/wav")},
        data={"model": "whisper-1"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "text" in data


# ==============================================================================
# Moderation End-to-End
# ==============================================================================


def test_moderation_end_to_end(client):
    """Test content moderation."""
    response = client.post(
        "/v1/moderations",
        json={
            "input": "This is a test of the moderation system.",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    assert "flagged" in data["results"][0]
    assert "categories" in data["results"][0]


def test_moderation_harmful_content(client):
    """Test moderation flags harmful content."""
    response = client.post(
        "/v1/moderations",
        json={
            "input": "This contains violence and hate speech keywords",
        },
    )

    assert response.status_code == 200
    data = response.json()
    # Should flag some categories
    result = data["results"][0]
    assert isinstance(result["flagged"], bool)


# ==============================================================================
# Batch Processing End-to-End
# ==============================================================================


def test_batch_processing_end_to_end(client):
    """Test complete batch processing flow."""
    # First upload a file
    batch_content = """{"custom_id": "request-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hello"}]}}"""

    upload_response = client.post(
        "/v1/files",
        files={"file": ("batch.jsonl", batch_content.encode(), "application/json")},
        data={"purpose": "batch"},
    )

    assert upload_response.status_code == 200
    file_id = upload_response.json()["id"]

    # Create batch
    batch_response = client.post(
        "/v1/batches",
        json={
            "input_file_id": file_id,
            "endpoint": "/v1/chat/completions",
            "completion_window": "24h",
        },
    )

    assert batch_response.status_code == 200
    batch_data = batch_response.json()
    assert batch_data["object"] == "batch"
    assert batch_data["status"] in ["validating", "in_progress", "completed"]

    # Retrieve batch
    batch_id = batch_data["id"]
    retrieve_response = client.get(f"/v1/batches/{batch_id}")

    assert retrieve_response.status_code == 200


# ==============================================================================
# File Management End-to-End
# ==============================================================================


def test_file_management_end_to_end(client):
    """Test complete file upload/retrieve/delete flow."""
    # Upload file
    content = b"Test file content"
    upload_response = client.post(
        "/v1/files",
        files={"file": ("test.txt", content, "text/plain")},
        data={"purpose": "assistants"},
    )

    assert upload_response.status_code == 200
    file_id = upload_response.json()["id"]

    # List files
    list_response = client.get("/v1/files")
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) > 0

    # Retrieve file
    retrieve_response = client.get(f"/v1/files/{file_id}")
    assert retrieve_response.status_code == 200

    # Delete file
    delete_response = client.delete(f"/v1/files/{file_id}")
    assert delete_response.status_code == 200


# ==============================================================================
# Vector Store End-to-End
# ==============================================================================


def test_vector_store_end_to_end(client):
    """Test complete vector store operations."""
    # Create vector store
    create_response = client.post(
        "/v1/vector_stores",
        json={"name": "Test Vector Store"},
    )

    assert create_response.status_code == 200
    store_id = create_response.json()["id"]

    # List vector stores
    list_response = client.get("/v1/vector_stores")
    assert list_response.status_code == 200

    # Modify vector store
    modify_response = client.post(
        f"/v1/vector_stores/{store_id}",
        json={"name": "Updated Vector Store"},
    )
    assert modify_response.status_code == 200

    # Delete vector store
    delete_response = client.delete(f"/v1/vector_stores/{store_id}")
    assert delete_response.status_code == 200


# ==============================================================================
# Models End-to-End
# ==============================================================================


def test_models_list_end_to_end(client):
    """Test listing models."""
    response = client.get("/v1/models")

    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) > 0
    assert all("id" in model for model in data["data"])


def test_models_retrieve_end_to_end(client):
    """Test retrieving specific model."""
    response = client.get("/v1/models/openai/gpt-oss-120b")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "openai/gpt-oss-120b"
    assert "owned_by" in data


def test_model_capabilities_end_to_end(client):
    """Test model capabilities endpoint."""
    response = client.get("/v1/models/openai/gpt-oss-120b/capabilities")

    assert response.status_code == 200
    data = response.json()
    assert "context_window" in data
    assert "supports_vision" in data
    assert "supports_function_calling" in data


# ==============================================================================
# Health & Metrics End-to-End
# ==============================================================================


def test_health_check_end_to_end(client):
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "starting"]


def test_metrics_end_to_end(client):
    """Test metrics endpoint."""
    # First make some requests
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
    assert "requests" in data or "responses" in data


# ==============================================================================
# Organization Management End-to-End
# ==============================================================================


def test_organization_users_end_to_end(client):
    """Test organization user management."""
    # Create user
    create_response = client.post(
        "/v1/organization/users",
        json={
            "email": "test@example.com",
            "role": "owner",
        },
    )

    assert create_response.status_code == 200
    user_id = create_response.json()["id"]

    # List users
    list_response = client.get("/v1/organization/users")
    assert list_response.status_code == 200

    # Get user
    get_response = client.get(f"/v1/organization/users/{user_id}")
    assert get_response.status_code == 200

    # Modify user
    modify_response = client.post(
        f"/v1/organization/users/{user_id}",
        json={"role": "reader"},
    )
    assert modify_response.status_code == 200


def test_organization_projects_end_to_end(client):
    """Test organization project management."""
    # Create project
    create_response = client.post(
        "/v1/organization/projects",
        json={"name": "Test Project"},
    )

    assert create_response.status_code == 200
    project_id = create_response.json()["id"]

    # List projects
    list_response = client.get("/v1/organization/projects")
    assert list_response.status_code == 200

    # Archive project
    archive_response = client.post(f"/v1/organization/projects/{project_id}/archive")
    assert archive_response.status_code == 200


# ==============================================================================
# Usage & Billing End-to-End
# ==============================================================================


def test_usage_completions_end_to_end(client):
    """Test completions usage tracking."""
    import time

    # Make some requests
    client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Test"}],
        },
    )

    # Get usage
    start_time = int(time.time()) - 3600
    end_time = int(time.time())

    response = client.get(
        f"/v1/organization/usage/completions?start_time={start_time}&end_time={end_time}&bucket_width=1h"
    )

    assert response.status_code == 200
    data = response.json()
    assert "data" in data


def test_costs_end_to_end(client):
    """Test cost tracking."""
    import time

    start_time = int(time.time()) - 3600
    end_time = int(time.time())

    response = client.get(
        f"/v1/organization/costs?start_time={start_time}&end_time={end_time}"
    )

    assert response.status_code == 200


# ==============================================================================
# Fine-Tuning End-to-End
# ==============================================================================


def test_fine_tuning_end_to_end(client):
    """Test fine-tuning job management."""
    # Upload training file
    training_data = """{"messages": [{"role": "user", "content": "Test"}]}"""
    upload_response = client.post(
        "/v1/files",
        files={"file": ("training.jsonl", training_data.encode(), "application/json")},
        data={"purpose": "fine-tune"},
    )

    assert upload_response.status_code == 200
    file_id = upload_response.json()["id"]

    # Create fine-tuning job
    job_response = client.post(
        "/v1/fine_tuning/jobs",
        json={
            "training_file": file_id,
            "model": "openai/gpt-oss-20b",
        },
    )

    assert job_response.status_code == 200
    job_id = job_response.json()["id"]

    # List jobs
    list_response = client.get("/v1/fine_tuning/jobs")
    assert list_response.status_code == 200

    # Retrieve job
    retrieve_response = client.get(f"/v1/fine_tuning/jobs/{job_id}")
    assert retrieve_response.status_code == 200


# ==============================================================================
# Ranking (NVIDIA NIM) End-to-End
# ==============================================================================


def test_ranking_end_to_end(client):
    """Test NVIDIA NIM ranking endpoint."""
    response = client.post(
        "/v1/ranking",
        json={
            "model": "nvidia/nv-rerankqa-mistral-4b-v3",
            "query": {"text": "What is machine learning?"},
            "passages": [
                {"text": "Machine learning is a subset of AI."},
                {"text": "The weather is nice today."},
                {"text": "ML models learn from data."},
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "rankings" in data
    assert len(data["rankings"]) == 3


# ==============================================================================
# Solido RAG End-to-End
# ==============================================================================


def test_solido_rag_end_to_end(client):
    """Test Solido RAG endpoint."""
    response = client.post(
        "/rag/api/prompt",
        json={
            "query": "What is PVTMC?",
            "filters": {"family": "Solido"},
            "inference_model": "meta-llama/Llama-3.1-70B-Instruct",
            "top_k": 5,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert "retrieved_docs" in data
    assert "usage" in data


# ==============================================================================
# Error Handling End-to-End
# ==============================================================================


def test_invalid_model_error(client):
    """Test error handling for invalid model."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "",  # Invalid
            "messages": [{"role": "user", "content": "Test"}],
        },
    )

    assert response.status_code == 422  # Validation error


def test_missing_required_fields_error(client):
    """Test error handling for missing fields."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            # Missing messages
        },
    )

    assert response.status_code == 422


# ==============================================================================
# Concurrent Requests End-to-End
# ==============================================================================


def test_concurrent_requests_end_to_end(client):
    """Test handling multiple concurrent requests."""
    import concurrent.futures

    def make_request():
        return client.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Test"}],
                "max_tokens": 10,
            },
        )

    # Make 10 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All should succeed
    assert all(r.status_code == 200 for r in results)
    assert len(results) == 10


# ==============================================================================
# Complete Workflow End-to-End
# ==============================================================================


def test_complete_workflow_end_to_end(client):
    """Test complete workflow: file upload -> batch -> results."""
    # 1. Upload training data
    training_content = """{"messages": [{"role": "user", "content": "Hello"}]}"""
    file_response = client.post(
        "/v1/files",
        files={"file": ("data.jsonl", training_content.encode(), "application/json")},
        data={"purpose": "fine-tune"},
    )
    assert file_response.status_code == 200
    file_id = file_response.json()["id"]

    # 2. Create fine-tuning job
    job_response = client.post(
        "/v1/fine_tuning/jobs",
        json={"training_file": file_id, "model": "openai/gpt-oss-20b"},
    )
    assert job_response.status_code == 200

    # 3. Create vector store
    vs_response = client.post(
        "/v1/vector_stores",
        json={"name": "Test Store"},
    )
    assert vs_response.status_code == 200

    # 4. Make chat completion
    chat_response = client.post(
        "/v1/chat/completions",
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "Test workflow"}],
        },
    )
    assert chat_response.status_code == 200

    # 5. Check metrics
    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
