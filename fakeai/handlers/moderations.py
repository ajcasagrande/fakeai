"""
Moderation handler for the /v1/moderations endpoint.

This handler delegates to the ModerationService for content safety checks.
"""
#  SPDX-License-Identifier: Apache-2.0

from typing import Optional

from fakeai.config import AppConfig
from fakeai.events import AsyncEventBus
from fakeai.handlers.base import EndpointHandler, RequestContext
from fakeai.handlers.registry import register_handler
from fakeai.metrics import MetricsTracker
from fakeai.models import ModerationRequest, ModerationResponse
from fakeai.services.moderation_service import ModerationService


@register_handler
class ModerationHandler(
        EndpointHandler[ModerationRequest, ModerationResponse]):
    """
    Handler for the /v1/moderations endpoint.

    This handler processes content moderation requests and returns safety
    classifications for text and image inputs.

    Features:
        - Text and multi-modal content scanning
        - 11 safety categories
        - Confidence scores
        - Binary flagging
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
        event_bus: Optional[AsyncEventBus] = None,
    ):
        """Initialize the handler."""
        super().__init__(config, metrics_tracker, event_bus=event_bus)
        from fakeai.models_registry import ModelRegistry

        self.moderation_service = ModerationService(
            config=config,
            metrics_tracker=metrics_tracker,
            model_registry=ModelRegistry(),
        )

    def endpoint_path(self) -> str:
        """Return the endpoint path."""
        return "/v1/moderations"

    async def execute(
        self,
        request: ModerationRequest,
        context: RequestContext,
    ) -> ModerationResponse:
        """
        Classify content for safety violations.

        Args:
            request: Moderation request with input content
            context: Request context

        Returns:
            ModerationResponse with safety classifications
        """
        return await self.moderation_service.create_moderation(request)
