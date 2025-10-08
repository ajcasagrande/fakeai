"""
Comprehensive tests for SLO monitoring and error budgets.

This test suite covers detailed SLO monitoring scenarios including:
- Error budget calculation for various SLO targets (99.9%, 99%, 95%)
- SLO violation detection (within budget, exceeded, at threshold)
- Burn rate calculation (normal, high, zero)
- Success rate tracking with edge cases
- Error budget consumption and remaining calculations
- Per-endpoint error tracking
- Real-world scenarios (gradual errors, spikes, recovery)

All tests use realistic scenarios to ensure production readiness.
"""
#  SPDX-License-Identifier: Apache-2.0

import importlib.util
import sys
from pathlib import Path

import pytest

# Import directly from the module file to avoid package-level app initialization
module_path = Path(__file__).parent.parent / "fakeai" / "error_metrics_tracker.py"
spec = importlib.util.spec_from_file_location("error_metrics_tracker", module_path)
error_metrics_tracker_module = importlib.util.module_from_spec(spec)
sys.modules['error_metrics_tracker'] = error_metrics_tracker_module
spec.loader.exec_module(error_metrics_tracker_module)

ErrorMetricsTracker = error_metrics_tracker_module.ErrorMetricsTracker
SLOStatus = error_metrics_tracker_module.SLOStatus


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def tracker_99_9():
    """Create tracker with 99.9% SLO (0.1% error budget)."""
    return ErrorMetricsTracker(
        max_recent_errors=1000,
        error_budget_slo=0.999,
        window_seconds=300,
        pattern_threshold=3,
    )


@pytest.fixture
def tracker_99():
    """Create tracker with 99% SLO (1% error budget)."""
    return ErrorMetricsTracker(
        max_recent_errors=1000,
        error_budget_slo=0.99,
        window_seconds=300,
        pattern_threshold=3,
    )


@pytest.fixture
def tracker_95():
    """Create tracker with 95% SLO (5% error budget)."""
    return ErrorMetricsTracker(
        max_recent_errors=1000,
        error_budget_slo=0.95,
        window_seconds=300,
        pattern_threshold=3,
    )


# ============================================================================
# TEST CLASS 1: ERROR BUDGET CALCULATION
# ============================================================================


class TestErrorBudgetCalculation:
    """Tests for error budget calculation with various SLO targets."""

    def test_999_slo_with_1000_requests_allows_1_error(self, tracker_99_9):
        """
        Test: 99.9% SLO with 1000 requests = 1 error allowed.

        Expected:
        - Error budget total = 1 (0.1% of 1000)
        - 1 error should consume entire budget
        - Error budget remaining = 0 after 1 error
        """
        # Record 1000 successes
        for _ in range(1000):
            tracker_99_9.record_success("/v1/chat/completions")

        # Record 1 error
        tracker_99_9.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalServerError",
            error_message="Database timeout",
        )

        slo_status = tracker_99_9.get_slo_status()

        # Verify budget calculation
        assert slo_status.total_requests == 1001
        assert slo_status.successful_requests == 1000
        assert slo_status.failed_requests == 1
        assert slo_status.error_budget_total == 1, "1000 requests * 0.001 = 1 error allowed"
        assert slo_status.error_budget_consumed == 1
        assert slo_status.error_budget_remaining == 0
        assert slo_status.error_budget_percentage == 0.0

    def test_99_slo_with_100_requests_allows_1_error(self, tracker_99):
        """
        Test: 99% SLO with 100 requests = 1 error allowed.

        Expected:
        - Error budget total = 1 (1% of 100)
        - 1 error should consume entire budget
        """
        # Record 100 successes
        for _ in range(100):
            tracker_99.record_success("/v1/completions")

        # Record 1 error
        tracker_99.record_error(
            endpoint="/v1/completions",
            status_code=429,
            error_type="RateLimitError",
            error_message="Rate limit exceeded",
        )

        slo_status = tracker_99.get_slo_status()

        # Verify budget calculation
        assert slo_status.total_requests == 101
        assert slo_status.error_budget_total == 1, "100 requests * 0.01 = 1 error allowed"
        assert slo_status.error_budget_consumed == 1
        assert slo_status.error_budget_remaining == 0

    def test_95_slo_with_100_requests_allows_5_errors(self, tracker_95):
        """
        Test: 95% SLO with 100 requests = 5 errors allowed.

        Expected:
        - Error budget total = 5 (5% of 100)
        - 5 errors should consume entire budget
        """
        # Record 100 successes
        for _ in range(100):
            tracker_95.record_success("/v1/embeddings")

        # Record 5 errors
        for i in range(5):
            tracker_95.record_error(
                endpoint="/v1/embeddings",
                status_code=503,
                error_type="ServiceUnavailable",
                error_message=f"Service unavailable attempt {i+1}",
            )

        slo_status = tracker_95.get_slo_status()

        # Verify budget calculation
        assert slo_status.total_requests == 105
        assert slo_status.error_budget_total == 5, "100 requests * 0.05 = 5 errors allowed"
        assert slo_status.error_budget_consumed == 5
        assert slo_status.error_budget_remaining == 0

    def test_error_budget_with_partial_consumption(self, tracker_99):
        """
        Test: Partial error budget consumption.

        Expected:
        - Budget total = 10 (1000 requests * 0.01)
        - Consume 3 errors
        - Remaining = 7
        - Percentage = 70%
        """
        # Record 1000 successes
        for _ in range(1000):
            tracker_99.record_success("/v1/chat/completions")

        # Record 3 errors (30% of budget)
        for i in range(3):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message=f"Error {i+1}",
            )

        slo_status = tracker_99.get_slo_status()

        # Verify partial consumption
        assert slo_status.error_budget_total == 10
        assert slo_status.error_budget_consumed == 3
        assert slo_status.error_budget_remaining == 7
        assert abs(slo_status.error_budget_percentage - 70.0) < 0.1

    def test_error_budget_zero_errors(self, tracker_99_9):
        """
        Test: Error budget with zero errors.

        Expected:
        - Budget fully available (100%)
        - No consumption
        """
        # Record only successes
        for _ in range(500):
            tracker_99_9.record_success("/v1/chat/completions")

        slo_status = tracker_99_9.get_slo_status()

        # Verify no consumption
        assert slo_status.error_budget_consumed == 0
        assert slo_status.error_budget_remaining == slo_status.error_budget_total
        assert slo_status.error_budget_percentage == 100.0


