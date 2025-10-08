"""Integration tests for organization management endpoints.

This module provides comprehensive integration tests for:
1. Organization user management (create, list, get, modify, delete)
2. Organization invitations (create, list, get, delete)
3. Project management (create, list, get, modify, archive)
4. Project user management (add, list, get, modify, remove)
5. Service account management (create, list, get, delete)
6. Usage tracking per organization/project
7. Billing/costs per organization/project
8. Roles and permissions validation
9. Pagination for all list endpoints
10. Error handling (not found, invalid parameters)
11. Cross-entity relationships (user deletion cascades)
12. Organization settings and configurations
"""

import time

import pytest

from .utils import FakeAIClient


@pytest.mark.integration
class TestOrganizationUsers:
    """Test organization user management functionality."""

    def test_create_organization_user(self, client: FakeAIClient):
        """Test creating a new organization user."""
        response = client.post(
            "/v1/organization/users",
            json={
                "email": "newuser@example.com",
                "role": "owner",
            },
        )
        response.raise_for_status()
        user = response.json()

        # Validate response structure
        assert user["object"] == "organization.user"
        assert user["id"].startswith("user-")
        assert user["email"] == "newuser@example.com"
        assert user["role"] == "owner"
        assert "name" in user
        assert "added_at" in user
        assert isinstance(user["added_at"], int)

    def test_list_organization_users(self, client: FakeAIClient):
        """Test listing organization users."""
        # Create multiple users
        user_emails = ["user1@example.com", "user2@example.com", "user3@example.com"]
        created_ids = []

        for email in user_emails:
            response = client.post(
                "/v1/organization/users",
                json={"email": email, "role": "reader"},
            )
            response.raise_for_status()
            created_ids.append(response.json()["id"])

        # List all users
        response = client.get("/v1/organization/users")
        response.raise_for_status()
        data = response.json()

        # Validate response structure
        assert data["object"] == "list"
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 3
        assert "first_id" in data
        assert "last_id" in data
        assert "has_more" in data

        # Verify created users are in the list
        user_ids = [user["id"] for user in data["data"]]
        for user_id in created_ids:
            assert user_id in user_ids

    def test_list_organization_users_pagination(self, client: FakeAIClient):
        """Test pagination for organization users."""
        # Create multiple users
        for i in range(5):
            client.post(
                "/v1/organization/users",
                json={"email": f"paging{i}@example.com", "role": "reader"},
            )

        # Get first page (limit 2)
        response = client.get("/v1/organization/users?limit=2")
        response.raise_for_status()
        page1 = response.json()

        assert len(page1["data"]) == 2

        # Get second page using 'after' cursor
        if page1.get("last_id"):
            response = client.get(f"/v1/organization/users?limit=2&after={page1['last_id']}")
            response.raise_for_status()
            page2 = response.json()

            assert len(page2["data"]) <= 2
            # Verify no overlap
            page1_ids = {user["id"] for user in page1["data"]}
            page2_ids = {user["id"] for user in page2["data"]}
            assert page1_ids.isdisjoint(page2_ids)

    def test_get_organization_user(self, client: FakeAIClient):
        """Test retrieving a specific organization user."""
        # Create a user
        response = client.post(
            "/v1/organization/users",
            json={"email": "getuser@example.com", "role": "owner"},
        )
        response.raise_for_status()
        user_id = response.json()["id"]

        # Get the user
        response = client.get(f"/v1/organization/users/{user_id}")
        response.raise_for_status()
        user = response.json()

        assert user["object"] == "organization.user"
        assert user["id"] == user_id
        assert user["email"] == "getuser@example.com"
        assert user["role"] == "owner"

    def test_get_organization_user_not_found(self, client: FakeAIClient):
        """Test getting non-existent organization user."""
        response = client.get("/v1/organization/users/user-nonexistent")
        assert response.status_code == 404

    def test_modify_organization_user(self, client: FakeAIClient):
        """Test modifying an organization user's role."""
        # Create a user with reader role
        response = client.post(
            "/v1/organization/users",
            json={"email": "modifyuser@example.com", "role": "reader"},
        )
        response.raise_for_status()
        user_id = response.json()["id"]
        assert response.json()["role"] == "reader"

        # Modify to owner role
        response = client.post(
            f"/v1/organization/users/{user_id}",
            json={"role": "owner"},
        )
        response.raise_for_status()
        modified_user = response.json()

        assert modified_user["id"] == user_id
        assert modified_user["role"] == "owner"

        # Verify change persisted
        response = client.get(f"/v1/organization/users/{user_id}")
        response.raise_for_status()
        assert response.json()["role"] == "owner"

    def test_delete_organization_user(self, client: FakeAIClient):
        """Test deleting an organization user."""
        # Create a user
        response = client.post(
            "/v1/organization/users",
            json={"email": "deleteuser@example.com", "role": "reader"},
        )
        response.raise_for_status()
        user_id = response.json()["id"]

        # Delete the user
        response = client.delete(f"/v1/organization/users/{user_id}")
        response.raise_for_status()
        deletion_result = response.json()

        assert deletion_result["object"] == "organization.user.deleted"
        assert deletion_result["id"] == user_id
        assert deletion_result["deleted"] is True

        # Verify user no longer exists
        response = client.get(f"/v1/organization/users/{user_id}")
        assert response.status_code == 404

    def test_delete_organization_user_cascades_to_projects(self, client: FakeAIClient):
        """Test that deleting an org user removes them from all projects."""
        # Create a user
        response = client.post(
            "/v1/organization/users",
            json={"email": "cascade@example.com", "role": "owner"},
        )
        response.raise_for_status()
        user_id = response.json()["id"]

        # Create a project
        response = client.post(
            "/v1/organization/projects",
            json={"name": "Cascade Test Project"},
        )
        response.raise_for_status()
        project_id = response.json()["id"]

        # Add user to project
        response = client.post(
            f"/v1/organization/projects/{project_id}/users",
            json={"user_id": user_id, "role": "member"},
        )
        response.raise_for_status()

        # Verify user is in project
        response = client.get(f"/v1/organization/projects/{project_id}/users")
        response.raise_for_status()
        project_users = response.json()["data"]
        assert any(u["id"] == user_id for u in project_users)

        # Delete the organization user
        response = client.delete(f"/v1/organization/users/{user_id}")
        response.raise_for_status()

        # Verify user is removed from project
        response = client.get(f"/v1/organization/projects/{project_id}/users")
        response.raise_for_status()
        project_users = response.json()["data"]
        assert not any(u["id"] == user_id for u in project_users)


