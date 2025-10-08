"""
Completion handler for the /v1/completions endpoint.

This handler supports both streaming and non-streaming text completions (legacy).
"""
#  SPDX-License-Identifier: Apache-2.0

from typing import AsyncGenerator, Optional

from fakeai.config import AppConfig
from fakeai.events import AsyncEventBus
from fakeai.fakeai_service import FakeAIService
from fakeai.handlers.base import EndpointHandler, RequestContext, StreamingHandler
from fakeai.handlers.registry import register_handler
from fakeai.metrics import MetricsTracker
from fakeai.models import CompletionChunk, CompletionRequest, CompletionResponse


@register_handler
class CompletionHandler(
    StreamingHandler[CompletionRequest, CompletionResponse | CompletionChunk]
):
    """
    Handler for the /v1/completions endpoint.

    This handler supports both streaming and non-streaming text completions.
    This is the legacy completion API (vs. chat completions).

    Features:
        - Streaming and non-streaming modes
        - Multiple completions (n parameter)
        - Best-of sampling
        - Logprobs support
        - Echo support
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
        event_bus: Optional[AsyncEventBus] = None,
    ):
        """Initialize the handler."""
        super().__init__(config, metrics_tracker, event_bus=event_bus)
        self.service = FakeAIService(config)

    def endpoint_path(self) -> str:
        """Return the endpoint path."""
        return "/v1/completions"

    async def pre_process(
        self,
        request: CompletionRequest,
        context: RequestContext,
    ) -> None:
        """Pre-process completion request."""
        context.streaming = request.stream or False
        await super().pre_process(request, context)

    async def execute(
        self,
        request: CompletionRequest,
        context: RequestContext,
    ) -> CompletionResponse:
        """
        Execute non-streaming completion.

        Args:
            request: Completion request
            context: Request context

        Returns:
            CompletionResponse with generated text
        """
        response = await self.service.create_completion(request)
        return response

    async def execute_stream(
        self,
        request: CompletionRequest,
        context: RequestContext,
    ) -> AsyncGenerator[CompletionChunk, None]:
        """
        Execute streaming completion.

        Args:
            request: Completion request
            context: Request context

        Yields:
            CompletionChunk objects
        """
        # All streaming metrics now tracked via events in base handler
        async for chunk in self.service.create_completion_stream(request):
            yield chunk

    async def __call__(
        self,
        request: CompletionRequest,
        fastapi_request,
        request_id: str,
    ):
        """Route to streaming or non-streaming handler."""
        if request.stream:
            # Use streaming handler (calls StreamingHandler.__call__ with
            # events)
            return await StreamingHandler.__call__(
                self, request, fastapi_request, request_id
            )
        else:
            # Use non-streaming handler (calls EndpointHandler.__call__ with
            # events)
            return await EndpointHandler.__call__(
                self, request, fastapi_request, request_id
            )
