"""
Usage and billing models for the OpenAI API.

This module contains models for tracking API usage, costs, and billing
across different services (completions, embeddings, images, audio, RAG).
"""
#  SPDX-License-Identifier: Apache-2.0

from typing import Literal

from pydantic import BaseModel, Field


class UsageTimeBucket(BaseModel):
    """Time bucket for usage aggregation."""

    object: Literal["bucket"] = Field(default="bucket", description="The object type.")
    start_time: int = Field(description="Unix timestamp for start of bucket.")
    end_time: int = Field(description="Unix timestamp for end of bucket.")


class UsageResultItem(BaseModel):
    """Individual usage result item."""

    object: Literal["organization.usage.result"] = Field(
        default="organization.usage.result", description="The object type."
    )
    input_tokens: int = Field(default=0, description="Number of input tokens.")
    output_tokens: int = Field(default=0, description="Number of output tokens.")
    input_cached_tokens: int = Field(default=0, description="Number of cached input tokens.")
    num_model_requests: int = Field(default=0, description="Number of requests.")


class UsageAggregationBucket(BaseModel):
    """Usage aggregated by time bucket."""

    object: Literal["bucket"] = Field(default="bucket", description="The object type.")
    start_time: int = Field(description="Unix timestamp for start of bucket.")
    end_time: int = Field(description="Unix timestamp for end of bucket.")
    results: list[UsageResultItem] = Field(description="Usage results for this time bucket.")


class CompletionsUsageResponse(BaseModel):
    """Response for completions usage data."""

    object: Literal["page"] = Field(default="page", description="The object type.")
    data: list[UsageAggregationBucket] = Field(description="List of usage buckets.")
    has_more: bool = Field(default=False, description="Whether there are more results.")
    next_page: str | None = Field(default=None, description="URL for next page.")


class EmbeddingsUsageResponse(BaseModel):
    """Response for embeddings usage data."""

    object: Literal["page"] = Field(default="page", description="The object type.")
    data: list[UsageAggregationBucket] = Field(description="List of usage buckets.")
    has_more: bool = Field(default=False, description="Whether there are more results.")
    next_page: str | None = Field(default=None, description="URL for next page.")


class ImagesUsageResponse(BaseModel):
    """Response for images usage data."""

    object: Literal["page"] = Field(default="page", description="The object type.")
    data: list[UsageAggregationBucket] = Field(description="List of usage buckets.")
    has_more: bool = Field(default=False, description="Whether there are more results.")
    next_page: str | None = Field(default=None, description="URL for next page.")


class AudioSpeechesUsageResponse(BaseModel):
    """Response for audio speeches usage data."""

    object: Literal["page"] = Field(default="page", description="The object type.")
    data: list[UsageAggregationBucket] = Field(description="List of usage buckets.")
    has_more: bool = Field(default=False, description="Whether there are more results.")
    next_page: str | None = Field(default=None, description="URL for next page.")


class AudioTranscriptionsUsageResponse(BaseModel):
    """Response for audio transcriptions usage data."""

    object: Literal["page"] = Field(default="page", description="The object type.")
    data: list[UsageAggregationBucket] = Field(description="List of usage buckets.")
    has_more: bool = Field(default=False, description="Whether there are more results.")
    next_page: str | None = Field(default=None, description="URL for next page.")


class CostAmount(BaseModel):
    """Cost amount in USD."""

    value: float = Field(description="Cost value in USD.")
    currency: Literal["usd"] = Field(default="usd", description="Currency code.")


class CostResult(BaseModel):
    """Cost result with details."""

    object: Literal["organization.costs.result"] = Field(
        default="organization.costs.result", description="The object type."
    )
    amount: CostAmount = Field(description="Total cost amount.")
    line_item: str = Field(
        description="Line item category (e.g., 'completions', 'embeddings')."
    )
    project_id: str | None = Field(
        default=None, description="Project ID if applicable."
    )


class CostBucket(BaseModel):
    """Cost aggregated by time bucket."""

    object: Literal["bucket"] = Field(default="bucket", description="The object type.")
    start_time: int = Field(description="Unix timestamp for start of bucket.")
    end_time: int = Field(description="Unix timestamp for end of bucket.")
    results: list[CostResult] = Field(description="Cost results for this time bucket.")


class CostsResponse(BaseModel):
    """Response for costs data."""

    object: Literal["page"] = Field(default="page", description="The object type.")
    data: list[CostBucket] = Field(description="List of cost buckets.")
    has_more: bool = Field(default=False, description="Whether there are more results.")
    next_page: str | None = Field(default=None, description="URL for next page.")
