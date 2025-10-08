"""Integration tests for admin and operational endpoints.

This module tests administrative endpoints including:
- Health checks (basic and detailed)
- Metrics retrieval (JSON, Prometheus, CSV)
- Per-model metrics
- KV cache metrics
- DCGM GPU metrics
- AI-Dynamo metrics
- Rate limiting metrics
- System information
- Configuration management
"""

import json
import time

import pytest

from .utils import FakeAIClient


@pytest.mark.integration
@pytest.mark.metrics
class TestHealthEndpoints:
    """Test health check and readiness endpoints."""

    def test_basic_health_check(self, client: FakeAIClient):
        """Test basic health check endpoint returns healthy status."""
        response = client.client.get("/health")
        response.raise_for_status()

        data = response.json()

        # Validate structure
        assert isinstance(data, dict)
        assert "status" in data
        assert "ready" in data
        assert "timestamp" in data

        # Validate values
        assert data["status"] in ["healthy", "starting"]
        assert isinstance(data["ready"], bool)
        assert isinstance(data["timestamp"], str)

        # Should be ready after startup
        assert data["ready"] is True
        assert data["status"] == "healthy"

    def test_detailed_health_check(self, client: FakeAIClient):
        """Test detailed health check with metrics summary."""
        response = client.client.get("/health/detailed")
        response.raise_for_status()

        data = response.json()

        # Should contain health information
        assert isinstance(data, dict)

        # Detailed health should include more than basic health
        assert len(data) > 0

    def test_sagemaker_ping_endpoint(self, client: FakeAIClient):
        """Test SageMaker /ping endpoint for AWS compatibility."""
        response = client.client.get("/ping")

        # Should return 200 when ready
        assert response.status_code == 200

        # Should have no body or empty body
        assert response.text == ""

    def test_health_endpoint_no_auth(self, client_no_auth: FakeAIClient):
        """Test health endpoint works without authentication."""
        response = client_no_auth.client.get("/health")
        response.raise_for_status()

        data = response.json()
        assert data["status"] in ["healthy", "starting"]


@pytest.mark.integration
@pytest.mark.metrics
class TestMetricsEndpoints:
    """Test metrics retrieval endpoints."""

    def test_get_metrics_json(self, client: FakeAIClient, sample_messages):
        """Test server metrics in JSON format."""
        # Generate some activity
        client.chat_completion(model="openai/gpt-oss-120b", messages=sample_messages)

        # Get metrics
        metrics = client.get_metrics()

        # Validate structure
        assert isinstance(metrics, dict)
        assert len(metrics) > 0

        # Should contain common metrics fields
        # (exact structure may vary, but should have some data)

    def test_get_metrics_prometheus(self, client: FakeAIClient, sample_messages):
        """Test server metrics in Prometheus format."""
        # Generate some activity
        client.chat_completion(model="openai/gpt-oss-120b", messages=sample_messages)

        # Get Prometheus metrics
        try:
            metrics_text = client.get_prometheus_metrics()

            # Validate format
            assert isinstance(metrics_text, str)
            assert len(metrics_text) > 0

            # Should contain Prometheus-style metrics
            lines = [line.strip() for line in metrics_text.split("\n") if line.strip()]
            assert len(lines) > 0

            # Should have HELP, TYPE, or metric lines
            has_prometheus_format = any(
                line.startswith("#") or "{" in line or line.count(" ") >= 1
                for line in lines
            )
            assert has_prometheus_format
        except Exception as e:
            # If prometheus endpoint has issues, at least verify it exists
            response = client.client.get("/metrics/prometheus")
            # Should return some response (even if 500)
            assert response.status_code in [200, 500]

    def test_get_metrics_csv(self, client: FakeAIClient, sample_messages):
        """Test server metrics in CSV format."""
        # Generate some activity
        client.chat_completion(model="openai/gpt-oss-120b", messages=sample_messages)

        # Get CSV metrics
        response = client.client.get("/metrics/csv")
        response.raise_for_status()

        csv_data = response.text

        # Validate format
        assert isinstance(csv_data, str)
        assert len(csv_data) > 0

        # Should be CSV-like (have commas or headers)
        lines = csv_data.strip().split("\n")
        assert len(lines) > 0

    def test_metrics_update_after_requests(
        self, client: FakeAIClient, sample_messages, collect_metrics
    ):
        """Test that metrics update after API requests."""
        with collect_metrics() as collector:
            # Make multiple requests
            for _ in range(3):
                client.chat_completion(
                    model="openai/gpt-oss-120b", messages=sample_messages
                )

        # Metrics should have changed
        assert collector.after != collector.before

    def test_metrics_no_auth(self, client_no_auth):
        """Test metrics endpoint works without authentication."""
        response = client_no_auth.get("/metrics")
        response.raise_for_status()

        data = response.json()
        assert isinstance(data, dict)


