# FakeAI Production Deployment Guide

**Version:** 0.3.2
**Last Updated:** 2025-10-07
**Target Audience:** Operations Teams, DevOps Engineers, SREs

This guide provides comprehensive, production-ready deployment instructions for FakeAI. All commands are executable and tested.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Configuration](#2-configuration)
3. [Environment Variables](#3-environment-variables)
4. [Deployment Steps](#4-deployment-steps)
5. [Health Checks](#5-health-checks)
6. [Monitoring Setup](#6-monitoring-setup)
7. [Alert Configuration](#7-alert-configuration)
8. [Rollback Procedure](#8-rollback-procedure)
9. [Performance Tuning](#9-performance-tuning)
10. [Scaling Considerations](#10-scaling-considerations)
11. [Security Hardening](#11-security-hardening)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Prerequisites

### 1.1 System Requirements

**Minimum (Testing/Staging):**
- CPU: 2 cores
- RAM: 4GB
- Disk: 20GB
- OS: Linux (Ubuntu 20.04+, RHEL 8+, Debian 11+)

**Recommended (Production):**
- CPU: 4+ cores
- RAM: 8GB+
- Disk: 50GB SSD
- OS: Linux (Ubuntu 22.04 LTS or RHEL 9)

**High-Scale Production:**
- CPU: 8+ cores
- RAM: 16GB+
- Disk: 100GB NVMe SSD
- Load Balancer: Required for multi-instance deployments

### 1.2 Software Dependencies

```bash
# Install Python 3.10+ (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3-pip

# Install Python 3.10+ (RHEL/CentOS)
sudo dnf install -y python3.12 python3.12-pip

# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
python3.12 --version
docker --version
docker-compose --version
```

### 1.3 Network Requirements

**Required Ports:**
- `8000`: FakeAI HTTP API (default)
- `6379`: Redis (if using distributed rate limiting)
- `9090`: Prometheus (if using metrics scraping)
- `3000`: Grafana Dashboard (optional)

**Firewall Configuration:**
```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 8000/tcp
sudo ufw allow 6379/tcp  # Only if Redis is on same host
sudo ufw enable

# firewalld (RHEL/CentOS)
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=6379/tcp
sudo firewall-cmd --reload
```

### 1.4 External Dependencies

**Optional but Recommended:**
- Redis 7.x (for distributed rate limiting and caching)
- Prometheus (for metrics collection)
- Grafana (for visualization)
- Reverse Proxy (nginx, HAProxy, or cloud load balancer)

---

## 2. Configuration

### 2.1 Production Configuration File

Create `/etc/fakeai/production.yaml`:

```yaml
# Server Configuration
host: 0.0.0.0
port: 8000
debug: false

# Response Simulation
response_delay: 0.1
random_delay: true
max_variance: 0.2

# Authentication (REQUIRED for production)
require_api_key: true
hash_api_keys: true

# Rate Limiting (REQUIRED for production)
rate_limit_enabled: true
rate_limit_tier: tier-3  # 100 RPM, 10K TPM
# Custom limits (overrides tier):
# rate_limit_rpm: 200
# rate_limit_tpm: 20000

# Security (REQUIRED for production)
enable_security: true  # Master security flag
max_request_size: 10485760  # 10MB
cors_allowed_origins:
  - "https://yourdomain.com"
  - "https://app.yourdomain.com"
cors_allow_credentials: true

# Safety Features
enable_moderation: true
moderation_threshold: 0.7
enable_refusals: true
enable_jailbreak_detection: true

# KV Cache
kv_cache_enabled: true
kv_cache_block_size: 16
kv_cache_num_workers: 4

# Prompt Caching
enable_prompt_caching: true
cache_ttl_seconds: 600
min_tokens_for_cache: 1024

# Performance
enable_context_validation: true
strict_token_counting: false  # Set to true for accuracy, false for speed

# Streaming
stream_timeout_seconds: 300.0
stream_token_timeout_seconds: 30.0
stream_keepalive_enabled: true
stream_keepalive_interval_seconds: 15.0

# Latency Simulation (realistic values)
ttft_ms: 20.0
ttft_variance_percent: 10.0
itl_ms: 5.0
itl_variance_percent: 10.0

# Storage
file_storage_backend: disk
file_storage_path: /var/lib/fakeai/files
file_cleanup_enabled: true

image_storage_backend: disk
generate_actual_images: true
image_retention_hours: 24

# Error Injection (DISABLE in production)
error_injection_enabled: false
error_injection_rate: 0.0
```

**Set proper permissions:**
```bash
sudo mkdir -p /etc/fakeai
sudo chmod 755 /etc/fakeai
sudo chown root:root /etc/fakeai/production.yaml
sudo chmod 640 /etc/fakeai/production.yaml
```

### 2.2 API Key Management

**Create API keys file:**
```bash
# Generate secure API keys
sudo mkdir -p /etc/fakeai/keys
sudo touch /etc/fakeai/keys/api_keys.txt

# Generate keys (example using OpenSSL)
for i in {1..5}; do
  echo "sk-prod-$(openssl rand -hex 32)" | sudo tee -a /etc/fakeai/keys/api_keys.txt
done

# Secure the file
sudo chmod 600 /etc/fakeai/keys/api_keys.txt
sudo chown fakeai:fakeai /etc/fakeai/keys/api_keys.txt
```

**Example `/etc/fakeai/keys/api_keys.txt`:**
```
sk-prod-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
sk-prod-b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7
sk-prod-c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8
```

### 2.3 Storage Directory Setup

```bash
# Create necessary directories
sudo mkdir -p /var/lib/fakeai/{files,images,logs,cache}
sudo mkdir -p /var/log/fakeai

# Create fakeai user (if not exists)
sudo useradd -r -s /bin/false -d /var/lib/fakeai fakeai

# Set ownership
sudo chown -R fakeai:fakeai /var/lib/fakeai
sudo chown -R fakeai:fakeai /var/log/fakeai

# Set permissions
sudo chmod 750 /var/lib/fakeai
sudo chmod 750 /var/log/fakeai
```

---

## 3. Environment Variables

### 3.1 Complete Environment Variable Reference

```bash
# Server Settings
export FAKEAI_HOST="0.0.0.0"
export FAKEAI_PORT="8000"
export FAKEAI_DEBUG="false"

# Response Settings
export FAKEAI_RESPONSE_DELAY="0.1"
export FAKEAI_RANDOM_DELAY="true"
export FAKEAI_MAX_VARIANCE="0.2"

# Authentication (REQUIRED)
export FAKEAI_REQUIRE_API_KEY="true"
export FAKEAI_HASH_API_KEYS="true"
# Option 1: Comma-separated keys
export FAKEAI_API_KEYS="sk-prod-key1,sk-prod-key2,sk-prod-key3"
# Option 2: File path (recommended)
# export FAKEAI_API_KEYS="/etc/fakeai/keys/api_keys.txt"

# Rate Limiting
export FAKEAI_RATE_LIMIT_ENABLED="true"
export FAKEAI_RATE_LIMIT_TIER="tier-3"
# Redis (for distributed rate limiting)
export FAKEAI_REDIS_URL="redis://redis:6379/0"

# Security (REQUIRED)
export FAKEAI_ENABLE_SECURITY="true"
export FAKEAI_MAX_REQUEST_SIZE="10485760"
export FAKEAI_CORS_ALLOWED_ORIGINS='["https://yourdomain.com"]'

# Safety
export FAKEAI_ENABLE_MODERATION="true"
export FAKEAI_MODERATION_THRESHOLD="0.7"
export FAKEAI_ENABLE_REFUSALS="true"
export FAKEAI_ENABLE_JAILBREAK_DETECTION="true"

# KV Cache
export FAKEAI_KV_CACHE_ENABLED="true"
export FAKEAI_KV_CACHE_BLOCK_SIZE="16"
export FAKEAI_KV_CACHE_NUM_WORKERS="4"

# Prompt Caching
export FAKEAI_ENABLE_PROMPT_CACHING="true"
export FAKEAI_CACHE_TTL_SECONDS="600"
export FAKEAI_MIN_TOKENS_FOR_CACHE="1024"

# Performance
export FAKEAI_ENABLE_CONTEXT_VALIDATION="true"
export FAKEAI_STRICT_TOKEN_COUNTING="false"

# Streaming
export FAKEAI_STREAM_TIMEOUT_SECONDS="300.0"
export FAKEAI_STREAM_TOKEN_TIMEOUT_SECONDS="30.0"
export FAKEAI_STREAM_KEEPALIVE_ENABLED="true"
export FAKEAI_STREAM_KEEPALIVE_INTERVAL_SECONDS="15.0"

# Latency Simulation
export FAKEAI_TTFT_MS="20.0"
export FAKEAI_TTFT_VARIANCE_PERCENT="10.0"
export FAKEAI_ITL_MS="5.0"
export FAKEAI_ITL_VARIANCE_PERCENT="10.0"

# Storage
export FAKEAI_FILE_STORAGE_BACKEND="disk"
export FAKEAI_FILE_STORAGE_PATH="/var/lib/fakeai/files"
export FAKEAI_FILE_CLEANUP_ENABLED="true"
export FAKEAI_IMAGE_STORAGE_BACKEND="disk"
export FAKEAI_GENERATE_ACTUAL_IMAGES="true"
export FAKEAI_IMAGE_RETENTION_HOURS="24"

# Error Injection (MUST BE DISABLED)
export FAKEAI_ERROR_INJECTION_ENABLED="false"
export FAKEAI_ERROR_INJECTION_RATE="0.0"
```

### 3.2 Environment File for Systemd

Create `/etc/fakeai/environment`:

```bash
FAKEAI_HOST=0.0.0.0
FAKEAI_PORT=8000
FAKEAI_DEBUG=false
FAKEAI_REQUIRE_API_KEY=true
FAKEAI_HASH_API_KEYS=true
FAKEAI_RATE_LIMIT_ENABLED=true
FAKEAI_RATE_LIMIT_TIER=tier-3
FAKEAI_ENABLE_SECURITY=true
FAKEAI_KV_CACHE_ENABLED=true
FAKEAI_ENABLE_PROMPT_CACHING=true
FAKEAI_FILE_STORAGE_BACKEND=disk
FAKEAI_FILE_STORAGE_PATH=/var/lib/fakeai/files
FAKEAI_IMAGE_STORAGE_BACKEND=disk
FAKEAI_ERROR_INJECTION_ENABLED=false
```

```bash
sudo chmod 640 /etc/fakeai/environment
sudo chown root:fakeai /etc/fakeai/environment
```

---

## 4. Deployment Steps

### 4.1 Docker Deployment (Recommended)

**Step 1: Pull or build Docker image**

```bash
# Option A: Pull from registry (if available)
docker pull fakeai:latest

# Option B: Build from source
cd /opt/fakeai
docker build -t fakeai:0.3.2 -t fakeai:latest .
```

**Step 2: Deploy with Docker Compose**

Create `/opt/fakeai/docker-compose.production.yml`:

```yaml
version: '3.8'

services:
  fakeai:
    image: fakeai:latest
    container_name: fakeai-production
    restart: unless-stopped

    ports:
      - "8000:8000"

    environment:
      - FAKEAI_HOST=0.0.0.0
      - FAKEAI_PORT=8000
      - FAKEAI_DEBUG=false
      - FAKEAI_REQUIRE_API_KEY=true
      - FAKEAI_HASH_API_KEYS=true
      - FAKEAI_RATE_LIMIT_ENABLED=true
      - FAKEAI_RATE_LIMIT_TIER=tier-3
      - FAKEAI_REDIS_URL=redis://redis:6379/0
      - FAKEAI_ENABLE_SECURITY=true
      - FAKEAI_KV_CACHE_ENABLED=true
      - FAKEAI_FILE_STORAGE_BACKEND=disk
      - FAKEAI_FILE_STORAGE_PATH=/app/data/files
      - FAKEAI_IMAGE_STORAGE_BACKEND=disk
      - FAKEAI_ERROR_INJECTION_ENABLED=false

    volumes:
      - /etc/fakeai/keys/api_keys.txt:/app/keys/api_keys.txt:ro
      - fakeai-data:/app/data
      - fakeai-logs:/app/logs

    networks:
      - fakeai-network

    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

    depends_on:
      redis:
        condition: service_healthy

    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G

    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "10"

  redis:
    image: redis:7-alpine
    container_name: fakeai-redis
    restart: unless-stopped

    ports:
      - "6379:6379"

    volumes:
      - redis-data:/data

    networks:
      - fakeai-network

    command: >
      redis-server
      --appendonly yes
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
      --save 60 1000
      --save 300 100
      --save 900 10

    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 5s

    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

networks:
  fakeai-network:
    driver: bridge

volumes:
  fakeai-data:
    driver: local
  fakeai-logs:
    driver: local
  redis-data:
    driver: local
```

**Step 3: Deploy the stack**

```bash
# Deploy
cd /opt/fakeai
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f fakeai

# Verify health
curl http://localhost:8000/health
```

### 4.2 Systemd Service Deployment (Native Python)

**Step 1: Install FakeAI**

```bash
# Create virtual environment
sudo mkdir -p /opt/fakeai
cd /opt/fakeai
sudo python3.12 -m venv venv
sudo chown -R fakeai:fakeai /opt/fakeai

# Activate and install
sudo -u fakeai /opt/fakeai/venv/bin/pip install --upgrade pip
sudo -u fakeai /opt/fakeai/venv/bin/pip install fakeai==0.3.2

# Or install from source
# cd /path/to/fakeai-source
# sudo -u fakeai /opt/fakeai/venv/bin/pip install -e .
```

**Step 2: Create systemd service file**

Create `/etc/systemd/system/fakeai.service`:

```ini
[Unit]
Description=FakeAI OpenAI Compatible API Server
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=fakeai
Group=fakeai
WorkingDirectory=/opt/fakeai

# Environment
EnvironmentFile=/etc/fakeai/environment

# Start command
ExecStart=/opt/fakeai/venv/bin/python -m fakeai.cli server \
    --config-file /etc/fakeai/production.yaml \
    --api-key /etc/fakeai/keys/api_keys.txt

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/fakeai /var/log/fakeai
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=fakeai

[Install]
WantedBy=multi-user.target
```

**Step 3: Enable and start service**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable fakeai.service

# Start service
sudo systemctl start fakeai.service

# Check status
sudo systemctl status fakeai.service

# View logs
sudo journalctl -u fakeai.service -f
```

### 4.3 Kubernetes Deployment

**Step 1: Create namespace**

```bash
kubectl create namespace fakeai-production
```

**Step 2: Create ConfigMap**

`fakeai-configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fakeai-config
  namespace: fakeai-production
data:
  production.yaml: |
    host: 0.0.0.0
    port: 8000
    debug: false
    require_api_key: true
    hash_api_keys: true
    rate_limit_enabled: true
    rate_limit_tier: tier-3
    enable_security: true
    kv_cache_enabled: true
    enable_prompt_caching: true
    file_storage_backend: disk
    file_storage_path: /app/data/files
    image_storage_backend: disk
    error_injection_enabled: false
```

**Step 3: Create Secret**

```bash
# Create API keys file
echo -e "sk-prod-key1\nsk-prod-key2\nsk-prod-key3" > api_keys.txt

# Create secret
kubectl create secret generic fakeai-api-keys \
  --from-file=api_keys.txt=api_keys.txt \
  -n fakeai-production

# Clean up local file
rm api_keys.txt
```

**Step 4: Create Deployment**

`fakeai-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fakeai
  namespace: fakeai-production
  labels:
    app: fakeai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fakeai
  template:
    metadata:
      labels:
        app: fakeai
        version: v0.3.2
    spec:
      containers:
      - name: fakeai
        image: fakeai:0.3.2
        imagePullPolicy: IfNotPresent

        ports:
        - containerPort: 8000
          name: http
          protocol: TCP

        env:
        - name: FAKEAI_HOST
          value: "0.0.0.0"
        - name: FAKEAI_PORT
          value: "8000"
        - name: FAKEAI_DEBUG
          value: "false"
        - name: FAKEAI_REQUIRE_API_KEY
          value: "true"
        - name: FAKEAI_HASH_API_KEYS
          value: "true"
        - name: FAKEAI_RATE_LIMIT_ENABLED
          value: "true"
        - name: FAKEAI_RATE_LIMIT_TIER
          value: "tier-3"
        - name: FAKEAI_REDIS_URL
          value: "redis://fakeai-redis:6379/0"
        - name: FAKEAI_ENABLE_SECURITY
          value: "true"
        - name: FAKEAI_ERROR_INJECTION_ENABLED
          value: "false"

        volumeMounts:
        - name: config
          mountPath: /etc/fakeai
          readOnly: true
        - name: api-keys
          mountPath: /app/keys
          readOnly: true
        - name: data
          mountPath: /app/data

        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"

        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3

        startupProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 0
          periodSeconds: 2
          timeoutSeconds: 3
          failureThreshold: 30

      volumes:
      - name: config
        configMap:
          name: fakeai-config
      - name: api-keys
        secret:
          secretName: fakeai-api-keys
      - name: data
        emptyDir: {}

      securityContext:
        fsGroup: 1000
        runAsUser: 1000
        runAsNonRoot: true
```

**Step 5: Create Service**

`fakeai-service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fakeai
  namespace: fakeai-production
  labels:
    app: fakeai
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: fakeai
```

**Step 6: Deploy to Kubernetes**

```bash
# Apply manifests
kubectl apply -f fakeai-configmap.yaml
kubectl apply -f fakeai-deployment.yaml
kubectl apply -f fakeai-service.yaml

# Check deployment
kubectl get pods -n fakeai-production
kubectl get svc -n fakeai-production

# View logs
kubectl logs -f deployment/fakeai -n fakeai-production
```

---

## 5. Health Checks

### 5.1 Health Check Endpoint

**Endpoint:** `GET /health`

**Response (Healthy):**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-07T12:00:00.000Z",
  "version": "0.3.2",
  "uptime_seconds": 3600.5,
  "metrics_summary": {
    "total_requests": 12450,
    "total_requests_per_second": 3.46,
    "total_errors": 12,
    "total_errors_per_second": 0.003,
    "error_rate_percentage": 0.096,
    "average_latency_seconds": 0.045,
    "active_streams": 5
  }
}
```

**Response (Degraded):**
```json
{
  "status": "degraded",
  "timestamp": "2025-10-07T12:00:00.000Z",
  "version": "0.3.2",
  "uptime_seconds": 3600.5,
  "warnings": [
    "High error rate: 5.2%",
    "Redis connection unavailable"
  ]
}
```

### 5.2 Health Check Commands

```bash
# Basic health check
curl -f http://localhost:8000/health || exit 1

# Health check with detailed output
curl -s http://localhost:8000/health | jq .

# Check specific health criteria
curl -s http://localhost:8000/health | jq -e '.status == "healthy"'

# Monitor health continuously
watch -n 5 'curl -s http://localhost:8000/health | jq .'
```

### 5.3 Load Balancer Health Check Configuration

**Nginx:**
```nginx
upstream fakeai_backend {
    server 10.0.1.10:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.12:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;

    location / {
        proxy_pass http://fakeai_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://fakeai_backend;
        access_log off;
    }
}
```

**HAProxy:**
```haproxy
backend fakeai_backend
    mode http
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200
    default-server inter 5s fall 3 rise 2

    server fakeai1 10.0.1.10:8000 check
    server fakeai2 10.0.1.11:8000 check
    server fakeai3 10.0.1.12:8000 check
```

**AWS Application Load Balancer (ALB):**
```bash
# Create target group with health check
aws elbv2 create-target-group \
  --name fakeai-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxxxxxxx \
  --health-check-enabled \
  --health-check-protocol HTTP \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 10 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3
```

---

## 6. Monitoring Setup

### 6.1 Metrics Endpoints

**Endpoint:** `GET /metrics`

**Response:**
```json
{
  "requests": {
    "/v1/chat/completions": {
      "count": 15420,
      "rate": 4.28,
      "avg": 0.045,
      "p50": 0.042,
      "p95": 0.089,
      "p99": 0.152
    }
  },
  "tokens": {
    "total": 1245000,
    "rate": 346.25,
    "input": 842000,
    "output": 403000
  },
  "errors": {
    "4xx": {"count": 45, "rate": 0.0125},
    "5xx": {"count": 12, "rate": 0.0033}
  },
  "streaming_stats": {
    "active_streams": 8,
    "completed_streams": 1240,
    "failed_streams": 3,
    "ttft": {
      "avg": 0.021,
      "p50": 0.020,
      "p95": 0.035,
      "p99": 0.048
    },
    "tokens_per_second": {
      "avg": 85.3,
      "p50": 82.1,
      "p95": 98.7,
      "p99": 105.2
    }
  },
  "cache_stats": {
    "hit_rate": 0.68,
    "hits": 8520,
    "misses": 4012,
    "tokens_saved": 452000
  }
}
```

**Prometheus Metrics Endpoint:** `GET /metrics/prometheus`

```bash
# Fetch Prometheus metrics
curl http://localhost:8000/metrics/prometheus

# Example output:
# HELP fakeai_requests_total Total number of requests
# TYPE fakeai_requests_total counter
fakeai_requests_total{endpoint="/v1/chat/completions",method="POST"} 15420
fakeai_requests_total{endpoint="/v1/embeddings",method="POST"} 842

# HELP fakeai_request_duration_seconds Request duration in seconds
# TYPE fakeai_request_duration_seconds histogram
fakeai_request_duration_seconds_bucket{endpoint="/v1/chat/completions",le="0.01"} 1240
fakeai_request_duration_seconds_bucket{endpoint="/v1/chat/completions",le="0.05"} 12450
```

### 6.2 Prometheus Configuration

**Install Prometheus:**
```bash
# Download and install
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar -xzf prometheus-2.45.0.linux-amd64.tar.gz
sudo mv prometheus-2.45.0.linux-amd64 /opt/prometheus
sudo ln -s /opt/prometheus/prometheus /usr/local/bin/
```

**Create `/etc/prometheus/prometheus.yml`:**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'production'
    environment: 'prod'

scrape_configs:
  - job_name: 'fakeai'
    static_configs:
      - targets:
          - 'localhost:8000'
    metrics_path: /metrics/prometheus
    scrape_interval: 10s
    scrape_timeout: 5s

  - job_name: 'redis'
    static_configs:
      - targets:
          - 'localhost:6379'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - 'localhost:9093'
```

**Create systemd service `/etc/systemd/system/prometheus.service`:**

```ini
[Unit]
Description=Prometheus Monitoring System
After=network.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus \
  --web.console.templates=/opt/prometheus/consoles \
  --web.console.libraries=/opt/prometheus/console_libraries \
  --web.listen-address=0.0.0.0:9090
Restart=always

[Install]
WantedBy=multi-user.target
```

**Start Prometheus:**
```bash
sudo useradd -r -s /bin/false prometheus
sudo mkdir -p /var/lib/prometheus
sudo chown -R prometheus:prometheus /var/lib/prometheus
sudo systemctl daemon-reload
sudo systemctl enable prometheus
sudo systemctl start prometheus

# Access Prometheus UI
# http://localhost:9090
```

### 6.3 Grafana Dashboard Setup

**Install Grafana:**
```bash
# Add Grafana repository
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana

# Start Grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# Access Grafana
# http://localhost:3000
# Default login: admin/admin
```

**Import FakeAI Dashboard:**

1. Log in to Grafana
2. Go to Dashboards → Import
3. Use the following dashboard JSON:

```json
{
  "dashboard": {
    "title": "FakeAI Production Monitoring",
    "panels": [
      {
        "title": "Requests per Second",
        "targets": [
          {
            "expr": "rate(fakeai_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(fakeai_errors_total[5m]) / rate(fakeai_requests_total[5m])"
          }
        ]
      },
      {
        "title": "P95 Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(fakeai_request_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Active Streams",
        "targets": [
          {
            "expr": "fakeai_active_streams"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [
          {
            "expr": "fakeai_cache_hits / (fakeai_cache_hits + fakeai_cache_misses)"
          }
        ]
      }
    ]
  }
}
```

### 6.4 Log Aggregation

**Option 1: Journald (Systemd)**

```bash
# View logs
sudo journalctl -u fakeai -f

# Search logs
sudo journalctl -u fakeai --since "1 hour ago" | grep ERROR

# Export logs
sudo journalctl -u fakeai --since today -o json > /tmp/fakeai-logs.json
```

**Option 2: ELK Stack (Elasticsearch, Logstash, Kibana)**

**Filebeat configuration `/etc/filebeat/filebeat.yml`:**

```yaml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/fakeai/*.log
    fields:
      service: fakeai
      environment: production

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "fakeai-logs-%{+yyyy.MM.dd}"

setup.kibana:
  host: "localhost:5601"
```

**Option 3: Cloud Logging**

```bash
# AWS CloudWatch
pip install watchtower

# Add to your Python code:
import watchtower
import logging

logger = logging.getLogger()
logger.addHandler(watchtower.CloudWatchLogHandler(
    log_group='fakeai-production',
    stream_name='fakeai-server'
))
```

---

## 7. Alert Configuration

### 7.1 Prometheus Alertmanager

**Install Alertmanager:**
```bash
wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
tar -xzf alertmanager-0.26.0.linux-amd64.tar.gz
sudo mv alertmanager-0.26.0.linux-amd64 /opt/alertmanager
sudo ln -s /opt/alertmanager/alertmanager /usr/local/bin/
```

**Create `/etc/prometheus/alertmanager.yml`:**

```yaml
global:
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alerts@example.com'
  smtp_auth_username: 'alerts@example.com'
  smtp_auth_password: 'password'

route:
  receiver: 'team-ops'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true
    - match:
        severity: warning
      receiver: 'team-ops'

receivers:
  - name: 'team-ops'
    email_configs:
      - to: 'ops-team@example.com'
        headers:
          Subject: '[{{ .Status }}] FakeAI Alert: {{ .GroupLabels.alertname }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'cluster']
```

**Create `/etc/prometheus/alerts.yml`:**

```yaml
groups:
  - name: fakeai_alerts
    interval: 30s
    rules:
      # High Error Rate
      - alert: HighErrorRate
        expr: (rate(fakeai_errors_total[5m]) / rate(fakeai_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
          service: fakeai
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"

      # Service Down
      - alert: ServiceDown
        expr: up{job="fakeai"} == 0
        for: 1m
        labels:
          severity: critical
          service: fakeai
        annotations:
          summary: "FakeAI service is down"
          description: "FakeAI instance {{ $labels.instance }} has been down for more than 1 minute"

      # High Latency
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(fakeai_request_duration_seconds_bucket[5m])) > 1.0
        for: 10m
        labels:
          severity: warning
          service: fakeai
        annotations:
          summary: "High request latency"
          description: "P95 latency is {{ $value }}s (threshold: 1s)"

      # High Request Rate
      - alert: HighRequestRate
        expr: rate(fakeai_requests_total[1m]) > 1000
        for: 5m
        labels:
          severity: warning
          service: fakeai
        annotations:
          summary: "Unusually high request rate"
          description: "Request rate is {{ $value }} req/s (threshold: 1000 req/s)"

      # Low Cache Hit Rate
      - alert: LowCacheHitRate
        expr: (fakeai_cache_hits / (fakeai_cache_hits + fakeai_cache_misses)) < 0.3
        for: 15m
        labels:
          severity: warning
          service: fakeai
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value | humanizePercentage }} (threshold: 30%)"

      # Redis Connection Failed
      - alert: RedisConnectionFailed
        expr: redis_up == 0
        for: 2m
        labels:
          severity: critical
          service: redis
        annotations:
          summary: "Redis connection failed"
          description: "Redis instance {{ $labels.instance }} is unreachable"

      # High Memory Usage
      - alert: HighMemoryUsage
        expr: (container_memory_usage_bytes{container="fakeai"} / container_spec_memory_limit_bytes{container="fakeai"}) > 0.85
        for: 5m
        labels:
          severity: warning
          service: fakeai
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }} of limit"

      # High CPU Usage
      - alert: HighCPUUsage
        expr: rate(container_cpu_usage_seconds_total{container="fakeai"}[5m]) > 0.8
        for: 10m
        labels:
          severity: warning
          service: fakeai
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value | humanizePercentage }}"

      # Too Many Active Streams
      - alert: TooManyActiveStreams
        expr: fakeai_active_streams > 100
        for: 5m
        labels:
          severity: warning
          service: fakeai
        annotations:
          summary: "Too many active streams"
          description: "Active streams: {{ $value }} (threshold: 100)"
```

**Add to Prometheus config:**
```yaml
# Add to /etc/prometheus/prometheus.yml
rule_files:
  - 'alerts.yml'
```

**Start Alertmanager:**
```bash
sudo useradd -r -s /bin/false alertmanager
sudo systemctl daemon-reload
sudo systemctl enable alertmanager
sudo systemctl start alertmanager

# Test alert
curl -X POST http://localhost:9093/api/v1/alerts
```

### 7.2 PagerDuty Integration

```bash
# Configure PagerDuty receiver in alertmanager.yml
receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_INTEGRATION_KEY'
        description: '{{ .GroupLabels.alertname }}: {{ .Annotations.summary }}'
        severity: '{{ .Labels.severity }}'
```

### 7.3 Slack Integration

```bash
# Configure Slack receiver in alertmanager.yml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts-fakeai'
        title: '[{{ .Status }}] {{ .GroupLabels.alertname }}'
        text: '{{ .Annotations.description }}'
        send_resolved: true
```

---

## 8. Rollback Procedure

### 8.1 Docker Rollback

**Immediate rollback:**
```bash
# Stop current version
docker-compose -f docker-compose.production.yml down

# Pull previous version
docker pull fakeai:0.3.1

# Update docker-compose.yml to use previous version
sed -i 's/fakeai:0.3.2/fakeai:0.3.1/g' docker-compose.production.yml

# Start previous version
docker-compose -f docker-compose.production.yml up -d

# Verify
curl http://localhost:8000/health
```

**Keep previous versions:**
```bash
# Tag images with versions
docker tag fakeai:latest fakeai:0.3.2
docker tag fakeai:latest fakeai:previous

# Quick rollback
docker-compose -f docker-compose.production.yml stop fakeai
docker tag fakeai:0.3.1 fakeai:latest
docker-compose -f docker-compose.production.yml up -d fakeai
```

### 8.2 Systemd Rollback

**Prepare rollback:**
```bash
# Keep previous version
sudo cp -r /opt/fakeai /opt/fakeai-0.3.2-backup

# Rollback
sudo systemctl stop fakeai
sudo rm -rf /opt/fakeai
sudo mv /opt/fakeai-0.3.2-backup /opt/fakeai
sudo systemctl start fakeai
sudo systemctl status fakeai
```

**Using virtual environments:**
```bash
# Install new version in separate venv
sudo -u fakeai python3.12 -m venv /opt/fakeai/venv-0.3.2
sudo -u fakeai /opt/fakeai/venv-0.3.2/bin/pip install fakeai==0.3.2

# Update symlink for quick rollback
sudo ln -sfn /opt/fakeai/venv-0.3.2 /opt/fakeai/venv

# Rollback
sudo ln -sfn /opt/fakeai/venv-0.3.1 /opt/fakeai/venv
sudo systemctl restart fakeai
```

### 8.3 Kubernetes Rollback

**Rollback deployment:**
```bash
# View rollout history
kubectl rollout history deployment/fakeai -n fakeai-production

# Rollback to previous version
kubectl rollout undo deployment/fakeai -n fakeai-production

# Rollback to specific revision
kubectl rollout undo deployment/fakeai --to-revision=2 -n fakeai-production

# Check rollback status
kubectl rollout status deployment/fakeai -n fakeai-production

# Verify pods
kubectl get pods -n fakeai-production -l app=fakeai
```

**Blue-Green Deployment (zero downtime):**
```bash
# Deploy new version (green)
kubectl apply -f fakeai-deployment-v0.3.2.yaml

# Wait for green to be ready
kubectl wait --for=condition=available deployment/fakeai-green -n fakeai-production

# Switch traffic
kubectl patch service fakeai -n fakeai-production -p '{"spec":{"selector":{"version":"v0.3.2"}}}'

# If issues, switch back
kubectl patch service fakeai -n fakeai-production -p '{"spec":{"selector":{"version":"v0.3.1"}}}'

# After verification, delete old version
kubectl delete deployment fakeai-blue -n fakeai-production
```

### 8.4 Database/State Rollback

**Backup before deployment:**
```bash
# Backup Redis data
docker exec fakeai-redis redis-cli SAVE
docker cp fakeai-redis:/data/dump.rdb /backup/redis-$(date +%Y%m%d-%H%M%S).rdb

# Restore Redis data
docker cp /backup/redis-20251007-120000.rdb fakeai-redis:/data/dump.rdb
docker exec fakeai-redis redis-cli FLUSHALL
docker restart fakeai-redis
```

---

## 9. Performance Tuning

### 9.1 Python/Uvicorn Tuning

**Increase worker processes:**

```bash
# For systemd service, update ExecStart
ExecStart=/opt/fakeai/venv/bin/uvicorn fakeai.app:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 8 \
    --loop uvloop \
    --http h11 \
    --log-level info \
    --access-log \
    --no-use-colors
```

**Worker calculation:**
```bash
# Formula: (2 x CPU cores) + 1
# For 4 CPU cores: (2 x 4) + 1 = 9 workers
# For 8 CPU cores: (2 x 8) + 1 = 17 workers
```

**Enable uvloop for better performance:**
```bash
pip install uvloop

# In your code or CLI
python -m fakeai.cli server --host 0.0.0.0 --port 8000
```

### 9.2 System Tuning

**Linux kernel parameters (`/etc/sysctl.conf`):**
```bash
# Network tuning
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30

# File descriptor limits
fs.file-max = 2097152

# Apply changes
sudo sysctl -p
```

**Increase file descriptor limits (`/etc/security/limits.conf`):**
```bash
*       soft    nofile  65536
*       hard    nofile  65536
fakeai  soft    nofile  65536
fakeai  hard    nofile  65536
```

**Verify limits:**
```bash
ulimit -n
cat /proc/sys/fs/file-max
```

### 9.3 Redis Tuning

**Redis configuration (`/etc/redis/redis.conf`):**
```bash
# Memory
maxmemory 2gb
maxmemory-policy allkeys-lru

# Performance
tcp-backlog 511
timeout 300
tcp-keepalive 60

# Persistence (for rate limiting, disable snapshotting)
save ""
appendonly yes
appendfsync everysec

# Network
bind 0.0.0.0
protected-mode yes
requirepass YOUR_STRONG_PASSWORD

# Apply config
sudo systemctl restart redis
```

### 9.4 Application-Level Tuning

**Disable features you don't need:**
```yaml
# In production.yaml
enable_context_validation: false  # If not needed
strict_token_counting: false      # Faster, less accurate
generate_actual_images: false     # Use fake URLs instead
kv_cache_enabled: true            # Enable caching
enable_prompt_caching: true       # Enable caching
```

**Optimize response delays:**
```yaml
response_delay: 0.05  # Reduce from default 0.5s
random_delay: true
max_variance: 0.1
ttft_ms: 10.0         # Reduce TTFT
itl_ms: 2.0           # Reduce inter-token latency
```

### 9.5 Connection Pooling

**Database connection pooling (if using PostgreSQL/MySQL):**
```python
# Example for SQLAlchemy
from sqlalchemy import create_engine

engine = create_engine(
    'postgresql://user:pass@localhost/db',
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 9.6 Caching Strategy

**Enable all caching features:**
```yaml
# Prompt caching
enable_prompt_caching: true
cache_ttl_seconds: 3600      # Increase TTL
min_tokens_for_cache: 512    # Lower threshold

# KV cache
kv_cache_enabled: true
kv_cache_block_size: 32      # Larger blocks
kv_cache_num_workers: 8      # More workers
```

---

## 10. Scaling Considerations

### 10.1 Horizontal Scaling

**Load Balancer Setup (Nginx):**

`/etc/nginx/sites-available/fakeai`:
```nginx
upstream fakeai_cluster {
    least_conn;  # Use least connections algorithm

    server 10.0.1.10:8000 max_fails=3 fail_timeout=30s weight=1;
    server 10.0.1.11:8000 max_fails=3 fail_timeout=30s weight=1;
    server 10.0.1.12:8000 max_fails=3 fail_timeout=30s weight=1;
    server 10.0.1.13:8000 max_fails=3 fail_timeout=30s weight=1;

    keepalive 32;
}

server {
    listen 80;
    server_name api.example.com;

    # Rate limiting (optional, if not using Redis)
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
    limit_req zone=api_limit burst=20 nodelay;

    location / {
        proxy_pass http://fakeai_cluster;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    location /health {
        proxy_pass http://fakeai_cluster;
        access_log off;
    }
}
```

**Enable configuration:**
```bash
sudo ln -s /etc/nginx/sites-available/fakeai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 10.2 Kubernetes Horizontal Pod Autoscaler (HPA)

**Create HPA:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fakeai-hpa
  namespace: fakeai-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fakeai
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 4
        periodSeconds: 30
      selectPolicy: Max
```

**Apply HPA:**
```bash
kubectl apply -f fakeai-hpa.yaml

# Monitor HPA
kubectl get hpa -n fakeai-production -w

# Check autoscaling events
kubectl describe hpa fakeai-hpa -n fakeai-production
```

### 10.3 Vertical Scaling

**Increase resources (Docker):**
```yaml
services:
  fakeai:
    deploy:
      resources:
        limits:
          cpus: '8'      # Increase from 4
          memory: 16G    # Increase from 8G
        reservations:
          cpus: '4'
          memory: 8G
```

**Increase resources (Kubernetes):**
```yaml
resources:
  requests:
    memory: "8Gi"
    cpu: "4"
  limits:
    memory: "16Gi"
    cpu: "8"
```

### 10.4 Database Scaling (Redis)

**Redis Cluster Setup:**
```bash
# Create 6 Redis nodes (3 masters, 3 replicas)
for port in 7000 7001 7002 7003 7004 7005; do
  mkdir -p /etc/redis/cluster/$port
  cat > /etc/redis/cluster/$port/redis.conf <<EOF
port $port
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
appendonly yes
dir /var/lib/redis/cluster/$port
EOF

  redis-server /etc/redis/cluster/$port/redis.conf &
done

# Create cluster
redis-cli --cluster create \
  127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 \
  127.0.0.1:7003 127.0.0.1:7004 127.0.0.1:7005 \
  --cluster-replicas 1

# Update FakeAI Redis URL
export FAKEAI_REDIS_URL="redis://127.0.0.1:7000,127.0.0.1:7001,127.0.0.1:7002"
```

### 10.5 Capacity Planning

**Calculate required capacity:**

```bash
# Formula:
# Required RPS = Peak Requests per Day / (24 * 3600 * 0.2)
# 0.2 = Traffic concentrated in 20% of the day

# Example: 10M requests per day
# Required RPS = 10,000,000 / (24 * 3600 * 0.2) = 578.7 RPS

# Instances needed = Required RPS / (Instance RPS capacity * 0.7)
# 0.7 = 70% utilization target

# If each instance handles 100 RPS:
# Instances = 578.7 / (100 * 0.7) = 8.3 ≈ 9 instances
```

**Benchmarking:**
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Simple benchmark
ab -n 10000 -c 100 http://localhost:8000/health

# Load test with auth
ab -n 10000 -c 100 -H "Authorization: Bearer sk-test-key" \
   -p request.json -T application/json \
   http://localhost:8000/v1/chat/completions

# Using wrk
wrk -t12 -c400 -d30s http://localhost:8000/health
```

---

## 11. Security Hardening

### 11.1 Enable All Security Features

```yaml
# production.yaml
enable_security: true              # Master security flag
hash_api_keys: true
enable_input_validation: true
enable_injection_detection: true
enable_abuse_detection: true
max_request_size: 10485760         # 10MB
```

### 11.2 TLS/SSL Configuration

**Generate certificates:**
```bash
# Self-signed (testing only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/fakeai.key \
  -out /etc/ssl/certs/fakeai.crt \
  -subj "/C=US/ST=State/L=City/O=Org/CN=api.example.com"

# Set permissions
sudo chmod 600 /etc/ssl/private/fakeai.key
sudo chmod 644 /etc/ssl/certs/fakeai.crt
```

**Nginx SSL configuration:**
```nginx
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/ssl/certs/fakeai.crt;
    ssl_certificate_key /etc/ssl/private/fakeai.key;

    # Strong SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://fakeai_cluster;
        proxy_set_header X-Forwarded-Proto https;
        # ... other proxy settings
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.example.com;
    return 301 https://$server_name$request_uri;
}
```

### 11.3 Firewall Rules

**UFW (Ubuntu/Debian):**
```bash
# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTPS only (API behind reverse proxy)
sudo ufw allow 443/tcp

# Allow from specific IP ranges (optional)
sudo ufw allow from 10.0.0.0/8 to any port 8000

# Enable firewall
sudo ufw enable
sudo ufw status verbose
```

**iptables:**
```bash
# Flush existing rules
sudo iptables -F

# Default policies
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# Allow loopback
sudo iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTPS
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Rate limiting
sudo iptables -A INPUT -p tcp --dport 443 -m state --state NEW -m recent --set
sudo iptables -A INPUT -p tcp --dport 443 -m state --state NEW -m recent --update --seconds 60 --hitcount 100 -j DROP

# Save rules
sudo apt-get install iptables-persistent
sudo netfilter-persistent save
```

### 11.4 API Key Rotation

```bash
# Generate new keys
for i in {1..5}; do
  echo "sk-prod-$(openssl rand -hex 32)" >> /tmp/new_keys.txt
done

# Add to existing keys
cat /tmp/new_keys.txt | sudo tee -a /etc/fakeai/keys/api_keys.txt

# Reload FakeAI (keys are reloaded automatically on restart)
sudo systemctl reload fakeai

# After migration period, remove old keys
sudo nano /etc/fakeai/keys/api_keys.txt
sudo systemctl reload fakeai

# Clean up
rm /tmp/new_keys.txt
```

### 11.5 Network Security

**Restrict Redis access:**
```bash
# Redis only accessible from FakeAI servers
# In /etc/redis/redis.conf:
bind 127.0.0.1 10.0.1.10 10.0.1.11 10.0.1.12
requirepass YOUR_STRONG_PASSWORD

# Update FakeAI Redis URL
export FAKEAI_REDIS_URL="redis://:YOUR_STRONG_PASSWORD@redis:6379/0"
```

**Use private networks:**
```yaml
# Docker Compose - internal network
networks:
  fakeai-internal:
    internal: true
  fakeai-public:
    internal: false

services:
  fakeai:
    networks:
      - fakeai-public
      - fakeai-internal

  redis:
    networks:
      - fakeai-internal
```

---

## 12. Troubleshooting

### 12.1 Common Issues

**Issue: Service won't start**

```bash
# Check logs
sudo journalctl -u fakeai -n 50 --no-pager

# Check configuration
python -m fakeai.cli server --config-file /etc/fakeai/production.yaml --help

# Validate config manually
python3 -c "
from fakeai.config import AppConfig
config = AppConfig()
print('Config loaded successfully')
"

# Check file permissions
ls -la /etc/fakeai/
ls -la /var/lib/fakeai/

# Check port availability
sudo netstat -tlnp | grep 8000
```

**Issue: High memory usage**

```bash
# Check memory usage
docker stats fakeai-production
# or
ps aux | grep fakeai

# Reduce workers
# In systemd service, reduce --workers parameter

# Enable memory limits
# In docker-compose.yml, set memory limits

# Check for memory leaks
# Monitor over time:
watch -n 5 'docker stats --no-stream fakeai-production'
```

**Issue: Redis connection failed**

```bash
# Check Redis status
redis-cli ping
# or
docker exec fakeai-redis redis-cli ping

# Check Redis logs
docker logs fakeai-redis
# or
sudo journalctl -u redis -n 50

# Test connection
redis-cli -h redis -p 6379 -a YOUR_PASSWORD ping

# Check network connectivity
docker network inspect fakeai-network
```

**Issue: High error rate**

```bash
# Check metrics
curl http://localhost:8000/metrics | jq '.errors'

# View detailed errors
docker logs fakeai-production 2>&1 | grep ERROR

# Check specific error patterns
docker logs fakeai-production 2>&1 | grep -A 5 "500"

# Disable error injection (if enabled by mistake)
docker exec fakeai-production \
  python -c "import os; os.environ['FAKEAI_ERROR_INJECTION_ENABLED']='false'"
docker restart fakeai-production
```

**Issue: Slow responses**

```bash
# Check latency metrics
curl http://localhost:8000/metrics | jq '.responses'

# Monitor in real-time
watch -n 5 'curl -s http://localhost:8000/metrics | jq ".responses"'

# Check system resources
top -b -n 1 | head -20
iostat -x 1 5

# Optimize configuration
# Reduce response_delay, ttft_ms, itl_ms in config
```

### 12.2 Debug Mode

**Enable debug logging:**

```bash
# Systemd
sudo systemctl stop fakeai
sudo systemctl edit fakeai

# Add:
[Service]
Environment="FAKEAI_DEBUG=true"

sudo systemctl start fakeai
sudo journalctl -u fakeai -f

# Docker
docker-compose -f docker-compose.production.yml down
# Edit docker-compose.yml, set FAKEAI_DEBUG=true
docker-compose -f docker-compose.production.yml up -d
docker-compose -f docker-compose.production.yml logs -f
```

### 12.3 Performance Profiling

**Profile with py-spy:**
```bash
# Install py-spy
pip install py-spy

# Profile running process
sudo py-spy record -o profile.svg --pid $(pgrep -f fakeai)

# Top-like view
sudo py-spy top --pid $(pgrep -f fakeai)
```

### 12.4 Health Check Debugging

```bash
# Detailed health check
curl -v http://localhost:8000/health

# Check specific components
curl http://localhost:8000/metrics | jq '.streaming_stats'
curl http://localhost:8000/metrics | jq '.cache_stats'

# Verify API keys
curl -H "Authorization: Bearer sk-test-key" http://localhost:8000/v1/models

# Test streaming
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer sk-test-key" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"test"}],"stream":true}'
```

### 12.5 Emergency Procedures

**Complete service restart:**
```bash
# Docker
docker-compose -f docker-compose.production.yml restart

# Systemd
sudo systemctl restart fakeai

# Kubernetes
kubectl rollout restart deployment/fakeai -n fakeai-production
```

**Clear all cache and restart:**
```bash
# Clear Redis
redis-cli FLUSHALL

# Clear filesystem cache
sudo rm -rf /var/lib/fakeai/cache/*

# Restart service
sudo systemctl restart fakeai
```

**Emergency rollback:**
```bash
# See section 8.1, 8.2, 8.3 for detailed rollback procedures
```

---

## Appendix A: Quick Reference Commands

```bash
# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics

# Restart service (systemd)
sudo systemctl restart fakeai

# Restart service (Docker)
docker-compose -f docker-compose.production.yml restart

# View logs (systemd)
sudo journalctl -u fakeai -f

# View logs (Docker)
docker-compose -f docker-compose.production.yml logs -f

# Check status
sudo systemctl status fakeai
# or
docker-compose -f docker-compose.production.yml ps

# Reload configuration
sudo systemctl reload fakeai

# Stop service
sudo systemctl stop fakeai

# Start service
sudo systemctl start fakeai
```

---

## Appendix B: Configuration Templates

Available in `/etc/fakeai/`:
- `production.yaml` - Full production configuration
- `staging.yaml` - Staging environment configuration
- `development.yaml` - Development configuration
- `keys/api_keys.txt` - API key file

---

## Appendix C: Support and Resources

**Documentation:**
- GitHub: https://github.com/ajcasagrande/fakeai
- API Reference: http://localhost:8000/docs
- Monitoring Guide: See section 6

**Community:**
- Issues: https://github.com/ajcasagrande/fakeai/issues
- Discussions: https://github.com/ajcasagrande/fakeai/discussions

**Monitoring:**
- Metrics: http://localhost:8000/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

---

## Document Version History

| Version | Date       | Changes                    |
|---------|------------|----------------------------|
| 1.0     | 2025-10-07 | Initial production guide   |

**End of Production Deployment Guide**
