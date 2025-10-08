/**
 * Cost Filters Component
 * Provides filtering options for cost data
 */

import React from 'react';
import { CostFilters as CostFiltersType } from '../types';

interface CostFiltersProps {
  filters: CostFiltersType;
  availableServices: string[];
  availableModels: string[];
  onFiltersChange: (filters: CostFiltersType) => void;
}

export const CostFilters: React.FC<CostFiltersProps> = ({
  filters,
  availableServices,
  availableModels,
  onFiltersChange,
}) => {
  const handleDatePreset = (preset: 'today' | 'yesterday' | 'last7days' | 'last30days' | 'thisMonth' | 'lastMonth') => {
    const now = new Date();
    let start: Date;
    let end: Date = now;

    switch (preset) {
      case 'today':
        start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        break;
      case 'yesterday':
        start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
        end = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        break;
      case 'last7days':
        start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case 'last30days':
        start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      case 'thisMonth':
        start = new Date(now.getFullYear(), now.getMonth(), 1);
        break;
      case 'lastMonth':
        start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        end = new Date(now.getFullYear(), now.getMonth(), 0);
        break;
      default:
        start = now;
    }

    onFiltersChange({
      ...filters,
      dateRange: { start, end, preset },
    });
  };

  return (
    <div className="cost-filters-container">
      <h3 className="section-title">Filters</h3>

      <div className="filter-section">
        <label className="filter-label">Date Range</label>
        <div className="date-presets">
          <button
            className={`preset-btn ${filters.dateRange.preset === 'today' ? 'active' : ''}`}
            onClick={() => handleDatePreset('today')}
          >
            Today
          </button>
          <button
            className={`preset-btn ${filters.dateRange.preset === 'yesterday' ? 'active' : ''}`}
            onClick={() => handleDatePreset('yesterday')}
          >
            Yesterday
          </button>
          <button
            className={`preset-btn ${filters.dateRange.preset === 'last7days' ? 'active' : ''}`}
            onClick={() => handleDatePreset('last7days')}
          >
            Last 7 Days
          </button>
          <button
            className={`preset-btn ${filters.dateRange.preset === 'last30days' ? 'active' : ''}`}
            onClick={() => handleDatePreset('last30days')}
          >
            Last 30 Days
          </button>
          <button
            className={`preset-btn ${filters.dateRange.preset === 'thisMonth' ? 'active' : ''}`}
            onClick={() => handleDatePreset('thisMonth')}
          >
            This Month
          </button>
        </div>

        <div className="custom-date-range">
          <div className="date-input-group">
            <label>Start Date</label>
            <input
              type="date"
              value={filters.dateRange.start?.toISOString().split('T')[0] || ''}
              onChange={(e) =>
                onFiltersChange({
                  ...filters,
                  dateRange: {
                    ...filters.dateRange,
                    start: e.target.value ? new Date(e.target.value) : null,
                    preset: 'custom',
                  },
                })
              }
            />
          </div>
          <div className="date-input-group">
            <label>End Date</label>
            <input
              type="date"
              value={filters.dateRange.end?.toISOString().split('T')[0] || ''}
              onChange={(e) =>
                onFiltersChange({
                  ...filters,
                  dateRange: {
                    ...filters.dateRange,
                    end: e.target.value ? new Date(e.target.value) : null,
                    preset: 'custom',
                  },
                })
              }
            />
          </div>
        </div>
      </div>

      <div className="filter-section">
        <label className="filter-label">Service</label>
        <select
          value={filters.service || ''}
          onChange={(e) =>
            onFiltersChange({ ...filters, service: e.target.value || null })
          }
        >
          <option value="">All Services</option>
          {availableServices.map((service) => (
            <option key={service} value={service}>
              {service}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-section">
        <label className="filter-label">Model</label>
        <select
          value={filters.model || ''}
          onChange={(e) =>
            onFiltersChange({ ...filters, model: e.target.value || null })
          }
        >
          <option value="">All Models</option>
          {availableModels.map((model) => (
            <option key={model} value={model}>
              {model}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-section">
        <label className="filter-label">Group By</label>
        <div className="group-by-buttons">
          <button
            className={`group-btn ${filters.groupBy === 'day' ? 'active' : ''}`}
            onClick={() => onFiltersChange({ ...filters, groupBy: 'day' })}
          >
            Day
          </button>
          <button
            className={`group-btn ${filters.groupBy === 'week' ? 'active' : ''}`}
            onClick={() => onFiltersChange({ ...filters, groupBy: 'week' })}
          >
            Week
          </button>
          <button
            className={`group-btn ${filters.groupBy === 'month' ? 'active' : ''}`}
            onClick={() => onFiltersChange({ ...filters, groupBy: 'month' })}
          >
            Month
          </button>
        </div>
      </div>

      <button
        className="reset-filters-btn"
        onClick={() =>
          onFiltersChange({
            dateRange: { start: null, end: null, preset: 'last30days' },
            service: null,
            model: null,
            groupBy: 'day',
          })
        }
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
        Reset Filters
      </button>
    </div>
  );
};
