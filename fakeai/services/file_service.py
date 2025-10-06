"""
File service for FakeAI.

This module provides file management services including upload, list, get,
delete, and retrieval operations. It integrates with FileManager for storage
and MetricsTracker for monitoring.
"""

#  SPDX-License-Identifier: Apache-2.0

import logging
import time
from typing import Any

from fakeai.config import AppConfig
from fakeai.file_manager import (
    FileManager,
    FileNotFoundError,
    FileQuotaError,
    FileValidationError,
)
from fakeai.metrics import MetricsTracker
from fakeai.models import FileListResponse, FileObject

logger = logging.getLogger(__name__)


class FileService:
    """
    File service for managing file operations.

    Provides high-level file operations including:
    - Upload with validation and quota enforcement
    - List with pagination and filtering
    - Get file metadata
    - Delete with quota cleanup
    - Get file content

    Features:
    - Purpose validation (assistants, fine-tune, batch, vision)
    - Quota enforcement per user
    - File format validation
    - Metrics tracking for all operations
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
        file_manager: FileManager,
    ):
        """
        Initialize file service.

        Args:
            config: Application configuration
            metrics_tracker: Metrics tracker for monitoring
            file_manager: File manager for storage operations
        """
        self.config = config
        self.metrics_tracker = metrics_tracker
        self.file_manager = file_manager
        logger.info("FileService initialized")

    async def list_files(
        self,
        purpose: str | None = None,
        limit: int = 20,
        after: str | None = None,
        order: str = "desc",
    ) -> FileListResponse:
        """
        List files with pagination.

        Args:
            purpose: Filter by purpose (optional)
            limit: Maximum number of files to return (default: 20)
            after: Cursor for pagination (file ID)
            order: Sort order ('asc' or 'desc', default: 'desc')

        Returns:
            FileListResponse with list of files

        Raises:
            ValueError: If parameters are invalid
        """
        start_time = time.time()
        endpoint = "/v1/files"

        try:
            # Track request
            self.metrics_tracker.track_request(endpoint)

            # Validate parameters
            if limit < 1 or limit > 10000:
                raise ValueError("Limit must be between 1 and 10000")

            if order not in ["asc", "desc"]:
                raise ValueError("Order must be 'asc' or 'desc'")

            # Validate purpose if provided
            if purpose and purpose not in self.file_manager.VALID_PURPOSES:
                raise ValueError(
                    f"Invalid purpose '{purpose}'. Valid purposes: {', '.join(sorted(self.file_manager.VALID_PURPOSES))}"
                )

            # Get files from file manager
            files = await self.file_manager.list_files(
                purpose=purpose,
                limit=limit,
                after=after,
                order=order,
            )

            # Track response
            latency = time.time() - start_time
            self.metrics_tracker.track_response(endpoint, latency)

            return FileListResponse(data=files)

        except Exception as e:
            # Track error
            self.metrics_tracker.track_error(endpoint)
            logger.error(f"Error listing files: {e}")
            raise

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        purpose: str,
        user_id: str = "default",
    ) -> FileObject:
        """
        Upload and validate file.

        Args:
            file_content: The file content as bytes
            filename: The filename
            purpose: The file purpose (assistants, fine-tune, batch, vision, etc.)
            user_id: User ID for quota tracking (default: 'default')

        Returns:
            FileObject with metadata

        Raises:
            FileValidationError: If validation fails
            FileQuotaError: If quota exceeded
            ValueError: If parameters are invalid
        """
        start_time = time.time()
        endpoint = "/v1/files"

        try:
            # Track request
            self.metrics_tracker.track_request(endpoint)

            # Validate parameters
            if not filename:
                raise ValueError("Filename is required")

            if not purpose:
                raise ValueError("Purpose is required")

            if file_content is None:
                raise ValueError("File content is required")

            if len(file_content) == 0:
                raise FileValidationError("File is empty")

            # Validate purpose
            if purpose not in self.file_manager.VALID_PURPOSES:
                raise ValueError(
                    f"Invalid purpose '{purpose}'. Valid purposes: {', '.join(sorted(self.file_manager.VALID_PURPOSES))}"
                )

            # Upload file via file manager
            file_object = await self.file_manager.upload_file(
                file_content=file_content,
                filename=filename,
                purpose=purpose,
                user_id=user_id,
            )

            # Track response
            latency = time.time() - start_time
            self.metrics_tracker.track_response(endpoint, latency)

            logger.info(
                f"File uploaded successfully: {file_object.id} ({file_object.filename}, {file_object.bytes} bytes)"
            )

            return file_object

        except (FileValidationError, FileQuotaError) as e:
            # Track error
            self.metrics_tracker.track_error(endpoint)
            logger.warning(f"File upload failed: {e}")
            raise
        except Exception as e:
            # Track error
            self.metrics_tracker.track_error(endpoint)
            logger.error(f"Error uploading file: {e}")
            raise

    async def get_file(self, file_id: str) -> FileObject:
        """
        Get file metadata.

        Args:
            file_id: The file ID

        Returns:
            FileObject with metadata

        Raises:
            FileNotFoundError: If file not found
            ValueError: If file_id is invalid
        """
        start_time = time.time()
        endpoint = "/v1/files"

        try:
            # Track request
            self.metrics_tracker.track_request(endpoint)

            # Validate parameter
            if not file_id:
                raise ValueError("File ID is required")

            # Get file from file manager
            file_object = await self.file_manager.get_file(file_id)

            # Track response
            latency = time.time() - start_time
            self.metrics_tracker.track_response(endpoint, latency)

            return file_object

        except FileNotFoundError as e:
            # Track error
            self.metrics_tracker.track_error(endpoint)
            logger.warning(f"File not found: {file_id}")
            raise
        except Exception as e:
            # Track error
            self.metrics_tracker.track_error(endpoint)
            logger.error(f"Error getting file: {e}")
            raise

    async def delete_file(self, file_id: str) -> dict[str, Any]:
        """
        Delete a file.

        Args:
            file_id: The file ID

        Returns:
            Dictionary with deletion confirmation

        Raises:
            FileNotFoundError: If file not found
            ValueError: If file_id is invalid
        """
        start_time = time.time()
        endpoint = "/v1/files"

        try:
            # Track request
            self.metrics_tracker.track_request(endpoint)

            # Validate parameter
            if not file_id:
                raise ValueError("File ID is required")

            # Delete file via file manager
            result = await self.file_manager.delete_file(file_id)

            # Track response
            latency = time.time() - start_time
            self.metrics_tracker.track_response(endpoint, latency)

            logger.info(f"File deleted successfully: {file_id}")

            return result

        except FileNotFoundError as e:
            # Track error
            self.metrics_tracker.track_error(endpoint)
            logger.warning(f"File not found: {file_id}")
            raise
        except Exception as e:
            # Track error
            self.metrics_tracker.track_error(endpoint)
            logger.error(f"Error deleting file: {e}")
            raise

    async def get_file_content(self, file_id: str) -> bytes:
        """
        Get file content.

        Args:
            file_id: The file ID

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If file not found
            ValueError: If file_id is invalid
        """
        start_time = time.time()
        endpoint = "/v1/files"

        try:
            # Track request
            self.metrics_tracker.track_request(endpoint)

            # Validate parameter
            if not file_id:
                raise ValueError("File ID is required")

            # Get file content from file manager
            content = await self.file_manager.get_file_content(file_id)

            # Track response
            latency = time.time() - start_time
            self.metrics_tracker.track_response(endpoint, latency)

            return content

        except FileNotFoundError as e:
            # Track error
            self.metrics_tracker.track_error(endpoint)
            logger.warning(f"File not found: {file_id}")
            raise
        except Exception as e:
            # Track error
            self.metrics_tracker.track_error(endpoint)
            logger.error(f"Error getting file content: {e}")
            raise

    async def get_user_quota_info(self, user_id: str = "default") -> dict[str, Any]:
        """
        Get quota information for a user.

        Args:
            user_id: User ID (default: 'default')

        Returns:
            Dictionary with quota information
        """
        return await self.file_manager.get_user_quota_info(user_id)

    async def verify_checksum(self, file_id: str, expected_checksum: str) -> bool:
        """
        Verify file checksum for integrity.

        Args:
            file_id: The file ID
            expected_checksum: Expected MD5 checksum

        Returns:
            True if checksum matches

        Raises:
            FileNotFoundError: If file not found
        """
        return await self.file_manager.verify_checksum(file_id, expected_checksum)
