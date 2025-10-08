#!/usr/bin/env python3
"""
Comprehensive Dashboard Metrics Test Script

This script validates that all metrics endpoints are working correctly by:
1. Sending 100 streaming requests to the backend
2. Checking /dynamo/metrics/json response
3. Validating all expected fields are populated
4. Checking /kv-cache/metrics response
5. Validating worker stats and cache metrics
6. Printing a beautiful report showing all metrics
7. Returning exit code 0 if all pass, 1 if any fail

Usage:
    python test_dashboard_metrics.py [--url http://localhost:8000] [--requests 100]
"""

import argparse
import asyncio
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

import aiohttp
from openai import AsyncOpenAI


# ANSI color codes for pretty output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print a section header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


async def send_streaming_request(
    client: AsyncOpenAI,
    request_num: int,
    progress_callback=None
) -> Dict[str, Any]:
    """
    Send a single streaming request and track metrics.

    Args:
        client: OpenAI async client
        request_num: Request number for tracking
        progress_callback: Optional callback for progress updates

    Returns:
        Dict with request metrics
    """
    start_time = time.time()

    try:
        # Use different prompts for variety
        prompts = [
            "Write a haiku about programming",
            "Explain quantum computing in 3 sentences",
            "List 5 Python best practices",
            "Describe what an API is",
            "What are the benefits of async programming?",
        ]
        prompt = prompts[request_num % len(prompts)]

        stream = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            max_tokens=50,  # Keep responses short for faster testing
        )

        token_count = 0
        first_token_time = None

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                if first_token_time is None:
                    first_token_time = time.time()
                token_count += 1

        end_time = time.time()

        if progress_callback:
            await progress_callback(request_num + 1)

        return {
            "success": True,
            "duration": end_time - start_time,
            "ttft": first_token_time - start_time if first_token_time else None,
            "tokens": token_count,
        }

    except Exception as e:
        if progress_callback:
            await progress_callback(request_num + 1)
        return {
            "success": False,
            "error": str(e),
        }


async def send_requests(base_url: str, num_requests: int) -> List[Dict[str, Any]]:
    """
    Send multiple streaming requests concurrently.

    Args:
        base_url: Base URL of the FakeAI server
        num_requests: Number of requests to send

    Returns:
        List of request results
    """
    print_header("SENDING STREAMING REQUESTS")
    print_info(f"Sending {num_requests} streaming requests to {base_url}")
    print_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    client = AsyncOpenAI(
        api_key="sk-fakeai-test-metrics",
        base_url=f"{base_url}/v1",
    )

    # Progress tracking
    completed = [0]

    async def update_progress(count: int):
        completed[0] = count
        progress = (count / num_requests) * 100
        bar_length = 50
        filled = int(bar_length * count / num_requests)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\rProgress: [{bar}] {progress:6.2f}% ({count}/{num_requests})", end='', flush=True)

    # Send requests with controlled concurrency (batches of 10)
    batch_size = 10
    results = []

    for i in range(0, num_requests, batch_size):
        batch_end = min(i + batch_size, num_requests)
        batch_tasks = [
            send_streaming_request(client, j, update_progress)
            for j in range(i, batch_end)
        ]
        batch_results = await asyncio.gather(*batch_tasks)
        results.extend(batch_results)

    print()  # New line after progress bar

    # Summary
    successful = sum(1 for r in results if r.get("success"))
    failed = num_requests - successful

    print()
    if successful == num_requests:
        print_success(f"All {num_requests} requests completed successfully!")
    else:
        print_warning(f"{successful} requests succeeded, {failed} failed")

    return results


