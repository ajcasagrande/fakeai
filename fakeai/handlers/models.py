"""
Model handler for the /v1/models endpoint.

This handler provides model listing and retrieval operations.
"""
#  SPDX-LICENSE-Identifier: Apache-2.0

from fakeai.config import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.handlers.base import EndpointHandler, RequestContext
from fakeai.handlers.registry import register_handler
from fakeai.metrics import MetricsTracker
from fakeai.models import Model, ModelListResponse


@register_handler
class ModelHandler(EndpointHandler[None, ModelListResponse]):
    """
    Handler for the /v1/models endpoint.

    This handler provides model listing and retrieval operations.
    Models are auto-created on first use.

    Features:
        - List all available models
        - Get model details
        - Model auto-creation
        - Pricing information
        - Capability detection
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
        return "/v1/models"

    async def execute(
        self,
        request: None,
        context: RequestContext,
    ) -> ModelListResponse:
        """
        List all available models.

        Args:
            request: Not used (GET request)
            context: Request context

        Returns:
            ModelListResponse with list of models
        """
        return await self.service.list_models()

    def extract_model(self, request: None) -> str | None:
        """Models endpoint doesn't have a model parameter."""
        return None


@register_handler(endpoint="/v1/models/{model_id}")
class ModelRetrievalHandler(EndpointHandler[str, Model]):
    """
    Handler for the /v1/models/{model_id} endpoint.

    This handler retrieves details for a specific model.
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
        return "/v1/models/{model_id}"

    async def execute(
        self,
        request: str,
        context: RequestContext,
    ) -> Model:
        """
        Get model details.

        Args:
            request: Model ID (path parameter)
            context: Request context

        Returns:
            Model object with details
        """
        return await self.service.get_model(request)

    def extract_model(self, request: str) -> str | None:
        """Extract model from path parameter."""
        return request