@pytest.mark.integration
class TestOrganizationInvites:
    """Test organization invitation management."""

    def test_create_organization_invite(self, client: FakeAIClient):
        """Test creating an organization invite."""
        response = client.post(
            "/v1/organization/invites",
            json={
                "email": "invitee@example.com",
                "role": "reader",
            },
        )
        response.raise_for_status()
        invite = response.json()

        # Validate response structure
        assert invite["object"] == "organization.invite"
        assert invite["id"].startswith("invite-")
        assert invite["email"] == "invitee@example.com"
        assert invite["role"] == "reader"
        assert invite["status"] == "pending"
        assert "invited_at" in invite
        assert "expires_at" in invite
        assert invite["accepted_at"] is None

        # Verify expiration is ~7 days in future
        expires_delta = invite["expires_at"] - invite["invited_at"]
        assert 6 * 24 * 60 * 60 <= expires_delta <= 8 * 24 * 60 * 60

    def test_list_organization_invites(self, client: FakeAIClient):
        """Test listing organization invites."""
        # Create multiple invites
        invite_emails = [
            "invite1@example.com",
            "invite2@example.com",
            "invite3@example.com",
        ]
        created_ids = []

        for email in invite_emails:
            response = client.post(
                "/v1/organization/invites",
                json={"email": email, "role": "owner"},
            )
            response.raise_for_status()
            created_ids.append(response.json()["id"])

        # List all invites
        response = client.get("/v1/organization/invites")
        response.raise_for_status()
        data = response.json()

        # Validate response structure
        assert data["object"] == "list"
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 3

        # Verify created invites are in the list
        invite_ids = [inv["id"] for inv in data["data"]]
        for invite_id in created_ids:
            assert invite_id in invite_ids

    def test_list_organization_invites_pagination(self, client: FakeAIClient):
        """Test pagination for organization invites."""
        # Create multiple invites
        for i in range(5):
            client.post(
                "/v1/organization/invites",
                json={"email": f"invpaging{i}@example.com", "role": "reader"},
            )

        # Get first page
        response = client.get("/v1/organization/invites?limit=2")
        response.raise_for_status()
        page1 = response.json()

        assert len(page1["data"]) == 2

        # Get second page
        if page1.get("last_id"):
            response = client.get(
                f"/v1/organization/invites?limit=2&after={page1['last_id']}"
            )
            response.raise_for_status()
            page2 = response.json()

            assert len(page2["data"]) <= 2

    def test_get_organization_invite(self, client: FakeAIClient):
        """Test retrieving a specific organization invite."""
        # Create an invite
        response = client.post(
            "/v1/organization/invites",
            json={"email": "getinvite@example.com", "role": "owner"},
        )
        response.raise_for_status()
        invite_id = response.json()["id"]

        # Get the invite
        response = client.get(f"/v1/organization/invites/{invite_id}")
        response.raise_for_status()
        invite = response.json()

        assert invite["object"] == "organization.invite"
        assert invite["id"] == invite_id
        assert invite["email"] == "getinvite@example.com"
        assert invite["status"] == "pending"

    def test_get_organization_invite_not_found(self, client: FakeAIClient):
        """Test getting non-existent organization invite."""
        response = client.get("/v1/organization/invites/invite-nonexistent")
        assert response.status_code == 404

    def test_delete_organization_invite(self, client: FakeAIClient):
        """Test deleting an organization invite."""
        # Create an invite
        response = client.post(
            "/v1/organization/invites",
            json={"email": "deleteinvite@example.com", "role": "reader"},
        )
        response.raise_for_status()
        invite_id = response.json()["id"]

        # Delete the invite
        response = client.delete(f"/v1/organization/invites/{invite_id}")
        response.raise_for_status()
        deletion_result = response.json()

        assert deletion_result["object"] == "organization.invite.deleted"
        assert deletion_result["id"] == invite_id
        assert deletion_result["deleted"] is True

        # Verify invite no longer exists
        response = client.get(f"/v1/organization/invites/{invite_id}")
        assert response.status_code == 404


