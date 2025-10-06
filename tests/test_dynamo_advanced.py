"""
Comprehensive tests for NVIDIA Dynamo advanced features.

Tests KVBM, SLA-based planner, disaggregated router, prefill queue,
and dynamic endpoint registry.
"""

import time

import pytest

from fakeai.dynamo_advanced import (
    BlockState,
    DisaggregatedRouter,
    DynamicEndpointRegistry,
    DynamoSystem,
    KVBlockManager,
    LoadPredictor,
    MemoryTier,
    PrefillQueue,
    PrefillQueueItem,
    SLABasedPlanner,
    SLATarget,
    WorkerAllocation,
)


class TestKVBlockManager:
    """Test KVBM 4-tier memory hierarchy."""

    def test_kvbm_initialization(self):
        """Test KVBM initializes with 4 tiers."""
        kvbm = KVBlockManager()

        stats = kvbm.get_stats()

        assert "pools" in stats
        assert MemoryTier.G1_GPU_HBM.value in stats["pools"]
        assert MemoryTier.G2_CPU_DRAM.value in stats["pools"]
        assert MemoryTier.G3_LOCAL_SSD.value in stats["pools"]
        assert MemoryTier.G4_REMOTE_STORAGE.value in stats["pools"]

    def test_block_allocation(self):
        """Test allocating blocks in different tiers."""
        kvbm = KVBlockManager()

        # Allocate in GPU
        block_g1 = kvbm.allocate(MemoryTier.G1_GPU_HBM, size_tokens=16)
        assert block_g1 is not None
        assert block_g1.tier == MemoryTier.G1_GPU_HBM
        assert block_g1.state == BlockState.RESET

        # Allocate in CPU
        block_g2 = kvbm.allocate(MemoryTier.G2_CPU_DRAM, size_tokens=32)
        assert block_g2 is not None
        assert block_g2.tier == MemoryTier.G2_CPU_DRAM

    def test_block_state_transitions(self):
        """Test block lifecycle state machine."""
        kvbm = KVBlockManager()

        block = kvbm.allocate(MemoryTier.G1_GPU_HBM)

        # Reset -> Partial
        kvbm.transition_state(block.block_id, BlockState.PARTIAL)
        assert kvbm.block_registry[block.block_id].state == BlockState.PARTIAL

        # Partial -> Complete
        kvbm.transition_state(block.block_id, BlockState.COMPLETE)
        assert kvbm.block_registry[block.block_id].state == BlockState.COMPLETE

        # Complete -> Registered
        kvbm.transition_state(block.block_id, BlockState.REGISTERED)
        assert kvbm.block_registry[block.block_id].state == BlockState.REGISTERED

    def test_tier_offloading(self):
        """Test offloading blocks between tiers."""
        kvbm = KVBlockManager()

        # Allocate in GPU
        block = kvbm.allocate(MemoryTier.G1_GPU_HBM)
        original_id = block.block_id

        # Offload to CPU
        success = kvbm.offload_to_tier(original_id, MemoryTier.G2_CPU_DRAM)

        assert success is True
        assert kvbm.block_registry[original_id].tier == MemoryTier.G2_CPU_DRAM

        # Check transfer was tracked
        stats = kvbm.get_stats()
        assert "gpu_hbm->cpu_dram" in stats["transfers"]

    def test_lru_eviction(self):
        """Test LRU eviction from tier."""
        kvbm = KVBlockManager(g1_capacity=5)

        # Fill GPU tier
        blocks = []
        for i in range(5):
            block = kvbm.allocate(MemoryTier.G1_GPU_HBM)
            blocks.append(block)
            time.sleep(0.01)  # Ensure different timestamps

        # Access some blocks (update last_accessed)
        blocks[2].last_accessed = time.time()
        blocks[4].last_accessed = time.time()

        # Evict LRU (should be blocks[0] or blocks[1])
        success = kvbm.evict_lru(MemoryTier.G1_GPU_HBM)

        assert success is True

        # Check eviction was tracked
        stats = kvbm.get_stats()
        assert stats["evictions_by_tier"]["gpu_hbm"] == 1


