"""
Vector store models for the OpenAI API.

This module contains models for vector stores used in the Assistants API
for semantic search and retrieval-augmented generation (RAG).
"""
#  SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChunkingStrategyType(str, Enum):
    """Available chunking strategies for vector stores."""

    AUTO = "auto"
    STATIC = "static"


class StaticChunkingStrategy(BaseModel):
    """Static chunking strategy configuration."""

    type: Literal["static"] = Field(
        default="static", description="The chunking strategy type."
    )
    max_chunk_size_tokens: int = Field(
        description="Maximum number of tokens in each chunk.",
        ge=100,
        le=4096,
    )
    chunk_overlap_tokens: int = Field(
        description="Number of tokens that overlap between chunks.",
        ge=0,
    )


class AutoChunkingStrategy(BaseModel):
    """Auto chunking strategy (default)."""

    type: Literal["auto"] = Field(
        default="auto", description="The chunking strategy type."
    )


ChunkingStrategy = StaticChunkingStrategy | AutoChunkingStrategy


class FileCounts(BaseModel):
    """Counts of files in various states in a vector store."""

    in_progress: int = Field(
        default=0, description="Number of files currently being processed."
    )
    completed: int = Field(
        default=0,
        description="Number of files successfully processed.")
    failed: int = Field(
        default=0,
        description="Number of files that failed processing.")
    cancelled: int = Field(
        default=0,
        description="Number of files that were cancelled.")
    total: int = Field(default=0, description="Total number of files.")


class ExpiresAfter(BaseModel):
    """Expiration policy for a vector store."""

    anchor: Literal["last_active_at"] = Field(
        description="Anchor timestamp for expiration (e.g., 'last_active_at')."
    )
    days: int = Field(
        description="Number of days after anchor before expiration.",
        ge=1,
        le=365)


class RankingOptions(BaseModel):
    """Ranking options for search results."""

    ranker: Literal["auto", "default_2024_08_21"] = Field(
        default="auto",
        description="The ranker to use for search results.",
    )
    score_threshold: float = Field(
        description="Minimum similarity score for results.",
        ge=0.0,
        le=1.0,
    )


class VectorStore(BaseModel):
    """Vector store object for semantic search."""

    id: str = Field(description="The vector store identifier.")
    object: Literal["vector_store"] = Field(
        default="vector_store", description="The object type."
    )
    created_at: int = Field(
        description="Unix timestamp when the vector store was created."
    )
    name: str = Field(description="The name of the vector store.")
    usage_bytes: int = Field(
        default=0,
        description="Total size of files in the vector store in bytes.")
    file_counts: FileCounts = Field(
        default_factory=FileCounts, description="File counts by status."
    )
    status: Literal["expired", "in_progress", "completed"] = Field(
        description="The status of the vector store."
    )
    expires_after: ExpiresAfter | None = Field(
        default=None, description="Expiration policy for the vector store."
    )
    expires_at: int | None = Field(
        default=None,
        description="Unix timestamp when the vector store will expire.")
    last_active_at: int | None = Field(
        default=None, description="Unix timestamp of last activity."
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Developer-provided metadata."
    )


class CreateVectorStoreRequest(BaseModel):
    """Request to create a new vector store."""

    file_ids: list[str] | None = Field(
        default=None, description="List of file IDs to add to the vector store.")
    name: str = Field(description="The name of the vector store.")
    expires_after: ExpiresAfter | None = Field(
        default=None, description="Expiration policy for the vector store."
    )
    chunking_strategy: ChunkingStrategy | None = Field(
        default=None, description="Chunking strategy for the vector store."
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Developer-provided metadata."
    )


class ModifyVectorStoreRequest(BaseModel):
    """Request to modify an existing vector store."""

    name: str | None = Field(default=None, description="Updated name.")
    expires_after: ExpiresAfter | None = Field(
        default=None, description="Updated expiration policy."
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Updated metadata."
    )


class VectorStoreListResponse(BaseModel):
    """Response for listing vector stores."""

    object: Literal["list"] = Field(
        default="list", description="The object type.")
    data: list[VectorStore] = Field(
        description="List of vector store objects.")
    first_id: str | None = Field(default=None,
                                 description="ID of the first vector store.")
    last_id: str | None = Field(default=None,
                                description="ID of the last vector store.")
    has_more: bool = Field(
        default=False, description="Whether there are more vector stores."
    )


class VectorStoreFile(BaseModel):
    """File attached to a vector store."""

    id: str = Field(description="The vector store file identifier.")
    object: Literal["vector_store.file"] = Field(
        default="vector_store.file", description="The object type."
    )
    usage_bytes: int = Field(
        default=0, description="Size of the file in bytes after processing."
    )
    created_at: int = Field(
        description="Unix timestamp when the file was added to the vector store.")
    vector_store_id: str = Field(
        description="The ID of the vector store this file belongs to."
    )
    status: Literal["in_progress", "completed", "cancelled", "failed"] = Field(
        description="The status of the file in the vector store."
    )
    last_error: dict[str, Any] | None = Field(
        default=None, description="Error information if processing failed."
    )
    chunking_strategy: ChunkingStrategy | None = Field(
        default=None, description="The chunking strategy used for this file."
    )


class CreateVectorStoreFileRequest(BaseModel):
    """Request to add a file to a vector store."""

    file_id: str = Field(description="The ID of the file to add.")
    chunking_strategy: ChunkingStrategy | None = Field(
        default=None, description="Chunking strategy for this file."
    )


class VectorStoreFileListResponse(BaseModel):
    """Response for listing vector store files."""

    object: Literal["list"] = Field(
        default="list", description="The object type.")
    data: list[VectorStoreFile] = Field(
        description="List of vector store file objects.")
    first_id: str | None = Field(
        default=None,
        description="ID of the first file.")
    last_id: str | None = Field(
        default=None,
        description="ID of the last file.")
    has_more: bool = Field(
        default=False,
        description="Whether there are more files.")


class VectorStoreFileBatch(BaseModel):
    """Batch of files being added to a vector store."""

    id: str = Field(description="The file batch identifier.")
    object: Literal["vector_store.files_batch"] = Field(
        default="vector_store.files_batch", description="The object type."
    )
    created_at: int = Field(
        description="Unix timestamp when the batch was created."
    )
    vector_store_id: str = Field(
        description="The ID of the vector store."
    )
    status: Literal["in_progress", "completed", "cancelled", "failed"] = Field(
        description="The status of the file batch."
    )
    file_counts: FileCounts = Field(
        description="File counts by status in the batch."
    )


class CreateVectorStoreFileBatchRequest(BaseModel):
    """Request to create a batch of files in a vector store."""

    file_ids: list[str] = Field(
        description="List of file IDs to add to the vector store."
    )
    chunking_strategy: ChunkingStrategy | None = Field(
        default=None, description="Chunking strategy for the files."
    )
