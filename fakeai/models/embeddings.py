"""
Embedding-related Pydantic models for the OpenAI API.

This module contains models for embeddings requests, responses, and usage tracking.
Embeddings convert text into dense vector representations for semantic search,
clustering, and similarity tasks.
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Literal

from pydantic import BaseModel, Field

from ._base import Usage


class EmbeddingRequest(BaseModel):
    """Request for embeddings."""

    model: str = Field(description="ID of the model to use.")
    input: str | list[str] | list[int] | list[list[int]] = Field(
        description="The input text to get embeddings for."
    )
    user: str | None = Field(
        default=None, description="A unique identifier for the end-user."
    )
    encoding_format: Literal["float", "base64"] | None = Field(
        default="float", description="The format of the embeddings."
    )
    dimensions: int | None = Field(
        default=None, description="The number of dimensions to use for the embeddings."
    )


class Embedding(BaseModel):
    """An embedding result."""

    object: Literal["embedding"] = Field(
        default="embedding", description="The object type."
    )
    embedding: list[float] = Field(description="The embedding vector.")
    index: int = Field(description="The index of the embedding.")


class EmbeddingResponse(BaseModel):
    """Response for embeddings."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[Embedding] = Field(description="The list of embedding objects.")
    model: str = Field(description="The model used for embeddings.")
    usage: Usage = Field(description="Usage statistics.")


class EmbeddingsUsageResponse(BaseModel):
    """Response for embeddings usage data."""

    object: Literal["page"] = Field(default="page", description="The object type.")
    data: list = Field(description="List of usage buckets.")
    has_more: bool = Field(default=False, description="Whether there are more results.")
    next_page: str | None = Field(default=None, description="URL for next page.")