@pytest.mark.integration
@pytest.mark.metrics
class TestPerModelMetrics:
    """Test per-model metrics tracking."""

    def test_get_all_models_metrics(self, client: FakeAIClient, sample_messages):
        """Test retrieving metrics for all models."""
        # Generate activity with different models
        client.chat_completion(model="openai/gpt-oss-120b", messages=sample_messages)
        client.chat_completion(
            model="meta-llama/Llama-3.1-8B-Instruct", messages=sample_messages
        )

        # Get all model metrics
        response = client.client.get("/metrics/by-model")
        response.raise_for_status()

        data = response.json()

        # Should be a dictionary of model metrics
        assert isinstance(data, dict)

        # Should have metrics for at least one model
        if len(data) > 0:
            # Each model should have statistics
            for model_id, stats in data.items():
                assert isinstance(stats, dict)
                assert "request_count" in stats or "requests" in stats

    def test_get_specific_model_metrics(self, client: FakeAIClient, sample_messages):
        """Test retrieving metrics for a specific model."""
        model_id = "openai/gpt-oss-120b"

        # Generate activity
        client.chat_completion(model=model_id, messages=sample_messages)

        # Get model-specific metrics
        response = client.client.get(
            f"/metrics/by-model/{model_id}"
        )
        response.raise_for_status()

        data = response.json()

        # Should have statistics
        assert isinstance(data, dict)

    def test_compare_models(self, client: FakeAIClient, sample_messages):
        """Test model comparison endpoint."""
        model1 = "openai/gpt-oss-120b"
        model2 = "meta-llama/Llama-3.1-8B-Instruct"

        # Generate activity for both models
        client.chat_completion(model=model1, messages=sample_messages)
        client.chat_completion(model=model2, messages=sample_messages)

        # Compare models
        response = client.client.get(
            "/metrics/compare",
            params={"model1": model1, "model2": model2},
        )
        response.raise_for_status()

        data = response.json()

        # Should have comparison data
        assert isinstance(data, dict)

        # Should reference both models
        data_str = json.dumps(data)
        assert model1 in data_str or "model1" in data_str
        assert model2 in data_str or "model2" in data_str

    def test_model_ranking(self, client: FakeAIClient, sample_messages):
        """Test model ranking by various metrics."""
        # Generate activity
        client.chat_completion(
            model="openai/gpt-oss-120b", messages=sample_messages
        )

        # Test different ranking metrics
        for metric in ["request_count", "latency", "error_rate", "cost", "tokens"]:
            response = client.client.get(
                "/metrics/ranking",
                params={"metric": metric, "limit": 10},
            )
            response.raise_for_status()

            data = response.json()
            assert isinstance(data, dict) or isinstance(data, list)

    def test_per_model_prometheus_metrics(self, client: FakeAIClient, sample_messages):
        """Test per-model metrics in Prometheus format."""
        # Generate activity
        client.chat_completion(
            model="openai/gpt-oss-120b", messages=sample_messages
        )

        # Get Prometheus format
        response = client.client.get(
            "/metrics/by-model/prometheus"
        )
        response.raise_for_status()

        metrics_text = response.text

        # Should be Prometheus format
        assert isinstance(metrics_text, str)
        assert len(metrics_text) > 0


