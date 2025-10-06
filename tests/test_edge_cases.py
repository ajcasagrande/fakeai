"""
Edge case and error handling tests.

Tests how the system handles unusual inputs, errors, and boundary conditions.
"""

import pytest

from fakeai.models import (
    ChatCompletionRequest,
    EmbeddingRequest,
    ImageGenerationRequest,
    Message,
    Role,
)


@pytest.mark.unit
@pytest.mark.edge_case
class TestEdgeCaseInputs:
    """Test edge case inputs."""

    @pytest.mark.asyncio
    async def test_empty_message_content_handled(self, service_no_auth):
        """Should handle empty message content gracefully."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="")],
        )

        response = await service_no_auth.create_chat_completion(request)

        # Should still generate a response
        assert response.choices[0].message.content is not None

    @pytest.mark.asyncio
    async def test_very_long_message(self, service_no_auth):
        """Should handle very long messages."""
        long_content = "word " * 1000  # 1000 words
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content=long_content)],
        )

        response = await service_no_auth.create_chat_completion(request)

        # Should successfully process
        assert response.choices[0].message.content
        assert (
            response.usage.prompt_tokens >= 1000
        )  # Should count many tokens (at least 1000 words)

    @pytest.mark.asyncio
    async def test_multiple_system_messages(self, service_no_auth):
        """Should handle multiple system messages."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                Message(role=Role.SYSTEM, content="Instruction 1"),
                Message(role=Role.SYSTEM, content="Instruction 2"),
                Message(role=Role.USER, content="Hello"),
            ],
        )

        response = await service_no_auth.create_chat_completion(request)

        # Should process successfully (uses last system message)
        assert response.choices[0].message.content

    @pytest.mark.asyncio
    async def test_zero_max_tokens(self, service_no_auth):
        """Should handle max_tokens=0 gracefully."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            max_tokens=0,
        )

        # Should not crash, though response may be minimal
        response = await service_no_auth.create_chat_completion(request)

        # finish_reason should likely be 'length'
        assert response.choices[0].finish_reason in ["stop", "length"]

    @pytest.mark.asyncio
    async def test_temperature_extremes(self, service_no_auth):
        """Should handle temperature at valid extremes."""
        # Temperature 0
        request_cold = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            temperature=0.0,
        )

        response_cold = await service_no_auth.create_chat_completion(request_cold)
        assert response_cold.choices[0].message.content

        # Temperature 2
        request_hot = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            temperature=2.0,
        )

        response_hot = await service_no_auth.create_chat_completion(request_hot)
        assert response_hot.choices[0].message.content


@pytest.mark.unit
@pytest.mark.edge_case
class TestEmbeddingEdgeCases:
    """Test embedding edge cases."""

    @pytest.mark.asyncio
    async def test_empty_string_embedding(self, service_no_auth):
        """Should handle empty string input."""
        request = EmbeddingRequest(
            model="sentence-transformers/all-mpnet-base-v2", input=""
        )

        response = await service_no_auth.create_embedding(request)

        # Should return an embedding even for empty string
        assert len(response.data) == 1
        assert len(response.data[0].embedding) > 0

    @pytest.mark.asyncio
    async def test_very_large_embedding_batch(self, service_no_auth):
        """Should handle large batch of embeddings."""
        # Create batch of 100 inputs
        inputs = [f"Text number {i}" for i in range(100)]

        request = EmbeddingRequest(
            model="sentence-transformers/all-mpnet-base-v2", input=inputs
        )

        response = await service_no_auth.create_embedding(request)

        assert len(response.data) == 100
        # All should have correct indices
        for i, emb in enumerate(response.data):
            assert emb.index == i

    @pytest.mark.asyncio
    async def test_custom_dimensions_lower_than_default(self, service_no_auth):
        """Should handle dimensions lower than default."""
        request = EmbeddingRequest(
            model="nomic-ai/nomic-embed-text-v1.5",
            input="Test",
            dimensions=256,  # Lower than default 1536
        )

        response = await service_no_auth.create_embedding(request)

        assert len(response.data[0].embedding) == 256


@pytest.mark.unit
@pytest.mark.edge_case
class TestErrorHandling:
    """Test error handling behavior."""

    @pytest.mark.asyncio
    async def test_invalid_model_id_handled(self, service_no_auth):
        """Non-existent models should be auto-created, not error."""
        request = ChatCompletionRequest(
            model="completely-invalid-model-xyz",
            messages=[Message(role=Role.USER, content="Test")],
        )

        # Should auto-create the model, not fail
        response = await service_no_auth.create_chat_completion(request)

        assert response.model == "completely-invalid-model-xyz"

    @pytest.mark.asyncio
    async def test_get_model_auto_creates(self, service_no_auth):
        """get_model should auto-create models that don't exist."""
        # Should auto-create the model
        model = await service_no_auth.get_model("this-model-definitely-does-not-exist")
        assert model.id == "this-model-definitely-does-not-exist"
        assert model.owned_by == "custom"

    @pytest.mark.asyncio
    async def test_invalid_image_model_raises(self, service_no_auth):
        """Invalid image generation model should raise."""
        request = ImageGenerationRequest(model="invalid-image-model", prompt="Test")

        with pytest.raises(ValueError, match="Invalid model"):
            await service_no_auth.generate_images(request)


