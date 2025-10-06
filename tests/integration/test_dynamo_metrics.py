"""
Integration Tests for AI-Dynamo Metrics Collection.

Comprehensive integration tests covering:
1. Dynamo metrics collection
2. Queue time tracking
3. Prefill latency
4. Decode latency
5. Batch efficiency
6. Request scheduling metrics
7. Dynamic batching stats
8. Iteration latency
9. KV cache hit rates in batching
10. Model parallelism metrics
11. Throughput optimization
12. Prometheus export
13. Real-time Dynamo dashboard data

These tests verify that the AI-Dynamo metrics system correctly
collects, aggregates, and exports metrics during realistic
request processing scenarios.
"""

import asyncio
import json
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from fakeai.app import app
from fakeai.config import AppConfig
from fakeai.dynamo_metrics import DynamoMetricsCollector
from fakeai.dynamo_metrics_advanced import (
    AdvancedDynamoMetrics,
    BatchOptimizer,
    DisaggregationTracker,
    QueueManager,
    RequestPriority,
)


@pytest.fixture
def client():
    """Test client with no auth required."""
    import fakeai.app as app_module

    app_module.server_ready = True
    return TestClient(app)


@pytest.fixture
def dynamo_collector():
    """Fresh DynamoMetricsCollector instance."""
    return DynamoMetricsCollector(window_size=300)


@pytest.fixture
def advanced_dynamo():
    """Fresh AdvancedDynamoMetrics instance."""
    return AdvancedDynamoMetrics(
        window_size=300,
        enable_queue_management=True,
        enable_batch_optimization=True,
        enable_disaggregation=True,
    )


@pytest.fixture
def queue_manager():
    """Fresh QueueManager instance."""
    return QueueManager()


@pytest.fixture
def batch_optimizer():
    """Fresh BatchOptimizer instance."""
    return BatchOptimizer(target_batch_size=32, max_padding_waste=20.0)


@pytest.fixture
def disaggregation_tracker():
    """Fresh DisaggregationTracker instance."""
    return DisaggregationTracker()


# ==============================================================================
# 1. Dynamo Metrics Collection Tests
# ==============================================================================


@pytest.mark.integration
@pytest.mark.dynamo
class TestDynamoMetricsCollection:
    """Test basic Dynamo metrics collection."""

    def test_start_and_complete_request(self, dynamo_collector):
        """Test request lifecycle tracking."""
        request_id = f"req-{uuid.uuid4().hex[:12]}"

        # Start request
        request = dynamo_collector.start_request(
            request_id=request_id,
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            input_tokens=100,
        )

        assert request.request_id == request_id
        assert request.model == "openai/gpt-oss-120b"
        assert request.input_tokens == 100
        assert dynamo_collector.total_requests == 1

        # Record phases
        time.sleep(0.01)  # Simulate queue time
        dynamo_collector.record_prefill_start(request_id)

        time.sleep(0.01)  # Simulate prefill time
        dynamo_collector.record_first_token(request_id)

        time.sleep(0.02)  # Simulate decode time
        dynamo_collector.complete_request(
            request_id=request_id,
            output_tokens=50,
            cached_tokens=0,
            kv_cache_hit=False,
            worker_id="worker-1",
            success=True,
        )

        # Verify completion
        assert dynamo_collector.successful_requests == 1
        assert len(dynamo_collector._active_requests) == 0

        # Get recent requests
        recent = dynamo_collector.get_recent_requests(60)
        assert len(recent) == 1
        assert recent[0].request_id == request_id
        assert recent[0].output_tokens == 50

    def test_multiple_concurrent_requests(self, dynamo_collector):
        """Test handling multiple concurrent requests."""
        request_ids = [f"req-{i}" for i in range(10)]

        # Start all requests
        for req_id in request_ids:
            dynamo_collector.start_request(
                request_id=req_id,
                model="openai/gpt-oss-120b",
                endpoint="/v1/chat/completions",
                input_tokens=100,
            )

        assert dynamo_collector.total_requests == 10
        assert len(dynamo_collector._active_requests) == 10

        # Complete all requests
        for req_id in request_ids:
            dynamo_collector.record_prefill_start(req_id)
            dynamo_collector.record_first_token(req_id)
            dynamo_collector.complete_request(
                request_id=req_id,
                output_tokens=50,
                success=True,
            )

        assert dynamo_collector.successful_requests == 10
        assert len(dynamo_collector._active_requests) == 0

    def test_failed_request_tracking(self, dynamo_collector):
        """Test tracking failed requests."""
        request_id = "req-failed"

        dynamo_collector.start_request(
            request_id=request_id,
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            input_tokens=100,
        )

        dynamo_collector.complete_request(
            request_id=request_id,
            output_tokens=0,
            success=False,
            finish_reason="error",
        )

        assert dynamo_collector.successful_requests == 0
        assert dynamo_collector.failed_requests == 1


