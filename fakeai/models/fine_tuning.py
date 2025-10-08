"""
Fine-tuning models for the OpenAI API.

This module contains models for creating and managing fine-tuning jobs,
including hyperparameters, events, checkpoints, and job status tracking.
"""
#  SPDX-License-Identifier: Apache-2.0

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class Hyperparameters(BaseModel):
    """Hyperparameters for fine-tuning."""

    n_epochs: int | Literal["auto"] = Field(
        default="auto",
        description="Number of training epochs. 'auto' decides based on dataset size.",
    )
    batch_size: int | Literal["auto"] = Field(
        default="auto",
        description="Batch size for training. 'auto' decides based on dataset size.",
    )
    learning_rate_multiplier: float | Literal["auto"] = Field(
        default="auto",
        description="Multiplier for the learning rate. 'auto' uses recommended value.",
    )


class FineTuningJobRequest(BaseModel):
    """Request to create a fine-tuning job."""

    training_file: str = Field(
        description="ID of uploaded file containing training data."
    )
    validation_file: str | None = Field(
        default=None, description="ID of uploaded file containing validation data.")
    model: str = Field(
        description="Base model to fine-tune (e.g., 'meta-llama/Llama-3.1-8B-Instruct', 'openai/gpt-oss-20b')."
    )
    hyperparameters: Hyperparameters | None = Field(
        default=None, description="Hyperparameters for fine-tuning."
    )
    suffix: str | None = Field(
        default=None,
        max_length=40,
        description="Suffix for the fine-tuned model name (max 40 characters).",
    )
    integrations: list[dict[str, Any]] | None = Field(
        default=None, description="Integrations to enable (e.g., Weights & Biases)."
    )
    seed: int | None = Field(
        default=None, description="Random seed for reproducibility."
    )

    @field_validator("suffix")
    @classmethod
    def validate_suffix_length(cls, v: str | None) -> str | None:
        """Validate suffix length."""
        if v is not None and len(v) > 40:
            raise ValueError("Suffix must not exceed 40 characters")
        return v


class FineTuningJobError(BaseModel):
    """Error information for failed fine-tuning jobs."""

    code: str = Field(description="Error code.")
    message: str = Field(description="Human-readable error message.")
    param: str | None = Field(
        default=None,
        description="Parameter that caused the error, if applicable.")


class FineTuningJob(BaseModel):
    """Fine-tuning job object."""

    id: str = Field(description="Unique identifier for the fine-tuning job.")
    object: Literal["fine_tuning.job"] = Field(
        default="fine_tuning.job", description="Object type."
    )
    created_at: int = Field(
        description="Unix timestamp when the job was created.")
    finished_at: int | None = Field(
        default=None, description="Unix timestamp when the job finished."
    )
    model: str = Field(description="Base model being fine-tuned.")
    fine_tuned_model: str | None = Field(
        default=None,
        description="Name of the fine-tuned model (null until completed).")
    organization_id: str = Field(description="Organization that owns the job.")
    status: Literal[
        "validating_files", "queued", "running", "succeeded", "failed", "cancelled"
    ] = Field(description="Current status of the fine-tuning job.")
    hyperparameters: Hyperparameters = Field(
        description="Hyperparameters used for training."
    )
    training_file: str = Field(description="ID of the training file.")
    validation_file: str | None = Field(
        default=None, description="ID of the validation file."
    )
    result_files: list[str] = Field(
        default_factory=list,
        description="List of result file IDs (e.g., metrics, model files).",
    )
    trained_tokens: int | None = Field(
        default=None,
        description="Total number of tokens processed during training.")
    error: FineTuningJobError | None = Field(
        default=None, description="Error details if the job failed."
    )
    integrations: list[dict[str, Any]] | None = Field(
        default=None, description="Enabled integrations."
    )
    seed: int | None = Field(default=None,
                             description="Random seed used for training.")
    estimated_finish: int | None = Field(
        default=None,
        description="Estimated Unix timestamp when the job will finish.")


class FineTuningJobList(BaseModel):
    """List of fine-tuning jobs."""

    object: Literal["list"] = Field(default="list", description="Object type.")
    data: list[FineTuningJob] = Field(description="List of fine-tuning jobs.")
    has_more: bool = Field(
        default=False, description="Whether there are more results available."
    )


class FineTuningEvent(BaseModel):
    """Event during fine-tuning job execution."""

    id: str = Field(description="Unique identifier for the event.")
    object: Literal["fine_tuning.job.event"] = Field(
        default="fine_tuning.job.event", description="Object type."
    )
    created_at: int = Field(
        description="Unix timestamp when the event occurred.")
    level: Literal["info", "warning", "error"] = Field(
        description="Severity level of the event."
    )
    message: str = Field(description="Event message.")
    data: dict[str, Any] | None = Field(
        default=None, description="Additional event data (e.g., metrics)."
    )
    type: Literal["message", "metrics"] = Field(
        default="message", description="Type of event."
    )


class FineTuningEventList(BaseModel):
    """List of fine-tuning events."""

    object: Literal["list"] = Field(default="list", description="Object type.")
    data: list[FineTuningEvent] = Field(description="List of events.")
    has_more: bool = Field(
        default=False, description="Whether there are more results available."
    )


class FineTuningCheckpoint(BaseModel):
    """Checkpoint saved during fine-tuning."""

    id: str = Field(description="Unique identifier for the checkpoint.")
    object: Literal["fine_tuning.job.checkpoint"] = Field(
        default="fine_tuning.job.checkpoint", description="Object type."
    )
    created_at: int = Field(
        description="Unix timestamp when checkpoint was created.")
    fine_tuning_job_id: str = Field(description="ID of the fine-tuning job.")
    fine_tuned_model_checkpoint: str = Field(
        description="Name of the checkpointed model."
    )
    step_number: int = Field(
        description="Training step number for this checkpoint.")
    metrics: dict[str, float] = Field(
        description="Training metrics at this checkpoint."
    )


class FineTuningCheckpointList(BaseModel):
    """List of fine-tuning checkpoints."""

    object: Literal["list"] = Field(default="list", description="Object type.")
    data: list[FineTuningCheckpoint] = Field(
        description="List of checkpoints.")
    has_more: bool = Field(
        default=False, description="Whether there are more results available."
    )
    first_id: str | None = Field(
        default=None, description="First checkpoint ID.")
    last_id: str | None = Field(
        default=None,
        description="Last checkpoint ID.")
