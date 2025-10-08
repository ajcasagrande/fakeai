import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  ImageIcon,
  Download,
  Loader2,
  Sparkles,
  X
} from 'lucide-react';

interface GeneratedImage {
  url: string;
  prompt: string;
  timestamp: number;
  model: string;
  size: string;
  quality: string;
  style: string;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8765';

const Images: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState('dall-e-3');
  const [numImages, setNumImages] = useState(1);
  const [size, setSize] = useState('1024x1024');
  const [quality, setQuality] = useState('standard');
  const [style, setStyle] = useState('vivid');
  const [isGenerating, setIsGenerating] = useState(false);
  const [images, setImages] = useState<GeneratedImage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState<GeneratedImage | null>(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/v1/images/generations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer fake-api-key',
        },
        body: JSON.stringify({
          prompt: prompt,
          model: model,
          n: numImages,
          size: size,
          quality: quality,
          style: style,
          response_format: 'url'
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'Failed to generate images');
      }

      const data = await response.json();

      const newImages: GeneratedImage[] = data.data.map((img: any) => ({
        url: img.url,
        prompt: prompt,
        timestamp: Date.now(),
        model: model,
        size: size,
        quality: quality,
        style: style,
      }));

      setImages([...newImages, ...images]);
      setPrompt('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = async (imageUrl: string, index: number) => {
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `fakeai-image-${Date.now()}-${index}.png`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to download image:', err);
    }
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
              <ImageIcon className="w-8 h-8 text-nvidia-green" />
              <h1 className="text-4xl font-bold">
                <span className="text-white">Image</span>
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
                  placeholder="A serene landscape with mountains and a lake..."
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
                  <option value="dall-e-3">DALL-E 3</option>
                  <option value="dall-e-2">DALL-E 2</option>
                  <option value="stabilityai/stable-diffusion-2-1">Stable Diffusion 2.1</option>
                </select>
              </div>

              {/* Number of Images */}
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">
                  Number of Images: {numImages}
                </label>
                <input
                  type="range"
                  min="1"
                  max="4"
                  value={numImages}
                  onChange={(e) => setNumImages(parseInt(e.target.value))}
                  className="w-full"
                  disabled={isGenerating}
                />
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
                  <option value="256x256">256x256</option>
                  <option value="512x512">512x512</option>
                  <option value="1024x1024">1024x1024</option>
                  <option value="1024x1792">1024x1792 (Portrait)</option>
                  <option value="1792x1024">1792x1024 (Landscape)</option>
                </select>
              </div>

              {/* Quality */}
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Quality</label>
                <select
                  value={quality}
                  onChange={(e) => setQuality(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-nvidia-green/50"
                  disabled={isGenerating}
                >
                  <option value="standard">Standard</option>
                  <option value="hd">HD</option>
                </select>
              </div>

              {/* Style */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">Style</label>
                <select
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-nvidia-green/50"
                  disabled={isGenerating}
                >
                  <option value="vivid">Vivid</option>
                  <option value="natural">Natural</option>
                </select>
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
                    Generate Images
                  </>
                )}
              </motion.button>
            </div>
          </div>

          {/* Gallery */}
          <div className="lg:col-span-2">
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
              <h2 className="text-xl font-bold mb-6">Generated Images</h2>

              {images.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-gray-500">
                  <ImageIcon className="w-16 h-16 mb-4 opacity-50" />
                  <p className="text-lg">No images generated yet</p>
                  <p className="text-sm">Enter a prompt and click generate to start</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {images.map((image, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="group relative bg-black/50 border border-white/10 rounded-lg overflow-hidden hover:border-nvidia-green/50 transition-all cursor-pointer"
                      onClick={() => setSelectedImage(image)}
                    >
                      <img
                        src={image.url}
                        alt={image.prompt}
                        className="w-full h-auto object-cover"
                      />
                      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-4 p-4">
                        <p className="text-sm text-center line-clamp-2">{image.prompt}</p>
                        <div className="flex gap-2">
                          <motion.button
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDownload(image.url, index);
                            }}
                            className="p-2 bg-nvidia-green text-black rounded-lg hover:bg-nvidia-green/90 transition-colors"
                          >
                            <Download className="w-5 h-5" />
                          </motion.button>
                        </div>
                      </div>
                      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
                        <p className="text-xs text-gray-400">{image.model} • {image.size}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Image Modal */}
      {selectedImage && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedImage(null)}
        >
          <motion.div
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            className="relative max-w-4xl max-h-[90vh] bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute top-4 right-4 p-2 bg-black/50 rounded-lg hover:bg-black/70 transition-colors z-10"
            >
              <X className="w-5 h-5" />
            </button>
            <img
              src={selectedImage.url}
              alt={selectedImage.prompt}
              className="w-full h-auto max-h-[70vh] object-contain"
            />
            <div className="p-6">
              <p className="text-lg mb-4">{selectedImage.prompt}</p>
              <div className="flex flex-wrap gap-2 text-sm text-gray-400">
                <span className="px-3 py-1 bg-white/5 rounded-full">{selectedImage.model}</span>
                <span className="px-3 py-1 bg-white/5 rounded-full">{selectedImage.size}</span>
                <span className="px-3 py-1 bg-white/5 rounded-full">{selectedImage.quality}</span>
                <span className="px-3 py-1 bg-white/5 rounded-full">{selectedImage.style}</span>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
};

export default Images;
