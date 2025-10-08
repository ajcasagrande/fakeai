/**
 * Service Accounts Management Component
 * Manage service accounts for API access within a project
 */

import React, { useState, useEffect } from 'react';
import { organizationAPI } from '../api';
import type { ServiceAccount, ServiceAccountRole } from '../types';

interface ServiceAccountsManagementProps {
  projectId: string;
  projectName: string;
  onBack: () => void;
}

export const ServiceAccountsManagement: React.FC<ServiceAccountsManagementProps> = ({
  projectId,
  projectName,
  onBack,
}) => {
  const [accounts, setAccounts] = useState<ServiceAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newAccountName, setNewAccountName] = useState('');
  const [newAccountRole, setNewAccountRole] = useState<ServiceAccountRole>('member');
  const [deletingAccountId, setDeletingAccountId] = useState<string | null>(null);

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await organizationAPI.listServiceAccounts(projectId, 100);
      setAccounts(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch service accounts');
      console.error('Error fetching service accounts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, [projectId]);

  const handleCreateAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAccountName) return;

    try {
      setLoading(true);
      await organizationAPI.createServiceAccount(projectId, {
        name: newAccountName,
        role: newAccountRole,
      });
      setShowCreateModal(false);
      setNewAccountName('');
      setNewAccountRole('member');
      await fetchAccounts();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create service account');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async (accountId: string) => {
    if (!confirm('Are you sure you want to delete this service account? This will revoke all API keys associated with it.')) {
      return;
    }

    try {
      setLoading(true);
      setDeletingAccountId(accountId);
      await organizationAPI.deleteServiceAccount(projectId, accountId);
      await fetchAccounts();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete service account');
    } finally {
      setLoading(false);
      setDeletingAccountId(null);
    }
  };

  const getRoleBadgeClass = (role: ServiceAccountRole): string => {
    return role === 'owner' ? 'badge-nvidia' : 'badge-secondary';
  };

  return (
    <div className="service-accounts-management">
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
          <h2 className="section-title">Service Accounts</h2>
          <p className="section-subtitle">
            Create and manage service accounts for programmatic API access
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
          disabled={loading}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Create Service Account
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

      {loading && accounts.length === 0 ? (
        <div className="loading-container">
          <div className="loading"></div>
          <p>Loading service accounts...</p>
        </div>
      ) : (
        <div className="accounts-grid">
          {accounts.map((account) => (
            <div key={account.id} className="account-card">
              <div className="account-card-header">
                <div className="account-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div className="account-info">
                  <h3 className="account-name">{account.name}</h3>
                  <span className={`badge ${getRoleBadgeClass(account.role)}`}>
                    {account.role}
                  </span>
                </div>
              </div>

              <div className="account-card-body">
                <div className="account-details">
                  <div className="detail-item">
                    <span className="detail-label">Account ID</span>
                    <code className="detail-value">{account.id}</code>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Created</span>
                    <span className="detail-value">
                      {new Date(account.created_at * 1000).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="account-permissions">
                  <h4 className="permissions-title">Permissions</h4>
                  <ul className="permissions-list">
                    <li>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      API Access
                    </li>
                    <li>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      {account.role === 'owner' ? 'Full Project Access' : 'Read Project Resources'}
                    </li>
                    {account.role === 'owner' && (
                      <li>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Manage Project Settings
                      </li>
                    )}
                  </ul>
                </div>
              </div>

              <div className="account-card-footer">
                <button
                  className="btn btn-danger btn-block"
                  onClick={() => handleDeleteAccount(account.id)}
                  disabled={loading || deletingAccountId === account.id}
                >
                  {deletingAccountId === account.id ? (
                    <>
                      <div className="loading" style={{ width: '16px', height: '16px' }}></div>
                      Deleting...
                    </>
                  ) : (
                    <>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      Delete Account
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {accounts.length === 0 && !loading && (
        <div className="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p>No service accounts yet</p>
          <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
            Create your first service account
          </button>
        </div>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create Service Account</h3>
              <button
                className="btn-icon"
                onClick={() => setShowCreateModal(false)}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <form onSubmit={handleCreateAccount}>
              <div className="modal-body">
                <div className="info-box">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p>
                    Service accounts provide programmatic access to your project resources.
                    Use them for automated workflows, CI/CD pipelines, and server-side applications.
                  </p>
                </div>
                <div className="form-group">
                  <label htmlFor="account-name">Account Name</label>
                  <input
                    id="account-name"
                    type="text"
                    className="input"
                    value={newAccountName}
                    onChange={(e) => setNewAccountName(e.target.value)}
                    placeholder="Production API Service"
                    required
                    autoFocus
                  />
                  <p className="help-text">
                    Choose a descriptive name to identify this service account
                  </p>
                </div>
                <div className="form-group">
                  <label htmlFor="account-role">Role</label>
                  <select
                    id="account-role"
                    className="input"
                    value={newAccountRole}
                    onChange={(e) => setNewAccountRole(e.target.value as ServiceAccountRole)}
                  >
                    <option value="member">Member</option>
                    <option value="owner">Owner</option>
                  </select>
                  <p className="help-text">
                    Owner: Full access to project resources and settings
                    <br />
                    Member: Can use project resources
                  </p>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowCreateModal(false)}
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading || !newAccountName}
                >
                  {loading ? 'Creating...' : 'Create Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ServiceAccountsManagement;
