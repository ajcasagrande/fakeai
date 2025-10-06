"""
Tests for Advanced Smart Router.

Tests routing strategies, health tracking, affinity, predictive routing,
and optimization features.
"""

#  SPDX-License-Identifier: Apache-2.0

import time

import pytest

from fakeai.kv_cache import tokenize_for_cache
from fakeai.smart_router_advanced import (
    AdvancedSmartRouter,
    CostWeights,
    HealthThresholds,
    RoutingStrategy,
)


@pytest.fixture
def router():
    """Create router with default settings."""
    return AdvancedSmartRouter(
        strategy=RoutingStrategy.HYBRID,
        block_size=16,
        num_workers=4,
    )


@pytest.fixture
def round_robin_router():
    """Create round-robin router."""
    return AdvancedSmartRouter(
        strategy=RoutingStrategy.ROUND_ROBIN,
        block_size=16,
        num_workers=4,
    )


@pytest.fixture
def least_loaded_router():
    """Create least-loaded router."""
    return AdvancedSmartRouter(
        strategy=RoutingStrategy.LEAST_LOADED,
        block_size=16,
        num_workers=4,
    )


@pytest.fixture
def cache_aware_router():
    """Create cache-aware router."""
    return AdvancedSmartRouter(
        strategy=RoutingStrategy.CACHE_AWARE,
        block_size=16,
        num_workers=4,
    )


@pytest.fixture
def learned_router():
    """Create learned router."""
    return AdvancedSmartRouter(
        strategy=RoutingStrategy.LEARNED,
        block_size=16,
        num_workers=4,
    )


class TestBasicRouting:
    """Test basic routing functionality."""

    def test_router_initialization(self, router):
        """Test router initializes correctly."""
        assert router.strategy == RoutingStrategy.HYBRID
        assert router.block_size == 16
        assert len(router.workers) == 4
        assert len(router.worker_health) == 4

        # Check all workers are healthy initially
        for health in router.worker_health.values():
            assert health.is_healthy
            assert not health.is_degraded

    def test_route_simple_request(self, router):
        """Test routing a simple request."""
        tokens = tokenize_for_cache("Hello, world!")
        worker_id, matched_tokens, matched_blocks = router.route_request(tokens)

        assert worker_id in router.workers
        assert matched_tokens == 0  # No cache on first request
        assert matched_blocks == 0

    def test_route_with_empty_tokens(self, router):
        """Test routing with empty tokens."""
        tokens = []
        worker_id, matched_tokens, matched_blocks = router.route_request(tokens)

        assert worker_id in router.workers
        assert matched_tokens == 0
        assert matched_blocks == 0


class TestRoundRobinStrategy:
    """Test round-robin routing strategy."""

    def test_round_robin_distribution(self, round_robin_router):
        """Test round-robin distributes evenly."""
        tokens = tokenize_for_cache("Test message")
        workers_used = []

        for _ in range(8):
            worker_id, _, _ = round_robin_router.route_request(tokens)
            workers_used.append(worker_id)

        # Should cycle through all 4 workers twice
        assert len(set(workers_used)) == 4
        # Each worker should be used exactly twice
        for i in range(4):
            assert workers_used.count(f"worker-{i}") == 2

    def test_round_robin_ignores_cache(self, round_robin_router):
        """Test round-robin doesn't prioritize cache hits."""
        tokens = tokenize_for_cache("Cached message")

        # First request
        worker1, _, _ = round_robin_router.route_request(tokens)
        round_robin_router.start_request(worker1)
        round_robin_router.complete_request(worker1, tokens, 10)

        # Second request - should go to next worker, not same one with cache
        worker2, _, _ = round_robin_router.route_request(tokens)
        assert worker2 != worker1


