"""
File management module for FakeAI.

Provides production-grade file upload, storage, retrieval, and deletion
with realistic behavior, validation, and quota enforcement.
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import hashlib
import io
import json
import mimetypes
import os
import re
import tempfile
import time
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from fakeai.models import FileObject


class FileValidationError(Exception):
    """Raised when file validation fails."""

    pass


class FileQuotaError(Exception):
    """Raised when file quota is exceeded."""

    pass


class FileNotFoundError(Exception):
    """Raised when file is not found."""

    pass


class StoredFile(BaseModel):
    """Internal representation of a stored file."""

    metadata: FileObject
    content: bytes
    checksum: str
    mime_type: str
    created_by: str = Field(default="default")
    expires_at: int | None = Field(default=None)


class FileStorageBackend:
    """Abstract base class for file storage backends."""

    async def store(self, file_id: str, file: StoredFile) -> None:
        """Store a file."""
        raise NotImplementedError

    async def retrieve(self, file_id: str) -> StoredFile:
        """Retrieve a file."""
        raise NotImplementedError

    async def delete(self, file_id: str) -> None:
        """Delete a file."""
        raise NotImplementedError

    async def list_all(self) -> list[StoredFile]:
        """List all stored files."""
        raise NotImplementedError

    async def exists(self, file_id: str) -> bool:
        """Check if file exists."""
        raise NotImplementedError


class InMemoryStorage(FileStorageBackend):
    """In-memory file storage backend."""

    def __init__(self):
        self.files: dict[str, StoredFile] = {}

    async def store(self, file_id: str, file: StoredFile) -> None:
        """Store a file in memory."""
        self.files[file_id] = file

    async def retrieve(self, file_id: str) -> StoredFile:
        """Retrieve a file from memory."""
        if file_id not in self.files:
            raise FileNotFoundError(f"File with ID '{file_id}' not found")
        return self.files[file_id]

    async def delete(self, file_id: str) -> None:
        """Delete a file from memory."""
        if file_id not in self.files:
            raise FileNotFoundError(f"File with ID '{file_id}' not found")
        del self.files[file_id]

    async def list_all(self) -> list[StoredFile]:
        """List all files in memory."""
        return list(self.files.values())

    async def exists(self, file_id: str) -> bool:
        """Check if file exists in memory."""
        return file_id in self.files


class DiskStorage(FileStorageBackend):
    """Disk-based file storage backend."""

    def __init__(self, base_dir: str | None = None):
        if base_dir is None:
            base_dir = os.path.join(tempfile.gettempdir(), "fakeai_files")
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, file_id: str) -> Path:
        """Get the full path for a file."""
        return self.base_dir / f"{file_id}.bin"

    def _get_metadata_path(self, file_id: str) -> Path:
        """Get the metadata path for a file."""
        return self.base_dir / f"{file_id}.json"

    async def store(self, file_id: str, file: StoredFile) -> None:
        """Store a file on disk."""
        # Store file content
        file_path = self._get_file_path(file_id)
        with open(file_path, "wb") as f:
            f.write(file.content)

        # Store metadata
        metadata_path = self._get_metadata_path(file_id)
        metadata_dict = {
            "metadata": file.metadata.model_dump(),
            "checksum": file.checksum,
            "mime_type": file.mime_type,
            "created_by": file.created_by,
            "expires_at": file.expires_at,
        }
        with open(metadata_path, "w") as f:
            json.dump(metadata_dict, f)

    async def retrieve(self, file_id: str) -> StoredFile:
        """Retrieve a file from disk."""
        file_path = self._get_file_path(file_id)
        metadata_path = self._get_metadata_path(file_id)

        if not file_path.exists() or not metadata_path.exists():
            raise FileNotFoundError(f"File with ID '{file_id}' not found")

        # Load file content
        with open(file_path, "rb") as f:
            content = f.read()

        # Load metadata
        with open(metadata_path, "r") as f:
            metadata_dict = json.load(f)

        return StoredFile(
            metadata=FileObject(**metadata_dict["metadata"]),
            content=content,
            checksum=metadata_dict["checksum"],
            mime_type=metadata_dict["mime_type"],
            created_by=metadata_dict.get("created_by", "default"),
            expires_at=metadata_dict.get("expires_at"),
        )

    async def delete(self, file_id: str) -> None:
        """Delete a file from disk."""
        file_path = self._get_file_path(file_id)
        metadata_path = self._get_metadata_path(file_id)

        if not file_path.exists():
            raise FileNotFoundError(f"File with ID '{file_id}' not found")

        file_path.unlink()
        if metadata_path.exists():
            metadata_path.unlink()

    async def list_all(self) -> list[StoredFile]:
        """List all files on disk."""
        files = []
        for metadata_path in self.base_dir.glob("*.json"):
            file_id = metadata_path.stem
            try:
                file = await self.retrieve(file_id)
                files.append(file)
            except FileNotFoundError:
                continue
        return files

    async def exists(self, file_id: str) -> bool:
        """Check if file exists on disk."""
        return self._get_file_path(file_id).exists()


class FileManager:
    """
    Production-grade file manager for FakeAI.

    Handles file upload, storage, retrieval, deletion with:
    - Actual file content storage (in-memory or disk)
    - Base64 encoding/decoding
    - MIME type detection
    - File size tracking
    - Checksum (MD5) for integrity
    - Purpose-based validation
    - File format validation
    - Quota enforcement
    - Automatic cleanup
    """

    # File size limits
    MAX_FILE_SIZE = 512 * 1024 * 1024  # 512 MB
    DEFAULT_FILE_TTL = 24 * 60 * 60  # 24 hours in seconds

    # Per-user quotas
    MAX_FILES_PER_USER = 1000
    MAX_STORAGE_PER_USER = 100 * 1024 * 1024 * 1024  # 100 GB

    # Valid purposes
    VALID_PURPOSES = {
        "assistants",
        "fine-tune",
        "batch",
        "vision",
        "responses",
        "user_data",
    }

    # Purpose-specific requirements
    PURPOSE_MIME_TYPES = {
        "assistants": {"text/plain", "application/json", "text/csv"},
        "fine-tune": {"application/jsonl", "application/x-jsonl"},
        "batch": {"application/jsonl", "application/x-jsonl"},
        "vision": {"image/png", "image/jpeg", "image/gif", "image/webp"},
        "responses": {"text/plain", "application/json"},
        "user_data": None,  # Any file type
    }

    def __init__(
        self,
        storage_backend: Literal["memory", "disk"] = "memory",
        storage_path: str | None = None,
        enable_cleanup: bool = True,
    ):
        """
        Initialize file manager.

        Args:
            storage_backend: Storage backend type ('memory' or 'disk')
            storage_path: Path for disk storage (only used if backend is 'disk')
            enable_cleanup: Enable automatic cleanup of expired files
        """
        if storage_backend == "memory":
            self.storage = InMemoryStorage()
        elif storage_backend == "disk":
            self.storage = DiskStorage(storage_path)
        else:
            raise ValueError(f"Invalid storage backend: {storage_backend}")

        self.enable_cleanup = enable_cleanup
        self.user_quotas: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"file_count": 0, "total_bytes": 0}
        )

        # Start cleanup task if enabled
        if enable_cleanup:
            asyncio.create_task(self._cleanup_expired_files())

    def _calculate_checksum(self, content: bytes) -> str:
        """Calculate MD5 checksum of file content."""
        return hashlib.md5(content).hexdigest()

    def _detect_mime_type(
        self, filename: str, content: bytes
    ) -> tuple[str, str | None]:
        """
        Detect MIME type from filename and content.

        Returns:
            Tuple of (mime_type, detected_format)
        """
        # First try to detect from filename extension
        mime_type, _ = mimetypes.guess_type(filename)

        # Special handling for JSONL files
        if filename.endswith(".jsonl"):
            return "application/jsonl", "jsonl"

        # If no MIME type detected, try content-based detection
        if mime_type is None:
            # Check for common formats
            if content.startswith(b"%PDF"):
                return "application/pdf", "pdf"
            elif content.startswith(b"\x89PNG"):
                return "image/png", "png"
            elif content.startswith(b"\xff\xd8\xff"):
                return "image/jpeg", "jpeg"
            elif content.startswith(b"GIF8"):
                return "image/gif", "gif"
            elif content.startswith(b"RIFF") and b"WEBP" in content[:20]:
                return "image/webp", "webp"
            elif content.startswith(b"{") or content.startswith(b"["):
                # Likely JSON
                return "application/json", "json"
            else:
                # Default to text/plain
                return "text/plain", "text"

        # Determine format from MIME type
        format_map = {
            "application/json": "json",
            "application/jsonl": "jsonl",
            "text/plain": "text",
            "text/csv": "csv",
            "application/pdf": "pdf",
            "image/png": "png",
            "image/jpeg": "jpeg",
            "image/gif": "gif",
            "image/webp": "webp",
        }
        detected_format = format_map.get(mime_type)

        return mime_type, detected_format

    def _validate_jsonl(self, content: bytes) -> tuple[bool, str | None]:
        """
        Validate JSONL format (newline-delimited JSON).

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            text = content.decode("utf-8")
            lines = text.strip().split("\n")

            if not lines:
                return False, "JSONL file is empty"

            for i, line in enumerate(lines):
                if not line.strip():
                    continue  # Allow empty lines
                try:
                    json.loads(line)
                except json.JSONDecodeError as e:
                    return False, f"Invalid JSON on line {i + 1}: {str(e)}"

            return True, None
        except UnicodeDecodeError:
            return False, "File is not valid UTF-8"

    def _validate_fine_tune_jsonl(self, content: bytes) -> tuple[bool, str | None]:
        """
        Validate fine-tuning JSONL format.

        Expected format:
        {"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
        """
        is_valid, error = self._validate_jsonl(content)
        if not is_valid:
            return False, error

        try:
            text = content.decode("utf-8")
            lines = text.strip().split("\n")

            for i, line in enumerate(lines):
                if not line.strip():
                    continue

                data = json.loads(line)

                # Check for required 'messages' field
                if "messages" not in data:
                    return (
                        False,
                        f"Line {i + 1}: Missing 'messages' field (required for fine-tuning)",
                    )

                messages = data["messages"]
                if not isinstance(messages, list) or len(messages) == 0:
                    return (
                        False,
                        f"Line {i + 1}: 'messages' must be a non-empty list",
                    )

                # Validate each message has role and content
                for j, msg in enumerate(messages):
                    if not isinstance(msg, dict):
                        return (
                            False,
                            f"Line {i + 1}, message {j + 1}: Message must be a dictionary",
                        )
                    if "role" not in msg:
                        return (
                            False,
                            f"Line {i + 1}, message {j + 1}: Missing 'role' field",
                        )
                    if "content" not in msg:
                        return (
                            False,
                            f"Line {i + 1}, message {j + 1}: Missing 'content' field",
                        )

            return True, None
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def _validate_batch_jsonl(self, content: bytes) -> tuple[bool, str | None]:
        """
        Validate batch JSONL format.

        Expected format:
        {"custom_id": "request-1", "method": "POST", "url": "/v1/chat/completions", "body": {...}}
        """
        is_valid, error = self._validate_jsonl(content)
        if not is_valid:
            return False, error

        try:
            text = content.decode("utf-8")
            lines = text.strip().split("\n")

            for i, line in enumerate(lines):
                if not line.strip():
                    continue

                data = json.loads(line)

                # Check for required fields
                required_fields = ["custom_id", "method", "url", "body"]
                for field in required_fields:
                    if field not in data:
                        return (
                            False,
                            f"Line {i + 1}: Missing required field '{field}' (batch format)",
                        )

                # Validate method
                if data["method"] not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    return (
                        False,
                        f"Line {i + 1}: Invalid HTTP method '{data['method']}'",
                    )

                # Validate body is a dict
                if not isinstance(data["body"], dict):
                    return False, f"Line {i + 1}: 'body' must be a dictionary"

            return True, None
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def _validate_image(
        self, content: bytes, mime_type: str
    ) -> tuple[bool, str | None]:
        """
        Validate image file.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check magic bytes
        if mime_type == "image/png" and not content.startswith(b"\x89PNG"):
            return False, "Invalid PNG file (bad magic bytes)"
        elif mime_type == "image/jpeg" and not content.startswith(b"\xff\xd8\xff"):
            return False, "Invalid JPEG file (bad magic bytes)"
        elif mime_type == "image/gif" and not content.startswith(b"GIF8"):
            return False, "Invalid GIF file (bad magic bytes)"
        elif mime_type == "image/webp" and not (
            content.startswith(b"RIFF") and b"WEBP" in content[:20]
        ):
            return False, "Invalid WEBP file (bad magic bytes)"

        # Basic size check (at least 100 bytes for a valid image)
        if len(content) < 100:
            return False, "Image file too small (likely corrupted)"

        return True, None

    def _validate_csv(self, content: bytes) -> tuple[bool, str | None]:
        """
        Validate CSV format.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            text = content.decode("utf-8")
            lines = text.strip().split("\n")

            if not lines:
                return False, "CSV file is empty"

            # Check first line has at least one column
            first_line = lines[0].strip()
            if not first_line:
                return False, "CSV file has empty header"

            # Very basic validation - just check it's parseable
            import csv
            import io as iomodule

            reader = csv.reader(iomodule.StringIO(text))
            try:
                rows = list(reader)
                if len(rows) == 0:
                    return False, "CSV file is empty"
                return True, None
            except csv.Error as e:
                return False, f"CSV parsing error: {str(e)}"

        except UnicodeDecodeError:
            return False, "CSV file is not valid UTF-8"

    async def validate_file_for_purpose(
        self, file_content: bytes, filename: str, purpose: str
    ) -> tuple[bool, str | None]:
        """
        Validate file matches purpose requirements.

        Args:
            file_content: The file content as bytes
            filename: The filename
            purpose: The file purpose

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check purpose is valid
        if purpose not in self.VALID_PURPOSES:
            return (
                False,
                f"Invalid purpose '{purpose}'. Valid purposes: {', '.join(sorted(self.VALID_PURPOSES))}",
            )

        # Detect MIME type
        mime_type, detected_format = self._detect_mime_type(filename, file_content)

        # Check MIME type is allowed for purpose
        allowed_types = self.PURPOSE_MIME_TYPES.get(purpose)
        if allowed_types is not None and mime_type not in allowed_types:
            return (
                False,
                f"MIME type '{mime_type}' not allowed for purpose '{purpose}'. Allowed types: {', '.join(sorted(allowed_types))}",
            )

        # Purpose-specific validation
        if purpose == "fine-tune":
            if detected_format != "jsonl":
                return False, "Fine-tuning files must be in JSONL format"
            return self._validate_fine_tune_jsonl(file_content)

        elif purpose == "batch":
            if detected_format != "jsonl":
                return False, "Batch files must be in JSONL format"
            return self._validate_batch_jsonl(file_content)

        elif purpose == "vision":
            if not mime_type.startswith("image/"):
                return False, "Vision files must be images"
            return self._validate_image(file_content, mime_type)

        elif purpose == "assistants":
            # Assistants can accept text, JSON, or CSV
            if detected_format == "csv":
                return self._validate_csv(file_content)
            elif detected_format == "json":
                try:
                    json.loads(file_content.decode("utf-8"))
                    return True, None
                except Exception as e:
                    return False, f"Invalid JSON: {str(e)}"
            # Text files are always valid
            return True, None

        # Default: no specific validation
        return True, None

    async def _check_quota(self, user_id: str, file_size: int) -> None:
        """
        Check if upload would exceed user quota.

        Raises:
            FileQuotaError if quota would be exceeded
        """
        quota = self.user_quotas[user_id]

        if quota["file_count"] >= self.MAX_FILES_PER_USER:
            raise FileQuotaError(
                f"User file count limit exceeded (max {self.MAX_FILES_PER_USER} files)"
            )

        if quota["total_bytes"] + file_size > self.MAX_STORAGE_PER_USER:
            max_gb = self.MAX_STORAGE_PER_USER / (1024 * 1024 * 1024)
            raise FileQuotaError(f"User storage limit exceeded (max {max_gb:.1f} GB)")

    async def _update_quota(
        self, user_id: str, file_size: int, increment: bool = True
    ) -> None:
        """Update user quota counters."""
        if increment:
            self.user_quotas[user_id]["file_count"] += 1
            self.user_quotas[user_id]["total_bytes"] += file_size
        else:
            self.user_quotas[user_id]["file_count"] = max(
                0, self.user_quotas[user_id]["file_count"] - 1
            )
            self.user_quotas[user_id]["total_bytes"] = max(
                0, self.user_quotas[user_id]["total_bytes"] - file_size
            )

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
            purpose: The file purpose
            user_id: User ID for quota tracking

        Returns:
            FileObject with metadata

        Raises:
            FileValidationError: If validation fails
            FileQuotaError: If quota exceeded
        """
        # Check file size
        file_size = len(file_content)
        if file_size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE / (1024 * 1024)
            raise FileValidationError(
                f"File size ({file_size / (1024 * 1024):.1f} MB) exceeds maximum allowed size ({max_mb:.1f} MB)"
            )

        if file_size == 0:
            raise FileValidationError("File is empty")

        # Check quota
        await self._check_quota(user_id, file_size)

        # Validate file for purpose
        is_valid, error_message = await self.validate_file_for_purpose(
            file_content, filename, purpose
        )
        if not is_valid:
            raise FileValidationError(f"File validation failed: {error_message}")

        # Generate file ID
        file_id = f"file-{uuid.uuid4().hex}"

        # Detect MIME type
        mime_type, _ = self._detect_mime_type(filename, file_content)

        # Calculate checksum
        checksum = self._calculate_checksum(file_content)

        # Create metadata
        created_at = int(time.time())
        expires_at = created_at + self.DEFAULT_FILE_TTL

        metadata = FileObject(
            id=file_id,
            bytes=file_size,
            created_at=created_at,
            filename=filename,
            purpose=purpose,
            status="uploaded",
            status_details=None,
        )

        # Store file
        stored_file = StoredFile(
            metadata=metadata,
            content=file_content,
            checksum=checksum,
            mime_type=mime_type,
            created_by=user_id,
            expires_at=expires_at,
        )

        await self.storage.store(file_id, stored_file)

        # Update quota
        await self._update_quota(user_id, file_size, increment=True)

        # Simulate processing delay
        await asyncio.sleep(0.1)

        return metadata

    async def get_file(self, file_id: str) -> FileObject:
        """
        Retrieve file metadata.

        Args:
            file_id: The file ID

        Returns:
            FileObject with metadata

        Raises:
            FileNotFoundError: If file not found
        """
        stored_file = await self.storage.retrieve(file_id)
        return stored_file.metadata

    async def get_file_content(self, file_id: str) -> bytes:
        """
        Retrieve file content.

        Args:
            file_id: The file ID

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If file not found
        """
        stored_file = await self.storage.retrieve(file_id)
        return stored_file.content

    async def get_file_with_content(self, file_id: str) -> tuple[FileObject, bytes]:
        """
        Retrieve file metadata and content together.

        Args:
            file_id: The file ID

        Returns:
            Tuple of (FileObject, content_bytes)

        Raises:
            FileNotFoundError: If file not found
        """
        stored_file = await self.storage.retrieve(file_id)
        return stored_file.metadata, stored_file.content

    async def delete_file(self, file_id: str) -> dict[str, Any]:
        """
        Delete a file.

        Args:
            file_id: The file ID

        Returns:
            Dictionary with deletion confirmation

        Raises:
            FileNotFoundError: If file not found
        """
        # Get file to update quota
        stored_file = await self.storage.retrieve(file_id)

        # Delete from storage
        await self.storage.delete(file_id)

        # Update quota
        await self._update_quota(
            stored_file.created_by,
            stored_file.metadata.bytes,
            increment=False,
        )

        return {
            "id": file_id,
            "object": "file",
            "deleted": True,
        }

    async def list_files(
        self,
        purpose: str | None = None,
        limit: int = 20,
        after: str | None = None,
        order: str = "desc",
    ) -> list[FileObject]:
        """
        List files with pagination.

        Args:
            purpose: Filter by purpose
            limit: Maximum number of files to return
            after: Cursor for pagination (file ID)
            order: Sort order ('asc' or 'desc')

        Returns:
            List of FileObject
        """
        # Get all files
        all_files = await self.storage.list_all()

        # Extract metadata
        files = [f.metadata for f in all_files]

        # Filter by purpose
        if purpose:
            files = [f for f in files if f.purpose == purpose]

        # Sort by created_at
        reverse = order == "desc"
        files.sort(key=lambda f: f.created_at, reverse=reverse)

        # Apply cursor-based pagination
        if after:
            # Find the position of the 'after' file
            after_index = -1
            for i, f in enumerate(files):
                if f.id == after:
                    after_index = i
                    break

            if after_index >= 0:
                # Return files after this position
                files = files[after_index + 1 :]

        # Apply limit
        files = files[:limit]

        return files

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
        stored_file = await self.storage.retrieve(file_id)
        return stored_file.checksum == expected_checksum

    async def _cleanup_expired_files(self) -> None:
        """Background task to clean up expired files."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour

                current_time = int(time.time())
                all_files = await self.storage.list_all()

                for stored_file in all_files:
                    if (
                        stored_file.expires_at
                        and stored_file.expires_at <= current_time
                    ):
                        try:
                            await self.delete_file(stored_file.metadata.id)
                        except Exception:
                            # Ignore errors during cleanup
                            pass

            except Exception:
                # Ignore errors in cleanup task
                pass

    async def get_user_quota_info(self, user_id: str = "default") -> dict[str, Any]:
        """
        Get quota information for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with quota information
        """
        quota = self.user_quotas[user_id]
        return {
            "user_id": user_id,
            "file_count": quota["file_count"],
            "total_bytes": quota["total_bytes"],
            "max_files": self.MAX_FILES_PER_USER,
            "max_bytes": self.MAX_STORAGE_PER_USER,
            "files_remaining": self.MAX_FILES_PER_USER - quota["file_count"],
            "bytes_remaining": self.MAX_STORAGE_PER_USER - quota["total_bytes"],
        }
