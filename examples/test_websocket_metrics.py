#!/usr/bin/env python3
"""
Quick test script to verify metrics streaming WebSocket endpoint.

Requires the FakeAI server to be running on port 8000.
"""
import asyncio
import json

try:
    import websockets
except ImportError:
    print("ERROR: websockets library not installed")
    print("Install with: pip install websockets")
    exit(1)


async def test_metrics_streaming():
    """Test the metrics streaming WebSocket endpoint."""
    uri = "ws://localhost:8000/metrics/stream"

    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri, timeout=5) as websocket:
            print("✓ Connected successfully")

            # Receive historical data
            message = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(message)

            assert (
                data["type"] == "historical_data"
            ), f"Expected historical_data, got {data['type']}"
            assert "timestamp" in data
            assert "data" in data
            print("✓ Received historical data")

            # Subscribe to metrics
            subscription = {
                "type": "subscribe",
                "filters": {"endpoint": "/v1/chat/completions", "interval": 1.0},
            }
            await websocket.send(json.dumps(subscription))
            print("✓ Sent subscription")

            # Wait for subscription confirmation
            message = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(message)

            assert (
                data["type"] == "subscribed"
            ), f"Expected subscribed, got {data['type']}"
            print("✓ Subscription confirmed")

            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            print("✓ Sent ping")

            # Wait for pong
            message = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(message)

            assert data["type"] == "pong", f"Expected pong, got {data['type']}"
            print("✓ Received pong")

            # Unsubscribe
            await websocket.send(json.dumps({"type": "unsubscribe"}))
            print("✓ Sent unsubscribe")

            # Wait for unsubscribe confirmation
            message = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(message)

            assert (
                data["type"] == "unsubscribed"
            ), f"Expected unsubscribed, got {data['type']}"
            print("✓ Unsubscribe confirmed")

            print("\n✅ All tests passed!")
            return True

    except asyncio.TimeoutError:
        print("\n❌ Timeout - server may not be responding")
        return False
    except ConnectionRefusedError:
        print("\n❌ Connection refused - is the server running?")
        print("Start server with: python -m fakeai server")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_metrics_streaming())
    exit(0 if success else 1)