# ============================================================================
# TEST CLASS 2: SLO VIOLATION DETECTION
# ============================================================================


class TestSLOViolationDetection:
    """Tests for detecting SLO violations."""

    def test_not_violated_when_within_budget(self, tracker_99):
        """
        Test: SLO not violated when error rate is within budget.

        Expected:
        - 99% success rate meets 99% SLO
        - slo_violated = False
        """
        # Record 99 successes, 1 error = 99% success rate
        for _ in range(99):
            tracker_99.record_success("/v1/chat/completions")

        tracker_99.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalServerError",
            error_message="Temporary error",
        )

        slo_status = tracker_99.get_slo_status()

        # Verify no violation
        assert slo_status.current_success_rate == 0.99
        assert slo_status.slo_violated is False

    def test_violated_when_budget_exceeded(self, tracker_99):
        """
        Test: SLO violated when error rate exceeds budget.

        Expected:
        - 98% success rate violates 99% SLO
        - slo_violated = True
        """
        # Record 98 successes, 2 errors = 98% success rate
        for _ in range(98):
            tracker_99.record_success("/v1/chat/completions")

        for _ in range(2):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message="Critical error",
            )

        slo_status = tracker_99.get_slo_status()

        # Verify violation
        assert slo_status.current_success_rate == 0.98
        assert slo_status.slo_violated is True

    def test_exactly_at_threshold_not_violated(self, tracker_99):
        """
        Test: Exactly at SLO threshold should not be violated.

        Expected:
        - Exactly 99% success rate meets 99% SLO
        - slo_violated = False
        """
        # Record exactly 99 successes, 1 error
        for _ in range(99):
            tracker_99.record_success("/v1/completions")

        tracker_99.record_error(
            endpoint="/v1/completions",
            status_code=500,
            error_type="InternalServerError",
            error_message="Edge case error",
        )

        slo_status = tracker_99.get_slo_status()

        # Verify at threshold (not violated)
        assert slo_status.current_success_rate == 0.99
        assert slo_status.target_success_rate == 0.99
        assert slo_status.slo_violated is False

    def test_just_below_threshold_is_violated(self, tracker_99):
        """
        Test: Just below SLO threshold is violated.

        Expected:
        - 98.99% success rate violates 99% SLO
        - slo_violated = True
        """
        # Record 9899 successes, 101 errors = 98.99% success rate
        for _ in range(9899):
            tracker_99.record_success("/v1/chat/completions")

        for _ in range(101):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message="Error",
            )

        slo_status = tracker_99.get_slo_status()

        # Verify violation
        assert slo_status.current_success_rate < 0.99
        assert abs(slo_status.current_success_rate - 0.9899) < 0.0001
        assert slo_status.slo_violated is True

    def test_multiple_slo_targets_violations(self):
        """
        Test: Different SLO targets detect violations correctly.

        Expected:
        - 96% success violates 99% SLO but not 95% SLO
        """
        # Test with 99% SLO
        tracker_99 = ErrorMetricsTracker(error_budget_slo=0.99)
        for _ in range(96):
            tracker_99.record_success("/v1/chat/completions")
        for _ in range(4):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="Error",
                error_message="Test",
            )

        slo_99 = tracker_99.get_slo_status()
        assert slo_99.current_success_rate == 0.96
        assert slo_99.slo_violated is True, "96% violates 99% SLO"

        # Test with 95% SLO
        tracker_95 = ErrorMetricsTracker(error_budget_slo=0.95)
        for _ in range(96):
            tracker_95.record_success("/v1/chat/completions")
        for _ in range(4):
            tracker_95.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="Error",
                error_message="Test",
            )

        slo_95 = tracker_95.get_slo_status()
        assert slo_95.current_success_rate == 0.96
        assert slo_95.slo_violated is False, "96% meets 95% SLO"


