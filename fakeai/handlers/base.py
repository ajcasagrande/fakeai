"""
Base handler classes for endpoint abstraction.

This module provides the foundational handler classes that all endpoint handlers
inherit from. It defines the request lifecycle, context management, and common
patterns for both standard and streaming endpoints.

Key concepts:
- EndpointHandler: Base class for all handlers (non-streaming)
- StreamingHandler: Base class for streaming endpoints
- RequestContext: Context object passed through the handler lifecycle
- Handler lifecycle: pre_process -> execute -> post_process (with on_error)

Design principles:
- Single Responsibility: Each handler handles one endpoint
- Template Method Pattern: Define lifecycle hooks
- Type Safety: Generic types for request/response
- Automatic Metrics: Track all requests/responses/errors
- Authorization Context: Extract user from auth headers
"""
#  SPDX-License-Identifier: Apache-2.0

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Generic, TypeVar

from fastapi import Request

from fakeai.config import AppConfig
from fakeai.metrics import MetricsTracker

logger = logging.getLogger(__name__)

# Type variables for generic handler classes
TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


@dataclass
class RequestContext:
    """
    Context object containing request metadata and state.

    This object is passed through the handler lifecycle and can be
    enriched with additional data during processing.

    Attributes:
        request_id: Unique identifier for this request
        endpoint: API endpoint path (e.g., "/v1/chat/completions")
        user_id: User identifier extracted from authorization
        api_key: API key used for authentication (if any)
        client_ip: Client IP address
        start_time: Request start timestamp
        model: Model name from request (if applicable)
        streaming: Whether this is a streaming request
        metadata: Additional context data
    """

    request_id: str
    endpoint: str
    user_id: str | None = None
    api_key: str | None = None
    client_ip: str | None = None
    start_time: float = field(default_factory=time.time)
    model: str | None = None
    streaming: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def elapsed_time(self) -> float:
        """Calculate elapsed time since request start."""
        return time.time() - self.start_time


