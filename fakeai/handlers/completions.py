"""
Completion handler for the /v1/completions endpoint.

This handler supports both streaming and non-streaming text completions (legacy).
"""
#  SPDX-License-Identifier: Apache-2.0

from typing import AsyncGenerator

from fakeai.config import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.handlers.base import RequestContext, StreamingHandler
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
    ):
        """Initialize the handler."""
        super().__init__(config, metrics_tracker)
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

        # Track token usage
        if response.usage:
            self.metrics_tracker.track_tokens(
                context.endpoint,
                response.usage.total_tokens,
            )

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
        # Track start of stream
        stream_id = context.request_id
        self.metrics_tracker.start_stream(stream_id, context.endpoint)

        total_tokens = 0
        first_token = True

        try:
            async for chunk in self.service.create_completion_stream(request):
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
        request: CompletionRequest,
        fastapi_request,
        request_id: str,
    ):
        """Route to streaming or non-streaming handler."""
        if request.stream:
            return await StreamingHandler.__call__(
                self, request, fastapi_request, request_id
            )
        else:
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
