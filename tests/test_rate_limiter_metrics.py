"""
Tests for rate limiter metrics tracking module.

This test suite validates detailed rate limiting behavior and patterns tracking,
including per-key metrics, quota tracking, throttling analytics, and abuse detection.
"""

#  SPDX-License-Identifier: Apache-2.0

import time
from unittest.mock import patch

import pytest

from fakeai.rate_limiter_metrics import KeyMetrics, RateLimiterMetrics, ThrottleEvent


@pytest.fixture
def metrics():
    """Create a fresh RateLimiterMetrics instance for each test."""
    # Reset singleton
    RateLimiterMetrics._instance = None
    metrics_instance = RateLimiterMetrics()
    yield metrics_instance
    # Cleanup
    metrics_instance.reset()


class TestRateLimiterMetrics:
    """Test suite for RateLimiterMetrics class."""

    def test_singleton_pattern(self):
        """Test that RateLimiterMetrics follows singleton pattern."""
        instance1 = RateLimiterMetrics()
        instance2 = RateLimiterMetrics()
        assert instance1 is instance2

    def test_assign_tier(self, metrics):
        """Test assigning a tier to an API key."""
        metrics.assign_tier("test-key-1", "tier-2")

        stats = metrics.get_key_stats("test-key-1")
        assert stats["tier"] == "tier-2"
        assert stats["api_key"] == "test-key-1"

    def test_record_allowed_request(self, metrics):
        """Test recording an allowed request."""
        metrics.assign_tier("test-key", "tier-1")
        metrics.record_request_attempt(
            api_key="test-key",
            allowed=True,
            tokens=100,
            rpm_limit=500,
            tpm_limit=30000,
        )

        stats = metrics.get_key_stats("test-key")
        assert stats["requests"]["total_attempted"] == 1
        assert stats["requests"]["total_allowed"] == 1
        assert stats["requests"]["total_throttled"] == 0
        assert stats["tokens"]["total_consumed"] == 100
        assert stats["requests"]["success_rate"] == 1.0

    def test_record_throttled_request(self, metrics):
        """Test recording a throttled request."""
        metrics.assign_tier("test-key", "tier-1")
        metrics.record_request_attempt(
            api_key="test-key",
            allowed=False,
            tokens=100,
            rpm_limit=500,
            tpm_limit=30000,
        )

        stats = metrics.get_key_stats("test-key")
        assert stats["requests"]["total_attempted"] == 1
        assert stats["requests"]["total_allowed"] == 0
        assert stats["requests"]["total_throttled"] == 1
        assert stats["tokens"]["total_consumed"] == 0
        assert stats["requests"]["throttle_rate"] == 1.0

    def test_record_throttle_event(self, metrics):
        """Test recording a throttle event with retry-after time."""
        metrics.assign_tier("test-key", "tier-1")
        metrics.record_throttle(
            api_key="test-key",
            retry_after_ms=5000.0,
            requested_tokens=100,
            rpm_exceeded=True,
            tpm_exceeded=False,
        )

        stats = metrics.get_key_stats("test-key")
        assert stats["throttling"]["total_throttle_time_ms"] == 5000.0
        assert stats["throttling"]["avg_retry_after_ms"] == 5000.0
        assert stats["throttling"]["throttle_event_count"] == 1

    def test_multiple_throttle_events(self, metrics):
        """Test recording multiple throttle events and calculating averages."""
        metrics.assign_tier("test-key", "tier-1")

        # Record multiple throttle events
        for retry_after in [1000, 2000, 3000, 4000, 5000]:
            metrics.record_throttle(
                api_key="test-key",
                retry_after_ms=float(retry_after),
                requested_tokens=50,
                rpm_exceeded=True,
                tpm_exceeded=False,
            )

        stats = metrics.get_key_stats("test-key")
        assert stats["throttling"]["total_throttle_time_ms"] == 15000.0
        assert stats["throttling"]["avg_retry_after_ms"] == 3000.0
        assert stats["throttling"]["throttle_event_count"] == 5

    def test_token_efficiency_calculation(self, metrics):
        """Test calculation of token efficiency (consumed vs requested)."""
        metrics.assign_tier("test-key", "tier-1")

        # Allow 3 requests, throttle 1 request
        for _ in range(3):
            metrics.record_request_attempt(
                api_key="test-key",
                allowed=True,
                tokens=100,
                rpm_limit=500,
                tpm_limit=30000,
            )

        metrics.record_request_attempt(
            api_key="test-key",
            allowed=False,
            tokens=100,
            rpm_limit=500,
            tpm_limit=30000,
        )

        stats = metrics.get_key_stats("test-key")
        # 300 consumed / 400 requested = 0.75
        assert stats["tokens"]["efficiency"] == 0.75
        assert stats["tokens"]["total_consumed"] == 300
        assert stats["tokens"]["total_requested"] == 400

    def test_burst_detection(self, metrics):
        """Test burst request detection (multiple requests in 1 second)."""
        metrics.assign_tier("test-key", "tier-1")

        # Simulate burst of 5 requests in rapid succession
        for _ in range(5):
            metrics.record_request_attempt(
                api_key="test-key",
                allowed=True,
                tokens=50,
                rpm_limit=500,
                tpm_limit=30000,
            )
            time.sleep(0.1)  # 100ms between requests

        stats = metrics.get_key_stats("test-key")
        # Should detect burst (all 5 requests within 1 second)
        assert stats["usage_patterns"]["current_burst_requests"] >= 5

    def test_peak_rpm_tracking(self, metrics):
        """Test tracking of peak RPM over time."""
        metrics.assign_tier("test-key", "tier-1")

        # Make requests over a period
        for _ in range(10):
            metrics.record_request_attempt(
                api_key="test-key",
                allowed=True,
                tokens=50,
                rpm_limit=500,
                tpm_limit=30000,
            )
            time.sleep(0.05)  # 50ms between requests

        stats = metrics.get_key_stats("test-key")
        # With 10 requests in ~0.5 seconds, peak RPM should be ~1200
        assert stats["usage_patterns"]["peak_rpm"] > 0

    def test_retry_count_tracking(self, metrics):
        """Test tracking of retry attempts."""
        metrics.assign_tier("test-key", "tier-1")

        # Record 5 retry attempts
        for _ in range(5):
            metrics.record_retry("test-key")

        stats = metrics.get_key_stats("test-key")
        assert stats["throttling"]["recent_retry_count"] == 5

    def test_quota_snapshot_updates(self, metrics):
        """Test updating and tracking quota snapshots."""
        metrics.assign_tier("test-key", "tier-1")

        # Update quota snapshots over time
        metrics.update_quota_snapshot(
            "test-key", rpm_remaining=400, tpm_remaining=25000
        )
        time.sleep(0.1)
        metrics.update_quota_snapshot(
            "test-key", rpm_remaining=300, tpm_remaining=20000
        )
        time.sleep(0.1)
        metrics.update_quota_snapshot(
            "test-key", rpm_remaining=200, tpm_remaining=15000
        )

        stats = metrics.get_key_stats("test-key")
        # Should have quota utilization data
        assert "quota_utilization" in stats

    def test_tier_stats_aggregation(self, metrics):
        """Test aggregation of statistics by tier."""
        # Create keys in different tiers
        metrics.assign_tier("key-tier1-1", "tier-1")
        metrics.assign_tier("key-tier1-2", "tier-1")
        metrics.assign_tier("key-tier2-1", "tier-2")

        # Record activity for each key
        for key in ["key-tier1-1", "key-tier1-2"]:
            for _ in range(5):
                metrics.record_request_attempt(
                    api_key=key,
                    allowed=True,
                    tokens=100,
                    rpm_limit=500,
                    tpm_limit=30000,
                )

        for _ in range(10):
            metrics.record_request_attempt(
                api_key="key-tier2-1",
                allowed=True,
                tokens=200,
                rpm_limit=5000,
                tpm_limit=450000,
            )

        tier_stats = metrics.get_tier_stats()

        # Verify tier-1 stats
        assert tier_stats["tier-1"]["key_count"] == 2
        assert tier_stats["tier-1"]["total_requests_attempted"] == 10
        assert tier_stats["tier-1"]["total_tokens_consumed"] == 1000

        # Verify tier-2 stats
        assert tier_stats["tier-2"]["key_count"] == 1
        assert tier_stats["tier-2"]["total_requests_attempted"] == 10
        assert tier_stats["tier-2"]["total_tokens_consumed"] == 2000

    def test_high_throttle_rate_detection(self, metrics):
        """Test detection of keys with high throttle rates."""
        metrics.assign_tier("test-key", "tier-1")

        # Simulate high throttle rate (60% throttled)
        for _ in range(40):
            metrics.record_request_attempt(
                api_key="test-key",
                allowed=True,
                tokens=50,
                rpm_limit=500,
                tpm_limit=30000,
            )

        for _ in range(60):
            metrics.record_request_attempt(
                api_key="test-key",
                allowed=False,
                tokens=50,
                rpm_limit=500,
                tpm_limit=30000,
            )

        tier_stats = metrics.get_tier_stats()
        # Should detect keys with high throttle rate (>50%)
        assert tier_stats["tier-1"]["keys_with_high_throttle"] == 1
        assert tier_stats["tier-1"]["avg_throttle_rate"] == 0.6

    def test_throttle_analytics_histogram(self, metrics):
        """Test throttle duration histogram generation."""
        metrics.assign_tier("test-key", "tier-1")

        # Record throttle events with various durations
        durations = [50, 150, 750, 2500, 7500, 15000, 45000]
        for duration in durations:
            metrics.record_throttle(
                api_key="test-key",
                retry_after_ms=float(duration),
                requested_tokens=100,
                rpm_exceeded=True,
                tpm_exceeded=False,
            )

        analytics = metrics.get_throttle_analytics()

        assert analytics["total_throttle_events"] == 7
        assert "<100ms" in analytics["duration_histogram"]
        assert "<1000ms" in analytics["duration_histogram"]
        assert "<10000ms" in analytics["duration_histogram"]

    def test_retry_after_distribution(self, metrics):
        """Test calculation of retry-after distribution percentiles."""
        metrics.assign_tier("test-key", "tier-1")

        # Record 100 throttle events with varying durations
        for i in range(100):
            metrics.record_throttle(
                api_key="test-key",
                retry_after_ms=float(i * 100),  # 0ms to 9900ms
                requested_tokens=50,
                rpm_exceeded=True,
                tpm_exceeded=False,
            )

        analytics = metrics.get_throttle_analytics()
        distribution = analytics["retry_after_distribution"]

        assert distribution["min"] == 0.0
        assert distribution["max"] == 9900.0
        assert 4000 < distribution["median"] < 5000  # Should be around 4950
        assert distribution["p90"] > distribution["median"]
        assert distribution["p99"] > distribution["p90"]

    def test_rpm_vs_tpm_exceeded_tracking(self, metrics):
        """Test tracking of RPM vs TPM limit exceeded."""
        metrics.assign_tier("test-key", "tier-1")

        # Record different types of throttle events
        # RPM only
        for _ in range(3):
            metrics.record_throttle(
                api_key="test-key",
                retry_after_ms=1000.0,
                requested_tokens=10,
                rpm_exceeded=True,
                tpm_exceeded=False,
            )

        # TPM only
        for _ in range(5):
            metrics.record_throttle(
                api_key="test-key",
                retry_after_ms=2000.0,
                requested_tokens=5000,
                rpm_exceeded=False,
                tpm_exceeded=True,
            )

        # Both
        for _ in range(2):
            metrics.record_throttle(
                api_key="test-key",
                retry_after_ms=3000.0,
                requested_tokens=5000,
                rpm_exceeded=True,
                tpm_exceeded=True,
            )

        analytics = metrics.get_throttle_analytics()
        exceeded = analytics["rpm_vs_tpm_exceeded"]

        assert exceeded["rpm_only"] == 3
        assert exceeded["tpm_only"] == 5
        assert exceeded["both"] == 2

    def test_abuse_pattern_detection_high_throttle(self, metrics):
        """Test detection of abuse pattern: high throttle rate."""
        metrics.assign_tier("test-key", "tier-1")

        # Create high throttle rate (70% throttled)
        for _ in range(30):
            metrics.record_request_attempt(
                api_key="test-key",
                allowed=True,
                tokens=50,
                rpm_limit=500,
                tpm_limit=30000,
            )

        for _ in range(70):
            metrics.record_request_attempt(
                api_key="test-key",
                allowed=False,
                tokens=50,
                rpm_limit=500,
                tpm_limit=30000,
            )

        patterns = metrics.detect_abuse_patterns()

        assert len(patterns) == 1
        assert patterns[0]["api_key"] == "test-key"
        assert any("High throttle rate" in issue for issue in patterns[0]["issues"])
        assert patterns[0]["throttle_rate"] == 0.7

    def test_abuse_pattern_detection_excessive_retries(self, metrics):
        """Test detection of abuse pattern: excessive retries."""
        metrics.assign_tier("test-key", "tier-1")

        # Record many recent throttle events (simulating excessive retries)
        for _ in range(15):
            metrics.record_throttle(
                api_key="test-key",
                retry_after_ms=1000.0,
                requested_tokens=100,
                rpm_exceeded=True,
                tpm_exceeded=False,
            )

        patterns = metrics.detect_abuse_patterns()

        assert len(patterns) == 1
        assert any("Excessive retries" in issue for issue in patterns[0]["issues"])

    def test_abuse_pattern_detection_burst_behavior(self, metrics):
        """Test detection of abuse pattern: burst behavior."""
        metrics.assign_tier("test-key", "tier-1")

        # Simulate large burst (25 requests in rapid succession)
        for _ in range(25):
            metrics.record_request_attempt(
                api_key="test-key",
                allowed=True,
                tokens=50,
                rpm_limit=500,
                tpm_limit=30000,
            )

        patterns = metrics.detect_abuse_patterns()

        assert len(patterns) == 1
        assert any("Burst behavior" in issue for issue in patterns[0]["issues"])

    def test_abuse_pattern_severity_classification(self, metrics):
        """Test classification of abuse pattern severity."""
        metrics.assign_tier("test-key-high", "tier-1")
        metrics.assign_tier("test-key-medium", "tier-1")

        # High severity: multiple issues
        # 1. High throttle rate
        for _ in range(40):
            metrics.record_request_attempt(
                api_key="test-key-high",
                allowed=False,
                tokens=50,
                rpm_limit=500,
                tpm_limit=30000,
            )
        # 2. Excessive retries
        for _ in range(15):
            metrics.record_throttle(
                api_key="test-key-high",
                retry_after_ms=1000.0,
                requested_tokens=100,
                rpm_exceeded=True,
                tpm_exceeded=False,
            )
        # 3. Burst behavior
        for _ in range(25):
            metrics.record_request_attempt(
                api_key="test-key-high",
                allowed=True,
                tokens=50,
                rpm_limit=500,
                tpm_limit=30000,
            )

        # Medium severity: single issue
        for _ in range(60):
            metrics.record_request_attempt(
                api_key="test-key-medium",
                allowed=False,
                tokens=50,
                rpm_limit=500,
                tpm_limit=30000,
            )
        for _ in range(40):
            metrics.record_request_attempt(
                api_key="test-key-medium",
                allowed=True,
                tokens=50,
                rpm_limit=500,
                tpm_limit=30000,
            )

        patterns = metrics.detect_abuse_patterns()

        high_severity = [p for p in patterns if p["severity"] == "high"]
        medium_severity = [p for p in patterns if p["severity"] == "medium"]

        assert len(high_severity) >= 1
        assert len(medium_severity) >= 1

    def test_get_all_metrics_summary(self, metrics):
        """Test comprehensive metrics summary retrieval."""
        # Setup multiple keys
        metrics.assign_tier("key1", "tier-1")
        metrics.assign_tier("key2", "tier-2")

        # Record some activity
        for key in ["key1", "key2"]:
            metrics.record_request_attempt(
                api_key=key,
                allowed=True,
                tokens=100,
                rpm_limit=500,
                tpm_limit=30000,
            )

        all_metrics = metrics.get_all_metrics()

        assert "summary" in all_metrics
        assert "tier_stats" in all_metrics
        assert "throttle_analytics" in all_metrics
        assert "abuse_patterns" in all_metrics

        assert all_metrics["summary"]["total_keys"] == 2
        assert "tier-1" in all_metrics["summary"]["tiers"]
        assert "tier-2" in all_metrics["summary"]["tiers"]

    def test_reset_specific_key(self, metrics):
        """Test resetting metrics for a specific API key."""
        metrics.assign_tier("key1", "tier-1")
        metrics.assign_tier("key2", "tier-1")

        metrics.record_request_attempt(
            api_key="key1",
            allowed=True,
            tokens=100,
            rpm_limit=500,
            tpm_limit=30000,
        )
        metrics.record_request_attempt(
            api_key="key2",
            allowed=True,
            tokens=100,
            rpm_limit=500,
            tpm_limit=30000,
        )

        # Reset only key1
        metrics.reset("key1")

        stats1 = metrics.get_key_stats("key1")
        stats2 = metrics.get_key_stats("key2")

        assert stats1 == {}
        assert stats2["requests"]["total_attempted"] == 1

    def test_reset_all_metrics(self, metrics):
        """Test resetting all metrics."""
        metrics.assign_tier("key1", "tier-1")
        metrics.assign_tier("key2", "tier-2")

        metrics.record_request_attempt(
            api_key="key1",
            allowed=True,
            tokens=100,
            rpm_limit=500,
            tpm_limit=30000,
        )

        metrics.reset()

        all_metrics = metrics.get_all_metrics()
        assert all_metrics["summary"]["total_keys"] == 0
        assert all_metrics["summary"]["total_throttle_events"] == 0

    def test_empty_metrics_returns_valid_structure(self, metrics):
        """Test that empty metrics return valid empty structures."""
        stats = metrics.get_key_stats("nonexistent-key")
        assert stats == {}

        tier_stats = metrics.get_tier_stats()
        assert isinstance(tier_stats, dict)

        analytics = metrics.get_throttle_analytics()
        assert analytics["total_throttle_events"] == 0

        patterns = metrics.detect_abuse_patterns()
        assert patterns == []

    def test_concurrent_request_recording(self, metrics):
        """Test thread safety of concurrent request recording."""
        import threading

        metrics.assign_tier("test-key", "tier-1")

        def record_requests():
            for _ in range(50):
                metrics.record_request_attempt(
                    api_key="test-key",
                    allowed=True,
                    tokens=50,
                    rpm_limit=500,
                    tpm_limit=30000,
                )

        threads = [threading.Thread(target=record_requests) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stats = metrics.get_key_stats("test-key")
        # 4 threads × 50 requests = 200 total
        assert stats["requests"]["total_attempted"] == 200

    def test_time_in_service_tracking(self, metrics):
        """Test tracking of time an API key has been in service."""
        metrics.assign_tier("test-key", "tier-1")

        # Record initial request
        metrics.record_request_attempt(
            api_key="test-key",
            allowed=True,
            tokens=100,
            rpm_limit=500,
            tpm_limit=30000,
        )

        # Wait a bit
        time.sleep(0.2)

        stats = metrics.get_key_stats("test-key")
        assert stats["time_in_service_seconds"] >= 0.2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