@pytest.mark.integration
class TestOrganizationProjects:
    """Test organization project management."""

    def test_create_organization_project(self, client: FakeAIClient):
        """Test creating a new project."""
        response = client.post(
            "/v1/organization/projects",
            json={"name": "My Test Project"},
        )
        response.raise_for_status()
        project = response.json()

        # Validate response structure
        assert project["object"] == "organization.project"
        assert project["id"].startswith("proj_")
        assert project["name"] == "My Test Project"
        assert project["status"] == "active"
        assert project["archived_at"] is None
        assert "created_at" in project
        assert isinstance(project["created_at"], int)

    def test_list_organization_projects(self, client: FakeAIClient):
        """Test listing organization projects."""
        # Create multiple projects
        project_names = ["Project Alpha", "Project Beta", "Project Gamma"]
        created_ids = []

        for name in project_names:
            response = client.post(
                "/v1/organization/projects",
                json={"name": name},
            )
            response.raise_for_status()
            created_ids.append(response.json()["id"])

        # List all projects
        response = client.get("/v1/organization/projects")
        response.raise_for_status()
        data = response.json()

        # Validate response structure
        assert data["object"] == "list"
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 3

        # Verify created projects are in the list
        project_ids = [proj["id"] for proj in data["data"]]
        for project_id in created_ids:
            assert project_id in project_ids

        # All should be active by default
        for proj in data["data"]:
            if proj["id"] in created_ids:
                assert proj["status"] == "active"

    def test_list_organization_projects_exclude_archived(self, client: FakeAIClient):
        """Test that archived projects are excluded by default."""
        # Create a project
        response = client.post(
            "/v1/organization/projects",
            json={"name": "Project to Archive"},
        )
        response.raise_for_status()
        project_id = response.json()["id"]

        # Archive the project
        response = client.post(f"/v1/organization/projects/{project_id}/archive")
        response.raise_for_status()

        # List projects (should exclude archived by default)
        response = client.get("/v1/organization/projects")
        response.raise_for_status()
        data = response.json()

        project_ids = [proj["id"] for proj in data["data"]]
        assert project_id not in project_ids

        # List with include_archived=true
        response = client.get("/v1/organization/projects?include_archived=true")
        response.raise_for_status()
        data = response.json()

        project_ids = [proj["id"] for proj in data["data"]]
        assert project_id in project_ids

    def test_list_organization_projects_pagination(self, client: FakeAIClient):
        """Test pagination for organization projects."""
        # Create multiple projects
        for i in range(5):
            client.post(
                "/v1/organization/projects",
                json={"name": f"Paging Project {i}"},
            )

        # Get first page
        response = client.get("/v1/organization/projects?limit=2")
        response.raise_for_status()
        page1 = response.json()

        assert len(page1["data"]) == 2

        # Get second page
        if page1.get("last_id"):
            response = client.get(
                f"/v1/organization/projects?limit=2&after={page1['last_id']}"
            )
            response.raise_for_status()
            page2 = response.json()

            assert len(page2["data"]) <= 2

    def test_get_organization_project(self, client: FakeAIClient):
        """Test retrieving a specific project."""
        # Create a project
        response = client.post(
            "/v1/organization/projects",
            json={"name": "Get Project Test"},
        )
        response.raise_for_status()
        project_id = response.json()["id"]

        # Get the project
        response = client.get(f"/v1/organization/projects/{project_id}")
        response.raise_for_status()
        project = response.json()

        assert project["object"] == "organization.project"
        assert project["id"] == project_id
        assert project["name"] == "Get Project Test"
        assert project["status"] == "active"

    def test_get_organization_project_not_found(self, client: FakeAIClient):
        """Test getting non-existent project."""
        response = client.get("/v1/organization/projects/proj_nonexistent")
        assert response.status_code == 404

    def test_modify_organization_project(self, client: FakeAIClient):
        """Test modifying a project's name."""
        # Create a project
        response = client.post(
            "/v1/organization/projects",
            json={"name": "Original Name"},
        )
        response.raise_for_status()
        project_id = response.json()["id"]

        # Modify the name
        response = client.post(
            f"/v1/organization/projects/{project_id}",
            json={"name": "Updated Name"},
        )
        response.raise_for_status()
        modified_project = response.json()

        assert modified_project["id"] == project_id
        assert modified_project["name"] == "Updated Name"

        # Verify change persisted
        response = client.get(f"/v1/organization/projects/{project_id}")
        response.raise_for_status()
        assert response.json()["name"] == "Updated Name"

    def test_archive_organization_project(self, client: FakeAIClient):
        """Test archiving a project."""
        # Create a project
        response = client.post(
            "/v1/organization/projects",
            json={"name": "Project to Archive"},
        )
        response.raise_for_status()
        project_id = response.json()["id"]

        # Archive the project
        response = client.post(f"/v1/organization/projects/{project_id}/archive")
        response.raise_for_status()
        archive_result = response.json()

        assert archive_result["object"] == "organization.project.archived"
        assert archive_result["id"] == project_id
        assert archive_result["archived"] is True

        # Verify project is archived
        response = client.get(f"/v1/organization/projects/{project_id}")
        response.raise_for_status()
        project = response.json()

        assert project["status"] == "archived"
        assert project["archived_at"] is not None
        assert isinstance(project["archived_at"], int)


