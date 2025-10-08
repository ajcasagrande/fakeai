import React from 'react';
import { Plus, Menu, X } from 'lucide-react';
import ConversationList from './ConversationList';
import type { Conversation } from './types';

interface ChatSidebarProps {
  conversations: Conversation[];
  currentConversationId: string | null;
  onNewChat: () => void;
  onSelectConversation: (conversationId: string) => void;
  onDeleteConversation: (conversationId: string) => void;
  isOpen: boolean;
  onToggle: () => void;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({
  conversations,
  currentConversationId,
  onNewChat,
  onSelectConversation,
  onDeleteConversation,
  isOpen,
  onToggle,
}) => {
  return (
    <>
      <button
        className="fixed top-4 left-4 z-[1000] bg-white/5 border border-white/10 text-white p-2 rounded-lg hover:bg-white/10 hover:border-green-500 transition-all flex items-center justify-center md:hidden"
        onClick={onToggle}
        title="Toggle sidebar"
      >
        {isOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {isOpen && <div className="fixed inset-0 bg-black/50 z-[900] md:hidden" onClick={onToggle} />}

      <aside className={`w-72 bg-[#111] border-r border-white/10 flex flex-col transition-transform duration-300 z-[950] ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'} fixed md:relative h-full`}>
        <div className="px-4 pt-6 pb-4 border-b border-white/10">
          <h1 className="text-2xl font-bold text-green-500 mb-4">Chat</h1>
          <button
            onClick={onNewChat}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-500 hover:bg-green-600 text-black font-semibold rounded-lg transition-all hover:shadow-lg hover:shadow-green-500/30 hover:-translate-y-0.5"
            title="New chat"
          >
            <Plus size={20} />
            <span>New Chat</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent hover:scrollbar-thumb-white/20">
          <ConversationList
            conversations={conversations}
            currentConversationId={currentConversationId}
            onSelectConversation={onSelectConversation}
            onDeleteConversation={onDeleteConversation}
          />
        </div>

        <div className="p-4 border-t border-white/10">
          <div className="flex items-center gap-3 p-2">
            <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-green-700 rounded-lg flex items-center justify-center text-white flex-shrink-0">
              <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                <path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.18L19.82 8 12 11.82 4.18 8 12 4.18zM4 9.5l7 3.5v7l-7-3.5v-7zm9 11v-7l7-3.5v7l-7 3.5z"/>
              </svg>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="font-bold text-sm text-green-500">FakeAI</span>
              <span className="text-xs text-gray-500">Chat Interface</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default ChatSidebar;
