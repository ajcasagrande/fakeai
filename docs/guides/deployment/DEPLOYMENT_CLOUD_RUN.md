# FakeAI Google Cloud Run Deployment Guide

This guide covers deploying FakeAI on Google Cloud Run, a fully managed serverless container platform that automatically scales your container based on incoming requests.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Why Cloud Run?](#why-cloud-run)
3. [Container Preparation](#container-preparation)
4. [Deployment Methods](#deployment-methods)
5. [Configuration](#configuration)
6. [Environment Variables and Secrets](#environment-variables-and-secrets)
7. [Scaling Policies](#scaling-policies)
8. [Custom Domains and SSL](#custom-domains-and-ssl)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [CI/CD Integration](#cicd-integration)
11. [Cost Optimization](#cost-optimization)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

- Google Cloud SDK (gcloud) installed
- Docker installed
- Google Cloud Project with billing enabled
- Appropriate IAM permissions

### Install Google Cloud SDK

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize gcloud
gcloud init

# Set default project
gcloud config set project YOUR_PROJECT_ID

# Authenticate Docker with Google Container Registry
gcloud auth configure-docker

# Or use Artifact Registry (recommended)
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### Enable Required APIs

```bash
# Enable Cloud Run API
gcloud services enable run.googleapis.com

# Enable Container Registry API
gcloud services enable containerregistry.googleapis.com

# Enable Artifact Registry API (recommended)
gcloud services enable artifactregistry.googleapis.com

# Enable Secret Manager API (for secrets)
gcloud services enable secretmanager.googleapis.com

# Enable Cloud Build API (for automated builds)
gcloud services enable cloudbuild.googleapis.com
```

### Set Environment Variables

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export SERVICE_NAME="fakeai"
```

---

## Why Cloud Run?

### Advantages

1. **Fully Managed**: No infrastructure management
2. **Auto-Scaling**: Scales to zero when idle, up to thousands of instances
3. **Pay-per-Use**: Only pay for actual request time
4. **HTTPS by Default**: Automatic SSL certificates
5. **Fast Deployment**: Deploy in seconds
6. **Container-Based**: Run any container that listens on a port

### Use Cases

- Development and testing environments
- API servers with variable load
- Microservices architecture
- Burst workloads
- Cost-sensitive deployments

### Limitations

- **Timeout**: Maximum 60 minutes per request
- **Memory**: Up to 32GB per instance
- **CPU**: Up to 8 vCPUs per instance
- **Cold Starts**: Initial requests may be slower
- **WebSockets**: Limited support (use Cloud Run for Anthos for full support)

---

## Container Preparation

### Optimized Dockerfile for Cloud Run

```dockerfile
# Dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install FakeAI
RUN pip install --no-cache-dir fakeai

# Create non-root user (Cloud Run best practice)
RUN useradd -m -u 1000 fakeai && \
    chown -R fakeai:fakeai /app

# Switch to non-root user
USER fakeai

# Cloud Run sets PORT environment variable
ENV PORT=8080

# Expose port (documentation only, Cloud Run ignores this)
EXPOSE 8080

# Health check (optional, Cloud Run has its own)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Run server on PORT environment variable
CMD fakeai-server --host 0.0.0.0 --port ${PORT}
```

### Multi-Stage Build (Smaller Image)

```dockerfile
# Dockerfile.multistage
# Stage 1: Builder
FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir --user fakeai

# Stage 2: Runtime
FROM python:3.10-slim

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /root/.local /root/.local

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH
ENV PORT=8080

EXPOSE 8080

CMD ["fakeai-server", "--host", "0.0.0.0", "--port", "${PORT}"]
```

### Build and Test Locally

```bash
# Build image
docker build -t fakeai:latest .

# Test locally with PORT environment variable
docker run -p 8080:8080 -e PORT=8080 fakeai:latest

# Test in another terminal
curl http://localhost:8080/health
curl http://localhost:8080/v1/models
```

---

## Deployment Methods

### Method 1: Deploy from Local Source

This method builds the container in Cloud Build and deploys to Cloud Run.

```bash
# Deploy directly from source code
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated

# The --source flag triggers Cloud Build to:
# 1. Build container from Dockerfile
# 2. Push to Container Registry
# 3. Deploy to Cloud Run
```

### Method 2: Deploy from Container Registry

```bash
# Build image locally
docker build -t gcr.io/$PROJECT_ID/fakeai:latest .

# Push to Google Container Registry
docker push gcr.io/$PROJECT_ID/fakeai:latest

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/fakeai:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated
```

### Method 3: Deploy from Artifact Registry (Recommended)

```bash
# Create Artifact Registry repository
gcloud artifacts repositories create fakeai \
  --repository-format=docker \
  --location=$REGION \
  --description="FakeAI container images"

# Configure Docker authentication
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build and tag image
docker build -t ${REGION}-docker.pkg.dev/$PROJECT_ID/fakeai/fakeai:latest .

# Push to Artifact Registry
docker push ${REGION}-docker.pkg.dev/$PROJECT_ID/fakeai/fakeai:latest

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image ${REGION}-docker.pkg.dev/$PROJECT_ID/fakeai/fakeai:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated
```

### Method 4: Deploy with Cloud Build

Create a Cloud Build configuration file:

```yaml
# cloudbuild.yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'build',
      '-t', '${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPOSITORY}/${_IMAGE}:${_TAG}',
      '-t', '${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPOSITORY}/${_IMAGE}:latest',
      '.'
    ]

  # Push the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'push',
      '--all-tags',
      '${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPOSITORY}/${_IMAGE}'
    ]

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - '${_SERVICE_NAME}'
      - '--image=${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPOSITORY}/${_IMAGE}:${_TAG}'
      - '--region=${_REGION}'
      - '--platform=managed'
      - '--allow-unauthenticated'

substitutions:
  _REGION: us-central1
  _REPOSITORY: fakeai
  _IMAGE: fakeai
  _SERVICE_NAME: fakeai
  _TAG: latest

images:
  - '${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPOSITORY}/${_IMAGE}:${_TAG}'
  - '${_REGION}-docker.pkg.dev/$PROJECT_ID/${_REPOSITORY}/${_IMAGE}:latest'
```

```bash
# Trigger build
gcloud builds submit --config cloudbuild.yaml
```

---

## Configuration

### Complete Deployment Configuration

```bash
# Deploy with full configuration
gcloud run deploy $SERVICE_NAME \
  --image ${REGION}-docker.pkg.dev/$PROJECT_ID/fakeai/fakeai:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 100 \
  --concurrency 80 \
  --timeout 300 \
  --set-env-vars "FAKEAI_DEBUG=false,FAKEAI_RESPONSE_DELAY=0.5,FAKEAI_REQUIRE_API_KEY=true" \
  --set-secrets "FAKEAI_API_KEYS=fakeai-api-keys:latest" \
  --service-account fakeai-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --ingress all \
  --cpu-boost \
  --execution-environment gen2
```

### Configuration Parameters Explained

```bash
# Image and region
--image                 # Container image URL
--region               # GCP region (us-central1, europe-west1, etc.)
--platform managed     # Use fully managed Cloud Run

# Access control
--allow-unauthenticated   # Allow public access
--no-allow-unauthenticated  # Require authentication

# Resource allocation
--memory 512Mi         # Memory: 128Mi to 32Gi
--cpu 1                # CPU: 1, 2, 4, or 8 vCPUs
--cpu-throttling       # Throttle CPU when no requests (default)
--no-cpu-throttling    # Always allocate CPU (costs more)

# Scaling
--min-instances 0      # Minimum instances (0 to scale to zero)
--max-instances 100    # Maximum instances (up to 1000)
--concurrency 80       # Max concurrent requests per instance (1-1000)

# Timeouts
--timeout 300          # Request timeout in seconds (max 3600)

# Network
--port 8080           # Container port to receive requests
--ingress all         # all, internal, internal-and-cloud-load-balancing

# Performance
--cpu-boost           # Startup CPU boost for faster cold starts
--execution-environment gen2  # Second generation execution environment

# Service account
--service-account     # IAM service account for the service
```

### Update Service Configuration

```bash
# Update environment variables
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --update-env-vars FAKEAI_RESPONSE_DELAY=0.3

# Update resource limits
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --memory 1Gi \
  --cpu 2

# Update scaling
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --min-instances 1 \
  --max-instances 50 \
  --concurrency 100
```

---

## Environment Variables and Secrets

### Set Environment Variables

```bash
# Set multiple environment variables
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --set-env-vars "FAKEAI_HOST=0.0.0.0,FAKEAI_PORT=8080,FAKEAI_DEBUG=false,FAKEAI_RESPONSE_DELAY=0.5,FAKEAI_RANDOM_DELAY=true,FAKEAI_REQUIRE_API_KEY=true"

# Update individual variable
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --update-env-vars FAKEAI_DEBUG=true

# Remove environment variable
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --remove-env-vars FAKEAI_DEBUG
```

### Use Secret Manager

```bash
# Create secret
echo -n "sk-key1,sk-key2,sk-key3" | \
  gcloud secrets create fakeai-api-keys \
    --data-file=-

# Grant service access to secret
gcloud secrets add-iam-policy-binding fakeai-api-keys \
  --member=serviceAccount:fakeai-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Mount secret as environment variable
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --set-secrets "FAKEAI_API_KEYS=fakeai-api-keys:latest"

# Mount secret as file (alternative)
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --set-secrets "/secrets/api-keys=fakeai-api-keys:latest"
```

### Update Secret

```bash
# Add new secret version
echo -n "sk-key1,sk-key2,sk-key3,sk-key4" | \
  gcloud secrets versions add fakeai-api-keys \
    --data-file=-

# Cloud Run automatically uses 'latest' version
# To pin to specific version:
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --set-secrets "FAKEAI_API_KEYS=fakeai-api-keys:2"
```

### Environment Variables via YAML

```yaml
# service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: fakeai
spec:
  template:
    spec:
      containers:
      - image: us-central1-docker.pkg.dev/project-id/fakeai/fakeai:latest
        env:
        - name: FAKEAI_HOST
          value: "0.0.0.0"
        - name: FAKEAI_PORT
          value: "8080"
        - name: FAKEAI_DEBUG
          value: "false"
        - name: FAKEAI_RESPONSE_DELAY
          value: "0.5"
        - name: FAKEAI_REQUIRE_API_KEY
          value: "true"
        - name: FAKEAI_API_KEYS
          valueFrom:
            secretKeyRef:
              name: fakeai-api-keys
              key: latest
        resources:
          limits:
            memory: 512Mi
            cpu: "1"
```

```bash
# Deploy from YAML
gcloud run services replace service.yaml --region $REGION
```

---

## Scaling Policies

### Auto-Scaling Configuration

```bash
# Configure auto-scaling
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --min-instances 0 \
  --max-instances 100 \
  --concurrency 80

# Scale to zero (no minimum instances)
# - Costs nothing when idle
# - Cold starts on first request after idle period

# Minimum instances (warm pool)
# - Reduces cold starts
# - Costs more (always running)
# - Use min-instances 1-5 for production
```

### Concurrency Settings

```bash
# High concurrency (80-1000)
# - Lower cost (fewer instances needed)
# - Higher latency under load
# - Good for I/O-bound workloads

gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --concurrency 80

# Low concurrency (1-10)
# - Higher cost (more instances needed)
# - Lower latency
# - Good for CPU-bound workloads

gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --concurrency 10
```

### CPU Allocation

```bash
# CPU throttling (default)
# - CPU only allocated during request processing
# - Lower cost
# - Suitable for most workloads

gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --cpu-throttling

# CPU always allocated
# - CPU allocated even when no requests
# - Higher cost
# - Needed for background tasks

gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --no-cpu-throttling
```

### Recommended Scaling Configurations

#### Development Environment
```bash
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --min-instances 0 \
  --max-instances 10 \
  --concurrency 80 \
  --memory 512Mi \
  --cpu 1
```

#### Production Environment (Cost-Optimized)
```bash
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --min-instances 1 \
  --max-instances 100 \
  --concurrency 80 \
  --memory 1Gi \
  --cpu 2
```

#### Production Environment (Performance-Optimized)
```bash
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --min-instances 5 \
  --max-instances 100 \
  --concurrency 50 \
  --memory 2Gi \
  --cpu 4 \
  --no-cpu-throttling \
  --cpu-boost
```

---

## Custom Domains and SSL

### Map Custom Domain

```bash
# Add domain mapping
gcloud run domain-mappings create \
  --service $SERVICE_NAME \
  --domain fakeai.example.com \
  --region $REGION

# Get DNS records to configure
gcloud run domain-mappings describe \
  --domain fakeai.example.com \
  --region $REGION

# Example output:
# Type: A
# Name: fakeai.example.com
# Value: 216.239.32.21
```

### Configure DNS

Add the following DNS records at your domain registrar:

```
Type: A
Name: fakeai.example.com
Value: [IP from above command]

Type: AAAA (IPv6, optional)
Name: fakeai.example.com
Value: [IPv6 from above command]
```

### Verify Domain Mapping

```bash
# Check domain status
gcloud run domain-mappings describe \
  --domain fakeai.example.com \
  --region $REGION

# Test domain
curl https://fakeai.example.com/health
```

### SSL Certificate

Cloud Run automatically provisions SSL certificates for custom domains. The process takes a few minutes after DNS propagation.

```bash
# Check certificate status
gcloud run domain-mappings describe \
  --domain fakeai.example.com \
  --region $REGION \
  --format="value(status.certificateStatus)"
```

---

## Monitoring and Logging

### View Logs

```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
  --limit 50 \
  --format json

# Follow logs in real-time
gcloud alpha logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME"

# Filter logs by severity
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND severity>=ERROR" \
  --limit 20
```

### Metrics and Monitoring

```bash
# View service details with metrics
gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format yaml

# Access Cloud Monitoring dashboard
echo "https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics?project=$PROJECT_ID"
```

### Key Metrics to Monitor

1. **Request Count**: Total number of requests
2. **Request Latency**: Response time (p50, p95, p99)
3. **Instance Count**: Number of running instances
4. **Billable Instance Time**: Total instance time (cost driver)
5. **CPU Utilization**: CPU usage per instance
6. **Memory Utilization**: Memory usage per instance
7. **Container Startup Latency**: Cold start time
8. **Error Rate**: HTTP 5xx error percentage

### Create Alerts

```bash
# Example: Alert on high error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="FakeAI High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=300s
```

### Enable Cloud Trace

Cloud Run automatically integrates with Cloud Trace for distributed tracing.

```bash
# View traces
gcloud trace list \
  --filter="span:$SERVICE_NAME" \
  --limit=10
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/deploy-cloud-run.yml
name: Deploy to Cloud Run

on:
  push:
    branches:
      - main

env:
  PROJECT_ID: your-project-id
  REGION: us-central1
  SERVICE_NAME: fakeai
  REPOSITORY: fakeai

jobs:
  deploy:
    runs-on: ubuntu-latest

    permissions:
      contents: read
      id-token: write

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Authenticate to Google Cloud
      uses: google-github-actions/auth@v1
      with:
        workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
        service_account: ${{ secrets.WIF_SERVICE_ACCOUNT }}

    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v1

    - name: Configure Docker
      run: |
        gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev

    - name: Build and Push Container
      run: |
        docker build -t ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/${{ env.REPOSITORY }}/fakeai:${{ github.sha }} .
        docker push ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/${{ env.REPOSITORY }}/fakeai:${{ github.sha }}

    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy ${{ env.SERVICE_NAME }} \
          --image ${{ env.REGION }}-docker.pkg.dev/${{ env.PROJECT_ID }}/${{ env.REPOSITORY }}/fakeai:${{ github.sha }} \
          --region ${{ env.REGION }} \
          --platform managed \
          --allow-unauthenticated
```

### GitLab CI/CD

```yaml
# .gitlab-ci.yml
stages:
  - build
  - deploy

variables:
  PROJECT_ID: your-project-id
  REGION: us-central1
  SERVICE_NAME: fakeai
  IMAGE: ${REGION}-docker.pkg.dev/${PROJECT_ID}/fakeai/fakeai

build:
  stage: build
  image: google/cloud-sdk:alpine
  services:
    - docker:dind
  script:
    - echo $GCP_SERVICE_KEY | gcloud auth activate-service-account --key-file=-
    - gcloud config set project $PROJECT_ID
    - gcloud auth configure-docker ${REGION}-docker.pkg.dev
    - docker build -t ${IMAGE}:${CI_COMMIT_SHA} .
    - docker push ${IMAGE}:${CI_COMMIT_SHA}
  only:
    - main

deploy:
  stage: deploy
  image: google/cloud-sdk:alpine
  script:
    - echo $GCP_SERVICE_KEY | gcloud auth activate-service-account --key-file=-
    - gcloud config set project $PROJECT_ID
    - |
      gcloud run deploy $SERVICE_NAME \
        --image ${IMAGE}:${CI_COMMIT_SHA} \
        --region $REGION \
        --platform managed \
        --allow-unauthenticated
  only:
    - main
```

### Cloud Build Trigger

```bash
# Create build trigger from GitHub
gcloud builds triggers create github \
  --repo-name=fakeai \
  --repo-owner=your-github-username \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

---

## Cost Optimization

### Pricing Components

1. **CPU**: Charged per vCPU-second
2. **Memory**: Charged per GB-second
3. **Requests**: First 2 million requests free per month
4. **Networking**: Egress traffic charges

### Cost Optimization Strategies

#### 1. Scale to Zero

```bash
# Allow scaling to zero when idle
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --min-instances 0

# Cost: $0 when no requests
# Trade-off: Cold starts
```

#### 2. Right-Size Resources

```bash
# Use minimum resources needed
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --memory 512Mi \
  --cpu 1

# Monitor and adjust based on metrics
```

#### 3. Enable CPU Throttling

```bash
# Throttle CPU between requests
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --cpu-throttling

# Saves ~50% on CPU costs
```

#### 4. Increase Concurrency

```bash
# Handle more requests per instance
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --concurrency 80

# Fewer instances = lower cost
```

#### 5. Use Cheaper Regions

Pricing varies by region. Choose cost-effective regions:
- `us-central1` (Iowa) - Often cheapest
- `us-east1` (South Carolina)
- `europe-west1` (Belgium)

### Cost Estimation

```bash
# Example calculation for 1 million requests/month:
# - 100ms average request time
# - 512MB memory
# - 1 vCPU

# Request cost: First 2M free
# CPU cost: 1M requests * 0.1s * $0.00002400/vCPU-s = $2.40
# Memory cost: 1M requests * 0.1s * 0.5GB * $0.00000250/GB-s = $0.13
# Total: ~$2.53/month
```

---

## Troubleshooting

### Common Issues

#### Issue: Container Fails to Start

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
  --limit 50

# Check container listens on correct port
# Cloud Run sets PORT environment variable
# Container must listen on this port
```

#### Issue: Health Check Failures

```bash
# Cloud Run expects HTTP 200 response on any path
# Container must respond within 10 seconds of startup

# Test locally
docker run -p 8080:8080 -e PORT=8080 fakeai:latest
curl http://localhost:8080/health
```

#### Issue: High Cold Start Latency

```bash
# Solutions:
# 1. Use minimum instances
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --min-instances 1

# 2. Enable CPU boost
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --cpu-boost

# 3. Optimize container image (use multi-stage build)
```

#### Issue: Out of Memory Errors

```bash
# Increase memory allocation
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --memory 1Gi

# Monitor memory usage
gcloud monitoring read "resource.type=cloud_run_revision AND metric.type=run.googleapis.com/container/memory/utilizations" \
  --filter="resource.labels.service_name=$SERVICE_NAME"
```

#### Issue: Request Timeout

```bash
# Increase timeout (max 3600s)
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --timeout 600

# Check application performance
```

### Debug Commands

```bash
# Get service details
gcloud run services describe $SERVICE_NAME --region $REGION

# List revisions
gcloud run revisions list --service $SERVICE_NAME --region $REGION

# Get revision details
gcloud run revisions describe REVISION_NAME --region $REGION

# View service URL
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"

# Test service
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)")
curl $SERVICE_URL/health
```

---

## Best Practices

### Container Best Practices

1. **Listen on PORT**: Always use `PORT` environment variable
2. **Fast Startup**: Optimize for quick container startup
3. **Stateless**: Don't rely on local disk or in-memory state
4. **Graceful Shutdown**: Handle SIGTERM signal properly
5. **Health Endpoints**: Implement /health for monitoring

### Security Best Practices

1. **Non-Root User**: Run container as non-root user
2. **Secrets Management**: Use Secret Manager for sensitive data
3. **IAM Roles**: Use service accounts with minimal permissions
4. **Authentication**: Require authentication for production
5. **HTTPS Only**: Never allow HTTP traffic

### Performance Best Practices

1. **Warm Pool**: Use min-instances for critical services
2. **Right-Size**: Match resources to actual needs
3. **Concurrency**: Tune concurrency based on workload
4. **CDN**: Use Cloud CDN for static content
5. **Connection Pooling**: Reuse connections when possible

---

## Production Checklist

- [ ] Container optimized (multi-stage build, minimal image)
- [ ] Health endpoint implemented
- [ ] Secrets stored in Secret Manager
- [ ] Service account with minimal permissions
- [ ] Custom domain configured with SSL
- [ ] Min instances set (1-5 for production)
- [ ] Resource limits appropriate
- [ ] Monitoring and alerts configured
- [ ] Logs being collected and analyzed
- [ ] CI/CD pipeline set up
- [ ] Cost monitoring enabled
- [ ] Backup/disaster recovery plan documented
- [ ] Load testing completed
- [ ] Security review passed

---

## Next Steps

1. Set up multi-region deployment for high availability
2. Implement Cloud CDN for better performance
3. Configure Cloud Armor for DDoS protection
4. Set up automated canary deployments
5. Implement comprehensive monitoring and alerting

For more information, see:
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- [Cloud Run Best Practices](https://cloud.google.com/run/docs/best-practices)