@pytest.mark.integration
class TestProjectUsers:
    """Test project user management."""

    @pytest.fixture
    def project_id(self, client: FakeAIClient) -> str:
        """Create a test project."""
        response = client.post(
            "/v1/organization/projects",
            json={"name": "User Management Test Project"},
        )
        response.raise_for_status()
        return response.json()["id"]

    @pytest.fixture
    def org_user_id(self, client: FakeAIClient) -> str:
        """Create a test organization user."""
        response = client.post(
            "/v1/organization/users",
            json={"email": "projectmember@example.com", "role": "owner"},
        )
        response.raise_for_status()
        return response.json()["id"]

    def test_create_project_user(
        self, client: FakeAIClient, project_id: str, org_user_id: str
    ):
        """Test adding a user to a project."""
        response = client.post(
            f"/v1/organization/projects/{project_id}/users",
            json={
                "user_id": org_user_id,
                "role": "member",
            },
        )
        response.raise_for_status()
        project_user = response.json()

        # Validate response structure
        assert project_user["object"] == "organization.project.user"
        assert project_user["id"] == org_user_id
        assert project_user["role"] == "member"
        assert "name" in project_user
        assert "email" in project_user
        assert "added_at" in project_user

    def test_list_project_users(
        self, client: FakeAIClient, project_id: str, org_user_id: str
    ):
        """Test listing users in a project."""
        # Add user to project
        client.post(
            f"/v1/organization/projects/{project_id}/users",
            json={"user_id": org_user_id, "role": "member"},
        )

        # List project users
        response = client.get(f"/v1/organization/projects/{project_id}/users")
        response.raise_for_status()
        data = response.json()

        # Validate response structure
        assert data["object"] == "list"
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 1

        # Verify our user is in the list
        user_ids = [user["id"] for user in data["data"]]
        assert org_user_id in user_ids

    def test_list_project_users_pagination(self, client: FakeAIClient, project_id: str):
        """Test pagination for project users."""
        # Create and add multiple users
        for i in range(5):
            response = client.post(
                "/v1/organization/users",
                json={"email": f"projuser{i}@example.com", "role": "owner"},
            )
            response.raise_for_status()
            user_id = response.json()["id"]

            client.post(
                f"/v1/organization/projects/{project_id}/users",
                json={"user_id": user_id, "role": "member"},
            )

        # Get first page
        response = client.get(f"/v1/organization/projects/{project_id}/users?limit=2")
        response.raise_for_status()
        page1 = response.json()

        assert len(page1["data"]) == 2

    def test_get_project_user(
        self, client: FakeAIClient, project_id: str, org_user_id: str
    ):
        """Test retrieving a specific project user."""
        # Add user to project
        client.post(
            f"/v1/organization/projects/{project_id}/users",
            json={"user_id": org_user_id, "role": "owner"},
        )

        # Get the project user
        response = client.get(
            f"/v1/organization/projects/{project_id}/users/{org_user_id}"
        )
        response.raise_for_status()
        project_user = response.json()

        assert project_user["object"] == "organization.project.user"
        assert project_user["id"] == org_user_id
        assert project_user["role"] == "owner"

    def test_get_project_user_not_found(self, client: FakeAIClient, project_id: str):
        """Test getting non-existent project user."""
        response = client.get(
            f"/v1/organization/projects/{project_id}/users/user-nonexistent"
        )
        assert response.status_code == 404

    def test_modify_project_user(
        self, client: FakeAIClient, project_id: str, org_user_id: str
    ):
        """Test modifying a project user's role."""
        # Add user with member role
        client.post(
            f"/v1/organization/projects/{project_id}/users",
            json={"user_id": org_user_id, "role": "member"},
        )

        # Modify to owner role
        response = client.post(
            f"/v1/organization/projects/{project_id}/users/{org_user_id}",
            json={"role": "owner"},
        )
        response.raise_for_status()
        modified_user = response.json()

        assert modified_user["id"] == org_user_id
        assert modified_user["role"] == "owner"

        # Verify change persisted
        response = client.get(
            f"/v1/organization/projects/{project_id}/users/{org_user_id}"
        )
        response.raise_for_status()
        assert response.json()["role"] == "owner"

    def test_delete_project_user(
        self, client: FakeAIClient, project_id: str, org_user_id: str
    ):
        """Test removing a user from a project."""
        # Add user to project
        client.post(
            f"/v1/organization/projects/{project_id}/users",
            json={"user_id": org_user_id, "role": "member"},
        )

        # Remove the user
        response = client.delete(
            f"/v1/organization/projects/{project_id}/users/{org_user_id}"
        )
        response.raise_for_status()
        deletion_result = response.json()

        assert deletion_result["object"] == "organization.project.user.deleted"
        assert deletion_result["id"] == org_user_id
        assert deletion_result["deleted"] is True

        # Verify user no longer in project
        response = client.get(
            f"/v1/organization/projects/{project_id}/users/{org_user_id}"
        )
        assert response.status_code == 404


