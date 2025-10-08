/**
 * Export Reports Component
 * Handles exporting cost reports in various formats
 */

import React, { useState } from 'react';
import { exportCostData, downloadBlob } from '../api';

interface ExportReportsProps {
  startTime: number;
  endTime: number;
}

export const ExportReports: React.FC<ExportReportsProps> = ({ startTime, endTime }) => {
  const [exporting, setExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState<'csv' | 'json' | 'pdf'>('csv');

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await exportCostData(exportFormat, startTime, endTime);
      const filename = `cost-report-${new Date().toISOString().split('T')[0]}.${exportFormat}`;
      downloadBlob(blob, filename);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Failed to export report. Please try again.');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="export-reports-container">
      <h3 className="section-title">Export Reports</h3>

      <div className="export-options">
        <div className="format-selector">
          <label>Format:</label>
          <div className="format-buttons">
            <button
              className={`format-btn ${exportFormat === 'csv' ? 'active' : ''}`}
              onClick={() => setExportFormat('csv')}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              CSV
            </button>
            <button
              className={`format-btn ${exportFormat === 'json' ? 'active' : ''}`}
              onClick={() => setExportFormat('json')}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              JSON
            </button>
            <button
              className={`format-btn ${exportFormat === 'pdf' ? 'active' : ''}`}
              onClick={() => setExportFormat('pdf')}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              PDF
            </button>
          </div>
        </div>

        <button
          className="export-btn"
          onClick={handleExport}
          disabled={exporting}
        >
          {exporting ? (
            <>
              <svg className="spinner" width="20" height="20" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" opacity="0.25" />
                <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="4" fill="none" />
              </svg>
              Exporting...
            </>
          ) : (
            <>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download Report
            </>
          )}
        </button>
      </div>

      <div className="export-info">
        <div className="info-item">
          <span className="info-label">Report Period:</span>
          <span className="info-value">
            {new Date(startTime * 1000).toLocaleDateString()} - {new Date(endTime * 1000).toLocaleDateString()}
          </span>
        </div>
        <div className="info-item">
          <span className="info-label">Format:</span>
          <span className="info-value">{exportFormat.toUpperCase()}</span>
        </div>
      </div>
    </div>
  );
};
