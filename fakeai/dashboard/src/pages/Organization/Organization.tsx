/**
 * Organization Management Dashboard
 * Main component for managing organizations, users, projects, and service accounts
 */

import React, { useState } from 'react';
import { UsersManagement } from './components/UsersManagement';
import { InvitesManagement } from './components/InvitesManagement';
import { ProjectsManagement } from './components/ProjectsManagement';
import { ProjectUsersManagement } from './components/ProjectUsersManagement';
import { ServiceAccountsManagement } from './components/ServiceAccountsManagement';
import './styles.css';

type TabType = 'users' | 'invites' | 'projects';
type ViewType = 'overview' | 'project-users' | 'service-accounts';

interface ProjectContext {
  id: string;
  name: string;
}

export const Organization: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('users');
  const [currentView, setCurrentView] = useState<ViewType>('overview');
  const [selectedProject, setSelectedProject] = useState<ProjectContext | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
  };

  const handleProjectSelect = (projectId: string, action: 'users' | 'accounts') => {
    const project = selectedProject || { id: projectId, name: 'Project' };
    setSelectedProject(project);
    setCurrentView(action === 'users' ? 'project-users' : 'service-accounts');
  };

  const handleBackToOverview = () => {
    setCurrentView('overview');
    setSelectedProject(null);
  };

  const renderContent = () => {
    if (currentView === 'project-users' && selectedProject) {
      return (
        <ProjectUsersManagement
          projectId={selectedProject.id}
          projectName={selectedProject.name}
          onBack={handleBackToOverview}
        />
      );
    }

    if (currentView === 'service-accounts' && selectedProject) {
      return (
        <ServiceAccountsManagement
          projectId={selectedProject.id}
          projectName={selectedProject.name}
          onBack={handleBackToOverview}
        />
      );
    }

    switch (activeTab) {
      case 'users':
        return <UsersManagement key={refreshKey} onRefresh={handleRefresh} />;
      case 'invites':
        return <InvitesManagement key={refreshKey} onRefresh={handleRefresh} />;
      case 'projects':
        return (
          <ProjectsManagement
            key={refreshKey}
            onProjectSelect={(projectId) => handleProjectSelect(projectId, 'users')}
            onRefresh={handleRefresh}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="organization-dashboard">
      {currentView === 'overview' && (
        <>
          <div className="dashboard-header">
            <div className="header-content">
              <h1 className="dashboard-title">Organization Management</h1>
              <p className="dashboard-subtitle">
                Manage your organization's users, projects, and access control
              </p>
            </div>
            <div className="header-badges">
              <div className="info-badge">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <span>Admin Dashboard</span>
              </div>
            </div>
          </div>

          <div className="tabs-container">
            <div className="tabs">
              <button
                className={`tab ${activeTab === 'users' ? 'active' : ''}`}
                onClick={() => setActiveTab('users')}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                Users
              </button>
              <button
                className={`tab ${activeTab === 'invites' ? 'active' : ''}`}
                onClick={() => setActiveTab('invites')}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Invitations
              </button>
              <button
                className={`tab ${activeTab === 'projects' ? 'active' : ''}`}
                onClick={() => setActiveTab('projects')}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
                Projects
              </button>
            </div>
          </div>
        </>
      )}

      <div className="dashboard-content">
        {renderContent()}
      </div>

      {currentView === 'overview' && (
        <div className="dashboard-info">
          <div className="info-card">
            <div className="info-card-header">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3>Quick Guide</h3>
            </div>
            <div className="info-card-body">
              <div className="guide-section">
                <h4>Users Tab</h4>
                <p>Add and manage organization members with owner or reader roles.</p>
              </div>
              <div className="guide-section">
                <h4>Invitations Tab</h4>
                <p>Send email invitations to new users. Invites expire after 7 days.</p>
              </div>
              <div className="guide-section">
                <h4>Projects Tab</h4>
                <p>Create projects, assign users, create service accounts, and manage API keys.</p>
              </div>
            </div>
          </div>

          <div className="info-card">
            <div className="info-card-header">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <h3>Role Permissions</h3>
            </div>
            <div className="info-card-body">
              <div className="permissions-grid">
                <div className="permission-item">
                  <strong>Organization Owner</strong>
                  <p>Full access to all organization resources and settings</p>
                </div>
                <div className="permission-item">
                  <strong>Organization Reader</strong>
                  <p>Read-only access to organization resources</p>
                </div>
                <div className="permission-item">
                  <strong>Project Owner</strong>
                  <p>Full control over project resources and members</p>
                </div>
                <div className="permission-item">
                  <strong>Project Member</strong>
                  <p>Can use project resources via API</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Organization;
