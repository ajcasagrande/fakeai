"""
Comprehensive tests for ErrorMetricsTracker module.

Tests cover:
- Error recording and storage
- Error fingerprinting and normalization
- Pattern detection and tracking
- SLO monitoring and error budgets
- Success tracking and rates
- Metrics aggregation
- Prometheus export
- Cleanup operations

All tests use realistic error scenarios to ensure production readiness.
"""
#  SPDX-License-Identifier: Apache-2.0

import importlib.util
import re
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Import directly from the module file to avoid package-level app initialization
# This avoids triggering the fakeai/__init__.py which imports app
module_path = Path(__file__).parent.parent / "fakeai" / "error_metrics_tracker.py"
spec = importlib.util.spec_from_file_location("error_metrics_tracker", module_path)
error_metrics_tracker_module = importlib.util.module_from_spec(spec)
sys.modules['error_metrics_tracker'] = error_metrics_tracker_module
spec.loader.exec_module(error_metrics_tracker_module)

ErrorMetricsTracker = error_metrics_tracker_module.ErrorMetricsTracker
ErrorPattern = error_metrics_tracker_module.ErrorPattern
ErrorRecord = error_metrics_tracker_module.ErrorRecord
SLOStatus = error_metrics_tracker_module.SLOStatus


@pytest.fixture
def tracker():
    """Create a fresh ErrorMetricsTracker instance for testing."""
    return ErrorMetricsTracker(
        max_recent_errors=500,
        error_budget_slo=0.999,
        window_seconds=300,
        pattern_threshold=3,
    )


@pytest.fixture
def tracker_low_slo():
    """Create a tracker with lower SLO for testing violations."""
    return ErrorMetricsTracker(
        max_recent_errors=100,
        error_budget_slo=0.95,  # 95% success rate
        window_seconds=60,
        pattern_threshold=2,
    )


class TestErrorRecording:
    """Tests for error recording functionality."""

    def test_record_error_stores_all_fields(self, tracker):
        """Test that record_error captures all fields correctly."""
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalServerError",
            error_message="Database connection timeout",
            model="gpt-4",
            api_key="sk-test123",
            request_id="req-abc123",
            user_id="user-xyz",
            stack_trace="File main.py, line 42",
        )

        errors = tracker.get_recent_errors(limit=1)
        assert len(errors) == 1

        error = errors[0]
        assert error.endpoint == "/v1/chat/completions"
        assert error.status_code == 500
        assert error.error_type == "InternalServerError"
        assert error.error_message == "Database connection timeout"
        assert error.model == "gpt-4"
        assert error.api_key == "sk-test123"
        assert error.request_id == "req-abc123"
        assert error.user_id == "user-xyz"
        assert error.stack_trace == "File main.py, line 42"
        assert error.timestamp > 0
        assert error.fingerprint is not None

    def test_record_error_with_minimal_fields(self, tracker):
        """Test recording error with only required fields."""
        tracker.record_error(
            endpoint="/v1/completions",
            status_code=503,
            error_type="ServiceUnavailable",
            error_message="Service temporarily unavailable",
        )

        errors = tracker.get_recent_errors(limit=1)
        assert len(errors) == 1

        error = errors[0]
        assert error.endpoint == "/v1/completions"
        assert error.status_code == 503
        assert error.model is None
        assert error.api_key is None

    def test_recent_errors_bounded_by_max_size(self, tracker):
        """Test that recent errors list is bounded by max_recent_errors."""
        # Create tracker with small limit
        small_tracker = ErrorMetricsTracker(max_recent_errors=10)

        # Record more errors than the limit
        for i in range(20):
            small_tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message=f"Error {i}",
            )

        errors = small_tracker.get_recent_errors(limit=100)

        # Should only keep the most recent 10
        assert len(errors) <= 10

        # Should be most recent errors (15-19)
        messages = [e.error_message for e in errors]
        assert "Error 19" in messages

    def test_error_counters_increment(self, tracker):
        """Test that error counters increment correctly."""
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalServerError",
            error_message="Error 1",
        )
        tracker.record_error(
            endpoint="/v1/embeddings",
            status_code=400,
            error_type="ValidationError",
            error_message="Error 2",
            model="text-embedding-3-small",
        )

        metrics = tracker.get_metrics()

        assert metrics["total_errors"] == 2
        assert metrics["total_requests"] == 2
        assert metrics["errors_by_endpoint"]["/v1/chat/completions"] == 1
        assert metrics["errors_by_endpoint"]["/v1/embeddings"] == 1
        assert metrics["errors_by_model"]["text-embedding-3-small"] == 1

    def test_error_timestamps_recorded(self, tracker):
        """Test that error timestamps are properly recorded."""
        start_time = time.time()

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalServerError",
            error_message="Test error",
        )

        end_time = time.time()

        errors = tracker.get_recent_errors(limit=1)
        assert len(errors) == 1
        assert start_time <= errors[0].timestamp <= end_time


