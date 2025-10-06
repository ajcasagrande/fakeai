"""
Tests for handler registry.

This module tests handler registration, discovery, and instantiation.
"""
#  SPDX-License-Identifier: Apache-2.0

import pytest

from fakeai.config import AppConfig
from fakeai.handlers.base import EndpointHandler, RequestContext
from fakeai.handlers.registry import HandlerRegistry, register_handler
from fakeai.metrics import MetricsTracker


class TestHandler1(EndpointHandler[dict, dict]):
    """Test handler 1."""

    def endpoint_path(self) -> str:
        return "/v1/test1"

    async def execute(self, request: dict, context: RequestContext) -> dict:
        return {"handler": "test1"}


class TestHandler2(EndpointHandler[dict, dict]):
    """Test handler 2."""

    def endpoint_path(self) -> str:
        return "/v1/test2"

    async def execute(self, request: dict, context: RequestContext) -> dict:
        return {"handler": "test2"}


class TestHandlerRegistry:
    """Tests for HandlerRegistry."""

    @pytest.fixture
    def registry(self):
        """Create fresh registry for each test."""
        # Clear singleton instance
        HandlerRegistry._instance = None
        registry = HandlerRegistry.instance()
        yield registry
        # Clean up
        registry.clear()

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return AppConfig()

    @pytest.fixture
    def metrics_tracker(self):
        """Create test metrics tracker."""
        return MetricsTracker()

    def test_singleton_pattern(self):
        """Test that registry follows singleton pattern."""
        registry1 = HandlerRegistry.instance()
        registry2 = HandlerRegistry.instance()

        assert registry1 is registry2

    def test_register_handler_class(self, registry):
        """Test registering a handler class."""
        registry.register(TestHandler1)

        assert registry.is_registered("/v1/test1")
        assert registry.get_handler_class("/v1/test1") == TestHandler1

    def test_register_with_custom_endpoint(self, registry):
        """Test registering handler with custom endpoint."""
        registry.register(TestHandler1, endpoint="/custom/path")

        assert registry.is_registered("/custom/path")
        assert not registry.is_registered("/v1/test1")

    def test_register_multiple_handlers(self, registry):
        """Test registering multiple handlers."""
        registry.register(TestHandler1)
        registry.register(TestHandler2)

        assert registry.is_registered("/v1/test1")
        assert registry.is_registered("/v1/test2")

    def test_register_duplicate_warns(self, registry, caplog):
        """Test that registering duplicate handler warns."""
        registry.register(TestHandler1)
        registry.register(TestHandler2, endpoint="/v1/test1")  # Duplicate endpoint

        assert "already registered" in caplog.text.lower()
        # Latest registration wins
        assert registry.get_handler_class("/v1/test1") == TestHandler2

    def test_get_handler_creates_instance(self, registry, config, metrics_tracker):
        """Test that get_handler creates and caches instance."""
        registry.register(TestHandler1)

        handler1 = registry.get_handler("/v1/test1", config, metrics_tracker)
        handler2 = registry.get_handler("/v1/test1", config, metrics_tracker)

        assert handler1 is not None
        assert handler1 is handler2  # Cached

    def test_get_handler_unregistered_returns_none(self, registry, config, metrics_tracker):
        """Test that get_handler returns None for unregistered endpoint."""
        handler = registry.get_handler("/v1/unknown", config, metrics_tracker)

        assert handler is None

    def test_get_handler_requires_dependencies(self, registry):
        """Test that get_handler requires config and metrics."""
        registry.register(TestHandler1)

        with pytest.raises(ValueError, match="config and metrics_tracker required"):
            registry.get_handler("/v1/test1")

    def test_list_endpoints(self, registry):
        """Test listing all registered endpoints."""
        registry.register(TestHandler1)
        registry.register(TestHandler2)

        endpoints = registry.list_endpoints()

        assert "/v1/test1" in endpoints
        assert "/v1/test2" in endpoints
        assert len(endpoints) == 2

    def test_list_handlers(self, registry):
        """Test listing all registered handlers."""
        registry.register(TestHandler1)
        registry.register(TestHandler2)

        handlers = registry.list_handlers()

        assert handlers["/v1/test1"] == TestHandler1
        assert handlers["/v1/test2"] == TestHandler2
        assert len(handlers) == 2

    def test_clear_registry(self, registry, config, metrics_tracker):
        """Test clearing the registry."""
        registry.register(TestHandler1)
        registry.get_handler("/v1/test1", config, metrics_tracker)

        registry.clear()

        assert not registry.is_registered("/v1/test1")
        assert len(registry.list_endpoints()) == 0

    def test_clear_instances_only(self, registry, config, metrics_tracker):
        """Test clearing only cached instances."""
        registry.register(TestHandler1)
        handler1 = registry.get_handler("/v1/test1", config, metrics_tracker)

        registry.clear_instances()

        # Registration still there
        assert registry.is_registered("/v1/test1")

        # New instance created
        handler2 = registry.get_handler("/v1/test1", config, metrics_tracker)
        assert handler1 is not handler2


class TestRegisterHandlerDecorator:
    """Tests for @register_handler decorator."""

    @pytest.fixture(autouse=True)
    def cleanup_registry(self):
        """Clean up registry before and after each test."""
        HandlerRegistry._instance = None
        yield
        if HandlerRegistry._instance:
            HandlerRegistry._instance.clear()

    def test_decorator_without_arguments(self):
        """Test @register_handler decorator without arguments."""

        @register_handler
        class DecoratedHandler(EndpointHandler[dict, dict]):
            def endpoint_path(self) -> str:
                return "/v1/decorated"

            async def execute(self, request: dict, context: RequestContext) -> dict:
                return {}

        registry = HandlerRegistry.instance()
        assert registry.is_registered("/v1/decorated")
        assert registry.get_handler_class("/v1/decorated") == DecoratedHandler

    def test_decorator_with_endpoint_override(self):
        """Test @register_handler decorator with endpoint override."""

        @register_handler(endpoint="/custom")
        class DecoratedHandler(EndpointHandler[dict, dict]):
            def endpoint_path(self) -> str:
                return "/v1/decorated"

            async def execute(self, request: dict, context: RequestContext) -> dict:
                return {}

        registry = HandlerRegistry.instance()
        assert registry.is_registered("/custom")
        assert not registry.is_registered("/v1/decorated")

    def test_decorator_returns_class(self):
        """Test that decorator returns the class unchanged."""

        @register_handler
        class DecoratedHandler(EndpointHandler[dict, dict]):
            def endpoint_path(self) -> str:
                return "/v1/decorated"

            async def execute(self, request: dict, context: RequestContext) -> dict:
                return {}

            def custom_method(self):
                return "custom"

        # Class should be unchanged
        handler = DecoratedHandler(AppConfig(), MetricsTracker())
        assert handler.custom_method() == "custom"

    def test_multiple_decorated_handlers(self):
        """Test registering multiple handlers via decorator."""

        @register_handler
        class Handler1(EndpointHandler[dict, dict]):
            def endpoint_path(self) -> str:
                return "/v1/handler1"

            async def execute(self, request: dict, context: RequestContext) -> dict:
                return {}

        @register_handler
        class Handler2(EndpointHandler[dict, dict]):
            def endpoint_path(self) -> str:
                return "/v1/handler2"

            async def execute(self, request: dict, context: RequestContext) -> dict:
                return {}

        registry = HandlerRegistry.instance()
        assert registry.is_registered("/v1/handler1")
        assert registry.is_registered("/v1/handler2")
