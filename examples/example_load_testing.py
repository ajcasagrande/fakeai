#!/usr/bin/env python3
"""
Load Testing and Performance Benchmarking with FakeAI.

This example demonstrates:
- Concurrent request handling
- Rate limiting behavior
- Performance metrics collection
- Throughput measurement
- Latency percentiles
- Cache performance under load
- Streaming vs non-streaming performance
- Resource utilization monitoring

Perfect for testing your application's behavior under load
before deploying to production.
"""
import asyncio
import statistics
import time
from dataclasses import dataclass, field
from typing import List

import httpx
from openai import AsyncOpenAI

# Base URL for FakeAI server
BASE_URL = "http://localhost:8000"


@dataclass
class LoadTestResult:
    """Results from a load test run."""

    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time_seconds: float
    requests_per_second: float
    latencies_ms: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def avg_latency_ms(self) -> float:
        return statistics.mean(self.latencies_ms) if self.latencies_ms else 0

    @property
    def median_latency_ms(self) -> float:
        return statistics.median(self.latencies_ms) if self.latencies_ms else 0

    @property
    def p95_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0
        sorted_latencies = sorted(self.latencies_ms)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[index]

    @property
    def p99_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0
        sorted_latencies = sorted(self.latencies_ms)
        index = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[index]

    @property
    def min_latency_ms(self) -> float:
        return min(self.latencies_ms) if self.latencies_ms else 0

    @property
    def max_latency_ms(self) -> float:
        return max(self.latencies_ms) if self.latencies_ms else 0


async def make_single_request(
    client: AsyncOpenAI,
    request_id: int,
    message: str = "Hello, world!",
    model: str = "openai/gpt-oss-120b",
) -> tuple[bool, float, str]:
    """
    Make a single chat completion request.

    Returns:
        (success, latency_ms, error_message)
    """
    start = time.time()

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": message}],
        )

        latency = (time.time() - start) * 1000
        return True, latency, ""

    except Exception as e:
        latency = (time.time() - start) * 1000
        return False, latency, str(e)


async def load_test_concurrent(
    num_requests: int,
    concurrency: int,
    model: str = "openai/gpt-oss-120b",
    message: str = "Hello, world!",
) -> LoadTestResult:
    """
    Run concurrent load test.

    Args:
        num_requests: Total number of requests
        concurrency: Number of concurrent requests
        model: Model to use
        message: Message to send

    Returns:
        LoadTestResult with metrics
    """
    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
        max_retries=0,  # Don't retry for load testing
    )

    successful = 0
    failed = 0
    latencies = []
    errors = []

    # Create semaphore to limit concurrency
    semaphore = asyncio.Semaphore(concurrency)

    async def make_request_with_semaphore(request_id: int):
        nonlocal successful, failed

        async with semaphore:
            success, latency, error = await make_single_request(
                client, request_id, message, model
            )

            if success:
                successful += 1
            else:
                failed += 1
                if error not in errors:
                    errors.append(error)

            latencies.append(latency)

    # Start timer
    start_time = time.time()

    # Create all tasks
    tasks = [make_request_with_semaphore(i) for i in range(num_requests)]

    # Wait for all to complete
    await asyncio.gather(*tasks)

    # Calculate metrics
    total_time = time.time() - start_time
    rps = num_requests / total_time if total_time > 0 else 0

    return LoadTestResult(
        total_requests=num_requests,
        successful_requests=successful,
        failed_requests=failed,
        total_time_seconds=total_time,
        requests_per_second=rps,
        latencies_ms=latencies,
        errors=errors,
    )


async def demonstrate_basic_load_test():
    """Demonstrate basic load testing."""
    print("=" * 80)
    print("PART 1: BASIC LOAD TEST")
    print("=" * 80)
    print()

    print("Running 100 requests with 10 concurrent...")
    print()

    result = await load_test_concurrent(
        num_requests=100,
        concurrency=10,
    )

    print("Results:")
    print("-" * 80)
    print(f"Total requests:       {result.total_requests}")
    print(f"Successful:           {result.successful_requests}")
    print(f"Failed:               {result.failed_requests}")
    print(f"Total time:           {result.total_time_seconds:.2f}s")
    print(f"Requests/second:      {result.requests_per_second:.2f}")
    print()
    print("Latency:")
    print(f"  Min:                {result.min_latency_ms:.2f}ms")
    print(f"  Max:                {result.max_latency_ms:.2f}ms")
    print(f"  Average:            {result.avg_latency_ms:.2f}ms")
    print(f"  Median:             {result.median_latency_ms:.2f}ms")
    print(f"  P95:                {result.p95_latency_ms:.2f}ms")
    print(f"  P99:                {result.p99_latency_ms:.2f}ms")
    print()


