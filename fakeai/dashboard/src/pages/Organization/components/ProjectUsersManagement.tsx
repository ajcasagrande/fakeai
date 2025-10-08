/**
 * Project Users Management Component
 * Manage users within a specific project
 */

import React, { useState, useEffect } from 'react';
import { organizationAPI } from '../api';
import type { ProjectUser, ProjectRole, OrganizationUser } from '../types';

interface ProjectUsersManagementProps {
  projectId: string;
  projectName: string;
  onBack: () => void;
}

export const ProjectUsersManagement: React.FC<ProjectUsersManagementProps> = ({
  projectId,
  projectName,
  onBack,
}) => {
  const [projectUsers, setProjectUsers] = useState<ProjectUser[]>([]);
  const [orgUsers, setOrgUsers] = useState<OrganizationUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedRole, setSelectedRole] = useState<ProjectRole>('member');
  const [editingUser, setEditingUser] = useState<ProjectUser | null>(null);
  const [removingUserId, setRemovingUserId] = useState<string | null>(null);

  const fetchProjectUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await organizationAPI.listProjectUsers(projectId, 100);
      setProjectUsers(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch project users');
      console.error('Error fetching project users:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchOrgUsers = async () => {
    try {
      const response = await organizationAPI.listUsers(100);
      setOrgUsers(response.data);
    } catch (err) {
      console.error('Error fetching org users:', err);
    }
  };

  useEffect(() => {
    fetchProjectUsers();
    fetchOrgUsers();
  }, [projectId]);

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUserId) return;

    try {
      setLoading(true);
      await organizationAPI.addProjectUser(projectId, {
        user_id: selectedUserId,
        role: selectedRole,
      });
      setShowAddModal(false);
      setSelectedUserId('');
      setSelectedRole('member');
      await fetchProjectUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add user');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateRole = async (userId: string, role: ProjectRole) => {
    try {
      setLoading(true);
      await organizationAPI.modifyProjectUser(projectId, userId, { role });
      setEditingUser(null);
      await fetchProjectUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveUser = async (userId: string) => {
    if (!confirm('Are you sure you want to remove this user from the project?')) {
      return;
    }

    try {
      setLoading(true);
      setRemovingUserId(userId);
      await organizationAPI.removeProjectUser(projectId, userId);
      await fetchProjectUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove user');
    } finally {
      setLoading(false);
      setRemovingUserId(null);
    }
  };

  const getAvailableUsers = () => {
    const projectUserIds = new Set(projectUsers.map((u) => u.id));
    return orgUsers.filter((u) => !projectUserIds.has(u.id));
  };

  const getRoleBadgeClass = (role: ProjectRole): string => {
    return role === 'owner' ? 'badge-nvidia' : 'badge-secondary';
  };

  return (
    <div className="project-users-management">
      <div className="breadcrumb">
        <button className="breadcrumb-link" onClick={onBack}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Projects
        </button>
        <span className="breadcrumb-separator">/</span>
        <span className="breadcrumb-current">{projectName}</span>
      </div>

      <div className="section-header">
        <div>
          <h2 className="section-title">Project Users</h2>
          <p className="section-subtitle">
            Manage user access and permissions for this project
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowAddModal(true)}
          disabled={loading}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add User
        </button>
      </div>

      {error && (
        <div className="error-banner">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}

      {loading && projectUsers.length === 0 ? (
        <div className="loading-container">
          <div className="loading"></div>
          <p>Loading project users...</p>
        </div>
      ) : (
        <div className="users-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Project Role</th>
                <th>Added</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {projectUsers.map((user) => (
                <tr key={user.id}>
                  <td>
                    <div className="user-info">
                      <div className="user-avatar">
                        {user.name.charAt(0).toUpperCase()}
                      </div>
                      <span className="user-name">{user.name}</span>
                    </div>
                  </td>
                  <td>{user.email}</td>
                  <td>
                    {editingUser?.id === user.id ? (
                      <select
                        className="role-select"
                        value={editingUser.role}
                        onChange={(e) =>
                          setEditingUser({
                            ...editingUser,
                            role: e.target.value as ProjectRole,
                          })
                        }
                      >
                        <option value="owner">Owner</option>
                        <option value="member">Member</option>
                      </select>
                    ) : (
                      <span className={`badge ${getRoleBadgeClass(user.role)}`}>
                        {user.role}
                      </span>
                    )}
                  </td>
                  <td>{new Date(user.added_at * 1000).toLocaleDateString()}</td>
                  <td>
                    <div className="action-buttons">
                      {editingUser?.id === user.id ? (
                        <>
                          <button
                            className="btn-icon btn-success"
                            onClick={() => handleUpdateRole(user.id, editingUser.role)}
                            disabled={loading}
                            title="Save"
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          </button>
                          <button
                            className="btn-icon btn-secondary"
                            onClick={() => setEditingUser(null)}
                            disabled={loading}
                            title="Cancel"
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            className="btn-icon btn-secondary"
                            onClick={() => setEditingUser(user)}
                            disabled={loading}
                            title="Edit role"
                          >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </button>
                          <button
                            className="btn-icon btn-danger"
                            onClick={() => handleRemoveUser(user.id)}
                            disabled={loading || removingUserId === user.id}
                            title="Remove from project"
                          >
                            {removingUserId === user.id ? (
                              <div className="loading" style={{ width: '16px', height: '16px' }}></div>
                            ) : (
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7a4 4 0 11-8 0 4 4 0 018 0zM9 14a6 6 0 00-6 6v1h12v-1a6 6 0 00-6-6zM21 12h-6" />
                              </svg>
                            )}
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {projectUsers.length === 0 && !loading && (
            <div className="empty-state">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <p>No users in this project</p>
              <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
                Add your first user
              </button>
            </div>
          )}
        </div>
      )}

      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add User to Project</h3>
              <button
                className="btn-icon"
                onClick={() => setShowAddModal(false)}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <form onSubmit={handleAddUser}>
              <div className="modal-body">
                <div className="form-group">
                  <label htmlFor="user-select">Organization User</label>
                  <select
                    id="user-select"
                    className="input"
                    value={selectedUserId}
                    onChange={(e) => setSelectedUserId(e.target.value)}
                    required
                  >
                    <option value="">Select a user...</option>
                    {getAvailableUsers().map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.name} ({user.email})
                      </option>
                    ))}
                  </select>
                  {getAvailableUsers().length === 0 && (
                    <p className="help-text text-warning">
                      All organization users are already in this project
                    </p>
                  )}
                </div>
                <div className="form-group">
                  <label htmlFor="user-role">Project Role</label>
                  <select
                    id="user-role"
                    className="input"
                    value={selectedRole}
                    onChange={(e) => setSelectedRole(e.target.value as ProjectRole)}
                  >
                    <option value="member">Member</option>
                    <option value="owner">Owner</option>
                  </select>
                  <p className="help-text">
                    Owner: Full control over project resources
                    <br />
                    Member: Can use project resources
                  </p>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowAddModal(false)}
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading || !selectedUserId}
                >
                  {loading ? 'Adding...' : 'Add User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectUsersManagement;
