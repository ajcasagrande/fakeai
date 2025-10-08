import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  MessageSquare,
  Zap,
  Sparkles,
  ArrowRight,
  Activity,
  TrendingUp,
  Brain,
  BarChart3,
  Cpu,
  Gauge,
  Database,
  ImageIcon,
  Volume2,
  Video as VideoIcon,
  Shield
} from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-black">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center mb-16"
        >
          <div className="flex items-center justify-center gap-3 mb-6">
            <Sparkles className="w-12 h-12 text-nvidia-green" />
            <h1 className="text-7xl font-bold">
              <span className="text-white">FakeAI</span>
              <span className="gradient-text"> Dashboard</span>
            </h1>
          </div>

          <h2 className="text-3xl text-gray-300 mb-6">
            OpenAI-Compatible API <span className="text-nvidia-green">Testing Platform</span>
          </h2>

          <p className="text-xl text-gray-400 max-w-3xl mx-auto mb-16">
            Comprehensive testing and monitoring dashboard for OpenAI-compatible APIs
            with real-time metrics, GPU monitoring, and interactive visualizations
          </p>
        </motion.div>

        {/* Features Grid - Now Clickable */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
          <FeatureCard
            icon={<MessageSquare className="w-8 h-8" />}
            title="Interactive Chat Interface"
            description="ChatGPT-style interface for testing conversational AI with streaming responses"
            link="/chat"
            delay={0.1}
          />

          <FeatureCard
            icon={<BarChart3 className="w-8 h-8" />}
            title="AIPerf Benchmarks"
            description="Comprehensive benchmark results visualization with TTFT, latency, and throughput metrics"
            link="/benchmarks"
            delay={0.2}
          />

          <FeatureCard
            icon={<Zap className="w-8 h-8" />}
            title="AI-Dynamo Performance"
            description="Advanced AI-Dynamo integration for detailed model performance analysis"
            link="/ai-dynamo"
            delay={0.3}
          />

          <FeatureCard
            icon={<Database className="w-8 h-8" />}
            title="KV Cache Monitoring"
            description="Real-time tracking of KV cache performance with hit rates and speedup metrics"
            link="/kv-cache"
            delay={0.4}
          />

          <FeatureCard
            icon={<Cpu className="w-8 h-8" />}
            title="GPU Metrics (DCGM)"
            description="Monitor NVIDIA GPU performance with real-time DCGM metrics: utilization, temperature, power, memory, and throttling"
            link="/dcgm"
            delay={0.5}
          />

          <FeatureCard
            icon={<Gauge className="w-8 h-8" />}
            title="System Monitoring"
            description="Comprehensive system metrics tracking for resource utilization"
            link="/metrics"
            delay={0.6}
          />

          <FeatureCard
            icon={<Activity className="w-8 h-8" />}
            title="Real-Time LLM Metrics"
            description="Live monitoring of LLM inference performance with comprehensive tracking"
            link="/metrics"
            delay={0.7}
          />

          <FeatureCard
            icon={<TrendingUp className="w-8 h-8" />}
            title="Performance Trends"
            description="Historical analysis and predictive analytics for capacity planning"
            link="/metrics"
            delay={0.8}
          />

          <FeatureCard
            icon={<Brain className="w-8 h-8" />}
            title="Advanced Analytics"
            description="Track throughput, latency, token usage, and performance trends"
            link="/metrics"
            delay={0.9}
          />

          <FeatureCard
            icon={<ImageIcon className="w-8 h-8" />}
            title="Image Generation"
            description="Create images from text prompts using DALL-E and Stable Diffusion models"
            link="/images"
            delay={1.0}
          />

          <FeatureCard
            icon={<Volume2 className="w-8 h-8" />}
            title="Text-to-Speech"
            description="Convert text to natural-sounding speech with multiple voices and formats"
            link="/audio"
            delay={1.1}
          />

          <FeatureCard
            icon={<VideoIcon className="w-8 h-8" />}
            title="Video Generation"
            description="Generate videos from text prompts with customizable duration and quality"
            link="/video"
            delay={1.2}
          />

          <FeatureCard
            icon={<Shield className="w-8 h-8" />}
            title="Admin Dashboard"
            description="Configure system settings, manage KV cache, workers, and model integrations"
            link="/admin/login"
            delay={1.3}
          />
        </div>

        {/* Stats Section */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 0.5 }}
          className="mt-20 grid grid-cols-1 md:grid-cols-4 gap-8 max-w-6xl mx-auto"
        >
          <StatCard value="100%" label="API Compatible" />
          <StatCard value="Real-Time" label="Monitoring" />
          <StatCard value="10" label="Active Pages" />
          <StatCard value="∞" label="Metrics Tracked" />
        </motion.div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2, duration: 0.5 }}
          className="mt-20 text-center text-gray-500"
        >
          <p className="mb-2">
            Powered by <span className="text-nvidia-green font-bold">NVIDIA</span> •
            Built with <span className="text-nvidia-green">AI-Dynamo</span> &
            <span className="text-nvidia-green"> DCGM</span>
          </p>
          <p className="text-sm">
            OpenAI-Compatible API Testing Platform
          </p>
        </motion.div>
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
  link,
  delay
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  link: string;
  delay: number;
}) {
  return (
    <Link to={link}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay, duration: 0.5 }}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="p-8 bg-[#1a1a1a] border-2 border-nvidia-green/20 hover:border-nvidia-green hover:bg-nvidia-green/5 transition-all cursor-pointer group h-full"
      >
        <div className="text-nvidia-green mb-4 group-hover:scale-110 transition-transform">
          {icon}
        </div>
        <h3 className="text-xl font-bold text-white mb-3">{title}</h3>
        <p className="text-gray-400 leading-relaxed">{description}</p>
      </motion.div>
    </Link>
  );
}

function StatCard({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center p-6 bg-[#1a1a1a] border-2 border-nvidia-green/20">
      <div className="text-5xl font-bold text-nvidia-green mb-2">{value}</div>
      <div className="text-gray-400 text-sm uppercase tracking-wider">{label}</div>
    </div>
  );
}