# ==============================================================================
# 2. Queue Time Tracking Tests
# ==============================================================================


@pytest.mark.integration
@pytest.mark.dynamo
class TestQueueTimeTracking:
    """Test queue time tracking and statistics."""

    def test_queue_time_calculation(self, dynamo_collector):
        """Test accurate queue time calculation."""
        request_id = "req-queue-test"

        # Start request (enters queue)
        request = dynamo_collector.start_request(
            request_id=request_id,
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            input_tokens=100,
        )

        # Simulate queue wait time
        time.sleep(0.05)  # 50ms queue time

        # Start prefill (exits queue)
        dynamo_collector.record_prefill_start(request_id)
        dynamo_collector.record_first_token(request_id)

        dynamo_collector.complete_request(
            request_id=request_id,
            output_tokens=50,
            success=True,
        )

        # Get stats
        stats = dynamo_collector.get_latency_stats(60)
        queue_stats = stats["queue"]

        # Queue time should be around 50ms
        assert queue_stats["avg"] >= 40
        assert queue_stats["avg"] <= 60

    def test_queue_depth_tracking(self, dynamo_collector):
        """Test queue depth tracking."""
        # Record queue depths
        dynamo_collector.record_queue_depth(5)
        dynamo_collector.record_queue_depth(10)
        dynamo_collector.record_queue_depth(7)

        stats = dynamo_collector.get_queue_stats()

        assert stats["current_depth"] == 7
        assert stats["max_depth"] == 10
        assert stats["avg_depth"] > 0

    def test_multi_tier_queue_management(self, queue_manager):
        """Test multi-tier queue with priorities."""
        # Enqueue different priority requests
        success, reason = queue_manager.enqueue(RequestPriority.CRITICAL)
        assert success is True

        success, reason = queue_manager.enqueue(RequestPriority.NORMAL)
        assert success is True

        # Check per-priority stats
        critical_stats = queue_manager.get_queue_stats(RequestPriority.CRITICAL)
        assert critical_stats["current_depth"] == 1
        assert critical_stats["total_enqueued"] == 1

        normal_stats = queue_manager.get_queue_stats(RequestPriority.NORMAL)
        assert normal_stats["current_depth"] == 1
        assert normal_stats["total_enqueued"] == 1


# ==============================================================================
# 3. Prefill Latency Tests
# ==============================================================================


@pytest.mark.integration
@pytest.mark.dynamo
class TestPrefillLatency:
    """Test prefill phase latency tracking."""

    def test_prefill_time_measurement(self, dynamo_collector):
        """Test prefill time measurement."""
        request_id = "req-prefill"

        dynamo_collector.start_request(
            request_id=request_id,
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            input_tokens=100,
        )

        # Simulate prefill phase
        dynamo_collector.record_prefill_start(request_id)
        time.sleep(0.03)  # 30ms prefill time
        dynamo_collector.record_first_token(request_id)

        dynamo_collector.complete_request(
            request_id=request_id,
            output_tokens=50,
            success=True,
        )

        stats = dynamo_collector.get_latency_stats(60)
        prefill_stats = stats["prefill"]

        # Prefill time should be around 30ms
        assert prefill_stats["avg"] >= 25
        assert prefill_stats["avg"] <= 40

    def test_prefill_percentiles(self, dynamo_collector):
        """Test prefill latency percentiles."""
        # Generate requests with varying prefill times
        for i in range(20):
            request_id = f"req-prefill-{i}"

            dynamo_collector.start_request(
                request_id=request_id,
                model="openai/gpt-oss-120b",
                endpoint="/v1/chat/completions",
                input_tokens=100 + i * 10,
            )

            dynamo_collector.record_prefill_start(request_id)
            time.sleep(0.01 + i * 0.001)  # Variable prefill time
            dynamo_collector.record_first_token(request_id)

            dynamo_collector.complete_request(
                request_id=request_id,
                output_tokens=50,
                success=True,
            )

        stats = dynamo_collector.get_latency_stats(60)
        prefill_stats = stats["prefill"]

        # Verify percentiles exist
        assert prefill_stats["p50"] > 0
        assert prefill_stats["p90"] > 0
        assert prefill_stats["p99"] > 0
        assert prefill_stats["p99"] >= prefill_stats["p90"]
        assert prefill_stats["p90"] >= prefill_stats["p50"]


# ==============================================================================
# 4. Decode Latency Tests
# ==============================================================================


