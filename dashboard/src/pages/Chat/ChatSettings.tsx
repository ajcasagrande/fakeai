import React from 'react';
import { Settings, X, Download } from 'lucide-react';
import { AVAILABLE_MODELS, type ChatSettings as ChatSettingsType, type TokenUsage } from './types';

interface ChatSettingsProps {
  settings: ChatSettingsType;
  onUpdateSettings: (settings: ChatSettingsType) => void;
  tokenUsage?: TokenUsage;
  isOpen: boolean;
  onClose: () => void;
  onExportChat?: (format: 'json' | 'markdown') => void;
  onClearChat?: () => void;
}

const ChatSettings: React.FC<ChatSettingsProps> = ({
  settings,
  onUpdateSettings,
  tokenUsage,
  isOpen,
  onClose,
  onExportChat,
  onClearChat,
}) => {
  if (!isOpen) return null;

  const handleModelChange = (model: string) => {
    onUpdateSettings({ ...settings, model });
  };

  const handleTemperatureChange = (temperature: number) => {
    onUpdateSettings({ ...settings, temperature });
  };

  const handleMaxTokensChange = (maxTokens: number) => {
    onUpdateSettings({ ...settings, maxTokens });
  };

  const handleSystemPromptChange = (systemPrompt: string) => {
    onUpdateSettings({ ...settings, systemPrompt });
  };

  return (
    <>
      <div className="fixed inset-0 bg-black/70 z-[1000] animate-fadeIn" onClick={onClose} />
      <div className="fixed top-0 right-0 w-full max-w-md h-screen bg-[#111] border-l border-white/10 z-[1001] flex flex-col animate-slideInRight">
        <div className="flex items-center justify-between px-6 py-6 border-b border-white/10">
          <div className="flex items-center gap-3 text-green-500">
            <Settings size={20} />
            <h2 className="text-xl font-semibold">Chat Settings</h2>
          </div>
          <button onClick={onClose} className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-all">
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-6 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
          <div className="mb-8">
            <label className="block text-sm font-semibold text-white mb-2">Model</label>
            <select
              value={settings.model}
              onChange={(e) => handleModelChange(e.target.value)}
              className="w-full bg-white/5 border border-white/10 text-white px-3 py-3 rounded-lg transition-all focus:outline-none focus:border-green-500 focus:bg-white/10 font-mono text-sm"
            >
              {(() => {
                // Group models by provider
                const grouped = AVAILABLE_MODELS.reduce((acc, model) => {
                  if (!acc[model.provider]) acc[model.provider] = [];
                  acc[model.provider].push(model);
                  return acc;
                }, {} as Record<string, typeof AVAILABLE_MODELS>);

                return Object.entries(grouped).map(([provider, models]) => (
                  <optgroup key={provider} label={`━━━ ${provider} (${models.length} models) ━━━`} className="bg-gray-900">
                    {models.map((model) => (
                      <option key={model.id} value={model.id} className="bg-gray-900">
                        {model.name} | {(model.contextWindow / 1000).toFixed(0)}K ctx | ${(model.costPer1kPrompt * 1000).toFixed(2)}/M
                      </option>
                    ))}
                  </optgroup>
                ));
              })()}
            </select>
            <div className="mt-3 p-3 bg-white/5 border border-white/10 rounded-lg">
              <div className="text-xs text-gray-300 leading-relaxed">
                {(() => {
                  const selected = AVAILABLE_MODELS.find((m) => m.id === settings.model);
                  if (!selected) return 'Choose the AI model for your conversation';

                  return (
                    <>
                      <div className="font-semibold text-green-500 mb-1">{selected.description}</div>
                      <div className="text-gray-400">
                        Context: {(selected.contextWindow ?? 0).toLocaleString()} tokens •
                        Cost: ${((selected.costPer1kPrompt ?? 0) * 1000).toFixed(2)}/${((selected.costPer1kCompletion ?? 0) * 1000).toFixed(2)} per M
                      </div>
                      {selected.tags && selected.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {selected.tags.map((tag) => (
                            <span key={tag} className="px-2 py-0.5 bg-green-500/20 text-green-500 text-xs rounded-full">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </>
                  );
                })()}
              </div>
            </div>
          </div>

          <div className="mb-8">
            <label className="block text-sm font-semibold text-white mb-2">
              Temperature: {settings.temperature.toFixed(2)}
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.01"
              value={settings.temperature}
              onChange={(e) => handleTemperatureChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-white/10 rounded-full outline-none appearance-none [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:bg-gradient-to-br [&::-webkit-slider-thumb]:from-green-500 [&::-webkit-slider-thumb]:to-green-700 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:transition-all [&::-webkit-slider-thumb]:hover:scale-110"
            />
            <p className="mt-2 text-xs text-gray-400 leading-relaxed">
              Controls randomness: 0 is focused, 2 is creative
            </p>
          </div>

          <div className="mb-8">
            <label className="block text-sm font-semibold text-white mb-2">Max Tokens</label>
            <input
              type="number"
              min="1"
              max="32000"
              value={settings.maxTokens}
              onChange={(e) => handleMaxTokensChange(parseInt(e.target.value, 10))}
              className="w-full bg-white/5 border border-white/10 text-white px-3 py-3 rounded-lg transition-all focus:outline-none focus:border-green-500 focus:bg-white/10"
            />
            <p className="mt-2 text-xs text-gray-400 leading-relaxed">
              Maximum length of the response
            </p>
          </div>

          <div className="mb-8">
            <label className="block text-sm font-semibold text-white mb-2">System Prompt</label>
            <textarea
              value={settings.systemPrompt}
              onChange={(e) => handleSystemPromptChange(e.target.value)}
              className="w-full bg-white/5 border border-white/10 text-white px-3 py-3 rounded-lg transition-all focus:outline-none focus:border-green-500 focus:bg-white/10 resize-none"
              rows={4}
              placeholder="You are a helpful AI assistant."
            />
            <p className="mt-2 text-xs text-gray-400 leading-relaxed">
              Set the behavior and personality of the assistant
            </p>
          </div>

          {tokenUsage && (
            <div className="mb-8 bg-white/5 border border-white/10 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-green-500 uppercase tracking-wide mb-4">Token Usage</h3>
              <div className="flex flex-col gap-3">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-400">Prompt Tokens:</span>
                  <span className="font-semibold text-white font-mono">{(tokenUsage.promptTokens ?? 0).toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-400">Completion Tokens:</span>
                  <span className="font-semibold text-white font-mono">{(tokenUsage.completionTokens ?? 0).toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-400">Total Tokens:</span>
                  <span className="font-semibold text-white font-mono">{(tokenUsage.totalTokens ?? 0).toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-center text-sm pt-3 border-t border-white/10 mt-2">
                  <span className="text-green-500 font-semibold">Estimated Cost:</span>
                  <span className="text-lg font-bold text-green-500 font-mono">${(tokenUsage.estimatedCost ?? 0).toFixed(4)}</span>
                </div>
              </div>
            </div>
          )}

          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-green-500 uppercase tracking-wide mb-4">Actions</h3>
            <div className="flex flex-col gap-2">
              {onExportChat && (
                <>
                  <button
                    onClick={() => onExportChat('json')}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 font-medium bg-white/5 hover:bg-white/10 text-white rounded-lg transition-all"
                  >
                    <Download size={16} />
                    Export as JSON
                  </button>
                  <button
                    onClick={() => onExportChat('markdown')}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 font-medium bg-white/5 hover:bg-white/10 text-white rounded-lg transition-all"
                  >
                    <Download size={16} />
                    Export as Markdown
                  </button>
                </>
              )}
              {onClearChat && (
                <button
                  onClick={onClearChat}
                  className="w-full px-4 py-3 font-medium bg-red-500/10 hover:bg-red-500 text-red-400 hover:text-white rounded-lg transition-all"
                >
                  Clear Conversation
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default ChatSettings;
