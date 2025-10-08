/**
 * Dynamo Settings Panel
 * Configure AI-Dynamo worker and queue parameters
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Zap, Save, RotateCcw } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { DynamoConfig } from '../types';

interface DynamoSettingsProps {
  config: DynamoConfig;
  onSave: (config: DynamoConfig) => void;
  loading?: boolean;
}

export const DynamoSettings: React.FC<DynamoSettingsProps> = ({
  config,
  onSave,
  loading = false,
}) => {
  const [localConfig, setLocalConfig] = useState<DynamoConfig>(config);
  const [hasChanges, setHasChanges] = useState(false);

  const handleChange = (field: keyof DynamoConfig, value: any) => {
    setLocalConfig((prev) => ({ ...prev, [field]: value }));
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
          <Zap className="w-6 h-6 text-nvidia-green" />
          <CardTitle className="text-nvidia-green">AI-Dynamo Configuration</CardTitle>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Number of Workers */}
        <div className="space-y-2">
          <Label htmlFor="dynamo_workers" className="text-white">
            Number of Workers
          </Label>
          <Input
            id="dynamo_workers"
            type="number"
            value={localConfig.num_workers}
            onChange={(e) => handleChange('num_workers', parseInt(e.target.value))}
            className="bg-black/50 border-nvidia-green/30 text-white"
            min={1}
            max={128}
          />
          <p className="text-xs text-gray-400">Number of Dynamo workers (1-128)</p>
        </div>

        {/* Max Queue Depth */}
        <div className="space-y-2">
          <Label htmlFor="max_queue_depth" className="text-white">
            Max Queue Depth
          </Label>
          <Input
            id="max_queue_depth"
            type="number"
            value={localConfig.max_queue_depth}
            onChange={(e) => handleChange('max_queue_depth', parseInt(e.target.value))}
            className="bg-black/50 border-nvidia-green/30 text-white"
            min={1}
            max={10000}
          />
          <p className="text-xs text-gray-400">Maximum queue depth (1-10000)</p>
        </div>

        {/* Batch Size */}
        <div className="space-y-2">
          <Label htmlFor="batch_size" className="text-white">
            Batch Size
          </Label>
          <Input
            id="batch_size"
            type="number"
            value={localConfig.batch_size}
            onChange={(e) => handleChange('batch_size', parseInt(e.target.value))}
            className="bg-black/50 border-nvidia-green/30 text-white"
            min={1}
            max={512}
          />
          <p className="text-xs text-gray-400">Batch size for inference (1-512)</p>
        </div>

        {/* Worker Timeout */}
        <div className="space-y-2">
          <Label htmlFor="worker_timeout_ms" className="text-white">
            Worker Timeout (ms)
          </Label>
          <Input
            id="worker_timeout_ms"
            type="number"
            value={localConfig.worker_timeout_ms}
            onChange={(e) => handleChange('worker_timeout_ms', parseInt(e.target.value))}
            className="bg-black/50 border-nvidia-green/30 text-white"
            min={100}
            max={60000}
          />
          <p className="text-xs text-gray-400">Worker timeout in milliseconds (100-60000)</p>
        </div>

        {/* Enable Dynamic Batching */}
        <div className="flex items-center justify-between p-4 bg-black/30 border border-nvidia-green/20 rounded">
          <div>
            <Label htmlFor="enable_dynamic_batching" className="text-white">
              Enable Dynamic Batching
            </Label>
            <p className="text-xs text-gray-400 mt-1">
              Automatically adjust batch size based on load
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              id="enable_dynamic_batching"
              type="checkbox"
              checked={localConfig.enable_dynamic_batching}
              onChange={(e) => handleChange('enable_dynamic_batching', e.target.checked)}
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
