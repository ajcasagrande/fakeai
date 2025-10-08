#!/usr/bin/env python3
"""
Live Cost Tracking Verification Test

This test performs comprehensive verification of cost tracking functionality by:
1. Sending real requests with different models (gpt-4, gpt-4o, gpt-4o-mini)
2. Varying token counts to test different pricing scenarios
3. Verifying costs are tracked and calculated correctly
4. Testing budget alerts (set $1 budget, exceed it)
5. Verifying optimization suggestions
6. Printing detailed cost breakdowns with 6 decimal place accuracy

USAGE:
    # Run with default server (assumes server is running on localhost:8000)
    python tests/verify_cost_tracking_live.py

    # Or import and use the test functions
    from tests.verify_cost_tracking_live import run_full_verification
    run_full_verification()
"""
#  SPDX-License-Identifier: Apache-2.0

import sys
from typing import Any

from openai import OpenAI

from fakeai.cost_tracker import (
    MODEL_PRICING,
    BudgetLimitType,
    BudgetPeriod,
    CostTracker,
)


class CostVerifier:
    """Helper class for verifying cost calculations."""

    @staticmethod
    def calculate_expected_cost(
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0,
    ) -> float:
        """Calculate expected cost based on model pricing."""
        if model not in MODEL_PRICING:
            # Use default pricing (gpt-3.5-turbo)
            pricing = MODEL_PRICING["gpt-3.5-turbo"]
        else:
            pricing = MODEL_PRICING[model]

        # Calculate input cost
        if cached_tokens > 0 and pricing.cached_input_price_per_million:
            # Calculate cached tokens cost
            cached_cost = (
                cached_tokens / 1_000_000 * pricing.cached_input_price_per_million
            )
            # Calculate non-cached input tokens cost
            regular_input_cost = (
                (prompt_tokens - cached_tokens)
                / 1_000_000
                * pricing.input_price_per_million
            )
            input_cost = regular_input_cost + cached_cost
        else:
            input_cost = prompt_tokens / 1_000_000 * pricing.input_price_per_million

        # Calculate output cost
        output_cost = completion_tokens / 1_000_000 * pricing.output_price_per_million

        return input_cost + output_cost

    @staticmethod
    def verify_cost(
        expected: float, actual: float, tolerance: float = 0.000001
    ) -> tuple[bool, float]:
        """
        Verify cost matches expected value within tolerance.

        Returns:
            Tuple of (matches, difference)
        """
        diff = abs(expected - actual)
        return diff <= tolerance, diff


