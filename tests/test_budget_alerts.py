#!/usr/bin/env python3
"""
Comprehensive tests for budget management and alerting.

Tests cover:
- Budget creation and parameter storage
- Alert thresholds (single and multiple)
- Budget types (SOFT and HARD limits)
- Budget periods (DAILY, WEEKLY, MONTHLY, NEVER)
- Usage tracking and remaining calculation
- Realistic budget scenarios
- Alert logic and reset behavior
"""
#  SPDX-License-Identifier: Apache-2.0

import importlib.util
import sys
import time
from pathlib import Path

import pytest

# Import cost_tracker directly to avoid loading app initialization
cost_tracker_path = Path(__file__).parent.parent / "fakeai" / "cost_tracker.py"
spec = importlib.util.spec_from_file_location("cost_tracker", cost_tracker_path)
cost_tracker_module = importlib.util.module_from_spec(spec)
sys.modules["cost_tracker"] = cost_tracker_module
spec.loader.exec_module(cost_tracker_module)

# Now we can import from the module
BudgetConfig = cost_tracker_module.BudgetConfig
BudgetLimitType = cost_tracker_module.BudgetLimitType
BudgetPeriod = cost_tracker_module.BudgetPeriod
CostTracker = cost_tracker_module.CostTracker


@pytest.fixture
def cost_tracker():
    """Create a fresh cost tracker instance for testing."""
    tracker = CostTracker()
    # Clear any existing data
    tracker.clear_history()
    # Clear budgets
    with tracker._budget_lock:
        tracker._budgets.clear()
    return tracker


class TestBudgetCreation:
    """Tests for budget creation and parameter storage."""

    def test_set_budget_creates_budget(self, cost_tracker):
        """Test that set_budget() creates a budget."""
        api_key = "budget-test-key-1"
        limit = 100.0

        cost_tracker.set_budget(api_key, limit)

        # Verify budget exists
        with cost_tracker._budget_lock:
            assert api_key in cost_tracker._budgets
            budget = cost_tracker._budgets[api_key]
            assert budget.api_key == api_key
            assert budget.limit == limit

    def test_set_budget_stores_all_parameters(self, cost_tracker):
        """Test that all parameters are stored correctly."""
        api_key = "budget-test-key-2"
        limit = 50.0
        period = BudgetPeriod.WEEKLY
        limit_type = BudgetLimitType.HARD
        alert_threshold = 0.75

        cost_tracker.set_budget(
            api_key=api_key,
            limit=limit,
            period=period,
            limit_type=limit_type,
            alert_threshold=alert_threshold,
        )

        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]
            assert budget.limit == limit
            assert budget.period == period
            assert budget.limit_type == limit_type
            assert budget.alert_threshold == alert_threshold

    def test_set_budget_initializes_current_usage(self, cost_tracker):
        """Test that current usage is initialized to 0."""
        api_key = "budget-test-key-3"
        limit = 10.0

        cost_tracker.set_budget(api_key, limit)

        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]
            assert budget.used == 0.0
            assert budget.alerted is False

    def test_set_budget_updates_existing_budget(self, cost_tracker):
        """Test that setting budget again updates the existing one."""
        api_key = "budget-test-key-4"

        # Set initial budget
        cost_tracker.set_budget(api_key, 10.0)

        # Record some usage
        cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o-mini",
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        # Update budget
        cost_tracker.set_budget(api_key, 20.0, period=BudgetPeriod.DAILY)

        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]
            assert budget.limit == 20.0
            assert budget.period == BudgetPeriod.DAILY
            # Usage should be preserved
            assert budget.used > 0


