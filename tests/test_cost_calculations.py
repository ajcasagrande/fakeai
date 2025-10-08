#!/usr/bin/env python3
"""
Comprehensive tests for cost calculations with various pricing models.

This test suite validates:
1. Model pricing accuracy for all supported models
2. Token cost calculations with high precision
3. Cached token discounts
4. Edge cases (0 tokens, 1 token, very large usage)
5. Fine-tuned model pricing
6. Image and audio pricing
"""
#  SPDX-License-Identifier: Apache-2.0

import importlib.util
import sys
from pathlib import Path

import pytest

# Import cost_tracker directly to avoid triggering app initialization via __init__.py
cost_tracker_path = Path(__file__).parent.parent / "fakeai" / "cost_tracker.py"
spec = importlib.util.spec_from_file_location("cost_tracker", cost_tracker_path)
cost_tracker_module = importlib.util.module_from_spec(spec)
sys.modules["cost_tracker"] = cost_tracker_module
spec.loader.exec_module(cost_tracker_module)

AUDIO_PRICING = cost_tracker_module.AUDIO_PRICING
FINE_TUNING_PRICING = cost_tracker_module.FINE_TUNING_PRICING
IMAGE_PRICING = cost_tracker_module.IMAGE_PRICING
MODEL_PRICING = cost_tracker_module.MODEL_PRICING
CostTracker = cost_tracker_module.CostTracker


@pytest.fixture
def cost_tracker():
    """Create a fresh cost tracker instance for testing."""
    tracker = CostTracker()
    tracker.clear_history()
    return tracker


class TestModelPricingAccuracy:
    """Test that model pricing matches OpenAI's published rates."""

    def test_gpt4_pricing(self, cost_tracker):
        """Test GPT-4 pricing: $30 input, $60 output per 1M tokens."""
        api_key = "test-gpt4-pricing"
        model = "gpt-4"

        # Test with 1M tokens
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
        )

        # Expected: $30 input + $60 output = $90
        expected_cost = 30.00 + 60.00
        assert abs(cost - expected_cost) < 0.000001, f"Expected ${expected_cost}, got ${cost}"

    def test_gpt4o_pricing(self, cost_tracker):
        """Test GPT-4o pricing: $5 input, $15 output, $2.50 cached per 1M tokens."""
        api_key = "test-gpt4o-pricing"
        model = "gpt-4o"

        # Test with 1M tokens (no cache)
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
            cached_tokens=0,
        )

        # Expected: $5 input + $15 output = $20
        expected_cost = 5.00 + 15.00
        assert abs(cost - expected_cost) < 0.000001, f"Expected ${expected_cost}, got ${cost}"

    def test_gpt4o_mini_pricing(self, cost_tracker):
        """Test GPT-4o-mini pricing: $0.15 input, $0.60 output per 1M tokens."""
        api_key = "test-gpt4o-mini-pricing"
        model = "gpt-4o-mini"

        # Test with 1M tokens
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
        )

        # Expected: $0.15 input + $0.60 output = $0.75
        expected_cost = 0.15 + 0.60
        assert abs(cost - expected_cost) < 0.000001, f"Expected ${expected_cost}, got ${cost}"

    def test_o1_pricing(self, cost_tracker):
        """Test O1 pricing: $15 input, $60 output per 1M tokens."""
        api_key = "test-o1-pricing"
        model = "o1"

        # Test with 1M tokens
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
        )

        # Expected: $15 input + $60 output = $75
        expected_cost = 15.00 + 60.00
        assert abs(cost - expected_cost) < 0.000001, f"Expected ${expected_cost}, got ${cost}"

    def test_gpt35_turbo_pricing(self, cost_tracker):
        """Test GPT-3.5-turbo pricing: $0.50 input, $1.50 output per 1M tokens."""
        api_key = "test-gpt35-pricing"
        model = "gpt-3.5-turbo"

        # Test with 1M tokens
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
        )

        # Expected: $0.50 input + $1.50 output = $2.00
        expected_cost = 0.50 + 1.50
        assert abs(cost - expected_cost) < 0.000001, f"Expected ${expected_cost}, got ${cost}"

    def test_all_models_have_pricing(self):
        """Verify all models in MODEL_PRICING have valid pricing data."""
        for model_id, pricing in MODEL_PRICING.items():
            assert pricing.input_price_per_million >= 0, f"{model_id} has invalid input price"
            assert pricing.output_price_per_million >= 0, f"{model_id} has invalid output price"
            assert pricing.model_id == model_id, f"{model_id} has mismatched model_id"


