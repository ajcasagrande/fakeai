/**
 * Organization Users Management Component
 * Displays and manages organization users with roles
 */

import React, { useState, useEffect } from 'react';
import { organizationAPI } from '../api';
import type { OrganizationUser, OrganizationRole } from '../types';

interface UsersManagementProps {
  onRefresh?: () => void;
}

export const UsersManagement: React.FC<UsersManagementProps> = ({ onRefresh }) => {
  const [users, setUsers] = useState<OrganizationUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserRole, setNewUserRole] = useState<OrganizationRole>('reader');
  const [editingUser, setEditingUser] = useState<OrganizationUser | null>(null);
  const [deletingUserId, setDeletingUserId] = useState<string | null>(null);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await organizationAPI.listUsers(100);
      setUsers(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch users');
      console.error('Error fetching users:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUserEmail) return;

    try {
      setLoading(true);
      await organizationAPI.createUser({
        email: newUserEmail,
        role: newUserRole,
      });
      setShowAddModal(false);
      setNewUserEmail('');
      setNewUserRole('reader');
      await fetchUsers();
      onRefresh?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add user');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateRole = async (userId: string, role: OrganizationRole) => {
    try {
      setLoading(true);
      await organizationAPI.modifyUser(userId, { role });
      setEditingUser(null);
      await fetchUsers();
      onRefresh?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to remove this user? This will also remove them from all projects.')) {
      return;
    }

    try {
      setLoading(true);
      setDeletingUserId(userId);
      await organizationAPI.deleteUser(userId);
      await fetchUsers();
      onRefresh?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete user');
    } finally {
      setLoading(false);
      setDeletingUserId(null);
    }
  };

  const getRoleBadgeClass = (role: OrganizationRole): string => {
    return role === 'owner' ? 'badge-nvidia' : 'badge-secondary';
  };

  return (
    <div className="users-management">
      <div className="section-header">
        <div>
          <h2 className="section-title">Organization Users</h2>
          <p className="section-subtitle">
            Manage users and their roles in your organization
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

      {loading && users.length === 0 ? (
        <div className="loading-container">
          <div className="loading"></div>
          <p>Loading users...</p>
        </div>
      ) : (
        <div className="users-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Added</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
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
                            role: e.target.value as OrganizationRole,
                          })
                        }
                      >
                        <option value="owner">Owner</option>
                        <option value="reader">Reader</option>
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
                            onClick={() => handleDeleteUser(user.id)}
                            disabled={loading || deletingUserId === user.id}
                            title="Remove user"
                          >
                            {deletingUserId === user.id ? (
                              <div className="loading" style={{ width: '16px', height: '16px' }}></div>
                            ) : (
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
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

          {users.length === 0 && !loading && (
            <div className="empty-state">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <p>No users yet</p>
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
              <h3>Add Organization User</h3>
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
                  <label htmlFor="user-email">Email Address</label>
                  <input
                    id="user-email"
                    type="email"
                    className="input"
                    value={newUserEmail}
                    onChange={(e) => setNewUserEmail(e.target.value)}
                    placeholder="user@example.com"
                    required
                    autoFocus
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="user-role">Role</label>
                  <select
                    id="user-role"
                    className="input"
                    value={newUserRole}
                    onChange={(e) => setNewUserRole(e.target.value as OrganizationRole)}
                  >
                    <option value="reader">Reader</option>
                    <option value="owner">Owner</option>
                  </select>
                  <p className="help-text">
                    Owner: Full access to organization settings and resources
                    <br />
                    Reader: Read-only access to organization resources
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
                  disabled={loading || !newUserEmail}
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

export default UsersManagement;