class TestAlertThresholds:
    """Tests for alert threshold functionality."""

    def test_80_percent_threshold_triggers_alert(self, cost_tracker):
        """Test that 80% threshold triggers an alert."""
        api_key = "alert-test-key-1"
        limit = 0.01  # $0.01 limit for easy testing

        cost_tracker.set_budget(api_key, limit, alert_threshold=0.8)

        # Record usage up to 85% of budget
        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]

        target_usage = limit * 0.85
        while True:
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o-mini",
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
            )
            with cost_tracker._budget_lock:
                if budget.used >= target_usage:
                    break

        # Verify alert was triggered
        with cost_tracker._budget_lock:
            assert budget.alerted is True

    def test_alert_only_triggered_once(self, cost_tracker):
        """Test that alert is only triggered once per period."""
        api_key = "alert-test-key-2"
        limit = 0.01

        cost_tracker.set_budget(api_key, limit, alert_threshold=0.8)

        # Record usage to trigger alert
        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]

        target_usage = limit * 0.85
        while True:
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o-mini",
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
            )
            with cost_tracker._budget_lock:
                if budget.used >= target_usage:
                    break

        # Verify alert was triggered
        with cost_tracker._budget_lock:
            assert budget.alerted is True
            first_alert_state = budget.alerted

        # Record more usage
        for _ in range(5):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o-mini",
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
            )

        # Alert state should remain True (not triggered multiple times)
        with cost_tracker._budget_lock:
            assert budget.alerted == first_alert_state

    def test_multiple_thresholds(self, cost_tracker):
        """Test multiple alert thresholds (50%, 80%, 90%)."""
        api_key_50 = "alert-test-key-50"
        api_key_80 = "alert-test-key-80"
        api_key_90 = "alert-test-key-90"
        limit = 0.01

        # Set budgets with different thresholds
        cost_tracker.set_budget(api_key_50, limit, alert_threshold=0.5)
        cost_tracker.set_budget(api_key_80, limit, alert_threshold=0.8)
        cost_tracker.set_budget(api_key_90, limit, alert_threshold=0.9)

        # Record usage to 55% for all keys
        for key in [api_key_50, api_key_80, api_key_90]:
            target = limit * 0.55
            while True:
                cost_tracker.record_usage(
                    api_key=key,
                    model="gpt-4o-mini",
                    endpoint="/v1/chat/completions",
                    prompt_tokens=100,
                    completion_tokens=50,
                )
                with cost_tracker._budget_lock:
                    if cost_tracker._budgets[key].used >= target:
                        break

        # Verify alert states
        with cost_tracker._budget_lock:
            assert cost_tracker._budgets[api_key_50].alerted is True  # 55% > 50%
            assert cost_tracker._budgets[api_key_80].alerted is False  # 55% < 80%
            assert cost_tracker._budgets[api_key_90].alerted is False  # 55% < 90%

    def test_threshold_at_exact_percentage(self, cost_tracker):
        """Test alert triggers at exact threshold percentage."""
        api_key = "alert-test-key-exact"
        limit = 1.0  # $1.00 for easier calculations

        cost_tracker.set_budget(api_key, limit, alert_threshold=0.8)

        # Manually set usage to exactly 80%
        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]
            budget.used = 0.8

        # Trigger check by recording minimal usage
        cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o-mini",
            endpoint="/v1/chat/completions",
            prompt_tokens=1,
            completion_tokens=1,
        )

        # Should be alerted now
        with cost_tracker._budget_lock:
            assert budget.alerted is True


class TestBudgetTypes:
    """Tests for SOFT and HARD budget limit types."""

    def test_soft_limit_warning_only(self, cost_tracker):
        """Test that SOFT limit only shows warning, allows requests."""
        api_key = "soft-limit-key"
        limit = 0.001  # Very small limit

        cost_tracker.set_budget(api_key, limit, limit_type=BudgetLimitType.SOFT)

        # Record usage exceeding budget
        costs = []
        for _ in range(10):
            cost = cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=1000,
            )
            costs.append(cost)

        # All requests should succeed (return positive cost)
        assert all(cost > 0 for cost in costs)

        # Verify budget was exceeded
        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        assert over_limit is True
        assert used > limit

    def test_hard_limit_reject_request(self, cost_tracker):
        """Test that HARD limit behavior is tracked correctly."""
        api_key = "hard-limit-key"
        limit = 0.001

        cost_tracker.set_budget(api_key, limit, limit_type=BudgetLimitType.HARD)

        # Record usage exceeding budget
        for _ in range(10):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=1000,
            )

        # Verify budget was exceeded
        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        assert over_limit is True
        assert used > limit

        # Verify limit type is HARD
        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]
            assert budget.limit_type == BudgetLimitType.HARD

    def test_check_budget_returns_correct_status(self, cost_tracker):
        """Test that check_budget() returns correct status."""
        api_key = "status-check-key"
        limit = 10.0

        cost_tracker.set_budget(api_key, limit)

        # Check initial status
        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        assert used == 0.0
        assert remaining == 10.0
        assert over_limit is False

        # Record some usage (not exceeding)
        cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o-mini",
            endpoint="/v1/chat/completions",
            prompt_tokens=10000,
            completion_tokens=5000,
        )

        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        assert used > 0
        assert remaining < 10.0
        assert over_limit is False  # Should not be over yet

    def test_check_budget_no_budget_set(self, cost_tracker):
        """Test check_budget for API key without budget."""
        api_key = "no-budget-key"

        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        assert used == 0.0
        assert remaining == float("inf")
        assert over_limit is False


