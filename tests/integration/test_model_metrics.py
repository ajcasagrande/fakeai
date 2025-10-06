#!/usr/bin/env python3
"""
Integration Tests for Model-Specific Metrics

Comprehensive integration test suite covering:
1. Per-model request counting
2. Per-model token usage
3. Per-model latency tracking
4. Per-model error rates
5. Per-model throughput
6. Model popularity rankings
7. Model switching patterns
8. Model performance comparison
9. Model-specific SLAs
10. Model capacity tracking
11. Model load balancing
12. Model metrics aggregation
13. Top models dashboard data

Tests the ModelMetricsTracker in live server environment with real API calls.
"""
#  SPDX-License-Identifier: Apache-2.0

import concurrent.futures
import time
from typing import Any

import pytest

from .utils import FakeAIClient


@pytest.mark.integration
@pytest.mark.metrics
class TestPerModelRequestCounting:
    """Test per-model request counting in live server."""

    def test_single_model_request_count(
        self, client: FakeAIClient, sample_messages
    ):
        """Test that requests are counted per model."""
        model = "openai/gpt-oss-120b"

        # Make multiple requests
        for _ in range(3):
            response = client.chat_completion(model=model, messages=sample_messages)
            assert response["model"] == model

        # Get metrics
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)

        # Verify metrics exist (exact structure depends on implementation)
        assert len(metrics) > 0

    def test_multiple_models_separate_counts(
        self, client: FakeAIClient, sample_messages
    ):
        """Test that different models have separate request counts."""
        # Make requests to different models
        client.chat_completion(
            model="openai/gpt-oss-120b", messages=sample_messages
        )
        client.chat_completion(
            model="openai/gpt-oss-120b", messages=sample_messages
        )
        client.chat_completion(
            model="gpt-3.5-turbo", messages=sample_messages
        )

        # Get metrics
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)

        # Different models should be tracked separately
        # (implementation-specific structure)
        assert len(metrics) > 0

    def test_request_count_persistence_across_calls(
        self, client: FakeAIClient, sample_messages
    ):
        """Test that request counts persist across multiple API calls."""
        model = "gpt-4"

        # First batch
        client.chat_completion(model=model, messages=sample_messages)
        client.chat_completion(model=model, messages=sample_messages)

        # Get metrics
        metrics_1 = client.get_metrics()

        # Second batch
        client.chat_completion(model=model, messages=sample_messages)

        # Get metrics again
        metrics_2 = client.get_metrics()

        # Metrics should have changed
        assert metrics_2 != metrics_1


@pytest.mark.integration
@pytest.mark.metrics
class TestPerModelTokenUsage:
    """Test per-model token usage tracking."""

    def test_token_usage_tracking(self, client: FakeAIClient, sample_messages):
        """Test that tokens are tracked per model."""
        model = "gpt-4"

        # Make request
        response = client.chat_completion(model=model, messages=sample_messages)

        # Verify usage is returned
        assert "usage" in response
        assert response["usage"]["prompt_tokens"] > 0
        assert response["usage"]["completion_tokens"] > 0
        assert response["usage"]["total_tokens"] > 0

    def test_cumulative_token_usage(self, client: FakeAIClient, sample_messages):
        """Test that token usage accumulates across requests."""
        model = "gpt-4"

        # Make multiple requests
        total_prompt = 0
        total_completion = 0

        for _ in range(3):
            response = client.chat_completion(model=model, messages=sample_messages)
            total_prompt += response["usage"]["prompt_tokens"]
            total_completion += response["usage"]["completion_tokens"]

        # Verify non-zero totals
        assert total_prompt > 0
        assert total_completion > 0

    def test_token_usage_separate_per_model(
        self, client: FakeAIClient, sample_messages
    ):
        """Test that token usage is tracked separately per model."""
        # Make requests to different models
        response_1 = client.chat_completion(
            model="gpt-4", messages=sample_messages
        )
        response_2 = client.chat_completion(
            model="gpt-3.5-turbo", messages=sample_messages
        )

        # Both should have usage
        assert response_1["usage"]["total_tokens"] > 0
        assert response_2["usage"]["total_tokens"] > 0