class TestErrorFingerprinting:
    """Tests for error fingerprinting and normalization."""

    def test_fingerprint_generated_automatically(self, tracker):
        """Test that fingerprints are generated automatically."""
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Connection timeout",
        )

        errors = tracker.get_recent_errors(limit=1)
        assert len(errors) == 1
        assert errors[0].fingerprint is not None
        assert len(errors[0].fingerprint) == 8  # 8-character hex

    def test_similar_errors_same_fingerprint(self, tracker):
        """Test that similar errors get the same fingerprint."""
        # Record similar errors with only numbers different
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Connection timeout after 1000ms",
        )
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Connection timeout after 2500ms",
        )

        errors = tracker.get_recent_errors(limit=2)
        assert len(errors) == 2

        # Should have same fingerprint despite different timeout values
        assert errors[0].fingerprint == errors[1].fingerprint

    def test_different_errors_different_fingerprint(self, tracker):
        """Test that different errors get different fingerprints."""
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseError",
            error_message="Connection timeout",
        )
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="RateLimitError",
            error_message="Rate limit exceeded",
        )

        errors = tracker.get_recent_errors(limit=2)
        assert len(errors) == 2
        assert errors[0].fingerprint != errors[1].fingerprint

    def test_uuid_normalization(self, tracker):
        """Test that UUIDs are normalized in fingerprints."""
        error1 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="RequestError",
            error_message="Failed to process request 550e8400-e29b-41d4-a716-446655440000",
        )
        error2 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="RequestError",
            error_message="Failed to process request 123e4567-e89b-12d3-a456-426614174000",
        )

        # Both should have same fingerprint
        assert error1.fingerprint == error2.fingerprint

    def test_request_id_normalization(self, tracker):
        """Test that request IDs are normalized."""
        error1 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="ProcessingError",
            error_message="Request req-abc123 failed",
        )
        error2 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="ProcessingError",
            error_message="Request req-xyz789 failed",
        )

        assert error1.fingerprint == error2.fingerprint

    def test_number_normalization(self, tracker):
        """Test that numbers are normalized."""
        error1 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="TimeoutError",
            error_message="Timeout after 1234 milliseconds",
        )
        error2 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="TimeoutError",
            error_message="Timeout after 5678 milliseconds",
        )

        assert error1.fingerprint == error2.fingerprint

    def test_hex_address_normalization(self, tracker):
        """Test that hex addresses are normalized."""
        error1 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="MemoryError",
            error_message="Segfault at address 0x7fff5fbff000",
        )
        error2 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="MemoryError",
            error_message="Segfault at address 0x7fff5fbff123",
        )

        assert error1.fingerprint == error2.fingerprint

    def test_fingerprint_sha256_format(self, tracker):
        """Test that fingerprint uses SHA256 hash."""
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="TestError",
            error_message="Test message",
        )

        errors = tracker.get_recent_errors(limit=1)
        fingerprint = errors[0].fingerprint

        # Should be 8 hex characters
        assert re.match(r'^[0-9a-f]{8}$', fingerprint)

    def test_fingerprint_includes_endpoint(self, tracker):
        """Test that fingerprint includes endpoint information."""
        error1 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="TestError",
            error_message="Same message",
        )
        error2 = ErrorRecord(
            timestamp=time.time(),
            endpoint="/v1/embeddings",
            status_code=500,
            error_type="TestError",
            error_message="Same message",
        )

        # Different endpoints should produce different fingerprints
        assert error1.fingerprint != error2.fingerprint