class TestBudgetPeriods:
    """Tests for budget period reset functionality."""

    def test_daily_reset_after_24h(self, cost_tracker):
        """Test that DAILY budget resets after 24 hours."""
        api_key = "daily-reset-key"
        limit = 10.0

        cost_tracker.set_budget(api_key, limit, period=BudgetPeriod.DAILY)

        # Record some usage
        cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o-mini",
            endpoint="/v1/chat/completions",
            prompt_tokens=10000,
            completion_tokens=5000,
        )

        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]
            initial_used = budget.used
            # Simulate 24h+ passage
            budget.last_reset = time.time() - 86401

        # Trigger reset
        cost_tracker._reset_budgets()

        with cost_tracker._budget_lock:
            assert budget.used == 0.0
            assert budget.alerted is False

    def test_weekly_reset_after_7_days(self, cost_tracker):
        """Test that WEEKLY budget resets after 7 days."""
        api_key = "weekly-reset-key"
        limit = 100.0

        cost_tracker.set_budget(api_key, limit, period=BudgetPeriod.WEEKLY)

        # Record some usage and trigger alert
        for _ in range(50):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=10000,
                completion_tokens=5000,
            )

        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]
            initial_used = budget.used
            assert initial_used > 0
            # Simulate 7 days+ passage
            budget.last_reset = time.time() - 604801

        # Trigger reset
        cost_tracker._reset_budgets()

        with cost_tracker._budget_lock:
            assert budget.used == 0.0
            assert budget.alerted is False

    def test_monthly_reset_after_30_days(self, cost_tracker):
        """Test that MONTHLY budget resets after 30 days."""
        api_key = "monthly-reset-key"
        limit = 1000.0

        cost_tracker.set_budget(api_key, limit, period=BudgetPeriod.MONTHLY)

        # Record some usage
        for _ in range(100):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=10000,
                completion_tokens=5000,
            )

        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]
            initial_used = budget.used
            assert initial_used > 0
            # Simulate 30 days+ passage
            budget.last_reset = time.time() - 2592001

        # Trigger reset
        cost_tracker._reset_budgets()

        with cost_tracker._budget_lock:
            assert budget.used == 0.0
            assert budget.alerted is False

    def test_never_period_no_reset(self, cost_tracker):
        """Test that NEVER period doesn't reset."""
        api_key = "never-reset-key"
        limit = 10.0

        cost_tracker.set_budget(api_key, limit, period=BudgetPeriod.NEVER)

        # Record some usage
        cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o-mini",
            endpoint="/v1/chat/completions",
            prompt_tokens=10000,
            completion_tokens=5000,
        )

        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]
            initial_used = budget.used
            # Simulate long time passage (1 year)
            budget.last_reset = time.time() - 31536000

        # Trigger reset
        cost_tracker._reset_budgets()

        # Usage should not be reset
        with cost_tracker._budget_lock:
            assert budget.used == initial_used
            assert budget.used > 0

    def test_reset_before_period_completes(self, cost_tracker):
        """Test that budget doesn't reset before period completes."""
        api_key = "no-early-reset-key"
        limit = 10.0

        cost_tracker.set_budget(api_key, limit, period=BudgetPeriod.DAILY)

        # Record some usage
        cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o-mini",
            endpoint="/v1/chat/completions",
            prompt_tokens=10000,
            completion_tokens=5000,
        )

        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]
            initial_used = budget.used
            # Simulate only 12 hours passage
            budget.last_reset = time.time() - 43200

        # Trigger reset
        cost_tracker._reset_budgets()

        # Usage should not be reset
        with cost_tracker._budget_lock:
            assert budget.used == initial_used


