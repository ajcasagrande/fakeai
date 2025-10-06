#!/usr/bin/env python3
"""
Tests for numpy-based sliding window metrics with smooth rate calculations.

These tests verify that the metrics window properly:
1. Tracks events with timestamps
2. Calculates rates that go up and down smoothly
3. Handles sliding window cleanup correctly
4. Uses numpy for efficient calculations
"""

import asyncio
import time

import numpy as np
import pytest

from fakeai.metrics import MetricsWindow


class TestNumpyMetricsWindow:
    """Test numpy-based sliding window implementation."""

    def test_empty_window(self):
        """Test that empty window returns 0 rate."""
        window = MetricsWindow(window_size=5.0)
        assert window.get_rate() == 0.0

    def test_single_event(self):
        """Test rate calculation with single event."""
        window = MetricsWindow(window_size=5.0)
        window.add(1)

        # Should have rate close to 1000 rps since time_span is very small
        rate = window.get_rate()
        assert rate > 0.0

    def test_rate_increases_with_events(self):
        """Test that rate increases as more events are added quickly."""
        window = MetricsWindow(window_size=5.0)

        # Add 100 events rapidly
        for _ in range(100):
            window.add(1)

        # Rate should be high (many events in short time)
        rate = window.get_rate()
        assert rate > 50.0  # Should be much higher than this

    def test_rate_decreases_over_time(self):
        """Test that rate decreases as window slides forward in time."""
        window = MetricsWindow(window_size=2.0)  # 2 second window

        # Add 100 events
        for _ in range(100):
            window.add(1)

        initial_rate = window.get_rate()
        assert initial_rate > 0.0

        # Wait 1 second and check rate (should still have events)
        time.sleep(1.0)
        mid_rate = window.get_rate()

        # Wait another 1.5 seconds (total 2.5s, past window)
        time.sleep(1.5)
        final_rate = window.get_rate()

        # Rate should decrease as events age out of window
        assert final_rate < mid_rate < initial_rate

        # After window expires, rate should be 0
        assert final_rate == 0.0

    def test_sliding_window_cleanup(self):
        """Test that old events are cleaned up from window."""
        window = MetricsWindow(window_size=1.0)  # 1 second window

        # Add events
        window.add(10)
        assert len(window.timestamps) == 1

        # Wait for window to expire
        time.sleep(1.1)

        # Add another event (triggers cleanup)
        window.add(1)

        # Old event should be cleaned up
        assert len(window.timestamps) == 1

    def test_latency_stats_empty(self):
        """Test latency stats with no data."""
        window = MetricsWindow(window_size=5.0)
        stats = window.get_latency_stats()

        assert stats["avg"] == 0.0
        assert stats["min"] == 0.0
        assert stats["max"] == 0.0
        assert stats["p50"] == 0.0
        assert stats["p90"] == 0.0
        assert stats["p99"] == 0.0

    def test_latency_stats_with_data(self):
        """Test latency stats calculation with numpy."""
        window = MetricsWindow(window_size=5.0)

        # Add latencies
        latencies = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        for lat in latencies:
            window.add_latency(lat)

        stats = window.get_latency_stats()

        # Check stats are reasonable
        assert stats["min"] == 0.1
        assert stats["max"] == 1.0
        assert 0.5 <= stats["avg"] <= 0.6  # Close to 0.55
        assert stats["p50"] == pytest.approx(0.5, abs=0.1)
        assert stats["p90"] >= stats["p50"]
        assert stats["p99"] >= stats["p90"]

    def test_numpy_percentiles(self):
        """Test that numpy percentile calculations are accurate."""
        window = MetricsWindow(window_size=10.0)

        # Add 100 latency values
        for i in range(100):
            window.add_latency(i / 100.0)  # 0.00 to 0.99

        stats = window.get_latency_stats()

        # Verify percentiles
        assert stats["p50"] == pytest.approx(0.495, abs=0.01)
        assert stats["p90"] == pytest.approx(0.895, abs=0.01)
        assert stats["p99"] == pytest.approx(0.985, abs=0.01)

    def test_concurrent_access(self):
        """Test thread-safe concurrent access to metrics window."""
        window = MetricsWindow(window_size=5.0)

        def add_events():
            for _ in range(100):
                window.add(1)

        # Run multiple threads
        import threading

        threads = [threading.Thread(target=add_events) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have 500 events total
        rate = window.get_rate()
        assert rate > 0.0

        # Check data integrity
        assert len(window.timestamps) == 500
        assert np.sum(window.values) == 500

    def test_max_samples_limit(self):
        """Test that max_samples limit is enforced."""
        window = MetricsWindow(window_size=60.0, max_samples=100)

        # Add more than max_samples
        for _ in range(200):
            window.add(1)

        # Should be limited to max_samples
        assert len(window.timestamps) <= 100

    def test_rate_calculation_accuracy(self):
        """Test rate calculation is accurate over known time period."""
        window = MetricsWindow(window_size=10.0)

        start_time = time.time()

        # Add 50 events over ~0.5 seconds
        for _ in range(50):
            window.add(1)
            time.sleep(0.01)

        elapsed = time.time() - start_time
        rate = window.get_rate()

        # Rate should be approximately 50 / elapsed
        expected_rate = 50.0 / elapsed
        assert rate == pytest.approx(expected_rate, rel=0.2)  # 20% tolerance

    def test_window_size_configuration(self):
        """Test different window sizes."""
        # Short window
        short_window = MetricsWindow(window_size=1.0)
        short_window.add(10)
        time.sleep(0.5)
        short_rate = short_window.get_rate()

        # Long window
        long_window = MetricsWindow(window_size=60.0)
        long_window.add(10)
        time.sleep(0.5)
        long_rate = long_window.get_rate()

        # Both should have positive rates
        assert short_rate > 0.0
        assert long_rate > 0.0

    def test_vectorized_operations(self):
        """Test that numpy vectorized operations are used."""
        window = MetricsWindow(window_size=5.0)

        # Add many events
        for _ in range(1000):
            window.add(1)

        # Verify numpy arrays are used
        assert isinstance(window.timestamps, np.ndarray)
        assert isinstance(window.values, np.ndarray)
        assert window.timestamps.dtype == np.float64
        assert window.values.dtype == np.float64

    def test_smooth_rate_changes(self):
        """Test that rates change smoothly over time (up and down)."""
        window = MetricsWindow(window_size=2.0)
        rates = []

        # Add burst of events
        for _ in range(100):
            window.add(1)
        rates.append(window.get_rate())

        # Wait and measure (rate should decrease)
        time.sleep(0.5)
        rates.append(window.get_rate())

        # Add more events (rate should increase)
        for _ in range(100):
            window.add(1)
        rates.append(window.get_rate())

        # Wait again (rate should decrease)
        time.sleep(0.5)
        rates.append(window.get_rate())

        # Verify smooth transitions
        assert rates[0] > 0  # Initial burst
        assert rates[2] > rates[1]  # Increased after second burst
        assert rates[3] < rates[2]  # Decreased after waiting

    def test_get_stats(self):
        """Test get_stats returns both rate and latency stats."""
        window = MetricsWindow(window_size=5.0)

        # Add events and latencies
        for i in range(10):
            window.add(1)
            window.add_latency(0.1 * i)

        stats = window.get_stats()

        # Should include rate
        assert "rate" in stats
        assert stats["rate"] > 0.0

        # Should include latency stats
        assert "avg" in stats
        assert "min" in stats
        assert "max" in stats
        assert "p50" in stats
        assert "p90" in stats
        assert "p99" in stats


@pytest.mark.asyncio
async def test_async_metrics_tracking():
    """Test metrics window in async context."""
    window = MetricsWindow(window_size=5.0)

    async def add_events_async():
        for _ in range(50):
            window.add(1)
            await asyncio.sleep(0.01)

    # Run async task
    await add_events_async()

    rate = window.get_rate()
    assert rate > 0.0
    assert len(window.timestamps) == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
