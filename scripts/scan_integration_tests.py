#!/usr/bin/env python3
"""
Comprehensive Integration Test Scanner
Runs each test file individually and generates a detailed failure matrix.
"""

import subprocess
import json
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import sys

@dataclass
class TestFileResult:
    file_path: str
    file_name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    exit_code: int
    failure_messages: List[str]
    error_type: str

    @property
    def status(self) -> str:
        if self.errors > 0:
            return "ERROR"
        elif self.failed > 0:
            return "FAILED"
        elif self.skipped == self.total_tests:
            return "ALL_SKIPPED"
        elif self.passed == self.total_tests:
            return "PASSED"
        else:
            return "PARTIAL"

def parse_pytest_output(output: str) -> Dict[str, Any]:
    """Parse pytest output to extract test counts and failures."""
    result = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'errors': 0,
        'duration': 0.0,
        'failure_messages': [],
        'error_type': ''
    }

    # Parse summary line (e.g., "5 passed, 2 failed in 1.23s")
    summary_pattern = r'(\d+)\s+(passed|failed|skipped|error)'
    matches = re.findall(summary_pattern, output, re.IGNORECASE)

    for count, status in matches:
        count = int(count)
        status_lower = status.lower()
        if 'pass' in status_lower:
            result['passed'] = count
        elif 'fail' in status_lower:
            result['failed'] = count
        elif 'skip' in status_lower:
            result['skipped'] = count
        elif 'error' in status_lower:
            result['errors'] = count

    result['total'] = result['passed'] + result['failed'] + result['skipped'] + result['errors']

    # Parse duration
    duration_match = re.search(r'in\s+([\d.]+)s', output)
    if duration_match:
        result['duration'] = float(duration_match.group(1))

    # Extract failure messages (first 3)
    failure_sections = re.findall(r'FAILED.*?(?=FAILED|\Z)', output, re.DOTALL)
    for section in failure_sections[:3]:
        # Extract the actual error message
        lines = section.split('\n')
        for i, line in enumerate(lines):
            if 'AssertionError' in line or 'Error:' in line or 'assert' in line:
                msg = '\n'.join(lines[i:min(i+3, len(lines))]).strip()
                if msg:
                    result['failure_messages'].append(msg[:200])  # Limit to 200 chars
                break

    # Detect common error types
    if 'ModuleNotFoundError' in output or 'ImportError' in output:
        result['error_type'] = 'IMPORT_ERROR'
    elif 'AttributeError' in output:
        result['error_type'] = 'ATTRIBUTE_ERROR'
    elif 'AssertionError' in output:
        result['error_type'] = 'ASSERTION_ERROR'
    elif 'TypeError' in output:
        result['error_type'] = 'TYPE_ERROR'
    elif 'ConnectionError' in output or 'refused' in output:
        result['error_type'] = 'CONNECTION_ERROR'
    elif 'Timeout' in output:
        result['error_type'] = 'TIMEOUT'
    elif 'KeyError' in output:
        result['error_type'] = 'KEY_ERROR'

    return result

def run_test_file(test_file: Path) -> TestFileResult:
    """Run a single test file and capture results."""
    print(f"Testing: {test_file.name}...", end=" ", flush=True)

    try:
        result = subprocess.run(
            ['pytest', str(test_file), '-v', '--tb=short', '--no-header'],
            capture_output=True,
            text=True,
            timeout=60
        )

        output = result.stdout + result.stderr
        parsed = parse_pytest_output(output)

        test_result = TestFileResult(
            file_path=str(test_file),
            file_name=test_file.name,
            total_tests=parsed['total'],
            passed=parsed['passed'],
            failed=parsed['failed'],
            skipped=parsed['skipped'],
            errors=parsed['errors'],
            duration=parsed['duration'],
            exit_code=result.returncode,
            failure_messages=parsed['failure_messages'],
            error_type=parsed['error_type']
        )

        print(f"{test_result.status} ({test_result.passed}/{test_result.total})")
        return test_result

    except subprocess.TimeoutExpired:
        print("TIMEOUT")
        return TestFileResult(
            file_path=str(test_file),
            file_name=test_file.name,
            total_tests=0,
            passed=0,
            failed=0,
            skipped=0,
            errors=1,
            duration=60.0,
            exit_code=-1,
            failure_messages=["Test execution timed out after 60 seconds"],
            error_type="TIMEOUT"
        )
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return TestFileResult(
            file_path=str(test_file),
            file_name=test_file.name,
            total_tests=0,
            passed=0,
            failed=0,
            skipped=0,
            errors=1,
            duration=0.0,
            exit_code=-1,
            failure_messages=[str(e)],
            error_type="EXECUTION_ERROR"
        )

