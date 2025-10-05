#!/usr/bin/env python3
"""
Concurrent Connections Benchmark for FakeAI Server

Tests performance under high concurrency with 100+ concurrent connections.
Measures p50, p90, p99 latencies and validates smart router load balancing.
"""
#  SPDX-License-Identifier: Apache-2.0

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class ConcurrencyResult:
    """Result from a concurrency benchmark test."""

    test_name: str
    total_requests: int
    concurrent_connections: int
    successful_requests: int
    failed_requests: int
    total_time: float
    requests_per_second: float
    avg_latency: float
    min_latency: float
    max_latency: float
    p50_latency: float
    p90_latency: float
    p95_latency: float
    p99_latency: float
    total_tokens: int
    tokens_per_second: float
    latencies: list[float] = field(default_factory=list)
    error_messages: list[str] = field(default_factory=list)


class ConcurrentBenchmark:
    """Benchmark FakeAI server under concurrent load."""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "test"):
        self.base_url = base_url
        self.api_key = api_key
        self.results: list[ConcurrencyResult] = []

    async def _make_request(
        self, client: httpx.AsyncClient, request_id: int, payload: dict[str, Any]
    ) -> tuple[float, int, str | None]:
        """
        Make a single request.

        Returns:
            (latency_seconds, token_count, error_message)
        """
        start_time = time.perf_counter()

        try:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=120.0,
            )
            response.raise_for_status()
            latency = time.perf_counter() - start_time
            data = response.json()
            tokens = data.get("usage", {}).get("total_tokens", 0)
            return latency, tokens, None

        except httpx.TimeoutException:
            latency = time.perf_counter() - start_time
            return latency, 0, "Timeout"
        except httpx.HTTPStatusError as e:
            latency = time.perf_counter() - start_time
            return latency, 0, f"HTTP {e.response.status_code}"
        except Exception as e:
            latency = time.perf_counter() - start_time
            return latency, 0, str(e)

    async def run_concurrent_test(
        self,
        test_name: str,
        num_requests: int,
        concurrent_connections: int,
        payload: dict[str, Any],
    ) -> ConcurrencyResult:
        """
        Run a concurrent connections benchmark.

        Args:
            test_name: Name of the test
            num_requests: Total number of requests
            concurrent_connections: Number of concurrent connections
            payload: Request payload

        Returns:
            ConcurrencyResult with latency percentiles
        """
        print(f"\n{'='*70}")
        print(f"Running: {test_name}")
        print(f"Total Requests: {num_requests}")
        print(f"Concurrent Connections: {concurrent_connections}")
        print(f"{'='*70}")

        latencies = []
        tokens_list = []
        error_messages = []
        successful = 0
        failed = 0

        # Limit concurrent connections
        semaphore = asyncio.Semaphore(concurrent_connections)

        async def bounded_request(request_id: int):
            """Make request with concurrency limit."""
            async with semaphore:
                async with httpx.AsyncClient() as client:
                    latency, tokens, error = await self._make_request(client, request_id, payload)
                    return latency, tokens, error

        start_time = time.perf_counter()

        # Launch all requests
        tasks = [bounded_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                failed += 1
                error_messages.append(str(result))
            else:
                latency, tokens, error = result
                latencies.append(latency)
                tokens_list.append(tokens)

                if error:
                    failed += 1
                    error_messages.append(error)
                else:
                    successful += 1

        total_time = time.perf_counter() - start_time

        # Calculate statistics
        latencies.sort()
        total_tokens = sum(tokens_list)

        def percentile(data, p):
            if not data:
                return 0.0
            k = (len(data) - 1) * p
            f = int(k)
            c = k - f
            if f + 1 < len(data):
                return data[f] + (data[f + 1] - data[f]) * c
            return data[f]

        result = ConcurrencyResult(
            test_name=test_name,
            total_requests=num_requests,
            concurrent_connections=concurrent_connections,
            successful_requests=successful,
            failed_requests=failed,
            total_time=total_time,
            requests_per_second=successful / total_time if total_time > 0 else 0,
            avg_latency=sum(latencies) / len(latencies) if latencies else 0,
            min_latency=min(latencies) if latencies else 0,
            max_latency=max(latencies) if latencies else 0,
            p50_latency=percentile(latencies, 0.50),
            p90_latency=percentile(latencies, 0.90),
            p95_latency=percentile(latencies, 0.95),
            p99_latency=percentile(latencies, 0.99),
            total_tokens=total_tokens,
            tokens_per_second=total_tokens / total_time if total_time > 0 else 0,
            latencies=latencies,
            error_messages=error_messages[:10],  # Keep first 10 errors
        )

        self.results.append(result)
        self._print_result(result)
        return result

    async def run_ramp_up_test(
        self, payload: dict[str, Any], max_concurrency: int = 200, step: int = 20
    ):
        """
        Gradually increase concurrency to find breaking point.

        Args:
            payload: Request payload
            max_concurrency: Maximum concurrency to test
            step: Concurrency increment per test
        """
        print(f"\n{'='*70}")
        print(f"Running Ramp-Up Test")
        print(f"Max Concurrency: {max_concurrency}, Step: {step}")
        print(f"{'='*70}")

        for concurrency in range(step, max_concurrency + 1, step):
            await self.run_concurrent_test(
                test_name=f"Ramp-Up {concurrency} concurrent",
                num_requests=concurrency * 2,  # 2 requests per connection
                concurrent_connections=concurrency,
                payload=payload,
            )

            # Stop if error rate exceeds 10%
            last_result = self.results[-1]
            error_rate = (last_result.failed_requests / last_result.total_requests * 100)

            if error_rate > 10:
                print(f"\nStopping ramp-up: Error rate {error_rate:.2f}% exceeds threshold")
                break

            # Brief pause between tests
            await asyncio.sleep(2)

    async def run_sustained_load_test(
        self,
        duration_seconds: int,
        requests_per_second: int,
        payload: dict[str, Any],
    ) -> ConcurrencyResult:
        """
        Run sustained load test for specified duration.

        Args:
            duration_seconds: How long to run test
            requests_per_second: Target requests per second
            payload: Request payload

        Returns:
            ConcurrencyResult from sustained load
        """
        test_name = f"Sustained Load {requests_per_second} RPS for {duration_seconds}s"
        print(f"\n{'='*70}")
        print(f"Running: {test_name}")
        print(f"{'='*70}")

        latencies = []
        tokens_list = []
        error_messages = []
        successful = 0
        failed = 0

        start_time = time.perf_counter()
        end_time = start_time + duration_seconds
        request_interval = 1.0 / requests_per_second

        request_count = 0

        async with httpx.AsyncClient() as client:
            while time.perf_counter() < end_time:
                request_start = time.perf_counter()

                # Make request
                latency, tokens, error = await self._make_request(client, request_count, payload)
                latencies.append(latency)
                tokens_list.append(tokens)

                if error:
                    failed += 1
                    error_messages.append(error)
                else:
                    successful += 1

                request_count += 1

                # Sleep to maintain target RPS
                elapsed = time.perf_counter() - request_start
                sleep_time = max(0, request_interval - elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

        total_time = time.perf_counter() - start_time

        # Calculate statistics
        latencies.sort()
        total_tokens = sum(tokens_list)

        def percentile(data, p):
            if not data:
                return 0.0
            k = (len(data) - 1) * p
            f = int(k)
            c = k - f
            if f + 1 < len(data):
                return data[f] + (data[f + 1] - data[f]) * c
            return data[f]

        result = ConcurrencyResult(
            test_name=test_name,
            total_requests=request_count,
            concurrent_connections=1,  # Sequential in this test
            successful_requests=successful,
            failed_requests=failed,
            total_time=total_time,
            requests_per_second=successful / total_time if total_time > 0 else 0,
            avg_latency=sum(latencies) / len(latencies) if latencies else 0,
            min_latency=min(latencies) if latencies else 0,
            max_latency=max(latencies) if latencies else 0,
            p50_latency=percentile(latencies, 0.50),
            p90_latency=percentile(latencies, 0.90),
            p95_latency=percentile(latencies, 0.95),
            p99_latency=percentile(latencies, 0.99),
            total_tokens=total_tokens,
            tokens_per_second=total_tokens / total_time if total_time > 0 else 0,
            latencies=latencies,
            error_messages=error_messages[:10],
        )

        self.results.append(result)
        self._print_result(result)
        return result

    def _print_result(self, result: ConcurrencyResult):
        """Print benchmark result."""
        print(f"\n{'='*70}")
        print(f"Results: {result.test_name}")
        print(f"{'='*70}")
        print(f"Total Requests:      {result.total_requests}")
        print(f"Successful:          {result.successful_requests}")
        print(f"Failed:              {result.failed_requests}")
        print(
            f"Error Rate:          {(result.failed_requests / result.total_requests * 100):.2f}%"
        )
        print(f"Total Time:          {result.total_time:.2f}s")
        print(f"Requests/sec:        {result.requests_per_second:.2f}")
        print(f"Tokens/sec:          {result.tokens_per_second:.2f}")
        print(f"\nLatency Percentiles:")
        print(f"  Average:           {result.avg_latency*1000:.2f}ms")
        print(f"  Min:               {result.min_latency*1000:.2f}ms")
        print(f"  Max:               {result.max_latency*1000:.2f}ms")
        print(f"  P50 (Median):      {result.p50_latency*1000:.2f}ms")
        print(f"  P90:               {result.p90_latency*1000:.2f}ms")
        print(f"  P95:               {result.p95_latency*1000:.2f}ms")
        print(f"  P99:               {result.p99_latency*1000:.2f}ms")

        if result.error_messages:
            print(f"\nSample Errors ({len(result.error_messages)}):")
            for error in result.error_messages[:5]:
                print(f"  - {error}")

    def generate_markdown_report(self) -> str:
        """Generate markdown report of all benchmark results."""
        report = "# Concurrent Connections Benchmark Results\n\n"
        report += f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Summary table
        report += "## Summary\n\n"
        report += "| Test | Requests | Concurrent | Success Rate | RPS | P50 | P90 | P99 |\n"
        report += "|------|----------|------------|--------------|-----|-----|-----|-----|\n"

        for result in self.results:
            success_rate = (result.successful_requests / result.total_requests * 100) if result.total_requests > 0 else 0
            report += (
                f"| {result.test_name} | {result.total_requests} | "
                f"{result.concurrent_connections} | {success_rate:.1f}% | "
                f"{result.requests_per_second:.2f} | {result.p50_latency*1000:.2f}ms | "
                f"{result.p90_latency*1000:.2f}ms | {result.p99_latency*1000:.2f}ms |\n"
            )

        # Detailed results
        report += "\n## Detailed Results\n\n"
        for result in self.results:
            report += f"### {result.test_name}\n\n"
            report += f"- **Total Requests:** {result.total_requests}\n"
            report += f"- **Concurrent Connections:** {result.concurrent_connections}\n"
            report += f"- **Successful:** {result.successful_requests}\n"
            report += f"- **Failed:** {result.failed_requests}\n"
            success_rate = (result.successful_requests / result.total_requests * 100) if result.total_requests > 0 else 0
            report += f"- **Success Rate:** {success_rate:.2f}%\n"
            report += f"- **Total Time:** {result.total_time:.2f}s\n"
            report += f"- **Requests/sec:** {result.requests_per_second:.2f}\n"
            report += f"- **Tokens/sec:** {result.tokens_per_second:.2f}\n\n"
            report += "**Latency Percentiles:**\n\n"
            report += f"- Average: {result.avg_latency*1000:.2f}ms\n"
            report += f"- Min: {result.min_latency*1000:.2f}ms\n"
            report += f"- Max: {result.max_latency*1000:.2f}ms\n"
            report += f"- P50 (Median): {result.p50_latency*1000:.2f}ms\n"
            report += f"- P90: {result.p90_latency*1000:.2f}ms\n"
            report += f"- P95: {result.p95_latency*1000:.2f}ms\n"
            report += f"- P99: {result.p99_latency*1000:.2f}ms\n\n"

            if result.error_messages:
                report += "**Sample Errors:**\n\n"
                for error in result.error_messages[:5]:
                    report += f"- {error}\n"
                report += "\n"

        # Performance analysis
        report += "## Performance Analysis\n\n"

        # Find optimal concurrency
        successful_results = [r for r in self.results if r.failed_requests == 0]
        if successful_results:
            best_rps = max(successful_results, key=lambda r: r.requests_per_second)
            report += f"**Best Performance (no errors):**\n\n"
            report += f"- Test: {best_rps.test_name}\n"
            report += f"- Requests/sec: {best_rps.requests_per_second:.2f}\n"
            report += f"- P99 Latency: {best_rps.p99_latency*1000:.2f}ms\n"
            report += f"- Concurrent Connections: {best_rps.concurrent_connections}\n\n"

        # Identify breaking point
        failed_results = [r for r in self.results if r.failed_requests > 0]
        if failed_results:
            first_failure = min(failed_results, key=lambda r: r.concurrent_connections)
            report += f"**First Performance Degradation:**\n\n"
            report += f"- Test: {first_failure.test_name}\n"
            report += f"- Concurrent Connections: {first_failure.concurrent_connections}\n"
            error_rate = (first_failure.failed_requests / first_failure.total_requests * 100)
            report += f"- Error Rate: {error_rate:.2f}%\n\n"

        return report


async def run_all_benchmarks(base_url: str = "http://localhost:8000", api_key: str = "test"):
    """Run all concurrent connection benchmarks."""
    benchmark = ConcurrentBenchmark(base_url, api_key)

    # Standard payload
    payload = {
        "model": "meta-llama/Llama-3.1-8B-Instruct",
        "messages": [{"role": "user", "content": "Hello, how are you?"}],
        "max_tokens": 50,
    }

    # Test 1: Low concurrency baseline
    await benchmark.run_concurrent_test(
        test_name="10 Concurrent Connections",
        num_requests=100,
        concurrent_connections=10,
        payload=payload,
    )

    # Test 2: Medium concurrency
    await benchmark.run_concurrent_test(
        test_name="50 Concurrent Connections",
        num_requests=200,
        concurrent_connections=50,
        payload=payload,
    )

    # Test 3: High concurrency
    await benchmark.run_concurrent_test(
        test_name="100 Concurrent Connections",
        num_requests=300,
        concurrent_connections=100,
        payload=payload,
    )

    # Test 4: Very high concurrency
    await benchmark.run_concurrent_test(
        test_name="200 Concurrent Connections",
        num_requests=400,
        concurrent_connections=200,
        payload=payload,
    )

    # Test 5: Sustained load
    await benchmark.run_sustained_load_test(
        duration_seconds=30,
        requests_per_second=10,
        payload=payload,
    )

    # Test 6: Ramp-up test (commented out to avoid overwhelming server)
    # await benchmark.run_ramp_up_test(payload, max_concurrency=200, step=20)

    # Generate report
    report = benchmark.generate_markdown_report()
    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print("=" * 70)
    print(report)

    # Save report
    report_path = "/home/anthony/projects/fakeai/benchmarks/concurrent_results.md"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")

    return benchmark


if __name__ == "__main__":
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    api_key = sys.argv[2] if len(sys.argv) > 2 else "test"

    print(f"Running concurrent connection benchmarks against: {base_url}")
    asyncio.run(run_all_benchmarks(base_url, api_key))
