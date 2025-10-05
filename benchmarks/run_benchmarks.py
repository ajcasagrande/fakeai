#!/usr/bin/env python3
"""
Main Benchmark Runner for FakeAI Server

Runs all benchmarks and generates comprehensive reports.
"""
#  SPDX-License-Identifier: Apache-2.0

import argparse
import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.benchmark_utils import BenchmarkReporter, check_server


async def run_all_benchmarks(
    base_url: str,
    api_key: str,
    quick: bool = False,
    skip_memory: bool = False,
):
    """
    Run all benchmarks and generate reports.

    Args:
        base_url: Server base URL
        api_key: API key for authentication
        quick: Run quick tests only
        skip_memory: Skip memory benchmarks (requires psutil)
    """
    print("=" * 70)
    print("FakeAI Performance Benchmark Suite")
    print("=" * 70)

    # Check server
    server_info = await check_server(base_url, api_key)

    if not server_info.reachable:
        print("\nERROR: Server is not reachable!")
        print(f"Please ensure FakeAI server is running at {base_url}")
        return False

    print(f"\nServer: {base_url}")
    print(f"Models available: {len(server_info.models)}")
    print(f"Timestamp: {server_info.timestamp}")

    reporter = BenchmarkReporter()

    # Import benchmark modules
    try:
        from benchmarks import benchmark_throughput
        from benchmarks import benchmark_kv_cache
        from benchmarks import benchmark_concurrent
        from benchmarks import benchmark_memory
    except ImportError as e:
        print(f"\nERROR: Failed to import benchmark modules: {e}")
        return False

    results = {}

    # 1. Throughput Benchmarks
    print("\n" + "=" * 70)
    print("1. THROUGHPUT BENCHMARKS")
    print("=" * 70)

    try:
        if quick:
            print("\nRunning quick throughput tests...")
            bench = benchmark_throughput.ThroughputBenchmark(base_url, api_key)

            small_payload = {
                "model": "meta-llama/Llama-3.1-8B-Instruct",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 50,
            }

            await bench.run_benchmark(
                "Quick Throughput Test",
                num_requests=20,
                payload=small_payload,
                payload_size="small",
                streaming=False,
                concurrent_limit=5,
            )

            results["throughput"] = bench
        else:
            print("\nRunning full throughput benchmarks...")
            results["throughput"] = await benchmark_throughput.run_all_benchmarks(
                base_url, api_key
            )

        print("\n✓ Throughput benchmarks completed")

    except Exception as e:
        print(f"\n✗ Throughput benchmarks failed: {e}")

    # 2. KV Cache Benchmarks
    print("\n" + "=" * 70)
    print("2. KV CACHE BENCHMARKS")
    print("=" * 70)

    try:
        if quick:
            print("\nRunning quick KV cache tests...")
            bench = benchmark_kv_cache.KVCacheBenchmark(base_url, api_key)

            await bench.test_prefix_sharing()

            results["kv_cache"] = bench
        else:
            print("\nRunning full KV cache benchmarks...")
            results["kv_cache"] = await benchmark_kv_cache.run_all_benchmarks(
                base_url, api_key
            )

        print("\n✓ KV cache benchmarks completed")

    except Exception as e:
        print(f"\n✗ KV cache benchmarks failed: {e}")

    # 3. Concurrent Connection Benchmarks
    print("\n" + "=" * 70)
    print("3. CONCURRENT CONNECTION BENCHMARKS")
    print("=" * 70)

    try:
        if quick:
            print("\nRunning quick concurrent tests...")
            bench = benchmark_concurrent.ConcurrentBenchmark(base_url, api_key)

            payload = {
                "model": "meta-llama/Llama-3.1-8B-Instruct",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 50,
            }

            await bench.run_concurrent_test(
                test_name="Quick Concurrency Test",
                num_requests=50,
                concurrent_connections=10,
                payload=payload,
            )

            results["concurrent"] = bench
        else:
            print("\nRunning full concurrent benchmarks...")
            results["concurrent"] = await benchmark_concurrent.run_all_benchmarks(
                base_url, api_key
            )

        print("\n✓ Concurrent benchmarks completed")

    except Exception as e:
        print(f"\n✗ Concurrent benchmarks failed: {e}")

    # 4. Memory Benchmarks
    if not skip_memory:
        print("\n" + "=" * 70)
        print("4. MEMORY BENCHMARKS")
        print("=" * 70)

        try:
            # Check if psutil is available
            try:
                import psutil
            except ImportError:
                print("\nSkipping memory benchmarks: psutil not installed")
                print("Install with: pip install psutil")
                skip_memory = True

            if not skip_memory:
                if quick:
                    print("\nRunning quick memory tests...")
                    bench = benchmark_memory.MemoryBenchmark(base_url, api_key)

                    payload = {
                        "model": "meta-llama/Llama-3.1-8B-Instruct",
                        "messages": [{"role": "user", "content": "Hello"}],
                        "max_tokens": 50,
                    }

                    await bench.run_memory_test(
                        test_name="Quick Memory Test",
                        duration_seconds=30,
                        requests_per_second=5,
                        payload=payload,
                        snapshot_interval=10.0,
                    )

                    results["memory"] = bench
                else:
                    print("\nRunning full memory benchmarks...")
                    results["memory"] = await benchmark_memory.run_all_benchmarks(
                        base_url, api_key
                    )

                print("\n✓ Memory benchmarks completed")

        except Exception as e:
            print(f"\n✗ Memory benchmarks failed: {e}")

    # Generate summary report
    print("\n" + "=" * 70)
    print("GENERATING SUMMARY REPORT")
    print("=" * 70)

    summary = generate_summary_report(results, server_info, quick)
    summary_path = Path("/home/anthony/projects/fakeai/benchmarks/BENCHMARK_SUMMARY.md")

    with open(summary_path, "w") as f:
        f.write(summary)

    print(f"\n✓ Summary report saved to: {summary_path}")

    # Save individual results as JSON
    for name, benchmark in results.items():
        if hasattr(benchmark, "results"):
            reporter.save_results(benchmark.results, f"{name}_results.json")

    print("\n" + "=" * 70)
    print("BENCHMARK SUITE COMPLETED")
    print("=" * 70)
    print(f"\nAll reports saved to: /home/anthony/projects/fakeai/benchmarks/")

    return True


