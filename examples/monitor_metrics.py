#!/usr/bin/env python3
"""
FakeAI Metrics Monitoring Example

This script demonstrates how to monitor FakeAI server metrics in real-time.
"""
#  SPDX-License-Identifier: Apache-2.0

import asyncio
import aiohttp
import time
import sys
from datetime import datetime


def print_header():
    """Print header for metrics display."""
    print("\n" + "="*80)
    print("FakeAI Server Metrics Monitor")
    print("="*80 + "\n")


def format_latency(seconds):
    """Format latency in milliseconds."""
    return f"{seconds * 1000:.2f}ms"


def format_rate(rate):
    """Format rate with 2 decimal places."""
    return f"{rate:.2f}/s"


def get_status_emoji(status):
    """Get emoji for health status."""
    return {
        "healthy": "✅",
        "degraded": "⚠️",
        "unhealthy": "❌"
    }.get(status, "❓")


async def monitor_basic(base_url="http://localhost:8000", interval=5):
    """
    Monitor basic metrics with simple output.

    Args:
        base_url: FakeAI server URL
        interval: Refresh interval in seconds
    """
    print_header()
    print("Basic Monitoring Mode (Ctrl+C to stop)")
    print(f"Refresh interval: {interval}s\n")

    try:
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    # Fetch health data
                    async with session.get(f"{base_url}/health/detailed", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        health = await response.json()

                    # Clear line
                    print("\r" + " " * 80 + "\r", end="")

                    # Print status
                    status = health['status']
                    emoji = get_status_emoji(status)
                    summary = health['metrics_summary']

                    print(f"{emoji} Status: {status.upper()} | "
                          f"RPS: {format_rate(summary['total_requests_per_second'])} | "
                          f"Latency: {format_latency(summary['average_latency_seconds'])} | "
                          f"Errors: {summary['error_rate_percentage']:.2f}% | "
                          f"Streams: {summary['active_streams']}",
                          end="", flush=True)

                    await asyncio.sleep(interval)

                except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as e:
                    print(f"\r❌ Connection error: {e}", end="", flush=True)
                    await asyncio.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n✓ Monitoring stopped")


async def monitor_detailed(base_url="http://localhost:8000", interval=5):
    """
    Monitor detailed metrics with full output.

    Args:
        base_url: FakeAI server URL
        interval: Refresh interval in seconds
    """
    print_header()
    print("Detailed Monitoring Mode (Ctrl+C to stop)")
    print(f"Refresh interval: {interval}s\n")

    try:
        iteration = 0
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    # Clear screen every 10 iterations
                    if iteration % 10 == 0:
                        print("\033[2J\033[H", end="")  # Clear screen
                        print_header()

                    # Fetch metrics
                    async with session.get(f"{base_url}/health/detailed", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        health = await response.json()

                    # Print timestamp
                    print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print("-" * 80)

                    # Print status
                    status = health['status']
                    emoji = get_status_emoji(status)
                    print(f"\n{emoji} Overall Status: {status.upper()}")

                    # Print summary
                    summary = health['metrics_summary']
                    print("\nMetrics Summary:")
                    print(f"  Total Requests/sec:  {format_rate(summary['total_requests_per_second'])}")
                    print(f"  Total Errors/sec:    {format_rate(summary['total_errors_per_second'])}")
                    print(f"  Error Rate:          {summary['error_rate_percentage']:.2f}%")
                    print(f"  Average Latency:     {format_latency(summary['average_latency_seconds'])}")
                    print(f"  Active Streams:      {summary['active_streams']}")

                    # Print endpoint details
                    endpoints = health.get('endpoints', {})
                    if endpoints:
                        print("\nEndpoint Details:")
                        for endpoint, metrics in endpoints.items():
                            print(f"\n  {endpoint}")
                            print(f"    Requests/sec:  {format_rate(metrics['requests_per_second'])}")
                            print(f"    P50 Latency:   {metrics['latency_p50_ms']:.2f}ms")
                            print(f"    P99 Latency:   {metrics['latency_p99_ms']:.2f}ms")

                    print("\n" + "-" * 80)
                    print(f"Next update in {interval}s... (Ctrl+C to stop)")

                    iteration += 1
                    await asyncio.sleep(interval)

                except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as e:
                    print(f"\n❌ Connection error: {e}")
                    print(f"Retrying in {interval}s...")
                    await asyncio.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n✓ Monitoring stopped")


async def monitor_streaming(base_url="http://localhost:8000", interval=5):
    """
    Monitor streaming-specific metrics.

    Args:
        base_url: FakeAI server URL
        interval: Refresh interval in seconds
    """
    print_header()
    print("Streaming Metrics Mode (Ctrl+C to stop)")
    print(f"Refresh interval: {interval}s\n")

    try:
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    # Fetch full metrics
                    async with session.get(f"{base_url}/metrics", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        data = await response.json()

                    streaming = data.get('streaming_stats', {})

                    if not streaming:
                        print("\r⚠️  No streaming data available", end="", flush=True)
                        await asyncio.sleep(interval)
                        continue

                    # Print streaming stats
                    print("\r" + " " * 80 + "\r", end="")

                    active = streaming.get('active_streams', 0)
                    completed = streaming.get('completed_streams', 0)
                    failed = streaming.get('failed_streams', 0)

                    print(f"📊 Active: {active} | Completed: {completed} | Failed: {failed}", end="")

                    # Print TTFT if available
                    ttft = streaming.get('ttft', {})
                    if ttft:
                        print(f" | TTFT p50: {format_latency(ttft['p50'])} p99: {format_latency(ttft['p99'])}", end="")

                    # Print tokens/sec if available
                    tps = streaming.get('tokens_per_second', {})
                    if tps:
                        print(f" | TPS: {tps['avg']:.1f}/s", end="")

                    print("", flush=True)

                    await asyncio.sleep(interval)

                except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as e:
                    print(f"\r❌ Connection error: {e}", end="", flush=True)
                    await asyncio.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n✓ Monitoring stopped")


async def export_metrics(base_url="http://localhost:8000", format="json", output=None):
    """
    Export metrics to file.

    Args:
        base_url: FakeAI server URL
        format: Export format (json, csv, prometheus)
        output: Output file path (None for stdout)
    """
    print(f"Exporting metrics in {format} format...")

    try:
        # Map format to endpoint
        endpoints = {
            "json": "/metrics",
            "csv": "/metrics/csv",
            "prometheus": "/metrics/prometheus",
        }

        endpoint = endpoints.get(format)
        if not endpoint:
            print(f"❌ Unknown format: {format}")
            print(f"Available formats: {', '.join(endpoints.keys())}")
            return

        # Fetch metrics
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}{endpoint}", timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                text = await response.text()

        # Write to file or stdout
        if output:
            with open(output, 'w') as f:
                f.write(text)
            print(f"✓ Metrics exported to {output}")
        else:
            print(text)

    except (aiohttp.ClientConnectorError, asyncio.TimeoutError, aiohttp.ClientResponseError) as e:
        print(f"❌ Error exporting metrics: {e}")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Monitor FakeAI server metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic monitoring (one-line display)
  python monitor_metrics.py

  # Detailed monitoring (full display)
  python monitor_metrics.py --detailed

  # Streaming metrics only
  python monitor_metrics.py --streaming

  # Export metrics to file
  python monitor_metrics.py --export json --output metrics.json
  python monitor_metrics.py --export csv --output metrics.csv
  python monitor_metrics.py --export prometheus --output metrics.prom

  # Custom server URL and interval
  python monitor_metrics.py --url http://remote-server:8000 --interval 10
        """
    )

    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="FakeAI server URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Refresh interval in seconds (default: 5)"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed metrics (default: basic)"
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Show only streaming metrics"
    )
    parser.add_argument(
        "--export",
        choices=["json", "csv", "prometheus"],
        help="Export metrics to file"
    )
    parser.add_argument(
        "--output",
        help="Output file path (default: stdout)"
    )

    args = parser.parse_args()

    # Handle export mode
    if args.export:
        await export_metrics(args.url, args.export, args.output)
        return

    # Handle monitoring modes
    if args.streaming:
        await monitor_streaming(args.url, args.interval)
    elif args.detailed:
        await monitor_detailed(args.url, args.interval)
    else:
        await monitor_basic(args.url, args.interval)


if __name__ == "__main__":
    asyncio.run(main())
