#!/usr/bin/env python3
"""
End-to-end event flow verification test.

This script tests that events are flowing through the entire system after wiring:
1. Waits for server to be running on port 8765
2. Sends POST to /v1/chat/completions (non-streaming)
3. Waits for event processing
4. Checks /metrics/events - verifies events_published > 0
5. Checks /metrics/errors - verifies total_requests > 0
6. Sends streaming request
7. Checks /metrics/streaming - verifies total_streams > 0
8. Prints comprehensive report
"""
#  SPDX-License-Identifier: Apache-2.0

import json
import socket
import sys
import time
from typing import Any, Optional

import requests


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"{Colors.CYAN}ℹ {message}{Colors.RESET}")


def is_port_open(host: str, port: int) -> bool:
    """Check if a port is open and accepting connections."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def wait_for_server(host: str = "127.0.0.1", port: int = 8765,
                    timeout: int = 30, check_interval: float = 0.5) -> bool:
    """
    Wait for server to be running on specified port.

    Args:
        host: Server host
        port: Server port
        timeout: Maximum time to wait in seconds
        check_interval: Time between checks in seconds

    Returns:
        True if server is ready, False if timeout
    """
    print_section("Step 1: Waiting for Server")
    print_info(f"Waiting for server at {host}:{port} (timeout: {timeout}s)")

    start_time = time.time()
    attempts = 0

    while time.time() - start_time < timeout:
        attempts += 1

        if is_port_open(host, port):
            # Port is open, now check if server responds
            try:
                response = requests.get(
                    f"http://{host}:{port}/health",
                    timeout=2
                )
                if response.status_code == 200:
                    elapsed = time.time() - start_time
                    print_success(f"Server is ready after {elapsed:.2f}s ({attempts} attempts)")
                    return True
            except requests.exceptions.RequestException:
                pass

        time.sleep(check_interval)

    print_error(f"Server did not start within {timeout}s")
    return False


def send_non_streaming_request(base_url: str) -> Optional[dict[str, Any]]:
    """
    Send a non-streaming chat completion request.

    Args:
        base_url: Base URL of the server

    Returns:
        Response JSON or None if failed
    """
    print_section("Step 2: Non-Streaming Request")

    url = f"{base_url}/v1/chat/completions"
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "Hello, this is a test message!"}
        ],
        "max_tokens": 50
    }

    print_info(f"Sending POST to {url}")
    print_info(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=10)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            print_success(f"Request successful (status: {response.status_code}, time: {elapsed:.3f}s)")
            print_info(f"Response ID: {data.get('id', 'N/A')}")
            print_info(f"Model: {data.get('model', 'N/A')}")

            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0].get('message', {}).get('content', '')
                print_info(f"Content preview: {content[:100]}...")

            if 'usage' in data:
                usage = data['usage']
                print_info(f"Tokens - Prompt: {usage.get('prompt_tokens', 0)}, "
                          f"Completion: {usage.get('completion_tokens', 0)}, "
                          f"Total: {usage.get('total_tokens', 0)}")

            return data
        else:
            print_error(f"Request failed with status {response.status_code}")
            print_error(f"Response: {response.text[:200]}")
            return None

    except Exception as e:
        print_error(f"Request failed with exception: {e}")
        return None


def wait_for_event_processing(delay: float = 0.5) -> None:
    """
    Wait for events to be processed.

    Args:
        delay: Time to wait in seconds
    """
    print_section("Step 3: Waiting for Event Processing")
    print_info(f"Waiting {delay}s for events to propagate through the system...")
    time.sleep(delay)
    print_success("Wait complete")


def check_event_metrics(base_url: str) -> Optional[dict[str, Any]]:
    """
    Check /metrics/events endpoint.

    Args:
        base_url: Base URL of the server

    Returns:
        Metrics data or None if failed
    """
    print_section("Step 4: Checking Event Bus Metrics")

    url = f"{base_url}/metrics/events"
    print_info(f"Fetching {url}")

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Event metrics retrieved successfully")

            # Check for events_published
            events_published = data.get('events_published', 0)
            events_processed = data.get('events_processed', 0)
            events_dropped = data.get('events_dropped', 0)
            queue_depth = data.get('queue_depth', 0)

            print_info(f"Events Published: {events_published}")
            print_info(f"Events Processed: {events_processed}")
            print_info(f"Events Dropped: {events_dropped}")
            print_info(f"Queue Depth: {queue_depth}")

            # Verify events_published > 0
            if events_published > 0:
                print_success(f"ASSERTION PASSED: events_published ({events_published}) > 0")
            else:
                print_error(f"ASSERTION FAILED: events_published ({events_published}) should be > 0")
                print_warning("Events are not being published to the event bus!")

            # Additional checks
            if events_processed > 0:
                print_success(f"Events are being processed ({events_processed} processed)")
            else:
                print_warning("No events have been processed yet")

            if events_dropped > 0:
                print_warning(f"Some events were dropped ({events_dropped} dropped)")

            # Show subscriber stats if available
            if 'subscribers' in data:
                subscribers = data['subscribers']
                print_info(f"Active Subscribers: {len(subscribers)}")
                for sub_name, sub_stats in subscribers.items():
                    print_info(f"  - {sub_name}: {sub_stats.get('events_received', 0)} events received")

            return data
        else:
            print_error(f"Failed to retrieve metrics (status: {response.status_code})")
            print_error(f"Response: {response.text[:200]}")
            return None

    except Exception as e:
        print_error(f"Failed to check event metrics: {e}")
        return None


def check_error_metrics(base_url: str) -> Optional[dict[str, Any]]:
    """
    Check /metrics/errors endpoint.

    Args:
        base_url: Base URL of the server

    Returns:
        Metrics data or None if failed
    """
    print_section("Step 5: Checking Error Metrics")

    url = f"{base_url}/metrics/errors"
    print_info(f"Fetching {url}")

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Error metrics retrieved successfully")

            # Check for total_requests
            total_requests = data.get('total_requests', 0)
            total_errors = data.get('total_errors', 0)
            error_rate = data.get('error_rate', 0.0)

            print_info(f"Total Requests: {total_requests}")
            print_info(f"Total Errors: {total_errors}")
            print_info(f"Error Rate: {error_rate:.2%}")

            # Verify total_requests > 0
            if total_requests > 0:
                print_success(f"ASSERTION PASSED: total_requests ({total_requests}) > 0")
            else:
                print_error(f"ASSERTION FAILED: total_requests ({total_requests}) should be > 0")
                print_warning("Error metrics tracker is not recording requests!")

            # Show additional stats
            if 'by_type' in data and data['by_type']:
                print_info("Errors by type:")
                for error_type, count in data['by_type'].items():
                    print_info(f"  - {error_type}: {count}")

            if 'by_endpoint' in data and data['by_endpoint']:
                print_info("Errors by endpoint:")
                for endpoint, count in list(data['by_endpoint'].items())[:5]:
                    print_info(f"  - {endpoint}: {count}")

            return data
        else:
            print_error(f"Failed to retrieve metrics (status: {response.status_code})")
            print_error(f"Response: {response.text[:200]}")
            return None

    except Exception as e:
        print_error(f"Failed to check error metrics: {e}")
        return None


def send_streaming_request(base_url: str) -> bool:
    """
    Send a streaming chat completion request.

    Args:
        base_url: Base URL of the server

    Returns:
        True if successful, False otherwise
    """
    print_section("Step 6: Streaming Request")

    url = f"{base_url}/v1/chat/completions"
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "Count from 1 to 5"}
        ],
        "stream": True,
        "max_tokens": 50
    }

    print_info(f"Sending streaming POST to {url}")
    print_info(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        start_time = time.time()
        response = requests.post(url, json=payload, stream=True, timeout=10)

        if response.status_code != 200:
            print_error(f"Request failed with status {response.status_code}")
            return False

        print_success(f"Streaming request initiated (status: {response.status_code})")

        # Consume the stream
        chunks = 0
        for line in response.iter_lines():
            if line:
                chunks += 1
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    data_str = decoded_line[6:]  # Remove 'data: ' prefix
                    if data_str.strip() != '[DONE]':
                        try:
                            json.loads(data_str)
                        except json.JSONDecodeError:
                            pass

        elapsed = time.time() - start_time
        print_success(f"Stream completed (chunks: {chunks}, time: {elapsed:.3f}s)")
        return True

    except Exception as e:
        print_error(f"Streaming request failed: {e}")
        return False


def check_streaming_metrics(base_url: str) -> Optional[dict[str, Any]]:
    """
    Check /metrics/streaming endpoint.

    Args:
        base_url: Base URL of the server

    Returns:
        Metrics data or None if failed
    """
    print_section("Step 7: Checking Streaming Metrics")

    url = f"{base_url}/metrics/streaming"
    print_info(f"Fetching {url}")

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Streaming metrics retrieved successfully")

            # Check for total_streams
            total_streams = data.get('total_streams', 0)
            successful_streams = data.get('successful_streams', 0)
            failed_streams = data.get('failed_streams', 0)

            print_info(f"Total Streams: {total_streams}")
            print_info(f"Successful Streams: {successful_streams}")
            print_info(f"Failed Streams: {failed_streams}")

            # Verify total_streams > 0
            if total_streams > 0:
                print_success(f"ASSERTION PASSED: total_streams ({total_streams}) > 0")
            else:
                print_error(f"ASSERTION FAILED: total_streams ({total_streams}) should be > 0")
                print_warning("Streaming metrics tracker is not recording streams!")

            # Show additional stats
            if 'ttft_percentiles' in data:
                ttft = data['ttft_percentiles']
                print_info(f"TTFT (Time To First Token):")
                if ttft:
                    print_info(f"  P50: {ttft.get('p50', 0):.3f}s")
                    print_info(f"  P95: {ttft.get('p95', 0):.3f}s")
                    print_info(f"  P99: {ttft.get('p99', 0):.3f}s")

            if 'itl_stats' in data:
                itl = data['itl_stats']
                print_info(f"ITL (Inter-Token Latency):")
                if itl:
                    print_info(f"  Mean: {itl.get('mean', 0):.3f}s")
                    print_info(f"  P95: {itl.get('p95', 0):.3f}s")

            if 'tps_stats' in data:
                tps = data['tps_stats']
                print_info(f"TPS (Tokens Per Second):")
                if tps:
                    print_info(f"  Mean: {tps.get('mean', 0):.2f}")
                    print_info(f"  Max: {tps.get('max', 0):.2f}")

            return data
        else:
            print_error(f"Failed to retrieve metrics (status: {response.status_code})")
            print_error(f"Response: {response.text[:200]}")
            return None

    except Exception as e:
        print_error(f"Failed to check streaming metrics: {e}")
        return None


def print_comprehensive_report(results: dict[str, Any]) -> int:
    """
    Print a comprehensive test report.

    Args:
        results: Dictionary containing all test results

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print_section("Step 8: Comprehensive Report")

    # Count successes and failures
    checks = [
        ("Server Ready", results.get('server_ready', False)),
        ("Non-Streaming Request", results.get('non_streaming_success', False)),
        ("Event Metrics Available", results.get('event_metrics') is not None),
        ("Events Published > 0",
         results.get('event_metrics', {}).get('events_published', 0) > 0),
        ("Error Metrics Available", results.get('error_metrics') is not None),
        ("Total Requests > 0",
         results.get('error_metrics', {}).get('total_requests', 0) > 0),
        ("Streaming Request", results.get('streaming_success', False)),
        ("Streaming Metrics Available", results.get('streaming_metrics') is not None),
        ("Total Streams > 0",
         results.get('streaming_metrics', {}).get('total_streams', 0) > 0),
    ]

    passed = sum(1 for _, success in checks if success)
    total = len(checks)

    print(f"{Colors.BOLD}Test Results Summary:{Colors.RESET}\n")

    for check_name, success in checks:
        if success:
            print_success(f"{check_name}")
        else:
            print_error(f"{check_name}")

    print(f"\n{Colors.BOLD}Overall: {passed}/{total} checks passed{Colors.RESET}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED!{Colors.RESET}")
        print(f"{Colors.GREEN}Events are flowing end-to-end correctly.{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED!{Colors.RESET}")
        print(f"{Colors.RED}Events are not flowing correctly through the system.{Colors.RESET}")
        print(f"{Colors.YELLOW}Check the logs above for details.{Colors.RESET}\n")
        return 1