class TestTokenCostCalculation:
    """Test token cost calculations with different token counts."""

    def test_1m_tokens_equals_base_price(self, cost_tracker):
        """Test that 1M tokens costs exactly the base price."""
        api_key = "test-1m-tokens"
        model = "gpt-4o"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1_000_000,
            completion_tokens=0,
        )

        expected_cost = 5.00  # $5 per 1M input tokens
        assert abs(cost - expected_cost) < 0.000001

    def test_100k_tokens_equals_base_price_div_10(self, cost_tracker):
        """Test that 100K tokens costs base price / 10."""
        api_key = "test-100k-tokens"
        model = "gpt-4o"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=100_000,
            completion_tokens=0,
        )

        expected_cost = 5.00 / 10  # $0.50
        assert abs(cost - expected_cost) < 0.000001

    def test_1k_tokens_equals_base_price_div_1000(self, cost_tracker):
        """Test that 1K tokens costs base price / 1000."""
        api_key = "test-1k-tokens"
        model = "gpt-4o"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1_000,
            completion_tokens=0,
        )

        expected_cost = 5.00 / 1000  # $0.005
        assert abs(cost - expected_cost) < 0.000001

    def test_precision_to_6_decimal_places(self, cost_tracker):
        """Test that cost calculations maintain 6+ decimal place precision."""
        api_key = "test-precision"
        model = "gpt-4o-mini"

        # Use a small number of tokens that will result in a very small cost
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1,
            completion_tokens=1,
        )

        # Expected: (1 * 0.15 + 1 * 0.60) / 1M = 0.00000075
        expected_cost = (1 * 0.15 + 1 * 0.60) / 1_000_000
        assert abs(cost - expected_cost) < 0.0000000001  # 10 decimal place precision

    def test_mixed_input_output_tokens(self, cost_tracker):
        """Test cost calculation with different input/output token counts."""
        api_key = "test-mixed-tokens"
        model = "gpt-4"

        # 500K input, 250K output
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=500_000,
            completion_tokens=250_000,
        )

        # Expected: (500K * $30 + 250K * $60) / 1M = $15 + $15 = $30
        expected_cost = (500_000 * 30.00 + 250_000 * 60.00) / 1_000_000
        assert abs(cost - expected_cost) < 0.000001

    def test_asymmetric_token_counts(self, cost_tracker):
        """Test with very different input vs output token counts."""
        api_key = "test-asymmetric"
        model = "gpt-4o"

        # Large input, small output
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=10_000,
            completion_tokens=100,
        )

        # Expected: (10000 * 5.00 + 100 * 15.00) / 1M
        expected_cost = (10_000 * 5.00 + 100 * 15.00) / 1_000_000
        assert abs(cost - expected_cost) < 0.000001


