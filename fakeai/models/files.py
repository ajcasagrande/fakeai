"""
File management models for the OpenAI API.

This module contains models for file upload, listing, and management
operations used in fine-tuning, assistants, and other file-based APIs.
"""
#  SPDX-License-Identifier: Apache-2.0

from typing import Literal

from pydantic import BaseModel, Field


class FileObject(BaseModel):
    """File object information."""

    id: str = Field(description="The ID of the file.")
    object: Literal["file"] = Field(default="file", description="The object type.")
    bytes: int = Field(description="The size of the file in bytes.")
    created_at: int = Field(
        description="The Unix timestamp when this file was created."
    )
    filename: str = Field(description="The filename.")
    purpose: str = Field(description="The purpose of the file.")
    status: str | None = Field(default=None, description="The status of the file.")
    status_details: str | None = Field(
        default=None, description="Additional details about the file status."
    )


class FileListResponse(BaseModel):
    """Response for listing files."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[FileObject] = Field(description="The list of file objects.")
