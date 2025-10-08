/**
 * Requests Table Component
 * Displays recent chat requests with pagination, sorting, and filtering
 */

import React, { useState } from 'react';
import { ChatRequest } from '../types';

interface RequestsTableProps {
  requests: ChatRequest[];
  total: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onRequestClick: (request: ChatRequest) => void;
  loading?: boolean;
}

type SortField = 'created' | 'model' | 'latency_ms' | 'total_tokens' | 'cost' | 'status';
type SortDirection = 'asc' | 'desc';

export const RequestsTable: React.FC<RequestsTableProps> = ({
  requests,
  total,
  page,
  pageSize,
  onPageChange,
  onRequestClick,
  loading,
}) => {
  const [sortField, setSortField] = useState<SortField>('created');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const sortedRequests = React.useMemo(() => {
    const sorted = [...requests].sort((a, b) => {
      let aVal: any = a[sortField];
      let bVal: any = b[sortField];

      if (sortField === 'status') {
        aVal = a.status === 'success' ? 1 : 0;
        bVal = b.status === 'success' ? 1 : 0;
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [requests, sortField, sortDirection]);

  const totalPages = Math.ceil(total / pageSize);

  const formatDate = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const formatCost = (cost: number): string => {
    return `$${cost.toFixed(6)}`;
  };

  const SortIcon: React.FC<{ field: SortField }> = ({ field }) => {
    if (sortField !== field) {
      return (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" className="sort-icon">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
        </svg>
      );
    }

    return sortDirection === 'asc' ? (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" className="sort-icon active">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
      </svg>
    ) : (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" className="sort-icon active">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    );
  };

  if (loading) {
    return (
      <div className="requests-table-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <span>Loading requests...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="requests-table-container">
      <div className="table-header">
        <h3 className="section-title">Recent Requests</h3>
        <div className="table-info">
          Showing {requests.length} of {total} requests
        </div>
      </div>

      <div className="table-wrapper">
        <table className="requests-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('created')} className="sortable">
                Timestamp <SortIcon field="created" />
              </th>
              <th>Request ID</th>
              <th onClick={() => handleSort('model')} className="sortable">
                Model <SortIcon field="model" />
              </th>
              <th onClick={() => handleSort('total_tokens')} className="sortable">
                Tokens <SortIcon field="total_tokens" />
              </th>
              <th onClick={() => handleSort('latency_ms')} className="sortable">
                Latency <SortIcon field="latency_ms" />
              </th>
              <th onClick={() => handleSort('cost')} className="sortable">
                Cost <SortIcon field="cost" />
              </th>
              <th>Type</th>
              <th onClick={() => handleSort('status')} className="sortable">
                Status <SortIcon field="status" />
              </th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedRequests.map((request) => (
              <tr key={request.id} className={request.status === 'error' ? 'error-row' : ''}>
                <td className="timestamp">{formatDate(request.created)}</td>
                <td className="request-id">
                  <code>{request.id}</code>
                </td>
                <td className="model-name">{request.model}</td>
                <td className="tokens">
                  <div className="token-breakdown">
                    <span className="total">{request.total_tokens}</span>
                    <span className="detail">
                      ({request.prompt_tokens} + {request.completion_tokens})
                    </span>
                  </div>
                </td>
                <td className="latency">{request.latency_ms.toFixed(0)}ms</td>
                <td className="cost">{formatCost(request.cost)}</td>
                <td className="type">
                  <span className={`type-badge ${request.streaming ? 'streaming' : 'non-streaming'}`}>
                    {request.streaming ? 'Streaming' : 'Standard'}
                  </span>
                </td>
                <td className="status">
                  <span className={`status-badge ${request.status}`}>
                    {request.status === 'success' ? (
                      <>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Success
                      </>
                    ) : (
                      <>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                        Error
                      </>
                    )}
                  </span>
                </td>
                <td className="actions">
                  <button
                    className="view-details-btn"
                    onClick={() => onRequestClick(request)}
                    title="View details"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="table-pagination">
        <button
          className="pagination-btn"
          onClick={() => onPageChange(page - 1)}
          disabled={page === 0}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Previous
        </button>

        <div className="pagination-info">
          Page {page + 1} of {totalPages}
        </div>

        <button
          className="pagination-btn"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages - 1}
        >
          Next
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
};
