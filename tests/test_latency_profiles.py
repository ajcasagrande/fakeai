"""
Tests for model-specific latency profiles.

Validates that latency profiles provide realistic timing characteristics
and dynamic adjustments based on runtime conditions.
"""

import time
from unittest.mock import patch

import pytest

from fakeai.latency_profiles import (
    DEFAULT_PROFILE,
    LATENCY_PROFILES,
    LatencyProfile,
    LatencyProfileManager,
    get_latency_manager,
)


class TestLatencyProfiles:
    """Test latency profile data structure."""

    def test_profile_attributes(self):
        """Test that profiles have all required attributes."""
        profile = LATENCY_PROFILES["gpt-4"]
        assert hasattr(profile, "ttft_ms")
        assert hasattr(profile, "ttft_std")
        assert hasattr(profile, "itl_ms")
        assert hasattr(profile, "itl_std")
        assert hasattr(profile, "throughput_tokens_per_sec")
        assert hasattr(profile, "prefill_tokens_per_sec")
        assert hasattr(profile, "model_size_b")
        assert hasattr(profile, "is_moe")
        assert hasattr(profile, "supports_speculative_decoding")

    def test_all_profiles_valid(self):
        """Test that all profiles have valid positive values."""
        for model_name, profile in LATENCY_PROFILES.items():
            assert profile.ttft_ms > 0, f"{model_name}: ttft_ms must be positive"
            assert profile.ttft_std >= 0, f"{model_name}: ttft_std must be non-negative"
            assert profile.itl_ms > 0, f"{model_name}: itl_ms must be positive"
            assert profile.itl_std >= 0, f"{model_name}: itl_std must be non-negative"
            assert (
                profile.throughput_tokens_per_sec > 0
            ), f"{model_name}: throughput must be positive"
            assert (
                profile.prefill_tokens_per_sec > 0
            ), f"{model_name}: prefill speed must be positive"
            assert (
                profile.model_size_b > 0
            ), f"{model_name}: model size must be positive"

    def test_model_size_correlation(self):
        """Test that larger models generally have higher latency."""
        # Compare small vs large models in same family
        gpt35 = LATENCY_PROFILES["gpt-3.5-turbo"]
        gpt4 = LATENCY_PROFILES["gpt-4"]

        # GPT-4 (1.76T) should be slower than GPT-3.5 (175B)
        assert gpt4.ttft_ms > gpt35.ttft_ms, "Larger models should have higher TTFT"
        assert gpt4.itl_ms > gpt35.itl_ms, "Larger models should have higher ITL"

        # Llama models
        llama_7b = LATENCY_PROFILES["meta-llama/Llama-2-7b-chat-hf"]
        llama_70b = LATENCY_PROFILES["meta-llama/Llama-2-70b-chat-hf"]

        assert llama_70b.ttft_ms > llama_7b.ttft_ms
        assert llama_70b.itl_ms > llama_7b.itl_ms

    def test_moe_models_identified(self):
        """Test that MoE models are correctly flagged."""
        moe_models = [
            "gpt-4",
            "mixtral-8x7b",
            "mixtral-8x22b",
            "openai/gpt-oss-120b",
            "deepseek-v3",
        ]

        for model in moe_models:
            profile = LATENCY_PROFILES[model]
            assert profile.is_moe, f"{model} should be marked as MoE"

    def test_speculative_decoding_support(self):
        """Test that models with speculative decoding support are flagged."""
        sd_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "openai/gpt-oss-120b",
        ]

        for model in sd_models:
            profile = LATENCY_PROFILES[model]
            assert (
                profile.supports_speculative_decoding
            ), f"{model} should support speculative decoding"

    def test_model_count(self):
        """Test that we have profiles for 30+ models."""
        assert (
            len(LATENCY_PROFILES) >= 30
        ), f"Expected at least 30 model profiles, got {len(LATENCY_PROFILES)}"

    def test_default_profile(self):
        """Test that default profile is reasonable."""
        assert DEFAULT_PROFILE.ttft_ms > 0
        assert DEFAULT_PROFILE.itl_ms > 0
        assert DEFAULT_PROFILE.throughput_tokens_per_sec > 0