async def demonstrate_concurrency_scaling():
    """Test different concurrency levels."""
    print("=" * 80)
    print("PART 2: CONCURRENCY SCALING")
    print("=" * 80)
    print()

    print("Testing different concurrency levels (50 requests each)...")
    print()

    concurrency_levels = [1, 5, 10, 20, 50]

    print(f"{'Concurrency':<15} {'Time (s)':<12} {'RPS':<12} {'Avg Latency (ms)':<20}")
    print("-" * 80)

    for concurrency in concurrency_levels:
        result = await load_test_concurrent(
            num_requests=50,
            concurrency=concurrency,
        )

        print(
            f"{concurrency:<15} {result.total_time_seconds:<12.2f} "
            f"{result.requests_per_second:<12.2f} {result.avg_latency_ms:<20.2f}"
        )

    print()
    print("Observations:")
    print("  • Higher concurrency = better throughput (RPS)")
    print("  • But may increase average latency")
    print("  • Find optimal balance for your use case")
    print()


async def demonstrate_streaming_vs_nonstreaming():
    """Compare streaming vs non-streaming performance."""
    print("=" * 80)
    print("PART 3: STREAMING vs NON-STREAMING")
    print("=" * 80)
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    num_requests = 20

    # Test non-streaming
    print("Non-streaming (20 requests)...")
    start = time.time()

    for i in range(num_requests):
        await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Count to 5"}],
            stream=False,
        )

    non_streaming_time = time.time() - start

    # Test streaming
    print("Streaming (20 requests)...")
    start = time.time()

    for i in range(num_requests):
        stream = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Count to 5"}],
            stream=True,
        )

        # Consume stream
        async for _ in stream:
            pass

    streaming_time = time.time() - start

    print()
    print("Results:")
    print("-" * 80)
    print(
        f"Non-streaming: {non_streaming_time:.2f}s ({num_requests/non_streaming_time:.2f} RPS)"
    )
    print(
        f"Streaming:     {streaming_time:.2f}s ({num_requests/streaming_time:.2f} RPS)"
    )
    print()

    if streaming_time < non_streaming_time:
        diff = (non_streaming_time - streaming_time) / non_streaming_time * 100
        print(f"Streaming is {diff:.1f}% faster (time to first token)")
    else:
        diff = (streaming_time - non_streaming_time) / streaming_time * 100
        print(f"Non-streaming is {diff:.1f}% faster (total completion time)")

    print()


async def demonstrate_cache_performance():
    """Test cache impact on load."""
    print("=" * 80)
    print("PART 4: CACHE PERFORMANCE UNDER LOAD")
    print("=" * 80)
    print()

    # Test without cache (different messages)
    print("Test 1: No cache (different messages)")
    print("-" * 80)

    tasks = []
    client = AsyncOpenAI(api_key="test-key", base_url=BASE_URL)

    start = time.time()
    for i in range(50):
        task = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": f"System message {i}"},
                {"role": "user", "content": "Hello"},
            ],
        )
        tasks.append(task)

    responses = await asyncio.gather(*tasks)
    no_cache_time = time.time() - start

    # Calculate cache stats
    cached_tokens_sum = sum(
        r.usage.prompt_tokens_details.cached_tokens
        for r in responses
        if r.usage.prompt_tokens_details
    )

    print(f"Time: {no_cache_time:.2f}s")
    print(f"Cached tokens: {cached_tokens_sum}")
    print()

    # Test with cache (same system message)
    print("Test 2: With cache (same system message)")
    print("-" * 80)

    tasks = []
    start = time.time()

    for i in range(50):
        task = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Question {i}"},
            ],
        )
        tasks.append(task)

    responses = await asyncio.gather(*tasks)
    cache_time = time.time() - start

    # Calculate cache stats
    cached_tokens_sum = sum(
        r.usage.prompt_tokens_details.cached_tokens
        for r in responses
        if r.usage.prompt_tokens_details
    )

    print(f"Time: {cache_time:.2f}s")
    print(f"Cached tokens: {cached_tokens_sum}")
    print()

    improvement = (
        ((no_cache_time - cache_time) / no_cache_time * 100) if no_cache_time > 0 else 0
    )
    print(f"Performance improvement with cache: {improvement:.1f}%")
    print()


async def demonstrate_rate_limiting():
    """Demonstrate rate limiting behavior."""
    print("=" * 80)
    print("PART 5: RATE LIMITING (if enabled)")
    print("=" * 80)
    print()

    print("Sending rapid burst of requests...")
    print("(FakeAI rate limiting is disabled by default)")
    print()

    client = AsyncOpenAI(
        api_key="test-key",
        base_url=BASE_URL,
    )

    # Send burst
    start = time.time()
    tasks = []

    for i in range(100):
        task = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": "Hi"}],
        )
        tasks.append(task)

    try:
        await asyncio.gather(*tasks)
        elapsed = time.time() - start

        print(f"✓ All 100 requests completed in {elapsed:.2f}s")
        print(f"  Throughput: {100/elapsed:.2f} requests/second")
        print()
        print("Note: To enable rate limiting, start server with:")
        print("  FAKEAI_RATE_LIMIT_ENABLED=true python run_server.py")

    except Exception as e:
        print(f"❌ Rate limit exceeded: {e}")

    print()


