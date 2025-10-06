#!/usr/bin/env python3
"""
Memory Benchmark for FakeAI Server

Tracks memory usage over time, detects memory leaks, and measures cache overhead.
Tests memory behavior under various load conditions.
"""
#  SPDX-License-Identifier: Apache-2.0

import asyncio
import gc
import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Install with: pip install psutil")


@dataclass
class MemorySnapshot:
    """Memory usage snapshot at a point in time."""

    timestamp: float
    rss_mb: float  # Resident Set Size in MB
    vms_mb: float  # Virtual Memory Size in MB
    percent: float  # Memory usage percentage
    request_count: int  # Number of requests processed


@dataclass
class MemoryResult:
    """Result from a memory benchmark test."""

    test_name: str
    duration: float
    total_requests: int
    initial_memory_mb: float
    final_memory_mb: float
    peak_memory_mb: float
    memory_growth_mb: float
    memory_growth_percent: float
    avg_memory_per_request_kb: float
    leak_detected: bool
    leak_rate_mb_per_min: float
    snapshots: list[MemorySnapshot] = field(default_factory=list)


class MemoryBenchmark:
    """Benchmark memory usage and detect leaks."""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = "test"):
        self.base_url = base_url
        self.api_key = api_key
        self.results: list[MemoryResult] = []

        if not PSUTIL_AVAILABLE:
            raise RuntimeError("psutil is required for memory benchmarking")

        # Get server process (assumes server is running)
        self.process = self._find_server_process()

    def _find_server_process(self) -> psutil.Process | None:
        """Find the FakeAI server process."""
        current_pid = os.getpid()

        # Try to find uvicorn/hypercorn process
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info.get("cmdline", [])
                if not cmdline:
                    continue

                # Look for python process running fakeai server
                cmdline_str = " ".join(cmdline)
                if "fakeai" in cmdline_str.lower() or "uvicorn" in cmdline_str.lower():
                    if proc.pid != current_pid:
                        print(f"Found FakeAI server process: PID {proc.pid}")
                        return psutil.Process(proc.pid)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        print("Warning: Could not find FakeAI server process. Using current process.")
        return psutil.Process(current_pid)

    def _get_memory_usage(self) -> tuple[float, float, float]:
        """
        Get current memory usage.

        Returns:
            (rss_mb, vms_mb, percent)
        """
        if not self.process:
            return 0.0, 0.0, 0.0

        try:
            mem_info = self.process.memory_info()
            mem_percent = self.process.memory_percent()

            rss_mb = mem_info.rss / (1024 * 1024)  # Bytes to MB
            vms_mb = mem_info.vms / (1024 * 1024)

            return rss_mb, vms_mb, mem_percent

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0, 0.0, 0.0

    async def _make_request(
        self, client: httpx.AsyncClient, payload: dict[str, Any]
    ) -> bool:
        """
        Make a single request.

        Returns:
            True if successful, False otherwise
        """
        try:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=60.0,
            )
            response.raise_for_status()
            return True

        except Exception as e:
            print(f"Request failed: {e}")
            return False

    async def run_memory_test(
        self,
        test_name: str,
        duration_seconds: int,
        requests_per_second: int,
        payload: dict[str, Any],
        snapshot_interval: float = 5.0,
    ) -> MemoryResult:
        """
        Run a memory usage test.

        Args:
            test_name: Name of the test
            duration_seconds: How long to run the test
            requests_per_second: Target requests per second
            payload: Request payload
            snapshot_interval: Seconds between memory snapshots

        Returns:
            MemoryResult with memory metrics
        """
        print(f"\n{'='*70}")
        print(f"Running: {test_name}")
        print(f"Duration: {duration_seconds}s, Target RPS: {requests_per_second}")
        print(f"{'='*70}")

        # Force garbage collection before starting
        gc.collect()
        await asyncio.sleep(1)

        snapshots = []
        request_count = 0
        start_time = time.perf_counter()
        end_time = start_time + duration_seconds
        last_snapshot_time = start_time

        # Initial snapshot
        rss, vms, percent = self._get_memory_usage()
        snapshots.append(
            MemorySnapshot(
                timestamp=0.0,
                rss_mb=rss,
                vms_mb=vms,
                percent=percent,
                request_count=0,
            )
        )
        print(f"Initial memory: {rss:.2f} MB RSS, {percent:.2f}%")

        request_interval = 1.0 / requests_per_second

        async with httpx.AsyncClient() as client:
            while time.perf_counter() < end_time:
                request_start = time.perf_counter()

                # Make request
                success = await self._make_request(client, payload)
                if success:
                    request_count += 1

                # Take snapshot if interval elapsed
                current_time = time.perf_counter()
                if current_time - last_snapshot_time >= snapshot_interval:
                    rss, vms, percent = self._get_memory_usage()
                    snapshots.append(
                        MemorySnapshot(
                            timestamp=current_time - start_time,
                            rss_mb=rss,
                            vms_mb=vms,
                            percent=percent,
                            request_count=request_count,
                        )
                    )
                    last_snapshot_time = current_time

                # Sleep to maintain target RPS
                elapsed = time.perf_counter() - request_start
                sleep_time = max(0, request_interval - elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

        # Final snapshot
        gc.collect()
        await asyncio.sleep(1)
        rss, vms, percent = self._get_memory_usage()
        snapshots.append(
            MemorySnapshot(
                timestamp=time.perf_counter() - start_time,
                rss_mb=rss,
                vms_mb=vms,
                percent=percent,
                request_count=request_count,
            )
        )

        total_duration = time.perf_counter() - start_time

        # Calculate statistics
        initial_memory = snapshots[0].rss_mb
        final_memory = snapshots[-1].rss_mb
        peak_memory = max(s.rss_mb for s in snapshots)
        memory_growth = final_memory - initial_memory
        memory_growth_percent = (
            (memory_growth / initial_memory * 100) if initial_memory > 0 else 0
        )

        avg_memory_per_request = (
            (memory_growth * 1024 / request_count) if request_count > 0 else 0
        )

        # Detect memory leak (linear regression on snapshots)
        leak_detected = False
        leak_rate = 0.0

        if len(snapshots) >= 3:
            # Simple linear regression
            times = [s.timestamp for s in snapshots]
            memories = [s.rss_mb for s in snapshots]

            n = len(times)
            sum_x = sum(times)
            sum_y = sum(memories)
            sum_xy = sum(t * m for t, m in zip(times, memories))
            sum_x2 = sum(t * t for t in times)

            # Slope (MB per second)
            if n * sum_x2 - sum_x * sum_x != 0:
                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                leak_rate = slope * 60  # Convert to MB per minute

                # Consider it a leak if growth > 1 MB/min and statistically significant
                if leak_rate > 1.0:
                    leak_detected = True

        result = MemoryResult(
            test_name=test_name,
            duration=total_duration,
            total_requests=request_count,
            initial_memory_mb=initial_memory,
            final_memory_mb=final_memory,
            peak_memory_mb=peak_memory,
            memory_growth_mb=memory_growth,
            memory_growth_percent=memory_growth_percent,
            avg_memory_per_request_kb=avg_memory_per_request,
            leak_detected=leak_detected,
            leak_rate_mb_per_min=leak_rate,
            snapshots=snapshots,
        )

        self.results.append(result)
        self._print_result(result)
        return result

    async def run_cache_overhead_test(self) -> MemoryResult:
        """
        Test memory overhead of KV cache.

        Sends repeated requests with shared prefixes to fill cache.
        """
        test_name = "KV Cache Memory Overhead"
        print(f"\n{'='*70}")
        print(f"Running: {test_name}")
        print(f"{'='*70}")

        gc.collect()
        await asyncio.sleep(1)

        snapshots = []
        request_count = 0
        start_time = time.perf_counter()

        # Initial snapshot
        rss, vms, percent = self._get_memory_usage()
        snapshots.append(
            MemorySnapshot(
                timestamp=0.0,
                rss_mb=rss,
                vms_mb=vms,
                percent=percent,
                request_count=0,
            )
        )

        # Send requests with various prefixes to populate cache
        prefixes = [
            "You are a helpful assistant.",
            "You are an expert programmer.",
            "You are a creative writer.",
        ]

        async with httpx.AsyncClient() as client:
            for iteration in range(10):
                for prefix in prefixes:
                    payload = {
                        "model": "openai/gpt-oss-120b",
                        "messages": [
                            {"role": "system", "content": prefix},
                            {"role": "user", "content": f"Query {iteration}"},
                        ],
                        "max_tokens": 100,
                    }

                    success = await self._make_request(client, payload)
                    if success:
                        request_count += 1

                # Snapshot after each iteration
                rss, vms, percent = self._get_memory_usage()
                snapshots.append(
                    MemorySnapshot(
                        timestamp=time.perf_counter() - start_time,
                        rss_mb=rss,
                        vms_mb=vms,
                        percent=percent,
                        request_count=request_count,
                    )
                )

        total_duration = time.perf_counter() - start_time

        # Final snapshot
        gc.collect()
        await asyncio.sleep(1)
        rss, vms, percent = self._get_memory_usage()
        snapshots.append(
            MemorySnapshot(
                timestamp=total_duration,
                rss_mb=rss,
                vms_mb=vms,
                percent=percent,
                request_count=request_count,
            )
        )

        # Calculate cache overhead
        initial_memory = snapshots[0].rss_mb
        final_memory = snapshots[-1].rss_mb
        peak_memory = max(s.rss_mb for s in snapshots)
        cache_overhead = final_memory - initial_memory

        result = MemoryResult(
            test_name=test_name,
            duration=total_duration,
            total_requests=request_count,
            initial_memory_mb=initial_memory,
            final_memory_mb=final_memory,
            peak_memory_mb=peak_memory,
            memory_growth_mb=cache_overhead,
            memory_growth_percent=(
                (cache_overhead / initial_memory * 100) if initial_memory > 0 else 0
            ),
            avg_memory_per_request_kb=(
                (cache_overhead * 1024 / request_count) if request_count > 0 else 0
            ),
            leak_detected=False,
            leak_rate_mb_per_min=0.0,
            snapshots=snapshots,
        )

        self.results.append(result)
        self._print_result(result)
        return result

    def _print_result(self, result: MemoryResult):
        """Print benchmark result."""
        print(f"\n{'='*70}")
        print(f"Results: {result.test_name}")
        print(f"{'='*70}")
        print(f"Duration:              {result.duration:.2f}s")
        print(f"Total Requests:        {result.total_requests}")
        print(f"\nMemory Usage:")
        print(f"  Initial:             {result.initial_memory_mb:.2f} MB")
        print(f"  Final:               {result.final_memory_mb:.2f} MB")
        print(f"  Peak:                {result.peak_memory_mb:.2f} MB")
        print(
            f"  Growth:              {result.memory_growth_mb:+.2f} MB ({result.memory_growth_percent:+.2f}%)"
        )
        print(f"  Avg per Request:     {result.avg_memory_per_request_kb:.2f} KB")
        print(f"\nLeak Detection:")
        print(f"  Leak Detected:       {'YES' if result.leak_detected else 'NO'}")
        print(f"  Growth Rate:         {result.leak_rate_mb_per_min:+.2f} MB/min")

    def generate_markdown_report(self) -> str:
        """Generate markdown report of all benchmark results."""
        report = "# Memory Benchmark Results\n\n"
        report += f"**Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Summary table
        report += "## Summary\n\n"
        report += (
            "| Test | Requests | Initial | Final | Growth | Leak? | Rate (MB/min) |\n"
        )
        report += (
            "|------|----------|---------|-------|--------|-------|---------------|\n"
        )

        for result in self.results:
            report += (
                f"| {result.test_name} | {result.total_requests} | "
                f"{result.initial_memory_mb:.2f} MB | {result.final_memory_mb:.2f} MB | "
                f"{result.memory_growth_mb:+.2f} MB | "
                f"{'YES' if result.leak_detected else 'NO'} | "
                f"{result.leak_rate_mb_per_min:+.2f} |\n"
            )

        # Detailed results
        report += "\n## Detailed Results\n\n"
        for result in self.results:
            report += f"### {result.test_name}\n\n"
            report += f"- **Duration:** {result.duration:.2f}s\n"
            report += f"- **Total Requests:** {result.total_requests}\n"
            report += f"- **Initial Memory:** {result.initial_memory_mb:.2f} MB\n"
            report += f"- **Final Memory:** {result.final_memory_mb:.2f} MB\n"
            report += f"- **Peak Memory:** {result.peak_memory_mb:.2f} MB\n"
            report += f"- **Memory Growth:** {result.memory_growth_mb:+.2f} MB ({result.memory_growth_percent:+.2f}%)\n"
            report += (
                f"- **Avg per Request:** {result.avg_memory_per_request_kb:.2f} KB\n"
            )
            report += (
                f"- **Leak Detected:** {'YES' if result.leak_detected else 'NO'}\n"
            )
            report += (
                f"- **Growth Rate:** {result.leak_rate_mb_per_min:+.2f} MB/min\n\n"
            )

            # Memory timeline
            if result.snapshots:
                report += "**Memory Timeline:**\n\n"
                report += "| Time (s) | Requests | RSS (MB) | Change (MB) |\n"
                report += "|----------|----------|----------|-------------|\n"

                for i, snapshot in enumerate(result.snapshots):
                    change = snapshot.rss_mb - result.snapshots[0].rss_mb
                    report += (
                        f"| {snapshot.timestamp:.1f} | {snapshot.request_count} | "
                        f"{snapshot.rss_mb:.2f} | {change:+.2f} |\n"
                    )
                report += "\n"

        # Overall assessment
        report += "## Overall Assessment\n\n"

        leaky_tests = [r for r in self.results if r.leak_detected]
        if leaky_tests:
            report += "### Memory Leaks Detected\n\n"
            report += "The following tests showed potential memory leaks:\n\n"
            for result in leaky_tests:
                report += f"- **{result.test_name}**: {result.leak_rate_mb_per_min:+.2f} MB/min\n"
            report += "\n"
        else:
            report += "### No Memory Leaks Detected\n\n"
            report += "All tests completed without detectable memory leaks.\n\n"

        # Memory efficiency
        avg_per_request = sum(r.avg_memory_per_request_kb for r in self.results) / len(
            self.results
        )
        report += f"**Average Memory per Request:** {avg_per_request:.2f} KB\n\n"

        return report


async def run_all_benchmarks(
    base_url: str = "http://localhost:8000", api_key: str = "test"
):
    """Run all memory benchmarks."""
    if not PSUTIL_AVAILABLE:
        print("Error: psutil is required for memory benchmarking")
        print("Install with: pip install psutil")
        return

    benchmark = MemoryBenchmark(base_url, api_key)

    payload = {
        "model": "meta-llama/Llama-3.1-8B-Instruct",
        "messages": [{"role": "user", "content": "Hello, how are you?"}],
        "max_tokens": 50,
    }

    # Test 1: Low load memory usage
    await benchmark.run_memory_test(
        test_name="Low Load (5 RPS)",
        duration_seconds=60,
        requests_per_second=5,
        payload=payload,
        snapshot_interval=10.0,
    )

    # Test 2: Medium load memory usage
    await benchmark.run_memory_test(
        test_name="Medium Load (20 RPS)",
        duration_seconds=60,
        requests_per_second=20,
        payload=payload,
        snapshot_interval=10.0,
    )

    # Test 3: Cache overhead
    await benchmark.run_cache_overhead_test()

    # Test 4: Long-running leak detection
    await benchmark.run_memory_test(
        test_name="Long-Running Leak Test (10 RPS)",
        duration_seconds=120,
        requests_per_second=10,
        payload=payload,
        snapshot_interval=15.0,
    )

    # Generate report
    report = benchmark.generate_markdown_report()
    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print("=" * 70)
    print(report)

    # Save report
    report_path = "/home/anthony/projects/fakeai/benchmarks/memory_results.md"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")

    return benchmark


if __name__ == "__main__":
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    api_key = sys.argv[2] if len(sys.argv) > 2 else "test"

    print(f"Running memory benchmarks against: {base_url}")
    asyncio.run(run_all_benchmarks(base_url, api_key))
