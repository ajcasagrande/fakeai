"""
Assistants API models for the OpenAI API.

This module contains models for the Assistants API including assistants,
threads, messages, runs, and run steps for building AI agent applications.
"""
#  SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from ._base import Usage


class AssistantToolResources(BaseModel):
    """Tool resources for an assistant (code interpreter, file search)."""

    code_interpreter: dict[str, Any] | None = Field(
        default=None, description="Code interpreter resources."
    )
    file_search: dict[str, Any] | None = Field(
        default=None, description="File search resources."
    )


class Assistant(BaseModel):
    """OpenAI Assistant object."""

    id: str = Field(description="The assistant ID.")
    object: Literal["assistant"] = Field(
        default="assistant", description="Object type."
    )
    created_at: int = Field(description="Unix timestamp of creation.")
    name: str | None = Field(
        default=None, max_length=256, description="The name of the assistant."
    )
    description: str | None = Field(
        default=None,
        max_length=512,
        description="The description of the assistant.")
    model: str = Field(description="Model used by the assistant.")
    instructions: str | None = Field(
        default=None,
        max_length=256000,
        description="System instructions for the assistant.",
    )
    tools: list[dict[str, Any]] = Field(
        default_factory=list,
        max_length=128,
        description="Tools enabled for the assistant.",
    )
    tool_resources: AssistantToolResources | None = Field(
        default=None, description="Resources for tools."
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="User-defined metadata (max 16 key-value pairs).",
    )
    temperature: float | None = Field(
        default=1.0, ge=0.0, le=2.0, description="Sampling temperature."
    )
    top_p: float | None = Field(
        default=1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter."
    )
    response_format: str | dict[str, Any] | None = Field(
        default="auto",
        description="Response format (auto, text, json_object, json_schema).",
    )

    @field_validator("name")
    @classmethod
    def validate_name_length(cls, v: str | None) -> str | None:
        """Validate name length."""
        if v is not None and len(v) > 256:
            raise ValueError("Name must not exceed 256 characters")
        return v

    @field_validator("description")
    @classmethod
    def validate_description_length(cls, v: str | None) -> str | None:
        """Validate description length."""
        if v is not None and len(v) > 512:
            raise ValueError("Description must not exceed 512 characters")
        return v

    @field_validator("instructions")
    @classmethod
    def validate_instructions_length(cls, v: str | None) -> str | None:
        """Validate instructions length."""
        if v is not None and len(v) > 256000:
            raise ValueError("Instructions must not exceed 256000 characters")
        return v

    @field_validator("tools")
    @classmethod
    def validate_tools_length(
            cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate tools list length."""
        if len(v) > 128:
            raise ValueError("Tools list must not exceed 128 items")
        return v


class CreateAssistantRequest(BaseModel):
    """Request to create an assistant."""

    model: str = Field(description="Model ID to use.")
    name: str | None = Field(
        default=None, max_length=256, description="Name of the assistant."
    )
    description: str | None = Field(
        default=None,
        max_length=512,
        description="Description of the assistant.")
    instructions: str | None = Field(
        default=None, max_length=256000, description="System instructions."
    )
    tools: list[dict[str, Any]] = Field(
        default_factory=list, max_length=128, description="Tools to enable."
    )
    tool_resources: AssistantToolResources | None = Field(
        default=None, description="Tool resources."
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Metadata (max 16 pairs)."
    )
    temperature: float | None = Field(
        default=1.0, ge=0.0, le=2.0, description="Sampling temperature."
    )
    top_p: float | None = Field(
        default=1.0, ge=0.0, le=1.0, description="Nucleus sampling."
    )
    response_format: str | dict[str, Any] | None = Field(
        default="auto", description="Response format."
    )

    @field_validator("name")
    @classmethod
    def validate_name_length(cls, v: str | None) -> str | None:
        """Validate name length."""
        if v is not None and len(v) > 256:
            raise ValueError("Name must not exceed 256 characters")
        return v

    @field_validator("description")
    @classmethod
    def validate_description_length(cls, v: str | None) -> str | None:
        """Validate description length."""
        if v is not None and len(v) > 512:
            raise ValueError("Description must not exceed 512 characters")
        return v

    @field_validator("instructions")
    @classmethod
    def validate_instructions_length(cls, v: str | None) -> str | None:
        """Validate instructions length."""
        if v is not None and len(v) > 256000:
            raise ValueError("Instructions must not exceed 256000 characters")
        return v

    @field_validator("tools")
    @classmethod
    def validate_tools_length(
            cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate tools list length."""
        if len(v) > 128:
            raise ValueError("Tools list must not exceed 128 items")
        return v


class ModifyAssistantRequest(BaseModel):
    """Request to modify an assistant."""

    model: str | None = Field(default=None, description="Model ID.")
    name: str | None = Field(default=None, max_length=256, description="Name.")
    description: str | None = Field(
        default=None, max_length=512, description="Description."
    )
    instructions: str | None = Field(
        default=None, max_length=256000, description="Instructions."
    )
    tools: list[dict[str, Any]] | None = Field(
        default=None, max_length=128, description="Tools."
    )
    tool_resources: AssistantToolResources | None = Field(
        default=None, description="Tool resources."
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Metadata.")
    temperature: float | None = Field(
        default=None, ge=0.0, le=2.0, description="Temperature."
    )
    top_p: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Top-p.")
    response_format: str | dict[str, Any] | None = Field(
        default=None, description="Response format."
    )

    @field_validator("name")
    @classmethod
    def validate_name_length(cls, v: str | None) -> str | None:
        """Validate name length."""
        if v is not None and len(v) > 256:
            raise ValueError("Name must not exceed 256 characters")
        return v

    @field_validator("description")
    @classmethod
    def validate_description_length(cls, v: str | None) -> str | None:
        """Validate description length."""
        if v is not None and len(v) > 512:
            raise ValueError("Description must not exceed 512 characters")
        return v

    @field_validator("instructions")
    @classmethod
    def validate_instructions_length(cls, v: str | None) -> str | None:
        """Validate instructions length."""
        if v is not None and len(v) > 256000:
            raise ValueError("Instructions must not exceed 256000 characters")
        return v

    @field_validator("tools")
    @classmethod
    def validate_tools_length(
            cls, v: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        """Validate tools list length."""
        if v is not None and len(v) > 128:
            raise ValueError("Tools list must not exceed 128 items")
        return v


class AssistantList(BaseModel):
    """List of assistants."""

    object: Literal["list"] = Field(default="list", description="Object type.")
    data: list[Assistant] = Field(description="List of assistant objects.")
    first_id: str | None = Field(
        default=None, description="First assistant ID.")
    last_id: str | None = Field(default=None, description="Last assistant ID.")
    has_more: bool = Field(
        default=False,
        description="Whether there are more results.")


class Thread(BaseModel):
    """OpenAI Thread object."""

    id: str = Field(description="The thread ID.")
    object: Literal["thread"] = Field(
        default="thread", description="Object type.")
    created_at: int = Field(description="Unix timestamp of creation.")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="User-defined metadata."
    )
    tool_resources: AssistantToolResources | None = Field(
        default=None, description="Tool resources for the thread."
    )


class CreateThreadRequest(BaseModel):
    """Request to create a thread."""

    messages: list[dict[str, Any]] = Field(
        default_factory=list, description="Initial messages for the thread."
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Metadata (max 16 pairs)."
    )
    tool_resources: AssistantToolResources | None = Field(
        default=None, description="Tool resources."
    )


class ModifyThreadRequest(BaseModel):
    """Request to modify a thread."""

    metadata: dict[str, str] | None = Field(
        default=None, description="Metadata.")
    tool_resources: AssistantToolResources | None = Field(
        default=None, description="Tool resources."
    )


class ThreadMessage(BaseModel):
    """Message in a thread (Assistants API)."""

    id: str = Field(description="Message ID.")
    object: Literal["thread.message"] = Field(
        default="thread.message", description="Object type."
    )
    created_at: int = Field(description="Unix timestamp of creation.")
    thread_id: str = Field(description="Thread ID this message belongs to.")
    role: Literal["user", "assistant"] = Field(description="Message role.")
    content: list[dict[str, Any]] = Field(description="Message content array.")
    assistant_id: str | None = Field(
        default=None, description="Assistant ID if role is assistant."
    )
    run_id: str | None = Field(default=None,
                               description="Run ID if created by a run.")
    attachments: list[dict[str, Any]] | None = Field(
        default=None, description="File attachments."
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="User-defined metadata."
    )


class CreateMessageRequest(BaseModel):
    """Request to create a message in a thread."""

    role: Literal["user", "assistant"] = Field(description="Message role.")
    content: str | list[dict[str, Any]] = Field(description="Message content.")
    attachments: list[dict[str, Any]] | None = Field(
        default=None, description="File attachments."
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Metadata (max 16 pairs)."
    )


class MessageList(BaseModel):
    """List of thread messages."""

    object: Literal["list"] = Field(default="list", description="Object type.")
    data: list[ThreadMessage] = Field(description="List of message objects.")
    first_id: str | None = Field(default=None, description="First message ID.")
    last_id: str | None = Field(default=None, description="Last message ID.")
    has_more: bool = Field(
        default=False,
        description="Whether there are more results.")


class RunStatus(str, Enum):
    """Run status values."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    REQUIRES_ACTION = "requires_action"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"
    INCOMPLETE = "incomplete"
    EXPIRED = "expired"


class Run(BaseModel):
    """OpenAI Run object."""

    id: str = Field(description="Run ID.")
    object: Literal["thread.run"] = Field(
        default="thread.run", description="Object type."
    )
    created_at: int = Field(description="Unix timestamp of creation.")
    thread_id: str = Field(description="Thread ID.")
    assistant_id: str = Field(description="Assistant ID.")
    status: RunStatus = Field(description="Run status.")
    required_action: dict[str, Any] | None = Field(
        default=None,
        description="Required action details if status is requires_action.",
    )
    last_error: dict[str, Any] | None = Field(
        default=None, description="Last error details if status is failed."
    )
    expires_at: int | None = Field(
        default=None, description="Unix timestamp when run expires."
    )
    started_at: int | None = Field(
        default=None, description="Unix timestamp when run started."
    )
    cancelled_at: int | None = Field(
        default=None, description="Unix timestamp when run was cancelled."
    )
    failed_at: int | None = Field(
        default=None, description="Unix timestamp when run failed."
    )
    completed_at: int | None = Field(
        default=None, description="Unix timestamp when run completed."
    )
    incomplete_details: dict[str, Any] | None = Field(
        default=None, description="Details about incompletion."
    )
    model: str = Field(description="Model used.")
    instructions: str | None = Field(
        default=None, description="Instructions used.")
    tools: list[dict[str, Any]] = Field(
        default_factory=list, description="Tools used in run."
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="User-defined metadata."
    )
    usage: Usage | None = Field(default=None, description="Token usage.")
    temperature: float | None = Field(
        default=None, description="Temperature used.")
    top_p: float | None = Field(default=None, description="Top-p used.")
    max_prompt_tokens: int | None = Field(
        default=None, description="Max prompt tokens."
    )
    max_completion_tokens: int | None = Field(
        default=None, description="Max completion tokens."
    )
    truncation_strategy: dict[str, Any] | None = Field(
        default=None, description="Truncation strategy."
    )
    tool_choice: str | dict[str, Any] | None = Field(
        default=None, description="Tool choice used."
    )
    parallel_tool_calls: bool = Field(
        default=True, description="Whether parallel tool calls are enabled."
    )
    response_format: str | dict[str, Any] | None = Field(
        default="auto", description="Response format."
    )


class CreateRunRequest(BaseModel):
    """Request to create a run."""

    assistant_id: str = Field(description="Assistant ID to use.")
    model: str | None = Field(default=None, description="Override model.")
    instructions: str | None = Field(
        default=None, description="Override instructions.")
    additional_instructions: str | None = Field(
        default=None, description="Additional instructions to append."
    )
    additional_messages: list[dict[str, Any]] | None = Field(
        default=None, description="Additional messages to add before run."
    )
    tools: list[dict[str, Any]] | None = Field(
        default=None, description="Override tools."
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Metadata (max 16 pairs)."
    )
    temperature: float | None = Field(
        default=None, ge=0.0, le=2.0, description="Temperature."
    )
    top_p: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Top-p.")
    max_prompt_tokens: int | None = Field(
        default=None, description="Max prompt tokens."
    )
    max_completion_tokens: int | None = Field(
        default=None, description="Max completion tokens."
    )
    truncation_strategy: dict[str, Any] | None = Field(
        default=None, description="Truncation strategy."
    )
    tool_choice: str | dict[str, Any] | None = Field(
        default=None, description="Tool choice."
    )
    parallel_tool_calls: bool = Field(
        default=True, description="Enable parallel tool calls."
    )
    response_format: str | dict[str, Any] | None = Field(
        default="auto", description="Response format."
    )
    stream: bool = Field(default=False, description="Stream run updates.")


class ModifyRunRequest(BaseModel):
    """Request to modify a run (only metadata supported)."""

    metadata: dict[str, str] | None = Field(
        default=None, description="Metadata.")


class RunList(BaseModel):
    """List of runs."""

    object: Literal["list"] = Field(default="list", description="Object type.")
    data: list[Run] = Field(description="List of run objects.")
    first_id: str | None = Field(default=None, description="First run ID.")
    last_id: str | None = Field(default=None, description="Last run ID.")
    has_more: bool = Field(
        default=False,
        description="Whether there are more results.")


class RunStep(BaseModel):
    """Run step object."""

    id: str = Field(description="Run step ID.")
    object: Literal["thread.run.step"] = Field(
        default="thread.run.step", description="Object type."
    )
    created_at: int = Field(description="Unix timestamp of creation.")
    run_id: str = Field(description="Run ID.")
    assistant_id: str = Field(description="Assistant ID.")
    thread_id: str = Field(description="Thread ID.")
    type: Literal["message_creation", "tool_calls"] = Field(
        description="Step type.")
    status: Literal["in_progress", "cancelled", "failed",
                    "completed", "expired"] = (Field(description="Step status."))
    cancelled_at: int | None = Field(
        default=None, description="Cancellation timestamp."
    )
    completed_at: int | None = Field(
        default=None, description="Completion timestamp.")
    expired_at: int | None = Field(
        default=None, description="Expiration timestamp.")
    failed_at: int | None = Field(
        default=None, description="Failure timestamp.")
    last_error: dict[str, Any] | None = Field(
        default=None, description="Error details."
    )
    step_details: dict[str, Any] = Field(description="Step-specific details.")
    usage: Usage | None = Field(default=None,
                                description="Token usage for this step.")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="User-defined metadata."
    )


class RunStepList(BaseModel):
    """List of run steps."""

    object: Literal["list"] = Field(default="list", description="Object type.")
    data: list[RunStep] = Field(description="List of run step objects.")
    first_id: str | None = Field(default=None, description="First step ID.")
    last_id: str | None = Field(default=None, description="Last step ID.")
    has_more: bool = Field(
        default=False,
        description="Whether there are more results.")
