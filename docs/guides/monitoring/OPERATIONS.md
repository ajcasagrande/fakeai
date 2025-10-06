# FakeAI Operations Guide

**Version:** 1.0.0
**Last Updated:** October 5, 2025
**Purpose:** Comprehensive guide for deploying, operating, and maintaining FakeAI in production

---

## Table of Contents

1. [Deployment Options](#deployment-options)
2. [Configuration](#configuration)
3. [Monitoring](#monitoring)
4. [Performance Tuning](#performance-tuning)
5. [Troubleshooting](#troubleshooting)
6. [Scaling](#scaling)
7. [Backup and Recovery](#backup-and-recovery)
8. [Security](#security)
9. [Maintenance](#maintenance)

---

## Deployment Options

### 1. Local Development

#### Quick Start
```bash
# Install FakeAI
pip install fakeai

# Start server with default settings
fakeai server

# Or with custom configuration
fakeai server --host 0.0.0.0 --port 8000 --debug
```

#### Development Configuration
```bash
# Fast iteration with auto-reload
fakeai server --debug --response-delay 0.0 --no-random-delay
```

**Use Cases:**
- Local development and testing
- API contract verification
- Integration testing
- Quick prototyping

**Resource Requirements:**
- CPU: 1 core
- Memory: 200-500 MB
- Storage: 50 MB

---

### 2. Docker Deployment

#### Single Container
```bash
# Build image
docker build -t fakeai:latest .

# Run with default settings
docker run -d -p 8000:8000 --name fakeai-server fakeai:latest

# Run with custom configuration
docker run -d -p 8000:8000 \
  -e FAKEAI_HOST=0.0.0.0 \
  -e FAKEAI_PORT=8000 \
  -e FAKEAI_DEBUG=false \
  -e FAKEAI_RESPONSE_DELAY=0.5 \
  --name fakeai-server \
  fakeai:latest

# Check logs
docker logs -f fakeai-server

# Health check
curl http://localhost:8000/health
```

#### Docker Compose Setup

**Basic Configuration (docker-compose.yml):**
```yaml
services:
  fakeai:
    build:
      context: .
      dockerfile: Dockerfile
    image: fakeai:latest
    container_name: fakeai-server
    ports:
      - "8000:8000"
    environment:
      # Server Configuration
      - FAKEAI_HOST=0.0.0.0
      - FAKEAI_PORT=8000
      - FAKEAI_DEBUG=false

      # Response Simulation
      - FAKEAI_RESPONSE_DELAY=0.5
      - FAKEAI_RANDOM_DELAY=true
      - FAKEAI_MAX_VARIANCE=0.3

      # Authentication
      - FAKEAI_REQUIRE_API_KEY=true
      - FAKEAI_API_KEYS=sk-key-1,sk-key-2

      # Rate Limiting
      - FAKEAI_RATE_LIMIT_ENABLED=true
      - FAKEAI_RATE_LIMIT_TIER=tier-1

      # KV Cache
      - FAKEAI_KV_CACHE_ENABLED=true
      - FAKEAI_KV_CACHE_BLOCK_SIZE=16
      - FAKEAI_KV_CACHE_NUM_WORKERS=4

    volumes:
      # Optional: Mount config files
      - ./config:/app/config:ro
      # Optional: Mount logs
      - ./logs:/app/logs

    networks:
      - fakeai-network

    restart: unless-stopped

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

networks:
  fakeai-network:
    driver: bridge
```

**Production Configuration with Redis:**
```yaml
services:
  fakeai:
    image: fakeai:latest
    ports:
      - "8000:8000"
    environment:
      - FAKEAI_HOST=0.0.0.0
      - FAKEAI_PORT=8000
      - FAKEAI_REQUIRE_API_KEY=true
      - FAKEAI_API_KEYS=sk-prod-key-1,sk-prod-key-2
      - FAKEAI_RATE_LIMIT_ENABLED=true
      - FAKEAI_RATE_LIMIT_TIER=tier-3
    depends_on:
      - redis
    networks:
      - fakeai-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - fakeai-network
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru

networks:
  fakeai-network:
    driver: bridge

volumes:
  redis-data:
    driver: local
```

**Commands:**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f fakeai

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Clean up volumes
docker-compose down -v
```

**Resource Requirements:**
- CPU: 2 cores
- Memory: 1-2 GB
- Storage: 500 MB

---

### 3. Kubernetes Deployment

#### Namespace Setup
```bash
kubectl create namespace fakeai
```

#### ConfigMap for Configuration
```yaml
# fakeai-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fakeai-config
  namespace: fakeai
data:
  FAKEAI_HOST: "0.0.0.0"
  FAKEAI_PORT: "8000"
  FAKEAI_DEBUG: "false"
  FAKEAI_RESPONSE_DELAY: "0.5"
  FAKEAI_RANDOM_DELAY: "true"
  FAKEAI_MAX_VARIANCE: "0.3"
  FAKEAI_KV_CACHE_ENABLED: "true"
  FAKEAI_KV_CACHE_BLOCK_SIZE: "16"
  FAKEAI_KV_CACHE_NUM_WORKERS: "4"
  FAKEAI_RATE_LIMIT_ENABLED: "true"
  FAKEAI_RATE_LIMIT_TIER: "tier-3"
```

#### Secret for API Keys
```yaml
# fakeai-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: fakeai-secrets
  namespace: fakeai
type: Opaque
stringData:
  FAKEAI_API_KEYS: "sk-prod-key-1,sk-prod-key-2,sk-prod-key-3"
  FAKEAI_REQUIRE_API_KEY: "true"
```

#### Deployment
```yaml
# fakeai-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fakeai
  namespace: fakeai
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
    spec:
      containers:
      - name: fakeai
        image: fakeai:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        envFrom:
        - configMapRef:
            name: fakeai-config
        - secretRef:
            name: fakeai-secrets
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 2
```

#### Service
```yaml
# fakeai-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: fakeai
  namespace: fakeai
  labels:
    app: fakeai
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: fakeai
```

#### Ingress
```yaml
# fakeai-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fakeai
  namespace: fakeai
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - fakeai.example.com
    secretName: fakeai-tls
  rules:
  - host: fakeai.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: fakeai
            port:
              number: 8000
```

#### Horizontal Pod Autoscaler (HPA)
```yaml
# fakeai-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fakeai-hpa
  namespace: fakeai
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fakeai
  minReplicas: 3
  maxReplicas: 10
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
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
```

#### Deploy to Kubernetes
```bash
# Create namespace
kubectl create namespace fakeai

# Apply configurations
kubectl apply -f fakeai-configmap.yaml
kubectl apply -f fakeai-secret.yaml
kubectl apply -f fakeai-deployment.yaml
kubectl apply -f fakeai-service.yaml
kubectl apply -f fakeai-ingress.yaml
kubectl apply -f fakeai-hpa.yaml

# Verify deployment
kubectl get pods -n fakeai
kubectl get svc -n fakeai
kubectl get ingress -n fakeai

# View logs
kubectl logs -f deployment/fakeai -n fakeai

# Scale manually
kubectl scale deployment fakeai --replicas=5 -n fakeai

# Check HPA status
kubectl get hpa -n fakeai
```

**Resource Requirements (per pod):**
- CPU: 500m (request), 2000m (limit)
- Memory: 512 Mi (request), 2 Gi (limit)
- Storage: 1 Gi

---

### 4. Systemd Service (Linux)

#### Create Service File
```bash
sudo tee /etc/systemd/system/fakeai.service > /dev/null <<EOF
[Unit]
Description=FakeAI OpenAI-Compatible API Server
After=network.target

[Service]
Type=simple
User=fakeai
Group=fakeai
WorkingDirectory=/opt/fakeai
Environment="FAKEAI_HOST=0.0.0.0"
Environment="FAKEAI_PORT=8000"
Environment="FAKEAI_DEBUG=false"
Environment="FAKEAI_RESPONSE_DELAY=0.5"
Environment="FAKEAI_REQUIRE_API_KEY=true"
Environment="FAKEAI_API_KEYS=sk-key-1,sk-key-2"
Environment="FAKEAI_RATE_LIMIT_ENABLED=true"
Environment="FAKEAI_RATE_LIMIT_TIER=tier-3"
Environment="FAKEAI_KV_CACHE_ENABLED=true"
ExecStart=/usr/local/bin/fakeai server
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

#### Create User and Setup
```bash
# Create dedicated user
sudo useradd -r -s /bin/false fakeai

# Create working directory
sudo mkdir -p /opt/fakeai
sudo chown fakeai:fakeai /opt/fakeai

# Install FakeAI
sudo pip install fakeai
```

#### Manage Service
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable fakeai

# Start service
sudo systemctl start fakeai

# Check status
sudo systemctl status fakeai

# View logs
sudo journalctl -u fakeai -f

# Restart service
sudo systemctl restart fakeai

# Stop service
sudo systemctl stop fakeai

# Disable service (don't start on boot)
sudo systemctl disable fakeai
```

**Resource Requirements:**
- CPU: 1-2 cores
- Memory: 500 MB - 1 GB
- Storage: 100 MB

---

### 5. PM2 Process Manager (Node.js)

#### Install PM2
```bash
npm install -g pm2
```

#### Create Ecosystem File
```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'fakeai',
    script: 'fakeai',
    args: 'server --host 0.0.0.0 --port 8000',
    instances: 4,
    exec_mode: 'cluster',
    env: {
      FAKEAI_HOST: '0.0.0.0',
      FAKEAI_PORT: '8000',
      FAKEAI_DEBUG: 'false',
      FAKEAI_RESPONSE_DELAY: '0.5',
      FAKEAI_RANDOM_DELAY: 'true',
      FAKEAI_REQUIRE_API_KEY: 'true',
      FAKEAI_API_KEYS: 'sk-key-1,sk-key-2',
      FAKEAI_RATE_LIMIT_ENABLED: 'true',
      FAKEAI_RATE_LIMIT_TIER: 'tier-3',
      FAKEAI_KV_CACHE_ENABLED: 'true',
      FAKEAI_KV_CACHE_NUM_WORKERS: '4',
    },
    max_memory_restart: '1G',
    error_file: './logs/fakeai-error.log',
    out_file: './logs/fakeai-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
  }]
}
```

#### Manage with PM2
```bash
# Start application
pm2 start ecosystem.config.js

# List processes
pm2 list

# Monitor processes
pm2 monit

# View logs
pm2 logs fakeai

# Restart application
pm2 restart fakeai

# Stop application
pm2 stop fakeai

# Delete application
pm2 delete fakeai

# Save process list
pm2 save

# Setup startup script
pm2 startup
# Follow the instructions printed by pm2

# Reload configuration
pm2 reload ecosystem.config.js
```

**Resource Requirements:**
- CPU: 4 cores (with 4 instances)
- Memory: 2-4 GB (500 MB per instance)
- Storage: 500 MB

---

## Configuration

### Environment Variables Reference

#### Server Settings
```bash
FAKEAI_HOST=0.0.0.0              # Host to bind (default: 127.0.0.1)
FAKEAI_PORT=8000                 # Port to bind (default: 8000)
FAKEAI_DEBUG=false               # Debug mode (default: false)
```

#### Response Timing
```bash
FAKEAI_RESPONSE_DELAY=0.5        # Base delay in seconds (default: 0.5)
FAKEAI_RANDOM_DELAY=true         # Random variation (default: true)
FAKEAI_MAX_VARIANCE=0.3          # Max variance factor (default: 0.3)
```

#### Authentication
```bash
FAKEAI_REQUIRE_API_KEY=true      # Require API keys (default: false)
FAKEAI_API_KEYS=key1,key2        # Comma-separated keys
FAKEAI_HASH_API_KEYS=false       # Hash keys for storage (default: false)
```

#### Rate Limiting
```bash
FAKEAI_RATE_LIMIT_ENABLED=true   # Enable rate limiting (default: false)
FAKEAI_RATE_LIMIT_TIER=tier-1    # Tier: free, tier-1 to tier-5
FAKEAI_RATE_LIMIT_RPM=500        # Custom requests per minute
FAKEAI_RATE_LIMIT_TPM=30000      # Custom tokens per minute
```

#### KV Cache Settings
```bash
FAKEAI_KV_CACHE_ENABLED=true     # Enable KV cache (default: true)
FAKEAI_KV_CACHE_BLOCK_SIZE=16    # Block size in tokens (default: 16)
FAKEAI_KV_CACHE_NUM_WORKERS=4    # Number of workers (default: 4)
FAKEAI_KV_OVERLAP_WEIGHT=1.0     # Overlap weight (default: 1.0)
```

#### Prompt Caching
```bash
FAKEAI_ENABLE_PROMPT_CACHING=true  # Enable prompt caching
FAKEAI_CACHE_TTL_SECONDS=600       # Cache TTL (default: 600)
FAKEAI_MIN_TOKENS_FOR_CACHE=1024   # Min tokens to cache (default: 1024)
```

#### Security Settings
```bash
FAKEAI_ENABLE_SECURITY=false            # Master security flag (default: false)
FAKEAI_ENABLE_INPUT_VALIDATION=false    # Input validation (default: false)
FAKEAI_ENABLE_INJECTION_DETECTION=false # Injection detection (default: false)
FAKEAI_ENABLE_ABUSE_DETECTION=false     # IP abuse detection (default: false)
FAKEAI_MAX_REQUEST_SIZE=104857600       # Max request size (default: 100MB)
```

#### Safety Features
```bash
FAKEAI_ENABLE_MODERATION=false          # Content moderation (default: false)
FAKEAI_MODERATION_THRESHOLD=0.5         # Moderation threshold (default: 0.5)
FAKEAI_ENABLE_REFUSALS=false            # Refusal responses (default: false)
FAKEAI_ENABLE_SAFETY_FEATURES=false     # Safety features (default: false)
FAKEAI_ENABLE_JAILBREAK_DETECTION=false # Jailbreak detection (default: false)
```

#### Audio Settings
```bash
FAKEAI_ENABLE_AUDIO=true               # Enable audio (default: true)
FAKEAI_DEFAULT_VOICE=alloy             # Default voice (default: alloy)
FAKEAI_DEFAULT_AUDIO_FORMAT=mp3        # Audio format (default: mp3)
```

#### Embedding Settings
```bash
FAKEAI_USE_SEMANTIC_EMBEDDINGS=false   # Use semantic embeddings (default: false)
FAKEAI_EMBEDDING_MODEL=all-MiniLM-L6-v2 # Sentence transformer model
```

#### Streaming Settings
```bash
FAKEAI_STREAM_TIMEOUT_SECONDS=300.0           # Stream timeout (default: 300)
FAKEAI_STREAM_TOKEN_TIMEOUT_SECONDS=30.0      # Token timeout (default: 30)
FAKEAI_STREAM_KEEPALIVE_ENABLED=true          # Keepalive (default: true)
FAKEAI_STREAM_KEEPALIVE_INTERVAL_SECONDS=15.0 # Keepalive interval (default: 15)
```

#### Context Validation
```bash
FAKEAI_ENABLE_CONTEXT_VALIDATION=false  # Context validation (default: false)
FAKEAI_STRICT_TOKEN_COUNTING=false      # Strict token counting (default: false)
```

#### Error Injection (Testing)
```bash
FAKEAI_ERROR_INJECTION_ENABLED=false    # Enable error injection (default: false)
FAKEAI_ERROR_INJECTION_RATE=0.15        # Global error rate (default: 0.0)
FAKEAI_ERROR_INJECTION_TYPES='["internal_error","service_unavailable"]'
```

#### CORS Settings
```bash
FAKEAI_CORS_ALLOWED_ORIGINS='["*"]'     # Allowed origins (default: ["*"])
FAKEAI_CORS_ALLOW_CREDENTIALS=true      # Allow credentials (default: true)
```

#### Image Generation
```bash
FAKEAI_GENERATE_ACTUAL_IMAGES=false     # Generate actual images (default: false)
```

#### Metrics and Monitoring
```bash
FAKEAI_METRICS_ENABLED=true             # Enable metrics (default: true)
FAKEAI_METRICS_WINDOW_SIZE=300          # Metrics window (default: 300s)
```

#### Latency Configuration
```bash
FAKEAI_TTFT_MS=20                       # Time to first token (default: 20ms)
FAKEAI_TTFT_VARIANCE_PCT=10             # TTFT variance (default: 10%)
FAKEAI_ITL_MS=5                         # Inter-token latency (default: 5ms)
FAKEAI_ITL_VARIANCE_PCT=10              # ITL variance (default: 10%)
```

### Configuration Profiles

#### Development Profile
```bash
export FAKEAI_DEBUG=true
export FAKEAI_RESPONSE_DELAY=0.0
export FAKEAI_RANDOM_DELAY=false
export FAKEAI_REQUIRE_API_KEY=false
export FAKEAI_RATE_LIMIT_ENABLED=false
export FAKEAI_KV_CACHE_ENABLED=false
export FAKEAI_ENABLE_SECURITY=false
export FAKEAI_ENABLE_MODERATION=false
```

#### Testing Profile
```bash
export FAKEAI_DEBUG=false
export FAKEAI_RESPONSE_DELAY=0.1
export FAKEAI_RANDOM_DELAY=true
export FAKEAI_MAX_VARIANCE=0.2
export FAKEAI_REQUIRE_API_KEY=true
export FAKEAI_API_KEYS=sk-test-key
export FAKEAI_RATE_LIMIT_ENABLED=true
export FAKEAI_RATE_LIMIT_TIER=tier-1
export FAKEAI_ERROR_INJECTION_ENABLED=true
export FAKEAI_ERROR_INJECTION_RATE=0.05
```

#### Production Profile
```bash
export FAKEAI_HOST=0.0.0.0
export FAKEAI_PORT=8000
export FAKEAI_DEBUG=false
export FAKEAI_RESPONSE_DELAY=0.5
export FAKEAI_RANDOM_DELAY=true
export FAKEAI_MAX_VARIANCE=0.3
export FAKEAI_REQUIRE_API_KEY=true
export FAKEAI_API_KEYS=sk-prod-key-1,sk-prod-key-2,sk-prod-key-3
export FAKEAI_RATE_LIMIT_ENABLED=true
export FAKEAI_RATE_LIMIT_TIER=tier-3
export FAKEAI_KV_CACHE_ENABLED=true
export FAKEAI_KV_CACHE_BLOCK_SIZE=16
export FAKEAI_KV_CACHE_NUM_WORKERS=4
export FAKEAI_ENABLE_PROMPT_CACHING=true
export FAKEAI_ENABLE_SECURITY=true
export FAKEAI_ENABLE_INPUT_VALIDATION=true
export FAKEAI_ENABLE_ABUSE_DETECTION=true
export FAKEAI_ENABLE_MODERATION=true
export FAKEAI_METRICS_ENABLED=true
```

### Configuration Files

#### YAML Configuration (config.yaml)
```yaml
server:
  host: 0.0.0.0
  port: 8000
  debug: false

response:
  delay: 0.5
  random_delay: true
  max_variance: 0.3

authentication:
  require_api_key: true
  api_keys:
    - sk-key-1
    - sk-key-2
  hash_api_keys: false

rate_limiting:
  enabled: true
  tier: tier-3
  rpm: 10000
  tpm: 1000000

kv_cache:
  enabled: true
  block_size: 16
  num_workers: 4
  overlap_weight: 1.0

security:
  enable_security: true
  enable_input_validation: true
  enable_injection_detection: true
  enable_abuse_detection: true
  max_request_size: 104857600

monitoring:
  metrics_enabled: true
  metrics_window_size: 300
```

#### JSON Configuration (config.json)
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": false
  },
  "response": {
    "delay": 0.5,
    "random_delay": true,
    "max_variance": 0.3
  },
  "authentication": {
    "require_api_key": true,
    "api_keys": ["sk-key-1", "sk-key-2"],
    "hash_api_keys": false
  },
  "rate_limiting": {
    "enabled": true,
    "tier": "tier-3",
    "rpm": 10000,
    "tpm": 1000000
  },
  "kv_cache": {
    "enabled": true,
    "block_size": 16,
    "num_workers": 4,
    "overlap_weight": 1.0
  }
}
```

---

## Monitoring

### Metrics Endpoints

#### 1. Health Check
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-05T12:00:00Z",
  "uptime": 3600.5,
  "version": "0.0.5"
}
```

#### 2. JSON Metrics
```bash
curl http://localhost:8000/metrics
```

**Response:**
```json
{
  "requests": {
    "/v1/chat/completions": {
      "rate": 10.5,
      "count": 1250,
      "avg": 0.123,
      "min": 0.085,
      "max": 0.450,
      "p50": 0.120,
      "p90": 0.180,
      "p99": 0.230
    }
  },
  "responses": {
    "200": 1240,
    "400": 5,
    "429": 3,
    "500": 2
  },
  "tokens": {
    "total": 125000,
    "prompt": 75000,
    "completion": 50000,
    "rate": 125.5
  },
  "errors": {
    "total": 10,
    "by_type": {
      "validation_error": 5,
      "rate_limit": 3,
      "internal_error": 2
    }
  },
  "streaming_stats": {
    "active_streams": 5,
    "completed_streams": 125,
    "failed_streams": 2,
    "ttft": {
      "avg": 0.020,
      "min": 0.015,
      "max": 0.035,
      "p50": 0.019,
      "p90": 0.028,
      "p99": 0.033
    },
    "tokens_per_second": {
      "avg": 45.2,
      "min": 20.1,
      "max": 85.3,
      "p50": 44.8,
      "p90": 65.2,
      "p99": 78.9
    }
  },
  "kv_cache": {
    "hit_rate": 0.85,
    "token_reuse_rate": 0.72,
    "avg_prefix_length": 1024,
    "total_lookups": 1000,
    "cache_hits": 850
  }
}
```

#### 3. Prometheus Metrics
```bash
curl http://localhost:8000/metrics/prometheus
```

**Response:**
```
# HELP fakeai_requests_per_second Request rate per endpoint
# TYPE fakeai_requests_per_second gauge
fakeai_requests_per_second{endpoint="/v1/chat/completions"} 10.500000

# HELP fakeai_latency_seconds Response latency in seconds
# TYPE fakeai_latency_seconds summary
fakeai_latency_seconds{endpoint="/v1/chat/completions",quantile="0.5"} 0.120000
fakeai_latency_seconds{endpoint="/v1/chat/completions",quantile="0.9"} 0.180000
fakeai_latency_seconds{endpoint="/v1/chat/completions",quantile="0.99"} 0.230000

# HELP fakeai_ttft_seconds Time to first token in seconds
# TYPE fakeai_ttft_seconds summary
fakeai_ttft_seconds{quantile="0.5"} 0.019000
fakeai_ttft_seconds{quantile="0.9"} 0.028000
fakeai_ttft_seconds{quantile="0.99"} 0.033000

# HELP fakeai_kv_cache_hit_rate KV cache hit rate
# TYPE fakeai_kv_cache_hit_rate gauge
fakeai_kv_cache_hit_rate 0.850000
```

#### 4. KV Cache Metrics
```bash
curl http://localhost:8000/kv-cache/metrics
```

**Response:**
```json
{
  "cache_performance": {
    "hit_rate": 0.85,
    "token_reuse_rate": 0.72,
    "avg_prefix_length": 1024,
    "total_lookups": 1000,
    "cache_hits": 850,
    "by_endpoint": {
      "/v1/chat/completions": {
        "hit_rate": 0.87,
        "lookups": 950
      }
    }
  },
  "smart_router": {
    "worker_stats": {
      "worker_0": {
        "active_requests": 2,
        "cached_blocks": 1024,
        "total_tokens_processed": 150000
      }
    }
  }
}
```

#### 5. DCGM GPU Metrics (if enabled)
```bash
curl http://localhost:8000/dcgm/metrics
```

**Response:**
```
# HELP dcgm_gpu_utilization GPU utilization percentage
# TYPE dcgm_gpu_utilization gauge
dcgm_gpu_utilization{gpu="0"} 85.5

# HELP dcgm_memory_used GPU memory used in bytes
# TYPE dcgm_memory_used gauge
dcgm_memory_used{gpu="0"} 12884901888
```

#### 6. Real-Time Metrics Streaming (WebSocket)
```python
import asyncio
import websockets
import json

async def stream_metrics():
    uri = "ws://localhost:8000/metrics/streaming"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            metrics = json.loads(message)
            print(f"Requests/s: {metrics['requests_per_second']}")
            print(f"Avg Latency: {metrics['avg_latency_ms']}ms")

asyncio.run(stream_metrics())
```

### Prometheus Integration

#### Prometheus Configuration (prometheus.yml)
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'fakeai'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics/prometheus'
    scrape_interval: 10s
    scrape_timeout: 5s
```

#### Docker Compose with Prometheus
```yaml
services:
  fakeai:
    image: fakeai:latest
    ports:
      - "8000:8000"
    networks:
      - monitoring

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana-dashboards:/etc/grafana/provisioning/dashboards
    depends_on:
      - prometheus
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus-data:
  grafana-data:
```

### Grafana Dashboard Examples

#### Dashboard JSON (fakeai-dashboard.json)
```json
{
  "dashboard": {
    "title": "FakeAI Monitoring",
    "panels": [
      {
        "title": "Requests Per Second",
        "targets": [
          {
            "expr": "fakeai_requests_per_second"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Latency (p50, p90, p99)",
        "targets": [
          {
            "expr": "fakeai_latency_seconds{quantile=\"0.5\"}"
          },
          {
            "expr": "fakeai_latency_seconds{quantile=\"0.9\"}"
          },
          {
            "expr": "fakeai_latency_seconds{quantile=\"0.99\"}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "KV Cache Hit Rate",
        "targets": [
          {
            "expr": "fakeai_kv_cache_hit_rate"
          }
        ],
        "type": "gauge"
      }
    ]
  }
}
```

### Alerting Setup

#### Prometheus Alerts (alerts.yml)
```yaml
groups:
  - name: fakeai_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(fakeai_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      # High latency
      - alert: HighLatency
        expr: fakeai_latency_seconds{quantile="0.99"} > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High p99 latency"
          description: "p99 latency is {{ $value }}s"

      # Low cache hit rate
      - alert: LowCacheHitRate
        expr: fakeai_kv_cache_hit_rate < 0.5
        for: 10m
        labels:
          severity: info
        annotations:
          summary: "Low KV cache hit rate"
          description: "Cache hit rate is {{ $value }}"

      # Service down
      - alert: ServiceDown
        expr: up{job="fakeai"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "FakeAI service is down"
```

### Log Aggregation

#### Fluentd Configuration
```
<source>
  @type tail
  path /var/log/fakeai/*.log
  pos_file /var/log/td-agent/fakeai.pos
  tag fakeai.*
  <parse>
    @type json
    time_key timestamp
    time_format %Y-%m-%dT%H:%M:%S.%LZ
  </parse>
</source>

<match fakeai.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name fakeai
  type_name _doc
  logstash_format true
  logstash_prefix fakeai
  <buffer>
    flush_interval 5s
  </buffer>
</match>
```

---

## Performance Tuning

### Worker Count Optimization

#### Calculate Optimal Workers
```bash
# Formula: (2 × CPU_CORES) + 1
CPU_CORES=$(nproc)
WORKERS=$((2 * CPU_CORES + 1))

# Start with calculated workers
uvicorn fakeai.app:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers $WORKERS
```

#### For Different Workloads
- **CPU-bound:** workers = CPU cores
- **I/O-bound:** workers = (2 × CPU cores) + 1
- **Mixed:** workers = 1.5 × CPU cores

### Memory Allocation

#### Docker Memory Limits
```bash
# Set memory limits
docker run -d \
  -m 2g \
  --memory-reservation 1g \
  --memory-swap 3g \
  fakeai:latest
```

#### Kubernetes Resource Limits
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

### Cache Sizing

#### KV Cache Configuration
```bash
# For high-throughput workloads
export FAKEAI_KV_CACHE_ENABLED=true
export FAKEAI_KV_CACHE_BLOCK_SIZE=16    # Smaller blocks = more granular
export FAKEAI_KV_CACHE_NUM_WORKERS=8    # Match CPU cores
export FAKEAI_KV_OVERLAP_WEIGHT=1.5     # Aggressive caching

# For low-latency workloads
export FAKEAI_KV_CACHE_BLOCK_SIZE=32    # Larger blocks = faster
export FAKEAI_KV_CACHE_NUM_WORKERS=4    # Fewer workers
export FAKEAI_KV_OVERLAP_WEIGHT=0.8     # Conservative caching
```

#### Prompt Cache Configuration
```bash
# High cache utilization
export FAKEAI_ENABLE_PROMPT_CACHING=true
export FAKEAI_CACHE_TTL_SECONDS=1800      # 30 minutes
export FAKEAI_MIN_TOKENS_FOR_CACHE=512    # Cache more prompts

# Low memory footprint
export FAKEAI_CACHE_TTL_SECONDS=300       # 5 minutes
export FAKEAI_MIN_TOKENS_FOR_CACHE=2048   # Cache fewer prompts
```

### Timeout Configuration

```bash
# Streaming timeouts
export FAKEAI_STREAM_TIMEOUT_SECONDS=600.0         # Total stream timeout
export FAKEAI_STREAM_TOKEN_TIMEOUT_SECONDS=60.0    # Per-token timeout
export FAKEAI_STREAM_KEEPALIVE_INTERVAL_SECONDS=30.0

# HTTP timeouts (uvicorn)
uvicorn fakeai.app:app \
  --timeout-keep-alive 60 \
  --timeout-graceful-shutdown 30
```

### Concurrency Limits

#### Rate Limiting Tiers
```bash
# Tier comparison
# free:    60 RPM,      10K TPM
# tier-1:  500 RPM,     30K TPM
# tier-2:  5K RPM,      450K TPM
# tier-3:  10K RPM,     1M TPM
# tier-4:  30K RPM,     5M TPM
# tier-5:  100K RPM,    15M TPM

# Set tier based on expected load
export FAKEAI_RATE_LIMIT_TIER=tier-3
```

#### Custom Rate Limits
```bash
# Override tier with custom limits
export FAKEAI_RATE_LIMIT_RPM=20000
export FAKEAI_RATE_LIMIT_TPM=2000000
```

### Response Timing Optimization

#### Fast Mode (Benchmarking)
```bash
export FAKEAI_RESPONSE_DELAY=0.0
export FAKEAI_RANDOM_DELAY=false
export FAKEAI_TTFT_MS=1
export FAKEAI_ITL_MS=1
```

#### Realistic Mode (Testing)
```bash
export FAKEAI_RESPONSE_DELAY=0.5
export FAKEAI_RANDOM_DELAY=true
export FAKEAI_MAX_VARIANCE=0.3
export FAKEAI_TTFT_MS=20
export FAKEAI_TTFT_VARIANCE_PCT=10
export FAKEAI_ITL_MS=5
export FAKEAI_ITL_VARIANCE_PCT=10
```

---

## Troubleshooting

### Common Issues

#### Issue 1: High Latency

**Symptoms:**
- Slow response times
- High p99 latency
- Client timeouts

**Diagnosis:**
```bash
# Check metrics
curl http://localhost:8000/metrics | jq '.requests'

# Check system resources
top
free -h
iostat -x 1

# Check network latency
ping localhost
```

**Solutions:**
```bash
# Reduce response delay
export FAKEAI_RESPONSE_DELAY=0.1

# Disable random delays
export FAKEAI_RANDOM_DELAY=false

# Increase workers
export WORKERS=$((2 * $(nproc) + 1))

# Enable KV cache
export FAKEAI_KV_CACHE_ENABLED=true
export FAKEAI_KV_CACHE_NUM_WORKERS=$(nproc)

# Restart service
systemctl restart fakeai
```

#### Issue 2: High Memory Usage

**Symptoms:**
- OOM kills
- Swap usage
- Slow performance

**Diagnosis:**
```bash
# Check memory usage
free -h
docker stats fakeai-server

# Check process memory
ps aux | grep fakeai

# Check metrics
curl http://localhost:8000/metrics | jq '.memory'
```

**Solutions:**
```bash
# Reduce cache TTL
export FAKEAI_CACHE_TTL_SECONDS=300

# Increase min tokens for cache
export FAKEAI_MIN_TOKENS_FOR_CACHE=2048

# Reduce KV cache workers
export FAKEAI_KV_CACHE_NUM_WORKERS=2

# Set memory limits (Docker)
docker update --memory 2g --memory-swap 3g fakeai-server

# Restart service
systemctl restart fakeai
```

#### Issue 3: Rate Limiting Errors

**Symptoms:**
- 429 Too Many Requests
- Clients being throttled
- High retry rates

**Diagnosis:**
```bash
# Check rate limiter metrics
curl http://localhost:8000/metrics | jq '.rate_limiting'

# Check logs
journalctl -u fakeai | grep "rate limit"
docker logs fakeai-server | grep "rate limit"
```

**Solutions:**
```bash
# Increase rate limits
export FAKEAI_RATE_LIMIT_TIER=tier-4
# Or set custom limits
export FAKEAI_RATE_LIMIT_RPM=50000
export FAKEAI_RATE_LIMIT_TPM=10000000

# Disable rate limiting (testing only)
export FAKEAI_RATE_LIMIT_ENABLED=false

# Restart service
systemctl restart fakeai
```

#### Issue 4: Authentication Failures

**Symptoms:**
- 401 Unauthorized
- Invalid API key errors
- Authentication required errors

**Diagnosis:**
```bash
# Check API key configuration
echo $FAKEAI_API_KEYS

# Check logs
journalctl -u fakeai | grep "auth"

# Test with known key
curl -H "Authorization: Bearer sk-test-key" \
  http://localhost:8000/v1/models
```

**Solutions:**
```bash
# Verify API keys are set
export FAKEAI_REQUIRE_API_KEY=true
export FAKEAI_API_KEYS=sk-key-1,sk-key-2

# Disable authentication (testing only)
export FAKEAI_REQUIRE_API_KEY=false

# Restart service
systemctl restart fakeai
```

#### Issue 5: Service Won't Start

**Symptoms:**
- Service fails to start
- Port already in use
- Configuration errors

**Diagnosis:**
```bash
# Check service status
systemctl status fakeai

# Check logs
journalctl -u fakeai -n 50

# Check port availability
netstat -tulpn | grep 8000
lsof -i :8000

# Test configuration
fakeai server --debug
```

**Solutions:**
```bash
# Kill process on port
sudo kill $(lsof -t -i:8000)

# Change port
export FAKEAI_PORT=8001

# Check configuration syntax
fakeai server --help

# Run in foreground for debugging
fakeai server --debug
```

### Debug Mode

#### Enable Debug Logging
```bash
# CLI
fakeai server --debug

# Environment variable
export FAKEAI_DEBUG=true

# Python logging
export PYTHONUNBUFFERED=1
export LOG_LEVEL=DEBUG
```

#### Verbose Output
```bash
# Enable verbose logging
uvicorn fakeai.app:app --log-level debug

# Log to file
fakeai server --debug > fakeai.log 2>&1
```

### Log Analysis

#### Common Log Patterns
```bash
# Find errors
journalctl -u fakeai | grep -i error

# Find rate limit issues
journalctl -u fakeai | grep "rate limit"

# Find authentication issues
journalctl -u fakeai | grep "unauthorized"

# Find slow requests
journalctl -u fakeai | grep "latency" | awk '$NF > 1.0'

# Count requests by endpoint
journalctl -u fakeai | grep "GET\|POST" | cut -d' ' -f7 | sort | uniq -c
```

### Performance Debugging

#### CPU Profiling
```python
# Add profiling to server
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# ... run server ...

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

#### Memory Profiling
```python
# Install memory_profiler
pip install memory_profiler

# Profile memory usage
from memory_profiler import profile

@profile
def my_endpoint():
    # ... endpoint logic ...
    pass
```

#### Request Tracing
```bash
# Enable request tracing
export FAKEAI_DEBUG=true

# Trace specific endpoints
curl -v http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "test"}]}'
```

---

## Scaling

### Horizontal Scaling Strategies

#### 1. Load Balancer Setup

**Nginx Configuration:**
```nginx
upstream fakeai_backend {
    least_conn;  # Load balancing method

    server fakeai-1:8000 max_fails=3 fail_timeout=30s;
    server fakeai-2:8000 max_fails=3 fail_timeout=30s;
    server fakeai-3:8000 max_fails=3 fail_timeout=30s;

    keepalive 32;
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://fakeai_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;

        # Buffering
        proxy_buffering off;
        proxy_request_buffering off;
    }

    location /health {
        access_log off;
        proxy_pass http://fakeai_backend/health;
    }
}
```

**HAProxy Configuration:**
```
global
    maxconn 4096
    daemon

defaults
    mode http
    timeout connect 5s
    timeout client 300s
    timeout server 300s
    option httplog
    option dontlognull

frontend fakeai_frontend
    bind *:80
    default_backend fakeai_backend

backend fakeai_backend
    balance leastconn
    option httpchk GET /health

    server fakeai-1 fakeai-1:8000 check inter 5s fall 3 rise 2
    server fakeai-2 fakeai-2:8000 check inter 5s fall 3 rise 2
    server fakeai-3 fakeai-3:8000 check inter 5s fall 3 rise 2
```

#### 2. Multi-Instance Deployment

**Docker Compose Scale:**
```bash
# Scale to 5 instances
docker-compose up -d --scale fakeai=5

# Verify instances
docker-compose ps
```

**Kubernetes Scale:**
```bash
# Scale deployment
kubectl scale deployment fakeai --replicas=10 -n fakeai

# Enable autoscaling
kubectl autoscale deployment fakeai \
  --cpu-percent=70 \
  --min=3 \
  --max=10 \
  -n fakeai
```

### Resource Requirements

#### Per Instance Requirements

**Small (Development):**
- CPU: 1 core
- Memory: 512 MB
- Throughput: ~100 req/s
- Use case: Dev/test environments

**Medium (Testing):**
- CPU: 2 cores
- Memory: 1 GB
- Throughput: ~500 req/s
- Use case: Integration testing, staging

**Large (Production):**
- CPU: 4 cores
- Memory: 2 GB
- Throughput: ~1000 req/s
- Use case: Production workloads

**Extra Large (High Load):**
- CPU: 8 cores
- Memory: 4 GB
- Throughput: ~2000 req/s
- Use case: High-traffic production

#### Capacity Planning

**Calculate Required Instances:**
```python
# Expected load
expected_rps = 5000  # requests per second

# Instance capacity
instance_capacity = 1000  # req/s per instance

# Calculate instances
min_instances = expected_rps / instance_capacity
recommended_instances = min_instances * 1.5  # 50% headroom

# Result
print(f"Minimum instances: {min_instances}")
print(f"Recommended instances: {recommended_instances}")
```

**Example Calculations:**
- 100 req/s → 1 instance (small)
- 500 req/s → 1-2 instances (medium)
- 1000 req/s → 2-3 instances (large)
- 5000 req/s → 8-10 instances (large)
- 10000 req/s → 15-20 instances (large)

### Multi-Region Deployment

#### Architecture
```
                    
                      Global DNS 
                      (Route 53) 
                    
                           
            
                                        
          
        US-EAST     US-WEST       EU     
        Region       Region      Region  
          
                                        
          
         ALB          ALB         ALB    
          
                                        
          
       FakeAI x3   FakeAI x3   FakeAI x3 
          
```

#### Deployment Regions
- **US-EAST-1**: Primary region
- **US-WEST-2**: Secondary region
- **EU-CENTRAL-1**: Europe region
- **AP-SOUTHEAST-1**: Asia region

---

## Backup and Recovery

### State Persistence

#### Metrics Persistence
```bash
# Enable metrics persistence
export FAKEAI_METRICS_PERSISTENCE_ENABLED=true
export FAKEAI_METRICS_DB_PATH=/var/lib/fakeai/metrics.db

# Backup metrics database
cp /var/lib/fakeai/metrics.db /backup/metrics-$(date +%Y%m%d).db

# Restore from backup
cp /backup/metrics-20251005.db /var/lib/fakeai/metrics.db
```

### Configuration Backup

#### Backup Script
```bash
#!/bin/bash
# backup-fakeai.sh

BACKUP_DIR=/backup/fakeai
DATE=$(date +%Y%m%d-%H%M%S)

mkdir -p $BACKUP_DIR

# Backup configuration
cp /etc/fakeai/config.yaml $BACKUP_DIR/config-$DATE.yaml

# Backup API keys
cp /etc/fakeai/api-keys.txt $BACKUP_DIR/api-keys-$DATE.txt

# Backup systemd service
cp /etc/systemd/system/fakeai.service $BACKUP_DIR/fakeai.service-$DATE

# Backup metrics database
cp /var/lib/fakeai/metrics.db $BACKUP_DIR/metrics-$DATE.db

# Create tarball
tar -czf $BACKUP_DIR/fakeai-backup-$DATE.tar.gz \
  $BACKUP_DIR/*-$DATE.*

# Clean up old backups (keep 30 days)
find $BACKUP_DIR -name "fakeai-backup-*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/fakeai-backup-$DATE.tar.gz"
```

#### Automated Backups (Cron)
```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /opt/fakeai/scripts/backup-fakeai.sh

# Weekly backup on Sunday at 3 AM
0 3 * * 0 /opt/fakeai/scripts/backup-fakeai.sh weekly
```

### Disaster Recovery

#### Recovery Plan
```bash
# 1. Stop service
systemctl stop fakeai

# 2. Restore configuration
tar -xzf /backup/fakeai-backup-20251005.tar.gz -C /

# 3. Restore metrics database
cp /backup/metrics-20251005.db /var/lib/fakeai/metrics.db

# 4. Verify configuration
fakeai server --help

# 5. Start service
systemctl start fakeai

# 6. Verify health
curl http://localhost:8000/health
```

### Upgrade Procedures

#### Standard Upgrade
```bash
# 1. Backup current version
/opt/fakeai/scripts/backup-fakeai.sh

# 2. Stop service
systemctl stop fakeai

# 3. Upgrade package
pip install --upgrade fakeai

# 4. Verify installation
fakeai --version

# 5. Test configuration
fakeai server --help

# 6. Start service
systemctl start fakeai

# 7. Verify health
curl http://localhost:8000/health

# 8. Monitor logs
journalctl -u fakeai -f
```

#### Zero-Downtime Upgrade (K8s)
```bash
# Rolling update
kubectl set image deployment/fakeai \
  fakeai=fakeai:1.0.0 \
  -n fakeai

# Monitor rollout
kubectl rollout status deployment/fakeai -n fakeai

# Rollback if needed
kubectl rollout undo deployment/fakeai -n fakeai
```

---

## Security

### API Key Management

#### Generate Secure Keys
```bash
# Generate API key
openssl rand -base64 32 | tr -d '/+=' | head -c 48
# Result: sk-abc123def456ghi789jkl012mno345pqr678stu901vwx
```

#### Store Keys Securely
```bash
# Use environment variables (not hardcoded)
export FAKEAI_API_KEYS=$(cat /secure/api-keys.txt)

# Use secrets management
kubectl create secret generic fakeai-secrets \
  --from-literal=api-keys=$(cat api-keys.txt) \
  -n fakeai

# Use HashiCorp Vault
vault kv put secret/fakeai api_keys=@api-keys.txt
```

#### Rotate Keys
```bash
# Generate new keys
NEW_KEYS=$(openssl rand -base64 32 | tr -d '/+=' | head -c 48)

# Add new keys alongside old (grace period)
export FAKEAI_API_KEYS="$NEW_KEYS,$OLD_KEYS"

# Restart service
systemctl restart fakeai

# After grace period, remove old keys
export FAKEAI_API_KEYS="$NEW_KEYS"
systemctl restart fakeai
```

### Rate Limiting Configuration

#### Per-Key Limits
```bash
# Set strict limits
export FAKEAI_RATE_LIMIT_ENABLED=true
export FAKEAI_RATE_LIMIT_TIER=tier-2
export FAKEAI_RATE_LIMIT_RPM=5000
export FAKEAI_RATE_LIMIT_TPM=450000
```

#### Abuse Prevention
```bash
# Enable abuse detection
export FAKEAI_ENABLE_ABUSE_DETECTION=true
export FAKEAI_ABUSE_CLEANUP_INTERVAL=3600

# Monitor abuse
curl http://localhost:8000/metrics | jq '.abuse'
```

### Security Best Practices

#### 1. Network Security
```bash
# Firewall rules (iptables)
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
iptables -A INPUT -j DROP

# Allow only specific IPs
iptables -A INPUT -p tcp --dport 8000 -s 10.0.0.0/8 -j ACCEPT
```

#### 2. TLS/SSL Configuration
```bash
# Generate self-signed cert (development)
openssl req -x509 -newkey rsa:4096 \
  -keyout key.pem -out cert.pem \
  -days 365 -nodes

# Run with TLS
uvicorn fakeai.app:app \
  --host 0.0.0.0 \
  --port 8443 \
  --ssl-keyfile key.pem \
  --ssl-certfile cert.pem
```

#### 3. Input Validation
```bash
# Enable input validation
export FAKEAI_ENABLE_INPUT_VALIDATION=true
export FAKEAI_ENABLE_INJECTION_DETECTION=true
export FAKEAI_MAX_REQUEST_SIZE=10485760  # 10 MB
```

#### 4. Content Moderation
```bash
# Enable safety features
export FAKEAI_ENABLE_MODERATION=true
export FAKEAI_MODERATION_THRESHOLD=0.5
export FAKEAI_ENABLE_REFUSALS=true
export FAKEAI_ENABLE_JAILBREAK_DETECTION=true
```

### Compliance Considerations

#### GDPR Compliance
- Log retention policies (30-90 days)
- Data anonymization in logs
- Right to erasure (delete user data)
- Data encryption at rest and in transit

#### SOC 2 Compliance
- Access control (API key authentication)
- Audit logging (all requests logged)
- Change management (version control)
- Incident response (alerting and monitoring)

#### HIPAA Compliance
- Encryption (TLS/SSL)
- Access controls (authentication required)
- Audit trails (comprehensive logging)
- Business associate agreements

---

## Maintenance

### Log Rotation

#### Logrotate Configuration
```bash
# /etc/logrotate.d/fakeai
/var/log/fakeai/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 fakeai fakeai
    sharedscripts
    postrotate
        systemctl reload fakeai > /dev/null 2>&1 || true
    endscript
}
```

#### Manual Log Cleanup
```bash
# Clean old logs
find /var/log/fakeai -name "*.log" -mtime +30 -delete
find /var/log/fakeai -name "*.gz" -mtime +90 -delete

# Archive logs
tar -czf /backup/logs-$(date +%Y%m%d).tar.gz /var/log/fakeai/*.log
```

### Cache Cleanup

#### Manual Cache Cleanup
```bash
# Clear prompt cache
curl -X POST http://localhost:8000/admin/clear-cache

# Clear KV cache
curl -X POST http://localhost:8000/admin/clear-kv-cache

# Restart to clear all caches
systemctl restart fakeai
```

#### Automated Cleanup (Cron)
```bash
# Daily cache cleanup at 3 AM
0 3 * * * curl -X POST http://localhost:8000/admin/clear-cache
```

### Database Maintenance

#### Metrics Database Cleanup
```bash
# Vacuum database
sqlite3 /var/lib/fakeai/metrics.db "VACUUM;"

# Analyze for optimization
sqlite3 /var/lib/fakeai/metrics.db "ANALYZE;"

# Clean old records (>90 days)
sqlite3 /var/lib/fakeai/metrics.db \
  "DELETE FROM metrics WHERE timestamp < datetime('now', '-90 days');"
```

### Health Checks

#### Automated Health Check Script
```bash
#!/bin/bash
# health-check.sh

ENDPOINT="http://localhost:8000/health"
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $ENDPOINT)

    if [ $RESPONSE -eq 200 ]; then
        echo "Health check passed"
        exit 0
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Health check failed (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done

echo "Health check failed after $MAX_RETRIES attempts"
exit 1
```

#### Monitoring Dashboards

**Key Metrics to Monitor:**
1. Request rate (requests/second)
2. Error rate (errors/second)
3. Latency percentiles (p50, p90, p99)
4. Memory usage (MB)
5. CPU utilization (%)
6. KV cache hit rate (%)
7. Active connections
8. Queue depth

**Alert Thresholds:**
- Error rate > 5% (warning)
- p99 latency > 1s (warning)
- Memory usage > 80% (warning)
- CPU usage > 90% (critical)
- Service down (critical)

---

## Appendix

### Quick Reference Commands

```bash
# Start server
fakeai server
fakeai server --debug
fakeai server --host 0.0.0.0 --port 8000

# Check health
curl http://localhost:8000/health

# View metrics
curl http://localhost:8000/metrics
curl http://localhost:8000/metrics/prometheus
curl http://localhost:8000/kv-cache/metrics

# Docker
docker-compose up -d
docker-compose logs -f fakeai
docker-compose restart fakeai

# Kubernetes
kubectl get pods -n fakeai
kubectl logs -f deployment/fakeai -n fakeai
kubectl scale deployment fakeai --replicas=5 -n fakeai

# Systemd
sudo systemctl start fakeai
sudo systemctl status fakeai
sudo journalctl -u fakeai -f

# PM2
pm2 start ecosystem.config.js
pm2 logs fakeai
pm2 restart fakeai
```

### Environment Variables Quick Reference

See [Configuration](#configuration) section for complete list.

### Resource Requirements Summary

| Deployment | CPU | Memory | Storage | Throughput |
|------------|-----|--------|---------|------------|
| Development | 1 core | 512 MB | 50 MB | ~100 req/s |
| Testing | 2 cores | 1 GB | 500 MB | ~500 req/s |
| Production | 4 cores | 2 GB | 1 GB | ~1000 req/s |
| High Load | 8 cores | 4 GB | 2 GB | ~2000 req/s |

---

## Support

### Getting Help

- **Documentation**: https://github.com/ajcasagrande/fakeai/docs
- **Issues**: https://github.com/ajcasagrande/fakeai/issues
- **Discussions**: https://github.com/ajcasagrande/fakeai/discussions

### Contributing

See [CONTRIBUTING.md](../../development/CONTRIBUTING.md) for guidelines.

---

**Last Updated:** October 5, 2025
**Version:** 1.0.0
**License:** Apache-2.0
