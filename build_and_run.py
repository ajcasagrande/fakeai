#!/usr/bin/env python3
"""
Quick Build and Run Script for FakeAI Dashboard

This is the simplest way to get started with FakeAI dashboard.
Just run: python build_and_run.py
"""

import subprocess
import sys


def main():
    """Quick build and run."""
    print("=" * 70)
    print(" FakeAI Dashboard - Quick Start")
    print("=" * 70)
    print()

    # Build dashboard
    print("Step 1/2: Building dashboard...")
    print("-" * 70)
    result = subprocess.run(
        [sys.executable, "-m", "fakeai.dashboard.build"],
        cwd=sys.path[0] if sys.path else ".",
    )

    if result.returncode != 0:
        print("\n❌ Build failed!")
        return 1

    print("\n✓ Build successful!")
    print()

    # Start server
    print("Step 2/2: Starting server...")
    print("-" * 70)
    print()
    print("Dashboard: http://localhost:9002/app")
    print("API:       http://localhost:9002/v1")
    print("Metrics:   http://localhost:9002/metrics")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    try:
        subprocess.run(
            [
                sys.executable, "-m", "uvicorn",
                "fakeai.app:app",
                "--host", "0.0.0.0",
                "--port", "9002"
            ],
            cwd=sys.path[0] if sys.path else ".",
        )
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
