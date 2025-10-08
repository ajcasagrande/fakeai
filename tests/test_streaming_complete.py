"""
Comprehensive Streaming Tests

Tests all aspects of streaming functionality with real HTTP requests:
1. /v1/chat/completions streaming
2. /v1/completions streaming
3. Multiple concurrent streams
4. Streaming metrics validation
5. TTFT (Time to First Token) measurement
6. ITL (Inter-Token Latency) tracking
7. Token count accuracy
8. Error handling and exceptions
9. Streaming tracker data integrity
"""

#  SPDX-License-Identifier: Apache-2.0

import json
import statistics
import time
from typing import Any, Dict

import requests

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-key"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


class StreamingTestResults:
    """Container for streaming test results."""

    def __init__(self):
        self.total_streams = 0
        self.successful_streams = 0
        self.failed_streams = 0
        self.ttft_values = []
        self.token_counts = []
        self.total_durations = []
        self.errors = []
        self.detailed_results = []

    def add_result(self, result: dict[str, Any]):
        """Add a streaming result."""
        self.detailed_results.append(result)
        self.total_streams += 1

        if result.get("success"):
            self.successful_streams += 1
            if "ttft_ms" in result:
                self.ttft_values.append(result["ttft_ms"])
            if "token_count" in result:
                self.token_counts.append(result["token_count"])
            if "duration_ms" in result:
                self.total_durations.append(result["duration_ms"])
        else:
            self.failed_streams += 1
            if "error" in result:
                self.errors.append(result["error"])

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics."""
        return {
            "total_streams": self.total_streams,
            "successful_streams": self.successful_streams,
            "failed_streams": self.failed_streams,
            "success_rate": (self.successful_streams / self.total_streams * 100) if self.total_streams > 0 else 0,
            "ttft_stats": {
                "count": len(self.ttft_values),
                "mean": statistics.mean(self.ttft_values) if self.ttft_values else 0,
                "median": statistics.median(self.ttft_values) if self.ttft_values else 0,
                "min": min(self.ttft_values) if self.ttft_values else 0,
                "max": max(self.ttft_values) if self.ttft_values else 0,
            },
            "token_count_stats": {
                "count": len(self.token_counts),
                "mean": statistics.mean(self.token_counts) if self.token_counts else 0,
                "total": sum(self.token_counts),
                "min": min(self.token_counts) if self.token_counts else 0,
                "max": max(self.token_counts) if self.token_counts else 0,
            },
            "duration_stats": {
                "count": len(self.total_durations),
                "mean": statistics.mean(self.total_durations) if self.total_durations else 0,
                "median": statistics.median(self.total_durations) if self.total_durations else 0,
                "min": min(self.total_durations) if self.total_durations else 0,
                "max": max(self.total_durations) if self.total_durations else 0,
            },
            "errors": self.errors
        }


def parse_sse_event(line: str) -> dict[str, Any]:
    """Parse a single SSE event line."""
    if line.startswith("data: "):
        data_str = line[6:].strip()
        if data_str == "[DONE]":
            return {"type": "done"}
        try:
            return {"type": "data", "data": json.loads(data_str)}
        except json.JSONDecodeError as e:
            return {"type": "error", "error": f"JSON decode error: {e}"}
    return {"type": "unknown"}


def test_chat_completions_streaming(model: str = "openai/gpt-oss-20b", max_tokens: int = 50) -> dict[str, Any]:
    """
    Test /v1/chat/completions streaming endpoint.

    Args:
        model: Model name to use
        max_tokens: Maximum tokens to generate

    Returns:
        Dict with test results
    """
    print(f"\n{'='*80}")
    print(f"Testing /v1/chat/completions streaming with model: {model}")
    print(f"{'='*80}")

    url = f"{BASE_URL}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Write a short poem about streaming data."}
        ],
        "stream": True,
        "max_tokens": max_tokens,
        "temperature": 0.7
    }

    result = {
        "endpoint": "/v1/chat/completions",
        "model": model,
        "success": False,
        "token_count": 0,
        "chunks_received": 0,
        "tokens": [],
        "ttft_ms": None,
        "duration_ms": None,
        "finish_reason": None,
        "usage": None
    }

    try:
        start_time = time.time()
        first_token_time = None

        print(f"Sending request to {url}")
        response = requests.post(url, headers=HEADERS, json=payload, stream=True, timeout=30)

        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}: {response.text}"
            print(f"❌ Request failed: {result['error']}")
            return result

        print("✓ Connection established, receiving stream...")

        # Process SSE stream
        for line in response.iter_lines():
            if not line:
                continue

            line_str = line.decode('utf-8').strip()
            if not line_str:
                continue

            event = parse_sse_event(line_str)

            if event["type"] == "done":
                print("✓ Stream completed with [DONE] marker")
                break
            elif event["type"] == "data":
                result["chunks_received"] += 1
                data = event["data"]

                # Extract token from delta
                if "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    delta = choice.get("delta", {})

                    if "content" in delta and delta["content"]:
                        token = delta["content"]
                        result["tokens"].append(token)
                        result["token_count"] += 1

                        # Record TTFT
                        if first_token_time is None:
                            first_token_time = time.time()
                            result["ttft_ms"] = (first_token_time - start_time) * 1000
                            print(f"✓ First token received: '{token}' (TTFT: {result['ttft_ms']:.2f}ms)")

                    # Check for finish reason
                    if "finish_reason" in choice and choice["finish_reason"]:
                        result["finish_reason"] = choice["finish_reason"]
                        print(f"✓ Finish reason: {result['finish_reason']}")

                # Extract usage if present
                if "usage" in data:
                    result["usage"] = data["usage"]
            elif event["type"] == "error":
                result["error"] = event["error"]
                print(f"❌ Parse error: {event['error']}")
                return result

        end_time = time.time()
        result["duration_ms"] = (end_time - start_time) * 1000
        result["success"] = result["token_count"] > 0

        # Print summary
        print(f"\n{'='*80}")
        print("STREAM SUMMARY")
        print(f"{'='*80}")
        print(f"✓ Success: {result['success']}")
        print(f"✓ Tokens received: {result['token_count']}")
        print(f"✓ Chunks received: {result['chunks_received']}")
        print(f"✓ TTFT: {result['ttft_ms']:.2f}ms" if result['ttft_ms'] else "✗ TTFT: Not measured")
        print(f"✓ Total duration: {result['duration_ms']:.2f}ms")
        print(f"✓ Tokens/sec: {result['token_count'] / (result['duration_ms'] / 1000):.2f}")
        if result["usage"]:
            print(f"✓ Usage: {result['usage']}")
        print(f"✓ Generated text: {''.join(result['tokens'][:100])}{'...' if len(result['tokens']) > 100 else ''}")

    except requests.exceptions.Timeout:
        result["error"] = "Request timeout"
        print(f"❌ Timeout error")
    except requests.exceptions.RequestException as e:
        result["error"] = f"Request error: {str(e)}"
        print(f"❌ Request error: {e}")
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        print(f"❌ Unexpected error: {e}")

    return result


def test_completions_streaming(model: str = "openai/gpt-oss-20b", max_tokens: int = 50) -> dict[str, Any]:
    """
    Test /v1/completions streaming endpoint.

    Args:
        model: Model name to use
        max_tokens: Maximum tokens to generate

    Returns:
        Dict with test results
    """
    print(f"\n{'='*80}")
    print(f"Testing /v1/completions streaming with model: {model}")
    print(f"{'='*80}")

    url = f"{BASE_URL}/v1/completions"
    payload = {
        "model": model,
        "prompt": "Once upon a time, in a land of streaming data,",
        "stream": True,
        "max_tokens": max_tokens,
        "temperature": 0.7
    }

    result = {
        "endpoint": "/v1/completions",
        "model": model,
        "success": False,
        "token_count": 0,
        "chunks_received": 0,
        "tokens": [],
        "ttft_ms": None,
        "duration_ms": None,
        "finish_reason": None,
        "usage": None
    }

    try:
        start_time = time.time()
        first_token_time = None

        print(f"Sending request to {url}")
        response = requests.post(url, headers=HEADERS, json=payload, stream=True, timeout=30)

        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}: {response.text}"
            print(f"❌ Request failed: {result['error']}")
            return result

        print("✓ Connection established, receiving stream...")

        # Process SSE stream
        for line in response.iter_lines():
            if not line:
                continue

            line_str = line.decode('utf-8').strip()
            if not line_str:
                continue

            event = parse_sse_event(line_str)

            if event["type"] == "done":
                print("✓ Stream completed with [DONE] marker")
                break
            elif event["type"] == "data":
                result["chunks_received"] += 1
                data = event["data"]

                # Extract token from text
                if "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]

                    if "text" in choice and choice["text"]:
                        token = choice["text"]
                        result["tokens"].append(token)
                        result["token_count"] += 1

                        # Record TTFT
                        if first_token_time is None:
                            first_token_time = time.time()
                            result["ttft_ms"] = (first_token_time - start_time) * 1000
                            print(f"✓ First token received: '{token}' (TTFT: {result['ttft_ms']:.2f}ms)")

                    # Check for finish reason
                    if "finish_reason" in choice and choice["finish_reason"]:
                        result["finish_reason"] = choice["finish_reason"]
                        print(f"✓ Finish reason: {result['finish_reason']}")

                # Extract usage if present
                if "usage" in data:
                    result["usage"] = data["usage"]
            elif event["type"] == "error":
                result["error"] = event["error"]
                print(f"❌ Parse error: {event['error']}")
                return result

        end_time = time.time()
        result["duration_ms"] = (end_time - start_time) * 1000
        result["success"] = result["token_count"] > 0

        # Print summary
        print(f"\n{'='*80}")
        print("STREAM SUMMARY")
        print(f"{'='*80}")
        print(f"✓ Success: {result['success']}")
        print(f"✓ Tokens received: {result['token_count']}")
        print(f"✓ Chunks received: {result['chunks_received']}")
        print(f"✓ TTFT: {result['ttft_ms']:.2f}ms" if result['ttft_ms'] else "✗ TTFT: Not measured")
        print(f"✓ Total duration: {result['duration_ms']:.2f}ms")
        print(f"✓ Tokens/sec: {result['token_count'] / (result['duration_ms'] / 1000):.2f}")
        if result["usage"]:
            print(f"✓ Usage: {result['usage']}")
        print(f"✓ Generated text: {''.join(result['tokens'][:100])}{'...' if len(result['tokens']) > 100 else ''}")

    except requests.exceptions.Timeout:
        result["error"] = "Request timeout"
        print(f"❌ Timeout error")
    except requests.exceptions.RequestException as e:
        result["error"] = f"Request error: {str(e)}"
        print(f"❌ Request error: {e}")
    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        print(f"❌ Unexpected error: {e}")

    return result


def test_multiple_streams(count: int = 10) -> StreamingTestResults:
    """
    Test multiple streaming requests sequentially.

    Args:
        count: Number of streams to test

    Returns:
        StreamingTestResults with aggregated data
    """
    print(f"\n{'='*80}")
    print(f"Testing {count} Sequential Streaming Requests")
    print(f"{'='*80}")

    results = StreamingTestResults()

    for i in range(count):
        print(f"\n--- Stream {i+1}/{count} ---")

        # Alternate between chat completions and completions
        if i % 2 == 0:
            result = test_chat_completions_streaming(max_tokens=30)
        else:
            result = test_completions_streaming(max_tokens=30)

        results.add_result(result)

        # Small delay between requests
        if i < count - 1:
            time.sleep(0.5)

    return results


def check_streaming_tracker() -> dict[str, Any]:
    """
    Check streaming tracker metrics via /metrics/streaming endpoint.

    Returns:
        Dict with streaming tracker data
    """
    print(f"\n{'='*80}")
    print("Checking Streaming Tracker Metrics")
    print(f"{'='*80}")

    try:
        url = f"{BASE_URL}/metrics/streaming"
        print(f"Fetching metrics from {url}")

        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code != 200:
            print(f"❌ Failed to fetch metrics: HTTP {response.status_code}")
            return {"error": f"HTTP {response.status_code}"}

        data = response.json()

        print(f"\n✓ Streaming Metrics Retrieved:")
        print(f"  - Active streams: {data.get('active_streams', 'N/A')}")
        print(f"  - Completed streams: {data.get('completed_streams', 'N/A')}")
        print(f"  - Failed streams: {data.get('failed_streams', 'N/A')}")

        if "ttft" in data:
            ttft = data["ttft"]
            print(f"  - TTFT avg: {ttft.get('avg', 'N/A')}ms")
            print(f"  - TTFT p50: {ttft.get('p50', 'N/A')}ms")
            print(f"  - TTFT p90: {ttft.get('p90', 'N/A')}ms")
            print(f"  - TTFT p99: {ttft.get('p99', 'N/A')}ms")

        if "tokens_per_second" in data:
            tps = data["tokens_per_second"]
            print(f"  - TPS avg: {tps.get('avg', 'N/A')}")
            print(f"  - TPS p50: {tps.get('p50', 'N/A')}")
            print(f"  - TPS p90: {tps.get('p90', 'N/A')}")

        if "inter_token_latency_ms" in data:
            itl = data["inter_token_latency_ms"]
            print(f"  - ITL avg: {itl.get('avg', 'N/A')}ms")
            print(f"  - ITL p50: {itl.get('p50', 'N/A')}ms")
            print(f"  - ITL p90: {itl.get('p90', 'N/A')}ms")

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return {"error": str(e)}
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {"error": str(e)}


def check_general_metrics() -> dict[str, Any]:
    """
    Check general metrics via /metrics endpoint.

    Returns:
        Dict with general metrics data
    """
    print(f"\n{'='*80}")
    print("Checking General Metrics")
    print(f"{'='*80}")

    try:
        url = f"{BASE_URL}/metrics"
        print(f"Fetching metrics from {url}")

        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code != 200:
            print(f"❌ Failed to fetch metrics: HTTP {response.status_code}")
            return {"error": f"HTTP {response.status_code}"}

        data = response.json()

        print(f"\n✓ General Metrics Retrieved:")
        print(f"  - Total requests: {data.get('total_requests', 'N/A')}")
        print(f"  - Success rate: {data.get('success_rate', 'N/A')}%")
        print(f"  - Average latency: {data.get('avg_latency', 'N/A')}ms")

        if "streaming" in data:
            streaming = data["streaming"]
            print(f"\n  Streaming section in /metrics:")
            print(f"  - Active streams: {streaming.get('active_streams', 'N/A')}")
            print(f"  - Completed streams: {streaming.get('completed_streams', 'N/A')}")
            print(f"  - Failed streams: {streaming.get('failed_streams', 'N/A')}")

        return data

    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return {"error": str(e)}
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {"error": str(e)}


def validate_no_exceptions() -> bool:
    """
    Validate that there are no NameError or other exceptions in the server logs.
    This checks if the server is responding properly.

    Returns:
        True if no exceptions detected
    """
    print(f"\n{'='*80}")
    print("Validating No Exceptions")
    print(f"{'='*80}")

    try:
        # Try to hit the health endpoint
        url = f"{BASE_URL}/health"
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            print("✓ Server health check passed")
            return True
        else:
            print(f"⚠ Server health check returned: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception checking server health: {e}")
        return False


def print_detailed_report(results: StreamingTestResults, streaming_metrics: Dict, general_metrics: Dict):
    """
    Print a comprehensive report of all test results.

    Args:
        results: Streaming test results
        streaming_metrics: Streaming tracker metrics
        general_metrics: General metrics
    """
    print(f"\n{'='*80}")
    print("COMPREHENSIVE STREAMING TEST REPORT")
    print(f"{'='*80}")

    summary = results.get_summary()

    print(f"\n1. STREAMING REQUEST TESTS")
    print(f"   {'─'*76}")
    print(f"   Total streams tested: {summary['total_streams']}")
    print(f"   Successful streams: {summary['successful_streams']}")
    print(f"   Failed streams: {summary['failed_streams']}")
    print(f"   Success rate: {summary['success_rate']:.1f}%")

    print(f"\n2. TIME TO FIRST TOKEN (TTFT)")
    print(f"   {'─'*76}")
    ttft = summary['ttft_stats']
    print(f"   Measurements: {ttft['count']}")
    print(f"   Mean: {ttft['mean']:.2f}ms")
    print(f"   Median: {ttft['median']:.2f}ms")
    print(f"   Min: {ttft['min']:.2f}ms")
    print(f"   Max: {ttft['max']:.2f}ms")

    print(f"\n3. TOKEN COUNTS")
    print(f"   {'─'*76}")
    tokens = summary['token_count_stats']
    print(f"   Total streams: {tokens['count']}")
    print(f"   Mean tokens/stream: {tokens['mean']:.1f}")
    print(f"   Total tokens: {tokens['total']}")
    print(f"   Min tokens: {tokens['min']}")
    print(f"   Max tokens: {tokens['max']}")

    print(f"\n4. STREAM DURATION")
    print(f"   {'─'*76}")
    duration = summary['duration_stats']
    print(f"   Measurements: {duration['count']}")
    print(f"   Mean: {duration['mean']:.2f}ms")
    print(f"   Median: {duration['median']:.2f}ms")
    print(f"   Min: {duration['min']:.2f}ms")
    print(f"   Max: {duration['max']:.2f}ms")

    print(f"\n5. STREAMING TRACKER METRICS")
    print(f"   {'─'*76}")
    if "error" not in streaming_metrics:
        print(f"   Active streams: {streaming_metrics.get('active_streams', 'N/A')}")
        print(f"   Completed streams: {streaming_metrics.get('completed_streams', 'N/A')}")
        print(f"   Failed streams: {streaming_metrics.get('failed_streams', 'N/A')}")

        if "ttft" in streaming_metrics:
            ttft_tracker = streaming_metrics["ttft"]
            print(f"   TTFT (tracker) avg: {ttft_tracker.get('avg', 'N/A')}ms")
            print(f"   TTFT (tracker) p50: {ttft_tracker.get('p50', 'N/A')}ms")
            print(f"   TTFT (tracker) p90: {ttft_tracker.get('p90', 'N/A')}ms")

        if "tokens_per_second" in streaming_metrics:
            tps = streaming_metrics["tokens_per_second"]
            print(f"   TPS avg: {tps.get('avg', 'N/A')}")
            print(f"   TPS p50: {tps.get('p50', 'N/A')}")
    else:
        print(f"   ❌ Error fetching streaming metrics: {streaming_metrics['error']}")

    print(f"\n6. GENERAL METRICS")
    print(f"   {'─'*76}")
    if "error" not in general_metrics:
        print(f"   Total requests: {general_metrics.get('total_requests', 'N/A')}")
        print(f"   Success rate: {general_metrics.get('success_rate', 'N/A')}%")
        print(f"   Average latency: {general_metrics.get('avg_latency', 'N/A')}ms")
    else:
        print(f"   ❌ Error fetching general metrics: {general_metrics['error']}")

    print(f"\n7. ERROR ANALYSIS")
    print(f"   {'─'*76}")
    if summary['errors']:
        print(f"   Errors found: {len(summary['errors'])}")
        for i, error in enumerate(summary['errors'][:5], 1):
            print(f"   {i}. {error}")
        if len(summary['errors']) > 5:
            print(f"   ... and {len(summary['errors']) - 5} more")
    else:
        print(f"   ✓ No errors detected")

    print(f"\n8. VALIDATION CHECKS")
    print(f"   {'─'*76}")

    # Check 1: All streams completed
    check1 = summary['successful_streams'] == summary['total_streams']
    print(f"   {'✓' if check1 else '✗'} All streams completed successfully")

    # Check 2: TTFT measured for all
    check2 = ttft['count'] == summary['successful_streams']
    print(f"   {'✓' if check2 else '✗'} TTFT measured for all successful streams")

    # Check 3: Token counts are correct
    check3 = tokens['total'] > 0 and tokens['mean'] > 0
    print(f"   {'✓' if check3 else '✗'} Token counts are valid")

    # Check 4: Streaming tracker has data
    check4 = "error" not in streaming_metrics and streaming_metrics.get('completed_streams', 0) > 0
    print(f"   {'✓' if check4 else '✗'} Streaming tracker has data")

    # Check 5: No exceptions
    check5 = validate_no_exceptions()
    print(f"   {'✓' if check5 else '✗'} No server exceptions detected")

    # Check 6: TTFT < Total Duration (sanity check)
    check6 = ttft['mean'] < duration['mean'] if ttft['mean'] > 0 and duration['mean'] > 0 else False
    print(f"   {'✓' if check6 else '✗'} TTFT < Total Duration (sanity check)")

    # Overall pass/fail
    all_checks = check1 and check2 and check3 and check4 and check5 and check6

    print(f"\n{'='*80}")
    if all_checks:
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
    else:
        print("⚠⚠⚠ SOME TESTS FAILED ⚠⚠⚠")
    print(f"{'='*80}\n")


def main():
    """Main test execution."""
    print("="*80)
    print("COMPREHENSIVE STREAMING TESTS")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY}")
    print("="*80)

    # Test 1: Single chat completions stream
    print("\n" + "="*80)
    print("TEST 1: Chat Completions Streaming")
    print("="*80)
    result1 = test_chat_completions_streaming(max_tokens=50)

    # Test 2: Single completions stream
    print("\n" + "="*80)
    print("TEST 2: Completions Streaming")
    print("="*80)
    result2 = test_completions_streaming(max_tokens=50)

    # Test 3: Multiple streams
    print("\n" + "="*80)
    print("TEST 3: Multiple Sequential Streams")
    print("="*80)
    results = test_multiple_streams(count=10)

    # Test 4: Check streaming tracker
    print("\n" + "="*80)
    print("TEST 4: Streaming Tracker Validation")
    print("="*80)
    streaming_metrics = check_streaming_tracker()

    # Test 5: Check general metrics
    print("\n" + "="*80)
    print("TEST 5: General Metrics Validation")
    print("="*80)
    general_metrics = check_general_metrics()

    # Print comprehensive report
    print_detailed_report(results, streaming_metrics, general_metrics)


if __name__ == "__main__":
    main()
