/**
 * Request Lifecycle Timeline Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Clock, CheckCircle, XCircle, Loader } from 'lucide-react';
import { RequestLifecycle } from '../types';

interface RequestLifecycleTimelineProps {
  lifecycles: RequestLifecycle[];
  loading?: boolean;
}

export const RequestLifecycleTimeline: React.FC<RequestLifecycleTimelineProps> = ({ lifecycles, loading }) => {
  if (loading || !lifecycles) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
      >
        <h3 className="text-lg font-bold text-white mb-2">Request Lifecycle Timeline</h3>
        <div className="text-center py-8 text-gray-400">
          {loading ? 'Loading...' : 'No lifecycle data available'}
        </div>
      </motion.div>
    );
  }

  if (lifecycles.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl"
      >
        <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
          <Clock className="w-5 h-5" />
          Request Lifecycle Timeline
        </h3>
        <div className="text-center py-8 text-gray-400">No lifecycle data available</div>
      </motion.div>
    );
  }

  // Show only recent requests (last 10)
  const recentLifecycles = lifecycles.slice(0, 10);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.005 }}
      className="p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:border-green-500/50 transition-all"
    >
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <Clock className="w-5 h-5 text-indigo-500" />
          Request Lifecycle Timeline
        </h3>
        <div className="flex gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-orange-500"></div>
            <span className="text-gray-400">Queue</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-blue-500"></div>
            <span className="text-gray-400">Prefill</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-green-500"></div>
            <span className="text-gray-400">Decode</span>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {recentLifecycles.map((lifecycle) => {
          const totalTime = lifecycle.total_duration_ms || 0;
          const queuePct = totalTime > 0 ? (lifecycle.queue_wait_ms / totalTime) * 100 : 0;
          const prefillPct = totalTime > 0 ? (lifecycle.prefill_duration_ms / totalTime) * 100 : 0;
          const decodePct = totalTime > 0 ? (lifecycle.decode_duration_ms / totalTime) * 100 : 0;

          return (
            <div
              key={lifecycle.request_id}
              className={`p-4 bg-white/5 rounded-lg border-l-4 ${
                lifecycle.status === 'completed' ? 'border-green-500' :
                lifecycle.status === 'failed' ? 'border-red-500' :
                'border-orange-500'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  {lifecycle.status === 'completed' && <CheckCircle className="w-4 h-4 text-green-500" />}
                  {lifecycle.status === 'failed' && <XCircle className="w-4 h-4 text-red-500" />}
                  {lifecycle.status === 'in_progress' && <Loader className="w-4 h-4 text-orange-500 animate-spin" />}
                  <span className="font-mono text-sm text-white">{lifecycle.request_id.slice(0, 8)}</span>
                  <span className="text-xs text-gray-400">{lifecycle.model}</span>
                  {lifecycle.cached_tokens > 0 && (
                    <span className="text-xs px-2 py-0.5 bg-orange-500/20 text-orange-500 rounded">
                      {lifecycle.cached_tokens} cached
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-400">
                  {lifecycle.output_tokens} tokens • {totalTime.toFixed(0)}ms
                </div>
              </div>

              <div className="h-8 flex rounded overflow-hidden bg-gray-900">
                {queuePct > 0 && (
                  <div
                    className="bg-orange-500 flex items-center justify-center text-white text-xs font-semibold"
                    style={{ width: `${queuePct}%` }}
                  >
                    {queuePct > 15 && `${lifecycle.queue_wait_ms.toFixed(0)}ms`}
                  </div>
                )}
                {prefillPct > 0 && (
                  <div
                    className="bg-blue-500 flex items-center justify-center text-white text-xs font-semibold"
                    style={{ width: `${prefillPct}%` }}
                  >
                    {prefillPct > 15 && `${lifecycle.prefill_duration_ms.toFixed(0)}ms`}
                  </div>
                )}
                {decodePct > 0 && (
                  <div
                    className="bg-green-500 flex items-center justify-center text-white text-xs font-semibold"
                    style={{ width: `${decodePct}%` }}
                  >
                    {decodePct > 15 && `${lifecycle.decode_duration_ms.toFixed(0)}ms`}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 text-xs text-gray-500 text-center">
        Showing {recentLifecycles.length} of {lifecycles.length} requests
      </div>
    </motion.div>
  );
};
