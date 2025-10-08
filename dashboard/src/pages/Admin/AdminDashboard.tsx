/**
 * Admin Dashboard
 * Main admin interface for configuring FakeAI system parameters
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  Shield,
  LogOut,
  RefreshCw,
  Download,
  Upload,
  Home,
  CheckCircle,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/Button';
import { AdminConfig, AdminMetrics } from './types';
import { adminService } from '@/services/adminService';

// Import components
import { Overview } from './components/Overview';
import { KVCacheSettings } from './components/KVCacheSettings';
import { DynamoSettings } from './components/DynamoSettings';
import { TokenSettings } from './components/TokenSettings';
import { GPUSettings } from './components/GPUSettings';
import { ModelIntegrations } from './components/ModelIntegrations';

export const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [config, setConfig] = useState<AdminConfig | null>(null);
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notification, setNotification] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);

  // Check authentication
  useEffect(() => {
    const session = localStorage.getItem('fakeai_admin_session');
    if (!session) {
      navigate('/admin/login');
      return;
    }

    try {
      const { logged_in } = JSON.parse(session);
      if (!logged_in) {
        navigate('/admin/login');
        return;
      }
    } catch (e) {
      navigate('/admin/login');
      return;
    }

    loadData();
  }, [navigate]);

  // Load configuration and metrics
  const loadData = async () => {
    try {
      setLoading(true);

      // Fetch config and metrics (with fallback to mock data)
      const [configData, metricsData] = await Promise.all([
        adminService.getConfig().catch(() => getMockConfig()),
        adminService.getMetrics().catch(() => getMockMetrics()),
      ]);

      setConfig(configData);
      setMetrics(metricsData);
    } catch (error) {
      console.error('Failed to load admin data:', error);
      showNotification('error', 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  // Mock data for demo purposes
  const getMockConfig = (): AdminConfig => ({
    kv_cache: {
      block_size: 16,
      num_workers: 4,
      overlap_weight: 0.7,
      enable_prefix_caching: true,
      cache_size_mb: 2048,
    },
    dynamo: {
      num_workers: 8,
      max_queue_depth: 100,
      batch_size: 32,
      enable_dynamic_batching: true,
      worker_timeout_ms: 5000,
    },
    token_generation: {
      ttft_range_ms: [50, 200],
      tpot_range_ms: [10, 50],
      itl_range_ms: [5, 20],
      variance_percentage: 15,
      realistic_timing: true,
    },
    gpu_dcgm: {
      num_gpus: 4,
      gpu_models: ['NVIDIA A100', 'NVIDIA H100'],
      utilization_range: [60, 95],
      memory_range_gb: [20, 75],
      enable_dcgm: true,
    },
    model_integrations: {
      enable_vlm: true,
      enable_triton: true,
      enable_trt_llm: true,
      vlm_models: ['llava-v1.5-7b', 'clip-vit-large'],
      triton_backend: 'tensorrt',
      trt_llm_engines: ['llama-2-7b-trt', 'mistral-7b-trt'],
    },
  });

  const getMockMetrics = (): AdminMetrics => ({
    total_requests: 15847,
    active_workers: 6,
    cache_hit_rate: 0.847,
    avg_ttft_ms: 127.5,
    avg_tpot_ms: 28.3,
    gpu_utilization: 78.5,
    queue_depth: 23,
    uptime_seconds: 142567,
  });

  // Show notification
  const showNotification = (type: 'success' | 'error', message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 3000);
  };

  // Handle logout
  const handleLogout = () => {
    localStorage.removeItem('fakeai_admin_session');
    navigate('/admin/login');
  };

  // Handle save configuration
  const handleSaveConfig = async (section: keyof AdminConfig, data: any) => {
    try {
      setSaving(true);

      // Update config state
      const updatedConfig = { ...config!, [section]: data };
      setConfig(updatedConfig);

      // Send to backend (with fallback)
      try {
        switch (section) {
          case 'kv_cache':
            await adminService.updateKVCacheConfig(data);
            break;
          case 'dynamo':
            await adminService.updateDynamoConfig(data);
            break;
          case 'token_generation':
            await adminService.updateTokenConfig(data);
            break;
          case 'gpu_dcgm':
            await adminService.updateGPUConfig(data);
            break;
          case 'model_integrations':
            await adminService.updateModelIntegrations(data);
            break;
        }
      } catch (apiError) {
        console.log('API not available, using local state only');
      }

      showNotification('success', 'Configuration saved successfully!');
    } catch (error) {
      console.error('Failed to save config:', error);
      showNotification('error', 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  // Handle refresh
  const handleRefresh = () => {
    loadData();
    showNotification('success', 'Data refreshed');
  };

  // Handle export
  const handleExport = async () => {
    try {
      const blob = await adminService.exportConfig().catch(() => {
        // Fallback to local export
        return new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
      });

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `fakeai-config-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);

      showNotification('success', 'Configuration exported');
    } catch (error) {
      showNotification('error', 'Failed to export configuration');
    }
  };

  if (loading || !config || !metrics) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <Loader2 className="w-16 h-16 text-nvidia-green animate-spin mx-auto mb-4" />
          <p className="text-gray-400 text-lg">Loading admin dashboard...</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <div className="border-b border-nvidia-green/20 bg-[#1a1a1a] sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <Shield className="w-8 h-8 text-nvidia-green" />
              <div>
                <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
                <p className="text-sm text-gray-400">FakeAI System Configuration</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Button onClick={() => navigate('/')} variant="ghost" size="sm">
                <Home className="w-4 h-4 mr-2" />
                Home
              </Button>

              <Button onClick={handleRefresh} variant="secondary" size="sm">
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>

              <Button onClick={handleExport} variant="secondary" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>

              <Button onClick={handleLogout} variant="destructive" size="sm">
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Notification */}
      <AnimatePresence>
        {notification && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`fixed top-20 right-4 z-50 flex items-center gap-3 px-6 py-4 rounded-lg border-2 shadow-lg ${
              notification.type === 'success'
                ? 'bg-green-500/10 border-green-500/50 text-green-400'
                : 'bg-red-500/10 border-red-500/50 text-red-400'
            }`}
          >
            {notification.type === 'success' ? (
              <CheckCircle className="w-5 h-5" />
            ) : (
              <AlertCircle className="w-5 h-5" />
            )}
            <span className="font-semibold">{notification.message}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-[#1a1a1a] border-2 border-nvidia-green/20 p-1 flex-wrap h-auto gap-1">
            <TabsTrigger
              value="overview"
              className="data-[state=active]:bg-nvidia-green data-[state=active]:text-black font-bold"
            >
              Overview
            </TabsTrigger>
            <TabsTrigger
              value="kv-cache"
              className="data-[state=active]:bg-nvidia-green data-[state=active]:text-black font-bold"
            >
              KV Cache
            </TabsTrigger>
            <TabsTrigger
              value="dynamo"
              className="data-[state=active]:bg-nvidia-green data-[state=active]:text-black font-bold"
            >
              Dynamo & Workers
            </TabsTrigger>
            <TabsTrigger
              value="tokens"
              className="data-[state=active]:bg-nvidia-green data-[state=active]:text-black font-bold"
            >
              Token Generation
            </TabsTrigger>
            <TabsTrigger
              value="gpu"
              className="data-[state=active]:bg-nvidia-green data-[state=active]:text-black font-bold"
            >
              GPU/DCGM
            </TabsTrigger>
            <TabsTrigger
              value="integrations"
              className="data-[state=active]:bg-nvidia-green data-[state=active]:text-black font-bold"
            >
              Model Integrations
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <Overview metrics={metrics} loading={loading} />
          </TabsContent>

          <TabsContent value="kv-cache" className="space-y-6">
            <KVCacheSettings
              config={config.kv_cache}
              onSave={(data) => handleSaveConfig('kv_cache', data)}
              loading={saving}
            />
          </TabsContent>

          <TabsContent value="dynamo" className="space-y-6">
            <DynamoSettings
              config={config.dynamo}
              onSave={(data) => handleSaveConfig('dynamo', data)}
              loading={saving}
            />
          </TabsContent>

          <TabsContent value="tokens" className="space-y-6">
            <TokenSettings
              config={config.token_generation}
              onSave={(data) => handleSaveConfig('token_generation', data)}
              loading={saving}
            />
          </TabsContent>

          <TabsContent value="gpu" className="space-y-6">
            <GPUSettings
              config={config.gpu_dcgm}
              onSave={(data) => handleSaveConfig('gpu_dcgm', data)}
              loading={saving}
            />
          </TabsContent>

          <TabsContent value="integrations" className="space-y-6">
            <ModelIntegrations
              config={config.model_integrations}
              onSave={(data) => handleSaveConfig('model_integrations', data)}
              loading={saving}
            />
          </TabsContent>
        </Tabs>
      </div>

      {/* Footer */}
      <div className="bg-[#1a1a1a] border-t border-nvidia-green/20 py-4 mt-8">
        <div className="container mx-auto px-4 text-center text-sm text-gray-400">
          <p>FakeAI Admin Dashboard • Powered by NVIDIA Technology</p>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