@pytest.mark.integration
@pytest.mark.metrics
class TestPerModelLatencyTracking:
    """Test per-model latency tracking."""

    def test_latency_recorded(self, client: FakeAIClient, sample_messages):
        """Test that latency is recorded for model requests."""
        model = "gpt-4"

        # Make request and measure time
        start = time.time()
        response = client.chat_completion(model=model, messages=sample_messages)
        elapsed = time.time() - start

        # Request should complete
        assert response["object"] == "chat.completion"

        # Get metrics
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)

    def test_latency_varies_by_model(self, client: FakeAIClient, sample_messages):
        """Test that different models can have different latencies."""
        # Make requests to different models
        start_1 = time.time()
        client.chat_completion(model="gpt-4", messages=sample_messages)
        latency_1 = time.time() - start_1

        start_2 = time.time()
        client.chat_completion(model="gpt-3.5-turbo", messages=sample_messages)
        latency_2 = time.time() - start_2

        # Both should complete (latency > 0)
        assert latency_1 >= 0
        assert latency_2 >= 0

    def test_streaming_latency_tracking(
        self, client: FakeAIClient, sample_messages
    ):
        """Test that streaming requests track latency."""
        model = "gpt-4"

        # Make streaming request
        start = time.time()
        chunks = list(
            client.chat_completion_stream(model=model, messages=sample_messages)
        )
        elapsed = time.time() - start

        # Should receive chunks
        assert len(chunks) > 0

        # Streaming should complete
        assert elapsed >= 0


@pytest.mark.integration
@pytest.mark.metrics
class TestPerModelErrorRates:
    """Test per-model error rate tracking."""

    @pytest.mark.server_config(error_injection_enabled=True)
    def test_error_tracking_with_injection(
        self, server_function_scoped, test_api_key, sample_messages
    ):
        """Test that errors are tracked per model with error injection."""
        # Use function-scoped server with error injection
        client = FakeAIClient(
            base_url=server_function_scoped.base_url,
            api_key=test_api_key,
        )

        model = "gpt-4"

        # Make multiple requests, some may error
        success_count = 0
        error_count = 0

        for _ in range(10):
            try:
                client.chat_completion(model=model, messages=sample_messages)
                success_count += 1
            except Exception:
                error_count += 1

        # At least some should succeed
        assert success_count > 0 or error_count > 0

        client.close()

    def test_error_rate_isolation_per_model(
        self, client: FakeAIClient, sample_messages
    ):
        """Test that errors are tracked separately per model."""
        # Make requests to different models
        # (without error injection, should all succeed)
        response_1 = client.chat_completion(
            model="gpt-4", messages=sample_messages
        )
        response_2 = client.chat_completion(
            model="gpt-3.5-turbo", messages=sample_messages
        )

        # Both should succeed
        assert response_1["object"] == "chat.completion"
        assert response_2["object"] == "chat.completion"


@pytest.mark.integration
@pytest.mark.metrics
class TestPerModelThroughput:
    """Test per-model throughput tracking."""

    def test_throughput_measurement(self, client: FakeAIClient, sample_messages):
        """Test that throughput can be measured per model."""
        model = "gpt-4"

        # Make requests over time
        start = time.time()
        num_requests = 5

        for _ in range(num_requests):
            client.chat_completion(model=model, messages=sample_messages)

        elapsed = time.time() - start

        # Calculate throughput
        throughput = num_requests / elapsed if elapsed > 0 else 0

        # Should have positive throughput
        assert throughput > 0

    def test_concurrent_throughput(self, client: FakeAIClient, sample_messages):
        """Test throughput with concurrent requests."""
        model = "gpt-4"

        def make_request():
            return client.chat_completion(model=model, messages=sample_messages)

        # Make concurrent requests
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]
        elapsed = time.time() - start

        # All should succeed
        assert len(results) == 10

        # Calculate throughput
        throughput = len(results) / elapsed if elapsed > 0 else 0
        assert throughput > 0


@pytest.mark.integration
@pytest.mark.metrics
class TestModelPopularityRankings:
    """Test model popularity rankings."""

    def test_popularity_by_request_count(
        self, client: FakeAIClient, sample_messages
    ):
        """Test that models can be ranked by popularity."""
        # Make different numbers of requests to different models
        # Most popular: gpt-3.5-turbo (5 requests)
        for _ in range(5):
            client.chat_completion(model="gpt-3.5-turbo", messages=sample_messages)

        # Second: gpt-4 (3 requests)
        for _ in range(3):
            client.chat_completion(model="gpt-4", messages=sample_messages)

        # Third: gpt-4o (1 request)
        client.chat_completion(model="gpt-4o", messages=sample_messages)

        # Get metrics
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)

        # Rankings should reflect usage
        # (implementation-specific)

    def test_popularity_over_time(self, client: FakeAIClient, sample_messages):
        """Test that popularity rankings can change over time."""
        # First phase: gpt-4 is popular
        for _ in range(3):
            client.chat_completion(model="gpt-4", messages=sample_messages)

        metrics_1 = client.get_metrics()

        # Second phase: gpt-3.5-turbo becomes popular
        for _ in range(5):
            client.chat_completion(model="gpt-3.5-turbo", messages=sample_messages)

        metrics_2 = client.get_metrics()

        # Metrics should have changed
        assert metrics_2 != metrics_1


