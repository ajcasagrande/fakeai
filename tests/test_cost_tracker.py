#!/usr/bin/env python3
"""
Tests for the FakeAI cost tracking and billing simulation module.
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
def cost_tracker():
    """Create a fresh cost tracker instance for testing."""
    tracker = CostTracker()
    # Clear any existing data
    tracker.clear_history()
    return tracker


class TestBasicCostTracking:
    """Tests for basic cost tracking functionality."""

    def test_singleton_pattern(self, cost_tracker):
        """Test that CostTracker is a singleton."""
        tracker1 = CostTracker()
        tracker2 = CostTracker()
        assert tracker1 is tracker2

    def test_record_chat_usage_gpt4o(self, cost_tracker):
        """Test recording chat completion usage for GPT-4o."""
        api_key = "test-key-1"
        model = "gpt-4o"
        endpoint = "/v1/chat/completions"
        prompt_tokens = 100
        completion_tokens = 50

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint=endpoint,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        # Verify cost calculation: (100 * 5.00 + 50 * 15.00) / 1M = 0.0011
        expected_cost = (100 * 5.00 + 50 * 15.00) / 1_000_000
        assert abs(cost - expected_cost) < 0.0001

    def test_record_chat_usage_gpt35(self, cost_tracker):
        """Test recording chat completion usage for GPT-3.5."""
        api_key = "test-key-2"
        model = "gpt-3.5-turbo"
        endpoint = "/v1/chat/completions"
        prompt_tokens = 1000
        completion_tokens = 500

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint=endpoint,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        # Verify cost calculation: (1000 * 0.50 + 500 * 1.50) / 1M
        expected_cost = (1000 * 0.50 + 500 * 1.50) / 1_000_000
        assert abs(cost - expected_cost) < 0.0001

    def test_record_embedding_usage(self, cost_tracker):
        """Test recording embedding usage."""
        api_key = "test-key-3"
        model = "text-embedding-3-small"
        endpoint = "/v1/embeddings"
        prompt_tokens = 1000
        completion_tokens = 0

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint=endpoint,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        # Verify cost calculation: 1000 * 0.02 / 1M
        expected_cost = 1000 * 0.02 / 1_000_000
        assert abs(cost - expected_cost) < 0.0001

    def test_record_usage_with_cache(self, cost_tracker):
        """Test recording usage with cached tokens."""
        api_key = "test-key-4"
        model = "gpt-4o"
        endpoint = "/v1/chat/completions"
        prompt_tokens = 1000
        completion_tokens = 500
        cached_tokens = 500

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint=endpoint,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cached_tokens=cached_tokens,
        )

        # Cost should be: (500 regular * 5.00 + 500 cached * 2.50 + 500 output * 15.00) / 1M
        pricing = MODEL_PRICING["gpt-4o"]
        expected_cost = (
            500 * pricing.input_price_per_million
            + 500 * pricing.cached_input_price_per_million
            + 500 * pricing.output_price_per_million
        ) / 1_000_000
        assert abs(cost - expected_cost) < 0.0001

    def test_record_unknown_model(self, cost_tracker):
        """Test recording usage for unknown model (should use default pricing)."""
        api_key = "test-key-5"
        model = "unknown-model-xyz"
        endpoint = "/v1/chat/completions"
        prompt_tokens = 100
        completion_tokens = 50

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint=endpoint,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        # Should use GPT-3.5 turbo pricing as default
        default_pricing = MODEL_PRICING["gpt-3.5-turbo"]
        expected_cost = (
            100 * default_pricing.input_price_per_million
            + 50 * default_pricing.output_price_per_million
        ) / 1_000_000
        assert abs(cost - expected_cost) < 0.0001


class TestCostAggregation:
    """Tests for cost aggregation and querying."""

    def test_get_cost_by_key(self, cost_tracker):
        """Test getting costs by API key."""
        api_key = "test-key-6"
        model = "gpt-4o-mini"

        # Record multiple requests
        for i in range(5):
            cost_tracker.record_usage(
                api_key=api_key,
                model=model,
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
            )

        result = cost_tracker.get_cost_by_key(api_key)

        assert result["api_key"] == api_key
        assert result["total_cost"] > 0
        assert result["requests"] == 5
        assert model in result["by_model"]
        assert result["tokens"]["total_tokens"] == 750  # (100 + 50) * 5

    def test_get_cost_by_model(self, cost_tracker):
        """Test getting costs by model."""
        api_key = "test-key-7"

        # Record usage for different models
        cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
        )
        cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-3.5-turbo",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
        )

        result = cost_tracker.get_cost_by_model()

        assert "gpt-4o" in result
        assert "gpt-3.5-turbo" in result
        assert result["gpt-4o"] > result["gpt-3.5-turbo"]  # GPT-4o is more expensive

    def test_get_cost_by_endpoint(self, cost_tracker):
        """Test getting costs by endpoint."""
        api_key = "test-key-8"

        # Record usage for different endpoints
        cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
        )
        cost_tracker.record_usage(
            api_key=api_key,
            model="text-embedding-3-small",
            endpoint="/v1/embeddings",
            prompt_tokens=1000,
            completion_tokens=0,
        )

        result = cost_tracker.get_cost_by_endpoint()

        assert "/v1/chat/completions" in result
        assert "/v1/embeddings" in result

    def test_get_total_cost(self, cost_tracker):
        """Test getting total cost across all keys."""
        # Record usage for multiple API keys
        for i in range(3):
            cost_tracker.record_usage(
                api_key=f"test-key-{i}",
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
            )

        total_cost = cost_tracker.get_total_cost()
        assert total_cost > 0

        # Calculate expected total
        expected_per_request = (100 * 5.00 + 50 * 15.00) / 1_000_000
        expected_total = expected_per_request * 3
        assert abs(total_cost - expected_total) < 0.0001

    def test_get_cost_by_key_with_period(self, cost_tracker):
        """Test getting costs with time period filter."""
        api_key = "test-key-9"

        # Record usage
        cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
        )

        # Get cost for last hour
        result = cost_tracker.get_cost_by_key(api_key, period_hours=1)
        assert result["total_cost"] > 0
        assert result["period_hours"] == 1


class TestBudgetManagement:
    """Tests for budget management functionality."""

    def test_set_budget(self, cost_tracker):
        """Test setting a budget for an API key."""
        api_key = "test-key-10"
        limit = 10.0

        cost_tracker.set_budget(api_key, limit)

        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        assert used == 0.0
        assert remaining == limit
        assert not over_limit

    def test_budget_tracking(self, cost_tracker):
        """Test that budget is tracked correctly."""
        api_key = "test-key-11"
        limit = 0.01  # $0.01 limit

        cost_tracker.set_budget(api_key, limit)

        # Record usage
        for _ in range(10):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=1000,
            )

        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        assert used > 0
        assert remaining < limit
        assert over_limit  # Should be over limit

    def test_budget_soft_limit(self, cost_tracker):
        """Test soft budget limit (warning only)."""
        api_key = "test-key-12"
        limit = 0.001

        cost_tracker.set_budget(api_key, limit, limit_type=BudgetLimitType.SOFT)

        # Record usage that exceeds budget
        for _ in range(5):
            cost = cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=1000,
            )
            # Request should still succeed (soft limit)
            assert cost > 0

    def test_budget_alert_threshold(self, cost_tracker):
        """Test budget alert threshold."""
        api_key = "test-key-13"
        limit = 0.01

        cost_tracker.set_budget(api_key, limit, alert_threshold=0.5)

        # Record usage up to 60% of budget
        while True:
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o-mini",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=1000,
            )
            used, _, _ = cost_tracker.check_budget(api_key)
            if used / limit > 0.6:
                break

        # Budget should have been alerted
        budget_info = cost_tracker.get_cost_by_key(api_key)["budget"]
        assert budget_info is not None

    def test_budget_periods(self, cost_tracker):
        """Test different budget periods."""
        api_key = "test-key-14"

        # Test daily budget
        cost_tracker.set_budget(api_key, 10.0, period=BudgetPeriod.DAILY)
        budget_info = cost_tracker.get_cost_by_key(api_key)["budget"]
        assert budget_info["period"] == "daily"

        # Test monthly budget
        cost_tracker.set_budget(api_key, 100.0, period=BudgetPeriod.MONTHLY)
        budget_info = cost_tracker.get_cost_by_key(api_key)["budget"]
        assert budget_info["period"] == "monthly"


class TestImageAndAudioCosts:
    """Tests for image and audio cost calculation."""

    def test_image_generation_cost(self, cost_tracker):
        """Test cost calculation for image generation."""
        api_key = "test-key-15"
        model = "dall-e-3"
        endpoint = "/v1/images/generations"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint=endpoint,
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "1024x1024", "quality": "standard", "n": 1},
        )

        # Verify cost matches pricing table
        expected_cost = 0.040
        assert abs(cost - expected_cost) < 0.001

    def test_image_generation_hd_cost(self, cost_tracker):
        """Test cost calculation for HD image generation."""
        api_key = "test-key-16"
        model = "dall-e-3"
        endpoint = "/v1/images/generations"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint=endpoint,
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"size": "1024x1792", "quality": "hd", "n": 1},
        )

        # Verify cost matches pricing table
        expected_cost = 0.120
        assert abs(cost - expected_cost) < 0.001

    def test_audio_tts_cost(self, cost_tracker):
        """Test cost calculation for text-to-speech."""
        api_key = "test-key-17"
        model = "tts-1"
        endpoint = "/v1/audio/speech"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint=endpoint,
            prompt_tokens=0,
            completion_tokens=0,
            metadata={"characters": 1000},
        )

        # Verify cost: 1000 chars * $15 / 1M = $0.015
        expected_cost = 1000 * 15.00 / 1_000_000
        assert abs(cost - expected_cost) < 0.0001


class TestFineTunedModels:
    """Tests for fine-tuned model cost calculation."""

    def test_fine_tuned_model_cost(self, cost_tracker):
        """Test cost calculation for fine-tuned models."""
        api_key = "test-key-18"
        model = "ft:gpt-4o-2024-08-06:my-org::abc123"
        endpoint = "/v1/chat/completions"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint=endpoint,
            prompt_tokens=1000,
            completion_tokens=500,
        )

        # Verify cost uses fine-tuned pricing: (1000 * 3.75 + 500 * 15.00) / 1M
        expected_cost = (1000 * 3.75 + 500 * 15.00) / 1_000_000
        assert abs(cost - expected_cost) < 0.0001

    def test_fine_tuned_mini_model_cost(self, cost_tracker):
        """Test cost calculation for fine-tuned mini models."""
        api_key = "test-key-19"
        model = "ft:gpt-4o-mini-2024-07-18:acme::xyz789"
        endpoint = "/v1/chat/completions"

        cost = cost_tracker.record_usage(
            api_key=api_key,
            model=model,
            endpoint=endpoint,
            prompt_tokens=1000,
            completion_tokens=500,
        )

        # Verify cost uses fine-tuned mini pricing: (1000 * 0.30 + 500 * 1.20) / 1M
        expected_cost = (1000 * 0.30 + 500 * 1.20) / 1_000_000
        assert abs(cost - expected_cost) < 0.0001


class TestCostOptimization:
    """Tests for cost optimization features."""

    def test_projected_monthly_cost(self, cost_tracker):
        """Test projected monthly cost calculation."""
        api_key = "test-key-20"

        # Record usage
        for _ in range(10):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        projected = cost_tracker.get_projected_monthly_cost(api_key)
        assert projected > 0

    def test_cache_savings_calculation(self, cost_tracker):
        """Test cache savings calculation."""
        api_key = "test-key-21"

        # Record usage with cached tokens
        for _ in range(10):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
                cached_tokens=500,
            )

        savings = cost_tracker.get_cache_savings(api_key)
        assert savings["cached_tokens"] == 5000
        assert savings["savings"] > 0

    def test_batch_savings_calculation(self, cost_tracker):
        """Test batch processing savings calculation."""
        api_key = "test-key-22"

        # Record batch usage
        for _ in range(5):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/batches",
                prompt_tokens=1000,
                completion_tokens=1000,
            )

        savings = cost_tracker.get_batch_savings(api_key)
        assert savings["batch_requests"] == 5
        assert savings["savings"] > 0

    def test_optimization_suggestions(self, cost_tracker):
        """Test generation of optimization suggestions."""
        api_key = "test-key-23"

        # Record many GPT-4 requests to trigger suggestion
        for _ in range(100):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        suggestions = cost_tracker.get_optimization_suggestions(api_key)
        # Should suggest cheaper model
        assert any(s.suggestion_type == "cheaper_model" for s in suggestions)


class TestSummaryAndReporting:
    """Tests for summary and reporting features."""

    def test_get_summary(self, cost_tracker):
        """Test getting comprehensive cost summary."""
        # Record usage for multiple keys
        for i in range(3):
            cost_tracker.record_usage(
                api_key=f"test-key-{i}",
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        summary = cost_tracker.get_summary()

        assert "total_cost" in summary
        assert "total_cost_24h" in summary
        assert "projected_monthly_cost" in summary
        assert "by_key" in summary
        assert "by_model" in summary
        assert "by_endpoint" in summary
        assert "cache_savings" in summary
        assert "batch_savings" in summary
        assert summary["total_requests"] == 3
        assert summary["unique_api_keys"] == 3

    def test_clear_history(self, cost_tracker):
        """Test clearing usage history."""
        api_key = "test-key-24"

        # Record usage
        cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        # Verify usage was recorded
        result = cost_tracker.get_cost_by_key(api_key)
        assert result["total_cost"] > 0

        # Clear history for this key
        cost_tracker.clear_history(api_key)

        # Verify history was cleared
        result = cost_tracker.get_cost_by_key(api_key)
        assert result["total_cost"] == 0

    def test_clear_all_history(self, cost_tracker):
        """Test clearing all usage history."""
        # Record usage for multiple keys
        for i in range(3):
            cost_tracker.record_usage(
                api_key=f"test-key-{i}",
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        # Clear all history
        cost_tracker.clear_history()

        # Verify all history was cleared
        summary = cost_tracker.get_summary()
        assert summary["total_cost"] == 0
        assert summary["total_requests"] == 0


class TestThreadSafety:
    """Tests for thread safety of the cost tracker."""

    def test_concurrent_recording(self, cost_tracker):
        """Test recording usage from multiple threads."""
        import threading

        api_key = "test-key-25"
        num_threads = 10
        records_per_thread = 10

        def record_usage():
            for _ in range(records_per_thread):
                cost_tracker.record_usage(
                    api_key=api_key,
                    model="gpt-4o",
                    endpoint="/v1/chat/completions",
                    prompt_tokens=100,
                    completion_tokens=50,
                )

        threads = [threading.Thread(target=record_usage) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        result = cost_tracker.get_cost_by_key(api_key)
        assert result["requests"] == num_threads * records_per_thread