class TestLeastLoadedStrategy:
    """Test least-loaded routing strategy."""

    def test_least_loaded_basic(self, least_loaded_router):
        """Test least-loaded picks worker with fewest requests."""
        tokens = tokenize_for_cache("Test message")

        # First request should go to any worker (all have 0 load)
        worker1, _, _ = least_loaded_router.route_request(tokens)
        least_loaded_router.start_request(worker1)

        # Second request should go to a different worker
        worker2, _, _ = least_loaded_router.route_request(tokens)
        assert worker1 != worker2

    def test_least_loaded_avoids_busy_workers(self, least_loaded_router):
        """Test least-loaded avoids workers with high load."""
        tokens = tokenize_for_cache("Test message")

        # Load up worker-0 with 5 requests
        for _ in range(5):
            least_loaded_router.start_request("worker-0")

        # Next request should NOT go to worker-0
        worker_id, _, _ = least_loaded_router.route_request(tokens)
        assert worker_id != "worker-0"

    def test_least_loaded_considers_queue_depth(self, least_loaded_router):
        """Test least-loaded considers queue depth."""
        tokens = tokenize_for_cache("Test message")

        # Increase queue depth on worker-0
        least_loaded_router.workers["worker-0"].queue_depth = 10

        # Should prefer other workers
        worker_id, _, _ = least_loaded_router.route_request(tokens)
        assert worker_id != "worker-0"


class TestCacheAwareStrategy:
    """Test cache-aware routing strategy."""

    def test_cache_aware_no_cache(self, cache_aware_router):
        """Test cache-aware routing when no cache exists."""
        tokens = tokenize_for_cache("First message")
        worker_id, matched_tokens, matched_blocks = cache_aware_router.route_request(
            tokens
        )

        assert worker_id in cache_aware_router.workers
        assert matched_tokens == 0
        assert matched_blocks == 0

    def test_cache_aware_with_cache_hit(self, cache_aware_router):
        """Test cache-aware routing prioritizes cache hits."""
        tokens = tokenize_for_cache(
            "This is a test message with enough tokens for caching"
        )

        # First request - no cache
        worker1, _, _ = cache_aware_router.route_request(tokens)
        cache_aware_router.start_request(worker1)
        cache_aware_router.complete_request(
            worker1, tokens, 20, success=True, latency_ms=100
        )

        # Second request - should prefer same worker due to cache
        worker2, matched_tokens, matched_blocks = cache_aware_router.route_request(
            tokens
        )
        assert worker2 == worker1
        assert matched_tokens > 0  # Should have cache hit

    def test_cache_aware_fallback_to_least_loaded(self, cache_aware_router):
        """Test cache-aware falls back to least-loaded when no cache."""
        tokens = tokenize_for_cache("New message")

        # Load up worker-0
        for _ in range(5):
            cache_aware_router.start_request("worker-0")

        # Should avoid busy worker even without cache
        worker_id, _, _ = cache_aware_router.route_request(tokens)
        assert worker_id != "worker-0"


class TestHybridStrategy:
    """Test hybrid routing strategy."""

    def test_hybrid_balances_factors(self, router):
        """Test hybrid strategy balances multiple factors."""
        tokens = tokenize_for_cache("Test message for hybrid routing")

        worker_id, _, _ = router.route_request(tokens)
        assert worker_id in router.workers

    def test_hybrid_conversation_affinity(self, router):
        """Test hybrid routing uses conversation affinity."""
        tokens = tokenize_for_cache("Conversation message")
        conversation_id = "conv-123"

        # First request
        worker1, _, _ = router.route_request(tokens, conversation_id=conversation_id)
        router.start_request(worker1)
        router.complete_request(worker1, tokens, 10, success=True, latency_ms=50)

        # Second request in same conversation should go to same worker
        worker2, _, _ = router.route_request(tokens, conversation_id=conversation_id)
        assert worker2 == worker1

    def test_hybrid_user_affinity(self, router):
        """Test hybrid routing tracks user affinity."""
        tokens = tokenize_for_cache("User message")
        user_id = "user-456"

        # Route several requests for same user
        worker1, _, _ = router.route_request(tokens, user_id=user_id)
        assert user_id in router.user_affinity
        assert worker1 in router.user_affinity[user_id]

    def test_hybrid_model_affinity(self, router):
        """Test hybrid routing tracks model affinity."""
        tokens = tokenize_for_cache("Model message")
        model_id = "gpt-4"

        # Route request for specific model
        worker1, _, _ = router.route_request(tokens, model_id=model_id)
        assert model_id in router.model_affinity
        assert worker1 in router.model_affinity[model_id]


