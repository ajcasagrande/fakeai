"""
Comprehensive tests for advanced FakeAI features.

Tests cover:
- KV cache reuse and AI-Dynamo smart routing
- Moderation endpoint (13 categories)
- Reasoning content (gpt-oss, deepseek-ai/DeepSeek-R1 models)
- Predicted outputs (EAGLE/speculative decoding)
- LoRA fine-tuned model naming
- MoE model support
- Streaming with usage statistics
"""
import pytest
from fakeai import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import (
    ChatCompletionRequest,
    Message,
    Role,
    PredictionContent,
    StreamOptions,
    ModerationRequest,
)


class TestKVCacheReuse:
    """Test AI-Dynamo KV cache and smart routing."""

    @pytest.mark.asyncio
    async def test_kv_cache_cold_start(self):
        """Test first request has no cached tokens."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello world")],
        )

        response = await service.create_chat_completion(request)

        assert response.usage.prompt_tokens_details.cached_tokens == 0
        assert service.kv_cache_metrics.get_cache_hit_rate() == 0.0

    @pytest.mark.asyncio
    async def test_kv_cache_warm_hit(self):
        """Test second request with same prompt gets cache hit."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        prompt = "This is a repeated system prompt " * 50  # Long prompt

        # First request
        request1 = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.SYSTEM, content=prompt), Message(role=Role.USER, content="Q1")],
        )
        response1 = await service.create_chat_completion(request1)
        cached1 = response1.usage.prompt_tokens_details.cached_tokens

        # Second request with same system prompt
        request2 = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.SYSTEM, content=prompt), Message(role=Role.USER, content="Q2")],
        )
        response2 = await service.create_chat_completion(request2)
        cached2 = response2.usage.prompt_tokens_details.cached_tokens

        # Second request should have cached tokens
        assert cached1 == 0
        assert cached2 > 0
        assert service.kv_cache_metrics.get_cache_hit_rate() == 50.0

    @pytest.mark.asyncio
    async def test_smart_router_load_balancing(self):
        """Test smart router distributes requests across workers."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        # Make multiple requests
        for i in range(10):
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b",
                messages=[Message(role=Role.USER, content=f"Request {i}")],
            )
            await service.create_chat_completion(request)

        # Check router stats
        stats = service.kv_cache_router.get_stats()
        workers = stats["workers"]

        # Verify all workers have processed requests
        assert len(workers) == 4
        total_requests = sum(w["total_requests"] for w in workers.values())
        assert total_requests == 10


class TestModeration:
    """Test content moderation endpoint."""

    @pytest.mark.asyncio
    async def test_moderation_safe_content(self):
        """Test moderation with safe content."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ModerationRequest(input="Hello, how are you today?")
        response = await service.create_moderation(request)

        assert response.id.startswith("modr-")
        assert len(response.results) == 1
        assert response.results[0].flagged is False

    @pytest.mark.asyncio
    async def test_moderation_violent_content(self):
        """Test moderation flags violent content."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ModerationRequest(input="I want to kill someone with a gun")
        response = await service.create_moderation(request)

        assert response.results[0].flagged is True
        assert response.results[0].categories.violence is True
        assert response.results[0].category_scores.violence > 0.5

    @pytest.mark.asyncio
    async def test_moderation_batch_input(self):
        """Test moderation with multiple texts."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ModerationRequest(
            input=["Hello", "I want to kill", "How are you?"]
        )
        response = await service.create_moderation(request)

        assert len(response.results) == 3
        assert response.results[0].flagged is False  # "Hello"
        assert response.results[1].flagged is True  # "I want to kill"
        assert response.results[2].flagged is False  # "How are you?"

    @pytest.mark.asyncio
    async def test_moderation_all_categories_exist(self):
        """Test all 13 moderation categories are present."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ModerationRequest(input="Test content")
        response = await service.create_moderation(request)

        categories = response.results[0].categories
        scores = response.results[0].category_scores

        # Check all 13 categories exist
        assert hasattr(categories, "sexual")
        assert hasattr(categories, "sexual_minors")
        assert hasattr(categories, "hate")
        assert hasattr(categories, "hate_threatening")
        assert hasattr(categories, "harassment")
        assert hasattr(categories, "harassment_threatening")
        assert hasattr(categories, "self_harm")
        assert hasattr(categories, "self_harm_intent")
        assert hasattr(categories, "self_harm_instructions")
        assert hasattr(categories, "violence")
        assert hasattr(categories, "violence_graphic")
        assert hasattr(categories, "illicit")
        assert hasattr(categories, "illicit_violent")

        # Check scores are in valid range
        assert 0.0 <= scores.violence <= 1.0


class TestReasoningContent:
    """Test reasoning content for gpt-oss and deepseek-ai/DeepSeek-R1 models."""

    @pytest.mark.asyncio
    async def test_gpt_oss_includes_reasoning(self):
        """Test gpt-oss models include reasoning content."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="gpt-oss-120b",
            messages=[Message(role=Role.USER, content="What is 2+2?")],
        )

        response = await service.create_chat_completion(request)

        assert response.choices[0].message.reasoning_content is not None
        assert len(response.choices[0].message.reasoning_content) > 0
        assert response.usage.completion_tokens_details is not None
        assert response.usage.completion_tokens_details.reasoning_tokens > 0

    @pytest.mark.asyncio
    async def test_regular_model_no_reasoning(self):
        """Test regular models don't include reasoning."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello")],
        )

        response = await service.create_chat_completion(request)

        assert response.choices[0].message.reasoning_content is None


class TestPredictedOutputs:
    """Test EAGLE/predicted outputs (speculative decoding)."""

    @pytest.mark.asyncio
    async def test_predicted_outputs_gpt4o(self):
        """Test predicted outputs with openai/gpt-oss-120b."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Refactor this code")],
            prediction=PredictionContent(
                type="content",
                content="result = [item.upper() for item in items]"
            ),
        )

        response = await service.create_chat_completion(request)

        details = response.usage.completion_tokens_details
        assert details is not None
        assert details.accepted_prediction_tokens >= 0
        assert details.rejected_prediction_tokens >= 0

    @pytest.mark.asyncio
    async def test_predicted_outputs_non_gpt4o_ignored(self):
        """Test predicted outputs ignored for non-openai/gpt-oss-120b models."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[Message(role=Role.USER, content="Hello")],
            prediction=PredictionContent(type="content", content="Prediction"),
        )

        response = await service.create_chat_completion(request)

        # Should be ignored for non-openai/gpt-oss-120b models
        details = response.usage.completion_tokens_details
        if details:
            assert details.accepted_prediction_tokens == 0
            assert details.rejected_prediction_tokens == 0


class TestLoRAModels:
    """Test LoRA fine-tuned model support."""

    @pytest.mark.asyncio
    async def test_lora_model_parsing(self):
        """Test LoRA model naming is parsed correctly."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        model_id = "ft:openai/gpt-oss-20b-2024-07-18:my-org::ABC123"

        request = ChatCompletionRequest(
            model=model_id,
            messages=[Message(role=Role.USER, content="Test")],
        )

        response = await service.create_chat_completion(request)

        # Model should be auto-created
        assert model_id in service.models
        model = service.models[model_id]

        # Check parsed fields
        assert model.owned_by == "my-org"
        assert model.root == "openai/gpt-oss-20b-2024-07-18"
        assert model.parent == "openai/gpt-oss-20b-2024-07-18"

    @pytest.mark.asyncio
    async def test_lora_model_no_special_token_handling(self):
        """Test LoRA models use same token counting as base."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        base_request = ChatCompletionRequest(
            model="openai/gpt-oss-20b",
            messages=[Message(role=Role.USER, content="Same prompt")],
        )

        lora_request = ChatCompletionRequest(
            model="ft:openai/gpt-oss-20b:org::id",
            messages=[Message(role=Role.USER, content="Same prompt")],
        )

        base_response = await service.create_chat_completion(base_request)
        lora_response = await service.create_chat_completion(lora_request)

        # Token counts should be identical
        assert base_response.usage.prompt_tokens == lora_response.usage.prompt_tokens


class TestMoEModels:
    """Test Mixture of Experts model detection."""

    def test_moe_detection(self):
        """Test MoE model detection."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        # MoE models
        assert service._is_moe_model("mixtral-8x7b") is True
        assert service._is_moe_model("gpt-oss-120b") is True
        assert service._is_moe_model("deepseek-v3") is True

        # Non-MoE models
        assert service._is_moe_model("openai/gpt-oss-120b") is False
        assert service._is_moe_model("meta-llama/Llama-3.1-8B-Instruct") is False


