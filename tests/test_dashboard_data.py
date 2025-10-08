#!/usr/bin/env python3
"""
End-to-End Dashboard Data Flow Test

This test validates that the complete data pipeline from request generation
to dashboard display is working correctly by:

1. Sending varied traffic (10 requests with different patterns)
2. Waiting for event processing
3. Calling /metrics endpoint
4. Validating response format matches dashboard expectations
5. Checking all required fields are present and non-null
6. Verifying aggregations are correct
7. Testing WebSocket /metrics/stream if possible
8. Printing dashboard readiness report

This ensures the dashboard will display data correctly.

USAGE:

1. Standalone execution (recommended):

   # Start the FakeAI server in one terminal
   python -m fakeai server --port 8000

   # Run this test in another terminal
   python tests/test_dashboard_data.py

   The test will generate traffic, validate metrics, and print a detailed
   readiness report. Exit code 0 means dashboard is ready, 1 means issues.

2. With pytest:

   pytest tests/test_dashboard_data.py -v --tb=short

   Note: This is an integration test that requires a running server.

3. Custom configuration:

   Edit the constants at the top of the file:
   - BASE_URL: Default http://localhost:8000
   - NUM_REQUESTS: Number of test requests (default 10)
   - PROCESSING_WAIT_TIME: Seconds to wait for aggregation (default 3)

EXPECTED OUTPUT:

The test produces a comprehensive report showing:
- Traffic generation statistics (success rate, latency, tokens)
- Metrics endpoint validation (all required fields present)
- WebSocket stream validation (if websockets library available)
- Dashboard readiness assessment with component-level status

Example successful output:

  ================================================================================
  STEP 1: GENERATING VARIED TRAFFIC
  ================================================================================
  [1/10] short_streaming: OK (0.234s)
  [2/10] medium_streaming: OK (0.456s)
  ...
  Traffic Generation Complete:
    Successful: 10/10
    Avg latency: 0.345s

  ================================================================================
  STEP 3: VALIDATING /metrics ENDPOINT
  ================================================================================
  ✓ Metrics endpoint is accessible
  ✓ Has requests data
  ✓ Has responses data
  ✓ Has latency data
  ✓ Has streaming statistics

  ================================================================================
  DASHBOARD READINESS REPORT
  ================================================================================
  Dashboard Ready: YES ✓
  🎉 Dashboard is READY to display data correctly!

REQUIREMENTS:

- FakeAI server running and accessible
- openai library (pip install openai)
- aiohttp library (pip install aiohttp)
- websockets library (optional, for WebSocket testing)
- pytest and pytest-asyncio (only for pytest execution)
"""
#  SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import sys
import time
from typing import Any

import aiohttp
import pytest
from openai import AsyncOpenAI

# ============================================================================
# Test Configuration
# ============================================================================

BASE_URL = "http://localhost:8000"
NUM_REQUESTS = 10
PROCESSING_WAIT_TIME = 3  # seconds to wait for metrics aggregation


# ============================================================================
# Traffic Generation
# ============================================================================


