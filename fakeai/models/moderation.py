"""
Content moderation models for the OpenAI API.

This module contains models for the moderation endpoint which checks
content for potential policy violations across multiple categories.
"""
#  SPDX-License-Identifier: Apache-2.0

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ModerationCategories(BaseModel):
    """Boolean flags for moderation categories."""

    model_config = ConfigDict(populate_by_name=True)

    sexual: bool = Field(default=False, description="Sexual content.")
    hate: bool = Field(default=False, description="Hate speech.")
    harassment: bool = Field(default=False, description="Harassment.")
    self_harm: bool = Field(
        default=False, description="Self-harm content.", alias="self-harm"
    )
    sexual_minors: bool = Field(
        default=False,
        description="Sexual content involving minors.",
        alias="sexual/minors",
    )
    hate_threatening: bool = Field(
        default=False,
        description="Hateful threatening content.",
        alias="hate/threatening",
    )
    harassment_threatening: bool = Field(
        default=False,
        description="Harassing threatening content.",
        alias="harassment/threatening",
    )
    self_harm_intent: bool = Field(
        default=False,
        description="Self-harm intent.",
        alias="self-harm/intent")
    self_harm_instructions: bool = Field(
        default=False,
        description="Self-harm instructions.",
        alias="self-harm/instructions",
    )
    violence: bool = Field(default=False, description="Violent content.")
    violence_graphic: bool = Field(
        default=False,
        description="Graphic violence.",
        alias="violence/graphic")
    illicit: bool = Field(default=False, description="Illicit activities.")
    illicit_violent: bool = Field(
        default=False,
        description="Violent illicit activities.",
        alias="illicit/violent",
    )


class ModerationCategoryScores(BaseModel):
    """Confidence scores for moderation categories (0.0-1.0)."""

    model_config = ConfigDict(populate_by_name=True)

    sexual: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Sexual content score.")
    hate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Hate speech score.")
    harassment: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Harassment score."
    )
    self_harm: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Self-harm score.",
        alias="self-harm")
    sexual_minors: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Sexual minors score.",
        alias="sexual/minors",
    )
    hate_threatening: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Hate threatening score.",
        alias="hate/threatening",
    )
    harassment_threatening: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Harassment threatening score.",
        alias="harassment/threatening",
    )
    self_harm_intent: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Self-harm intent score.",
        alias="self-harm/intent",
    )
    self_harm_instructions: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Self-harm instructions score.",
        alias="self-harm/instructions",
    )
    violence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Violence score.")
    violence_graphic: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Graphic violence score.",
        alias="violence/graphic",
    )
    illicit: float = Field(default=0.0, ge=0.0, le=1.0,
                           description="Illicit score.")
    illicit_violent: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Violent illicit score.",
        alias="illicit/violent",
    )


class ModerationResult(BaseModel):
    """Single moderation result."""

    flagged: bool = Field(description="True if any category violated.")
    categories: ModerationCategories = Field(description="Category flags.")
    category_scores: ModerationCategoryScores = Field(
        description="Category scores.")
    category_applied_input_types: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Which input types (text/image) triggered each category.",
    )


class ModerationRequest(BaseModel):
    """Request for content moderation."""

    input: str | list[str] | list[dict[str, Any]] = Field(
        description="Text, array of texts, or multimodal content to moderate."
    )
    model: str | None = Field(
        default="omni-moderation-latest",
        description="Moderation model ID.",
    )


class ModerationResponse(BaseModel):
    """Response from moderation endpoint."""

    id: str = Field(description="Unique moderation ID.")
    model: str = Field(description="Model used.")
    results: list[ModerationResult] = Field(description="Moderation results.")