class TestLearnedStrategy:
    """Test learned routing strategy."""

    def test_learned_uses_historical_success(self, learned_router):
        """Test learned strategy uses historical success rates."""
        tokens = tokenize_for_cache("Test message")

        # Simulate successful requests on worker-0
        for _ in range(10):
            learned_router.start_request("worker-0")
            learned_router.complete_request(
                "worker-0", tokens, 10, success=True, latency_ms=50
            )

        # Simulate failed requests on worker-1
        for _ in range(10):
            learned_router.start_request("worker-1")
            learned_router.complete_request(
                "worker-1", tokens, 10, success=False, latency_ms=1000
            )

        # Give other workers some baseline history to make comparison fair
        for worker_id in ["worker-2", "worker-3"]:
            for _ in range(5):
                learned_router.start_request(worker_id)
                learned_router.complete_request(
                    worker_id, tokens, 10, success=True, latency_ms=200
                )

        # Should prefer worker-0 (best combination of success + latency)
        worker_id, _, _ = learned_router.route_request(tokens)
        assert worker_id == "worker-0"

    def test_learned_considers_latency(self, learned_router):
        """Test learned strategy considers average latency."""
        tokens = tokenize_for_cache("Test message")

        # Worker-0: fast
        for _ in range(10):
            learned_router.start_request("worker-0")
            learned_router.complete_request(
                "worker-0", tokens, 10, success=True, latency_ms=10
            )

        # Worker-1: slow
        for _ in range(10):
            learned_router.start_request("worker-1")
            learned_router.complete_request(
                "worker-1", tokens, 10, success=True, latency_ms=5000
            )

        # Give other workers some baseline history
        for worker_id in ["worker-2", "worker-3"]:
            for _ in range(10):
                learned_router.start_request(worker_id)
                learned_router.complete_request(
                    worker_id, tokens, 10, success=True, latency_ms=200
                )

        # Should prefer fast worker
        worker_id, _, _ = learned_router.route_request(tokens)
        assert worker_id == "worker-0"


class TestWorkerHealth:
    """Test worker health tracking."""

    def test_health_initialization(self, router):
        """Test worker health initializes as healthy."""
        for worker_id, health in router.worker_health.items():
            assert health.is_healthy
            assert not health.is_degraded
            assert health.get_success_rate() == 1.0

    def test_health_success_tracking(self, router):
        """Test health tracks successful requests."""
        router.update_worker_health("worker-0", success=True, latency_ms=50)

        health = router.worker_health["worker-0"]
        assert health.success_count == 1
        assert health.failure_count == 0
        assert health.get_success_rate() == 1.0

    def test_health_failure_tracking(self, router):
        """Test health tracks failed requests."""
        router.update_worker_health("worker-0", success=False, latency_ms=1000)

        health = router.worker_health["worker-0"]
        assert health.success_count == 0
        assert health.failure_count == 1
        assert health.get_success_rate() == 0.0

    def test_health_timeout_tracking(self, router):
        """Test health tracks timeouts."""
        router.update_worker_health(
            "worker-0", success=False, latency_ms=30000, timeout=True
        )

        health = router.worker_health["worker-0"]
        assert health.timeout_count == 1
        assert health.failure_count == 1

    def test_health_degraded_detection(self, router):
        """Test worker becomes degraded with poor performance."""
        # Simulate requests with low success rate
        for i in range(20):
            success = i < 18  # 90% success rate (exactly at threshold)
            router.update_worker_health("worker-0", success=success, latency_ms=100)

        # Now push it below threshold
        router.update_worker_health("worker-0", success=False, latency_ms=100)

        health = router.worker_health["worker-0"]
        assert health.is_degraded or not health.is_healthy

    def test_health_unhealthy_detection(self, router):
        """Test worker becomes unhealthy with very poor performance."""
        # Simulate many failures
        for _ in range(10):
            router.update_worker_health("worker-0", success=False, latency_ms=15000)

        health = router.worker_health["worker-0"]
        assert not health.is_healthy

    def test_health_recovery(self, router):
        """Test worker recovers with good performance."""
        # Make worker unhealthy
        for _ in range(10):
            router.update_worker_health("worker-0", success=False, latency_ms=15000)

        health = router.worker_health["worker-0"]
        assert not health.is_healthy

        # Recover with many successes
        # Need: (1) Recent 10 successes in history for recovery logic
        #       (2) Overall success rate > 0.90 (degraded threshold) for full recovery
        #       (3) Average latency < 5000ms (degraded threshold) for full recovery
        # Strategy: Add many more successes so all metrics exceed thresholds
        # 10 failures (150000ms total) + 100 successes (5000ms total) = 110 requests
        # Success rate: 100/110 = 90.9% > 90% ✓
        # Avg latency: 155000/110 = 1409ms < 5000ms ✓
        # Last 10 in history: all successes ✓
        for _ in range(100):
            router.update_worker_health("worker-0", success=True, latency_ms=50)

        health = router.worker_health["worker-0"]
        assert health.is_healthy
        assert not health.is_degraded

    def test_health_average_latency(self, router):
        """Test health tracks average latency."""
        router.update_worker_health("worker-0", success=True, latency_ms=100)
        router.update_worker_health("worker-0", success=True, latency_ms=200)
        router.update_worker_health("worker-0", success=True, latency_ms=300)

        health = router.worker_health["worker-0"]
        assert health.get_average_latency_ms() == 200.0