@pytest.mark.integration
@pytest.mark.dynamo
class TestDecodeLatency:
    """Test decode phase latency tracking."""

    def test_decode_time_measurement(self, dynamo_collector):
        """Test decode time and per-token latency."""
        request_id = "req-decode"

        dynamo_collector.start_request(
            request_id=request_id,
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            input_tokens=100,
        )

        dynamo_collector.record_prefill_start(request_id)
        dynamo_collector.record_first_token(request_id)

        # Simulate decode phase
        time.sleep(0.05)  # 50ms decode time

        dynamo_collector.complete_request(
            request_id=request_id,
            output_tokens=50,  # 50 tokens in 50ms = ~1ms per token
            success=True,
        )

        recent = dynamo_collector.get_recent_requests(60)
        assert len(recent) == 1

        request = recent[0]
        # ITL should be around 1ms per token
        assert request.itl_ms > 0

    def test_tpot_calculation(self, dynamo_collector):
        """Test Time Per Output Token (TPOT) calculation."""
        request_id = "req-tpot"

        dynamo_collector.start_request(
            request_id=request_id,
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            input_tokens=100,
        )

        dynamo_collector.record_prefill_start(request_id)
        dynamo_collector.record_first_token(request_id)
        time.sleep(0.1)  # 100ms for decode

        dynamo_collector.complete_request(
            request_id=request_id,
            output_tokens=100,  # 100 tokens
            success=True,
        )

        recent = dynamo_collector.get_recent_requests(60)
        request = recent[0]

        # TPOT should be around 1ms per token (100ms / 100 tokens)
        assert 0.5 <= request.tpot_ms <= 2.0


# ==============================================================================
# 5. Batch Efficiency Tests
# ==============================================================================


@pytest.mark.integration
@pytest.mark.dynamo
class TestBatchEfficiency:
    """Test batch efficiency tracking and optimization."""

    def test_batch_size_tracking(self, dynamo_collector):
        """Test batch size tracking."""
        # Record batch sizes
        dynamo_collector.record_batch_size(16)
        dynamo_collector.record_batch_size(24)
        dynamo_collector.record_batch_size(32)

        stats = dynamo_collector.get_batch_stats()

        assert stats["current_size"] == 32
        assert stats["avg_size"] > 0
        assert stats["max_size"] == 32

    def test_batch_padding_efficiency(self, batch_optimizer):
        """Test batch padding efficiency tracking."""
        batch_id = "batch-1"

        # Start batch with varying input token counts
        input_tokens = [100, 150, 120, 180, 200]  # Max 200
        batch = batch_optimizer.start_batch(
            batch_id=batch_id, batch_size=5, input_tokens_per_request=input_tokens
        )

        # Calculate expected padding
        max_tokens = 200
        total_padding = sum(max_tokens - tokens for tokens in input_tokens)

        assert batch.total_padding_tokens == total_padding
        assert batch.max_input_tokens == 200
        assert batch.min_input_tokens == 100
        assert batch.padding_waste_percentage > 0

    def test_batch_efficiency_score(self, batch_optimizer):
        """Test batch efficiency score calculation."""
        batch_id = "batch-2"

        # Efficient batch with larger size (low padding, good batch size)
        input_tokens = [190 + i for i in range(24)]  # 24 requests with low variance
        batch = batch_optimizer.start_batch(
            batch_id=batch_id, batch_size=24, input_tokens_per_request=input_tokens
        )

        batch_optimizer.complete_batch(batch_id, output_tokens=1200)

        # Check efficiency score
        completed_batch = list(batch_optimizer.completed_batches)[-1]
        # Efficiency considers both padding waste (low) and batch size (24/32 = 0.75)
        # Should be reasonably efficient
        assert completed_batch.efficiency_score > 60.0

    def test_optimal_batch_size_recommendation(self, batch_optimizer):
        """Test optimal batch size recommendation."""
        # Create several batches with different efficiencies
        for i in range(10):
            batch_id = f"batch-{i}"
            # Efficient batches with size around 24
            input_tokens = [100 + j * 5 for j in range(24)]
            batch_optimizer.start_batch(
                batch_id=batch_id, batch_size=24, input_tokens_per_request=input_tokens
            )
            batch_optimizer.complete_batch(batch_id, output_tokens=100)

        optimal_size = batch_optimizer.get_optimal_batch_size()
        # Should recommend 24 or default 32 (target_batch_size) if no batches meet threshold
        assert optimal_size in [24, 32]


# ==============================================================================
# 6. Request Scheduling Metrics Tests
# ==============================================================================


