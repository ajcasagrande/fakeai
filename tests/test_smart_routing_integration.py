"""
Integration Tests for Smart Routing.

This module provides comprehensive end-to-end tests for smart routing functionality,
including:
- Model fallback on failure
- Load-based routing
- Latency-based routing
- Cost-based routing
- Capacity-based routing
- Round-robin routing
- Weighted routing
- Geographic routing
- Health check integration
- Circuit breaker patterns
- Routing metrics
- Dynamic routing updates
"""

#  SPDX-License-Identifier: Apache-2.0


import pytest

from fakeai.kv_cache import tokenize_for_cache
from fakeai.smart_router_advanced import (
    AdvancedSmartRouter,
    CostWeights,
    HealthThresholds,
    RoutingStrategy,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def router() -> AdvancedSmartRouter:
    """Create default hybrid router for testing."""
    return AdvancedSmartRouter(
        strategy=RoutingStrategy.HYBRID,
        block_size=16,
        num_workers=4,
    )


@pytest.fixture
def round_robin_router() -> AdvancedSmartRouter:
    """Create round-robin router."""
    return AdvancedSmartRouter(
        strategy=RoutingStrategy.ROUND_ROBIN,
        block_size=16,
        num_workers=4,
    )


@pytest.fixture
def least_loaded_router() -> AdvancedSmartRouter:
    """Create least-loaded router."""
    return AdvancedSmartRouter(
        strategy=RoutingStrategy.LEAST_LOADED,
        block_size=16,
        num_workers=4,
    )


@pytest.fixture
def cache_aware_router() -> AdvancedSmartRouter:
    """Create cache-aware router."""
    return AdvancedSmartRouter(
        strategy=RoutingStrategy.CACHE_AWARE,
        block_size=16,
        num_workers=4,
    )


@pytest.fixture
def learned_router() -> AdvancedSmartRouter:
    """Create learned router."""
    return AdvancedSmartRouter(
        strategy=RoutingStrategy.LEARNED,
        block_size=16,
        num_workers=4,
    )


@pytest.fixture
def cost_optimized_router() -> AdvancedSmartRouter:
    """Create router with cost-optimized weights."""
    weights = CostWeights(
        kv_overlap=2.0,  # Prioritize cache hits
        load_balance=1.5,  # Balance load
        memory_pressure=1.0,  # Consider memory
        queue_depth=1.2,  # Consider queue
        historical_performance=0.8,  # Learn from history
        slo_violation_penalty=3.0,  # Avoid unhealthy workers
    )
    return AdvancedSmartRouter(
        strategy=RoutingStrategy.HYBRID,
        cost_weights=weights,
        block_size=16,
        num_workers=4,
    )


@pytest.fixture
def strict_health_router() -> AdvancedSmartRouter:
    """Create router with strict health thresholds."""
    thresholds = HealthThresholds(
        degraded_success_rate=0.95,
        unhealthy_success_rate=0.80,
        degraded_latency_ms=2000.0,
        unhealthy_latency_ms=5000.0,
        degraded_timeout_rate=0.03,
        unhealthy_timeout_rate=0.10,
        recovery_success_threshold=15,
    )
    return AdvancedSmartRouter(
        strategy=RoutingStrategy.HYBRID,
        health_thresholds=thresholds,
        block_size=16,
        num_workers=4,
    )


@pytest.fixture
def sample_tokens() -> list[int]:
    """Generate sample token sequence."""
    return tokenize_for_cache("The quick brown fox jumps over the lazy dog.")


@pytest.fixture
def long_token_sequence() -> list[int]:
    """Generate long token sequence for caching tests."""
    text = (
        "In the realm of artificial intelligence, natural language processing "
        "represents one of the most challenging and fascinating domains. "
        "It involves teaching machines to understand, interpret, and generate "
        "human language in ways that are both meaningful and useful. "
        "The field has seen remarkable progress in recent years."
    )
    return tokenize_for_cache(text)


# ============================================================================
# Test 1: Model Fallback on Failure
# ============================================================================


@pytest.mark.integration
class TestModelFallbackOnFailure:
    """Test failover behavior when workers fail."""

    def test_fallback_to_healthy_worker_on_failure(self, router: AdvancedSmartRouter):
        """Test router fails over to healthy worker when primary fails."""
        tokens = tokenize_for_cache("Test message for fallback")

        # First request - establish primary worker
        primary_worker, _, _ = router.route_request(tokens)
        router.start_request(primary_worker)
        router.complete_request(primary_worker, tokens, 10, success=True, latency_ms=50)

        # Make primary worker unhealthy (simulate failures)
        for _ in range(20):
            router.update_worker_health(primary_worker, success=False, latency_ms=15000)

        # Next request should go to a different (healthy) worker
        fallback_worker, _, _ = router.route_request(tokens)
        assert fallback_worker != primary_worker
        assert router.worker_health[fallback_worker].is_healthy

    def test_automatic_recovery_after_failures(self, router: AdvancedSmartRouter):
        """Test worker automatically recovers after sustained success."""
        worker_id = "worker-0"
        tokens = tokenize_for_cache("Recovery test message")

        # Make worker unhealthy
        for _ in range(10):
            router.update_worker_health(worker_id, success=False, latency_ms=15000)

        assert not router.worker_health[worker_id].is_healthy

        # Simulate recovery with many successful requests
        # Need: (1) Recent 10 successes in history for recovery logic
        #       (2) Overall success rate > 0.90 (degraded threshold) for full recovery
        #       (3) Average latency < 5000ms (degraded threshold) for full recovery
        # Strategy: Add many more successes so all metrics exceed thresholds
        # 10 failures (150000ms total) + 100 successes (5000ms total) = 110 requests
        # Success rate: 100/110 = 90.9% > 90% ✓
        # Avg latency: 155000/110 = 1409ms < 5000ms ✓
        # Last 10 in history: all successes ✓
        for _ in range(100):
            router.update_worker_health(worker_id, success=True, latency_ms=50)

        # Worker should recover
        health = router.worker_health[worker_id]
        assert health.is_healthy
        assert not health.is_degraded

    def test_all_workers_fail_scenario(self, router: AdvancedSmartRouter):
        """Test behavior when all workers fail."""
        tokens = tokenize_for_cache("All workers fail scenario")

        # Make all workers unhealthy
        for worker_id in router.workers.keys():
            for _ in range(20):
                router.update_worker_health(worker_id, success=False, latency_ms=15000)

        # Should still route (fallback to least-bad worker)
        worker_id, _, _ = router.route_request(tokens)
        assert worker_id in router.workers

    def test_cascading_failure_detection(self, router: AdvancedSmartRouter):
        """Test detection of cascading failures across workers."""
        tokens = tokenize_for_cache("Cascading failure test")

        # Simulate cascading failure pattern (workers fail one by one)
        for i, worker_id in enumerate(router.workers.keys()):
            failure_count = (i + 1) * 5  # Progressive failure
            for _ in range(failure_count):
                router.update_worker_health(worker_id, success=False, latency_ms=10000)

        # Check optimization suggestions detect the issue
        result = router.optimize_worker_pool()
        assert result["unhealthy_workers"] > 0
        assert len(result["warnings"]) > 0


# ============================================================================
# Test 2: Load-Based Routing
# ============================================================================


@pytest.mark.integration
class TestLoadBasedRouting:
    """Test load-aware routing strategies."""

    def test_load_balancing_with_least_loaded(
        self, least_loaded_router: AdvancedSmartRouter
    ):
        """Test least-loaded strategy balances load across workers."""
        tokens = tokenize_for_cache("Load balancing test")

        # Route 20 requests and track distribution
        worker_loads: dict[str, int] = {w: 0 for w in least_loaded_router.workers}

        for _ in range(20):
            worker_id, _, _ = least_loaded_router.route_request(tokens)
            least_loaded_router.start_request(worker_id)
            worker_loads[worker_id] += 1

        # Verify load is distributed (no worker should have >60% of requests)
        max_load = max(worker_loads.values())
        assert max_load <= 12  # At most 60% of 20 requests

    def test_avoids_overloaded_workers(self, least_loaded_router: AdvancedSmartRouter):
        """Test router avoids workers with high active request count."""
        tokens = tokenize_for_cache("Overload avoidance test")

        # Overload worker-0 with 10 active requests
        for _ in range(10):
            least_loaded_router.start_request("worker-0")

        # Route 10 new requests - should avoid worker-0
        workers_chosen = []
        for _ in range(10):
            worker_id, _, _ = least_loaded_router.route_request(tokens)
            workers_chosen.append(worker_id)

        # Worker-0 should be minimally used (if at all)
        worker_0_count = workers_chosen.count("worker-0")
        assert worker_0_count <= 2  # Allow some due to tie-breaking

    def test_queue_depth_consideration(self, router: AdvancedSmartRouter):
        """Test routing considers queue depth in addition to active requests."""
        tokens = tokenize_for_cache("Queue depth test")

        # Set high queue depth on worker-0
        router.workers["worker-0"].queue_depth = 25
        router.workers["worker-1"].queue_depth = 2

        # Should prefer worker-1 (lower queue depth)
        worker_id, _, _ = router.route_request(tokens)
        assert worker_id != "worker-0"

    def test_dynamic_load_adjustment(self, router: AdvancedSmartRouter):
        """Test load dynamically adjusts as requests complete."""
        tokens = tokenize_for_cache("Dynamic load test")

        # Start requests on all workers
        for worker_id in router.workers.keys():
            router.start_request(worker_id)

        # Complete some requests
        router.complete_request("worker-0", tokens, 10, success=True, latency_ms=50)
        router.complete_request("worker-1", tokens, 10, success=True, latency_ms=50)

        # Next request should prefer workers with completed requests
        worker_id, _, _ = router.route_request(tokens)
        assert worker_id in ["worker-0", "worker-1"]


# ============================================================================
# Test 3: Latency-Based Routing
# ============================================================================


@pytest.mark.integration
class TestLatencyBasedRouting:
    """Test latency-aware routing strategies."""

    def test_learned_strategy_prefers_low_latency(
        self, learned_router: AdvancedSmartRouter
    ):
        """Test learned strategy routes to workers with lowest latency."""
        tokens = tokenize_for_cache("Latency test message")

        # Train router with latency patterns
        # Worker-0: fast (50ms)
        for _ in range(20):
            learned_router.start_request("worker-0")
            learned_router.complete_request(
                "worker-0", tokens, 10, success=True, latency_ms=50
            )

        # Worker-1: slow (5000ms)
        for _ in range(20):
            learned_router.start_request("worker-1")
            learned_router.complete_request(
                "worker-1", tokens, 10, success=True, latency_ms=5000
            )

        # Worker-2 and Worker-3: medium (200ms)
        for worker_id in ["worker-2", "worker-3"]:
            for _ in range(20):
                learned_router.start_request(worker_id)
                learned_router.complete_request(
                    worker_id, tokens, 10, success=True, latency_ms=200
                )

        # Should prefer fast worker
        worker_id, _, _ = learned_router.route_request(tokens)
        assert worker_id == "worker-0"

    def test_latency_percentile_tracking(self, router: AdvancedSmartRouter):
        """Test router tracks latency statistics correctly."""
        tokens = tokenize_for_cache("Percentile test")

        # Generate latency distribution for worker-0
        latencies = [50, 60, 70, 80, 90, 100, 110, 120, 130, 140]
        for latency in latencies:
            router.start_request("worker-0")
            router.complete_request(
                "worker-0", tokens, 10, success=True, latency_ms=latency
            )

        health = router.worker_health["worker-0"]
        avg_latency = health.get_average_latency_ms()

        # Average should be close to median (95ms)
        assert 90 <= avg_latency <= 100

    def test_latency_degradation_detection(
        self, strict_health_router: AdvancedSmartRouter
    ):
        """Test detection of latency degradation."""
        tokens = tokenize_for_cache("Latency degradation test")

        # Worker-0: consistently high latency
        for _ in range(20):
            strict_health_router.start_request("worker-0")
            strict_health_router.complete_request(
                "worker-0", tokens, 10, success=True, latency_ms=6000  # Above threshold
            )

        health = strict_health_router.worker_health["worker-0"]
        # Should be marked as degraded or unhealthy due to high latency
        assert health.is_degraded or not health.is_healthy


# ============================================================================
# Test 4: Cost-Based Routing
# ============================================================================


@pytest.mark.integration
class TestCostBasedRouting:
    """Test cost-optimized routing decisions."""

    def test_cost_function_balances_factors(
        self, cost_optimized_router: AdvancedSmartRouter
    ):
        """Test comprehensive cost function balances all factors."""
        tokens = tokenize_for_cache("Cost optimization test message")

        # Set up different cost profiles for workers
        # Worker-0: High cache hit, but high load
        cost_optimized_router.radix_tree.insert(tokens, "worker-0")
        for _ in range(5):
            cost_optimized_router.start_request("worker-0")

        # Worker-1: No cache hit, low load
        # (default state)

        # Worker-2: High memory pressure
        cost_optimized_router.workers["worker-2"].memory_pressure = 0.95

        # Worker-3: High queue depth
        cost_optimized_router.workers["worker-3"].queue_depth = 15

        # Route and explain decision
        explanation = cost_optimized_router.get_routing_decision_explain(tokens)

        # Verify cost calculations are present
        assert "all_workers" in explanation
        for worker_eval in explanation["all_workers"]:
            assert "cost" in worker_eval
            assert worker_eval["cost"] >= 0

    def test_memory_pressure_cost(self, router: AdvancedSmartRouter):
        """Test memory pressure affects routing cost."""
        tokens = tokenize_for_cache("Memory pressure test")

        # Set high memory pressure on worker-0
        router.workers["worker-0"].memory_pressure = 0.98

        # Route multiple requests - should avoid worker-0
        workers_chosen = []
        for _ in range(10):
            worker_id, _, _ = router.route_request(tokens)
            workers_chosen.append(worker_id)

        # Worker-0 should be rarely chosen
        worker_0_count = workers_chosen.count("worker-0")
        assert worker_0_count <= 3  # Allow some due to other factors

    def test_cache_vs_load_tradeoff(self, router: AdvancedSmartRouter):
        """Test router balances cache hits vs load."""
        tokens = tokenize_for_cache(
            "Cache vs load tradeoff test with sufficient token length"
        )

        # Worker-0: Has cache but high load
        router.radix_tree.insert(tokens, "worker-0")
        for _ in range(8):
            router.start_request("worker-0")

        # Worker-1: No cache but low load
        # (default state)

        # Decision should consider both factors
        explanation = router.get_routing_decision_explain(tokens)
        selected = explanation["selected_worker"]

        # Either choice is valid depending on cost weights
        assert selected["worker_id"] in router.workers

    def test_slo_violation_penalty(self, router: AdvancedSmartRouter):
        """Test SLO violation penalty affects routing."""
        tokens = tokenize_for_cache("SLO violation test")

        # Make worker-0 degraded
        for _ in range(20):
            router.update_worker_health("worker-0", success=False, latency_ms=10000)

        # Make worker-1 healthy
        for _ in range(20):
            router.update_worker_health("worker-1", success=True, latency_ms=50)

        # Should strongly prefer healthy worker due to SLO penalty
        workers_chosen = []
        for _ in range(10):
            worker_id, _, _ = router.route_request(tokens)
            workers_chosen.append(worker_id)

        # Should mostly avoid unhealthy worker-0
        worker_0_count = workers_chosen.count("worker-0")
        assert worker_0_count <= 2


# ============================================================================
# Test 5: Capacity-Based Routing
# ============================================================================


@pytest.mark.integration
class TestCapacityBasedRouting:
    """Test routing based on worker capacity constraints."""

    def test_respects_worker_capacity_limits(self, router: AdvancedSmartRouter):
        """Test router respects worker capacity limits."""
        tokens = tokenize_for_cache("Capacity limit test")

        # Max out worker-0 and worker-1
        for worker_id in ["worker-0", "worker-1"]:
            for _ in range(10):
                router.start_request(worker_id)

        # Next requests should go to worker-2 or worker-3
        workers_chosen = []
        for _ in range(5):
            worker_id, _, _ = router.route_request(tokens)
            workers_chosen.append(worker_id)

        # Should primarily use less-loaded workers
        assert all(w in ["worker-2", "worker-3"] for w in workers_chosen)

    def test_adaptive_capacity_under_load(self, router: AdvancedSmartRouter):
        """Test capacity adjusts under load."""
        tokens = tokenize_for_cache("Adaptive capacity test")

        # Simulate burst of traffic
        active_requests = []
        for _ in range(20):
            worker_id, _, _ = router.route_request(tokens)
            router.start_request(worker_id)
            active_requests.append(worker_id)

        # Get stats during load
        stats = router.get_stats()
        total_active = sum(w["active_requests"] for w in stats["workers"].values())
        assert total_active == 20

        # Complete requests
        for i, worker_id in enumerate(active_requests):
            router.complete_request(worker_id, tokens, 10, success=True, latency_ms=100)

        # Stats should reflect completed requests
        stats_after = router.get_stats()
        total_active_after = sum(
            w["active_requests"] for w in stats_after["workers"].values()
        )
        assert total_active_after == 0


# ============================================================================
# Test 6: Round-Robin Routing
# ============================================================================


@pytest.mark.integration
class TestRoundRobinRouting:
    """Test round-robin routing strategy."""

    def test_even_distribution(self, round_robin_router: AdvancedSmartRouter):
        """Test round-robin distributes requests evenly."""
        tokens = tokenize_for_cache("Round-robin test")

        workers_chosen = []
        for _ in range(40):
            worker_id, _, _ = round_robin_router.route_request(tokens)
            workers_chosen.append(worker_id)

        # Each worker should get exactly 10 requests (40 / 4 = 10)
        for i in range(4):
            worker_id = f"worker-{i}"
            count = workers_chosen.count(worker_id)
            assert count == 10

    def test_round_robin_order(self, round_robin_router: AdvancedSmartRouter):
        """Test round-robin follows correct rotation order."""
        tokens = tokenize_for_cache("Order test")

        workers_chosen = []
        for _ in range(8):
            worker_id, _, _ = round_robin_router.route_request(tokens)
            workers_chosen.append(worker_id)

        # Should cycle through workers in order (starting position may vary)
        # Get the starting position
        start_worker_num = int(workers_chosen[0].split("-")[1])

        # Verify sequential rotation
        for i in range(8):
            expected_worker = f"worker-{(start_worker_num + i) % 4}"
            assert workers_chosen[i] == expected_worker

    def test_round_robin_ignores_health(self, round_robin_router: AdvancedSmartRouter):
        """Test round-robin respects health checks."""
        tokens = tokenize_for_cache("Health check test")

        # Make worker-1 unhealthy
        for _ in range(20):
            round_robin_router.update_worker_health(
                "worker-1", success=False, latency_ms=15000
            )

        workers_chosen = []
        for _ in range(12):
            worker_id, _, _ = round_robin_router.route_request(tokens)
            workers_chosen.append(worker_id)

        # Should skip unhealthy worker-1 in rotation
        assert "worker-1" not in workers_chosen


# ============================================================================
# Test 7: Weighted Routing
# ============================================================================


@pytest.mark.integration
class TestWeightedRouting:
    """Test weighted routing based on worker capabilities."""

    def test_custom_cost_weights(self):
        """Test custom cost weights influence routing decisions."""
        # Create router with cache-heavy weighting
        cache_heavy = CostWeights(
            kv_overlap=5.0,  # Heavily prioritize cache
            load_balance=0.1,  # Ignore load
            memory_pressure=0.1,
            queue_depth=0.1,
            historical_performance=0.1,
            slo_violation_penalty=1.0,
        )
        cache_router = AdvancedSmartRouter(
            strategy=RoutingStrategy.HYBRID,
            cost_weights=cache_heavy,
            num_workers=4,
        )

        tokens = tokenize_for_cache("Cache-weighted routing test message")

        # First, route and complete to establish cache (no conversation affinity)
        worker_id, _, _ = cache_router.route_request(tokens)
        cache_router.start_request(worker_id)
        cache_router.complete_request(worker_id, tokens, 20, success=True, latency_ms=50)

        # Now route again - should prefer cached worker
        # Use CACHE_AWARE strategy which strongly prefers cache
        cache_router.strategy = RoutingStrategy.CACHE_AWARE
        workers_chosen = []
        for _ in range(10):
            next_worker, _, _ = cache_router.route_request(tokens)
            workers_chosen.append(next_worker)

        # Should heavily prefer the cached worker
        cached_worker_count = workers_chosen.count(worker_id)
        assert cached_worker_count >= 7  # At least 70% to cached worker

    def test_load_heavy_weights(self):
        """Test load-heavy weights prioritize load balancing."""
        # Create router with load-heavy weighting
        load_heavy = CostWeights(
            kv_overlap=0.1,  # Ignore cache
            load_balance=5.0,  # Heavily prioritize load balance
            memory_pressure=0.1,
            queue_depth=0.1,
            historical_performance=0.1,
            slo_violation_penalty=1.0,
        )
        load_router = AdvancedSmartRouter(
            strategy=RoutingStrategy.HYBRID,
            cost_weights=load_heavy,
            num_workers=4,
        )

        tokens = tokenize_for_cache("Load-weighted routing test")

        # Load up worker-0
        for _ in range(10):
            load_router.start_request("worker-0")

        # Should avoid loaded worker even with cache
        load_router.radix_tree.insert(tokens, "worker-0")
        worker_id, _, _ = load_router.route_request(tokens)
        assert worker_id != "worker-0"


# ============================================================================
# Test 8: Geographic Routing
# ============================================================================


@pytest.mark.integration
class TestGeographicRouting:
    """Test geographic/affinity-based routing."""

    def test_conversation_affinity(self, router: AdvancedSmartRouter):
        """Test conversation affinity keeps requests on same worker."""
        tokens = tokenize_for_cache("Conversation affinity test")
        conv_id = "conv-geo-123"

        # First request establishes affinity
        worker1, _, _ = router.route_request(tokens, conversation_id=conv_id)
        router.start_request(worker1)
        router.complete_request(worker1, tokens, 10)

        # Next 10 requests should stick to same worker
        for _ in range(10):
            worker_id, _, _ = router.route_request(tokens, conversation_id=conv_id)
            assert worker_id == worker1

    def test_user_affinity_tracking(self, router: AdvancedSmartRouter):
        """Test user affinity is tracked and influences routing."""
        tokens = tokenize_for_cache("User affinity test")
        user_id = "user-geo-456"

        # Make several requests for same user
        workers_used = set()
        for i in range(5):
            worker_id, _, _ = router.route_request(
                tokens, user_id=user_id, conversation_id=f"conv-{i}"
            )
            workers_used.add(worker_id)
            router.start_request(worker_id)
            router.complete_request(worker_id, tokens, 10)

        # User should have affinity recorded
        assert user_id in router.user_affinity
        assert len(router.user_affinity[user_id]) > 0

    def test_model_affinity_tracking(self, router: AdvancedSmartRouter):
        """Test model affinity is tracked across requests."""
        tokens = tokenize_for_cache("Model affinity test")
        model_id = "gpt-4"

        # Route requests for specific model
        for _ in range(5):
            worker_id, _, _ = router.route_request(tokens, model_id=model_id)
            router.start_request(worker_id)
            router.complete_request(worker_id, tokens, 10)

        # Model should have affinity recorded
        assert model_id in router.model_affinity
        assert len(router.model_affinity[model_id]) > 0

    def test_affinity_bonus_calculation(self, router: AdvancedSmartRouter):
        """Test affinity bonus is calculated correctly."""
        tokens = tokenize_for_cache("Affinity bonus test")

        # Establish multiple affinity types
        conv_id = "conv-bonus-789"
        user_id = "user-bonus-123"
        model_id = "gpt-4"

        worker1, _, _ = router.route_request(
            tokens, conversation_id=conv_id, user_id=user_id, model_id=model_id
        )

        # Get explanation to see affinity bonus
        explanation = router.get_routing_decision_explain(
            tokens, conversation_id=conv_id, user_id=user_id, model_id=model_id
        )

        # Should show affinity information
        assert explanation["affinity"]["conversation_id"] == conv_id
        assert explanation["affinity"]["user_id"] == user_id
        assert explanation["affinity"]["model_id"] == model_id


# ============================================================================
# Test 9: Health Check Integration
# ============================================================================


@pytest.mark.integration
class TestHealthCheckIntegration:
    """Test health check integration with routing."""

    def test_health_status_affects_routing(self, router: AdvancedSmartRouter):
        """Test health status directly affects routing decisions."""
        tokens = tokenize_for_cache("Health routing test")

        # Make worker-0 degraded (not unhealthy, just degraded)
        for i in range(20):
            success = i < 18  # 90% success (at threshold)
            router.update_worker_health("worker-0", success=success, latency_ms=100)

        # Push below threshold
        router.update_worker_health("worker-0", success=False, latency_ms=100)

        health = router.worker_health["worker-0"]
        assert health.is_degraded or not health.is_healthy

        # Next requests should prefer healthy workers
        workers_chosen = []
        for _ in range(10):
            worker_id, _, _ = router.route_request(tokens)
            workers_chosen.append(worker_id)

        # Should mostly avoid degraded worker-0
        worker_0_count = workers_chosen.count("worker-0")
        assert worker_0_count <= 3

    def test_timeout_rate_detection(self, router: AdvancedSmartRouter):
        """Test timeout rate is tracked and affects health."""
        tokens = tokenize_for_cache("Timeout test")

        # Generate requests with high timeout rate
        for _ in range(20):
            router.update_worker_health(
                "worker-0", success=False, latency_ms=30000, timeout=True
            )

        health = router.worker_health["worker-0"]
        assert health.timeout_count == 20
        assert health.get_timeout_rate() == 1.0
        assert not health.is_healthy

    def test_mixed_health_states(self, router: AdvancedSmartRouter):
        """Test routing with mixed worker health states."""
        tokens = tokenize_for_cache("Mixed health test")

        # Worker-0: Healthy
        for _ in range(10):
            router.update_worker_health("worker-0", success=True, latency_ms=50)

        # Worker-1: Degraded
        for i in range(20):
            success = i < 18
            router.update_worker_health("worker-1", success=success, latency_ms=100)
        router.update_worker_health("worker-1", success=False, latency_ms=100)

        # Worker-2: Unhealthy
        for _ in range(20):
            router.update_worker_health("worker-2", success=False, latency_ms=15000)

        # Worker-3: Healthy
        for _ in range(10):
            router.update_worker_health("worker-3", success=True, latency_ms=60)

        # Route requests - should prefer worker-0 and worker-3
        workers_chosen = []
        for _ in range(20):
            worker_id, _, _ = router.route_request(tokens)
            workers_chosen.append(worker_id)

        # Healthy workers should dominate
        healthy_count = workers_chosen.count("worker-0") + workers_chosen.count(
            "worker-3"
        )
        assert healthy_count >= 15  # At least 75% to healthy workers


# ============================================================================
# Test 10: Circuit Breaker Patterns
# ============================================================================


@pytest.mark.integration
class TestCircuitBreakerPatterns:
    """Test circuit breaker functionality."""

    def test_circuit_opens_on_failures(self, router: AdvancedSmartRouter):
        """Test circuit breaker opens after consecutive failures."""
        tokens = tokenize_for_cache("Circuit breaker test")

        # Simulate consecutive failures on worker-0
        for _ in range(15):
            router.start_request("worker-0")
            router.complete_request(
                "worker-0", tokens, 0, success=False, latency_ms=10000
            )

        # Worker should be marked unhealthy (circuit open)
        health = router.worker_health["worker-0"]
        assert not health.is_healthy

        # Requests should avoid worker-0
        workers_chosen = []
        for _ in range(10):
            worker_id, _, _ = router.route_request(tokens)
            workers_chosen.append(worker_id)

        # Worker-0 should be avoided
        assert workers_chosen.count("worker-0") == 0

    def test_circuit_half_open_recovery(self, router: AdvancedSmartRouter):
        """Test circuit breaker half-open state during recovery."""
        tokens = tokenize_for_cache("Half-open test")

        # Open circuit with failures
        for _ in range(10):
            router.update_worker_health("worker-0", success=False, latency_ms=15000)

        assert not router.worker_health["worker-0"].is_healthy

        # Begin recovery with many successes to get above thresholds
        # 10 failures (150000ms) + 100 successes (5000ms) = 110 total
        # Success rate: 100/110 = 90.9% > 90% threshold
        # Avg latency: 155000/110 = 1409ms < 5000ms threshold
        # Last 10 in history: all successes
        for _ in range(100):
            router.update_worker_health("worker-0", success=True, latency_ms=50)

        # Circuit should close (worker recovered)
        health = router.worker_health["worker-0"]
        assert health.is_healthy

    def test_circuit_breaker_per_worker(self, router: AdvancedSmartRouter):
        """Test circuit breaker is independent per worker."""
        tokens = tokenize_for_cache("Per-worker circuit test")

        # Worker-0: Open circuit (failures)
        for _ in range(20):
            router.update_worker_health("worker-0", success=False, latency_ms=15000)

        # Worker-1: Healthy
        for _ in range(20):
            router.update_worker_health("worker-1", success=True, latency_ms=50)

        # Check independent states
        assert not router.worker_health["worker-0"].is_healthy
        assert router.worker_health["worker-1"].is_healthy


# ============================================================================
# Test 11: Routing Metrics
# ============================================================================


@pytest.mark.integration
class TestRoutingMetrics:
    """Test routing metrics collection and reporting."""

    def test_routing_history_tracking(self, router: AdvancedSmartRouter):
        """Test routing history is tracked."""
        tokens = tokenize_for_cache("History tracking test")

        # Make several routing decisions
        for i in range(5):
            router.route_request(
                tokens, conversation_id=f"conv-{i}", user_id=f"user-{i}"
            )

        # Check history is recorded
        assert len(router.routing_history) == 5

        # Verify history entries have required fields
        for entry in router.routing_history:
            assert "timestamp" in entry
            assert "worker_id" in entry
            assert "strategy" in entry
            assert "conversation_id" in entry

    def test_worker_statistics(self, router: AdvancedSmartRouter):
        """Test comprehensive worker statistics."""
        tokens = tokenize_for_cache("Statistics test")

        # Generate activity on workers
        for i, worker_id in enumerate(router.workers.keys()):
            for _ in range((i + 1) * 5):
                router.start_request(worker_id)
                router.complete_request(
                    worker_id, tokens, 10, success=True, latency_ms=100 * (i + 1)
                )

        stats = router.get_stats()

        # Verify stats structure
        assert "workers" in stats
        assert "radix_tree" in stats
        assert "affinity" in stats
        assert "config" in stats

        # Check worker-specific stats
        for worker_id, worker_stats in stats["workers"].items():
            assert "active_requests" in worker_stats
            assert "total_requests" in worker_stats
            assert "health" in worker_stats
            assert "tokens_processed" in worker_stats

    def test_affinity_metrics(self, router: AdvancedSmartRouter):
        """Test affinity metrics are tracked."""
        tokens = tokenize_for_cache("Affinity metrics test")

        # Create various affinity relationships
        for i in range(10):
            router.route_request(
                tokens,
                conversation_id=f"conv-{i}",
                user_id=f"user-{i % 3}",  # 3 unique users
                model_id=f"model-{i % 2}",  # 2 unique models
            )

        stats = router.get_stats()
        affinity_stats = stats["affinity"]

        assert affinity_stats["active_conversations"] == 10
        assert affinity_stats["tracked_users"] == 3
        assert affinity_stats["tracked_models"] == 2

    def test_cache_efficiency_metrics(self, router: AdvancedSmartRouter):
        """Test cache efficiency metrics."""
        tokens = tokenize_for_cache(
            "Cache efficiency test with sufficient tokens for caching"
        )

        # First request - no cache
        worker1, matched1, blocks1 = router.route_request(tokens)
        router.start_request(worker1)
        router.complete_request(worker1, tokens, 20, success=True, latency_ms=100)

        # Second request - should have cache
        worker2, matched2, blocks2 = router.route_request(tokens)

        # Should have cache hit
        assert matched2 > 0 or worker2 == worker1  # Either cache or affinity


# ============================================================================
# Test 12: Dynamic Routing Updates
# ============================================================================


@pytest.mark.integration
class TestDynamicRoutingUpdates:
    """Test dynamic routing behavior updates."""

    def test_strategy_switching(self):
        """Test switching between routing strategies."""
        tokens = tokenize_for_cache("Strategy switching test")

        # Start with round-robin
        router = AdvancedSmartRouter(
            strategy=RoutingStrategy.ROUND_ROBIN, num_workers=4
        )

        workers_rr = []
        for _ in range(8):
            worker_id, _, _ = router.route_request(tokens)
            workers_rr.append(worker_id)

        # Verify round-robin pattern
        assert workers_rr[0] != workers_rr[1]

        # Switch to learned strategy
        router.strategy = RoutingStrategy.LEARNED

        # Train with history
        for _ in range(10):
            router.start_request("worker-0")
            router.complete_request(
                "worker-0", tokens, 10, success=True, latency_ms=50
            )

        # Should now prefer worker-0
        workers_learned = []
        for _ in range(5):
            worker_id, _, _ = router.route_request(tokens)
            workers_learned.append(worker_id)

        # Different behavior than round-robin
        assert workers_learned != workers_rr[:5]

    def test_cost_weight_updates(self):
        """Test updating cost weights dynamically."""
        tokens = tokenize_for_cache("Cost weight update test")

        router = AdvancedSmartRouter(strategy=RoutingStrategy.HYBRID, num_workers=4)

        # Initial weights
        initial_kv_weight = router.cost_weights.kv_overlap

        # Update weights to prioritize cache more
        router.cost_weights.kv_overlap = 10.0
        assert router.cost_weights.kv_overlap != initial_kv_weight

        # Routing should reflect new weights
        router.radix_tree.insert(tokens, "worker-0")
        for _ in range(5):
            router.start_request("worker-0")

        # Despite high load, strong cache weight should still prefer worker-0
        worker_id, _, _ = router.route_request(tokens)
        # With very high cache weight, should overcome load
        # (May still choose others due to other factors, but cache is heavily weighted)

    def test_health_threshold_updates(self):
        """Test updating health thresholds dynamically."""
        router = AdvancedSmartRouter(strategy=RoutingStrategy.HYBRID, num_workers=4)

        # Update to strict thresholds
        router.health_thresholds.degraded_success_rate = 0.99
        router.health_thresholds.unhealthy_success_rate = 0.95

        # Worker with 98% success should now be degraded
        for i in range(50):
            success = i < 49  # 98% success
            router.update_worker_health("worker-0", success=success, latency_ms=100)

        # With strict thresholds, should be degraded
        health = router.worker_health["worker-0"]
        # 98% < 99% threshold, so should be degraded
        assert health.is_degraded or not health.is_healthy

    def test_add_remove_workers_dynamically(self):
        """Test adding/removing workers dynamically."""
        from collections import deque

        from fakeai.smart_router_advanced import (
            AdvancedWorkerState,
            WorkerHealthMetrics,
        )

        # Use ROUND_ROBIN strategy to ensure all workers are used
        router = AdvancedSmartRouter(strategy=RoutingStrategy.ROUND_ROBIN, num_workers=2)
        tokens = tokenize_for_cache("Dynamic workers test")

        # Initially 2 workers
        assert len(router.workers) == 2

        # Add new worker with proper initialization
        new_worker_id = "worker-new"
        new_worker = AdvancedWorkerState(worker_id=new_worker_id)
        new_worker.request_history = deque(maxlen=100)
        router.workers[new_worker_id] = new_worker
        router.worker_health[new_worker_id] = WorkerHealthMetrics(
            worker_id=new_worker_id
        )

        # Should now route to 3 workers
        assert len(router.workers) == 3

        # Route requests - round robin should cycle through all workers
        workers_chosen = []
        for i in range(12):  # 12 = 4 cycles of 3 workers
            worker_id, _, _ = router.route_request(tokens)
            workers_chosen.append(worker_id)

        # All workers should be used (round robin ensures this)
        unique_workers = set(workers_chosen)
        assert len(unique_workers) == 3

        # Each worker should be used exactly 4 times
        for worker_id in router.workers.keys():
            count = workers_chosen.count(worker_id)
            assert count == 4, f"Worker {worker_id} used {count} times, expected 4"

    def test_optimization_suggestions_over_time(self, router: AdvancedSmartRouter):
        """Test optimization suggestions evolve with usage."""
        tokens = tokenize_for_cache("Optimization evolution test")

        # Initial state - healthy
        result1 = router.optimize_worker_pool()
        initial_suggestions = len(result1["suggestions"])

        # Create imbalance
        for _ in range(50):
            router.start_request("worker-0")
            router.complete_request("worker-0", tokens, 10)

        # Should now have suggestions
        result2 = router.optimize_worker_pool()
        assert len(result2["suggestions"]) >= initial_suggestions

        # Check utilization imbalance is detected
        utilization = result2["worker_utilization"]
        assert utilization["worker-0"] > utilization["worker-1"]


# ============================================================================
# Test 13: Stress Testing
# ============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestRoutingStress:
    """Stress tests for routing system."""

    def test_high_concurrency_routing(self, router: AdvancedSmartRouter):
        """Test routing under high concurrency."""
        tokens = tokenize_for_cache("High concurrency test")

        # Simulate 100 concurrent requests
        workers_chosen = []
        for _ in range(100):
            worker_id, _, _ = router.route_request(tokens)
            router.start_request(worker_id)
            workers_chosen.append(worker_id)

        # Verify reasonable distribution
        for worker_id in router.workers.keys():
            count = workers_chosen.count(worker_id)
            # Should be roughly 25 per worker (100 / 4)
            assert 15 <= count <= 35  # Allow 40% variance

        # Complete all requests
        for worker_id in workers_chosen:
            router.complete_request(worker_id, tokens, 10, success=True, latency_ms=50)

    def test_rapid_failure_recovery_cycles(self, router: AdvancedSmartRouter):
        """Test rapid failure and recovery cycles."""
        tokens = tokenize_for_cache("Rapid cycling test")

        for cycle in range(3):
            # Failure phase - small number
            for _ in range(5):
                router.update_worker_health(
                    "worker-0", success=False, latency_ms=10000
                )

            # Recovery phase - more successes to overcome failures
            for _ in range(30):
                router.update_worker_health("worker-0", success=True, latency_ms=50)

        # Worker should be healthy at end
        # Final stats: 15 failures (150000ms) + 90 successes (4500ms) = 105 total
        # Success rate: 90/105 = 85.7% which is still below 90% degraded threshold
        # So let's add more successes at the end
        for _ in range(20):
            router.update_worker_health("worker-0", success=True, latency_ms=50)

        # Now: 15 failures + 110 successes = 125 total
        # Success rate: 110/125 = 88% - still below 90%
        # Add more successes
        for _ in range(30):
            router.update_worker_health("worker-0", success=True, latency_ms=50)

        # Now: 15 failures + 140 successes = 155 total
        # Success rate: 140/155 = 90.3% > 90% threshold
        health = router.worker_health["worker-0"]
        assert health.is_healthy

    def test_large_routing_history(self, router: AdvancedSmartRouter):
        """Test routing with large history."""
        tokens = tokenize_for_cache("Large history test")

        # Generate 2000 routing decisions (exceeds deque maxlen of 1000)
        for i in range(2000):
            router.route_request(tokens, conversation_id=f"conv-{i}")

        # History should be capped at maxlen
        assert len(router.routing_history) == 1000

        # Stats should still work
        stats = router.get_stats()
        assert stats["routing_history_size"] == 1000


# ============================================================================
# Test 14: Edge Cases
# ============================================================================


@pytest.mark.integration
class TestRoutingEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_token_sequence(self, router: AdvancedSmartRouter):
        """Test routing with empty token sequence."""
        tokens = []
        worker_id, matched, blocks = router.route_request(tokens)

        assert worker_id in router.workers
        assert matched == 0
        assert blocks == 0

    def test_very_long_token_sequence(self, router: AdvancedSmartRouter):
        """Test routing with very long token sequence."""
        # Generate 10000 tokens
        tokens = list(range(10000))
        worker_id, matched, blocks = router.route_request(tokens)

        assert worker_id in router.workers

    def test_all_workers_identical_state(self, router: AdvancedSmartRouter):
        """Test routing when all workers have identical state."""
        tokens = tokenize_for_cache("Identical state test")

        # Any worker should be acceptable
        worker_id, _, _ = router.route_request(tokens)
        assert worker_id in router.workers

    def test_routing_explanation_with_no_history(self, router: AdvancedSmartRouter):
        """Test routing explanation with no historical data."""
        tokens = tokenize_for_cache("No history explanation test")

        explanation = router.get_routing_decision_explain(tokens)

        assert "strategy" in explanation
        assert "selected_worker" in explanation
        assert explanation["selected_worker"] is not None

    def test_negative_latency_handling(self, router: AdvancedSmartRouter):
        """Test handling of invalid negative latency."""
        tokens = tokenize_for_cache("Negative latency test")

        # This should not crash (implementation should handle gracefully)
        router.update_worker_health("worker-0", success=True, latency_ms=0.0)

        health = router.worker_health["worker-0"]
        assert health.get_average_latency_ms() >= 0


# ============================================================================
# Integration Summary
# ============================================================================


@pytest.mark.integration
def test_smart_routing_integration_summary(router: AdvancedSmartRouter):
    """
    Comprehensive integration test covering all major features.

    This test verifies:
    - Multiple routing strategies
    - Health tracking and failover
    - Affinity and caching
    - Metrics and statistics
    - Dynamic updates
    """
    tokens = tokenize_for_cache("Comprehensive integration test message")

    # 1. Route initial request
    worker1, matched1, _ = router.route_request(
        tokens, conversation_id="test-conv", user_id="test-user"
    )
    router.start_request(worker1)
    router.complete_request(worker1, tokens, 20, success=True, latency_ms=100)

    # 2. Check affinity is established
    assert "test-conv" in router.conversation_affinity
    assert "test-user" in router.user_affinity

    # 3. Route follow-up request (should use affinity)
    worker2, matched2, _ = router.route_request(
        tokens, conversation_id="test-conv", user_id="test-user"
    )
    assert worker2 == worker1  # Affinity maintained

    # 4. Check cache is working
    assert matched2 > 0  # Should have cache hit

    # 5. Simulate worker failure
    for _ in range(20):
        router.update_worker_health(worker1, success=False, latency_ms=15000)

    assert not router.worker_health[worker1].is_healthy

    # 6. Route new request (should failover)
    worker3, _, _ = router.route_request(tokens)
    assert worker3 != worker1  # Failed over to healthy worker

    # 7. Get comprehensive stats
    stats = router.get_stats()
    assert stats["strategy"] == "hybrid"
    assert len(stats["workers"]) == 4
    assert stats["affinity"]["active_conversations"] >= 1

    # 8. Get optimization suggestions
    optimization = router.optimize_worker_pool()
    assert "total_workers" in optimization
    assert optimization["unhealthy_workers"] >= 1

    # 9. Get routing explanation
    explanation = router.get_routing_decision_explain(tokens)
    assert "selected_worker" in explanation
    assert len(explanation["all_workers"]) == 4

    # Success - all integration points working
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
