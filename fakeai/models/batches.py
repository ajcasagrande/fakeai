"""
Batch processing models for FakeAI.

This module contains Pydantic models for OpenAI-compatible batch processing:
- CreateBatchRequest: Request to create a new batch
- Batch: Main batch object with lifecycle states
- BatchRequest: Single request in a batch JSONL file
- BatchRequestCounts: Counts of batch requests by status
- BatchListResponse: Response for listing batches
- BatchOutputResponse: Single response in a batch output JSONL file

Batch Lifecycle States:
- validating: Validating the input file
- failed: Validation or processing failed
- in_progress: Processing requests
- finalizing: Creating output files
- completed: Successfully completed
- expired: Batch expired before completion
- cancelling: Cancellation in progress
- cancelled: Successfully cancelled
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any, Literal

from pydantic import BaseModel, Field


class BatchRequestCounts(BaseModel):
    """Counts of batch requests by status."""

    total: int = Field(description="Total number of requests in the batch.")
    completed: int = Field(default=0, description="Number of requests completed.")
    failed: int = Field(default=0, description="Number of requests that failed.")


class Batch(BaseModel):
    """Batch object representing a batch processing job."""

    id: str = Field(description="The batch identifier.")
    object: Literal["batch"] = Field(default="batch", description="The object type.")
    endpoint: str = Field(
        description="The API endpoint used (e.g., /v1/chat/completions)."
    )
    errors: dict[str, Any] | None = Field(
        default=None, description="Error information if the batch failed."
    )
    input_file_id: str = Field(description="The ID of the input file for the batch.")
    completion_window: str = Field(
        description="The time window for completion (e.g., '24h')."
    )
    status: Literal[
        "validating",
        "failed",
        "in_progress",
        "finalizing",
        "completed",
        "expired",
        "cancelling",
        "cancelled",
    ] = Field(description="The current status of the batch.")
    output_file_id: str | None = Field(
        default=None, description="The ID of the output file (once completed)."
    )
    error_file_id: str | None = Field(
        default=None, description="The ID of the error file (if errors occurred)."
    )
    created_at: int = Field(description="Unix timestamp when the batch was created.")
    in_progress_at: int | None = Field(
        default=None, description="Unix timestamp when batch processing started."
    )
    expires_at: int | None = Field(
        default=None, description="Unix timestamp when the batch will expire."
    )
    finalizing_at: int | None = Field(
        default=None, description="Unix timestamp when batch finalization started."
    )
    completed_at: int | None = Field(
        default=None, description="Unix timestamp when the batch completed."
    )
    failed_at: int | None = Field(
        default=None, description="Unix timestamp when the batch failed."
    )
    expired_at: int | None = Field(
        default=None, description="Unix timestamp when the batch expired."
    )
    cancelling_at: int | None = Field(
        default=None, description="Unix timestamp when cancellation started."
    )
    cancelled_at: int | None = Field(
        default=None, description="Unix timestamp when the batch was cancelled."
    )
    request_counts: BatchRequestCounts = Field(
        description="Counts of requests by status."
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Developer-provided metadata."
    )


class CreateBatchRequest(BaseModel):
    """Request to create a new batch."""

    input_file_id: str = Field(description="The ID of the input file (JSONL format).")
    endpoint: str = Field(
        description="The API endpoint to call (e.g., /v1/chat/completions)."
    )
    completion_window: str = Field(
        description="Time window for completion (e.g., '24h')."
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Optional developer metadata."
    )


class BatchListResponse(BaseModel):
    """Response for listing batches."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[Batch] = Field(description="List of batch objects.")
    first_id: str | None = Field(default=None, description="ID of the first batch.")
    last_id: str | None = Field(default=None, description="ID of the last batch.")
    has_more: bool = Field(default=False, description="Whether there are more batches.")


class BatchRequest(BaseModel):
    """Single request in a batch JSONL file."""

    custom_id: str = Field(description="Developer-provided ID for this request.")
    method: Literal["POST"] = Field(description="HTTP method (always POST).")
    url: str = Field(description="The API endpoint URL (e.g., /v1/chat/completions).")
    body: dict[str, Any] = Field(description="The request body.")


class BatchOutputResponse(BaseModel):
    """Single response in a batch output JSONL file."""

    id: str = Field(description="Unique ID for this response.")
    custom_id: str = Field(description="The custom_id from the request.")
    response: dict[str, Any] | None = Field(
        default=None, description="The API response (if successful)."
    )
    error: dict[str, Any] | None = Field(
        default=None, description="Error information (if failed)."
    )


__all__ = [
    "BatchRequestCounts",
    "Batch",
    "CreateBatchRequest",
    "BatchListResponse",
    "BatchRequest",
    "BatchOutputResponse",
]
