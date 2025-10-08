# FakeAI Dashboard Setup Guide

This guide explains how to set up and run the FakeAI dashboard frontend, and how to configure it to connect to your backend server.

## Quick Start

### Production Mode (Recommended)
The dashboard is built and served by FastAPI itself - no configuration needed!

```bash
# 1. Build the dashboard
cd dashboard
npm install
npm run build

# 2. Start the FakeAI server (on any port)
cd ..
python -m fakeai.cli server --port 8000

# 3. Open browser
# Dashboard is automatically available at http://localhost:8000/
```

The built dashboard automatically uses the **same host and port** as the FastAPI server, so it works with any port!

---

## Development Mode
For live development with hot reload:

### Step 1: Start the Backend Server

```bash
# Start FakeAI server (note the port!)
python -m fakeai.cli server --port 8000
```

### Step 2: Configure the Frontend

Edit `dashboard/.env` to match your backend port:

```bash
# If backend is on port 8000 (default):
VITE_BACKEND_URL=http://localhost:8000

# If backend is on custom port 9002:
VITE_BACKEND_URL=http://localhost:9002

# If backend is on remote server:
VITE_BACKEND_URL=http://192.168.1.100:8000
```

### Step 3: Start the Dev Server

```bash
cd dashboard
npm run dev
```

The Vite dev server will:
- Run on `http://localhost:5173` (hot reload enabled)
- Proxy all API requests to your backend URL
- Display the backend URL in the console

```
[Vite] Mode: development
[Vite] Backend URL: http://localhost:8000
[Vite] Dev server will proxy API requests to: http://localhost:8000
```

---

## How It Works

### Production Mode (Built Dashboard)
```
User Browser → http://localhost:8000/
              ↓
          FastAPI Server (port 8000)
              ↓
        Serves index.html from /static/app/
              ↓
        Frontend makes API calls to /v1, /metrics, /dcgm
              ↓
        Same server handles API requests (no CORS issues!)
```

The built dashboard uses **relative URLs** and `window.location.host`, so it automatically adapts to whatever port FastAPI is running on.

### Development Mode (Vite Dev Server)
```
User Browser → http://localhost:5173 (Vite dev server)
              ↓
        Vite proxy intercepts /v1, /metrics, /dcgm, etc.
              ↓
        Forwards to: http://localhost:8000 (backend from .env)
              ↓
        Backend processes API requests
```

The Vite dev server proxies API requests to your backend based on `VITE_BACKEND_URL` in `.env`.

---

## Configuration Files

### `dashboard/.env`
Your local development configuration (not committed to git):

```bash
VITE_BACKEND_URL=http://localhost:8000
VITE_API_KEY=
NODE_ENV=development
```

### `dashboard/.env.example`
Template with all available options (committed to git):

```bash
VITE_BACKEND_URL=http://localhost:8000
VITE_API_KEY=
VITE_POLLING_INTERVAL=5000
VITE_ENABLE_ANALYTICS=false
```

### `dashboard/vite.config.ts`
Vite configuration that reads `VITE_BACKEND_URL` and sets up proxy:

```typescript
const backendUrl = env.VITE_BACKEND_URL || 'http://localhost:8000';

server: {
  proxy: {
    '/v1': { target: backendUrl, ws: true },
    '/metrics': { target: backendUrl, ws: true },
    '/dcgm': { target: backendUrl, ws: true },
    // ... all API routes
  }
}
```

---

## Common Scenarios

### Scenario 1: Default Setup (Port 8000)
**Production:**
```bash
python -m fakeai.cli server
# Dashboard at http://localhost:8000/
```

**Development:**
```bash
# .env: VITE_BACKEND_URL=http://localhost:8000
cd dashboard && npm run dev
# Dashboard at http://localhost:5173/
```

### Scenario 2: Custom Port (Port 9000)
**Production:**
```bash
python -m fakeai.cli server --port 9000
# Dashboard at http://localhost:9000/
```

**Development:**
```bash
# .env: VITE_BACKEND_URL=http://localhost:9000
cd dashboard && npm run dev
# Dashboard at http://localhost:5173/
```

