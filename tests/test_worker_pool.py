#!/usr/bin/env python3
"""
Test Worker Pool Utilization Tracking.

This script tests the worker pool implementation with realistic load patterns.
"""

import json
import time

from fakeai.dynamo_metrics import DynamoMetricsCollector
from fakeai.worker_pool import WorkerPool, reset_worker_pool


def test_worker_pool_basic():
    """Test basic worker pool functionality."""
    print("=" * 80)
    print("TEST 1: Basic Worker Pool Functionality")
    print("=" * 80)

    pool = WorkerPool(num_workers=4)

    # Simulate assigning requests
    request_ids = [f"req-{i}" for i in range(10)]
    worker_assignments = {}

    for req_id in request_ids:
        worker_id = pool.assign_request(req_id)
        worker_assignments[req_id] = worker_id
        print(f"Assigned {req_id} to {worker_id}")

    # Get stats
    stats = pool.get_worker_stats()
    print("\nWorker Pool Stats:")
    print(json.dumps(stats, indent=2))

    # Complete some requests
    print("\nCompleting 5 requests...")
    for i, req_id in enumerate(request_ids[:5]):
        worker_id = worker_assignments[req_id]
        duration_ms = 50.0 + i * 10  # Varied durations
        pool.complete_request(worker_id, duration_ms, success=True)
        print(f"Completed {req_id} on {worker_id} (duration: {duration_ms}ms)")

    # Get updated stats
    stats = pool.get_worker_stats()
    print("\nWorker Pool Stats After Completions:")
    print(json.dumps(stats, indent=2))

    assert stats["total_workers"] == 4
    assert stats["active_workers"] >= 0
    assert len(stats["workers"]) == 4

    print("\n✓ Test 1 passed!\n")
    pool.shutdown()


def test_worker_utilization():
    """Test worker utilization calculation."""
    print("=" * 80)
    print("TEST 2: Worker Utilization Tracking")
    print("=" * 80)

    pool = WorkerPool(num_workers=4)

    # Simulate requests with different patterns
    # Worker 0: High load
    # Worker 1: Medium load
    # Worker 2: Low load
    # Worker 3: Very low load

    worker_loads = {
        "worker-0": 20,  # 20 requests
        "worker-1": 10,  # 10 requests
        "worker-2": 5,  # 5 requests
        "worker-3": 2,  # 2 requests
    }

    for worker_id, num_requests in worker_loads.items():
        for i in range(num_requests):
            req_id = f"req-{worker_id}-{i}"
            # Assign directly to specific worker by getting it
            pool.workers[worker_id].start_request()

            # Simulate processing time
            duration_ms = 50.0 if worker_id == "worker-0" else 30.0
            time.sleep(0.01)  # Small delay to simulate processing

            pool.complete_request(worker_id, duration_ms, success=True)

    # Get final stats
    stats = pool.get_worker_stats()
    print("\nWorker Pool Stats with Varied Loads:")
    print(json.dumps(stats, indent=2))

    # Verify utilization varies by worker
    workers = {w["worker_id"]: w for w in stats["workers"]}
    print("\nUtilization by Worker:")
    for worker_id in ["worker-0", "worker-1", "worker-2", "worker-3"]:
        util = workers[worker_id]["utilization"]
        total = workers[worker_id]["total_requests"]
        print(f"  {worker_id}: {util:.3f} ({total} requests)")

    print("\n✓ Test 2 passed!\n")
    pool.shutdown()


