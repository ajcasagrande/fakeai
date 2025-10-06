"""
Base Pydantic models for the OpenAI API.

This module contains foundational models used across the API including
model metadata, usage tracking, errors, and common enumerations.
"""

#  SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ModelPermission(BaseModel):
    """Model permissions."""

    id: str = Field(description="The ID of this model permission.")
    object: Literal["model_permission"] = Field(
        default="model_permission", description="The object type."
    )
    created: int = Field(description="Unix timestamp when this permission was created.")
    allow_create_engine: bool = Field(
        description="Whether the user can create engines with this model."
    )
    allow_sampling: bool = Field(
        description="Whether sampling is allowed on this model."
    )
    allow_logprobs: bool = Field(
        description="Whether logprobs is allowed on this model."
    )
    allow_search_indices: bool = Field(
        description="Whether search indices are allowed for this model."
    )
    allow_view: bool = Field(description="Whether the model can be viewed.")
    allow_fine_tuning: bool = Field(description="Whether the model can be fine-tuned.")
    organization: str = Field(description="The organization this permission is for.")
    group: str | None = Field(
        default=None, description="The group this permission is for."
    )
    is_blocking: bool = Field(description="Whether this permission is blocking.")


class ModelPricing(BaseModel):
    """Model pricing information per 1M tokens."""

    input_per_million: float = Field(
        description="Cost per 1 million input tokens in USD."
    )
    output_per_million: float = Field(
        description="Cost per 1 million output tokens in USD."
    )
    cached_input_per_million: float | None = Field(
        default=None, description="Cost per 1 million cached input tokens in USD."
    )


class Model(BaseModel):
    """OpenAI model information."""

    id: str = Field(description="The model identifier.")
    object: Literal["model"] = Field(default="model", description="The object type.")
    created: int = Field(description="Unix timestamp when this model was created.")
    owned_by: str = Field(description="Organization that owns the model.")
    permission: list[ModelPermission] = Field(
        description="List of permissions for this model."
    )
    root: str | None = Field(
        default=None, description="Root model from which this model was created."
    )
    parent: str | None = Field(
        default=None, description="Parent model from which this model was created."
    )
    context_window: int = Field(
        default=8192, description="Maximum context window size in tokens."
    )
    max_output_tokens: int = Field(
        default=4096, description="Maximum number of tokens that can be generated."
    )
    supports_vision: bool = Field(
        default=False, description="Whether the model supports vision/image inputs."
    )
    supports_audio: bool = Field(
        default=False, description="Whether the model supports audio inputs."
    )
    supports_tools: bool = Field(
        default=True, description="Whether the model supports function/tool calling."
    )
    training_cutoff: str | None = Field(
        default=None, description="Training data cutoff date (YYYY-MM format)."
    )
    pricing: ModelPricing | None = Field(
        default=None, description="Pricing information for the model."
    )


class ModelListResponse(BaseModel):
    """Response for listing available models."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[Model] = Field(description="List of model objects.")


class ModelCapabilitiesResponse(BaseModel):
    """Response for model capabilities endpoint."""

    id: str = Field(description="The model identifier.")
    object: Literal["model.capabilities"] = Field(
        default="model.capabilities", description="The object type."
    )
    context_window: int = Field(description="Maximum context window size in tokens.")
    max_output_tokens: int = Field(
        description="Maximum number of tokens that can be generated."
    )
    supports_vision: bool = Field(
        description="Whether the model supports vision/image inputs."
    )
    supports_audio: bool = Field(description="Whether the model supports audio inputs.")
    supports_tools: bool = Field(
        description="Whether the model supports function/tool calling."
    )
    training_cutoff: str | None = Field(
        description="Training data cutoff date (YYYY-MM format)."
    )
    pricing: ModelPricing | None = Field(
        description="Pricing information for the model."
    )


class PromptTokensDetails(BaseModel):
    """Breakdown of prompt tokens."""

    cached_tokens: int = Field(default=0, description="Number of cached tokens.")
    audio_tokens: int = Field(default=0, description="Number of audio tokens.")


class CompletionTokensDetails(BaseModel):
    """Breakdown of completion tokens."""

    reasoning_tokens: int = Field(default=0, description="Number of reasoning tokens.")
    audio_tokens: int = Field(default=0, description="Number of audio tokens.")
    accepted_prediction_tokens: int = Field(
        default=0, description="Number of accepted prediction tokens."
    )
    rejected_prediction_tokens: int = Field(
        default=0, description="Number of rejected prediction tokens."
    )


class Usage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = Field(description="Number of tokens used in the prompt.")
    completion_tokens: int | None = Field(
        default=None, description="Number of tokens used in the completion."
    )
    total_tokens: int = Field(description="Total number of tokens used.")
    prompt_tokens_details: PromptTokensDetails | None = Field(
        default=None, description="Breakdown of prompt tokens."
    )
    completion_tokens_details: CompletionTokensDetails | None = Field(
        default=None, description="Breakdown of completion tokens."
    )

    # For Responses API compatibility
    input_tokens: int | None = Field(
        default=None, description="Alias for prompt_tokens in Responses API."
    )
    output_tokens: int | None = Field(
        default=None, description="Alias for completion_tokens in Responses API."
    )


class ErrorDetail(BaseModel):
    """Error details."""

    message: str = Field(description="Error message.")
    type: str = Field(description="Error type.")
    param: str | None = Field(
        default=None, description="Parameter that caused the error."
    )
    code: str | None = Field(default=None, description="Error code.")


class ErrorResponse(BaseModel):
    """Error response."""

    error: ErrorDetail = Field(description="Error details.")


class Role(str, Enum):
    """Message role."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    FUNCTION = "function"


class AudioOutput(BaseModel):
    """Audio output in assistant message."""

    id: str = Field(description="Unique identifier for the audio output.")
    data: str = Field(description="Base64-encoded audio data.")
    transcript: str = Field(description="Text transcript of the audio.")
    expires_at: int = Field(description="Unix timestamp when the audio expires.")
