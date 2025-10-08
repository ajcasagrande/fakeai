import React, { useState, useEffect, useCallback } from 'react';
import { Settings as SettingsIcon, Menu } from 'lucide-react';
import ChatSidebar from './ChatSidebar';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';
import ChatSettings from './ChatSettings';
import ModelSelector from './ModelSelector';
import chatAPI from './api';
import {
  type Conversation,
  type Message,
  type ChatSettings as ChatSettingsType,
  type TokenUsage,
  DEFAULT_SETTINGS,
  AVAILABLE_MODELS,
  isReasoningModel,
} from './types';

const STORAGE_KEY = 'fakeai-chat-conversations';
const SETTINGS_KEY = 'fakeai-chat-settings';

const Chat: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [settings, setSettings] = useState<ChatSettingsType>(DEFAULT_SETTINGS);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [enableReasoning, setEnableReasoning] = useState(true);
  const [tokenUsage, setTokenUsage] = useState<TokenUsage>({
    promptTokens: 0,
    completionTokens: 0,
    totalTokens: 0,
    estimatedCost: 0,
  });

  // Load conversations and settings from localStorage
  useEffect(() => {
    const savedConversations = localStorage.getItem(STORAGE_KEY);
    if (savedConversations) {
      try {
        const parsed = JSON.parse(savedConversations);
        setConversations(parsed);
      } catch (e) {
        console.error('Error loading conversations:', e);
      }
    }

    const savedSettings = localStorage.getItem(SETTINGS_KEY);
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(parsed);
      } catch (e) {
        console.error('Error loading settings:', e);
      }
    }
  }, []);

  // Save conversations to localStorage
  useEffect(() => {
    if (conversations.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    }
  }, [conversations]);

  // Save settings to localStorage
  useEffect(() => {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  }, [settings]);

  const currentConversation = conversations.find(
    (conv) => conv.id === currentConversationId
  );

  const generateConversationTitle = (firstMessage: string): string => {
    const title = firstMessage.slice(0, 50);
    return title.length < firstMessage.length ? title + '...' : title;
  };

  const createNewConversation = useCallback((): Conversation => {
    const newConversation: Conversation = {
      id: `conv-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      title: 'New Chat',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
      model: settings.model,
      systemPrompt: settings.systemPrompt,
    };
    return newConversation;
  }, [settings]);

  const handleNewChat = useCallback(() => {
    const newConv = createNewConversation();
    setConversations((prev) => [newConv, ...prev]);
    setCurrentConversationId(newConv.id);
    setTokenUsage({
      promptTokens: 0,
      completionTokens: 0,
      totalTokens: 0,
      estimatedCost: 0,
    });
  }, [createNewConversation]);

  const handleSelectConversation = useCallback((conversationId: string) => {
    setCurrentConversationId(conversationId);
    setIsSidebarOpen(false);
  }, []);

  const handleDeleteConversation = useCallback((conversationId: string) => {
    setConversations((prev) => prev.filter((conv) => conv.id !== conversationId));
    if (currentConversationId === conversationId) {
      setCurrentConversationId(null);
    }
  }, [currentConversationId]);

  const updateConversation = useCallback((conversationId: string, updates: Partial<Conversation>) => {
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === conversationId
          ? { ...conv, ...updates, updatedAt: Date.now() }
          : conv
      )
    );
  }, []);

  const addMessage = useCallback((conversationId: string, message: Message) => {
    setConversations((prev) =>
      prev.map((conv) => {
        if (conv.id === conversationId) {
          const newMessages = [...conv.messages, message];
          const title = conv.messages.length === 0 && message.role === 'user'
            ? generateConversationTitle(message.content)
            : conv.title;
          return {
            ...conv,
            messages: newMessages,
            title,
            updatedAt: Date.now(),
          };
        }
        return conv;
      })
    );
  }, []);

  const updateMessage = useCallback((conversationId: string, messageId: string, updates: Partial<Message>) => {
    setConversations((prev) =>
      prev.map((conv) => {
        if (conv.id === conversationId) {
          return {
            ...conv,
            messages: conv.messages.map((msg) =>
              msg.id === messageId ? { ...msg, ...updates } : msg
            ),
            updatedAt: Date.now(),
          };
        }
        return conv;
      })
    );
  }, []);

  const calculateCost = (promptTokens: number, completionTokens: number, model: string): number => {
    const modelData = AVAILABLE_MODELS.find((m) => m.id === model);
    if (!modelData) return 0;

    const promptCost = (promptTokens / 1000) * modelData.costPer1kPrompt;
    const completionCost = (completionTokens / 1000) * modelData.costPer1kCompletion;
    return promptCost + completionCost;
  };

  const handleSendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    let conversationId = currentConversationId;

    // Create new conversation if none exists
    if (!conversationId) {
      const newConv = createNewConversation();
      setConversations((prev) => [newConv, ...prev]);
      conversationId = newConv.id;
      setCurrentConversationId(newConv.id);
    }

    const userMessage: Message = {
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      role: 'user',
      content,
      timestamp: Date.now(),
    };

    addMessage(conversationId, userMessage);

    const assistantMessage: Message = {
      id: `msg-${Date.now() + 1}-${Math.random().toString(36).substr(2, 9)}`,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isStreaming: true,
    };

    addMessage(conversationId, assistantMessage);
    setIsGenerating(true);

    try {
      const conversation = conversations.find((c) => c.id === conversationId) ||
                          { messages: [userMessage], systemPrompt: settings.systemPrompt };

      const messages = [
        { role: 'system' as const, content: settings.systemPrompt },
        ...conversation.messages.map((m) => ({
          role: m.role as 'user' | 'assistant',
          content: m.content,
        })),
        { role: 'user' as const, content },
      ];

      const stream = chatAPI.createStreamingCompletion({
        model: settings.model,
        messages,
        temperature: settings.temperature,
        max_tokens: settings.maxTokens,
      });

      let fullContent = '';
      let fullReasoningContent = '';
      for await (const chunk of stream) {
        // Handle reasoning content from reasoning models
        if (typeof chunk === 'object' && chunk.reasoning_content) {
          fullReasoningContent += chunk.reasoning_content;
          updateMessage(conversationId, assistantMessage.id, {
            content: fullContent,
            reasoning_content: fullReasoningContent,
            isStreaming: true,
          });
        } else if (typeof chunk === 'object' && chunk.content) {
          // Object with content property
          fullContent += chunk.content;
          updateMessage(conversationId, assistantMessage.id, {
            content: fullContent,
            reasoning_content: fullReasoningContent || undefined,
            isStreaming: true,
          });
        } else if (typeof chunk === 'string') {
          fullContent += chunk;
          updateMessage(conversationId, assistantMessage.id, {
            content: fullContent,
            reasoning_content: fullReasoningContent || undefined,
            isStreaming: true,
          });
        }
      }

      updateMessage(conversationId, assistantMessage.id, {
        content: fullContent,
        reasoning_content: fullReasoningContent || undefined,
        isStreaming: false,
      });

      // Debug: Check if content has newlines
      console.log('Full content length:', fullContent.length);
      console.log('Has newlines:', fullContent.includes('\n'));
      console.log('Newline count:', (fullContent.match(/\n/g) || []).length);
      console.log('First 200 chars:', fullContent.substring(0, 200));

      // Estimate token usage (rough approximation)
      const estimatedPromptTokens = messages.reduce((acc, m) => acc + Math.ceil(m.content.length / 4), 0);
      const estimatedCompletionTokens = Math.ceil(fullContent.length / 4);
      const estimatedCost = calculateCost(estimatedPromptTokens, estimatedCompletionTokens, settings.model);

      setTokenUsage((prev) => ({
        promptTokens: prev.promptTokens + estimatedPromptTokens,
        completionTokens: prev.completionTokens + estimatedCompletionTokens,
        totalTokens: prev.totalTokens + estimatedPromptTokens + estimatedCompletionTokens,
        estimatedCost: prev.estimatedCost + estimatedCost,
      }));
    } catch (error) {
      console.error('Error sending message:', error);
      updateMessage(conversationId, assistantMessage.id, {
        content: '',
        isStreaming: false,
        error: error instanceof Error ? error.message : 'Failed to generate response',
      });
    } finally {
      setIsGenerating(false);
    }
  }, [currentConversationId, conversations, settings, createNewConversation, addMessage, updateMessage]);

  const handleStopGeneration = useCallback(() => {
    setIsGenerating(false);
    // In a real implementation, you would abort the fetch request here
  }, []);

  const handleEditMessage = useCallback((messageId: string) => {
    // TODO: Implement message editing
    console.log('Edit message:', messageId);
  }, []);

  const handleDeleteMessage = useCallback((messageId: string) => {
    if (currentConversationId) {
      setConversations((prev) =>
        prev.map((conv) => {
          if (conv.id === currentConversationId) {
            return {
              ...conv,
              messages: conv.messages.filter((msg) => msg.id !== messageId),
              updatedAt: Date.now(),
            };
          }
          return conv;
        })
      );
    }
  }, [currentConversationId]);

  const handleRegenerateResponse = useCallback(async (messageId: string) => {
    if (!currentConversationId || isGenerating) return;

    const conversation = conversations.find((c) => c.id === currentConversationId);
    if (!conversation) return;

    // Find the message to regenerate
    const messageIndex = conversation.messages.findIndex((m) => m.id === messageId);
    if (messageIndex === -1 || conversation.messages[messageIndex].role !== 'assistant') return;

    // Find the previous user message
    let userMessageContent = '';
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (conversation.messages[i].role === 'user') {
        userMessageContent = conversation.messages[i].content;
        break;
      }
    }

    if (!userMessageContent) return;

    // Remove the assistant message we're regenerating
    setConversations((prev) =>
      prev.map((conv) => {
        if (conv.id === currentConversationId) {
          return {
            ...conv,
            messages: conv.messages.filter((msg) => msg.id !== messageId),
            updatedAt: Date.now(),
          };
        }
        return conv;
      })
    );

    // Create a new assistant message with "Regenerating..." state
    const newAssistantMessage: Message = {
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isStreaming: true,
    };

    addMessage(currentConversationId, newAssistantMessage);
    setIsGenerating(true);

    try {
      // Get all messages up to (but not including) the removed assistant message
      const messagesForRegeneration = conversation.messages
        .slice(0, messageIndex)
        .map((m) => ({
          role: m.role as 'user' | 'assistant',
          content: m.content,
        }));

      const messages = [
        { role: 'system' as const, content: settings.systemPrompt },
        ...messagesForRegeneration,
      ];

      const stream = chatAPI.createStreamingCompletion({
        model: settings.model,
        messages,
        temperature: settings.temperature,
        max_tokens: settings.maxTokens,
      });

      let fullContent = '';
      let fullReasoningContent = '';
      for await (const chunk of stream) {
        if (typeof chunk === 'object' && chunk.reasoning_content) {
          fullReasoningContent += chunk.reasoning_content;
          updateMessage(currentConversationId, newAssistantMessage.id, {
            content: fullContent,
            reasoning_content: fullReasoningContent,
            isStreaming: true,
          });
        } else if (typeof chunk === 'string') {
          fullContent += chunk;
          updateMessage(currentConversationId, newAssistantMessage.id, {
            content: fullContent,
            reasoning_content: fullReasoningContent || undefined,
            isStreaming: true,
          });
        }
      }

      updateMessage(currentConversationId, newAssistantMessage.id, {
        content: fullContent,
        reasoning_content: fullReasoningContent || undefined,
        isStreaming: false,
      });

      // Update token usage
      const estimatedPromptTokens = messages.reduce((acc, m) => acc + Math.ceil(m.content.length / 4), 0);
      const estimatedCompletionTokens = Math.ceil(fullContent.length / 4);
      const estimatedCost = calculateCost(estimatedPromptTokens, estimatedCompletionTokens, settings.model);

      setTokenUsage((prev) => ({
        promptTokens: prev.promptTokens + estimatedPromptTokens,
        completionTokens: prev.completionTokens + estimatedCompletionTokens,
        totalTokens: prev.totalTokens + estimatedPromptTokens + estimatedCompletionTokens,
        estimatedCost: prev.estimatedCost + estimatedCost,
      }));
    } catch (error) {
      console.error('Error regenerating response:', error);
      updateMessage(currentConversationId, newAssistantMessage.id, {
        content: '',
        isStreaming: false,
        error: error instanceof Error ? error.message : 'Failed to regenerate response',
      });
    } finally {
      setIsGenerating(false);
    }
  }, [currentConversationId, conversations, settings, isGenerating, addMessage, updateMessage, calculateCost]);

  const handleExportChat = useCallback((format: 'json' | 'markdown') => {
    if (!currentConversation) return;

    let content: string;
    let filename: string;
    let mimeType: string;

    if (format === 'json') {
      content = JSON.stringify(currentConversation, null, 2);
      filename = `chat-${currentConversation.id}.json`;
      mimeType = 'application/json';
    } else {
      content = `# ${currentConversation.title}\n\n`;
      content += `**Model:** ${currentConversation.model}\n\n`;
      content += `**Created:** ${new Date(currentConversation.createdAt).toLocaleString()}\n\n`;
      content += '---\n\n';

      currentConversation.messages.forEach((msg) => {
        const role = msg.role === 'user' ? 'User' : 'Assistant';
        content += `### ${role}\n\n${msg.content}\n\n`;
      });

      filename = `chat-${currentConversation.id}.md`;
      mimeType = 'text/markdown';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }, [currentConversation]);

  const handleClearChat = useCallback(() => {
    if (currentConversationId && window.confirm('Are you sure you want to clear this conversation?')) {
      updateConversation(currentConversationId, { messages: [] });
      setTokenUsage({
        promptTokens: 0,
        completionTokens: 0,
        totalTokens: 0,
        estimatedCost: 0,
      });
    }
  }, [currentConversationId, updateConversation]);

  return (
    <div className="flex h-screen bg-gradient-to-br from-black via-gray-900 to-black text-gray-200 overflow-hidden">
      <ChatSidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onNewChat={handleNewChat}
        onSelectConversation={handleSelectConversation}
        onDeleteConversation={handleDeleteConversation}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      <div className="flex-1 flex flex-col bg-[#0a0a0a] relative">
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-[#111]">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2 bg-white/5 border border-white/10 text-white rounded-lg hover:bg-white/10 hover:border-green-500 transition-all md:hidden"
              title="Toggle sidebar"
            >
              <Menu size={20} />
            </button>
            <ModelSelector
              selectedModel={settings.model}
              onModelChange={(model) => setSettings({ ...settings, model })}
            />
            {isReasoningModel(settings.model) && (
              <label className="flex items-center gap-2 px-3 py-2 bg-purple-500/10 border border-purple-500/30 rounded-lg cursor-pointer hover:bg-purple-500/20 transition-all">
                <input
                  type="checkbox"
                  checked={enableReasoning}
                  onChange={(e) => setEnableReasoning(e.target.checked)}
                  className="w-4 h-4 rounded border-purple-500/50 bg-purple-500/10 text-purple-500 focus:ring-purple-500 focus:ring-offset-0"
                />
                <span className="text-sm font-medium text-purple-300">Show Reasoning</span>
              </label>
            )}
          </div>
          <button
            onClick={() => setIsSettingsOpen(true)}
            className="p-2 bg-white/5 border border-white/10 text-white rounded-lg hover:bg-white/10 hover:border-green-500 transition-all flex items-center justify-center"
            title="Settings"
          >
            <SettingsIcon size={20} />
          </button>
        </div>

        <ChatMessages
          messages={currentConversation?.messages || []}
          isLoading={isGenerating && !currentConversation?.messages.some(m => m.isStreaming)}
          onEditMessage={handleEditMessage}
          onDeleteMessage={handleDeleteMessage}
          onRegenerateResponse={handleRegenerateResponse}
          onSendMessage={handleSendMessage}
          enableReasoning={enableReasoning}
        />

        <ChatInput
          onSendMessage={handleSendMessage}
          onStopGeneration={handleStopGeneration}
          isGenerating={isGenerating}
          disabled={isGenerating}
        />
      </div>

      <ChatSettings
        settings={settings}
        onUpdateSettings={setSettings}
        tokenUsage={tokenUsage}
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onExportChat={handleExportChat}
        onClearChat={handleClearChat}
      />
    </div>
  );
};

export default Chat;