class TestCachedTokenDiscount:
    """Test cached token pricing (50% discount)."""

    def test_cached_tokens_cost_50_percent(self, cost_tracker):
        """Test that cached tokens cost 50% of regular input tokens."""
        api_key = "test-cached-50"
        model = "gpt-4o"

        # Test with 1M cached tokens
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1_000_000,
            completion_tokens=0,
            cached_tokens=1_000_000,
        )

        # Expected: cached cost only = 1M * $2.50 = $2.50
        # (all prompt tokens are cached, so no regular input cost)
        expected_cost = 1_000_000 * 2.50 / 1_000_000
        assert abs(cost - expected_cost) < 0.000001

    def test_cached_subtracted_from_input_count(self, cost_tracker):
        """Test that cached tokens are subtracted from input count."""
        api_key = "test-cached-subtraction"
        model = "gpt-4o"

        # 1M total prompt tokens, 500K cached
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1_000_000,
            completion_tokens=0,
            cached_tokens=500_000,
        )

        # Expected: 500K regular * $5 + 500K cached * $2.50 = $2.50 + $1.25 = $3.75
        regular_cost = 500_000 * 5.00 / 1_000_000
        cached_cost = 500_000 * 2.50 / 1_000_000
        expected_cost = regular_cost + cached_cost
        assert abs(cost - expected_cost) < 0.000001

    def test_cached_added_as_separate_cost(self, cost_tracker):
        """Test that cached tokens add a separate cached cost component."""
        api_key = "test-cached-separate"
        model = "gpt-4o"

        # Record usage with cache
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1_000_000,
            completion_tokens=500_000,
            cached_tokens=400_000,
        )

        # Expected:
        # - Regular input: 600K * $5 = $3.00
        # - Cached input: 400K * $2.50 = $1.00
        # - Output: 500K * $15 = $7.50
        # Total: $11.50
        regular_input = 600_000 * 5.00 / 1_000_000
        cached_input = 400_000 * 2.50 / 1_000_000
        output = 500_000 * 15.00 / 1_000_000
        expected_cost = regular_input + cached_input + output
        assert abs(cost - expected_cost) < 0.000001

    def test_gpt4o_mini_cached_pricing(self, cost_tracker):
        """Test cached pricing for GPT-4o-mini (50% of $0.15 = $0.075)."""
        api_key = "test-mini-cached"
        model = "gpt-4o-mini"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1_000_000,
            completion_tokens=0,
            cached_tokens=1_000_000,
        )

        # Expected: 1M * $0.075 = $0.075
        expected_cost = 0.075
        assert abs(cost - expected_cost) < 0.000001

    def test_no_cache_for_models_without_cache_pricing(self, cost_tracker):
        """Test that models without cache pricing ignore cached_tokens."""
        api_key = "test-no-cache-support"
        model = "gpt-4"  # No cache pricing

        # Try to use cached tokens (should be ignored)
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1_000_000,
            completion_tokens=0,
            cached_tokens=500_000,
        )

        # Expected: full input cost (cache ignored) = 1M * $30 = $30
        expected_cost = 30.00
        assert abs(cost - expected_cost) < 0.000001


class TestEdgeCases:
    """Test edge cases in cost calculations."""

    def test_zero_tokens_equals_zero_cost(self, cost_tracker):
        """Test that 0 tokens results in $0.00 cost."""
        api_key = "test-zero-tokens"
        model = "gpt-4o"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=0,
            completion_tokens=0,
        )

        assert cost == 0.0

    def test_very_small_usage_1_token(self, cost_tracker):
        """Test cost calculation with minimal usage (1 token)."""
        api_key = "test-1-token"
        model = "gpt-4o"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1,
            completion_tokens=0,
        )

        # Expected: 1 * $5 / 1M = $0.000005
        expected_cost = 1 * 5.00 / 1_000_000
        assert abs(cost - expected_cost) < 0.0000000001

    def test_very_large_usage_10m_tokens(self, cost_tracker):
        """Test cost calculation with very large usage (10M tokens)."""
        api_key = "test-10m-tokens"
        model = "gpt-4o"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=10_000_000,
            completion_tokens=10_000_000,
        )

        # Expected: 10M * $5 + 10M * $15 = $50 + $150 = $200
        expected_cost = 50.00 + 150.00
        assert abs(cost - expected_cost) < 0.000001

    def test_unknown_model_falls_back_to_default(self, cost_tracker):
        """Test that unknown models fall back to GPT-3.5-turbo pricing."""
        api_key = "test-unknown-model"
        model = "totally-unknown-model-xyz-123"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=100_000,
            completion_tokens=50_000,
        )

        # Expected: GPT-3.5-turbo pricing
        # (100K * $0.50 + 50K * $1.50) / 1M = $0.05 + $0.075 = $0.125
        expected_cost = (100_000 * 0.50 + 50_000 * 1.50) / 1_000_000
        assert abs(cost - expected_cost) < 0.000001

    def test_only_input_tokens(self, cost_tracker):
        """Test cost with only input tokens (e.g., embeddings)."""
        api_key = "test-input-only"
        model = "text-embedding-3-small"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/embeddings",
            prompt_tokens=10_000,
            completion_tokens=0,
        )

        # Expected: 10K * $0.02 / 1M = $0.0002
        expected_cost = 10_000 * 0.02 / 1_000_000
        assert abs(cost - expected_cost) < 0.000001

    def test_only_output_tokens(self, cost_tracker):
        """Test cost with only output tokens (unusual but valid)."""
        api_key = "test-output-only"
        model = "gpt-4o"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=0,
            completion_tokens=10_000,
        )

        # Expected: 10K * $15 / 1M = $0.15
        expected_cost = 10_000 * 15.00 / 1_000_000
        assert abs(cost - expected_cost) < 0.000001


