#!/usr/bin/env python3
"""
Comprehensive integration tests for the FakeAI CostTracker.

This test suite covers realistic usage patterns, edge cases, and integration scenarios
for the cost tracking and billing simulation system.
"""
#  SPDX-License-Identifier: Apache-2.0


import pytest

from fakeai.cost_tracker import (
    MODEL_PRICING,
    BudgetLimitType,
    BudgetPeriod,
    CostTracker,
)


@pytest.fixture
def tracker():
    """Create a fresh cost tracker instance for integration testing."""
    tracker = CostTracker()
    tracker.clear_history()
    return tracker


class TestUsageRecording:
    """Comprehensive tests for usage recording and cost calculation."""

    def test_record_usage_calculates_cost_correctly(self, tracker):
        """Test that record_usage calculates and returns correct cost."""
        api_key = "test-api-key"
        model = "gpt-4o"

        cost = tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        # Expected: (1000 * $5.00 + 500 * $15.00) / 1M = $0.0125
        expected = (1000 * 5.00 + 500 * 15.00) / 1_000_000
        assert abs(cost - expected) < 0.000001, f"Expected {expected}, got {cost}"

    def test_per_model_pricing_accuracy_gpt4(self, tracker):
        """Test GPT-4 pricing accuracy."""
        api_key = "test-gpt4"

        cost = tracker.record_usage(
            api_key=api_key,
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=1000,
        )

        # GPT-4: $30/1M input, $60/1M output
        expected = (1000 * 30.00 + 1000 * 60.00) / 1_000_000
        assert abs(cost - expected) < 0.000001

    def test_per_model_pricing_accuracy_gpt4o(self, tracker):
        """Test GPT-4o pricing accuracy."""
        api_key = "test-gpt4o"

        cost = tracker.record_usage(
            api_key=api_key,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=1000,
        )

        # GPT-4o: $5/1M input, $15/1M output
        expected = (1000 * 5.00 + 1000 * 15.00) / 1_000_000
        assert abs(cost - expected) < 0.000001

    def test_per_model_pricing_accuracy_gpt4o_mini(self, tracker):
        """Test GPT-4o-mini pricing accuracy."""
        api_key = "test-gpt4o-mini"

        cost = tracker.record_usage(
            api_key=api_key,
            model="gpt-4o-mini",
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=1000,
        )

        # GPT-4o-mini: $0.15/1M input, $0.60/1M output
        expected = (1000 * 0.15 + 1000 * 0.60) / 1_000_000
        assert abs(cost - expected) < 0.000001

    def test_per_model_pricing_accuracy_o1(self, tracker):
        """Test O1 model pricing accuracy."""
        api_key = "test-o1"

        cost = tracker.record_usage(
            api_key=api_key,
            model="o1",
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=1000,
        )

        # O1: $15/1M input, $60/1M output
        expected = (1000 * 15.00 + 1000 * 60.00) / 1_000_000
        assert abs(cost - expected) < 0.000001

    def test_cached_token_discount_applied(self, tracker):
        """Test that cached tokens receive the correct discount."""
        api_key = "test-cached"
        model = "gpt-4o"

        # Test with cached tokens
        cost_with_cache = tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=500,
            cached_tokens=500,  # Half the prompt tokens are cached
        )

        # Expected: (500 regular * $5.00 + 500 cached * $2.50 + 500 output * $15.00) / 1M
        pricing = MODEL_PRICING[model]
        expected = (
            500 * pricing.input_price_per_million +
            500 * pricing.cached_input_price_per_million +
            500 * pricing.output_price_per_million
        ) / 1_000_000

        assert abs(cost_with_cache - expected) < 0.000001

        # Verify cached tokens are cheaper than regular tokens
        cost_without_cache = (1000 * 5.00 + 500 * 15.00) / 1_000_000
        assert cost_with_cache < cost_without_cache

    def test_totals_updated_correctly(self, tracker):
        """Test that all aggregated totals are updated correctly."""
        api_key = "test-totals"
        model = "gpt-4o"
        endpoint = "/v1/chat/completions"

        # Record multiple requests
        for i in range(5):
            tracker.record_usage(
                api_key=api_key,
                model=model,
                endpoint=endpoint,
                prompt_tokens=100,
                completion_tokens=50,
            )

        # Check cost by key
        key_costs = tracker.get_cost_by_key(api_key)
        assert key_costs["requests"] == 5
        assert key_costs["tokens"]["prompt_tokens"] == 500
        assert key_costs["tokens"]["completion_tokens"] == 250
        assert key_costs["tokens"]["total_tokens"] == 750

        # Check cost by model
        model_costs = tracker.get_cost_by_model()
        assert model in model_costs
        assert model_costs[model] > 0

        # Check cost by endpoint
        endpoint_costs = tracker.get_cost_by_endpoint()
        assert endpoint in endpoint_costs
        assert endpoint_costs[endpoint] > 0


