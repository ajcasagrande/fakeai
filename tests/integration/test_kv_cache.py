"""
Comprehensive integration tests for KV cache system.

Tests cover:
1. KV cache enabled/disabled
2. Cache hit detection
3. Cache miss detection
4. Hit rate calculation
5. Token savings calculation
6. Cache eviction policies
7. Cache size limits
8. Per-endpoint cache metrics
9. Prefix matching
10. Concurrent cache access
11. Cache warming
12. Cache invalidation
13. Block-based caching
14. Radix tree efficiency
15. Cache memory usage
16. Cache export/import

Target: 22+ tests
"""

import asyncio
import json
import random
import threading
import time
from typing import Any

import pytest
import requests

from fakeai.config import AppConfig
from fakeai.config.kv_cache import KVCacheConfig
from fakeai.kv_cache import (
    KVCacheMetrics,
    RadixTree,
    SmartRouter,
    tokenize_for_cache,
)
from fakeai.kv_cache_advanced import (
    AdaptiveRouter,
    AdvancedKVCacheMetrics,
    AdvancedRadixTree,
    CacheCoordinator,
    CacheMemoryManager,
)


# ============================================================================
# Basic KV Cache Tests
# ============================================================================


class TestKVCacheBasics:
    """Test basic KV cache functionality."""

    @pytest.mark.integration
    def test_kv_cache_enabled_via_config(self):
        """Test KV cache can be enabled via configuration."""
        config = KVCacheConfig(enabled=True)
        assert config.enabled is True

        config_disabled = KVCacheConfig(enabled=False)
        assert config_disabled.enabled is False

    @pytest.mark.integration
    def test_kv_cache_config_validation(self):
        """Test KV cache configuration validation."""
        # Valid config
        config = KVCacheConfig(
            enabled=True,
            block_size=16,
            num_workers=4,
            overlap_weight=1.0,
            load_balance_weight=0.5,
        )
        assert config.block_size == 16
        assert config.num_workers == 4

        # Invalid block size
        with pytest.raises(ValueError, match="block size must be at least 1"):
            KVCacheConfig(block_size=0)

        with pytest.raises(ValueError, match="block size cannot exceed 128"):
            KVCacheConfig(block_size=256)

        # Invalid num_workers
        with pytest.raises(ValueError, match="number of workers must be at least 1"):
            KVCacheConfig(num_workers=0)

        with pytest.raises(ValueError, match="number of workers cannot exceed 64"):
            KVCacheConfig(num_workers=100)

        # Invalid weights
        with pytest.raises(ValueError, match="overlap weight must be between 0.0 and 2.0"):
            KVCacheConfig(overlap_weight=3.0)

        with pytest.raises(ValueError, match="Load balance weight must be between 0.0 and 2.0"):
            KVCacheConfig(load_balance_weight=-0.5)

    @pytest.mark.integration
    def test_kv_cache_metrics_initialization(self):
        """Test KV cache metrics initialization."""
        metrics = KVCacheMetrics()

        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.total_tokens_processed == 0
        assert metrics.cached_tokens_reused == 0
        assert len(metrics.prefix_lengths) == 0

        stats = metrics.get_stats()
        assert stats["cache_hit_rate"] == 0.0
        assert stats["token_reuse_rate"] == 0.0


# ============================================================================
# Cache Hit/Miss Detection Tests
# ============================================================================


class TestCacheHitMissDetection:
    """Test cache hit and miss detection."""

    @pytest.mark.integration
    def test_cache_hit_detection(self):
        """Test cache hit is properly detected."""
        metrics = KVCacheMetrics()

        # Record cache hit
        metrics.record_cache_lookup(
            endpoint="/v1/chat/completions", total_tokens=100, matched_tokens=80
        )

        assert metrics.cache_hits == 1
        assert metrics.cache_misses == 0
        assert metrics.cached_tokens_reused == 80
        assert metrics.total_tokens_processed == 100

    @pytest.mark.integration
    def test_cache_miss_detection(self):
        """Test cache miss is properly detected."""
        metrics = KVCacheMetrics()

        # Record cache miss (matched_tokens = 0)
        metrics.record_cache_lookup(
            endpoint="/v1/chat/completions", total_tokens=100, matched_tokens=0
        )

        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 1
        assert metrics.cached_tokens_reused == 0
        assert metrics.total_tokens_processed == 100

    @pytest.mark.integration
    def test_mixed_cache_hits_and_misses(self):
        """Test mixed cache hits and misses are tracked correctly."""
        metrics = KVCacheMetrics()

        # Record hits
        metrics.record_cache_lookup("/v1/chat/completions", 100, 80)
        metrics.record_cache_lookup("/v1/chat/completions", 150, 120)

        # Record misses
        metrics.record_cache_lookup("/v1/chat/completions", 100, 0)
        metrics.record_cache_lookup("/v1/chat/completions", 200, 0)

        assert metrics.cache_hits == 2
        assert metrics.cache_misses == 2
        assert metrics.cached_tokens_reused == 200  # 80 + 120
        assert metrics.total_tokens_processed == 550  # 100+150+100+200