class LiveCostTrackingTest:
    """Live cost tracking verification test suite."""

    def __init__(
        self, base_url: str = "http://localhost:8000/v1", api_key: str = "test-key"
    ):
        """Initialize test with OpenAI client."""
        self.base_url = base_url
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.cost_tracker = CostTracker()
        self.verifier = CostVerifier()

        # Test results tracking
        self.results: list[dict[str, Any]] = []
        self.passed = 0
        self.failed = 0

    def print_header(self, title: str) -> None:
        """Print section header."""
        print(f"\n{'=' * 80}")
        print(f"{title:^80}")
        print(f"{'=' * 80}\n")

    def print_subheader(self, title: str) -> None:
        """Print subsection header."""
        print(f"\n{'-' * 80}")
        print(f"{title}")
        print(f"{'-' * 80}")

    def print_cost_details(
        self,
        test_name: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int,
        expected_cost: float,
        actual_cost: float,
        matches: bool,
        difference: float,
    ) -> None:
        """Print detailed cost breakdown."""
        status = "PASS" if matches else "FAIL"
        pricing = MODEL_PRICING.get(model, MODEL_PRICING["gpt-3.5-turbo"])

        print(f"\nTest: {test_name}")
        print(f"  Model: {model}")
        print(f"  Tokens:")
        print(f"    Prompt:     {prompt_tokens:>10,}")
        print(f"    Completion: {completion_tokens:>10,}")
        if cached_tokens > 0:
            print(f"    Cached:     {cached_tokens:>10,}")
        print(f"  Pricing (per 1M tokens):")
        print(f"    Input:      ${pricing.input_price_per_million:>10.2f}")
        print(f"    Output:     ${pricing.output_price_per_million:>10.2f}")
        if cached_tokens > 0 and pricing.cached_input_price_per_million:
            print(
                f"    Cached:     ${pricing.cached_input_price_per_million:>10.2f}"
            )
        print(f"  Cost:")
        print(f"    Expected:   ${expected_cost:>10.6f}")
        print(f"    Actual:     ${actual_cost:>10.6f}")
        print(f"    Difference: ${difference:>10.6f}")
        print(f"  Status: {status}")

        if matches:
            self.passed += 1
        else:
            self.failed += 1

    def test_basic_models(self) -> None:
        """Test 1: Basic requests with different models."""
        self.print_header("TEST 1: Different Models with Varied Token Counts")

        test_cases = [
            # (model, prompt_tokens, completion_tokens, description)
            ("gpt-4", 100, 50, "GPT-4 - Small request"),
            ("gpt-4", 1000, 500, "GPT-4 - Medium request"),
            ("gpt-4", 5000, 2500, "GPT-4 - Large request"),
            ("gpt-4o", 100, 50, "GPT-4o - Small request"),
            ("gpt-4o", 1000, 500, "GPT-4o - Medium request"),
            ("gpt-4o", 5000, 2500, "GPT-4o - Large request"),
            ("gpt-4o-mini", 100, 50, "GPT-4o-mini - Small request"),
            ("gpt-4o-mini", 1000, 500, "GPT-4o-mini - Medium request"),
            ("gpt-4o-mini", 10000, 5000, "GPT-4o-mini - Large request"),
        ]

        for model, prompt_tokens, completion_tokens, description in test_cases:
            # Make request
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=completion_tokens,
            )

            # Get actual usage from response
            actual_prompt = response.usage.prompt_tokens
            actual_completion = response.usage.completion_tokens

            # Calculate expected cost
            expected_cost = self.verifier.calculate_expected_cost(
                model, actual_prompt, actual_completion
            )

            # Get tracked cost
            cost_info = self.cost_tracker.get_cost_by_key(self.api_key)
            # Calculate cost for this request (difference from previous total)
            if hasattr(self, "_last_total_cost"):
                actual_cost = cost_info["total_cost"] - self._last_total_cost
            else:
                actual_cost = cost_info["total_cost"]
            self._last_total_cost = cost_info["total_cost"]

            # Verify cost
            matches, diff = self.verifier.verify_cost(expected_cost, actual_cost)

            # Print details
            self.print_cost_details(
                description,
                model,
                actual_prompt,
                actual_completion,
                0,
                expected_cost,
                actual_cost,
                matches,
                diff,
            )

    def test_cached_tokens(self) -> None:
        """Test 2: Requests with cached tokens."""
        self.print_header("TEST 2: Cached Token Cost Calculation")

        # Models that support caching
        test_cases = [
            ("gpt-4o", 2000, 1000, 1000, "GPT-4o with 50% cache hits"),
            ("gpt-4o", 3000, 1500, 2000, "GPT-4o with 66% cache hits"),
            ("gpt-4o-mini", 2000, 1000, 1000, "GPT-4o-mini with 50% cache hits"),
            ("gpt-4o-mini", 4000, 2000, 3000, "GPT-4o-mini with 75% cache hits"),
        ]

        for model, prompt_tokens, completion_tokens, cached_tokens, description in (
            test_cases
        ):
            # Make request (FakeAI doesn't actually cache, but we can simulate in tracking)
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=completion_tokens,
            )

            # Get actual usage
            actual_prompt = response.usage.prompt_tokens
            actual_completion = response.usage.completion_tokens

            # Manually record with cached tokens (simulating cache behavior)
            expected_cost = self.verifier.calculate_expected_cost(
                model, actual_prompt, actual_completion, cached_tokens
            )

            actual_cost = self.cost_tracker.record_usage(
                api_key=f"{self.api_key}-cached",
                model=model,
                endpoint="/v1/chat/completions",
                prompt_tokens=actual_prompt,
                completion_tokens=actual_completion,
                cached_tokens=cached_tokens,
            )

            # Verify cost
            matches, diff = self.verifier.verify_cost(expected_cost, actual_cost)

            # Print details
            self.print_cost_details(
                description,
                model,
                actual_prompt,
                actual_completion,
                cached_tokens,
                expected_cost,
                actual_cost,
                matches,
                diff,
            )

    def test_cost_aggregation(self) -> None:
        """Test 3: Verify cost aggregation across multiple requests."""
        self.print_header("TEST 3: Cost Aggregation and Tracking")

        test_key = f"{self.api_key}-aggregation"
        self.cost_tracker.clear_history(test_key)

        # Make multiple requests
        models_and_counts = [
            ("gpt-4o-mini", 5),
            ("gpt-4o", 3),
            ("gpt-4", 2),
        ]

        expected_total = 0.0
        request_count = 0

        for model, count in models_and_counts:
            for i in range(count):
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": f"Request {i}"}],
                    max_tokens=100,
                )

                # Calculate expected cost for this request
                cost = self.verifier.calculate_expected_cost(
                    model, response.usage.prompt_tokens, response.usage.completion_tokens
                )
                expected_total += cost

                # Manually record to track under our test key
                self.cost_tracker.record_usage(
                    api_key=test_key,
                    model=model,
                    endpoint="/v1/chat/completions",
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                )

                request_count += 1

        # Get aggregated cost
        cost_info = self.cost_tracker.get_cost_by_key(test_key)
        actual_total = cost_info["total_cost"]

        # Verify
        matches, diff = self.verifier.verify_cost(expected_total, actual_total)

        print(f"\nAggregation Test:")
        print(f"  Total Requests: {request_count}")
        print(f"  Expected Total Cost: ${expected_total:.6f}")
        print(f"  Actual Total Cost:   ${actual_total:.6f}")
        print(f"  Difference:          ${diff:.6f}")
        print(f"  Status: {'PASS' if matches else 'FAIL'}")

        # Print breakdown by model
        print(f"\n  Cost Breakdown by Model:")
        for model, model_cost in cost_info["by_model"].items():
            print(f"    {model:20s}: ${model_cost:.6f}")

        if matches:
            self.passed += 1
        else:
            self.failed += 1

    def test_budget_alerts(self) -> None:
        """Test 4: Budget alerts and thresholds."""
        self.print_header("TEST 4: Budget Alerts and Enforcement")

        test_key = f"{self.api_key}-budget"
        self.cost_tracker.clear_history(test_key)

        # Set a $1 budget
        budget_limit = 1.0
        self.cost_tracker.set_budget(
            test_key,
            budget_limit,
            period=BudgetPeriod.MONTHLY,
            limit_type=BudgetLimitType.SOFT,
            alert_threshold=0.8,
        )

        print(f"\nBudget Configuration:")
        print(f"  Limit: ${budget_limit:.2f}")
        print(f"  Period: MONTHLY")
        print(f"  Type: SOFT")
        print(f"  Alert Threshold: 80%")

        # Make requests to approach budget
        request_num = 0
        alert_triggered = False
        budget_exceeded = False

        while True:
            request_num += 1

            # Use expensive model to hit budget faster
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"Request {request_num}"}],
                max_tokens=500,
            )

            # Record usage
            self.cost_tracker.record_usage(
                api_key=test_key,
                model="gpt-4o",
                endpoint="/v1/chat/completions",
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
            )

            # Check budget status
            used, remaining, over_limit = self.cost_tracker.check_budget(test_key)
            percentage = (used / budget_limit) * 100

            # Check if alert should be triggered
            with self.cost_tracker._budget_lock:
                budget = self.cost_tracker._budgets[test_key]
                if budget.alerted and not alert_triggered:
                    print(f"\n  Alert Triggered at Request #{request_num}:")
                    print(f"    Used: ${used:.6f} ({percentage:.2f}%)")
                    print(f"    Remaining: ${remaining:.6f}")
                    alert_triggered = True

            # Check if budget exceeded
            if over_limit and not budget_exceeded:
                print(f"\n  Budget Exceeded at Request #{request_num}:")
                print(f"    Used: ${used:.6f} ({percentage:.2f}%)")
                print(f"    Remaining: ${remaining:.6f}")
                budget_exceeded = True
                break

            # Safety limit - don't run forever
            if request_num > 1000:
                print(f"\n  ERROR: Budget not exceeded after 1000 requests")
                break

        # Verify alert was triggered before budget exceeded
        print(f"\n  Test Results:")
        print(f"    Alert Triggered: {alert_triggered}")
        print(f"    Budget Exceeded: {budget_exceeded}")
        print(f"    Alert Before Exceed: {alert_triggered and budget_exceeded}")

        # Get final budget info
        cost_info = self.cost_tracker.get_cost_by_key(test_key)
        budget_info = cost_info["budget"]
        print(f"\n  Final Budget Status:")
        print(f"    Used: ${budget_info['used']:.6f}")
        print(f"    Remaining: ${budget_info['remaining']:.6f}")
        print(f"    Percentage: {budget_info['percentage']:.2f}%")

        if alert_triggered and budget_exceeded:
            print(f"\n  Status: PASS")
            self.passed += 1
        else:
            print(f"\n  Status: FAIL")
            self.failed += 1

    def test_optimization_suggestions(self) -> None:
        """Test 5: Cost optimization suggestions."""
        self.print_header("TEST 5: Cost Optimization Suggestions")

        test_key = f"{self.api_key}-optimization"
        self.cost_tracker.clear_history(test_key)

        # Make many expensive GPT-4 requests to trigger suggestions
        print(f"\nGenerating expensive usage pattern with GPT-4...")
        for i in range(100):
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": f"Request {i}"}],
                max_tokens=500,
            )

            # Record usage
            self.cost_tracker.record_usage(
                api_key=test_key,
                model="gpt-4",
                endpoint="/v1/chat/completions",
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
            )

        # Get cost info
        cost_info = self.cost_tracker.get_cost_by_key(test_key)
        total_cost = cost_info["total_cost"]

        print(f"\n  Total GPT-4 Cost: ${total_cost:.6f}")
        print(f"  Total Requests: {cost_info['requests']}")

        # Get optimization suggestions
        suggestions = self.cost_tracker.get_optimization_suggestions(test_key)

        print(f"\n  Optimization Suggestions: {len(suggestions)}")
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                print(f"\n  Suggestion #{i}:")
                print(f"    Type: {suggestion.suggestion_type}")
                print(f"    Description: {suggestion.description}")
                print(f"    Potential Savings: ${suggestion.potential_savings:.2f}")
                if suggestion.details:
                    print(f"    Details:")
                    for key, value in suggestion.details.items():
                        print(f"      {key}: {value}")

            print(f"\n  Status: PASS")
            self.passed += 1
        else:
            print(f"\n  ERROR: No suggestions generated")
            print(f"\n  Status: FAIL")
            self.failed += 1

    def test_cost_comparison(self) -> None:
        """Test 6: Cost comparison across models."""
        self.print_header("TEST 6: Model Cost Comparison")

        test_key = f"{self.api_key}-comparison"
        self.cost_tracker.clear_history(test_key)

        models = [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-3.5-turbo",
        ]

        print(f"\nCost for 10,000 prompt tokens + 5,000 completion tokens:\n")

        costs = {}
        for model in models:
            # Calculate expected cost
            expected_cost = self.verifier.calculate_expected_cost(
                model, 10000, 5000
            )

            # Record (simulate the usage)
            actual_cost = self.cost_tracker.record_usage(
                api_key=f"{test_key}-{model}",
                model=model,
                endpoint="/v1/chat/completions",
                prompt_tokens=10000,
                completion_tokens=5000,
            )

            # Verify
            matches, diff = self.verifier.verify_cost(expected_cost, actual_cost)

            costs[model] = actual_cost

            status = "PASS" if matches else "FAIL"
            print(f"  {model:20s}: ${actual_cost:.6f} ({status})")

            if matches:
                self.passed += 1
            else:
                self.failed += 1

        # Show cost ratios
        print(f"\n  Cost Ratios (compared to gpt-4o-mini):")
        mini_cost = costs["gpt-4o-mini"]
        for model in models:
            ratio = costs[model] / mini_cost
            print(f"    {model:20s}: {ratio:.2f}x")

    def test_precision_accuracy(self) -> None:
        """Test 7: Verify 6 decimal place precision."""
        self.print_header("TEST 7: Precision and Accuracy Verification")

        test_cases = [
            # (model, prompt, completion, description)
            ("gpt-4o-mini", 1, 1, "Minimal tokens"),
            ("gpt-4o-mini", 10, 5, "Very small request"),
            ("gpt-4o", 1, 1, "GPT-4o minimal"),
            ("gpt-4", 1, 1, "GPT-4 minimal"),
        ]

        print(f"\nTesting precision for very small costs:\n")

        all_match = True
        for model, prompt_tokens, completion_tokens, description in test_cases:
            expected_cost = self.verifier.calculate_expected_cost(
                model, prompt_tokens, completion_tokens
            )

            actual_cost = self.cost_tracker.record_usage(
                api_key=f"{self.api_key}-precision",
                model=model,
                endpoint="/v1/chat/completions",
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

            matches, diff = self.verifier.verify_cost(expected_cost, actual_cost)
            all_match = all_match and matches

            print(f"  {description}:")
            print(f"    Expected: ${expected_cost:.6f}")
            print(f"    Actual:   ${actual_cost:.6f}")
            print(f"    Match:    {matches} (diff: ${diff:.9f})")

        if all_match:
            print(f"\n  Status: PASS - All costs accurate to 6 decimal places")
            self.passed += 1
        else:
            print(f"\n  Status: FAIL - Some costs exceed precision tolerance")
            self.failed += 1

    def print_summary(self) -> None:
        """Print test summary."""
        self.print_header("TEST SUMMARY")

        total_tests = self.passed + self.failed
        pass_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0

        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {self.passed}")
        print(f"  Failed: {self.failed}")
        print(f"  Pass Rate: {pass_rate:.1f}%")
        print()

        if self.failed == 0:
            print(f"  Result: ALL TESTS PASSED!")
        else:
            print(f"  Result: SOME TESTS FAILED")

        print()

    def run_all_tests(self) -> bool:
        """
        Run all verification tests.

        Returns:
            True if all tests passed, False otherwise
        """
        print("\n" + "=" * 80)
        print("LIVE COST TRACKING VERIFICATION TEST SUITE".center(80))
        print("=" * 80)
        print(f"\nConnecting to: {self.base_url}")
        print(f"API Key: {self.api_key}")

        # Clear history before starting
        self.cost_tracker.clear_history()
        self._last_total_cost = 0.0

        try:
            # Run all tests
            self.test_basic_models()
            self.test_cached_tokens()
            self.test_cost_aggregation()
            self.test_budget_alerts()
            self.test_optimization_suggestions()
            self.test_cost_comparison()
            self.test_precision_accuracy()

            # Print summary
            self.print_summary()

            return self.failed == 0

        except Exception as e:
            print(f"\n\nERROR: Test suite failed with exception:")
            print(f"  {type(e).__name__}: {e}")
            import traceback

            traceback.print_exc()
            return False


def run_full_verification(
    base_url: str = "http://localhost:8000/v1", api_key: str = "test-key"
) -> bool:
    """
    Run full cost tracking verification.

    Args:
        base_url: Base URL of FakeAI server
        api_key: API key for authentication

    Returns:
        True if all tests passed, False otherwise
    """
    test_suite = LiveCostTrackingTest(base_url=base_url, api_key=api_key)
    return test_suite.run_all_tests()


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000/v1"

    if len(sys.argv) > 2:
        api_key = sys.argv[2]
    else:
        api_key = "test-key"

    # Run verification
    success = run_full_verification(base_url=base_url, api_key=api_key)

    # Exit with appropriate code
    sys.exit(0 if success else 1)
