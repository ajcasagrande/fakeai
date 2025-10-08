/**
 * Benchmark Selector Component
 */

import React from 'react';
import { motion } from 'framer-motion';
import { FileText, ChevronDown } from 'lucide-react';
import { BenchmarkFile } from '../types';

interface BenchmarkSelectorProps {
  benchmarks: BenchmarkFile[];
  selectedBenchmark: BenchmarkFile | null;
  onSelect: (benchmark: BenchmarkFile) => void;
  loading?: boolean;
}

export const BenchmarkSelector: React.FC<BenchmarkSelectorProps> = ({
  benchmarks,
  selectedBenchmark,
  onSelect,
  loading,
}) => {
  const [isOpen, setIsOpen] = React.useState(false);

  if (loading) {
    return (
      <div className="mb-6 p-6 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl animate-pulse">
        <div className="h-8 bg-white/10 rounded w-1/3"></div>
      </div>
    );
  }

  return (
    <div className="mb-6">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative"
      >
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full p-4 bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl hover:border-nvidia-green/50 transition-all flex items-center justify-between group"
        >
          <div className="flex items-center gap-3">
            <FileText className="w-5 h-5 text-nvidia-green" />
            <div className="text-left">
              <div className="text-sm text-gray-400 mb-1">Selected Benchmark</div>
              {selectedBenchmark ? (
                <div className="text-white font-semibold">
                  {selectedBenchmark.model} - Concurrency: {selectedBenchmark.concurrency}
                </div>
              ) : (
                <div className="text-gray-500">Select a benchmark run...</div>
              )}
            </div>
          </div>
          <ChevronDown
            className={`w-5 h-5 text-gray-400 transition-transform ${
              isOpen ? 'rotate-180' : ''
            }`}
          />
        </button>

        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-full left-0 right-0 mt-2 bg-black/95 backdrop-blur-lg border border-white/10 rounded-xl shadow-2xl z-50 max-h-96 overflow-y-auto"
          >
            {benchmarks.length === 0 ? (
              <div className="p-6 text-center text-gray-400">
                No benchmark runs available
              </div>
            ) : (
              <div className="p-2">
                {benchmarks.map((benchmark, index) => (
                  <motion.button
                    key={benchmark.path}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.03 }}
                    onClick={() => {
                      onSelect(benchmark);
                      setIsOpen(false);
                    }}
                    className={`w-full p-3 rounded-lg text-left transition-all ${
                      selectedBenchmark?.path === benchmark.path
                        ? 'bg-nvidia-green/20 border border-nvidia-green/50 text-white'
                        : 'hover:bg-white/5 text-gray-300 hover:text-white'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold mb-1">{benchmark.model}</div>
                        <div className="text-xs text-gray-400">
                          Concurrency: {benchmark.concurrency}
                        </div>
                      </div>
                      {selectedBenchmark?.path === benchmark.path && (
                        <div className="w-2 h-2 bg-nvidia-green rounded-full"></div>
                      )}
                    </div>
                  </motion.button>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </motion.div>
    </div>
  );
};