@pytest.mark.integration
@pytest.mark.dynamo
class TestRequestScheduling:
    """Test request scheduling and routing metrics."""

    def test_priority_based_scheduling(self, advanced_dynamo):
        """Test priority-based request scheduling."""
        # Start requests with different priorities
        high_priority_id = "req-high"
        normal_priority_id = "req-normal"

        # High priority request
        request_high, reason = advanced_dynamo.start_request(
            request_id=high_priority_id,
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            input_tokens=100,
            priority=RequestPriority.HIGH,
        )

        assert request_high is not None
        assert request_high.priority == RequestPriority.HIGH

        # Normal priority request
        request_normal, reason = advanced_dynamo.start_request(
            request_id=normal_priority_id,
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            input_tokens=100,
            priority=RequestPriority.NORMAL,
        )

        assert request_normal is not None
        assert request_normal.priority == RequestPriority.NORMAL

    def test_router_decision_timing(self, advanced_dynamo):
        """Test router decision timing tracking."""
        request_id = "req-router"

        request, reason = advanced_dynamo.start_request(
            request_id=request_id,
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            input_tokens=100,
        )

        # Record router decision
        start_time = time.time()
        time.sleep(0.001)  # 1ms router decision
        end_time = time.time()

        advanced_dynamo.record_router_decision(request_id, start_time, end_time)

        # Complete request
        advanced_dynamo.record_scheduler_queue_exit(request_id)
        advanced_dynamo.record_worker_queue_exit(request_id)
        advanced_dynamo.record_first_token(request_id)

        advanced_dynamo.complete_request(
            request_id=request_id,
            output_tokens=50,
            success=True,
        )

        # Verify router timing
        recent = advanced_dynamo.get_recent_requests(60)
        assert len(recent) == 1
        assert recent[0].router_decision_time_us > 0


# ==============================================================================
# 7. Dynamic Batching Stats Tests
# ==============================================================================


@pytest.mark.integration
@pytest.mark.dynamo
class TestDynamicBatching:
    """Test dynamic batching statistics."""

    def test_dynamic_batch_formation(self, batch_optimizer):
        """Test dynamic batch formation tracking."""
        # Create batches of varying sizes
        batch_sizes = [8, 16, 24, 32, 16, 20]

        for i, size in enumerate(batch_sizes):
            batch_id = f"batch-{i}"
            input_tokens = [100 + j for j in range(size)]

            batch_optimizer.start_batch(
                batch_id=batch_id, batch_size=size, input_tokens_per_request=input_tokens
            )
            batch_optimizer.complete_batch(batch_id, output_tokens=size * 50)

        stats = batch_optimizer.get_batch_stats()

        assert stats["total_batches_processed"] == len(batch_sizes)
        assert stats["avg_batch_size"] > 0
        assert stats["min_batch_size"] == 8
        assert stats["max_batch_size"] == 32

    def test_batch_padding_waste_tracking(self, batch_optimizer):
        """Test batch padding waste tracking."""
        # Create batch with high padding waste
        batch_id = "batch-high-padding"
        input_tokens = [50, 100, 150, 200, 250]  # High variance

        batch_optimizer.start_batch(
            batch_id=batch_id, batch_size=5, input_tokens_per_request=input_tokens
        )
        batch_optimizer.complete_batch(batch_id, output_tokens=100)

        stats = batch_optimizer.get_batch_stats()

        # Should have measurable padding waste
        assert stats["avg_padding_waste"] > 0
        assert stats["max_padding_waste"] > 0


# ==============================================================================
# 8. Iteration Latency Tests
# ==============================================================================


@pytest.mark.integration
@pytest.mark.dynamo
class TestIterationLatency:
    """Test per-iteration latency tracking."""

    def test_first_token_latency(self, dynamo_collector):
        """Test time to first token (TTFT) measurement."""
        request_id = "req-ttft"

        start_time = time.time()

        dynamo_collector.start_request(
            request_id=request_id,
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            input_tokens=100,
        )

        time.sleep(0.02)  # Simulate processing time
        dynamo_collector.record_prefill_start(request_id)

        time.sleep(0.03)  # Simulate prefill
        dynamo_collector.record_first_token(request_id)

        dynamo_collector.complete_request(
            request_id=request_id,
            output_tokens=50,
            success=True,
        )

        recent = dynamo_collector.get_recent_requests(60)
        request = recent[0]

        # TTFT should be around 50ms (20ms + 30ms)
        assert request.ttft_ms >= 40
        assert request.ttft_ms <= 60

    def test_inter_token_latency_statistics(self, dynamo_collector):
        """Test inter-token latency (ITL) statistics."""
        # Generate multiple requests
        for i in range(10):
            request_id = f"req-itl-{i}"

            dynamo_collector.start_request(
                request_id=request_id,
                model="openai/gpt-oss-120b",
                endpoint="/v1/chat/completions",
                input_tokens=100,
            )

            dynamo_collector.record_prefill_start(request_id)
            dynamo_collector.record_first_token(request_id)

            time.sleep(0.01 + i * 0.001)  # Variable decode time

            dynamo_collector.complete_request(
                request_id=request_id,
                output_tokens=50,
                success=True,
            )

        stats = dynamo_collector.get_latency_stats(60)
        itl_stats = stats["itl"]

        # Should have ITL metrics
        assert itl_stats["avg"] > 0
        assert itl_stats["p50"] > 0
        assert itl_stats["p90"] > 0
        assert itl_stats["p99"] > 0


