"""
Tests for Organization and Project Management API.

This module tests the complete organization and project management functionality,
including user management, invites, projects, project users, and service accounts.
"""

import pytest
from fakeai import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import (
    CreateOrganizationUserRequest,
    ModifyOrganizationUserRequest,
    CreateOrganizationInviteRequest,
    CreateOrganizationProjectRequest,
    ModifyOrganizationProjectRequest,
    CreateProjectUserRequest,
    ModifyProjectUserRequest,
    CreateServiceAccountRequest,
    OrganizationRole,
    ProjectRole,
    ServiceAccountRole,
)


@pytest.fixture
def service():
    """Create a FakeAIService instance for testing."""
    config = AppConfig(response_delay=0.0, debug=True)
    return FakeAIService(config)


class TestOrganizationUsers:
    """Test organization user management."""

    @pytest.mark.asyncio
    async def test_create_organization_user(self, service):
        """Test creating an organization user."""
        request = CreateOrganizationUserRequest(
            email="test@example.com",
            role=OrganizationRole.READER,
        )
        user = await service.create_organization_user(request)

        assert user.id.startswith("user-")
        assert user.email == "test@example.com"
        assert user.role == OrganizationRole.READER
        assert user.name  # Should have a generated name
        assert user.added_at > 0

    @pytest.mark.asyncio
    async def test_list_organization_users(self, service):
        """Test listing organization users."""
        # Create multiple users
        for i in range(3):
            request = CreateOrganizationUserRequest(
                email=f"user{i}@example.com",
                role=OrganizationRole.OWNER if i == 0 else OrganizationRole.READER,
            )
            await service.create_organization_user(request)

        # List users
        response = await service.list_organization_users(limit=10)

        assert len(response.data) == 3
        assert response.object == "list"
        assert response.has_more is False

    @pytest.mark.asyncio
    async def test_get_organization_user(self, service):
        """Test getting a specific organization user."""
        # Create a user
        request = CreateOrganizationUserRequest(
            email="test@example.com",
            role=OrganizationRole.OWNER,
        )
        created_user = await service.create_organization_user(request)

        # Get the user
        user = await service.get_organization_user(created_user.id)

        assert user.id == created_user.id
        assert user.email == created_user.email
        assert user.role == OrganizationRole.OWNER

    @pytest.mark.asyncio
    async def test_modify_organization_user(self, service):
        """Test modifying an organization user's role."""
        # Create a user
        request = CreateOrganizationUserRequest(
            email="test@example.com",
            role=OrganizationRole.READER,
        )
        user = await service.create_organization_user(request)

        # Modify the user
        modify_request = ModifyOrganizationUserRequest(role=OrganizationRole.OWNER)
        modified_user = await service.modify_organization_user(user.id, modify_request)

        assert modified_user.id == user.id
        assert modified_user.role == OrganizationRole.OWNER

    @pytest.mark.asyncio
    async def test_delete_organization_user(self, service):
        """Test deleting an organization user."""
        # Create a user
        request = CreateOrganizationUserRequest(
            email="test@example.com",
            role=OrganizationRole.READER,
        )
        user = await service.create_organization_user(request)

        # Delete the user
        result = await service.delete_organization_user(user.id)

        assert result["deleted"] is True
        assert result["id"] == user.id

        # Verify user is deleted
        with pytest.raises(ValueError, match="User not found"):
            await service.get_organization_user(user.id)

    @pytest.mark.asyncio
    async def test_pagination_organization_users(self, service):
        """Test pagination for organization users."""
        # Create multiple users
        for i in range(5):
            request = CreateOrganizationUserRequest(
                email=f"user{i}@example.com",
                role=OrganizationRole.READER,
            )
            await service.create_organization_user(request)

        # Get first page
        page1 = await service.list_organization_users(limit=2)
        assert len(page1.data) == 2
        assert page1.has_more is True

        # Get second page
        page2 = await service.list_organization_users(limit=2, after=page1.last_id)
        assert len(page2.data) == 2
        assert page2.has_more is True