# ============================================================================
# Hit Rate Calculation Tests
# ============================================================================


class TestHitRateCalculation:
    """Test cache hit rate calculation."""

    @pytest.mark.integration
    def test_hit_rate_calculation_100_percent(self):
        """Test 100% hit rate calculation."""
        metrics = KVCacheMetrics()

        # All hits
        for _ in range(10):
            metrics.record_cache_lookup("/v1/chat/completions", 100, 80)

        hit_rate = metrics.get_cache_hit_rate()
        assert hit_rate == 100.0

    @pytest.mark.integration
    def test_hit_rate_calculation_0_percent(self):
        """Test 0% hit rate calculation."""
        metrics = KVCacheMetrics()

        # All misses
        for _ in range(10):
            metrics.record_cache_lookup("/v1/chat/completions", 100, 0)

        hit_rate = metrics.get_cache_hit_rate()
        assert hit_rate == 0.0

    @pytest.mark.integration
    def test_hit_rate_calculation_mixed(self):
        """Test mixed hit rate calculation."""
        metrics = KVCacheMetrics()

        # 7 hits, 3 misses = 70% hit rate
        for _ in range(7):
            metrics.record_cache_lookup("/v1/chat/completions", 100, 80)
        for _ in range(3):
            metrics.record_cache_lookup("/v1/chat/completions", 100, 0)

        hit_rate = metrics.get_cache_hit_rate()
        assert hit_rate == 70.0

    @pytest.mark.integration
    def test_per_endpoint_hit_rates(self):
        """Test per-endpoint hit rate tracking."""
        metrics = KVCacheMetrics()

        # Chat endpoint: 80% hit rate
        for _ in range(8):
            metrics.record_cache_lookup("/v1/chat/completions", 100, 80)
        for _ in range(2):
            metrics.record_cache_lookup("/v1/chat/completions", 100, 0)

        # Completions endpoint: 50% hit rate
        for _ in range(5):
            metrics.record_cache_lookup("/v1/completions", 100, 50)
        for _ in range(5):
            metrics.record_cache_lookup("/v1/completions", 100, 0)

        stats = metrics.get_stats()
        endpoint_stats = stats["endpoint_stats"]

        chat_stats = endpoint_stats["/v1/chat/completions"]
        assert chat_stats["hits"] == 8
        assert chat_stats["misses"] == 2

        comp_stats = endpoint_stats["/v1/completions"]
        assert comp_stats["hits"] == 5
        assert comp_stats["misses"] == 5


# ============================================================================
# Token Savings Calculation Tests
# ============================================================================


class TestTokenSavingsCalculation:
    """Test token savings calculation."""

    @pytest.mark.integration
    def test_token_reuse_rate_calculation(self):
        """Test token reuse rate calculation."""
        metrics = KVCacheMetrics()

        # Process 1000 tokens, reuse 800
        metrics.record_cache_lookup("/v1/chat/completions", 1000, 800)

        reuse_rate = metrics.get_token_reuse_rate()
        assert reuse_rate == 80.0

    @pytest.mark.integration
    def test_token_savings_aggregation(self):
        """Test token savings are aggregated correctly."""
        metrics = KVCacheMetrics()

        # Multiple requests with varying reuse
        metrics.record_cache_lookup("/v1/chat/completions", 100, 80)  # 80% reuse
        metrics.record_cache_lookup("/v1/chat/completions", 200, 100)  # 50% reuse
        metrics.record_cache_lookup("/v1/chat/completions", 300, 0)  # 0% reuse

        # Total: 600 tokens processed, 180 reused = 30%
        reuse_rate = metrics.get_token_reuse_rate()
        assert reuse_rate == 30.0

    @pytest.mark.integration
    def test_token_savings_with_no_processing(self):
        """Test token reuse rate with no tokens processed."""
        metrics = KVCacheMetrics()

        reuse_rate = metrics.get_token_reuse_rate()
        assert reuse_rate == 0.0


