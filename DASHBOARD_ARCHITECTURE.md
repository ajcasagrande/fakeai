# FakeAI Dashboard Architecture

## Visual Overview

### Production Mode (Built Dashboard)

```
┌─────────────────────────────────────────────────────────────┐
│  User's Browser                                             │
│                                                             │
│  URL: http://localhost:8000/                               │
│  or   http://localhost:9000/                               │
│  or   http://localhost:ANY_PORT/                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP Request
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Server (fakeai.app)                               │
│  Port: Whatever you specify (--port 8000)                  │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │  Static File Handler                          │          │
│  │  Route: /app/*                                │          │
│  │  Serves: fakeai/static/app/                  │          │
│  │  Returns: index.html, assets/*.js, etc.      │          │
│  └──────────────────────────────────────────────┘          │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │  API Endpoints                                │          │
│  │  /v1/chat/completions                        │          │
│  │  /metrics, /dcgm/*, /dynamo/*, etc.          │          │
│  │  /dcgm/stream (WebSocket)                    │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                     ▲
                     │ API Calls (relative URLs)
                     │ - fetch('/dcgm/metrics/json')
                     │ - ws://host/dcgm/stream
                     │
┌────────────────────┴────────────────────────────────────────┐
│  React App (running in browser)                            │
│                                                             │
│  window.location.host = "localhost:8000"                   │
│  All URLs are relative → same host:port                    │
│                                                             │
│  Example API call:                                          │
│    fetch('/dcgm/metrics/json')                             │
│    → http://localhost:8000/dcgm/metrics/json              │
│                                                             │
│  Example WebSocket:                                         │
│    ws://${window.location.host}/dcgm/stream               │
│    → ws://localhost:8000/dcgm/stream                      │
└─────────────────────────────────────────────────────────────┘

KEY INSIGHT: Dashboard uses window.location.host, so it ALWAYS
             connects to the same port FastAPI is running on!
```

---

### Development Mode (Vite Dev Server + Proxy)

```
┌─────────────────────────────────────────────────────────────┐
│  User's Browser                                             │
│                                                             │
│  URL: http://localhost:5173/                               │
│       (Vite dev server - fixed port)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP Request
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Vite Dev Server (Port 5173)                               │
│                                                             │
│  Reads: dashboard/.env                                      │
│  Config: VITE_BACKEND_URL=http://localhost:8000           │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │  React Source Files (Hot Reload)             │          │
│  │  - Serves .tsx/.jsx files directly           │          │
│  │  - Instant updates on save                   │          │
│  │  - Source maps for debugging                 │          │
│  └──────────────────────────────────────────────┘          │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │  Proxy Layer (vite.config.ts)                │          │
│  │                                               │          │
│  │  Rule: /v1/*                                  │───┐      │
│  │  Rule: /metrics/*                             │   │      │
│  │  Rule: /dcgm/*                                │   │      │
│  │  Rule: /dynamo/*                              │   │      │
│  │  Rule: /kv-cache/*                            │   │      │
│  │  Target: http://localhost:8000                │   │      │
│  │  WebSocket: Enabled (ws: true)                │   │      │
│  └──────────────────────────────────────────────┘   │      │
└──────────────────────────────────────────────────────┼──────┘
                                                       │
                     ┌─────────────────────────────────┘
                     │ Proxied requests
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Server (fakeai.app)                               │
│  Port: 8000 (or whatever you configured)                   │
│                                                             │
│  ┌──────────────────────────────────────────────┐          │
│  │  API Endpoints                                │          │
│  │  /v1/chat/completions                        │          │
│  │  /metrics, /dcgm/*, /dynamo/*, etc.          │          │
│  │  /dcgm/stream (WebSocket)                    │          │
│  └──────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘

KEY INSIGHT: Vite dev server proxies API calls to backend URL
             from .env, allowing frontend and backend on different ports.
```

---

## Configuration Flow

### Production Build Process

