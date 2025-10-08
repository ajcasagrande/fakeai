"""
Vector store service for FakeAI.

This module provides vector store management services including CRUD operations,
file attachment, batch processing, and expiration policies.
"""

#  SPDX-License-Identifier: Apache-2.0

import logging
import threading
import time
import uuid
from typing import Any

from fakeai.config import AppConfig
from fakeai.file_manager import FileManager, FileNotFoundError
from fakeai.metrics import MetricsTracker
from fakeai.models import (
    AutoChunkingStrategy,
    ChunkingStrategy,
    CreateVectorStoreFileBatchRequest,
    CreateVectorStoreFileRequest,
    CreateVectorStoreRequest,
    ExpiresAfter,
    FileCounts,
    ModifyVectorStoreRequest,
    VectorStore,
    VectorStoreFile,
    VectorStoreFileBatch,
    VectorStoreFileListResponse,
    VectorStoreListResponse,
)

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    Vector store service for managing vector store operations.

    Provides high-level vector store operations including:
    - CRUD operations for vector stores
    - File attachment and management
    - Batch file processing
    - Expiration policy management
    - File count and usage tracking

    Features:
    - In-memory storage with thread safety
    - Automatic file processing simulation
    - Expiration policy support
    - Chunking strategy support
    - Metrics tracking for all operations
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
        file_manager: FileManager,
    ):
        """
        Initialize vector store service.

        Args:
            config: Application configuration
            metrics_tracker: Metrics tracker for monitoring
            file_manager: File manager for file validation
        """
        self.config = config
        self.metrics_tracker = metrics_tracker
        self.file_manager = file_manager
        self._lock = threading.RLock()

        # In-memory storage
        self._vector_stores: dict[str, VectorStore] = {}
        # vs_id -> files
        self._vector_store_files: dict[str, list[VectorStoreFile]] = {}
        # batch_id -> batch
        self._file_batches: dict[str, VectorStoreFileBatch] = {}
        # batch_id -> files
        self._batch_files: dict[str, list[VectorStoreFile]] = {}

        logger.info("VectorStoreService initialized")

    def _generate_vector_store_id(self) -> str:
        """Generate a unique vector store ID."""
        return f"vs_{uuid.uuid4().hex[:24]}"

    def _generate_vector_store_file_id(self) -> str:
        """Generate a unique vector store file ID."""
        return f"vsf_{uuid.uuid4().hex[:24]}"

    def _generate_file_batch_id(self) -> str:
        """Generate a unique file batch ID."""
        return f"vsfb_{uuid.uuid4().hex[:24]}"

    def _calculate_expiration(
        self, created_at: int, expires_after: ExpiresAfter | None
    ) -> int | None:
        """
        Calculate expiration timestamp based on policy.

        Args:
            created_at: Creation timestamp
            expires_after: Expiration policy

        Returns:
            Expiration timestamp or None
        """
        if not expires_after:
            return None

        # For last_active_at anchor, use created_at initially
        return created_at + (expires_after.days * 86400)

    def _update_file_counts(self, vs_id: str) -> FileCounts:
        """
        Update and return file counts for a vector store.

        Args:
            vs_id: Vector store ID

        Returns:
            Updated file counts
        """
        with self._lock:
            files = self._vector_store_files.get(vs_id, [])

            counts = FileCounts(
                in_progress=sum(1 for f in files if f.status == "in_progress"),
                completed=sum(1 for f in files if f.status == "completed"),
                failed=sum(1 for f in files if f.status == "failed"),
                cancelled=sum(1 for f in files if f.status == "cancelled"),
                total=len(files),
            )

            return counts

    def _calculate_usage_bytes(self, vs_id: str) -> int:
        """
        Calculate total usage bytes for a vector store.

        Args:
            vs_id: Vector store ID

        Returns:
            Total bytes used
        """
        with self._lock:
            files = self._vector_store_files.get(vs_id, [])
            return sum(f.usage_bytes for f in files)

    async def create_vector_store(
        self, request: CreateVectorStoreRequest
    ) -> VectorStore:
        """
        Create a new vector store.

        Args:
            request: Vector store creation request

        Returns:
            Created vector store

        Raises:
            FileNotFoundError: If any file_id doesn't exist
        """
        start_time = time.time()
        endpoint = "/v1/vector_stores"

        try:

            # Generate ID and timestamps
            vs_id = self._generate_vector_store_id()
            created_at = int(time.time())

            # Calculate expiration
            expires_at = self._calculate_expiration(
                created_at, request.expires_after)

            # Create vector store
            vector_store = VectorStore(
                id=vs_id,
                object="vector_store",
                created_at=created_at,
                name=request.name,
                usage_bytes=0,
                file_counts=FileCounts(),
                status="completed",  # Will be "in_progress" if files added
                expires_after=request.expires_after,
                expires_at=expires_at,
                last_active_at=created_at,
                metadata=request.metadata,
            )

            # Store vector store
            with self._lock:
                self._vector_stores[vs_id] = vector_store
                self._vector_store_files[vs_id] = []

            # Add initial files if provided
            if request.file_ids:
                # Validate all files exist first
                for file_id in request.file_ids:
                    file_obj = self.file_manager.get_file(file_id)
                    if not file_obj:
                        # Clean up the vector store we just created
                        with self._lock:
                            del self._vector_stores[vs_id]
                            del self._vector_store_files[vs_id]
                        raise FileNotFoundError(f"File {file_id} not found")

                # Add files
                for file_id in request.file_ids:
                    await self._add_file_internal(
                        vs_id, file_id, request.chunking_strategy
                    )

                # Update vector store status and counts
                with self._lock:
                    vector_store.file_counts = self._update_file_counts(vs_id)
                    vector_store.usage_bytes = self._calculate_usage_bytes(
                        vs_id)

                    # Check if any files are still in progress
                    if vector_store.file_counts.in_progress > 0:
                        vector_store.status = "in_progress"
                    else:
                        vector_store.status = "completed"

            # Track latency
            latency_ms = (time.time() - start_time) * 1000
            self.metrics_tracker.record_request(endpoint, latency_ms)

            logger.info(
                f"Created vector store {vs_id} with {len(request.file_ids or [])} files")
            return vector_store

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            raise

    async def list_vector_stores(
        self,
        limit: int = 20,
        order: str = "desc",
        after: str | None = None,
        before: str | None = None,
    ) -> VectorStoreListResponse:
        """
        List vector stores with pagination.

        Args:
            limit: Maximum number of vector stores to return
            order: Sort order ('asc' or 'desc')
            after: Cursor for pagination (vector store ID)
            before: Cursor for backward pagination

        Returns:
            List response with vector stores
        """
        start_time = time.time()
        endpoint = "/v1/vector_stores"

        try:

            with self._lock:
                # Get all vector stores
                stores = list(self._vector_stores.values())

            # Sort by created_at
            reverse = order == "desc"
            stores.sort(key=lambda x: x.created_at, reverse=reverse)

            # Apply cursor filtering
            if after:
                try:
                    after_index = next(
                        i for i, s in enumerate(stores) if s.id == after)
                    stores = stores[after_index + 1:]
                except StopIteration:
                    stores = []

            if before:
                try:
                    before_index = next(
                        i for i, s in enumerate(stores) if s.id == before)
                    stores = stores[:before_index]
                except StopIteration:
                    pass

            # Apply limit
            has_more = len(stores) > limit
            stores = stores[:limit]

            # Build response
            response = VectorStoreListResponse(
                object="list",
                data=stores,
                first_id=stores[0].id if stores else None,
                last_id=stores[-1].id if stores else None,
                has_more=has_more,
            )

            # Track latency
            latency_ms = (time.time() - start_time) * 1000
            self.metrics_tracker.record_request(endpoint, latency_ms)

            return response

        except Exception as e:
            logger.error(f"Error listing vector stores: {e}")
            raise

    async def retrieve_vector_store(self, vs_id: str) -> VectorStore:
        """
        Retrieve a vector store by ID.

        Args:
            vs_id: Vector store ID

        Returns:
            Vector store object

        Raises:
            ValueError: If vector store not found
        """
        start_time = time.time()
        endpoint = f"/v1/vector_stores/{vs_id}"

        try:

            with self._lock:
                if vs_id not in self._vector_stores:
                    raise ValueError(f"Vector store {vs_id} not found")

                vector_store = self._vector_stores[vs_id]

                # Update last_active_at
                vector_store.last_active_at = int(time.time())

                # Update file counts and usage
                vector_store.file_counts = self._update_file_counts(vs_id)
                vector_store.usage_bytes = self._calculate_usage_bytes(vs_id)

            # Track latency
            latency_ms = (time.time() - start_time) * 1000
            self.metrics_tracker.record_request(endpoint, latency_ms)

            return vector_store

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving vector store: {e}")
            raise

    async def modify_vector_store(
        self, vs_id: str, request: ModifyVectorStoreRequest
    ) -> VectorStore:
        """
        Modify a vector store.

        Args:
            vs_id: Vector store ID
            request: Modification request

        Returns:
            Updated vector store

        Raises:
            ValueError: If vector store not found
        """
        start_time = time.time()
        endpoint = f"/v1/vector_stores/{vs_id}"

        try:

            with self._lock:
                if vs_id not in self._vector_stores:
                    raise ValueError(f"Vector store {vs_id} not found")

                vector_store = self._vector_stores[vs_id]

                # Update fields
                if request.name is not None:
                    vector_store.name = request.name

                if request.metadata is not None:
                    vector_store.metadata = request.metadata

                if request.expires_after is not None:
                    vector_store.expires_after = request.expires_after
                    vector_store.expires_at = self._calculate_expiration(
                        vector_store.last_active_at or vector_store.created_at,
                        request.expires_after,
                    )

                # Update last_active_at
                vector_store.last_active_at = int(time.time())

            # Track latency
            latency_ms = (time.time() - start_time) * 1000
            self.metrics_tracker.record_request(endpoint, latency_ms)

            logger.info(f"Modified vector store {vs_id}")
            return vector_store

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error modifying vector store: {e}")
            raise

    async def delete_vector_store(self, vs_id: str) -> dict[str, Any]:
        """
        Delete a vector store.

        Args:
            vs_id: Vector store ID

        Returns:
            Deletion confirmation

        Raises:
            ValueError: If vector store not found
        """
        start_time = time.time()
        endpoint = f"/v1/vector_stores/{vs_id}"

        try:

            with self._lock:
                if vs_id not in self._vector_stores:
                    raise ValueError(f"Vector store {vs_id} not found")

                # Remove vector store and associated files
                del self._vector_stores[vs_id]
                self._vector_store_files.pop(vs_id, None)

            # Track latency
            latency_ms = (time.time() - start_time) * 1000
            self.metrics_tracker.record_request(endpoint, latency_ms)

            logger.info(f"Deleted vector store {vs_id}")
            return {
                "id": vs_id,
                "object": "vector_store.deleted",
                "deleted": True,
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error deleting vector store: {e}")
            raise

    async def _add_file_internal(
        self,
        vs_id: str,
        file_id: str,
        chunking_strategy: ChunkingStrategy | None = None,
    ) -> VectorStoreFile:
        """
        Internal method to add a file to a vector store.

        Args:
            vs_id: Vector store ID
            file_id: File ID to add
            chunking_strategy: Chunking strategy to use

        Returns:
            Vector store file object

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        # Validate file exists
        file_obj = self.file_manager.get_file(file_id)
        if not file_obj:
            raise FileNotFoundError(f"File {file_id} not found")

        # Generate vector store file ID
        vsf_id = self._generate_vector_store_file_id()
        created_at = int(time.time())

        # Use auto chunking if not specified
        if chunking_strategy is None:
            chunking_strategy = AutoChunkingStrategy(type="auto")

        # Create vector store file (simulate instant completion)
        vs_file = VectorStoreFile(
            id=vsf_id,
            object="vector_store.file",
            usage_bytes=file_obj.bytes or 0,
            created_at=created_at,
            vector_store_id=vs_id,
            status="completed",  # Simulate instant processing
            last_error=None,
            chunking_strategy=chunking_strategy,
        )

        # Add to vector store
        with self._lock:
            if vs_id not in self._vector_store_files:
                self._vector_store_files[vs_id] = []
            self._vector_store_files[vs_id].append(vs_file)

        return vs_file

    async def add_file_to_vector_store(
        self, vs_id: str, request: CreateVectorStoreFileRequest
    ) -> VectorStoreFile:
        """
        Add a file to a vector store.

        Args:
            vs_id: Vector store ID
            request: File addition request

        Returns:
            Vector store file object

        Raises:
            ValueError: If vector store not found
            FileNotFoundError: If file doesn't exist
        """
        start_time = time.time()
        endpoint = f"/v1/vector_stores/{vs_id}/files"

        try:

            # Validate vector store exists
            with self._lock:
                if vs_id not in self._vector_stores:
                    raise ValueError(f"Vector store {vs_id} not found")

            # Add file
            vs_file = await self._add_file_internal(
                vs_id, request.file_id, request.chunking_strategy
            )

            # Update vector store
            with self._lock:
                vector_store = self._vector_stores[vs_id]
                vector_store.file_counts = self._update_file_counts(vs_id)
                vector_store.usage_bytes = self._calculate_usage_bytes(vs_id)
                vector_store.last_active_at = int(time.time())

            # Track latency
            latency_ms = (time.time() - start_time) * 1000
            self.metrics_tracker.record_request(endpoint, latency_ms)

            logger.info(
                f"Added file {
                    request.file_id} to vector store {vs_id}")
            return vs_file

        except (ValueError, FileNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error adding file to vector store: {e}")
            raise

    async def list_vector_store_files(
        self,
        vs_id: str,
        limit: int = 20,
        order: str = "desc",
        after: str | None = None,
        before: str | None = None,
        filter_status: str | None = None,
    ) -> VectorStoreFileListResponse:
        """
        List files in a vector store.

        Args:
            vs_id: Vector store ID
            limit: Maximum number of files to return
            order: Sort order ('asc' or 'desc')
            after: Cursor for pagination
            before: Cursor for backward pagination
            filter_status: Filter by status

        Returns:
            List response with vector store files

        Raises:
            ValueError: If vector store not found
        """
        start_time = time.time()
        endpoint = f"/v1/vector_stores/{vs_id}/files"

        try:

            with self._lock:
                if vs_id not in self._vector_stores:
                    raise ValueError(f"Vector store {vs_id} not found")

                # Get files
                files = list(self._vector_store_files.get(vs_id, []))

            # Filter by status if requested
            if filter_status:
                files = [f for f in files if f.status == filter_status]

            # Sort by created_at
            reverse = order == "desc"
            files.sort(key=lambda x: x.created_at, reverse=reverse)

            # Apply cursor filtering
            if after:
                try:
                    after_index = next(
                        i for i, f in enumerate(files) if f.id == after)
                    files = files[after_index + 1:]
                except StopIteration:
                    files = []

            if before:
                try:
                    before_index = next(
                        i for i, f in enumerate(files) if f.id == before)
                    files = files[:before_index]
                except StopIteration:
                    pass

            # Apply limit
            has_more = len(files) > limit
            files = files[:limit]

            # Build response
            response = VectorStoreFileListResponse(
                object="list",
                data=files,
                first_id=files[0].id if files else None,
                last_id=files[-1].id if files else None,
                has_more=has_more,
            )

            # Track latency
            latency_ms = (time.time() - start_time) * 1000
            self.metrics_tracker.record_request(endpoint, latency_ms)

            return response

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error listing vector store files: {e}")
            raise

    async def retrieve_vector_store_file(
        self, vs_id: str, file_id: str
    ) -> VectorStoreFile:
        """
        Retrieve a specific file from a vector store.

        Args:
            vs_id: Vector store ID
            file_id: Vector store file ID

        Returns:
            Vector store file object

        Raises:
            ValueError: If vector store or file not found
        """
        start_time = time.time()
        endpoint = f"/v1/vector_stores/{vs_id}/files/{file_id}"

        try:

            with self._lock:
                if vs_id not in self._vector_stores:
                    raise ValueError(f"Vector store {vs_id} not found")

                files = self._vector_store_files.get(vs_id, [])
                vs_file = next((f for f in files if f.id == file_id), None)

                if not vs_file:
                    raise ValueError(
                        f"File {file_id} not found in vector store {vs_id}")

            # Track latency
            latency_ms = (time.time() - start_time) * 1000
            self.metrics_tracker.record_request(endpoint, latency_ms)

            return vs_file

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving vector store file: {e}")
            raise

    async def delete_vector_store_file(
        self, vs_id: str, file_id: str
    ) -> dict[str, Any]:
        """
        Delete a file from a vector store.

        Args:
            vs_id: Vector store ID
            file_id: Vector store file ID

        Returns:
            Deletion confirmation

        Raises:
            ValueError: If vector store or file not found
        """
        start_time = time.time()
        endpoint = f"/v1/vector_stores/{vs_id}/files/{file_id}"

        try:

            with self._lock:
                if vs_id not in self._vector_stores:
                    raise ValueError(f"Vector store {vs_id} not found")

                files = self._vector_store_files.get(vs_id, [])
                file_index = next(
                    (i for i, f in enumerate(files) if f.id == file_id), None
                )

                if file_index is None:
                    raise ValueError(
                        f"File {file_id} not found in vector store {vs_id}")

                # Remove file
                del self._vector_store_files[vs_id][file_index]

                # Update vector store
                vector_store = self._vector_stores[vs_id]
                vector_store.file_counts = self._update_file_counts(vs_id)
                vector_store.usage_bytes = self._calculate_usage_bytes(vs_id)
                vector_store.last_active_at = int(time.time())

            # Track latency
            latency_ms = (time.time() - start_time) * 1000
            self.metrics_tracker.record_request(endpoint, latency_ms)

            logger.info(f"Deleted file {file_id} from vector store {vs_id}")
            return {
                "id": file_id,
                "object": "vector_store.file.deleted",
                "deleted": True,
            }

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error deleting vector store file: {e}")
            raise

    async def create_file_batch(
        self, vs_id: str, request: CreateVectorStoreFileBatchRequest
    ) -> VectorStoreFileBatch:
        """
        Create a batch of files in a vector store.

        Args:
            vs_id: Vector store ID
            request: Batch creation request

        Returns:
            File batch object

        Raises:
            ValueError: If vector store not found
            FileNotFoundError: If any file doesn't exist
        """
        start_time = time.time()
        endpoint = f"/v1/vector_stores/{vs_id}/file_batches"

        try:

            # Validate vector store exists
            with self._lock:
                if vs_id not in self._vector_stores:
                    raise ValueError(f"Vector store {vs_id} not found")

            # Validate all files exist
            for file_id in request.file_ids:
                file_obj = self.file_manager.get_file(file_id)
                if not file_obj:
                    raise FileNotFoundError(f"File {file_id} not found")

            # Generate batch ID
            batch_id = self._generate_file_batch_id()
            created_at = int(time.time())

            # Add all files
            batch_files = []
            for file_id in request.file_ids:
                vs_file = await self._add_file_internal(
                    vs_id, file_id, request.chunking_strategy
                )
                batch_files.append(vs_file)

            # Create batch object
            file_counts = FileCounts(
                completed=len(batch_files),  # Simulate instant completion
                total=len(batch_files),
            )

            batch = VectorStoreFileBatch(
                id=batch_id,
                object="vector_store.files_batch",
                created_at=created_at,
                vector_store_id=vs_id,
                status="completed",  # Simulate instant completion
                file_counts=file_counts,
            )

            # Store batch
            with self._lock:
                self._file_batches[batch_id] = batch
                self._batch_files[batch_id] = batch_files

                # Update vector store
                vector_store = self._vector_stores[vs_id]
                vector_store.file_counts = self._update_file_counts(vs_id)
                vector_store.usage_bytes = self._calculate_usage_bytes(vs_id)
                vector_store.last_active_at = int(time.time())

            # Track latency
            latency_ms = (time.time() - start_time) * 1000
            self.metrics_tracker.record_request(endpoint, latency_ms)

            logger.info(
                f"Created file batch {batch_id} with {len(request.file_ids)} files")
            return batch

        except (ValueError, FileNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error creating file batch: {e}")
            raise

    async def retrieve_file_batch(
        self, vs_id: str, batch_id: str
    ) -> VectorStoreFileBatch:
        """
        Retrieve a file batch.

        Args:
            vs_id: Vector store ID
            batch_id: Batch ID

        Returns:
            File batch object

        Raises:
            ValueError: If batch not found
        """
        start_time = time.time()
        endpoint = f"/v1/vector_stores/{vs_id}/file_batches/{batch_id}"

        try:

            with self._lock:
                if batch_id not in self._file_batches:
                    raise ValueError(f"Batch {batch_id} not found")

                batch = self._file_batches[batch_id]

                # Verify it belongs to this vector store
                if batch.vector_store_id != vs_id:
                    raise ValueError(
                        f"Batch {batch_id} does not belong to vector store {vs_id}")

            # Track latency
            latency_ms = (time.time() - start_time) * 1000
            self.metrics_tracker.record_request(endpoint, latency_ms)

            return batch

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving file batch: {e}")
            raise

    async def cancel_file_batch(
        self, vs_id: str, batch_id: str
    ) -> VectorStoreFileBatch:
        """
        Cancel a file batch.

        Args:
            vs_id: Vector store ID
            batch_id: Batch ID

        Returns:
            Updated file batch object

        Raises:
            ValueError: If batch not found or already completed
        """
        start_time = time.time()
        endpoint = f"/v1/vector_stores/{vs_id}/file_batches/{batch_id}/cancel"

        try:

            with self._lock:
                if batch_id not in self._file_batches:
                    raise ValueError(f"Batch {batch_id} not found")

                batch = self._file_batches[batch_id]

                # Verify it belongs to this vector store
                if batch.vector_store_id != vs_id:
                    raise ValueError(
                        f"Batch {batch_id} does not belong to vector store {vs_id}")

                # Update status
                batch.status = "cancelled"

                # Update file counts
                batch.file_counts.cancelled = batch.file_counts.total
                batch.file_counts.in_progress = 0
                batch.file_counts.completed = 0

            # Track latency
            latency_ms = (time.time() - start_time) * 1000
            self.metrics_tracker.record_request(endpoint, latency_ms)

            logger.info(f"Cancelled file batch {batch_id}")
            return batch

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error cancelling file batch: {e}")
            raise

    async def list_batch_files(
        self,
        vs_id: str,
        batch_id: str,
        limit: int = 20,
        order: str = "desc",
        after: str | None = None,
        before: str | None = None,
        filter_status: str | None = None,
    ) -> VectorStoreFileListResponse:
        """
        List files in a batch.

        Args:
            vs_id: Vector store ID
            batch_id: Batch ID
            limit: Maximum number of files to return
            order: Sort order ('asc' or 'desc')
            after: Cursor for pagination
            before: Cursor for backward pagination
            filter_status: Filter by status

        Returns:
            List response with vector store files

        Raises:
            ValueError: If batch not found
        """
        start_time = time.time()
        endpoint = f"/v1/vector_stores/{vs_id}/file_batches/{batch_id}/files"

        try:

            with self._lock:
                if batch_id not in self._file_batches:
                    raise ValueError(f"Batch {batch_id} not found")

                # Get batch files
                files = list(self._batch_files.get(batch_id, []))

            # Filter by status if requested
            if filter_status:
                files = [f for f in files if f.status == filter_status]

            # Sort by created_at
            reverse = order == "desc"
            files.sort(key=lambda x: x.created_at, reverse=reverse)

            # Apply cursor filtering
            if after:
                try:
                    after_index = next(
                        i for i, f in enumerate(files) if f.id == after)
                    files = files[after_index + 1:]
                except StopIteration:
                    files = []

            if before:
                try:
                    before_index = next(
                        i for i, f in enumerate(files) if f.id == before)
                    files = files[:before_index]
                except StopIteration:
                    pass

            # Apply limit
            has_more = len(files) > limit
            files = files[:limit]

            # Build response
            response = VectorStoreFileListResponse(
                object="list",
                data=files,
                first_id=files[0].id if files else None,
                last_id=files[-1].id if files else None,
                has_more=has_more,
            )

            # Track latency
            latency_ms = (time.time() - start_time) * 1000
            self.metrics_tracker.record_request(endpoint, latency_ms)

            return response

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error listing batch files: {e}")
            raise
