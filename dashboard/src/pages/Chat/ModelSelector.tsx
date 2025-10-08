import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Check, Sparkles, Brain } from 'lucide-react';
import { getModelGroups, getModelDisplayName, isReasoningModel, type ModelInfo } from './types';

interface ModelSelectorProps {
  selectedModel: string;
  onModelChange: (modelId: string) => void;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({ selectedModel, onModelChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const modelGroups = getModelGroups();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleModelSelect = (modelId: string) => {
    onModelChange(modelId);
    setIsOpen(false);
  };

  const selectedModelName = getModelDisplayName(selectedModel);
  const isReasoning = isReasoningModel(selectedModel);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 hover:border-green-500/50 transition-all group"
      >
        {isReasoning && (
          <Brain size={16} className="text-purple-400" />
        )}
        <span className="text-sm font-semibold text-white">{selectedModelName}</span>
        <ChevronDown
          size={16}
          className={`text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full left-0 mt-2 w-96 bg-[#1a1a1a] border border-white/20 rounded-xl shadow-2xl overflow-hidden z-50"
          >
            <div className="max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
              {Object.entries(modelGroups).map(([groupName, models]) => (
                <div key={groupName} className="border-b border-white/10 last:border-b-0">
                  <div className="px-4 py-2 bg-white/5 sticky top-0 z-10">
                    <div className="flex items-center gap-2">
                      {groupName === 'Reasoning Models' && (
                        <Brain size={14} className="text-purple-400" />
                      )}
                      {groupName === 'GPT Models' && (
                        <Sparkles size={14} className="text-green-400" />
                      )}
                      <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                        {groupName}
                      </span>
                    </div>
                  </div>
                  {models.map((model) => (
                    <button
                      key={model.id}
                      onClick={() => handleModelSelect(model.id)}
                      className={`w-full px-4 py-3 text-left hover:bg-white/5 transition-colors flex items-start gap-3 group ${
                        selectedModel === model.id ? 'bg-white/10' : ''
                      }`}
                    >
                      <div className="flex-shrink-0 pt-0.5">
                        {selectedModel === model.id ? (
                          <Check size={16} className="text-green-500" />
                        ) : (
                          <div className="w-4 h-4" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-sm font-semibold ${
                            selectedModel === model.id ? 'text-green-400' : 'text-white'
                          }`}>
                            {model.name}
                          </span>
                          {model.tags?.includes('latest') && (
                            <span className="px-1.5 py-0.5 bg-green-500/20 text-green-400 text-xs rounded">
                              Latest
                            </span>
                          )}
                          {model.tags?.includes('reasoning') && (
                            <span className="px-1.5 py-0.5 bg-purple-500/20 text-purple-400 text-xs rounded">
                              Reasoning
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-400 leading-relaxed">
                          {model.description}
                        </p>
                        <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                          <span>{(model.contextWindow / 1000).toFixed(0)}K ctx</span>
                          <span>•</span>
                          <span>${(model.costPer1kPrompt * 1000).toFixed(2)}/M</span>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ModelSelector;
