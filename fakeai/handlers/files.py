"""
File handler for the /v1/files endpoint.

This handler delegates to the FileService for file management operations.
"""
#  SPDX-License-Identifier: Apache-2.0

from typing import Optional

from fakeai.config import AppConfig
from fakeai.events import AsyncEventBus
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
        event_bus: Optional[AsyncEventBus] = None,
    ):
        """Initialize the handler."""
        super().__init__(config, metrics_tracker, event_bus=event_bus)
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

        This handler supports multiple operations based on the request type
        and HTTP method stored in context metadata.

        Args:
            request: File operation request
            context: Request context

        Returns:
            FileListResponse for list operations, FileObject for single file operations

        Raises:
            ValueError: If HTTP method is not supported
        """
        # Get HTTP method from context metadata
        http_method = context.metadata.get("http_method", "GET")
        file_id = context.metadata.get("file_id")

        if http_method == "GET":
            if file_id:
                # Get specific file
                return await self.file_service.get_file(file_id)
            else:
                # List files
                purpose = request.get("purpose") if request else None
                return await self.file_service.list_files(purpose=purpose)
        elif http_method == "POST":
            # Upload file
            file = request.get("file")
            purpose = request.get("purpose", "assistants")
            return await self.file_service.upload_file(file, purpose)
        elif http_method == "DELETE":
            # Delete file
            if not file_id:
                raise ValueError("file_id required for DELETE operation")
            return await self.file_service.delete_file(file_id)
        else:
            raise ValueError(f"Unsupported HTTP method: {http_method}")
