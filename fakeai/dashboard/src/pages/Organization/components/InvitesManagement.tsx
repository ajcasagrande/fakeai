/**
 * Organization Invites Management Component
 * Manage organization invitations
 */

import React, { useState, useEffect } from 'react';
import { organizationAPI } from '../api';
import type { OrganizationInvite, OrganizationRole, InviteStatus } from '../types';

interface InvitesManagementProps {
  onRefresh?: () => void;
}

export const InvitesManagement: React.FC<InvitesManagementProps> = ({ onRefresh }) => {
  const [invites, setInvites] = useState<OrganizationInvite[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [newInviteEmail, setNewInviteEmail] = useState('');
  const [newInviteRole, setNewInviteRole] = useState<OrganizationRole>('reader');
  const [deletingInviteId, setDeletingInviteId] = useState<string | null>(null);

  const fetchInvites = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await organizationAPI.listInvites(100);
      setInvites(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch invites');
      console.error('Error fetching invites:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvites();
  }, []);

  const handleSendInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newInviteEmail) return;

    try {
      setLoading(true);
      await organizationAPI.createInvite({
        email: newInviteEmail,
        role: newInviteRole,
      });
      setShowInviteModal(false);
      setNewInviteEmail('');
      setNewInviteRole('reader');
      await fetchInvites();
      onRefresh?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send invite');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteInvite = async (inviteId: string) => {
    if (!confirm('Are you sure you want to delete this invitation?')) {
      return;
    }

    try {
      setLoading(true);
      setDeletingInviteId(inviteId);
      await organizationAPI.deleteInvite(inviteId);
      await fetchInvites();
      onRefresh?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete invite');
    } finally {
      setLoading(false);
      setDeletingInviteId(null);
    }
  };

  const getStatusBadgeClass = (status: InviteStatus): string => {
    switch (status) {
      case 'pending':
        return 'badge-warning';
      case 'accepted':
        return 'badge-success';
      case 'expired':
        return 'badge-error';
      default:
        return 'badge-secondary';
    }
  };

  const getRoleBadgeClass = (role: OrganizationRole): string => {
    return role === 'owner' ? 'badge-nvidia' : 'badge-secondary';
  };

  const formatExpiresIn = (expiresAt: number): string => {
    const now = Date.now() / 1000;
    const diff = expiresAt - now;

    if (diff < 0) return 'Expired';

    const days = Math.floor(diff / (24 * 60 * 60));
    const hours = Math.floor((diff % (24 * 60 * 60)) / (60 * 60));

    if (days > 0) return `${days} day${days > 1 ? 's' : ''}`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''}`;
    return 'Less than 1 hour';
  };

  return (
    <div className="invites-management">
      <div className="section-header">
        <div>
          <h2 className="section-title">Organization Invitations</h2>
          <p className="section-subtitle">
            Send and manage invitations to join your organization
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowInviteModal(true)}
          disabled={loading}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          Send Invite
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

      {loading && invites.length === 0 ? (
        <div className="loading-container">
          <div className="loading"></div>
          <p>Loading invitations...</p>
        </div>
      ) : (
        <div className="invites-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Invited</th>
                <th>Expires</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invites.map((invite) => (
                <tr key={invite.id}>
                  <td>
                    <div className="invite-email">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      {invite.email}
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${getRoleBadgeClass(invite.role)}`}>
                      {invite.role}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${getStatusBadgeClass(invite.status)}`}>
                      {invite.status}
                    </span>
                  </td>
                  <td>{new Date(invite.invited_at * 1000).toLocaleDateString()}</td>
                  <td>
                    {invite.status === 'pending' ? (
                      <span className="expires-in">
                        {formatExpiresIn(invite.expires_at)}
                      </span>
                    ) : (
                      <span className="text-tertiary">-</span>
                    )}
                  </td>
                  <td>
                    <div className="action-buttons">
                      {invite.status === 'pending' && (
                        <button
                          className="btn-icon btn-danger"
                          onClick={() => handleDeleteInvite(invite.id)}
                          disabled={loading || deletingInviteId === invite.id}
                          title="Delete invitation"
                        >
                          {deletingInviteId === invite.id ? (
                            <div className="loading" style={{ width: '16px', height: '16px' }}></div>
                          ) : (
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          )}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {invites.length === 0 && !loading && (
            <div className="empty-state">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <p>No pending invitations</p>
              <button className="btn btn-primary" onClick={() => setShowInviteModal(true)}>
                Send your first invitation
              </button>
            </div>
          )}
        </div>
      )}

      {showInviteModal && (
        <div className="modal-overlay" onClick={() => setShowInviteModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Send Organization Invitation</h3>
              <button
                className="btn-icon"
                onClick={() => setShowInviteModal(false)}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <form onSubmit={handleSendInvite}>
              <div className="modal-body">
                <div className="form-group">
                  <label htmlFor="invite-email">Email Address</label>
                  <input
                    id="invite-email"
                    type="email"
                    className="input"
                    value={newInviteEmail}
                    onChange={(e) => setNewInviteEmail(e.target.value)}
                    placeholder="user@example.com"
                    required
                    autoFocus
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="invite-role">Role</label>
                  <select
                    id="invite-role"
                    className="input"
                    value={newInviteRole}
                    onChange={(e) => setNewInviteRole(e.target.value as OrganizationRole)}
                  >
                    <option value="reader">Reader</option>
                    <option value="owner">Owner</option>
                  </select>
                  <p className="help-text">
                    The invitation will expire in 7 days
                  </p>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowInviteModal(false)}
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading || !newInviteEmail}
                >
                  {loading ? 'Sending...' : 'Send Invitation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default InvitesManagement;