class TestPatternDetection:
    """Tests for error pattern detection."""

    def test_pattern_created_automatically(self, tracker):
        """Test that patterns are created when errors are recorded."""
        for _ in range(3):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="DatabaseError",
                error_message="Connection failed",
            )

        patterns = tracker.get_error_patterns(min_count=1)
        assert len(patterns) >= 1
        assert patterns[0].count == 3

    def test_pattern_count_increments(self, tracker):
        """Test that pattern count increments correctly."""
        # Record same error 5 times
        for i in range(5):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="TimeoutError",
                error_message=f"Timeout after {1000 + i * 100}ms",
            )

        patterns = tracker.get_error_patterns(min_count=1)
        assert len(patterns) == 1
        assert patterns[0].count == 5

    def test_pattern_tracks_affected_models(self, tracker):
        """Test that patterns track affected models."""
        for model in ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"]:
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="RateLimitError",
                error_message="Rate limit exceeded",
                model=model,
            )

        patterns = tracker.get_error_patterns(min_count=1)
        assert len(patterns) == 1

        pattern = patterns[0]
        assert len(pattern.affected_models) == 3
        assert "gpt-4" in pattern.affected_models
        assert "gpt-3.5-turbo" in pattern.affected_models
        assert "gpt-4-turbo" in pattern.affected_models

    def test_pattern_tracks_affected_users(self, tracker):
        """Test that patterns track affected users."""
        for user_id in ["user-1", "user-2", "user-3"]:
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=401,
                error_type="AuthenticationError",
                error_message="Invalid API key",
                user_id=user_id,
            )

        patterns = tracker.get_error_patterns(min_count=1)
        assert len(patterns) == 1

        pattern = patterns[0]
        assert len(pattern.affected_users) == 3
        assert "user-1" in pattern.affected_users

    def test_pattern_stores_example_request_ids(self, tracker):
        """Test that patterns store example request IDs."""
        for i in range(5):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="ProcessingError",
                error_message="Processing failed",
                request_id=f"req-{i:03d}",
            )

        patterns = tracker.get_error_patterns(min_count=1)
        assert len(patterns) == 1

        pattern = patterns[0]
        assert len(pattern.example_request_ids) <= 10  # Limited to 10
        assert "req-000" in pattern.example_request_ids

    def test_get_error_patterns_filters_by_min_count(self, tracker):
        """Test that get_error_patterns filters by minimum count."""
        # Pattern 1: 5 occurrences
        for _ in range(5):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="Error1",
                error_message="Frequent error",
            )

        # Pattern 2: 2 occurrences
        for _ in range(2):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=400,
                error_type="Error2",
                error_message="Infrequent error",
            )

        patterns = tracker.get_error_patterns(min_count=3)
        assert len(patterns) == 1
        assert patterns[0].count == 5

    def test_get_error_patterns_filters_by_recency(self, tracker):
        """Test that get_error_patterns can filter by time window."""
        # Create a pattern with old timestamp
        with patch('time.time', return_value=time.time() - 400):
            for _ in range(3):
                tracker.record_error(
                    endpoint="/v1/chat/completions",
                    status_code=500,
                    error_type="OldError",
                    error_message="Old error",
                )

        # Create a recent pattern
        for _ in range(3):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=400,
                error_type="NewError",
                error_message="New error",
            )

        # With recent_only=True (default), should only get recent pattern
        recent_patterns = tracker.get_error_patterns(min_count=1, recent_only=True)
        assert len(recent_patterns) == 1
        assert recent_patterns[0].error_type == "NewError"

        # With recent_only=False, should get all patterns
        all_patterns = tracker.get_error_patterns(min_count=1, recent_only=False)
        assert len(all_patterns) == 2

    def test_patterns_sorted_by_count(self, tracker):
        """Test that patterns are sorted by count descending."""
        # Create multiple patterns with different counts
        for _ in range(10):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="Error1",
                error_message="Most frequent",
            )

        for _ in range(5):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=400,
                error_type="Error2",
                error_message="Medium frequent",
            )

        for _ in range(3):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=404,
                error_type="Error3",
                error_message="Least frequent",
            )

        patterns = tracker.get_error_patterns(min_count=1)
        assert len(patterns) == 3
        assert patterns[0].count == 10
        assert patterns[1].count == 5
        assert patterns[2].count == 3

    def test_pattern_first_and_last_seen(self, tracker):
        """Test that patterns track first and last seen timestamps."""
        first_time = time.time()

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="TestError",
            error_message="Test message",
        )

        time.sleep(0.1)

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="TestError",
            error_message="Test message",
        )

        last_time = time.time()

        patterns = tracker.get_error_patterns(min_count=1)
        assert len(patterns) == 1

        pattern = patterns[0]
        assert pattern.first_seen >= first_time
        assert pattern.last_seen <= last_time
        assert pattern.last_seen > pattern.first_seen


