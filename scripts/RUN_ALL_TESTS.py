#!/usr/bin/env python3
"""
Intelligent Master Test Runner for FakeAI
==========================================

Systematically tests all test files with beautiful reporting, timeout handling,
failure analysis, and actionable recommendations.

Features:
- Individual file testing with 60s timeout
- Real-time progress updates
- Beautiful ASCII table report
- Color-coded results (green/yellow/red)
- Pass rate calculations
- Common failure pattern detection
- Actionable fix suggestions
- Parallel or sequential execution
- Filter by status (passed/failed/skipped)
- JSON export for CI/CD integration

Usage:
    python RUN_ALL_TESTS.py                 # Run all tests sequentially
    python RUN_ALL_TESTS.py --parallel      # Run in parallel (4 workers)
    python RUN_ALL_TESTS.py --parallel 8    # Run with 8 workers
    python RUN_ALL_TESTS.py --filter failed # Only show failed tests
    python RUN_ALL_TESTS.py --export results.json  # Export to JSON
    python RUN_ALL_TESTS.py --timeout 120   # Custom timeout (seconds)
    python RUN_ALL_TESTS.py --verbose       # Show detailed output
"""

import argparse
import json
import re
import subprocess
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional, Tuple


# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

    @staticmethod
    def disable():
        """Disable colors for non-TTY environments"""
        Colors.GREEN = ''
        Colors.YELLOW = ''
        Colors.RED = ''
        Colors.BLUE = ''
        Colors.CYAN = ''
        Colors.MAGENTA = ''
        Colors.BOLD = ''
        Colors.UNDERLINE = ''
        Colors.RESET = ''


@dataclass
class TestResult:
    """Individual test file result"""
    file_path: str
    file_name: str
    status: str  # 'passed', 'failed', 'error', 'timeout'
    passed: int
    failed: int
    skipped: int
    errors: int
    warnings: int
    duration: float
    exit_code: int
    error_message: Optional[str] = None
    failure_patterns: List[str] = None

    def __post_init__(self):
        if self.failure_patterns is None:
            self.failure_patterns = []

    @property
    def total_tests(self) -> int:
        return self.passed + self.failed + self.skipped + self.errors

    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100

    @property
    def status_color(self) -> str:
        if self.status == 'passed':
            return Colors.GREEN
        elif self.status in ('failed', 'error'):
            return Colors.RED
        elif self.status == 'timeout':
            return Colors.MAGENTA
        else:
            return Colors.YELLOW


