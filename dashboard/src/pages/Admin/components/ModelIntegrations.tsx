/**
 * Model Integrations Panel
 * Enable/disable various model integration features
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Brain, Save, RotateCcw, Plus, X } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ModelIntegrationsConfig } from '../types';

interface ModelIntegrationsProps {
  config: ModelIntegrationsConfig;
  onSave: (config: ModelIntegrationsConfig) => void;
  loading?: boolean;
}

export const ModelIntegrations: React.FC<ModelIntegrationsProps> = ({
  config,
  onSave,
  loading = false,
}) => {
  const [localConfig, setLocalConfig] = useState<ModelIntegrationsConfig>(config);
  const [hasChanges, setHasChanges] = useState(false);
  const [newVLMModel, setNewVLMModel] = useState('');
  const [newTRTEngine, setNewTRTEngine] = useState('');

  const handleChange = (field: keyof ModelIntegrationsConfig, value: any) => {
    setLocalConfig((prev) => ({ ...prev, [field]: value }));
    setHasChanges(true);
  };

  const addVLMModel = () => {
    if (newVLMModel.trim() && !localConfig.vlm_models.includes(newVLMModel.trim())) {
      setLocalConfig((prev) => ({
        ...prev,
        vlm_models: [...prev.vlm_models, newVLMModel.trim()],
      }));
      setNewVLMModel('');
      setHasChanges(true);
    }
  };

  const removeVLMModel = (model: string) => {
    setLocalConfig((prev) => ({
      ...prev,
      vlm_models: prev.vlm_models.filter((m) => m !== model),
    }));
    setHasChanges(true);
  };

  const addTRTEngine = () => {
    if (newTRTEngine.trim() && !localConfig.trt_llm_engines.includes(newTRTEngine.trim())) {
      setLocalConfig((prev) => ({
        ...prev,
        trt_llm_engines: [...prev.trt_llm_engines, newTRTEngine.trim()],
      }));
      setNewTRTEngine('');
      setHasChanges(true);
    }
  };

  const removeTRTEngine = (engine: string) => {
    setLocalConfig((prev) => ({
      ...prev,
      trt_llm_engines: prev.trt_llm_engines.filter((e) => e !== engine),
    }));
    setHasChanges(true);
  };

  const handleSave = () => {
    onSave(localConfig);
    setHasChanges(false);
  };

  const handleReset = () => {
    setLocalConfig(config);
    setHasChanges(false);
  };

  return (
    <Card className="border-nvidia-green/30">
      <CardHeader>
        <div className="flex items-center gap-3">
          <Brain className="w-6 h-6 text-nvidia-green" />
          <CardTitle className="text-nvidia-green">Model Integrations</CardTitle>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Vision-Language Models (VLM) */}
        <div className="space-y-3 p-4 bg-black/30 border border-nvidia-green/20 rounded">
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="enable_vlm" className="text-white">
                Vision-Language Models (VLM)
              </Label>
              <p className="text-xs text-gray-400 mt-1">
                Enable multimodal vision and language models
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                id="enable_vlm"
                type="checkbox"
                checked={localConfig.enable_vlm}
                onChange={(e) => handleChange('enable_vlm', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-nvidia-green rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-nvidia-green"></div>
            </label>
          </div>

          {localConfig.enable_vlm && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-2 mt-3"
            >
              <Label className="text-sm text-gray-300">VLM Models</Label>
              <div className="flex gap-2">
                <Input
                  type="text"
                  value={newVLMModel}
                  onChange={(e) => setNewVLMModel(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addVLMModel()}
                  placeholder="e.g., llava-v1.5-7b"
                  className="bg-black/50 border-nvidia-green/30 text-white flex-1 text-sm"
                />
                <Button onClick={addVLMModel} variant="secondary" size="icon">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>

              <div className="flex flex-wrap gap-2">
                {localConfig.vlm_models.map((model, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex items-center gap-2 bg-nvidia-green/10 border border-nvidia-green/30 px-2 py-1 rounded-full text-xs text-nvidia-green"
                  >
                    <span>{model}</span>
                    <button
                      onClick={() => removeVLMModel(model)}
                      className="hover:text-red-400 transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </div>

        {/* Triton Inference Server */}
        <div className="space-y-3 p-4 bg-black/30 border border-nvidia-green/20 rounded">
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="enable_triton" className="text-white">
                Triton Inference Server
              </Label>
              <p className="text-xs text-gray-400 mt-1">
                Enable NVIDIA Triton inference backend
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                id="enable_triton"
                type="checkbox"
                checked={localConfig.enable_triton}
                onChange={(e) => handleChange('enable_triton', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-nvidia-green rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-nvidia-green"></div>
            </label>
          </div>

          {localConfig.enable_triton && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-2 mt-3"
            >
              <Label htmlFor="triton_backend" className="text-sm text-gray-300">
                Triton Backend
              </Label>
              <Input
                id="triton_backend"
                type="text"
                value={localConfig.triton_backend}
                onChange={(e) => handleChange('triton_backend', e.target.value)}
                placeholder="e.g., tensorrt, onnx, pytorch"
                className="bg-black/50 border-nvidia-green/30 text-white text-sm"
              />
            </motion.div>
          )}
        </div>

        {/* TensorRT-LLM */}
        <div className="space-y-3 p-4 bg-black/30 border border-nvidia-green/20 rounded">
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="enable_trt_llm" className="text-white">
                TensorRT-LLM
              </Label>
              <p className="text-xs text-gray-400 mt-1">
                Enable TensorRT-LLM optimized engines
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                id="enable_trt_llm"
                type="checkbox"
                checked={localConfig.enable_trt_llm}
                onChange={(e) => handleChange('enable_trt_llm', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-nvidia-green rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-nvidia-green"></div>
            </label>
          </div>

          {localConfig.enable_trt_llm && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-2 mt-3"
            >
              <Label className="text-sm text-gray-300">TRT-LLM Engines</Label>
              <div className="flex gap-2">
                <Input
                  type="text"
                  value={newTRTEngine}
                  onChange={(e) => setNewTRTEngine(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addTRTEngine()}
                  placeholder="e.g., llama-2-7b-trt"
                  className="bg-black/50 border-nvidia-green/30 text-white flex-1 text-sm"
                />
                <Button onClick={addTRTEngine} variant="secondary" size="icon">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>

              <div className="flex flex-wrap gap-2">
                {localConfig.trt_llm_engines.map((engine, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex items-center gap-2 bg-nvidia-green/10 border border-nvidia-green/30 px-2 py-1 rounded-full text-xs text-nvidia-green"
                  >
                    <span>{engine}</span>
                    <button
                      onClick={() => removeTRTEngine(engine)}
                      className="hover:text-red-400 transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 pt-4">
          <Button
            onClick={handleSave}
            disabled={!hasChanges || loading}
            variant="primary"
            className="flex-1"
          >
            <Save className="w-4 h-4 mr-2" />
            Save Changes
          </Button>

          <Button
            onClick={handleReset}
            disabled={!hasChanges || loading}
            variant="secondary"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset
          </Button>
        </div>

        {hasChanges && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-yellow-500 text-xs text-center"
          >
            You have unsaved changes
          </motion.p>
        )}
      </CardContent>
    </Card>
  );
};
