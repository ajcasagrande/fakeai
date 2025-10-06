#!/usr/bin/env python3
"""
Test FakeAI with 10,000 concurrent requests using proper async patterns.

Validates that asyncio/uvloop implementation can handle extreme concurrency.
"""
import asyncio
import time
from datetime import datetime

import aiohttp


async def make_request(session, request_id):
    """Make a single async request."""
    try:
        async with session.post(
            "http://localhost:9001/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": f"Request {request_id}"}],
                "max_tokens": 5,  # Small response for speed
            },
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            if response.status == 200:
                data = await response.json()
                return {"id": request_id, "success": True, "status": 200}
            else:
                return {"id": request_id, "success": False, "status": response.status}

    except asyncio.TimeoutError:
        return {"id": request_id, "success": False, "error": "timeout"}
    except Exception as e:
        return {"id": request_id, "success": False, "error": str(e)}


async def load_test_concurrent(num_requests=10000, batch_size=1000):
    """
    Run load test with high concurrency.

    Args:
        num_requests: Total requests to make
        batch_size: Requests per batch (to avoid overwhelming client)
    """
    print("=" * 70)
    print(f"  FakeAI Load Test - {num_requests:,} Concurrent Requests")
    print("=" * 70)
    print()
    print(f"Start time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"Target: {num_requests:,} requests")
    print(f"Batch size: {batch_size:,}")
    print(f"Batches: {num_requests // batch_size}")
    print()

    start_time = time.time()
    total_success = 0
    total_failed = 0
    all_results = []

    # High-concurrency connector
    connector = aiohttp.TCPConnector(
        limit=2000,  # Max 2000 concurrent connections
        limit_per_host=2000,
        ttl_dns_cache=300,
        force_close=False,  # Reuse connections
        enable_cleanup_closed=True,
    )

    async with aiohttp.ClientSession(connector=connector) as session:
        # Process in batches
        for batch_num in range(0, num_requests, batch_size):
            batch_start = time.time()

            # Create tasks for this batch
            batch_tasks = [
                make_request(session, i)
                for i in range(batch_num, min(batch_num + batch_size, num_requests))
            ]

            # Execute batch concurrently
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=False)

            # Count successes
            batch_success = sum(1 for r in batch_results if r.get("success"))
            batch_failed = len(batch_results) - batch_success

            total_success += batch_success
            total_failed += batch_failed
            all_results.extend(batch_results)

            batch_elapsed = time.time() - batch_start
            batch_rate = len(batch_results) / batch_elapsed if batch_elapsed > 0 else 0

            print(
                f"Batch {batch_num//batch_size + 1}/{num_requests//batch_size}: "
                f"{batch_success}/{len(batch_results)} succeeded "
                f"({batch_elapsed:.2f}s, {batch_rate:.0f} req/s)"
            )

    total_elapsed = time.time() - start_time

    # Summary
    print()
    print("=" * 70)
    print("  RESULTS")
    print("=" * 70)
    print(f"Total requests: {num_requests:,}")
    print(f"Successful: {total_success:,} ({total_success/num_requests*100:.1f}%)")
    print(f"Failed: {total_failed:,} ({total_failed/num_requests*100:.1f}%)")
    print(f"Time: {total_elapsed:.2f}s")
    print(f"Throughput: {num_requests/total_elapsed:.0f} req/s")
    print(f"Avg latency: {total_elapsed/num_requests*1000:.2f}ms")
    print()

    # Get final metrics
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:9001/dynamo/metrics/json") as resp:
                metrics = await resp.json()

                print("Server Metrics:")
                print(f"  Total tracked: {metrics['summary']['total_requests']}")
                print(f"  TTFT p50: {metrics['latency']['ttft']['p50']:.2f}ms")
                print(f"  TTFT p99: {metrics['latency']['ttft']['p99']:.2f}ms")
                print(
                    f"  Throughput: {metrics['throughput']['tokens_per_second']:.1f} tok/s"
                )
                print(f"  Cache hit rate: {metrics['cache']['hit_rate']:.1f}%")
    except:
        pass

    print()
    print("=" * 70)

    return total_success == num_requests


async def quick_test(num_requests=100):
    """Quick test with 100 requests."""
    print(f"Quick test: {num_requests} requests...")

    start = time.time()
    connector = aiohttp.TCPConnector(limit=100)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [make_request(session, i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)

    elapsed = time.time() - start
    success = sum(1 for r in results if r.get("success"))

    print(
        f"  {success}/{num_requests} succeeded in {elapsed:.2f}s ({num_requests/elapsed:.0f} req/s)"
    )
    print()

    return success == num_requests


async def main():
    """Main entry point."""
    import sys

    print()
    print("FakeAI Async Load Test")
    print()

    # Check if server is running
    async def check_server():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:9001/health",
                    timeout=aiohttp.ClientTimeout(total=2),
                ) as r:
                    if r.status == 200:
                        print("✓ Server is running on port 9001")
                        print()
                        return True
        except:
            pass
        print("✗ Server not running on port 9001")
        print()
        print("Start server with:")
        print("  FAKEAI_RESPONSE_DELAY=0.0 fakeai server --port 9001")
        print()
        return False

    if not await check_server():
        sys.exit(1)

    # Run tests
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # Quick test mode
        success = await quick_test(100)
    elif len(sys.argv) > 1 and sys.argv[1] == "full":
        # Full 10k test
        success = await load_test_concurrent(10000, batch_size=1000)
    else:
        # Progressive test
        print("Running progressive test (100 → 1000 → 10000)...")
        print()

        success = await quick_test(100)
        if success:
            print("✓ 100 requests passed, trying 1000...")
            success = await load_test_concurrent(1000, batch_size=500)

        if success:
            print()
            print("✓ 1000 requests passed, trying 10000...")
            success = await load_test_concurrent(10000, batch_size=1000)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