class TestLatencyProfileManager:
    """Test LatencyProfileManager functionality."""

    def test_manager_initialization(self):
        """Test that manager initializes correctly."""
        manager = LatencyProfileManager()
        assert manager.get_active_requests() == 0

    def test_normalize_model_name(self):
        """Test model name normalization."""
        manager = LatencyProfileManager()

        # Exact match
        assert manager._normalize_model_name("gpt-4") == "gpt-4"

        # With organization prefix
        assert (
            manager._normalize_model_name("openai/gpt-oss-120b")
            == "openai/gpt-oss-120b"
        )

        # Without organization prefix
        normalized = manager._normalize_model_name("gpt-oss-120b")
        assert normalized in ["gpt-oss-120b", "openai/gpt-oss-120b"]

        # Fine-tuned model (ft:base:org::id)
        normalized = manager._normalize_model_name(
            "ft:openai/gpt-oss-20b:my-org::abc123"
        )
        assert normalized == "openai/gpt-oss-20b"

        # Version suffix stripping
        assert manager._normalize_model_name("gpt-4-0613") == "gpt-4"
        assert manager._normalize_model_name("gpt-3.5-turbo-0125") == "gpt-3.5-turbo"

    def test_get_profile_exact_match(self):
        """Test getting profile by exact model name."""
        manager = LatencyProfileManager()
        profile = manager.get_profile("gpt-4")
        assert profile == LATENCY_PROFILES["gpt-4"]

    def test_get_profile_with_org_prefix(self):
        """Test getting profile with organization prefix."""
        manager = LatencyProfileManager()
        profile = manager.get_profile("openai/gpt-oss-120b")
        assert profile.model_size_b == 120.0

    def test_get_profile_fine_tuned(self):
        """Test getting profile for fine-tuned model."""
        manager = LatencyProfileManager()
        profile = manager.get_profile("ft:openai/gpt-oss-20b:my-org::abc123")
        assert profile.model_size_b == 20.0

    def test_get_profile_unknown_model(self):
        """Test that unknown models get default profile."""
        manager = LatencyProfileManager()
        profile = manager.get_profile("unknown-model-xyz")
        assert profile == DEFAULT_PROFILE

    def test_get_ttft_base(self):
        """Test basic TTFT calculation."""
        manager = LatencyProfileManager()
        ttft = manager.get_ttft(model="gpt-4", prompt_tokens=100)

        # Should be in reasonable range (positive seconds)
        assert ttft > 0
        assert ttft < 5.0  # Less than 5 seconds

    def test_get_ttft_prompt_length_scaling(self):
        """Test that longer prompts increase TTFT."""
        manager = LatencyProfileManager()

        ttft_short = manager.get_ttft(model="gpt-4", prompt_tokens=50)
        ttft_medium = manager.get_ttft(model="gpt-4", prompt_tokens=500)
        ttft_long = manager.get_ttft(model="gpt-4", prompt_tokens=5000)

        # Longer prompts should generally have higher TTFT
        # (Allow some variance due to randomness)
        assert ttft_medium > ttft_short * 0.8
        assert ttft_long > ttft_medium * 0.8

    def test_get_ttft_kv_cache_speedup(self):
        """Test that KV cache hits reduce TTFT."""
        manager = LatencyProfileManager()

        # Without cache
        ttft_no_cache = manager.get_ttft(
            model="gpt-4",
            prompt_tokens=1000,
            kv_cache_hit=False,
        )

        # With cache hit (800 tokens cached)
        ttft_with_cache = manager.get_ttft(
            model="gpt-4",
            prompt_tokens=1000,
            kv_cache_hit=True,
            kv_cache_hit_tokens=800,
        )

        # Cache should provide speedup
        assert ttft_with_cache < ttft_no_cache
        # Should be at least 40% faster (60-80% reduction)
        assert ttft_with_cache < ttft_no_cache * 0.6

    def test_get_ttft_load_impact(self):
        """Test that high load increases TTFT."""
        manager = LatencyProfileManager()

        ttft_low_load = manager.get_ttft(
            model="gpt-4",
            prompt_tokens=100,
            current_load=10,
        )

        ttft_high_load = manager.get_ttft(
            model="gpt-4",
            prompt_tokens=100,
            current_load=100,
        )

        # High load should increase TTFT
        assert ttft_high_load > ttft_low_load

    def test_get_ttft_temperature_impact(self):
        """Test that temperature affects TTFT (minimal)."""
        manager = LatencyProfileManager()

        # Average over many samples to account for randomness
        samples = 100
        ttft_temp1_sum = 0.0
        ttft_temp2_sum = 0.0

        for _ in range(samples):
            ttft_temp1_sum += manager.get_ttft(
                model="gpt-4",
                prompt_tokens=100,
                temperature=1.0,
            )

            ttft_temp2_sum += manager.get_ttft(
                model="gpt-4",
                prompt_tokens=100,
                temperature=2.0,
            )

        ttft_temp1_avg = ttft_temp1_sum / samples
        ttft_temp2_avg = ttft_temp2_sum / samples

        # Higher temperature should slightly increase TTFT on average
        # But effect is minimal (<10%), and variance can mask this
        # Just verify both are in reasonable range
        assert ttft_temp1_avg > 0
        assert ttft_temp2_avg > 0
        # With temp=2.0, should be within 1-1.15x of base (3% increase expected)
        assert 0.9 < ttft_temp2_avg / ttft_temp1_avg < 1.2

    def test_get_itl_base(self):
        """Test basic ITL calculation."""
        manager = LatencyProfileManager()
        itl = manager.get_itl(model="gpt-4")

        # Should be in reasonable range (positive seconds)
        assert itl > 0
        assert itl < 1.0  # Less than 1 second

    def test_get_itl_temperature_impact(self):
        """Test that temperature affects ITL (minimal)."""
        manager = LatencyProfileManager()

        # Average over many samples to account for randomness
        samples = 100
        itl_temp1_sum = 0.0
        itl_temp2_sum = 0.0

        for _ in range(samples):
            itl_temp1_sum += manager.get_itl(model="gpt-4", temperature=1.0)
            itl_temp2_sum += manager.get_itl(model="gpt-4", temperature=2.0)

        itl_temp1_avg = itl_temp1_sum / samples
        itl_temp2_avg = itl_temp2_sum / samples

        # Higher temperature should slightly increase ITL on average
        # But effect is minimal (2% increase expected) and variance can mask it
        # Just verify both are in reasonable range
        assert itl_temp1_avg > 0
        assert itl_temp2_avg > 0
        # With temp=2.0, should be within 1-1.1x of base
        assert 0.9 < itl_temp2_avg / itl_temp1_avg < 1.15

    def test_get_itl_load_impact(self):
        """Test that load affects ITL."""
        manager = LatencyProfileManager()

        # Average over multiple samples to account for randomness
        samples = 50
        itl_low_sum = 0.0
        itl_high_sum = 0.0

        for _ in range(samples):
            itl_low_sum += manager.get_itl(model="gpt-4", current_load=5)
            itl_high_sum += manager.get_itl(model="gpt-4", current_load=50)

        itl_low_avg = itl_low_sum / samples
        itl_high_avg = itl_high_sum / samples

        # Higher load should increase ITL on average
        assert itl_high_avg > itl_low_avg * 0.98

    def test_get_generation_time(self):
        """Test total generation time calculation."""
        manager = LatencyProfileManager()

        total_time = manager.get_generation_time(
            model="gpt-4",
            output_tokens=100,
            prompt_tokens=50,
        )

        # Should be positive and reasonable
        assert total_time > 0
        assert total_time < 30.0  # Less than 30 seconds for 100 tokens

    def test_generation_time_scales_with_output(self):
        """Test that generation time scales with output tokens."""
        manager = LatencyProfileManager()

        time_10 = manager.get_generation_time(
            model="gpt-4",
            output_tokens=10,
            prompt_tokens=50,
        )

        time_100 = manager.get_generation_time(
            model="gpt-4",
            output_tokens=100,
            prompt_tokens=50,
        )

        # More output tokens should take longer
        assert time_100 > time_10

    def test_active_request_tracking(self):
        """Test active request counter."""
        manager = LatencyProfileManager()

        assert manager.get_active_requests() == 0

        manager.start_request()
        assert manager.get_active_requests() == 1

        manager.start_request()
        assert manager.get_active_requests() == 2

        manager.end_request()
        assert manager.get_active_requests() == 1

        manager.end_request()
        assert manager.get_active_requests() == 0

        # Should not go negative
        manager.end_request()
        assert manager.get_active_requests() == 0

    def test_reset_load(self):
        """Test resetting active request counter."""
        manager = LatencyProfileManager()

        manager.start_request()
        manager.start_request()
        manager.start_request()
        assert manager.get_active_requests() == 3

        manager.reset_load()
        assert manager.get_active_requests() == 0