### Scenario 3: Remote Backend
**Production:**
```bash
# Backend running on server: http://192.168.1.100:8000
# Access dashboard directly: http://192.168.1.100:8000/
```

**Development:**
```bash
# .env: VITE_BACKEND_URL=http://192.168.1.100:8000
cd dashboard && npm run dev
# Dashboard at http://localhost:5173/ (connects to remote backend)
```

### Scenario 4: Multiple Backends
Use different `.env` files or environment variables:

```bash
# Development with local backend
VITE_BACKEND_URL=http://localhost:8000 npm run dev

# Development with staging backend
VITE_BACKEND_URL=https://staging.example.com npm run dev

# Development with production backend (read-only testing)
VITE_BACKEND_URL=https://api.example.com npm run dev
```

---

## Troubleshooting

### Issue: "Failed to fetch" in dev mode

**Symptom:** Dashboard shows connection errors

**Solution:** Check that `VITE_BACKEND_URL` matches your backend server:

```bash
# Check backend server is running
curl http://localhost:8000/health

# Update .env to match backend port
echo "VITE_BACKEND_URL=http://localhost:8000" > dashboard/.env

# Restart dev server
cd dashboard && npm run dev
```

### Issue: WebSocket connection fails

**Symptom:** Real-time metrics don't update

**Solution:**
1. Ensure backend is running: `python -m fakeai.cli server`
2. Check WebSocket endpoint: `ws://localhost:8000/dcgm/stream`
3. In dev mode, Vite proxy handles WebSocket (ws: true)
4. In production, relative URLs handle WebSocket automatically

### Issue: Dashboard shows wrong port in production

**Symptom:** API calls fail after building

**Solution:** The built dashboard should use relative URLs automatically. If hardcoded URLs exist:

1. Check for hardcoded URLs: `grep -r "localhost:8000" dashboard/src/`
2. Replace with relative URLs or environment variables
3. Use `window.location.host` for dynamic URLs
4. Rebuild: `cd dashboard && npm run build`

### Issue: CORS errors

**Symptom:** "Access-Control-Allow-Origin" error

**Solutions:**
- **Production:** Should never happen (same origin)
- **Development:** Vite proxy should handle it
- **If using VITE_API_URL:** Check proxy config in `vite.config.ts`

---

## Environment Variables Reference

| Variable | Purpose | Default | Example |
|----------|---------|---------|---------|
| `VITE_BACKEND_URL` | Backend server URL (dev mode only) | `http://localhost:8000` | `http://localhost:9002` |
| `VITE_API_URL` | Fallback for compatibility | - | `http://localhost:8000` |
| `VITE_API_KEY` | API authentication key | - | `sk-1234567890` |
| `VITE_POLLING_INTERVAL` | Metrics refresh interval (ms) | `5000` | `10000` |
| `NODE_ENV` | Node environment | `development` | `production` |

---

## Build Scripts

### Build for Production
```bash
cd dashboard
npm run build
# Output: dashboard/dist/ (copied to fakeai/static/app/)
```

### Build with Python Script
```bash
python -m fakeai.dashboard.build
# Automatically installs deps, builds, and copies
```

### Build with Type Checking
```bash
cd dashboard
npm run build:check
# Runs TypeScript compiler before building
```

### Preview Production Build
```bash
cd dashboard
npm run build
npm run preview
# Preview at http://localhost:4173
```

---

## Summary

✅ **Production:** No configuration needed - dashboard uses same host/port as FastAPI
✅ **Development:** Set `VITE_BACKEND_URL` in `.env` to match backend port
✅ **WebSockets:** Automatically work in both modes (ws: true in proxy)
✅ **Dynamic Ports:** Frontend adapts to any backend port automatically
✅ **No CORS Issues:** Production uses same origin, dev uses proxy

For more help, see:
- Main README: `/README.md`
- Dashboard build script: `/fakeai/dashboard/build.py`
- Vite config: `/dashboard/vite.config.ts`