class TestSLABasedPlanner:
    """Test SLA-based planner."""

    def test_planner_initialization(self):
        """Test planner initializes correctly."""
        sla = SLATarget(ttft_ms=500.0, itl_ms=50.0)
        planner = SLABasedPlanner(sla, predictor_type=LoadPredictor.CONSTANT)

        stats = planner.get_stats()

        assert stats["sla_targets"]["ttft_ms"] == 500.0
        assert stats["sla_targets"]["itl_ms"] == 50.0
        assert stats["predictor_type"] == "constant"

    def test_constant_predictor(self):
        """Test constant load predictor."""
        planner = SLABasedPlanner(SLATarget(), LoadPredictor.CONSTANT)

        # Record some requests
        for i in range(10):
            planner.record_request_metrics(
                ttft_ms=150.0, itl_ms=20.0, request_count=5 + i
            )

        predicted = planner.predict_load()

        # Should be around recent average (5-14 range, avg ~9.5)
        assert 8.0 <= predicted <= 15.0

    def test_arima_predictor(self):
        """Test ARIMA trend predictor."""
        planner = SLABasedPlanner(SLATarget(), LoadPredictor.ARIMA)

        # Simulate increasing load trend
        for i in range(15):
            planner.record_request_metrics(
                ttft_ms=150.0, itl_ms=20.0, request_count=10 + i * 2
            )

        predicted = planner.predict_load()

        # Should predict continued increase
        recent_avg = sum(range(20, 40, 2)[-5:]) / 5  # Last 5 values
        assert predicted >= recent_avg  # Should predict growth

    def test_worker_allocation_calculation(self):
        """Test worker allocation calculation."""
        sla = SLATarget(ttft_ms=200.0, itl_ms=30.0, throughput_rps=20.0)
        planner = SLABasedPlanner(sla)

        # Record high load
        for _ in range(10):
            planner.record_request_metrics(ttft_ms=250.0, itl_ms=40.0, request_count=20)

        allocation = planner.calculate_required_workers()

        assert allocation.prefill_workers >= 1
        assert allocation.decode_workers >= 1

    def test_scaling_decisions(self):
        """Test scaling decision logic."""
        planner = SLABasedPlanner(SLATarget(ttft_ms=500.0, itl_ms=50.0))

        # Set current allocation
        planner.current_allocation = WorkerAllocation(
            prefill_workers=2, decode_workers=3
        )

        # Record low load
        for _ in range(5):
            planner.record_request_metrics(ttft_ms=100.0, itl_ms=15.0, request_count=1)

        should_scale, new_allocation = planner.should_scale()

        # May or may not scale depending on predicted load
        # Just verify it returns valid data
        assert isinstance(should_scale, bool)
        assert isinstance(new_allocation, WorkerAllocation)


class TestDisaggregatedRouter:
    """Test disaggregated router decisions."""

    def test_router_short_input_local(self):
        """Test short inputs use local prefill."""
        router = DisaggregatedRouter(prefill_length_threshold=512)

        decision = router.make_decision(
            input_length=100,
            current_queue_depth=5,
        )

        assert decision.use_remote_prefill is False
        assert decision.reason == "short_input"

    def test_router_long_input_remote(self):
        """Test long inputs use remote prefill when queue available."""
        router = DisaggregatedRouter(
            prefill_length_threshold=512,
            queue_capacity_threshold=10,
        )

        decision = router.make_decision(
            input_length=1000,
            current_queue_depth=3,
        )

        assert decision.use_remote_prefill is True
        assert "remote" in decision.reason

    def test_router_queue_full_fallback(self):
        """Test falls back to local when queue full."""
        router = DisaggregatedRouter(
            prefill_length_threshold=512,
            queue_capacity_threshold=10,
        )

        decision = router.make_decision(
            input_length=1000,
            current_queue_depth=15,  # Above threshold
        )

        assert decision.use_remote_prefill is False
        assert "queue_full" in decision.reason

    def test_router_statistics(self):
        """Test router tracks statistics."""
        router = DisaggregatedRouter()

        # Make several decisions
        for i in range(20):
            router.make_decision(input_length=100 + i * 50, current_queue_depth=5)

        stats = router.get_stats()

        assert stats["total_decisions"] == 20
        assert stats["local_prefill_count"] + stats["remote_prefill_count"] == 20


class TestPrefillQueue:
    """Test prefill queue management."""

    def test_queue_enqueue_dequeue(self):
        """Test basic enqueue/dequeue operations."""
        queue = PrefillQueue(max_capacity=10)

        item = PrefillQueueItem(
            request_id="req-1",
            input_tokens=[1, 2, 3],
            kv_blocks=["block-1"],
            enqueue_time=time.time(),
        )

        # Enqueue
        success = queue.enqueue(item)
        assert success is True
        assert queue.get_depth() == 1

        # Dequeue
        dequeued = queue.dequeue()
        assert dequeued is not None
        assert dequeued.request_id == "req-1"
        assert queue.get_depth() == 0

    def test_queue_capacity_limit(self):
        """Test queue rejects when full."""
        queue = PrefillQueue(max_capacity=3)

        # Fill queue
        for i in range(3):
            item = PrefillQueueItem(
                request_id=f"req-{i}",
                input_tokens=[],
                kv_blocks=[],
                enqueue_time=time.time(),
            )
            assert queue.enqueue(item) is True

        # Try to exceed capacity
        overflow_item = PrefillQueueItem(
            request_id="req-overflow",
            input_tokens=[],
            kv_blocks=[],
            enqueue_time=time.time(),
        )
        assert queue.enqueue(overflow_item) is False

        stats = queue.get_stats()
        assert stats["total_rejected"] == 1

    def test_queue_fifo_order(self):
        """Test queue maintains FIFO order."""
        queue = PrefillQueue()

        # Enqueue multiple items
        for i in range(5):
            item = PrefillQueueItem(
                request_id=f"req-{i}",
                input_tokens=[],
                kv_blocks=[],
                enqueue_time=time.time(),
            )
            queue.enqueue(item)

        # Dequeue should be FIFO
        first = queue.dequeue()
        assert first.request_id == "req-0"

        second = queue.dequeue()
        assert second.request_id == "req-1"