# ============================================================================
# TEST CLASS 3: BURN RATE CALCULATION
# ============================================================================


class TestBurnRateCalculation:
    """Tests for burn rate calculation."""

    def test_normal_burn_rate_is_1x(self, tracker_99):
        """
        Test: Normal error rate = 1.0x burn rate.

        Expected:
        - Error rate exactly at SLO target = 1.0x burn rate
        - 99% SLO allows 1% errors
        - 1% error rate = 1.0x burn rate
        """
        # Record 99 successes, 1 error = 1% error rate
        for _ in range(99):
            tracker_99.record_success("/v1/chat/completions")

        tracker_99.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalServerError",
            error_message="Normal error",
        )

        slo_status = tracker_99.get_slo_status()

        # Verify 1x burn rate
        assert slo_status.current_error_rate == 0.01
        assert abs(slo_status.burn_rate - 1.0) < 0.01, "Error rate at SLO = 1x burn"

    def test_high_burn_rate_10x(self, tracker_99_9):
        """
        Test: High burn rate = 10x (alert threshold).

        Expected:
        - 99.9% SLO allows 0.1% errors
        - 1% error rate = 10x burn rate
        """
        # Record 99 successes, 1 error = 1% error rate
        for _ in range(99):
            tracker_99_9.record_success("/v1/chat/completions")

        tracker_99_9.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalServerError",
            error_message="High error rate",
        )

        slo_status = tracker_99_9.get_slo_status()

        # Verify 10x burn rate
        # Current error rate = 1/100 = 1%
        # Target error rate = 0.1%
        # Burn rate = 1% / 0.1% = 10
        assert slo_status.current_error_rate == 0.01
        assert abs(slo_status.burn_rate - 10.0) < 0.1, "1% error rate = 10x burn for 99.9% SLO"

    def test_zero_errors_zero_burn_rate(self, tracker_99):
        """
        Test: Zero errors = 0 burn rate.

        Expected:
        - No errors = 0% error rate = 0x burn rate
        """
        # Record only successes
        for _ in range(100):
            tracker_99.record_success("/v1/chat/completions")

        slo_status = tracker_99.get_slo_status()

        # Verify zero burn rate
        assert slo_status.current_error_rate == 0.0
        assert slo_status.burn_rate == 0.0

    def test_burn_rate_2x(self, tracker_95):
        """
        Test: Burn rate at 2x.

        Expected:
        - 95% SLO allows 5% errors
        - 10% error rate = 2x burn rate
        """
        # Record 90 successes, 10 errors = 10% error rate
        for _ in range(90):
            tracker_95.record_success("/v1/chat/completions")

        for _ in range(10):
            tracker_95.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message="Error",
            )

        slo_status = tracker_95.get_slo_status()

        # Verify 2x burn rate
        assert slo_status.current_error_rate == 0.10
        assert abs(slo_status.burn_rate - 2.0) < 0.01, "10% error rate = 2x burn for 95% SLO"

    def test_burn_rate_below_1x(self, tracker_99):
        """
        Test: Burn rate below 1x (healthy).

        Expected:
        - Error rate below SLO = burn rate < 1.0
        - 99% SLO allows 1% errors
        - 0.5% error rate = 0.5x burn rate
        """
        # Record 199 successes, 1 error = 0.5% error rate
        for _ in range(199):
            tracker_99.record_success("/v1/chat/completions")

        tracker_99.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalServerError",
            error_message="Rare error",
        )

        slo_status = tracker_99.get_slo_status()

        # Verify 0.5x burn rate
        assert slo_status.current_error_rate == 0.005
        assert abs(slo_status.burn_rate - 0.5) < 0.01, "0.5% error rate = 0.5x burn"

    def test_burn_rate_extremely_high(self, tracker_99_9):
        """
        Test: Extremely high burn rate (100x).

        Expected:
        - 99.9% SLO allows 0.1% errors
        - 10% error rate = 100x burn rate
        """
        # Record 90 successes, 10 errors = 10% error rate
        for _ in range(90):
            tracker_99_9.record_success("/v1/chat/completions")

        for _ in range(10):
            tracker_99_9.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message="Critical error",
            )

        slo_status = tracker_99_9.get_slo_status()

        # Verify 100x burn rate
        assert slo_status.current_error_rate == 0.10
        assert abs(slo_status.burn_rate - 100.0) < 1.0, "10% error rate = 100x burn"