@pytest.mark.integration
class TestServiceAccounts:
    """Test service account management."""

    @pytest.fixture
    def project_id(self, client: FakeAIClient) -> str:
        """Create a test project."""
        response = client.post(
            "/v1/organization/projects",
            json={"name": "Service Account Test Project"},
        )
        response.raise_for_status()
        return response.json()["id"]

    def test_create_service_account(self, client: FakeAIClient, project_id: str):
        """Test creating a service account."""
        response = client.post(
            f"/v1/organization/projects/{project_id}/service_accounts",
            json={
                "name": "API Service Account",
                "role": "member",
            },
        )
        response.raise_for_status()
        service_account = response.json()

        # Validate response structure
        assert service_account["object"] == "organization.project.service_account"
        assert service_account["id"].startswith("svc_acct_")
        assert service_account["name"] == "API Service Account"
        assert service_account["role"] == "member"
        assert "created_at" in service_account

    def test_list_service_accounts(self, client: FakeAIClient, project_id: str):
        """Test listing service accounts in a project."""
        # Create multiple service accounts
        account_names = ["Account 1", "Account 2", "Account 3"]
        created_ids = []

        for name in account_names:
            response = client.post(
                f"/v1/organization/projects/{project_id}/service_accounts",
                json={"name": name, "role": "member"},
            )
            response.raise_for_status()
            created_ids.append(response.json()["id"])

        # List all service accounts
        response = client.get(
            f"/v1/organization/projects/{project_id}/service_accounts"
        )
        response.raise_for_status()
        data = response.json()

        # Validate response structure
        assert data["object"] == "list"
        assert isinstance(data["data"], list)
        assert len(data["data"]) >= 3

        # Verify created accounts are in the list
        account_ids = [acct["id"] for acct in data["data"]]
        for account_id in created_ids:
            assert account_id in account_ids

    def test_list_service_accounts_pagination(self, client: FakeAIClient, project_id: str):
        """Test pagination for service accounts."""
        # Create multiple service accounts
        for i in range(5):
            client.post(
                f"/v1/organization/projects/{project_id}/service_accounts",
                json={"name": f"Service Account {i}", "role": "member"},
            )

        # Get first page
        response = client.get(
            f"/v1/organization/projects/{project_id}/service_accounts?limit=2"
        )
        response.raise_for_status()
        page1 = response.json()

        assert len(page1["data"]) == 2

    def test_get_service_account(self, client: FakeAIClient, project_id: str):
        """Test retrieving a specific service account."""
        # Create a service account
        response = client.post(
            f"/v1/organization/projects/{project_id}/service_accounts",
            json={"name": "Get Test Account", "role": "owner"},
        )
        response.raise_for_status()
        account_id = response.json()["id"]

        # Get the service account
        response = client.get(
            f"/v1/organization/projects/{project_id}/service_accounts/{account_id}"
        )
        response.raise_for_status()
        account = response.json()

        assert account["object"] == "organization.project.service_account"
        assert account["id"] == account_id
        assert account["name"] == "Get Test Account"
        assert account["role"] == "owner"

    def test_get_service_account_not_found(self, client: FakeAIClient, project_id: str):
        """Test getting non-existent service account."""
        response = client.get(
            f"/v1/organization/projects/{project_id}/service_accounts/svc_acct_nonexistent"
        )
        assert response.status_code == 404

    def test_delete_service_account(self, client: FakeAIClient, project_id: str):
        """Test deleting a service account."""
        # Create a service account
        response = client.post(
            f"/v1/organization/projects/{project_id}/service_accounts",
            json={"name": "Delete Test Account", "role": "member"},
        )
        response.raise_for_status()
        account_id = response.json()["id"]

        # Delete the service account
        response = client.delete(
            f"/v1/organization/projects/{project_id}/service_accounts/{account_id}"
        )
        response.raise_for_status()
        deletion_result = response.json()

        assert deletion_result["object"] == "organization.project.service_account.deleted"
        assert deletion_result["id"] == account_id
        assert deletion_result["deleted"] is True

        # Verify account no longer exists
        response = client.get(
            f"/v1/organization/projects/{project_id}/service_accounts/{account_id}"
        )
        assert response.status_code == 404

    def test_service_account_default_role(self, client: FakeAIClient, project_id: str):
        """Test that service account defaults to member role."""
        response = client.post(
            f"/v1/organization/projects/{project_id}/service_accounts",
            json={"name": "Default Role Account"},
        )
        response.raise_for_status()
        account = response.json()

        # Should default to member role
        assert account["role"] == "member"