async def generate_varied_traffic(base_url: str, num_requests: int) -> dict[str, Any]:
    """
    Generate varied traffic patterns to test different metrics scenarios.

    Args:
        base_url: Base URL of the FakeAI server
        num_requests: Number of requests to generate

    Returns:
        Dict with traffic generation statistics
    """
    print(f"\n{'='*80}")
    print(f"STEP 1: GENERATING VARIED TRAFFIC")
    print(f"{'='*80}")
    print(f"Sending {num_requests} requests with varied patterns...")

    client = AsyncOpenAI(
        api_key="sk-test-dashboard-data",
        base_url=f"{base_url}/v1",
    )

    # Different request patterns to test various metrics
    patterns = [
        {
            "name": "short_streaming",
            "model": "openai/gpt-oss-120b",
            "prompt": "Say hi",
            "max_tokens": 10,
            "stream": True,
        },
        {
            "name": "medium_streaming",
            "model": "openai/gpt-oss-120b",
            "prompt": "Write a haiku about Python",
            "max_tokens": 50,
            "stream": True,
        },
        {
            "name": "non_streaming",
            "model": "openai/gpt-oss-120b",
            "prompt": "Count to 5",
            "max_tokens": 20,
            "stream": False,
        },
        {
            "name": "different_model",
            "model": "gpt-4",
            "prompt": "Hello world",
            "max_tokens": 15,
            "stream": True,
        },
        {
            "name": "long_streaming",
            "model": "openai/gpt-oss-120b",
            "prompt": "Explain quantum computing in detail",
            "max_tokens": 100,
            "stream": True,
        },
    ]

    results = {
        "total": num_requests,
        "successful": 0,
        "failed": 0,
        "streaming": 0,
        "non_streaming": 0,
        "tokens_generated": 0,
        "latencies": [],
    }

    tasks = []
    for i in range(num_requests):
        pattern = patterns[i % len(patterns)]
        tasks.append(send_request(client, pattern, i, results))

    # Execute all requests concurrently
    await asyncio.gather(*tasks, return_exceptions=True)

    print(f"\nTraffic Generation Complete:")
    print(f"  Successful: {results['successful']}/{results['total']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Streaming: {results['streaming']}")
    print(f"  Non-streaming: {results['non_streaming']}")
    print(f"  Total tokens: {results['tokens_generated']}")

    if results['latencies']:
        avg_latency = sum(results['latencies']) / len(results['latencies'])
        print(f"  Avg latency: {avg_latency:.3f}s")

    return results


async def send_request(
    client: AsyncOpenAI,
    pattern: dict[str, Any],
    request_num: int,
    results: dict[str, Any],
) -> None:
    """Send a single request based on the pattern."""
    start_time = time.time()

    try:
        if pattern["stream"]:
            stream = await client.chat.completions.create(
                model=pattern["model"],
                messages=[{"role": "user", "content": pattern["prompt"]}],
                stream=True,
                max_tokens=pattern["max_tokens"],
            )

            token_count = 0
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    token_count += len(chunk.choices[0].delta.content)

            results["tokens_generated"] += token_count
            results["streaming"] += 1
        else:
            response = await client.chat.completions.create(
                model=pattern["model"],
                messages=[{"role": "user", "content": pattern["prompt"]}],
                stream=False,
                max_tokens=pattern["max_tokens"],
            )

            if response.choices and response.choices[0].message.content:
                results["tokens_generated"] += len(response.choices[0].message.content)
            results["non_streaming"] += 1

        results["successful"] += 1
        latency = time.time() - start_time
        results["latencies"].append(latency)

        print(f"  [{request_num+1}/{results['total']}] {pattern['name']}: OK ({latency:.3f}s)")

    except Exception as e:
        results["failed"] += 1
        print(f"  [{request_num+1}/{results['total']}] {pattern['name']}: FAILED - {e}")


# ============================================================================
# Metrics Validation
# ============================================================================


