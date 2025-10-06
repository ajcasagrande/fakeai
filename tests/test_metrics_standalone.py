#!/usr/bin/env python3
"""
Standalone tests for FakeAI Metrics functionality

Tests metrics functionality without importing the full app.
"""
#  SPDX-License-Identifier: Apache-2.0

import csv
import io
import os
import sys
import time

# Add parent directory to path for direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import only the metrics module
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
    assert "p50_latency" in header, "Should have p50_latency column"
    assert "p99_latency" in header, "Should have p99_latency column"

    print("✓ CSV export test passed")


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
    assert "uptime_seconds" in health, "Should have uptime"
    assert "metrics_summary" in health, "Should have metrics summary"
    assert "endpoints" in health, "Should have endpoints"

    # Verify metrics summary structure
    summary = health["metrics_summary"]
    assert "total_requests_per_second" in summary, "Should have total requests"
    assert "total_errors_per_second" in summary, "Should have total errors"
    assert "error_rate_percentage" in summary, "Should have error rate"
    assert "average_latency_seconds" in summary, "Should have average latency"
    assert "active_streams" in summary, "Should have active streams count"

    # Should be healthy with no errors
    assert health["status"] == "healthy", "Status should be healthy"
    assert (
        health["metrics_summary"]["error_rate_percentage"] == 0
    ), "Error rate should be 0"

    print("✓ Detailed health check test passed")


def test_latency_percentiles():
    """Test latency percentile calculations."""
    print("Testing latency percentiles...")

    tracker = MetricsTracker()

    endpoint = "/test/endpoint"

    # Track responses with known latencies
    latencies = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    for latency in latencies:
        tracker.track_request(endpoint)
        tracker.track_response(endpoint, latency=latency)

    # Get metrics
    metrics = tracker.get_metrics()
    stats = metrics["responses"][endpoint]

    # Verify percentiles are in reasonable ranges
    assert stats["p50"] >= 0.4, f"P50 should be >= 0.4, got {stats['p50']}"
    assert stats["p50"] <= 0.7, f"P50 should be <= 0.7, got {stats['p50']}"
    assert stats["p90"] >= 0.8, f"P90 should be >= 0.8, got {stats['p90']}"
    assert stats["p99"] >= 0.9, f"P99 should be >= 0.9, got {stats['p99']}"
    assert stats["min"] == 0.1, f"Min should be 0.1, got {stats['min']}"
    assert stats["max"] == 1.0, f"Max should be 1.0, got {stats['max']}"

    print("✓ Latency percentiles test passed")


def test_streaming_metrics():
    """Test streaming metrics tracking."""
    print("Testing streaming metrics...")

    tracker = MetricsTracker()

    stream_id = "test-stream"
    endpoint = "/v1/chat/completions"

    # Start stream and track first token with known timing
    tracker.start_stream(stream_id, endpoint)
    time.sleep(0.1)  # Wait 100ms
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
    assert "failed_streams" in stats, "Should have failed_streams"

    # Should have at least one completed stream
    assert stats["completed_streams"] > 0, "Should have completed streams"

    # Check TTFT
    ttft = stats.get("ttft", {})
    if ttft:
        assert ttft["avg"] >= 0.08, f"TTFT avg should be >= 0.08s, got {ttft['avg']}"
        assert ttft["avg"] <= 0.15, f"TTFT avg should be <= 0.15s, got {ttft['avg']}"

    print("✓ Streaming metrics test passed")


def test_prometheus_labels():
    """Test Prometheus format includes correct labels."""
    print("Testing Prometheus labels...")

    tracker = MetricsTracker()

    tracker.track_request("/v1/embeddings")
    tracker.track_response("/v1/embeddings", latency=0.05)

    prometheus_output = tracker.get_prometheus_metrics()

    # Verify labels are present
    assert (
        'endpoint="/v1/embeddings"' in prometheus_output
    ), "Should have endpoint labels"

    print("✓ Prometheus labels test passed")


def test_csv_data_rows():
    """Test CSV format contains correct data rows."""
    print("Testing CSV data rows...")

    tracker = MetricsTracker()

    # Track metrics for multiple endpoints
    endpoints = ["/v1/chat/completions", "/v1/embeddings", "/v1/completions"]

    for endpoint in endpoints:
        tracker.track_request(endpoint)
        tracker.track_response(endpoint, latency=0.1)
        tracker.track_tokens(endpoint, 50)

    csv_output = tracker.get_csv_metrics()
    reader = csv.reader(io.StringIO(csv_output))
    rows = list(reader)

    # Should have header + multiple data rows
    assert len(rows) > 1, "Should have data rows"

    # Check that we have requests, responses, and tokens rows
    metric_types = [row[0] for row in rows[1:]]
    assert "requests" in metric_types, "Should have requests rows"
    assert "responses" in metric_types, "Should have responses rows"
    assert "tokens" in metric_types, "Should have tokens rows"

    print("✓ CSV data rows test passed")


def test_error_tracking():
    """Test error rate tracking."""
    print("Testing error tracking...")

    tracker = MetricsTracker()

    endpoint = "/v1/chat/completions"

    # Track some errors
    for _ in range(3):
        tracker.track_error(endpoint)

    # Get metrics
    metrics = tracker.get_metrics()
    error_rate = metrics["errors"][endpoint]["rate"]

    # Should have positive error rate
    assert error_rate > 0, "Should have positive error rate"

    print("✓ Error tracking test passed")


def run_all_tests():
    """Run all standalone tests."""
    print("\n" + "=" * 60)
    print("Running FakeAI Metrics Standalone Tests")
    print("=" * 60 + "\n")

    tests = [
        test_prometheus_export,
        test_csv_export,
        test_detailed_health,
        test_latency_percentiles,
        test_streaming_metrics,
        test_prometheus_labels,
        test_csv_data_rows,
        test_error_tracking,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
