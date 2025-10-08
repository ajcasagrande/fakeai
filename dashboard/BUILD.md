# FakeAI Dashboard Build Guide

This guide explains how to build and integrate the React-based dashboard with the FakeAI pip package.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Building the Dashboard](#building-the-dashboard)
- [Development Workflow](#development-workflow)
- [CI/CD Integration](#cicd-integration)
- [Package Distribution](#package-distribution)
- [Troubleshooting](#troubleshooting)

## Overview

The FakeAI dashboard is a React-based Single Page Application (SPA) built with:
- React 18
- TypeScript
- Vite (build tool)
- TailwindCSS
- Recharts for visualizations
- React Router for client-side routing

The build process compiles the TypeScript/React code into static HTML, CSS, and JavaScript files that are:
1. Copied to `fakeai/static/spa/`
2. Included in the pip package via `MANIFEST.in`
3. Served by FastAPI at the `/spa` endpoint

## Prerequisites

### Required for Building

- **Node.js**: Version 18 or later
- **npm**: Version 9 or later (comes with Node.js)

### Check Installation

```bash
node --version  # Should show v18.0.0 or later
npm --version   # Should show 9.0.0 or later
```

### Installing Node.js

**macOS:**
```bash
brew install node
```

**Ubuntu/Debian:**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Windows:**
Download from [nodejs.org](https://nodejs.org/)

## Building the Dashboard

### Method 1: Using the Build Script (Recommended)

```bash
# From the project root directory
python -m fakeai.dashboard.build
```

This will:
1. Check for Node.js and npm
2. Install dependencies (`npm install`)
3. Build the dashboard (`npm run build`)
4. Copy files to `fakeai/static/spa/`
5. Verify the build

**Options:**

```bash
# Skip npm install (if dependencies already installed)
python -m fakeai.dashboard.build --skip-install

# Clean build artifacts
python -m fakeai.dashboard.build --clean

# Verify existing build
python -m fakeai.dashboard.build --verify-only
```

### Method 2: Manual Build

```bash
# Navigate to dashboard directory
cd dashboard

# Install dependencies
npm install

# Build the dashboard
npm run build

# Copy to static directory (from project root)
cd ..
mkdir -p fakeai/static/spa
cp -r dashboard/dist/* fakeai/static/spa/
```

### Method 3: Using the Shell Script

```bash
# From the project root
./scripts/build_dashboard.sh
```

## Development Workflow

### Local Development

For dashboard development with hot-reload:

```bash
cd dashboard
npm run dev
```

This starts the Vite dev server at `http://localhost:5173`. Configure API proxy in `vite.config.ts`:

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/v1': 'http://localhost:8000',
      '/metrics': 'http://localhost:8000',
    }
  }
})
```

### Testing the Built Dashboard

1. Build the dashboard:
   ```bash
   python -m fakeai.dashboard.build
   ```

2. Start the FakeAI server:
   ```bash
   fakeai serve
   ```

3. Access the dashboard:
   ```
   http://localhost:8000/spa
   ```

## CI/CD Integration

### GitHub Actions Workflow

The project includes a GitHub Actions workflow (`.github/workflows/build-dashboard.yml`) that:
1. Installs Node.js
2. Builds the dashboard
3. Includes built files in the release artifact

**Manual Workflow Trigger:**

```bash
gh workflow run build-dashboard.yml
```

### Building in CI Environments

For CI/CD pipelines without Node.js:

**Option 1: Install Node.js**
```yaml
- name: Setup Node.js
  uses: actions/setup-node@v3
  with:
    node-version: '18'

- name: Build Dashboard
  run: python -m fakeai.dashboard.build
```

**Option 2: Use Pre-built Assets**
```bash
# Download pre-built assets from GitHub release
curl -L -o dashboard-build.tar.gz \
  https://github.com/ajcasagrande/fakeai/releases/latest/download/dashboard-build.tar.gz
tar -xzf dashboard-build.tar.gz -C fakeai/static/
```

**Option 3: Skip Dashboard**
```bash
# Build without dashboard
pip install -e .
# The package will work, but /spa endpoint will return 404
```

## Package Distribution

### Building a Distribution Package

```bash
# Build the dashboard first
python -m fakeai.dashboard.build

# Build the Python package
python -m build

# The wheel will include the dashboard files
ls dist/fakeai-*.whl
```

### Verifying Package Contents

```bash
# Extract and inspect the wheel
unzip -l dist/fakeai-*.whl | grep "static/spa"
```

You should see:
```
fakeai/static/spa/index.html
fakeai/static/spa/assets/*.js
fakeai/static/spa/assets/*.css
```

### Publishing to PyPI

```bash
# Build with dashboard
python -m fakeai.dashboard.build

# Build distribution
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

### Installing from PyPI

```bash
# Regular install (includes pre-built dashboard)
pip install fakeai

# The dashboard will be available at /spa endpoint
```

## Troubleshooting

### Dashboard Not Found (404)

**Problem:** Accessing `/spa` returns 404

**Solutions:**
1. Verify the build:
   ```bash
   python -m fakeai.dashboard.build --verify-only
   ```

2. Check if files exist:
   ```bash
   ls -la fakeai/static/spa/
   ```

3. Rebuild the dashboard:
   ```bash
   python -m fakeai.dashboard.build --clean
   python -m fakeai.dashboard.build
   ```

### Node.js Not Found

**Problem:** Build script reports Node.js not installed

**Solutions:**
1. Install Node.js (see [Prerequisites](#prerequisites))
2. Use pre-built assets (see [CI/CD Integration](#cicd-integration))
3. Build on another system and copy files

### Build Fails with npm Errors

**Problem:** `npm install` or `npm run build` fails

**Solutions:**
1. Clear npm cache:
   ```bash
   npm cache clean --force
   cd dashboard
   rm -rf node_modules package-lock.json
   npm install
   ```

2. Update npm:
   ```bash
   npm install -g npm@latest
   ```

3. Check Node.js version:
   ```bash
   node --version  # Should be >= 18
   ```

### Assets Not Loading

**Problem:** Dashboard loads but assets (JS/CSS) return 404

**Solutions:**
1. Check Vite base configuration in `vite.config.ts`:
   ```typescript
   export default defineConfig({
     base: '/spa/',  // Must match FastAPI route
   })
   ```

2. Verify asset paths in `index.html`
3. Check browser console for errors

### Dashboard Shows Old Version

**Problem:** Changes not reflected after rebuild

**Solutions:**
1. Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
2. Clear browser cache
3. Restart the FakeAI server

### Package Missing Dashboard Files

**Problem:** Installed package doesn't include dashboard

**Solutions:**
1. Verify `MANIFEST.in` includes:
   ```
   recursive-include fakeai/static *.html *.css *.js *.json *.png *.jpg *.svg
   ```

2. Rebuild with verbose output:
   ```bash
   python -m build --wheel -v
   ```

3. Check `pyproject.toml` package-data:
   ```toml
   [tool.setuptools.package-data]
   fakeai = ["static/**/*"]
   ```

## Advanced Topics

### Custom Build Configuration

Edit `dashboard/vite.config.ts` to customize:
- Output directory
- Asset optimization
- Source maps
- Compression

### Environment Variables

Create `dashboard/.env` for build-time configuration:
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_ANALYTICS=false
```

### Multiple Dashboard Builds

Build different versions for different environments:
```bash
# Production build
npm run build

# Development build (with source maps)
npm run build -- --mode development
```

## Getting Help

- GitHub Issues: https://github.com/ajcasagrande/fakeai/issues
- Documentation: https://github.com/ajcasagrande/fakeai#readme
- Discord: [Link to community]

## Additional Resources

- [React Documentation](https://react.dev/)
- [Vite Guide](https://vitejs.dev/guide/)
- [FastAPI Static Files](https://fastapi.tiangolo.com/tutorial/static-files/)
- [Python Packaging Guide](https://packaging.python.org/)
