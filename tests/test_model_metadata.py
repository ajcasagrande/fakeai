"""
Comprehensive tests for model metadata system.

Tests model capabilities, pricing information, and feature validation.
"""
import pytest


@pytest.mark.unit
class TestModelMetadata:
    """Test model metadata properties."""

    def test_all_models_have_metadata(self, service_no_auth):
        """All pre-defined models should have complete metadata."""
        for model_id, model in service_no_auth.models.items():
            assert model.context_window > 0, f"{model_id} has invalid context_window"
            assert model.max_output_tokens >= 0, f"{model_id} has invalid max_output_tokens"
            assert isinstance(model.supports_vision, bool), f"{model_id} has invalid supports_vision"
            assert isinstance(model.supports_audio, bool), f"{model_id} has invalid supports_audio"
            assert isinstance(model.supports_tools, bool), f"{model_id} has invalid supports_tools"

    def test_gpt4o_supports_vision_and_audio(self, service_no_auth):
        """GPT-4o should support vision and audio."""
        model = service_no_auth.models["openai/gpt-oss-120b"]
        assert model.supports_vision is True
        assert model.supports_audio is True
        assert model.supports_tools is True

    def test_gpt35_no_vision_support(self, service_no_auth):
        """GPT-3.5-turbo should not support vision."""
        model = service_no_auth.models["meta-llama/Llama-3.1-8B-Instruct"]
        assert model.supports_vision is False
        assert model.supports_audio is False
        assert model.supports_tools is True

    def test_o1_no_tool_support(self, service_no_auth):
        """O1 models should not support tool calling."""
        model = service_no_auth.models["deepseek-ai/DeepSeek-R1"]
        assert model.supports_tools is False
        assert model.supports_vision is False

    def test_claude_models_have_vision_support(self, service_no_auth):
        """Claude 3 models should support vision."""
        for model_id in ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]:
            model = service_no_auth.models[model_id]
            assert model.supports_vision is True
            assert model.supports_tools is True

    def test_gemini_supports_multimodal(self, service_no_auth):
        """Gemini models should support vision and audio."""
        for model_id in ["gemini-1.5-pro", "gemini-1.5-flash"]:
            model = service_no_auth.models[model_id]
            assert model.supports_vision is True
            assert model.supports_audio is True
            assert model.supports_tools is True

    def test_embedding_models_no_tools(self, service_no_auth):
        """Embedding models should not support tool calling."""
        for model_id in ["sentence-transformers/all-mpnet-base-v2", "nomic-ai/nomic-embed-text-v1.5", "BAAI/bge-m3"]:
            model = service_no_auth.models[model_id]
            assert model.supports_tools is False
            assert model.max_output_tokens == 0

    def test_models_have_training_cutoff(self, service_no_auth):
        """Models should have training cutoff dates."""
        model = service_no_auth.models["openai/gpt-oss-120b"]
        assert model.training_cutoff == "2023-10"

        model = service_no_auth.models["meta-llama/Llama-3.1-8B-Instruct"]
        assert model.training_cutoff == "2021-09"

    def test_models_have_correct_context_windows(self, service_no_auth):
        """Models should have accurate context window sizes."""
        assert service_no_auth.models["meta-llama/Llama-3.1-8B-Instruct"].context_window == 16385
        assert service_no_auth.models["openai/gpt-oss-120b"].context_window == 128000
        assert service_no_auth.models["claude-3-opus"].context_window == 200000
        assert service_no_auth.models["gemini-1.5-pro"].context_window == 2000000

    def test_models_have_pricing(self, service_no_auth):
        """Models should have pricing information."""
        model = service_no_auth.models["openai/gpt-oss-120b"]
        assert model.pricing is not None
        assert model.pricing.input_per_million == 2.50
        assert model.pricing.output_per_million == 10.00
        assert model.pricing.cached_input_per_million == 1.25

    def test_free_models_zero_pricing(self, service_no_auth):
        """Open source models should have zero pricing."""
        model = service_no_auth.models["gpt-oss-120b"]
        assert model.pricing is not None
        assert model.pricing.input_per_million == 0.0
        assert model.pricing.output_per_million == 0.0