async def check_dynamo_metrics(base_url: str, expected_requests: int) -> Dict[str, bool]:
    """
    Check /dynamo/metrics/json endpoint and validate fields.

    Args:
        base_url: Base URL of the FakeAI server
        expected_requests: Expected number of requests in metrics

    Returns:
        Dict of validation results
    """
    print_header("VALIDATING DYNAMO METRICS")

    validations = {}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/dynamo/metrics/json") as response:
                if response.status != 200:
                    print_error(f"Failed to fetch metrics: HTTP {response.status}")
                    return {"endpoint_accessible": False}

                data = await response.json()

        print_success(f"Successfully fetched /dynamo/metrics/json")
        validations["endpoint_accessible"] = True

        # Validate summary section
        print_info("\nValidating summary section...")
        if "summary" in data:
            summary = data["summary"]

            # Check total_requests
            total_requests = summary.get("total_requests", 0)
            if total_requests >= expected_requests:
                print_success(f"  total_requests: {total_requests} (>= {expected_requests})")
                validations["total_requests"] = True
            else:
                print_error(f"  total_requests: {total_requests} (expected >= {expected_requests})")
                validations["total_requests"] = False

            # Check other summary fields
            for field in ["successful_requests", "failed_requests", "active_requests"]:
                value = summary.get(field)
                if value is not None:
                    print_success(f"  {field}: {value}")
                    validations[f"summary_{field}"] = True
                else:
                    print_error(f"  {field}: MISSING")
                    validations[f"summary_{field}"] = False
        else:
            print_error("  summary section MISSING")
            validations["summary_section"] = False

        # Validate latency section
        print_info("\nValidating latency section...")
        if "latency" in data:
            latency = data["latency"]

            # Check TTFT
            if "ttft" in latency:
                ttft = latency["ttft"]
                avg = ttft.get("avg", 0)
                if avg > 0:
                    print_success(f"  ttft.avg: {avg:.2f}ms")
                    validations["ttft_avg"] = True
                else:
                    print_error(f"  ttft.avg: {avg} (expected > 0)")
                    validations["ttft_avg"] = False
            else:
                print_error("  ttft section MISSING")
                validations["ttft"] = False

            # Check other latency fields
            for field in ["itl", "total", "prefill", "decode"]:
                if field in latency:
                    field_data = latency[field]
                    avg = field_data.get("avg", 0)
                    print_success(f"  {field}.avg: {avg:.2f}ms")
                    validations[f"latency_{field}"] = True
                else:
                    print_warning(f"  {field} section missing (may be expected)")
        else:
            print_error("  latency section MISSING")
            validations["latency_section"] = False

        # Validate throughput section
        print_info("\nValidating throughput section...")
        if "throughput" in data:
            throughput = data["throughput"]
            rps = throughput.get("requests_per_second", 0)
            if rps > 0:
                print_success(f"  requests_per_second: {rps:.2f}")
                validations["requests_per_second"] = True
            else:
                print_error(f"  requests_per_second: {rps} (expected > 0)")
                validations["requests_per_second"] = False

            tps = throughput.get("tokens_per_second", 0)
            if tps > 0:
                print_success(f"  tokens_per_second: {tps:.2f}")
                validations["tokens_per_second"] = True
            else:
                print_warning(f"  tokens_per_second: {tps} (may be 0 initially)")
        else:
            print_error("  throughput section MISSING")
            validations["throughput_section"] = False

        # Validate latency_breakdown array
        print_info("\nValidating latency_breakdown array...")
        if "latency_breakdown" in data:
            breakdown = data["latency_breakdown"]
            if isinstance(breakdown, list) and len(breakdown) > 0:
                print_success(f"  latency_breakdown: {len(breakdown)} items")
                validations["latency_breakdown"] = True
            else:
                print_warning(f"  latency_breakdown: empty array")
                validations["latency_breakdown"] = False
        else:
            print_warning("  latency_breakdown MISSING")
            validations["latency_breakdown"] = False

        # Validate request_lifecycles array
        print_info("\nValidating request_lifecycles array...")
        if "request_lifecycles" in data:
            lifecycles = data["request_lifecycles"]
            if isinstance(lifecycles, list) and len(lifecycles) > 0:
                print_success(f"  request_lifecycles: {len(lifecycles)} items")
                validations["request_lifecycles"] = True
            else:
                print_warning(f"  request_lifecycles: empty array")
                validations["request_lifecycles"] = False
        else:
            print_warning("  request_lifecycles MISSING")
            validations["request_lifecycles"] = False

        # Validate per_model section
        print_info("\nValidating per_model section...")
        if "per_model" in data:
            per_model = data["per_model"]
            if isinstance(per_model, dict) and len(per_model) > 0:
                print_success(f"  per_model: {len(per_model)} models")
                for model, stats in per_model.items():
                    print_info(f"    {model}: {stats.get('requests', 0)} requests")
                validations["per_model"] = True
            else:
                print_error(f"  per_model: empty dict")
                validations["per_model"] = False
        else:
            print_error("  per_model section MISSING")
            validations["per_model"] = False

        # Validate worker_stats section
        print_info("\nValidating worker_stats section...")
        if "worker_stats" in data:
            worker_stats = data["worker_stats"]
            total_workers = worker_stats.get("total_workers", 0)
            if total_workers == 4:
                print_success(f"  total_workers: {total_workers}")
                validations["worker_stats_count"] = True
            else:
                print_warning(f"  total_workers: {total_workers} (expected 4)")
                validations["worker_stats_count"] = False

            # Check workers array
            if "workers" in worker_stats:
                workers = worker_stats["workers"]
                if isinstance(workers, list):
                    print_success(f"  workers array: {len(workers)} workers")
                    for worker in workers[:3]:  # Show first 3
                        print_info(f"    {worker.get('worker_id')}: {worker.get('total_requests', 0)} requests")
                    validations["workers_array"] = True
                else:
                    print_error("  workers: not an array")
                    validations["workers_array"] = False
        else:
            print_warning("  worker_stats section MISSING (may be expected)")
            validations["worker_stats"] = False

    except Exception as e:
        print_error(f"Exception while checking Dynamo metrics: {e}")
        validations["exception"] = False

    return validations