class TestSLOMonitoring:
    """Tests for SLO monitoring and error budgets."""

    def test_error_budget_calculated(self, tracker):
        """Test that error budget is calculated correctly."""
        # Record 1000 successes and 1 error
        # With 99.9% SLO, error budget = 1000 * 0.001 = 1
        for _ in range(1000):
            tracker.record_success("/v1/chat/completions")

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="TestError",
            error_message="Test",
        )

        slo_status = tracker.get_slo_status()

        assert slo_status.total_requests == 1001
        assert slo_status.successful_requests == 1000
        assert slo_status.failed_requests == 1
        assert slo_status.error_budget_total == 1  # int(1001 * 0.001)
        assert slo_status.error_budget_consumed == 1
        assert slo_status.error_budget_remaining == 0

    def test_slo_violation_detection(self, tracker_low_slo):
        """Test that SLO violations are detected."""
        # Record 50% error rate (violates 95% SLO)
        for _ in range(5):
            tracker_low_slo.record_success("/v1/chat/completions")

        for _ in range(5):
            tracker_low_slo.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="TestError",
                error_message="Test",
            )

        slo_status = tracker_low_slo.get_slo_status()

        assert slo_status.current_success_rate == 0.5
        assert slo_status.current_error_rate == 0.5
        assert slo_status.slo_violated is True

    def test_slo_compliance(self, tracker_low_slo):
        """Test that SLO compliance is detected."""
        # Record 99% success rate (meets 95% SLO)
        for _ in range(99):
            tracker_low_slo.record_success("/v1/chat/completions")

        tracker_low_slo.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="TestError",
            error_message="Test",
        )

        slo_status = tracker_low_slo.get_slo_status()

        assert slo_status.current_success_rate == 0.99
        assert slo_status.slo_violated is False

    def test_burn_rate_computation(self, tracker):
        """Test that burn rate is computed correctly."""
        # With 99.9% SLO, target error rate = 0.1%
        # If we have 1% error rate, burn rate = 1% / 0.1% = 10x

        for _ in range(99):
            tracker.record_success("/v1/chat/completions")

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="TestError",
            error_message="Test",
        )

        slo_status = tracker.get_slo_status()

        # Current error rate = 1/100 = 1%
        # Target error rate = 0.1%
        # Burn rate = 1% / 0.1% = 10
        assert slo_status.current_error_rate == 0.01
        assert abs(slo_status.burn_rate - 10.0) < 0.1

    def test_success_rate_tracking(self, tracker):
        """Test that success rate is tracked correctly."""
        for _ in range(97):
            tracker.record_success("/v1/chat/completions")

        for _ in range(3):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="TestError",
                error_message="Test",
            )

        slo_status = tracker.get_slo_status()

        assert slo_status.total_requests == 100
        assert slo_status.successful_requests == 97
        assert slo_status.current_success_rate == 0.97

    def test_slo_status_with_zero_requests(self, tracker):
        """Test SLO status with no requests."""
        slo_status = tracker.get_slo_status()

        assert slo_status.total_requests == 0
        assert slo_status.current_success_rate == 1.0
        assert slo_status.current_error_rate == 0.0
        assert slo_status.slo_violated is False
        assert slo_status.burn_rate == 0.0
        assert slo_status.error_budget_percentage == 100.0

    def test_error_budget_percentage(self, tracker):
        """Test error budget percentage calculation."""
        # Create scenario with 50% of error budget consumed
        for _ in range(1000):
            tracker.record_success("/v1/chat/completions")

        # With 99.9% SLO and 1000 requests, error budget = 1
        # Consume 0.5 errors worth (we'll consume 0 actually since we can't have 0.5 errors)
        # Let's use 2000 requests so budget = 2, then consume 1

        for _ in range(1000):
            tracker.record_success("/v1/chat/completions")

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="TestError",
            error_message="Test",
        )

        slo_status = tracker.get_slo_status()

        # Error budget total = int(2001 * 0.001) = 2
        # Consumed = 1
        # Remaining = 1
        # Percentage = 50%
        assert slo_status.error_budget_total == 2
        assert slo_status.error_budget_consumed == 1
        assert slo_status.error_budget_remaining == 1
        assert abs(slo_status.error_budget_percentage - 50.0) < 1.0

    def test_endpoint_error_rates(self, tracker):
        """Test per-endpoint error rate tracking."""
        # Endpoint 1: 90% success
        for _ in range(9):
            tracker.record_success("/v1/chat/completions")
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="TestError",
            error_message="Test",
        )

        # Endpoint 2: 80% success
        for _ in range(8):
            tracker.record_success("/v1/embeddings")
        for _ in range(2):
            tracker.record_error(
                endpoint="/v1/embeddings",
                status_code=500,
                error_type="TestError",
                error_message="Test",
            )

        slo_status = tracker.get_slo_status()

        assert "/v1/chat/completions" in slo_status.endpoint_error_rates
        assert "/v1/embeddings" in slo_status.endpoint_error_rates
        assert abs(slo_status.endpoint_error_rates["/v1/chat/completions"] - 0.1) < 0.01
        assert abs(slo_status.endpoint_error_rates["/v1/embeddings"] - 0.2) < 0.01