@pytest.mark.unit
class TestGetModelCapability:
    """Test get_model_capability helper method."""

    def test_check_vision_capability(self, service_no_auth):
        """Should correctly check vision capability."""
        assert service_no_auth.get_model_capability("openai/gpt-oss-120b", "vision") is True
        assert service_no_auth.get_model_capability("meta-llama/Llama-3.1-8B-Instruct", "vision") is False

    def test_check_audio_capability(self, service_no_auth):
        """Should correctly check audio capability."""
        assert service_no_auth.get_model_capability("openai/gpt-oss-120b", "audio") is True
        assert service_no_auth.get_model_capability("openai/gpt-oss-120b", "audio") is False

    def test_check_tools_capability(self, service_no_auth):
        """Should correctly check tools capability."""
        assert service_no_auth.get_model_capability("openai/gpt-oss-120b", "tools") is True
        assert service_no_auth.get_model_capability("deepseek-ai/DeepSeek-R1", "tools") is False

    def test_invalid_capability_raises_error(self, service_no_auth):
        """Invalid capability name should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid capability"):
            service_no_auth.get_model_capability("openai/gpt-oss-120b", "invalid")

    def test_auto_creates_model(self, service_no_auth):
        """Should auto-create model if it doesn't exist."""
        # Model doesn't exist yet
        assert "my-custom-model" not in service_no_auth.models

        # Should auto-create with defaults
        result = service_no_auth.get_model_capability("my-custom-model", "tools")
        assert result is True  # Default is True
        assert "my-custom-model" in service_no_auth.models


@pytest.mark.unit
class TestGetModelPricing:
    """Test get_model_pricing helper method."""

    def test_get_pricing_for_gpt4o(self, service_no_auth):
        """Should return pricing for GPT-4o."""
        pricing = service_no_auth.get_model_pricing("openai/gpt-oss-120b")
        assert pricing is not None
        assert pricing.input_per_million == 2.50
        assert pricing.output_per_million == 10.00
        assert pricing.cached_input_per_million == 1.25

    def test_get_pricing_for_claude(self, service_no_auth):
        """Should return pricing for Claude models."""
        pricing = service_no_auth.get_model_pricing("claude-3-sonnet")
        assert pricing is not None
        assert pricing.input_per_million == 3.00
        assert pricing.output_per_million == 15.00

    def test_get_pricing_for_free_model(self, service_no_auth):
        """Should return zero pricing for open source models."""
        pricing = service_no_auth.get_model_pricing("gpt-oss-120b")
        assert pricing is not None
        assert pricing.input_per_million == 0.0
        assert pricing.output_per_million == 0.0

    def test_no_pricing_for_image_models(self, service_no_auth):
        """Image models should have None pricing (priced per image)."""
        pricing = service_no_auth.get_model_pricing("stabilityai/stable-diffusion-xl-base-1.0")
        assert pricing is None

    def test_auto_creates_model(self, service_no_auth):
        """Should auto-create model if it doesn't exist."""
        pricing = service_no_auth.get_model_pricing("new-model")
        # Auto-created models have no pricing by default
        assert pricing is None


@pytest.mark.unit
class TestValidateModelFeature:
    """Test validate_model_feature helper method."""

    def test_validates_supported_feature(self, service_no_auth):
        """Should not raise error for supported features."""
        # Should not raise
        service_no_auth.validate_model_feature("openai/gpt-oss-120b", "vision")
        service_no_auth.validate_model_feature("openai/gpt-oss-120b", "audio")
        service_no_auth.validate_model_feature("openai/gpt-oss-120b", "tools")

    def test_raises_error_for_unsupported_vision(self, service_no_auth):
        """Should raise error if model doesn't support vision."""
        with pytest.raises(ValueError, match="does not support vision"):
            service_no_auth.validate_model_feature("meta-llama/Llama-3.1-8B-Instruct", "vision")

    def test_raises_error_for_unsupported_audio(self, service_no_auth):
        """Should raise error if model doesn't support audio."""
        with pytest.raises(ValueError, match="does not support audio"):
            service_no_auth.validate_model_feature("openai/gpt-oss-120b", "audio")

    def test_raises_error_for_unsupported_tools(self, service_no_auth):
        """Should raise error if model doesn't support tools."""
        with pytest.raises(ValueError, match="does not support tools"):
            service_no_auth.validate_model_feature("deepseek-ai/DeepSeek-R1", "tools")

    def test_custom_feature_name_in_error(self, service_no_auth):
        """Should use custom feature name in error message."""
        with pytest.raises(ValueError, match="does not support image inputs"):
            service_no_auth.validate_model_feature("meta-llama/Llama-3.1-8B-Instruct", "vision", "image inputs")