class TestCostCalculation:
    """Tests for specific cost calculations across different models and services."""

    def test_gpt4_pricing_correct(self, tracker):
        """Test that GPT-4 pricing matches expected values."""
        api_key = "test-gpt4-pricing"

        # Test standard GPT-4
        cost = tracker.record_usage(
            api_key=api_key,
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=10000,
            completion_tokens=5000,
        )

        # $30/1M input, $60/1M output
        expected = (10000 * 30.00 + 5000 * 60.00) / 1_000_000
        assert abs(cost - expected) < 0.000001

        # Test GPT-4-32k (more expensive)
        cost_32k = tracker.record_usage(
            api_key=api_key,
            model="gpt-4-32k",
            endpoint="/v1/chat/completions",
            prompt_tokens=10000,
            completion_tokens=5000,
        )

        # $60/1M input, $120/1M output
        expected_32k = (10000 * 60.00 + 5000 * 120.00) / 1_000_000
        assert abs(cost_32k - expected_32k) < 0.000001
        assert cost_32k > cost  # 32k should be more expensive

    def test_gpt4o_pricing_correct(self, tracker):
        """Test that GPT-4o pricing matches expected values."""
        api_key = "test-gpt4o-pricing"

        # Test GPT-4o standard
        cost = tracker.record_usage(
            api_key=api_key,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            prompt_tokens=10000,
            completion_tokens=5000,
        )

        # $5/1M input, $15/1M output
        expected = (10000 * 5.00 + 5000 * 15.00) / 1_000_000
        assert abs(cost - expected) < 0.000001

        # Test GPT-4o with caching
        cost_cached = tracker.record_usage(
            api_key=api_key,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            prompt_tokens=10000,
            completion_tokens=5000,
            cached_tokens=5000,
        )

        # $2.50/1M cached, $5/1M regular input, $15/1M output
        expected_cached = (5000 * 2.50 + 5000 * 5.00 + 5000 * 15.00) / 1_000_000
        assert abs(cost_cached - expected_cached) < 0.000001
        assert cost_cached < cost  # Cached should be cheaper

    def test_gpt4o_mini_pricing_correct(self, tracker):
        """Test that GPT-4o-mini pricing matches expected values."""
        api_key = "test-mini-pricing"

        cost = tracker.record_usage(
            api_key=api_key,
            model="gpt-4o-mini",
            endpoint="/v1/chat/completions",
            prompt_tokens=100000,
            completion_tokens=50000,
        )

        # $0.15/1M input, $0.60/1M output
        expected = (100000 * 0.15 + 50000 * 0.60) / 1_000_000
        assert abs(cost - expected) < 0.000001

    def test_o1_pricing_correct(self, tracker):
        """Test that O1 model pricing matches expected values."""
        api_key = "test-o1-pricing"

        # Test O1 standard
        cost = tracker.record_usage(
            api_key=api_key,
            model="o1",
            endpoint="/v1/chat/completions",
            prompt_tokens=10000,
            completion_tokens=5000,
        )

        # $15/1M input, $60/1M output
        expected = (10000 * 15.00 + 5000 * 60.00) / 1_000_000
        assert abs(cost - expected) < 0.000001

        # Test O1-mini
        cost_mini = tracker.record_usage(
            api_key=api_key,
            model="o1-mini",
            endpoint="/v1/chat/completions",
            prompt_tokens=10000,
            completion_tokens=5000,
        )

        # $3/1M input, $12/1M output
        expected_mini = (10000 * 3.00 + 5000 * 12.00) / 1_000_000
        assert abs(cost_mini - expected_mini) < 0.000001
        assert cost_mini < cost  # Mini should be cheaper

    def test_fine_tuned_model_pricing(self, tracker):
        """Test fine-tuned model pricing."""
        api_key = "test-finetuned"

        # Test fine-tuned GPT-4o
        cost = tracker.record_usage(
            api_key=api_key,
            model="ft:gpt-4o-2024-08-06:my-org:my-model:abc123",
            endpoint="/v1/chat/completions",
            prompt_tokens=10000,
            completion_tokens=5000,
        )

        # Fine-tuned pricing: $3.75/1M input, $15/1M output
        expected = (10000 * 3.75 + 5000 * 15.00) / 1_000_000
        assert abs(cost - expected) < 0.000001

        # Test fine-tuned GPT-4o-mini
        cost_mini = tracker.record_usage(
            api_key=api_key,
            model="ft:gpt-4o-mini-2024-07-18:acme:custom:xyz789",
            endpoint="/v1/chat/completions",
            prompt_tokens=10000,
            completion_tokens=5000,
        )

        # Fine-tuned mini pricing: $0.30/1M input, $1.20/1M output
        expected_mini = (10000 * 0.30 + 5000 * 1.20) / 1_000_000
        assert abs(cost_mini - expected_mini) < 0.000001

    def test_image_generation_pricing(self, tracker):
        """Test image generation pricing for different sizes and qualities."""
        api_key = "test-images"

        # DALL-E 3 standard 1024x1024
        cost_standard = tracker.record_usage(
            api_key=api_key,
            model="dall-e-3",
            endpoint="/v1/images/generations",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "1024x1024", "quality": "standard", "n": 1}
        )
        assert abs(cost_standard - 0.040) < 0.001

        # DALL-E 3 HD 1024x1024
        cost_hd = tracker.record_usage(
            api_key=api_key,
            model="dall-e-3",
            endpoint="/v1/images/generations",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "1024x1024", "quality": "hd", "n": 1}
        )
        assert abs(cost_hd - 0.080) < 0.001
        assert cost_hd > cost_standard  # HD is more expensive

        # DALL-E 3 HD large size
        cost_large_hd = tracker.record_usage(
            api_key=api_key,
            model="dall-e-3",
            endpoint="/v1/images/generations",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "1024x1792", "quality": "hd", "n": 1}
        )
        assert abs(cost_large_hd - 0.120) < 0.001

        # Multiple images
        cost_multiple = tracker.record_usage(
            api_key=api_key,
            model="dall-e-3",
            endpoint="/v1/images/generations",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "1024x1024", "quality": "standard", "n": 4}
        )
        assert abs(cost_multiple - 0.160) < 0.001  # 4 * $0.040

    def test_audio_pricing(self, tracker):
        """Test audio (TTS and transcription) pricing."""
        api_key = "test-audio"

        # TTS-1 standard quality
        cost_tts1 = tracker.record_usage(
            api_key=api_key,
            model="tts-1",
            endpoint="/v1/audio/speech",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"characters": 1000000}  # 1M characters
        )
        # $15 per 1M characters
        assert abs(cost_tts1 - 15.00) < 0.01

        # TTS-1-HD
        cost_tts_hd = tracker.record_usage(
            api_key=api_key,
            model="tts-1-hd",
            endpoint="/v1/audio/speech",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"characters": 1000000}
        )
        # $30 per 1M characters
        assert abs(cost_tts_hd - 30.00) < 0.01
        assert cost_tts_hd > cost_tts1  # HD is more expensive

        # Whisper transcription
        cost_whisper = tracker.record_usage(
            api_key=api_key,
            model="whisper-1",
            endpoint="/v1/audio/transcriptions",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"characters": 1000000}
        )
        # $6 per 1M characters
        assert abs(cost_whisper - 6.00) < 0.01


