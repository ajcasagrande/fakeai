"""
Image generation models for the OpenAI API.

This module contains Pydantic models for DALL-E compatible image generation,
including requests, responses, and usage tracking. Supports various image sizes,
quality modes, style presets, and response formats (URL or base64).
"""

#  SPDX-License-Identifier: Apache-2.0

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ImageSize(str, Enum):
    """Available image sizes."""

    SIZE_256 = "256x256"
    SIZE_512 = "512x512"
    SIZE_1024 = "1024x1024"
    SIZE_1792_1024 = "1792x1024"
    SIZE_1024_1792 = "1024x1792"


class ImageQuality(str, Enum):
    """Available image qualities."""

    STANDARD = "standard"
    HD = "hd"


class ImageStyle(str, Enum):
    """Available image styles."""

    VIVID = "vivid"
    NATURAL = "natural"


class ImageResponseFormat(str, Enum):
    """Available response formats for images."""

    URL = "url"
    B64_JSON = "b64_json"


class GeneratedImage(BaseModel):
    """A generated image."""

    url: str | None = Field(
        default=None,
        description="The URL of the generated image.")
    b64_json: str | None = Field(
        default=None,
        description="The base64-encoded JSON of the generated image.")
    revised_prompt: str | None = Field(
        default=None,
        description="The revised prompt used to generate the image.")


class ImageGenerationRequest(BaseModel):
    """Request for image generation."""

    prompt: str = Field(
        max_length=1000,
        description="A text description of the desired image(s).")
    model: str | None = Field(
        default="stabilityai/stable-diffusion-2-1",
        description="The model to use for image generation.",
    )
    n: int | None = Field(
        default=1, ge=1, le=10, description="The number of images to generate."
    )
    quality: ImageQuality | None = Field(
        default=ImageQuality.STANDARD, description="The quality of the image."
    )
    response_format: ImageResponseFormat | None = Field(
        default=ImageResponseFormat.URL,
        description="The format in which the images are returned.",
    )
    size: ImageSize | None = Field(
        default=ImageSize.SIZE_1024,
        description="The size of the generated images.")
    style: ImageStyle | None = Field(
        default=ImageStyle.VIVID,
        description="The style of the generated images.")
    user: str | None = Field(
        default=None, description="A unique identifier for the end-user."
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt_length(cls, v: str) -> str:
        """Validate prompt length."""
        if len(v) > 1000:
            raise ValueError("Prompt must not exceed 1000 characters")
        return v


class ImageGenerationResponse(BaseModel):
    """Response for image generation."""

    created: int = Field(
        description="The Unix timestamp of when the images were created."
    )
    data: list[GeneratedImage] = Field(
        description="The list of generated images.")


# Note: ImagesUsageResponse is now in billing.py to avoid duplication with
# other usage models


# Video Generation Models
class VideoSize(str, Enum):
    """Available video sizes."""

    SIZE_512_512 = "512x512"
    SIZE_1024_576 = "1024x576"
    SIZE_576_1024 = "576x1024"
    SIZE_1280_720 = "1280x720"
    SIZE_720_1280 = "720x1280"


class VideoFormat(str, Enum):
    """Available video formats."""

    MP4 = "mp4"
    WEBM = "webm"
    MOV = "mov"


class GeneratedVideo(BaseModel):
    """A generated video."""

    url: str | None = Field(
        default=None,
        description="The URL of the generated video.")
    b64_json: str | None = Field(
        default=None,
        description="The base64-encoded JSON of the generated video.")


class VideoGenerationRequest(BaseModel):
    """Request for video generation."""

    prompt: str = Field(
        max_length=1000, description="A text description of the desired video."
    )
    model: str | None = Field(
        default="runway-gen3",
        description="The model to use for video generation.",
    )
    duration: float | None = Field(
        default=5.0,
        ge=1.0,
        le=10.0,
        description="Duration of the video in seconds.")
    size: VideoSize | None = Field(
        default=VideoSize.SIZE_1280_720,
        description="The size of the generated video.")
    format: VideoFormat | None = Field(
        default=VideoFormat.MP4,
        description="The format of the generated video.")
    fps: int | None = Field(
        default=24, ge=12, le=60, description="Frames per second."
    )
    user: str | None = Field(
        default=None, description="A unique identifier for the end-user."
    )

    @field_validator("prompt")
    @classmethod
    def validate_prompt_length(cls, v: str) -> str:
        """Validate prompt length."""
        if len(v) > 1000:
            raise ValueError("Prompt must not exceed 1000 characters")
        return v


class VideoGenerationResponse(BaseModel):
    """Response for video generation."""

    created: int = Field(
        description="The Unix timestamp of when the video was created."
    )
    data: list[GeneratedVideo] = Field(
        description="The list of generated videos.")