def main() -> int:
    """
    Main test function.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("=" * 70)
    print("  End-to-End Event Flow Verification")
    print("=" * 70)
    print(f"{Colors.RESET}\n")

    base_url = "http://127.0.0.1:8765"
    results = {}

    # Step 1: Wait for server
    results['server_ready'] = wait_for_server(port=8765)
    if not results['server_ready']:
        print_error("Server is not running. Please start the server first:")
        print_info("  python -m fakeai --port 8765")
        return 1

    # Step 2: Non-streaming request
    non_streaming_response = send_non_streaming_request(base_url)
    results['non_streaming_success'] = non_streaming_response is not None
    results['non_streaming_response'] = non_streaming_response

    # Step 3: Wait for event processing
    wait_for_event_processing(delay=0.5)

    # Step 4: Check event metrics
    results['event_metrics'] = check_event_metrics(base_url)

    # Step 5: Check error metrics
    results['error_metrics'] = check_error_metrics(base_url)

    # Step 6: Streaming request
    results['streaming_success'] = send_streaming_request(base_url)

    # Wait a bit for streaming metrics to update
    time.sleep(0.3)

    # Step 7: Check streaming metrics
    results['streaming_metrics'] = check_streaming_metrics(base_url)

    # Step 8: Print comprehensive report
    exit_code = print_comprehensive_report(results)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