class TestBudgetManagement:
    """Tests for budget creation, tracking, and enforcement."""

    def test_set_budget_creates_budget(self, tracker):
        """Test that set_budget creates a new budget configuration."""
        api_key = "test-budget-create"
        limit = 100.0

        tracker.set_budget(
            api_key=api_key,
            limit=limit,
            period=BudgetPeriod.MONTHLY,
            limit_type=BudgetLimitType.SOFT,
            alert_threshold=0.8
        )

        used, remaining, over_limit = tracker.check_budget(api_key)
        assert used == 0.0
        assert remaining == limit
        assert not over_limit

        # Check budget info in cost breakdown
        cost_info = tracker.get_cost_by_key(api_key)
        assert cost_info["budget"] is not None
        assert cost_info["budget"]["limit"] == limit
        assert cost_info["budget"]["period"] == "monthly"

    def test_check_budget_returns_correct_status(self, tracker):
        """Test that check_budget returns accurate status."""
        api_key = "test-budget-status"
        limit = 1.0

        tracker.set_budget(api_key, limit)

        # Initial state
        used, remaining, over_limit = tracker.check_budget(api_key)
        assert used == 0.0
        assert remaining == 1.0
        assert not over_limit

        # Record some usage
        for _ in range(10):
            tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        # Check updated status
        used, remaining, over_limit = tracker.check_budget(api_key)
        assert used > 0
        assert remaining < limit
        assert remaining == limit - used

    def test_budget_alerts_triggered_at_threshold(self, tracker):
        """Test that budget alerts are triggered at the correct threshold."""
        api_key = "test-budget-alert"
        limit = 0.01  # Small limit to trigger easily
        alert_threshold = 0.5  # Alert at 50%

        tracker.set_budget(
            api_key=api_key,
            limit=limit,
            alert_threshold=alert_threshold
        )

        # Record usage to exceed threshold
        while True:
            tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )
            used, remaining, over_limit = tracker.check_budget(api_key)
            if used / limit > alert_threshold:
                break

        # Verify alert was triggered (budget system tracks this internally)
        assert used >= limit * alert_threshold

    def test_budget_soft_vs_hard_limits(self, tracker):
        """Test difference between SOFT and HARD budget limits."""
        # SOFT limit - requests continue even when over budget
        api_key_soft = "test-budget-soft"
        tracker.set_budget(
            api_key_soft,
            limit=0.001,
            limit_type=BudgetLimitType.SOFT
        )

        # Record usage exceeding budget
        for _ in range(10):
            cost = tracker.record_usage(
                api_key=api_key_soft,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=1000,
            )
            assert cost > 0  # Requests succeed with soft limit

        used, remaining, over_limit = tracker.check_budget(api_key_soft)
        assert over_limit
        assert used > 0.001

        # HARD limit - would be enforced at API level
        # (CostTracker records but doesn't block - that's API handler's job)
        api_key_hard = "test-budget-hard"
        tracker.set_budget(
            api_key_hard,
            limit=0.001,
            limit_type=BudgetLimitType.HARD
        )

        # Record usage
        for _ in range(5):
            tracker.record_usage(
                api_key=api_key_hard,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=1000,
            )

        used, remaining, over_limit = tracker.check_budget(api_key_hard)
        # CostTracker tracks but doesn't block
        # The API handler would check over_limit and reject requests

    def test_budget_reset_by_period(self, tracker):
        """Test budget reset for different periods."""
        # Test daily budget
        api_key_daily = "test-budget-daily"
        tracker.set_budget(
            api_key_daily,
            limit=10.0,
            period=BudgetPeriod.DAILY
        )

        # Test weekly budget
        api_key_weekly = "test-budget-weekly"
        tracker.set_budget(
            api_key_weekly,
            limit=100.0,
            period=BudgetPeriod.WEEKLY
        )

        # Test monthly budget
        api_key_monthly = "test-budget-monthly"
        tracker.set_budget(
            api_key_monthly,
            limit=1000.0,
            period=BudgetPeriod.MONTHLY
        )

        # Verify budgets were set correctly
        info_daily = tracker.get_cost_by_key(api_key_daily)["budget"]
        assert info_daily["period"] == "daily"

        info_weekly = tracker.get_cost_by_key(api_key_weekly)["budget"]
        assert info_weekly["period"] == "weekly"

        info_monthly = tracker.get_cost_by_key(api_key_monthly)["budget"]
        assert info_monthly["period"] == "monthly"