@pytest.mark.integration
class TestUsageTracking:
    """Test usage tracking per organization and project."""

    @pytest.fixture
    def project_id(self, client: FakeAIClient) -> str:
        """Create a test project."""
        response = client.post(
            "/v1/organization/projects",
            json={"name": "Usage Tracking Test Project"},
        )
        response.raise_for_status()
        return response.json()["id"]

    def test_get_completions_usage(self, client: FakeAIClient):
        """Test getting completions usage data."""
        # Make some chat completion requests to generate usage
        for _ in range(3):
            client.post(
                "/v1/chat/completions",
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [{"role": "user", "content": "Hello"}],
                },
            )

        # Query usage
        current_time = int(time.time())
        start_time = current_time - 3600  # 1 hour ago
        end_time = current_time

        response = client.get(
            f"/v1/organization/usage/completions?start_time={start_time}&end_time={end_time}&bucket_width=1h"
        )
        response.raise_for_status()
        usage = response.json()

        # Validate response structure
        assert "data" in usage
        assert isinstance(usage["data"], list)
        assert "has_more" in usage

        if len(usage["data"]) > 0:
            bucket = usage["data"][0]
            assert "start_time" in bucket
            assert "end_time" in bucket
            assert "results" in bucket
            assert isinstance(bucket["results"], list)

    def test_get_completions_usage_with_project_filter(
        self, client: FakeAIClient, project_id: str
    ):
        """Test getting completions usage filtered by project."""
        current_time = int(time.time())
        start_time = current_time - 3600
        end_time = current_time

        response = client.get(
            f"/v1/organization/usage/completions?start_time={start_time}&end_time={end_time}&project_id={project_id}"
        )
        response.raise_for_status()
        usage = response.json()

        assert "data" in usage
        assert isinstance(usage["data"], list)

    def test_get_completions_usage_with_model_filter(self, client: FakeAIClient):
        """Test getting completions usage filtered by model."""
        current_time = int(time.time())
        start_time = current_time - 3600
        end_time = current_time

        response = client.get(
            f"/v1/organization/usage/completions?start_time={start_time}&end_time={end_time}&model=openai/gpt-oss-120b"
        )
        response.raise_for_status()
        usage = response.json()

        assert "data" in usage
        assert isinstance(usage["data"], list)

    def test_get_embeddings_usage(self, client: FakeAIClient):
        """Test getting embeddings usage data."""
        # Make some embedding requests
        for _ in range(2):
            client.post(
                "/v1/embeddings",
                json={
                    "model": "text-embedding-ada-002",
                    "input": "Test embedding",
                },
            )

        # Query usage
        current_time = int(time.time())
        start_time = current_time - 3600
        end_time = current_time

        response = client.get(
            f"/v1/organization/usage/embeddings?start_time={start_time}&end_time={end_time}&bucket_width=1h"
        )
        response.raise_for_status()
        usage = response.json()

        assert "data" in usage
        assert isinstance(usage["data"], list)

    def test_get_images_usage(self, client: FakeAIClient):
        """Test getting images usage data."""
        current_time = int(time.time())
        start_time = current_time - 3600
        end_time = current_time

        response = client.get(
            f"/v1/organization/usage/images?start_time={start_time}&end_time={end_time}&bucket_width=1d"
        )
        response.raise_for_status()
        usage = response.json()

        assert "data" in usage
        assert isinstance(usage["data"], list)

    def test_get_audio_speeches_usage(self, client: FakeAIClient):
        """Test getting audio speeches usage data."""
        current_time = int(time.time())
        start_time = current_time - 3600
        end_time = current_time

        response = client.get(
            f"/v1/organization/usage/audio_speeches?start_time={start_time}&end_time={end_time}&bucket_width=1h"
        )
        response.raise_for_status()
        usage = response.json()

        assert "data" in usage
        assert isinstance(usage["data"], list)

    def test_get_audio_transcriptions_usage(self, client: FakeAIClient):
        """Test getting audio transcriptions usage data."""
        current_time = int(time.time())
        start_time = current_time - 3600
        end_time = current_time

        response = client.get(
            f"/v1/organization/usage/audio_transcriptions?start_time={start_time}&end_time={end_time}&bucket_width=1h"
        )
        response.raise_for_status()
        usage = response.json()

        assert "data" in usage
        assert isinstance(usage["data"], list)

    def test_usage_bucket_widths(self, client: FakeAIClient):
        """Test different bucket width options."""
        current_time = int(time.time())
        start_time = current_time - 86400  # 24 hours ago
        end_time = current_time

        for bucket_width in ["1m", "1h", "1d"]:
            response = client.get(
                f"/v1/organization/usage/completions?start_time={start_time}&end_time={end_time}&bucket_width={bucket_width}"
            )
            response.raise_for_status()
            usage = response.json()

            assert "data" in usage
            assert isinstance(usage["data"], list)