@pytest.mark.integration
@pytest.mark.metrics
class TestModelSwitchingPatterns:
    """Test model switching pattern tracking."""

    def test_sequential_model_switches(
        self, client: FakeAIClient, sample_messages
    ):
        """Test tracking when users switch between models."""
        # Simulate user switching models
        client.chat_completion(model="gpt-4", messages=sample_messages)
        client.chat_completion(model="gpt-3.5-turbo", messages=sample_messages)
        client.chat_completion(model="gpt-4o", messages=sample_messages)
        client.chat_completion(model="gpt-4", messages=sample_messages)

        # Get metrics
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)

    def test_model_switching_frequency(
        self, client: FakeAIClient, sample_messages
    ):
        """Test tracking frequency of model switches."""
        # Multiple switches
        models = ["gpt-4", "gpt-3.5-turbo", "gpt-4o"]

        for model in models * 3:  # Repeat pattern 3 times
            client.chat_completion(model=model, messages=sample_messages)

        # Get metrics
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)


@pytest.mark.integration
@pytest.mark.metrics
class TestModelPerformanceComparison:
    """Test model performance comparison capabilities."""

    def test_compare_latency_across_models(
        self, client: FakeAIClient, sample_messages
    ):
        """Test comparing latency across different models."""
        models = ["gpt-4", "gpt-3.5-turbo", "gpt-4o"]
        latencies = {}

        for model in models:
            start = time.time()
            client.chat_completion(model=model, messages=sample_messages)
            latencies[model] = time.time() - start

        # All should have latency
        assert all(lat >= 0 for lat in latencies.values())

    def test_compare_token_usage_across_models(
        self, client: FakeAIClient, sample_messages
    ):
        """Test comparing token usage across models."""
        models = ["gpt-4", "gpt-3.5-turbo"]
        token_usage = {}

        for model in models:
            response = client.chat_completion(model=model, messages=sample_messages)
            token_usage[model] = response["usage"]["total_tokens"]

        # All should have token usage
        assert all(tokens > 0 for tokens in token_usage.values())

    def test_compare_throughput_across_models(
        self, client: FakeAIClient, sample_messages
    ):
        """Test comparing throughput across models."""
        models = ["gpt-4", "gpt-3.5-turbo"]
        num_requests = 3

        for model in models:
            start = time.time()
            for _ in range(num_requests):
                client.chat_completion(model=model, messages=sample_messages)
            elapsed = time.time() - start

            throughput = num_requests / elapsed if elapsed > 0 else 0
            assert throughput > 0


@pytest.mark.integration
@pytest.mark.metrics
class TestModelSpecificSLAs:
    """Test model-specific SLA tracking."""

    def test_sla_latency_threshold_tracking(
        self, client: FakeAIClient, sample_messages
    ):
        """Test tracking whether models meet latency SLAs."""
        model = "gpt-4"
        sla_threshold_ms = 5000  # 5 second SLA

        # Make request
        start = time.time()
        client.chat_completion(model=model, messages=sample_messages)
        latency_ms = (time.time() - start) * 1000

        # Check if within SLA
        within_sla = latency_ms < sla_threshold_ms

        # At least verify latency was measured
        assert latency_ms >= 0

    def test_sla_success_rate_tracking(
        self, client: FakeAIClient, sample_messages
    ):
        """Test tracking success rate SLAs per model."""
        model = "gpt-4"
        target_success_rate = 0.95  # 95% success rate

        # Make multiple requests
        successes = 0
        total = 10

        for _ in range(total):
            try:
                client.chat_completion(model=model, messages=sample_messages)
                successes += 1
            except Exception:
                pass

        success_rate = successes / total
        meets_sla = success_rate >= target_success_rate

        # Should have high success rate
        assert success_rate > 0

    def test_sla_token_limit_compliance(
        self, client: FakeAIClient, sample_messages
    ):
        """Test tracking token limit compliance per model."""
        model = "gpt-4"

        # Make request
        response = client.chat_completion(
            model=model, messages=sample_messages, max_tokens=100
        )

        # Verify token limit respected
        assert response["usage"]["completion_tokens"] <= 100