# ==============================================================================
# 9. KV Cache Hit Rates in Batching Tests
# ==============================================================================


@pytest.mark.integration
@pytest.mark.dynamo
class TestKVCacheHitRates:
    """Test KV cache hit rates in batching scenarios."""

    def test_kv_cache_hit_tracking(self, dynamo_collector):
        """Test KV cache hit tracking."""
        # Request with cache hit
        request_id_hit = "req-cache-hit"
        dynamo_collector.start_request(
            request_id=request_id_hit,
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            input_tokens=100,
        )

        dynamo_collector.record_prefill_start(request_id_hit)
        dynamo_collector.record_first_token(request_id_hit)

        dynamo_collector.complete_request(
            request_id=request_id_hit,
            output_tokens=50,
            cached_tokens=50,  # 50% cache hit
            kv_cache_hit=True,
            success=True,
        )

        # Request with cache miss
        request_id_miss = "req-cache-miss"
        dynamo_collector.start_request(
            request_id=request_id_miss,
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            input_tokens=100,
        )

        dynamo_collector.record_prefill_start(request_id_miss)
        dynamo_collector.record_first_token(request_id_miss)

        dynamo_collector.complete_request(
            request_id=request_id_miss,
            output_tokens=50,
            cached_tokens=0,
            kv_cache_hit=False,
            success=True,
        )

        cache_stats = dynamo_collector.get_cache_stats(60)

        # Should have 50% hit rate (1 hit, 1 miss)
        assert cache_stats["hit_rate"] == 50.0
        assert cache_stats["total_cached_tokens"] == 50

    def test_kv_cache_overlap_score(self, dynamo_collector):
        """Test KV cache overlap score tracking."""
        request_id = "req-overlap"

        dynamo_collector.start_request(
            request_id=request_id,
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            input_tokens=100,
        )

        # Manually set overlap score
        if request_id in dynamo_collector._active_requests:
            dynamo_collector._active_requests[request_id].kv_cache_overlap_score = 0.75
            dynamo_collector._active_requests[request_id].kv_cache_blocks_matched = 10

        dynamo_collector.record_prefill_start(request_id)
        dynamo_collector.record_first_token(request_id)

        dynamo_collector.complete_request(
            request_id=request_id,
            output_tokens=50,
            kv_cache_hit=True,
            success=True,
        )

        cache_stats = dynamo_collector.get_cache_stats(60)

        assert cache_stats["avg_overlap_score"] > 0
        assert cache_stats["avg_blocks_matched"] > 0


# ==============================================================================
# 10. Model Parallelism Metrics Tests
# ==============================================================================


