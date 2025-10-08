#!/usr/bin/env python3
"""
FakeAI Dashboard Launcher

This script provides a convenient way to build and start the FakeAI server
with the integrated dashboard.

Usage:
    python start_dashboard.py                    # Build and start server
    python start_dashboard.py --skip-build       # Start server without building
    python start_dashboard.py --build-only       # Only build dashboard
    python start_dashboard.py --port 8000        # Start on custom port
    python start_dashboard.py --host 0.0.0.0     # Bind to all interfaces
"""

import argparse
import subprocess
import sys


def build_dashboard(skip_install=False):
    """Build the dashboard using the build module."""
    print("\n" + "="*60)
    print("Building Dashboard")
    print("="*60 + "\n")

    cmd = [sys.executable, "-m", "fakeai.dashboard.build"]
    if skip_install:
        cmd.append("--skip-install")

    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\nError building dashboard: {e}", file=sys.stderr)
        return False


def start_server(host="0.0.0.0", port=9002, reload=False):
    """Start the FakeAI server."""
    print("\n" + "="*60)
    print(f"Starting FakeAI Server on {host}:{port}")
    print("="*60 + "\n")
    print(f"Dashboard will be available at: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/app")
    print(f"API endpoints at: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/v1")
    print(f"Metrics at: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/metrics")
    print("\nPress Ctrl+C to stop the server\n")

    cmd = [
        sys.executable, "-m", "uvicorn",
        "fakeai.app:app",
        "--host", host,
        "--port", str(port),
    ]

    if reload:
        cmd.append("--reload")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
    except subprocess.CalledProcessError as e:
        print(f"\nError starting server: {e}", file=sys.stderr)
        return False

    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        pass
    except ImportError as e:
        print(f"\nError: Required dependency not found: {e}", file=sys.stderr)
        print("\nPlease install the package first:")
        print("  pip install -e .")
        print("\nOr install dependencies:")
        print("  pip install uvicorn fastapi")
        return False

    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build and start FakeAI server with dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip building the dashboard",
    )
    parser.add_argument(
        "--build-only",
        action="store_true",
        help="Only build the dashboard, don't start server",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip npm install when building (faster if deps already installed)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9002,
        help="Port to bind to (default: 9002)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (development mode)",
    )

    args = parser.parse_args()

    # Check dependencies
    if not args.build_only and not check_dependencies():
        return 1

    # Build dashboard if not skipped
    if not args.skip_build:
        if not build_dashboard(skip_install=args.skip_install):
            print("\nFailed to build dashboard. Exiting.", file=sys.stderr)
            return 1
    else:
        print("\n==> Skipping dashboard build (--skip-build flag)")

    # Exit if build-only mode
    if args.build_only:
        print("\n==> Build complete (--build-only flag). Not starting server.")
        return 0

    # Start server
    if not start_server(host=args.host, port=args.port, reload=args.reload):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
