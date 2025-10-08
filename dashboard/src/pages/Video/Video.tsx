import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Video as VideoIcon,
  Download,
  Loader2,
  Sparkles,
  Play,
  X
} from 'lucide-react';

interface GeneratedVideo {
  url: string;
  prompt: string;
  timestamp: number;
  model: string;
  size: string;
  duration: number;
  format: string;
  fps: number;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8765';

const Video: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState('runway-gen3');
  const [duration, setDuration] = useState(5.0);
  const [size, setSize] = useState('1280x720');
  const [format, setFormat] = useState('mp4');
  const [fps, setFps] = useState(24);
  const [isGenerating, setIsGenerating] = useState(false);
  const [videos, setVideos] = useState<GeneratedVideo[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedVideo, setSelectedVideo] = useState<GeneratedVideo | null>(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/v1/videos/generations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer fake-api-key',
        },
        body: JSON.stringify({
          prompt: prompt,
          model: model,
          duration: duration,
          size: size,
          format: format,
          fps: fps,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'Failed to generate video');
      }

      const data = await response.json();

      const newVideo: GeneratedVideo = {
        url: data.data[0].url,
        prompt: prompt,
        timestamp: Date.now(),
        model: model,
        size: size,
        duration: duration,
        format: format,
        fps: fps,
      };

