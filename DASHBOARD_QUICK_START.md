# FakeAI Dashboard - Quick Start Guide

## TL;DR

### Production (Recommended) ✅
```bash
# Build and run (works with any port!)
cd dashboard && npm install && npm run build && cd ..
python -m fakeai.cli server --port 8000
# Open: http://localhost:8000/
```

### Development (Hot Reload) 🔥
```bash
# Terminal 1: Backend
python -m fakeai.cli server --port 8000

# Terminal 2: Frontend
cd dashboard
./configure-backend.sh  # Configure once
npm run dev
# Open: http://localhost:5173/
```

---

## How Port Configuration Works

### In Production Mode (Built)
The frontend **automatically uses the correct port** because:
1. The built dashboard is served by FastAPI itself
2. All API calls use relative URLs (e.g., `/v1/chat/completions`)
3. WebSocket connections use `window.location.host`

**Result:** Run server on ANY port, dashboard works immediately!

```bash
python -m fakeai.cli server --port 8000  # Dashboard at :8000/
python -m fakeai.cli server --port 9000  # Dashboard at :9000/
python -m fakeai.cli server --port 7777  # Dashboard at :7777/
```

### In Development Mode (Vite Dev Server)
The frontend needs to know where to proxy API requests:
1. Edit `dashboard/.env` and set `VITE_BACKEND_URL`
2. Vite proxies all API calls to that URL
3. WebSocket connections are also proxied

**Result:** Dev server on :5173, backend on any port you configure!

```bash
# Example: Backend on port 9002
echo "VITE_BACKEND_URL=http://localhost:9002" > dashboard/.env
cd dashboard && npm run dev
# Dashboard dev server: http://localhost:5173/
# API calls proxied to: http://localhost:9002/
```

---

## Step-by-Step Setup

### First Time Setup

#### 1. Install Dependencies
```bash
cd dashboard
npm install
```

#### 2. Choose Your Mode

**Option A: Production Mode** (no dev dependencies needed)
```bash
npm run build
cd ..
python -m fakeai.cli server
# Open http://localhost:8000/
```

**Option B: Development Mode** (hot reload)
```bash
# Configure backend URL (one-time)
./configure-backend.sh
# or manually edit .env:
# echo "VITE_BACKEND_URL=http://localhost:8000" > .env

# Start backend (Terminal 1)
cd ..
python -m fakeai.cli server

# Start frontend (Terminal 2)
cd dashboard
npm run dev
# Open http://localhost:5173/
```

---

## Configuration Reference

### Environment Variables (Development Only)

Create `dashboard/.env`:
```bash
# Required: Backend server URL
VITE_BACKEND_URL=http://localhost:8000

# Optional: API key
VITE_API_KEY=sk-your-key-here

# Optional: Polling intervals (milliseconds)
VITE_POLLING_INTERVAL=5000
VITE_BATCH_DETAIL_POLLING_INTERVAL=3000
```

### Vite Configuration

The `dashboard/vite.config.ts` reads `VITE_BACKEND_URL` and configures proxy:

```typescript
// Automatically configured!
proxy: {
  '/v1': { target: backendUrl, ws: true },
  '/metrics': { target: backendUrl, ws: true },
  '/dcgm': { target: backendUrl, ws: true },
  // ... all API routes
}
```

---

## Troubleshooting

### Dashboard can't connect to backend in dev mode

**Check 1:** Is backend running?
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

**Check 2:** Is `.env` configured correctly?
```bash
cat dashboard/.env
# Should show: VITE_BACKEND_URL=http://localhost:8000
```

**Check 3:** Restart dev server
```bash
cd dashboard
npm run dev
# Console should show: [Vite] Backend URL: http://localhost:8000
```

### WebSocket not connecting

**Check 1:** Verify WebSocket endpoint
```bash
# Install websocat: https://github.com/vi/websocat
websocat ws://localhost:8000/dcgm/stream
# Should connect and send data
```

**Check 2:** Check browser console
- Open DevTools → Network → WS tab
- Look for WebSocket connection status
- Should see `/dcgm/stream` with status 101 (Switching Protocols)

### "Failed to fetch" in production

**This shouldn't happen!** The dashboard uses relative URLs.

If you see this:
```bash
# Rebuild the dashboard
cd dashboard
npm run build
cd ..
python -m fakeai.cli server
```

---

## Advanced Usage

### Running on a Different Port

**Production:**
```bash
python -m fakeai.cli server --port 9000
# Dashboard automatically at http://localhost:9000/
```

**Development:**
```bash
# Update .env
echo "VITE_BACKEND_URL=http://localhost:9000" > dashboard/.env

# Restart dev server
cd dashboard
npm run dev
```

### Remote Backend

**Production:**
```bash
# Just access the remote server's URL
# If backend is at http://192.168.1.100:8000
# Dashboard is at http://192.168.1.100:8000/
```

**Development:**
```bash
# Point dev server to remote backend
echo "VITE_BACKEND_URL=http://192.168.1.100:8000" > dashboard/.env
cd dashboard
npm run dev
```

### Docker Deployment

The built dashboard is included in the Docker image:

```bash
# Build image
docker build -t fakeai:latest .

# Run on port 8080
docker run -p 8080:8000 fakeai:latest
# Dashboard at http://localhost:8080/
```

---

## File Structure

```
fakeai/
├── dashboard/                    # React frontend source
│   ├── src/                     # React components
│   │   ├── pages/DCGM/         # DCGM dashboard
│   │   ├── pages/AIDynamo/     # AI-Dynamo dashboard
│   │   └── ...
│   ├── dist/                    # Built files (after npm run build)
│   ├── .env                     # Your local config (not in git)
│   ├── .env.example             # Template
│   ├── vite.config.ts           # Vite configuration
│   ├── configure-backend.sh     # Setup helper script
│   ├── DASHBOARD_SETUP.md       # Detailed setup guide
│   └── package.json
│
├── fakeai/
│   ├── static/app/              # Built dashboard (served by FastAPI)
│   │   ├── index.html
│   │   └── assets/
│   ├── app.py                   # FastAPI application
│   └── cli.py                   # CLI commands
│
└── DASHBOARD_QUICK_START.md    # This file
```

---

## Summary

✅ **Production mode**: No configuration needed, works with any port
✅ **Development mode**: Configure once with `./configure-backend.sh`
✅ **Port flexibility**: Frontend adapts to backend port automatically
✅ **WebSocket support**: Real-time metrics work in both modes
✅ **No CORS issues**: Same origin in prod, proxy in dev

**Next:** See [dashboard/DASHBOARD_SETUP.md](dashboard/DASHBOARD_SETUP.md) for detailed docs.
