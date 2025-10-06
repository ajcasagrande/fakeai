#!/usr/bin/env python3
"""
Tests for Per-Model Metrics Tracking

Comprehensive test suite for ModelMetricsTracker with 20+ tests covering:
- Basic tracking
- Multi-dimensional metrics
- Cost calculation
- Model comparison
- Prometheus export
- Edge cases
"""
#  SPDX-License-Identifier: Apache-2.0

import time

import pytest

from fakeai.model_metrics import (
    DEFAULT_PRICING,
    MODEL_PRICING,
    ModelMetricsTracker,
    ModelStats,
)


@pytest.fixture
def tracker():
    """Create a fresh ModelMetricsTracker instance for each test."""
    # Reset the singleton
    ModelMetricsTracker._instance = None
    return ModelMetricsTracker()


class TestBasicTracking:
    """Test basic tracking functionality."""

    def test_track_single_request(self, tracker):
        """Test tracking a single request."""
        tracker.track_request(
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=250.0,
        )

        stats = tracker.get_model_stats("openai/gpt-oss-120b")
        assert stats["request_count"] == 1
        assert stats["tokens"]["prompt"] == 100
        assert stats["tokens"]["completion"] == 50
        assert stats["tokens"]["total"] == 150
        assert stats["latency"]["avg_ms"] == 250.0

    def test_track_multiple_requests_same_model(self, tracker):
        """Test tracking multiple requests for the same model."""
        for i in range(5):
            tracker.track_request(
                model="gpt-4",
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
                latency_ms=200.0 + i * 10,
            )

        stats = tracker.get_model_stats("gpt-4")
        assert stats["request_count"] == 5
        assert stats["tokens"]["total"] == 750  # (100 + 50) * 5
        assert stats["latency"]["avg_ms"] == 220.0  # (200+210+220+230+240)/5

    def test_tracks_multiple_models_separately(self, tracker):
        """Test that different models are tracked separately."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=200.0,
        )

        tracker.track_request(
            model="gpt-3.5-turbo",
            endpoint="/v1/chat/completions",
            prompt_tokens=200,
            completion_tokens=100,
            latency_ms=150.0,
        )

        stats_gpt4 = tracker.get_model_stats("gpt-4")
        stats_gpt35 = tracker.get_model_stats("gpt-3.5-turbo")

        assert stats_gpt4["request_count"] == 1
        assert stats_gpt4["tokens"]["total"] == 150

        assert stats_gpt35["request_count"] == 1
        assert stats_gpt35["tokens"]["total"] == 300

    def test_track_tokens_only(self, tracker):
        """Test tracking tokens without full request."""
        tracker.track_tokens(model="gpt-4", prompt_tokens=500, completion_tokens=200)

        stats = tracker.get_model_stats("gpt-4")
        assert stats["tokens"]["prompt"] == 500
        assert stats["tokens"]["completion"] == 200
        assert stats["tokens"]["total"] == 700

    def test_track_latency_only(self, tracker):
        """Test tracking latency separately."""
        tracker.track_latency(model="gpt-4", latency_ms=300.0)
        tracker.track_latency(model="gpt-4", latency_ms=400.0)

        stats = tracker.get_model_stats("gpt-4")
        assert len(stats["latency"]) > 0

    def test_track_errors(self, tracker):
        """Test error tracking."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=0,
            latency_ms=100.0,
            error=True,
        )

        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=200.0,
            error=False,
        )

        stats = tracker.get_model_stats("gpt-4")
        assert stats["request_count"] == 2
        assert stats["errors"]["count"] == 1
        assert stats["errors"]["rate_percent"] == 50.0


