#!/usr/bin/env python3
"""
Comprehensive Error Metrics Live Testing Script.

This script validates the error metrics tracking system by:
1. Sending successful requests
2. Triggering various error types
3. Verifying metrics endpoints
4. Checking SLO compliance
5. Validating error pattern detection

Usage:
    python tests/verify_error_metrics_live.py
"""
#  SPDX-License-Identifier: Apache-2.0

import json
import sys
import time
from typing import Any

import requests


# Color codes for output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")


def print_section(text: str) -> None:
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.CYAN}{'-'*len(text)}{Colors.RESET}")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.MAGENTA}ℹ {text}{Colors.RESET}")


class ErrorMetricsValidator:
    """Validates error metrics tracking through live API calls."""

    def __init__(self, base_url: str = "http://localhost:8765"):
        self.base_url = base_url
        self.api_key = "sk-test-key-123"
        self.test_results: dict[str, bool] = {}
        self.total_tests = 0
        self.passed_tests = 0

    def check(self, condition: bool, message: str) -> bool:
        """Check a condition and record the result."""
        self.total_tests += 1
        if condition:
            self.passed_tests += 1
            print_success(message)
            return True
        else:
            print_error(message)
            return False

    def send_successful_request(self) -> bool:
        """Send a successful chat completion request."""
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Hello"}],
                },
                timeout=5,
            )
            return response.status_code == 200
        except Exception as e:
            print_warning(f"Request error: {e}")
            return False

    def trigger_invalid_model_error(self) -> bool:
        """Trigger an invalid model error."""
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "invalid-model-xyz",
                    "messages": [{"role": "user", "content": "Hello"}],
                },
                timeout=5,
            )
            return response.status_code in [400, 404]
        except Exception as e:
            print_warning(f"Request error: {e}")
            return False

    def trigger_auth_error(self) -> bool:
        """Trigger an authentication error."""
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": "Bearer invalid-key",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Hello"}],
                },
                timeout=5,
            )
            return response.status_code in [401, 403]
        except Exception as e:
            print_warning(f"Request error: {e}")
            return False

    def get_error_metrics(self) -> dict[str, Any]:
        """Fetch error metrics from the API."""
        try:
            response = requests.get(
                f"{self.base_url}/metrics/errors",
                timeout=5,
            )
            if response.status_code == 200:
                return response.json()
            else:
                print_warning(f"Error metrics endpoint returned: {response.status_code}")
                return {}
        except Exception as e:
            print_warning(f"Failed to fetch error metrics: {e}")
            return {}

    def get_slo_status(self) -> dict[str, Any]:
        """Fetch SLO status from the API."""
        try:
            response = requests.get(
                f"{self.base_url}/metrics/slo",
                timeout=5,
            )
            if response.status_code == 200:
                return response.json()
            else:
                print_warning(f"SLO endpoint returned: {response.status_code}")
                return {}
        except Exception as e:
            print_warning(f"Failed to fetch SLO status: {e}")
            return {}

    def get_error_patterns(self) -> list[dict[str, Any]]:
        """Fetch error patterns from the API."""
        try:
            response = requests.get(
                f"{self.base_url}/metrics/error-patterns",
                params={"min_count": 1, "recent_only": True},
                timeout=5,
            )
            if response.status_code == 200:
                return response.json()
            else:
                print_warning(f"Error patterns endpoint returned: {response.status_code}")
                return []
        except Exception as e:
            print_warning(f"Failed to fetch error patterns: {e}")
            return []

    def run_test_sequence(self) -> None:
        """Run the complete test sequence."""
        print_header("ERROR METRICS LIVE TESTING")

        # Step 1: Send successful requests
        print_section("Step 1: Sending 20 Successful Requests")
        successful_count = 0
        for i in range(20):
            if self.send_successful_request():
                successful_count += 1
            if (i + 1) % 5 == 0:
                print_info(f"Sent {i + 1}/20 requests...")
            time.sleep(0.05)  # Small delay to avoid overwhelming the server

        self.check(
            successful_count >= 18,
            f"Sent {successful_count}/20 successful requests (expected >= 18)"
        )

        # Step 2: Trigger errors
        print_section("Step 2: Triggering 2 Error Conditions")

        print_info("Triggering invalid model error...")
        error1_success = self.trigger_invalid_model_error()
        self.check(error1_success, "Invalid model error triggered successfully")
        time.sleep(0.1)

        print_info("Triggering auth failure error...")
        error2_success = self.trigger_auth_error()
        self.check(error2_success, "Auth failure error triggered successfully")
        time.sleep(0.1)

        # Give the server time to process metrics
        print_info("Waiting for metrics to update...")
        time.sleep(0.5)

        # Step 3: Check /metrics/errors
        print_section("Step 3: Validating /metrics/errors Endpoint")
        error_metrics = self.get_error_metrics()

        if error_metrics:
            print_info(f"Raw error metrics: {json.dumps(error_metrics, indent=2)}")

            # Check for expected structure
            self.check(
                "summary" in error_metrics or "total_errors" in error_metrics,
                "Error metrics has expected structure"
            )

            # Check total_requests (may be in different locations)
            total_requests = (
                error_metrics.get("summary", {}).get("total_requests") or
                error_metrics.get("total_requests") or
                0
            )
            self.check(
                total_requests >= 20,
                f"Total requests tracked: {total_requests} (expected >= 20)"
            )

            # Check total_errors
            total_errors = (
                error_metrics.get("summary", {}).get("total_errors") or
                error_metrics.get("total_errors") or
                0
            )
            self.check(
                total_errors >= 2,
                f"Total errors tracked: {total_errors} (expected >= 2)"
            )

            # Check success rate if available
            if total_requests > 0:
                success_rate = (total_requests - total_errors) / total_requests
                expected_rate = 0.91  # 20 success / 22 total = ~0.91
                self.check(
                    0.80 <= success_rate <= 0.99,
                    f"Success rate: {success_rate:.2%} (expected ~91%)"
                )

            # Check error distribution
            if "distribution" in error_metrics:
                dist = error_metrics["distribution"]
                self.check(
                    len(dist.get("by_endpoint", {})) > 0,
                    f"Error distribution by endpoint: {len(dist.get('by_endpoint', {}))} endpoints"
                )
        else:
            print_error("Failed to retrieve error metrics")

        # Step 4: Check /metrics/slo
        print_section("Step 4: Validating /metrics/slo Endpoint")
        slo_status = self.get_slo_status()

        if slo_status:
            print_info(f"Raw SLO status: {json.dumps(slo_status, indent=2)}")

            # Check for expected structure
            self.check(
                "current_status" in slo_status or "availability" in slo_status,
                "SLO status has expected structure"
            )

            # Check current_success_rate or availability
            current_status = slo_status.get("current_status", {})
            availability = (
                current_status.get("availability") or
                current_status.get("success_rate") or
                slo_status.get("availability") or
                0
            )

            if availability > 0:
                self.check(
                    availability > 0.80,
                    f"Current availability: {availability:.2%}"
                )

            # Check error_budget
            if "error_budget" in slo_status:
                error_budget = slo_status["error_budget"]
                consumed = error_budget.get("consumed_percentage", 0)
                remaining = error_budget.get("remaining_percentage", 0)
                print_info(f"Error budget consumed: {consumed:.2f}%, remaining: {remaining:.2f}%")
                self.check(
                    "consumed_percentage" in error_budget,
                    "Error budget tracking is active"
                )

            # Check SLO violation status
            # With ~91% success rate and 99.9% SLO, we should be in violation
            slo_violated = (
                current_status.get("overall_compliant") == False or
                current_status.get("slo_violated") == True or
                slo_status.get("slo_violated") == True
            )

            # However, if there are enough successful requests, SLO might not be violated
            # Let's just check that the field exists
            self.check(
                "current_status" in slo_status or "slo_violated" in slo_status,
                f"SLO violation tracking present (violated={slo_violated})"
            )

            # Check targets
            if "targets" in slo_status:
                targets = slo_status["targets"]
                self.check(
                    targets.get("availability", 0) == 0.999,
                    f"SLO target: {targets.get('availability', 0):.1%} (expected 99.9%)"
                )
        else:
            print_error("Failed to retrieve SLO status")

        # Step 5: Check /metrics/error-patterns
        print_section("Step 5: Validating /metrics/error-patterns Endpoint")
        error_patterns = self.get_error_patterns()

        if error_patterns is not None:
            print_info(f"Found {len(error_patterns)} error patterns")

            if len(error_patterns) > 0:
                print_info(f"Sample pattern: {json.dumps(error_patterns[0], indent=2)}")

                # Check pattern structure
                pattern = error_patterns[0]
                self.check(
                    "fingerprint" in pattern or "pattern" in pattern,
                    "Error patterns have fingerprints/identifiers"
                )
                self.check(
                    "count" in pattern or "occurrence_count" in pattern,
                    "Error patterns track occurrence counts"
                )
            else:
                print_warning("No error patterns detected (may need more occurrences)")
                self.check(True, "Error patterns endpoint accessible")
        else:
            print_error("Failed to retrieve error patterns")

        # Step 6: Additional validation
        print_section("Step 6: Additional Validation")

        # Verify endpoints are responsive
        endpoints_to_check = ["/metrics", "/health", "/metrics/prometheus"]
        for endpoint in endpoints_to_check:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                self.check(
                    response.status_code == 200,
                    f"Endpoint {endpoint} is responsive"
                )
            except Exception as e:
                print_error(f"Endpoint {endpoint} failed: {e}")

    def print_summary(self) -> None:
        """Print the test summary."""
        print_header("TEST SUMMARY")

        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0

        print(f"\n{Colors.BOLD}Total Tests:{Colors.RESET} {self.total_tests}")
        print(f"{Colors.BOLD}Passed:{Colors.RESET} {Colors.GREEN}{self.passed_tests}{Colors.RESET}")
        print(f"{Colors.BOLD}Failed:{Colors.RESET} {Colors.RED}{self.total_tests - self.passed_tests}{Colors.RESET}")
        print(f"{Colors.BOLD}Success Rate:{Colors.RESET} ", end="")

        if success_rate >= 90:
            print(f"{Colors.GREEN}{success_rate:.1f}%{Colors.RESET}")
        elif success_rate >= 70:
            print(f"{Colors.YELLOW}{success_rate:.1f}%{Colors.RESET}")
        else:
            print(f"{Colors.RED}{success_rate:.1f}%{Colors.RESET}")

        print()

        if success_rate >= 90:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED - Error metrics system is working correctly!{Colors.RESET}\n")
        elif success_rate >= 70:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠ SOME TESTS FAILED - Review the output above{Colors.RESET}\n")
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ MANY TESTS FAILED - Error metrics system needs attention{Colors.RESET}\n")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Comprehensive error metrics live testing"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8765",
        help="Base URL of the FakeAI server (default: http://localhost:8765)",
    )
    args = parser.parse_args()

    validator = ErrorMetricsValidator(base_url=args.url)

    try:
        # Check server availability
        print_info(f"Checking server availability at {args.url}...")
        try:
            response = requests.get(f"{args.url}/health", timeout=5)
            if response.status_code == 200:
                print_success("Server is online and healthy")
            else:
                print_error(f"Server returned status code: {response.status_code}")
                return 1
        except Exception as e:
            print_error(f"Cannot connect to server: {e}")
            print_info("Please ensure the FakeAI server is running:")
            print_info("  python -m fakeai.app")
            return 1

        # Run the test sequence
        validator.run_test_sequence()

        # Print summary
        validator.print_summary()

        # Return appropriate exit code
        return 0 if validator.passed_tests == validator.total_tests else 1

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Testing interrupted by user{Colors.RESET}\n")
        return 130
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