@pytest.mark.integration
@pytest.mark.dynamo
class TestModelParallelismMetrics:
    """Test model parallelism and worker distribution metrics."""

    def test_worker_assignment_tracking(self, dynamo_collector):
        """Test worker assignment tracking."""
        # Assign requests to different workers
        for i in range(10):
            request_id = f"req-worker-{i}"
            worker_id = f"worker-{i % 3}"  # 3 workers

            dynamo_collector.start_request(
                request_id=request_id,
                model="openai/gpt-oss-120b",
                endpoint="/v1/chat/completions",
                input_tokens=100,
            )

            dynamo_collector.record_prefill_start(request_id)
            dynamo_collector.record_first_token(request_id)

            dynamo_collector.complete_request(
                request_id=request_id,
                output_tokens=50,
                worker_id=worker_id,
                success=True,
            )

        recent = dynamo_collector.get_recent_requests(60)

        # Verify worker assignments
        worker_counts = {}
        for req in recent:
            worker_counts[req.worker_id] = worker_counts.get(req.worker_id, 0) + 1

        assert len(worker_counts) == 3
        # Should be roughly evenly distributed
        for count in worker_counts.values():
            assert 2 <= count <= 5

    def test_disaggregation_prefill_decode(self, disaggregation_tracker):
        """Test prefill/decode disaggregation tracking."""
        # Record prefill requests
        for i in range(5):
            disaggregation_tracker.record_prefill_request(
                worker_id=f"prefill-worker-{i % 2}",
                kv_cache_size_bytes=1024 * 100,  # 100KB
            )

        # Record decode requests
        for i in range(10):
            disaggregation_tracker.record_decode_request(
                worker_id=f"decode-worker-{i % 3}"
            )

        stats = disaggregation_tracker.get_stats(60)

        assert stats["prefill_requests"] == 5
        assert stats["decode_requests"] == 10
        assert stats["total_requests"] == 15
        # Prefill ratio should be 33.33% (5/15)
        assert 30.0 <= stats["prefill_ratio"] <= 35.0

    def test_kv_transfer_tracking(self, disaggregation_tracker):
        """Test KV cache transfer between workers."""
        # Record KV transfers
        for i in range(5):
            disaggregation_tracker.record_kv_transfer(
                prefill_worker_id="prefill-worker-0",
                decode_worker_id="decode-worker-0",
                transfer_bytes=1024 * 50,  # 50KB
                transfer_time_ms=5.0,
                overhead_us=100.0,
            )

        stats = disaggregation_tracker.get_stats(60)

        assert stats["cross_worker_transfers"] == 5
        assert stats["kv_transfer_bytes"] == 1024 * 50 * 5
        assert stats["kv_transfer_time_ms"] == 25.0  # 5 transfers * 5ms
        assert stats["disaggregation_overhead_us"] == 500.0  # 5 * 100us


# ==============================================================================
# 11. Throughput Optimization Tests
# ==============================================================================


@pytest.mark.integration
@pytest.mark.dynamo
class TestThroughputOptimization:
    """Test throughput optimization metrics."""

    def test_throughput_calculation(self, dynamo_collector):
        """Test requests per second and tokens per second."""
        # Generate multiple requests quickly
        start_time = time.time()

        for i in range(20):
            request_id = f"req-throughput-{i}"

            dynamo_collector.start_request(
                request_id=request_id,
                model="openai/gpt-oss-120b",
                endpoint="/v1/chat/completions",
                input_tokens=100,
            )

            dynamo_collector.record_prefill_start(request_id)
            dynamo_collector.record_first_token(request_id)

            dynamo_collector.complete_request(
                request_id=request_id,
                output_tokens=50,
                success=True,
            )

        throughput_stats = dynamo_collector.get_throughput_stats(60)

        # Should have positive throughput
        assert throughput_stats["requests_per_second"] > 0
        assert throughput_stats["tokens_per_second"] > 0
        assert throughput_stats["input_tokens_per_second"] > 0
        assert throughput_stats["output_tokens_per_second"] > 0

    def test_per_model_throughput(self, dynamo_collector):
        """Test per-model throughput tracking."""
        models = ["openai/gpt-oss-120b", "meta-llama/Llama-3.1-8B-Instruct"]

        for model in models:
            for i in range(5):
                request_id = f"req-{model}-{i}"

                dynamo_collector.start_request(
                    request_id=request_id,
                    model=model,
                    endpoint="/v1/chat/completions",
                    input_tokens=100,
                )

                dynamo_collector.record_prefill_start(request_id)
                dynamo_collector.record_first_token(request_id)

                dynamo_collector.complete_request(
                    request_id=request_id,
                    output_tokens=50,
                    success=True,
                )

        model_stats = dynamo_collector.get_model_stats()

        # Both models should have stats
        assert len(model_stats) == 2
        for model in models:
            assert model in model_stats
            assert model_stats[model]["requests"] == 5
            # Model stats tracks output tokens only in basic version
            assert model_stats[model]["total_tokens"] == 250  # 5 * 50


# ==============================================================================
# 12. Prometheus Export Tests
# ==============================================================================


