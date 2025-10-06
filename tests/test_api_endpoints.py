"""
API endpoint behavior tests.

Tests the HTTP API behavior - status codes, response formats, error handling.
Focuses on what the API DOES, not how it does it.
"""

import pytest


@pytest.mark.integration
class TestChatCompletionsEndpoint:
    """Test /v1/chat/completions endpoint behavior."""

    def test_returns_200_for_valid_request(self, client_no_auth):
        """Valid chat completion request should return 200 OK."""
        response = client_no_auth.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Hello"}],
            },
        )

        assert response.status_code == 200

    def test_response_has_required_fields(self, client_no_auth):
        """Response should contain all required OpenAI fields."""
        response = client_no_auth.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Test"}],
            },
        )

        data = response.json()

        # Required fields per OpenAI spec
        assert "id" in data
        assert "object" in data
        assert data["object"] == "chat.completion"
        assert "created" in data
        assert "model" in data
        assert "choices" in data
        assert "usage" in data

    def test_streaming_returns_event_stream(self, client_no_auth):
        """Streaming request should return text/event-stream."""
        response = client_no_auth.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Test"}],
                "stream": True,
            },
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

    def test_accepts_multi_modal_content(self, client_no_auth):
        """Should accept multi-modal content arrays."""
        response = client_no_auth.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": "data:image/png;base64,abc123",
                                    "detail": "high",
                                },
                            },
                        ],
                    }
                ],
            },
        )

        assert response.status_code == 200

    def test_accepts_new_parameters(self, client_no_auth):
        """Should accept all new 2024-2025 parameters."""
        response = client_no_auth.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Test"}],
                "parallel_tool_calls": False,
                "logprobs": True,
                "top_logprobs": 5,
                "seed": 12345,
                "store": True,
                "metadata": {"test": "value"},
            },
        )

        assert response.status_code == 200


@pytest.mark.integration
class TestEmbeddingsEndpoint:
    """Test /v1/embeddings endpoint behavior."""

    def test_returns_200_for_valid_request(self, client_no_auth):
        """Valid embedding request should return 200 OK."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "sentence-transformers/all-mpnet-base-v2",
                "input": "Test text",
            },
        )

        assert response.status_code == 200

    def test_response_structure_matches_openai(self, client_no_auth):
        """Response should match OpenAI embeddings format."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={"model": "sentence-transformers/all-mpnet-base-v2", "input": "Test"},
        )

        data = response.json()

        assert data["object"] == "list"
        assert "data" in data
        assert "model" in data
        assert "usage" in data
        assert len(data["data"]) > 0
        assert data["data"][0]["object"] == "embedding"
        assert "embedding" in data["data"][0]
        assert "index" in data["data"][0]

    def test_batch_input_returns_multiple_embeddings(self, client_no_auth):
        """Batch input should return multiple embeddings."""
        response = client_no_auth.post(
            "/v1/embeddings",
            json={
                "model": "sentence-transformers/all-mpnet-base-v2",
                "input": ["text 1", "text 2", "text 3"],
            },
        )

        data = response.json()

        assert len(data["data"]) == 3


@pytest.mark.integration
class TestResponsesAPIEndpoint:
    """Test /v1/responses endpoint behavior."""

    def test_returns_200_for_valid_request(self, client_no_auth):
        """Valid Responses API request should return 200 OK."""
        response = client_no_auth.post(
            "/v1/responses", json={"model": "openai/gpt-oss-120b", "input": "Hello"}
        )

        assert response.status_code == 200

    def test_response_structure_matches_spec(self, client_no_auth):
        """Response should match Responses API format."""
        response = client_no_auth.post(
            "/v1/responses",
            json={
                "model": "openai/gpt-oss-120b",
                "input": "Test",
                "max_output_tokens": 100,
            },
        )

        data = response.json()

        # Required fields per Responses API spec
        assert data["object"] == "response"
        assert "id" in data
        assert "created_at" in data
        assert "model" in data
        assert "status" in data
        assert "output" in data
        assert "usage" in data

    def test_output_contains_message_item(self, client_no_auth):
        """Output array should contain message items."""
        response = client_no_auth.post(
            "/v1/responses", json={"model": "openai/gpt-oss-120b", "input": "Hello"}
        )

        data = response.json()

        assert len(data["output"]) > 0
        assert data["output"][0]["type"] == "message"
        assert data["output"][0]["role"] == "assistant"


@pytest.mark.integration
class TestRankingEndpoint:
    """Test /v1/ranking endpoint behavior."""

    def test_returns_200_for_valid_request(self, client_no_auth):
        """Valid ranking request should return 200 OK."""
        response = client_no_auth.post(
            "/v1/ranking",
            json={
                "model": "nvidia/model",
                "query": {"text": "test query"},
                "passages": [
                    {"text": "passage 1"},
                    {"text": "passage 2"},
                ],
            },
        )

        assert response.status_code == 200

    def test_response_structure_matches_nim_spec(self, client_no_auth):
        """Response should match NVIDIA NIM format."""
        response = client_no_auth.post(
            "/v1/ranking",
            json={
                "model": "nvidia/model",
                "query": {"text": "test"},
                "passages": [{"text": "p1"}, {"text": "p2"}],
            },
        )

        data = response.json()

        assert "rankings" in data
        assert isinstance(data["rankings"], list)
        assert len(data["rankings"]) == 2

        # Each ranking should have index and logit
        for ranking in data["rankings"]:
            assert "index" in ranking
            assert "logit" in ranking


@pytest.mark.integration
class TestModelsEndpoint:
    """Test /v1/models endpoint behavior."""

    def test_list_models_returns_200(self, client_no_auth):
        """GET /v1/models should return 200 OK."""
        response = client_no_auth.get("/v1/models")

        assert response.status_code == 200

    def test_list_models_returns_list_object(self, client_no_auth):
        """Response object type should be 'list'."""
        response = client_no_auth.get("/v1/models")

        data = response.json()

        assert data["object"] == "list"
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

    def test_get_model_returns_200_for_existing(self, client_no_auth):
        """GET /v1/models/{id} should return 200 for existing model."""
        response = client_no_auth.get("/v1/models/openai/gpt-oss-120b")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "openai/gpt-oss-120b"


@pytest.mark.integration
class TestHealthAndMetrics:
    """Test utility endpoints behavior."""

    def test_health_returns_200(self, client_no_auth):
        """Health endpoint should always return 200."""
        response = client_no_auth.get("/health")

        assert response.status_code == 200

    def test_health_includes_status(self, client_no_auth):
        """Health response should include status field."""
        response = client_no_auth.get("/health")

        data = response.json()

        assert "status" in data
        assert data["status"] in [
            "healthy",
            "starting",
        ]  # Can be starting during test setup
        assert "ready" in data  # Should have readiness flag

    def test_metrics_returns_200(self, client_no_auth):
        """Metrics endpoint should return 200."""
        response = client_no_auth.get("/metrics")

        assert response.status_code == 200

    def test_metrics_returns_dict(self, client_no_auth):
        """Metrics should return dictionary structure."""
        response = client_no_auth.get("/metrics")

        data = response.json()

        assert isinstance(data, dict)
