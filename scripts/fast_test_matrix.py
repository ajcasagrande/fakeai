#!/usr/bin/env python3
"""Fast test matrix - runs each file with 10s timeout."""

import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

def test_file(test_file):
    """Test a single file with short timeout."""
    fname = test_file.name
    try:
        result = subprocess.run(
            ['pytest', str(test_file), '-v', '--tb=line', '-q'],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout + result.stderr

        # Quick parse
        import re
        passed = len(re.findall(r'PASSED', output))
        failed = len(re.findall(r'FAILED', output))
        errors = len(re.findall(r'ERROR', output))
        skipped = len(re.findall(r'SKIPPED', output))

        # Get error type
        error_type = 'N/A'
        if 'ImportError' in output or 'ModuleNotFoundError' in output:
            error_type = 'IMPORT'
        elif 'AttributeError' in output:
            error_type = 'ATTRIBUTE'
        elif 'AssertionError' in output:
            error_type = 'ASSERTION'
        elif 'ConnectionError' in output or 'Connection refused' in output:
            error_type = 'CONNECTION'
        elif 'TypeError' in output:
            error_type = 'TYPE'

        # Extract first failure
        first_failure = ''
        fail_match = re.search(r'FAILED.*?- (.*?)(?:\n|$)', output)
        if fail_match:
            first_failure = fail_match.group(1)[:80]

        status = 'PASS'
        if errors > 0:
            status = 'ERROR'
        elif failed > 0:
            status = 'FAIL'
        elif passed == 0 and skipped > 0:
            status = 'SKIP'

        return {
            'file': fname,
            'status': status,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'skipped': skipped,
            'error_type': error_type,
            'first_failure': first_failure,
            'exit_code': result.returncode
        }

    except subprocess.TimeoutExpired:
        return {
            'file': fname,
            'status': 'TIMEOUT',
            'passed': 0,
            'failed': 0,
            'errors': 1,
            'skipped': 0,
            'error_type': 'TIMEOUT',
            'first_failure': 'Test execution timed out',
            'exit_code': -1
        }
    except Exception as e:
        return {
            'file': fname,
            'status': 'EXCEPTION',
            'passed': 0,
            'failed': 0,
            'errors': 1,
            'skipped': 0,
            'error_type': 'EXCEPTION',
            'first_failure': str(e)[:80],
            'exit_code': -1
        }

def main():
    integration_dir = Path('tests/integration')
    test_files = sorted(integration_dir.glob('test_*.py'))

    print(f"Testing {len(test_files)} files (10s timeout each)...\n")

    # Test files in parallel
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(test_file, f): f for f in test_files}

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            status_emoji = {
                'PASS': '✅', 'FAIL': '❌', 'ERROR': '💥',
                'SKIP': '⏭️', 'TIMEOUT': '⏱️', 'EXCEPTION': '💀'
            }.get(result['status'], '❓')
            print(f"{status_emoji} {result['file']:<45} {result['status']:<10} "
                  f"P:{result['passed']:<3} F:{result['failed']:<3} E:{result['errors']:<3}")

    # Sort results
    results.sort(key=lambda x: (x['status'] != 'PASS', x['failed'] + x['errors'], x['file']), reverse=True)

    # Generate report
    total_tests = sum(r['passed'] + r['failed'] + r['errors'] + r['skipped'] for r in results)
    total_passed = sum(r['passed'] for r in results)
    total_failed = sum(r['failed'] for r in results)
    total_errors = sum(r['errors'] for r in results)
    total_skipped = sum(r['skipped'] for r in results)

    report_lines = [
        "\n" + "=" * 120,
        "INTEGRATION TEST FAILURE MATRIX",
        "=" * 120,
        f"\nSUMMARY:",
        f"  Total Files: {len(results)}",
        f"  Total Tests: {total_tests}",
        f"  Passed: {total_passed} ({100*total_passed/total_tests if total_tests > 0 else 0:.1f}%)",
        f"  Failed: {total_failed}",
        f"  Errors: {total_errors}",
        f"  Skipped: {total_skipped}",
        "",
        f"  Files Passing: {sum(1 for r in results if r['status'] == 'PASS')}",
        f"  Files Failing: {sum(1 for r in results if r['status'] in ['FAIL', 'ERROR'])}",
        f"  Files Timeout: {sum(1 for r in results if r['status'] == 'TIMEOUT')}",
        "\n" + "=" * 120,
        f"{'File':<45} {'Status':<12} {'Pass':<6} {'Fail':<6} {'Error':<6} {'Skip':<6} {'Type':<12} {'Difficulty':<12}",
        "=" * 120
    ]

    for r in results:
        # Categorize difficulty
        difficulty = 'NONE'
        if r['status'] == 'PASS' or r['status'] == 'SKIP':
            difficulty = 'NONE'
        elif r['error_type'] == 'IMPORT':
            difficulty = 'EASY'
        elif r['error_type'] in ['TYPE', 'ATTRIBUTE']:
            difficulty = 'MEDIUM'
        elif r['error_type'] in ['CONNECTION', 'TIMEOUT']:
            difficulty = 'HARD'
        elif r['failed'] > 0 or r['errors'] > 0:
            difficulty = 'MEDIUM'

        report_lines.append(
            f"{r['file']:<45} {r['status']:<12} {r['passed']:<6} {r['failed']:<6} "
            f"{r['errors']:<6} {r['skipped']:<6} {r['error_type']:<12} {difficulty:<12}"
        )

    report_lines.append("=" * 120)

    # Problem files
    report_lines.append("\n" + "=" * 120)
    report_lines.append("PROBLEM FILES (with first failure)")
    report_lines.append("=" * 120)

    for r in results:
        if r['status'] in ['FAIL', 'ERROR', 'TIMEOUT', 'EXCEPTION']:
            report_lines.append(f"\n{r['file']}:")
            report_lines.append(f"  Status: {r['status']}")
            report_lines.append(f"  Issues: {r['failed']} failed, {r['errors']} errors")
            report_lines.append(f"  Error Type: {r['error_type']}")
            if r['first_failure']:
                report_lines.append(f"  First Failure: {r['first_failure']}")

    report_lines.append("\n" + "=" * 120)

    # Categorization
    report_lines.append("\nFIX PRIORITY BY DIFFICULTY:")
    report_lines.append("=" * 120)

    for difficulty in ['EASY', 'MEDIUM', 'HARD']:
        files = [r for r in results if r['status'] != 'PASS' and
                 ((r['error_type'] == 'IMPORT' and difficulty == 'EASY') or
                  (r['error_type'] in ['TYPE', 'ATTRIBUTE', 'ASSERTION'] and difficulty == 'MEDIUM') or
                  (r['error_type'] in ['CONNECTION', 'TIMEOUT'] and difficulty == 'HARD'))]
        if files:
            report_lines.append(f"\n{difficulty} ({len(files)} files):")
            for r in files:
                report_lines.append(f"  - {r['file']}: {r['failed'] + r['errors']} issues ({r['error_type']})")

    report_lines.append("\n" + "=" * 120)

    report = '\n'.join(report_lines)
    print(report)

    # Save
    Path('INTEGRATION_TEST_MATRIX.txt').write_text(report)
    Path('integration_results.json').write_text(json.dumps(results, indent=2))

    print("\n✅ Report saved to: INTEGRATION_TEST_MATRIX.txt")
    print("✅ JSON data saved to: integration_results.json")

if __name__ == '__main__':
    main()