async def demonstrate_server_metrics():
    """Fetch and display server metrics."""
    print("=" * 80)
    print("PART 6: SERVER METRICS")
    print("=" * 80)
    print()

    # Make some requests first
    print("Making 50 requests to generate metrics...")

    client = AsyncOpenAI(api_key="test-key", base_url=BASE_URL)
    tasks = [
        client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": f"Request {i}"}],
        )
        for i in range(50)
    ]
    await asyncio.gather(*tasks)

    print()
    print("Fetching server metrics...")
    print()

    # Fetch metrics from server
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(f"{BASE_URL}/metrics")
        metrics = response.json()

    # Display key metrics
    print("Chat Completions Endpoint:")
    print("-" * 80)

    if "requests" in metrics and "/v1/chat/completions" in metrics["requests"]:
        req_metrics = metrics["requests"]["/v1/chat/completions"]
        print(f"Request rate:  {req_metrics.get('rate', 0):.2f} req/s")

    if "responses" in metrics and "/v1/chat/completions" in metrics["responses"]:
        resp_metrics = metrics["responses"]["/v1/chat/completions"]
        print(f"Response rate: {resp_metrics.get('rate', 0):.2f} req/s")
        print(f"Avg latency:   {resp_metrics.get('avg', 0):.2f}ms")
        print(f"P50 latency:   {resp_metrics.get('p50', 0):.2f}ms")
        print(f"P90 latency:   {resp_metrics.get('p90', 0):.2f}ms")
        print(f"P99 latency:   {resp_metrics.get('p99', 0):.2f}ms")

    if "tokens" in metrics and "/v1/chat/completions" in metrics["tokens"]:
        token_metrics = metrics["tokens"]["/v1/chat/completions"]
        print(f"Token rate:    {token_metrics.get('rate', 0):.2f} tokens/s")

    print()


async def run_benchmark_suite():
    """Run comprehensive benchmark suite."""
    print("=" * 80)
    print("PART 7: COMPREHENSIVE BENCHMARK SUITE")
    print("=" * 80)
    print()

    benchmark_configs = [
        {"name": "Light load", "requests": 50, "concurrency": 5},
        {"name": "Medium load", "requests": 100, "concurrency": 10},
        {"name": "Heavy load", "requests": 200, "concurrency": 20},
    ]

    print(
        f"{'Benchmark':<20} {'Requests':<12} {'RPS':<12} {'P95 (ms)':<12} {'P99 (ms)':<12}"
    )
    print("-" * 80)

    for config in benchmark_configs:
        result = await load_test_concurrent(
            num_requests=config["requests"],
            concurrency=config["concurrency"],
        )

        print(
            f"{config['name']:<20} {result.successful_requests:<12} "
            f"{result.requests_per_second:<12.2f} "
            f"{result.p95_latency_ms:<12.2f} {result.p99_latency_ms:<12.2f}"
        )

    print()


async def main():
    """Run all load testing demonstrations."""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 18 + "FakeAI Load Testing & Benchmarking" + " " * 25 + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("This demo performs load testing and performance benchmarking of FakeAI.")
    print("Use these patterns to test your application's behavior under load.")
    print()
    input("Press Enter to start...")
    print()

    try:
        await demonstrate_basic_load_test()
        input("Press Enter to continue...")
        print()

        await demonstrate_concurrency_scaling()
        input("Press Enter to continue...")
        print()

        await demonstrate_streaming_vs_nonstreaming()
        input("Press Enter to continue...")
        print()

        await demonstrate_cache_performance()
        input("Press Enter to continue...")
        print()

        await demonstrate_rate_limiting()
        input("Press Enter to continue...")
        print()

        await demonstrate_server_metrics()
        input("Press Enter to continue...")
        print()

        await run_benchmark_suite()

        print("=" * 80)
        print("LOAD TESTING BEST PRACTICES")
        print("=" * 80)
        print()
        print("1. Understand Your Metrics:")
        print("   • RPS (requests per second) - throughput")
        print("   • Latency percentiles - user experience")
        print("   • P95/P99 more important than average")
        print("   • Error rate - reliability")
        print()
        print("2. Test Scenarios:")
        print("   • Light, medium, heavy load")
        print("   • Burst traffic")
        print("   • Sustained load")
        print("   • Gradual ramp-up")
        print()
        print("3. Optimize Based on Findings:")
        print("   • Adjust concurrency limits")
        print("   • Tune cache strategies")
        print("   • Set appropriate timeouts")
        print("   • Configure rate limiting")
        print()
        print("4. Monitor Production:")
        print("   • Track same metrics in production")
        print("   • Set up alerts on anomalies")
        print("   • Compare to load test baselines")
        print()
        print("5. Load Testing FakeAI Benefits:")
        print("   • Test without using real API credits")
        print("   • Validate error handling")
        print("   • Measure client-side performance")
        print("   • Test retry logic")
        print("   • Verify rate limiting")
        print()

    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Make sure FakeAI server is running:")
        print("  python run_server.py")
        print()


if __name__ == "__main__":
    asyncio.run(main())
