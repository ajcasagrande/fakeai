# Quick Start Guide - Chat Completions Dashboard

Get the dashboard up and running in 5 minutes!

## Prerequisites

- Node.js 16+
- React 18+
- TypeScript 4.5+
- FakeAI server running on `http://localhost:8000`

## Installation

### Option 1: Copy into Existing React App

1. **Copy the directory**:
   ```bash
   cp -r fakeai/dashboard/src/pages/ChatCompletions your-react-app/src/pages/
   ```

2. **Install dependencies** (if not already installed):
   ```bash
   npm install react react-dom typescript
   ```

3. **Import and use**:
   ```tsx
   // In your App.tsx or routing file
   import { ChatCompletions } from './pages/ChatCompletions';

   function App() {
     return <ChatCompletions />;
   }
   ```

### Option 2: Create New React App

1. **Create React app with TypeScript**:
   ```bash
   npx create-react-app my-dashboard --template typescript
   cd my-dashboard
   ```

2. **Copy dashboard files**:
   ```bash
   mkdir -p src/pages
   cp -r /path/to/fakeai/dashboard/src/pages/ChatCompletions src/pages/
   ```

3. **Update App.tsx**:
   ```tsx
   import React from 'react';
   import { ChatCompletions } from './pages/ChatCompletions';
   import './App.css';

   function App() {
     return (
       <div className="App">
         <ChatCompletions />
       </div>
     );
   }

   export default App;
   ```

4. **Start the app**:
   ```bash
   npm start
   ```

## Configuration

### 1. Environment Variables

Create `.env` in your project root:

```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_KEY=your-api-key-here
```

### 2. API Key Setup

**Option A: Set in localStorage** (Development)
```javascript
// In browser console
localStorage.setItem('apiKey', 'your-api-key');
```

**Option B: Use environment variable** (Production)
```bash
export REACT_APP_API_KEY=your-production-key
```

### 3. CORS Configuration

Ensure your FakeAI server allows CORS. In `fakeai/app.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Verify Installation

### 1. Start FakeAI Server

```bash
cd fakeai
python -m fakeai
# Server starts on http://localhost:8000
```

### 2. Generate Some Test Data

```bash
# Open another terminal
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### 3. Open Dashboard

Navigate to `http://localhost:3000` and you should see:
- ✅ Metrics cards with data
- ✅ Model usage charts
- ✅ Token statistics
- ✅ Recent requests table

## Common Issues & Solutions

### Issue: "Failed to fetch model metrics"

**Cause**: API server not running or CORS issue

**Solution**:
1. Verify FakeAI is running: `curl http://localhost:8000/metrics/by-model`
2. Check browser console for CORS errors
3. Update CORS settings in `app.py`

### Issue: Dashboard shows no data

**Cause**: No requests have been made to the API

**Solution**:
1. Make some test requests using curl or the examples
2. Verify data exists: `curl http://localhost:8000/metrics/by-model`
3. Check browser console for errors

### Issue: Styling looks broken

**Cause**: CSS file not imported

**Solution**:
Ensure `styles.css` is imported in `ChatCompletions.tsx`:
```tsx
import './styles.css';
```

### Issue: TypeScript errors

**Cause**: Missing type definitions

**Solution**:
1. Ensure all files in `ChatCompletions/` directory are copied
2. Check `tsconfig.json` has proper settings:
   ```json
   {
     "compilerOptions": {
       "jsx": "react-jsx",
       "module": "esnext",
       "target": "es5",
       "lib": ["dom", "dom.iterable", "esnext"]
     }
   }
   ```

## Testing the Dashboard

### 1. Basic Functionality Test

```bash
# Generate test traffic
for i in {1..10}; do
  curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d "{
      \"model\": \"gpt-4\",
      \"messages\": [{\"role\": \"user\", \"content\": \"Test $i\"}]
    }"
done
```

Refresh dashboard and verify:
- Request count increases
- New requests appear in table
- Charts update

### 2. Filter Test

1. Click a model in the dropdown
2. Verify table shows only that model's requests
3. Click "Reset All" to clear filters

### 3. Modal Test

1. Click eye icon on any request row
2. Verify modal opens with request details
3. Click tabs to see request/response data
4. Click X or outside to close

### 4. Sorting Test

1. Click "Latency" column header
2. Verify requests sort by latency
3. Click again to reverse order

## Next Steps

### Customize the Dashboard

1. **Change colors**: Edit `styles.css` CSS variables
2. **Add metrics**: Create new component in `components/`
3. **Modify layout**: Update `ChatCompletions.tsx` grid
4. **Add charts**: Use Chart.js or D3.js libraries

### Production Deployment

1. **Build for production**:
   ```bash
   npm run build
   ```

2. **Serve static files**:
   ```bash
   npm install -g serve
   serve -s build -p 3000
   ```

3. **Deploy to hosting**:
   - Vercel: `vercel deploy`
   - Netlify: `netlify deploy`
   - AWS S3: `aws s3 sync build/ s3://bucket-name`

### Integration with Backend

Replace mock data in `api.ts`:

```typescript
// Before (mock)
export async function fetchChatRequests(...) {
  // Mock implementation
}

// After (real)
export async function fetchChatRequests(
  limit: number,
  offset: number,
  filters?: RequestFilters
): Promise<{ requests: ChatRequest[]; total: number }> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
    ...filters
  });

  const response = await fetch(
    `${BASE_URL}/api/chat/requests?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${getApiKey()}`,
      },
    }
  );

  return response.json();
}
```

## Resources

- **Full Documentation**: See `README.md`
- **Implementation Details**: See `SUMMARY.md`
- **FakeAI API**: Check `fakeai/app.py` for endpoint details
- **React Docs**: https://react.dev
- **TypeScript Docs**: https://typescriptlang.org

## Support

If you run into issues:

1. Check browser console for errors
2. Verify API endpoints are accessible
3. Review the README.md for detailed documentation
4. Check FakeAI server logs

## Quick Reference

### Keyboard Shortcuts

- `Tab`: Navigate between elements
- `Enter`: Activate buttons/links
- `Escape`: Close modal

### Important Files

| File | Purpose |
|------|---------|
| `ChatCompletions.tsx` | Main component |
| `api.ts` | API integration |
| `types.ts` | TypeScript types |
| `styles.css` | NVIDIA theme styles |
| `components/*.tsx` | Individual UI components |

### Default Behavior

- Auto-refresh: Every 30 seconds
- Pagination: 20 items per page
- Date range: All time
- Model filter: All models
- Chart type: Pie chart

### API Endpoints Used

1. `GET /metrics/by-model` - Model statistics
2. `GET /v1/organization/usage/completions` - Usage data

---

**🎉 That's it! You're ready to monitor your chat completions!**

For detailed information, see the comprehensive README.md file.