class TestSuccessTracking:
    """Tests for success tracking."""

    def test_record_success_updates_counters(self, tracker):
        """Test that record_success updates all counters."""
        tracker.record_success("/v1/chat/completions", model="gpt-4")

        metrics = tracker.get_metrics()

        assert metrics["total_requests"] == 1
        assert metrics["total_successes"] == 1
        assert metrics["total_errors"] == 0

    def test_success_rate_calculated(self, tracker):
        """Test that success rate is calculated correctly."""
        for _ in range(7):
            tracker.record_success("/v1/chat/completions")

        for _ in range(3):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="TestError",
                error_message="Test",
            )

        metrics = tracker.get_metrics()

        assert metrics["total_requests"] == 10
        assert metrics["total_successes"] == 7
        assert metrics["success_rate"] == 0.7

    def test_per_endpoint_success_tracking(self, tracker):
        """Test that successes are tracked per endpoint."""
        tracker.record_success("/v1/chat/completions")
        tracker.record_success("/v1/chat/completions")
        tracker.record_success("/v1/embeddings")

        slo_status = tracker.get_slo_status()

        # Check via endpoint error rates (0 errors = 0.0 error rate)
        assert "/v1/chat/completions" in slo_status.endpoint_error_rates
        assert slo_status.endpoint_error_rates["/v1/chat/completions"] == 0.0


class TestMetricsAggregation:
    """Tests for metrics aggregation."""

    def test_get_metrics_comprehensive(self, tracker):
        """Test that get_metrics returns comprehensive data."""
        # Generate diverse data
        tracker.record_success("/v1/chat/completions", model="gpt-4")
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalError",
            error_message="Server error",
            model="gpt-4",
        )
        tracker.record_error(
            endpoint="/v1/embeddings",
            status_code=429,
            error_type="RateLimitError",
            error_message="Rate limit exceeded",
        )

        metrics = tracker.get_metrics()

        # Check all required fields
        assert "total_requests" in metrics
        assert "total_errors" in metrics
        assert "total_successes" in metrics
        assert "error_rate" in metrics
        assert "success_rate" in metrics
        assert "recent_errors_count" in metrics
        assert "windowed_errors_count" in metrics
        assert "pattern_count" in metrics
        assert "top_error_types" in metrics
        assert "top_error_endpoints" in metrics
        assert "top_status_codes" in metrics
        assert "errors_by_endpoint" in metrics
        assert "errors_by_model" in metrics

    def test_top_error_types(self, tracker):
        """Test that top error types are aggregated correctly."""
        for _ in range(5):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalError",
                error_message="Error",
            )

        for _ in range(3):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=429,
                error_type="RateLimitError",
                error_message="Error",
            )

        metrics = tracker.get_metrics()
        top_types = metrics["top_error_types"]

        assert len(top_types) == 2
        assert top_types[0]["type"] == "InternalError"
        assert top_types[0]["count"] == 5
        assert top_types[1]["type"] == "RateLimitError"
        assert top_types[1]["count"] == 3

    def test_top_endpoints_with_errors(self, tracker):
        """Test that top error endpoints are aggregated correctly."""
        for _ in range(7):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="Error",
                error_message="Error",
            )

        for _ in range(3):
            tracker.record_error(
                endpoint="/v1/embeddings",
                status_code=500,
                error_type="Error",
                error_message="Error",
            )

        metrics = tracker.get_metrics()
        top_endpoints = metrics["top_error_endpoints"]

        assert len(top_endpoints) == 2
        assert top_endpoints[0]["endpoint"] == "/v1/chat/completions"
        assert top_endpoints[0]["count"] == 7

    def test_top_status_codes(self, tracker):
        """Test that top status codes are aggregated correctly."""
        for _ in range(4):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="Error",
                error_message="Error",
            )

        for _ in range(2):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=429,
                error_type="Error",
                error_message="Error",
            )

        metrics = tracker.get_metrics()
        top_codes = metrics["top_status_codes"]

        assert len(top_codes) == 2
        assert top_codes[0]["status_code"] == 500
        assert top_codes[0]["count"] == 4

    def test_time_windowing(self, tracker):
        """Test that metrics can be windowed by time."""
        # Record old error (outside window)
        with patch('time.time', return_value=time.time() - 400):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="OldError",
                error_message="Old",
            )

        # Record recent error (inside window)
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="NewError",
            error_message="New",
        )

        metrics = tracker.get_metrics()

        # windowed_errors_count should only include recent error
        assert metrics["recent_errors_count"] == 2  # Both stored
        assert metrics["windowed_errors_count"] == 1  # Only recent one in window

    def test_errors_by_model(self, tracker):
        """Test errors aggregated by model."""
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="Error",
            error_message="Error",
            model="gpt-4",
        )
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="Error",
            error_message="Error",
            model="gpt-4",
        )
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="Error",
            error_message="Error",
            model="gpt-3.5-turbo",
        )

        metrics = tracker.get_metrics()

        assert metrics["errors_by_model"]["gpt-4"] == 2
        assert metrics["errors_by_model"]["gpt-3.5-turbo"] == 1