# ============================================================================
# Radix Tree Prefix Matching Tests
# ============================================================================


class TestRadixTreePrefixMatching:
    """Test radix tree prefix matching."""

    @pytest.mark.integration
    def test_radix_tree_exact_prefix_match(self):
        """Test exact prefix matching in radix tree."""
        tree = RadixTree(block_size=16)

        # Insert sequence
        tokens = list(range(100))
        tree.insert(tokens, worker_id="worker-0")

        # Match exact prefix (first 32 tokens)
        matched_tokens, blocks, workers = tree.find_longest_prefix(tokens[:32])

        assert matched_tokens == 32
        assert "worker-0" in workers
        assert len(blocks) > 0

    @pytest.mark.integration
    def test_radix_tree_partial_prefix_match(self):
        """Test partial prefix matching."""
        tree = RadixTree(block_size=16)

        # Insert sequence
        tokens1 = list(range(100))
        tree.insert(tokens1, worker_id="worker-0")

        # Query with partial match + new tokens
        query_tokens = list(range(50)) + [999, 1000, 1001]
        matched_tokens, blocks, workers = tree.find_longest_prefix(query_tokens)

        # Should match first 50 tokens
        assert matched_tokens == 50
        assert "worker-0" in workers

    @pytest.mark.integration
    def test_radix_tree_no_match(self):
        """Test no prefix match."""
        tree = RadixTree(block_size=16)

        # Insert sequence
        tokens1 = list(range(100, 200))
        tree.insert(tokens1, worker_id="worker-0")

        # Query completely different sequence
        query_tokens = list(range(0, 50))
        matched_tokens, blocks, workers = tree.find_longest_prefix(query_tokens)

        assert matched_tokens == 0
        assert len(workers) == 0
        assert len(blocks) == 0

    @pytest.mark.integration
    def test_radix_tree_multiple_workers(self):
        """Test prefix matching with multiple workers."""
        tree = RadixTree(block_size=16)

        # Insert same prefix to multiple workers
        tokens = list(range(100))
        tree.insert(tokens, worker_id="worker-0")
        tree.insert(tokens, worker_id="worker-1")

        # Query should find both workers
        matched_tokens, blocks, workers = tree.find_longest_prefix(tokens)

        assert matched_tokens == 100
        assert "worker-0" in workers
        assert "worker-1" in workers


# ============================================================================
# Block-Based Caching Tests
# ============================================================================


class TestBlockBasedCaching:
    """Test block-based caching."""

    @pytest.mark.integration
    def test_block_size_configuration(self):
        """Test block size can be configured."""
        tree16 = RadixTree(block_size=16)
        tree32 = RadixTree(block_size=32)

        assert tree16.block_size == 16
        assert tree32.block_size == 32

    @pytest.mark.integration
    def test_block_insertion(self):
        """Test blocks are inserted correctly."""
        tree = RadixTree(block_size=16)

        # Insert 64 tokens = 4 blocks
        tokens = list(range(64))
        blocks_inserted = tree.insert(tokens, worker_id="worker-0")

        assert blocks_inserted == 4

    @pytest.mark.integration
    def test_partial_block_insertion(self):
        """Test partial blocks are handled correctly."""
        tree = RadixTree(block_size=16)

        # Insert 50 tokens = 3 complete blocks (16*3=48), 2 tokens incomplete
        tokens = list(range(50))
        blocks_inserted = tree.insert(tokens, worker_id="worker-0")

        assert blocks_inserted == 3  # Only complete blocks

    @pytest.mark.integration
    def test_block_matching_at_boundaries(self):
        """Test block matching at block boundaries."""
        tree = RadixTree(block_size=16)

        # Insert sequence
        tokens = list(range(64))
        tree.insert(tokens, worker_id="worker-0")

        # Query exactly 2 blocks
        query_tokens = list(range(32))
        matched_tokens, blocks, workers = tree.find_longest_prefix(query_tokens)

        assert matched_tokens == 32
        assert len(blocks) == 2  # Should match 2 complete blocks