class TestFineTunedModels:
    """Test fine-tuned model pricing."""

    def test_fine_tuned_gpt4o_format(self, cost_tracker):
        """Test fine-tuned model format: ft:gpt-4o-2024-08-06:org::id."""
        api_key = "test-ft-format"
        model = "ft:gpt-4o-2024-08-06:my-org::abc123xyz"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
        )

        # Expected: fine-tuned pricing (input: $3.75, output: $15.00)
        expected_cost = 3.75 + 15.00
        assert abs(cost - expected_cost) < 0.000001

    def test_fine_tuned_uses_base_model_pricing(self, cost_tracker):
        """Test that fine-tuned models use their base model's pricing."""
        api_key = "test-ft-base-pricing"
        model = "ft:gpt-4o-mini-2024-07-18:acme::xyz789"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
        )

        # Expected: fine-tuned mini pricing (input: $0.30, output: $1.20)
        expected_cost = 0.30 + 1.20
        assert abs(cost - expected_cost) < 0.000001

    def test_fine_tuned_gpt35_turbo(self, cost_tracker):
        """Test fine-tuned GPT-3.5-turbo pricing."""
        api_key = "test-ft-gpt35"
        model = "ft:gpt-3.5-turbo:company::model123"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
        )

        # Expected: fine-tuned 3.5 pricing (input: $3.00, output: $6.00)
        expected_cost = 3.00 + 6.00
        assert abs(cost - expected_cost) < 0.000001

    def test_training_cost_vs_inference_cost(self):
        """Test that training costs are different from inference costs."""
        # Training costs (per 1M tokens)
        gpt4o_training = FINE_TUNING_PRICING["gpt-4o-2024-08-06"]["training"]
        gpt4o_input = FINE_TUNING_PRICING["gpt-4o-2024-08-06"]["input"]

        # Training should be more expensive than inference input
        assert gpt4o_training > gpt4o_input
        assert gpt4o_training == 25.00
        assert gpt4o_input == 3.75

    def test_fine_tuned_with_org_name_variations(self, cost_tracker):
        """Test fine-tuned models with various organization name formats."""
        api_key = "test-ft-variations"

        # Test with hyphenated org name
        model1 = "ft:gpt-4o-2024-08-06:my-company-name::id1"
        cost1 = cost_tracker.record_usage(
            api_key=api_key,
            model=model1,
            endpoint="/v1/chat/completions",
            prompt_tokens=100_000,
            completion_tokens=100_000,
        )

        # Test with underscore org name
        model2 = "ft:gpt-4o-2024-08-06:my_company_name::id2"
        cost2 = cost_tracker.record_usage(
            api_key=api_key,
            model=model2,
            endpoint="/v1/chat/completions",
            prompt_tokens=100_000,
            completion_tokens=100_000,
        )

        # Both should have same cost (same base model)
        assert abs(cost1 - cost2) < 0.000001


