# Deployment Guide

Complete guide for deploying the FakeAI Dashboard to production environments.

---

## Table of Contents

- [Overview](#overview)
- [Build for Production](#build-for-production)
- [Deployment with FakeAI Server](#deployment-with-fakeai-server)
- [Static Hosting](#static-hosting)
- [Docker Deployment](#docker-deployment)
- [Cloud Platforms](#cloud-platforms)
- [CDN Configuration](#cdn-configuration)
- [Environment Variables](#environment-variables)
- [Performance Optimization](#performance-optimization)
- [Security](#security)
- [Monitoring](#monitoring)

---

## Overview

The FakeAI Dashboard can be deployed in several ways:

1. **Bundled with FakeAI Server** (recommended)
2. **Static hosting** (Netlify, Vercel, S3)
3. **Docker containers**
4. **Cloud platforms** (AWS, Azure, GCP)

---

## Build for Production

### Standard Build

```bash
# Navigate to dashboard directory
cd fakeai/dashboard

# Install dependencies
npm install

# Build for production
npm run build

# Output: dist/ directory
```

### Build Output

```
dist/
├── index.html           # Entry point
├── assets/
│   ├── index-*.js      # Main JavaScript bundle
│   ├── vendor-*.js     # Third-party libraries
│   ├── *.css           # Stylesheets
│   └── *.woff2         # Fonts
└── favicon.ico         # Favicon
```

### Build Optimizations

The production build includes:

- **Minification** - Reduced file sizes
- **Code splitting** - Separate vendor and app bundles
- **Tree shaking** - Remove unused code
- **Compression** - Gzip/Brotli ready
- **Source maps** - For debugging

---

## Deployment with FakeAI Server

### Using Build Script (Recommended)

The dashboard is designed to be served by the FakeAI server:

```bash
# Build and copy to static directory
cd fakeai/dashboard
python build.py

# Or use Python module
python -m fakeai.dashboard.build

# Start FakeAI server
fakeai server

# Dashboard available at: http://localhost:8000/dashboard
```

### Manual Deployment

```bash
# Build dashboard
cd fakeai/dashboard
npm run build

# Copy to FakeAI static directory
cp -r dist/* ../fakeai/static/spa/

# Start server
fakeai server
```

### Verify Deployment

```bash
# Check if dashboard is accessible
curl http://localhost:8000/dashboard

# Should return the HTML of index.html
```

---

## Static Hosting

### Netlify

1. **Connect Repository**
   ```bash
   # netlify.toml
   [build]
     command = "cd fakeai/dashboard && npm install && npm run build"
     publish = "fakeai/dashboard/dist"

   [[redirects]]
     from = "/*"
     to = "/index.html"
     status = 200
   ```

2. **Environment Variables**
   - Set `VITE_API_URL` to your FakeAI server URL
   - Example: `https://api.example.com`

3. **Deploy**
   ```bash
   netlify deploy --prod
   ```

### Vercel

1. **Configure Build**
   ```json
   // vercel.json
   {
     "buildCommand": "cd fakeai/dashboard && npm install && npm run build",
     "outputDirectory": "fakeai/dashboard/dist",
     "routes": [
       {
         "src": "/(.*)",
         "dest": "/index.html"
       }
     ]
   }
   ```

2. **Deploy**
   ```bash
   vercel --prod
   ```

### AWS S3 + CloudFront

1. **Build Dashboard**
   ```bash
   npm run build
   ```

2. **Upload to S3**
   ```bash
   aws s3 sync dist/ s3://your-bucket-name \
     --acl public-read \
     --cache-control max-age=31536000,public
   ```

3. **Configure CloudFront**
   - Origin: S3 bucket
   - Default root object: `index.html`
   - Error pages: Redirect 404 to `/index.html`

4. **Enable HTTPS**
   - Use AWS Certificate Manager
   - Configure custom domain

---

## Docker Deployment

### Dockerfile

```dockerfile
# Multi-stage build for dashboard
FROM node:18-alpine AS dashboard-build

WORKDIR /app/dashboard
COPY fakeai/dashboard/package*.json ./
RUN npm ci
COPY fakeai/dashboard/ ./
RUN npm run build

# Production image
FROM python:3.10-slim

WORKDIR /app
COPY --from=dashboard-build /app/dashboard/dist /app/fakeai/static/spa
COPY . /app

RUN pip install --no-cache-dir .

EXPOSE 8000
CMD ["fakeai", "server", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  fakeai:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FAKEAI_HOST=0.0.0.0
      - FAKEAI_PORT=8000
    volumes:
      - ./data:/app/data
```

### Build and Run

```bash
# Build image
docker build -t fakeai:latest .

# Run container
docker run -p 8000:8000 fakeai:latest

# Or use docker-compose
docker-compose up -d
```

---

## Cloud Platforms

### AWS Elastic Beanstalk

1. **Create Application**
   ```bash
   eb init fakeai
   ```

2. **Configure Environment**
   ```bash
   eb create fakeai-env
   ```

3. **Deploy**
   ```bash
   eb deploy
   ```

### Azure App Service

1. **Create Web App**
   ```bash
   az webapp create --resource-group myResourceGroup \
     --plan myAppServicePlan \
     --name fakeai-dashboard \
     --runtime "PYTHON|3.10"
   ```

2. **Deploy**
   ```bash
   az webapp deployment source config-zip \
     --resource-group myResourceGroup \
     --name fakeai-dashboard \
     --src fakeai.zip
   ```

### Google Cloud Run

1. **Build Container**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/fakeai
   ```

2. **Deploy**
   ```bash
   gcloud run deploy fakeai \
     --image gcr.io/PROJECT_ID/fakeai \
     --platform managed \
     --allow-unauthenticated
   ```

### Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fakeai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fakeai
  template:
    metadata:
      labels:
        app: fakeai
    spec:
      containers:
      - name: fakeai
        image: fakeai:latest
        ports:
        - containerPort: 8000
        env:
        - name: FAKEAI_HOST
          value: "0.0.0.0"
---
apiVersion: v1
kind: Service
metadata:
  name: fakeai-service
spec:
  selector:
    app: fakeai
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## CDN Configuration

### CloudFlare

1. **Add Site to CloudFlare**
2. **Configure Caching**
   - Cache static assets: `*.js`, `*.css`, `*.woff2`
   - Bypass cache: `/v1/*`, `/metrics/*`

3. **Page Rules**
   ```
   *example.com/dashboard/*
   - Cache Level: Standard
   - Browser Cache TTL: 1 year
   ```

### Fastly

```vcl
sub vcl_recv {
  # Cache static assets
  if (req.url ~ "\.(js|css|woff2|png|jpg|svg)$") {
    return(lookup);
  }

  # Don't cache API calls
  if (req.url ~ "^/v1/") {
    return(pass);
  }
}
```

---

## Environment Variables

### Production Configuration

Create `.env.production`:

```bash
# API Configuration
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com

# Feature Flags
VITE_ENABLE_WEBSOCKETS=true
VITE_ENABLE_STREAMING_METRICS=true
VITE_ENABLE_DEBUG_MODE=false

# Analytics (optional)
VITE_ANALYTICS_ID=UA-XXXXXXXXX-X
VITE_SENTRY_DSN=https://xxx@sentry.io/xxx
```

### Build with Environment

```bash
# Use production environment
npm run build -- --mode production

# Use staging environment
npm run build -- --mode staging
```

---

## Performance Optimization

### 1. Enable Compression

```nginx
# nginx.conf
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/css text/javascript application/javascript application/json;

# Brotli compression
brotli on;
brotli_types text/css text/javascript application/javascript application/json;
```

### 2. Set Cache Headers

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. HTTP/2

```nginx
listen 443 ssl http2;
```

### 4. Preload Critical Resources

```html
<!-- index.html -->
<link rel="preload" href="/assets/vendor.js" as="script">
<link rel="preload" href="/assets/main.css" as="style">
```

---

## Security

### 1. HTTPS Only

```nginx
server {
    listen 80;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
}
```

### 2. Security Headers

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

### 3. Rate Limiting

```nginx
limit_req_zone $binary_remote_addr zone=dashboard:10m rate=10r/s;

location /dashboard {
    limit_req zone=dashboard burst=20;
}
```

---

## Monitoring

### 1. Application Monitoring

**Sentry Integration**:

```typescript
// src/main.tsx
import * as Sentry from '@sentry/react';

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE,
});
```

### 2. Performance Monitoring

**Google Analytics**:

```typescript
// src/analytics.ts
import ReactGA from 'react-ga4';

ReactGA.initialize(import.meta.env.VITE_ANALYTICS_ID);

export const trackPageView = (path: string) => {
  ReactGA.send({ hitType: 'pageview', page: path });
};
```

### 3. Health Checks

```bash
# Check dashboard is accessible
curl -f https://yourdomain.com/dashboard || exit 1

# Check API connectivity
curl -f https://yourdomain.com/health || exit 1
```

### 4. Uptime Monitoring

Use services like:
- Pingdom
- UptimeRobot
- StatusCake
- DataDog

---

## Rollback Strategy

### Version Tagging

```bash
# Tag releases
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Rollback to previous version
git checkout v0.9.0
npm run build
./deploy.sh
```

### Blue-Green Deployment

```bash
# Deploy to green environment
deploy_to_green()

# Test green environment
test_green()

# Switch traffic to green
switch_to_green()

# Keep blue as fallback
```

---

## Troubleshooting Deployment

### Issue: 404 on Refresh

**Solution**: Configure server to redirect all routes to `index.html`

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

### Issue: Environment Variables Not Loading

**Solution**: Ensure variables start with `VITE_`

```bash
# Bad
API_URL=http://localhost:8000

# Good
VITE_API_URL=http://localhost:8000
```

### Issue: Assets Not Loading

**Solution**: Check base URL in `vite.config.ts`

```typescript
export default defineConfig({
  base: '/dashboard/',
});
```

---

## Deployment Checklist

- [ ] Build dashboard with production config
- [ ] Set correct API URL in environment variables
- [ ] Enable HTTPS
- [ ] Configure security headers
- [ ] Set up CDN (if using)
- [ ] Configure caching
- [ ] Enable compression
- [ ] Set up monitoring
- [ ] Test all pages and features
- [ ] Verify API connectivity
- [ ] Check console for errors
- [ ] Test on multiple devices
- [ ] Run lighthouse audit
- [ ] Document deployment process

---

**For deployment issues, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)**
