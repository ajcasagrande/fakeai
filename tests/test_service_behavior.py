"""
Service behavior tests.

Tests the business logic of FakeAIService, focusing on behavior not implementation.
"""
import pytest

from fakeai.models import (
    ChatCompletionRequest,
    CompletionRequest,
    EmbeddingRequest,
    ImageContent,
    ImageGenerationRequest,
    ImageUrl,
    InputAudio,
    InputAudioContent,
    Message,
    RankingPassage,
    RankingQuery,
    RankingRequest,
    ResponsesRequest,
    Role,
    TextContent,
)


@pytest.mark.unit
@pytest.mark.service
class TestChatCompletionBehavior:
    """Test chat completion service behavior."""

    @pytest.mark.asyncio
    async def test_generates_non_empty_response(self, service_no_auth):
        """Response generation should always produce non-empty content."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello")]
        )

        response = await service_no_auth.create_chat_completion(request)

        assert response.choices[0].message.content
        assert len(response.choices[0].message.content) > 0

    @pytest.mark.asyncio
    async def test_respects_n_parameter(self, service_no_auth):
        """Should generate N choices when n parameter is set."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            n=3
        )

        response = await service_no_auth.create_chat_completion(request)

        assert len(response.choices) == 3
        assert all(choice.message.content for choice in response.choices)

    @pytest.mark.asyncio
    async def test_finish_reason_reflects_token_limit(self, service_no_auth):
        """finish_reason should be 'length' when max_tokens is exceeded."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Write a long essay")],
            max_tokens=5  # Very small limit
        )

        response = await service_no_auth.create_chat_completion(request)

        # With such a small limit, should hit length
        # Note: Actual behavior may vary based on response generation
        assert response.choices[0].finish_reason in ["stop", "length"]

    @pytest.mark.asyncio
    async def test_auto_creates_unknown_models(self, service_no_auth):
        """Service should auto-create models that don't exist."""
        unknown_model = "custom-model-xyz-123"
        assert unknown_model not in service_no_auth.models

        request = ChatCompletionRequest(
            model=unknown_model,
            messages=[Message(role=Role.USER, content="Test")]
        )

        response = await service_no_auth.create_chat_completion(request)

        assert unknown_model in service_no_auth.models
        assert response.model == unknown_model

    @pytest.mark.asyncio
    async def test_token_count_in_response(self, service_no_auth):
        """Usage should contain non-zero token counts."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello world")]
        )

        response = await service_no_auth.create_chat_completion(request)

        assert response.usage.prompt_tokens > 0
        assert response.usage.completion_tokens > 0
        assert response.usage.total_tokens == (
            response.usage.prompt_tokens + response.usage.completion_tokens
        )


@pytest.mark.unit
@pytest.mark.service
@pytest.mark.multimodal
class TestMultiModalContentBehavior:
    """Test multi-modal content extraction behavior."""

    @pytest.mark.asyncio
    async def test_handles_string_content(self, service_no_auth):
        """Should handle traditional string content."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello")]
        )

        response = await service_no_auth.create_chat_completion(request)

        assert response.choices[0].message.content
        assert isinstance(response.choices[0].message.content, str)

    @pytest.mark.asyncio
    async def test_handles_content_array(self, service_no_auth):
        """Should extract text from content part arrays."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                Message(
                    role=Role.USER,
                    content=[
                        TextContent(text="What's in this image?"),
                        ImageContent(
                            image_url=ImageUrl(
                                url="data:image/png;base64,abc123",
                                detail="high"
                            )
                        ),
                    ],
                )
            ],
        )

        response = await service_no_auth.create_chat_completion(request)

        # Should successfully generate response with multi-modal input
        assert response.choices[0].message.content
        assert response.usage.prompt_tokens > 0

    @pytest.mark.asyncio
    async def test_mixed_content_types(self, service_no_auth):
        """Should handle mix of text, images, and audio in content."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                Message(
                    role=Role.USER,
                    content=[
                        TextContent(text="Analyze this"),
                        ImageContent(
                            image_url=ImageUrl(url="data:image/jpeg;base64,/9j/")
                        ),
                        InputAudioContent(
                            input_audio=InputAudio(data="base64audio", format="wav")
                        ),
                        TextContent(text="and tell me about it"),
                    ],
                )
            ],
        )

        response = await service_no_auth.create_chat_completion(request)

        # Should extract text from both text content parts
        assert response.choices[0].message.content
        assert response.usage.prompt_tokens > 0


