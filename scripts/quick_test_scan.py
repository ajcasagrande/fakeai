#!/usr/bin/env python3
"""Quick integration test scanner - runs all tests at once with detailed output."""

import subprocess
import re
from pathlib import Path
from collections import defaultdict

def main():
    integration_dir = Path('tests/integration')
    test_files = sorted(integration_dir.glob('test_*.py'))

    print(f"Found {len(test_files)} test files\n")
    print("Running all integration tests with detailed output...")
    print("=" * 100)

    # Run pytest with JSON report
    result = subprocess.run(
        ['pytest', 'tests/integration/', '-v', '--tb=short', '-x', '--maxfail=100'],
        capture_output=True,
        text=True,
        timeout=180
    )

    output = result.stdout + result.stderr

    # Parse output for per-file results
    file_results = defaultdict(lambda: {'passed': 0, 'failed': 0, 'error': 0, 'skipped': 0, 'failures': []})

    current_file = None
    for line in output.split('\n'):
        # Detect test file
        if 'tests/integration/test_' in line:
            match = re.search(r'tests/integration/(test_\w+\.py)', line)
            if match:
                current_file = match.group(1)

        # Count results
        if current_file:
            if ' PASSED' in line:
                file_results[current_file]['passed'] += 1
            elif ' FAILED' in line:
                file_results[current_file]['failed'] += 1
                # Extract failure info
                failure_match = re.search(r'FAILED.*?::(.*?) -', line)
                if failure_match:
                    file_results[current_file]['failures'].append(failure_match.group(1))
            elif ' ERROR' in line:
                file_results[current_file]['error'] += 1
            elif ' SKIPPED' in line:
                file_results[current_file]['skipped'] += 1

    # Also parse summary
    summary_match = re.search(r'(\d+) passed', output)
    total_passed = int(summary_match.group(1)) if summary_match else 0

    summary_match = re.search(r'(\d+) failed', output)
    total_failed = int(summary_match.group(1)) if summary_match else 0

    summary_match = re.search(r'(\d+) error', output)
    total_errors = int(summary_match.group(1)) if summary_match else 0

    summary_match = re.search(r'(\d+) skipped', output)
    total_skipped = int(summary_match.group(1)) if summary_match else 0

    total_tests = total_passed + total_failed + total_errors + total_skipped

    # Generate report
    lines = []
    lines.append("\n" + "=" * 100)
    lines.append("INTEGRATION TEST FAILURE MATRIX")
    lines.append("=" * 100)
    lines.append(f"\nTOTAL SUMMARY:")
    lines.append(f"  Tests: {total_tests}")
    lines.append(f"  Passed: {total_passed} ({100*total_passed/total_tests if total_tests > 0 else 0:.1f}%)")
    lines.append(f"  Failed: {total_failed}")
    lines.append(f"  Errors: {total_errors}")
    lines.append(f"  Skipped: {total_skipped}")
    lines.append("\n" + "=" * 100)
    lines.append(f"{'File':<45} {'Status':<10} {'Pass':<6} {'Fail':<6} {'Error':<6} {'Skip':<6}")
    lines.append("=" * 100)

    for test_file in test_files:
        fname = test_file.name
        if fname in file_results:
            r = file_results[fname]
            total_file = r['passed'] + r['failed'] + r['error'] + r['skipped']

            if r['error'] > 0:
                status = "💥 ERROR"
            elif r['failed'] > 0:
                status = "❌ FAIL"
            elif total_file == r['skipped']:
                status = "⏭️ SKIP"
            elif total_file == r['passed']:
                status = "✅ PASS"
            else:
                status = "⚠️ PARTIAL"

            lines.append(f"{fname:<45} {status:<10} {r['passed']:<6} {r['failed']:<6} {r['error']:<6} {r['skipped']:<6}")
        else:
            lines.append(f"{fname:<45} {'❓ NORUN':<10} {0:<6} {0:<6} {0:<6} {0:<6}")

    lines.append("=" * 100)

    # Detailed failures
    lines.append("\n" + "=" * 100)
    lines.append("DETAILED FAILURES")
    lines.append("=" * 100)

    for fname, data in sorted(file_results.items(), key=lambda x: x[1]['failed'] + x[1]['error'], reverse=True):
        if data['failed'] > 0 or data['error'] > 0:
            lines.append(f"\n{fname}:")
            lines.append(f"  Failed: {data['failed']}, Errors: {data['error']}")
            if data['failures']:
                lines.append(f"  Sample failures:")
                for failure in data['failures'][:3]:
                    lines.append(f"    - {failure}")

    report = '\n'.join(lines)
    print(report)

    # Save report
    Path('INTEGRATION_TEST_MATRIX.txt').write_text(report)
    print("\n\nReport saved to: INTEGRATION_TEST_MATRIX.txt")

    # Print raw pytest output for debugging
    print("\n" + "=" * 100)
    print("PYTEST OUTPUT (Last 100 lines):")
    print("=" * 100)
    print('\n'.join(output.split('\n')[-100:]))

if __name__ == '__main__':
    main()