# ============================================================================
# TEST CLASS 4: SUCCESS RATE TRACKING
# ============================================================================


class TestSuccessRateTracking:
    """Tests for success rate calculation."""

    def test_99_successes_1_error_equals_99_percent(self, tracker_99):
        """
        Test: 99 successes, 1 error = 99% success rate.
        """
        for _ in range(99):
            tracker_99.record_success("/v1/chat/completions")

        tracker_99.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalServerError",
            error_message="Error",
        )

        slo_status = tracker_99.get_slo_status()

        assert slo_status.total_requests == 100
        assert slo_status.successful_requests == 99
        assert slo_status.failed_requests == 1
        assert slo_status.current_success_rate == 0.99

    def test_zero_requests_default_100_percent(self, tracker_99):
        """
        Test: 0 requests = 100% success (default).

        Expected:
        - No requests = assume healthy state
        - Success rate = 100%
        - No SLO violation
        """
        slo_status = tracker_99.get_slo_status()

        assert slo_status.total_requests == 0
        assert slo_status.successful_requests == 0
        assert slo_status.failed_requests == 0
        assert slo_status.current_success_rate == 1.0
        assert slo_status.current_error_rate == 0.0
        assert slo_status.slo_violated is False

    def test_all_successes_100_percent(self, tracker_99):
        """
        Test: All successes = 100% success rate.
        """
        for _ in range(1000):
            tracker_99.record_success("/v1/chat/completions")

        slo_status = tracker_99.get_slo_status()

        assert slo_status.total_requests == 1000
        assert slo_status.successful_requests == 1000
        assert slo_status.failed_requests == 0
        assert slo_status.current_success_rate == 1.0

    def test_all_failures_0_percent(self, tracker_99):
        """
        Test: All failures = 0% success rate.
        """
        for _ in range(100):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message="Complete failure",
            )

        slo_status = tracker_99.get_slo_status()

        assert slo_status.total_requests == 100
        assert slo_status.successful_requests == 0
        assert slo_status.failed_requests == 100
        assert slo_status.current_success_rate == 0.0
        assert slo_status.current_error_rate == 1.0

    def test_50_50_split(self, tracker_99):
        """
        Test: 50% success, 50% failure.
        """
        for _ in range(50):
            tracker_99.record_success("/v1/chat/completions")

        for _ in range(50):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message="Error",
            )

        slo_status = tracker_99.get_slo_status()

        assert slo_status.total_requests == 100
        assert slo_status.successful_requests == 50
        assert slo_status.failed_requests == 50
        assert slo_status.current_success_rate == 0.5


# ============================================================================
# TEST CLASS 5: ERROR BUDGET CONSUMPTION
# ============================================================================