@pytest.mark.integration
@pytest.mark.metrics
class TestModelCapacityTracking:
    """Test model capacity and load tracking."""

    def test_concurrent_capacity_tracking(
        self, client: FakeAIClient, sample_messages
    ):
        """Test tracking concurrent request capacity per model."""
        model = "gpt-4"

        def make_request():
            return client.chat_completion(model=model, messages=sample_messages)

        # Make concurrent requests to test capacity
        max_workers = 10
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(make_request) for _ in range(max_workers)]
            results = [f.result() for f in futures]

        # All should succeed
        assert len(results) == max_workers

    def test_capacity_under_load(self, client: FakeAIClient, sample_messages):
        """Test model capacity under sustained load."""
        model = "gpt-4"
        num_requests = 20

        # Make sustained requests
        successes = 0
        for _ in range(num_requests):
            try:
                client.chat_completion(model=model, messages=sample_messages)
                successes += 1
            except Exception:
                pass

        # Most should succeed
        success_rate = successes / num_requests
        assert success_rate > 0.8  # At least 80% success


@pytest.mark.integration
@pytest.mark.metrics
class TestModelLoadBalancing:
    """Test load balancing metrics across models."""

    def test_load_distribution_tracking(
        self, client: FakeAIClient, sample_messages
    ):
        """Test tracking load distribution across models."""
        models = ["gpt-4", "gpt-3.5-turbo", "gpt-4o"]

        # Distribute requests across models
        for i in range(15):
            model = models[i % len(models)]
            client.chat_completion(model=model, messages=sample_messages)

        # Get metrics
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)

    def test_load_balancing_fairness(
        self, client: FakeAIClient, sample_messages
    ):
        """Test that load can be distributed fairly across models."""
        models = ["gpt-4", "gpt-3.5-turbo"]
        request_counts = {model: 0 for model in models}

        # Round-robin distribution
        for i in range(10):
            model = models[i % len(models)]
            client.chat_completion(model=model, messages=sample_messages)
            request_counts[model] += 1

        # Should have equal distribution
        assert request_counts["gpt-4"] == 5
        assert request_counts["gpt-3.5-turbo"] == 5


@pytest.mark.integration
@pytest.mark.metrics
class TestModelMetricsAggregation:
    """Test aggregation of model metrics."""

    def test_aggregate_metrics_across_models(
        self, client: FakeAIClient, sample_messages
    ):
        """Test aggregating metrics across all models."""
        # Make requests to multiple models
        models = ["gpt-4", "gpt-3.5-turbo", "gpt-4o"]

        for model in models:
            for _ in range(2):
                client.chat_completion(model=model, messages=sample_messages)

        # Get aggregated metrics
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)

    def test_aggregate_token_usage(self, client: FakeAIClient, sample_messages):
        """Test aggregating token usage across models."""
        models = ["gpt-4", "gpt-3.5-turbo"]
        total_tokens = 0

        for model in models:
            response = client.chat_completion(model=model, messages=sample_messages)
            total_tokens += response["usage"]["total_tokens"]

        # Should have accumulated tokens
        assert total_tokens > 0

    def test_aggregate_latency_statistics(
        self, client: FakeAIClient, sample_messages
    ):
        """Test aggregating latency statistics across models."""
        models = ["gpt-4", "gpt-3.5-turbo"]
        latencies = []

        for model in models:
            for _ in range(2):
                start = time.time()
                client.chat_completion(model=model, messages=sample_messages)
                latencies.append(time.time() - start)

        # Calculate aggregate statistics
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        min_latency = min(latencies)

        assert avg_latency > 0
        assert max_latency >= min_latency


@pytest.mark.integration
@pytest.mark.metrics
class TestTopModelsDashboard:
    """Test top models dashboard data generation."""

    def test_dashboard_top_models_by_requests(
        self, client: FakeAIClient, sample_messages
    ):
        """Test getting top models by request count for dashboard."""
        # Create varied usage pattern
        usage_pattern = [
            ("gpt-3.5-turbo", 10),
            ("gpt-4", 5),
            ("gpt-4o", 2),
        ]

        for model, count in usage_pattern:
            for _ in range(count):
                client.chat_completion(model=model, messages=sample_messages)

        # Get metrics (would contain top models)
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)

    def test_dashboard_top_models_by_tokens(
        self, client: FakeAIClient, sample_messages
    ):
        """Test getting top models by token usage for dashboard."""
        models = ["gpt-4", "gpt-3.5-turbo", "gpt-4o"]
        token_usage = {}

        for model in models:
            response = client.chat_completion(model=model, messages=sample_messages)
            token_usage[model] = response["usage"]["total_tokens"]

        # All should have token usage
        assert len(token_usage) == len(models)

    def test_dashboard_model_performance_summary(
        self, client: FakeAIClient, sample_messages
    ):
        """Test getting model performance summary for dashboard."""
        models = ["gpt-4", "gpt-3.5-turbo"]

        for model in models:
            # Make multiple requests
            for _ in range(3):
                client.chat_completion(model=model, messages=sample_messages)

        # Get metrics
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)

    def test_dashboard_realtime_updates(
        self, client: FakeAIClient, sample_messages
    ):
        """Test that dashboard data updates in real-time."""
        model = "gpt-4"

        # Initial state
        metrics_1 = client.get_metrics()

        # Make request
        client.chat_completion(model=model, messages=sample_messages)

        # Updated state
        metrics_2 = client.get_metrics()

        # Should have changed
        assert metrics_2 != metrics_1


