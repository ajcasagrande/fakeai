/**
 * Filter Panel Component
 * Provides filtering controls for model, date range, and status
 */

import React, { useState } from 'react';
import { DashboardFilters } from '../types';

interface FilterPanelProps {
  filters: DashboardFilters;
  availableModels: string[];
  onFiltersChange: (filters: DashboardFilters) => void;
}

export const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  availableModels,
  onFiltersChange,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);

  const handleModelChange = (model: string) => {
    onFiltersChange({
      ...filters,
      model: model === 'all' ? null : model,
    });
  };

  const handleDateRangeChange = (type: 'start' | 'end', value: string) => {
    const date = value ? new Date(value) : null;
    onFiltersChange({
      ...filters,
      dateRange: {
        ...filters.dateRange,
        [type]: date,
      },
    });
  };

  const handleStatusChange = (status: 'all' | 'success' | 'error') => {
    onFiltersChange({
      ...filters,
      status,
    });
  };

  const handleStreamingChange = (streaming: 'all' | 'streaming' | 'non-streaming') => {
    onFiltersChange({
      ...filters,
      streaming,
    });
  };

  const handleQuickDateRange = (range: string) => {
    const now = new Date();
    let start: Date | null = null;

    switch (range) {
      case 'last-hour':
        start = new Date(now.getTime() - 60 * 60 * 1000);
        break;
      case 'last-24h':
        start = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        break;
      case 'last-7d':
        start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case 'last-30d':
        start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      case 'all':
        start = null;
        break;
    }

    onFiltersChange({
      ...filters,
      dateRange: {
        start,
        end: range === 'all' ? null : now,
      },
    });
  };

  const handleReset = () => {
    onFiltersChange({
      model: null,
      dateRange: {
        start: null,
        end: null,
      },
      status: 'all',
      streaming: 'all',
    });
  };

  const formatDateForInput = (date: Date | null): string => {
    if (!date) return '';
    return date.toISOString().slice(0, 16);
  };

  const hasActiveFilters =
    filters.model !== null ||
    filters.dateRange.start !== null ||
    filters.dateRange.end !== null ||
    filters.status !== 'all' ||
    filters.streaming !== 'all';

  return (
    <div className="filter-panel-container">
      <div className="filter-panel-header">
        <h3 className="section-title">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Filters
        </h3>
        <div className="filter-panel-actions">
          {hasActiveFilters && (
            <button className="reset-btn" onClick={handleReset}>
              Reset All
            </button>
          )}
          <button
            className="toggle-btn"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isExpanded ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"} />
            </svg>
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="filter-panel-content">
          <div className="filter-section">
            <label className="filter-label">Model</label>
            <select
              className="filter-select"
              value={filters.model || 'all'}
              onChange={(e) => handleModelChange(e.target.value)}
            >
              <option value="all">All Models</option>
              {availableModels.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-section">
            <label className="filter-label">Quick Date Range</label>
            <div className="quick-range-buttons">
              <button
                className="quick-range-btn"
                onClick={() => handleQuickDateRange('last-hour')}
              >
                Last Hour
              </button>
              <button
                className="quick-range-btn"
                onClick={() => handleQuickDateRange('last-24h')}
              >
                Last 24h
              </button>
              <button
                className="quick-range-btn"
                onClick={() => handleQuickDateRange('last-7d')}
              >
                Last 7 Days
              </button>
              <button
                className="quick-range-btn"
                onClick={() => handleQuickDateRange('last-30d')}
              >
                Last 30 Days
              </button>
              <button
                className="quick-range-btn"
                onClick={() => handleQuickDateRange('all')}
              >
                All Time
              </button>
            </div>
          </div>

          <div className="filter-section">
            <label className="filter-label">Custom Date Range</label>
            <div className="date-range-inputs">
              <div className="date-input-group">
                <label className="date-label">Start</label>
                <input
                  type="datetime-local"
                  className="filter-input"
                  value={formatDateForInput(filters.dateRange.start)}
                  onChange={(e) => handleDateRangeChange('start', e.target.value)}
                />
              </div>
              <div className="date-input-group">
                <label className="date-label">End</label>
                <input
                  type="datetime-local"
                  className="filter-input"
                  value={formatDateForInput(filters.dateRange.end)}
                  onChange={(e) => handleDateRangeChange('end', e.target.value)}
                />
              </div>
            </div>
          </div>

          <div className="filter-section">
            <label className="filter-label">Status</label>
            <div className="filter-radio-group">
              <label className="radio-label">
                <input
                  type="radio"
                  name="status"
                  value="all"
                  checked={filters.status === 'all'}
                  onChange={() => handleStatusChange('all')}
                />
                All
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  name="status"
                  value="success"
                  checked={filters.status === 'success'}
                  onChange={() => handleStatusChange('success')}
                />
                Success
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  name="status"
                  value="error"
                  checked={filters.status === 'error'}
                  onChange={() => handleStatusChange('error')}
                />
                Error
              </label>
            </div>
          </div>

          <div className="filter-section">
            <label className="filter-label">Request Type</label>
            <div className="filter-radio-group">
              <label className="radio-label">
                <input
                  type="radio"
                  name="streaming"
                  value="all"
                  checked={filters.streaming === 'all'}
                  onChange={() => handleStreamingChange('all')}
                />
                All
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  name="streaming"
                  value="streaming"
                  checked={filters.streaming === 'streaming'}
                  onChange={() => handleStreamingChange('streaming')}
                />
                Streaming
              </label>
              <label className="radio-label">
                <input
                  type="radio"
                  name="streaming"
                  value="non-streaming"
                  checked={filters.streaming === 'non-streaming'}
                  onChange={() => handleStreamingChange('non-streaming')}
                />
                Non-Streaming
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
