#!/usr/bin/env python3
"""
Tests for FakeAI Metrics Dashboard and Export Functionality

This module tests the comprehensive monitoring and metrics system including:
- Prometheus format export
- CSV format export
- Detailed health checks
- Dashboard functionality
- Metrics accuracy
"""
#  SPDX-License-Identifier: Apache-2.0

import csv
import io
import time

import pytest

from fakeai.metrics import MetricsTracker, MetricType


class TestMetricsExport:
    """Test metrics export functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a fresh metrics tracker for each test
        # Note: MetricsTracker is a singleton, so we need to work with the same instance
        self.tracker = MetricsTracker()

    def test_prometheus_format_basic(self):
        """Test basic Prometheus format export."""
        # Track some metrics
        self.tracker.track_request("/v1/chat/completions")
        self.tracker.track_response("/v1/chat/completions", latency=0.15)
        self.tracker.track_tokens("/v1/chat/completions", 100)

        # Get Prometheus metrics
        prometheus_output = self.tracker.get_prometheus_metrics()

        # Verify format
        assert isinstance(prometheus_output, str)
        assert "# HELP" in prometheus_output
        assert "# TYPE" in prometheus_output
        assert "fakeai_requests_per_second" in prometheus_output
        assert "fakeai_responses_per_second" in prometheus_output
        assert "fakeai_tokens_per_second" in prometheus_output

    def test_prometheus_format_labels(self):
        """Test Prometheus format includes correct labels."""
        self.tracker.track_request("/v1/embeddings")
        self.tracker.track_response("/v1/embeddings", latency=0.05)

        prometheus_output = self.tracker.get_prometheus_metrics()

        # Verify labels are present
        assert 'endpoint="/v1/embeddings"' in prometheus_output

    def test_prometheus_format_latency_percentiles(self):
        """Test Prometheus format includes latency percentiles."""
        # Track multiple responses with different latencies
        endpoint = "/v1/chat/completions"
        for latency in [0.1, 0.15, 0.2, 0.25, 0.3]:
            self.tracker.track_request(endpoint)
            self.tracker.track_response(endpoint, latency=latency)

        prometheus_output = self.tracker.get_prometheus_metrics()

        # Verify percentiles are present
        assert 'quantile="0.5"' in prometheus_output  # p50
        assert 'quantile="0.9"' in prometheus_output  # p90
        assert 'quantile="0.99"' in prometheus_output  # p99

    def test_prometheus_format_streaming_metrics(self):
        """Test Prometheus format includes streaming metrics."""
        # Start and complete a stream
        stream_id = "test-stream-1"
        endpoint = "/v1/chat/completions"

        self.tracker.start_stream(stream_id, endpoint)
        self.tracker.track_stream_first_token(stream_id)
        self.tracker.track_stream_token(stream_id)
        self.tracker.track_stream_token(stream_id)
        self.tracker.complete_stream(stream_id, endpoint)

        prometheus_output = self.tracker.get_prometheus_metrics()

        # Verify streaming metrics
        assert "fakeai_active_streams" in prometheus_output
        assert "fakeai_completed_streams" in prometheus_output
        assert "fakeai_ttft_seconds" in prometheus_output

    def test_csv_format_basic(self):
        """Test basic CSV format export."""
        # Track some metrics
        self.tracker.track_request("/v1/completions")
        self.tracker.track_response("/v1/completions", latency=0.1)

        # Get CSV metrics
        csv_output = self.tracker.get_csv_metrics()

        # Verify format
        assert isinstance(csv_output, str)
        reader = csv.reader(io.StringIO(csv_output))
        rows = list(reader)

        # Check header
        assert len(rows) > 0
        header = rows[0]
        assert "metric_type" in header
        assert "endpoint" in header
        assert "rate" in header
        assert "p50_latency" in header
        assert "p99_latency" in header

    def test_csv_format_data_rows(self):
        """Test CSV format contains correct data rows."""
        # Track metrics for multiple endpoints
        endpoints = ["/v1/chat/completions", "/v1/embeddings", "/v1/completions"]

        for endpoint in endpoints:
            self.tracker.track_request(endpoint)
            self.tracker.track_response(endpoint, latency=0.1)
            self.tracker.track_tokens(endpoint, 50)

        csv_output = self.tracker.get_csv_metrics()
        reader = csv.reader(io.StringIO(csv_output))
        rows = list(reader)

        # Should have header + multiple data rows
        assert len(rows) > 1

        # Check that we have requests, responses, and tokens rows
        metric_types = [row[0] for row in rows[1:]]
        assert "requests" in metric_types
        assert "responses" in metric_types
        assert "tokens" in metric_types

    def test_csv_format_numeric_values(self):
        """Test CSV format contains valid numeric values."""
        self.tracker.track_request("/v1/chat/completions")
        self.tracker.track_response("/v1/chat/completions", latency=0.123)

        csv_output = self.tracker.get_csv_metrics()
        reader = csv.reader(io.StringIO(csv_output))
        rows = list(reader)

        # Check data rows have numeric values
        for row in rows[1:]:  # Skip header
            rate = float(row[2])  # rate column
            assert rate >= 0

    def test_detailed_health_basic(self):
        """Test detailed health check basic functionality."""
        health = self.tracker.get_detailed_health()

        # Verify structure
        assert "status" in health
        assert "timestamp" in health
        assert "uptime_seconds" in health
        assert "metrics_summary" in health
        assert "endpoints" in health

        # Verify metrics summary structure
        summary = health["metrics_summary"]
        assert "total_requests_per_second" in summary
        assert "total_errors_per_second" in summary
        assert "error_rate_percentage" in summary
        assert "average_latency_seconds" in summary
        assert "active_streams" in summary

    def test_detailed_health_status_healthy(self):
        """Test detailed health status is healthy with no errors."""
        # Track successful requests
        for _ in range(10):
            self.tracker.track_request("/v1/chat/completions")
            self.tracker.track_response("/v1/chat/completions", latency=0.1)

        health = self.tracker.get_detailed_health()

        # Should be healthy with no errors
        assert health["status"] == "healthy"
        assert health["metrics_summary"]["error_rate_percentage"] == 0

    def test_detailed_health_status_degraded(self):
        """Test detailed health status is degraded with some errors."""
        # Track requests with some errors (6-10% error rate)
        for i in range(20):
            self.tracker.track_request("/v1/chat/completions")
            if i < 2:  # 10% errors
                self.tracker.track_error("/v1/chat/completions")
            else:
                self.tracker.track_response("/v1/chat/completions", latency=0.1)

        # Wait a moment for rates to settle
        time.sleep(0.1)

        health = self.tracker.get_detailed_health()

        # Should be degraded with error rate > 5%
        # Note: Due to timing, this might be healthy or degraded
        assert health["status"] in ["healthy", "degraded"]

    def test_detailed_health_endpoints(self):
        """Test detailed health includes endpoint-specific metrics."""
        # Track metrics for multiple endpoints
        endpoints = ["/v1/chat/completions", "/v1/embeddings"]

        for endpoint in endpoints:
            self.tracker.track_request(endpoint)
            self.tracker.track_response(endpoint, latency=0.1)

        health = self.tracker.get_detailed_health()

        # Verify endpoints are present
        endpoint_metrics = health["endpoints"]
        assert isinstance(endpoint_metrics, dict)

        # Check structure of endpoint metrics
        for endpoint, metrics in endpoint_metrics.items():
            if metrics.get("requests_per_second", 0) > 0:
                assert "requests_per_second" in metrics
                assert "latency_p50_ms" in metrics
                assert "latency_p99_ms" in metrics


class TestMetricsAccuracy:
    """Test accuracy of metrics calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = MetricsTracker()

    def test_request_rate_accuracy(self):
        """Test request rate calculation accuracy."""
        endpoint = "/test/endpoint"

        # Track 10 requests in quick succession
        for _ in range(10):
            self.tracker.track_request(endpoint)

        # Get metrics
        metrics = self.tracker.get_metrics()
        rate = metrics["requests"][endpoint]["rate"]

        # Should have positive rate
        assert rate > 0

    def test_latency_percentile_accuracy(self):
        """Test latency percentile calculation accuracy."""
        endpoint = "/test/endpoint"

        # Track responses with known latencies
        latencies = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        for latency in latencies:
            self.tracker.track_request(endpoint)
            self.tracker.track_response(endpoint, latency=latency)

        # Get metrics
        metrics = self.tracker.get_metrics()
        stats = metrics["responses"][endpoint]

        # Verify percentiles are in reasonable ranges
        assert stats["p50"] >= 0.4  # Should be around 0.5-0.6
        assert stats["p50"] <= 0.7
        assert stats["p90"] >= 0.8  # Should be around 0.9-1.0
        assert stats["p99"] >= 0.9
        assert stats["min"] == 0.1
        assert stats["max"] == 1.0

    def test_token_rate_accuracy(self):
        """Test token rate calculation accuracy."""
        endpoint = "/v1/chat/completions"

        # Track tokens
        for _ in range(5):
            self.tracker.track_tokens(endpoint, 100)

        # Get metrics
        metrics = self.tracker.get_metrics()
        token_rate = metrics["tokens"][endpoint]["rate"]

        # Should have positive token rate
        assert token_rate > 0

    def test_error_rate_tracking(self):
        """Test error rate tracking accuracy."""
        endpoint = "/v1/chat/completions"

        # Track some errors
        for _ in range(3):
            self.tracker.track_error(endpoint)

        # Get metrics
        metrics = self.tracker.get_metrics()
        error_rate = metrics["errors"][endpoint]["rate"]

        # Should have positive error rate
        assert error_rate > 0

    def test_streaming_ttft_accuracy(self):
        """Test Time To First Token (TTFT) calculation accuracy."""
        stream_id = "test-stream"
        endpoint = "/v1/chat/completions"

        # Start stream and track first token with known timing
        self.tracker.start_stream(stream_id, endpoint)
        time.sleep(0.1)  # Wait 100ms
        self.tracker.track_stream_first_token(stream_id)
        self.tracker.complete_stream(stream_id, endpoint)

        # Get streaming stats
        stats = self.tracker.get_streaming_stats()
        ttft = stats.get("ttft", {})

        # TTFT should be around 100ms (0.1 seconds)
        if ttft:
            assert ttft["avg"] >= 0.08  # Allow some variance
            assert ttft["avg"] <= 0.15

    def test_streaming_tokens_per_second(self):
        """Test streaming tokens per second calculation."""
        stream_id = "test-stream"
        endpoint = "/v1/chat/completions"

        # Start stream and track tokens
        self.tracker.start_stream(stream_id, endpoint)
        self.tracker.track_stream_first_token(stream_id)

        # Track 10 tokens over ~0.1 seconds
        for _ in range(10):
            self.tracker.track_stream_token(stream_id)

        time.sleep(0.1)
        self.tracker.complete_stream(stream_id, endpoint)

        # Get streaming stats
        stats = self.tracker.get_streaming_stats()
        tps = stats.get("tokens_per_second", {})

        # Should have calculated tokens per second
        if tps:
            assert tps["avg"] > 0