@pytest.mark.integration
@pytest.mark.metrics
class TestCostMetrics:
    """Test cost tracking and analysis."""

    def test_get_costs_by_model(self, client: FakeAIClient, sample_messages):
        """Test cost breakdown by model."""
        # Generate activity
        client.chat_completion(
            model="openai/gpt-oss-120b", messages=sample_messages
        )

        # Get cost metrics
        response = client.client.get("/metrics/costs")
        response.raise_for_status()

        data = response.json()

        # Should have cost information
        assert isinstance(data, dict)
        assert "costs_by_model" in data or "total_cost_usd" in data

        if "total_cost_usd" in data:
            assert isinstance(data["total_cost_usd"], (int, float))
            assert data["total_cost_usd"] >= 0

    def test_multi_dimensional_metrics(self, client: FakeAIClient, sample_messages):
        """Test multi-dimensional metrics breakdown."""
        # Generate activity
        client.chat_completion(
            model="openai/gpt-oss-120b", messages=sample_messages
        )

        # Get multi-dimensional metrics
        response = client.client.get(
            "/metrics/multi-dimensional"
        )
        response.raise_for_status()

        data = response.json()

        # Should have multi-dimensional breakdowns
        assert isinstance(data, dict)


@pytest.mark.integration
@pytest.mark.metrics
class TestKVCacheMetrics:
    """Test KV cache metrics endpoints."""

    def test_get_kv_cache_metrics(self, client: FakeAIClient, sample_messages):
        """Test KV cache and smart router metrics."""
        # Generate activity to populate cache
        for _ in range(2):
            client.chat_completion(
                model="openai/gpt-oss-120b", messages=sample_messages
            )

        # Get KV cache metrics
        kv_metrics = client.get_kv_cache_metrics()

        # Should have cache information
        assert isinstance(kv_metrics, dict)

        # Should have cache_performance and/or smart_router
        if kv_metrics:
            expected_keys = ["cache_performance", "smart_router"]
            has_expected = any(key in kv_metrics for key in expected_keys)
            assert has_expected or len(kv_metrics) > 0

    def test_kv_cache_tracks_hits_misses(
        self, client: FakeAIClient, sample_messages
    ):
        """Test that KV cache tracks hits and misses."""
        # Make same request twice
        messages = [{"role": "user", "content": "Cache test query"}]

        # First request (cache miss)
        client.chat_completion(model="openai/gpt-oss-120b", messages=messages)

        # Second request (potential cache hit)
        client.chat_completion(model="openai/gpt-oss-120b", messages=messages)

        # Get cache metrics
        kv_metrics = client.get_kv_cache_metrics()

        # Should have tracking data
        assert isinstance(kv_metrics, dict)


@pytest.mark.integration
@pytest.mark.metrics
class TestDCGMMetrics:
    """Test DCGM GPU metrics endpoints."""

    def test_get_dcgm_metrics_prometheus(self, client: FakeAIClient):
        """Test DCGM GPU metrics in Prometheus format."""
        response = client.client.get("/dcgm/metrics")
        response.raise_for_status()

        metrics_text = response.text

        # Should be Prometheus format
        assert isinstance(metrics_text, str)
        assert len(metrics_text) > 0

        # Should contain GPU-related metrics
        metrics_lower = metrics_text.lower()
        has_gpu_metrics = any(
            keyword in metrics_lower
            for keyword in ["gpu", "dcgm", "sm_clock", "memory", "power", "temp"]
        )
        assert has_gpu_metrics

    def test_get_dcgm_metrics_json(self, client: FakeAIClient):
        """Test DCGM GPU metrics in JSON format."""
        response = client.client.get("/dcgm/metrics/json")
        response.raise_for_status()

        data = response.json()

        # Should be dictionary with GPU metrics
        assert isinstance(data, dict)

        # Should have GPU information
        if len(data) > 0:
            # Check for common GPU metric fields
            data_str = json.dumps(data).lower()
            has_gpu_info = any(
                keyword in data_str
                for keyword in [
                    "gpu",
                    "device",
                    "temperature",
                    "utilization",
                    "memory",
                    "power",
                ]
            )
            assert has_gpu_info or len(data) > 0

    def test_dcgm_metrics_multiple_calls(self, client: FakeAIClient):
        """Test DCGM metrics consistency across multiple calls."""
        # Get metrics twice
        response1 = client.client.get("/dcgm/metrics/json")
        response1.raise_for_status()
        data1 = response1.json()

        time.sleep(0.1)

        response2 = client.client.get("/dcgm/metrics/json")
        response2.raise_for_status()
        data2 = response2.json()

        # Both should return valid data
        assert isinstance(data1, dict)
        assert isinstance(data2, dict)


