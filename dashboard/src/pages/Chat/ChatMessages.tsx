import React, { useEffect, useRef } from 'react';
import { Loader2 } from 'lucide-react';
import ChatMessage from './ChatMessage';
import type { Message } from './types';

interface ChatMessagesProps {
  messages: Message[];
  isLoading?: boolean;
  onEditMessage?: (messageId: string) => void;
  onDeleteMessage?: (messageId: string) => void;
  onRegenerateResponse?: (messageId: string) => void;
  onSendMessage?: (content: string) => void;
  enableReasoning?: boolean;
}

const ChatMessages: React.FC<ChatMessagesProps> = ({
  messages,
  isLoading = false,
  onEditMessage,
  onDeleteMessage,
  onRegenerateResponse,
  onSendMessage,
  enableReasoning = true,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 overflow-y-auto">
        <div className="text-center max-w-2xl">
          <div className="text-6xl mb-4">💬</div>
          <h2 className="text-3xl font-bold text-white mb-2">Start a Conversation</h2>
          <p className="text-base text-gray-400 mb-8">
            Send a message to begin chatting with the AI assistant
          </p>
          <div>
            <h3 className="text-sm font-semibold text-green-500 uppercase tracking-wide mb-4">Try asking:</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <button
                onClick={() => onSendMessage?.('Explain quantum computing in simple terms')}
                className="px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white text-sm hover:bg-white/10 hover:border-green-500/50 transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-green-500/20 text-left group cursor-pointer"
              >
                <span className="group-hover:text-green-500 transition-colors">Explain quantum computing in simple terms</span>
              </button>
              <button
                onClick={() => onSendMessage?.('Write a Python function to sort a list')}
                className="px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white text-sm hover:bg-white/10 hover:border-green-500/50 transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-green-500/20 text-left group cursor-pointer"
              >
                <span className="group-hover:text-green-500 transition-colors">Write a Python function to sort a list</span>
              </button>
              <button
                onClick={() => onSendMessage?.('What are the best practices for REST APIs?')}
                className="px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white text-sm hover:bg-white/10 hover:border-green-500/50 transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-green-500/20 text-left group cursor-pointer"
              >
                <span className="group-hover:text-green-500 transition-colors">What are the best practices for REST APIs?</span>
              </button>
              <button
                onClick={() => onSendMessage?.('Help me debug this code snippet')}
                className="px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white text-sm hover:bg-white/10 hover:border-green-500/50 transition-all hover:-translate-y-0.5 hover:shadow-lg hover:shadow-green-500/20 text-left group cursor-pointer"
              >
                <span className="group-hover:text-green-500 transition-colors">Help me debug this code snippet</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-8 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent hover:scrollbar-thumb-white/20" ref={messagesContainerRef}>
      <div className="max-w-4xl mx-auto">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            onEdit={onEditMessage}
            onDelete={onDeleteMessage}
            onRegenerate={onRegenerateResponse}
            enableReasoning={enableReasoning}
          />
        ))}
        {isLoading && (
          <div className="mb-6">
            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-green-500 to-green-700 flex items-center justify-center text-white">
                  <Loader2 size={20} className="animate-spin" />
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-semibold text-sm text-white">Assistant</span>
                </div>
                <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4">
                  <div className="flex gap-2">
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatMessages;
