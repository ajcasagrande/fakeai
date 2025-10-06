#!/usr/bin/env python3
"""
Throughput Benchmark for FakeAI Server

Measures requests per second (RPS) with various payload sizes and configurations.
Compares streaming vs non-streaming performance.
"""
#  SPDX-License-Identifier: Apache-2.0

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class ThroughputResult:
    """Result from a throughput benchmark run."""

    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float
    requests_per_second: float
    avg_latency: float
    min_latency: float
    max_latency: float
    p50_latency: float
    p90_latency: float
    p99_latency: float
    total_tokens: int
    tokens_per_second: float
    payload_size: str
    streaming: bool
    latencies: list[float] = field(default_factory=list)


class ThroughputBenchmark:
    """Benchmark FakeAI server throughput."""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "test"):
        self.base_url = base_url
        self.api_key = api_key
        self.results: list[ThroughputResult] = []

    async def _make_request(
        self,
        client: httpx.AsyncClient,
        payload: dict[str, Any],
        streaming: bool = False,
    ) -> tuple[float, int]:
        """
        Make a single request and measure latency.

        Returns:
            (latency_seconds, token_count)
        """
        start_time = time.perf_counter()
        tokens = 0

        try:
            if streaming:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=60.0,
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: ") and not line.endswith("[DONE]"):
                            # Count tokens in streaming response
                            tokens += 1
            else:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()
                tokens = data.get("usage", {}).get("total_tokens", 0)

            latency = time.perf_counter() - start_time
            return latency, tokens

        except Exception as e:
            latency = time.perf_counter() - start_time
            print(f"Request failed: {e}")
            return latency, 0

    async def run_benchmark(
        self,
        test_name: str,
        num_requests: int,
        payload: dict[str, Any],
        payload_size: str,
        streaming: bool = False,
        concurrent_limit: int = 10,
    ) -> ThroughputResult:
        """
        Run a throughput benchmark.

        Args:
            test_name: Name of the test
            num_requests: Total number of requests to make
            payload: Request payload
            payload_size: Description of payload size (e.g., "small", "medium", "large")
            streaming: Whether to use streaming
            concurrent_limit: Maximum concurrent requests

        Returns:
            ThroughputResult with benchmark metrics
        """
        print(f"\n{'='*70}")
        print(f"Running: {test_name}")
        print(
            f"Requests: {num_requests}, Concurrent: {concurrent_limit}, Streaming: {streaming}"
        )
        print(f"{'='*70}")

        latencies = []
        tokens_list = []
        successful = 0
        failed = 0

        semaphore = asyncio.Semaphore(concurrent_limit)

        async def bounded_request(client: httpx.AsyncClient):
            """Make a request with concurrency limit."""
            async with semaphore:
                latency, tokens = await self._make_request(client, payload, streaming)
                return latency, tokens

        start_time = time.perf_counter()

        async with httpx.AsyncClient() as client:
            tasks = [bounded_request(client) for _ in range(num_requests)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    failed += 1
                else:
                    latency, tokens = result
                    latencies.append(latency)
                    tokens_list.append(tokens)
                    if tokens > 0:
                        successful += 1
                    else:
                        failed += 1

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

        result = ThroughputResult(
            test_name=test_name,
            total_requests=num_requests,
            successful_requests=successful,
            failed_requests=failed,
            total_time=total_time,
            requests_per_second=successful / total_time if total_time > 0 else 0,
            avg_latency=sum(latencies) / len(latencies) if latencies else 0,
            min_latency=min(latencies) if latencies else 0,
            max_latency=max(latencies) if latencies else 0,
            p50_latency=percentile(latencies, 0.50),
            p90_latency=percentile(latencies, 0.90),
            p99_latency=percentile(latencies, 0.99),
            total_tokens=total_tokens,
            tokens_per_second=total_tokens / total_time if total_time > 0 else 0,
            payload_size=payload_size,
            streaming=streaming,
            latencies=latencies,
        )

        self.results.append(result)
        self._print_result(result)
        return result

    def _print_result(self, result: ThroughputResult):
        """Print benchmark result."""
        print(f"\n{'='*70}")
        print(f"Results: {result.test_name}")
        print(f"{'='*70}")
        print(f"Total Requests:      {result.total_requests}")
        print(f"Successful:          {result.successful_requests}")
        print(f"Failed:              {result.failed_requests}")
        print(f"Total Time:          {result.total_time:.2f}s")
        print(f"Requests/sec:        {result.requests_per_second:.2f}")
        print(f"Tokens/sec:          {result.tokens_per_second:.2f}")
        print(f"\nLatency Statistics:")
        print(f"  Average:           {result.avg_latency*1000:.2f}ms")
        print(f"  Min:               {result.min_latency*1000:.2f}ms")
        print(f"  Max:               {result.max_latency*1000:.2f}ms")
        print(f"  P50:               {result.p50_latency*1000:.2f}ms")
        print(f"  P90:               {result.p90_latency*1000:.2f}ms")
        print(f"  P99:               {result.p99_latency*1000:.2f}ms")

    def generate_markdown_report(self) -> str:
        """Generate markdown report of all benchmark results."""
        report = "# Throughput Benchmark Results\n\n"
        report += f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Summary table
        report += "## Summary\n\n"
        report += "| Test | Requests | RPS | Tokens/sec | Avg Latency | P90 Latency | P99 Latency |\n"
        report += "|------|----------|-----|------------|-------------|-------------|-------------|\n"

        for result in self.results:
            report += (
                f"| {result.test_name} | {result.successful_requests} | "
                f"{result.requests_per_second:.2f} | {result.tokens_per_second:.2f} | "
                f"{result.avg_latency*1000:.2f}ms | {result.p50_latency*1000:.2f}ms | "
                f"{result.p99_latency*1000:.2f}ms |\n"
            )

        # Detailed results
        report += "\n## Detailed Results\n\n"
        for result in self.results:
            report += f"### {result.test_name}\n\n"
            report += f"- **Payload Size:** {result.payload_size}\n"
            report += f"- **Streaming:** {result.streaming}\n"
            report += f"- **Total Requests:** {result.total_requests}\n"
            report += f"- **Successful:** {result.successful_requests}\n"
            report += f"- **Failed:** {result.failed_requests}\n"
            report += f"- **Total Time:** {result.total_time:.2f}s\n"
            report += f"- **Requests/sec:** {result.requests_per_second:.2f}\n"
            report += f"- **Tokens/sec:** {result.tokens_per_second:.2f}\n\n"
            report += "**Latency Statistics:**\n\n"
            report += f"- Average: {result.avg_latency*1000:.2f}ms\n"
            report += f"- Min: {result.min_latency*1000:.2f}ms\n"
            report += f"- Max: {result.max_latency*1000:.2f}ms\n"
            report += f"- P50: {result.p50_latency*1000:.2f}ms\n"
            report += f"- P90: {result.p90_latency*1000:.2f}ms\n"
            report += f"- P99: {result.p99_latency*1000:.2f}ms\n\n"

        # Streaming vs Non-streaming comparison
        streaming_results = [r for r in self.results if r.streaming]
        non_streaming_results = [r for r in self.results if not r.streaming]

        if streaming_results and non_streaming_results:
            report += "## Streaming vs Non-Streaming\n\n"
            report += "| Metric | Non-Streaming | Streaming | Difference |\n"
            report += "|--------|---------------|-----------|------------|\n"

            avg_non_stream_rps = sum(
                r.requests_per_second for r in non_streaming_results
            ) / len(non_streaming_results)
            avg_stream_rps = sum(
                r.requests_per_second for r in streaming_results
            ) / len(streaming_results)
            diff_rps = (avg_stream_rps - avg_non_stream_rps) / avg_non_stream_rps * 100

            avg_non_stream_latency = sum(
                r.avg_latency for r in non_streaming_results
            ) / len(non_streaming_results)
            avg_stream_latency = sum(r.avg_latency for r in streaming_results) / len(
                streaming_results
            )
            diff_latency = (
                (avg_stream_latency - avg_non_stream_latency)
                / avg_non_stream_latency
                * 100
            )

            report += (
                f"| Avg RPS | {avg_non_stream_rps:.2f} | {avg_stream_rps:.2f} | "
                f"{diff_rps:+.1f}% |\n"
            )
            report += (
                f"| Avg Latency | {avg_non_stream_latency*1000:.2f}ms | "
                f"{avg_stream_latency*1000:.2f}ms | {diff_latency:+.1f}% |\n"
            )

        return report


async def run_all_benchmarks(
    base_url: str = "http://localhost:8000", api_key: str = "test"
):
    """Run all throughput benchmarks."""
    benchmark = ThroughputBenchmark(base_url, api_key)

    # Test configurations
    small_payload = {
        "model": "meta-llama/Llama-3.1-8B-Instruct",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 50,
    }

    medium_payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": "Write a short story about a robot learning to code.",
            },
        ],
        "max_tokens": 200,
    }

    large_payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": "You are an expert software engineer."},
            {
                "role": "user",
                "content": (
                    "Please explain the concept of asynchronous programming in Python, "
                    "including coroutines, event loops, and async/await syntax. "
                    "Provide code examples and best practices."
                ),
            },
        ],
        "max_tokens": 500,
    }

    # Run benchmarks
    await benchmark.run_benchmark(
        "Small Payload - Non-Streaming",
        num_requests=100,
        payload=small_payload,
        payload_size="small",
        streaming=False,
        concurrent_limit=10,
    )

    await benchmark.run_benchmark(
        "Small Payload - Streaming",
        num_requests=100,
        payload={**small_payload, "stream": True},
        payload_size="small",
        streaming=True,
        concurrent_limit=10,
    )

    await benchmark.run_benchmark(
        "Medium Payload - Non-Streaming",
        num_requests=50,
        payload=medium_payload,
        payload_size="medium",
        streaming=False,
        concurrent_limit=10,
    )

    await benchmark.run_benchmark(
        "Medium Payload - Streaming",
        num_requests=50,
        payload={**medium_payload, "stream": True},
        payload_size="medium",
        streaming=True,
        concurrent_limit=10,
    )

    await benchmark.run_benchmark(
        "Large Payload - Non-Streaming",
        num_requests=20,
        payload=large_payload,
        payload_size="large",
        streaming=False,
        concurrent_limit=5,
    )

    await benchmark.run_benchmark(
        "Large Payload - Streaming",
        num_requests=20,
        payload={**large_payload, "stream": True},
        payload_size="large",
        streaming=True,
        concurrent_limit=5,
    )

    # High concurrency test
    await benchmark.run_benchmark(
        "High Concurrency - Small Payload",
        num_requests=200,
        payload=small_payload,
        payload_size="small",
        streaming=False,
        concurrent_limit=50,
    )

    # Generate report
    report = benchmark.generate_markdown_report()
    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print("=" * 70)
    print(report)

    # Save report
    report_path = "/home/anthony/projects/fakeai/benchmarks/throughput_results.md"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")

    return benchmark


if __name__ == "__main__":
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    api_key = sys.argv[2] if len(sys.argv) > 2 else "test"

    print(f"Running throughput benchmarks against: {base_url}")
    asyncio.run(run_all_benchmarks(base_url, api_key))
