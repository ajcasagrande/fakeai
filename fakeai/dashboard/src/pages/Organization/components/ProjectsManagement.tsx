/**
 * Projects Management Component
 * Manage organization projects with archive/restore functionality
 */

import React, { useState, useEffect } from 'react';
import { organizationAPI } from '../api';
import type { OrganizationProject } from '../types';

interface ProjectsManagementProps {
  onProjectSelect?: (projectId: string) => void;
  onRefresh?: () => void;
}

export const ProjectsManagement: React.FC<ProjectsManagementProps> = ({
  onProjectSelect,
  onRefresh,
}) => {
  const [projects, setProjects] = useState<OrganizationProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [editingProject, setEditingProject] = useState<OrganizationProject | null>(null);
  const [archivingProjectId, setArchivingProjectId] = useState<string | null>(null);
  const [showArchived, setShowArchived] = useState(false);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await organizationAPI.listProjects(100, undefined, showArchived);
      setProjects(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch projects');
      console.error('Error fetching projects:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [showArchived]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName) return;

    try {
      setLoading(true);
      await organizationAPI.createProject({ name: newProjectName });
      setShowCreateModal(false);
      setNewProjectName('');
      await fetchProjects();
      onRefresh?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProject = async (projectId: string, name: string) => {
    try {
      setLoading(true);
      await organizationAPI.modifyProject(projectId, { name });
      setEditingProject(null);
      await fetchProjects();
      onRefresh?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update project');
    } finally {
      setLoading(false);
    }
  };

  const handleArchiveProject = async (projectId: string) => {
    if (!confirm('Are you sure you want to archive this project?')) {
      return;
    }

    try {
      setLoading(true);
      setArchivingProjectId(projectId);
      await organizationAPI.archiveProject(projectId);
      await fetchProjects();
      onRefresh?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to archive project');
    } finally {
      setLoading(false);
      setArchivingProjectId(null);
    }
  };

  const getStatusBadgeClass = (status: string): string => {
    return status === 'active' ? 'badge-success' : 'badge-secondary';
  };

  return (
    <div className="projects-management">
      <div className="section-header">
        <div>
          <h2 className="section-title">Organization Projects</h2>
          <p className="section-subtitle">
            Manage your organization's projects and resources
          </p>
        </div>
        <div className="header-actions">
          <label className="toggle-archived">
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
            />
            <span>Show archived</span>
          </label>
          <button
            className="btn btn-primary"
            onClick={() => setShowCreateModal(true)}
            disabled={loading}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Project
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}

      {loading && projects.length === 0 ? (
        <div className="loading-container">
          <div className="loading"></div>
          <p>Loading projects...</p>
        </div>
      ) : (
        <div className="projects-grid">
          {projects.map((project) => (
            <div
              key={project.id}
              className={`project-card ${project.status === 'archived' ? 'archived' : ''}`}
            >
              <div className="project-card-header">
                <div className="project-info">
                  {editingProject?.id === project.id ? (
                    <input
                      type="text"
                      className="input project-name-input"
                      value={editingProject.name}
                      onChange={(e) =>
                        setEditingProject({ ...editingProject, name: e.target.value })
                      }
                      onBlur={() =>
                        handleUpdateProject(project.id, editingProject.name)
                      }
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleUpdateProject(project.id, editingProject.name);
                        } else if (e.key === 'Escape') {
                          setEditingProject(null);
                        }
                      }}
                      autoFocus
                    />
                  ) : (
                    <h3 className="project-name">{project.name}</h3>
                  )}
                  <span className={`badge ${getStatusBadgeClass(project.status)}`}>
                    {project.status}
                  </span>
                </div>
                <div className="project-actions">
                  {project.status === 'active' && (
                    <>
                      <button
                        className="btn-icon btn-secondary"
                        onClick={() => setEditingProject(project)}
                        disabled={loading}
                        title="Rename project"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button
                        className="btn-icon btn-warning"
                        onClick={() => handleArchiveProject(project.id)}
                        disabled={loading || archivingProjectId === project.id}
                        title="Archive project"
                      >
                        {archivingProjectId === project.id ? (
                          <div className="loading" style={{ width: '16px', height: '16px' }}></div>
                        ) : (
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                          </svg>
                        )}
                      </button>
                    </>
                  )}
                </div>
              </div>

              <div className="project-card-body">
                <div className="project-meta">
                  <div className="meta-item">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <span>Created {new Date(project.created_at * 1000).toLocaleDateString()}</span>
                  </div>
                  {project.archived_at && (
                    <div className="meta-item">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                      </svg>
                      <span>Archived {new Date(project.archived_at * 1000).toLocaleDateString()}</span>
                    </div>
                  )}
                </div>

                <div className="project-id">
                  <code>{project.id}</code>
                </div>
              </div>

              <div className="project-card-footer">
                <button
                  className="btn btn-secondary btn-block"
                  onClick={() => onProjectSelect?.(project.id)}
                  disabled={project.status === 'archived'}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  Manage Project
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {projects.length === 0 && !loading && (
        <div className="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
          <p>{showArchived ? 'No archived projects' : 'No projects yet'}</p>
          {!showArchived && (
            <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
              Create your first project
            </button>
          )}
        </div>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create New Project</h3>
              <button
                className="btn-icon"
                onClick={() => setShowCreateModal(false)}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <form onSubmit={handleCreateProject}>
              <div className="modal-body">
                <div className="form-group">
                  <label htmlFor="project-name">Project Name</label>
                  <input
                    id="project-name"
                    type="text"
                    className="input"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    placeholder="My AI Project"
                    required
                    autoFocus
                  />
                  <p className="help-text">
                    Give your project a descriptive name
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
                  disabled={loading || !newProjectName}
                >
                  {loading ? 'Creating...' : 'Create Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectsManagement;