class TestErrorBudgetConsumption:
    """Tests for error budget consumption tracking."""

    def test_starts_at_zero_consumption(self, tracker_99):
        """
        Test: Error budget starts at 0% consumed.
        """
        # Record some successes but no errors
        for _ in range(100):
            tracker_99.record_success("/v1/chat/completions")

        slo_status = tracker_99.get_slo_status()

        assert slo_status.error_budget_consumed == 0
        assert slo_status.error_budget_percentage == 100.0

    def test_increments_with_each_error(self, tracker_99):
        """
        Test: Error budget increments with each error.
        """
        # Record successes
        for _ in range(1000):
            tracker_99.record_success("/v1/chat/completions")

        # Record errors one by one and verify incrementing
        for i in range(1, 6):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message=f"Error {i}",
            )

            slo_status = tracker_99.get_slo_status()
            assert slo_status.error_budget_consumed == i

    def test_remaining_calculated_correctly(self, tracker_99):
        """
        Test: Error budget remaining = total - consumed.
        """
        # Record 1000 successes (budget = 10)
        for _ in range(1000):
            tracker_99.record_success("/v1/chat/completions")

        # Consume 3 errors
        for _ in range(3):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message="Error",
            )

        slo_status = tracker_99.get_slo_status()

        assert slo_status.error_budget_total == 10
        assert slo_status.error_budget_consumed == 3
        assert slo_status.error_budget_remaining == 7
        assert slo_status.error_budget_remaining == (
            slo_status.error_budget_total - slo_status.error_budget_consumed
        )

    def test_percentage_accurate(self, tracker_99):
        """
        Test: Error budget percentage is accurate.

        Expected:
        - Budget = 10, consumed = 3, remaining = 7
        - Percentage = 70%
        """
        # Record 1000 successes
        for _ in range(1000):
            tracker_99.record_success("/v1/chat/completions")

        # Consume 3 errors
        for _ in range(3):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message="Error",
            )

        slo_status = tracker_99.get_slo_status()

        expected_percentage = (7 / 10) * 100  # 70%
        assert abs(slo_status.error_budget_percentage - expected_percentage) < 0.1

    def test_cannot_go_negative(self, tracker_99):
        """
        Test: Error budget remaining cannot go negative.

        Expected:
        - When errors exceed budget, remaining = 0 (not negative)
        """
        # Record 100 successes (budget = 1)
        for _ in range(100):
            tracker_99.record_success("/v1/chat/completions")

        # Consume 5 errors (exceeds budget of 1)
        for _ in range(5):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message="Error",
            )

        slo_status = tracker_99.get_slo_status()

        assert slo_status.error_budget_consumed == 5
        assert slo_status.error_budget_remaining == 0, "Budget remaining should not be negative"
        assert slo_status.error_budget_remaining >= 0

    def test_percentage_at_full_consumption(self, tracker_99):
        """
        Test: Percentage = 0% when budget fully consumed.
        """
        # Record 100 successes (budget = 1)
        for _ in range(100):
            tracker_99.record_success("/v1/chat/completions")

        # Consume entire budget
        tracker_99.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalServerError",
            error_message="Error",
        )

        slo_status = tracker_99.get_slo_status()

        assert slo_status.error_budget_remaining == 0
        assert slo_status.error_budget_percentage == 0.0


# ============================================================================
# TEST CLASS 6: PER-ENDPOINT TRACKING
# ============================================================================


class TestPerEndpointTracking:
    """Tests for per-endpoint error tracking."""

    def test_different_endpoints_tracked_separately(self, tracker_99):
        """
        Test: Different endpoints have separate error rates.
        """
        # Endpoint 1: 90% success
        for _ in range(90):
            tracker_99.record_success("/v1/chat/completions")
        for _ in range(10):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="Error",
                error_message="Error",
            )

        # Endpoint 2: 95% success
        for _ in range(95):
            tracker_99.record_success("/v1/completions")
        for _ in range(5):
            tracker_99.record_error(
                endpoint="/v1/completions",
                status_code=500,
                error_type="Error",
                error_message="Error",
            )

        slo_status = tracker_99.get_slo_status()

        # Verify per-endpoint rates
        assert "/v1/chat/completions" in slo_status.endpoint_error_rates
        assert "/v1/completions" in slo_status.endpoint_error_rates

        chat_error_rate = slo_status.endpoint_error_rates["/v1/chat/completions"]
        completions_error_rate = slo_status.endpoint_error_rates["/v1/completions"]

        assert abs(chat_error_rate - 0.10) < 0.01, "Chat completions = 10% error"
        assert abs(completions_error_rate - 0.05) < 0.01, "Completions = 5% error"

    def test_endpoint_error_rates_calculated(self, tracker_99):
        """
        Test: Endpoint error rates are calculated correctly.
        """
        # Create different error rates for different endpoints
        endpoints = [
            ("/v1/chat/completions", 100, 5),  # 5% error
            ("/v1/embeddings", 200, 2),         # 1% error
            ("/v1/images/generations", 50, 10), # 20% error
        ]

        for endpoint, successes, errors in endpoints:
            for _ in range(successes):
                tracker_99.record_success(endpoint)
            for _ in range(errors):
                tracker_99.record_error(
                    endpoint=endpoint,
                    status_code=500,
                    error_type="Error",
                    error_message="Error",
                )

        slo_status = tracker_99.get_slo_status()

        # Verify each endpoint
        assert abs(
            slo_status.endpoint_error_rates["/v1/chat/completions"] - 0.05
        ) < 0.01
        assert abs(
            slo_status.endpoint_error_rates["/v1/embeddings"] - 0.01
        ) < 0.01
        assert abs(
            slo_status.endpoint_error_rates["/v1/images/generations"] - 0.20
        ) < 0.01

    def test_zero_requests_endpoint_not_in_rates(self, tracker_99):
        """
        Test: Endpoint with no requests not included in error rates.
        """
        # Record requests for one endpoint only
        tracker_99.record_success("/v1/chat/completions")

        slo_status = tracker_99.get_slo_status()

        # Only the endpoint with requests should be present
        assert "/v1/chat/completions" in slo_status.endpoint_error_rates
        assert "/v1/completions" not in slo_status.endpoint_error_rates