def categorize_difficulty(result: TestFileResult) -> str:
    """Categorize fix difficulty based on error patterns."""
    # EASY: Import errors, simple attribute errors
    if result.error_type in ['IMPORT_ERROR']:
        return 'EASY'

    # EASY: All tests passed
    if result.status == 'PASSED':
        return 'NONE'

    # EASY: All tests skipped
    if result.status == 'ALL_SKIPPED':
        return 'NONE'

    # MEDIUM: Type errors, key errors, simple assertions
    if result.error_type in ['TYPE_ERROR', 'KEY_ERROR', 'ATTRIBUTE_ERROR']:
        return 'MEDIUM'

    # HARD: Connection errors, timeouts, complex assertions
    if result.error_type in ['CONNECTION_ERROR', 'TIMEOUT']:
        return 'HARD'

    # MEDIUM: Assertion errors (depends on complexity)
    if result.error_type == 'ASSERTION_ERROR':
        return 'MEDIUM'

    # Default
    if result.failed > 0 or result.errors > 0:
        return 'MEDIUM'

    return 'NONE'

def generate_markdown_table(results: List[TestFileResult]) -> str:
    """Generate a comprehensive markdown table."""
    lines = []
    lines.append("# Integration Test Failure Matrix")
    lines.append("")
    lines.append(f"Total Test Files: {len(results)}")
    lines.append(f"Generated: {subprocess.check_output(['date']).decode().strip()}")
    lines.append("")

    # Summary statistics
    total_passed = sum(r.passed for r in results)
    total_failed = sum(r.failed for r in results)
    total_errors = sum(r.errors for r in results)
    total_skipped = sum(r.skipped for r in results)
    total_tests = sum(r.total_tests for r in results)

    lines.append("## Summary")
    lines.append(f"- Total Tests: {total_tests}")
    lines.append(f"- Passed: {total_passed} ({100*total_passed/total_tests if total_tests > 0 else 0:.1f}%)")
    lines.append(f"- Failed: {total_failed}")
    lines.append(f"- Errors: {total_errors}")
    lines.append(f"- Skipped: {total_skipped}")
    lines.append("")

    # Group by status
    passed_files = [r for r in results if r.status == 'PASSED']
    failed_files = [r for r in results if r.status == 'FAILED']
    error_files = [r for r in results if r.status == 'ERROR']
    partial_files = [r for r in results if r.status == 'PARTIAL']
    skipped_files = [r for r in results if r.status == 'ALL_SKIPPED']

    lines.append(f"- Files Fully Passing: {len(passed_files)}")
    lines.append(f"- Files with Failures: {len(failed_files)}")
    lines.append(f"- Files with Errors: {len(error_files)}")
    lines.append(f"- Files Partially Passing: {len(partial_files)}")
    lines.append(f"- Files All Skipped: {len(skipped_files)}")
    lines.append("")

    # Main table
    lines.append("## Detailed Results")
    lines.append("")
    lines.append("| File | Status | Tests | Pass | Fail | Error | Skip | Error Type | Difficulty |")
    lines.append("|------|--------|-------|------|------|-------|------|------------|------------|")

    for result in sorted(results, key=lambda r: (r.status != 'PASSED', r.failed + r.errors, r.file_name)):
        difficulty = categorize_difficulty(result)
        status_emoji = {
            'PASSED': '✅',
            'FAILED': '❌',
            'ERROR': '💥',
            'PARTIAL': '⚠️',
            'ALL_SKIPPED': '⏭️'
        }.get(result.status, '❓')

        lines.append(f"| {result.file_name} | {status_emoji} {result.status} | {result.total_tests} | "
                    f"{result.passed} | {result.failed} | {result.errors} | {result.skipped} | "
                    f"{result.error_type or 'N/A'} | {difficulty} |")

    lines.append("")

    # Failure details
    lines.append("## Failure Details")
    lines.append("")

    problem_files = [r for r in results if r.status in ['FAILED', 'ERROR', 'PARTIAL']]
    if problem_files:
        for result in sorted(problem_files, key=lambda r: (r.errors + r.failed, r.file_name), reverse=True):
            lines.append(f"### {result.file_name}")
            lines.append(f"- **Status**: {result.status}")
            lines.append(f"- **Tests**: {result.passed}/{result.total_tests} passed")
            lines.append(f"- **Error Type**: {result.error_type or 'Unknown'}")
            lines.append(f"- **Difficulty**: {categorize_difficulty(result)}")

            if result.failure_messages:
                lines.append(f"- **Sample Failures**:")
                for i, msg in enumerate(result.failure_messages[:3], 1):
                    lines.append(f"  {i}. `{msg}`")

            lines.append("")
    else:
        lines.append("No failures detected!")
        lines.append("")

    # Categorization by difficulty
    lines.append("## Fix Priority by Difficulty")
    lines.append("")

    for difficulty in ['EASY', 'MEDIUM', 'HARD']:
        files = [r for r in results if categorize_difficulty(r) == difficulty]
        if files:
            lines.append(f"### {difficulty} ({len(files)} files)")
            lines.append("")
            for result in sorted(files, key=lambda r: r.errors + r.failed, reverse=True):
                lines.append(f"- **{result.file_name}**: {result.failed + result.errors} issues ({result.error_type or 'Unknown'})")
            lines.append("")

    # Common error patterns
    lines.append("## Common Error Patterns")
    lines.append("")
    error_type_counts = {}
    for result in results:
        if result.error_type:
            error_type_counts[result.error_type] = error_type_counts.get(result.error_type, 0) + 1

    if error_type_counts:
        for error_type, count in sorted(error_type_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- **{error_type}**: {count} files")
        lines.append("")
    else:
        lines.append("No common error patterns detected.")
        lines.append("")

    return '\n'.join(lines)

def main():
    """Main execution function."""
    # Find all integration test files
    integration_dir = Path('tests/integration')

    if not integration_dir.exists():
        print(f"Error: Directory {integration_dir} not found!")
        sys.exit(1)

    test_files = sorted(integration_dir.glob('test_*.py'))

    if not test_files:
        print(f"Error: No test files found in {integration_dir}")
        sys.exit(1)

    print(f"\nFound {len(test_files)} integration test files")
    print("=" * 80)

    # Run all tests
    results = []
    for test_file in test_files:
        result = run_test_file(test_file)
        results.append(result)

    print("=" * 80)
    print("\nGenerating report...")

    # Generate markdown report
    markdown_report = generate_markdown_table(results)

    # Write to file
    report_path = Path('INTEGRATION_TEST_MATRIX.md')
    report_path.write_text(markdown_report)
    print(f"\nReport saved to: {report_path.absolute()}")

    # Also save JSON data
    json_path = Path('integration_test_results.json')
    json_data = {
        'results': [asdict(r) for r in results],
        'summary': {
            'total_files': len(results),
            'total_tests': sum(r.total_tests for r in results),
            'total_passed': sum(r.passed for r in results),
            'total_failed': sum(r.failed for r in results),
            'total_errors': sum(r.errors for r in results),
            'total_skipped': sum(r.skipped for r in results)
        }
    }
    json_path.write_text(json.dumps(json_data, indent=2))
    print(f"JSON data saved to: {json_path.absolute()}")

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Test Files: {len(results)}")
    print(f"Total Tests: {sum(r.total_tests for r in results)}")
    print(f"Passed: {sum(r.passed for r in results)}")
    print(f"Failed: {sum(r.failed for r in results)}")
    print(f"Errors: {sum(r.errors for r in results)}")
    print(f"Skipped: {sum(r.skipped for r in results)}")
    print("=" * 80)

    # Print console-friendly table
    print("\nQuick View:")
    print("-" * 100)
    print(f"{'File':<40} {'Status':<12} {'Tests':<8} {'Pass':<6} {'Fail':<6} {'Error':<7} {'Type':<20}")
    print("-" * 100)

    for result in sorted(results, key=lambda r: (r.status != 'PASSED', r.failed + r.errors, r.file_name)):
        file_display = result.file_name[:38] + '..' if len(result.file_name) > 40 else result.file_name
        print(f"{file_display:<40} {result.status:<12} {result.total_tests:<8} {result.passed:<6} "
              f"{result.failed:<6} {result.errors:<7} {result.error_type[:18]:<20}")

    print("-" * 100)

if __name__ == '__main__':
    main()