class TestRunner:
    """Main test runner orchestrator"""

    def __init__(self,
                 tests_dir: Path,
                 timeout: int = 60,
                 verbose: bool = False):
        self.tests_dir = tests_dir
        self.timeout = timeout
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.start_time: float = 0
        self.end_time: float = 0

    def find_test_files(self) -> List[Path]:
        """Find all test files recursively"""
        test_files = []
        for pattern in ['test_*.py', '*_test.py']:
            test_files.extend(self.tests_dir.rglob(pattern))

        # Exclude __pycache__ and special files
        test_files = [
            f for f in test_files
            if '__pycache__' not in str(f) and f.name != '__init__.py'
        ]

        return sorted(test_files)

    def run_single_test_file(self, test_file: Path) -> TestResult:
        """Run a single test file with timeout"""
        # Use absolute path for display
        rel_path = test_file.relative_to(self.tests_dir) if test_file.is_relative_to(self.tests_dir) else test_file.name

        if self.verbose:
            print(f"\n{Colors.CYAN}Running: {rel_path}{Colors.RESET}")

        start = time.time()

        try:
            # Run pytest on single file with absolute path
            # Find project root (where pyproject.toml or setup.py exists)
            project_root = test_file
            while project_root.parent != project_root:
                if (project_root / 'pyproject.toml').exists() or (project_root / 'setup.py').exists():
                    break
                project_root = project_root.parent
            else:
                # Fallback: use test file's parent
                project_root = self.tests_dir.parent if (self.tests_dir.parent / 'pyproject.toml').exists() else self.tests_dir

            cmd = [
                'pytest',
                str(test_file.resolve()),  # Use absolute path
                '-v',
                '--tb=short',
                '--color=no',
                '-q'
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(project_root)  # Run from project root
            )

            duration = time.time() - start

            # Parse output
            output = result.stdout + result.stderr
            passed, failed, skipped, errors, warnings = self._parse_pytest_output(output)

            # Determine status
            if result.returncode == 0:
                status = 'passed'
            elif result.returncode == 1:
                status = 'failed'
            else:
                status = 'error'

            # Extract error messages and patterns
            error_msg = None
            patterns = []
            if status in ('failed', 'error'):
                error_msg = self._extract_error_message(output)
                patterns = self._identify_failure_patterns(output)

            return TestResult(
                file_path=str(rel_path),
                file_name=test_file.name,
                status=status,
                passed=passed,
                failed=failed,
                skipped=skipped,
                errors=errors,
                warnings=warnings,
                duration=duration,
                exit_code=result.returncode,
                error_message=error_msg,
                failure_patterns=patterns
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start
            return TestResult(
                file_path=str(rel_path),
                file_name=test_file.name,
                status='timeout',
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                warnings=0,
                duration=duration,
                exit_code=-1,
                error_message=f"Test timed out after {self.timeout}s",
                failure_patterns=['timeout']
            )

        except Exception as e:
            duration = time.time() - start
            return TestResult(
                file_path=str(rel_path),
                file_name=test_file.name,
                status='error',
                passed=0,
                failed=0,
                skipped=0,
                errors=1,
                warnings=0,
                duration=duration,
                exit_code=-1,
                error_message=str(e),
                failure_patterns=['exception']
            )

    def _parse_pytest_output(self, output: str) -> Tuple[int, int, int, int, int]:
        """Parse pytest output for test counts"""
        passed = failed = skipped = errors = warnings = 0

        # Look for summary line: "1 passed, 2 failed, 3 skipped in 1.23s"
        summary_pattern = r'(\d+)\s+(passed|failed|skipped|error|warning)'
        matches = re.findall(summary_pattern, output.lower())

        for count, status in matches:
            count = int(count)
            if 'passed' in status:
                passed = count
            elif 'failed' in status:
                failed = count
            elif 'skipped' in status:
                skipped = count
            elif 'error' in status:
                errors = count
            elif 'warning' in status:
                warnings = count

        return passed, failed, skipped, errors, warnings

    def _extract_error_message(self, output: str) -> str:
        """Extract concise error message from output"""
        lines = output.split('\n')

        # Look for FAILED, ERROR, or assertion messages
        error_lines = []
        capture = False

        for line in lines:
            if 'FAILED' in line or 'ERROR' in line or 'AssertionError' in line:
                capture = True

            if capture:
                error_lines.append(line)
                if len(error_lines) >= 5:  # Limit to 5 lines
                    break

        return '\n'.join(error_lines[:5]) if error_lines else "Unknown error"

    def _identify_failure_patterns(self, output: str) -> List[str]:
        """Identify common failure patterns"""
        patterns = []

        # Common patterns
        pattern_checks = {
            'import_error': r'ImportError|ModuleNotFoundError',
            'attribute_error': r'AttributeError',
            'assertion_error': r'AssertionError',
            'type_error': r'TypeError',
            'value_error': r'ValueError',
            'connection_error': r'ConnectionError|ConnectionRefusedError',
            'timeout': r'TimeoutError|asyncio\.TimeoutError',
            'fixture_error': r'fixture .* not found',
            'async_error': r'RuntimeError.*Event loop',
            'deprecation': r'DeprecationWarning',
        }

        for pattern_name, pattern_regex in pattern_checks.items():
            if re.search(pattern_regex, output):
                patterns.append(pattern_name)

        return patterns

    def run_sequential(self, test_files: List[Path]) -> None:
        """Run tests sequentially with progress bar"""
        total = len(test_files)

        print(f"\n{Colors.BOLD}{Colors.BLUE}Running {total} test files sequentially...{Colors.RESET}\n")

        for i, test_file in enumerate(test_files, 1):
            # Progress indicator
            print(f"[{i}/{total}] {test_file.name:<50}", end='', flush=True)

            result = self.run_single_test_file(test_file)
            self.results.append(result)

            # Status indicator
            if result.status == 'passed':
                print(f"{Colors.GREEN}✓ PASS{Colors.RESET} ({result.duration:.2f}s)")
            elif result.status == 'failed':
                print(f"{Colors.RED}✗ FAIL{Colors.RESET} ({result.duration:.2f}s)")
            elif result.status == 'timeout':
                print(f"{Colors.MAGENTA}⏱ TIMEOUT{Colors.RESET} ({result.duration:.2f}s)")
            else:
                print(f"{Colors.YELLOW}⚠ ERROR{Colors.RESET} ({result.duration:.2f}s)")

    def run_parallel(self, test_files: List[Path], workers: int = 4) -> None:
        """Run tests in parallel with thread pool"""
        total = len(test_files)
        completed = 0

        print(f"\n{Colors.BOLD}{Colors.BLUE}Running {total} test files in parallel ({workers} workers)...{Colors.RESET}\n")

        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all jobs
            future_to_file = {
                executor.submit(self.run_single_test_file, test_file): test_file
                for test_file in test_files
            }

            # Process as they complete
            for future in as_completed(future_to_file):
                completed += 1
                test_file = future_to_file[future]

                try:
                    result = future.result()
                    self.results.append(result)

                    # Progress with status
                    status_char = '✓' if result.status == 'passed' else '✗'
                    status_color = result.status_color

                    print(f"[{completed}/{total}] {status_color}{status_char}{Colors.RESET} "
                          f"{test_file.name:<50} ({result.duration:.2f}s)")

                except Exception as e:
                    print(f"[{completed}/{total}] {Colors.RED}✗{Colors.RESET} "
                          f"{test_file.name:<50} (exception: {e})")

    def generate_report(self, filter_status: Optional[str] = None) -> str:
        """Generate beautiful formatted report"""
        if not self.results:
            return "No test results to report."

        # Filter results if needed
        results = self.results
        if filter_status:
            results = [r for r in results if r.status == filter_status]

        if not results:
            return f"No tests with status '{filter_status}' found."

        # Calculate summary stats
        total_tests = len(results)
        total_passed = sum(r.passed for r in results)
        total_failed = sum(r.failed for r in results)
        total_skipped = sum(r.skipped for r in results)
        total_errors = sum(r.errors for r in results)
        total_duration = sum(r.duration for r in results)

        passed_files = sum(1 for r in results if r.status == 'passed')
        failed_files = sum(1 for r in results if r.status == 'failed')
        error_files = sum(1 for r in results if r.status == 'error')
        timeout_files = sum(1 for r in results if r.status == 'timeout')

        overall_pass_rate = (passed_files / total_tests * 100) if total_tests > 0 else 0

        # Build report
        lines = []
        lines.append("")
        lines.append(f"{Colors.BOLD}{Colors.BLUE}{'=' * 120}{Colors.RESET}")
        lines.append(f"{Colors.BOLD}{Colors.BLUE}                           FAKEAI TEST SUITE - COMPREHENSIVE RESULTS{Colors.RESET}")
        lines.append(f"{Colors.BOLD}{Colors.BLUE}{'=' * 120}{Colors.RESET}")
        lines.append("")

        # Summary section
        lines.append(f"{Colors.BOLD}SUMMARY:{Colors.RESET}")
        lines.append(f"  Total Test Files:     {total_tests}")
        lines.append(f"  {Colors.GREEN}✓ Passed Files:{Colors.RESET}      {passed_files} ({overall_pass_rate:.1f}%)")
        lines.append(f"  {Colors.RED}✗ Failed Files:{Colors.RESET}      {failed_files}")
        lines.append(f"  {Colors.YELLOW}⚠ Error Files:{Colors.RESET}       {error_files}")
        lines.append(f"  {Colors.MAGENTA}⏱ Timeout Files:{Colors.RESET}     {timeout_files}")
        lines.append(f"  Total Duration:       {total_duration:.2f}s ({total_duration/60:.1f}m)")
        lines.append("")
        lines.append(f"{Colors.BOLD}TEST COUNTS:{Colors.RESET}")
        lines.append(f"  Tests Passed:         {total_passed}")
        lines.append(f"  Tests Failed:         {total_failed}")
        lines.append(f"  Tests Skipped:        {total_skipped}")
        lines.append(f"  Test Errors:          {total_errors}")
        lines.append("")

        # Detailed table
        lines.append(f"{Colors.BOLD}DETAILED RESULTS:{Colors.RESET}")
        lines.append("")

        # Table header
        header = f"{'FILE':<50} {'STATUS':<12} {'PASS':<6} {'FAIL':<6} {'SKIP':<6} {'ERR':<6} {'RATE':<8} {'TIME':<8}"
        lines.append(f"{Colors.BOLD}{header}{Colors.RESET}")
        lines.append("-" * 120)

        # Sort by status (failed first, then errors, then passed)
        status_priority = {'failed': 0, 'error': 1, 'timeout': 2, 'passed': 3}
        sorted_results = sorted(results, key=lambda r: (status_priority.get(r.status, 4), r.file_name))

        # Table rows
        for result in sorted_results:
            status_text = result.status.upper()
            status_colored = f"{result.status_color}{status_text:<12}{Colors.RESET}"

            pass_rate = f"{result.pass_rate:.1f}%" if result.total_tests > 0 else "N/A"

            row = (f"{result.file_name:<50} {status_colored} "
                   f"{result.passed:<6} {result.failed:<6} {result.skipped:<6} "
                   f"{result.errors:<6} {pass_rate:<8} {result.duration:<7.2f}s")
            lines.append(row)

        lines.append("-" * 120)
        lines.append("")

        # Collect all failure patterns first (needed for recommendations)
        pattern_counts = defaultdict(int)
        for result in results:
            if result.status in ('failed', 'error', 'timeout'):
                for pattern in result.failure_patterns:
                    pattern_counts[pattern] += 1

        # Failure analysis
        if failed_files > 0 or error_files > 0 or timeout_files > 0:
            lines.append(f"{Colors.BOLD}{Colors.RED}FAILURE ANALYSIS:{Colors.RESET}")
            lines.append("")

            if pattern_counts:
                lines.append(f"{Colors.BOLD}Common Failure Patterns:{Colors.RESET}")
                for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"  • {pattern:<20} ({count} occurrences)")
                lines.append("")

            # Show failed file details
            lines.append(f"{Colors.BOLD}Failed Files Details:{Colors.RESET}")
            for result in sorted_results:
                if result.status in ('failed', 'error', 'timeout'):
                    lines.append(f"\n  {Colors.RED}✗ {result.file_name}{Colors.RESET}")
                    lines.append(f"    Status: {result.status}")
                    lines.append(f"    Exit Code: {result.exit_code}")
                    if result.failure_patterns:
                        lines.append(f"    Patterns: {', '.join(result.failure_patterns)}")
                    if result.error_message:
                        # Show first 3 lines of error
                        error_lines = result.error_message.split('\n')[:3]
                        for line in error_lines:
                            lines.append(f"    {line}")
            lines.append("")

        # Recommendations
        lines.append(f"{Colors.BOLD}{Colors.CYAN}RECOMMENDATIONS:{Colors.RESET}")
        lines.append("")

        if overall_pass_rate == 100:
            lines.append(f"  {Colors.GREEN}✓ Excellent! All tests passing!{Colors.RESET}")
        elif overall_pass_rate >= 90:
            lines.append(f"  {Colors.GREEN}✓ Great! Most tests passing ({overall_pass_rate:.1f}%).{Colors.RESET}")
            lines.append(f"  • Fix {failed_files + error_files} remaining test files")
        elif overall_pass_rate >= 75:
            lines.append(f"  {Colors.YELLOW}⚠ Good progress ({overall_pass_rate:.1f}%), but needs attention.{Colors.RESET}")
            lines.append(f"  • Focus on common failure patterns")
            lines.append(f"  • Run individual failed tests with -vv for details")
        else:
            lines.append(f"  {Colors.RED}⚠ Significant issues ({overall_pass_rate:.1f}% pass rate).{Colors.RESET}")
            lines.append(f"  • Start with most common failure patterns")
            lines.append(f"  • Consider running tests individually with verbose output")

        # Specific recommendations based on patterns
        if pattern_counts:  # Only if we have patterns
            if 'import_error' in pattern_counts:
                lines.append(f"  • Fix import errors (check dependencies and module paths)")
            if 'fixture_error' in pattern_counts:
                lines.append(f"  • Fix fixture errors (check conftest.py and fixture names)")
            if 'async_error' in pattern_counts:
                lines.append(f"  • Fix async errors (add @pytest.mark.asyncio decorators)")
            if 'timeout' in pattern_counts:
                lines.append(f"  • Investigate timeouts (increase --timeout or optimize tests)")
            if 'connection_error' in pattern_counts:
                lines.append(f"  • Fix connection errors (check test setup and cleanup)")

        lines.append("")
        lines.append(f"{Colors.BOLD}{Colors.BLUE}{'=' * 120}{Colors.RESET}")
        lines.append("")

        return '\n'.join(lines)

    def export_json(self, output_file: Path) -> None:
        """Export results to JSON"""
        data = {
            'summary': {
                'total_files': len(self.results),
                'passed_files': sum(1 for r in self.results if r.status == 'passed'),
                'failed_files': sum(1 for r in self.results if r.status == 'failed'),
                'error_files': sum(1 for r in self.results if r.status == 'error'),
                'timeout_files': sum(1 for r in self.results if r.status == 'timeout'),
                'total_duration': sum(r.duration for r in self.results),
                'total_tests_passed': sum(r.passed for r in self.results),
                'total_tests_failed': sum(r.failed for r in self.results),
                'total_tests_skipped': sum(r.skipped for r in self.results),
                'total_tests_errors': sum(r.errors for r in self.results),
            },
            'results': [asdict(r) for r in self.results]
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n{Colors.GREEN}Results exported to: {output_file}{Colors.RESET}")

    def run(self, parallel: bool = False, workers: int = 4) -> None:
        """Main run method"""
        self.start_time = time.time()

        # Find all test files
        test_files = self.find_test_files()

        if not test_files:
            print(f"{Colors.RED}No test files found in {self.tests_dir}{Colors.RESET}")
            return

        print(f"{Colors.BOLD}Found {len(test_files)} test files{Colors.RESET}")

        # Run tests
        if parallel:
            self.run_parallel(test_files, workers)
        else:
            self.run_sequential(test_files)

        self.end_time = time.time()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Intelligent Master Test Runner for FakeAI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--parallel',
        nargs='?',
        const=4,
        type=int,
        metavar='WORKERS',
        help='Run tests in parallel (default: 4 workers)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=60,
        metavar='SECONDS',
        help='Timeout per test file (default: 60s)'
    )

    parser.add_argument(
        '--filter',
        choices=['passed', 'failed', 'error', 'timeout'],
        help='Filter results by status'
    )

    parser.add_argument(
        '--export',
        type=Path,
        metavar='FILE',
        help='Export results to JSON file'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output during test execution'
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )

    parser.add_argument(
        '--dir',
        type=Path,
        default=None,
        help='Test directory (default: auto-detect)'
    )

    args = parser.parse_args()

    # Disable colors if requested or not a TTY
    if args.no_color or not sys.stdout.isatty():
        Colors.disable()

    # Determine tests directory
    if args.dir:
        tests_dir = args.dir
    else:
        # Auto-detect: assume script is in tests/integration/
        script_dir = Path(__file__).parent
        tests_dir = script_dir.parent

    if not tests_dir.exists():
        print(f"{Colors.RED}Error: Tests directory not found: {tests_dir}{Colors.RESET}")
        sys.exit(1)

    # Create runner
    runner = TestRunner(
        tests_dir=tests_dir,
        timeout=args.timeout,
        verbose=args.verbose
    )

    # Run tests
    try:
        runner.run(
            parallel=args.parallel is not None,
            workers=args.parallel if args.parallel else 4
        )
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test run interrupted by user{Colors.RESET}")
        sys.exit(1)

    # Generate report
    report = runner.generate_report(filter_status=args.filter)
    print(report)

    # Export if requested
    if args.export:
        runner.export_json(args.export)

    # Exit with appropriate code
    failed_count = sum(1 for r in runner.results if r.status in ('failed', 'error', 'timeout'))
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == '__main__':
    main()
