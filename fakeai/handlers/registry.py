"""
Handler registry for endpoint management.

This module provides the handler registry system that allows handlers to be
registered, discovered, and instantiated dynamically. It supports both
decorator-based registration and manual registration.

Key features:
- Automatic handler discovery
- Type-safe handler registration
- Singleton pattern for global registry
- Handler instantiation with dependency injection
- Route mapping management

Usage:
    # Register a handler
    @register_handler
    class MyHandler(EndpointHandler[MyRequest, MyResponse]):
        def endpoint_path(self) -> str:
            return "/v1/my/endpoint"

        async def execute(self, request, context):
            return MyResponse(...)

    # Get registry instance
    registry = HandlerRegistry.instance()

    # Get a handler
    handler = registry.get_handler("/v1/my/endpoint")
"""
#  SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, Dict, Type

from fakeai.config import AppConfig
from fakeai.handlers.base import EndpointHandler
from fakeai.metrics import MetricsTracker

logger = logging.getLogger(__name__)


class HandlerRegistry:
    """
    Singleton registry for endpoint handlers.

    This registry maintains a mapping from endpoint paths to handler classes
    and provides methods for handler registration, discovery, and instantiation.

    The registry uses a singleton pattern to ensure there is only one global
    registry across the application.

    Attributes:
        _handlers: Dictionary mapping endpoint paths to handler classes
        _instances: Dictionary caching instantiated handlers
    """

    _instance = None

    def __init__(self):
        """Initialize the registry."""
        self._handlers: Dict[str, Type[EndpointHandler]] = {}
        self._instances: Dict[str, EndpointHandler] = {}

    @classmethod
    def instance(cls) -> "HandlerRegistry":
        """
        Get the singleton registry instance.

        Returns:
            The global HandlerRegistry instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(
        self,
        handler_class: Type[EndpointHandler],
        endpoint: str | None = None,
    ) -> Type[EndpointHandler]:
        """
        Register a handler class.

        Args:
            handler_class: Handler class to register
            endpoint: Optional endpoint path override (uses handler's endpoint_path() if not provided)

        Returns:
            The handler class (for decorator chaining)

        Raises:
            ValueError: If a handler is already registered for the endpoint
        """
        # Get endpoint from handler class if not provided
        if endpoint is None:
            # Instantiate temporarily to get endpoint path
            temp_instance = handler_class.__new__(handler_class)
            endpoint = temp_instance.endpoint_path()

        # Check for conflicts
        if endpoint in self._handlers:
            existing = self._handlers[endpoint]
            logger.warning(
                f"Handler for {endpoint} already registered "
                f"({existing.__name__}), replacing with {handler_class.__name__}"
            )

        # Register handler
        self._handlers[endpoint] = handler_class
        logger.info(f"Registered handler {handler_class.__name__} for {endpoint}")

        return handler_class

    def get_handler(
        self,
        endpoint: str,
        config: AppConfig | None = None,
        metrics_tracker: MetricsTracker | None = None,
    ) -> EndpointHandler | None:
        """
        Get a handler instance for an endpoint.

        Handlers are cached after first instantiation.

        Args:
            endpoint: Endpoint path
            config: Application configuration (required for first instantiation)
            metrics_tracker: Metrics tracker (required for first instantiation)

        Returns:
            Handler instance or None if not registered

        Raises:
            ValueError: If handler not registered or dependencies missing
        """
        # Check if handler is registered
        if endpoint not in self._handlers:
            return None

        # Return cached instance if available
        if endpoint in self._instances:
            return self._instances[endpoint]

        # Instantiate handler
        if config is None or metrics_tracker is None:
            raise ValueError(
                f"Cannot instantiate handler for {endpoint}: "
                "config and metrics_tracker required"
            )

        handler_class = self._handlers[endpoint]
        try:
            handler = handler_class(config, metrics_tracker)
            self._instances[endpoint] = handler
            logger.info(f"Instantiated handler {handler_class.__name__} for {endpoint}")
            return handler
        except Exception as e:
            logger.error(f"Failed to instantiate handler for {endpoint}: {e}")
            raise

    def get_handler_class(
        self,
        endpoint: str,
    ) -> Type[EndpointHandler] | None:
        """
        Get the handler class for an endpoint.

        Args:
            endpoint: Endpoint path

        Returns:
            Handler class or None if not registered
        """
        return self._handlers.get(endpoint)

    def is_registered(self, endpoint: str) -> bool:
        """
        Check if a handler is registered for an endpoint.

        Args:
            endpoint: Endpoint path

        Returns:
            True if handler is registered, False otherwise
        """
        return endpoint in self._handlers

    def list_endpoints(self) -> list[str]:
        """
        Get list of all registered endpoints.

        Returns:
            List of endpoint paths
        """
        return list(self._handlers.keys())

    def list_handlers(self) -> Dict[str, Type[EndpointHandler]]:
        """
        Get all registered handlers.

        Returns:
            Dictionary mapping endpoints to handler classes
        """
        return self._handlers.copy()

    def clear(self) -> None:
        """
        Clear all registered handlers and instances.

        This is primarily useful for testing.
        """
        self._handlers.clear()
        self._instances.clear()
        logger.info("Cleared handler registry")

    def clear_instances(self) -> None:
        """
        Clear cached handler instances.

        Handlers will be re-instantiated on next access.
        """
        self._instances.clear()
        logger.info("Cleared handler instance cache")


def register_handler(
    handler_class: Type[EndpointHandler] | None = None,
    *,
    endpoint: str | None = None,
) -> Any:
    """
    Decorator to register a handler with the global registry.

    This decorator can be used with or without arguments:
        @register_handler
        class MyHandler(EndpointHandler):
            ...

        @register_handler(endpoint="/custom/path")
        class MyHandler(EndpointHandler):
            ...

    Args:
        handler_class: Handler class (when used without arguments)
        endpoint: Optional endpoint path override

    Returns:
        Decorated handler class or decorator function

    Example:
        >>> @register_handler
        ... class EmbeddingHandler(EndpointHandler[EmbeddingRequest, EmbeddingResponse]):
        ...     def endpoint_path(self) -> str:
        ...         return "/v1/embeddings"
        ...
        ...     async def execute(self, request, context):
        ...         return await self.embedding_service.create_embedding(request)
    """
    # Get global registry
    registry = HandlerRegistry.instance()

    # Called with arguments: @register_handler(endpoint="/path")
    if handler_class is None:

        def decorator(cls: Type[EndpointHandler]) -> Type[EndpointHandler]:
            registry.register(cls, endpoint=endpoint)
            return cls

        return decorator

    # Called without arguments: @register_handler
    registry.register(handler_class, endpoint=endpoint)
    return handler_class
