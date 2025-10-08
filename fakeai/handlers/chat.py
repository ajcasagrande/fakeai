"""
Chat completion handler for the /v1/chat/completions endpoint.

This handler supports both streaming and non-streaming chat completions.
"""
#  SPDX-License-Identifier: Apache-2.0

from typing import AsyncGenerator, Optional

from fakeai.config import AppConfig
from fakeai.events import AsyncEventBus
from fakeai.fakeai_service import FakeAIService
from fakeai.handlers.base import EndpointHandler, RequestContext, StreamingHandler
from fakeai.handlers.registry import register_handler
from fakeai.metrics import MetricsTracker
from fakeai.models import (
    ChatCompletionChunk,
    ChatCompletionRequest,
    ChatCompletionResponse,
)


@register_handler
class ChatCompletionHandler(
    StreamingHandler[ChatCompletionRequest, ChatCompletionResponse | ChatCompletionChunk]
):
    """
    Handler for the /v1/chat/completions endpoint.

    This handler supports both streaming and non-streaming chat completions.
    It handles all 38 parameters of the OpenAI Chat API including function
    calling, multi-modal inputs, reasoning tokens, and predicted outputs.

    Features:
        - Streaming and non-streaming modes
        - Function/tool calling
        - Multi-modal content (text, images, audio, video)
        - Reasoning tokens (o1 models)
        - Predicted outputs (EAGLE speedup)
        - System fingerprinting
        - 38+ parameters
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
        event_bus: Optional[AsyncEventBus] = None,
    ):
        """Initialize the handler."""
        super().__init__(config, metrics_tracker, event_bus=event_bus)
        # Use full FakeAIService for chat completions
        self.service = FakeAIService(config)

    def endpoint_path(self) -> str:
        """Return the endpoint path."""
        return "/v1/chat/completions"

    async def pre_process(
        self,
        request: ChatCompletionRequest,
        context: RequestContext,
    ) -> None:
        """Pre-process chat completion request."""
        # Update streaming flag in context
        context.streaming = request.stream or False
        await super().pre_process(request, context)

    async def execute(
        self,
        request: ChatCompletionRequest,
        context: RequestContext,
    ) -> ChatCompletionResponse:
        """
        Execute non-streaming chat completion.

        Args:
            request: Chat completion request
            context: Request context

        Returns:
            ChatCompletionResponse with generated message
        """
        response = await self.service.create_chat_completion(request)
        return response

    async def execute_stream(
        self,
        request: ChatCompletionRequest,
        context: RequestContext,
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        """
        Execute streaming chat completion.

        Args:
            request: Chat completion request
            context: Request context

        Yields:
            ChatCompletionChunk objects
        """
        # All streaming metrics now tracked via events in base handler
        async for chunk in self.service.create_chat_completion_stream(request):
            yield chunk

    async def __call__(
        self,
        request: ChatCompletionRequest,
        fastapi_request,
        request_id: str,
    ):
        """
        Route to streaming or non-streaming handler.

        This override is needed because we need to return different types
        based on whether streaming is requested.
        """
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
