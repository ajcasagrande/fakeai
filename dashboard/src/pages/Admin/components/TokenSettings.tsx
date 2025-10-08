/**
 * Token Generation Settings Panel
 * Configure timing parameters for token generation
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Clock, Save, RotateCcw } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { TokenGenerationConfig } from '../types';

interface TokenSettingsProps {
  config: TokenGenerationConfig;
  onSave: (config: TokenGenerationConfig) => void;
  loading?: boolean;
}

export const TokenSettings: React.FC<TokenSettingsProps> = ({
  config,
  onSave,
  loading = false,
}) => {
  const [localConfig, setLocalConfig] = useState<TokenGenerationConfig>(config);
  const [hasChanges, setHasChanges] = useState(false);

  const handleRangeChange = (field: 'ttft_range_ms' | 'tpot_range_ms' | 'itl_range_ms', index: 0 | 1, value: number) => {
    const newRange: [number, number] = [...localConfig[field]] as [number, number];
    newRange[index] = value;
    setLocalConfig((prev) => ({ ...prev, [field]: newRange }));
    setHasChanges(true);
  };

  const handleChange = (field: keyof TokenGenerationConfig, value: any) => {
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
          <Clock className="w-6 h-6 text-nvidia-green" />
          <CardTitle className="text-nvidia-green">Token Generation Timing</CardTitle>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* TTFT Range */}
        <div className="space-y-3">
          <Label className="text-white">Time to First Token (TTFT) Range (ms)</Label>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label htmlFor="ttft_min" className="text-xs text-gray-400">Min</Label>
              <Input
                id="ttft_min"
                type="number"
                value={localConfig.ttft_range_ms[0]}
                onChange={(e) => handleRangeChange('ttft_range_ms', 0, parseInt(e.target.value))}
                className="bg-black/50 border-nvidia-green/30 text-white"
                min={1}
                max={localConfig.ttft_range_ms[1]}
              />
            </div>
            <div>
              <Label htmlFor="ttft_max" className="text-xs text-gray-400">Max</Label>
              <Input
                id="ttft_max"
                type="number"
                value={localConfig.ttft_range_ms[1]}
                onChange={(e) => handleRangeChange('ttft_range_ms', 1, parseInt(e.target.value))}
                className="bg-black/50 border-nvidia-green/30 text-white"
                min={localConfig.ttft_range_ms[0]}
                max={10000}
              />
            </div>
          </div>
          <p className="text-xs text-gray-400">Time before first token is generated</p>
        </div>

        {/* TPOT Range */}
        <div className="space-y-3">
          <Label className="text-white">Time Per Output Token (TPOT) Range (ms)</Label>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label htmlFor="tpot_min" className="text-xs text-gray-400">Min</Label>
              <Input
                id="tpot_min"
                type="number"
                value={localConfig.tpot_range_ms[0]}
                onChange={(e) => handleRangeChange('tpot_range_ms', 0, parseInt(e.target.value))}
                className="bg-black/50 border-nvidia-green/30 text-white"
                min={1}
                max={localConfig.tpot_range_ms[1]}
              />
            </div>
            <div>
              <Label htmlFor="tpot_max" className="text-xs text-gray-400">Max</Label>
              <Input
                id="tpot_max"
                type="number"
                value={localConfig.tpot_range_ms[1]}
                onChange={(e) => handleRangeChange('tpot_range_ms', 1, parseInt(e.target.value))}
                className="bg-black/50 border-nvidia-green/30 text-white"
                min={localConfig.tpot_range_ms[0]}
                max={1000}
              />
            </div>
          </div>
          <p className="text-xs text-gray-400">Time between each output token</p>
        </div>

        {/* ITL Range */}
        <div className="space-y-3">
          <Label className="text-white">Inter-Token Latency (ITL) Range (ms)</Label>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label htmlFor="itl_min" className="text-xs text-gray-400">Min</Label>
              <Input
                id="itl_min"
                type="number"
                value={localConfig.itl_range_ms[0]}
                onChange={(e) => handleRangeChange('itl_range_ms', 0, parseInt(e.target.value))}
                className="bg-black/50 border-nvidia-green/30 text-white"
                min={1}
                max={localConfig.itl_range_ms[1]}
              />
            </div>
            <div>
              <Label htmlFor="itl_max" className="text-xs text-gray-400">Max</Label>
              <Input
                id="itl_max"
                type="number"
                value={localConfig.itl_range_ms[1]}
                onChange={(e) => handleRangeChange('itl_range_ms', 1, parseInt(e.target.value))}
                className="bg-black/50 border-nvidia-green/30 text-white"
                min={localConfig.itl_range_ms[0]}
                max={1000}
              />
            </div>
          </div>
          <p className="text-xs text-gray-400">Latency variance between tokens</p>
        </div>

        {/* Variance Percentage */}
        <div className="space-y-2">
          <Label htmlFor="variance_percentage" className="text-white">
            Variance Percentage
          </Label>
          <Input
            id="variance_percentage"
            type="number"
            step="0.1"
            value={localConfig.variance_percentage}
            onChange={(e) => handleChange('variance_percentage', parseFloat(e.target.value))}
            className="bg-black/50 border-nvidia-green/30 text-white"
            min={0}
            max={100}
          />
          <p className="text-xs text-gray-400">Random variance in timing (0-100%)</p>
        </div>

        {/* Realistic Timing */}
        <div className="flex items-center justify-between p-4 bg-black/30 border border-nvidia-green/20 rounded">
          <div>
            <Label htmlFor="realistic_timing" className="text-white">
              Realistic Timing Mode
            </Label>
            <p className="text-xs text-gray-400 mt-1">
              Use model-based realistic timing patterns
            </p>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              id="realistic_timing"
              type="checkbox"
              checked={localConfig.realistic_timing}
              onChange={(e) => handleChange('realistic_timing', e.target.checked)}
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
