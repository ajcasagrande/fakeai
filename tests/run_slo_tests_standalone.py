#!/usr/bin/env python3
"""
Standalone test runner for SLO monitoring tests.

This bypasses pytest's conftest to demonstrate the tests work independently.
Run with: python tests/run_slo_tests_standalone.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the module directly
import importlib.util

module_path = Path(__file__).parent.parent / "fakeai" / "error_metrics_tracker.py"
spec = importlib.util.spec_from_file_location("error_metrics_tracker", module_path)
error_metrics_tracker_module = importlib.util.module_from_spec(spec)
sys.modules['error_metrics_tracker'] = error_metrics_tracker_module
spec.loader.exec_module(error_metrics_tracker_module)

ErrorMetricsTracker = error_metrics_tracker_module.ErrorMetricsTracker
SLOStatus = error_metrics_tracker_module.SLOStatus

# Run a few key tests manually
def test_999_slo_with_1000_requests():
    """Test 99.9% SLO with 1000 requests allows 1 error."""
    print("Testing: 99.9% SLO with 1000 requests...")

    tracker = ErrorMetricsTracker(error_budget_slo=0.999)

    # Record 1000 successes
    for _ in range(1000):
        tracker.record_success("/v1/chat/completions")

    # Record 1 error
    tracker.record_error(
        endpoint="/v1/chat/completions",
        status_code=500,
        error_type="InternalServerError",
        error_message="Database timeout",
    )

    slo_status = tracker.get_slo_status()

    # Verify
    assert slo_status.total_requests == 1001, f"Expected 1001 requests, got {slo_status.total_requests}"
    assert slo_status.error_budget_total == 1, f"Expected budget of 1, got {slo_status.error_budget_total}"
    assert slo_status.error_budget_consumed == 1, f"Expected 1 consumed, got {slo_status.error_budget_consumed}"
    assert slo_status.error_budget_remaining == 0, f"Expected 0 remaining, got {slo_status.error_budget_remaining}"

    print("  ✓ PASSED")


def test_burn_rate_10x():
    """Test burn rate at 10x (alert threshold)."""
    print("Testing: 10x burn rate...")

    tracker = ErrorMetricsTracker(error_budget_slo=0.999)

    # Record 99 successes, 1 error = 1% error rate
    for _ in range(99):
        tracker.record_success("/v1/chat/completions")

    tracker.record_error(
        endpoint="/v1/chat/completions",
        status_code=500,
        error_type="InternalServerError",
        error_message="High error rate",
    )

    slo_status = tracker.get_slo_status()

    # Verify 10x burn rate
    assert slo_status.current_error_rate == 0.01, f"Expected 1% error rate, got {slo_status.current_error_rate}"
    assert abs(slo_status.burn_rate - 10.0) < 0.1, f"Expected ~10x burn rate, got {slo_status.burn_rate}"

    print("  ✓ PASSED")


def test_zero_errors_zero_burn():
    """Test zero errors = 0 burn rate."""
    print("Testing: Zero errors, zero burn rate...")

    tracker = ErrorMetricsTracker(error_budget_slo=0.99)

    # Record only successes
    for _ in range(100):
        tracker.record_success("/v1/chat/completions")

    slo_status = tracker.get_slo_status()

    # Verify
    assert slo_status.current_error_rate == 0.0, f"Expected 0% error rate, got {slo_status.current_error_rate}"
    assert slo_status.burn_rate == 0.0, f"Expected 0 burn rate, got {slo_status.burn_rate}"

    print("  ✓ PASSED")


def test_slo_violation():
    """Test SLO violation detection."""
    print("Testing: SLO violation detection...")

    tracker = ErrorMetricsTracker(error_budget_slo=0.99)

    # Record 98 successes, 2 errors = 98% success rate (violates 99% SLO)
    for _ in range(98):
        tracker.record_success("/v1/chat/completions")

    for _ in range(2):
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="InternalServerError",
            error_message="Critical error",
        )

    slo_status = tracker.get_slo_status()

    # Verify
    assert slo_status.current_success_rate == 0.98, f"Expected 98% success, got {slo_status.current_success_rate}"
    assert slo_status.slo_violated is True, f"Expected SLO violated, got {slo_status.slo_violated}"

    print("  ✓ PASSED")


def test_per_endpoint_tracking():
    """Test per-endpoint error rates."""
    print("Testing: Per-endpoint tracking...")

    tracker = ErrorMetricsTracker(error_budget_slo=0.99)

    # Endpoint 1: 10% error rate
    for _ in range(90):
        tracker.record_success("/v1/chat/completions")
    for _ in range(10):
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="Error",
            error_message="Error",
        )

    # Endpoint 2: 5% error rate
    for _ in range(95):
        tracker.record_success("/v1/embeddings")
    for _ in range(5):
        tracker.record_error(
            endpoint="/v1/embeddings",
            status_code=500,
            error_type="Error",
            error_message="Error",
        )

    slo_status = tracker.get_slo_status()

    # Verify
    chat_rate = slo_status.endpoint_error_rates["/v1/chat/completions"]
    embeddings_rate = slo_status.endpoint_error_rates["/v1/embeddings"]

    assert abs(chat_rate - 0.10) < 0.01, f"Expected 10% error rate for chat, got {chat_rate}"
    assert abs(embeddings_rate - 0.05) < 0.01, f"Expected 5% error rate for embeddings, got {embeddings_rate}"

    print("  ✓ PASSED")


def test_gradual_error_accumulation():
    """Test gradual error accumulation scenario."""
    print("Testing: Gradual error accumulation...")

    tracker = ErrorMetricsTracker(error_budget_slo=0.99)

    # Phase 1: Healthy
    for _ in range(100):
        tracker.record_success("/v1/chat/completions")

    slo_1 = tracker.get_slo_status()
    assert slo_1.slo_violated is False

    # Phase 2: Some errors (still healthy)
    for _ in range(99):
        tracker.record_success("/v1/chat/completions")
    tracker.record_error(
        endpoint="/v1/chat/completions",
        status_code=500,
        error_type="Error",
        error_message="Error",
    )

    slo_2 = tracker.get_slo_status()
    assert slo_2.slo_violated is False

    # Phase 3: More errors (approaching threshold)
    for _ in range(98):
        tracker.record_success("/v1/chat/completions")
    for _ in range(2):
        tracker.record_error(
            endpoint="/v1/chat/completions",
            status_code=500,
            error_type="Error",
            error_message="Error",
        )

    slo_3 = tracker.get_slo_status()
    # Total: 297 success, 3 errors = 1% error rate (at threshold)
    assert abs(slo_3.current_error_rate - 0.01) < 0.001

    print("  ✓ PASSED")


def main():
    """Run all standalone tests."""
    print("\n" + "="*60)
    print("SLO MONITORING TESTS - STANDALONE RUNNER")
    print("="*60 + "\n")

    tests = [
        test_999_slo_with_1000_requests,
        test_burn_rate_10x,
        test_zero_errors_zero_burn,
        test_slo_violation,
        test_per_endpoint_tracking,
        test_gradual_error_accumulation,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")

    if failed > 0:
        sys.exit(1)
    else:
        print("✓ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
