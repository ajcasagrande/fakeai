import React, { useState, useRef, useEffect } from 'react';
import { Send, Square } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onStopGeneration?: () => void;
  disabled?: boolean;
  isGenerating?: boolean;
  placeholder?: string;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  onStopGeneration,
  disabled = false,
  isGenerating = false,
  placeholder = 'Send a message...',
}) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled && !isGenerating) {
      onSendMessage(message.trim());
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleStop = () => {
    if (onStopGeneration) {
      onStopGeneration();
    }
  };

  return (
    <div className="border-t border-white/10 bg-[#111] px-8 py-4">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
        <div className="flex items-end gap-3 px-4 py-3 bg-white/5 border-2 border-white/10 rounded-xl transition-all focus-within:border-green-500">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className="flex-1 bg-transparent border-none text-white text-base resize-none outline-none max-h-48 overflow-y-auto placeholder:text-gray-500 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent"
            rows={1}
          />
          {isGenerating ? (
            <button
              type="button"
              onClick={handleStop}
              className="flex-shrink-0 w-10 h-10 bg-red-500 hover:bg-red-600 border-none text-white rounded-lg cursor-pointer flex items-center justify-center transition-all"
              title="Stop generation"
            >
              <Square size={20} fill="currentColor" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!message.trim() || disabled}
              className="flex-shrink-0 w-10 h-10 bg-green-500 hover:bg-green-600 border-none text-white rounded-lg cursor-pointer flex items-center justify-center transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-600"
              title="Send message"
            >
              <Send size={20} />
            </button>
          )}
        </div>
      </form>
      <div className="text-center py-2">
        <span className="text-xs text-gray-500">
          Press <kbd className="inline-block px-1.5 py-0.5 bg-white/10 border border-white/20 rounded text-xs mx-0.5">Enter</kbd> to send, <kbd className="inline-block px-1.5 py-0.5 bg-white/10 border border-white/20 rounded text-xs mx-0.5">Shift + Enter</kbd> for new line
        </span>
      </div>
    </div>
  );
};

export default ChatInput;