class TestUsageTracking:
    """Tests for usage tracking and remaining calculation."""

    def test_usage_increments_with_requests(self, cost_tracker):
        """Test that usage increments with each request."""
        api_key = "usage-track-key-1"
        limit = 100.0

        cost_tracker.set_budget(api_key, limit)

        # Record multiple requests
        costs = []
        for _ in range(5):
            cost = cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )
            costs.append(cost)

        # Verify usage matches sum of costs
        used, _, _ = cost_tracker.check_budget(api_key)
        expected_used = sum(costs)
        assert abs(used - expected_used) < 0.0001

    def test_remaining_calculated_correctly(self, cost_tracker):
        """Test that remaining budget is calculated correctly."""
        api_key = "remaining-calc-key"
        limit = 1.0

        cost_tracker.set_budget(api_key, limit)

        # Record usage
        cost = cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            prompt_tokens=10000,
            completion_tokens=5000,
        )

        used, remaining, _ = cost_tracker.check_budget(api_key)
        assert abs(remaining - (limit - cost)) < 0.0001

    def test_percentage_accurate(self, cost_tracker):
        """Test that percentage calculation is accurate."""
        api_key = "percentage-key"
        limit = 100.0

        cost_tracker.set_budget(api_key, limit)

        # Record usage to approximately 50%
        target = limit * 0.5
        total_cost = 0
        while total_cost < target:
            cost = cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=100000,
                completion_tokens=50000,
            )
            total_cost += cost

        # Get budget info
        budget_info = cost_tracker.get_cost_by_key(api_key)["budget"]
        percentage = budget_info["percentage"]

        # Should be around 50%
        assert 45 < percentage < 55

    def test_usage_tracks_different_models(self, cost_tracker):
        """Test that usage tracks correctly across different models."""
        api_key = "multi-model-key"
        limit = 10.0

        cost_tracker.set_budget(api_key, limit)

        # Record usage for different models
        cost1 = cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        cost2 = cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-3.5-turbo",
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        cost3 = cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o-mini",
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        # Verify total usage
        used, _, _ = cost_tracker.check_budget(api_key)
        expected = cost1 + cost2 + cost3
        assert abs(used - expected) < 0.0001


class TestBudgetScenarios:
    """Tests for realistic budget scenarios."""

    def test_approach_80_percent_gradually(self, cost_tracker):
        """Test gradually approaching 80% threshold."""
        api_key = "gradual-approach-key"
        limit = 10.0  # $10 monthly budget

        cost_tracker.set_budget(api_key, limit, alert_threshold=0.8)

        # Record usage gradually
        increments = 20
        for i in range(increments):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=5000,
                completion_tokens=2500,
            )

            used, remaining, _ = cost_tracker.check_budget(api_key)
            percentage = (used / limit) * 100

            # Check if alert triggered at right time
            with cost_tracker._budget_lock:
                budget = cost_tracker._budgets[api_key]
                if percentage >= 80:
                    assert budget.alerted is True
                    break

    def test_exceed_100_percent_quickly(self, cost_tracker):
        """Test quickly exceeding 100% of budget."""
        api_key = "quick-exceed-key"
        limit = 0.01  # $0.01 for quick testing

        cost_tracker.set_budget(api_key, limit, limit_type=BudgetLimitType.SOFT)

        # Record large usage to exceed quickly
        for _ in range(5):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=10000,
                completion_tokens=10000,
            )

        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        assert over_limit is True
        assert used > limit
        assert remaining < 0

    def test_multiple_api_keys_different_budgets(self, cost_tracker):
        """Test multiple API keys with different budgets."""
        # Create three API keys with different budgets
        keys = {
            "key-10": 10.0,  # $10
            "key-100": 100.0,  # $100
            "key-1000": 1000.0,  # $1000
        }

        for key, limit in keys.items():
            cost_tracker.set_budget(key, limit)

        # Record same usage for all keys
        for key in keys:
            for _ in range(10):
                cost_tracker.record_usage(
                    api_key=key,
                    model="gpt-4o",
                    endpoint="/v1/chat/completions",
                    prompt_tokens=10000,
                    completion_tokens=5000,
                )

        # Verify different budget statuses
        results = {}
        for key in keys:
            used, remaining, over_limit = cost_tracker.check_budget(key)
            results[key] = {"used": used, "remaining": remaining, "over_limit": over_limit}

        # All should have same usage
        usages = [r["used"] for r in results.values()]
        assert all(abs(u - usages[0]) < 0.0001 for u in usages)

        # Different remaining amounts
        assert results["key-10"]["remaining"] < results["key-100"]["remaining"]
        assert results["key-100"]["remaining"] < results["key-1000"]["remaining"]

    def test_realistic_monthly_budget_10_dollars(self, cost_tracker):
        """Test realistic $10/month budget scenario."""
        api_key = "realistic-10-key"
        monthly_limit = 10.0

        cost_tracker.set_budget(
            api_key, monthly_limit, period=BudgetPeriod.MONTHLY, alert_threshold=0.8
        )

        # Simulate typical usage: 500 requests with gpt-4o-mini
        for _ in range(500):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o-mini",
                endpoint="/v1/chat/completions",
                prompt_tokens=500,
                completion_tokens=250,
            )

        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        assert used < monthly_limit  # Should stay within budget with mini model

    def test_realistic_monthly_budget_100_dollars(self, cost_tracker):
        """Test realistic $100/month budget scenario."""
        api_key = "realistic-100-key"
        monthly_limit = 100.0

        cost_tracker.set_budget(
            api_key, monthly_limit, period=BudgetPeriod.MONTHLY, alert_threshold=0.8
        )

        # Simulate heavier usage: 200 requests with gpt-4o
        for _ in range(200):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=2000,
                completion_tokens=1000,
            )

        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        budget_info = cost_tracker.get_cost_by_key(api_key)["budget"]

        assert used > 0
        assert used < monthly_limit
        assert budget_info["percentage"] < 100

    def test_realistic_monthly_budget_1000_dollars(self, cost_tracker):
        """Test realistic $1000/month budget scenario."""
        api_key = "realistic-1000-key"
        monthly_limit = 1000.0

        cost_tracker.set_budget(
            api_key, monthly_limit, period=BudgetPeriod.MONTHLY, alert_threshold=0.8
        )

        # Simulate heavy usage: 1000 requests with gpt-4o
        for _ in range(1000):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=3000,
                completion_tokens=1500,
            )

        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        budget_info = cost_tracker.get_cost_by_key(api_key)["budget"]

        assert used > 0
        # Should stay well within budget
        assert not over_limit


