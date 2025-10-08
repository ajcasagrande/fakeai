"""Pytest configuration for integration tests."""

import os
from unittest.mock import patch

import pytest

from .utils import FakeAIClient, ServerManager


@pytest.fixture
def client(request):
    """Provide a FakeAI client for testing."""
    # Check for server_config marker
    marker = request.node.get_closest_marker("server_config")
    if marker:
        config = marker.kwargs

        # Extract configuration
        enable_context_validation = config.get("enable_context_validation", True)

        # Set up environment variables
        env_vars = {
            "FAKEAI_FEATURES__ENABLE_CONTEXT_VALIDATION": str(enable_context_validation).lower(),
        }

        # Patch environment and reload config
        with patch.dict(os.environ, env_vars, clear=False):
            # Reload the app config to pick up new environment variables
            import sys

            from fakeai.config import AppConfig
            app_module = sys.modules['fakeai.app']

            # Create new config with updated environment
            new_config = AppConfig()

            # Store original config
            original_config = app_module.config

            # Update app config
            app_module.config = new_config

            # Also update fakeai_service config
            app_module.fakeai_service.config = new_config

            try:
                yield FakeAIClient()
            finally:
                # Restore original config
                app_module.config = original_config
                app_module.fakeai_service.config = original_config
    else:
        yield FakeAIClient()


@pytest.fixture
def server():
    """Provide a ServerManager for WebSocket and other advanced tests."""
    return ServerManager()


@pytest.fixture
def sample_speech_input():
    """Provide sample text for speech synthesis testing."""
    return "Hello, this is a sample text for testing the text-to-speech functionality."


@pytest.fixture
def sample_messages():
    """Provide sample messages for chat completion testing."""
    return [
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there! How can I help you today?"},
        {"role": "user", "content": "Tell me a joke."}
    ]


@pytest.fixture
def collect_metrics():
    """Context manager fixture for collecting metrics before/after operations."""
    from contextlib import contextmanager

    @contextmanager
    def _collect():
        """Collect metrics."""

        class MetricsCollector:
            def __init__(self):
                self.before = None
                self.after = None

        collector = MetricsCollector()
        # Get metrics before
        from fakeai.app import metrics_tracker

        collector.before = metrics_tracker.get_metrics()

        yield collector

        # Get metrics after
        collector.after = metrics_tracker.get_metrics()

    return _collect


@pytest.fixture
def server_function_scoped(request):
    """
    Provide a configured test server for function-scoped tests.

    Supports configuration via @pytest.mark.server_config decorator:
    - rate_limit_enabled: Enable/disable rate limiting
    - api_keys: List of API keys to use
    - env_overrides: Dict of environment variable overrides
    """
    # Get configuration from marker
    marker = request.node.get_closest_marker("server_config")
    if marker:
        config = marker.kwargs
    else:
        config = {}

    # Extract configuration
    rate_limit_enabled = config.get("rate_limit_enabled", False)
    enable_context_validation = config.get("enable_context_validation", True)
    api_keys = config.get("api_keys", ["test-key-1", "test-key-2"])
    env_overrides = config.get("env_overrides", {})

    # Set up environment variables
    env_vars = {
        "FAKEAI_RATE_LIMITS__ENABLED": str(rate_limit_enabled).lower(),
        "FAKEAI_FEATURES__ENABLE_CONTEXT_VALIDATION": str(enable_context_validation).lower(),
        "FAKEAI_REQUIRE_API_KEY": "true",
    }

    # Apply env_overrides (already in proper format from tests)
    for key, value in env_overrides.items():
        env_vars[key] = str(value)

    # Patch environment and reload config
    with patch.dict(os.environ, env_vars, clear=False):
        # Reload the app config to pick up new environment variables
        import sys

        from fakeai.config import AppConfig
        app_module = sys.modules['fakeai.app']

        # Create new config with updated environment
        new_config = AppConfig()

        # Store original config
        original_config = app_module.config

        # Update rate limiter configuration
        app_module.rate_limiter.reset()  # Reset all rate limit buckets
        app_module.rate_limiter.configure(
            tier=new_config.rate_limit_tier,
            rpm_override=new_config.rate_limit_rpm,
            tpm_override=new_config.rate_limit_tpm,
        )

        # Update app config
        app_module.config = new_config

        # Create server info object
        class ServerInfo:
            def __init__(self, keys):
                self.base_url = "http://testserver"
                self.api_keys = keys

        try:
            yield ServerInfo(api_keys)
        finally:
            # Restore original config
            app_module.config = original_config
            # Reset rate limiter
            app_module.rate_limiter.reset()