class TestStreamingWithUsage:
    """Test streaming with usage statistics."""

    @pytest.mark.asyncio
    async def test_streaming_without_usage(self):
        """Test streaming doesn't include usage by default."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello")],
            stream=True,
        )

        chunks = []
        async for chunk in service.create_chat_completion_stream(request):
            chunks.append(chunk)

        # No chunk should have usage
        assert all(chunk.usage is None for chunk in chunks)

    @pytest.mark.asyncio
    async def test_streaming_with_usage_enabled(self):
        """Test streaming includes usage when requested."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello")],
            stream=True,
            stream_options=StreamOptions(include_usage=True),
        )

        chunks = []
        usage_chunks = []

        async for chunk in service.create_chat_completion_stream(request):
            chunks.append(chunk)
            if chunk.usage:
                usage_chunks.append(chunk)

        # Exactly one chunk should have usage (final chunk)
        assert len(usage_chunks) == 1
        usage_chunk = usage_chunks[0]

        assert usage_chunk.usage.prompt_tokens > 0
        assert usage_chunk.usage.completion_tokens > 0
        assert usage_chunk.usage.total_tokens > 0
        assert usage_chunk.choices[0].finish_reason == "stop"


class TestTokenBasedStreaming:
    """Test token-based streaming (words + punctuation)."""

    @pytest.mark.asyncio
    async def test_tokens_are_words_or_punctuation(self):
        """Test streaming returns token-sized chunks."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True,
        )

        content_chunks = []
        async for chunk in service.create_chat_completion_stream(request):
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                content_chunks.append(content)

        # Each chunk should be relatively small (token-sized)
        # Words are typically 1-15 characters
        for chunk in content_chunks:
            # Remove leading space for checking
            chunk_stripped = chunk.lstrip()
            assert len(chunk_stripped) < 20  # Reasonable token size


class TestModelAutoCreation:
    """Test automatic model creation for various formats."""

    @pytest.mark.asyncio
    async def test_auto_create_custom_model(self):
        """Test custom model names are auto-created."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        custom_model = "my-custom-model-v1"

        request = ChatCompletionRequest(
            model=custom_model,
            messages=[Message(role=Role.USER, content="Test")],
        )

        response = await service.create_chat_completion(request)

        assert custom_model in service.models
        assert response.model == custom_model

    @pytest.mark.asyncio
    async def test_auto_create_mixtral_sets_owner(self):
        """Test Mixtral models get correct owner."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="mixtral-custom-8x7b",
            messages=[Message(role=Role.USER, content="Test")],
        )

        await service.create_chat_completion(request)

        model = service.models["mixtral-custom-8x7b"]
        assert model.owned_by == "mistralai"


class TestIntegration:
    """Integration tests combining multiple features."""

    @pytest.mark.asyncio
    async def test_gpt_oss_with_kv_cache_and_reasoning(self):
        """Test gpt-oss with KV cache and reasoning content."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        system_prompt = "You are a helpful assistant. " * 100

        # First request
        request1 = ChatCompletionRequest(
            model="gpt-oss-20b",
            messages=[
                Message(role=Role.SYSTEM, content=system_prompt),
                Message(role=Role.USER, content="Question 1"),
            ],
        )
        response1 = await service.create_chat_completion(request1)

        # Should have reasoning but no cache
        assert response1.choices[0].message.reasoning_content is not None
        assert response1.usage.prompt_tokens_details.cached_tokens == 0
        assert response1.usage.completion_tokens_details.reasoning_tokens > 0

        # Second request
        request2 = ChatCompletionRequest(
            model="gpt-oss-20b",
            messages=[
                Message(role=Role.SYSTEM, content=system_prompt),
                Message(role=Role.USER, content="Question 2"),
            ],
        )
        response2 = await service.create_chat_completion(request2)

        # Should have reasoning AND cache hit
        assert response2.choices[0].message.reasoning_content is not None
        assert response2.usage.prompt_tokens_details.cached_tokens > 0
        assert response2.usage.completion_tokens_details.reasoning_tokens > 0

    @pytest.mark.asyncio
    async def test_predicted_outputs_with_streaming(self):
        """Test predicted outputs work in streaming mode."""
        config = AppConfig(response_delay=0.0)
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Refactor code")],
            prediction=PredictionContent(type="content", content="Code here"),
            stream=True,
            stream_options=StreamOptions(include_usage=True),
        )

        usage_found = False
        async for chunk in service.create_chat_completion_stream(request):
            if chunk.usage:
                usage_found = True
                # Usage is included
                assert chunk.usage.prompt_tokens > 0
                assert chunk.usage.completion_tokens > 0

        assert usage_found
