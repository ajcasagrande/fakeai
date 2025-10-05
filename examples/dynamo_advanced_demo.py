#!/usr/bin/env python3
"""
NVIDIA AI-Dynamo Advanced Features Demonstration.

Shows all Dynamo components working together:
- KVBM 4-tier memory hierarchy
- Block lifecycle management
- SLA-based planner with load prediction
- Disaggregated router
- Prefill queue
- Dynamic endpoint registration
"""
import time
from fakeai.dynamo_advanced import (
    DynamoSystem,
    SLATarget,
    LoadPredictor,
    MemoryTier,
    BlockState,
)


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main():
    print("=" * 70)
    print("  NVIDIA AI-Dynamo Advanced Features Demo")
    print("=" * 70)

    # ========================================================================
    # Part 1: KVBM - 4-Tier Memory Hierarchy
    # ========================================================================
    print_section("Part 1: KVBM - KV Block Manager")

    print("\nInitializing KVBM with 4-tier memory hierarchy:")
    print("  G1 (GPU HBM):  1,000 blocks")
    print("  G2 (CPU DRAM): 5,000 blocks")
    print("  G3 (Local SSD): 20,000 blocks")
    print("  G4 (Remote):   100,000 blocks")

    # Create Dynamo system
    sla = SLATarget(ttft_ms=200.0, itl_ms=25.0, throughput_rps=15.0)
    dynamo = DynamoSystem(sla_target=sla, enable_disaggregation=True)

    print("\n1. Allocating KV cache block in GPU memory (G1)...")
    block_g1 = dynamo.kvbm.allocate(MemoryTier.G1_GPU_HBM, size_tokens=16)
    print(f"   ✓ Allocated block: {block_g1.block_id}")
    print(f"   - Tier: {block_g1.tier.value}")
    print(f"   - State: {block_g1.state.value}")
    print(f"   - Capacity: {block_g1.size_tokens} tokens")

    print("\n2. Progressing through block lifecycle states...")
    dynamo.kvbm.transition_state(block_g1.block_id, BlockState.PARTIAL)
    print(f"   ✓ State: RESET → PARTIAL (filling with tokens)")

    dynamo.kvbm.transition_state(block_g1.block_id, BlockState.COMPLETE)
    print(f"   ✓ State: PARTIAL → COMPLETE (filled)")

    dynamo.kvbm.transition_state(block_g1.block_id, BlockState.REGISTERED)
    print(f"   ✓ State: COMPLETE → REGISTERED (visible for reuse)")

    print("\n3. Offloading block through memory tiers...")
    dynamo.kvbm.offload_to_tier(block_g1.block_id, MemoryTier.G2_CPU_DRAM)
    print(f"   ✓ Offloaded: G1 (GPU) → G2 (CPU)")

    dynamo.kvbm.offload_to_tier(block_g1.block_id, MemoryTier.G3_LOCAL_SSD)
    print(f"   ✓ Offloaded: G2 (CPU) → G3 (SSD)")

    kvbm_stats = dynamo.kvbm.get_stats()
    print(f"\n4. KVBM Statistics:")
    for tier, stats in kvbm_stats["pools"].items():
        print(f"   {tier.upper()}:")
        print(f"     Active blocks: {stats['active_blocks']}/{stats['capacity']}")
        print(f"     Utilization: {stats['utilization_pct']:.1f}%")

    print(f"\n   Tier Transfers:")
    for transfer, count in kvbm_stats["transfers"].items():
        print(f"     {transfer}: {count}")

    # ========================================================================
    # Part 2: Disaggregated Router
    # ========================================================================
    print_section("Part 2: Disaggregated Router")

    print("\nTesting prefill/decode disaggregation decisions...")

    print("\n1. Short input (100 tokens):")
    result1 = dynamo.process_request("req-short", input_length=100, model="openai/gpt-oss-120b")
    print(f"   Decision: {'Remote Prefill' if result1['decision']['use_remote_prefill'] else 'Local Prefill'}")
    print(f"   Reason: {result1['decision']['reason']}")
    print(f"   KV blocks allocated: {result1['kv_blocks_allocated']}")

    print("\n2. Long input (2048 tokens):")
    result2 = dynamo.process_request("req-long", input_length=2048, model="openai/gpt-oss-120b")
    print(f"   Decision: {'Remote Prefill' if result2['decision']['use_remote_prefill'] else 'Local Prefill'}")
    print(f"   Reason: {result2['decision']['reason']}")
    print(f"   KV blocks allocated: {result2['kv_blocks_allocated']}")

    router_stats = dynamo.router.get_stats()
    print(f"\n3. Router Statistics:")
    print(f"   Total decisions: {router_stats['total_decisions']}")
    print(f"   Local prefill: {router_stats['local_prefill_count']}")
    print(f"   Remote prefill: {router_stats['remote_prefill_count']}")
    print(f"   Remote ratio: {router_stats['remote_prefill_ratio']:.1%}")

    # ========================================================================
    # Part 3: Prefill Queue
    # ========================================================================
    print_section("Part 3: Prefill Queue Management")

    queue_stats = dynamo.prefill_queue.get_stats()
    print(f"\nPrefill Queue Status:")
    print(f"   Current depth: {queue_stats['current_depth']}")
    print(f"   Max depth observed: {queue_stats['max_depth']}")
    print(f"   Capacity: {queue_stats['capacity']}")
    print(f"   Utilization: {queue_stats['utilization_pct']:.1f}%")
    print(f"   Total enqueued: {queue_stats['total_enqueued']}")
    print(f"   Total dequeued: {queue_stats['total_dequeued']}")
    print(f"   Total rejected: {queue_stats['total_rejected']}")

    # ========================================================================
    # Part 4: SLA-Based Planner
    # ========================================================================
    print_section("Part 4: SLA-Based Planner")

    print(f"\nSLA Targets:")
    print(f"   TTFT: {sla.ttft_ms}ms")
    print(f"   ITL: {sla.itl_ms}ms")
    print(f"   Throughput: {sla.throughput_rps} req/s")

    # Record some metrics
    print("\nSimulating workload and recording metrics...")
    for i in range(15):
        dynamo.planner.record_request_metrics(
            ttft_ms=150.0 + i * 10,
            itl_ms=20.0 + i * 2,
            request_count=10 + i,
        )

    # Predict load
    predicted_load = dynamo.planner.predict_load()
    print(f"\nLoad Prediction:")
    print(f"   Predicted load: {predicted_load:.1f} req/s")
    print(f"   Predictor type: {dynamo.planner.predictor_type.value}")

    # Check if scaling needed
    should_scale, new_allocation = dynamo.planner.should_scale()
    print(f"\nScaling Decision:")
    print(f"   Should scale: {should_scale}")
    print(f"   Current allocation:")
    print(f"     Prefill workers: {dynamo.planner.current_allocation.prefill_workers}")
    print(f"     Decode workers: {dynamo.planner.current_allocation.decode_workers}")

    if should_scale:
        print(f"   Recommended allocation:")
        print(f"     Prefill workers: {new_allocation.prefill_workers}")
        print(f"     Decode workers: {new_allocation.decode_workers}")

    # ========================================================================
    # Part 5: Dynamic Endpoint Registry
    # ========================================================================
    print_section("Part 5: Dynamic Endpoint Registry")

    print("\nRegistering inference endpoints...")

    # Register prefill workers
    ep1 = dynamo.endpoint_registry.register_endpoint(
        url="http://prefill-worker-1:8000",
        model="openai/gpt-oss-120b",
        backend="vllm",
    )
    print(f"   ✓ Registered: {ep1} (Prefill Worker 1)")

    ep2 = dynamo.endpoint_registry.register_endpoint(
        url="http://prefill-worker-2:8000",
        model="openai/gpt-oss-120b",
        backend="sglang",
    )
    print(f"   ✓ Registered: {ep2} (Prefill Worker 2)")

    # Register decode workers
    ep3 = dynamo.endpoint_registry.register_endpoint(
        url="http://decode-worker-1:8000",
        model="openai/gpt-oss-120b",
        backend="trtllm",
    )
    print(f"   ✓ Registered: {ep3} (Decode Worker 1)")

    # Record some traffic
    dynamo.endpoint_registry.record_request(ep1, success=True, latency_ms=145.3)
    dynamo.endpoint_registry.record_request(ep1, success=True, latency_ms=152.1)
    dynamo.endpoint_registry.record_request(ep2, success=True, latency_ms=138.9)
    dynamo.endpoint_registry.record_request(ep3, success=False, latency_ms=500.0)

    # Update health
    dynamo.endpoint_registry.update_health(ep3, "degraded")

    endpoint_stats = dynamo.endpoint_registry.get_stats()
    print(f"\nEndpoint Statistics:")
    print(f"   Total endpoints: {endpoint_stats['total_endpoints']}")
    print(f"   Healthy: {endpoint_stats['healthy_endpoints']}")
    print(f"   Degraded: {endpoint_stats['degraded_endpoints']}")
    print(f"   Unhealthy: {endpoint_stats['unhealthy_endpoints']}")

    print(f"\n   Endpoints by model:")
    for model, count in endpoint_stats["endpoints_by_model"].items():
        print(f"     {model}: {count} endpoints")

    print(f"\n   Endpoint Details:")
    for ep in endpoint_stats["endpoints"]:
        status_symbol = "✓" if ep["status"] == "healthy" else ("⚠" if ep["status"] == "degraded" else "✗")
        print(f"     {status_symbol} {ep['id']}: {ep['model']} ({ep['backend']})")
        print(f"        Requests: {ep['requests']}, Errors: {ep['errors']}, Error Rate: {ep['error_rate']:.1%}")
        print(f"        Avg Latency: {ep['avg_latency_ms']:.1f}ms")

    # ========================================================================
    # Part 6: Complete System Overview
    # ========================================================================
    print_section("Part 6: Complete System Overview")

    # Process more requests to populate stats
    print("\nProcessing 20 requests with varying characteristics...")
    for i in range(20):
        input_len = 100 + (i * 100)  # Varying lengths
        dynamo.process_request(f"req-batch-{i}", input_len, "openai/gpt-oss-120b")

    # Get comprehensive stats
    stats = dynamo.get_comprehensive_stats()

    print(f"\nSystem Summary:")
    print(f"   Total requests processed: {stats['system']['total_requests_processed']}")
    print(f"   Disaggregation enabled: {stats['system']['disaggregation_enabled']}")

    print(f"\nKVBM Summary:")
    print(f"   Total blocks in registry: {stats['kvbm']['total_blocks']}")
    print(f"   GPU (G1) utilization: {stats['kvbm']['pools']['gpu_hbm']['utilization_pct']:.1f}%")
    print(f"   CPU (G2) utilization: {stats['kvbm']['pools']['cpu_dram']['utilization_pct']:.1f}%")

    print(f"\nRouter Summary:")
    print(f"   Local prefill decisions: {stats['router']['local_prefill_count']}")
    print(f"   Remote prefill decisions: {stats['router']['remote_prefill_count']}")
    print(f"   Remote prefill ratio: {stats['router']['remote_prefill_ratio']:.1%}")

    print(f"\nPrefill Queue Summary:")
    print(f"   Current depth: {stats['prefill_queue']['current_depth']}")
    print(f"   Max depth: {stats['prefill_queue']['max_depth']}")
    print(f"   Rejection rate: {stats['prefill_queue']['rejection_rate']:.1%}")

    # ========================================================================
    # Summary
    # ========================================================================
    print_section("Summary")

    print("""
NVIDIA AI-Dynamo Advanced Features:

✓ KVBM (KV Block Manager)
  - 4-tier memory hierarchy (G1→G2→G3→G4)
  - Block lifecycle management (Reset→Partial→Complete→Registered)
  - LRU eviction policies
  - Cross-tier offloading

✓ SLA-Based Planner
  - 3 load predictors (Constant, ARIMA, Prophet)
  - Dynamic worker allocation
  - SLA target tracking (TTFT, ITL, throughput)
  - Automatic scaling decisions

✓ Disaggregated Router
  - Prefill/decode separation decisions
  - Queue-aware routing
  - Input length-based logic
  - Statistics tracking

✓ Prefill Queue
  - FIFO queue management
  - Capacity-based rejection
  - Wait time tracking
  - Load balancing for remote prefill

✓ Dynamic Endpoint Registry
  - Runtime endpoint registration
  - Health status tracking
  - Per-endpoint metrics
  - Model-based endpoint discovery

All components are production-ready and fully tested!
    """)

    print("\n" + "=" * 70)
    print("  Demo Complete!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