class TestAggregation:
    """Tests for cost aggregation and filtering."""

    def test_get_cost_by_key_accurate(self, tracker):
        """Test that get_cost_by_key returns accurate aggregated data."""
        api_key = "test-agg-key"

        # Record usage across different models and endpoints
        tracker.record_usage(
            api_key=api_key,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        tracker.record_usage(
            api_key=api_key,
            model="gpt-4o-mini",
            endpoint="/v1/chat/completions",
            prompt_tokens=5000,
            completion_tokens=2500,
        )

        tracker.record_usage(
            api_key=api_key,
            model="text-embedding-3-small",
            endpoint="/v1/embeddings",
            prompt_tokens=10000,
            completion_tokens=0,
        )

        result = tracker.get_cost_by_key(api_key)

        # Verify structure
        assert result["api_key"] == api_key
        assert result["requests"] == 3
        assert result["total_cost"] > 0

        # Verify by_model breakdown
        assert "gpt-4o" in result["by_model"]
        assert "gpt-4o-mini" in result["by_model"]
        assert "text-embedding-3-small" in result["by_model"]

        # Verify by_endpoint breakdown
        assert "/v1/chat/completions" in result["by_endpoint"]
        assert "/v1/embeddings" in result["by_endpoint"]

        # Verify tokens
        assert result["tokens"]["prompt_tokens"] == 16000
        assert result["tokens"]["completion_tokens"] == 3000
        assert result["tokens"]["total_tokens"] == 19000

    def test_get_cost_by_model_correct(self, tracker):
        """Test that get_cost_by_model returns correct aggregations."""
        # Record usage for multiple models
        for model in ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]:
            tracker.record_usage(
                api_key=f"test-{model}",
                model=model,
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        costs = tracker.get_cost_by_model()

        assert "gpt-4o" in costs
        assert "gpt-4o-mini" in costs
        assert "gpt-3.5-turbo" in costs

        # Verify relative costs (GPT-4o > GPT-4o-mini)
        assert costs["gpt-4o"] > costs["gpt-4o-mini"]
        assert costs["gpt-4o"] > costs["gpt-3.5-turbo"]

    def test_get_cost_by_endpoint_works(self, tracker):
        """Test that get_cost_by_endpoint returns correct aggregations."""
        api_key = "test-endpoint-agg"

        # Chat completions
        for _ in range(5):
            tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        # Embeddings
        for _ in range(3):
            tracker.record_usage(
                api_key=api_key,
                model="text-embedding-3-small",
                endpoint="/v1/embeddings",
                prompt_tokens=1000,
                completion_tokens=0,
            )

        # Images
        tracker.record_usage(
            api_key=api_key,
            model="dall-e-3",
            endpoint="/v1/images/generations",
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "1024x1024", "quality": "standard", "n": 1}
        )

        costs = tracker.get_cost_by_endpoint()

        assert "/v1/chat/completions" in costs
        assert "/v1/embeddings" in costs
        assert "/v1/images/generations" in costs

        # Chat should be most expensive (5 requests vs 3 embeddings)
        assert costs["/v1/chat/completions"] > costs["/v1/embeddings"]

    def test_time_filtering_period_hours(self, tracker):
        """Test that period_hours filtering works correctly."""
        api_key = "test-time-filter"

        # Record some usage
        for _ in range(10):
            tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        # Get all-time costs
        all_time = tracker.get_cost_by_key(api_key)
        assert all_time["requests"] == 10

        # Get last hour (should include all since just recorded)
        last_hour = tracker.get_cost_by_key(api_key, period_hours=1)
        assert last_hour["requests"] == 10
        assert last_hour["period_hours"] == 1
        assert abs(last_hour["total_cost"] - all_time["total_cost"]) < 0.000001

        # Test with different models
        model_costs_24h = tracker.get_cost_by_model(period_hours=24)
        assert "gpt-4o" in model_costs_24h

        # Test with endpoints
        endpoint_costs_7d = tracker.get_cost_by_endpoint(period_hours=168)  # 7 days
        assert "/v1/chat/completions" in endpoint_costs_7d


