/**
 * Organization API Client
 * Handles all API calls to /v1/organization/* endpoints
 */

import axios, { AxiosInstance } from 'axios';
import type {
  OrganizationUser,
  OrganizationUserListResponse,
  CreateOrganizationUserRequest,
  ModifyOrganizationUserRequest,
  DeleteOrganizationUserResponse,
  OrganizationInvite,
  OrganizationInviteListResponse,
  CreateOrganizationInviteRequest,
  DeleteOrganizationInviteResponse,
  OrganizationProject,
  OrganizationProjectListResponse,
  CreateOrganizationProjectRequest,
  ModifyOrganizationProjectRequest,
  ArchiveOrganizationProjectResponse,
  ProjectUser,
  ProjectUserListResponse,
  CreateProjectUserRequest,
  ModifyProjectUserRequest,
  DeleteProjectUserResponse,
  ServiceAccount,
  ServiceAccountListResponse,
  CreateServiceAccountRequest,
  DeleteServiceAccountResponse,
} from './types';

class OrganizationAPI {
  private client: AxiosInstance;

  constructor(baseURL: string = '/v1') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // ============================================================================
  // Organization Users
  // ============================================================================

  async listUsers(limit: number = 20, after?: string): Promise<OrganizationUserListResponse> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (after) params.append('after', after);
    const response = await this.client.get<OrganizationUserListResponse>(
      '/organization/users?' + params.toString()
    );
    return response.data;
  }

  async getUser(userId: string): Promise<OrganizationUser> {
    const response = await this.client.get<OrganizationUser>(
      `/organization/users/${userId}`
    );
    return response.data;
  }

  async createUser(data: CreateOrganizationUserRequest): Promise<OrganizationUser> {
    const response = await this.client.post<OrganizationUser>(
      '/organization/users',
      data
    );
    return response.data;
  }

  async modifyUser(
    userId: string,
    data: ModifyOrganizationUserRequest
  ): Promise<OrganizationUser> {
    const response = await this.client.post<OrganizationUser>(
      `/organization/users/${userId}`,
      data
    );
    return response.data;
  }

  async deleteUser(userId: string): Promise<DeleteOrganizationUserResponse> {
    const response = await this.client.delete<DeleteOrganizationUserResponse>(
      `/organization/users/${userId}`
    );
    return response.data;
  }

  // ============================================================================
  // Organization Invites
  // ============================================================================

  async listInvites(limit: number = 20, after?: string): Promise<OrganizationInviteListResponse> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (after) params.append('after', after);
    const response = await this.client.get<OrganizationInviteListResponse>(
      '/organization/invites?' + params.toString()
    );
    return response.data;
  }

  async getInvite(inviteId: string): Promise<OrganizationInvite> {
    const response = await this.client.get<OrganizationInvite>(
      `/organization/invites/${inviteId}`
    );
    return response.data;
  }

  async createInvite(data: CreateOrganizationInviteRequest): Promise<OrganizationInvite> {
    const response = await this.client.post<OrganizationInvite>(
      '/organization/invites',
      data
    );
    return response.data;
  }

  async deleteInvite(inviteId: string): Promise<DeleteOrganizationInviteResponse> {
    const response = await this.client.delete<DeleteOrganizationInviteResponse>(
      `/organization/invites/${inviteId}`
    );
    return response.data;
  }

  // ============================================================================
  // Organization Projects
  // ============================================================================

  async listProjects(
    limit: number = 20,
    after?: string,
    includeArchived: boolean = false
  ): Promise<OrganizationProjectListResponse> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (after) params.append('after', after);
    if (includeArchived) params.append('include_archived', 'true');
    const response = await this.client.get<OrganizationProjectListResponse>(
      '/organization/projects?' + params.toString()
    );
    return response.data;
  }

  async getProject(projectId: string): Promise<OrganizationProject> {
    const response = await this.client.get<OrganizationProject>(
      `/organization/projects/${projectId}`
    );
    return response.data;
  }

  async createProject(data: CreateOrganizationProjectRequest): Promise<OrganizationProject> {
    const response = await this.client.post<OrganizationProject>(
      '/organization/projects',
      data
    );
    return response.data;
  }

  async modifyProject(
    projectId: string,
    data: ModifyOrganizationProjectRequest
  ): Promise<OrganizationProject> {
    const response = await this.client.post<OrganizationProject>(
      `/organization/projects/${projectId}`,
      data
    );
    return response.data;
  }

  async archiveProject(projectId: string): Promise<ArchiveOrganizationProjectResponse> {
    const response = await this.client.post<ArchiveOrganizationProjectResponse>(
      `/organization/projects/${projectId}/archive`
    );
    return response.data;
  }

  // ============================================================================
  // Project Users
  // ============================================================================

  async listProjectUsers(
    projectId: string,
    limit: number = 20,
    after?: string
  ): Promise<ProjectUserListResponse> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (after) params.append('after', after);
    const response = await this.client.get<ProjectUserListResponse>(
      `/organization/projects/${projectId}/users?` + params.toString()
    );
    return response.data;
  }

  async getProjectUser(projectId: string, userId: string): Promise<ProjectUser> {
    const response = await this.client.get<ProjectUser>(
      `/organization/projects/${projectId}/users/${userId}`
    );
    return response.data;
  }

  async addProjectUser(
    projectId: string,
    data: CreateProjectUserRequest
  ): Promise<ProjectUser> {
    const response = await this.client.post<ProjectUser>(
      `/organization/projects/${projectId}/users`,
      data
    );
    return response.data;
  }

  async modifyProjectUser(
    projectId: string,
    userId: string,
    data: ModifyProjectUserRequest
  ): Promise<ProjectUser> {
    const response = await this.client.post<ProjectUser>(
      `/organization/projects/${projectId}/users/${userId}`,
      data
    );
    return response.data;
  }

  async removeProjectUser(
    projectId: string,
    userId: string
  ): Promise<DeleteProjectUserResponse> {
    const response = await this.client.delete<DeleteProjectUserResponse>(
      `/organization/projects/${projectId}/users/${userId}`
    );
    return response.data;
  }

  // ============================================================================
  // Service Accounts
  // ============================================================================

  async listServiceAccounts(
    projectId: string,
    limit: number = 20,
    after?: string
  ): Promise<ServiceAccountListResponse> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (after) params.append('after', after);
    const response = await this.client.get<ServiceAccountListResponse>(
      `/organization/projects/${projectId}/service_accounts?` + params.toString()
    );
    return response.data;
  }

  async getServiceAccount(projectId: string, accountId: string): Promise<ServiceAccount> {
    const response = await this.client.get<ServiceAccount>(
      `/organization/projects/${projectId}/service_accounts/${accountId}`
    );
    return response.data;
  }

  async createServiceAccount(
    projectId: string,
    data: CreateServiceAccountRequest
  ): Promise<ServiceAccount> {
    const response = await this.client.post<ServiceAccount>(
      `/organization/projects/${projectId}/service_accounts`,
      data
    );
    return response.data;
  }

  async deleteServiceAccount(
    projectId: string,
    accountId: string
  ): Promise<DeleteServiceAccountResponse> {
    const response = await this.client.delete<DeleteServiceAccountResponse>(
      `/organization/projects/${projectId}/service_accounts/${accountId}`
    );
    return response.data;
  }
}

export const organizationAPI = new OrganizationAPI();
export default organizationAPI;
