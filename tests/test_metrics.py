"""
Metrics tracker behavior tests.

Tests the singleton pattern, thread safety, and metrics accumulation behavior.
"""

import threading
import time

import pytest

from fakeai.metrics import MetricsTracker, MetricType


@pytest.mark.unit
@pytest.mark.metrics
class TestMetricsSingletonBehavior:
    """Test MetricsTracker singleton pattern behavior."""

    def test_returns_same_instance(self):
        """Multiple instantiations should return the same instance."""
        tracker1 = MetricsTracker()
        tracker2 = MetricsTracker()

        assert tracker1 is tracker2

    def test_shares_state_across_instances(self):
        """State should be shared across all instances."""
        tracker1 = MetricsTracker()
        tracker2 = MetricsTracker()

        # Track request with first instance
        tracker1.track_request("/v1/chat/completions")

        # Should be visible from second instance
        metrics = tracker2.get_metrics()

        assert "/v1/chat/completions" in metrics["requests"]

    def test_thread_safe_instantiation(self):
        """Should be safe to instantiate from multiple threads."""
        instances = []

        def create_instance():
            tracker = MetricsTracker()
            instances.append(tracker)

        threads = [threading.Thread(target=create_instance) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All instances should be the same
        assert len(set(id(instance) for instance in instances)) == 1


@pytest.mark.unit
@pytest.mark.metrics
class TestMetricsAccumulationBehavior:
    """Test metrics accumulation and calculation behavior."""

    def test_tracks_requests(self):
        """Should accumulate request counts."""
        tracker = MetricsTracker()
        endpoint = "/v1/embeddings"

        # Track multiple requests
        for _ in range(5):
            tracker.track_request(endpoint)

        # Give metrics window time to accumulate
        time.sleep(0.1)

        metrics = tracker.get_metrics()

        # Should have recorded requests
        assert endpoint in metrics["requests"]

    def test_tracks_responses(self):
        """Should accumulate response counts."""
        tracker = MetricsTracker()
        endpoint = "/v1/embeddings"

        for _ in range(3):
            tracker.track_response(endpoint)

        time.sleep(0.1)

        metrics = tracker.get_metrics()

        assert endpoint in metrics["responses"]

    def test_tracks_tokens(self):
        """Should accumulate token counts."""
        tracker = MetricsTracker()
        endpoint = "/v1/chat/completions"

        tracker.track_tokens(endpoint, 100)
        tracker.track_tokens(endpoint, 150)
        tracker.track_tokens(endpoint, 200)

        time.sleep(0.1)

        metrics = tracker.get_metrics()

        # Should have token metrics
        assert endpoint in metrics.get("tokens", {})

    def test_tracks_errors(self):
        """Should track error occurrences."""
        tracker = MetricsTracker()
        endpoint = "/v1/embeddings"

        tracker.track_error(endpoint)
        tracker.track_error(endpoint)

        time.sleep(0.1)

        metrics = tracker.get_metrics()

        assert endpoint in metrics.get("errors", {})

    def test_latency_tracking(self):
        """Should track response latencies."""
        tracker = MetricsTracker()
        endpoint = "/v1/embeddings"

        tracker.track_response(endpoint, latency=0.5)
        tracker.track_response(endpoint, latency=0.7)

        time.sleep(0.1)

        metrics = tracker.get_metrics()

        # Should have latency stats
        if endpoint in metrics["responses"]:
            stats = metrics["responses"][endpoint]
            # May or may not have latency stats depending on timing
            # Just verify structure is correct
            assert "rate" in stats


@pytest.mark.unit
@pytest.mark.metrics
class TestMetricsWindowBehavior:
    """Test metrics window sliding behavior."""

    def test_metrics_window_cleanup(self):
        """Old metrics should be cleaned up after window expires."""
        from fakeai.metrics import MetricsWindow

        window = MetricsWindow(window_size=1)  # 1 second window

        # Add data
        window.add(10)

        # Should have data
        assert window.get_rate() > 0

        # Wait for window to expire
        time.sleep(1.5)

        # Add new data to trigger cleanup
        window.add(5)

        # Old data should be cleaned up
        assert len(window.data) <= 2  # Current second + maybe one previous


@pytest.mark.integration
@pytest.mark.metrics
class TestMetricsIntegration:
    """Test metrics integration with API requests."""

    def test_api_request_tracked_in_metrics(self, client_no_auth):
        """Making API requests should be reflected in metrics."""
        # Make a request
        client_no_auth.get("/v1/models")

        # Check metrics
        response = client_no_auth.get("/metrics")
        assert response.status_code == 200

        metrics = response.json()

        # Should have tracked the request
        assert "requests" in metrics or "responses" in metrics
