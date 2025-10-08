import React from 'react';
import { motion } from 'framer-motion';
import { User, Bot, Edit2, Trash2, RotateCw, Brain } from 'lucide-react';
import { format } from 'date-fns';
import MarkdownRenderer from './MarkdownRenderer';
import type { Message } from './types';

interface ChatMessageProps {
  message: Message;
  onEdit?: (messageId: string) => void;
  onDelete?: (messageId: string) => void;
  onRegenerate?: (messageId: string) => void;
  showActions?: boolean;
  enableReasoning?: boolean;
}

const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onEdit,
  onDelete,
  onRegenerate,
  showActions = true,
  enableReasoning = true,
}) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="mb-6 p-4 bg-white/5 border border-white/10 rounded-xl"
      >
        <div className="text-xs font-semibold uppercase text-green-500 mb-2 tracking-wide">System Prompt</div>
        <div className="text-sm text-gray-400 leading-relaxed">{message.content}</div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="mb-6 group"
    >
      <div className="flex gap-4">
        <div className="flex-shrink-0">
          {isUser ? (
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-white">
              <User size={20} />
            </div>
          ) : (
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-green-500 to-green-700 flex items-center justify-center text-white">
              <Bot size={20} />
            </div>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-semibold text-sm text-white">{isUser ? 'You' : 'Assistant'}</span>
            <span className="text-xs text-gray-500">
              {format(message.timestamp, 'HH:mm')}
            </span>
          </div>
          <div className={`bg-white/5 backdrop-blur-sm border rounded-xl p-4 text-white leading-relaxed ${
            isUser ? 'border-white/10' : 'border-white/10'
          } ${message.isStreaming ? 'border-green-500/50' : ''}`}>
            {message.error ? (
              <div className="flex items-center gap-2 text-red-400 bg-red-500/10 border border-red-500/20 p-3 rounded-lg">
                <span className="text-lg">⚠️</span>
                <span className="text-sm">{message.error}</span>
              </div>
            ) : (
              <>
                {/* Show reasoning content if available and enabled */}
                {!isUser && message.reasoning_content && enableReasoning && (
                  <div className="mb-4 pb-4 border-b border-purple-500/20">
                    <div className="flex items-center gap-2 mb-2">
                      <Brain size={14} className="text-purple-400" />
                      <span className="text-xs font-semibold text-purple-400 uppercase tracking-wide">Thinking</span>
                    </div>
                    <div className="text-gray-500 italic border-l-2 border-purple-500/30 pl-3 text-sm leading-relaxed">
                      <MarkdownRenderer content={message.reasoning_content} />
                    </div>
                  </div>
                )}
                {isUser ? (
                  <div className="whitespace-pre-wrap break-words">{message.content}</div>
                ) : (
                  <MarkdownRenderer content={message.content} />
                )}
                {message.isStreaming && (
                  <span className="inline-block w-0.5 h-5 bg-green-500 ml-0.5 animate-pulse align-text-bottom">▊</span>
                )}
              </>
            )}
          </div>
          {showActions && !message.isStreaming && !message.error && (
            <div className="flex gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
              {isUser && onEdit && (
                <button
                  onClick={() => onEdit(message.id)}
                  className="px-3 py-1.5 text-xs font-medium text-gray-400 hover:text-white bg-white/5 hover:bg-white/10 rounded-lg transition-all flex items-center gap-1.5"
                  title="Edit message"
                >
                  <Edit2 size={14} />
                  <span>Edit</span>
                </button>
              )}
              {!isUser && onRegenerate && (
                <button
                  onClick={() => onRegenerate(message.id)}
                  className="px-3 py-1.5 text-xs font-medium text-gray-400 hover:text-white bg-white/5 hover:bg-green-500 rounded-lg transition-all flex items-center gap-1.5"
                  title="Regenerate response"
                >
                  <RotateCw size={14} />
                  <span>Regenerate</span>
                </button>
              )}
              {onDelete && (
                <button
                  onClick={() => onDelete(message.id)}
                  className="px-3 py-1.5 text-xs font-medium text-gray-400 hover:text-white bg-white/5 hover:bg-red-500 rounded-lg transition-all flex items-center gap-1.5"
                  title="Delete message"
                >
                  <Trash2 size={14} />
                  <span>Delete</span>
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default ChatMessage;