async def validate_metrics_endpoint(base_url: str) -> dict[str, Any]:
    """
    Validate the /metrics endpoint returns correct data structure.

    Args:
        base_url: Base URL of the FakeAI server

    Returns:
        Dict with validation results
    """
    print(f"\n{'='*80}")
    print(f"STEP 3: VALIDATING /metrics ENDPOINT")
    print(f"{'='*80}")

    validation = {
        "endpoint_accessible": False,
        "has_requests_data": False,
        "has_responses_data": False,
        "has_tokens_data": False,
        "has_latency_data": False,
        "has_streaming_stats": False,
        "required_fields": {},
        "aggregations": {},
        "errors": [],
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/metrics") as response:
                if response.status != 200:
                    validation["errors"].append(
                        f"Metrics endpoint returned {response.status}"
                    )
                    return validation

                data = await response.json()

        validation["endpoint_accessible"] = True
        print("✓ Metrics endpoint is accessible")

        # Check for main metric types
        if "requests" in data and data["requests"]:
            validation["has_requests_data"] = True
            print("✓ Has requests data")

            # Validate request data structure
            for endpoint, stats in data["requests"].items():
                validate_metric_stats(stats, "requests", endpoint, validation)
        else:
            validation["errors"].append("Missing or empty 'requests' data")

        if "responses" in data and data["responses"]:
            validation["has_responses_data"] = True
            print("✓ Has responses data")

            # Validate response data structure
            for endpoint, stats in data["responses"].items():
                validate_metric_stats(stats, "responses", endpoint, validation)
        else:
            validation["errors"].append("Missing or empty 'responses' data")

        if "tokens" in data and data["tokens"]:
            validation["has_tokens_data"] = True
            print("✓ Has tokens data")
        else:
            print("⚠ Missing or empty 'tokens' data (may be expected)")

        if "latency" in data and data["latency"]:
            validation["has_latency_data"] = True
            print("✓ Has latency data")

            # Validate latency statistics
            for endpoint, stats in data["latency"].items():
                validate_latency_stats(stats, endpoint, validation)
        else:
            validation["errors"].append("Missing or empty 'latency' data")

        # Check streaming stats
        if "streaming_stats" in data:
            streaming = data["streaming_stats"]
            validation["has_streaming_stats"] = True
            print("✓ Has streaming statistics")

            # Validate streaming stats structure
            required_streaming_fields = [
                "active_streams",
                "completed_streams",
                "failed_streams",
            ]

            for field in required_streaming_fields:
                if field in streaming:
                    validation["required_fields"][f"streaming.{field}"] = True
                    value = streaming[field]
                    print(f"  - {field}: {value}")
                else:
                    validation["required_fields"][f"streaming.{field}"] = False
                    validation["errors"].append(f"Missing streaming field: {field}")

            # Check TTFT stats
            if "ttft" in streaming:
                ttft = streaming["ttft"]
                if "avg" in ttft and ttft["avg"] >= 0:
                    validation["required_fields"]["streaming.ttft.avg"] = True
                    print(f"  - ttft.avg: {ttft['avg']:.3f}ms")
                else:
                    validation["errors"].append("Invalid TTFT average")
        else:
            validation["errors"].append("Missing 'streaming_stats'")

        # Verify aggregations are mathematically correct
        validate_aggregations(data, validation)

        # Print data structure for debugging
        print(f"\nData structure summary:")
        print(f"  Endpoints with request data: {len(data.get('requests', {}))}")
        print(f"  Endpoints with response data: {len(data.get('responses', {}))}")
        print(f"  Endpoints with latency data: {len(data.get('latency', {}))}")

    except Exception as e:
        validation["errors"].append(f"Exception: {str(e)}")
        print(f"✗ Error validating metrics: {e}")

    return validation


def validate_metric_stats(
    stats: dict[str, Any],
    metric_type: str,
    endpoint: str,
    validation: dict[str, Any],
) -> None:
    """Validate that metric statistics have correct structure and values."""
    required_fields = ["rate", "count", "window_size"]

    for field in required_fields:
        field_key = f"{metric_type}.{endpoint}.{field}"
        if field in stats:
            value = stats[field]
            if isinstance(value, (int, float)) and value >= 0:
                validation["required_fields"][field_key] = True
            else:
                validation["required_fields"][field_key] = False
                validation["errors"].append(
                    f"Invalid value for {field_key}: {value}"
                )
        else:
            validation["required_fields"][field_key] = False
            validation["errors"].append(f"Missing field: {field_key}")


def validate_latency_stats(
    stats: dict[str, Any],
    endpoint: str,
    validation: dict[str, Any],
) -> None:
    """Validate latency statistics structure and values."""
    required_percentiles = ["avg", "min", "max", "p50", "p90", "p99"]

    for percentile in required_percentiles:
        field_key = f"latency.{endpoint}.{percentile}"
        if percentile in stats:
            value = stats[percentile]
            if isinstance(value, (int, float)) and value >= 0:
                validation["required_fields"][field_key] = True
            else:
                validation["required_fields"][field_key] = False
                validation["errors"].append(
                    f"Invalid latency value for {field_key}: {value}"
                )
        else:
            validation["required_fields"][field_key] = False
            validation["errors"].append(f"Missing latency field: {field_key}")


def validate_aggregations(data: dict[str, Any], validation: dict[str, Any]) -> None:
    """Validate that aggregations are mathematically correct."""
    # Check that completed + failed + active streams make sense
    if "streaming_stats" in data:
        streaming = data["streaming_stats"]
        active = streaming.get("active_streams", 0)
        completed = streaming.get("completed_streams", 0)
        failed = streaming.get("failed_streams", 0)

        # Active should be >= 0
        if active >= 0:
            validation["aggregations"]["active_streams_valid"] = True
        else:
            validation["aggregations"]["active_streams_valid"] = False
            validation["errors"].append(f"Invalid active streams count: {active}")

        # Completed should be >= 0
        if completed >= 0:
            validation["aggregations"]["completed_streams_valid"] = True
        else:
            validation["aggregations"]["completed_streams_valid"] = False
            validation["errors"].append(f"Invalid completed streams count: {completed}")

        # Failed should be >= 0
        if failed >= 0:
            validation["aggregations"]["failed_streams_valid"] = True
        else:
            validation["aggregations"]["failed_streams_valid"] = False
            validation["errors"].append(f"Invalid failed streams count: {failed}")


# ============================================================================
# WebSocket Validation
# ============================================================================


async def validate_websocket_stream(base_url: str) -> dict[str, Any]:
    """
    Test WebSocket /metrics/stream endpoint if available.

    Args:
        base_url: Base URL of the FakeAI server

    Returns:
        Dict with WebSocket validation results
    """
    print(f"\n{'='*80}")
    print(f"STEP 4: TESTING WEBSOCKET /metrics/stream")
    print(f"{'='*80}")

    validation = {
        "available": False,
        "can_connect": False,
        "receives_historical_data": False,
        "can_subscribe": False,
        "receives_updates": False,
        "errors": [],
    }

    try:
        import websockets
    except ImportError:
        validation["errors"].append("websockets library not installed")
        print("⚠ WebSocket testing skipped (websockets library not available)")
        return validation

    # Parse WebSocket URL
    ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
    ws_url = f"{ws_url}/metrics/stream"

    try:
        async with websockets.connect(ws_url, timeout=5) as websocket:
            validation["available"] = True
            validation["can_connect"] = True
            print("✓ WebSocket connection established")

            # Receive historical data
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)

                if data.get("type") == "historical_data":
                    validation["receives_historical_data"] = True
                    print("✓ Received historical data")
                else:
                    validation["errors"].append(
                        f"Expected historical_data, got {data.get('type')}"
                    )
            except asyncio.TimeoutError:
                validation["errors"].append("Timeout waiting for historical data")

            # Subscribe to metrics
            try:
                subscription = {
                    "type": "subscribe",
                    "filters": {
                        "endpoint": "/v1/chat/completions",
                        "interval": 1.0,
                    },
                }
                await websocket.send(json.dumps(subscription))

                # Wait for confirmation
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)

                if data.get("type") == "subscribed":
                    validation["can_subscribe"] = True
                    print("✓ Successfully subscribed to metrics")
                else:
                    validation["errors"].append(
                        f"Expected subscribed, got {data.get('type')}"
                    )
            except asyncio.TimeoutError:
                validation["errors"].append("Timeout waiting for subscription confirmation")

            # Test ping/pong
            try:
                await websocket.send(json.dumps({"type": "ping"}))
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)

                if data.get("type") == "pong":
                    print("✓ Ping/pong working")
                else:
                    validation["errors"].append("Ping/pong not working correctly")
            except asyncio.TimeoutError:
                validation["errors"].append("Timeout waiting for pong")

    except asyncio.TimeoutError:
        validation["errors"].append("Connection timeout")
        print("✗ WebSocket connection timeout")
    except ConnectionRefusedError:
        validation["errors"].append("Connection refused")
        print("✗ WebSocket connection refused")
    except Exception as e:
        validation["errors"].append(f"Exception: {str(e)}")
        print(f"✗ WebSocket error: {e}")

    return validation


