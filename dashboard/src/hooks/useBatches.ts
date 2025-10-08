/**
 * Custom Hook: useBatches
 * Manages batch list with real-time polling updates
 */

import { useState, useEffect, useCallback } from 'react';
import batchService from '../services/batchService';
import type { Batch } from '../types/batch';

const POLLING_INTERVAL = 5000; // 5 seconds

export const useBatches = (autoRefresh: boolean = true) => {
  const [batches, setBatches] = useState<Batch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBatches = useCallback(async () => {
    try {
      const response = await batchService.listBatches({ limit: 100 });
      setBatches(response.data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch batches');
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshBatches = useCallback(() => {
    setLoading(true);
    fetchBatches();
  }, [fetchBatches]);

  const cancelBatch = useCallback(
    async (batchId: string) => {
      try {
        const updatedBatch = await batchService.cancelBatch(batchId);
        setBatches(prev =>
          prev.map(b => (b.id === batchId ? updatedBatch : b))
        );
        return updatedBatch;
      } catch (err) {
        throw err;
      }
    },
    []
  );

  // Initial fetch
  useEffect(() => {
    fetchBatches();
  }, [fetchBatches]);

  // Auto-refresh for active batches
  useEffect(() => {
    if (!autoRefresh) return;

    const hasActiveBatches = batches.some(
      b =>
        b.status === 'validating' ||
        b.status === 'in_progress' ||
        b.status === 'cancelling'
    );

    if (!hasActiveBatches) return;

    const intervalId = setInterval(() => {
      fetchBatches();
    }, POLLING_INTERVAL);

    return () => clearInterval(intervalId);
  }, [autoRefresh, batches, fetchBatches]);

  return {
    batches,
    loading,
    error,
    refreshBatches,
    cancelBatch,
  };
};

export default useBatches;
