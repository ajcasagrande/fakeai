/**
 * KV Cache Settings Panel
 * Configure KV cache parameters
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Database, Save, RotateCcw } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { KVCacheConfig } from '../types';

interface KVCacheSettingsProps {
  config: KVCacheConfig;
  onSave: (config: KVCacheConfig) => void;
  loading?: boolean;
}

export const KVCacheSettings: React.FC<KVCacheSettingsProps> = ({
  config,
  onSave,
  loading = false,
}) => {
  const [localConfig, setLocalConfig] = useState<KVCacheConfig>(config);
  const [hasChanges, setHasChanges] = useState(false);

  const handleChange = (field: keyof KVCacheConfig, value: any) => {
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
          <Database className="w-6 h-6 text-nvidia-green" />
          <CardTitle className="text-nvidia-green">KV Cache Configuration</CardTitle>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Block Size */}
        <div className="space-y-2">
          <Label htmlFor="block_size" className="text-white">
            Block Size
          </Label>
          <Input
            id="block_size"
            type="number"
            value={localConfig.block_size}
            onChange={(e) => handleChange('block_size', parseInt(e.target.value))}
            className="bg-black/50 border-nvidia-green/30 text-white"
            min={1}
            max={1024}
          />
          <p className="text-xs text-gray-400">Size of each cache block (1-1024)</p>
        </div>

        {/* Number of Workers */}
        <div className="space-y-2">
          <Label htmlFor="num_workers" className="text-white">
            Number of Workers
          </Label>
          <Input
            id="num_workers"
            type="number"
            value={localConfig.num_workers}
            onChange={(e) => handleChange('num_workers', parseInt(e.target.value))}
            className="bg-black/50 border-nvidia-green/30 text-white"
            min={1}
            max={64}
          />
          <p className="text-xs text-gray-400">Number of cache workers (1-64)</p>
        </div>

        {/* Overlap Weight */}
        <div className="space-y-2">
          <Label htmlFor="overlap_weight" className="text-white">
            Overlap Weight
          </Label>
          <Input
            id="overlap_weight"
            type="number"
            step="0.1"
            value={localConfig.overlap_weight}
            onChange={(e) => handleChange('overlap_weight', parseFloat(e.target.value))}
            className="bg-black/50 border-nvidia-green/30 text-white"
            min={0}
            max={1}
          />
          <p className="text-xs text-gray-400">Weight for overlapping cache entries (0.0-1.0)</p>
        </div>

        {/* Cache Size */}
        <div className="space-y-2">
          <Label htmlFor="cache_size_mb" className="text-white">
            Cache Size (MB)
          </Label>
          <Input
            id="cache_size_mb"
            type="number"
            value={localConfig.cache_size_mb}
            onChange={(e) => handleChange('cache_size_mb', parseInt(e.target.value))}
            className="bg-black/50 border-nvidia-green/30 text-white"
            min={64}
            max={16384}
          />
          <p className="text-xs text-gray-400">Total cache size in megabytes (64-16384)</p>
        </div>

        {/* Enable Prefix Caching */}
        <div className="flex items-center justify-between p-4 bg-black/30 border border-nvidia-green/20 rounded">
          <div>
            <Label htmlFor="enable_prefix_caching" className="text-white">
              Enable Prefix Caching
            </Label>
            <p className="text-xs text-gray-400 mt-1">
              Cache common prompt prefixes for faster inference
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              id="enable_prefix_caching"
              type="checkbox"
              checked={localConfig.enable_prefix_caching}
              onChange={(e) => handleChange('enable_prefix_caching', e.target.checked)}
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