class TestImagePricing:
    """Test image generation pricing."""

    def test_dalle3_1024x1024_standard(self, cost_tracker):
        """Test DALL-E 3 standard quality 1024x1024 pricing."""
        api_key = "test-dalle3-std"
        model = "dall-e-3"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/images/generations",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "1024x1024", "quality": "standard", "n": 1},
        )

        expected_cost = 0.040
        assert abs(cost - expected_cost) < 0.000001

    def test_dalle3_1024x1024_hd(self, cost_tracker):
        """Test DALL-E 3 HD quality 1024x1024 pricing."""
        api_key = "test-dalle3-hd"
        model = "dall-e-3"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/images/generations",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "1024x1024", "quality": "hd", "n": 1},
        )

        expected_cost = 0.080
        assert abs(cost - expected_cost) < 0.000001

    def test_dalle3_1024x1792_standard(self, cost_tracker):
        """Test DALL-E 3 standard quality 1024x1792 pricing."""
        api_key = "test-dalle3-wide-std"
        model = "dall-e-3"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/images/generations",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "1024x1792", "quality": "standard", "n": 1},
        )

        expected_cost = 0.080
        assert abs(cost - expected_cost) < 0.000001

    def test_dalle3_1024x1792_hd(self, cost_tracker):
        """Test DALL-E 3 HD quality 1024x1792 pricing."""
        api_key = "test-dalle3-wide-hd"
        model = "dall-e-3"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/images/generations",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "1024x1792", "quality": "hd", "n": 1},
        )

        expected_cost = 0.120
        assert abs(cost - expected_cost) < 0.000001

    def test_dalle3_1792x1024_standard(self, cost_tracker):
        """Test DALL-E 3 standard quality 1792x1024 pricing."""
        api_key = "test-dalle3-tall-std"
        model = "dall-e-3"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/images/generations",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "1792x1024", "quality": "standard", "n": 1},
        )

        expected_cost = 0.080
        assert abs(cost - expected_cost) < 0.000001

    def test_dalle3_1792x1024_hd(self, cost_tracker):
        """Test DALL-E 3 HD quality 1792x1024 pricing."""
        api_key = "test-dalle3-tall-hd"
        model = "dall-e-3"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/images/generations",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "1792x1024", "quality": "hd", "n": 1},
        )

        expected_cost = 0.120
        assert abs(cost - expected_cost) < 0.000001

    def test_dalle3_multiple_images(self, cost_tracker):
        """Test DALL-E 3 pricing with multiple images (n parameter)."""
        api_key = "test-dalle3-multiple"
        model = "dall-e-3"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/images/generations",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "1024x1024", "quality": "standard", "n": 3},
        )

        # Expected: 3 images * $0.040 = $0.120
        expected_cost = 0.040 * 3
        assert abs(cost - expected_cost) < 0.000001

    def test_dalle2_1024x1024(self, cost_tracker):
        """Test DALL-E 2 1024x1024 pricing."""
        api_key = "test-dalle2-1024"
        model = "dall-e-2"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/images/generations",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "1024x1024", "quality": "standard", "n": 1},
        )

        expected_cost = 0.020
        assert abs(cost - expected_cost) < 0.000001

    def test_dalle2_512x512(self, cost_tracker):
        """Test DALL-E 2 512x512 pricing."""
        api_key = "test-dalle2-512"
        model = "dall-e-2"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/images/generations",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "512x512", "quality": "standard", "n": 1},
        )

        expected_cost = 0.018
        assert abs(cost - expected_cost) < 0.000001

    def test_dalle2_256x256(self, cost_tracker):
        """Test DALL-E 2 256x256 pricing."""
        api_key = "test-dalle2-256"
        model = "dall-e-2"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/images/generations",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "256x256", "quality": "standard", "n": 1},
        )

        expected_cost = 0.016
        assert abs(cost - expected_cost) < 0.000001


class TestAudioPricing:
    """Test audio pricing (TTS and Whisper)."""

    def test_tts1_character_pricing(self, cost_tracker):
        """Test TTS-1 pricing by character count: $15 per 1M chars."""
        api_key = "test-tts1"
        model = "tts-1"

        # 1M characters
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/audio/speech",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"characters": 1_000_000},
        )

        expected_cost = 15.00
        assert abs(cost - expected_cost) < 0.000001

    def test_tts1_hd_character_pricing(self, cost_tracker):
        """Test TTS-1-HD pricing: $30 per 1M chars."""
        api_key = "test-tts1-hd"
        model = "tts-1-hd"

        # 1M characters
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/audio/speech",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"characters": 1_000_000},
        )

        expected_cost = 30.00
        assert abs(cost - expected_cost) < 0.000001

    def test_tts_small_character_count(self, cost_tracker):
        """Test TTS pricing with small character count (typical usage)."""
        api_key = "test-tts-small"
        model = "tts-1"

        # 1000 characters (about 150-200 words)
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/audio/speech",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"characters": 1000},
        )

        # Expected: 1000 * $15 / 1M = $0.015
        expected_cost = 1000 * 15.00 / 1_000_000
        assert abs(cost - expected_cost) < 0.000001

    def test_whisper_character_pricing(self, cost_tracker):
        """Test Whisper pricing: $6 per 1M chars (derived from audio length)."""
        api_key = "test-whisper"
        model = "whisper-1"

        # 1M characters worth of audio transcription
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/audio/transcriptions",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"characters": 1_000_000},
        )

        expected_cost = 6.00
        assert abs(cost - expected_cost) < 0.000001

    def test_tts_zero_characters(self, cost_tracker):
        """Test TTS with zero characters."""
        api_key = "test-tts-zero"
        model = "tts-1"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/audio/speech",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"characters": 0},
        )

        assert cost == 0.0

    def test_tts_vs_tts_hd_cost_ratio(self, cost_tracker):
        """Test that TTS-1-HD costs exactly 2x TTS-1."""
        api_key = "test-tts-ratio"

        # TTS-1
        cost_standard = cost_tracker.record_usage(
            api_key=f"{api_key}-std",
            model="tts-1",
            endpoint="/v1/audio/speech",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"characters": 10_000},
        )

        # TTS-1-HD
        cost_hd = cost_tracker.record_usage(
            api_key=f"{api_key}-hd",
            model="tts-1-hd",
            endpoint="/v1/audio/speech",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"characters": 10_000},
        )

        # HD should be exactly 2x standard
        assert abs(cost_hd - (cost_standard * 2)) < 0.000001