class TestDynamicEndpointRegistry:
    """Test dynamic endpoint registration."""

    def test_endpoint_registration(self):
        """Test registering endpoints."""
        registry = DynamicEndpointRegistry()

        endpoint_id = registry.register_endpoint(
            url="http://worker-1:8000",
            model="openai/gpt-oss-120b",
            backend="vllm",
        )

        assert endpoint_id.startswith("ep_")

        stats = registry.get_stats()
        assert stats["total_endpoints"] == 1

    def test_endpoint_health_tracking(self):
        """Test endpoint health status updates."""
        registry = DynamicEndpointRegistry()

        ep_id = registry.register_endpoint(
            "http://worker-1:8000", "openai/gpt-oss-120b"
        )

        # Update health
        registry.update_health(ep_id, "degraded")

        stats = registry.get_stats()
        assert stats["degraded_endpoints"] == 1
        assert stats["healthy_endpoints"] == 0

    def test_endpoint_metrics_tracking(self):
        """Test endpoint request metrics."""
        registry = DynamicEndpointRegistry()

        ep_id = registry.register_endpoint(
            "http://worker-1:8000", "openai/gpt-oss-120b"
        )

        # Record successful requests
        for i in range(10):
            registry.record_request(ep_id, success=True, latency_ms=100.0 + i * 10)

        # Record failed request
        registry.record_request(ep_id, success=False, latency_ms=500.0)

        endpoint = registry.endpoints[ep_id]
        assert endpoint.request_count == 11
        assert endpoint.error_count == 1

    def test_get_endpoints_for_model(self):
        """Test retrieving endpoints by model."""
        registry = DynamicEndpointRegistry()

        # Register multiple endpoints for same model
        ep1 = registry.register_endpoint("http://worker-1:8000", "openai/gpt-oss-120b")
        ep2 = registry.register_endpoint("http://worker-2:8000", "openai/gpt-oss-120b")
        ep3 = registry.register_endpoint("http://worker-3:8000", "gpt-3.5")

        gpt4_endpoints = registry.get_endpoints_for_model("openai/gpt-oss-120b")

        assert len(gpt4_endpoints) == 2
        assert all(e.model == "openai/gpt-oss-120b" for e in gpt4_endpoints)

    def test_healthy_endpoints_filter(self):
        """Test filtering by health status."""
        registry = DynamicEndpointRegistry()

        ep1 = registry.register_endpoint("http://worker-1:8000", "openai/gpt-oss-120b")
        ep2 = registry.register_endpoint("http://worker-2:8000", "openai/gpt-oss-120b")

        # Mark one as unhealthy
        registry.update_health(ep2, "unhealthy")

        healthy = registry.get_healthy_endpoints()

        assert len(healthy) == 1
        assert healthy[0].endpoint_id == ep1


