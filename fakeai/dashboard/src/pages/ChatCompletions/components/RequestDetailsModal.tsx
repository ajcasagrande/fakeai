/**
 * Request Details Modal Component
 * Displays full request and response data in a modal
 */

import React, { useState } from 'react';
import { ChatRequest } from '../types';

interface RequestDetailsModalProps {
  request: ChatRequest | null;
  onClose: () => void;
}

export const RequestDetailsModal: React.FC<RequestDetailsModalProps> = ({ request, onClose }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'request' | 'response'>('overview');

  if (!request) return null;

  const formatDate = (timestamp: number): string => {
    return new Date(timestamp).toLocaleString();
  };

  const formatJSON = (data: any): string => {
    try {
      return JSON.stringify(data, null, 2);
    } catch {
      return 'Unable to format data';
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content request-details-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Request Details</h2>
          <button className="modal-close-btn" onClick={onClose}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="modal-tabs">
          <button
            className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            className={`tab-btn ${activeTab === 'request' ? 'active' : ''}`}
            onClick={() => setActiveTab('request')}
          >
            Request Data
          </button>
          <button
            className={`tab-btn ${activeTab === 'response' ? 'active' : ''}`}
            onClick={() => setActiveTab('response')}
          >
            Response Data
          </button>
        </div>

        <div className="modal-body">
          {activeTab === 'overview' && (
            <div className="overview-tab">
              <div className="details-grid">
                <div className="detail-item">
                  <span className="detail-label">Request ID</span>
                  <code className="detail-value">{request.id}</code>
                </div>

                <div className="detail-item">
                  <span className="detail-label">Model</span>
                  <span className="detail-value">{request.model}</span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">Timestamp</span>
                  <span className="detail-value">{formatDate(request.created)}</span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">Status</span>
                  <span className={`status-badge ${request.status}`}>
                    {request.status === 'success' ? 'Success' : 'Error'}
                  </span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">Type</span>
                  <span className={`type-badge ${request.streaming ? 'streaming' : 'non-streaming'}`}>
                    {request.streaming ? 'Streaming' : 'Non-Streaming'}
                  </span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">Latency</span>
                  <span className="detail-value">{request.latency_ms.toFixed(2)} ms</span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">Prompt Tokens</span>
                  <span className="detail-value">{request.prompt_tokens.toLocaleString()}</span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">Completion Tokens</span>
                  <span className="detail-value">{request.completion_tokens.toLocaleString()}</span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">Total Tokens</span>
                  <span className="detail-value">{request.total_tokens.toLocaleString()}</span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">Cost</span>
                  <span className="detail-value cost">${request.cost.toFixed(6)}</span>
                </div>
              </div>

              {request.error_message && (
                <div className="error-message-container">
                  <div className="error-header">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Error Message
                  </div>
                  <div className="error-content">
                    {request.error_message}
                  </div>
                </div>
              )}

              <div className="token-visualization">
                <h4 className="subsection-title">Token Distribution</h4>
                <div className="token-bar">
                  <div
                    className="token-segment prompt"
                    style={{ width: `${(request.prompt_tokens / request.total_tokens) * 100}%` }}
                  >
                    <span className="segment-label">
                      Prompt: {((request.prompt_tokens / request.total_tokens) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div
                    className="token-segment completion"
                    style={{ width: `${(request.completion_tokens / request.total_tokens) * 100}%` }}
                  >
                    <span className="segment-label">
                      Completion: {((request.completion_tokens / request.total_tokens) * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'request' && (
            <div className="data-tab">
              <div className="data-header">
                <h4>Request Payload</h4>
                <button
                  className="copy-btn"
                  onClick={() => {
                    navigator.clipboard.writeText(formatJSON(request.request_data));
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy
                </button>
              </div>
              <pre className="code-block">
                <code>{formatJSON(request.request_data || { message: 'No request data available' })}</code>
              </pre>
            </div>
          )}

          {activeTab === 'response' && (
            <div className="data-tab">
              <div className="data-header">
                <h4>Response Payload</h4>
                <button
                  className="copy-btn"
                  onClick={() => {
                    navigator.clipboard.writeText(formatJSON(request.response_data));
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy
                </button>
              </div>
              <pre className="code-block">
                <code>{formatJSON(request.response_data || { message: 'No response data available' })}</code>
              </pre>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