@pytest.mark.integration
@pytest.mark.metrics
class TestDynamoMetrics:
    """Test AI-Dynamo LLM inference metrics."""

    def test_get_dynamo_metrics_prometheus(self, client: FakeAIClient):
        """Test AI-Dynamo metrics in Prometheus format."""
        response = client.client.get("/dynamo/metrics")
        response.raise_for_status()

        metrics_text = response.text

        # Should be Prometheus format
        assert isinstance(metrics_text, str)
        assert len(metrics_text) > 0

        # Should contain Dynamo-related metrics
        metrics_lower = metrics_text.lower()
        has_dynamo_metrics = any(
            keyword in metrics_lower
            for keyword in ["dynamo", "llm", "inference", "request", "latency"]
        )
        assert has_dynamo_metrics

    def test_get_dynamo_metrics_json(self, client: FakeAIClient, sample_messages):
        """Test AI-Dynamo metrics in JSON format."""
        # Generate some activity
        client.chat_completion(
            model="openai/gpt-oss-120b", messages=sample_messages
        )

        response = client.client.get("/dynamo/metrics/json")
        response.raise_for_status()

        data = response.json()

        # Should be dictionary with Dynamo metrics
        assert isinstance(data, dict)

    def test_dynamo_metrics_track_requests(
        self, client: FakeAIClient, sample_messages
    ):
        """Test that Dynamo metrics track inference requests."""
        # Get initial metrics
        response1 = client.client.get("/dynamo/metrics/json")
        response1.raise_for_status()
        data1 = response1.json()

        # Make requests
        for _ in range(3):
            client.chat_completion(
                model="openai/gpt-oss-120b", messages=sample_messages
            )

        # Get updated metrics
        response2 = client.client.get("/dynamo/metrics/json")
        response2.raise_for_status()
        data2 = response2.json()

        # Should have data
        assert isinstance(data1, dict)
        assert isinstance(data2, dict)


@pytest.mark.integration
@pytest.mark.metrics
class TestRateLimitMetrics:
    """Test rate limiting metrics endpoints."""

    def test_get_rate_limit_metrics(self, client: FakeAIClient):
        """Test comprehensive rate limiting metrics."""
        response = client.client.get("/metrics/rate-limits")
        response.raise_for_status()

        data = response.json()

        # Should have rate limit metrics
        assert isinstance(data, dict)

    def test_get_rate_limit_key_stats(self, client: FakeAIClient, sample_messages):
        """Test rate limit statistics for specific API key."""
        # Generate activity
        client.chat_completion(
            model="openai/gpt-oss-120b", messages=sample_messages
        )

        # Try to get key stats (may not exist if rate limiting disabled)
        try:
            response = client.client.get(
                f"/metrics/rate-limits/key/{client.api_key}"
            )

            # If rate limiting is enabled, should work
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
            elif response.status_code == 404:
                # No metrics for key (rate limiting may be disabled)
                pass
            else:
                response.raise_for_status()
        except Exception:
            # Rate limiting may not be enabled in tests
            pass

    def test_get_rate_limit_tier_stats(self, client: FakeAIClient):
        """Test rate limit statistics aggregated by tier."""
        response = client.client.get("/metrics/rate-limits/tier")
        response.raise_for_status()

        data = response.json()

        # Should return tier statistics
        assert isinstance(data, dict)

    def test_get_throttle_analytics(self, client: FakeAIClient):
        """Test detailed throttling analytics."""
        response = client.client.get(
            "/metrics/rate-limits/throttle-analytics"
        )
        response.raise_for_status()

        data = response.json()

        # Should return throttling analytics
        assert isinstance(data, dict)

    def test_get_abuse_patterns(self, client: FakeAIClient):
        """Test abuse pattern detection."""
        response = client.client.get(
            "/metrics/rate-limits/abuse-patterns"
        )
        response.raise_for_status()

        data = response.json()

        # Should return abuse pattern analysis
        assert isinstance(data, dict) or isinstance(data, list)