class TestMultiDimensionalMetrics:
    """Test multi-dimensional metric tracking."""

    def test_track_by_endpoint(self, tracker):
        """Test tracking requests by endpoint."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
        )

        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/completions",
            prompt_tokens=100,
            completion_tokens=50,
        )

        stats = tracker.get_model_stats("gpt-4")
        assert stats["endpoints"]["/v1/chat/completions"] == 1
        assert stats["endpoints"]["/v1/completions"] == 1

    def test_track_by_user(self, tracker):
        """Test tracking requests by user/API key."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
            user="user-1",
        )

        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=200,
            completion_tokens=100,
            user="user-2",
        )

        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=150,
            completion_tokens=75,
            user="user-1",
        )

        stats = tracker.get_model_stats("gpt-4")
        assert stats["users"]["user-1"] == 2
        assert stats["users"]["user-2"] == 1

    def test_model_endpoint_2d_tracking(self, tracker):
        """Test 2D model-endpoint tracking."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
        )

        tracker.track_request(
            model="gpt-3.5-turbo",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
        )

        multi_stats = tracker.get_multi_dimensional_stats()
        assert "gpt-4" in multi_stats["model_by_endpoint"]
        assert "gpt-3.5-turbo" in multi_stats["model_by_endpoint"]

    def test_model_user_2d_tracking(self, tracker):
        """Test 2D model-user tracking."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
            user="user-1",
        )

        multi_stats = tracker.get_multi_dimensional_stats()
        assert "gpt-4" in multi_stats["model_by_user"]
        assert "user-1" in multi_stats["model_by_user"]["gpt-4"]

    def test_model_time_tracking(self, tracker):
        """Test time-based tracking."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
        )

        multi_stats = tracker.get_multi_dimensional_stats()
        assert "gpt-4" in multi_stats["model_by_time_24h"]


class TestCostTracking:
    """Test cost calculation and tracking."""

    def test_cost_calculation_gpt4(self, tracker):
        """Test cost calculation for GPT-4."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        stats = tracker.get_model_stats("gpt-4")
        # GPT-4: $0.03/1K input, $0.06/1K output
        # Cost = (1000/1000)*0.03 + (500/1000)*0.06 = 0.03 + 0.03 = 0.06
        expected_cost = 0.06
        assert abs(stats["cost"]["total_usd"] - expected_cost) < 0.001

    def test_cost_calculation_gpt35(self, tracker):
        """Test cost calculation for GPT-3.5."""
        tracker.track_request(
            model="gpt-3.5-turbo",
            endpoint="/v1/chat/completions",
            prompt_tokens=2000,
            completion_tokens=1000,
        )

        stats = tracker.get_model_stats("gpt-3.5-turbo")
        # GPT-3.5: $0.0005/1K input, $0.0015/1K output
        # Cost = (2000/1000)*0.0005 + (1000/1000)*0.0015 = 0.001 + 0.0015 = 0.0025
        expected_cost = 0.0025
        assert abs(stats["cost"]["total_usd"] - expected_cost) < 0.0001

    def test_cost_per_request(self, tracker):
        """Test per-request cost calculation."""
        for _ in range(10):
            tracker.track_request(
                model="gpt-4",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        stats = tracker.get_model_stats("gpt-4")
        assert abs(stats["cost"]["per_request_usd"] - 0.06) < 0.001

    def test_get_cost_by_model(self, tracker):
        """Test getting costs for all models."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        tracker.track_request(
            model="gpt-3.5-turbo",
            endpoint="/v1/chat/completions",
            prompt_tokens=2000,
            completion_tokens=1000,
        )

        costs = tracker.get_cost_by_model()
        assert "gpt-4" in costs
        assert "gpt-3.5-turbo" in costs
        assert abs(costs["gpt-4"] - 0.06) < 0.001
        assert abs(costs["gpt-3.5-turbo"] - 0.0025) < 0.0001

    def test_cost_calculation_unknown_model(self, tracker):
        """Test cost calculation for unknown model uses default pricing."""
        tracker.track_request(
            model="unknown-model",
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        stats = tracker.get_model_stats("unknown-model")
        # Default: $0.001/1K input, $0.002/1K output
        # Cost = (1000/1000)*0.001 + (500/1000)*0.002 = 0.001 + 0.001 = 0.002
        expected_cost = 0.002
        assert abs(stats["cost"]["total_usd"] - expected_cost) < 0.0001


class TestModelComparison:
    """Test model comparison functionality."""

    def test_model_comparison(self, tracker):
        """Test comparing two models."""
        # Track requests for model 1
        for _ in range(10):
            tracker.track_request(
                model="gpt-4",
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
                latency_ms=200.0,
            )

        # Track requests for model 2
        for _ in range(5):
            tracker.track_request(
                model="gpt-3.5-turbo",
                endpoint="/v1/chat/completions",
                prompt_tokens=200,
                completion_tokens=100,
                latency_ms=150.0,
            )

        comparison = tracker.compare_models("gpt-4", "gpt-3.5-turbo")

        assert comparison["model1"] == "gpt-4"
        assert comparison["model2"] == "gpt-3.5-turbo"
        assert comparison["comparison"]["request_count"]["model1"] == 10
        assert comparison["comparison"]["request_count"]["model2"] == 5
        assert comparison["comparison"]["avg_latency_ms"]["model1"] == 200.0
        assert comparison["comparison"]["avg_latency_ms"]["model2"] == 150.0

    def test_model_comparison_winner(self, tracker):
        """Test winner determination in model comparison."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=300.0,
        )

        tracker.track_request(
            model="gpt-3.5-turbo",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=150.0,
        )

        comparison = tracker.compare_models("gpt-4", "gpt-3.5-turbo")

        # GPT-3.5 should win on latency and cost
        assert comparison["winner"]["latency"] == "gpt-3.5-turbo"
        assert comparison["winner"]["cost_efficiency"] == "gpt-3.5-turbo"

    def test_model_comparison_nonexistent_model(self, tracker):
        """Test comparison with non-existent model."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
        )

        comparison = tracker.compare_models("gpt-4", "nonexistent-model")
        assert "error" in comparison


class TestLatencyMetrics:
    """Test latency tracking and percentiles."""

    def test_latency_percentiles(self, tracker):
        """Test latency percentile calculation."""
        # Track requests with varying latencies
        latencies = [100, 150, 200, 250, 300, 350, 400, 450, 500, 1000]
        for lat in latencies:
            tracker.track_request(
                model="gpt-4",
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
                latency_ms=lat,
            )

        stats = tracker.get_model_stats("gpt-4")
        percentiles = stats["latency"]

        assert percentiles["p50"] > 0
        assert percentiles["p90"] > percentiles["p50"]
        assert percentiles["p99"] > percentiles["p90"]

    def test_average_latency(self, tracker):
        """Test average latency calculation."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=100.0,
        )

        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=200.0,
        )

        stats = tracker.get_model_stats("gpt-4")
        assert stats["latency"]["avg_ms"] == 150.0


