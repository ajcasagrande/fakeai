/**
 * Custom Hook: useBatch
 * Manages single batch with real-time polling updates
 */

import { useState, useEffect, useCallback } from 'react';
import batchService from '../services/batchService';
import type { Batch } from '../types/batch';

const POLLING_INTERVAL = 3000; // 3 seconds

export const useBatch = (batchId: string) => {
  const [batch, setBatch] = useState<Batch | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBatch = useCallback(async () => {
    try {
      const data = await batchService.getBatch(batchId);
      setBatch(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch batch');
    } finally {
      setLoading(false);
    }
  }, [batchId]);

  const refreshBatch = useCallback(() => {
    setLoading(true);
    fetchBatch();
  }, [fetchBatch]);

  const cancelBatch = useCallback(async () => {
    try {
      const updatedBatch = await batchService.cancelBatch(batchId);
      setBatch(updatedBatch);
      return updatedBatch;
    } catch (err) {
      throw err;
    }
  }, [batchId]);

  // Initial fetch
  useEffect(() => {
    fetchBatch();
  }, [fetchBatch]);

  // Auto-refresh for active batches
  useEffect(() => {
    if (!batch) return;

    const isActive =
      batch.status === 'validating' ||
      batch.status === 'in_progress' ||
      batch.status === 'cancelling';

    if (!isActive) return;

    const intervalId = setInterval(() => {
      fetchBatch();
    }, POLLING_INTERVAL);

    return () => clearInterval(intervalId);
  }, [batch, fetchBatch]);

  return {
    batch,
    loading,
    error,
    refreshBatch,
    cancelBatch,
  };
};

export default useBatch;
