/**
 * GPU & DCGM Settings Panel
 * Configure GPU and DCGM monitoring parameters
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Cpu, Save, RotateCcw, Plus, X } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { GPUConfig } from '../types';

interface GPUSettingsProps {
  config: GPUConfig;
  onSave: (config: GPUConfig) => void;
  loading?: boolean;
}

export const GPUSettings: React.FC<GPUSettingsProps> = ({
  config,
  onSave,
  loading = false,
}) => {
  const [localConfig, setLocalConfig] = useState<GPUConfig>(config);
  const [hasChanges, setHasChanges] = useState(false);
  const [newGPUModel, setNewGPUModel] = useState('');

  const handleRangeChange = (field: 'utilization_range' | 'memory_range_gb', index: 0 | 1, value: number) => {
    const newRange: [number, number] = [...localConfig[field]] as [number, number];
    newRange[index] = value;
    setLocalConfig((prev) => ({ ...prev, [field]: newRange }));
    setHasChanges(true);
  };

  const handleChange = (field: keyof GPUConfig, value: any) => {
    setLocalConfig((prev) => ({ ...prev, [field]: value }));
    setHasChanges(true);
  };

  const addGPUModel = () => {
    if (newGPUModel.trim() && !localConfig.gpu_models.includes(newGPUModel.trim())) {
      setLocalConfig((prev) => ({
        ...prev,
        gpu_models: [...prev.gpu_models, newGPUModel.trim()],
      }));
      setNewGPUModel('');
      setHasChanges(true);
    }
  };

  const removeGPUModel = (model: string) => {
    setLocalConfig((prev) => ({
      ...prev,
      gpu_models: prev.gpu_models.filter((m) => m !== model),
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
          <Cpu className="w-6 h-6 text-nvidia-green" />
          <CardTitle className="text-nvidia-green">GPU & DCGM Configuration</CardTitle>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Number of GPUs */}
        <div className="space-y-2">
          <Label htmlFor="num_gpus" className="text-white">
            Number of GPUs
          </Label>
          <Input
            id="num_gpus"
            type="number"
            value={localConfig.num_gpus}
            onChange={(e) => handleChange('num_gpus', parseInt(e.target.value))}
            className="bg-black/50 border-nvidia-green/30 text-white"
            min={1}
            max={16}
          />
          <p className="text-xs text-gray-400">Number of GPUs to simulate (1-16)</p>
        </div>

        {/* GPU Models */}
        <div className="space-y-3">
          <Label className="text-white">GPU Models</Label>
          <div className="flex gap-2">
            <Input
              type="text"
              value={newGPUModel}
              onChange={(e) => setNewGPUModel(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addGPUModel()}
              placeholder="e.g., NVIDIA A100"
              className="bg-black/50 border-nvidia-green/30 text-white flex-1"
            />
            <Button onClick={addGPUModel} variant="secondary" size="icon">
              <Plus className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            {localConfig.gpu_models.map((model, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="flex items-center gap-2 bg-nvidia-green/10 border border-nvidia-green/30 px-3 py-1 rounded-full text-sm text-nvidia-green"
              >
                <span>{model}</span>
                <button
                  onClick={() => removeGPUModel(model)}
                  className="hover:text-red-400 transition-colors"
                >
                  <X className="w-3 h-3" />
                </button>
              </motion.div>
            ))}
          </div>
          <p className="text-xs text-gray-400">GPU models to simulate</p>
        </div>

        {/* Utilization Range */}
        <div className="space-y-3">
          <Label className="text-white">GPU Utilization Range (%)</Label>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label htmlFor="util_min" className="text-xs text-gray-400">Min</Label>
              <Input
                id="util_min"
                type="number"
                value={localConfig.utilization_range[0]}
                onChange={(e) => handleRangeChange('utilization_range', 0, parseInt(e.target.value))}
                className="bg-black/50 border-nvidia-green/30 text-white"
                min={0}
                max={localConfig.utilization_range[1]}
              />
            </div>
            <div>
              <Label htmlFor="util_max" className="text-xs text-gray-400">Max</Label>
              <Input
                id="util_max"
                type="number"
                value={localConfig.utilization_range[1]}
                onChange={(e) => handleRangeChange('utilization_range', 1, parseInt(e.target.value))}
                className="bg-black/50 border-nvidia-green/30 text-white"
                min={localConfig.utilization_range[0]}
                max={100}
              />
            </div>
          </div>
          <p className="text-xs text-gray-400">GPU utilization percentage range (0-100%)</p>
        </div>

        {/* Memory Range */}
        <div className="space-y-3">
          <Label className="text-white">GPU Memory Range (GB)</Label>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label htmlFor="mem_min" className="text-xs text-gray-400">Min</Label>
              <Input
                id="mem_min"
                type="number"
                value={localConfig.memory_range_gb[0]}
                onChange={(e) => handleRangeChange('memory_range_gb', 0, parseInt(e.target.value))}
                className="bg-black/50 border-nvidia-green/30 text-white"
                min={0}
                max={localConfig.memory_range_gb[1]}
              />
            </div>
            <div>
              <Label htmlFor="mem_max" className="text-xs text-gray-400">Max</Label>
              <Input
                id="mem_max"
                type="number"
                value={localConfig.memory_range_gb[1]}
                onChange={(e) => handleRangeChange('memory_range_gb', 1, parseInt(e.target.value))}
                className="bg-black/50 border-nvidia-green/30 text-white"
                min={localConfig.memory_range_gb[0]}
                max={512}
              />
            </div>
          </div>
          <p className="text-xs text-gray-400">GPU memory usage range in GB</p>
        </div>

        {/* Enable DCGM */}
        <div className="flex items-center justify-between p-4 bg-black/30 border border-nvidia-green/20 rounded">
          <div>
            <Label htmlFor="enable_dcgm" className="text-white">
              Enable DCGM Monitoring
            </Label>
            <p className="text-xs text-gray-400 mt-1">
              Enable NVIDIA Data Center GPU Manager metrics
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              id="enable_dcgm"
              type="checkbox"
              checked={localConfig.enable_dcgm}
              onChange={(e) => handleChange('enable_dcgm', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-nvidia-green rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-nvidia-green"></div>
          </label>
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