@pytest.mark.integration
class TestCapabilitiesEndpoint:
    """Test /v1/models/{id}/capabilities endpoint."""

    def test_returns_200_for_valid_model(self, client_no_auth):
        """Should return 200 for valid model."""
        response = client_no_auth.get("/v1/models/openai/gpt-oss-120b/capabilities")
        assert response.status_code == 200

    def test_response_has_all_fields(self, client_no_auth):
        """Response should contain all capability fields."""
        response = client_no_auth.get("/v1/models/openai/gpt-oss-120b/capabilities")
        data = response.json()

        # Check all required fields
        assert data["id"] == "openai/gpt-oss-120b"
        assert data["object"] == "model.capabilities"
        assert "context_window" in data
        assert "max_output_tokens" in data
        assert "supports_vision" in data
        assert "supports_audio" in data
        assert "supports_tools" in data
        assert "training_cutoff" in data
        assert "pricing" in data

    def test_gpt4o_capabilities(self, client_no_auth):
        """GPT-4o should have correct capabilities."""
        response = client_no_auth.get("/v1/models/openai/gpt-oss-120b/capabilities")
        data = response.json()

        assert data["context_window"] == 128000
        assert data["max_output_tokens"] == 16384
        assert data["supports_vision"] is True
        assert data["supports_audio"] is True
        assert data["supports_tools"] is True
        assert data["training_cutoff"] == "2023-10"

    def test_gpt35_capabilities(self, client_no_auth):
        """GPT-3.5-turbo should have correct capabilities."""
        response = client_no_auth.get("/v1/models/meta-llama/Llama-3.1-8B-Instruct/capabilities")
        data = response.json()

        assert data["context_window"] == 16385
        assert data["max_output_tokens"] == 4096
        assert data["supports_vision"] is False
        assert data["supports_audio"] is False
        assert data["supports_tools"] is True

    def test_o1_capabilities(self, client_no_auth):
        """O1 models should not support tools."""
        response = client_no_auth.get("/v1/models/deepseek-ai/DeepSeek-R1/capabilities")
        data = response.json()

        assert data["supports_tools"] is False
        assert data["context_window"] == 200000
        assert data["max_output_tokens"] == 100000

    def test_pricing_information(self, client_no_auth):
        """Should return pricing information."""
        response = client_no_auth.get("/v1/models/openai/gpt-oss-120b/capabilities")
        data = response.json()

        assert data["pricing"] is not None
        assert data["pricing"]["input_per_million"] == 2.50
        assert data["pricing"]["output_per_million"] == 10.00
        assert data["pricing"]["cached_input_per_million"] == 1.25

    def test_auto_creates_unknown_model(self, client_no_auth):
        """Should auto-create unknown model with defaults."""
        response = client_no_auth.get("/v1/models/unknown-model/capabilities")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "unknown-model"
        assert data["context_window"] == 8192  # Default
        assert data["supports_tools"] is True  # Default

    def test_claude_capabilities(self, client_no_auth):
        """Claude models should have vision and tool support."""
        response = client_no_auth.get("/v1/models/claude-3-opus/capabilities")
        data = response.json()

        assert data["supports_vision"] is True
        assert data["supports_tools"] is True
        assert data["context_window"] == 200000

    def test_gemini_capabilities(self, client_no_auth):
        """Gemini models should support vision and audio."""
        response = client_no_auth.get("/v1/models/gemini-1.5-pro/capabilities")
        data = response.json()

        assert data["supports_vision"] is True
        assert data["supports_audio"] is True
        assert data["supports_tools"] is True
        assert data["context_window"] == 2000000

    def test_embedding_model_capabilities(self, client_no_auth):
        """Embedding models should have zero output tokens."""
        response = client_no_auth.get("/v1/models/sentence-transformers/all-mpnet-base-v2/capabilities")
        data = response.json()

        assert data["max_output_tokens"] == 0
        assert data["supports_tools"] is False