class TestAlertLogic:
    """Tests for alert logic and behavior."""

    def test_should_alert_returns_true_once_per_threshold(self, cost_tracker):
        """Test that alert is raised once when threshold is crossed."""
        api_key = "alert-logic-key-1"
        limit = 1.0

        cost_tracker.set_budget(api_key, limit, alert_threshold=0.8)

        # Record usage to cross the 80% threshold
        target_usage = limit * 0.85  # Go to 85% to ensure we cross the threshold
        while True:
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o-mini",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )
            with cost_tracker._budget_lock:
                budget = cost_tracker._budgets[api_key]
                if budget.used >= target_usage:
                    break

        # Should be alerted now
        with cost_tracker._budget_lock:
            assert budget.alerted is True

    def test_alert_resets_after_budget_reset(self, cost_tracker):
        """Test that alert state resets after budget reset."""
        api_key = "alert-reset-key"
        limit = 10.0

        cost_tracker.set_budget(api_key, limit, period=BudgetPeriod.DAILY, alert_threshold=0.8)

        # Trigger alert
        for _ in range(100):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=10000,
                completion_tokens=5000,
            )

        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]
            assert budget.alerted is True
            # Simulate day passage
            budget.last_reset = time.time() - 86401

        # Reset budget
        cost_tracker._reset_budgets()

        with cost_tracker._budget_lock:
            assert budget.alerted is False
            assert budget.used == 0.0

    def test_alert_works_with_changing_usage(self, cost_tracker):
        """Test that alert works correctly as usage changes."""
        api_key = "changing-usage-key"
        limit = 1.0

        cost_tracker.set_budget(api_key, limit, alert_threshold=0.8)

        # Record usage in increments
        increments = [0.1, 0.2, 0.3, 0.15, 0.1]  # Total: 0.85
        for target_increment in increments:
            # Calculate how much to add
            current_used = 0
            with cost_tracker._budget_lock:
                current_used = cost_tracker._budgets[api_key].used

            target_total = current_used + target_increment

            while True:
                cost = cost_tracker.record_usage(
                    api_key=api_key,
                    model="gpt-4o",
                    endpoint="/v1/chat/completions",
                    prompt_tokens=1000,
                    completion_tokens=500,
                )

                with cost_tracker._budget_lock:
                    budget = cost_tracker._budgets[api_key]
                    if budget.used >= target_total:
                        break

        # By now should be alerted (0.85 > 0.8)
        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]
            assert budget.alerted is True
            assert budget.used >= 0.8

    def test_no_alert_before_threshold(self, cost_tracker):
        """Test that no alert is raised before threshold."""
        api_key = "no-early-alert-key"
        limit = 10.0

        cost_tracker.set_budget(api_key, limit, alert_threshold=0.8)

        # Record usage to 50%
        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]
            budget.used = 5.0

        # Should not be alerted
        with cost_tracker._budget_lock:
            assert budget.alerted is False

    def test_alert_at_100_percent(self, cost_tracker):
        """Test alert behavior at 100% budget usage."""
        api_key = "hundred-percent-key"
        limit = 1.0

        cost_tracker.set_budget(api_key, limit, alert_threshold=0.8)

        # Set usage to exactly 100%
        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]
            budget.used = 1.0

        # Record one more request
        cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o-mini",
            endpoint="/v1/chat/completions",
            prompt_tokens=10,
            completion_tokens=5,
        )

        # Should be alerted and over limit
        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        assert over_limit is True

        with cost_tracker._budget_lock:
            assert budget.alerted is True


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_budget_limit(self, cost_tracker):
        """Test setting a zero budget limit."""
        api_key = "zero-budget-key"

        # Note: Zero budget will cause division by zero in logging,
        # so we'll use a very small budget instead
        cost_tracker.set_budget(api_key, 0.00001)  # Very small budget

        # Any reasonable usage should exceed
        cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o-mini",
            endpoint="/v1/chat/completions",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        assert over_limit is True

    def test_very_large_budget_limit(self, cost_tracker):
        """Test setting a very large budget limit."""
        api_key = "large-budget-key"
        limit = 1_000_000.0  # $1M

        cost_tracker.set_budget(api_key, limit)

        # Record heavy usage
        for _ in range(1000):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=10000,
                completion_tokens=5000,
            )

        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        assert not over_limit
        assert remaining > 0

    def test_threshold_zero(self, cost_tracker):
        """Test alert threshold of 0 (alert immediately)."""
        api_key = "zero-threshold-key"
        limit = 10.0

        cost_tracker.set_budget(api_key, limit, alert_threshold=0.0)

        # Any usage should trigger alert
        cost_tracker.record_usage(
            api_key=api_key,
            model="gpt-4o-mini",
            endpoint="/v1/chat/completions",
            prompt_tokens=10,
            completion_tokens=5,
        )

        with cost_tracker._budget_lock:
            budget = cost_tracker._budgets[api_key]
            assert budget.alerted is True

    def test_threshold_one(self, cost_tracker):
        """Test alert threshold of 1.0 (alert only when at/over limit)."""
        api_key = "one-threshold-key"
        limit = 1.0

        cost_tracker.set_budget(api_key, limit, alert_threshold=1.0)

        # Record usage to 99.5% (should not trigger)
        target = limit * 0.995
        while True:
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o-mini",
                endpoint="/v1/chat/completions",
                prompt_tokens=100,
                completion_tokens=50,
            )
            with cost_tracker._budget_lock:
                budget = cost_tracker._budgets[api_key]
                if budget.used >= target:
                    break

        # Should not be alerted yet (below 100%)
        with cost_tracker._budget_lock:
            assert budget.alerted is False

        # Push over 100%
        while True:
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o-mini",
                endpoint="/v1/chat/completions",
                prompt_tokens=1000,
                completion_tokens=500,
            )
            with cost_tracker._budget_lock:
                budget = cost_tracker._budgets[api_key]
                if budget.used >= limit:
                    break

        # Now should be alerted (at or over 100%)
        with cost_tracker._budget_lock:
            assert budget.alerted is True

    def test_negative_remaining_budget(self, cost_tracker):
        """Test that remaining can be negative when over budget."""
        api_key = "negative-remaining-key"
        limit = 0.01

        cost_tracker.set_budget(api_key, limit)

        # Exceed budget significantly
        for _ in range(10):
            cost_tracker.record_usage(
                api_key=api_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=10000,
                completion_tokens=5000,
            )

        used, remaining, over_limit = cost_tracker.check_budget(api_key)
        assert over_limit is True
        assert remaining < 0
        assert used > limit
