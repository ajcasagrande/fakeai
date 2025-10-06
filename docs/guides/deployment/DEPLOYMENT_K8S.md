# FakeAI Kubernetes Deployment Guide

This guide covers deploying FakeAI on Kubernetes clusters, including configuration, scaling, monitoring, and best practices.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Image Preparation](#docker-image-preparation)
3. [Kubernetes Manifests](#kubernetes-manifests)
4. [ConfigMap and Secrets](#configmap-and-secrets)
5. [Deployment](#deployment)
6. [Service Configuration](#service-configuration)
7. [Ingress Setup](#ingress-setup)
8. [Horizontal Pod Autoscaler](#horizontal-pod-autoscaler)
9. [Health Probes](#health-probes)
10. [Monitoring and Logging](#monitoring-and-logging)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

- kubectl installed and configured
- Docker installed
- Access to a Kubernetes cluster (minikube, GKE, EKS, AKS, or self-hosted)
- Container registry access (Docker Hub, GCR, ECR, or private registry)

### Kubernetes Cluster Requirements

- Kubernetes 1.20+
- Metrics Server installed (for HPA)
- Ingress controller installed (nginx, traefik, or cloud provider)
- Persistent storage (optional, for logs or state)

### Install Required Tools

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verify kubectl
kubectl version --client

# Install metrics-server (if not installed)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verify cluster access
kubectl cluster-info
kubectl get nodes
```

---

## Docker Image Preparation

### Step 1: Create Optimized Dockerfile

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

# Create non-root user
RUN useradd -m -u 1000 fakeai && \
    chown -R fakeai:fakeai /app

# Switch to non-root user
USER fakeai

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["fakeai-server", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Build and Push Image

```bash
# Build image
docker build -t fakeai:1.0.0 .

# Tag for registry
docker tag fakeai:1.0.0 your-registry.io/fakeai:1.0.0
docker tag fakeai:1.0.0 your-registry.io/fakeai:latest

# Push to registry
docker push your-registry.io/fakeai:1.0.0
docker push your-registry.io/fakeai:latest
```

### Multi-Architecture Build (Optional)

```bash
# Build for multiple platforms
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 \
  -t your-registry.io/fakeai:1.0.0 \
  -t your-registry.io/fakeai:latest \
  --push .
```

---

## Kubernetes Manifests

### Complete Deployment Stack

Create a directory structure for your manifests:

```bash
mkdir -p k8s/{base,overlays/production,overlays/staging}
```

### Namespace

```yaml
# k8s/base/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: fakeai
  labels:
    name: fakeai
    environment: production
```

### ConfigMap

```yaml
# k8s/base/configmap.yaml
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
  FAKEAI_REQUIRE_API_KEY: "true"
  FAKEAI_RATE_LIMIT_ENABLED: "false"
  FAKEAI_REQUESTS_PER_MINUTE: "10000"
```

### Secret

```yaml
# k8s/base/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: fakeai-secrets
  namespace: fakeai
type: Opaque
stringData:
  FAKEAI_API_KEYS: "sk-prod-key-1,sk-prod-key-2,sk-prod-key-3"
```

```bash
# Create secret from command line (alternative)
kubectl create secret generic fakeai-secrets \
  --from-literal=FAKEAI_API_KEYS="sk-key1,sk-key2" \
  -n fakeai
```

---

## Deployment

### Complete Deployment Manifest

```yaml
# k8s/base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fakeai
  namespace: fakeai
  labels:
    app: fakeai
    version: v1
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: fakeai
  template:
    metadata:
      labels:
        app: fakeai
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      # Security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault

      # Init containers (optional - for migrations, setup, etc.)
      initContainers:
      - name: init-check
        image: busybox:1.35
        command: ['sh', '-c', 'echo "Initializing FakeAI..." && sleep 2']

      containers:
      - name: fakeai
        image: your-registry.io/fakeai:1.0.0
        imagePullPolicy: IfNotPresent

        ports:
        - name: http
          containerPort: 8000
          protocol: TCP

        # Environment variables from ConfigMap
        envFrom:
        - configMapRef:
            name: fakeai-config
        - secretRef:
            name: fakeai-secrets

        # Resource limits and requests
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 512Mi

        # Liveness probe
        livenessProbe:
          httpGet:
            path: /health
            port: http
            scheme: HTTP
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3

        # Readiness probe
        readinessProbe:
          httpGet:
            path: /health
            port: http
            scheme: HTTP
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3

        # Startup probe (for slow-starting apps)
        startupProbe:
          httpGet:
            path: /health
            port: http
            scheme: HTTP
          initialDelaySeconds: 0
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 12

        # Security context
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false
          runAsNonRoot: true
          runAsUser: 1000
          capabilities:
            drop:
            - ALL

        # Lifecycle hooks
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]

      # Image pull secrets (if using private registry)
      imagePullSecrets:
      - name: registry-credentials

      # Node affinity (optional)
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - fakeai
              topologyKey: kubernetes.io/hostname

      # Tolerations (optional)
      tolerations:
      - key: "node.kubernetes.io/not-ready"
        operator: "Exists"
        effect: "NoExecute"
        tolerationSeconds: 300
```

### Apply Deployment

```bash
# Create namespace
kubectl apply -f k8s/base/namespace.yaml

# Create ConfigMap and Secret
kubectl apply -f k8s/base/configmap.yaml
kubectl apply -f k8s/base/secret.yaml

# Create Deployment
kubectl apply -f k8s/base/deployment.yaml

# Verify deployment
kubectl get deployments -n fakeai
kubectl get pods -n fakeai
kubectl logs -f -n fakeai -l app=fakeai
```

---

## Service Configuration

### ClusterIP Service (Internal)

```yaml
# k8s/base/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: fakeai
  namespace: fakeai
  labels:
    app: fakeai
spec:
  type: ClusterIP
  selector:
    app: fakeai
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
  sessionAffinity: None
```

### LoadBalancer Service (External)

```yaml
# k8s/base/service-lb.yaml
apiVersion: v1
kind: Service
metadata:
  name: fakeai-lb
  namespace: fakeai
  labels:
    app: fakeai
  annotations:
    # Cloud provider specific annotations
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-cross-zone-load-balancing-enabled: "true"
spec:
  type: LoadBalancer
  selector:
    app: fakeai
  ports:
  - name: http
    port: 80
    targetPort: 8000
    protocol: TCP
  - name: https
    port: 443
    targetPort: 8000
    protocol: TCP
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
```

### Headless Service (for StatefulSet)

```yaml
# k8s/base/service-headless.yaml
apiVersion: v1
kind: Service
metadata:
  name: fakeai-headless
  namespace: fakeai
  labels:
    app: fakeai
spec:
  clusterIP: None
  selector:
    app: fakeai
  ports:
  - name: http
    port: 8000
    targetPort: 8000
    protocol: TCP
```

### Apply Service

```bash
# Create service
kubectl apply -f k8s/base/service.yaml

# Verify service
kubectl get svc -n fakeai
kubectl describe svc fakeai -n fakeai

# Test service from within cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n fakeai -- \
  curl http://fakeai.fakeai.svc.cluster.local/health
```

---

## Ingress Setup

### Nginx Ingress

```yaml
# k8s/base/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fakeai-ingress
  namespace: fakeai
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/limit-connections: "10"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
spec:
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
              number: 80
```

### Traefik Ingress

```yaml
# k8s/base/ingress-traefik.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fakeai-ingress
  namespace: fakeai
  annotations:
    kubernetes.io/ingress.class: traefik
    traefik.ingress.kubernetes.io/router.entrypoints: websecure
    traefik.ingress.kubernetes.io/router.tls: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
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
              number: 80
```

### IngressRoute (Traefik CRD)

```yaml
# k8s/base/ingressroute.yaml
apiVersion: traefik.containo.us/v1alpha1
kind: IngressRoute
metadata:
  name: fakeai-ingressroute
  namespace: fakeai
spec:
  entryPoints:
    - websecure
  routes:
  - match: Host(`fakeai.example.com`)
    kind: Rule
    services:
    - name: fakeai
      port: 80
    middlewares:
    - name: rate-limit
  tls:
    certResolver: letsencrypt
```

### Middleware (Rate Limiting)

```yaml
# k8s/base/middleware.yaml
apiVersion: traefik.containo.us/v1alpha1
kind: Middleware
metadata:
  name: rate-limit
  namespace: fakeai
spec:
  rateLimit:
    average: 100
    burst: 50
    period: 1m
```

### Apply Ingress

```bash
# Install ingress-nginx (if not installed)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Create ingress
kubectl apply -f k8s/base/ingress.yaml

# Verify ingress
kubectl get ingress -n fakeai
kubectl describe ingress fakeai-ingress -n fakeai

# Test ingress
curl https://fakeai.example.com/health
```

---

## Horizontal Pod Autoscaler

### HPA Configuration

```yaml
# k8s/base/hpa.yaml
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
  maxReplicas: 20
  metrics:
  # CPU-based scaling
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  # Memory-based scaling
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  # Custom metric scaling (requests per second)
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 15
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Min
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 60
      selectPolicy: Max
```

### Vertical Pod Autoscaler (Optional)

```yaml
# k8s/base/vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: fakeai-vpa
  namespace: fakeai
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fakeai
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: fakeai
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: 2000m
        memory: 1Gi
      controlledResources:
      - cpu
      - memory
```

### Apply HPA

```bash
# Verify metrics-server is running
kubectl get deployment metrics-server -n kube-system

# Create HPA
kubectl apply -f k8s/base/hpa.yaml

# Verify HPA
kubectl get hpa -n fakeai
kubectl describe hpa fakeai-hpa -n fakeai

# Watch HPA in action
kubectl get hpa fakeai-hpa -n fakeai --watch

# Generate load for testing
kubectl run -it --rm load-generator --image=busybox --restart=Never -n fakeai -- \
  sh -c "while true; do wget -q -O- http://fakeai.fakeai.svc.cluster.local/v1/models; done"
```

---

## Health Probes

### Comprehensive Health Check Configuration

```yaml
# Health probes explained
containers:
- name: fakeai
  # ...

  # Liveness Probe: Is the container alive?
  # If this fails, Kubernetes will restart the container
  livenessProbe:
    httpGet:
      path: /health
      port: 8000
      httpHeaders:
      - name: X-Health-Check
        value: liveness
    initialDelaySeconds: 30    # Wait 30s before first check
    periodSeconds: 10          # Check every 10s
    timeoutSeconds: 5          # Timeout after 5s
    successThreshold: 1        # 1 success = healthy
    failureThreshold: 3        # 3 failures = restart

  # Readiness Probe: Is the container ready to serve traffic?
  # If this fails, traffic will be removed from this pod
  readinessProbe:
    httpGet:
      path: /health
      port: 8000
      httpHeaders:
      - name: X-Health-Check
        value: readiness
    initialDelaySeconds: 10    # Wait 10s before first check
    periodSeconds: 5           # Check every 5s
    timeoutSeconds: 3          # Timeout after 3s
    successThreshold: 1        # 1 success = ready
    failureThreshold: 3        # 3 failures = not ready

  # Startup Probe: Has the container started successfully?
  # Disables liveness/readiness checks until this succeeds
  startupProbe:
    httpGet:
      path: /health
      port: 8000
      httpHeaders:
      - name: X-Health-Check
        value: startup
    initialDelaySeconds: 0     # Start immediately
    periodSeconds: 5           # Check every 5s
    timeoutSeconds: 3          # Timeout after 3s
    successThreshold: 1        # 1 success = started
    failureThreshold: 12       # Up to 60s total (12 * 5s)
```

### Alternative Probe Types

```yaml
# TCP Socket Probe
livenessProbe:
  tcpSocket:
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 10

# Exec Probe
livenessProbe:
  exec:
    command:
    - /bin/sh
    - -c
    - curl -f http://localhost:8000/health || exit 1
  initialDelaySeconds: 30
  periodSeconds: 10

# gRPC Probe (Kubernetes 1.24+)
livenessProbe:
  grpc:
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 10
```

---

## Monitoring and Logging

### Prometheus Monitoring

```yaml
# k8s/base/servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: fakeai
  namespace: fakeai
  labels:
    app: fakeai
spec:
  selector:
    matchLabels:
      app: fakeai
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
```

### Grafana Dashboard ConfigMap

```yaml
# k8s/base/dashboard.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fakeai-dashboard
  namespace: fakeai
  labels:
    grafana_dashboard: "1"
data:
  fakeai-dashboard.json: |
    {
      "dashboard": {
        "title": "FakeAI Metrics",
        "panels": [
          {
            "title": "Request Rate",
            "targets": [
              {
                "expr": "rate(http_requests_total{namespace=\"fakeai\"}[5m])"
              }
            ]
          }
        ]
      }
    }
```

### Logging with Fluentd

```yaml
# k8s/base/fluentd-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-config
  namespace: kube-system
data:
  fluent.conf: |
    <source>
      @type tail
      path /var/log/containers/fakeai-*.log
      pos_file /var/log/fluentd-fakeai.pos
      tag fakeai.*
      <parse>
        @type json
        time_format %Y-%m-%dT%H:%M:%S.%NZ
      </parse>
    </source>

    <filter fakeai.**>
      @type parser
      key_name log
      <parse>
        @type json
      </parse>
    </filter>

    <match fakeai.**>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      logstash_format true
      logstash_prefix fakeai
    </match>
```

### PodMonitor for Detailed Metrics

```yaml
# k8s/base/podmonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: fakeai
  namespace: fakeai
spec:
  selector:
    matchLabels:
      app: fakeai
  podMetricsEndpoints:
  - port: http
    path: /metrics
    interval: 30s
```

---

## Advanced Configurations

### NetworkPolicy

```yaml
# k8s/base/networkpolicy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: fakeai-network-policy
  namespace: fakeai
spec:
  podSelector:
    matchLabels:
      app: fakeai
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: fakeai
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
  - to:
    - namespaceSelector: {}
```

### PodDisruptionBudget

```yaml
# k8s/base/pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: fakeai-pdb
  namespace: fakeai
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: fakeai
```

### ResourceQuota

```yaml
# k8s/base/resourcequota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: fakeai-quota
  namespace: fakeai
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    persistentvolumeclaims: "5"
    services.loadbalancers: "2"
```

### LimitRange

```yaml
# k8s/base/limitrange.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: fakeai-limits
  namespace: fakeai
spec:
  limits:
  - max:
      cpu: "2"
      memory: 2Gi
    min:
      cpu: 100m
      memory: 128Mi
    default:
      cpu: 500m
      memory: 512Mi
    defaultRequest:
      cpu: 250m
      memory: 256Mi
    type: Container
```

---

## Kustomize Configuration

### Base Kustomization

```yaml
# k8s/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: fakeai

resources:
- namespace.yaml
- configmap.yaml
- secret.yaml
- deployment.yaml
- service.yaml
- ingress.yaml
- hpa.yaml
- pdb.yaml
- networkpolicy.yaml

commonLabels:
  app: fakeai
  managed-by: kustomize

images:
- name: your-registry.io/fakeai
  newTag: 1.0.0
```

### Production Overlay

```yaml
# k8s/overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: fakeai

bases:
- ../../base

patchesStrategicMerge:
- deployment-patch.yaml
- hpa-patch.yaml

configMapGenerator:
- name: fakeai-config
  behavior: merge
  literals:
  - FAKEAI_DEBUG=false
  - FAKEAI_RESPONSE_DELAY=0.3

images:
- name: your-registry.io/fakeai
  newTag: 1.0.0
```

```yaml
# k8s/overlays/production/deployment-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fakeai
spec:
  replicas: 5
  template:
    spec:
      containers:
      - name: fakeai
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 1Gi
```

### Apply with Kustomize

```bash
# Build and preview
kubectl kustomize k8s/overlays/production

# Apply production configuration
kubectl apply -k k8s/overlays/production

# Delete resources
kubectl delete -k k8s/overlays/production
```

---

## Troubleshooting

### Common Issues

#### Issue: Pods Not Starting

```bash
# Check pod status
kubectl get pods -n fakeai

# Describe pod for events
kubectl describe pod <pod-name> -n fakeai

# Check logs
kubectl logs <pod-name> -n fakeai

# Check previous container logs (if crashed)
kubectl logs <pod-name> -n fakeai --previous
```

#### Issue: Image Pull Errors

```bash
# Check image pull secret
kubectl get secret registry-credentials -n fakeai -o yaml

# Create image pull secret
kubectl create secret docker-registry registry-credentials \
  --docker-server=your-registry.io \
  --docker-username=your-username \
  --docker-password=your-password \
  --docker-email=your-email \
  -n fakeai
```

#### Issue: Service Not Accessible

```bash
# Check service
kubectl get svc -n fakeai
kubectl describe svc fakeai -n fakeai

# Check endpoints
kubectl get endpoints -n fakeai

# Port forward for testing
kubectl port-forward svc/fakeai 8000:80 -n fakeai
curl http://localhost:8000/health
```

#### Issue: HPA Not Scaling

```bash
# Check HPA status
kubectl get hpa -n fakeai
kubectl describe hpa fakeai-hpa -n fakeai

# Check metrics-server
kubectl get deployment metrics-server -n kube-system
kubectl logs -n kube-system deployment/metrics-server

# Check pod metrics
kubectl top pods -n fakeai
kubectl top nodes
```

#### Issue: Ingress Not Working

```bash
# Check ingress
kubectl get ingress -n fakeai
kubectl describe ingress fakeai-ingress -n fakeai

# Check ingress controller
kubectl get pods -n ingress-nginx
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Test DNS resolution
nslookup fakeai.example.com
```

### Debug Commands

```bash
# Execute command in pod
kubectl exec -it <pod-name> -n fakeai -- /bin/sh

# Copy files from pod
kubectl cp fakeai/<pod-name>:/app/logs ./logs

# View events
kubectl get events -n fakeai --sort-by='.lastTimestamp'

# Watch resources
kubectl get pods -n fakeai -w

# Debug with ephemeral container (Kubernetes 1.23+)
kubectl debug <pod-name> -n fakeai --image=busybox --target=fakeai
```

---

## Best Practices

### Resource Management

1. **Set Resource Requests/Limits**: Always define CPU and memory
2. **Use HPA**: Auto-scale based on metrics
3. **PodDisruptionBudget**: Ensure availability during updates
4. **Resource Quotas**: Prevent resource exhaustion

### Security

1. **Run as Non-Root**: Use security contexts
2. **Read-Only Root Filesystem**: Prevent modifications
3. **Network Policies**: Restrict traffic
4. **Secrets Management**: Use external secrets operator
5. **Image Scanning**: Scan images for vulnerabilities

### Reliability

1. **Multiple Replicas**: At least 3 for high availability
2. **Pod Anti-Affinity**: Spread pods across nodes
3. **Health Probes**: Implement all three probe types
4. **Graceful Shutdown**: Use preStop hooks
5. **Rolling Updates**: Zero-downtime deployments

### Monitoring

1. **Prometheus Metrics**: Export application metrics
2. **Log Aggregation**: Centralize logs
3. **Distributed Tracing**: Use Jaeger or Zipkin
4. **Alerting**: Set up alerts for critical issues
5. **Dashboards**: Create Grafana dashboards

---

## Production Checklist

- [ ] Resource requests and limits set
- [ ] Health probes configured
- [ ] HPA configured
- [ ] PDB configured
- [ ] Network policies applied
- [ ] Ingress with TLS configured
- [ ] Monitoring and logging set up
- [ ] Secrets externalized
- [ ] Image from trusted registry
- [ ] Resource quotas defined
- [ ] Backup strategy in place
- [ ] Disaster recovery plan documented
- [ ] Load testing completed
- [ ] Security scan passed

---

## Next Steps

1. Set up GitOps with ArgoCD or Flux
2. Implement Canary deployments
3. Add service mesh (Istio/Linkerd)
4. Configure mutual TLS
5. Implement advanced observability

For more information, see:
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize Documentation](https://kustomize.io/)
- [Helm Documentation](https://helm.sh/docs/)
