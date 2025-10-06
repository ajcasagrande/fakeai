"""
Organization and project management models for the OpenAI API.

This module contains models for managing organizations, projects, users,
invites, and service accounts in the OpenAI platform.
"""
#  SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class OrganizationRole(str, Enum):
    """Role in an organization."""

    OWNER = "owner"
    READER = "reader"


class ProjectRole(str, Enum):
    """Role in a project."""

    OWNER = "owner"
    MEMBER = "member"


class ServiceAccountRole(str, Enum):
    """Role for service accounts."""

    OWNER = "owner"
    MEMBER = "member"


class OrganizationUser(BaseModel):
    """User within an organization."""

    object: Literal["organization.user"] = Field(
        default="organization.user", description="The object type."
    )
    id: str = Field(description="The user identifier.")
    name: str = Field(description="The name of the user.")
    email: str = Field(description="The email address of the user.")
    role: OrganizationRole = Field(description="The role of the user in the organization.")
    added_at: int = Field(description="Unix timestamp when the user was added.")


class OrganizationUserListResponse(BaseModel):
    """Response for listing organization users."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[OrganizationUser] = Field(description="List of organization user objects.")
    first_id: str | None = Field(default=None, description="ID of the first user.")
    last_id: str | None = Field(default=None, description="ID of the last user.")
    has_more: bool = Field(default=False, description="Whether there are more users.")


class CreateOrganizationUserRequest(BaseModel):
    """Request to add a user to an organization."""

    email: str = Field(description="Email address of the user to add.")
    role: OrganizationRole = Field(description="Role to assign to the user.")


class ModifyOrganizationUserRequest(BaseModel):
    """Request to modify an organization user."""

    role: OrganizationRole = Field(description="New role for the user.")


class OrganizationInvite(BaseModel):
    """Invitation to join an organization."""

    object: Literal["organization.invite"] = Field(
        default="organization.invite", description="The object type."
    )
    id: str = Field(description="The invite identifier.")
    email: str = Field(description="The email address of the invited user.")
    role: OrganizationRole = Field(description="The role the user will have.")
    status: Literal["pending", "accepted", "expired"] = Field(
        description="Status of the invitation."
    )
    invited_at: int = Field(description="Unix timestamp when the invite was created.")
    expires_at: int = Field(description="Unix timestamp when the invite expires.")
    accepted_at: int | None = Field(
        default=None, description="Unix timestamp when the invite was accepted."
    )


class OrganizationInviteListResponse(BaseModel):
    """Response for listing organization invites."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[OrganizationInvite] = Field(description="List of organization invite objects.")
    first_id: str | None = Field(default=None, description="ID of the first invite.")
    last_id: str | None = Field(default=None, description="ID of the last invite.")
    has_more: bool = Field(default=False, description="Whether there are more invites.")


class CreateOrganizationInviteRequest(BaseModel):
    """Request to create an organization invite."""

    email: str = Field(description="Email address to invite.")
    role: OrganizationRole = Field(description="Role to assign to the invited user.")


class DeleteOrganizationInviteResponse(BaseModel):
    """Response for deleting an organization invite."""

    object: Literal["organization.invite.deleted"] = Field(
        default="organization.invite.deleted", description="The object type."
    )
    id: str = Field(description="The ID of the deleted invite.")
    deleted: bool = Field(default=True, description="Whether the invite was deleted.")


class OrganizationProject(BaseModel):
    """Project within an organization."""

    object: Literal["organization.project"] = Field(
        default="organization.project", description="The object type."
    )
    id: str = Field(description="The project identifier.")
    name: str = Field(description="The name of the project.")
    created_at: int = Field(description="Unix timestamp when the project was created.")
    archived_at: int | None = Field(
        default=None, description="Unix timestamp when the project was archived."
    )
    status: Literal["active", "archived"] = Field(
        default="active", description="The status of the project."
    )


