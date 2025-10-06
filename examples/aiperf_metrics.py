#!/usr/bin/env python3
"""
FakeAI AIPerf Metrics Exporter

This script gets metrics from the FakeAI server and formats them for AIPerf.
It can be used to export metrics in a format compatible with AIPerf benchmarking tool.
"""

import argparse
import asyncio
import json
import sys
import time
from typing import Any, Dict

import aiohttp


async def get_metrics(url="http://localhost:8000") -> Dict[str, Any]:
    """Get metrics from the FakeAI server."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}/metrics") as response:
                return await response.json()
    except aiohttp.ClientConnectorError as e:
        print(f"Error getting metrics: {e}")
        return {}
    except asyncio.TimeoutError as e:
        print(f"Error getting metrics: {e}")
        return {}


def format_aiperf_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Format metrics for AIPerf."""
    result = {
        "timestamp": int(time.time()),
        "requests_per_second": 0.0,
        "responses_per_second": 0.0,
        "tokens_per_second": 0.0,
        "time_to_first_token": 0.0,
        "time_to_second_token": 0.0,
        "inter_token_latency": 0.0,
        "output_token_throughput_per_user": 0.0,
        "average_response_time": 0.0,
    }

    # Extract requests per second
    if "requests" in metrics:
        for endpoint, stats in metrics["requests"].items():
            if endpoint == "/v1/chat/completions" and "rate" in stats:
                result["requests_per_second"] += stats["rate"]
            if endpoint == "/v1/completions" and "rate" in stats:
                result["requests_per_second"] += stats["rate"]

    # Extract responses per second
    if "responses" in metrics:
        for endpoint, stats in metrics["responses"].items():
            if endpoint == "/v1/chat/completions" and "rate" in stats:
                result["responses_per_second"] += stats["rate"]
                if "avg" in stats:
                    result["average_response_time"] = stats["avg"]
            if endpoint == "/v1/completions" and "rate" in stats:
                result["responses_per_second"] += stats["rate"]
                if "avg" in stats and result["average_response_time"] == 0.0:
                    result["average_response_time"] = stats["avg"]

    # Extract tokens per second
    if "tokens" in metrics:
        for endpoint, stats in metrics["tokens"].items():
            if endpoint == "/v1/chat/completions" and "rate" in stats:
                result["tokens_per_second"] += stats["rate"]
            if endpoint == "/v1/completions" and "rate" in stats:
                result["tokens_per_second"] += stats["rate"]

    # AIPerf specific metrics - use approximate values
    if "tokens_per_second" in result and result["tokens_per_second"] > 0:
        # Rough estimates for these values
        result["time_to_first_token"] = 0.2  # 200ms
        result["time_to_second_token"] = 0.3  # 300ms
        result["inter_token_latency"] = 0.05  # 50ms

        # Calculate output token throughput per user
        if result["responses_per_second"] > 0:
            result["output_token_throughput_per_user"] = (
                result["tokens_per_second"] / result["responses_per_second"]
            )

    return result


async def main():
    parser = argparse.ArgumentParser(description="AIPerf Metrics Exporter for FakeAI")
    parser.add_argument(
        "--url", default="http://localhost:8000", help="FakeAI server URL"
    )
    parser.add_argument("--output", default="-", help="Output file (- for stdout)")
    parser.add_argument(
        "--format", default="json", choices=["json", "csv"], help="Output format"
    )
    args = parser.parse_args()

    # Get metrics
    metrics = await get_metrics(args.url)
    if not metrics:
        print("Error: No metrics available", file=sys.stderr)
        sys.exit(1)

    # Format metrics for AIPerf
    aiperf_metrics = format_aiperf_metrics(metrics)

    # Output metrics
    if args.format == "json":
        output_data = json.dumps(aiperf_metrics, indent=2)
    else:  # csv
        headers = aiperf_metrics.keys()
        values = [str(aiperf_metrics[key]) for key in headers]
        output_data = ",".join(headers) + "\n" + ",".join(values)

    if args.output == "-":
        print(output_data)
    else:
        with open(args.output, "w") as f:
            f.write(output_data)
        print(f"Metrics written to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