@pytest.mark.integration
@pytest.mark.dynamo
class TestPrometheusExport:
    """Test Prometheus format export."""

    def test_prometheus_format(self, dynamo_collector):
        """Test Prometheus metrics export format."""
        # Generate some metrics
        for i in range(5):
            request_id = f"req-prom-{i}"

            dynamo_collector.start_request(
                request_id=request_id,
                model="openai/gpt-oss-120b",
                endpoint="/v1/chat/completions",
                input_tokens=100,
            )

            dynamo_collector.record_prefill_start(request_id)
            dynamo_collector.record_first_token(request_id)

            dynamo_collector.complete_request(
                request_id=request_id,
                output_tokens=50,
                success=True,
            )

        prometheus_output = dynamo_collector.get_prometheus_metrics()

        # Verify Prometheus format
        assert isinstance(prometheus_output, str)
        assert "# TYPE fakeai_dynamo_requests_total counter" in prometheus_output
        assert "fakeai_dynamo_requests_total" in prometheus_output
        assert "fakeai_dynamo_ttft_seconds" in prometheus_output
        assert "fakeai_dynamo_itl_seconds" in prometheus_output
        assert "fakeai_dynamo_tokens_per_second" in prometheus_output
        assert 'quantile="0.5"' in prometheus_output
        assert 'quantile="0.9"' in prometheus_output
        assert 'quantile="0.99"' in prometheus_output

    def test_prometheus_metrics_values(self, dynamo_collector):
        """Test Prometheus metrics contain valid values."""
        # Generate metrics
        dynamo_collector.start_request(
            request_id="req-test",
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            input_tokens=100,
        )

        dynamo_collector.record_prefill_start("req-test")
        dynamo_collector.record_first_token("req-test")

        dynamo_collector.complete_request(
            request_id="req-test",
            output_tokens=50,
            success=True,
        )

        prometheus_output = dynamo_collector.get_prometheus_metrics()

        # Should contain numeric values
        lines = prometheus_output.split("\n")
        metric_lines = [line for line in lines if not line.startswith("#") and line]

        assert len(metric_lines) > 0

        # Verify each metric line has a value
        for line in metric_lines:
            if line.strip():
                parts = line.rsplit(" ", 1)
                assert len(parts) == 2
                value = float(parts[1])
                assert value >= 0


# ==============================================================================
# 13. Real-Time Dynamo Dashboard Data Tests
# ==============================================================================


@pytest.mark.integration
@pytest.mark.dynamo
class TestDynamoDashboard:
    """Test real-time dashboard data aggregation."""

    def test_complete_stats_dict(self, dynamo_collector):
        """Test complete statistics dictionary for dashboard."""
        # Generate diverse metrics
        for i in range(10):
            request_id = f"req-dashboard-{i}"

            dynamo_collector.start_request(
                request_id=request_id,
                model="openai/gpt-oss-120b",
                endpoint="/v1/chat/completions",
                input_tokens=100,
            )

            dynamo_collector.record_queue_depth(i)
            dynamo_collector.record_batch_size(16 + i)

            dynamo_collector.record_prefill_start(request_id)
            dynamo_collector.record_first_token(request_id)

            dynamo_collector.complete_request(
                request_id=request_id,
                output_tokens=50,
                cached_tokens=i * 5,
                kv_cache_hit=i % 2 == 0,
                success=True,
            )

        stats = dynamo_collector.get_stats_dict()

        # Verify all dashboard sections exist
        assert "summary" in stats
        assert "latency" in stats
        assert "throughput" in stats
        assert "queue" in stats
        assert "batch" in stats
        assert "cache" in stats
        assert "disaggregation" in stats
        assert "per_model" in stats

        # Verify summary
        summary = stats["summary"]
        assert summary["total_requests"] == 10
        assert summary["successful_requests"] == 10
        assert summary["failed_requests"] == 0
        assert summary["active_requests"] == 0

        # Verify latency breakdown
        latency = stats["latency"]
        assert "ttft" in latency
        assert "itl" in latency
        assert "total" in latency
        assert "queue" in latency
        assert "prefill" in latency
        assert "decode" in latency

    def test_advanced_dashboard_metrics(self, advanced_dynamo):
        """Test advanced dashboard with all components."""
        # Generate requests
        for i in range(5):
            request_id = f"req-advanced-{i}"

            request, reason = advanced_dynamo.start_request(
                request_id=request_id,
                model="openai/gpt-oss-120b",
                endpoint="/v1/chat/completions",
                input_tokens=100,
                priority=RequestPriority.NORMAL,
            )

            advanced_dynamo.record_scheduler_queue_exit(request_id)
            advanced_dynamo.record_worker_queue_exit(request_id)
            advanced_dynamo.record_first_token(request_id)

            advanced_dynamo.complete_request(
                request_id=request_id,
                output_tokens=50,
                success=True,
            )

        stats = advanced_dynamo.get_stats_dict(60)

        # Should have all components
        assert "summary" in stats
        assert "latency" in stats
        assert "long_tail" in stats
        assert "per_model" in stats
        assert "request_distribution" in stats
        assert "queues" in stats  # Multi-tier queue stats
        assert "batch" in stats  # Batch optimization stats
        assert "disaggregation" in stats  # Disaggregation stats

        # Verify advanced latency metrics
        latency = stats["latency"]
        assert "router_decision" in latency
        assert "scheduler_queue" in latency
        assert "worker_queue" in latency
        assert "total_queue" in latency
        assert "kv_cache_lookup" in latency

    def test_long_tail_analysis(self, advanced_dynamo):
        """Test long-tail request analysis."""
        # Generate requests with varying latencies
        for i in range(20):
            request_id = f"req-longtail-{i}"

            request, reason = advanced_dynamo.start_request(
                request_id=request_id,
                model="openai/gpt-oss-120b",
                endpoint="/v1/chat/completions",
                input_tokens=100 + i * 50,  # Varying sizes
            )

            advanced_dynamo.record_scheduler_queue_exit(request_id)
            advanced_dynamo.record_worker_queue_exit(request_id)
            advanced_dynamo.record_first_token(request_id)

            # Simulate varying processing times
            time.sleep(0.001 * i)

            advanced_dynamo.complete_request(
                request_id=request_id,
                output_tokens=50 + i * 10,
                success=True,
            )

        stats = advanced_dynamo.get_stats_dict(60)
        long_tail = stats["long_tail"]

        # Should have long-tail analysis
        assert "long_tail_requests" in long_tail
        assert "p99_threshold_ms" in long_tail

        if long_tail["long_tail_requests"] > 0:
            assert "analysis" in long_tail
            analysis = long_tail["analysis"]
            assert "avg_input_tokens" in analysis
            assert "avg_output_tokens" in analysis
            assert "avg_queue_time_ms" in analysis