class EndpointHandler(ABC, Generic[TRequest, TResponse]):
    """
    Base class for all endpoint handlers.

    This class defines the handler lifecycle and provides common functionality
    for request processing, metrics tracking, and error handling.

    Handler lifecycle:
        1. __call__() - Entry point, creates context
        2. pre_process() - Validate and prepare request
        3. execute() - Main business logic (abstract)
        4. post_process() - Process and track response
        5. on_error() - Handle any errors

    Subclasses must implement:
        - execute(): Core business logic
        - endpoint_path(): API endpoint path

    Subclasses may override:
        - pre_process(): Custom validation/preparation
        - post_process(): Custom response processing
        - on_error(): Custom error handling
        - extract_model(): Extract model name from request

    Example:
        >>> class MyHandler(EndpointHandler[MyRequest, MyResponse]):
        ...     def endpoint_path(self) -> str:
        ...         return "/v1/my/endpoint"
        ...
        ...     async def execute(self, request: MyRequest, context: RequestContext) -> MyResponse:
        ...         return MyResponse(data="processed")
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
    ):
        """
        Initialize the handler.

        Args:
            config: Application configuration
            metrics_tracker: Metrics tracker singleton
        """
        self.config = config
        self.metrics_tracker = metrics_tracker

    @abstractmethod
    def endpoint_path(self) -> str:
        """
        Return the endpoint path for this handler.

        Returns:
            Endpoint path (e.g., "/v1/chat/completions")
        """
        pass

    @abstractmethod
    async def execute(
        self,
        request: TRequest,
        context: RequestContext,
    ) -> TResponse:
        """
        Execute the main handler logic.

        This is the core business logic of the handler. It receives the
        validated request and context, and returns the response.

        Args:
            request: Validated request object
            context: Request context with metadata

        Returns:
            Response object

        Raises:
            Exception: Any errors during processing
        """
        pass

    async def pre_process(
        self,
        request: TRequest,
        context: RequestContext,
    ) -> None:
        """
        Pre-process hook called before execute().

        Override this method to add custom validation, preparation,
        or context enrichment logic.

        Args:
            request: Request object
            context: Request context

        Raises:
            Exception: If validation or preparation fails
        """
        pass

    async def post_process(
        self,
        response: TResponse,
        context: RequestContext,
    ) -> TResponse:
        """
        Post-process hook called after execute().

        Override this method to add custom response processing,
        logging, or metrics tracking.

        Default implementation tracks basic metrics.

        Args:
            response: Response object
            context: Request context

        Returns:
            Processed response (may be modified)
        """
        # Track response metrics (latency is passed to track_response)
        elapsed = context.elapsed_time()
        self.metrics_tracker.track_response(context.endpoint, elapsed)

        logger.info(
            f"{context.endpoint} completed: "
            f"request_id={context.request_id}, "
            f"user={context.user_id}, "
            f"model={context.model}, "
            f"elapsed={elapsed:.3f}s"
        )

        return response

    async def on_error(
        self,
        error: Exception,
        context: RequestContext,
    ) -> None:
        """
        Error handling hook called when an exception occurs.

        Override this method to add custom error handling, logging,
        or metrics tracking.

        Default implementation tracks error metrics and logs the error.

        Args:
            error: Exception that was raised
            context: Request context
        """
        # Track error metrics
        self.metrics_tracker.track_error(context.endpoint)

        logger.error(
            f"{context.endpoint} failed: "
            f"request_id={context.request_id}, "
            f"user={context.user_id}, "
            f"error={type(error).__name__}: {str(error)}"
        )

    def extract_model(self, request: TRequest) -> str | None:
        """
        Extract model name from request.

        Override this method if the request has a model field.

        Args:
            request: Request object

        Returns:
            Model name or None if not applicable
        """
        # Try to get model attribute if it exists
        if hasattr(request, "model"):
            return getattr(request, "model")
        return None

    def create_context(
        self,
        request: TRequest,
        fastapi_request: Request,
        request_id: str,
    ) -> RequestContext:
        """
        Create request context from FastAPI request.

        Args:
            request: Parsed request object
            fastapi_request: FastAPI request object
            request_id: Unique request identifier

        Returns:
            RequestContext object
        """
        # Extract user from authorization header
        user_id = self._extract_user_from_auth(fastapi_request)

        # Get client IP
        client_ip = fastapi_request.client.host if fastapi_request.client else None

        # Extract model name
        model = self.extract_model(request)

        return RequestContext(
            request_id=request_id,
            endpoint=self.endpoint_path(),
            user_id=user_id,
            client_ip=client_ip,
            model=model,
            streaming=False,
        )

    def _extract_user_from_auth(self, request: Request) -> str | None:
        """
        Extract user identifier from Authorization header.

        Supports formats:
            - Bearer sk-user-abc123xyz -> user-abc123xyz
            - Bearer sk-proj-abc123 -> proj-abc123
            - Bearer token -> token[:16]

        Args:
            request: FastAPI request

        Returns:
            User identifier or None
        """
        auth_header = request.headers.get("authorization")
        if not auth_header:
            return None

        # Remove "Bearer " prefix
        token = auth_header.replace("Bearer ", "").replace("bearer ", "")

        # Extract user from OpenAI-style keys
        if token.startswith("sk-"):
            # sk-user-abc123xyz -> user-abc123xyz
            # sk-proj-abc123 -> proj-abc123
            parts = token.split("-", 2)
            if len(parts) >= 3:
                return f"{parts[1]}-{parts[2]}"
            elif len(parts) == 2:
                return parts[1]

        # Use first 16 chars of token as user ID
        return token[:16] if token else None

    async def __call__(
        self,
        request: TRequest,
        fastapi_request: Request,
        request_id: str,
    ) -> TResponse:
        """
        Handle the request through the complete lifecycle.

        This is the main entry point called by FastAPI routes.

        Args:
            request: Parsed request object
            fastapi_request: FastAPI request object
            request_id: Unique request identifier

        Returns:
            Response object

        Raises:
            Exception: Any errors during processing
        """
        # Track request
        self.metrics_tracker.track_request(self.endpoint_path())

        # Create context
        context = self.create_context(request, fastapi_request, request_id)

        try:
            # Pre-process
            await self.pre_process(request, context)

            # Execute main logic
            response = await self.execute(request, context)

            # Post-process
            response = await self.post_process(response, context)

            return response

        except Exception as error:
            # Handle error
            await self.on_error(error, context)
            raise


class StreamingHandler(EndpointHandler[TRequest, TResponse], Generic[TRequest, TResponse]):
    """
    Base class for streaming endpoint handlers.

    Streaming handlers generate responses incrementally using async generators.
    They follow the same lifecycle as standard handlers but yield chunks instead
    of returning a complete response.

    Handler lifecycle:
        1. __call__() - Entry point, creates context
        2. pre_process() - Validate and prepare request
        3. execute_stream() - Main streaming logic (abstract)
        4. post_process() - Track completion after streaming
        5. on_error() - Handle any errors

    Subclasses must implement:
        - execute_stream(): Core streaming logic (async generator)
        - endpoint_path(): API endpoint path

    Example:
        >>> class MyStreamingHandler(StreamingHandler[MyRequest, MyChunk]):
        ...     def endpoint_path(self) -> str:
        ...         return "/v1/stream/endpoint"
        ...
        ...     async def execute_stream(
        ...         self, request: MyRequest, context: RequestContext
        ...     ) -> AsyncGenerator[MyChunk, None]:
        ...         for i in range(10):
        ...             yield MyChunk(index=i)
    """

    @abstractmethod
    async def execute_stream(
        self,
        request: TRequest,
        context: RequestContext,
    ) -> AsyncGenerator[TResponse, None]:
        """
        Execute the streaming handler logic.

        This is the core business logic for streaming handlers. It receives the
        validated request and context, and yields response chunks.

        Args:
            request: Validated request object
            context: Request context with metadata

        Yields:
            Response chunks

        Raises:
            Exception: Any errors during processing
        """
        yield  # Make this a generator
        raise NotImplementedError("Subclasses must implement execute_stream()")

    async def execute(
        self,
        request: TRequest,
        context: RequestContext,
    ) -> TResponse:
        """
        Not used for streaming handlers.

        Streaming handlers should implement execute_stream() instead.
        This method is here to satisfy the abstract base class.

        Raises:
            NotImplementedError: Always
        """
        raise NotImplementedError("Streaming handlers should implement execute_stream()")

    def create_context(
        self,
        request: TRequest,
        fastapi_request: Request,
        request_id: str,
    ) -> RequestContext:
        """Create context for streaming request."""
        context = super().create_context(request, fastapi_request, request_id)
        context.streaming = True
        return context

    async def __call__(
        self,
        request: TRequest,
        fastapi_request: Request,
        request_id: str,
    ) -> AsyncGenerator[TResponse, None]:
        """
        Handle the streaming request through the complete lifecycle.

        This is the main entry point called by FastAPI routes.

        Args:
            request: Parsed request object
            fastapi_request: FastAPI request object
            request_id: Unique request identifier

        Yields:
            Response chunks

        Raises:
            Exception: Any errors during processing
        """
        # Track request
        self.metrics_tracker.track_request(self.endpoint_path())

        # Create context
        context = self.create_context(request, fastapi_request, request_id)

        try:
            # Pre-process
            await self.pre_process(request, context)

            # Execute streaming logic
            chunk_count = 0
            async for chunk in self.execute_stream(request, context):
                chunk_count += 1
                yield chunk

            # Store chunk count in metadata for post-process
            context.metadata["chunk_count"] = chunk_count

            # Post-process (after streaming completes)
            # We don't have a final response object, so we pass None
            # Handlers can override post_process to handle this case
            await self.post_process(None, context)  # type: ignore

        except Exception as error:
            # Handle error
            await self.on_error(error, context)
            raise