```
1. Developer runs: npm run build
   ↓
2. Vite compiles React app
   - TypeScript → JavaScript
   - SCSS/CSS → Optimized CSS
   - Tree-shaking, minification
   - Code splitting
   ↓
3. Output to: dashboard/dist/
   - index.html
   - assets/*.js
   - assets/*.css
   ↓
4. Build script copies to: fakeai/static/app/
   (Happens automatically with Python build script)
   ↓
5. FastAPI serves from: /app/*
   - GET /app/ → serves index.html
   - GET /app/assets/*.js → serves JS bundles
   ↓
6. User accesses: http://localhost:PORT/
   - FastAPI redirects to /app/
   - Browser loads index.html
   - React app uses relative URLs
   - Works with ANY port!
```

### Development Configuration Flow

```
1. Developer edits: dashboard/.env
   VITE_BACKEND_URL=http://localhost:8000
   ↓
2. Developer runs: npm run dev
   ↓
3. Vite reads .env file
   - Loads VITE_BACKEND_URL
   - Configures proxy rules
   - Prints to console
   ↓
4. Dev server starts on port 5173
   - Hot module replacement enabled
   - Source maps enabled
   - Proxy configured to backend URL
   ↓
5. User accesses: http://localhost:5173/
   - Vite serves React source files
   - API calls → proxied to backend
   - WebSocket → proxied to backend
   - Changes auto-reload
```

---

## Port Configuration Examples

### Example 1: Default Setup

```bash
# Production
$ npm run build
$ python -m fakeai.cli server
# Backend: http://localhost:8000
# Dashboard: http://localhost:8000/

# Development
$ echo "VITE_BACKEND_URL=http://localhost:8000" > dashboard/.env
$ npm run dev  # Terminal 1
$ python -m fakeai.cli server  # Terminal 2
# Backend: http://localhost:8000
# Dashboard: http://localhost:5173/ (proxies to :8000)
```

### Example 2: Custom Backend Port

```bash
# Production
$ npm run build
$ python -m fakeai.cli server --port 9000
# Backend: http://localhost:9000
# Dashboard: http://localhost:9000/  ✅ Auto-adapts!

# Development
$ echo "VITE_BACKEND_URL=http://localhost:9000" > dashboard/.env
$ npm run dev  # Terminal 1
$ python -m fakeai.cli server --port 9000  # Terminal 2
# Backend: http://localhost:9000
# Dashboard: http://localhost:5173/ (proxies to :9000)
```

### Example 3: Remote Backend

```bash
# Production
# Backend running at: http://192.168.1.100:8000
# Access dashboard at: http://192.168.1.100:8000/  ✅ Works!

# Development
$ echo "VITE_BACKEND_URL=http://192.168.1.100:8000" > dashboard/.env
$ npm run dev
# Dashboard: http://localhost:5173/
# Proxies to: http://192.168.1.100:8000
```

---

## API Call Patterns

### Production (Built App)

```typescript
// Example 1: HTTP API call
async function fetchDCGMMetrics() {
  const response = await fetch('/dcgm/metrics/json');
  // Browser resolves to: http://localhost:8000/dcgm/metrics/json
  return response.json();
}

// Example 2: WebSocket connection
const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//` +
              `${window.location.host}/dcgm/stream`;
const ws = new WebSocket(wsUrl);
// Resolves to: ws://localhost:8000/dcgm/stream
```

### Development (Vite Proxy)

```typescript
// Same code as production!
async function fetchDCGMMetrics() {
  const response = await fetch('/dcgm/metrics/json');
  // Browser requests: http://localhost:5173/dcgm/metrics/json
  // Vite proxy forwards to: http://localhost:8000/dcgm/metrics/json
  return response.json();
}

