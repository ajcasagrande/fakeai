# Troubleshooting Guide

Common issues and solutions for the FakeAI Dashboard.

---

## Table of Contents

- [Installation Issues](#installation-issues)
- [Development Server Issues](#development-server-issues)
- [Build Issues](#build-issues)
- [API Connection Issues](#api-connection-issues)
- [WebSocket Issues](#websocket-issues)
- [Display and Styling Issues](#display-and-styling-issues)
- [Performance Issues](#performance-issues)
- [Browser Compatibility](#browser-compatibility)
- [Deployment Issues](#deployment-issues)
- [Getting Help](#getting-help)

---

## Installation Issues

### npm install fails

**Symptoms**: Errors during `npm install`

**Solutions**:

1. **Clear npm cache**
   ```bash
   npm cache clean --force
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Check Node.js version**
   ```bash
   node --version  # Should be 18.0.0 or higher
   npm --version   # Should be 9.0.0 or higher
   ```

3. **Use correct registry**
   ```bash
   npm config set registry https://registry.npmjs.org/
   ```

4. **Install with legacy peer deps**
   ```bash
   npm install --legacy-peer-deps
   ```

### Permission errors on macOS/Linux

**Symptoms**: `EACCES` permission errors

**Solution**:
```bash
# Fix npm permissions
sudo chown -R $(whoami) ~/.npm
sudo chown -R $(whoami) /usr/local/lib/node_modules

# Or use nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

---

## Development Server Issues

### Port already in use

**Symptoms**: `Error: listen EADDRINUSE :::5173`

**Solutions**:

1. **Kill process using the port**
   ```bash
   # Find process
   lsof -i :5173

   # Kill process
   kill -9 <PID>
   ```

2. **Use different port**
   ```bash
   npm run dev -- --port 3000
   ```

### Hot reload not working

**Symptoms**: Changes not reflected in browser

**Solutions**:

1. **Clear browser cache**
   - Chrome: Ctrl+Shift+Delete (Cmd+Shift+Delete on Mac)
   - Hard refresh: Ctrl+Shift+R (Cmd+Shift+R on Mac)

2. **Restart development server**
   ```bash
   # Stop server (Ctrl+C)
   npm run dev
   ```

3. **Check file watchers limit (Linux)**
   ```bash
   # Increase limit
   echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
   sudo sysctl -p
   ```

### Module not found errors

**Symptoms**: `Cannot find module '@/components/...'`

**Solutions**:

1. **Check TypeScript configuration**
   ```json
   // tsconfig.json
   {
     "compilerOptions": {
       "baseUrl": ".",
       "paths": {
         "@/*": ["./src/*"]
       }
     }
   }
   ```

2. **Check Vite configuration**
   ```typescript
   // vite.config.ts
   export default defineConfig({
     resolve: {
       alias: {
         '@': path.resolve(__dirname, './src'),
       },
     },
   });
   ```

3. **Restart TypeScript server** (VS Code)
   - Cmd+Shift+P → "TypeScript: Restart TS Server"

---

## Build Issues

### Build fails with TypeScript errors

**Symptoms**: `TS2304: Cannot find name '...'`

**Solutions**:

1. **Fix type errors**
   ```bash
   # Check for type errors
   npm run type-check
   ```

2. **Install missing type definitions**
   ```bash
   npm install --save-dev @types/node
   npm install --save-dev @types/react
   npm install --save-dev @types/react-dom
   ```

3. **Update TypeScript**
   ```bash
   npm install --save-dev typescript@latest
   ```

### Build fails with memory errors

**Symptoms**: `JavaScript heap out of memory`

**Solution**:
```bash
# Increase Node.js memory limit
export NODE_OPTIONS=--max_old_space_size=4096
npm run build
```

### Build output missing files

**Symptoms**: `index.html` or assets missing from `dist/`

**Solutions**:

1. **Clean and rebuild**
   ```bash
   rm -rf dist node_modules
   npm install
   npm run build
   ```

2. **Check build configuration**
   ```typescript
   // vite.config.ts
   export default defineConfig({
     build: {
       outDir: 'dist',
       assetsDir: 'assets',
     },
   });
   ```

---

## API Connection Issues

### Cannot connect to FakeAI server

**Symptoms**: `Network Error` or `Failed to fetch`

**Solutions**:

1. **Check if server is running**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "ok"}
   ```

2. **Start FakeAI server**
   ```bash
   fakeai server --port 8000
   ```

3. **Check API URL in .env**
   ```bash
   # .env
   VITE_API_URL=http://localhost:8000
   ```

4. **Check CORS configuration**
   - Ensure FakeAI server allows CORS from your origin
   - Check browser console for CORS errors

### API returns 401 Unauthorized

**Symptoms**: All API calls fail with 401

**Solutions**:

1. **Check authentication token**
   ```javascript
   console.log(localStorage.getItem('auth_token'));
   ```

2. **Clear token and re-login**
   ```javascript
   localStorage.removeItem('auth_token');
   // Refresh page and login again
   ```

3. **Check API key configuration**
   ```bash
   # On FakeAI server
   export FAKEAI_REQUIRE_API_KEY=false
   fakeai server
   ```

### API requests timeout

**Symptoms**: Requests fail after 30 seconds

**Solutions**:

1. **Increase timeout**
   ```typescript
   // src/api/client.ts
   const DEFAULT_CONFIG = {
     timeout: 60000, // 60 seconds
   };
   ```

2. **Check server performance**
   ```bash
   # Monitor server logs
   fakeai server --debug
   ```

---

## WebSocket Issues

### WebSocket connection fails

**Symptoms**: `WebSocket connection failed`

**Solutions**:

1. **Check WebSocket URL**
   ```bash
   # .env
   VITE_WS_URL=ws://localhost:8000
   # Or for HTTPS:
   VITE_WS_URL=wss://yourdomain.com
   ```

2. **Check server WebSocket support**
   ```bash
   curl --include \
        --no-buffer \
        --header "Connection: Upgrade" \
        --header "Upgrade: websocket" \
        --header "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
        --header "Sec-WebSocket-Version: 13" \
        http://localhost:8000/metrics/stream
   ```

3. **Disable WebSocket temporarily**
   ```bash
   # .env
   VITE_ENABLE_WEBSOCKETS=false
   ```

### WebSocket keeps reconnecting

**Symptoms**: Constant connect/disconnect cycle

**Solutions**:

1. **Check server stability**
   ```bash
   # Monitor server logs
   fakeai server --debug
   ```

2. **Increase reconnect interval**
   ```typescript
   useWebSocket('/metrics/stream', {
     reconnectInterval: 10000, // 10 seconds
     maxReconnectAttempts: 5,
   });
   ```

---

## Display and Styling Issues

### Dashboard not loading / blank page

**Symptoms**: White screen, no content

**Solutions**:

1. **Check browser console**
   - Press F12 to open DevTools
   - Look for errors in Console tab

2. **Check if JavaScript is enabled**
   - Dashboard requires JavaScript

3. **Clear browser cache**
   ```bash
   # Chrome
   Ctrl+Shift+Delete → Clear browsing data
   ```

4. **Check base URL configuration**
   ```typescript
   // vite.config.ts
   export default defineConfig({
     base: '/', // or '/dashboard/' if deployed to subdirectory
   });
   ```

### Charts not rendering

**Symptoms**: Empty chart containers

**Solutions**:

1. **Check data is loading**
   ```javascript
   console.log('Chart data:', data);
   ```

2. **Verify Recharts installation**
   ```bash
   npm list recharts
   # Should show recharts@2.x.x
   ```

3. **Check for console errors**
   - Look for Recharts-related errors

### Styles not applied / CSS missing

**Symptoms**: Unstyled content, broken layout

**Solutions**:

1. **Check CSS files are imported**
   ```typescript
   // src/main.tsx
   import './index.css';
   ```

2. **Clear Vite cache**
   ```bash
   rm -rf node_modules/.vite
   npm run dev
   ```

3. **Check for CSS import errors**
   - Look for 404 errors in Network tab

---

## Performance Issues

### Dashboard is slow / laggy

**Symptoms**: Slow rendering, high CPU usage

**Solutions**:

1. **Disable auto-refresh**
   - Turn off auto-refresh in dashboard header

2. **Reduce data fetching frequency**
   ```typescript
   // Increase interval
   useEffect(() => {
     const interval = setInterval(fetchData, 60000); // 60 seconds
     return () => clearInterval(interval);
   }, []);
   ```

3. **Optimize large tables**
   - Enable pagination
   - Reduce page size

4. **Check browser extensions**
   - Disable extensions that might interfere
   - Try incognito mode

### Memory leaks

**Symptoms**: Memory usage keeps growing

**Solutions**:

1. **Check for cleanup in useEffect**
   ```typescript
   useEffect(() => {
     const interval = setInterval(() => {}, 1000);
     // Important: cleanup!
     return () => clearInterval(interval);
   }, []);
   ```

2. **Monitor memory in DevTools**
   - Chrome DevTools → Memory tab
   - Take heap snapshots to identify leaks

3. **Close WebSocket connections**
   ```typescript
   useEffect(() => {
     const ws = new WebSocket(url);
     return () => ws.close(); // Cleanup!
   }, []);
   ```

---

## Browser Compatibility

### Dashboard not working in Safari

**Symptoms**: Features broken in Safari

**Solutions**:

1. **Check Safari version**
   - Requires Safari 14+

2. **Enable JavaScript**
   - Safari → Preferences → Security → Enable JavaScript

3. **Clear Safari cache**
   - Safari → Preferences → Privacy → Manage Website Data → Remove All

### Internet Explorer not supported

**Symptoms**: Dashboard doesn't work in IE

**Solution**:
- IE is not supported
- Use modern browser: Chrome, Firefox, Safari, or Edge

---

## Deployment Issues

### 404 errors on page refresh

**Symptoms**: Page works initially but 404 on refresh

**Solution**: Configure server to redirect to `index.html`

```nginx
# nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### Environment variables not working

**Symptoms**: API URL not loading from .env

**Solutions**:

1. **Check variable name**
   ```bash
   # Must start with VITE_
   VITE_API_URL=http://localhost:8000
   ```

2. **Restart development server**
   ```bash
   # .env changes require restart
   npm run dev
   ```

3. **Check build command**
   ```bash
   # Ensure .env is loaded
   npm run build
   ```

### Assets not loading after deployment

**Symptoms**: Broken images, missing CSS/JS

**Solutions**:

1. **Check base URL**
   ```typescript
   // vite.config.ts
   export default defineConfig({
     base: '/dashboard/', // Match deployment path
   });
   ```

2. **Use absolute paths**
   ```html
   <!-- Use absolute paths in index.html -->
   <link rel="stylesheet" href="/dashboard/assets/style.css">
   ```

3. **Check server configuration**
   - Ensure static files are served correctly

---

## Common Error Messages

### "Failed to fetch"

**Cause**: Cannot connect to API server

**Solution**: Check API URL, ensure server is running, check CORS

### "Module not found"

**Cause**: Missing dependency or incorrect import path

**Solution**: Check import paths, install missing packages, verify aliases

### "TypeError: Cannot read property '...' of undefined"

**Cause**: Accessing property of null/undefined object

**Solution**: Add null checks, use optional chaining (`?.`)

### "Maximum update depth exceeded"

**Cause**: Infinite render loop, usually in useEffect

**Solution**: Fix useEffect dependencies, add proper cleanup

---

## Debug Mode

### Enable Debug Logging

```bash
# .env
VITE_DEBUG_API_CALLS=true
VITE_DEBUG_WEBSOCKETS=true
VITE_ENABLE_DEBUG_MODE=true
```

### Browser DevTools

**Console Tab**: View logs and errors
```javascript
console.log('Debug info:', data);
console.error('Error:', error);
```

**Network Tab**: Monitor API requests
- Check request/response
- View timing
- Inspect headers

**React DevTools**: Inspect component state
- Install React DevTools extension
- View props and state
- Profile performance

---

## Performance Profiling

### Chrome DevTools Performance

1. Open DevTools → Performance tab
2. Click Record
3. Interact with dashboard
4. Stop recording
5. Analyze flame graph

### React Profiler

```typescript
import { Profiler } from 'react';

<Profiler id="Dashboard" onRender={(id, phase, actualDuration) => {
  console.log(`${id} ${phase} took ${actualDuration}ms`);
}}>
  <Dashboard />
</Profiler>
```

---

## Getting Help

### Before Asking for Help

1. **Check this troubleshooting guide**
2. **Search existing issues**: https://github.com/ajcasagrande/fakeai/issues
3. **Check documentation**: Other .md files in this directory
4. **Try in incognito mode**: Rule out browser extensions
5. **Test with latest version**: Update dependencies

### Reporting Issues

When reporting issues, include:

1. **Environment Information**
   ```bash
   node --version
   npm --version
   # Browser and version
   # OS and version
   ```

2. **Steps to Reproduce**
   - Detailed steps
   - Expected behavior
   - Actual behavior

3. **Error Messages**
   - Full error message
   - Console logs
   - Network tab errors

4. **Screenshots** (if applicable)

### Resources

- **GitHub Issues**: https://github.com/ajcasagrande/fakeai/issues
- **Discussions**: https://github.com/ajcasagrande/fakeai/discussions
- **Documentation**: Other .md files in this directory

---

## Emergency Fixes

### Nuclear Option: Complete Reset

```bash
# Stop all processes
pkill -f node
pkill -f fakeai

# Clean everything
cd fakeai/dashboard
rm -rf node_modules dist .vite package-lock.json

# Reinstall
npm install

# Rebuild
npm run build

# Start fresh
npm run dev
```

### Rollback to Previous Version

```bash
# Check previous commits
git log --oneline

# Rollback
git checkout <commit-hash>

# Reinstall and rebuild
npm install
npm run build
```

---

**Still having issues? Open an issue on GitHub with detailed information.**