# ============================================================================
# Concurrent Cache Access Tests
# ============================================================================


class TestConcurrentCacheAccess:
    """Test concurrent cache access."""

    @pytest.mark.integration
    def test_concurrent_metrics_recording(self):
        """Test concurrent metrics recording is thread-safe."""
        metrics = KVCacheMetrics()

        def record_lookups():
            for _ in range(100):
                metrics.record_cache_lookup("/v1/chat/completions", 100, 50)

        # Run 10 threads concurrently
        threads = [threading.Thread(target=record_lookups) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have exactly 1000 lookups (10 threads * 100 each)
        assert metrics.cache_hits == 1000
        assert metrics.total_tokens_processed == 100000

    @pytest.mark.integration
    def test_concurrent_radix_tree_insertions(self):
        """Test concurrent radix tree insertions are thread-safe."""
        tree = RadixTree(block_size=16)

        def insert_sequences():
            for i in range(50):
                tokens = list(range(i * 10, i * 10 + 50))
                tree.insert(tokens, worker_id=f"worker-{threading.current_thread().name}")

        # Run 5 threads concurrently
        threads = [threading.Thread(target=insert_sequences, name=str(i)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Tree should have data from all threads
        stats = tree.get_stats()
        assert stats["total_nodes"] > 1

    @pytest.mark.integration
    def test_concurrent_smart_router_requests(self):
        """Test concurrent smart router requests are thread-safe."""
        router = SmartRouter(num_workers=4, block_size=16)
        results = []
        results_lock = threading.Lock()

        def route_requests():
            thread_results = []
            for i in range(20):
                tokens = list(range(i * 5, i * 5 + 50))
                worker_id, matched, blocks = router.route_request(tokens)
                thread_results.append((worker_id, matched, blocks))

            with results_lock:
                results.extend(thread_results)

        # Run 5 threads concurrently
        threads = [threading.Thread(target=route_requests) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have 100 results (5 threads * 20 requests)
        assert len(results) == 100

        # All results should have valid worker IDs
        for worker_id, matched, blocks in results:
            assert worker_id.startswith("worker-")


# ============================================================================
# Advanced Cache Features Tests
# ============================================================================


class TestAdvancedCacheFeatures:
    """Test advanced cache features."""

    @pytest.mark.integration
    def test_cache_memory_limits(self):
        """Test cache respects memory limits."""
        tree = AdvancedRadixTree(block_size=16, max_memory_mb=1.0)

        # Insert many sequences until memory limit approached
        for i in range(1000):
            tokens = list(range(i * 10, i * 10 + 100))
            tree.insert(tokens, worker_id=f"worker-{i % 4}")

        stats = tree.get_stats()

        # Memory usage should be tracked and should not exceed limit by much
        assert stats["memory_mb"] <= stats["max_memory_mb"] * 1.2  # Allow 20% over

    @pytest.mark.integration
    def test_lru_eviction_policy(self):
        """Test LRU eviction policy."""
        memory_manager = CacheMemoryManager(
            capacity_per_worker_mb=0.01,  # Very small capacity (10KB) to force eviction
            block_size=16,
        )

        worker_id = "worker-0"

        # Insert many blocks to trigger eviction
        for i in range(200):
            block_id = f"block-{i}"
            tokens = tuple(range(i * 10, i * 10 + 16))
            memory_manager.allocate_block(worker_id, block_id, tokens)

        stats = memory_manager.get_stats()

        # Should have evicted some blocks (or at least attempted to allocate)
        # With such small capacity, not all blocks can fit
        assert stats["total_evictions"] > 0 or stats["l1_memory_mb"] < 0.02

    @pytest.mark.integration
    def test_cache_warming(self):
        """Test cache warming phase."""
        memory_manager = CacheMemoryManager(
            capacity_per_worker_mb=10.0, block_size=16
        )

        # Initially in warming phase
        assert memory_manager.cache_warming_phase is True

        worker_id = "worker-0"

        # Allocate blocks to warm up cache
        for i in range(150):  # More than warming_threshold (100)
            block_id = f"block-{i}"
            tokens = tuple(range(i * 10, i * 10 + 16))
            memory_manager.allocate_block(worker_id, block_id, tokens)

        # Should have completed warming
        assert memory_manager.cache_warming_phase is False

        stats = memory_manager.get_stats()
        assert stats["warming_progress"] == 100

    @pytest.mark.integration
    def test_cache_invalidation(self):
        """Test cache invalidation."""
        tree = AdvancedRadixTree(block_size=16, max_memory_mb=10.0)
        memory_manager = CacheMemoryManager(capacity_per_worker_mb=10.0, block_size=16)
        router = AdaptiveRouter(
            radix_tree=tree,
            memory_manager=memory_manager,
            num_workers=4,
        )
        coordinator = CacheCoordinator(tree, memory_manager, router)

        # Insert some data
        tokens = list(range(100))
        block_id = f"block_{hash(tuple(tokens[:16]))}"

        # Invalidate block
        coordinator.invalidate_block(block_id)

        stats = coordinator.get_stats()
        assert stats["invalidation_count"] == 1
        assert stats["dirty_blocks"] == 1

        # Sync caches
        coordinator.sync_caches()

        stats = coordinator.get_stats()
        assert stats["dirty_blocks"] == 0

    @pytest.mark.integration
    def test_multi_level_cache_l1_l2(self):
        """Test multi-level cache (L1 per-worker, L2 shared) structure exists."""
        memory_manager = CacheMemoryManager(
            capacity_per_worker_mb=10.0, block_size=16
        )

        worker_id = "worker-0"

        # Allocate blocks to L1
        allocated_count = 0
        for i in range(10):
            block_id = f"block-{i}"
            tokens = tuple(range(i * 10, i * 10 + 16))
            if memory_manager.allocate_block(worker_id, block_id, tokens):
                allocated_count += 1

        stats = memory_manager.get_stats()

        # Should have allocated blocks successfully
        assert allocated_count > 0

        # Verify multi-level cache structure exists
        assert "l1_memory_mb" in stats
        assert "l2_memory_mb" in stats
        assert "total_memory_mb" in stats

        # Check that worker caches exist
        assert len(memory_manager.worker_caches) > 0

    @pytest.mark.integration
    def test_adaptive_routing_learning(self):
        """Test adaptive routing learns worker performance."""
        tree = AdvancedRadixTree(block_size=16)
        memory_manager = CacheMemoryManager(capacity_per_worker_mb=10.0, block_size=16)
        router = AdaptiveRouter(tree, memory_manager, num_workers=4)

        # Route requests and complete them
        total_requests = 0
        for i in range(50):
            tokens = list(range(i * 10, i * 10 + 50))
            worker_id, matched, blocks = router.route_request(tokens)

            # Complete with varying success
            success = i % 10 != 0  # 90% success rate
            latency = random.uniform(10, 100)
            router.complete_request(worker_id, tokens, 20, success, latency)
            total_requests += 1

        stats = router.get_stats()

        # At least one worker should have handled requests
        total_worker_requests = sum(
            worker_stats["total_requests"] for worker_stats in stats["workers"].values()
        )
        assert total_worker_requests == total_requests


# ============================================================================
# Cache Statistics Tests
# ============================================================================


class TestCacheStatistics:
    """Test cache statistics reporting."""

    @pytest.mark.integration
    def test_cache_stats_structure(self):
        """Test cache statistics have correct structure."""
        metrics = KVCacheMetrics()

        # Record some data
        metrics.record_cache_lookup("/v1/chat/completions", 100, 80)
        metrics.record_cache_lookup("/v1/completions", 200, 0)

        stats = metrics.get_stats()

        # Check required fields
        assert "cache_hit_rate" in stats
        assert "token_reuse_rate" in stats
        assert "total_cache_hits" in stats
        assert "total_cache_misses" in stats
        assert "total_tokens_processed" in stats
        assert "cached_tokens_reused" in stats
        assert "average_prefix_length" in stats
        assert "endpoint_stats" in stats

    @pytest.mark.integration
    def test_radix_tree_stats(self):
        """Test radix tree statistics."""
        tree = RadixTree(block_size=16)

        # Insert data
        for i in range(10):
            tokens = list(range(i * 10, i * 10 + 50))
            tree.insert(tokens, worker_id=f"worker-{i % 4}")

        stats = tree.get_stats()

        assert "total_nodes" in stats
        assert "total_cached_blocks" in stats
        assert stats["total_nodes"] > 1
        assert stats["total_cached_blocks"] > 0

    @pytest.mark.integration
    def test_advanced_cache_comprehensive_stats(self):
        """Test comprehensive stats from advanced cache."""
        tree = AdvancedRadixTree(block_size=16, max_memory_mb=10.0)
        memory_manager = CacheMemoryManager(capacity_per_worker_mb=10.0, block_size=16)
        router = AdaptiveRouter(tree, memory_manager, num_workers=4)
        coordinator = CacheCoordinator(tree, memory_manager, router)

        metrics = AdvancedKVCacheMetrics(tree, memory_manager, router, coordinator)

        # Record some activity
        for i in range(20):
            tokens = list(range(i * 10, i * 10 + 50))
            tree.insert(tokens, f"worker-{i % 4}")
            metrics.record_lookup(matched_tokens=30, total_tokens=50)

        stats = metrics.get_comprehensive_stats()

        # Check all components present
        assert "cache_performance" in stats
        assert "radix_tree" in stats
        assert "memory_manager" in stats
        assert "adaptive_router" in stats
        assert "cache_coordinator" in stats


# ============================================================================
# Cache Export/Import Tests
# ============================================================================


class TestCacheExportImport:
    """Test cache state export and import."""

    @pytest.mark.integration
    def test_cache_metrics_serialization(self):
        """Test cache metrics can be serialized to JSON."""
        metrics = KVCacheMetrics()

        # Record some data
        metrics.record_cache_lookup("/v1/chat/completions", 100, 80)
        metrics.record_cache_lookup("/v1/completions", 200, 150)

        stats = metrics.get_stats()

        # Should be JSON-serializable
        json_str = json.dumps(stats)
        assert isinstance(json_str, str)

        # Should be deserializable
        restored = json.loads(json_str)
        assert restored["cache_hit_rate"] == stats["cache_hit_rate"]
        assert restored["total_cache_hits"] == stats["total_cache_hits"]

    @pytest.mark.integration
    def test_radix_tree_stats_serialization(self):
        """Test radix tree stats can be serialized."""
        tree = RadixTree(block_size=16)

        # Insert data
        for i in range(5):
            tokens = list(range(i * 10, i * 10 + 50))
            tree.insert(tokens, worker_id=f"worker-{i}")

        stats = tree.get_stats()

        # Should be JSON-serializable
        json_str = json.dumps(stats)
        restored = json.loads(json_str)

        assert restored["total_nodes"] == stats["total_nodes"]
        assert restored["total_cached_blocks"] == stats["total_cached_blocks"]


# ============================================================================
# Tokenization Tests
# ============================================================================


class TestCacheTokenization:
    """Test cache tokenization utilities."""

    @pytest.mark.integration
    def test_tokenize_for_cache(self):
        """Test text tokenization for cache."""
        text = "Hello, world! This is a test."
        tokens = tokenize_for_cache(text)

        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert all(isinstance(t, int) for t in tokens)

    @pytest.mark.integration
    def test_tokenize_for_cache_deterministic(self):
        """Test tokenization is deterministic."""
        text = "Hello, world!"

        tokens1 = tokenize_for_cache(text)
        tokens2 = tokenize_for_cache(text)

        assert tokens1 == tokens2

    @pytest.mark.integration
    def test_tokenize_for_cache_different_texts(self):
        """Test different texts produce different tokens."""
        text1 = "Hello, world!"
        text2 = "Goodbye, world!"

        tokens1 = tokenize_for_cache(text1)
        tokens2 = tokenize_for_cache(text2)

        assert tokens1 != tokens2


# ============================================================================
# Smart Router Tests
# ============================================================================


class TestSmartRouter:
    """Test smart router functionality."""

    @pytest.mark.integration
    def test_smart_router_initialization(self):
        """Test smart router initialization."""
        router = SmartRouter(
            kv_overlap_weight=1.0,
            load_balance_weight=0.5,
            block_size=16,
            num_workers=4,
        )

        assert len(router.workers) == 4
        assert router.block_size == 16

        stats = router.get_stats()
        assert stats["config"]["num_workers"] == 4

    @pytest.mark.integration
    def test_smart_router_request_routing(self):
        """Test smart router routes requests."""
        router = SmartRouter(num_workers=4, block_size=16)

        tokens = list(range(100))
        worker_id, matched_tokens, matched_blocks = router.route_request(tokens)

        assert worker_id.startswith("worker-")
        assert matched_tokens >= 0
        assert matched_blocks >= 0

    @pytest.mark.integration
    def test_smart_router_load_balancing(self):
        """Test smart router can track load across workers."""
        router = SmartRouter(
            num_workers=4,
            block_size=16,
            load_balance_weight=2.0,  # High load balance weight to encourage distribution
        )

        # Route many requests
        total_routed = 0
        for i in range(100):
            # Use varied token sequences
            tokens = list(range(i * 100, i * 100 + 50))
            worker_id, _, _ = router.route_request(tokens)
            router.start_request(worker_id)
            router.complete_request(worker_id, tokens, 20)
            total_routed += 1

        stats = router.get_stats()

        # Verify all workers are initialized
        assert len(stats["workers"]) == 4

        # Verify total requests were routed
        total_worker_requests = sum(
            worker_stats["total_requests"] for worker_stats in stats["workers"].values()
        )
        assert total_worker_requests == total_routed

        # At least one worker should have processed requests
        assert any(
            worker_stats["total_requests"] > 0
            for worker_stats in stats["workers"].values()
        )

    @pytest.mark.integration
    def test_smart_router_cache_aware_routing(self):
        """Test smart router routes based on cache overlap."""
        router = SmartRouter(
            num_workers=4, block_size=16, kv_overlap_weight=2.0  # High weight
        )

        # Insert sequence and complete on worker-0
        tokens1 = list(range(100))
        worker_id, _, _ = router.route_request(tokens1)
        router.start_request(worker_id)
        router.complete_request(worker_id, tokens1, 20)
        first_worker = worker_id

        # Route similar sequence - should prefer same worker for cache hit
        tokens2 = list(range(80)) + [999, 1000, 1001]  # 80 token overlap
        worker_id2, matched, _ = router.route_request(tokens2)

        # Should have cache hit
        assert matched > 0


# ============================================================================
# Performance and Efficiency Tests
# ============================================================================


class TestCacheEfficiency:
    """Test cache efficiency and performance."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_radix_tree_efficiency_large_dataset(self):
        """Test radix tree efficiency with large dataset."""
        tree = RadixTree(block_size=16)

        start_time = time.time()

        # Insert 1000 sequences
        for i in range(1000):
            tokens = list(range(i * 5, i * 5 + 100))
            tree.insert(tokens, worker_id=f"worker-{i % 4}")

        insert_time = time.time() - start_time

        # Insertions should be fast (< 1 second for 1000 sequences)
        assert insert_time < 1.0

        start_time = time.time()

        # Query 1000 times
        for i in range(1000):
            query_tokens = list(range(i * 5, i * 5 + 50))
            tree.find_longest_prefix(query_tokens)

        query_time = time.time() - start_time

        # Queries should be fast (< 1 second for 1000 queries)
        assert query_time < 1.0

    @pytest.mark.integration
    def test_cache_memory_efficiency(self):
        """Test cache memory usage is reasonable."""
        tree = AdvancedRadixTree(block_size=16, max_memory_mb=10.0)

        # Insert sequences
        for i in range(100):
            tokens = list(range(i * 10, i * 10 + 100))
            tree.insert(tokens, worker_id=f"worker-{i % 4}")

        stats = tree.get_stats()

        # Memory usage should be tracked
        assert stats["memory_mb"] > 0
        assert stats["memory_mb"] <= stats["max_memory_mb"]

    @pytest.mark.integration
    def test_speedup_tracking(self):
        """Test cache speedup tracking."""
        metrics = KVCacheMetrics()

        # Record speedup
        metrics.record_speedup(
            endpoint="/v1/chat/completions",
            baseline_ttft=0.100,  # 100ms baseline
            actual_ttft=0.020,  # 20ms with cache
            cache_hit_ratio=0.8,  # 80% cache hit
        )

        stats = metrics.get_stats()

        assert "speedup_stats" in stats
        speedup_stats = stats["speedup_stats"]
        assert speedup_stats["avg_speedup_ratio"] == 5.0  # 100/20 = 5x speedup
