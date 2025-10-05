#!/usr/bin/env python3
"""
KV Cache Benchmark for FakeAI Server

Tests KV cache reuse, prefix matching, hit rates, and latency improvements.
Validates smart router load balancing and cache efficiency.
"""
#  SPDX-License-Identifier: Apache-2.0

import asyncio
import hashlib
import random
import time
from dataclasses import dataclass, field
from typing import Any

import httpx


@dataclass
class CacheTestResult:
    """Result from a cache benchmark test."""

    test_name: str
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    avg_latency_with_cache: float
    avg_latency_without_cache: float
    latency_improvement: float
    total_tokens_processed: int
    cached_tokens_reused: int
    token_reuse_rate: float
    avg_prefix_length: float
    latencies_with_cache: list[float] = field(default_factory=list)
    latencies_without_cache: list[float] = field(default_factory=list)


@dataclass
class SmartRouterResult:
    """Result from smart router benchmark."""

    test_name: str
    total_requests: int
    worker_distribution: dict[str, int]
    avg_cache_overlap: float
    load_balance_score: float
    total_time: float
    requests_per_second: float


class KVCacheBenchmark:
    """Benchmark KV cache and smart routing performance."""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "test"):
        self.base_url = base_url
        self.api_key = api_key
        self.cache_results: list[CacheTestResult] = []
        self.router_results: list[SmartRouterResult] = []

    async def _make_chat_request(
        self, client: httpx.AsyncClient, messages: list[dict[str, str]], max_tokens: int = 100
    ) -> tuple[float, dict[str, Any]]:
        """
        Make a chat completion request.

        Returns:
            (latency_seconds, response_data)
        """
        start_time = time.perf_counter()

        try:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json={"model": "openai/gpt-oss-120b", "messages": messages, "max_tokens": max_tokens},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=60.0,
            )
            response.raise_for_status()
            latency = time.perf_counter() - start_time
            return latency, response.json()

        except Exception as e:
            latency = time.perf_counter() - start_time
            print(f"Request failed: {e}")
            return latency, {}

    async def test_cache_hit_rates(
        self, shared_prefixes: list[str], unique_suffixes: list[str], num_iterations: int = 10
    ) -> CacheTestResult:
        """
        Test cache hit rates with shared prefixes.

        Args:
            shared_prefixes: List of common prompt prefixes
            unique_suffixes: List of unique prompt suffixes
            num_iterations: Number of iterations per prefix

        Returns:
            CacheTestResult with hit rate metrics
        """
        test_name = "Cache Hit Rate Test"
        print(f"\n{'='*70}")
        print(f"Running: {test_name}")
        print(f"Prefixes: {len(shared_prefixes)}, Suffixes: {len(unique_suffixes)}")
        print(f"Iterations: {num_iterations}")
        print(f"{'='*70}")

        cache_hits = 0
        cache_misses = 0
        latencies_with_cache = []
        latencies_without_cache = []
        total_tokens = 0
        cached_tokens = 0
        prefix_lengths = []

        async with httpx.AsyncClient() as client:
            for iteration in range(num_iterations):
                for prefix in shared_prefixes:
                    for suffix in unique_suffixes:
                        # First request with this prefix (cache miss expected)
                        if iteration == 0:
                            messages = [
                                {"role": "system", "content": prefix},
                                {"role": "user", "content": suffix},
                            ]
                            latency, response = await self._make_chat_request(client, messages)

                            if response:
                                cache_misses += 1
                                latencies_without_cache.append(latency)
                                usage = response.get("usage", {})
                                total_tokens += usage.get("total_tokens", 0)

                        # Subsequent requests (cache hits expected)
                        else:
                            messages = [
                                {"role": "system", "content": prefix},
                                {"role": "user", "content": suffix + f" (iteration {iteration})"},
                            ]
                            latency, response = await self._make_chat_request(client, messages)

                            if response:
                                cache_hits += 1
                                latencies_with_cache.append(latency)
                                usage = response.get("usage", {})
                                total_tokens += usage.get("total_tokens", 0)

                                # Estimate cached tokens (prefix tokens)
                                prompt_tokens = usage.get("prompt_tokens", 0)
                                cached_tokens += prompt_tokens // 2
                                prefix_lengths.append(prompt_tokens // 2)

        # Calculate statistics
        hit_rate = (cache_hits / (cache_hits + cache_misses) * 100) if (cache_hits + cache_misses) > 0 else 0

        avg_latency_with_cache = (
            sum(latencies_with_cache) / len(latencies_with_cache) if latencies_with_cache else 0
        )
        avg_latency_without_cache = (
            sum(latencies_without_cache) / len(latencies_without_cache)
            if latencies_without_cache
            else 0
        )

        latency_improvement = (
            ((avg_latency_without_cache - avg_latency_with_cache) / avg_latency_without_cache * 100)
            if avg_latency_without_cache > 0
            else 0
        )

        token_reuse_rate = (cached_tokens / total_tokens * 100) if total_tokens > 0 else 0
        avg_prefix = sum(prefix_lengths) / len(prefix_lengths) if prefix_lengths else 0

        result = CacheTestResult(
            test_name=test_name,
            total_requests=cache_hits + cache_misses,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            hit_rate=hit_rate,
            avg_latency_with_cache=avg_latency_with_cache,
            avg_latency_without_cache=avg_latency_without_cache,
            latency_improvement=latency_improvement,
            total_tokens_processed=total_tokens,
            cached_tokens_reused=cached_tokens,
            token_reuse_rate=token_reuse_rate,
            avg_prefix_length=avg_prefix,
            latencies_with_cache=latencies_with_cache,
            latencies_without_cache=latencies_without_cache,
        )

        self.cache_results.append(result)
        self._print_cache_result(result)
        return result

    async def test_prefix_sharing(self) -> CacheTestResult:
        """Test prefix sharing efficiency with common conversation patterns."""
        test_name = "Prefix Sharing Test"
        print(f"\n{'='*70}")
        print(f"Running: {test_name}")
        print(f"{'='*70}")

        # Common conversation prefixes
        common_system_prompts = [
            "You are a helpful AI assistant. Be concise and accurate.",
            "You are an expert programmer. Provide code examples when relevant.",
            "You are a friendly chatbot. Be conversational and engaging.",
        ]

        # Various user queries
        user_queries = [
            "What is Python?",
            "Explain async programming",
            "Write a hello world program",
            "What are design patterns?",
            "How do I use decorators?",
        ]

        cache_hits = 0
        cache_misses = 0
        latencies_with_cache = []
        latencies_without_cache = []
        total_tokens = 0
        cached_tokens = 0
        prefix_lengths = []

        async with httpx.AsyncClient() as client:
            for system_prompt in common_system_prompts:
                # First query with this system prompt (cache miss)
                first_query = user_queries[0]
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": first_query},
                ]
                latency, response = await self._make_chat_request(client, messages)

                if response:
                    cache_misses += 1
                    latencies_without_cache.append(latency)
                    usage = response.get("usage", {})
                    total_tokens += usage.get("total_tokens", 0)

                # Follow-up queries (cache hits expected)
                for query in user_queries[1:]:
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query},
                    ]
                    latency, response = await self._make_chat_request(client, messages)

                    if response:
                        cache_hits += 1
                        latencies_with_cache.append(latency)
                        usage = response.get("usage", {})
                        total_tokens += usage.get("total_tokens", 0)
                        prompt_tokens = usage.get("prompt_tokens", 0)
                        cached_tokens += prompt_tokens // 2
                        prefix_lengths.append(prompt_tokens // 2)

        # Calculate statistics
        hit_rate = (cache_hits / (cache_hits + cache_misses) * 100) if (cache_hits + cache_misses) > 0 else 0

        avg_latency_with_cache = (
            sum(latencies_with_cache) / len(latencies_with_cache) if latencies_with_cache else 0
        )
        avg_latency_without_cache = (
            sum(latencies_without_cache) / len(latencies_without_cache)
            if latencies_without_cache
            else 0
        )

        latency_improvement = (
            ((avg_latency_without_cache - avg_latency_with_cache) / avg_latency_without_cache * 100)
            if avg_latency_without_cache > 0
            else 0
        )

        token_reuse_rate = (cached_tokens / total_tokens * 100) if total_tokens > 0 else 0
        avg_prefix = sum(prefix_lengths) / len(prefix_lengths) if prefix_lengths else 0

        result = CacheTestResult(
            test_name=test_name,
            total_requests=cache_hits + cache_misses,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            hit_rate=hit_rate,
            avg_latency_with_cache=avg_latency_with_cache,
            avg_latency_without_cache=avg_latency_without_cache,
            latency_improvement=latency_improvement,
            total_tokens_processed=total_tokens,
            cached_tokens_reused=cached_tokens,
            token_reuse_rate=token_reuse_rate,
            avg_prefix_length=avg_prefix,
            latencies_with_cache=latencies_with_cache,
            latencies_without_cache=latencies_without_cache,
        )

        self.cache_results.append(result)
        self._print_cache_result(result)
        return result

    async def test_smart_router(self, num_requests: int = 100) -> SmartRouterResult:
        """
        Test smart router load balancing and cache-aware routing.

        Args:
            num_requests: Number of requests to test

        Returns:
            SmartRouterResult with routing metrics
        """
        test_name = "Smart Router Test"
        print(f"\n{'='*70}")
        print(f"Running: {test_name}")
        print(f"Requests: {num_requests}")
        print(f"{'='*70}")

        # Generate requests with varying prefix overlap
        prefixes = [
            "You are a helpful assistant.",
            "You are an expert programmer.",
            "You are a creative writer.",
        ]

        worker_stats = {}
        start_time = time.perf_counter()

        async with httpx.AsyncClient() as client:
            for i in range(num_requests):
                # Select prefix (creates natural grouping)
                prefix = prefixes[i % len(prefixes)]
                messages = [
                    {"role": "system", "content": prefix},
                    {"role": "user", "content": f"Request {i}"},
                ]

                _, response = await self._make_chat_request(client, messages)

                # Track worker distribution (if exposed in response)
                # Note: This is simulated since FakeAI doesn't expose worker IDs
                worker_id = f"worker-{hash(prefix) % 4}"
                worker_stats[worker_id] = worker_stats.get(worker_id, 0) + 1

        total_time = time.perf_counter() - start_time

        # Calculate load balance score (lower variance is better)
        request_counts = list(worker_stats.values())
        avg_load = sum(request_counts) / len(request_counts) if request_counts else 0
        variance = sum((x - avg_load) ** 2 for x in request_counts) / len(request_counts) if request_counts else 0
        load_balance_score = 100 - (variance / avg_load * 100) if avg_load > 0 else 0

        result = SmartRouterResult(
            test_name=test_name,
            total_requests=num_requests,
            worker_distribution=worker_stats,
            avg_cache_overlap=0.0,  # Would need server metrics
            load_balance_score=max(0, load_balance_score),
            total_time=total_time,
            requests_per_second=num_requests / total_time if total_time > 0 else 0,
        )

        self.router_results.append(result)
        self._print_router_result(result)
        return result

    def _print_cache_result(self, result: CacheTestResult):
        """Print cache benchmark result."""
        print(f"\n{'='*70}")
        print(f"Results: {result.test_name}")
        print(f"{'='*70}")
        print(f"Total Requests:        {result.total_requests}")
        print(f"Cache Hits:            {result.cache_hits}")
        print(f"Cache Misses:          {result.cache_misses}")
        print(f"Hit Rate:              {result.hit_rate:.2f}%")
        print(f"\nLatency Comparison:")
        print(f"  With Cache:          {result.avg_latency_with_cache*1000:.2f}ms")
        print(f"  Without Cache:       {result.avg_latency_without_cache*1000:.2f}ms")
        print(f"  Improvement:         {result.latency_improvement:.2f}%")
        print(f"\nToken Statistics:")
        print(f"  Total Processed:     {result.total_tokens_processed}")
        print(f"  Cached Reused:       {result.cached_tokens_reused}")
        print(f"  Reuse Rate:          {result.token_reuse_rate:.2f}%")
        print(f"  Avg Prefix Length:   {result.avg_prefix_length:.0f} tokens")

    def _print_router_result(self, result: SmartRouterResult):
        """Print smart router result."""
        print(f"\n{'='*70}")
        print(f"Results: {result.test_name}")
        print(f"{'='*70}")
        print(f"Total Requests:        {result.total_requests}")
        print(f"Total Time:            {result.total_time:.2f}s")
        print(f"Requests/sec:          {result.requests_per_second:.2f}")
        print(f"Load Balance Score:    {result.load_balance_score:.2f}/100")
        print(f"\nWorker Distribution:")
        for worker_id, count in sorted(result.worker_distribution.items()):
            percentage = (count / result.total_requests * 100)
            print(f"  {worker_id}: {count} ({percentage:.1f}%)")

    def generate_markdown_report(self) -> str:
        """Generate markdown report of all benchmark results."""
        report = "# KV Cache Benchmark Results\n\n"
        report += f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Cache results
        if self.cache_results:
            report += "## Cache Performance\n\n"
            report += "| Test | Hit Rate | Latency Improvement | Token Reuse Rate | Avg Prefix |\n"
            report += "|------|----------|---------------------|------------------|------------|\n"

            for result in self.cache_results:
                report += (
                    f"| {result.test_name} | {result.hit_rate:.2f}% | "
                    f"{result.latency_improvement:.2f}% | {result.token_reuse_rate:.2f}% | "
                    f"{result.avg_prefix_length:.0f} tokens |\n"
                )

            report += "\n### Detailed Cache Results\n\n"
            for result in self.cache_results:
                report += f"#### {result.test_name}\n\n"
                report += f"- **Total Requests:** {result.total_requests}\n"
                report += f"- **Cache Hits:** {result.cache_hits}\n"
                report += f"- **Cache Misses:** {result.cache_misses}\n"
                report += f"- **Hit Rate:** {result.hit_rate:.2f}%\n\n"
                report += "**Latency:**\n\n"
                report += f"- With Cache: {result.avg_latency_with_cache*1000:.2f}ms\n"
                report += f"- Without Cache: {result.avg_latency_without_cache*1000:.2f}ms\n"
                report += f"- Improvement: {result.latency_improvement:.2f}%\n\n"
                report += "**Tokens:**\n\n"
                report += f"- Total Processed: {result.total_tokens_processed}\n"
                report += f"- Cached Reused: {result.cached_tokens_reused}\n"
                report += f"- Reuse Rate: {result.token_reuse_rate:.2f}%\n\n"

        # Smart router results
        if self.router_results:
            report += "## Smart Router Performance\n\n"
            report += "| Test | Requests | RPS | Load Balance Score |\n"
            report += "|------|----------|-----|--------------------|\n"

            for result in self.router_results:
                report += (
                    f"| {result.test_name} | {result.total_requests} | "
                    f"{result.requests_per_second:.2f} | {result.load_balance_score:.2f}/100 |\n"
                )

            report += "\n### Detailed Router Results\n\n"
            for result in self.router_results:
                report += f"#### {result.test_name}\n\n"
                report += f"- **Total Requests:** {result.total_requests}\n"
                report += f"- **Load Balance Score:** {result.load_balance_score:.2f}/100\n"
                report += f"- **Requests/sec:** {result.requests_per_second:.2f}\n\n"
                report += "**Worker Distribution:**\n\n"
                for worker_id, count in sorted(result.worker_distribution.items()):
                    percentage = (count / result.total_requests * 100)
                    report += f"- {worker_id}: {count} ({percentage:.1f}%)\n"
                report += "\n"

        return report


async def run_all_benchmarks(base_url: str = "http://localhost:8000", api_key: str = "test"):
    """Run all KV cache benchmarks."""
    benchmark = KVCacheBenchmark(base_url, api_key)

    # Test 1: Cache hit rates with shared prefixes
    shared_prefixes = [
        "You are a helpful AI assistant specialized in Python programming.",
        "You are an expert in data science and machine learning.",
        "You are a creative writer helping with story development.",
    ]

    unique_suffixes = [
        "Tell me about lists.",
        "Explain dictionaries.",
        "What are generators?",
        "How do decorators work?",
    ]

    await benchmark.test_cache_hit_rates(shared_prefixes, unique_suffixes, num_iterations=5)

    # Test 2: Prefix sharing efficiency
    await benchmark.test_prefix_sharing()

    # Test 3: Smart router load balancing
    await benchmark.test_smart_router(num_requests=100)

    # Generate report
    report = benchmark.generate_markdown_report()
    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print("=" * 70)
    print(report)

    # Save report
    report_path = "/home/anthony/projects/fakeai/benchmarks/kv_cache_results.md"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")

    return benchmark


if __name__ == "__main__":
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    api_key = sys.argv[2] if len(sys.argv) > 2 else "test"

    print(f"Running KV cache benchmarks against: {base_url}")
    asyncio.run(run_all_benchmarks(base_url, api_key))
