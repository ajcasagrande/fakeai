#!/usr/bin/env python3
"""
Direct test of FakeAI Metrics functionality

Tests metrics functionality with direct import.
"""

import csv
import io
import time

# Import directly
from fakeai.metrics import MetricsTracker


def test_prometheus_export():
    """Test Prometheus format export."""
    print("Testing Prometheus export...")

    tracker = MetricsTracker()

    # Track some metrics
    tracker.track_request("/v1/chat/completions")
    tracker.track_response("/v1/chat/completions", latency=0.15)
    tracker.track_tokens("/v1/chat/completions", 100)

    # Get Prometheus metrics
    prometheus_output = tracker.get_prometheus_metrics()

    # Verify format
    assert isinstance(prometheus_output, str), "Prometheus output should be string"
    assert "# HELP" in prometheus_output, "Should have HELP comments"
    assert "# TYPE" in prometheus_output, "Should have TYPE comments"
    assert (
        "fakeai_requests_per_second" in prometheus_output
    ), "Should have request metrics"
    assert (
        "fakeai_responses_per_second" in prometheus_output
    ), "Should have response metrics"
    assert "fakeai_tokens_per_second" in prometheus_output, "Should have token metrics"

    print("✓ Prometheus export test passed")
    return True


def test_csv_export():
    """Test CSV format export."""
    print("Testing CSV export...")

    tracker = MetricsTracker()

    # Track some metrics
    tracker.track_request("/v1/completions")
    tracker.track_response("/v1/completions", latency=0.1)

    # Get CSV metrics
    csv_output = tracker.get_csv_metrics()

    # Verify format
    assert isinstance(csv_output, str), "CSV output should be string"
    reader = csv.reader(io.StringIO(csv_output))
    rows = list(reader)

    # Check header
    assert len(rows) > 0, "Should have rows"
    header = rows[0]
    assert "metric_type" in header, "Should have metric_type column"
    assert "endpoint" in header, "Should have endpoint column"
    assert "rate" in header, "Should have rate column"

    print("✓ CSV export test passed")
    return True


def test_detailed_health():
    """Test detailed health check."""
    print("Testing detailed health check...")

    tracker = MetricsTracker()

    # Track some metrics
    for _ in range(10):
        tracker.track_request("/v1/chat/completions")
        tracker.track_response("/v1/chat/completions", latency=0.1)

    # Get detailed health
    health = tracker.get_detailed_health()

    # Verify structure
    assert "status" in health, "Should have status"
    assert "timestamp" in health, "Should have timestamp"
    assert "metrics_summary" in health, "Should have metrics summary"
    assert "endpoints" in health, "Should have endpoints"

    print("✓ Detailed health check test passed")
    return True


def test_streaming_metrics():
    """Test streaming metrics tracking."""
    print("Testing streaming metrics...")

    tracker = MetricsTracker()

    stream_id = "test-stream"
    endpoint = "/v1/chat/completions"

    # Start stream
    tracker.start_stream(stream_id, endpoint)
    time.sleep(0.1)
    tracker.track_stream_first_token(stream_id)

    # Track some tokens
    for _ in range(10):
        tracker.track_stream_token(stream_id)

    time.sleep(0.05)
    tracker.complete_stream(stream_id, endpoint)

    # Get streaming stats
    stats = tracker.get_streaming_stats()

    assert "active_streams" in stats, "Should have active_streams"
    assert "completed_streams" in stats, "Should have completed_streams"
    assert stats["completed_streams"] > 0, "Should have completed streams"

    print("✓ Streaming metrics test passed")
    return True


def run_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("FakeAI Metrics Dashboard Tests")
    print("=" * 60 + "\n")

    tests = [
        test_prometheus_export,
        test_csv_export,
        test_detailed_health,
        test_streaming_metrics,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            import traceback

            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")

    return failed == 0


if __name__ == "__main__":
    import sys

    success = run_tests()
    sys.exit(0 if success else 1)