@pytest.mark.integration
class TestModelListIncludesMetadata:
    """Test that model list includes metadata."""

    def test_list_models_includes_metadata(self, client_no_auth):
        """List models endpoint should include metadata fields."""
        response = client_no_auth.get("/v1/models")
        data = response.json()

        assert "data" in data
        assert len(data["data"]) > 0

        # Check first model has metadata
        model = data["data"][0]
        assert "context_window" in model
        assert "max_output_tokens" in model
        assert "supports_vision" in model
        assert "supports_audio" in model
        assert "supports_tools" in model

    def test_get_model_includes_metadata(self, client_no_auth):
        """Get model endpoint should include metadata fields."""
        response = client_no_auth.get("/v1/models/openai/gpt-oss-120b")
        data = response.json()

        assert data["id"] == "openai/gpt-oss-120b"
        assert "context_window" in data
        assert "max_output_tokens" in data
        assert "supports_vision" in data
        assert "supports_audio" in data
        assert "supports_tools" in data
        assert "pricing" in data


@pytest.mark.integration
class TestModelCount:
    """Test that we have comprehensive model coverage."""

    def test_has_30_plus_models(self, service_no_auth):
        """Should have at least 30 pre-defined models."""
        assert len(service_no_auth.models) >= 30

    def test_has_gpt_models(self, service_no_auth):
        """Should have comprehensive GPT model coverage."""
        gpt_models = [
            "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            "meta-llama/Llama-3.1-8B-Instruct",
            "meta-llama/Llama-3.1-8B-Instruct",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b-realtime",
        ]
        for model in gpt_models:
            assert model in service_no_auth.models

    def test_has_reasoning_models(self, service_no_auth):
        """Should have reasoning models."""
        reasoning_models = ["deepseek-ai/DeepSeek-R1", "deepseek-ai/DeepSeek-R1", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B", "gpt-oss-120b", "gpt-oss-20b"]
        for model in reasoning_models:
            assert model in service_no_auth.models

    def test_has_claude_models(self, service_no_auth):
        """Should have Claude models."""
        claude_models = ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
        for model in claude_models:
            assert model in service_no_auth.models

    def test_has_gemini_models(self, service_no_auth):
        """Should have Gemini models."""
        gemini_models = ["gemini-1.5-pro", "gemini-1.5-flash"]
        for model in gemini_models:
            assert model in service_no_auth.models

    def test_has_mixtral_models(self, service_no_auth):
        """Should have Mixtral models."""
        mixtral_models = ["mixtral-8x7b", "mixtral-8x22b", "mistral-large"]
        for model in mixtral_models:
            assert model in service_no_auth.models

    def test_has_deepseek_models(self, service_no_auth):
        """Should have DeepSeek models."""
        deepseek_models = ["deepseek-v3", "deepseek-ai/DeepSeek-R1-Distill-Llama-8B"]
        for model in deepseek_models:
            assert model in service_no_auth.models

    def test_has_llama_models(self, service_no_auth):
        """Should have Llama models."""
        llama_models = ["llama-3.1-405b", "llama-3.1-70b", "llama-3.1-8b"]
        for model in llama_models:
            assert model in service_no_auth.models

    def test_has_embedding_models(self, service_no_auth):
        """Should have embedding models."""
        embedding_models = [
            "sentence-transformers/all-mpnet-base-v2",
            "nomic-ai/nomic-embed-text-v1.5",
            "BAAI/bge-m3",
        ]
        for model in embedding_models:
            assert model in service_no_auth.models

    def test_has_image_models(self, service_no_auth):
        """Should have image generation models."""
        image_models = ["stabilityai/stable-diffusion-2-1", "stabilityai/stable-diffusion-xl-base-1.0"]
        for model in image_models:
            assert model in service_no_auth.models

    def test_has_tts_models(self, service_no_auth):
        """Should have TTS models."""
        tts_models = ["tts-1", "tts-1-hd"]
        for model in tts_models:
            assert model in service_no_auth.models
