"""
Test suite for model registry catalogs.

Comprehensive tests covering all provider catalogs, registry loading,
capabilities, pricing, and model characteristics.
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest

from fakeai.models_registry import ModelDefinition, ModelRegistry
from fakeai.models_registry.catalog import (
    ANTHROPIC_MODELS,
    DEEPSEEK_MODELS,
    META_MODELS,
    MISTRAL_MODELS,
    NVIDIA_MODELS,
    OPENAI_MODELS,
    create_default_registry,
    find_models_by_capability,
    get_anthropic_models,
    get_deepseek_models,
    get_meta_models,
    get_mistral_models,
    get_nvidia_models,
    get_openai_models,
    get_provider_models,
    get_provider_stats,
    list_all_model_ids,
    load_all_models,
    load_provider_models,
)

# Provider Catalog Tests


class TestOpenAICatalog:
    """Tests for OpenAI model catalog."""

    def test_openai_models_exist(self):
        """Test that OpenAI models list is not empty."""
        assert len(OPENAI_MODELS) > 0
        assert len(get_openai_models()) > 0

    def test_gpt_oss_models_present(self):
        """Test that GPT-OSS models are included."""
        model_ids = [m.model_id for m in OPENAI_MODELS]
        assert "openai/gpt-oss-120b" in model_ids
        assert "openai/gpt-oss-20b" in model_ids

    def test_gpt_oss_has_reasoning(self):
        """Test that GPT-OSS models have reasoning capability."""
        gpt_oss_120b = next(
            m for m in OPENAI_MODELS if m.model_id == "openai/gpt-oss-120b"
        )
        assert gpt_oss_120b.capabilities.supports_reasoning
        assert gpt_oss_120b.capabilities.supports_predicted_outputs
        assert gpt_oss_120b.capabilities.is_moe

    def test_gpt_oss_moe_config(self):
        """Test that GPT-OSS models have correct MoE configuration."""
        gpt_oss_120b = next(
            m for m in OPENAI_MODELS if m.model_id == "openai/gpt-oss-120b"
        )
        assert gpt_oss_120b.capabilities.moe_config is not None
        assert gpt_oss_120b.capabilities.moe_config.total_params == 120_000_000_000
        assert gpt_oss_120b.capabilities.moe_config.active_params == 37_000_000_000
        assert gpt_oss_120b.capabilities.moe_config.num_experts == 16
        assert gpt_oss_120b.capabilities.moe_config.experts_per_token == 2

    def test_gpt4o_multimodal(self):
        """Test that GPT-4o has multimodal capabilities."""
        gpt4o = next(m for m in OPENAI_MODELS if m.model_id == "openai/gpt-oss-120b")
        assert gpt4o.capabilities.supports_vision
        assert gpt4o.capabilities.supports_audio_input
        assert gpt4o.capabilities.supports_audio_output
        assert gpt4o.capabilities.supports_predicted_outputs

    def test_embedding_models(self):
        """Test that embedding models are present and configured correctly."""
        model_ids = [m.model_id for m in OPENAI_MODELS]
        assert "nomic-ai/nomic-embed-text-v1.5" in model_ids
        assert "BAAI/bge-m3" in model_ids

        embed_small = next(
            m for m in OPENAI_MODELS if m.model_id == "nomic-ai/nomic-embed-text-v1.5"
        )
        assert embed_small.capabilities.supports_embeddings
        assert not embed_small.capabilities.supports_chat
        assert embed_small.custom_fields["dimensions"] == 1536

    def test_moderation_models(self):
        """Test that moderation models are present."""
        model_ids = [m.model_id for m in OPENAI_MODELS]
        assert "text-moderation-latest" in model_ids
        assert "text-moderation-stable" in model_ids

        mod = next(m for m in OPENAI_MODELS if m.model_id == "text-moderation-latest")
        assert mod.capabilities.supports_moderation

    def test_o1_legacy_models(self):
        """Test that O1 legacy models are included."""
        model_ids = [m.model_id for m in OPENAI_MODELS]
        assert "deepseek-ai/DeepSeek-R1" in model_ids
        assert "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B" in model_ids

        o1 = next(m for m in OPENAI_MODELS if m.model_id == "deepseek-ai/DeepSeek-R1")
        assert o1.capabilities.supports_reasoning
        assert o1.capabilities.is_moe

    def test_openai_pricing_accuracy(self):
        """Test that OpenAI pricing is accurate."""
        gpt4o = next(m for m in OPENAI_MODELS if m.model_id == "openai/gpt-oss-120b")
        assert gpt4o.custom_fields["pricing"]["input_per_million"] == 2.50
        assert gpt4o.custom_fields["pricing"]["output_per_million"] == 10.0

        gpt_oss_120b = next(
            m for m in OPENAI_MODELS if m.model_id == "openai/gpt-oss-120b"
        )
        assert gpt_oss_120b.custom_fields["pricing"]["input_per_million"] == 10.0
        assert gpt_oss_120b.custom_fields["pricing"]["output_per_million"] == 30.0


class TestAnthropicCatalog:
    """Tests for Anthropic model catalog."""

    def test_anthropic_models_exist(self):
        """Test that Anthropic models list is not empty."""
        assert len(ANTHROPIC_MODELS) > 0
        assert len(get_anthropic_models()) > 0

    def test_claude_35_present(self):
        """Test that Claude 3.5 Sonnet is present."""
        model_ids = [m.model_id for m in ANTHROPIC_MODELS]
        assert "claude-3-5-sonnet-20241022" in model_ids

    def test_claude_3_family(self):
        """Test that Claude 3 family is complete."""
        model_ids = [m.model_id for m in ANTHROPIC_MODELS]
        assert "claude-3-opus-20240229" in model_ids
        assert "claude-3-sonnet-20240229" in model_ids
        assert "claude-3-haiku-20240307" in model_ids

    def test_claude_vision_support(self):
        """Test that Claude models have vision support."""
        opus = next(
            m for m in ANTHROPIC_MODELS if m.model_id == "claude-3-opus-20240229"
        )
        assert opus.capabilities.supports_vision
        assert opus.capabilities.max_context_length == 200000

    def test_claude_legacy(self):
        """Test that Claude 2.1 is present as legacy."""
        claude_21 = next(m for m in ANTHROPIC_MODELS if m.model_id == "claude-2.1")
        assert not claude_21.capabilities.supports_vision
        assert "legacy" in claude_21.capabilities.tags


class TestMetaCatalog:
    """Tests for Meta Llama model catalog."""

    def test_meta_models_exist(self):
        """Test that Meta models list is not empty."""
        assert len(META_MODELS) > 0
        assert len(get_meta_models()) > 0

    def test_llama_31_family(self):
        """Test that Llama 3.1 family is complete."""
        model_ids = [m.model_id for m in META_MODELS]
        assert "meta-llama/Llama-3.1-405B-Instruct" in model_ids
        assert "meta-llama/Llama-3.1-70B-Instruct" in model_ids
        assert "meta-llama/Llama-3.1-8B-Instruct" in model_ids

    def test_llama_31_context_window(self):
        """Test that Llama 3.1 models have 128K context."""
        llama_8b = next(
            m for m in META_MODELS if m.model_id == "meta-llama/Llama-3.1-8B-Instruct"
        )
        assert llama_8b.capabilities.max_context_length == 128000

    def test_llama_3_family(self):
        """Test that Llama 3 family is present."""
        model_ids = [m.model_id for m in META_MODELS]
        assert "meta-llama/Llama-3-70B-Instruct" in model_ids
        assert "meta-llama/Llama-3-8B-Instruct" in model_ids

    def test_llama_2_legacy(self):
        """Test that Llama 2 family is present as legacy."""
        model_ids = [m.model_id for m in META_MODELS]
        assert "meta-llama/Llama-2-70b-chat-hf" in model_ids
        assert "meta-llama/Llama-2-13b-chat-hf" in model_ids
        assert "meta-llama/Llama-2-7b-chat-hf" in model_ids

        llama_2_7b = next(
            m for m in META_MODELS if m.model_id == "meta-llama/Llama-2-7b-chat-hf"
        )
        assert "legacy" in llama_2_7b.capabilities.tags
        assert not llama_2_7b.capabilities.supports_function_calling


class TestMistralCatalog:
    """Tests for Mistral AI model catalog."""

    def test_mistral_models_exist(self):
        """Test that Mistral models list is not empty."""
        assert len(MISTRAL_MODELS) > 0
        assert len(get_mistral_models()) > 0

    def test_mixtral_moe_models(self):
        """Test that Mixtral MoE models are present."""
        model_ids = [m.model_id for m in MISTRAL_MODELS]
        assert "mistralai/Mixtral-8x22B-Instruct-v0.1" in model_ids
        assert "mistralai/Mixtral-8x7B-Instruct-v0.1" in model_ids

    def test_mixtral_8x7b_moe_config(self):
        """Test Mixtral 8x7B MoE configuration."""
        mixtral = next(
            m
            for m in MISTRAL_MODELS
            if m.model_id == "mistralai/Mixtral-8x7B-Instruct-v0.1"
        )
        assert mixtral.capabilities.is_moe
        assert mixtral.capabilities.moe_config is not None
        assert mixtral.capabilities.moe_config.total_params == 46_700_000_000
        assert mixtral.capabilities.moe_config.active_params == 12_900_000_000
        assert mixtral.capabilities.moe_config.num_experts == 8
        assert mixtral.capabilities.moe_config.experts_per_token == 2

    def test_mixtral_8x22b_moe_config(self):
        """Test Mixtral 8x22B MoE configuration."""
        mixtral = next(
            m
            for m in MISTRAL_MODELS
            if m.model_id == "mistralai/Mixtral-8x22B-Instruct-v0.1"
        )
        assert mixtral.capabilities.is_moe
        assert mixtral.capabilities.moe_config.total_params == 141_000_000_000
        assert mixtral.capabilities.moe_config.active_params == 39_000_000_000

    def test_mistral_short_aliases(self):
        """Test that short aliases exist."""
        model_ids = [m.model_id for m in MISTRAL_MODELS]
        assert "mixtral-8x7b" in model_ids
        assert "mixtral-8x22b" in model_ids

    def test_mistral_commercial_models(self):
        """Test that commercial Mistral models are present."""
        model_ids = [m.model_id for m in MISTRAL_MODELS]
        assert "mistral-small-latest" in model_ids
        assert "mistral-medium-latest" in model_ids
        assert "mistral-large-latest" in model_ids


class TestDeepSeekCatalog:
    """Tests for DeepSeek model catalog."""

    def test_deepseek_models_exist(self):
        """Test that DeepSeek models list is not empty."""
        assert len(DEEPSEEK_MODELS) > 0
        assert len(get_deepseek_models()) > 0

    def test_deepseek_v3_moe(self):
        """Test DeepSeek V3 MoE configuration."""
        v3 = next(m for m in DEEPSEEK_MODELS if m.model_id == "deepseek-v3")
        assert v3.capabilities.is_moe
        assert v3.capabilities.moe_config.total_params == 671_000_000_000
        assert v3.capabilities.moe_config.active_params == 37_000_000_000
        assert v3.capabilities.moe_config.num_experts == 256
        assert v3.capabilities.moe_config.experts_per_token == 8

    def test_deepseek_r1_reasoning(self):
        """Test DeepSeek-R1 reasoning capabilities."""
        r1 = next(m for m in DEEPSEEK_MODELS if m.model_id == "deepseek-ai/DeepSeek-R1")
        assert r1.capabilities.supports_reasoning
        assert r1.capabilities.is_moe
        assert r1.capabilities.max_context_length == 200000
        assert r1.capabilities.max_output_tokens == 100000

    def test_deepseek_r1_distill_models(self):
        """Test DeepSeek-R1-Distill variants."""
        model_ids = [m.model_id for m in DEEPSEEK_MODELS]
        assert "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B" in model_ids
        assert "deepseek-ai/DeepSeek-R1-Distill-Llama-70B" in model_ids

        distill_32b = next(
            m
            for m in DEEPSEEK_MODELS
            if m.model_id == "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
        )
        assert distill_32b.capabilities.supports_reasoning
        assert not distill_32b.capabilities.is_moe  # Distilled models are not MoE
        assert distill_32b.capabilities.parameter_count == 32_000_000_000

    def test_deepseek_coder(self):
        """Test DeepSeek Coder model."""
        coder = next(m for m in DEEPSEEK_MODELS if m.model_id == "deepseek-coder")
        assert "code" in coder.capabilities.tags
        assert coder.capabilities.supports_chat


class TestNVIDIACatalog:
    """Tests for NVIDIA model catalog."""

    def test_nvidia_models_exist(self):
        """Test that NVIDIA models list is not empty."""
        assert len(NVIDIA_MODELS) > 0
        assert len(get_nvidia_models()) > 0

    def test_cosmos_vision(self):
        """Test NVIDIA Cosmos Vision model."""
        cosmos = next(m for m in NVIDIA_MODELS if m.model_id == "nvidia/cosmos-vision")
        assert cosmos.capabilities.supports_video
        assert cosmos.capabilities.supports_vision
        assert cosmos.custom_fields.get("video_support") is True

    def test_nemo_optimized(self):
        """Test NVIDIA NeMo optimized model."""
        nemo = next(
            m
            for m in NVIDIA_MODELS
            if m.model_id == "nvidia/llama-3.1-nemotron-70b-instruct"
        )
        assert nemo.capabilities.parameter_count == 70_000_000_000
        assert nemo.custom_fields.get("nim_optimized") is True

    def test_reranking_model(self):
        """Test NVIDIA reranking model."""
        rerank = next(
            m for m in NVIDIA_MODELS if m.model_id == "nvidia/nv-rerank-qa-mistral-4b"
        )
        assert not rerank.capabilities.supports_chat
        assert rerank.custom_fields.get("reranking") is True


# Registry Loader Tests


class TestRegistryLoader:
    """Tests for registry loader functions."""

    def test_get_provider_models_openai(self):
        """Test getting models from specific provider."""
        models = get_provider_models("openai")
        assert len(models) > 0
        assert all(isinstance(m, ModelDefinition) for m in models)

    def test_get_provider_models_all(self):
        """Test getting models from all providers."""
        models = get_provider_models("all")
        assert len(models) > 0
        # Should be more than any single provider
        openai_count = len(get_provider_models("openai"))
        assert len(models) > openai_count

    def test_get_provider_models_invalid(self):
        """Test that invalid provider raises error."""
        with pytest.raises(ValueError, match="Invalid provider"):
            get_provider_models("invalid_provider")

    def test_load_provider_models_single(self):
        """Test loading models from single provider."""
        registry = ModelRegistry()
        count = load_provider_models(registry, "openai")
        assert count > 0
        assert len(registry) == count

    def test_load_provider_models_multiple(self):
        """Test loading models from multiple providers."""
        registry = ModelRegistry()
        count = load_provider_models(registry, ["openai", "meta"])
        assert count > 0
        assert len(registry) == count

    def test_load_all_models(self):
        """Test loading all models."""
        registry = ModelRegistry()
        count = load_all_models(registry)
        assert count > 0
        assert len(registry) == count

    def test_create_default_registry(self):
        """Test creating default registry."""
        registry = create_default_registry()
        assert len(registry) > 0

    def test_create_default_registry_specific_provider(self):
        """Test creating registry with specific provider."""
        registry = create_default_registry(providers="openai")
        assert len(registry) > 0
        # Should only have OpenAI models
        openai_count = len(get_provider_models("openai"))
        assert len(registry) == openai_count

    def test_get_provider_stats(self):
        """Test getting provider statistics."""
        stats = get_provider_stats()
        assert "openai" in stats
        assert "anthropic" in stats
        assert "meta" in stats
        assert "mistral" in stats
        assert "deepseek" in stats
        assert "nvidia" in stats
        assert "total" in stats
        assert stats["total"] > 0

    def test_list_all_model_ids(self):
        """Test listing all model IDs."""
        all_ids = list_all_model_ids()
        assert len(all_ids) > 0
        assert "openai/gpt-oss-120b" in all_ids
        assert "claude-3-opus-20240229" in all_ids

    def test_find_models_by_capability_reasoning(self):
        """Test finding models by reasoning capability."""
        reasoning_models = find_models_by_capability("reasoning")
        assert len(reasoning_models) > 0
        assert all(m.capabilities.supports_reasoning for m in reasoning_models)

    def test_find_models_by_capability_vision(self):
        """Test finding models by vision capability."""
        vision_models = find_models_by_capability("vision")
        assert len(vision_models) > 0
        assert all(m.capabilities.supports_vision for m in vision_models)


# Integration Tests


class TestModelCountsAndCoverage:
    """Test overall model counts and coverage."""

    def test_total_model_count(self):
        """Test that we have a good number of models."""
        stats = get_provider_stats()
        # Should have at least 30 models total across all providers
        assert stats["total"] >= 30

    def test_openai_model_count(self):
        """Test OpenAI has expected number of models."""
        # At least 10 OpenAI models (GPT-OSS, GPT-4, GPT-3.5, O1, embeddings, moderation)
        assert len(OPENAI_MODELS) >= 10

    def test_anthropic_model_count(self):
        """Test Anthropic has expected number of models."""
        # At least 5 Claude models
        assert len(ANTHROPIC_MODELS) >= 5

    def test_meta_model_count(self):
        """Test Meta has expected number of models."""
        # At least 9 Llama models (3.1, 3, 2 families)
        assert len(META_MODELS) >= 9

    def test_mistral_model_count(self):
        """Test Mistral has expected number of models."""
        # At least 8 Mistral models (Mixtral + Mistral + commercial)
        assert len(MISTRAL_MODELS) >= 8

    def test_deepseek_model_count(self):
        """Test DeepSeek has expected number of models."""
        # At least 5 DeepSeek models (V3, R1, distills, coder)
        assert len(DEEPSEEK_MODELS) >= 5

    def test_nvidia_model_count(self):
        """Test NVIDIA has expected number of models."""
        # At least 3 NVIDIA models
        assert len(NVIDIA_MODELS) >= 3

    def test_all_models_have_pricing(self):
        """Test that all models have pricing information."""
        all_models = get_provider_models("all")
        for model in all_models:
            assert "pricing" in model.custom_fields
            pricing = model.custom_fields["pricing"]
            assert "input_per_million" in pricing
            assert "output_per_million" in pricing
            assert isinstance(pricing["input_per_million"], (int, float))
            assert isinstance(pricing["output_per_million"], (int, float))

    def test_all_models_have_latency_profile(self):
        """Test that all models have latency profiles."""
        all_models = get_provider_models("all")
        for model in all_models:
            assert model.capabilities.latency_profile is not None
            assert model.capabilities.latency_profile.time_to_first_token > 0
            assert model.capabilities.latency_profile.tokens_per_second > 0

    def test_moe_models_have_config(self):
        """Test that all MoE models have proper configuration."""
        all_models = get_provider_models("all")
        for model in all_models:
            if model.capabilities.is_moe:
                assert model.capabilities.moe_config is not None
                config = model.capabilities.moe_config
                assert config.total_params > config.active_params
                assert config.num_experts >= config.experts_per_token
                assert config.total_params > 0
                assert config.active_params > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
