import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Volume2,
  Play,
  Pause,
  Download,
  Loader2,
  Sparkles,
  Mic
} from 'lucide-react';

interface GeneratedAudio {
  url: string;
  text: string;
  timestamp: number;
  model: string;
  voice: string;
  format: string;
  speed: number;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8765';

const VOICES = [
  { id: 'alloy', name: 'Alloy', description: 'Neutral and balanced' },
  { id: 'echo', name: 'Echo', description: 'Warm and expressive' },
  { id: 'fable', name: 'Fable', description: 'Storytelling voice' },
  { id: 'onyx', name: 'Onyx', description: 'Deep and authoritative' },
  { id: 'nova', name: 'Nova', description: 'Energetic and bright' },
  { id: 'shimmer', name: 'Shimmer', description: 'Clear and articulate' },
];

const Audio: React.FC = () => {
  const [text, setText] = useState('');
  const [model, setModel] = useState('tts-1');
  const [voice, setVoice] = useState('alloy');
  const [format, setFormat] = useState('mp3');
  const [speed, setSpeed] = useState(1.0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [audioFiles, setAudioFiles] = useState<GeneratedAudio[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [playingIndex, setPlayingIndex] = useState<number | null>(null);
  const audioRefs = useRef<(HTMLAudioElement | null)[]>([]);

  const handleGenerate = async () => {
    if (!text.trim()) {
      setError('Please enter text to convert to speech');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/v1/audio/speech`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer fake-api-key',
        },
        body: JSON.stringify({
          model: model,
          input: text,
          voice: voice,
          response_format: format,
          speed: speed,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'Failed to generate audio');
      }

      // Get the audio as a blob
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);

      const newAudio: GeneratedAudio = {
        url: url,
        text: text,
        timestamp: Date.now(),
        model: model,
        voice: voice,
        format: format,
        speed: speed,
      };

      setAudioFiles([newAudio, ...audioFiles]);
      setText('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePlayPause = (index: number) => {
    const audio = audioRefs.current[index];
    if (!audio) return;

    if (playingIndex === index) {
      audio.pause();
      setPlayingIndex(null);
    } else {
      // Pause any currently playing audio
      if (playingIndex !== null && audioRefs.current[playingIndex]) {
        audioRefs.current[playingIndex]?.pause();
      }
      audio.play();
      setPlayingIndex(index);
    }
  };

  const handleDownload = (audioFile: GeneratedAudio, index: number) => {
    const a = document.createElement('a');
    a.href = audioFile.url;
    a.download = `fakeai-audio-${Date.now()}-${index}.${audioFile.format}`;
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
              <Volume2 className="w-8 h-8 text-nvidia-green" />
              <h1 className="text-4xl font-bold">
                <span className="text-white">Text-to-Speech</span>
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

              {/* Text Input */}
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Text</label>
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-nvidia-green/50 resize-none"
                  rows={6}
                  placeholder="Enter text to convert to speech..."
                  disabled={isGenerating}
                  maxLength={4096}
                />
                <div className="text-xs text-gray-500 mt-1">
                  {text.length} / 4096 characters
                </div>
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
                  <option value="tts-1">TTS-1 (Fast)</option>
                  <option value="tts-1-hd">TTS-1-HD (High Quality)</option>
                </select>
              </div>

              {/* Voice */}
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Voice</label>
                <select
                  value={voice}
                  onChange={(e) => setVoice(e.target.value)}
                  className="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-nvidia-green/50"
                  disabled={isGenerating}
                >
                  {VOICES.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.name} - {v.description}
                    </option>
                  ))}
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
                  <option value="mp3">MP3</option>
                  <option value="opus">Opus</option>
                  <option value="aac">AAC</option>
                  <option value="flac">FLAC</option>
                  <option value="wav">WAV</option>
                  <option value="pcm">PCM</option>
                </select>
              </div>

              {/* Speed */}
              <div className="mb-6">
                <label className="block text-sm font-medium mb-2">
                  Speed: {speed.toFixed(2)}x
                </label>
                <input
                  type="range"
                  min="0.25"
                  max="4.0"
                  step="0.25"
                  value={speed}
                  onChange={(e) => setSpeed(parseFloat(e.target.value))}
                  className="w-full"
                  disabled={isGenerating}
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0.25x</span>
                  <span>4.0x</span>
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
                    <Mic className="w-5 h-5" />
                    Generate Speech
                  </>
                )}
              </motion.button>
            </div>
          </div>

          {/* Audio Files List */}
          <div className="lg:col-span-2">
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
              <h2 className="text-xl font-bold mb-6">Generated Audio</h2>

              {audioFiles.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-gray-500">
                  <Volume2 className="w-16 h-16 mb-4 opacity-50" />
                  <p className="text-lg">No audio generated yet</p>
                  <p className="text-sm">Enter text and click generate to start</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {audioFiles.map((audioFile, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="bg-black/50 border border-white/10 rounded-lg p-4 hover:border-nvidia-green/50 transition-all"
                    >
                      <div className="flex items-start gap-4">
                        <motion.button
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => handlePlayPause(index)}
                          className="flex-shrink-0 p-3 bg-nvidia-green text-black rounded-full hover:bg-nvidia-green/90 transition-colors"
                        >
                          {playingIndex === index ? (
                            <Pause className="w-6 h-6" />
                          ) : (
                            <Play className="w-6 h-6" />
                          )}
                        </motion.button>

                        <div className="flex-grow">
                          <p className="text-white mb-2">{audioFile.text}</p>
                          <div className="flex flex-wrap gap-2 text-xs text-gray-400 mb-3">
                            <span className="px-2 py-1 bg-white/5 rounded">
                              {audioFile.voice}
                            </span>
                            <span className="px-2 py-1 bg-white/5 rounded">
                              {audioFile.model}
                            </span>
                            <span className="px-2 py-1 bg-white/5 rounded">
                              {audioFile.format}
                            </span>
                            <span className="px-2 py-1 bg-white/5 rounded">
                              {audioFile.speed}x
                            </span>
                          </div>
                          <audio
                            ref={(el) => (audioRefs.current[index] = el)}
                            src={audioFile.url}
                            onEnded={() => setPlayingIndex(null)}
                            className="w-full"
                            controls
                          />
                        </div>

                        <motion.button
                          whileHover={{ scale: 1.1 }}
                          whileTap={{ scale: 0.9 }}
                          onClick={() => handleDownload(audioFile, index)}
                          className="flex-shrink-0 p-2 bg-white/5 border border-white/10 rounded-lg hover:bg-nvidia-green hover:text-black hover:border-nvidia-green transition-colors"
                        >
                          <Download className="w-5 h-5" />
                        </motion.button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Audio;