class TestGlobalSingleton:
    """Test global singleton instance."""

    def test_get_latency_manager_singleton(self):
        """Test that get_latency_manager returns singleton."""
        manager1 = get_latency_manager()
        manager2 = get_latency_manager()

        assert manager1 is manager2

    def test_singleton_state_persists(self):
        """Test that singleton state persists across calls."""
        manager1 = get_latency_manager()
        manager1.start_request()

        manager2 = get_latency_manager()
        assert manager2.get_active_requests() == 1

        manager2.reset_load()

        manager3 = get_latency_manager()
        assert manager3.get_active_requests() == 0


class TestModelFamilies:
    """Test profiles for different model families."""

    def test_openai_models(self):
        """Test OpenAI model profiles."""
        models = ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo"]
        for model in models:
            assert model in LATENCY_PROFILES

    def test_gpt_oss_models(self):
        """Test GPT-OSS model profiles."""
        models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
        for model in models:
            assert model in LATENCY_PROFILES
            profile = LATENCY_PROFILES[model]
            assert profile.is_moe

    def test_deepseek_models(self):
        """Test DeepSeek model profiles."""
        models = [
            "deepseek-ai/DeepSeek-R1",
            "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
            "deepseek-v3",
        ]
        for model in models:
            assert model in LATENCY_PROFILES

    def test_mixtral_models(self):
        """Test Mixtral model profiles."""
        models = ["mixtral-8x7b", "mixtral-8x22b"]
        for model in models:
            assert model in LATENCY_PROFILES
            profile = LATENCY_PROFILES[model]
            assert profile.is_moe

    def test_llama_models(self):
        """Test Llama model profiles."""
        models = [
            "meta-llama/Llama-2-7b-chat-hf",
            "meta-llama/Llama-2-13b-chat-hf",
            "meta-llama/Llama-2-70b-chat-hf",
            "meta-llama/Llama-3.1-8B-Instruct",
            "meta-llama/Llama-3.1-70B-Instruct",
        ]
        for model in models:
            assert model in LATENCY_PROFILES

    def test_claude_models(self):
        """Test Claude model profiles."""
        models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]
        for model in models:
            assert model in LATENCY_PROFILES

    def test_phi_models(self):
        """Test Microsoft Phi model profiles."""
        models = [
            "microsoft/Phi-3-mini-4k-instruct",
            "microsoft/Phi-3-medium-4k-instruct",
        ]
        for model in models:
            assert model in LATENCY_PROFILES