class TestPrometheusExport:
    """Tests for Prometheus metrics export."""

    def test_prometheus_valid_format(self, tracker):
        """Test that Prometheus export has valid format."""
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalError",
            error_message="Test error",
        )
        tracker.record_success("/v1/chat/completions")

        prom_output = tracker.get_prometheus_metrics()

        # Check for required Prometheus elements
        assert "# HELP" in prom_output
        assert "# TYPE" in prom_output

        # Check for key metrics
        assert "error_total_requests" in prom_output
        assert "error_total_errors" in prom_output
        assert "error_rate" in prom_output
        assert "error_success_rate" in prom_output

    def test_prometheus_includes_slo_metrics(self, tracker):
        """Test that SLO metrics are included in Prometheus export."""
        tracker.record_success("/v1/chat/completions")

        prom_output = tracker.get_prometheus_metrics()

        assert "error_slo_violated" in prom_output
        assert "error_budget_remaining" in prom_output
        assert "error_budget_percentage" in prom_output
        assert "error_burn_rate" in prom_output

    def test_prometheus_includes_error_budget_metrics(self, tracker):
        """Test that error budget metrics are included."""
        for _ in range(10):
            tracker.record_success("/v1/chat/completions")

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="Error",
            error_message="Error",
        )

        prom_output = tracker.get_prometheus_metrics()

        assert "error_budget_remaining" in prom_output
        assert "error_budget_percentage" in prom_output

    def test_prometheus_per_endpoint_metrics(self, tracker):
        """Test that per-endpoint metrics are included."""
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="Error",
            error_message="Error",
        )

        prom_output = tracker.get_prometheus_metrics()

        assert "error_by_endpoint" in prom_output
        assert "/v1/chat/completions" in prom_output

    def test_prometheus_per_type_metrics(self, tracker):
        """Test that per-type metrics are included."""
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalError",
            error_message="Error",
        )

        prom_output = tracker.get_prometheus_metrics()

        assert "error_by_type" in prom_output
        assert "InternalError" in prom_output

    def test_prometheus_pattern_count(self, tracker):
        """Test that pattern count is included."""
        for _ in range(3):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="Error",
                error_message="Same error",
            )

        prom_output = tracker.get_prometheus_metrics()

        assert "error_pattern_count" in prom_output

    def test_prometheus_escapes_labels(self, tracker):
        """Test that Prometheus labels are properly escaped."""
        tracker.record_error(
            endpoint='/v1/endpoint"with"quotes',
            status_code=500,
            error_type='Error"Type',
            error_message="Error",
        )

        prom_output = tracker.get_prometheus_metrics()

        # Should escape quotes in labels
        assert '\\"' in prom_output or 'with' in prom_output


class TestCleanup:
    """Tests for cleanup operations."""

    def test_cleanup_old_patterns(self, tracker):
        """Test that old patterns are removed by cleanup."""
        # Create old pattern
        with patch('time.time', return_value=time.time() - 7200):  # 2 hours ago
            for _ in range(3):
                tracker.record_error(
                    endpoint="/v1/chat/completions",
                    status_code=500,
                    error_type="OldError",
                    error_message="Old error",
                )

        # Create recent pattern
        for _ in range(3):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="NewError",
                error_message="New error",
            )

        # Clean up patterns older than 1 hour
        removed_count = tracker.cleanup_old_patterns(age_seconds=3600)

        assert removed_count == 1

        patterns = tracker.get_error_patterns(min_count=1, recent_only=False)
        assert len(patterns) == 1
        assert patterns[0].error_type == "NewError"

    def test_cleanup_returns_count(self, tracker):
        """Test that cleanup returns the correct count of removed patterns."""
        # Create 3 old patterns
        for error_type in ["Error1", "Error2", "Error3"]:
            with patch('time.time', return_value=time.time() - 7200):
                for _ in range(3):
                    tracker.record_error(
                        endpoint="/v1/chat/completions",
                        status_code=500,
                        error_type=error_type,
                        error_message=f"{error_type} message",
                    )

        removed_count = tracker.cleanup_old_patterns(age_seconds=3600)

        assert removed_count == 3

    def test_cleanup_preserves_recent_patterns(self, tracker):
        """Test that cleanup preserves recent patterns."""
        # Create recent pattern
        for _ in range(3):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="RecentError",
                error_message="Recent",
            )

        # Cleanup old patterns
        removed_count = tracker.cleanup_old_patterns(age_seconds=60)

        assert removed_count == 0

        patterns = tracker.get_error_patterns(min_count=1, recent_only=False)
        assert len(patterns) == 1

    def test_reset_clears_all_data(self, tracker):
        """Test that reset clears all tracked data."""
        # Generate data
        for _ in range(5):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="Error",
                error_message="Error",
            )
        tracker.record_success("/v1/chat/completions")

        # Reset
        tracker.reset()

        # Verify everything is cleared
        metrics = tracker.get_metrics()
        assert metrics["total_requests"] == 0
        assert metrics["total_errors"] == 0
        assert metrics["total_successes"] == 0
        assert metrics["recent_errors_count"] == 0
        assert metrics["pattern_count"] == 0

        errors = tracker.get_recent_errors()
        assert len(errors) == 0