class TestComplexScenarios:
    """Test complex real-world scenarios combining multiple features."""

    def test_full_conversation_with_cache(self, cost_tracker):
        """Test a complete conversation with prompt caching."""
        api_key = "test-conversation"
        model = "gpt-4o"

        # First message: no cache
        cost1 = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=500,
            cached_tokens=0,
        )

        # Second message: 800 tokens cached from system prompt
        cost2 = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1200,
            completion_tokens=600,
            cached_tokens=800,
        )

        # Verify costs
        expected_cost1 = (1000 * 5.00 + 500 * 15.00) / 1_000_000
        expected_cost2 = (
            (1200 - 800) * 5.00 + 800 * 2.50 + 600 * 15.00
        ) / 1_000_000

        assert abs(cost1 - expected_cost1) < 0.000001
        assert abs(cost2 - expected_cost2) < 0.000001

        # Total cost
        total = cost_tracker.get_cost_by_key(api_key)["total_cost"]
        expected_total = expected_cost1 + expected_cost2
        assert abs(total - expected_total) < 0.000001

    def test_multimodal_workflow(self, cost_tracker):
        """Test a workflow combining chat, image generation, and TTS."""
        api_key = "test-multimodal"

        # Chat completion
        cost_chat = cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            prompt_tokens=5000,
            completion_tokens=2000,
        )

        # Image generation
        cost_image = cost_tracker.record_usage(
            api_key=api_key,
            model="dall-e-3",
            endpoint="/v1/images/generations",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "1024x1024", "quality": "hd", "n": 1},
        )

        # Text-to-speech
        cost_tts = cost_tracker.record_usage(
            api_key=api_key,
            model="tts-1",
            endpoint="/v1/audio/speech",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"characters": 2000},
        )

        # Verify individual costs
        expected_chat = (5000 * 5.00 + 2000 * 15.00) / 1_000_000
        expected_image = 0.080
        expected_tts = 2000 * 15.00 / 1_000_000

        assert abs(cost_chat - expected_chat) < 0.000001
        assert abs(cost_image - expected_image) < 0.000001
        assert abs(cost_tts - expected_tts) < 0.000001

        # Verify total
        total = cost_tracker.get_cost_by_key(api_key)["total_cost"]
        expected_total = expected_chat + expected_image + expected_tts
        assert abs(total - expected_total) < 0.000001

    def test_mixed_models_cost_comparison(self, cost_tracker):
        """Test cost comparison between different model tiers."""
        api_key = "test-comparison"
        prompt_tokens = 10_000
        completion_tokens = 5_000

        # GPT-4
        cost_gpt4 = cost_tracker.record_usage(
            api_key=f"{api_key}-gpt4",
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        # GPT-4o
        cost_gpt4o = cost_tracker.record_usage(
            api_key=f"{api_key}-gpt4o",
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        # GPT-4o-mini
        cost_mini = cost_tracker.record_usage(
            api_key=f"{api_key}-mini",
            model="gpt-4o-mini",
            endpoint="/v1/chat/completions",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        # GPT-3.5-turbo
        cost_gpt35 = cost_tracker.record_usage(
            api_key=f"{api_key}-gpt35",
            model="gpt-3.5-turbo",
            endpoint="/v1/chat/completions",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        # Verify cost ordering: GPT-4 > GPT-4o > GPT-3.5 > GPT-4o-mini
        assert cost_gpt4 > cost_gpt4o
        assert cost_gpt4o > cost_gpt35
        assert cost_gpt35 > cost_mini

    def test_batch_processing_vs_regular(self, cost_tracker):
        """Test cost difference between batch and regular processing."""
        api_key = "test-batch-vs-regular"
        model = "gpt-4o"

        # Regular processing
        cost_regular = cost_tracker.record_usage(
            api_key=f"{api_key}-regular",
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=100_000,
            completion_tokens=50_000,
        )

        # Batch processing (tracked separately for metrics)
        cost_batch = cost_tracker.record_usage(
            api_key=f"{api_key}-batch",
            model=model,
            endpoint="/v1/batches",
            prompt_tokens=100_000,
            completion_tokens=50_000,
        )

        # Note: The cost calculation itself is the same, but batch savings
        # are calculated separately via get_batch_savings()
        # Both should have same base cost
        assert abs(cost_regular - cost_batch) < 0.000001

    def test_embedding_cost_at_scale(self, cost_tracker):
        """Test embedding costs at scale (typical RAG pipeline)."""
        api_key = "test-embeddings-scale"
        model = "text-embedding-3-small"

        # Process 100 documents, 1000 tokens each
        total_cost = 0
        for i in range(100):
            cost = cost_tracker.record_usage(
                api_key=api_key,
                model=model,
                endpoint="/v1/embeddings",
                prompt_tokens=1000,
                completion_tokens=0,
            )
            total_cost += cost

        # Expected: 100K tokens * $0.02 / 1M = $0.002
        expected_cost = 100_000 * 0.02 / 1_000_000
        assert abs(total_cost - expected_cost) < 0.000001

        # Verify request count
        result = cost_tracker.get_cost_by_key(api_key)
        assert result["requests"] == 100


class TestPricingConsistency:
    """Test consistency and relationships in pricing."""

    def test_output_always_more_expensive_than_input(self):
        """Test that output tokens are always priced >= input tokens (for chat models)."""
        for model_id, pricing in MODEL_PRICING.items():
            # Skip embedding models which don't have output tokens
            if "embedding" in model_id:
                continue
            assert pricing.output_price_per_million >= pricing.input_price_per_million, \
                f"{model_id} has cheaper output than input"

    def test_cached_always_cheaper_than_input(self):
        """Test that cached tokens are always cheaper than regular input."""
        for model_id, pricing in MODEL_PRICING.items():
            if pricing.cached_input_price_per_million is not None:
                assert pricing.cached_input_price_per_million < pricing.input_price_per_million, \
                    f"{model_id} cached price not cheaper than input"

    def test_cached_approximately_50_percent_discount(self):
        """Test that cached tokens are approximately 50% of input cost."""
        for model_id, pricing in MODEL_PRICING.items():
            if pricing.cached_input_price_per_million is not None:
                expected_cached = pricing.input_price_per_million * 0.5
                # Allow small tolerance for rounding
                assert abs(pricing.cached_input_price_per_million - expected_cached) < 0.01, \
                    f"{model_id} cached price not ~50% of input"

    def test_model_family_pricing_relationships(self):
        """Test pricing relationships within model families."""
        # GPT-4o should be cheaper than GPT-4
        assert MODEL_PRICING["gpt-4o"].input_price_per_million < \
               MODEL_PRICING["gpt-4"].input_price_per_million

        # GPT-4o-mini should be cheaper than GPT-4o
        assert MODEL_PRICING["gpt-4o-mini"].input_price_per_million < \
               MODEL_PRICING["gpt-4o"].input_price_per_million

        # O1-mini should be cheaper than O1
        assert MODEL_PRICING["o1-mini"].input_price_per_million < \
               MODEL_PRICING["o1"].input_price_per_million

    def test_hd_images_more_expensive_than_standard(self):
        """Test that HD images cost more than standard quality."""
        for standard in IMAGE_PRICING:
            if standard.quality == "standard":
                # Find corresponding HD version
                hd_versions = [
                    p for p in IMAGE_PRICING
                    if p.model == standard.model
                    and p.size == standard.size
                    and p.quality == "hd"
                ]
                if hd_versions:
                    assert hd_versions[0].price > standard.price, \
                        f"{standard.model} {standard.size} HD not more expensive"

    def test_larger_images_more_expensive(self):
        """Test that larger images cost more (for DALL-E 3)."""
        dalle3_std = [p for p in IMAGE_PRICING if p.model == "dall-e-3" and p.quality == "standard"]

        size_1024 = next(p for p in dalle3_std if p.size == "1024x1024")
        size_wide = next(p for p in dalle3_std if p.size == "1024x1792")

        assert size_wide.price > size_1024.price, "Larger size not more expensive"