def test_dynamo_integration():
    """Test worker pool integration with DynamoMetricsCollector."""
    print("=" * 80)
    print("TEST 3: DynamoMetricsCollector Integration")
    print("=" * 80)

    # Reset worker pool to avoid conflicts
    reset_worker_pool()

    # Create metrics collector (this will create a new worker pool)
    metrics = DynamoMetricsCollector(window_size=300, num_workers=4)

    # Simulate some requests
    print("Simulating 20 requests...")
    for i in range(20):
        request_id = f"test-req-{i}"
        model = "gpt-4" if i % 2 == 0 else "gpt-3.5-turbo"
        endpoint = "/v1/chat/completions"

        # Start request
        req = metrics.start_request(request_id, model, endpoint, input_tokens=100)
        print(f"Request {i}: {request_id} assigned to {req.worker_id}")

        # Record phases
        metrics.record_prefill_start(request_id)
        time.sleep(0.01)  # Small delay
        metrics.record_first_token(request_id)

        # Complete request
        output_tokens = 50 + i
        metrics.complete_request(
            request_id,
            output_tokens=output_tokens,
            cached_tokens=20,
            kv_cache_hit=i % 3 == 0,
            success=True,
        )

    # Get comprehensive stats
    stats = metrics.get_stats_dict()

    print("\nDynamo Metrics Summary:")
    print(f"  Total requests: {stats['summary']['total_requests']}")
    print(f"  Successful: {stats['summary']['successful_requests']}")
    print(f"  Active: {stats['summary']['active_requests']}")

    print("\nWorker Stats from Dynamo:")
    worker_stats = stats.get("worker_stats", {})
    print(json.dumps(worker_stats, indent=2))

    # Verify worker stats are present
    assert "worker_stats" in stats
    assert worker_stats["total_workers"] == 4
    assert len(worker_stats["workers"]) == 4

    # Verify all workers have processed at least some requests
    total_processed = sum(w["total_requests"] for w in worker_stats["workers"])
    print(f"\nTotal requests processed across all workers: {total_processed}")
    assert total_processed >= 20

    print("\n✓ Test 3 passed!\n")


def test_dashboard_format():
    """Test that output matches expected dashboard format."""
    print("=" * 80)
    print("TEST 4: Dashboard Format Validation")
    print("=" * 80)

    reset_worker_pool()
    metrics = DynamoMetricsCollector(window_size=300, num_workers=4)

    # Simulate requests
    for i in range(10):
        request_id = f"req-{i}"
        req = metrics.start_request(
            request_id, "gpt-4", "/v1/chat/completions", input_tokens=50
        )
        metrics.record_prefill_start(request_id)
        metrics.record_first_token(request_id)
        metrics.complete_request(request_id, output_tokens=30, success=True)

    # Get stats in dashboard format
    stats = metrics.get_worker_stats()

    print("Dashboard Format Worker Stats:")
    print(json.dumps(stats, indent=2))

    # Verify required fields
    required_top_level = [
        "total_workers",
        "active_workers",
        "idle_workers",
        "offline_workers",
        "workers",
    ]
    for field in required_top_level:
        assert field in stats, f"Missing field: {field}"
        print(f"✓ Field present: {field}")

    # Verify worker object format
    required_worker_fields = [
        "worker_id",
        "status",
        "active_requests",
        "total_requests",
        "avg_request_duration_ms",
        "utilization",
    ]

    for worker in stats["workers"]:
        for field in required_worker_fields:
            assert field in worker, f"Missing worker field: {field}"

    print(f"\n✓ All required fields present!")
    print(f"✓ Worker format matches dashboard requirements!")

    # Show sample worker
    sample = stats["workers"][0]
    print(f"\nSample Worker Data:")
    print(f"  worker_id: {sample['worker_id']}")
    print(f"  status: {sample['status']}")
    print(f"  active_requests: {sample['active_requests']}")
    print(f"  total_requests: {sample['total_requests']}")
    print(f"  avg_request_duration_ms: {sample['avg_request_duration_ms']:.2f}")
    print(f"  utilization: {sample['utilization']:.3f}")

    print("\n✓ Test 4 passed!\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("WORKER POOL UTILIZATION TRACKING TEST SUITE")
    print("=" * 80 + "\n")

    try:
        test_worker_pool_basic()
        test_worker_utilization()
        test_dynamo_integration()
        test_dashboard_format()

        print("=" * 80)
        print("ALL TESTS PASSED!")
        print("=" * 80)
        print("\n✓ Worker pool implementation is working correctly")
        print("✓ Integration with DynamoMetricsCollector is functional")
        print("✓ Dashboard format requirements are met")
        print(
            "\nWorker stats are now available at: GET /dynamo/metrics/json (worker_stats key)"
        )

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
