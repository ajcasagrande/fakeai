"""
NVIDIA NIM rankings API models.

This module contains models for the NVIDIA NIM reranking API which provides
semantic relevance scoring for information retrieval and search applications.
"""
#  SPDX-License-Identifier: Apache-2.0

from typing import Any, Literal

from pydantic import BaseModel, Field

from ._base import Usage
from ._content import RagDocument


class RankingQuery(BaseModel):
    """Query object for rankings."""

    text: str = Field(description="The search query text.")


class RankingPassage(BaseModel):
    """Passage object for rankings."""

    text: str = Field(description="The passage text content.")


class RankingRequest(BaseModel):
    """Request for NVIDIA NIM rankings."""

    model: str = Field(description="Reranking model identifier.")
    query: RankingQuery = Field(description="Query to rank against.")
    passages: list[RankingPassage] = Field(
        description="Array of passages to rank (max 512)."
    )
    truncate: Literal["NONE", "END"] | None = Field(
        default="NONE", description="Truncation strategy for long sequences."
    )


class RankingObject(BaseModel):
    """Ranking result object."""

    index: int = Field(
        description="Zero-based index of passage in original request.")
    logit: float = Field(
        description="Raw unnormalized relevance score (higher is better).")


class RankingResponse(BaseModel):
    """Response from NVIDIA NIM rankings."""

    rankings: list[RankingObject] = Field(
        description="Array of rankings sorted by logit descending."
    )


class SolidoRagRequest(BaseModel):
    """Request for Solido RAG endpoint (/rag/api/prompt)."""

    query: str | list[str] = Field(
        description="Query text for retrieval (string or array of strings)."
    )
    filters: dict[str, Any] | None = Field(
        default=None,
        description="Metadata filters for document retrieval (e.g. {'family': 'Solido', 'tool': 'SDE'}).",
    )
    inference_model: str = Field(
        default="meta-llama/Llama-3.1-70B-Instruct",
        description="Model to use for generation."
    )
    top_k: int | None = Field(
        default=5, description="Number of documents to retrieve.", ge=1, le=20
    )
    stream: bool | None = Field(
        default=False, description="Whether to stream the response."
    )


class SolidoRagResponse(BaseModel):
    """Response for Solido RAG endpoint."""

    content: str = Field(description="Generated content with RAG context.")
    retrieved_docs: list[RagDocument] | None = Field(
        default=None, description="Retrieved documents (if requested)."
    )
    usage: Usage | None = Field(
        default=None, description="Token usage information."
    )
