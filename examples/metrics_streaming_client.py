#!/usr/bin/env python3
"""
Example client for FakeAI metrics streaming.

Demonstrates how to connect to the metrics WebSocket endpoint and
subscribe to real-time metrics updates.
"""
import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("websockets library not installed. Install with: pip install websockets")
    sys.exit(1)


async def stream_metrics():
    """Connect to metrics stream and display updates."""
    uri = "ws://localhost:8000/metrics/stream"

    print(f"Connecting to {uri}...")

    async with websockets.connect(uri) as websocket:
        print("Connected! Waiting for historical data...")

        # Receive historical data
        message = await websocket.recv()
        data = json.loads(message)
        print(f"\nReceived {data['type']}: timestamp={data['timestamp']}")
        if data["type"] == "historical_data":
            print_metrics_summary(data["data"])

        # Subscribe to specific metrics
        subscription = {
            "type": "subscribe",
            "filters": {
                "endpoint": "/v1/chat/completions",
                "metric_type": "all",
                "interval": 2.0,  # Update every 2 seconds
            },
        }
        await websocket.send(json.dumps(subscription))
        print(f"\nSubscribed with filters: {subscription['filters']}")

        # Wait for subscription confirmation
        message = await websocket.recv()
        data = json.loads(message)
        if data["type"] == "subscribed":
            print(f"Subscription confirmed: {data['filters']}")

        print("\nStreaming real-time metrics (press Ctrl+C to stop)...\n")

        # Receive and display metrics updates
        update_count = 0
        while True:
            message = await websocket.recv()
            data = json.loads(message)

            if data["type"] == "metrics_update":
                update_count += 1
                print(f"--- Update #{update_count} at {data['timestamp']:.2f} ---")
                print_metrics_summary(data["data"])

                # Display deltas if available
                if data.get("deltas"):
                    print("\nDeltas:")
                    for key, value in data["deltas"].items():
                        print(f"  {key}: {value}")

                print()  # Blank line between updates

            elif data["type"] == "error":
                print(f"Error: {data['message']}")


def print_metrics_summary(metrics):
    """Print a summary of metrics data."""

    # Throughput
    if "throughput" in metrics:
        throughput = metrics["throughput"]
        if "total_requests_per_sec" in throughput:
            print(f"  Requests/sec: {throughput['total_requests_per_sec']:.2f}")
        if "total_tokens_per_sec" in throughput:
            print(f"  Tokens/sec: {throughput['total_tokens_per_sec']:.2f}")

    # Latency
    if "latency" in metrics:
        for endpoint, stats in metrics["latency"].items():
            print(f"  Latency [{endpoint}]:")
            print(f"    avg: {stats['avg']:.2f}ms")
            print(f"    p99: {stats['p99']:.2f}ms")

    # Cache
    if "cache" in metrics and metrics["cache"]:
        cache = metrics["cache"]
        if "hit_rate" in cache:
            print(f"  Cache hit rate: {cache['hit_rate']:.1f}%")
        if "token_reuse_rate" in cache:
            print(f"  Token reuse rate: {cache['token_reuse_rate']:.1f}%")

    # Streaming
    if "streaming" in metrics and metrics["streaming"]:
        streaming = metrics["streaming"]
        if "active_streams" in streaming:
            print(f"  Active streams: {streaming['active_streams']}")
        if "ttft" in streaming:
            ttft = streaming["ttft"]
            print(f"  TTFT: avg={ttft['avg']:.2f}ms, p99={ttft['p99']:.2f}ms")

    # Errors
    if "error" in metrics and metrics["error"].get("total_errors_per_sec", 0) > 0:
        print(f"  Errors/sec: {metrics['error']['total_errors_per_sec']:.2f}")


async def main():
    """Main entry point."""
    try:
        await stream_metrics()
    except KeyboardInterrupt:
        print("\nDisconnected.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