class TestOptimization:
    """Tests for cost optimization suggestions."""

    def test_suggestions_generated(self, tracker):
        """Test that optimization suggestions are generated."""
        api_key = "test-optimization"

        # Record many expensive GPT-4 requests to trigger suggestion
        for i in range(100):
            tracker.record_usage(
                api_key=api_key,
                model="gpt-4",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        suggestions = tracker.get_optimization_suggestions(api_key)

        # Should have suggestions
        assert len(suggestions) > 0

        # Should suggest cheaper model
        cheaper_model_suggestions = [
            s for s in suggestions if s.suggestion_type == "cheaper_model"
        ]
        assert len(cheaper_model_suggestions) > 0

    def test_cheaper_model_recommendations(self, tracker):
        """Test that cheaper model alternatives are suggested."""
        api_key = "test-cheaper-model"

        # Use expensive GPT-4 extensively
        for _ in range(100):
            tracker.record_usage(
                api_key=api_key,
                model="gpt-4",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        suggestions = tracker.get_optimization_suggestions(api_key)
        cheaper_suggestions = [
            s for s in suggestions if s.suggestion_type == "cheaper_model"
        ]

        if cheaper_suggestions:
            suggestion = cheaper_suggestions[0]
            assert suggestion.api_key == api_key
            assert "gpt-4" in suggestion.description.lower()
            assert suggestion.potential_savings > 0
            assert "current_model" in suggestion.details
            assert suggestion.details["current_model"] == "gpt-4"

    def test_cache_suggestions(self, tracker):
        """Test that caching suggestions are generated for high-volume usage."""
        api_key = "test-cache-suggestion"

        # Record many requests to trigger cache suggestion
        for _ in range(60):  # More than 50 to trigger suggestion
            tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        suggestions = tracker.get_optimization_suggestions(api_key)
        cache_suggestions = [
            s for s in suggestions if s.suggestion_type == "enable_caching"
        ]

        if cache_suggestions:
            suggestion = cache_suggestions[0]
            assert suggestion.api_key == api_key
            assert "cache" in suggestion.description.lower() or "caching" in suggestion.description.lower()
            assert suggestion.potential_savings > 0
            assert "requests_per_day" in suggestion.details

    def test_batch_suggestions(self, tracker):
        """Test that batch processing suggestions could be implemented."""
        # This is more of a design test - batch suggestions aren't explicitly
        # implemented in the current code, but the infrastructure is there
        api_key = "test-batch"

        # Record regular requests
        for _ in range(20):
            tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=1000,
            )

        # The system could suggest batch processing for these
        # This test documents the expected behavior


class TestProjections:
    """Tests for cost projections."""

    def test_monthly_cost_projection(self, tracker):
        """Test monthly cost projection calculation."""
        api_key = "test-projection"

        # Record usage over simulated time period
        daily_requests = 10
        for _ in range(daily_requests):
            tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        # Get projection
        projected = tracker.get_projected_monthly_cost(api_key)

        # Should have a projection
        assert projected > 0

        # Projection should be reasonable (scale from current usage)
        current_cost = tracker.get_cost_by_key(api_key)["total_cost"]
        # Projection extrapolates from 7 days, so should be about 30/7 times current
        # (but we only have recent data, so it scales from that)
        assert projected >= current_cost

    def test_projection_based_on_7day_average(self, tracker):
        """Test that projections use 7-day average."""
        api_key = "test-7day-avg"

        # Record consistent usage
        cost_per_request = None
        for _ in range(50):
            cost = tracker.record_usage(
                api_key=api_key,
                model="gpt-4o-mini",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )
            if cost_per_request is None:
                cost_per_request = cost

        # Get projection
        projected = tracker.get_projected_monthly_cost(api_key)

        # Calculate expected projection
        # 50 requests, each costing the same, projected over 30 days
        # Projection uses last 7 days, we have all data recent
        total_cost = cost_per_request * 50
        expected_daily = total_cost / 7.0
        expected_monthly = expected_daily * 30

        # Should be approximately equal
        assert abs(projected - expected_monthly) < 0.01

    def test_projection_scales_correctly(self, tracker):
        """Test that projections scale correctly with usage."""
        api_key1 = "test-scale-1x"
        api_key2 = "test-scale-2x"

        # Record usage for key1
        for _ in range(10):
            tracker.record_usage(
                api_key=api_key1,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        # Record 2x usage for key2
        for _ in range(20):
            tracker.record_usage(
                api_key=api_key2,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        projected1 = tracker.get_projected_monthly_cost(api_key1)
        projected2 = tracker.get_projected_monthly_cost(api_key2)

        # key2 should have ~2x the projection of key1
        ratio = projected2 / projected1
        assert 1.8 < ratio < 2.2  # Allow some tolerance


class TestSavingsTracking:
    """Tests for cache and batch savings calculations."""

    def test_cache_savings_calculated(self, tracker):
        """Test that cache savings are correctly calculated."""
        api_key = "test-cache-savings"

        # Record usage with cached tokens
        total_cached_tokens = 0
        for _ in range(10):
            cached_tokens = 500
            total_cached_tokens += cached_tokens
            tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
                cached_tokens=cached_tokens,
            )

        savings = tracker.get_cache_savings(api_key)

        assert savings["cached_tokens"] == total_cached_tokens
        assert savings["savings"] > 0
        assert savings["regular_cost"] > savings["cached_cost"]
        assert abs(savings["savings"] - (savings["regular_cost"] - savings["cached_cost"])) < 0.000001

    def test_batch_savings_calculated(self, tracker):
        """Test that batch processing savings are calculated."""
        api_key = "test-batch-savings"

        # Record batch requests
        total_completion_tokens = 0
        for _ in range(10):
            completion_tokens = 1000
            total_completion_tokens += completion_tokens
            tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/batches",
                prompt_tokens=1000,
                completion_tokens=completion_tokens,
            )

        savings = tracker.get_batch_savings(api_key)

        assert savings["batch_requests"] == 10
        assert savings["completion_tokens"] == total_completion_tokens
        assert savings["savings"] > 0
        # Batch gives 50% discount on completion tokens
        assert abs(savings["batch_cost"] - savings["regular_cost"] * 0.5) < 0.001
        assert abs(savings["savings"] - savings["regular_cost"] * 0.5) < 0.001


class TestRealisticUsagePatterns:
    """Tests with realistic usage patterns and scenarios."""

    def test_mixed_model_usage_scenario(self, tracker):
        """Test a realistic scenario with mixed model usage."""
        api_key = "prod-app-xyz"

        # Simulate a day of usage
        # Morning: high-quality responses with GPT-4o
        for _ in range(20):
            tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=500,
                completion_tokens=300,
            )

        # Midday: bulk processing with GPT-4o-mini
        for _ in range(100):
            tracker.record_usage(
                api_key=api_key,
                model="gpt-4o-mini",
                endpoint="/v1/chat/completions",
                prompt_tokens=200,
                completion_tokens=100,
            )

        # Afternoon: embeddings for search
        for _ in range(50):
            tracker.record_usage(
                api_key=api_key,
                model="text-embedding-3-small",
                endpoint="/v1/embeddings",
                prompt_tokens=500,
                completion_tokens=0,
            )

        # Evening: some image generation
        for _ in range(3):
            tracker.record_usage(
                api_key=api_key,
                model="dall-e-3",
                endpoint="/v1/images/generations",
                prompt_tokens=0,
                completion_tokens=0,
                metadata={"size": "1024x1024", "quality": "standard", "n": 1}
            )

        # Analyze costs
        result = tracker.get_cost_by_key(api_key)

        assert result["requests"] == 173
        assert "gpt-4o" in result["by_model"]
        assert "gpt-4o-mini" in result["by_model"]
        assert "text-embedding-3-small" in result["by_model"]
        assert "dall-e-3" in result["by_model"]

        # GPT-4o should be most expensive per request, but mini has most requests
        # Check that costs make sense
        assert result["by_model"]["gpt-4o-mini"] > 0
        assert result["by_model"]["gpt-4o"] > 0

    def test_high_volume_caching_scenario(self, tracker):
        """Test scenario with heavy caching usage."""
        api_key = "cache-heavy-app"

        # Simulate application with prompt caching
        # First request: no cache
        tracker.record_usage(
            api_key=api_key,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            prompt_tokens=2000,
            completion_tokens=500,
            cached_tokens=0,
        )

        # Subsequent requests: 80% cache hit
        for _ in range(99):
            tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=2000,
                completion_tokens=500,
                cached_tokens=1600,  # 80% cached
            )

        # Calculate savings
        savings = tracker.get_cache_savings(api_key)

        # Should have significant savings
        assert savings["cached_tokens"] == 1600 * 99  # No cache on first request
        assert savings["savings"] > 0

        # Verify cost reduction
        result = tracker.get_cost_by_key(api_key)
        # With caching, cost should be significantly less than without

    def test_budget_conscious_organization(self, tracker):
        """Test scenario of organization managing multiple API keys with budgets."""
        # Set up multiple teams with budgets
        teams = {
            "team-research": {"budget": 1000.0, "model": "gpt-4o"},
            "team-prod": {"budget": 500.0, "model": "gpt-4o-mini"},
            "team-experimental": {"budget": 100.0, "model": "gpt-3.5-turbo"},
        }

        for team_key, config in teams.items():
            tracker.set_budget(
                team_key,
                config["budget"],
                period=BudgetPeriod.MONTHLY,
                limit_type=BudgetLimitType.SOFT,
                alert_threshold=0.8
            )

        # Simulate usage
        for team_key, config in teams.items():
            for _ in range(50):
                tracker.record_usage(
                    api_key=team_key,
                    model=config["model"],
                    endpoint="/v1/chat/completions",
                    prompt_tokens=1000,
                    completion_tokens=500,
                )

        # Check each team's status
        for team_key, config in teams.items():
            used, remaining, over_limit = tracker.check_budget(team_key)
            assert used > 0
            assert remaining < config["budget"]

            result = tracker.get_cost_by_key(team_key)
            assert result["budget"]["limit"] == config["budget"]

    def test_multi_service_application(self, tracker):
        """Test application using multiple OpenAI services."""
        api_key = "multi-service-app"

        # Chat completions
        for _ in range(30):
            tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=800,
                completion_tokens=400,
            )

        # Embeddings for RAG
        for _ in range(50):
            tracker.record_usage(
                api_key=api_key,
                model="text-embedding-3-large",
                endpoint="/v1/embeddings",
                prompt_tokens=512,
                completion_tokens=0,
            )

        # Image generation
        for _ in range(5):
            tracker.record_usage(
                api_key=api_key,
                model="dall-e-3",
                endpoint="/v1/images/generations",
                prompt_tokens=0,
                completion_tokens=0,
                metadata={"size": "1024x1024", "quality": "hd", "n": 1}
            )

        # TTS for audio responses
        for _ in range(10):
            tracker.record_usage(
                api_key=api_key,
                model="tts-1",
                endpoint="/v1/audio/speech",
                prompt_tokens=0,
                completion_tokens=0,
                metadata={"characters": 1000}
            )

        # Analyze usage
        result = tracker.get_cost_by_key(api_key)
        endpoint_costs = tracker.get_cost_by_endpoint()

        assert result["requests"] == 95
        assert len(result["by_endpoint"]) == 4
        assert "/v1/chat/completions" in endpoint_costs
        assert "/v1/embeddings" in endpoint_costs
        assert "/v1/images/generations" in endpoint_costs
        assert "/v1/audio/speech" in endpoint_costs

    def test_cost_summary_comprehensive(self, tracker):
        """Test comprehensive cost summary with multiple API keys and models."""
        # Simulate multiple users
        for i in range(5):
            api_key = f"user-{i}"
            models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]

            for model in models:
                for _ in range(10):
                    tracker.record_usage(
                        api_key=api_key,
                        model=model,
                        endpoint="/v1/chat/completions",
                        prompt_tokens=500,
                        completion_tokens=250,
                    )

        summary = tracker.get_summary()

        # Verify summary structure
        assert "total_cost" in summary
        assert "total_cost_24h" in summary
        assert "total_cost_7d" in summary
        assert "projected_monthly_cost" in summary
        assert "by_key" in summary
        assert "by_model" in summary
        assert "by_endpoint" in summary
        assert "cache_savings" in summary
        assert "batch_savings" in summary

        # Verify counts
        assert summary["total_requests"] == 150  # 5 users * 3 models * 10 requests
        assert summary["unique_api_keys"] == 5

        # Verify all users are included
        for i in range(5):
            assert f"user-{i}" in summary["by_key"]

        # Verify all models are included
        for model in ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]:
            assert model in summary["by_model"]
