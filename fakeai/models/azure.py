"""
Azure compatibility models for the OpenAI API.

This module contains models for Azure-specific endpoints that provide
compatibility with Azure OpenAI Service.
"""
#  SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field

from ._base import Usage


class TextGenerationRequest(BaseModel):
    """Request for text generation (Azure API)."""

    input: str = Field(description="The input text to generate from.")
    model: str = Field(description="ID of the model to use.")
    max_output_tokens: int | None = Field(
        default=100, description="The maximum number of tokens to generate."
    )
    temperature: float | None = Field(
        default=1.0, ge=0, le=2, description="The temperature to use for sampling."
    )
    top_p: float | None = Field(
        default=0.95, ge=0, le=1, description="Top-p sampling parameter."
    )
    stop: list[str] | None = Field(
        default=None, description="A list of tokens at which to stop generation."
    )
    user: str | None = Field(
        default=None, description="A unique identifier for the end-user."
    )


class TextGenerationResponse(BaseModel):
    """Response for text generation (Azure API)."""

    id: str = Field(description="A unique identifier for this text generation.")
    created: int = Field(
        description="The Unix timestamp of when this text generation was created."
    )
    output: str = Field(description="The generated text.")
    usage: Usage = Field(description="Usage statistics.")
    model: str = Field(description="The model used for text generation.")
