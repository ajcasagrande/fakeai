"""
Embedding handler for the /v1/embeddings endpoint.

This handler delegates to the EmbeddingService for generating text embeddings.
"""
#  SPDX-License-Identifier: Apache-2.0

from fakeai.config import AppConfig
from fakeai.handlers.base import EndpointHandler, RequestContext
from fakeai.handlers.registry import register_handler
from fakeai.metrics import MetricsTracker
from fakeai.models import EmbeddingRequest, EmbeddingResponse
from fakeai.services.embedding_service import EmbeddingService


@register_handler
class EmbeddingHandler(EndpointHandler[EmbeddingRequest, EmbeddingResponse]):
    """
    Handler for the /v1/embeddings endpoint.

    This handler processes embedding requests and returns vector embeddings
    for the input text(s). Supports both semantic embeddings (when enabled)
    and hash-based embeddings.

    Features:
        - Single or batch text embedding
        - Custom dimensions (1-3072)
        - Semantic embeddings (optional)
        - Token usage tracking
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
    ):
        """Initialize the handler."""
        super().__init__(config, metrics_tracker)
        self.embedding_service = EmbeddingService(
            config=config,
            metrics_tracker=metrics_tracker,
        )

    def endpoint_path(self) -> str:
        """Return the endpoint path."""
        return "/v1/embeddings"

    async def execute(
        self,
        request: EmbeddingRequest,
        context: RequestContext,
    ) -> EmbeddingResponse:
        """
        Generate embeddings for input text(s).

        Args:
            request: Embedding request with input and model
            context: Request context

        Returns:
            EmbeddingResponse with generated embeddings and usage stats
        """
        return await self.embedding_service.create_embedding(request)

    async def post_process(
        self,
        response: EmbeddingResponse,
        context: RequestContext,
    ) -> EmbeddingResponse:
        """Post-process the embedding response."""
        # Track token usage
        if response.usage:
            self.metrics_tracker.track_tokens(
                context.endpoint,
                response.usage.total_tokens,
            )

        # Call parent post-process
        return await super().post_process(response, context)
