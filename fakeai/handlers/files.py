"""
File handler for the /v1/files endpoint.

This handler delegates to the FileService for file management operations.
"""
#  SPDX-License-Identifier: Apache-2.0

from fakeai.config import AppConfig
from fakeai.file_manager import FileManager
from fakeai.handlers.base import EndpointHandler, RequestContext
from fakeai.handlers.registry import register_handler
from fakeai.metrics import MetricsTracker
from fakeai.models import FileListResponse, FileObject
from fakeai.services.file_service import FileService


@register_handler
class FileHandler(EndpointHandler[dict, FileListResponse | FileObject]):
    """
    Handler for the /v1/files endpoint.

    This handler processes file management requests including list, upload,
    get, and delete operations.

    Features:
        - File upload with validation
        - List with pagination and filtering
        - File metadata retrieval
        - File deletion with quota cleanup
        - Purpose validation
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
    ):
        """Initialize the handler."""
        super().__init__(config, metrics_tracker)
        self.file_manager = FileManager()
        self.file_service = FileService(
            config=config,
            metrics_tracker=metrics_tracker,
            file_manager=self.file_manager,
        )

    def endpoint_path(self) -> str:
        """Return the endpoint path."""
        return "/v1/files"

    async def execute(
        self,
        request: dict,
        context: RequestContext,
    ) -> FileListResponse | FileObject:
        """
        Execute file operations.

        This handler supports multiple operations based on the request type.
        For now, we'll implement list_files as the primary operation.

        Args:
            request: File operation request
            context: Request context

        Returns:
            FileListResponse for list operations, FileObject for single file operations
        """
        # Default to listing files
        # In a real implementation, this would be determined by the HTTP method
        # and request parameters
        return await self.file_service.list_files()
