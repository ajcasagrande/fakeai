"""
Legacy completion models for the OpenAI API.

This module contains models for the legacy text completion endpoint,
which predates the chat completion API. Includes streaming support.
"""
#  SPDX-License-Identifier: Apache-2.0

from typing import Literal

from pydantic import BaseModel, Field

from ._base import Usage


class CompletionRequest(BaseModel):
    """Request for text completion."""

    model: str = Field(description="ID of the model to use.")
    prompt: str | list[str] | list[int] | list[list[int]] = Field(
        description="The prompt to generate completions for."
    )
    suffix: str | None = Field(
        default=None, description="The suffix that comes after a completion."
    )
    max_tokens: int | None = Field(
        default=16, ge=0, description="Maximum number of tokens to generate."
    )
    temperature: float | None = Field(
        default=1.0, ge=0, le=2, description="Sampling temperature."
    )
    top_p: float | None = Field(
        default=1.0, ge=0, le=1, description="Nucleus sampling parameter."
    )
    n: int | None = Field(
        default=1, ge=1, description="Number of completion choices to generate."
    )
    stream: bool | None = Field(
        default=False, description="Whether to stream responses."
    )
    logprobs: int | None = Field(
        default=None,
        ge=0,
        le=5,
        description="Include log probabilities on most likely tokens.",
    )
    echo: bool | None = Field(
        default=False, description="Echo the prompt in the completion."
    )
    stop: str | list[str] | None = Field(
        default=None,
        description="Sequences where the API will stop generating further tokens.",
    )
    presence_penalty: float | None = Field(
        default=0,
        ge=-2.0,
        le=2.0,
        description="Penalty for new tokens based on presence in text so far.",
    )
    frequency_penalty: float | None = Field(
        default=0,
        ge=-2.0,
        le=2.0,
        description="Penalty for new tokens based on frequency in text so far.",
    )
    best_of: int | None = Field(
        default=1,
        ge=1,
        description="Generate best_of completions server-side and return the best.",
    )
    logit_bias: dict[str, float] | None = Field(
        default=None,
        description="Modify the likelihood of specified tokens appearing in the completion.",
    )
    user: str | None = Field(
        default=None, description="A unique identifier for the end-user."
    )


class LogProbs(BaseModel):
    """Log probability information."""

    tokens: list[str] = Field(description="The tokens.")
    token_logprobs: list[float] = Field(
        description="The log probabilities of the tokens."
    )
    top_logprobs: list[dict[str, float]] | None = Field(
        default=None, description="The log probabilities of the most likely tokens."
    )
    text_offset: list[int] = Field(description="The text offsets of the tokens.")


class CompletionChoice(BaseModel):
    """A choice in completion results."""

    text: str = Field(description="The completed text.")
    index: int = Field(description="The index of this choice.")
    logprobs: LogProbs | None = Field(
        default=None, description="Log probability information."
    )
    finish_reason: str | None = Field(
        default=None, description="The reason why generation stopped."
    )
    token_timing: list[float] | None = Field(
        default=None, description="Timing information for token generation."
    )


class CompletionResponse(BaseModel):
    """Response for text completion."""

    id: str = Field(description="A unique identifier for this completion.")
    object: Literal["text_completion"] = Field(
        default="text_completion", description="The object type."
    )
    created: int = Field(
        description="The Unix timestamp of when this completion was created."
    )
    model: str = Field(description="The model used for completion.")
    choices: list[CompletionChoice] = Field(
        description="The list of completion choices."
    )
    usage: Usage = Field(description="Usage statistics.")


class CompletionChunk(BaseModel):
    """Streaming response for text completion."""

    id: str = Field(description="A unique identifier for this completion.")
    object: Literal["text_completion"] = Field(
        default="text_completion", description="The object type."
    )
    created: int = Field(
        description="The Unix timestamp of when this completion was created."
    )
    model: str = Field(description="The model used for completion.")
    choices: list[CompletionChoice] = Field(
        description="The list of completion choices."
    )