async def check_kv_cache_metrics(base_url: str) -> Dict[str, bool]:
    """
    Check /kv-cache/metrics endpoint and validate fields.

    Args:
        base_url: Base URL of the FakeAI server

    Returns:
        Dict of validation results
    """
    print_header("VALIDATING KV-CACHE METRICS")

    validations = {}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/kv-cache/metrics") as response:
                if response.status != 200:
                    print_error(f"Failed to fetch metrics: HTTP {response.status}")
                    return {"endpoint_accessible": False}

                data = await response.json()

        print_success(f"Successfully fetched /kv-cache/metrics")
        validations["endpoint_accessible"] = True

        # Validate cache_performance section
        print_info("\nValidating cache_performance section...")
        if "cache_performance" in data:
            cache_perf = data["cache_performance"]

            # Check cache_hit_rate
            hit_rate = cache_perf.get("cache_hit_rate", 0)
            if hit_rate >= 0:
                print_success(f"  cache_hit_rate: {hit_rate:.2f}%")
                validations["cache_hit_rate"] = True
            else:
                print_error(f"  cache_hit_rate: MISSING")
                validations["cache_hit_rate"] = False

            # Check total_cache_hits
            total_hits = cache_perf.get("total_cache_hits", 0)
            if total_hits >= 0:
                print_success(f"  total_cache_hits: {total_hits}")
                validations["total_cache_hits"] = True
            else:
                print_error(f"  total_cache_hits: MISSING")
                validations["total_cache_hits"] = False

            # Check other fields
            for field in ["total_requests", "cache_misses", "tokens_saved"]:
                value = cache_perf.get(field)
                if value is not None:
                    print_success(f"  {field}: {value}")
                else:
                    print_warning(f"  {field}: missing")
        else:
            print_error("  cache_performance section MISSING")
            validations["cache_performance"] = False

        # Validate smart_router section
        print_info("\nValidating smart_router section...")
        if "smart_router" in data:
            router = data["smart_router"]

            # Check workers
            if "workers" in router or "worker_stats" in router:
                workers = router.get("workers") or router.get("worker_stats", {}).get("workers", [])
                if isinstance(workers, list):
                    print_success(f"  workers: {len(workers)} workers found")

                    if len(workers) == 4:
                        print_success(f"  All 4 workers present")
                        validations["all_workers_present"] = True
                    else:
                        print_warning(f"  Expected 4 workers, found {len(workers)}")
                        validations["all_workers_present"] = False

                    # Show worker details
                    for worker in workers[:4]:
                        worker_id = worker.get("worker_id") or worker.get("id")
                        requests = worker.get("total_requests") or worker.get("requests", 0)
                        print_info(f"    {worker_id}: {requests} requests")
                else:
                    print_error("  workers: not an array")
                    validations["workers_array"] = False
            else:
                print_warning("  workers data MISSING")
                validations["workers"] = False

            # Check routing stats
            if "total_routed" in router or "total_requests" in router:
                total = router.get("total_routed") or router.get("total_requests", 0)
                print_success(f"  total_routed: {total}")
                validations["total_routed"] = True
            else:
                print_warning("  total_routed: missing")
        else:
            print_error("  smart_router section MISSING")
            validations["smart_router"] = False

    except Exception as e:
        print_error(f"Exception while checking KV cache metrics: {e}")
        validations["exception"] = False

    return validations