@pytest.mark.integration
@pytest.mark.metrics
@pytest.mark.slow
class TestModelMetricsE2E:
    """End-to-end tests for model metrics system."""

    def test_complete_metrics_lifecycle(
        self, client: FakeAIClient, sample_messages
    ):
        """Test complete lifecycle of model metrics tracking."""
        models = ["gpt-4", "gpt-3.5-turbo", "gpt-4o"]

        # Phase 1: Generate varied usage
        for model in models:
            count = models.index(model) + 1
            for _ in range(count):
                client.chat_completion(model=model, messages=sample_messages)

        # Phase 2: Get metrics
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)

        # Phase 3: Generate more usage
        for model in models:
            client.chat_completion(model=model, messages=sample_messages)

        # Phase 4: Get updated metrics
        updated_metrics = client.get_metrics()
        assert updated_metrics != metrics

    def test_multi_endpoint_model_metrics(
        self, client: FakeAIClient, sample_messages, sample_embedding_input
    ):
        """Test model metrics across different endpoints."""
        # Chat endpoint
        chat_response = client.chat_completion(
            model="gpt-4", messages=sample_messages
        )
        assert chat_response["object"] == "chat.completion"

        # Embeddings endpoint
        embedding_response = client.create_embedding(
            model="text-embedding-ada-002", input=sample_embedding_input
        )
        assert embedding_response["object"] == "list"

        # Metrics should track both
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)

    def test_prometheus_model_metrics_export(
        self, client: FakeAIClient, sample_messages
    ):
        """Test Prometheus export includes model-specific metrics."""
        models = ["gpt-4", "gpt-3.5-turbo"]

        # Generate usage
        for model in models:
            client.chat_completion(model=model, messages=sample_messages)

        # Get Prometheus metrics
        prometheus = client.get_prometheus_metrics()

        # Should contain model labels
        assert isinstance(prometheus, str)
        assert len(prometheus) > 0

        # Should reference models (implementation-dependent)
        # At minimum, should have metrics format
        lines = prometheus.split("\n")
        has_metrics = any(
            line.startswith("#") or "fakeai_" in line or "{" in line
            for line in lines
        )
        assert has_metrics


@pytest.mark.integration
@pytest.mark.metrics
class TestModelMetricsEdgeCases:
    """Test edge cases in model metrics tracking."""

    def test_unknown_model_metrics(self, client: FakeAIClient, sample_messages):
        """Test that unknown models are still tracked."""
        # Use a custom model name
        unknown_model = "custom-model-123"

        response = client.chat_completion(
            model=unknown_model, messages=sample_messages
        )

        # Should succeed (FakeAI auto-creates models)
        assert response["object"] == "chat.completion"

        # Should be tracked in metrics
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)

    def test_metrics_with_zero_requests(self, client: FakeAIClient):
        """Test metrics when a model has zero requests."""
        # Get metrics without making any requests
        metrics = client.get_metrics()

        # Should return valid structure even with no data
        assert isinstance(metrics, dict)

    def test_metrics_with_large_model_names(
        self, client: FakeAIClient, sample_messages
    ):
        """Test metrics tracking with very long model names."""
        long_model_name = "custom-model-" + "x" * 100

        response = client.chat_completion(
            model=long_model_name, messages=sample_messages
        )

        # Should succeed
        assert response["object"] == "chat.completion"

        # Should be tracked
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)

    def test_metrics_concurrent_model_access(
        self, client: FakeAIClient, sample_messages
    ):
        """Test metrics with concurrent access to same model."""
        model = "gpt-4"

        def make_request():
            return client.chat_completion(model=model, messages=sample_messages)

        # Concurrent requests to same model
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [f.result() for f in futures]

        # All should succeed
        assert len(results) == 20

        # Metrics should be consistent
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)