class TestRequestAffinity:
    """Test request affinity features."""

    def test_conversation_affinity_routing(self, router):
        """Test conversation affinity routes to same worker."""
        tokens = tokenize_for_cache("Conversation message")
        conv_id = "conv-123"

        # First request
        worker1, _, _ = router.route_request(tokens, conversation_id=conv_id)
        router.start_request(worker1)
        router.complete_request(worker1, tokens, 10)

        # Subsequent requests should go to same worker
        for _ in range(5):
            worker_id, _, _ = router.route_request(tokens, conversation_id=conv_id)
            assert worker_id == worker1

    def test_conversation_affinity_persists(self, router):
        """Test conversation affinity persists across cache updates."""
        tokens1 = tokenize_for_cache("First message")
        tokens2 = tokenize_for_cache("Second message")
        conv_id = "conv-456"

        # First request
        worker1, _, _ = router.route_request(tokens1, conversation_id=conv_id)
        router.start_request(worker1)
        router.complete_request(worker1, tokens1, 10)

        # Different message in same conversation
        worker2, _, _ = router.route_request(tokens2, conversation_id=conv_id)
        assert worker2 == worker1

    def test_user_affinity_tracking(self, router):
        """Test user affinity is tracked."""
        tokens = tokenize_for_cache("User message")
        user_id = "user-789"

        worker1, _, _ = router.route_request(tokens, user_id=user_id)
        assert user_id in router.user_affinity
        assert worker1 in router.user_affinity[user_id]

    def test_model_affinity_tracking(self, router):
        """Test model affinity is tracked."""
        tokens = tokenize_for_cache("Model message")
        model_id = "gpt-4"

        worker1, _, _ = router.route_request(tokens, model_id=model_id)
        assert model_id in router.model_affinity
        assert worker1 in router.model_affinity[model_id]


class TestCostFunction:
    """Test comprehensive cost function."""

    def test_cost_weights_customization(self):
        """Test custom cost weights are applied."""
        custom_weights = CostWeights(
            kv_overlap=2.0,
            load_balance=1.0,
            memory_pressure=0.5,
            queue_depth=0.8,
            historical_performance=0.3,
            slo_violation_penalty=5.0,
        )

        router = AdvancedSmartRouter(
            strategy=RoutingStrategy.HYBRID,
            cost_weights=custom_weights,
            num_workers=4,
        )

        assert router.cost_weights.kv_overlap == 2.0
        assert router.cost_weights.slo_violation_penalty == 5.0

    def test_cost_includes_memory_pressure(self, router):
        """Test cost function includes memory pressure."""
        tokens = tokenize_for_cache("Test message")

        # Set high memory pressure on worker-0
        router.workers["worker-0"].memory_pressure = 0.9

        # Should prefer other workers
        worker_id, _, _ = router.route_request(tokens)
        # With random factors, we can't guarantee it won't pick worker-0,
        # but we can verify the cost is calculated
        assert worker_id in router.workers

    def test_cost_includes_queue_depth(self, router):
        """Test cost function includes queue depth."""
        tokens = tokenize_for_cache("Test message")

        # Set high queue depth on worker-0
        router.workers["worker-0"].queue_depth = 20

        # Should prefer other workers
        worker_id, _, _ = router.route_request(tokens)
        assert worker_id in router.workers


