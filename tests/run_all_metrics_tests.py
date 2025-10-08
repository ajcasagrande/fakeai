#!/usr/bin/env python3
"""
Test Runner for FakeAI Metrics Tests

This script discovers and runs all test_*.py files in the tests/ directory,
generates coverage reports, and provides a comprehensive summary.

Usage:
    python tests/run_all_metrics_tests.py
    python tests/run_all_metrics_tests.py --coverage-threshold 80
    python tests/run_all_metrics_tests.py --metrics-only

Exit codes:
    0 - All tests passed and coverage meets threshold
    1 - Tests failed or coverage below threshold
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TestRunner:
    """Discovers and runs pytest tests with coverage reporting."""

    def __init__(
        self,
        coverage_threshold: int = 80,
        metrics_only: bool = False,
        verbose: bool = False,
        html_report: bool = True,
    ):
        self.coverage_threshold = coverage_threshold
        self.metrics_only = metrics_only
        self.verbose = verbose
        self.html_report = html_report
        self.test_dir = Path(__file__).parent.resolve()
        self.project_root = self.test_dir.parent

    def discover_tests(self) -> dict[str, list[Path]]:
        """
        Discover all test files in the tests/ directory.

        Returns:
            Dictionary categorizing test files
        """
        all_tests = list(self.test_dir.glob("test_*.py"))

        # Categorize tests
        metrics_tests = [
            t for t in all_tests
            if any(keyword in t.stem for keyword in [
                'metrics', 'streaming', 'error', 'cost', 'event',
                'prometheus', 'slo', 'latency', 'batch_metrics'
            ])
        ]

        other_tests = [t for t in all_tests if t not in metrics_tests]

        return {
            'metrics': sorted(metrics_tests),
            'other': sorted(other_tests),
            'all': sorted(all_tests)
        }

    def count_tests_in_file(self, test_file: Path) -> int:
        """
        Count the number of test functions in a file.

        Args:
            test_file: Path to test file

        Returns:
            Number of test functions
        """
        count = 0
        try:
            with open(test_file, 'r') as f:
                for line in f:
                    if line.strip().startswith('def test_') or line.strip().startswith('async def test_'):
                        count += 1
        except Exception:
            return 0
        return count

    def print_test_summary(self, tests: dict[str, list[Path]]) -> None:
        """Print summary of discovered tests."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}=== Test Discovery ==={Colors.ENDC}")
        print(f"{Colors.OKBLUE}Test directory: {self.test_dir}{Colors.ENDC}\n")

        # Metrics tests
        print(f"{Colors.OKCYAN}Metrics-related tests ({len(tests['metrics'])} files):{Colors.ENDC}")
        total_metrics_tests = 0
        for test_file in tests['metrics']:
            count = self.count_tests_in_file(test_file)
            total_metrics_tests += count
            print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {test_file.name:50s} ({count:3d} tests)")

        print(f"\n{Colors.BOLD}Total metrics tests: {total_metrics_tests}{Colors.ENDC}")

        # Other tests (if not metrics-only)
        if not self.metrics_only:
            print(f"\n{Colors.OKCYAN}Other tests ({len(tests['other'])} files):{Colors.ENDC}")
            total_other_tests = 0
            for test_file in tests['other'][:10]:  # Show first 10
                count = self.count_tests_in_file(test_file)
                total_other_tests += count
                print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {test_file.name:50s} ({count:3d} tests)")

            if len(tests['other']) > 10:
                remaining = len(tests['other']) - 10
                remaining_count = sum(self.count_tests_in_file(f) for f in tests['other'][10:])
                total_other_tests += remaining_count
                print(f"  ... and {remaining} more files ({remaining_count} tests)")

            print(f"\n{Colors.BOLD}Total other tests: {total_other_tests}{Colors.ENDC}")
            print(f"{Colors.BOLD}Grand total: {total_metrics_tests + total_other_tests} tests{Colors.ENDC}")

    def run_pytest(self, test_pattern: str = None) -> tuple[int, dict]:
        """
        Run pytest with coverage.

        Args:
            test_pattern: Optional pattern to filter tests

        Returns:
            Tuple of (exit_code, coverage_data)
        """
        print(f"\n{Colors.HEADER}{Colors.BOLD}=== Running Tests ==={Colors.ENDC}\n")

        # Build pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            f"--cov={self.project_root / 'fakeai'}",
            "--cov-report=term-missing",
            "--cov-report=json",
            "--noconftest",  # Skip conftest.py to avoid event loop issues
        ]

        if self.html_report:
            cmd.extend([
                "--cov-report=html:htmlcov",
            ])

        # Add verbosity
        if self.verbose:
            cmd.append("-vv")
        else:
            cmd.append("-v")

        # Filter tests if needed
        if self.metrics_only:
            # Run only metrics-related tests
            patterns = [
                'test_metrics', 'test_streaming', 'test_error', 'test_cost',
                'test_event', 'test_prometheus', 'test_slo', 'test_latency',
                'test_batch_metrics', 'test_handler_events'
            ]
            cmd.append("-k")
            cmd.append(" or ".join(patterns))
        elif test_pattern:
            cmd.extend(["-k", test_pattern])

        # Additional pytest options
        cmd.extend([
            "--tb=short",
            "--color=yes",
            "-ra",  # Show summary of all test outcomes
            "--continue-on-collection-errors",  # Continue even if some tests fail to collect
        ])

        # Run pytest
        result = subprocess.run(cmd, cwd=self.project_root)

        # Load coverage data
        coverage_data = {}
        coverage_json = self.project_root / "coverage.json"
        if coverage_json.exists():
            try:
                with open(coverage_json, 'r') as f:
                    coverage_data = json.load(f)
            except Exception as e:
                print(f"{Colors.WARNING}Warning: Could not load coverage data: {e}{Colors.ENDC}")

        return result.returncode, coverage_data

    def print_coverage_summary(self, coverage_data: dict) -> bool:
        """
        Print coverage summary and check threshold.

        Args:
            coverage_data: Coverage data from coverage.json

        Returns:
            True if coverage meets threshold, False otherwise
        """
        if not coverage_data:
            print(f"{Colors.WARNING}No coverage data available{Colors.ENDC}")
            return False

        print(f"\n{Colors.HEADER}{Colors.BOLD}=== Coverage Summary ==={Colors.ENDC}\n")

        # Overall coverage
        total_percent = coverage_data.get('totals', {}).get('percent_covered', 0)
        total_statements = coverage_data.get('totals', {}).get('num_statements', 0)
        total_missing = coverage_data.get('totals', {}).get('missing_lines', 0)
        total_covered = total_statements - total_missing

        print(f"Overall Coverage: {Colors.BOLD}{total_percent:.2f}%{Colors.ENDC}")
        print(f"Statements: {total_covered}/{total_statements}")
        print(f"Missing: {total_missing}\n")

        # Key modules coverage
        key_modules = [
            'fakeai/events/subscribers.py',
            'fakeai/events/emitter.py',
            'fakeai/events/event_types.py',
            'fakeai/events/bus.py',
            'fakeai/events/base.py',
            'fakeai/streaming_metrics_tracker.py',
            'fakeai/error_metrics_tracker.py',
            'fakeai/cost_tracker.py',
        ]

        print(f"{Colors.OKCYAN}Key Modules Coverage:{Colors.ENDC}")
        files_data = coverage_data.get('files', {})

        for module in key_modules:
            module_data = files_data.get(module, {})
            if module_data:
                summary = module_data.get('summary', {})
                percent = summary.get('percent_covered', 0)
                num_statements = summary.get('num_statements', 0)
                missing = summary.get('missing_lines', 0)
                covered = num_statements - missing

                color = Colors.OKGREEN if percent >= self.coverage_threshold else Colors.WARNING
                status = "✓" if percent >= self.coverage_threshold else "✗"

                print(f"  {color}{status}{Colors.ENDC} {module:50s} {percent:6.2f}% ({covered}/{num_statements})")
            else:
                print(f"  {Colors.WARNING}✗{Colors.ENDC} {module:50s} {Colors.WARNING}Not covered{Colors.ENDC}")

        # Check threshold
        meets_threshold = total_percent >= self.coverage_threshold

        print(f"\n{Colors.BOLD}Coverage Threshold: {self.coverage_threshold}%{Colors.ENDC}")
        if meets_threshold:
            print(f"{Colors.OKGREEN}✓ Coverage meets threshold!{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}✗ Coverage below threshold ({total_percent:.2f}% < {self.coverage_threshold}%){Colors.ENDC}")

        if self.html_report:
            html_path = self.project_root / "htmlcov" / "index.html"
            if html_path.exists():
                print(f"\n{Colors.OKCYAN}HTML coverage report: {html_path}{Colors.ENDC}")

        return meets_threshold

    def run(self) -> int:
        """
        Run the full test suite.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("=" * 80)
        print("FakeAI Metrics Test Runner")
        print("=" * 80)
        print(f"{Colors.ENDC}")

        # Discover tests
        tests = self.discover_tests()
        self.print_test_summary(tests)

        # Verify imports work (warn but don't fail on event loop issues)
        print(f"\n{Colors.HEADER}{Colors.BOLD}=== Verifying Imports ==={Colors.ENDC}")
        import_check = self.verify_imports()
        if import_check:
            print(f"{Colors.OKGREEN}✓ All imports verified{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠ Some imports have warnings (this is OK - pytest will handle them){Colors.ENDC}")

        # Run tests
        exit_code, coverage_data = self.run_pytest()

        # Print coverage summary
        coverage_ok = self.print_coverage_summary(coverage_data)

        # Final summary
        print(f"\n{Colors.HEADER}{Colors.BOLD}=== Final Summary ==={Colors.ENDC}\n")

        if exit_code == 0 and coverage_ok:
            print(f"{Colors.OKGREEN}{Colors.BOLD}✓ ALL TESTS PASSED AND COVERAGE MEETS THRESHOLD!{Colors.ENDC}")
            return 0
        elif exit_code == 0:
            print(f"{Colors.WARNING}{Colors.BOLD}⚠ Tests passed but coverage below threshold{Colors.ENDC}")
            return 1
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}✗ TESTS FAILED{Colors.ENDC}")
            return 1

    def verify_imports(self) -> bool:
        """Verify that key modules can be imported."""
        modules_to_test = [
            'fakeai.events',
            'fakeai.events.subscribers',
            'fakeai.events.emitter',
            'fakeai.events.event_types',
            'fakeai.events.bus',
            'fakeai.streaming_metrics_tracker',
            'fakeai.error_metrics_tracker',
            'fakeai.cost_tracker',
        ]

        all_ok = True
        for module in modules_to_test:
            try:
                # Import module in a subprocess to avoid event loop issues
                # Use PYTHONWARNINGS to suppress warnings during import check
                result = subprocess.run(
                    [sys.executable, "-c", f"import warnings; warnings.filterwarnings('ignore'); import {module}"],
                    capture_output=True,
                    timeout=5,
                    cwd=self.project_root,
                    env={**subprocess.os.environ, 'PYTHONWARNINGS': 'ignore'},
                )
                if result.returncode == 0:
                    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {module}")
                else:
                    # Only show actual errors, not warnings
                    stderr = result.stderr.decode().strip()
                    if stderr and not all('Warning' in line or 'warning' in line for line in stderr.split('\n')):
                        error = stderr.split('\n')[-1]
                        print(f"  {Colors.FAIL}✗{Colors.ENDC} {module}: {error}")
                        all_ok = False
                    else:
                        # Import succeeded but with warnings
                        print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {module} (with warnings)")
            except Exception as e:
                print(f"  {Colors.FAIL}✗{Colors.ENDC} {module}: {e}")
                all_ok = False

        return all_ok


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run FakeAI metrics tests with coverage reporting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests with default 80% coverage threshold
  python tests/run_all_metrics_tests.py

  # Run only metrics-related tests
  python tests/run_all_metrics_tests.py --metrics-only

  # Set custom coverage threshold
  python tests/run_all_metrics_tests.py --coverage-threshold 85

  # Verbose output without HTML report
  python tests/run_all_metrics_tests.py --verbose --no-html
        """
    )

    parser.add_argument(
        '--coverage-threshold',
        type=int,
        default=80,
        help='Minimum coverage percentage required (default: 80)'
    )

    parser.add_argument(
        '--metrics-only',
        action='store_true',
        help='Run only metrics-related tests'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )

    parser.add_argument(
        '--no-html',
        action='store_true',
        help='Skip HTML coverage report generation'
    )

    args = parser.parse_args()

    runner = TestRunner(
        coverage_threshold=args.coverage_threshold,
        metrics_only=args.metrics_only,
        verbose=args.verbose,
        html_report=not args.no_html,
    )

    exit_code = runner.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