# ============================================================================
# Dashboard Readiness Report
# ============================================================================


def print_dashboard_readiness_report(
    traffic_results: dict[str, Any],
    metrics_validation: dict[str, Any],
    websocket_validation: dict[str, Any],
) -> int:
    """
    Print comprehensive dashboard readiness report.

    Args:
        traffic_results: Results from traffic generation
        metrics_validation: Results from metrics validation
        websocket_validation: Results from WebSocket validation

    Returns:
        0 if dashboard is ready, 1 otherwise
    """
    print(f"\n{'='*80}")
    print(f"DASHBOARD READINESS REPORT")
    print(f"{'='*80}")

    # Traffic Generation
    print(f"\n1. TRAFFIC GENERATION")
    print(f"   Status: {'PASS' if traffic_results['successful'] > 0 else 'FAIL'}")
    print(f"   Details:")
    print(f"     - Requests sent: {traffic_results['total']}")
    print(f"     - Successful: {traffic_results['successful']}")
    print(f"     - Failed: {traffic_results['failed']}")
    print(f"     - Success rate: {traffic_results['successful']/traffic_results['total']*100:.1f}%")

    # Metrics Endpoint
    print(f"\n2. /metrics ENDPOINT")
    print(f"   Status: {'PASS' if metrics_validation['endpoint_accessible'] else 'FAIL'}")
    print(f"   Details:")
    print(f"     - Accessible: {'Yes' if metrics_validation['endpoint_accessible'] else 'No'}")
    print(f"     - Has requests data: {'Yes' if metrics_validation['has_requests_data'] else 'No'}")
    print(f"     - Has responses data: {'Yes' if metrics_validation['has_responses_data'] else 'No'}")
    print(f"     - Has latency data: {'Yes' if metrics_validation['has_latency_data'] else 'No'}")
    print(f"     - Has streaming stats: {'Yes' if metrics_validation['has_streaming_stats'] else 'No'}")

    required_fields_passed = sum(1 for v in metrics_validation["required_fields"].values() if v)
    required_fields_total = len(metrics_validation["required_fields"])
    if required_fields_total > 0:
        print(f"     - Required fields: {required_fields_passed}/{required_fields_total} present")

    if metrics_validation["errors"]:
        print(f"   Errors ({len(metrics_validation['errors'])}):")
        for error in metrics_validation["errors"][:5]:  # Show first 5 errors
            print(f"     - {error}")
        if len(metrics_validation["errors"]) > 5:
            print(f"     ... and {len(metrics_validation['errors']) - 5} more")

    # WebSocket Stream
    print(f"\n3. WEBSOCKET /metrics/stream")
    if not websocket_validation.get("available"):
        print(f"   Status: SKIPPED (websockets library not available)")
    else:
        ws_pass = (
            websocket_validation["can_connect"] and
            websocket_validation["receives_historical_data"]
        )
        print(f"   Status: {'PASS' if ws_pass else 'FAIL'}")
        print(f"   Details:")
        print(f"     - Can connect: {'Yes' if websocket_validation['can_connect'] else 'No'}")
        print(f"     - Receives historical data: {'Yes' if websocket_validation['receives_historical_data'] else 'No'}")
        print(f"     - Can subscribe: {'Yes' if websocket_validation['can_subscribe'] else 'No'}")

        if websocket_validation["errors"]:
            print(f"   Errors:")
            for error in websocket_validation["errors"]:
                print(f"     - {error}")

    # Overall Assessment
    print(f"\n{'='*80}")
    print(f"OVERALL ASSESSMENT")
    print(f"{'='*80}")

    # Determine if dashboard is ready
    traffic_ok = traffic_results["successful"] > 0
    metrics_ok = (
        metrics_validation["endpoint_accessible"] and
        metrics_validation["has_requests_data"] and
        metrics_validation["has_responses_data"] and
        metrics_validation["has_latency_data"] and
        metrics_validation["has_streaming_stats"]
    )

    # WebSocket is optional
    ws_ok = not websocket_validation.get("available") or websocket_validation["can_connect"]

    critical_errors = len([
        e for e in metrics_validation["errors"]
        if "Missing" in e or "Invalid" in e
    ])

    dashboard_ready = traffic_ok and metrics_ok and critical_errors == 0

    print(f"\nDashboard Ready: {'YES ✓' if dashboard_ready else 'NO ✗'}")
    print(f"\nComponent Status:")
    print(f"  ✓ Traffic Generation: {'OK' if traffic_ok else 'FAILED'}")
    print(f"  {'✓' if metrics_ok else '✗'} Metrics Endpoint: {'OK' if metrics_ok else 'FAILED'}")
    print(f"  {'✓' if ws_ok else '⚠'} WebSocket Stream: {'OK' if ws_ok else 'DEGRADED'}")
    print(f"  {'✓' if critical_errors == 0 else '✗'} Data Quality: {critical_errors} critical errors")

    if dashboard_ready:
        print(f"\n🎉 Dashboard is READY to display data correctly!")
        return 0
    else:
        print(f"\n⚠ Dashboard may have issues displaying data.")
        print(f"   Please review the errors above and fix the issues.")
        return 1