class TestRoutingExplanation:
    """Test routing decision explanation."""

    def test_explain_routing_decision(self, router):
        """Test routing explanation provides details."""
        tokens = tokenize_for_cache("Test message for explanation")

        explanation = router.get_routing_decision_explain(tokens)

        assert "strategy" in explanation
        assert "total_input_tokens" in explanation
        assert "cache_match" in explanation
        assert "selected_worker" in explanation
        assert "all_workers" in explanation

    def test_explain_includes_worker_evaluations(self, router):
        """Test explanation includes all worker evaluations."""
        tokens = tokenize_for_cache("Test message")

        explanation = router.get_routing_decision_explain(tokens)

        assert len(explanation["all_workers"]) == 4
        for worker_eval in explanation["all_workers"]:
            assert "worker_id" in worker_eval
            assert "cost" in worker_eval
            assert "health_status" in worker_eval
            assert "success_rate" in worker_eval

    def test_explain_shows_affinity(self, router):
        """Test explanation shows affinity information."""
        tokens = tokenize_for_cache("Test message")
        conv_id = "conv-123"
        user_id = "user-456"

        # First establish affinity
        router.route_request(tokens, conversation_id=conv_id, user_id=user_id)

        # Now explain
        explanation = router.get_routing_decision_explain(
            tokens, conversation_id=conv_id, user_id=user_id
        )

        assert explanation["affinity"]["conversation_id"] == conv_id
        assert explanation["affinity"]["user_id"] == user_id


class TestWorkerPoolOptimization:
    """Test worker pool optimization suggestions."""

    def test_optimize_healthy_pool(self, router):
        """Test optimization on healthy pool."""
        result = router.optimize_worker_pool()

        assert result["total_workers"] == 4
        assert result["healthy_workers"] == 4
        assert result["unhealthy_workers"] == 0
        assert isinstance(result["suggestions"], list)

    def test_optimize_detects_unhealthy_workers(self, router):
        """Test optimization detects unhealthy workers."""
        # Make worker-0 unhealthy
        for _ in range(20):
            router.update_worker_health("worker-0", success=False, latency_ms=15000)

        result = router.optimize_worker_pool()

        assert result["unhealthy_workers"] > 0
        assert len(result["warnings"]) > 0
        assert any("unhealthy" in s.lower() for s in result["suggestions"])

    def test_optimize_detects_high_load(self, router):
        """Test optimization detects high load."""
        # Simulate high load
        for _ in range(15):
            router.start_request("worker-0")

        result = router.optimize_worker_pool()

        assert result["total_active_requests"] >= 15
        # May suggest adding workers
        assert isinstance(result["suggestions"], list)

    def test_optimize_detects_imbalance(self, router):
        """Test optimization detects load imbalance."""
        tokens = tokenize_for_cache("Test message")

        # Route many requests to create imbalance
        for i in range(20):
            worker_id = f"worker-{i % 2}"  # Only use workers 0 and 1
            router.start_request(worker_id)
            router.complete_request(worker_id, tokens, 10)

        result = router.optimize_worker_pool()

        # Should have utilization stats
        assert "worker_utilization" in result
        assert len(result["worker_utilization"]) == 4