// WebSocket also proxied
const ws = new WebSocket('ws://localhost:5173/dcgm/stream');
// Vite proxy forwards to: ws://localhost:8000/dcgm/stream
```

---

## File Structure

```
fakeai/
├── dashboard/                          # Frontend source
│   ├── src/                           # React components
│   │   ├── pages/
│   │   │   ├── DCGM/                 # DCGM dashboard
│   │   │   │   ├── DCGMDashboard.tsx
│   │   │   │   ├── api.ts            # API_BASE_URL from .env
│   │   │   │   └── components/
│   │   │   ├── AIDynamo/             # AI-Dynamo dashboard
│   │   │   └── Home.tsx              # Home page with cards
│   │   └── services/
│   │       ├── useGenericWebSocket.ts # WebSocket hook
│   │       └── adminService.ts       # Admin API client
│   │
│   ├── dist/                          # Built files (after npm run build)
│   │   ├── index.html
│   │   └── assets/
│   │       ├── index-*.js
│   │       └── index-*.css
│   │
│   ├── .env                           # Your local config
│   │   └── VITE_BACKEND_URL=http://localhost:8000
│   │
│   ├── .env.example                   # Template
│   ├── vite.config.ts                 # Proxy configuration
│   ├── package.json
│   ├── DASHBOARD_SETUP.md             # Detailed guide
│   └── configure-backend.sh           # Setup helper
│
├── fakeai/
│   ├── static/                        # Static files served by FastAPI
│   │   └── app/                       # Built dashboard (copy of dist/)
│   │       ├── index.html
│   │       └── assets/
│   │
│   ├── app.py                         # FastAPI application
│   │   ├── GET  /app/                → Serves index.html
│   │   ├── GET  /v1/*                → API endpoints
│   │   ├── GET  /dcgm/metrics/json   → DCGM metrics
│   │   └── WS   /dcgm/stream         → DCGM WebSocket
│   │
│   ├── config/__init__.py             # AppConfig
│   │   └── enable_security property  ← Bug fix added
│   │
│   └── cli.py                         # CLI commands
│       └── server command            ← Fixed AttributeError
│
├── DASHBOARD_QUICK_START.md          # Quick reference
└── DASHBOARD_PORT_CONFIGURATION_SUMMARY.md  # Complete summary
```

---

## Technical Implementation Details

### 1. Environment Variable Priority

```
Vite reads backend URL in this order:
1. VITE_BACKEND_URL         (new, recommended)
2. VITE_API_URL             (fallback for compatibility)
3. http://localhost:8000    (default)
```

### 2. Proxy Configuration (vite.config.ts)

```typescript
const backendUrl = env.VITE_BACKEND_URL ||
                   env.VITE_API_URL ||
                   'http://localhost:8000';

proxy: {
  '/v1': {
    target: backendUrl,
    changeOrigin: true,  // Changes Host header
    ws: true             // Enables WebSocket proxying
  },
  // ... all routes
}
```

### 3. FastAPI Static File Serving

```python
# fakeai/app.py
from fastapi.staticfiles import StaticFiles

app.mount("/app", StaticFiles(
    directory="fakeai/static/app",
    html=True  # Serves index.html for all routes
), name="dashboard")
```

### 4. React Router + Base URL

```typescript
// vite.config.ts
base: mode === 'production' ? '/app/' : '/'

// React Router uses this base automatically
// Production: http://localhost:8000/app/dcgm
// Development: http://localhost:5173/dcgm
```

---

## Summary

### Production Mode
✅ **Zero config:** Built app adapts to any port
✅ **Same origin:** No CORS issues
✅ **Fast:** Optimized bundles, code splitting
✅ **CDN-ready:** Static files can be cached

### Development Mode
✅ **Hot reload:** Instant feedback on changes
✅ **Source maps:** Easy debugging
✅ **Proxy:** Seamless API calls to backend
✅ **Flexible:** Change backend port anytime

### Key Design Principles
1. **Relative URLs in production** → Port-agnostic
2. **window.location.host** → Always correct for WebSockets
3. **Vite proxy in dev** → Separate frontend/backend
4. **Environment variables** → Easy configuration
5. **Backward compatibility** → VITE_API_URL still works