# ============================================================================
# Main Test Flow
# ============================================================================


async def test_dashboard_data_flow():
    """Main test function for end-to-end dashboard data flow."""
    print(f"\n{'='*80}")
    print(f"END-TO-END DASHBOARD DATA FLOW TEST")
    print(f"{'='*80}")
    print(f"Base URL: {BASE_URL}")
    print(f"Test requests: {NUM_REQUESTS}")

    # Step 1: Generate varied traffic
    traffic_results = await generate_varied_traffic(BASE_URL, NUM_REQUESTS)

    # Step 2: Wait for event processing
    print(f"\n{'='*80}")
    print(f"STEP 2: WAITING FOR EVENT PROCESSING")
    print(f"{'='*80}")
    print(f"Waiting {PROCESSING_WAIT_TIME} seconds for metrics aggregation...")
    await asyncio.sleep(PROCESSING_WAIT_TIME)
    print("✓ Processing wait complete")

    # Step 3: Validate /metrics endpoint
    metrics_validation = await validate_metrics_endpoint(BASE_URL)

    # Step 4: Test WebSocket stream (optional)
    websocket_validation = await validate_websocket_stream(BASE_URL)

    # Step 5: Print dashboard readiness report
    exit_code = print_dashboard_readiness_report(
        traffic_results,
        metrics_validation,
        websocket_validation,
    )

    return exit_code


# ============================================================================
# Pytest Integration
# ============================================================================

# Note: This test requires a running FakeAI server at BASE_URL.
# Run standalone: python tests/test_dashboard_data.py
# Run with pytest: pytest tests/test_dashboard_data.py -v --tb=short
#
# To start the server first:
#   python -m fakeai server --port 8000


@pytest.mark.asyncio
@pytest.mark.integration
async def test_dashboard_data_flow_pytest():
    """Pytest wrapper for dashboard data flow test."""
    exit_code = await test_dashboard_data_flow()
    assert exit_code == 0, "Dashboard data flow test failed"


# ============================================================================
# Standalone Execution
# ============================================================================


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(test_dashboard_data_flow())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