# ============================================================================
# TEST CLASS 7: REAL-WORLD SCENARIOS
# ============================================================================


class TestRealWorldScenarios:
    """Tests for realistic production scenarios."""

    def test_gradual_error_accumulation(self, tracker_99):
        """
        Test: Gradual error accumulation over time.

        Scenario:
        - Start healthy
        - Gradually accumulate errors
        - Monitor burn rate increase
        """
        # Phase 1: Healthy operation (100 requests, 0 errors)
        for _ in range(100):
            tracker_99.record_success("/v1/chat/completions")

        slo_1 = tracker_99.get_slo_status()
        assert slo_1.slo_violated is False
        assert slo_1.burn_rate == 0.0

        # Phase 2: Some errors appear (100 requests, 1 error = 0.5% rate)
        for _ in range(99):
            tracker_99.record_success("/v1/chat/completions")
        tracker_99.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="DatabaseTimeout",
            error_message="DB timeout",
        )

        slo_2 = tracker_99.get_slo_status()
        assert slo_2.slo_violated is False
        assert slo_2.burn_rate < 1.0, "Still below target"

        # Phase 3: Error rate increases (100 requests, 2 errors = 1.0% rate)
        for _ in range(98):
            tracker_99.record_success("/v1/chat/completions")
        for _ in range(2):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=503,
                error_type="ServiceUnavailable",
                error_message="Service degraded",
            )

        slo_3 = tracker_99.get_slo_status()
        # Total: 297 success, 3 errors = 1% error rate
        assert abs(slo_3.current_error_rate - 0.01) < 0.001
        assert abs(slo_3.burn_rate - 1.0) < 0.1, "Now at target burn rate"

    def test_sudden_error_spike(self, tracker_99_9):
        """
        Test: Sudden spike in errors (incident).

        Scenario:
        - Normal operation
        - Sudden error spike
        - Budget exhausted quickly
        - High burn rate alert
        """
        # Normal operation: 1000 requests, 0 errors
        for _ in range(1000):
            tracker_99_9.record_success("/v1/chat/completions")

        slo_before = tracker_99_9.get_slo_status()
        assert slo_before.burn_rate == 0.0

        # Sudden spike: 10 errors in quick succession
        for i in range(10):
            tracker_99_9.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="DatabaseFailure",
                error_message=f"DB connection failed {i+1}",
            )

        slo_after = tracker_99_9.get_slo_status()

        # Verify spike detected
        assert slo_after.failed_requests == 10
        assert slo_after.burn_rate > 10.0, "High burn rate during spike"
        assert slo_after.slo_violated is True
        assert slo_after.error_budget_remaining == 0

    def test_recovery_after_incident(self, tracker_99):
        """
        Test: Service recovery after incident.

        Scenario:
        - Incident causes errors
        - Service recovers
        - Error rate normalizes
        - But budget remains consumed
        """
        # Incident: 50 requests, 5 errors (10% error rate)
        for _ in range(45):
            tracker_99.record_success("/v1/chat/completions")
        for _ in range(5):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="IncidentError",
                error_message="Service down",
            )

        slo_incident = tracker_99.get_slo_status()
        budget_after_incident = slo_incident.error_budget_consumed

        # Recovery: 950 successful requests, 0 errors
        for _ in range(950):
            tracker_99.record_success("/v1/chat/completions")

        slo_recovery = tracker_99.get_slo_status()

        # Verify recovery
        # Total: 995 success, 5 errors = 0.5% error rate (back to healthy)
        assert slo_recovery.current_error_rate == 0.005
        assert slo_recovery.burn_rate < 1.0, "Burn rate normalized"
        # But budget consumption persists
        assert slo_recovery.error_budget_consumed == budget_after_incident

    def test_multiple_partial_incidents(self, tracker_99):
        """
        Test: Multiple small incidents over time.

        Scenario:
        - Several small error spikes
        - Each spike consumes part of budget
        - Eventually budget exhausted
        """
        # Incident 1: 2 errors
        for _ in range(100):
            tracker_99.record_success("/v1/chat/completions")
        for _ in range(2):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="Error",
                error_message="Incident 1",
            )

        slo_1 = tracker_99.get_slo_status()
        consumed_1 = slo_1.error_budget_consumed

        # Incident 2: 2 more errors
        for _ in range(100):
            tracker_99.record_success("/v1/chat/completions")
        for _ in range(2):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=503,
                error_type="Error",
                error_message="Incident 2",
            )

        slo_2 = tracker_99.get_slo_status()
        consumed_2 = slo_2.error_budget_consumed

        # Incident 3: 2 more errors
        for _ in range(100):
            tracker_99.record_success("/v1/chat/completions")
        for _ in range(2):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=429,
                error_type="RateLimit",
                error_message="Incident 3",
            )

        slo_3 = tracker_99.get_slo_status()
        consumed_3 = slo_3.error_budget_consumed

        # Verify cumulative consumption
        assert consumed_2 > consumed_1, "Budget consumption accumulates"
        assert consumed_3 > consumed_2, "Budget consumption accumulates"
        assert consumed_3 == 6, "Total 6 errors consumed"

    def test_high_traffic_with_acceptable_errors(self, tracker_99_9):
        """
        Test: High traffic scenario with acceptable error rate.

        Scenario:
        - 10,000 requests
        - 10 errors (0.1% error rate)
        - Exactly at SLO target
        - Should not violate SLO
        """
        # Simulate high traffic
        for _ in range(10000):
            tracker_99_9.record_success("/v1/chat/completions")

        # 10 errors = 0.1% error rate (exactly at 99.9% SLO)
        for i in range(10):
            tracker_99_9.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="InternalServerError",
                error_message=f"Acceptable error {i+1}",
            )

        slo_status = tracker_99_9.get_slo_status()

        # Verify high traffic handling
        assert slo_status.total_requests == 10010
        assert slo_status.failed_requests == 10
        assert abs(slo_status.current_error_rate - 0.001) < 0.0001
        assert abs(slo_status.burn_rate - 1.0) < 0.1
        assert slo_status.slo_violated is False

    def test_endpoint_specific_incident(self, tracker_99):
        """
        Test: Incident affecting only specific endpoint.

        Scenario:
        - Multiple endpoints
        - One endpoint has incident
        - Other endpoints remain healthy
        - Overall SLO may still be met
        """
        # Endpoint 1: Healthy (1000 requests, 0 errors)
        for _ in range(1000):
            tracker_99.record_success("/v1/embeddings")

        # Endpoint 2: Incident (100 requests, 20 errors = 20% rate)
        for _ in range(80):
            tracker_99.record_success("/v1/chat/completions")
        for _ in range(20):
            tracker_99.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="ModelError",
                error_message="Model unavailable",
            )

        slo_status = tracker_99.get_slo_status()

        # Overall: 1080 success, 20 errors = 1.8% error rate
        # Violates 99% SLO but shows endpoint-specific issue
        assert abs(slo_status.current_error_rate - 0.018) < 0.001
        assert slo_status.slo_violated is True

        # Verify endpoint-specific rates
        embeddings_rate = slo_status.endpoint_error_rates["/v1/embeddings"]
        chat_rate = slo_status.endpoint_error_rates["/v1/chat/completions"]

        assert embeddings_rate == 0.0, "Embeddings healthy"
        assert abs(chat_rate - 0.20) < 0.01, "Chat has 20% error rate"