class TestOrganizationInvites:
    """Test organization invite management."""

    @pytest.mark.asyncio
    async def test_create_organization_invite(self, service):
        """Test creating an organization invite."""
        request = CreateOrganizationInviteRequest(
            email="invite@example.com",
            role=OrganizationRole.READER,
        )
        invite = await service.create_organization_invite(request)

        assert invite.id.startswith("invite-")
        assert invite.email == "invite@example.com"
        assert invite.role == OrganizationRole.READER
        assert invite.status == "pending"
        assert invite.invited_at > 0
        assert invite.expires_at > invite.invited_at
        assert invite.accepted_at is None

    @pytest.mark.asyncio
    async def test_list_organization_invites(self, service):
        """Test listing organization invites."""
        # Create multiple invites
        for i in range(3):
            request = CreateOrganizationInviteRequest(
                email=f"invite{i}@example.com",
                role=OrganizationRole.READER,
            )
            await service.create_organization_invite(request)

        # List invites
        response = await service.list_organization_invites(limit=10)

        assert len(response.data) == 3
        assert response.object == "list"

    @pytest.mark.asyncio
    async def test_get_organization_invite(self, service):
        """Test getting a specific organization invite."""
        # Create an invite
        request = CreateOrganizationInviteRequest(
            email="test@example.com",
            role=OrganizationRole.OWNER,
        )
        created_invite = await service.create_organization_invite(request)

        # Get the invite
        invite = await service.get_organization_invite(created_invite.id)

        assert invite.id == created_invite.id
        assert invite.email == created_invite.email

    @pytest.mark.asyncio
    async def test_delete_organization_invite(self, service):
        """Test deleting an organization invite."""
        # Create an invite
        request = CreateOrganizationInviteRequest(
            email="test@example.com",
            role=OrganizationRole.READER,
        )
        invite = await service.create_organization_invite(request)

        # Delete the invite
        result = await service.delete_organization_invite(invite.id)

        assert result.deleted is True
        assert result.id == invite.id

        # Verify invite is deleted
        with pytest.raises(ValueError, match="Invite not found"):
            await service.get_organization_invite(invite.id)


class TestOrganizationProjects:
    """Test organization project management."""

    @pytest.mark.asyncio
    async def test_create_organization_project(self, service):
        """Test creating a project."""
        request = CreateOrganizationProjectRequest(name="Test Project")
        project = await service.create_organization_project(request)

        assert project.id.startswith("proj_")
        assert project.name == "Test Project"
        assert project.status == "active"
        assert project.created_at > 0
        assert project.archived_at is None

    @pytest.mark.asyncio
    async def test_list_organization_projects(self, service):
        """Test listing projects."""
        # Create multiple projects
        for i in range(3):
            request = CreateOrganizationProjectRequest(name=f"Project {i}")
            await service.create_organization_project(request)

        # List projects
        response = await service.list_organization_projects(limit=10)

        assert len(response.data) == 3
        assert response.object == "list"

    @pytest.mark.asyncio
    async def test_get_organization_project(self, service):
        """Test getting a specific project."""
        # Create a project
        request = CreateOrganizationProjectRequest(name="Test Project")
        created_project = await service.create_organization_project(request)

        # Get the project
        project = await service.get_organization_project(created_project.id)

        assert project.id == created_project.id
        assert project.name == created_project.name

    @pytest.mark.asyncio
    async def test_modify_organization_project(self, service):
        """Test modifying a project."""
        # Create a project
        request = CreateOrganizationProjectRequest(name="Old Name")
        project = await service.create_organization_project(request)

        # Modify the project
        modify_request = ModifyOrganizationProjectRequest(name="New Name")
        modified_project = await service.modify_organization_project(
            project.id, modify_request
        )

        assert modified_project.id == project.id
        assert modified_project.name == "New Name"

    @pytest.mark.asyncio
    async def test_archive_organization_project(self, service):
        """Test archiving a project."""
        # Create a project
        request = CreateOrganizationProjectRequest(name="Test Project")
        project = await service.create_organization_project(request)

        # Archive the project
        result = await service.archive_organization_project(project.id)

        assert result.archived is True
        assert result.id == project.id

        # Verify project is archived
        archived_project = await service.get_organization_project(project.id)
        assert archived_project.status == "archived"
        assert archived_project.archived_at is not None

    @pytest.mark.asyncio
    async def test_list_projects_exclude_archived(self, service):
        """Test listing projects excludes archived by default."""
        # Create active project
        request1 = CreateOrganizationProjectRequest(name="Active Project")
        active_project = await service.create_organization_project(request1)

        # Create and archive project
        request2 = CreateOrganizationProjectRequest(name="Archived Project")
        archived_project = await service.create_organization_project(request2)
        await service.archive_organization_project(archived_project.id)

        # List projects (exclude archived)
        response = await service.list_organization_projects(
            limit=10, include_archived=False
        )

        assert len(response.data) == 1
        assert response.data[0].id == active_project.id

        # List projects (include archived)
        response_all = await service.list_organization_projects(
            limit=10, include_archived=True
        )

        assert len(response_all.data) == 2