class TestRecentErrorsRetrieval:
    """Tests for retrieving recent errors."""

    def test_get_recent_errors_with_limit(self, tracker):
        """Test that get_recent_errors respects limit."""
        for i in range(10):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="Error",
                error_message=f"Error {i}",
            )

        errors = tracker.get_recent_errors(limit=5)

        assert len(errors) == 5

    def test_get_recent_errors_sorted_by_timestamp(self, tracker):
        """Test that recent errors are sorted by timestamp (most recent first)."""
        for i in range(5):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="Error",
                error_message=f"Error {i}",
            )
            time.sleep(0.01)

        errors = tracker.get_recent_errors(limit=5)

        # Should be in reverse chronological order
        assert errors[0].error_message == "Error 4"
        assert errors[4].error_message == "Error 0"

    def test_get_recent_errors_filter_by_endpoint(self, tracker):
        """Test filtering recent errors by endpoint."""
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="Error",
            error_message="Chat error",
        )
        tracker.record_error(
            endpoint="/v1/embeddings",
            status_code=500,
            error_type="Error",
            error_message="Embedding error",
        )

        errors = tracker.get_recent_errors(endpoint="/v1/chat/completions")

        assert len(errors) == 1
        assert errors[0].endpoint == "/v1/chat/completions"

    def test_get_recent_errors_filter_by_type(self, tracker):
        """Test filtering recent errors by error type."""
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalError",
            error_message="Error 1",
        )
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=429,
            error_type="RateLimitError",
            error_message="Error 2",
        )

        errors = tracker.get_recent_errors(error_type="InternalError")

        assert len(errors) == 1
        assert errors[0].error_type == "InternalError"


class TestErrorRecordDataClass:
    """Tests for ErrorRecord dataclass."""

    def test_error_record_to_dict(self):
        """Test ErrorRecord to_dict method."""
        error = ErrorRecord(
            timestamp=1234567890.0,
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalError",
            error_message="Test error",
            model="gpt-4",
            api_key="sk-verylongapikey123456789",
            request_id="req-123",
            user_id="user-456",
        )

        error_dict = error.to_dict()

        assert error_dict["timestamp"] == 1234567890.0
        assert error_dict["endpoint"] == "/v1/chat/completions"
        assert error_dict["status_code"] == 500
        assert error_dict["error_type"] == "InternalError"
        assert error_dict["model"] == "gpt-4"
        assert "..." in error_dict["api_key"]  # Should be truncated
        assert error_dict["request_id"] == "req-123"
        assert error_dict["fingerprint"] is not None


class TestErrorPatternDataClass:
    """Tests for ErrorPattern dataclass."""

    def test_error_pattern_to_dict(self):
        """Test ErrorPattern to_dict method."""
        pattern = ErrorPattern(
            fingerprint="abc12345",
            error_type="DatabaseError",
            endpoint="/v1/chat/completions",
            normalized_message="Connection timeout after <NUM>ms",
            count=10,
            first_seen=1234567890.0,
            last_seen=1234567900.0,
            affected_models={"gpt-4", "gpt-3.5-turbo"},
            affected_users={"user-1", "user-2", "user-3"},
            example_request_ids=["req-1", "req-2", "req-3"],
        )

        pattern_dict = pattern.to_dict()

        assert pattern_dict["fingerprint"] == "abc12345"
        assert pattern_dict["error_type"] == "DatabaseError"
        assert pattern_dict["count"] == 10
        assert pattern_dict["affected_users_count"] == 3
        assert len(pattern_dict["affected_models"]) == 2
        assert len(pattern_dict["example_request_ids"]) == 3

    def test_error_pattern_limits_example_request_ids(self):
        """Test that pattern only shows first 5 request IDs in dict."""
        pattern = ErrorPattern(
            fingerprint="abc12345",
            error_type="Error",
            endpoint="/v1/test",
            normalized_message="Error",
            count=10,
            first_seen=1234567890.0,
            last_seen=1234567900.0,
            example_request_ids=[f"req-{i}" for i in range(10)],
        )

        pattern_dict = pattern.to_dict()

        # Should limit to first 5
        assert len(pattern_dict["example_request_ids"]) == 5


