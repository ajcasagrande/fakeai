"""
Batch handler for the /v1/batches endpoint.

This handler delegates to the BatchService for batch processing operations.
"""
#  SPDX-License-Identifier: Apache-2.0

from fakeai.config import AppConfig
from fakeai.file_manager import FileManager
from fakeai.handlers.base import EndpointHandler, RequestContext
from fakeai.handlers.registry import register_handler
from fakeai.metrics import MetricsTracker
from fakeai.models import Batch, BatchListResponse, CreateBatchRequest
from fakeai.services.batch_service import BatchService


@register_handler
class BatchHandler(EndpointHandler[CreateBatchRequest, Batch]):
    """
    Handler for the /v1/batches endpoint.

    This handler processes batch job requests including create, retrieve,
    cancel, and list operations.

    Features:
        - Batch job creation
        - Job status tracking
        - Cancellation support
        - Progress monitoring
        - Output file generation
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
    ):
        """Initialize the handler."""
        super().__init__(config, metrics_tracker)
        self.file_manager = FileManager()
        self.batch_service = BatchService(
            config=config,
            metrics_tracker=metrics_tracker,
            file_manager=self.file_manager,
        )

    def endpoint_path(self) -> str:
        """Return the endpoint path."""
        return "/v1/batches"

    async def execute(
        self,
        request: CreateBatchRequest,
        context: RequestContext,
    ) -> Batch:
        """
        Create a batch processing job.

        Args:
            request: Batch creation request with input file and endpoint
            context: Request context

        Returns:
            Batch object with job details
        """
        return await self.batch_service.create_batch(request)
