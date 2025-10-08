"""
Batch service for FakeAI.

This module provides batch processing services including batch creation, lifecycle
management, background processing, and status tracking. It integrates with
FileManager for file operations, BatchMetricsTracker for monitoring, and delegates
to other services for actual request execution.
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import logging
import time
import uuid
from typing import TYPE_CHECKING, Any

from fakeai.batch_metrics import BatchMetricsTracker
from fakeai.config import AppConfig
from fakeai.file_manager import FileManager
from fakeai.metrics import MetricsTracker
from fakeai.models import (
    Batch,
    BatchListResponse,
    BatchOutputResponse,
    BatchRequestCounts,
    ChatCompletionRequest,
    CompletionRequest,
    CreateBatchRequest,
    EmbeddingRequest,
)
from fakeai.models_registry.registry import ModelRegistry

if TYPE_CHECKING:
    # Import for type checking only to avoid circular imports
    from fakeai.fakeai_service import FakeAIService

logger = logging.getLogger(__name__)


class BatchService:
    """
    Batch service for managing batch processing operations.

    Provides high-level batch operations including:
    - Batch creation with validation
    - Background async processing
    - State management (validating, in_progress, finalizing, completed, failed, cancelled)
    - Request count tracking
    - Error handling with error file generation
    - Output file creation (JSONL format)
    - Cancellation support
    - Integration with batch_metrics module

    Features:
    - Async background processing with asyncio tasks
    - State transitions with lifecycle timestamps
    - Request-level error tracking
    - JSONL input/output file format
    - Metrics tracking for all operations
    - Support for multiple endpoints (chat, embeddings, completions)
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
        model_registry: ModelRegistry,
        file_manager: FileManager,
        batch_metrics: BatchMetricsTracker,
    ):
        """
        Initialize batch service.

        Args:
            config: Application configuration
            metrics_tracker: Metrics tracker for monitoring
            model_registry: Model registry for model management
            file_manager: File manager for storage operations
            batch_metrics: Batch-specific metrics tracker
        """
        self.config = config
        self.metrics_tracker = metrics_tracker
        self.model_registry = model_registry
        self.file_manager = file_manager
        self.batch_metrics = batch_metrics

        # State management
        self.batches: dict[str, Batch] = {}
        self._processing_tasks: dict[str, asyncio.Task] = {}
        self._batch_file_contents: dict[str, str] = {}

        # Reference to parent service (set later to avoid circular dependency)
        self._parent_service: "FakeAIService | None" = None

        logger.info("BatchService initialized")

    def set_parent_service(self, parent_service: "FakeAIService") -> None:
        """
        Set reference to parent FakeAIService for delegating execution.

        Args:
            parent_service: Parent FakeAIService instance
        """
        self._parent_service = parent_service

    async def create_batch(self, request: CreateBatchRequest) -> Batch:
        """
        Create a new batch processing job.

        Args:
            request: Batch creation request with input file and endpoint

        Returns:
            Batch object with initial state

        Raises:
            ValueError: If input file not found or invalid endpoint
        """
        start_time = time.time()
        endpoint = "/v1/batches"

        try:
            # Validate input file exists
            input_file = await self.file_manager.get_file(request.input_file_id)
            if not input_file:
                raise ValueError(
                    f"Input file not found: {
                        request.input_file_id}")

            # Create batch object
            batch_id = f"batch_{uuid.uuid4().hex}"
            created_at = int(time.time())

            # Parse completion window (e.g., "24h")
            window_hours = int(request.completion_window.replace("h", ""))
            expires_at = created_at + (window_hours * 3600)

            batch = Batch(
                id=batch_id,
                endpoint=request.endpoint,
                input_file_id=request.input_file_id,
                completion_window=request.completion_window,
                status="validating",
                created_at=created_at,
                expires_at=expires_at,
                request_counts=BatchRequestCounts(
                    total=0,
                    completed=0,
                    failed=0),
                metadata=request.metadata,
            )

            # Store batch
            self.batches[batch_id] = batch

            # Start background processing
            task = asyncio.create_task(self._process_batch(batch_id))
            self._processing_tasks[batch_id] = task

            logger.info(
                f"Created batch {batch_id} for endpoint {
                    request.endpoint}")
            return batch

        except Exception as e:
            logger.error(f"Error creating batch: {e}")
            raise

    async def _process_batch(self, batch_id: str) -> None:
        """
        Background task to process a batch.

        This method runs asynchronously and handles the entire batch lifecycle:
        1. Validation phase
        2. Processing phase (execute all requests)
        3. Finalization phase (create output files)
        4. Completion or failure

        Args:
            batch_id: Unique identifier for the batch to process
        """
        try:
            batch = self.batches[batch_id]

            # Start batch metrics tracking
            self.batch_metrics.start_batch(
                batch_id, 0
            )  # Will update total after parsing

            # Simulate validation
            await asyncio.sleep(0.5)
            batch.status = "in_progress"
            batch.in_progress_at = int(time.time())

            # Record validation complete
            self.batch_metrics.record_validation_complete(batch_id)
            self.batch_metrics.record_processing_start(batch_id)

            # Read input file content
            file_content_bytes = await self.file_manager.get_file_content(
                batch.input_file_id
            )
            file_content = (file_content_bytes.decode(
                "utf-8") if file_content_bytes else "")

            # If no content stored, generate sample requests for testing
            if not file_content:
                file_content = self._generate_sample_batch_input(
                    batch.endpoint)
                # Store it for testing
                self._batch_file_contents[batch.input_file_id] = file_content

            # Parse JSONL input
            requests = []
            for line in file_content.strip().split("\n"):
                if line:
                    try:
                        req = json.loads(line)
                        requests.append(req)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in batch input: {line}")

            batch.request_counts.total = len(requests)

            # Process each request
            output_lines = []
            error_lines = []

            for idx, req_data in enumerate(requests):
                request_start_time = time.time()
                try:
                    # Execute the request
                    response = await self._execute_batch_request(
                        req_data, batch.endpoint
                    )

                    # Calculate latency and tokens
                    latency_ms = (time.time() - request_start_time) * 1000
                    tokens = response.get("usage", {}).get("total_tokens", 0)

                    # Create output response
                    output = BatchOutputResponse(
                        id=f"batch_req_{uuid.uuid4().hex}",
                        custom_id=req_data.get("custom_id", ""),
                        response=response,
                        error=None,
                    )
                    output_lines.append(output.model_dump_json())
                    batch.request_counts.completed += 1

                    # Record request metrics
                    self.batch_metrics.record_request_processed(
                        batch_id=batch_id,
                        request_num=idx,
                        latency_ms=latency_ms,
                        tokens=tokens,
                        success=True,
                    )

                except Exception as e:
                    # Calculate latency
                    latency_ms = (time.time() - request_start_time) * 1000

                    # Create error output
                    error_output = BatchOutputResponse(
                        id=f"batch_req_{uuid.uuid4().hex}",
                        custom_id=req_data.get("custom_id", ""),
                        response=None,
                        error={
                            "message": str(e),
                            "type": "invalid_request_error",
                            "code": "invalid_request",
                        },
                    )
                    error_lines.append(error_output.model_dump_json())
                    batch.request_counts.failed += 1

                    # Record error metrics
                    self.batch_metrics.record_request_processed(
                        batch_id=batch_id,
                        request_num=idx,
                        latency_ms=latency_ms,
                        tokens=0,
                        success=False,
                        error_type="invalid_request_error",
                    )
                    logger.error(f"Batch request failed: {e}")

                # Simulate processing delay
                await asyncio.sleep(0.05)

            # Record processing complete
            self.batch_metrics.record_processing_complete(batch_id)

            # Finalize batch
            batch.status = "finalizing"
            batch.finalizing_at = int(time.time())
            await asyncio.sleep(0.2)

            # Create output file
            output_content = "\n".join(output_lines)
            output_file = await self.file_manager.upload_file(
                file_content=output_content.encode("utf-8"),
                filename=f"{batch_id}_output.jsonl",
                purpose="user_data",
            )
            self._batch_file_contents[output_file.id] = output_content
            batch.output_file_id = output_file.id

            bytes_written = len(output_content)

            # Create error file if needed
            if error_lines:
                error_content = "\n".join(error_lines)
                error_file = await self.file_manager.upload_file(
                    file_content=error_content.encode("utf-8"),
                    filename=f"{batch_id}_errors.jsonl",
                    purpose="user_data",
                )
                self._batch_file_contents[error_file.id] = error_content
                batch.error_file_id = error_file.id
                bytes_written += len(error_content)

            # Record finalization complete
            self.batch_metrics.record_finalization_complete(batch_id)

            # Mark as completed
            batch.status = "completed"
            batch.completed_at = int(time.time())

            # Complete batch metrics
            bytes_read = len(file_content) if file_content else 0
            self.batch_metrics.complete_batch(
                batch_id=batch_id,
                bytes_written=bytes_written,
                bytes_read=bytes_read,
            )

            logger.info(
                f"Batch {batch_id} completed: {
                    batch.request_counts.completed} succeeded, " f"{
                    batch.request_counts.failed} failed")

        except asyncio.CancelledError:
            # Batch was cancelled
            batch = self.batches.get(batch_id)
            if batch:
                batch.status = "cancelled"
                batch.cancelled_at = int(time.time())
            logger.info(f"Batch {batch_id} was cancelled")
            raise

        except Exception as e:
            # Batch failed
            batch = self.batches.get(batch_id)
            if batch:
                batch.status = "failed"
                batch.failed_at = int(time.time())
                batch.errors = {"message": str(e), "type": "server_error"}

            # Record batch failure
            self.batch_metrics.fail_batch(batch_id, str(e))
            logger.exception(f"Batch {batch_id} failed: {e}")

    async def _execute_batch_request(
            self, req_data: dict, endpoint: str) -> dict:
        """
        Execute a single batch request and return the response as a dict.

        Args:
            req_data: Request data from JSONL input
            endpoint: Endpoint to execute against

        Returns:
            Response dictionary

        Raises:
            ValueError: If endpoint is not supported
            Exception: If request execution fails
        """
        if not self._parent_service:
            raise RuntimeError(
                "Parent service not set. Call set_parent_service() first."
            )

        body = req_data.get("body", {})

        if endpoint == "/v1/chat/completions":
            # Parse request
            request = ChatCompletionRequest(**body)
            # Execute via parent service
            response = await self._parent_service.create_chat_completion(request)
            return response.model_dump()

        elif endpoint == "/v1/embeddings":
            # Parse request
            request = EmbeddingRequest(**body)
            # Execute via parent service
            response = await self._parent_service.create_embedding(request)
            return response.model_dump()

        elif endpoint == "/v1/completions":
            # Parse request
            request = CompletionRequest(**body)
            # Execute via parent service
            response = await self._parent_service.create_completion(request)
            return response.model_dump()

        else:
            raise ValueError(f"Unsupported batch endpoint: {endpoint}")

    def _generate_sample_batch_input(self, endpoint: str) -> str:
        """
        Generate sample JSONL input for testing.

        Args:
            endpoint: Endpoint to generate sample input for

        Returns:
            JSONL string with sample requests
        """
        lines = []
        for i in range(5):
            if endpoint == "/v1/chat/completions":
                req = {
                    "custom_id": f"request-{i + 1}",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "meta-llama/Llama-3.1-8B-Instruct",
                        "messages": [{"role": "user", "content": f"Hello world {i + 1}"}],
                        "max_tokens": 50,
                    },
                }
            elif endpoint == "/v1/embeddings":
                req = {
                    "custom_id": f"request-{i + 1}",
                    "method": "POST",
                    "url": "/v1/embeddings",
                    "body": {
                        "model": "sentence-transformers/all-mpnet-base-v2",
                        "input": f"Sample text {i + 1}",
                    },
                }
            else:
                req = {
                    "custom_id": f"request-{i + 1}",
                    "method": "POST",
                    "url": endpoint,
                    "body": {},
                }
            lines.append(json.dumps(req))
        return "\n".join(lines)

    async def retrieve_batch(self, batch_id: str) -> Batch:
        """
        Retrieve a batch by ID.

        Args:
            batch_id: Batch identifier

        Returns:
            Batch object

        Raises:
            ValueError: If batch not found
        """
        start_time = time.time()
        endpoint = "/v1/batches"

        try:
            batch = self.batches.get(batch_id)
            if not batch:
                raise ValueError(f"Batch not found: {batch_id}")

            return batch

        except Exception as e:
            logger.error(f"Error retrieving batch {batch_id}: {e}")
            raise

    async def cancel_batch(self, batch_id: str) -> Batch:
        """
        Cancel a batch.

        Only batches in validating, in_progress, or finalizing states can be cancelled.

        Args:
            batch_id: Batch identifier

        Returns:
            Batch object with updated status

        Raises:
            ValueError: If batch not found
        """
        start_time = time.time()
        endpoint = "/v1/batches"

        try:
            batch = self.batches.get(batch_id)
            if not batch:
                raise ValueError(f"Batch not found: {batch_id}")

            # Only cancel if still in progress
            if batch.status in ["validating", "in_progress", "finalizing"]:
                batch.status = "cancelling"
                batch.cancelling_at = int(time.time())

                # Cancel the background task
                task = self._processing_tasks.get(batch_id)
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                batch.status = "cancelled"
                batch.cancelled_at = int(time.time())
                logger.info(f"Cancelled batch {batch_id}")

            return batch

        except Exception as e:
            logger.error(f"Error cancelling batch {batch_id}: {e}")
            raise

    async def list_batches(
        self,
        limit: int = 20,
        after: str | None = None,
    ) -> BatchListResponse:
        """
        List all batches with pagination.

        Args:
            limit: Maximum number of batches to return (default: 20)
            after: Cursor for pagination (batch ID)

        Returns:
            BatchListResponse with list of batches

        Raises:
            ValueError: If parameters are invalid
        """
        start_time = time.time()
        endpoint = "/v1/batches"

        try:
            # Validate parameters
            if limit < 1 or limit > 100:
                raise ValueError("Limit must be between 1 and 100")

            # Get all batches
            all_batches = list(self.batches.values())

            # Sort by created_at descending
            all_batches.sort(key=lambda b: b.created_at, reverse=True)

            # Apply pagination
            if after:
                # Find the batch with this ID and start after it
                try:
                    after_idx = next(
                        i for i, b in enumerate(all_batches) if b.id == after
                    )
                    all_batches = all_batches[after_idx + 1:]
                except StopIteration:
                    pass

            # Limit results
            batches = all_batches[:limit]
            has_more = len(all_batches) > limit

            first_id = batches[0].id if batches else None
            last_id = batches[-1].id if batches else None

            return BatchListResponse(
                data=batches,
                first_id=first_id,
                last_id=last_id,
                has_more=has_more,
            )

        except Exception as e:
            logger.error(f"Error listing batches: {e}")
            raise

    def get_batch_file_content(self, file_id: str) -> str | None:
        """
        Get batch file content by file ID.

        Args:
            file_id: File identifier

        Returns:
            File content as string, or None if not found
        """
        return self._batch_file_contents.get(file_id)

    def get_batch_stats(self, batch_id: str) -> dict[str, Any] | None:
        """
        Get statistics for a specific batch.

        Args:
            batch_id: Batch identifier

        Returns:
            Dictionary containing batch statistics, or None if not found
        """
        return self.batch_metrics.get_batch_stats(batch_id)

    def get_all_batches_stats(self) -> dict[str, Any]:
        """
        Get aggregate statistics for all batches.

        Returns:
            Dictionary containing aggregate statistics across all batches
        """
        return self.batch_metrics.get_all_batches_stats()