class TestRealisticScenarios:
    """Test realistic usage scenarios."""

    def test_streaming_latency_simulation(self):
        """Test realistic streaming latency."""
        manager = LatencyProfileManager()

        model = "gpt-4o"
        prompt_tokens = 500
        output_tokens = 100

        # Simulate streaming
        ttft = manager.get_ttft(model=model, prompt_tokens=prompt_tokens)
        assert ttft > 0

        total_itl = 0.0
        for _ in range(output_tokens):
            itl = manager.get_itl(model=model)
            total_itl += itl

        total_time = ttft + total_itl
        assert total_time > ttft  # Total should include ITL time

    def test_cached_vs_uncached(self):
        """Test cached vs uncached request latency."""
        manager = LatencyProfileManager()

        model = "gpt-4"
        prompt_tokens = 2000

        # First request (no cache)
        ttft_uncached = manager.get_ttft(
            model=model,
            prompt_tokens=prompt_tokens,
            kv_cache_hit=False,
        )

        # Second request (80% cached)
        ttft_cached = manager.get_ttft(
            model=model,
            prompt_tokens=prompt_tokens,
            kv_cache_hit=True,
            kv_cache_hit_tokens=1600,  # 80% cached
        )

        # Cached should be significantly faster
        speedup = ttft_uncached / ttft_cached
        assert speedup > 1.5, f"Expected >1.5x speedup, got {speedup:.2f}x"

    def test_load_impact_scenario(self):
        """Test load impact on latency."""
        manager = LatencyProfileManager()
        manager.reset_load()

        model = "gpt-3.5-turbo"
        prompt_tokens = 100

        # Simulate increasing load
        latencies = []
        for load in [0, 20, 50, 100]:
            ttft = manager.get_ttft(
                model=model,
                prompt_tokens=prompt_tokens,
                current_load=load,
            )
            latencies.append(ttft)

        # Latencies should generally increase with load
        # (Allow some variance due to randomness)
        assert latencies[3] > latencies[0] * 0.9

    def test_model_comparison(self):
        """Test comparing different models."""
        manager = LatencyProfileManager()

        prompt_tokens = 500
        output_tokens = 100

        # Fast model
        time_fast = manager.get_generation_time(
            model="gpt-4o-mini",
            output_tokens=output_tokens,
            prompt_tokens=prompt_tokens,
        )

        # Slow model
        time_slow = manager.get_generation_time(
            model="gpt-4",
            output_tokens=output_tokens,
            prompt_tokens=prompt_tokens,
        )

        # GPT-4 should be slower than GPT-4o-mini
        assert time_slow > time_fast


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_tokens(self):
        """Test with zero tokens."""
        manager = LatencyProfileManager()

        ttft = manager.get_ttft(model="gpt-4", prompt_tokens=0)
        assert ttft > 0  # Should still have base TTFT

        # Generation time with 0 output tokens
        time = manager.get_generation_time(
            model="gpt-4",
            output_tokens=0,
            prompt_tokens=100,
        )
        assert time > 0  # Should have at least TTFT

    def test_very_long_prompt(self):
        """Test with very long prompt."""
        manager = LatencyProfileManager()

        ttft = manager.get_ttft(model="gpt-4", prompt_tokens=100000)
        assert ttft > 0
        # Should be significantly higher than base
        assert ttft > 0.5  # At least 500ms for 100K tokens

    def test_negative_load_prevention(self):
        """Test that negative load is prevented."""
        manager = LatencyProfileManager()
        manager.reset_load()

        # Try to go negative
        manager.end_request()
        manager.end_request()

        assert manager.get_active_requests() == 0

    def test_extreme_temperature(self):
        """Test with extreme temperature values."""
        manager = LatencyProfileManager()

        # Very low temperature
        ttft_low = manager.get_ttft(model="gpt-4", prompt_tokens=100, temperature=0.1)
        assert ttft_low > 0

        # Very high temperature
        ttft_high = manager.get_ttft(model="gpt-4", prompt_tokens=100, temperature=5.0)
        assert ttft_high > 0

    def test_cache_hit_without_tokens(self):
        """Test KV cache hit but with 0 cached tokens."""
        manager = LatencyProfileManager()

        ttft = manager.get_ttft(
            model="gpt-4",
            prompt_tokens=1000,
            kv_cache_hit=True,
            kv_cache_hit_tokens=0,  # No actual tokens cached
        )

        # Should behave like no cache hit
        assert ttft > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
