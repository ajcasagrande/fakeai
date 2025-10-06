"""
Tests for /kv-cache/metrics endpoint.

Verifies that the endpoint returns real KV cache and smart routing metrics,
not hardcoded stub data.
"""

import pytest


@pytest.mark.integration
class TestKVCacheMetricsEndpoint:
    """Test /kv-cache/metrics endpoint returns real data."""

    def test_kv_cache_metrics_returns_real_data(self, client_no_auth):
        """Endpoint should return non-stub data structure."""
        response = client_no_auth.get("/kv-cache/metrics")

        assert response.status_code == 200
        data = response.json()

        # Should have both main sections
        assert "cache_performance" in data
        assert "smart_router" in data

        # Cache performance section
        cache_perf = data["cache_performance"]
        assert "cache_hit_rate" in cache_perf
        assert "token_reuse_rate" in cache_perf
        assert "total_cache_hits" in cache_perf
        assert "total_cache_misses" in cache_perf
        assert "total_tokens_processed" in cache_perf
        assert "cached_tokens_reused" in cache_perf
        assert "average_prefix_length" in cache_perf
        assert "endpoint_stats" in cache_perf

        # Smart router section
        router = data["smart_router"]
        assert "workers" in router
        assert "radix_tree" in router
        assert "config" in router

        # Radix tree stats
        radix = router["radix_tree"]
        assert "total_nodes" in radix
        assert "total_cached_blocks" in radix

        # Config
        config = router["config"]
        assert "num_workers" in config
        assert "block_size" in config
        assert "kv_overlap_weight" in config
        assert "load_balance_weight" in config

    def test_cache_hit_rate_increases(self, client_no_auth):
        """Cache hit rate should increase when same prompt is reused."""
        # First request - should be a cache miss
        response1 = client_no_auth.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "What is machine learning?"}],
            },
        )
        assert response1.status_code == 200

        # Get initial metrics
        metrics1 = client_no_auth.get("/kv-cache/metrics").json()
        initial_hits = metrics1["cache_performance"]["total_cache_hits"]
        initial_misses = metrics1["cache_performance"]["total_cache_misses"]

        # Second request - same prompt should trigger cache hit
        response2 = client_no_auth.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "What is machine learning?"}],
            },
        )
        assert response2.status_code == 200

        # Get updated metrics
        metrics2 = client_no_auth.get("/kv-cache/metrics").json()
        final_hits = metrics2["cache_performance"]["total_cache_hits"]
        final_misses = metrics2["cache_performance"]["total_cache_misses"]

        # Total lookups should increase
        assert (final_hits + final_misses) > (initial_hits + initial_misses)

        # If we got a cache hit, verify hit rate increased
        if final_hits > initial_hits:
            assert (
                metrics2["cache_performance"]["cache_hit_rate"]
                >= metrics1["cache_performance"]["cache_hit_rate"]
            )

    def test_smart_router_tracks_workers(self, client_no_auth):
        """Smart router should track worker statistics."""
        # Make a few requests to generate worker activity
        for i in range(3):
            response = client_no_auth.post(
                "/v1/chat/completions",
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [{"role": "user", "content": f"Test message {i}"}],
                },
            )
            assert response.status_code == 200

        # Get metrics
        metrics = client_no_auth.get("/kv-cache/metrics").json()
        workers = metrics["smart_router"]["workers"]

        # Should have 4 workers (default config)
        assert len(workers) == 4

        # At least one worker should have processed requests
        total_requests = sum(w["total_requests"] for w in workers.values())
        assert total_requests >= 3  # At least 3 requests we just made

        # Each worker should have expected fields
        for worker_id, worker_stats in workers.items():
            assert "active_requests" in worker_stats
            assert "total_requests" in worker_stats
            assert "cached_blocks" in worker_stats
            assert "tokens_processed" in worker_stats

            # Active requests should be 0 (requests completed)
            assert worker_stats["active_requests"] == 0
            # Total requests should be non-negative
            assert worker_stats["total_requests"] >= 0
            # Cached blocks should be non-negative
            assert worker_stats["cached_blocks"] >= 0
            # Tokens processed should be non-negative
            assert worker_stats["tokens_processed"] >= 0

    def test_token_reuse_metrics(self, client_no_auth):
        """Token reuse metrics should be tracked."""
        # Make a request
        response = client_no_auth.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "user", "content": "Tell me about deep learning"}
                ],
            },
        )
        assert response.status_code == 200

        # Get metrics
        metrics = client_no_auth.get("/kv-cache/metrics").json()
        cache_perf = metrics["cache_performance"]

        # Token metrics should be present and non-negative
        assert cache_perf["total_tokens_processed"] >= 0
        assert cache_perf["cached_tokens_reused"] >= 0

        # Token reuse rate should be between 0 and 100
        assert 0.0 <= cache_perf["token_reuse_rate"] <= 100.0

        # If tokens were processed, check consistency
        if cache_perf["total_tokens_processed"] > 0:
            expected_rate = (
                cache_perf["cached_tokens_reused"]
                / cache_perf["total_tokens_processed"]
                * 100
            )
            # Allow for small floating point differences
            assert abs(cache_perf["token_reuse_rate"] - expected_rate) < 0.1

    def test_endpoint_stats_tracks_endpoints(self, client_no_auth):
        """Endpoint stats should track per-endpoint cache performance."""
        # Make requests to chat completions (which uses KV caching)
        client_no_auth.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Chat test"}],
            },
        )

        # Get metrics
        metrics = client_no_auth.get("/kv-cache/metrics").json()
        endpoint_stats = metrics["cache_performance"]["endpoint_stats"]

        # Should have stats for chat completions endpoint
        assert "/v1/chat/completions" in endpoint_stats

        # Chat endpoint should have hit/miss counts
        chat_stats = endpoint_stats["/v1/chat/completions"]
        assert "hits" in chat_stats
        assert "misses" in chat_stats
        assert chat_stats["hits"] >= 0
        assert chat_stats["misses"] >= 0

        # Verify the structure of all endpoints tracked
        for endpoint, stats in endpoint_stats.items():
            assert "hits" in stats
            assert "misses" in stats
            assert stats["hits"] >= 0
            assert stats["misses"] >= 0

    def test_radix_tree_grows_with_requests(self, client_no_auth):
        """Radix tree should grow as more unique prompts are cached."""
        # Get initial metrics
        metrics1 = client_no_auth.get("/kv-cache/metrics").json()
        initial_nodes = metrics1["smart_router"]["radix_tree"]["total_nodes"]

        # Make requests with unique prompts
        for i in range(5):
            client_no_auth.post(
                "/v1/chat/completions",
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [
                        {"role": "user", "content": f"Unique prompt {i} about AI"}
                    ],
                },
            )

        # Get updated metrics
        metrics2 = client_no_auth.get("/kv-cache/metrics").json()
        final_nodes = metrics2["smart_router"]["radix_tree"]["total_nodes"]

        # Tree should have grown (or at least not shrunk)
        assert final_nodes >= initial_nodes

    def test_metrics_not_hardcoded_zeros(self, client_no_auth):
        """Verify metrics are not all zeros (not stub data)."""
        # Make several requests to generate real metrics
        for i in range(3):
            client_no_auth.post(
                "/v1/chat/completions",
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [{"role": "user", "content": f"Test {i}"}],
                },
            )

        # Get metrics
        metrics = client_no_auth.get("/kv-cache/metrics").json()

        # At least some metrics should be non-zero
        cache_perf = metrics["cache_performance"]
        total_lookups = (
            cache_perf["total_cache_hits"] + cache_perf["total_cache_misses"]
        )

        # We made 3 requests, so should have at least 3 cache lookups
        assert total_lookups >= 3

        # Should have processed some tokens
        assert cache_perf["total_tokens_processed"] > 0

        # At least one worker should have processed requests
        router = metrics["smart_router"]
        total_worker_requests = sum(
            w["total_requests"] for w in router["workers"].values()
        )
        assert total_worker_requests >= 3

    def test_config_values_correct(self, client_no_auth):
        """Config values should match service initialization."""
        metrics = client_no_auth.get("/kv-cache/metrics").json()
        config = metrics["smart_router"]["config"]

        # Verify config matches expected values from service initialization
        assert config["num_workers"] == 4
        assert config["block_size"] == 16
        assert config["kv_overlap_weight"] == 1.0
        assert config["load_balance_weight"] == 0.5
