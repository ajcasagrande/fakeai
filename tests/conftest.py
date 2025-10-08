"""
Pytest fixtures for FakeAI tests.

Provides shared fixtures for testing without duplicating setup code.
"""

import pytest
from fastapi.testclient import TestClient

from fakeai.app import app
from fakeai.config import AppConfig
from fakeai.fakeai_service import FakeAIService


@pytest.fixture
def config_no_auth():
    """Config with authentication disabled for testing."""
    return AppConfig(
        require_api_key=False,
        response_delay=0.0,  # Faster tests
        random_delay=False,  # Predictable tests
    )


@pytest.fixture
def config_with_auth():
    """Config with authentication enabled for testing."""
    return AppConfig(
        require_api_key=True,
        api_keys=["test-key-1", "test-key-2"],
        response_delay=0.0,
        random_delay=False,
    )


@pytest.fixture
def service_no_auth(config_no_auth):
    """FakeAI service without authentication."""
    return FakeAIService(config_no_auth)


@pytest.fixture
def service_with_auth(config_with_auth):
    """FakeAI service with authentication."""
    return FakeAIService(config_with_auth)


@pytest.fixture
def client_no_auth(config_no_auth, monkeypatch):
    """Test client with authentication disabled."""
    # Monkeypatch the config to disable auth
    monkeypatch.setenv("FAKEAI_REQUIRE_API_KEY", "false")

    # Manually trigger startup event since TestClient doesn't

    from fakeai import app as fakeai_app_module

    fakeai_app_module.server_ready = True

    return TestClient(app)


@pytest.fixture
def client_with_auth(monkeypatch):
    """Test client with authentication enabled."""
    # For pydantic-settings, list env vars need JSON format
    import json

    monkeypatch.setenv("FAKEAI_REQUIRE_API_KEY", "true")
    monkeypatch.setenv("FAKEAI_API_KEYS", json.dumps(["test-key-1", "test-key-2"]))

    # Need to reload the config after setting env vars
    from fakeai.app import config
    from fakeai.config import AppConfig

    new_config = AppConfig()
    # Update the global config
    for key, value in new_config.__dict__.items():
        if not key.startswith("_"):
            setattr(config, key, value)

    # Manually trigger startup event since TestClient doesn't
    from fakeai import app as fakeai_app_module

    fakeai_app_module.server_ready = True

    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Valid authentication headers."""
    return {"Authorization": "Bearer test-key-1"}


@pytest.fixture
def invalid_auth_headers():
    """Invalid authentication headers."""
    return {"Authorization": "Bearer invalid-key"}