@pytest.mark.integration
class TestBillingAndCosts:
    """Test billing and cost tracking per organization."""

    def test_get_costs(self, client: FakeAIClient):
        """Test getting cost data."""
        current_time = int(time.time())
        start_time = current_time - 86400  # 24 hours ago
        end_time = current_time

        response = client.get(
            f"/v1/organization/costs?start_time={start_time}&end_time={end_time}&bucket_width=1d"
        )
        response.raise_for_status()
        costs = response.json()

        # Validate response structure
        assert "data" in costs
        assert isinstance(costs["data"], list)
        assert "has_more" in costs

    def test_get_costs_with_project_filter(self, client: FakeAIClient):
        """Test getting costs filtered by project."""
        # Create a project
        response = client.post(
            "/v1/organization/projects",
            json={"name": "Cost Tracking Project"},
        )
        response.raise_for_status()
        project_id = response.json()["id"]

        current_time = int(time.time())
        start_time = current_time - 86400
        end_time = current_time

        response = client.get(
            f"/v1/organization/costs?start_time={start_time}&end_time={end_time}&project_id={project_id}"
        )
        response.raise_for_status()
        costs = response.json()

        assert "data" in costs
        assert isinstance(costs["data"], list)

    def test_get_costs_with_grouping(self, client: FakeAIClient):
        """Test getting costs with grouping dimensions."""
        current_time = int(time.time())
        start_time = current_time - 86400
        end_time = current_time

        response = client.get(
            f"/v1/organization/costs?start_time={start_time}&end_time={end_time}&group_by=model&group_by=project_id"
        )
        response.raise_for_status()
        costs = response.json()

        assert "data" in costs
        assert isinstance(costs["data"], list)