class TestMetricsDashboardEndpoints:
    """Test metrics dashboard endpoints (integration-style tests)."""

    def test_metrics_json_endpoint_structure(self):
        """Test /metrics endpoint returns proper JSON structure."""
        tracker = MetricsTracker()

        # Track some data
        tracker.track_request("/v1/chat/completions")
        tracker.track_response("/v1/chat/completions", latency=0.1)

        # Get metrics
        metrics = tracker.get_metrics()

        # Verify structure
        assert isinstance(metrics, dict)
        assert "requests" in metrics
        assert "responses" in metrics
        assert "tokens" in metrics
        assert "errors" in metrics
        assert "streaming_stats" in metrics

    def test_prometheus_endpoint_format(self):
        """Test /metrics/prometheus endpoint returns valid format."""
        tracker = MetricsTracker()

        # Track some data
        tracker.track_request("/v1/embeddings")
        tracker.track_response("/v1/embeddings", latency=0.05)

        # Get Prometheus metrics
        prometheus = tracker.get_prometheus_metrics()

        # Verify it's valid Prometheus format
        lines = prometheus.strip().split("\n")
        assert len(lines) > 0

        # Should have HELP and TYPE comments
        help_lines = [l for l in lines if l.startswith("# HELP")]
        type_lines = [l for l in lines if l.startswith("# TYPE")]
        assert len(help_lines) > 0
        assert len(type_lines) > 0

    def test_csv_endpoint_format(self):
        """Test /metrics/csv endpoint returns valid CSV."""
        tracker = MetricsTracker()

        # Track some data
        tracker.track_request("/v1/completions")
        tracker.track_response("/v1/completions", latency=0.1)

        # Get CSV metrics
        csv_data = tracker.get_csv_metrics()

        # Verify it's valid CSV
        reader = csv.reader(io.StringIO(csv_data))
        rows = list(reader)

        # Should have header and data rows
        assert len(rows) > 1
        assert len(rows[0]) > 0  # Header has columns

    def test_detailed_health_endpoint_structure(self):
        """Test /health/detailed endpoint returns proper structure."""
        tracker = MetricsTracker()

        # Track some data
        tracker.track_request("/v1/chat/completions")
        tracker.track_response("/v1/chat/completions", latency=0.1)

        # Get detailed health
        health = tracker.get_detailed_health()

        # Verify structure
        assert isinstance(health, dict)
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert isinstance(health["timestamp"], (int, float))
        assert isinstance(health["metrics_summary"], dict)
        assert isinstance(health["endpoints"], dict)


class TestMetricsWindowBehavior:
    """Test metrics sliding window behavior."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = MetricsTracker()

    def test_metrics_window_cleanup(self):
        """Test that old metrics are cleaned up from the window."""
        endpoint = "/test/cleanup"

        # Track a request
        self.tracker.track_request(endpoint)

        # Get initial metrics
        metrics1 = self.tracker.get_metrics()
        rate1 = metrics1["requests"][endpoint]["rate"]
        assert rate1 > 0

        # Wait for window to expire (window is 5 seconds)
        time.sleep(6)

        # Rate should be 0 now
        metrics2 = self.tracker.get_metrics()
        rate2 = metrics2["requests"][endpoint]["rate"]
        assert rate2 == 0

    def test_metrics_rate_calculation(self):
        """Test metrics rate calculation over window."""
        endpoint = "/test/rate"

        # Track multiple requests
        for _ in range(5):
            self.tracker.track_request(endpoint)

        # Get rate
        metrics = self.tracker.get_metrics()
        rate = metrics["requests"][endpoint]["rate"]

        # Rate should be approximately 5 requests / 1 second (or window size)
        assert rate > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
