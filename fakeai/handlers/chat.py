"""
Chat completion handler for the /v1/chat/completions endpoint.

This handler supports both streaming and non-streaming chat completions.
"""
#  SPDX-License-Identifier: Apache-2.0

from typing import AsyncGenerator

from fakeai.config import AppConfig
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
    ):
        """Initialize the handler."""
        super().__init__(config, metrics_tracker)
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

        # Track token usage
        if response.usage:
            self.metrics_tracker.track_tokens(
                context.endpoint,
                response.usage.total_tokens,
            )

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
        # Track start of stream
        stream_id = context.request_id
        self.metrics_tracker.start_stream(stream_id, context.endpoint)

        total_tokens = 0
        first_token = True

        try:
            async for chunk in self.service.create_chat_completion_stream(request):
                # Track first token
                if first_token:
                    self.metrics_tracker.track_stream_first_token(stream_id)
                    first_token = False

                # Track token
                self.metrics_tracker.track_stream_token(stream_id)
                total_tokens += 1

                yield chunk

            # Track completion
            self.metrics_tracker.complete_stream(stream_id, context.endpoint)
            self.metrics_tracker.track_tokens(context.endpoint, total_tokens)

        except Exception as e:
            # Track failure
            self.metrics_tracker.fail_stream(stream_id, context.endpoint, str(e))
            raise

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
            # Use streaming handler
            return await StreamingHandler.__call__(
                self, request, fastapi_request, request_id
            )
        else:
            # Use non-streaming handler (execute only, no stream)
            self.metrics_tracker.track_request(self.endpoint_path())
            context = self.create_context(request, fastapi_request, request_id)
            context.streaming = False

            try:
                await self.pre_process(request, context)
                response = await self.execute(request, context)
                response = await self.post_process(response, context)
                return response
            except Exception as error:
                await self.on_error(error, context)
                raise
