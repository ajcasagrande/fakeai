"""
Responses API models for the OpenAI API.

This module contains models for the Responses API, a stateful conversation
API introduced in March 2025 that simplifies message management.
"""
#  SPDX-License-Identifier: Apache-2.0

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field, Tag

from ._base import ErrorDetail, Role, Usage
from ._content import ContentPart
from .chat import JsonSchemaResponseFormat, Message, ResponseFormat, Tool, ToolChoice


class ResponsesInput(BaseModel):
    """Input for Responses API - can be string or message array."""

    pass  # Union type handled in request


class ResponsesRequest(BaseModel):
    """Request for OpenAI Responses API."""

    model: str = Field(description="ID of the model to use.")
    input: str | list[Message] = Field(
        description="Text or array of messages."
    )
    instructions: str | None = Field(
        default=None, description="System-level instructions."
    )
    tools: list[Tool] | None = Field(
        default=None, description="Tools the model may use."
    )
    previous_response_id: str | None = Field(
        default=None, description="ID of prior response to continue conversation.")
    max_output_tokens: int | None = Field(
        default=None, ge=0, description="Maximum tokens in output."
    )
    temperature: float | None = Field(
        default=None, ge=0, le=2, description="Sampling temperature."
    )
    top_p: float | None = Field(
        default=None, ge=0, le=1, description="Nucleus sampling parameter."
    )
    stream: bool | None = Field(
        default=False, description="Whether to stream via server-sent events."
    )
    store: bool | None = Field(
        default=False, description="Whether to store response for retrieval."
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Developer-defined tags (max 16 key-value pairs)."
    )
    parallel_tool_calls: bool | None = Field(
        default=True, description="Whether to allow parallel tool execution."
    )
    tool_choice: Literal["auto", "none", "required"] | ToolChoice | None = Field(
        default=None, description="Tool selection strategy.")
    response_format: ResponseFormat | JsonSchemaResponseFormat | None = Field(
        default=None, description="Output format specification."
    )
    background: bool | None = Field(
        default=False, description="Whether to run as background task."
    )


class ResponseMessageOutput(BaseModel):
    """Message output item in Responses API."""

    type: Literal["message"] = Field(
        default="message", description="Item type.")
    id: str = Field(description="Unique identifier.")
    status: Literal["queued", "in_progress", "completed", "failed"] = Field(
        description="Status of this output item."
    )
    role: Role = Field(description="Message role.")
    content: list[ContentPart] = Field(description="Message content parts.")


class ResponseFunctionCallOutput(BaseModel):
    """Function call output item in Responses API."""

    type: Literal["function_call"] = Field(
        default="function_call", description="Item type.")
    id: str = Field(description="Unique identifier.")
    status: Literal["queued", "in_progress", "completed", "failed"] = Field(
        description="Status of this output item."
    )
    call_id: str = Field(description="Tool call ID.")
    name: str = Field(description="Function name.")
    arguments: str = Field(description="Function arguments JSON string.")


# Discriminated union for response output items
ResponseOutputItem = Annotated[
    Union[
        Annotated[ResponseMessageOutput, Tag("message")],
        Annotated[ResponseFunctionCallOutput, Tag("function_call")],
    ],
    Field(discriminator="type"),
]


class ResponsesResponse(BaseModel):
    """Response from OpenAI Responses API."""

    id: str = Field(description="Unique identifier for response.")
    object: Literal["response"] = Field(
        default="response", description="Object type.")
    created_at: int = Field(description="Unix timestamp of creation.")
    model: str = Field(description="Model used.")
    status: Literal["queued",
                    "in_progress",
                    "completed",
                    "failed",
                    "cancelled",
                    "incomplete"] = Field(description="Response status.")
    error: ErrorDetail | None = Field(
        default=None, description="Error details if failed.")
    incomplete_details: dict[str, Any] | None = Field(
        default=None, description="Details about incompletion."
    )
    instructions: str | None = Field(
        default=None, description="Instructions used.")
    max_output_tokens: int | None = Field(
        default=None, description="Max tokens specified.")
    metadata: dict[str, str] | None = Field(
        default=None, description="Metadata.")
    previous_response_id: str | None = Field(
        default=None, description="Previous response ID."
    )
    temperature: float | None = Field(
        default=None, description="Temperature used.")
    top_p: float | None = Field(default=None, description="Top-p value used.")
    parallel_tool_calls: bool | None = Field(
        default=None, description="Parallel tool calls setting."
    )
    tool_choice: str | dict[str, Any] | None = Field(
        default=None, description="Tool choice used."
    )
    tools: list[Tool] | None = Field(default=None, description="Tools used.")
    output: list[ResponseOutputItem] = Field(
        description="Polymorphic output items array (discriminated by 'type' field).")
    usage: Usage | None = Field(default=None, description="Token usage.")
