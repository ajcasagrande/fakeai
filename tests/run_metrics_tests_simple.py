#!/usr/bin/env python3
"""
Simple Test Runner for FakeAI Metrics Tests

Runs metrics tests without importing the full app infrastructure.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run metrics tests directly with pytest."""
    test_dir = Path(__file__).parent
    project_root = test_dir.parent

    # Metrics test patterns
    metrics_tests = [
        "test_streaming_metrics_tracker.py",
        "test_error_metrics_tracker.py",
        "test_cost_tracker.py",
        "test_event_*.py",
        "test_metrics_*.py",
        "test_*_metrics.py",
        "test_prometheus_export.py",
        "test_slo_monitoring.py",
    ]

    # Build pytest command
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        "--cov=fakeai/events",
        "--cov=fakeai/streaming_metrics_tracker.py",
        "--cov=fakeai/error_metrics_tracker.py",
        "--cov=fakeai/cost_tracker.py",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=json",
        "--tb=short",
        "--color=yes",
        "-x",  # Stop on first failure
    ]

    # Add test files
    for pattern in metrics_tests:
        test_files = list(test_dir.glob(pattern))
        for test_file in test_files:
            cmd.append(str(test_file))

    print(f"Running: {' '.join(cmd[:10])}...")
    print(f"Testing {len(cmd) - 10} files\n")

    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