class TestProjectUsers:
    """Test project user management."""

    @pytest.mark.asyncio
    async def test_add_user_to_project(self, service):
        """Test adding a user to a project."""
        # Create organization user
        user_request = CreateOrganizationUserRequest(
            email="test@example.com",
            role=OrganizationRole.OWNER,
        )
        user = await service.create_organization_user(user_request)

        # Create project
        project_request = CreateOrganizationProjectRequest(name="Test Project")
        project = await service.create_organization_project(project_request)

        # Add user to project
        add_request = CreateProjectUserRequest(
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        project_user = await service.create_project_user(project.id, add_request)

        assert project_user.id == user.id
        assert project_user.email == user.email
        assert project_user.role == ProjectRole.MEMBER

    @pytest.mark.asyncio
    async def test_list_project_users(self, service):
        """Test listing users in a project."""
        # Create project
        project_request = CreateOrganizationProjectRequest(name="Test Project")
        project = await service.create_organization_project(project_request)

        # Create and add multiple users
        for i in range(3):
            user_request = CreateOrganizationUserRequest(
                email=f"user{i}@example.com",
                role=OrganizationRole.READER,
            )
            user = await service.create_organization_user(user_request)

            add_request = CreateProjectUserRequest(
                user_id=user.id,
                role=ProjectRole.OWNER if i == 0 else ProjectRole.MEMBER,
            )
            await service.create_project_user(project.id, add_request)

        # List project users
        response = await service.list_project_users(project.id, limit=10)

        assert len(response.data) == 3
        assert response.object == "list"

    @pytest.mark.asyncio
    async def test_get_project_user(self, service):
        """Test getting a specific user in a project."""
        # Create user and project
        user_request = CreateOrganizationUserRequest(
            email="test@example.com",
            role=OrganizationRole.OWNER,
        )
        user = await service.create_organization_user(user_request)

        project_request = CreateOrganizationProjectRequest(name="Test Project")
        project = await service.create_organization_project(project_request)

        # Add user to project
        add_request = CreateProjectUserRequest(
            user_id=user.id,
            role=ProjectRole.OWNER,
        )
        await service.create_project_user(project.id, add_request)

        # Get project user
        project_user = await service.get_project_user(project.id, user.id)

        assert project_user.id == user.id
        assert project_user.role == ProjectRole.OWNER

    @pytest.mark.asyncio
    async def test_modify_project_user(self, service):
        """Test modifying a user's role in a project."""
        # Create user and project
        user_request = CreateOrganizationUserRequest(
            email="test@example.com",
            role=OrganizationRole.OWNER,
        )
        user = await service.create_organization_user(user_request)

        project_request = CreateOrganizationProjectRequest(name="Test Project")
        project = await service.create_organization_project(project_request)

        # Add user to project
        add_request = CreateProjectUserRequest(
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        await service.create_project_user(project.id, add_request)

        # Modify user role
        modify_request = ModifyProjectUserRequest(role=ProjectRole.OWNER)
        modified_user = await service.modify_project_user(
            project.id, user.id, modify_request
        )

        assert modified_user.role == ProjectRole.OWNER

    @pytest.mark.asyncio
    async def test_remove_user_from_project(self, service):
        """Test removing a user from a project."""
        # Create user and project
        user_request = CreateOrganizationUserRequest(
            email="test@example.com",
            role=OrganizationRole.OWNER,
        )
        user = await service.create_organization_user(user_request)

        project_request = CreateOrganizationProjectRequest(name="Test Project")
        project = await service.create_organization_project(project_request)

        # Add user to project
        add_request = CreateProjectUserRequest(
            user_id=user.id,
            role=ProjectRole.MEMBER,
        )
        await service.create_project_user(project.id, add_request)

        # Remove user from project
        result = await service.delete_project_user(project.id, user.id)

        assert result.deleted is True
        assert result.id == user.id

        # Verify user is removed
        with pytest.raises(ValueError, match="User not found in project"):
            await service.get_project_user(project.id, user.id)

    @pytest.mark.asyncio
    async def test_project_isolation(self, service):
        """Test that users are isolated between projects."""
        # Create user
        user_request = CreateOrganizationUserRequest(
            email="test@example.com",
            role=OrganizationRole.OWNER,
        )
        user = await service.create_organization_user(user_request)

        # Create two projects
        project1_request = CreateOrganizationProjectRequest(name="Project 1")
        project1 = await service.create_organization_project(project1_request)

        project2_request = CreateOrganizationProjectRequest(name="Project 2")
        project2 = await service.create_organization_project(project2_request)

        # Add user to project 1 only
        add_request = CreateProjectUserRequest(
            user_id=user.id,
            role=ProjectRole.OWNER,
        )
        await service.create_project_user(project1.id, add_request)

        # Verify user is in project 1
        project1_users = await service.list_project_users(project1.id)
        assert len(project1_users.data) == 1

        # Verify user is NOT in project 2
        project2_users = await service.list_project_users(project2.id)
        assert len(project2_users.data) == 0

    @pytest.mark.asyncio
    async def test_user_not_in_organization(self, service):
        """Test that adding non-existent user to project fails."""
        # Create project
        project_request = CreateOrganizationProjectRequest(name="Test Project")
        project = await service.create_organization_project(project_request)

        # Try to add non-existent user
        add_request = CreateProjectUserRequest(
            user_id="user-nonexistent",
            role=ProjectRole.MEMBER,
        )

        with pytest.raises(ValueError, match="User not found in organization"):
            await service.create_project_user(project.id, add_request)


class TestServiceAccounts:
    """Test service account management."""

    @pytest.mark.asyncio
    async def test_create_service_account(self, service):
        """Test creating a service account."""
        # Create project
        project_request = CreateOrganizationProjectRequest(name="Test Project")
        project = await service.create_organization_project(project_request)

        # Create service account
        account_request = CreateServiceAccountRequest(
            name="Test Service Account",
            role=ServiceAccountRole.MEMBER,
        )
        account = await service.create_service_account(project.id, account_request)

        assert account.id.startswith("svc_acct_")
        assert account.name == "Test Service Account"
        assert account.role == ServiceAccountRole.MEMBER
        assert account.created_at > 0

    @pytest.mark.asyncio
    async def test_list_service_accounts(self, service):
        """Test listing service accounts."""
        # Create project
        project_request = CreateOrganizationProjectRequest(name="Test Project")
        project = await service.create_organization_project(project_request)

        # Create multiple service accounts
        for i in range(3):
            account_request = CreateServiceAccountRequest(
                name=f"Service Account {i}",
                role=ServiceAccountRole.MEMBER,
            )
            await service.create_service_account(project.id, account_request)

        # List service accounts
        response = await service.list_service_accounts(project.id, limit=10)

        assert len(response.data) == 3
        assert response.object == "list"

    @pytest.mark.asyncio
    async def test_get_service_account(self, service):
        """Test getting a specific service account."""
        # Create project
        project_request = CreateOrganizationProjectRequest(name="Test Project")
        project = await service.create_organization_project(project_request)

        # Create service account
        account_request = CreateServiceAccountRequest(
            name="Test Account",
            role=ServiceAccountRole.OWNER,
        )
        created_account = await service.create_service_account(
            project.id, account_request
        )

        # Get the account
        account = await service.get_service_account(project.id, created_account.id)

        assert account.id == created_account.id
        assert account.name == created_account.name

    @pytest.mark.asyncio
    async def test_delete_service_account(self, service):
        """Test deleting a service account."""
        # Create project
        project_request = CreateOrganizationProjectRequest(name="Test Project")
        project = await service.create_organization_project(project_request)

        # Create service account
        account_request = CreateServiceAccountRequest(
            name="Test Account",
            role=ServiceAccountRole.MEMBER,
        )
        account = await service.create_service_account(project.id, account_request)

        # Delete the account
        result = await service.delete_service_account(project.id, account.id)

        assert result.deleted is True
        assert result.id == account.id

        # Verify account is deleted
        with pytest.raises(ValueError, match="Service account not found"):
            await service.get_service_account(project.id, account.id)

    @pytest.mark.asyncio
    async def test_service_account_project_isolation(self, service):
        """Test that service accounts are isolated between projects."""
        # Create two projects
        project1_request = CreateOrganizationProjectRequest(name="Project 1")
        project1 = await service.create_organization_project(project1_request)

        project2_request = CreateOrganizationProjectRequest(name="Project 2")
        project2 = await service.create_organization_project(project2_request)

        # Create service account in project 1
        account_request = CreateServiceAccountRequest(
            name="Test Account",
            role=ServiceAccountRole.MEMBER,
        )
        account = await service.create_service_account(project1.id, account_request)

        # Verify account is in project 1
        project1_accounts = await service.list_service_accounts(project1.id)
        assert len(project1_accounts.data) == 1

        # Verify account is NOT in project 2
        project2_accounts = await service.list_service_accounts(project2.id)
        assert len(project2_accounts.data) == 0


class TestRoleBasedAccess:
    """Test role-based access control scenarios."""

    @pytest.mark.asyncio
    async def test_organization_roles(self, service):
        """Test different organization roles."""
        # Create owner
        owner_request = CreateOrganizationUserRequest(
            email="owner@example.com",
            role=OrganizationRole.OWNER,
        )
        owner = await service.create_organization_user(owner_request)
        assert owner.role == OrganizationRole.OWNER

        # Create reader
        reader_request = CreateOrganizationUserRequest(
            email="reader@example.com",
            role=OrganizationRole.READER,
        )
        reader = await service.create_organization_user(reader_request)
        assert reader.role == OrganizationRole.READER

    @pytest.mark.asyncio
    async def test_project_roles(self, service):
        """Test different project roles."""
        # Create organization user
        user_request = CreateOrganizationUserRequest(
            email="test@example.com",
            role=OrganizationRole.OWNER,
        )
        user = await service.create_organization_user(user_request)

        # Create project
        project_request = CreateOrganizationProjectRequest(name="Test Project")
        project = await service.create_organization_project(project_request)

        # Add user as owner
        owner_request = CreateProjectUserRequest(
            user_id=user.id,
            role=ProjectRole.OWNER,
        )
        project_owner = await service.create_project_user(project.id, owner_request)
        assert project_owner.role == ProjectRole.OWNER

        # Create another user and add as member
        user2_request = CreateOrganizationUserRequest(
            email="member@example.com",
            role=OrganizationRole.READER,
        )
        user2 = await service.create_organization_user(user2_request)

        member_request = CreateProjectUserRequest(
            user_id=user2.id,
            role=ProjectRole.MEMBER,
        )
        project_member = await service.create_project_user(project.id, member_request)
        assert project_member.role == ProjectRole.MEMBER

    @pytest.mark.asyncio
    async def test_service_account_roles(self, service):
        """Test different service account roles."""
        # Create project
        project_request = CreateOrganizationProjectRequest(name="Test Project")
        project = await service.create_organization_project(project_request)

        # Create owner service account
        owner_request = CreateServiceAccountRequest(
            name="Owner Account",
            role=ServiceAccountRole.OWNER,
        )
        owner_account = await service.create_service_account(project.id, owner_request)
        assert owner_account.role == ServiceAccountRole.OWNER

        # Create member service account
        member_request = CreateServiceAccountRequest(
            name="Member Account",
            role=ServiceAccountRole.MEMBER,
        )
        member_account = await service.create_service_account(
            project.id, member_request
        )
        assert member_account.role == ServiceAccountRole.MEMBER


class TestCascadingDeletion:
    """Test cascading deletion behavior."""

    @pytest.mark.asyncio
    async def test_deleting_user_removes_from_projects(self, service):
        """Test that deleting a user removes them from all projects."""
        # Create user
        user_request = CreateOrganizationUserRequest(
            email="test@example.com",
            role=OrganizationRole.OWNER,
        )
        user = await service.create_organization_user(user_request)

        # Create multiple projects and add user to all
        projects = []
        for i in range(3):
            project_request = CreateOrganizationProjectRequest(name=f"Project {i}")
            project = await service.create_organization_project(project_request)
            projects.append(project)

            add_request = CreateProjectUserRequest(
                user_id=user.id,
                role=ProjectRole.MEMBER,
            )
            await service.create_project_user(project.id, add_request)

        # Verify user is in all projects
        for project in projects:
            users = await service.list_project_users(project.id)
            assert len(users.data) == 1

        # Delete user from organization
        await service.delete_organization_user(user.id)

        # Verify user is removed from all projects
        for project in projects:
            users = await service.list_project_users(project.id)
            assert len(users.data) == 0