class OrganizationProjectListResponse(BaseModel):
    """Response for listing organization projects."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[OrganizationProject] = Field(description="List of organization project objects.")
    first_id: str | None = Field(default=None, description="ID of the first project.")
    last_id: str | None = Field(default=None, description="ID of the last project.")
    has_more: bool = Field(default=False, description="Whether there are more projects.")


class CreateOrganizationProjectRequest(BaseModel):
    """Request to create a new project."""

    name: str = Field(description="The name of the project.")


class ModifyOrganizationProjectRequest(BaseModel):
    """Request to modify a project."""

    name: str = Field(description="The new name of the project.")


class ArchiveOrganizationProjectResponse(BaseModel):
    """Response for archiving a project."""

    object: Literal["organization.project.archived"] = Field(
        default="organization.project.archived", description="The object type."
    )
    id: str = Field(description="The ID of the archived project.")
    archived: bool = Field(default=True, description="Whether the project was archived.")


class ProjectUser(BaseModel):
    """User within a project."""

    object: Literal["organization.project.user"] = Field(
        default="organization.project.user", description="The object type."
    )
    id: str = Field(description="The user identifier.")
    name: str = Field(description="The name of the user.")
    email: str = Field(description="The email address of the user.")
    role: ProjectRole = Field(description="The role of the user in the project.")
    added_at: int = Field(description="Unix timestamp when the user was added to the project.")


class ProjectUserListResponse(BaseModel):
    """Response for listing project users."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[ProjectUser] = Field(description="List of project user objects.")
    first_id: str | None = Field(default=None, description="ID of the first user.")
    last_id: str | None = Field(default=None, description="ID of the last user.")
    has_more: bool = Field(default=False, description="Whether there are more users.")


class CreateProjectUserRequest(BaseModel):
    """Request to add a user to a project."""

    user_id: str = Field(description="The ID of the user to add to the project.")
    role: ProjectRole = Field(description="Role to assign to the user in the project.")


class ModifyProjectUserRequest(BaseModel):
    """Request to modify a project user."""

    role: ProjectRole = Field(description="New role for the user in the project.")


class DeleteProjectUserResponse(BaseModel):
    """Response for removing a user from a project."""

    object: Literal["organization.project.user.deleted"] = Field(
        default="organization.project.user.deleted", description="The object type."
    )
    id: str = Field(description="The ID of the removed user.")
    deleted: bool = Field(default=True, description="Whether the user was removed.")


class ServiceAccount(BaseModel):
    """Service account for API access."""

    object: Literal["organization.project.service_account"] = Field(
        default="organization.project.service_account", description="The object type."
    )
    id: str = Field(description="The service account identifier.")
    name: str = Field(description="The name of the service account.")
    role: ServiceAccountRole = Field(description="The role of the service account.")
    created_at: int = Field(description="Unix timestamp when the service account was created.")


class ServiceAccountListResponse(BaseModel):
    """Response for listing service accounts."""

    object: Literal["list"] = Field(default="list", description="The object type.")
    data: list[ServiceAccount] = Field(description="List of service account objects.")
    first_id: str | None = Field(default=None, description="ID of the first service account.")
    last_id: str | None = Field(default=None, description="ID of the last service account.")
    has_more: bool = Field(default=False, description="Whether there are more service accounts.")


class CreateServiceAccountRequest(BaseModel):
    """Request to create a service account."""

    name: str = Field(description="The name of the service account.")
    role: ServiceAccountRole = Field(
        default=ServiceAccountRole.MEMBER, description="Role for the service account."
    )


class DeleteServiceAccountResponse(BaseModel):
    """Response for deleting a service account."""

    object: Literal["organization.project.service_account.deleted"] = Field(
        default="organization.project.service_account.deleted", description="The object type."
    )
    id: str = Field(description="The ID of the deleted service account.")
    deleted: bool = Field(default=True, description="Whether the service account was deleted.")
