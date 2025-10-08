/**
 * TypeScript type definitions for Organization Management
 */

export type OrganizationRole = 'owner' | 'reader';
export type ProjectRole = 'owner' | 'member';
export type ServiceAccountRole = 'owner' | 'member';
export type InviteStatus = 'pending' | 'accepted' | 'expired';
export type ProjectStatus = 'active' | 'archived';

export interface OrganizationUser {
  object: 'organization.user';
  id: string;
  name: string;
  email: string;
  role: OrganizationRole;
  added_at: number;
}

export interface OrganizationUserListResponse {
  object: 'list';
  data: OrganizationUser[];
  first_id: string | null;
  last_id: string | null;
  has_more: boolean;
}

export interface CreateOrganizationUserRequest {
  email: string;
  role: OrganizationRole;
}

export interface ModifyOrganizationUserRequest {
  role: OrganizationRole;
}

export interface DeleteOrganizationUserResponse {
  object: 'organization.user.deleted';
  id: string;
  deleted: boolean;
}

export interface OrganizationInvite {
  object: 'organization.invite';
  id: string;
  email: string;
  role: OrganizationRole;
  status: InviteStatus;
  invited_at: number;
  expires_at: number;
  accepted_at: number | null;
}

export interface OrganizationInviteListResponse {
  object: 'list';
  data: OrganizationInvite[];
  first_id: string | null;
  last_id: string | null;
  has_more: boolean;
}

export interface CreateOrganizationInviteRequest {
  email: string;
  role: OrganizationRole;
}

export interface DeleteOrganizationInviteResponse {
  object: 'organization.invite.deleted';
  id: string;
  deleted: boolean;
}

export interface OrganizationProject {
  object: 'organization.project';
  id: string;
  name: string;
  created_at: number;
  archived_at: number | null;
  status: ProjectStatus;
}

export interface OrganizationProjectListResponse {
  object: 'list';
  data: OrganizationProject[];
  first_id: string | null;
  last_id: string | null;
  has_more: boolean;
}

export interface CreateOrganizationProjectRequest {
  name: string;
}

export interface ModifyOrganizationProjectRequest {
  name: string;
}

export interface ArchiveOrganizationProjectResponse {
  object: 'organization.project.archived';
  id: string;
  archived: boolean;
}

export interface ProjectUser {
  object: 'organization.project.user';
  id: string;
  name: string;
  email: string;
  role: ProjectRole;
  added_at: number;
}

export interface ProjectUserListResponse {
  object: 'list';
  data: ProjectUser[];
  first_id: string | null;
  last_id: string | null;
  has_more: boolean;
}

export interface CreateProjectUserRequest {
  user_id: string;
  role: ProjectRole;
}

export interface ModifyProjectUserRequest {
  role: ProjectRole;
}

export interface DeleteProjectUserResponse {
  object: 'organization.project.user.deleted';
  id: string;
  deleted: boolean;
}

export interface ServiceAccount {
  object: 'organization.project.service_account';
  id: string;
  name: string;
  role: ServiceAccountRole;
  created_at: number;
}

export interface ServiceAccountListResponse {
  object: 'list';
  data: ServiceAccount[];
  first_id: string | null;
  last_id: string | null;
  has_more: boolean;
}

export interface CreateServiceAccountRequest {
  name: string;
  role?: ServiceAccountRole;
}

export interface DeleteServiceAccountResponse {
  object: 'organization.project.service_account.deleted';
  id: string;
  deleted: boolean;
}