def print_final_report(
    request_results: List[Dict[str, Any]],
    dynamo_validations: Dict[str, bool],
    kv_cache_validations: Dict[str, bool]
):
    """Print final test report."""
    print_header("FINAL TEST REPORT")

    # Request summary
    successful = sum(1 for r in request_results if r.get("success"))
    total = len(request_results)
    success_rate = (successful / total * 100) if total > 0 else 0

    print(f"\n{Colors.BOLD}Request Summary:{Colors.ENDC}")
    print(f"  Total Requests:     {total}")
    print(f"  Successful:         {successful}")
    print(f"  Failed:             {total - successful}")
    print(f"  Success Rate:       {success_rate:.2f}%")

    # Calculate average metrics from successful requests
    successful_requests = [r for r in request_results if r.get("success")]
    if successful_requests:
        avg_duration = sum(r.get("duration", 0) for r in successful_requests) / len(successful_requests)
        avg_ttft = sum(r.get("ttft", 0) for r in successful_requests if r.get("ttft")) / len([r for r in successful_requests if r.get("ttft")])
        avg_tokens = sum(r.get("tokens", 0) for r in successful_requests) / len(successful_requests)

        print(f"\n{Colors.BOLD}Average Metrics:{Colors.ENDC}")
        print(f"  Duration:           {avg_duration:.3f}s")
        print(f"  TTFT:               {avg_ttft*1000:.2f}ms")
        print(f"  Tokens/Request:     {avg_tokens:.1f}")

    # Dynamo validations
    dynamo_passed = sum(1 for v in dynamo_validations.values() if v)
    dynamo_total = len(dynamo_validations)
    dynamo_rate = (dynamo_passed / dynamo_total * 100) if dynamo_total > 0 else 0

    print(f"\n{Colors.BOLD}Dynamo Metrics Validation:{Colors.ENDC}")
    print(f"  Passed:             {dynamo_passed}/{dynamo_total}")
    print(f"  Pass Rate:          {dynamo_rate:.2f}%")

    # KV Cache validations
    kv_passed = sum(1 for v in kv_cache_validations.values() if v)
    kv_total = len(kv_cache_validations)
    kv_rate = (kv_passed / kv_total * 100) if kv_total > 0 else 0

    print(f"\n{Colors.BOLD}KV-Cache Metrics Validation:{Colors.ENDC}")
    print(f"  Passed:             {kv_passed}/{kv_total}")
    print(f"  Pass Rate:          {kv_rate:.2f}%")

    # Overall result
    print(f"\n{Colors.BOLD}Overall Result:{Colors.ENDC}")

    # Determine if test passed
    # We expect at least 90% success rate and most critical metrics present
    critical_dynamo = ["endpoint_accessible", "total_requests", "ttft_avg", "requests_per_second"]
    critical_kv = ["endpoint_accessible", "cache_hit_rate", "total_cache_hits"]

    critical_dynamo_passed = all(dynamo_validations.get(k, False) for k in critical_dynamo)
    critical_kv_passed = all(kv_cache_validations.get(k, False) for k in critical_kv)

    all_passed = (
        success_rate >= 90 and
        critical_dynamo_passed and
        critical_kv_passed
    )

    if all_passed:
        print_success("ALL CRITICAL TESTS PASSED!")
        print()
        return 0
    else:
        print_error("SOME TESTS FAILED")
        if success_rate < 90:
            print_error(f"  Request success rate too low: {success_rate:.2f}% < 90%")
        if not critical_dynamo_passed:
            print_error("  Critical Dynamo metrics missing:")
            for k in critical_dynamo:
                if not dynamo_validations.get(k, False):
                    print_error(f"    - {k}")
        if not critical_kv_passed:
            print_error("  Critical KV-Cache metrics missing:")
            for k in critical_kv:
                if not kv_cache_validations.get(k, False):
                    print_error(f"    - {k}")
        print()
        return 1


async def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Dashboard Metrics Test Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of FakeAI server (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=100,
        help="Number of streaming requests to send (default: 100)",
    )

    args = parser.parse_args()

    print_header("COMPREHENSIVE DASHBOARD METRICS TEST")
    print_info(f"Target URL: {args.url}")
    print_info(f"Test Requests: {args.requests}")
    print_info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Step 1: Send streaming requests
        request_results = await send_requests(args.url, args.requests)

        # Wait a moment for metrics to update
        print_info("\nWaiting 2 seconds for metrics to update...")
        await asyncio.sleep(2)

        # Step 2: Check Dynamo metrics
        dynamo_validations = await check_dynamo_metrics(args.url, args.requests)

        # Step 3: Check KV-cache metrics
        kv_cache_validations = await check_kv_cache_metrics(args.url)

        # Step 4: Print final report
        exit_code = print_final_report(
            request_results,
            dynamo_validations,
            kv_cache_validations
        )

        return exit_code

    except KeyboardInterrupt:
        print_warning("\n\nTest interrupted by user")
        return 1
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