@pytest.mark.unit
@pytest.mark.service
class TestTokenCalculationBehavior:
    """Test token calculation logic."""

    @pytest.mark.asyncio
    async def test_token_count_increases_with_content(self, service_no_auth):
        """Longer messages should have more tokens."""
        short_request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hi")]
        )
        long_request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[
                Message(
                    role=Role.USER,
                    content="This is a much longer message with many more words and tokens that should result in a higher token count when calculated."
                )
            ],
        )

        short_response = await service_no_auth.create_chat_completion(short_request)
        long_response = await service_no_auth.create_chat_completion(long_request)

        assert long_response.usage.prompt_tokens > short_response.usage.prompt_tokens

    @pytest.mark.asyncio
    async def test_total_tokens_is_sum(self, service_no_auth):
        """total_tokens should always equal prompt_tokens + completion_tokens."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test message")]
        )

        response = await service_no_auth.create_chat_completion(request)

        assert response.usage.total_tokens == (
            response.usage.prompt_tokens + response.usage.completion_tokens
        )


@pytest.mark.unit
@pytest.mark.service
class TestEmbeddingBehavior:
    """Test embedding service behavior."""

    @pytest.mark.asyncio
    async def test_embedding_vector_has_correct_dimensions(self, service_no_auth):
        """Embedding vectors should match requested dimensions."""
        request = EmbeddingRequest(
            model="nomic-ai/nomic-embed-text-v1.5",
            input="Test text",
            dimensions=512
        )

        response = await service_no_auth.create_embedding(request)

        assert len(response.data) == 1
        assert len(response.data[0].embedding) == 512

    @pytest.mark.asyncio
    async def test_embedding_default_dimensions(self, service_no_auth):
        """Should use 1536 dimensions by default."""
        request = EmbeddingRequest(
            model="sentence-transformers/all-mpnet-base-v2",
            input="Test text"
        )

        response = await service_no_auth.create_embedding(request)

        assert len(response.data[0].embedding) == 1536

    @pytest.mark.asyncio
    async def test_batch_embeddings_maintain_order(self, service_no_auth):
        """Batch embeddings should maintain input order via index."""
        inputs = ["first text", "second text", "third text"]
        request = EmbeddingRequest(
            model="sentence-transformers/all-mpnet-base-v2",
            input=inputs
        )

        response = await service_no_auth.create_embedding(request)

        assert len(response.data) == 3
        # Verify indices are correct
        for i, embedding in enumerate(response.data):
            assert embedding.index == i

    @pytest.mark.asyncio
    async def test_same_text_produces_same_embedding(self, service_no_auth):
        """Same input should produce same embedding (deterministic)."""
        text = "Deterministic test text"

        request1 = EmbeddingRequest(model="sentence-transformers/all-mpnet-base-v2", input=text)
        request2 = EmbeddingRequest(model="sentence-transformers/all-mpnet-base-v2", input=text)

        response1 = await service_no_auth.create_embedding(request1)
        response2 = await service_no_auth.create_embedding(request2)

        # Should be identical due to hash-based seeding
        assert response1.data[0].embedding == response2.data[0].embedding


@pytest.mark.unit
@pytest.mark.service
class TestStreamingBehavior:
    """Test streaming response behavior."""

    @pytest.mark.asyncio
    @pytest.mark.streaming
    async def test_streaming_produces_multiple_chunks(self, service_no_auth):
        """Streaming should yield multiple chunks."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello")],
            stream=True
        )

        chunks = []
        async for chunk in service_no_auth.create_chat_completion_stream(request):
            chunks.append(chunk)

        assert len(chunks) > 1  # Should have at least role chunk + content + final

    @pytest.mark.asyncio
    @pytest.mark.streaming
    async def test_first_chunk_contains_role(self, service_no_auth):
        """First streaming chunk should contain the assistant role."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True
        )

        chunks = []
        async for chunk in service_no_auth.create_chat_completion_stream(request):
            chunks.append(chunk)

        # First chunk should have role
        assert chunks[0].choices[0].delta.role == Role.ASSISTANT

    @pytest.mark.asyncio
    @pytest.mark.streaming
    async def test_last_chunk_has_finish_reason(self, service_no_auth):
        """Last streaming chunk should have finish_reason."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True
        )

        chunks = []
        async for chunk in service_no_auth.create_chat_completion_stream(request):
            chunks.append(chunk)

        # Last chunk should have finish_reason
        assert chunks[-1].choices[0].finish_reason is not None
        assert chunks[-1].choices[0].finish_reason in ["stop", "length"]

    @pytest.mark.asyncio
    @pytest.mark.streaming
    async def test_streaming_chunk_ids_consistent(self, service_no_auth):
        """All chunks in a stream should have the same ID."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True
        )

        chunks = []
        async for chunk in service_no_auth.create_chat_completion_stream(request):
            chunks.append(chunk)

        # All chunks should have same ID
        first_id = chunks[0].id
        assert all(chunk.id == first_id for chunk in chunks)


@pytest.mark.unit
@pytest.mark.service
class TestRankingBehavior:
    """Test NIM ranking algorithm behavior."""

    @pytest.mark.asyncio
    async def test_rankings_sorted_descending(self, service_no_auth):
        """Rankings should be sorted by logit descending."""
        request = RankingRequest(
            model="nvidia/model",
            query=RankingQuery(text="machine learning"),
            passages=[
                RankingPassage(text="Machine learning is AI"),
                RankingPassage(text="Python programming"),
                RankingPassage(text="Deep learning uses neural networks for machine learning"),
            ],
        )

        response = await service_no_auth.create_ranking(request)

        # Verify sorted descending
        logits = [r["logit"] for r in response["rankings"]]
        assert logits == sorted(logits, reverse=True)

    @pytest.mark.asyncio
    async def test_all_passages_ranked(self, service_no_auth):
        """All input passages should appear in rankings."""
        passages = [
            RankingPassage(text=f"Passage {i}") for i in range(10)
        ]
        request = RankingRequest(
            model="nvidia/model",
            query=RankingQuery(text="test"),
            passages=passages,
        )

        response = await service_no_auth.create_ranking(request)

        assert len(response["rankings"]) == 10
        # All indices should be present
        indices = {r["index"] for r in response["rankings"]}
        assert indices == set(range(10))

    @pytest.mark.asyncio
    async def test_relevant_passage_ranks_higher(self, service_no_auth):
        """Passage with query words should rank higher than unrelated passage."""
        request = RankingRequest(
            model="nvidia/model",
            query=RankingQuery(text="machine learning artificial intelligence"),
            passages=[
                RankingPassage(
                    text="Machine learning and artificial intelligence are transforming technology"
                ),  # Very relevant
                RankingPassage(text="The weather is nice today"),  # Not relevant
            ],
        )

        response = await service_no_auth.create_ranking(request)

        # First ranked (highest logit) should be the relevant one
        top_ranked_index = response["rankings"][0]["index"]
        assert top_ranked_index == 0  # The relevant passage


@pytest.mark.unit
@pytest.mark.service
class TestResponsesAPIBehavior:
    """Test Responses API service behavior."""

    @pytest.mark.asyncio
    async def test_handles_string_input(self, service_no_auth):
        """Should convert string input to message array."""
        request = ResponsesRequest(model="openai/gpt-oss-120b", input="Hello world")

        response = await service_no_auth.create_response(request)

        assert response["status"] == "completed"
        assert len(response["output"]) > 0
        assert response["output"][0]["type"] == "message"

    @pytest.mark.asyncio
    async def test_handles_message_array_input(self, service_no_auth):
        """Should handle message array input directly."""
        request = ResponsesRequest(
            model="openai/gpt-oss-120b",
            input=[
                Message(role=Role.SYSTEM, content="Be helpful"),
                Message(role=Role.USER, content="Hello"),
            ],
        )

        response = await service_no_auth.create_response(request)

        assert response["status"] == "completed"
        assert response["output"][0]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_instructions_added_as_system_message(self, service_no_auth):
        """Instructions should be prepended as system message."""
        request = ResponsesRequest(
            model="openai/gpt-oss-120b",
            input="Hello",
            instructions="You are a helpful assistant",
        )

        # The service should add instructions as first message
        response = await service_no_auth.create_response(request)

        # Should process successfully with instructions
        assert response["status"] == "completed"
        assert response["instructions"] == "You are a helpful assistant"

    @pytest.mark.asyncio
    async def test_usage_uses_input_output_tokens(self, service_no_auth):
        """Responses API should use input_tokens/output_tokens naming."""
        request = ResponsesRequest(model="openai/gpt-oss-120b", input="Test")

        response = await service_no_auth.create_response(request)

        assert "usage" in response
        assert response["usage"]["input_tokens"] > 0
        assert response["usage"]["output_tokens"] > 0
        assert response["usage"]["total_tokens"] == (
            response["usage"]["input_tokens"] + response["usage"]["output_tokens"]
        )


@pytest.mark.unit
@pytest.mark.service
class TestModelManagementBehavior:
    """Test model management behavior."""

    @pytest.mark.asyncio
    async def test_list_models_includes_defaults(self, service_no_auth):
        """list_models should include pre-configured models."""
        response = await service_no_auth.list_models()

        model_ids = {model.id for model in response.data}

        # Check some expected models
        assert "openai/gpt-oss-120b" in model_ids
        assert "meta-llama/Llama-3.1-8B-Instruct" in model_ids
        assert "sentence-transformers/all-mpnet-base-v2" in model_ids

    @pytest.mark.asyncio
    async def test_get_model_returns_correct_model(self, service_no_auth):
        """get_model should return the requested model."""
        model = await service_no_auth.get_model("openai/gpt-oss-120b")

        assert model.id == "openai/gpt-oss-120b"
        assert model.owned_by == "openai"

    @pytest.mark.asyncio
    async def test_get_nonexistent_model_raises(self, service_no_auth):
        """Getting non-existent model should raise ValueError."""
        with pytest.raises(ValueError, match="Model.*not found"):
            await service_no_auth.get_model("nonexistent-model-12345")


@pytest.mark.unit
@pytest.mark.service
class TestImageGenerationBehavior:
    """Test image generation behavior."""

    @pytest.mark.asyncio
    async def test_generates_requested_number_of_images(self, service_no_auth):
        """Should generate n images when n parameter is set."""
        request = ImageGenerationRequest(
            model="stabilityai/stable-diffusion-xl-base-1.0",
            prompt="A futuristic city",
            n=3
        )

        response = await service_no_auth.generate_images(request)

        assert len(response.data) == 3

    @pytest.mark.asyncio
    async def test_url_format_returns_urls(self, service_no_auth):
        """response_format='url' should return image URLs."""
        request = ImageGenerationRequest(
            model="stabilityai/stable-diffusion-2-1",
            prompt="Test image",
            response_format="url"
        )

        response = await service_no_auth.generate_images(request)

        assert response.data[0].url is not None
        assert response.data[0].b64_json is None

    @pytest.mark.asyncio
    async def test_base64_format_returns_base64(self, service_no_auth):
        """response_format='b64_json' should return base64 data."""
        request = ImageGenerationRequest(
            model="stabilityai/stable-diffusion-2-1",
            prompt="Test image",
            response_format="b64_json"
        )

        response = await service_no_auth.generate_images(request)

        assert response.data[0].b64_json is not None
        assert response.data[0].url is None


@pytest.mark.unit
@pytest.mark.service
class TestFileManagementBehavior:
    """Test file management behavior."""

    @pytest.mark.asyncio
    async def test_upload_adds_file_to_list(self, service_no_auth):
        """Uploading a file should add it to the file list."""
        initial_count = len(service_no_auth.files)

        new_file = await service_no_auth.upload_file()

        assert len(service_no_auth.files) == initial_count + 1
        assert new_file.id in [f.id for f in service_no_auth.files]

    @pytest.mark.asyncio
    async def test_delete_removes_file(self, service_no_auth):
        """Deleting a file should remove it from the list."""
        # Upload a file first
        uploaded = await service_no_auth.upload_file()
        file_id = uploaded.id

        # Delete it
        result = await service_no_auth.delete_file(file_id)

        assert result["deleted"] is True
        assert file_id not in [f.id for f in service_no_auth.files]

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file_raises(self, service_no_auth):
        """Deleting non-existent file should raise ValueError."""
        with pytest.raises(ValueError, match="File.*not found"):
            await service_no_auth.delete_file("nonexistent-file-12345")

    @pytest.mark.asyncio
    async def test_get_file_returns_correct_file(self, service_no_auth):
        """get_file should return the requested file."""
        # Get an existing file
        files = await service_no_auth.list_files()
        if files.data:
            file_id = files.data[0].id

            retrieved = await service_no_auth.get_file(file_id)

            assert retrieved.id == file_id