@pytest.mark.integration
class TestRolesAndPermissions:
    """Test role validation and permissions."""

    def test_organization_roles(self, client: FakeAIClient):
        """Test valid organization roles."""
        for role in ["owner", "reader"]:
            response = client.post(
                "/v1/organization/users",
                json={"email": f"role-{role}@example.com", "role": role},
            )
            response.raise_for_status()
            user = response.json()
            assert user["role"] == role

    def test_project_roles(self, client: FakeAIClient):
        """Test valid project roles."""
        # Create project
        response = client.post(
            "/v1/organization/projects",
            json={"name": "Roles Test Project"},
        )
        response.raise_for_status()
        project_id = response.json()["id"]

        # Create org user
        response = client.post(
            "/v1/organization/users",
            json={"email": "projectrole@example.com", "role": "owner"},
        )
        response.raise_for_status()
        user_id = response.json()["id"]

        # Test project roles
        for role in ["owner", "member"]:
            response = client.post(
                f"/v1/organization/projects/{project_id}/users",
                json={"user_id": user_id, "role": role},
            )
            response.raise_for_status()
            project_user = response.json()
            assert project_user["role"] == role

            # Clean up for next iteration
            client.delete(f"/v1/organization/projects/{project_id}/users/{user_id}")

    def test_service_account_roles(self, client: FakeAIClient):
        """Test valid service account roles."""
        # Create project
        response = client.post(
            "/v1/organization/projects",
            json={"name": "Service Account Roles Test"},
        )
        response.raise_for_status()
        project_id = response.json()["id"]

        # Test service account roles
        for role in ["owner", "member"]:
            response = client.post(
                f"/v1/organization/projects/{project_id}/service_accounts",
                json={"name": f"Account with {role} role", "role": role},
            )
            response.raise_for_status()
            account = response.json()
            assert account["role"] == role