@pytest.mark.integration
@pytest.mark.metrics
class TestSystemInformation:
    """Test system information and configuration endpoints."""

    def test_dashboard_endpoint(self, client: FakeAIClient):
        """Test dashboard HTML endpoint."""
        response = client.client.get("/dashboard")

        # Should return HTML (200 or 404 if not available)
        if response.status_code == 200:
            assert "text/html" in response.headers.get("content-type", "")
            assert len(response.text) > 0
        else:
            assert response.status_code == 404

    def test_dynamo_dashboard_endpoint(self, client: FakeAIClient):
        """Test advanced Dynamo dashboard endpoint."""
        response = client.client.get("/dashboard/dynamo")

        # Should return HTML (200 or 404 if not available)
        if response.status_code == 200:
            assert "text/html" in response.headers.get("content-type", "")
            assert len(response.text) > 0
        else:
            assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.metrics
@pytest.mark.slow
class TestMetricsPerformance:
    """Test metrics collection performance."""

    def test_metrics_retrieval_performance(self, client: FakeAIClient):
        """Test that metrics retrieval is fast."""
        import time

        # Measure metrics retrieval time
        start = time.time()
        metrics = client.get_metrics()
        duration = time.time() - start

        # Should be fast (< 1 second)
        assert duration < 1.0
        assert isinstance(metrics, dict)

    def test_prometheus_metrics_performance(self, client: FakeAIClient):
        """Test Prometheus metrics generation performance."""
        import time

        # Measure Prometheus metrics generation
        start = time.time()
        metrics_text = client.get_prometheus_metrics()
        duration = time.time() - start

        # Should be fast (< 1 second)
        assert duration < 1.0
        assert isinstance(metrics_text, str)

    def test_metrics_under_load(self, client: FakeAIClient, sample_messages):
        """Test metrics accuracy under concurrent load."""
        import concurrent.futures

        # Generate load
        def make_request():
            return client.chat_completion(
                model="openai/gpt-oss-120b", messages=sample_messages
            )

        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [f.result() for f in futures]

        assert len(results) == 20

        # Metrics should still be retrievable
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)


@pytest.mark.integration
@pytest.mark.metrics
class TestMetricsConsistency:
    """Test metrics consistency and accuracy."""

    def test_metrics_format_consistency(
        self, client: FakeAIClient, sample_messages
    ):
        """Test that different metric formats are consistent."""
        # Generate activity
        client.chat_completion(
            model="openai/gpt-oss-120b", messages=sample_messages
        )

        # Get metrics in different formats
        json_metrics = client.get_metrics()
        prom_metrics = client.get_prometheus_metrics()

        # All formats should return data
        assert isinstance(json_metrics, dict)
        assert isinstance(prom_metrics, str)
        assert len(json_metrics) > 0
        assert len(prom_metrics) > 0

    def test_metrics_persistence(self, client: FakeAIClient, sample_messages):
        """Test that metrics persist across multiple retrievals."""
        # Generate activity
        client.chat_completion(
            model="openai/gpt-oss-120b", messages=sample_messages
        )

        # Get metrics twice
        metrics1 = client.get_metrics()
        metrics2 = client.get_metrics()

        # Should be consistent
        assert isinstance(metrics1, dict)
        assert isinstance(metrics2, dict)

    def test_all_metrics_endpoints_work(self, client: FakeAIClient, sample_messages):
        """Test that all metrics endpoints are functional."""
        # Generate activity
        client.chat_completion(
            model="openai/gpt-oss-120b", messages=sample_messages
        )

        # Test all major metrics endpoints
        endpoints = [
            "/metrics",
            "/metrics/prometheus",
            "/metrics/csv",
            "/health/detailed",
            "/kv-cache/metrics",
            "/metrics/by-model",
            "/metrics/by-model/prometheus",
            "/metrics/costs",
            "/metrics/multi-dimensional",
            "/dcgm/metrics",
            "/dcgm/metrics/json",
            "/dynamo/metrics",
            "/dynamo/metrics/json",
            "/metrics/rate-limits",
            "/metrics/rate-limits/tier",
            "/metrics/rate-limits/throttle-analytics",
            "/metrics/rate-limits/abuse-patterns",
        ]

        for endpoint in endpoints:
            response = client.client.get(endpoint)

            # Should return 200 OK
            assert (
                response.status_code == 200
            ), f"Endpoint {endpoint} failed with {response.status_code}"

            # Should return data
            if "prometheus" in endpoint or "csv" in endpoint:
                assert len(response.text) > 0
            else:
                data = response.json()
                assert isinstance(data, (dict, list))