@pytest.mark.integration
@pytest.mark.edge_case
class TestAPIErrorResponses:
    """Test API error response behavior."""

    def test_validation_errors_handled_gracefully(self, client_no_auth):
        """Invalid request data should be handled gracefully (422 or 500)."""
        response = client_no_auth.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                # Missing required "messages" field - Pydantic will catch this
            },
        )

        # Should return 422 (validation error) or 401 (if auth middleware runs first)
        assert response.status_code in [401, 422]

    def test_type_validation_errors_handled(self, client_no_auth):
        """Type errors should be handled gracefully."""
        response = client_no_auth.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": "not an array",  # Should be array
            },
        )

        # Should return 422 (validation error) or 401 (if auth runs first)
        assert response.status_code in [401, 422]

    def test_malformed_json_returns_422(self, client_no_auth):
        """Malformed JSON should return 422."""
        response = client_no_auth.post(
            "/v1/chat/completions",
            data="{{invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422


@pytest.mark.unit
@pytest.mark.edge_case
class TestPromptProcessing:
    """Test prompt processing edge cases."""

    @pytest.mark.asyncio
    async def test_list_of_strings_prompt(self, service_no_auth):
        """Should handle list of strings as prompt."""
        from fakeai.models import CompletionRequest

        request = CompletionRequest(
            model="meta-llama/Llama-3.1-8B-Instruct",
            prompt=["Line 1", "Line 2", "Line 3"],
        )

        response = await service_no_auth.create_completion(request)

        # Should process successfully
        assert response.choices[0].text

    @pytest.mark.asyncio
    async def test_token_ids_prompt(self, service_no_auth):
        """Should handle token IDs as prompt."""
        from fakeai.models import CompletionRequest

        request = CompletionRequest(
            model="meta-llama/Llama-3.1-8B-Instruct",
            prompt=[1, 2, 3, 4, 5],  # Token IDs
        )

        response = await service_no_auth.create_completion(request)

        # Should return placeholder response
        assert response.choices[0].text


@pytest.mark.unit
@pytest.mark.edge_case
class TestConcurrentRequests:
    """Test behavior under concurrent load."""

    @pytest.mark.asyncio
    async def test_concurrent_chat_completions(self, service_no_auth):
        """Should handle concurrent chat completion requests."""
        import asyncio

        from fakeai.models import ChatCompletionRequest, Message, Role

        async def make_request(i):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Request {i}")],
            )
            return await service_no_auth.create_chat_completion(request)

        # Make 10 concurrent requests
        tasks = [make_request(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        assert len(responses) == 10
        assert all(r.choices[0].message.content for r in responses)

    @pytest.mark.asyncio
    async def test_concurrent_embeddings(self, service_no_auth):
        """Should handle concurrent embedding requests."""
        import asyncio

        from fakeai.models import EmbeddingRequest

        async def make_request(i):
            request = EmbeddingRequest(
                model="sentence-transformers/all-mpnet-base-v2", input=f"Text {i}"
            )
            return await service_no_auth.create_embedding(request)

        tasks = [make_request(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)

        assert len(responses) == 10
        assert all(len(r.data) > 0 for r in responses)
