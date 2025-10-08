"""
Image generation handler for the /v1/images/generations endpoint.

This handler delegates to the ImageGenerationService for generating images.
"""
#  SPDX-License-Identifier: Apache-2.0

from typing import Optional

from fakeai.config import AppConfig
from fakeai.events import AsyncEventBus
from fakeai.handlers.base import EndpointHandler, RequestContext
from fakeai.handlers.registry import register_handler
from fakeai.metrics import MetricsTracker
from fakeai.models import ImageGenerationRequest, ImageGenerationResponse
from fakeai.services.image_generation_service import ImageGenerationService


@register_handler
class ImageGenerationHandler(
    EndpointHandler[ImageGenerationRequest, ImageGenerationResponse]
):
    """
    Handler for the /v1/images/generations endpoint.

    This handler processes image generation requests and returns generated images
    either as URLs or base64-encoded data.

    Features:
        - Multiple models (DALL-E 2, DALL-E 3)
        - Various sizes and quality settings
        - URL or base64 response format
        - Batch generation (up to 10 images)
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
        event_bus: Optional[AsyncEventBus] = None,
    ):
        """Initialize the handler."""
        super().__init__(config, metrics_tracker, event_bus=event_bus)
        self.image_service = ImageGenerationService(
            config=config,
            metrics_tracker=metrics_tracker,
        )

    def endpoint_path(self) -> str:
        """Return the endpoint path."""
        return "/v1/images/generations"

    async def execute(
        self,
        request: ImageGenerationRequest,
        context: RequestContext,
    ) -> ImageGenerationResponse:
        """
        Generate images based on prompt.

        Args:
            request: Image generation request with prompt and settings
            context: Request context

        Returns:
            ImageGenerationResponse with generated images
        """
        return await self.image_service.generate_images(request)