def generate_summary_report(results: dict, server_info, quick: bool) -> str:
    """Generate summary report of all benchmarks."""
    report = "# FakeAI Performance Benchmark Summary\n\n"
    report += f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"**Server:** {server_info.base_url}\n"
    report += f"**Test Mode:** {'Quick' if quick else 'Full'}\n\n"

    report += "## Server Information\n\n"
    report += f"- **Base URL:** {server_info.base_url}\n"
    report += f"- **Reachable:** {'Yes' if server_info.reachable else 'No'}\n"
    report += f"- **Models:** {len(server_info.models)}\n"
    report += f"- **Timestamp:** {server_info.timestamp}\n\n"

    report += "## Benchmark Results\n\n"

    # Throughput results
    if "throughput" in results:
        bench = results["throughput"]
        if hasattr(bench, "results") and bench.results:
            report += "### Throughput\n\n"

            best_rps = max(bench.results, key=lambda r: r.requests_per_second)
            report += f"- **Best RPS:** {best_rps.requests_per_second:.2f} ({best_rps.test_name})\n"

            avg_latency = sum(r.avg_latency for r in bench.results) / len(bench.results)
            report += f"- **Average Latency:** {avg_latency*1000:.2f}ms\n"

            total_requests = sum(r.successful_requests for r in bench.results)
            report += f"- **Total Requests:** {total_requests}\n\n"

    # KV Cache results
    if "kv_cache" in results:
        bench = results["kv_cache"]
        if hasattr(bench, "cache_results") and bench.cache_results:
            report += "### KV Cache\n\n"

            avg_hit_rate = sum(r.hit_rate for r in bench.cache_results) / len(
                bench.cache_results
            )
            report += f"- **Average Hit Rate:** {avg_hit_rate:.2f}%\n"

            avg_improvement = sum(r.latency_improvement for r in bench.cache_results) / len(
                bench.cache_results
            )
            report += f"- **Average Latency Improvement:** {avg_improvement:.2f}%\n"

            avg_reuse = sum(r.token_reuse_rate for r in bench.cache_results) / len(
                bench.cache_results
            )
            report += f"- **Average Token Reuse Rate:** {avg_reuse:.2f}%\n\n"

    # Concurrent results
    if "concurrent" in results:
        bench = results["concurrent"]
        if hasattr(bench, "results") and bench.results:
            report += "### Concurrent Connections\n\n"

            successful_results = [r for r in bench.results if r.failed_requests == 0]
            if successful_results:
                best = max(successful_results, key=lambda r: r.requests_per_second)
                report += f"- **Best RPS (no errors):** {best.requests_per_second:.2f} @ {best.concurrent_connections} concurrent\n"
                report += f"- **P99 Latency:** {best.p99_latency*1000:.2f}ms\n"

            max_concurrent = max(r.concurrent_connections for r in bench.results)
            report += f"- **Max Concurrent Tested:** {max_concurrent}\n\n"

    # Memory results
    if "memory" in results:
        bench = results["memory"]
        if hasattr(bench, "results") and bench.results:
            report += "### Memory Usage\n\n"

            leaks = [r for r in bench.results if r.leak_detected]
            report += f"- **Memory Leaks Detected:** {'Yes' if leaks else 'No'}\n"

            avg_growth = sum(r.memory_growth_mb for r in bench.results) / len(bench.results)
            report += f"- **Average Memory Growth:** {avg_growth:+.2f} MB\n"

            avg_per_request = sum(r.avg_memory_per_request_kb for r in bench.results) / len(
                bench.results
            )
            report += f"- **Average Memory per Request:** {avg_per_request:.2f} KB\n\n"

    report += "## Detailed Reports\n\n"
    report += "See individual report files for detailed results:\n\n"
    report += "- `throughput_results.md` - Throughput benchmark details\n"
    report += "- `kv_cache_results.md` - KV cache benchmark details\n"
    report += "- `concurrent_results.md` - Concurrent connections benchmark details\n"
    report += "- `memory_results.md` - Memory usage benchmark details\n\n"

    report += "## Recommendations\n\n"

    # Generate recommendations based on results
    recommendations = []

    if "throughput" in results:
        bench = results["throughput"]
        if hasattr(bench, "results") and bench.results:
            avg_rps = sum(r.requests_per_second for r in bench.results) / len(bench.results)
            if avg_rps < 10:
                recommendations.append(
                    "⚠️  Throughput is low. Consider optimizing response generation or reducing delays."
                )

    if "kv_cache" in results:
        bench = results["kv_cache"]
        if hasattr(bench, "cache_results") and bench.cache_results:
            avg_hit_rate = sum(r.hit_rate for r in bench.cache_results) / len(
                bench.cache_results
            )
            if avg_hit_rate < 50:
                recommendations.append(
                    "⚠️  Cache hit rate is low. Review prefix matching strategy."
                )

    if "memory" in results:
        bench = results["memory"]
        if hasattr(bench, "results") and bench.results:
            leaks = [r for r in bench.results if r.leak_detected]
            if leaks:
                recommendations.append(
                    "❌ Memory leaks detected! Review memory management in server code."
                )

    if recommendations:
        for rec in recommendations:
            report += f"- {rec}\n"
    else:
        report += "✅ All benchmarks performed well. No issues detected.\n"

    report += "\n---\n\n"
    report += f"*Generated by FakeAI Benchmark Suite on {time.strftime('%Y-%m-%d at %H:%M:%S')}*\n"

    return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run FakeAI performance benchmarks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all benchmarks
  python run_benchmarks.py

  # Run quick tests only
  python run_benchmarks.py --quick

  # Test different server
  python run_benchmarks.py --url http://localhost:9000

  # Skip memory tests
  python run_benchmarks.py --skip-memory

  # Custom API key
  python run_benchmarks.py --api-key my-secret-key
        """,
    )

    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="FakeAI server URL (default: http://localhost:8000)",
    )

    parser.add_argument(
        "--api-key",
        default="test",
        help="API key for authentication (default: test)",
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick tests only (faster but less comprehensive)",
    )

    parser.add_argument(
        "--skip-memory",
        action="store_true",
        help="Skip memory benchmarks (useful if psutil not available)",
    )

    args = parser.parse_args()

    # Run benchmarks
    success = asyncio.run(
        run_all_benchmarks(
            base_url=args.url,
            api_key=args.api_key,
            quick=args.quick,
            skip_memory=args.skip_memory,
        )
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