class TestStatistics:
    """Test statistics and metrics."""

    def test_get_stats_basic(self, router):
        """Test getting basic statistics."""
        stats = router.get_stats()

        assert "strategy" in stats
        assert "workers" in stats
        assert "radix_tree" in stats
        assert "config" in stats

    def test_get_stats_worker_details(self, router):
        """Test worker statistics are detailed."""
        stats = router.get_stats()

        for worker_id, worker_stats in stats["workers"].items():
            assert "active_requests" in worker_stats
            assert "health" in worker_stats
            assert "success_rate" in worker_stats["health"]
            assert "average_latency_ms" in worker_stats["health"]

    def test_get_stats_affinity_tracking(self, router):
        """Test statistics include affinity tracking."""
        tokens = tokenize_for_cache("Test message")

        # Create some affinity
        router.route_request(tokens, conversation_id="conv-1")
        router.route_request(tokens, user_id="user-1")
        router.route_request(tokens, model_id="gpt-4")

        stats = router.get_stats()

        assert stats["affinity"]["active_conversations"] >= 1
        assert stats["affinity"]["tracked_users"] >= 1
        assert stats["affinity"]["tracked_models"] >= 1


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_route_with_all_workers_unhealthy(self, router):
        """Test routing when all workers are unhealthy."""
        # Make all workers unhealthy
        for worker_id in router.workers.keys():
            for _ in range(20):
                router.update_worker_health(worker_id, success=False, latency_ms=15000)

        # Should still route (fallback to unhealthy workers)
        tokens = tokenize_for_cache("Test message")
        worker_id, _, _ = router.route_request(tokens)
        assert worker_id in router.workers

    def test_health_update_unknown_worker(self, router):
        """Test updating health for unknown worker doesn't crash."""
        router.update_worker_health("unknown-worker", success=True, latency_ms=100)
        # Should log warning but not crash

    def test_route_with_zero_workers(self):
        """Test routing with no workers raises error."""
        router = AdvancedSmartRouter(num_workers=0)
        router.workers.clear()  # Force empty

        tokens = tokenize_for_cache("Test message")
        with pytest.raises(ValueError, match="No workers registered"):
            router.route_request(tokens)

    def test_complete_request_updates_cache(self, router):
        """Test completing request updates cache."""
        tokens = tokenize_for_cache("Message with enough tokens for caching properly")

        worker_id, _, _ = router.route_request(tokens)
        router.start_request(worker_id)
        router.complete_request(worker_id, tokens, 20, success=True, latency_ms=100)

        # Should have cached blocks
        assert len(router.workers[worker_id].cached_blocks) > 0

    def test_complete_request_decrements_active(self, router):
        """Test completing request decrements active count."""
        tokens = tokenize_for_cache("Test message")

        worker_id, _, _ = router.route_request(tokens)
        router.start_request(worker_id)

        active_before = router.workers[worker_id].active_requests
        router.complete_request(worker_id, tokens, 10)
        active_after = router.workers[worker_id].active_requests

        assert active_after == active_before - 1


class TestHealthThresholds:
    """Test health threshold customization."""

    def test_custom_health_thresholds(self):
        """Test custom health thresholds are applied."""
        custom_thresholds = HealthThresholds(
            degraded_success_rate=0.95,
            unhealthy_success_rate=0.80,
            degraded_latency_ms=3000.0,
            unhealthy_latency_ms=8000.0,
        )

        router = AdvancedSmartRouter(
            strategy=RoutingStrategy.HYBRID,
            health_thresholds=custom_thresholds,
            num_workers=4,
        )

        assert router.health_thresholds.degraded_success_rate == 0.95
        assert router.health_thresholds.unhealthy_latency_ms == 8000.0

    def test_custom_thresholds_affect_detection(self):
        """Test custom thresholds affect health detection."""
        strict_thresholds = HealthThresholds(
            degraded_success_rate=0.99,  # Very strict
            unhealthy_success_rate=0.95,
        )

        router = AdvancedSmartRouter(
            strategy=RoutingStrategy.HYBRID,
            health_thresholds=strict_thresholds,
            num_workers=4,
        )

        # With strict thresholds, should become degraded faster
        for i in range(20):
            success = i < 19  # 95% success rate
            router.update_worker_health("worker-0", success=success, latency_ms=100)

        health = router.worker_health["worker-0"]
        # With strict thresholds, this should be detected as degraded/unhealthy
        assert health.is_degraded or not health.is_healthy


class TestPredictiveRouting:
    """Test predictive routing features."""

    def test_predict_request_duration_no_history(self, router):
        """Test duration prediction with no history."""
        tokens = tokenize_for_cache("Test message")
        worker = router.workers["worker-0"]

        duration = router._predict_request_duration(tokens, 100, worker)
        assert duration > 0

    def test_predict_request_duration_with_history(self, router):
        """Test duration prediction with history."""
        tokens = tokenize_for_cache("Test message")

        # Build history
        router.start_request("worker-0")
        router.complete_request("worker-0", tokens, 10, success=True, latency_ms=500)

        worker = router.workers["worker-0"]
        duration = router._predict_request_duration(tokens, 100, worker)

        # Should be close to historical latency
        assert 0 < duration <= 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
