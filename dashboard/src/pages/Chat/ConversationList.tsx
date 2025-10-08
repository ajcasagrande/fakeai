import React from 'react';
import { MessageSquare, Trash2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { Conversation } from './types';

interface ConversationListProps {
  conversations: Conversation[];
  currentConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
  onDeleteConversation: (conversationId: string) => void;
}

const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  currentConversationId,
  onSelectConversation,
  onDeleteConversation,
}) => {
  const sortedConversations = [...conversations].sort(
    (a, b) => b.updatedAt - a.updatedAt
  );

  const handleDelete = (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      onDeleteConversation(conversationId);
    }
  };

  if (conversations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 text-gray-500 text-center">
        <MessageSquare size={32} className="opacity-30 mb-2" />
        <p className="text-sm">No conversations yet</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {sortedConversations.map((conversation) => {
        const isActive = conversation.id === currentConversationId;
        const lastMessage = conversation.messages[conversation.messages.length - 1];
        const preview = lastMessage
          ? lastMessage.content.slice(0, 60) + (lastMessage.content.length > 60 ? '...' : '')
          : 'New conversation';

        return (
          <div
            key={conversation.id}
            className={`flex items-start gap-3 p-3 bg-white/5 backdrop-blur-sm border rounded-lg cursor-pointer transition-all relative group ${
              isActive
                ? 'border-green-500 bg-green-500/10'
                : 'border-white/10 hover:bg-white/10 hover:border-white/20'
            }`}
            onClick={() => onSelectConversation(conversation.id)}
          >
            <div className={`flex-shrink-0 w-8 h-8 rounded-md flex items-center justify-center ${
              isActive ? 'bg-green-500 text-black' : 'bg-white/10 text-green-500'
            }`}>
              <MessageSquare size={18} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-sm text-white mb-1 truncate">{conversation.title}</div>
              <div className="text-xs text-gray-400 mb-1 truncate">{preview}</div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span className="px-2 py-0.5 bg-white/10 rounded">{conversation.model}</span>
                <span>{formatDistanceToNow(conversation.updatedAt, { addSuffix: true })}</span>
              </div>
            </div>
            <button
              className="flex-shrink-0 p-1 text-gray-500 hover:text-white hover:bg-red-500/20 rounded transition-all opacity-0 group-hover:opacity-100"
              onClick={(e) => handleDelete(e, conversation.id)}
              title="Delete conversation"
            >
              <Trash2 size={16} />
            </button>
          </div>
        );
      })}
    </div>
  );
};

export default ConversationList;