# ============================================================================
# TEST CLASS 8: EDGE CASES AND BOUNDARY CONDITIONS
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_single_request_single_error(self, tracker_99):
        """
        Test: Single request that fails.

        Expected:
        - 100% error rate
        - Violates any realistic SLO
        """
        tracker_99.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="Error",
            error_message="First request failed",
        )

        slo_status = tracker_99.get_slo_status()

        assert slo_status.total_requests == 1
        assert slo_status.current_error_rate == 1.0
        assert slo_status.slo_violated is True

    def test_very_strict_slo(self):
        """
        Test: Very strict SLO (99.99%).
        """
        tracker = ErrorMetricsTracker(error_budget_slo=0.9999)

        # 10,000 requests, 1 error = 99.99% success
        for _ in range(10000):
            tracker.record_success("/v1/chat/completions")

        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="Error",
            error_message="Single error",
        )

        slo_status = tracker.get_slo_status()

        # Should just meet SLO
        assert abs(slo_status.current_success_rate - 0.9999) < 0.00001
        assert slo_status.slo_violated is False

    def test_very_loose_slo(self):
        """
        Test: Very loose SLO (90%).
        """
        tracker = ErrorMetricsTracker(error_budget_slo=0.90)

        # 90 successes, 10 errors = 90% success
        for _ in range(90):
            tracker.record_success("/v1/chat/completions")
        for _ in range(10):
            tracker.record_error(
                endpoint="/v1/chat/completions",
                status_code=500,
                error_type="Error",
                error_message="Error",
            )

        slo_status = tracker.get_slo_status()

        # Should just meet SLO
        assert slo_status.current_success_rate == 0.90
        assert slo_status.slo_violated is False

    def test_fractional_error_budget(self, tracker_99_9):
        """
        Test: Error budget calculation with fractional results.

        Expected:
        - Small number of requests may result in 0 error budget
        - 10 requests * 0.001 = 0.01 errors = int(0) = 0 budget
        """
        # Only 10 requests
        for _ in range(10):
            tracker_99_9.record_success("/v1/chat/completions")

        slo_status = tracker_99_9.get_slo_status()

        # With 99.9% SLO and 10 requests, budget = int(10 * 0.001) = 0
        assert slo_status.error_budget_total == 0

        # Any error will violate
        tracker_99_9.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="Error",
            error_message="Error",
        )

        slo_status_after = tracker_99_9.get_slo_status()
        assert slo_status_after.slo_violated is True