class TestPrometheusExport:
    """Test Prometheus metrics export."""

    def test_prometheus_export_with_labels(self, tracker):
        """Test Prometheus export includes model labels."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=200.0,
        )

        prometheus = tracker.get_prometheus_metrics()

        # Check for model labels
        assert 'model="gpt-4"' in prometheus
        assert "fakeai_model_requests_total" in prometheus
        assert "fakeai_model_tokens_total" in prometheus
        assert "fakeai_model_latency_milliseconds" in prometheus
        assert "fakeai_model_cost_usd_total" in prometheus

    def test_prometheus_export_multiple_models(self, tracker):
        """Test Prometheus export with multiple models."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
        )

        tracker.track_request(
            model="gpt-3.5-turbo",
            endpoint="/v1/chat/completions",
            prompt_tokens=200,
            completion_tokens=100,
        )

        prometheus = tracker.get_prometheus_metrics()

        assert 'model="gpt-4"' in prometheus
        assert 'model="gpt-3.5-turbo"' in prometheus

    def test_prometheus_export_endpoint_labels(self, tracker):
        """Test Prometheus export includes endpoint labels."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
        )

        prometheus = tracker.get_prometheus_metrics()

        assert 'endpoint="/v1/chat/completions"' in prometheus
        assert "fakeai_model_endpoint_requests_total" in prometheus


class TestModelRanking:
    """Test model ranking functionality."""

    def test_ranking_by_request_count(self, tracker):
        """Test ranking models by request count."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
        )

        for _ in range(5):
            tracker.track_request(
                model="gpt-3.5-turbo",
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
            )

        for _ in range(3):
            tracker.track_request(
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
            )

        ranking = tracker.get_model_ranking(metric="request_count", limit=3)

        assert len(ranking) == 3
        assert ranking[0]["model"] == "gpt-3.5-turbo"
        assert ranking[1]["model"] == "gpt-4o"
        assert ranking[2]["model"] == "gpt-4"

    def test_ranking_by_cost(self, tracker):
        """Test ranking models by cost."""
        # GPT-4 (expensive)
        for _ in range(2):
            tracker.track_request(
                model="gpt-4",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        # GPT-3.5 (cheap)
        for _ in range(10):
            tracker.track_request(
                model="gpt-3.5-turbo",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )

        ranking = tracker.get_model_ranking(metric="cost", limit=2)

        # GPT-4 should be first despite fewer requests (more expensive per token)
        assert ranking[0]["model"] == "gpt-4"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_get_stats_nonexistent_model(self, tracker):
        """Test getting stats for non-existent model."""
        stats = tracker.get_model_stats("nonexistent-model")
        assert stats["request_count"] == 0
        assert "error" in stats

    def test_zero_requests(self, tracker):
        """Test metrics with zero requests."""
        stats = tracker.get_model_stats("gpt-4")
        assert stats["request_count"] == 0

    def test_get_all_models_empty(self, tracker):
        """Test getting all models when none exist."""
        all_stats = tracker.get_all_models_stats()
        assert all_stats == {}

    def test_reset_stats(self, tracker):
        """Test resetting statistics."""
        tracker.track_request(
            model="gpt-4",
            endpoint="/v1/chat/completions",
            prompt_tokens=100,
            completion_tokens=50,
        )

        tracker.reset_stats()
        all_stats = tracker.get_all_models_stats()
        assert all_stats == {}

    def test_thread_safety(self, tracker):
        """Test thread-safe tracking."""
        import threading

        def track_requests():
            for _ in range(10):  # Reduced for faster testing
                tracker.track_request(
                    model="gpt-4",
                    endpoint="/v1/chat/completions",
                    prompt_tokens=100,
                    completion_tokens=50,
                    latency_ms=200.0,
                )

        threads = [
            threading.Thread(target=track_requests) for _ in range(3)
        ]  # Reduced for faster testing
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = tracker.get_model_stats("gpt-4")
        assert stats["request_count"] == 30  # 10 * 3


class TestModelStats:
    """Test ModelStats dataclass directly."""

    def test_model_stats_initialization(self):
        """Test ModelStats initialization."""
        stats = ModelStats(model="gpt-4")
        assert stats.model == "gpt-4"
        assert stats.request_count == 0
        assert stats.total_tokens == 0

    def test_model_stats_add_request(self):
        """Test adding request to ModelStats."""
        stats = ModelStats(model="gpt-4")
        stats.add_request(
            prompt_tokens=100,
            completion_tokens=50,
            latency_ms=200.0,
            endpoint="/v1/chat/completions",
            user="user-1",
        )

        assert stats.request_count == 1
        assert stats.total_prompt_tokens == 100
        assert stats.total_completion_tokens == 50
        assert stats.total_tokens == 150

    def test_model_stats_uptime(self):
        """Test uptime calculation."""
        stats = ModelStats(model="gpt-4")

        stats.add_request(100, 50, 100.0)
        time.sleep(0.1)
        stats.add_request(100, 50, 100.0)

        uptime = stats.get_uptime_seconds()
        assert uptime >= 0.1
        assert uptime < 1.0  # Should be less than 1 second


class TestPricingConfiguration:
    """Test pricing configuration."""

    def test_pricing_for_all_major_models(self):
        """Test that pricing exists for major models."""
        major_models = [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-3.5-turbo",
            "openai/gpt-oss-120b",
            "deepseek-v3",
            "mixtral-8x7b",
        ]

        for model in major_models:
            assert model in MODEL_PRICING
            assert "input" in MODEL_PRICING[model]
            assert "output" in MODEL_PRICING[model]

    def test_default_pricing_exists(self):
        """Test that default pricing exists."""
        assert "input" in DEFAULT_PRICING
        assert "output" in DEFAULT_PRICING
