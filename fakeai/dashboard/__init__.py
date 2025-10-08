"""
FakeAI Dashboard Module

This module provides the build infrastructure for the React-based dashboard.
The dashboard can be built and included in the pip package.
"""

from pathlib import Path

__all__ = ["get_dashboard_path", "is_dashboard_built"]


def get_dashboard_path() -> Path:
    """
    Get the path to the built dashboard files.

    Returns:
        Path: Path to the static/spa directory containing the built dashboard.
    """
    return Path(__file__).parent.parent / "static" / "spa"


def is_dashboard_built() -> bool:
    """
    Check if the dashboard has been built.

    Returns:
        bool: True if the dashboard index.html exists, False otherwise.
    """
    dashboard_path = get_dashboard_path()
    index_html = dashboard_path / "index.html"
    return index_html.exists()