# ============================================================================
# TEST CLASS 9: SLO STATUS OBJECT
# ============================================================================


class TestSLOStatusObject:
    """Tests for SLOStatus dataclass."""

    def test_slo_status_to_dict(self, tracker_99):
        """
        Test: SLOStatus can be converted to dictionary.
        """
        tracker_99.record_success("/v1/chat/completions")
        slo_status = tracker_99.get_slo_status()

        status_dict = slo_status.to_dict()

        # Verify dictionary contains expected keys
        assert isinstance(status_dict, dict)
        assert "target_success_rate" in status_dict
        assert "current_success_rate" in status_dict
        assert "error_budget_total" in status_dict
        assert "error_budget_remaining" in status_dict
        assert "burn_rate" in status_dict
        assert "slo_violated" in status_dict

    def test_slo_status_immutable_after_creation(self, tracker_99):
        """
        Test: SLOStatus represents point-in-time snapshot.
        """
        tracker_99.record_success("/v1/chat/completions")
        slo_1 = tracker_99.get_slo_status()

        # Record more data
        tracker_99.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="Error",
            error_message="Error",
        )

        slo_2 = tracker_99.get_slo_status()

        # Original snapshot unchanged
        assert slo_1.failed_requests == 0
        assert slo_2.failed_requests == 1


# ============================================================================
# TEST CLASS 10: INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_complete_monitoring_workflow(self, tracker_99):
        """
        Test: Complete SLO monitoring workflow.

        Scenario:
        1. Start monitoring
        2. Record mixed success/failures
        3. Check SLO status
        4. Verify all metrics
        """
        # Phase 1: Initial requests
        for i in range(100):
            if i % 10 == 0:  # 10% error rate
                tracker_99.record_error(
                    endpoint="/v1/chat/completions",
                    status_code=500,
                    error_type="Error",
                    error_message=f"Error {i}",
                )
            else:
                tracker_99.record_success("/v1/chat/completions")

        slo_status = tracker_99.get_slo_status()

        # Verify comprehensive status
        assert slo_status.total_requests == 100
        assert slo_status.successful_requests == 90
        assert slo_status.failed_requests == 10
        assert slo_status.current_success_rate == 0.90
        assert slo_status.current_error_rate == 0.10
        assert slo_status.slo_violated is True  # 90% < 99%
        assert slo_status.burn_rate > 1.0  # 10x expected rate
        assert slo_status.error_budget_consumed == 10
        assert "/v1/chat/completions" in slo_status.endpoint_error_rates

    def test_multiple_slo_targets_parallel(self):
        """
        Test: Multiple trackers with different SLOs running in parallel.
        """
        trackers = {
            "strict": ErrorMetricsTracker(error_budget_slo=0.999),
            "moderate": ErrorMetricsTracker(error_budget_slo=0.99),
            "relaxed": ErrorMetricsTracker(error_budget_slo=0.95),
        }

        # Same traffic pattern for all
        for _ in range(98):
            for tracker in trackers.values():
                tracker.record_success("/v1/chat/completions")

        for _ in range(2):
            for tracker in trackers.values():
                tracker.record_error(
                    endpoint="/v1/chat/completions",
                    status_code=500,
                    error_type="Error",
                    error_message="Error",
                )

        # 98% success rate
        results = {name: t.get_slo_status() for name, t in trackers.items()}

        # Verify different SLO evaluations
        assert results["strict"].slo_violated is True   # 98% < 99.9%
        assert results["moderate"].slo_violated is True # 98% < 99%
        assert results["relaxed"].slo_violated is False # 98% >= 95%

    def test_prometheus_export_includes_slo_metrics(self, tracker_99):
        """
        Test: Prometheus export includes SLO-related metrics.
        """
        # Generate some traffic
        for _ in range(99):
            tracker_99.record_success("/v1/chat/completions")

        tracker_99.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="Error",
            error_message="Error",
        )

        prometheus_output = tracker_99.get_prometheus_metrics()

        # Verify SLO metrics present
        assert "error_budget_remaining" in prometheus_output
        assert "error_budget_percentage" in prometheus_output
        assert "error_burn_rate" in prometheus_output
        assert "error_slo_violated" in prometheus_output
