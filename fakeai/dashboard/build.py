#!/usr/bin/env python3
"""
Dashboard Build Script

This script builds the React dashboard and copies the output to the static directory
for serving as part of the fakeai package.

Usage:
    python -m fakeai.dashboard.build
    python -m fakeai.dashboard.build --skip-install
    python -m fakeai.dashboard.build --clean
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


class DashboardBuilder:
    """Handles building and packaging the React dashboard."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.dashboard_dir = project_root / "dashboard"
        self.static_dir = project_root / "fakeai" / "static" / "app"
        self.dist_dir = self.dashboard_dir / "dist"

    def check_node_installed(self) -> bool:
        """Check if Node.js is installed."""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            print(f"Node.js version: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def check_npm_installed(self) -> bool:
        """Check if npm is installed."""
        try:
            result = subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            print(f"npm version: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def install_dependencies(self) -> bool:
        """Install npm dependencies."""
        print("\n==> Installing npm dependencies...")
        try:
            subprocess.run(
                ["npm", "install"],
                cwd=self.dashboard_dir,
                check=True,
            )
            print("Dependencies installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {e}", file=sys.stderr)
            return False

    def build_dashboard(self) -> bool:
        """Build the React dashboard using Vite."""
        print("\n==> Building dashboard...")
        try:
            subprocess.run(
                ["npm", "run", "build"],
                cwd=self.dashboard_dir,
                check=True,
            )
            print("Dashboard built successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error building dashboard: {e}", file=sys.stderr)
            return False

    def copy_to_static(self) -> bool:
        """Copy built files to static directory."""
        print(f"\n==> Copying built files to {self.static_dir}...")

        if not self.dist_dir.exists():
            print(
                f"Error: Build directory {
                    self.dist_dir} does not exist",
                file=sys.stderr)
            return False

        # Create static directory if it doesn't exist
        self.static_dir.mkdir(parents=True, exist_ok=True)

        # Remove old files
        if self.static_dir.exists():
            for item in self.static_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

        # Copy new files
        try:
            for item in self.dist_dir.iterdir():
                if item.is_dir():
                    shutil.copytree(item, self.static_dir / item.name)
                else:
                    shutil.copy2(item, self.static_dir / item.name)
            print(f"Files copied successfully to {self.static_dir}")
            return True
        except Exception as e:
            print(f"Error copying files: {e}", file=sys.stderr)
            return False

    def clean(self) -> bool:
        """Clean build artifacts."""
        print("\n==> Cleaning build artifacts...")

        # Remove dist directory
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            print(f"Removed {self.dist_dir}")

        # Remove static directory
        if self.static_dir.exists():
            shutil.rmtree(self.static_dir)
            print(f"Removed {self.static_dir}")

        # Remove node_modules (optional, commented out by default)
        # node_modules = self.dashboard_dir / "node_modules"
        # if node_modules.exists():
        #     shutil.rmtree(node_modules)
        #     print(f"Removed {node_modules}")

        print("Clean completed.")
        return True

    def verify_build(self) -> bool:
        """Verify that the build was successful."""
        print("\n==> Verifying build...")

        # Check if index.html exists
        index_html = self.static_dir / "index.html"
        if not index_html.exists():
            print(
                "Error: index.html not found in static directory",
                file=sys.stderr)
            return False

        # Check if assets directory exists
        assets_dir = self.static_dir / "assets"
        if not assets_dir.exists():
            print("Warning: assets directory not found")
            return True  # Still return True as some builds might not have assets

        print(f"Build verification successful. Files in {self.static_dir}:")
        for item in self.static_dir.iterdir():
            print(f"  - {item.name}")

        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build FakeAI dashboard")
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip npm install step",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts and exit",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing build",
    )
    args = parser.parse_args()

    # Determine project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent

    builder = DashboardBuilder(project_root)

    # Handle clean
    if args.clean:
        return 0 if builder.clean() else 1

    # Handle verify only
    if args.verify_only:
        return 0 if builder.verify_build() else 1

    # Check prerequisites
    print("==> Checking prerequisites...")
    if not builder.check_node_installed():
        print("\nError: Node.js is not installed.", file=sys.stderr)
        print("Please install Node.js from https://nodejs.org/", file=sys.stderr)
        print("\nAlternatively, you can use the pre-built dashboard by:")
        print("  1. Downloading the pre-built assets from GitHub releases")
        print("  2. Or building on a system with Node.js installed")
        return 1

    if not builder.check_npm_installed():
        print("\nError: npm is not installed.", file=sys.stderr)
        print(
            "npm should come with Node.js. Please reinstall Node.js.",
            file=sys.stderr)
        return 1

    # Check if dashboard directory exists
    if not builder.dashboard_dir.exists():
        print(
            f"\nError: Dashboard directory {
                builder.dashboard_dir} does not exist",
            file=sys.stderr)
        return 1

    # Install dependencies
    if not args.skip_install:
        if not builder.install_dependencies():
            return 1
    else:
        print("\n==> Skipping npm install (--skip-install flag)")

    # Build dashboard
    if not builder.build_dashboard():
        return 1

    # Copy to static
    if not builder.copy_to_static():
        return 1

    # Verify build
    if not builder.verify_build():
        return 1

    print("\n" + "=" * 60)
    print("Dashboard build completed successfully!")
    print("=" * 60)
    print(f"\nDashboard files are available at: {builder.static_dir}")
    print("\nYou can now install the package with:")
    print("  pip install -e .")
    print("\nOr build a distribution package with:")
    print("  python -m build")

    return 0


if __name__ == "__main__":
    sys.exit(main())