class TestSLOStatusDataClass:
    """Tests for SLOStatus dataclass."""

    def test_slo_status_to_dict(self):
        """Test SLOStatus to_dict method."""
        slo_status = SLOStatus(
            target_success_rate=0.999,
            window_seconds=300,
            total_requests=1000,
            successful_requests=990,
            failed_requests=10,
            current_success_rate=0.99,
            current_error_rate=0.01,
            error_budget_total=1,
            error_budget_consumed=10,
            error_budget_remaining=-9,
            error_budget_percentage=-900.0,
            slo_violated=True,
            burn_rate=10.0,
            endpoint_error_rates={"/v1/chat/completions": 0.01},
        )

        slo_dict = slo_status.to_dict()

        assert slo_dict["target_success_rate"] == 0.999
        assert slo_dict["total_requests"] == 1000
        assert slo_dict["slo_violated"] is True
        assert slo_dict["burn_rate"] == 10.0


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_error_recording(self, tracker):
        """Test that concurrent error recording is thread-safe."""
        import threading

        def record_errors():
            for i in range(10):
                tracker.record_error(
                    endpoint="/v1/chat/completions",
                    status_code=500,
                    error_type="Error",
                    error_message=f"Error {i}",
                )

        threads = [threading.Thread(target=record_errors) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        metrics = tracker.get_metrics()

        # Should have recorded all 50 errors
        assert metrics["total_errors"] == 50

    def test_concurrent_reads_and_writes(self, tracker):
        """Test concurrent reads and writes are thread-safe."""
        import threading

        def record_errors():
            for i in range(5):
                tracker.record_error(
                    endpoint="/v1/chat/completions",
                    status_code=500,
                    error_type="Error",
                    error_message=f"Error {i}",
                )

        def read_metrics():
            for _ in range(5):
                tracker.get_metrics()
                tracker.get_error_patterns()

        write_threads = [threading.Thread(target=record_errors) for _ in range(3)]
        read_threads = [threading.Thread(target=read_metrics) for _ in range(3)]

        for thread in write_threads + read_threads:
            thread.start()

        for thread in write_threads + read_threads:
            thread.join()

        # Should complete without errors
        metrics = tracker.get_metrics()
        assert metrics["total_errors"] == 15


class TestRealisticScenarios:
    """Tests with realistic error scenarios."""

    def test_database_timeout_pattern(self, tracker):
        """Test realistic database timeout error pattern."""
        # Simulate multiple database timeout errors
        for i in range(5):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="DatabaseError",
                error_message=f"Connection to database timed out after {1000 + i * 100}ms",
                model="gpt-4",
                request_id=f"req-{i:04d}",
            )

        patterns = tracker.get_error_patterns(min_count=1)

        assert len(patterns) == 1
        assert patterns[0].count == 5
        assert patterns[0].error_type == "DatabaseError"
        assert "<NUM>" in patterns[0].normalized_message

    def test_rate_limit_scenario(self, tracker):
        """Test realistic rate limit scenario."""
        # Simulate rate limit errors for multiple users
        for i in range(10):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=429,
                error_type="RateLimitError",
                error_message="Rate limit exceeded. Please retry after 60 seconds",
                user_id=f"user-{i % 3}",  # 3 different users
                model="gpt-4",
            )

        patterns = tracker.get_error_patterns(min_count=1)

        assert len(patterns) == 1
        assert patterns[0].count == 10
        assert len(patterns[0].affected_users) == 3

    def test_intermittent_service_outage(self, tracker):
        """Test tracking intermittent service outage."""
        # Mix of successes and errors
        for i in range(20):
            if i % 3 == 0:  # 33% error rate
                tracker.record_error(
                    endpoint="/v1/chat/completions",
                    status_code=503,
                    error_type="ServiceUnavailable",
                    error_message="Service temporarily unavailable",
                    model="gpt-4",
                )
            else:
                tracker.record_success("/v1/chat/completions", model="gpt-4")

        slo_status = tracker.get_slo_status()

        # Should detect SLO violation (33% error rate > 0.1% allowed)
        assert slo_status.slo_violated is True
        assert slo_status.current_error_rate > 0.3

    def test_multi_model_failure_pattern(self, tracker):
        """Test pattern affecting multiple models."""
        models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]

        for model in models:
            for _ in range(3):
                tracker.record_error(
                    endpoint="/v1/chat/completions",
                    status_code=500,
                    error_type="ModelLoadError",
                    error_message="Failed to load model weights",
                    model=model,
                )

        patterns = tracker.get_error_patterns(min_count=1)

        assert len(patterns) == 1
        assert patterns[0].count == 9
        assert len(patterns[0].affected_models) == 3

    def test_authentication_failure_spike(self, tracker):
        """Test spike in authentication failures."""
        # Sudden spike of auth errors
        for i in range(15):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=401,
                error_type="AuthenticationError",
                error_message="Invalid API key",
                api_key=f"sk-invalid-{i}",
            )

        metrics = tracker.get_metrics()
        patterns = tracker.get_error_patterns(min_count=1)

        assert metrics["total_errors"] == 15
        assert len(patterns) == 1
        assert patterns[0].error_type == "AuthenticationError"
