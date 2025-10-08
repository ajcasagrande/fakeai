# Chat Interface - Quick Start Guide

## Getting Started

### 1. Start the Dev Server
```bash
cd /home/anthony/projects/fakeai/dashboard
npm run dev
```

### 2. Access the Chat
Open your browser and navigate to:
```
http://localhost:5173/chat
```

## Quick Overview

### What You'll See

**Left Sidebar:**
- 💬 New Chat button (NVIDIA green)
- 📋 List of past conversations
- 🏢 NVIDIA branding at bottom

**Main Chat Area:**
- 📝 Message display area
- ⚙️ Settings button (top right)
- ✍️ Message input box (bottom)

**Settings Panel (click ⚙️):**
- 🤖 Model selector
- 🌡️ Temperature slider
- 📊 Token usage stats
- 💾 Export options

## How to Use

### Send Your First Message
1. Click "New Chat" or start typing in the input box
2. Type your message
3. Press **Enter** to send (or click the send button)
4. Watch the AI respond with streaming text

### Keyboard Shortcuts
- `Enter` - Send message
- `Shift + Enter` - New line
- `Escape` - Close settings panel

### Change Settings
1. Click the ⚙️ settings icon
2. Select a model (GPT-4, GPT-3.5, Claude, etc.)
3. Adjust temperature (0 = focused, 2 = creative)
4. Set max tokens for response length
5. Customize system prompt

### Manage Conversations
- **New Chat** - Start fresh conversation
- **Select** - Click on past conversation to continue
- **Delete** - Hover over conversation, click trash icon
- **Export** - Settings → Export as JSON or Markdown
- **Clear** - Settings → Clear Conversation

## Features to Try

### 1. Code Snippets
Try asking:
```
Write a Python function to sort a list
```
You'll see syntax-highlighted code with a copy button!

### 2. Markdown
Try:
```
Explain REST APIs with a table and examples
```
See beautiful tables, lists, and formatting!

### 3. Math Equations
Try:
```
Show me the quadratic formula in LaTeX
```
Math renders beautifully with KaTeX!

### 4. Different Models
Switch between models to compare:
- GPT-4 (powerful, expensive)
- GPT-3.5 Turbo (fast, cheap)
- Claude 3 Opus (high quality)
- Claude 3 Haiku (ultra fast)

### 5. Temperature Control
- **0.0** - Deterministic, focused responses
- **0.7** - Balanced (default)
- **2.0** - Creative, varied responses

## Example Prompts

**Code Help:**
- "Write a React component for a todo list"
- "Debug this Python code: [paste code]"
- "Explain async/await in JavaScript"

**Writing:**
- "Write a professional email about..."
- "Create a blog post outline about..."
- "Proofread this text: [paste text]"

**Analysis:**
- "Summarize this article: [paste text]"
- "Compare pros and cons of..."
- "Explain like I'm 5: [topic]"

**Creative:**
- "Generate 10 business name ideas for..."
- "Write a short story about..."
- "Come up with marketing taglines for..."

## Tips & Tricks

### Save Money
- Use GPT-3.5 for simple tasks
- Use Claude Haiku for speed
- Lower max_tokens for shorter responses
- Check token usage in settings

### Better Responses
- Be specific in your prompts
- Provide context and examples
- Use system prompt to set behavior
- Adjust temperature based on task

### Organize Conversations
- Name conversations clearly
- Export important chats
- Delete old conversations
- Use new chat for different topics

## Troubleshooting

### No Response?
- Check if backend API is running
- Verify `/v1/chat/completions` endpoint
- Check browser console for errors
- Try refreshing the page

### Slow Streaming?
- Check network connection
- Try a faster model (GPT-3.5, Claude Haiku)
- Lower max_tokens
- Check backend server load

### Conversations Not Saving?
- Check browser localStorage
- Try different browser
- Clear cache and reload
- Check browser console

### Code Not Highlighting?
- Use proper markdown code fences:
  ````
  ```python
  def hello():
      print("Hello")
  ```
  ````
- Specify language after opening fence
- Check browser console for errors

## API Integration

### Required Endpoint
The chat expects:
```
POST /v1/chat/completions
```

### Request Format
```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 2048,
  "stream": true
}
```

### Streaming Response
Server-Sent Events format:
```
data: {"choices":[{"delta":{"content":"Hello"}}]}
data: {"choices":[{"delta":{"content":" there"}}]}
data: [DONE]
```

## File Structure

```
Chat/
├── Chat.tsx              ← Main component
├── ChatSidebar.tsx       ← Left sidebar
├── ChatMessages.tsx      ← Message list
├── ChatMessage.tsx       ← Single message
├── ChatInput.tsx         ← Input box
├── ChatSettings.tsx      ← Settings panel
├── ConversationList.tsx  ← Conversation history
├── MarkdownRenderer.tsx  ← Markdown + syntax highlighting
├── api.ts                ← API client
├── types.ts              ← TypeScript types
├── styles.css            ← NVIDIA theme
└── index.ts              ← Exports
```

## Next Steps

1. **Test the interface** - Send some messages, try features
2. **Customize settings** - Set your preferred model and temperature
3. **Connect your API** - Point to your chat completions endpoint
4. **Style adjustments** - Modify `styles.css` for custom branding
5. **Add features** - Implement edit, regenerate, etc.

## Support

For issues or questions:
- Check `README.md` for detailed documentation
- Check `SUMMARY.md` for implementation details
- Review component files for inline comments
- Check browser console for errors

## Have Fun! 🚀

Enjoy your new ChatGPT-style interface powered by FakeAI and NVIDIA!
