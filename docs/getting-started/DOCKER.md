# FakeAI Docker Deployment Guide

Complete guide for deploying FakeAI using Docker and Docker Compose.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Building the Image](#building-the-image)
3. [Running with Docker](#running-with-docker)
4. [Running with Docker Compose](#running-with-docker-compose)
5. [Configuration](#configuration)
6. [Redis Integration](#redis-integration)
7. [Scaling and Load Balancing](#scaling-and-load-balancing)
8. [Production Deployment](#production-deployment)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Usage](#advanced-usage)

---

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/ajcasagrande/fakeai.git
cd fakeai

# Start FakeAI server
docker-compose up -d

# Check logs
docker-compose logs -f fakeai

# Test the API
curl http://localhost:8000/health
```

### Option 2: Docker Run

```bash
# Build the image
docker build -t fakeai:latest .

# Run the container
docker run -d -p 8000:8000 --name fakeai-server fakeai:latest

# Check logs
docker logs -f fakeai-server

# Test the API
curl http://localhost:8000/health
```

---

## Building the Image

### Standard Build

```bash
docker build -t fakeai:latest .
```

### Build with Custom Tag

```bash
docker build -t fakeai:0.0.4 .
docker build -t myregistry.com/fakeai:latest .
```

### Multi-Platform Build

```bash
# Build for multiple architectures
docker buildx build --platform linux/amd64,linux/arm64 -t fakeai:latest .
```

### Build Arguments

The Dockerfile supports multi-stage builds for optimal image size:

```bash
# Build with specific Python version (modify Dockerfile)
docker build --build-arg PYTHON_VERSION=3.11 -t fakeai:py311 .
```

### Image Size Optimization

The multi-stage build produces a minimal image:
- Builder stage: Installs dependencies and builds
- Runtime stage: Only includes runtime dependencies
- Final image size: ~150-200MB

---

## Running with Docker

### Basic Run

```bash
docker run -d \
  -p 8000:8000 \
  --name fakeai-server \
  fakeai:latest
```

### Run with Environment Variables

```bash
docker run -d \
  -p 8000:8000 \
  --name fakeai-server \
  -e FAKEAI_DEBUG=true \
  -e FAKEAI_RESPONSE_DELAY=0.1 \
  -e FAKEAI_REQUIRE_API_KEY=true \
  -e FAKEAI_API_KEYS=sk-test-key-1,sk-test-key-2 \
  fakeai:latest
```

### Run with Volume Mounts

```bash
docker run -d \
  -p 8000:8000 \
  --name fakeai-server \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config:/app/config:ro \
  fakeai:latest
```

### Run with Custom Network

```bash
# Create network
docker network create fakeai-net

# Run container
docker run -d \
  -p 8000:8000 \
  --name fakeai-server \
  --network fakeai-net \
  fakeai:latest
```

### Interactive Mode (for debugging)

```bash
docker run -it --rm \
  -p 8000:8000 \
  fakeai:latest \
  /bin/bash
```

---

## Running with Docker Compose

### Basic Deployment

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### With Redis (Distributed Rate Limiting)

```bash
# Start with Redis profile
docker-compose --profile with-redis up -d

# Check all services
docker-compose ps

# View Redis logs
docker-compose logs -f redis
```

### Custom Configuration

Create a `.env` file:

```env
# Server Settings
FAKEAI_HOST=0.0.0.0
FAKEAI_PORT=8000
FAKEAI_DEBUG=false

# Response Simulation
FAKEAI_RESPONSE_DELAY=0.5
FAKEAI_RANDOM_DELAY=true
FAKEAI_MAX_VARIANCE=0.3

# Authentication
FAKEAI_REQUIRE_API_KEY=true
FAKEAI_API_KEYS=sk-prod-key-1,sk-prod-key-2

# Rate Limiting
FAKEAI_RATE_LIMIT_ENABLED=true
FAKEAI_REQUESTS_PER_MINUTE=100
FAKEAI_REDIS_URL=redis://redis:6379/0
```

Then start with:

```bash
docker-compose --env-file .env up -d
```

### Scale Services

```bash
# Run multiple FakeAI instances
docker-compose up -d --scale fakeai=3

# With load balancer (see Scaling section)
docker-compose -f docker-compose.yml -f docker-compose.scale.yml up -d
```

---

## Configuration

### Environment Variables

All configuration is done via environment variables with the `FAKEAI_` prefix.

#### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FAKEAI_HOST` | `0.0.0.0` | Server bind host |
| `FAKEAI_PORT` | `8000` | Server port |
| `FAKEAI_DEBUG` | `false` | Enable debug mode |

#### Response Simulation

| Variable | Default | Description |
|----------|---------|-------------|
| `FAKEAI_RESPONSE_DELAY` | `0.5` | Base response delay (seconds) |
| `FAKEAI_RANDOM_DELAY` | `true` | Enable random delay variance |
| `FAKEAI_MAX_VARIANCE` | `0.3` | Maximum delay variance (seconds) |

#### Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `FAKEAI_REQUIRE_API_KEY` | `false` | Require API key authentication |
| `FAKEAI_API_KEYS` | `[]` | Comma-separated list of valid API keys |

#### Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `FAKEAI_RATE_LIMIT_ENABLED` | `false` | Enable rate limiting |
| `FAKEAI_REQUESTS_PER_MINUTE` | `10000` | Maximum requests per minute |
| `FAKEAI_REDIS_URL` | None | Redis connection URL for distributed rate limiting |

### Docker Compose Configuration

Edit `docker-compose.yml` to customize:

```yaml
services:
  fakeai:
    environment:
      - FAKEAI_DEBUG=true
      - FAKEAI_RESPONSE_DELAY=0.1
    ports:
      - "9000:8000"  # Change external port
    volumes:
      - ./my-config:/app/config:ro
```

---

## Redis Integration

### Why Redis?

Redis provides:
- Distributed rate limiting across multiple FakeAI instances
- Shared state for consistent rate limiting
- High-performance in-memory storage

### Enabling Redis

#### Option 1: Docker Compose with Profile

```bash
docker-compose --profile with-redis up -d
```

#### Option 2: Standalone Redis

```bash
# Start Redis
docker run -d \
  --name fakeai-redis \
  --network fakeai-net \
  -p 6379:6379 \
  redis:7-alpine

# Configure FakeAI to use Redis
docker run -d \
  --name fakeai-server \
  --network fakeai-net \
  -p 8000:8000 \
  -e FAKEAI_RATE_LIMIT_ENABLED=true \
  -e FAKEAI_REDIS_URL=redis://fakeai-redis:6379/0 \
  fakeai:latest
```

### Redis Configuration

The provided Redis configuration includes:

```bash
redis-server \
  --appendonly yes \            # Persistence
  --maxmemory 256mb \           # Memory limit
  --maxmemory-policy allkeys-lru  # Eviction policy
```

### Testing Redis Connection

```bash
# Connect to Redis CLI
docker exec -it fakeai-redis redis-cli

# Check connection
127.0.0.1:6379> PING
PONG

# View keys
127.0.0.1:6379> KEYS *

# Monitor commands
127.0.0.1:6379> MONITOR
```

---

## Scaling and Load Balancing

### Horizontal Scaling

#### Simple Scaling with Docker Compose

```bash
# Scale to 3 instances
docker-compose up -d --scale fakeai=3
```

Note: You'll need a load balancer in front (see below).

#### With Nginx Load Balancer

Create `docker-compose.scale.yml`:

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: fakeai-nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - fakeai
    networks:
      - fakeai-network

  fakeai:
    # Remove ports from main service when using nginx
    ports: []
    expose:
      - "8000"
```

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream fakeai_backend {
        least_conn;
        server fakeai:8000 max_fails=3 fail_timeout=30s;
        # Add more servers when scaling
        # server fakeai-2:8000;
        # server fakeai-3:8000;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://fakeai_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Streaming support
            proxy_buffering off;
            proxy_cache off;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }

        location /health {
            access_log off;
            proxy_pass http://fakeai_backend/health;
        }
    }
}
```

Run with:

```bash
docker-compose -f docker-compose.yml -f docker-compose.scale.yml up -d --scale fakeai=3
```

### Kubernetes Deployment

Example Kubernetes deployment:

```yaml
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
        - name: FAKEAI_PORT
          value: "8000"
        - name: FAKEAI_RATE_LIMIT_ENABLED
          value: "true"
        - name: FAKEAI_REDIS_URL
          value: "redis://redis-service:6379/0"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: fakeai-service
spec:
  selector:
    app: fakeai
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

---

## Production Deployment

### Best Practices

#### 1. Security

```bash
# Use API key authentication
FAKEAI_REQUIRE_API_KEY=true
FAKEAI_API_KEYS=sk-strong-random-key-1,sk-strong-random-key-2

# Run as non-root user (built into Dockerfile)
# Container runs as 'fakeai' user

# Use secrets management
docker run -d \
  -p 8000:8000 \
  --name fakeai-server \
  -e FAKEAI_API_KEYS=$(cat /run/secrets/fakeai-api-keys) \
  fakeai:latest
```

#### 2. Resource Limits

```yaml
# docker-compose.yml
services:
  fakeai:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 256M
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

#### 3. Health Checks

```yaml
# docker-compose.yml
services:
  fakeai:
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

#### 4. Logging

```yaml
# docker-compose.yml
services:
  fakeai:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Or use a centralized logging solution:

```yaml
services:
  fakeai:
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://logserver:514"
        tag: "fakeai"
```

#### 5. Monitoring

```yaml
# Add Prometheus monitoring
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

#### 6. SSL/TLS Termination

Use a reverse proxy with SSL:

```yaml
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.myresolver.acme.tlschallenge=true"
      - "--certificatesresolvers.myresolver.acme.email=admin@example.com"
      - "--certificatesresolvers.myresolver.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"

  fakeai:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.fakeai.rule=Host(`api.example.com`)"
      - "traefik.http.routers.fakeai.entrypoints=websecure"
      - "traefik.http.routers.fakeai.tls.certresolver=myresolver"
```

### Production Checklist

- [ ] API key authentication enabled
- [ ] Rate limiting configured
- [ ] Resource limits set
- [ ] Health checks configured
- [ ] Logging configured
- [ ] Monitoring set up
- [ ] Backups configured (if using Redis persistence)
- [ ] SSL/TLS termination
- [ ] Auto-restart policy
- [ ] Multiple replicas for HA
- [ ] Load balancer configured

---

## Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check logs
docker logs fakeai-server

# Check container status
docker ps -a

# Inspect container
docker inspect fakeai-server

# Check entry point
docker run -it --rm fakeai:latest /bin/bash
```

#### Port Already in Use

```bash
# Check what's using the port
sudo lsof -i :8000

# Use a different port
docker run -d -p 9000:8000 fakeai:latest
```

#### Redis Connection Failed

```bash
# Check Redis is running
docker ps | grep redis

# Test Redis connection
docker exec -it fakeai-redis redis-cli PING

# Check network connectivity
docker exec -it fakeai-server ping redis

# Verify Redis URL
docker exec -it fakeai-server env | grep REDIS
```

#### Health Check Failing

```bash
# Manual health check
docker exec -it fakeai-server curl http://localhost:8000/health

# Check if server is running
docker exec -it fakeai-server ps aux

# Check logs
docker logs fakeai-server
```

#### Out of Memory

```bash
# Check memory usage
docker stats fakeai-server

# Increase memory limit
docker run -d -p 8000:8000 --memory="1g" fakeai:latest
```

### Debug Mode

Enable debug mode for verbose logging:

```bash
docker run -d \
  -p 8000:8000 \
  -e FAKEAI_DEBUG=true \
  fakeai:latest

# View debug logs
docker logs -f fakeai-server
```

### Interactive Debugging

```bash
# Start container with bash
docker run -it --rm \
  -p 8000:8000 \
  fakeai:latest \
  /bin/bash

# Inside container
python -m fakeai.cli --debug

# Or use Python directly
python
>>> from fakeai import AppConfig, FakeAIService
>>> config = AppConfig()
>>> service = FakeAIService(config)
```

---

## Advanced Usage

### Custom Dockerfile

Create a custom Dockerfile for your needs:

```dockerfile
FROM fakeai:latest

# Add custom models or configurations
COPY custom_models.json /app/config/

# Install additional dependencies
RUN pip install --no-cache-dir my-custom-package

# Override entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["fakeai-server", "--response-delay", "0.1"]
```

### Docker Swarm Deployment

```bash
# Initialize swarm
docker swarm init

# Create stack file (docker-stack.yml)
version: '3.8'

services:
  fakeai:
    image: fakeai:latest
    ports:
      - "8000:8000"
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    networks:
      - fakeai-net

networks:
  fakeai-net:
    driver: overlay

# Deploy stack
docker stack deploy -c docker-stack.yml fakeai-stack

# Check services
docker service ls
docker service ps fakeai-stack_fakeai
```

### Multi-Environment Setup

Use different compose files for different environments:

```bash
# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Staging
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Example `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  fakeai:
    environment:
      - FAKEAI_DEBUG=true
      - FAKEAI_RESPONSE_DELAY=0.0
    volumes:
      - ./fakeai:/app/fakeai
    command: fakeai-server --debug --reload
```

### CI/CD Integration

#### GitHub Actions Example

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            myuser/fakeai:latest
            myuser/fakeai:${{ github.sha }}
          cache-from: type=registry,ref=myuser/fakeai:buildcache
          cache-to: type=registry,ref=myuser/fakeai:buildcache,mode=max
```

### Performance Tuning

#### Optimize Uvicorn Workers

```bash
docker run -d \
  -p 8000:8000 \
  fakeai:latest \
  fakeai-server --workers 4
```

#### Use Hypercorn for HTTP/2

```bash
docker run -d \
  -p 8000:8000 \
  fakeai:latest \
  hypercorn fakeai.app:app \
    --bind 0.0.0.0:8000 \
    --workers 4
```

---

## Additional Resources

- [FakeAI Documentation](https://github.com/ajcasagrande/fakeai)
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/ajcasagrande/fakeai/issues
- Documentation: https://github.com/ajcasagrande/fakeai#readme

---

**Version:** 0.0.4
**Last Updated:** 2025-10-04
