# Chat Interface

A beautiful ChatGPT-style chat interface for the FakeAI dashboard.

## Features

### User Interface
- **Clean ChatGPT-style Design**: Modern, professional interface similar to OpenAI ChatGPT
- **Sidebar Navigation**: Conversation history with search and organization
- **Message Display**: User messages on right (blue), assistant messages on left (green)
- **Avatar Icons**: Distinct icons for user and AI assistant
- **Timestamps**: Shows time for each message
- **NVIDIA Theme**: Dark theme with NVIDIA green accents (#76b900)

### Markdown & Code Support
- **Full Markdown Rendering**: Supports headers, lists, links, tables, blockquotes
- **Syntax Highlighting**: Code blocks with language-specific highlighting
- **Copy Button**: Easy code copying with visual feedback
- **Math Support**: LaTeX math rendering with KaTeX
- **GFM Support**: GitHub Flavored Markdown (tables, strikethrough, task lists)

### Chat Features
- **New Chat**: Create new conversations
- **Model Selection**: Choose from GPT-4, GPT-3.5, Claude models
- **Temperature Control**: Adjust randomness (0-2)
- **Max Tokens**: Control response length
- **System Prompt**: Customize assistant behavior
- **Streaming Responses**: Typewriter effect for responses
- **Stop Generation**: Cancel ongoing responses
- **Edit Messages**: Modify and resend messages
- **Delete Messages**: Remove individual messages
- **Regenerate**: Re-generate assistant responses
- **Clear Conversation**: Reset current chat

### Data Management
- **LocalStorage**: Conversations persist across sessions
- **Export Conversation**: Download as JSON or Markdown
- **Token Counter**: Track token usage
- **Cost Estimator**: Estimate API costs

### API Integration
- **OpenAI Compatible**: Works with `/v1/chat/completions` endpoint
- **Streaming Support**: Server-Sent Events (SSE)
- **Error Handling**: Graceful error display
- **Retry Logic**: Handle failed requests

## File Structure

```
Chat/
├── Chat.tsx              # Main chat page with state management
├── ChatSidebar.tsx       # Left sidebar with conversations
├── ChatMessages.tsx      # Message list container
├── ChatMessage.tsx       # Individual message bubble
├── ChatInput.tsx         # Message input with send button
├── ChatSettings.tsx      # Settings panel (model, temperature, etc.)
├── ConversationList.tsx  # List of past conversations
├── MarkdownRenderer.tsx  # Markdown renderer with code highlighting
├── api.ts                # API client for chat completions
├── types.ts              # TypeScript interfaces
├── styles.css            # NVIDIA-themed styles
├── index.ts              # Export barrel
└── README.md             # This file
```

## Component Overview

### Chat.tsx
Main component that orchestrates the entire chat interface. Manages:
- Conversation state
- Message sending/receiving
- LocalStorage persistence
- Settings management
- Token usage tracking

### ChatSidebar.tsx
Left sidebar containing:
- New chat button
- Conversation list
- NVIDIA branding
- Mobile toggle

### ChatMessages.tsx
Displays the message list with:
- Empty state with example prompts
- Auto-scroll to latest message
- Loading indicators
- Message list rendering

### ChatMessage.tsx
Individual message bubble with:
- User/assistant avatar
- Message content with markdown
- Timestamp
- Action buttons (edit, delete, regenerate)
- Error states

### ChatInput.tsx
Message input area with:
- Auto-expanding textarea
- Send button
- Stop generation button
- Keyboard shortcuts (Enter to send, Shift+Enter for newline)

### ChatSettings.tsx
Settings panel with:
- Model selector
- Temperature slider
- Max tokens input
- System prompt textarea
- Token usage stats
- Cost estimator
- Export/clear actions

### ConversationList.tsx
List of conversations with:
- Conversation title
- Last message preview
- Model badge
- Timestamp
- Delete button

### MarkdownRenderer.tsx
Renders markdown content with:
- Syntax highlighting (Prism)
- Code block copy button
- Math rendering (KaTeX)
- GFM support
- Custom link handling

## Usage

### Basic Usage

```tsx
import Chat from './pages/Chat';

// In your router
<Route path="/chat" element={<Chat />} />
```

### Access the Chat

Navigate to `/chat` in your application.

### Keyboard Shortcuts

- `Enter`: Send message
- `Shift + Enter`: New line in input
- `Escape`: Close settings panel

## Styling

The interface uses a dark NVIDIA theme with:
- Primary color: `#76b900` (NVIDIA green)
- Background: `#0a0a0a` (Deep black)
- Surfaces: `#111`, `#1a1a1a`, `#2a2a2a`
- Text: `#e5e5e5` (Light gray)

All styles are in `styles.css` and follow a consistent design system.

## API Integration

The chat interface expects a backend API at `/v1/chat/completions` that follows the OpenAI Chat Completions API format.

### Request Format

```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    { "role": "system", "content": "You are a helpful assistant." },
    { "role": "user", "content": "Hello!" }
  ],
  "temperature": 0.7,
  "max_tokens": 2048,
  "stream": true
}
```

### Streaming Response Format

```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"gpt-3.5-turbo","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1234567890,"model":"gpt-3.5-turbo","choices":[{"index":0,"delta":{"content":" there"},"finish_reason":null}]}

data: [DONE]
```

## Responsive Design

The interface is fully responsive:
- **Desktop**: Full sidebar + chat area
- **Tablet**: Collapsible sidebar
- **Mobile**: Overlay sidebar, optimized input

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Dependencies

- `react` - UI framework
- `react-markdown` - Markdown rendering
- `react-syntax-highlighter` - Code syntax highlighting
- `remark-gfm` - GitHub Flavored Markdown
- `remark-math` - Math support
- `rehype-katex` - KaTeX rendering
- `date-fns` - Date formatting
- `lucide-react` - Icons
- `axios` - HTTP client

## Future Enhancements

- [ ] Message search
- [ ] Conversation folders
- [ ] Voice input
- [ ] Image attachments
- [ ] Code execution
- [ ] Export to PDF
- [ ] Conversation sharing
- [ ] Multi-language support
- [ ] Custom themes
- [ ] Keyboard shortcuts panel

## License

Part of the FakeAI Dashboard project.