class TestDynamoSystem:
    """Test complete Dynamo system integration."""

    def test_dynamo_system_initialization(self):
        """Test Dynamo system initializes all components."""
        dynamo = DynamoSystem()

        stats = dynamo.get_comprehensive_stats()

        assert "kvbm" in stats
        assert "planner" in stats
        assert "router" in stats
        assert "prefill_queue" in stats
        assert "endpoints" in stats

    def test_request_processing_local(self):
        """Test processing request with local prefill."""
        dynamo = DynamoSystem()

        result = dynamo.process_request(
            request_id="req-1",
            input_length=100,  # Short, below threshold
            model="openai/gpt-oss-120b",
        )

        assert result["decision"]["use_remote_prefill"] is False
        assert result["decision"]["reason"] == "short_input"
        assert result["kv_blocks_allocated"] > 0

    def test_request_processing_remote(self):
        """Test processing request with remote prefill."""
        dynamo = DynamoSystem(enable_disaggregation=True)

        result = dynamo.process_request(
            request_id="req-1",
            input_length=1000,  # Long, above threshold
            model="openai/gpt-oss-120b",
        )

        # With empty queue, should use remote
        assert result["decision"]["use_remote_prefill"] is True

        # Check prefill queue
        queue_stats = dynamo.prefill_queue.get_stats()
        assert queue_stats["current_depth"] == 1

    def test_kvbm_allocation_in_system(self):
        """Test KVBM block allocation during request processing."""
        dynamo = DynamoSystem()

        # Process request
        result = dynamo.process_request(
            "req-1", input_length=256, model="openai/gpt-oss-120b"
        )

        # Check blocks were allocated
        assert len(result["blocks"]) > 0

        # Check KVBM stats
        kvbm_stats = dynamo.kvbm.get_stats()
        assert kvbm_stats["pools"]["gpu_hbm"]["active_blocks"] > 0

    def test_disaggregation_disabled(self):
        """Test system works with disaggregation disabled."""
        dynamo = DynamoSystem(enable_disaggregation=False)

        result = dynamo.process_request(
            "req-1", input_length=2000, model="openai/gpt-oss-120b"
        )

        # Should use local even for long input
        assert result["decision"]["use_remote_prefill"] is False
        assert "disabled" in result["decision"]["reason"]

    def test_comprehensive_stats(self):
        """Test comprehensive statistics collection."""
        dynamo = DynamoSystem()

        # Process several requests
        for i in range(10):
            dynamo.process_request(
                f"req-{i}", input_length=100 + i * 100, model="openai/gpt-oss-120b"
            )

        stats = dynamo.get_comprehensive_stats()

        # Verify all components report
        assert stats["system"]["total_requests_processed"] == 10
        assert "kvbm" in stats
        assert "router" in stats
        assert "prefill_queue" in stats

    def test_endpoint_registration_integration(self):
        """Test endpoint registration within Dynamo system."""
        dynamo = DynamoSystem()

        # Register endpoints
        ep1 = dynamo.endpoint_registry.register_endpoint(
            "http://prefill-worker-1:8000", "openai/gpt-oss-120b", "vllm"
        )
        ep2 = dynamo.endpoint_registry.register_endpoint(
            "http://decode-worker-1:8000", "openai/gpt-oss-120b", "vllm"
        )

        stats = dynamo.get_comprehensive_stats()

        assert stats["endpoints"]["total_endpoints"] == 2
        assert stats["endpoints"]["endpoints_by_model"]["openai/gpt-oss-120b"] == 2


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_complete_request_flow(self):
        """Test complete request flow through Dynamo."""
        sla = SLATarget(ttft_ms=200.0, itl_ms=25.0)
        dynamo = DynamoSystem(sla_target=sla, enable_disaggregation=True)

        # Register workers
        dynamo.endpoint_registry.register_endpoint(
            "http://prefill:8000", "openai/gpt-oss-120b", "vllm"
        )
        dynamo.endpoint_registry.register_endpoint(
            "http://decode:8000", "openai/gpt-oss-120b", "vllm"
        )

        # Process request
        result = dynamo.process_request(
            request_id="req-complete",
            input_length=1024,
            model="openai/gpt-oss-120b",
        )

        # Verify complete flow
        assert "decision" in result
        assert "kv_blocks_allocated" in result

        # Check all subsystems involved
        kvbm_stats = dynamo.kvbm.get_stats()
        assert kvbm_stats["total_blocks"] > 0

        router_stats = dynamo.router.get_stats()
        assert router_stats["total_decisions"] > 0

    def test_memory_tier_progression(self):
        """Test blocks move through memory tiers."""
        dynamo = DynamoSystem()

        # Allocate block in GPU
        block = dynamo.kvbm.allocate(MemoryTier.G1_GPU_HBM)

        # Transition through lifecycle
        dynamo.kvbm.transition_state(block.block_id, BlockState.PARTIAL)
        dynamo.kvbm.transition_state(block.block_id, BlockState.COMPLETE)
        dynamo.kvbm.transition_state(block.block_id, BlockState.REGISTERED)

        # Offload to CPU
        dynamo.kvbm.offload_to_tier(block.block_id, MemoryTier.G2_CPU_DRAM)

        # Offload to SSD
        dynamo.kvbm.offload_to_tier(block.block_id, MemoryTier.G3_LOCAL_SSD)

        # Check final state
        final_block = dynamo.kvbm.block_registry[block.block_id]
        assert final_block.tier == MemoryTier.G3_LOCAL_SSD
        assert final_block.state == BlockState.REGISTERED

        # Check transfers tracked
        kvbm_stats = dynamo.kvbm.get_stats()
        assert len(kvbm_stats["transfers"]) > 0