      setVideos([newVideo, ...videos]);
      setPrompt('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = (videoUrl: string, index: number) => {
    const a = document.createElement('a');
    a.href = videoUrl;
    a.download = `fakeai-video-${Date.now()}-${index}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-nvidia-darkGray to-black text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link to="/">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="p-2 bg-white/5 border border-white/10 rounded-lg hover:border-nvidia-green/50 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </motion.button>
            </Link>
            <div className="flex items-center gap-3">
              <VideoIcon className="w-8 h-8 text-nvidia-green" />
              <h1 className="text-4xl font-bold">
                <span className="text-white">Video</span>
                <span className="gradient-text"> Generation</span>
              </h1>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Generation Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 sticky top-8">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-nvidia-green" />
                Generation Settings
              </h2>

              {/* Prompt */}
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Prompt</label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-nvidia-green/50 resize-none"
                  rows={4}
                  placeholder="A drone flying over a futuristic city at sunset..."
                  disabled={isGenerating}
                />
              </div>

              {/* Model */}
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Model</label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-nvidia-green/50"
                  disabled={isGenerating}
                >
                  <option value="runway-gen3">Runway Gen-3</option>
                  <option value="runway-gen2">Runway Gen-2</option>
                  <option value="pika-1.0">Pika 1.0</option>
                  <option value="stable-video">Stable Video Diffusion</option>
                </select>
              </div>

              {/* Duration */}
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">
                  Duration: {duration.toFixed(1)}s
                </label>
                <input
                  type="range"
                  min="1"
                  max="10"
                  step="0.5"
                  value={duration}
                  onChange={(e) => setDuration(parseFloat(e.target.value))}
                  className="w-full"
                  disabled={isGenerating}
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>1s</span>
                  <span>10s</span>
                </div>
              </div>

              {/* Size */}
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Size</label>
                <select
                  value={size}
                  onChange={(e) => setSize(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-nvidia-green/50"
                  disabled={isGenerating}
                >
                  <option value="512x512">512x512 (Square)</option>
                  <option value="1024x576">1024x576 (Widescreen)</option>
                  <option value="576x1024">576x1024 (Portrait)</option>
                  <option value="1280x720">1280x720 (HD)</option>
                  <option value="720x1280">720x1280 (Vertical HD)</option>
                </select>
              </div>

              {/* Format */}
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Format</label>
                <select
                  value={format}
                  onChange={(e) => setFormat(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-nvidia-green/50"
                  disabled={isGenerating}
                >
                  <option value="mp4">MP4</option>
                  <option value="webm">WebM</option>
                  <option value="mov">MOV</option>
                </select>
              </div>

              {/* FPS */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">
                  FPS: {fps}
                </label>
                <input
                  type="range"
                  min="12"
                  max="60"
                  step="6"
                  value={fps}
                  onChange={(e) => setFps(parseInt(e.target.value))}
                  className="w-full"
                  disabled={isGenerating}
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>12</span>
                  <span>24</span>
                  <span>30</span>
                  <span>60</span>
                </div>
              </div>

              {/* Error Display */}
              {error && (
                <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
                  {error}
                </div>
              )}

              {/* Generate Button */}
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleGenerate}
                disabled={isGenerating}
                className="w-full py-3 bg-nvidia-green text-black font-bold rounded-lg flex items-center justify-center gap-2 hover:bg-nvidia-green/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    Generate Video
                  </>
                )}
              </motion.button>
            </div>
          </div>

          {/* Video Gallery */}
          <div className="lg:col-span-2">
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
              <h2 className="text-xl font-bold mb-6">Generated Videos</h2>

              {videos.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-gray-500">
                  <VideoIcon className="w-16 h-16 mb-4 opacity-50" />
                  <p className="text-lg">No videos generated yet</p>
                  <p className="text-sm">Enter a prompt and click generate to start</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {videos.map((video, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="bg-black/50 border border-white/10 rounded-lg overflow-hidden hover:border-nvidia-green/50 transition-all"
                    >
                      {/* Video Preview Placeholder */}
                      <div className="relative bg-gradient-to-br from-purple-900/20 to-blue-900/20 aspect-video flex items-center justify-center">
                        <div className="text-center">
                          <VideoIcon className="w-16 h-16 mx-auto mb-4 text-nvidia-green/50" />
                          <p className="text-gray-400 text-sm">
                            Video generation simulated
                          </p>
                          <p className="text-gray-500 text-xs mt-1">
                            {video.size} • {video.duration}s • {video.fps}fps
                          </p>
                        </div>
                        <motion.button
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => setSelectedVideo(video)}
                          className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 hover:opacity-100 transition-opacity"
                        >
                          <div className="p-4 bg-nvidia-green rounded-full">
                            <Play className="w-8 h-8 text-black" />
                          </div>
                        </motion.button>
                      </div>

                      {/* Video Info */}
                      <div className="p-4">
                        <p className="text-white mb-3">{video.prompt}</p>
                        <div className="flex items-center justify-between">
                          <div className="flex flex-wrap gap-2 text-xs text-gray-400">
                            <span className="px-2 py-1 bg-white/5 rounded">
                              {video.model}
                            </span>
                            <span className="px-2 py-1 bg-white/5 rounded">
                              {video.format}
                            </span>
                            <span className="px-2 py-1 bg-white/5 rounded">
                              {video.size}
                            </span>
                          </div>
                          <motion.button
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={() => handleDownload(video.url, index)}
                            className="p-2 bg-white/5 border border-white/10 rounded-lg hover:bg-nvidia-green hover:text-black hover:border-nvidia-green transition-colors"
                          >
                            <Download className="w-5 h-5" />
                          </motion.button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Video Modal */}
      {selectedVideo && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedVideo(null)}
        >
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            className="relative max-w-4xl max-h-[90vh] bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setSelectedVideo(null)}
              className="absolute top-4 right-4 p-2 bg-black/50 rounded-lg hover:bg-black/70 transition-colors z-10"
            >
              <X className="w-5 h-5" />
            </button>
            <div className="aspect-video bg-gradient-to-br from-purple-900/20 to-blue-900/20 flex items-center justify-center">
              <div className="text-center">
                <VideoIcon className="w-24 h-24 mx-auto mb-4 text-nvidia-green/50" />
                <p className="text-xl mb-2">Video Preview</p>
                <p className="text-gray-400">
                  Simulated video generation - no actual video file
                </p>
              </div>
            </div>
            <div className="p-6">
              <p className="text-lg mb-4">{selectedVideo.prompt}</p>
              <div className="flex flex-wrap gap-2 text-sm text-gray-400">
                <span className="px-3 py-1 bg-white/5 rounded-full">
                  {selectedVideo.model}
                </span>
                <span className="px-3 py-1 bg-white/5 rounded-full">
                  {selectedVideo.size}
                </span>
                <span className="px-3 py-1 bg-white/5 rounded-full">
                  {selectedVideo.duration}s
                </span>
                <span className="px-3 py-1 bg-white/5 rounded-full">
                  {selectedVideo.format}
                </span>
                <span className="px-3 py-1 bg-white/5 rounded-full">
                  {selectedVideo.fps} fps
                </span>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
};

export default Video;