# ==============================================================================
# Integration Test: Complete Dynamo Flow
# ==============================================================================


@pytest.mark.integration
@pytest.mark.dynamo
class TestCompleteDynamoFlow:
    """Test complete end-to-end Dynamo metrics flow."""

    def test_complete_request_lifecycle_with_all_metrics(self, advanced_dynamo):
        """Test complete request with all metric collection points."""
        request_id = "req-complete-flow"

        # 1. Start request with priority
        request, reason = advanced_dynamo.start_request(
            request_id=request_id,
            model="openai/gpt-oss-120b",
            endpoint="/v1/chat/completions",
            input_tokens=100,
            priority=RequestPriority.HIGH,
        )

        assert request is not None
        assert reason == "success"

        # 2. Record router decision
        router_start = time.time()
        time.sleep(0.001)
        router_end = time.time()
        advanced_dynamo.record_router_decision(request_id, router_start, router_end)

        # 3. Exit scheduler queue
        advanced_dynamo.record_scheduler_queue_exit(request_id)

        # 4. Exit worker queue
        time.sleep(0.01)
        advanced_dynamo.record_worker_queue_exit(request_id)

        # 5. KV cache lookup
        kv_start = time.time()
        time.sleep(0.002)
        kv_end = time.time()
        advanced_dynamo.record_kv_cache_lookup(request_id, kv_start, kv_end)

        # 6. Prefill phase
        prefill_start = time.time()
        time.sleep(0.02)
        prefill_end = time.time()
        advanced_dynamo.record_prefill_phase(request_id, prefill_start, prefill_end)

        # 7. First token
        advanced_dynamo.record_first_token(request_id)

        # 8. Decode phase
        decode_start = time.time()
        time.sleep(0.03)
        decode_end = time.time()
        advanced_dynamo.record_decode_phase(request_id, decode_start, decode_end)

        # 9. Complete request
        advanced_dynamo.complete_request(
            request_id=request_id,
            output_tokens=50,
            cached_tokens=20,
            kv_cache_hit=True,
            worker_id="worker-1",
            success=True,
            batch_id="batch-1",
            batch_size=16,
        )

        # Verify all metrics collected
        recent = advanced_dynamo.get_recent_requests(60)
        assert len(recent) == 1

        completed_request = recent[0]

        # Verify timing metrics
        assert completed_request.router_decision_time_us > 0
        assert completed_request.total_queue_time_ms > 0
        assert completed_request.kv_cache_lookup_time_us > 0
        assert completed_request.prefill_time_ms > 0
        assert completed_request.decode_time_ms > 0
        assert completed_request.ttft_ms > 0
        assert completed_request.tpot_ms > 0

        # Verify metadata
        assert completed_request.kv_cache_hit is True
        assert completed_request.cached_tokens == 20
        assert completed_request.worker_id == "worker-1"
        assert completed_request.batch_size == 16

        # Get complete stats
        stats = advanced_dynamo.get_stats_dict(60)

        assert stats["summary"]["total_requests"] == 1
        assert stats["summary"]["successful_requests"] == 1

        # All latency components should be present
        latency = stats["latency"]
        assert latency["router_decision"]["avg"] > 0
        assert latency["total_queue"]["avg"] > 0
        assert latency["kv_cache_lookup"]["avg"] > 0
        assert latency["prefill"]["avg"] > 0
        assert latency["decode"]["avg"] > 0
