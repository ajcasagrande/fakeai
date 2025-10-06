# FakeAI Azure Deployment Guide

This guide covers deploying FakeAI on Microsoft Azure using Azure Container Instances (ACI), Azure App Service, and Azure Kubernetes Service (AKS).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options Overview](#deployment-options-overview)
3. [Azure Container Instances (ACI)](#azure-container-instances-aci)
4. [Azure App Service](#azure-app-service)
5. [Azure Kubernetes Service (AKS)](#azure-kubernetes-service-aks)
6. [Configuration and Secrets](#configuration-and-secrets)
7. [Custom Domains and SSL](#custom-domains-and-ssl)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [CI/CD Integration](#cicd-integration)
10. [Cost Optimization](#cost-optimization)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

- Azure CLI installed
- Docker installed
- Azure subscription with billing enabled
- Appropriate Azure permissions

### Install Azure CLI

```bash
# Install Azure CLI (Linux)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install Azure CLI (macOS)
brew update && brew install azure-cli

# Install Azure CLI (Windows)
# Download from: https://aka.ms/installazurecliwindows

# Verify installation
az --version
```

### Login and Setup

```bash
# Login to Azure
az login

# List subscriptions
az account list --output table

# Set default subscription
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Set default location
az configure --defaults location=eastus

# Create resource group
az group create --name fakeai-rg --location eastus
```

### Environment Variables

```bash
# Set common variables
export RESOURCE_GROUP="fakeai-rg"
export LOCATION="eastus"
export ACR_NAME="fakeaiacr"
export APP_NAME="fakeai"
```

---

## Deployment Options Overview

### Comparison Matrix

| Feature | Container Instances (ACI) | App Service | AKS |
|---------|--------------------------|-------------|-----|
| **Management** | Fully managed | Fully managed | Self-managed |
| **Scaling** | Manual | Auto-scale | Auto-scale + HPA |
| **Cost** | Pay per second | Pay per tier | Pay for VMs |
| **Cold Start** | Fast | Faster | N/A |
| **Complexity** | Simple | Simple | Complex |
| **Best For** | Dev/Test, Batch | Web apps, APIs | Production, Microservices |

### When to Use Each

**Azure Container Instances (ACI)**
- Quick deployment for testing
- Batch processing jobs
- CI/CD build agents
- Cost-effective for low-traffic scenarios

**Azure App Service**
- Production web applications
- Consistent traffic patterns
- Need auto-scaling
- Integrated CI/CD

**Azure Kubernetes Service (AKS)**
- Complex microservices
- High availability requirements
- Advanced networking needs
- Multi-region deployments

---

## Azure Container Instances (ACI)

Azure Container Instances provides the fastest and simplest way to run a container in Azure.

### Step 1: Create Azure Container Registry

```bash
# Create ACR
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --location $LOCATION

# Enable admin access (for quick testing)
az acr update --name $ACR_NAME --admin-enabled true

# Get credentials
az acr credential show --name $ACR_NAME

# Login to ACR
az acr login --name $ACR_NAME
```

### Step 2: Build and Push Container

```bash
# Build image locally
docker build -t fakeai:latest .

# Tag for ACR
docker tag fakeai:latest $ACR_NAME.azurecr.io/fakeai:latest

# Push to ACR
docker push $ACR_NAME.azurecr.io/fakeai:latest

# Or build directly in ACR (recommended)
az acr build \
  --registry $ACR_NAME \
  --image fakeai:latest \
  --file Dockerfile \
  .
```

### Step 3: Create Container Instance

```bash
# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query "username" -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

# Create container instance
az container create \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-aci \
  --image $ACR_NAME.azurecr.io/fakeai:latest \
  --registry-login-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --dns-name-label fakeai-aci \
  --ports 8000 \
  --cpu 1 \
  --memory 1.5 \
  --environment-variables \
    FAKEAI_HOST=0.0.0.0 \
    FAKEAI_PORT=8000 \
    FAKEAI_DEBUG=false \
    FAKEAI_RESPONSE_DELAY=0.5 \
    FAKEAI_REQUIRE_API_KEY=true \
  --secure-environment-variables \
    FAKEAI_API_KEYS=sk-key1,sk-key2 \
  --location $LOCATION
```

### Step 4: Verify Deployment

```bash
# Get container status
az container show \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-aci \
  --output table

# Get container logs
az container logs \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-aci

# Get FQDN
FQDN=$(az container show \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-aci \
  --query ipAddress.fqdn \
  --output tsv)

# Test endpoint
curl http://$FQDN:8000/health
curl http://$FQDN:8000/v1/models
```

### ACI Advanced Configuration

#### Using YAML Definition

```yaml
# aci-deployment.yaml
apiVersion: '2021-09-01'
location: eastus
name: fakeai-aci
properties:
  containers:
  - name: fakeai
    properties:
      image: fakeaiacr.azurecr.io/fakeai:latest
      resources:
        requests:
          cpu: 1.0
          memoryInGb: 1.5
      ports:
      - port: 8000
        protocol: TCP
      environmentVariables:
      - name: FAKEAI_HOST
        value: "0.0.0.0"
      - name: FAKEAI_PORT
        value: "8000"
      - name: FAKEAI_DEBUG
        value: "false"
      - name: FAKEAI_RESPONSE_DELAY
        value: "0.5"
      - name: FAKEAI_REQUIRE_API_KEY
        value: "true"
      - name: FAKEAI_API_KEYS
        secureValue: "sk-key1,sk-key2"
      livenessProbe:
        httpGet:
          path: /health
          port: 8000
        periodSeconds: 10
        failureThreshold: 3
      readinessProbe:
        httpGet:
          path: /health
          port: 8000
        periodSeconds: 5
        failureThreshold: 3
  osType: Linux
  ipAddress:
    type: Public
    ports:
    - protocol: TCP
      port: 8000
    dnsNameLabel: fakeai-aci
  imageRegistryCredentials:
  - server: fakeaiacr.azurecr.io
    username: fakeaiacr
    password: <password>
  restartPolicy: Always
tags:
  environment: production
  application: fakeai
type: Microsoft.ContainerInstance/containerGroups
```

```bash
# Deploy from YAML
az container create \
  --resource-group $RESOURCE_GROUP \
  --file aci-deployment.yaml
```

#### Using Managed Identity (Recommended)

```bash
# Create user-assigned managed identity
az identity create \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-identity

# Get identity ID
IDENTITY_ID=$(az identity show \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-identity \
  --query id \
  --output tsv)

# Grant ACR pull permission to identity
az role assignment create \
  --assignee $(az identity show --resource-group $RESOURCE_GROUP --name fakeai-identity --query principalId -o tsv) \
  --role AcrPull \
  --scope $(az acr show --name $ACR_NAME --query id -o tsv)

# Create container with managed identity
az container create \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-aci \
  --image $ACR_NAME.azurecr.io/fakeai:latest \
  --acr-identity $IDENTITY_ID \
  --assign-identity $IDENTITY_ID \
  --dns-name-label fakeai-aci \
  --ports 8000 \
  --cpu 1 \
  --memory 1.5
```

### ACI with Azure Key Vault

```bash
# Create Key Vault
az keyvault create \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-kv \
  --location $LOCATION

# Store secret
az keyvault secret set \
  --vault-name fakeai-kv \
  --name api-keys \
  --value "sk-key1,sk-key2,sk-key3"

# Grant identity access to Key Vault
az keyvault set-policy \
  --name fakeai-kv \
  --object-id $(az identity show --resource-group $RESOURCE_GROUP --name fakeai-identity --query principalId -o tsv) \
  --secret-permissions get

# Reference secret in container
# Note: Requires Azure CLI extension
az container create \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-aci \
  --image $ACR_NAME.azurecr.io/fakeai:latest \
  --assign-identity $IDENTITY_ID \
  --secrets \
    FAKEAI_API_KEYS=keyvault:fakeai-kv:api-keys
```

---

## Azure App Service

Azure App Service provides a fully managed platform for building, deploying, and scaling web apps.

### Step 1: Create App Service Plan

```bash
# Create Linux App Service Plan
az appservice plan create \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-plan \
  --is-linux \
  --sku B1 \
  --location $LOCATION

# For production, use higher SKU (S1, P1V2, P2V2, etc.)
# az appservice plan create \
#   --resource-group $RESOURCE_GROUP \
#   --name fakeai-plan \
#   --is-linux \
#   --sku P1V2 \
#   --location $LOCATION
```

### Step 2: Create Web App

```bash
# Create web app with container
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan fakeai-plan \
  --name $APP_NAME \
  --deployment-container-image-name $ACR_NAME.azurecr.io/fakeai:latest

# Configure ACR credentials
az webapp config container set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --docker-custom-image-name $ACR_NAME.azurecr.io/fakeai:latest \
  --docker-registry-server-url https://$ACR_NAME.azurecr.io \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD

# Or use managed identity (recommended)
az webapp identity assign \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME

# Grant ACR pull permission
az role assignment create \
  --assignee $(az webapp identity show --resource-group $RESOURCE_GROUP --name $APP_NAME --query principalId -o tsv) \
  --role AcrPull \
  --scope $(az acr show --name $ACR_NAME --query id -o tsv)

az webapp config container set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --docker-custom-image-name $ACR_NAME.azurecr.io/fakeai:latest \
  --docker-registry-server-url https://$ACR_NAME.azurecr.io
```

### Step 3: Configure App Settings

```bash
# Set environment variables
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    FAKEAI_HOST=0.0.0.0 \
    FAKEAI_PORT=8000 \
    FAKEAI_DEBUG=false \
    FAKEAI_RESPONSE_DELAY=0.5 \
    FAKEAI_RANDOM_DELAY=true \
    FAKEAI_REQUIRE_API_KEY=true \
    WEBSITES_PORT=8000

# Set secret from Key Vault (recommended)
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    FAKEAI_API_KEYS="@Microsoft.KeyVault(SecretUri=https://fakeai-kv.vault.azure.net/secrets/api-keys/)"
```

### Step 4: Configure Health Check

```bash
# Enable health check
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --health-check-path "/health"

# Configure container settings
az webapp config set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --always-on true \
  --http20-enabled true
```

### Step 5: Configure Auto-Scaling

```bash
# Enable auto-scaling (requires S1 or higher tier)
az monitor autoscale create \
  --resource-group $RESOURCE_GROUP \
  --resource $APP_NAME \
  --resource-type Microsoft.Web/serverfarms \
  --name fakeai-autoscale \
  --min-count 1 \
  --max-count 10 \
  --count 2

# Scale up rule (CPU > 70%)
az monitor autoscale rule create \
  --resource-group $RESOURCE_GROUP \
  --autoscale-name fakeai-autoscale \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 2

# Scale down rule (CPU < 30%)
az monitor autoscale rule create \
  --resource-group $RESOURCE_GROUP \
  --autoscale-name fakeai-autoscale \
  --condition "Percentage CPU < 30 avg 5m" \
  --scale in 1
```

### Step 6: Verify Deployment

```bash
# Get app URL
APP_URL=$(az webapp show \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --query defaultHostName \
  --output tsv)

# Test endpoint
curl https://$APP_URL/health
curl https://$APP_URL/v1/models

# View logs
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME
```

### App Service Deployment Slots

```bash
# Create staging slot
az webapp deployment slot create \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --slot staging

# Deploy to staging
az webapp config container set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --slot staging \
  --docker-custom-image-name $ACR_NAME.azurecr.io/fakeai:latest

# Test staging
STAGING_URL=$(az webapp show \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --slot staging \
  --query defaultHostName \
  --output tsv)

curl https://$STAGING_URL/health

# Swap slots (blue-green deployment)
az webapp deployment slot swap \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --slot staging \
  --target-slot production
```

---

## Azure Kubernetes Service (AKS)

For production deployments requiring advanced orchestration, use AKS.

### Step 1: Create AKS Cluster

```bash
# Create AKS cluster
az aks create \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-aks \
  --node-count 3 \
  --node-vm-size Standard_D2s_v3 \
  --enable-managed-identity \
  --generate-ssh-keys \
  --attach-acr $ACR_NAME \
  --enable-addons monitoring \
  --location $LOCATION

# Get credentials
az aks get-credentials \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-aks

# Verify connection
kubectl get nodes
```

### Step 2: Deploy to AKS

Use Kubernetes manifests from the [Kubernetes Deployment Guide](DEPLOYMENT_K8S.md).

```bash
# Create namespace
kubectl create namespace fakeai

# Create ConfigMap
kubectl create configmap fakeai-config \
  --from-literal=FAKEAI_HOST=0.0.0.0 \
  --from-literal=FAKEAI_PORT=8000 \
  --from-literal=FAKEAI_DEBUG=false \
  --from-literal=FAKEAI_RESPONSE_DELAY=0.5 \
  --from-literal=FAKEAI_REQUIRE_API_KEY=true \
  -n fakeai

# Create Secret
kubectl create secret generic fakeai-secrets \
  --from-literal=FAKEAI_API_KEYS=sk-key1,sk-key2 \
  -n fakeai

# Create Deployment
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fakeai
  namespace: fakeai
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
        image: $ACR_NAME.azurecr.io/fakeai:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: fakeai-config
        - secretRef:
            name: fakeai-secrets
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
EOF

# Create Service
kubectl apply -f - <<EOF
apiVersion: v1
kind: Service
metadata:
  name: fakeai
  namespace: fakeai
spec:
  type: LoadBalancer
  selector:
    app: fakeai
  ports:
  - port: 80
    targetPort: 8000
EOF

# Wait for external IP
kubectl get service fakeai -n fakeai --watch
```

### Step 3: Configure Ingress

```bash
# Install nginx ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Create Ingress
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fakeai-ingress
  namespace: fakeai
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
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
EOF
```

---

## Configuration and Secrets

### Azure Key Vault Integration

#### For ACI

```bash
# Reference secret in environment variable
az container create \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-aci \
  --image $ACR_NAME.azurecr.io/fakeai:latest \
  --assign-identity $IDENTITY_ID \
  --environment-variables \
    FAKEAI_API_KEYS=@keyvault:fakeai-kv:api-keys
```

#### For App Service

```bash
# Reference Key Vault secret
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    FAKEAI_API_KEYS="@Microsoft.KeyVault(SecretUri=https://fakeai-kv.vault.azure.net/secrets/api-keys/)"
```

#### For AKS

```bash
# Install Azure Key Vault Provider for Secrets Store CSI Driver
az aks enable-addons \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-aks \
  --addons azure-keyvault-secrets-provider

# Create SecretProviderClass
kubectl apply -f - <<EOF
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: azure-kvname
  namespace: fakeai
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "<client-id>"
    keyvaultName: fakeai-kv
    objects: |
      array:
        - |
          objectName: api-keys
          objectType: secret
          objectVersion: ""
    tenantId: "<tenant-id>"
EOF
```

---

## Custom Domains and SSL

### App Service Custom Domain

```bash
# Add custom domain
az webapp config hostname add \
  --resource-group $RESOURCE_GROUP \
  --webapp-name $APP_NAME \
  --hostname fakeai.example.com

# Bind SSL certificate (App Service Managed Certificate)
az webapp config ssl create \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --hostname fakeai.example.com

az webapp config ssl bind \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --certificate-thumbprint <thumbprint> \
  --ssl-type SNI
```

### Application Gateway for AKS

```bash
# Create Application Gateway
az network application-gateway create \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-appgw \
  --location $LOCATION \
  --sku Standard_v2 \
  --capacity 2 \
  --vnet-name aks-vnet \
  --subnet appgw-subnet \
  --http-settings-cookie-based-affinity Disabled \
  --http-settings-port 80 \
  --http-settings-protocol Http

# Install Application Gateway Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/Azure/application-gateway-kubernetes-ingress/master/docs/examples/aspnetapp.yaml
```

---

## Monitoring and Logging

### Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --resource-group $RESOURCE_GROUP \
  --app fakeai-insights \
  --location $LOCATION \
  --application-type web

# Get instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --resource-group $RESOURCE_GROUP \
  --app fakeai-insights \
  --query instrumentationKey \
  --output tsv)

# Configure App Service
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY \
    APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=$INSTRUMENTATION_KEY"
```

### Log Analytics

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --workspace-name fakeai-logs \
  --location $LOCATION

# Enable container insights for AKS
az aks enable-addons \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-aks \
  --addons monitoring \
  --workspace-resource-id $(az monitor log-analytics workspace show --resource-group $RESOURCE_GROUP --workspace-name fakeai-logs --query id -o tsv)
```

### View Logs

```bash
# ACI logs
az container logs \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-aci

# App Service logs
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME

# AKS logs
kubectl logs -f -n fakeai -l app=fakeai
```

---

## CI/CD Integration

### Azure DevOps Pipeline

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
    - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  dockerRegistryServiceConnection: 'acr-connection'
  imageRepository: 'fakeai'
  containerRegistry: 'fakeaiacr.azurecr.io'
  dockerfilePath: 'Dockerfile'
  tag: '$(Build.BuildId)'

stages:
- stage: Build
  displayName: Build and push image
  jobs:
  - job: Build
    displayName: Build
    steps:
    - task: Docker@2
      displayName: Build and push image
      inputs:
        command: buildAndPush
        repository: $(imageRepository)
        dockerfile: $(dockerfilePath)
        containerRegistry: $(dockerRegistryServiceConnection)
        tags: |
          $(tag)
          latest

- stage: Deploy
  displayName: Deploy to App Service
  dependsOn: Build
  jobs:
  - deployment: Deploy
    displayName: Deploy
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - task: AzureWebAppContainer@1
            displayName: 'Deploy to Azure App Service'
            inputs:
              azureSubscription: 'azure-subscription'
              appName: 'fakeai'
              containers: '$(containerRegistry)/$(imageRepository):$(tag)'
```

### GitHub Actions

```yaml
# .github/workflows/azure-deploy.yml
name: Deploy to Azure

on:
  push:
    branches:
      - main

env:
  AZURE_WEBAPP_NAME: fakeai
  CONTAINER_REGISTRY: fakeaiacr.azurecr.io

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Login to Azure
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}

    - name: Login to ACR
      run: |
        az acr login --name fakeaiacr

    - name: Build and push image
      run: |
        docker build -t ${{ env.CONTAINER_REGISTRY }}/fakeai:${{ github.sha }} .
        docker push ${{ env.CONTAINER_REGISTRY }}/fakeai:${{ github.sha }}

    - name: Deploy to App Service
      uses: azure/webapps-deploy@v2
      with:
        app-name: ${{ env.AZURE_WEBAPP_NAME }}
        images: ${{ env.CONTAINER_REGISTRY }}/fakeai:${{ github.sha }}
```

---

## Cost Optimization

### Pricing Comparison

| Service | Estimated Cost (per month) | Best For |
|---------|---------------------------|----------|
| **ACI** | $30-50 (1 CPU, 1.5GB, 730 hrs) | Dev/Test |
| **App Service** | $55+ (B1), $200+ (P1V2) | Production Web Apps |
| **AKS** | $145+ (3 D2s_v3 nodes) | Enterprise |

### Cost Optimization Strategies

#### ACI Cost Savings

```bash
# Use lower CPU/memory
az container create \
  --cpu 0.5 \
  --memory 1

# Delete when not in use
az container delete \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-aci \
  --yes
```

#### App Service Cost Savings

```bash
# Use lower tier for dev/test
az appservice plan create \
  --sku B1  # $55/month vs P1V2 $200/month

# Stop app when not in use
az webapp stop \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME
```

#### AKS Cost Savings

```bash
# Use fewer/smaller nodes
az aks create \
  --node-count 2 \
  --node-vm-size Standard_B2s

# Enable cluster autoscaler
az aks update \
  --resource-group $RESOURCE_GROUP \
  --name fakeai-aks \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 5

# Use spot instances
az aks nodepool add \
  --resource-group $RESOURCE_GROUP \
  --cluster-name fakeai-aks \
  --name spotpool \
  --priority Spot \
  --eviction-policy Delete \
  --spot-max-price -1 \
  --node-count 2
```

---

## Troubleshooting

### Common Issues

#### Issue: Container Won't Start (ACI)

```bash
# View logs
az container logs --resource-group $RESOURCE_GROUP --name fakeai-aci

# View container state
az container show --resource-group $RESOURCE_GROUP --name fakeai-aci --query containers[0].instanceView.currentState
```

#### Issue: App Service Container Crash

```bash
# Enable logging
az webapp log config \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --docker-container-logging filesystem

# View logs
az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME
```

#### Issue: ACR Authentication Failures

```bash
# Verify credentials
az acr credential show --name $ACR_NAME

# Test login
docker login $ACR_NAME.azurecr.io

# Use managed identity instead
az webapp identity assign --resource-group $RESOURCE_GROUP --name $APP_NAME
```

---

## Best Practices

1. **Use Managed Identity**: Avoid storing credentials
2. **Store Secrets in Key Vault**: Don't use environment variables for secrets
3. **Enable Auto-Scaling**: Handle variable load
4. **Use Deployment Slots**: Zero-downtime deployments
5. **Monitor with Application Insights**: Track performance and errors
6. **Enable Health Checks**: Detect and restart failed instances
7. **Use Private Networking**: Secure communication between services
8. **Tag Resources**: Organize and track costs

---

## Production Checklist

- [ ] Managed identity configured
- [ ] Secrets stored in Key Vault
- [ ] Health check endpoint configured
- [ ] Auto-scaling enabled
- [ ] SSL/TLS configured
- [ ] Monitoring and logging set up
- [ ] Deployment slots configured (App Service)
- [ ] Backup strategy in place
- [ ] Cost alerts configured
- [ ] Security scan completed

---

## Next Steps

1. Configure Azure Front Door for global distribution
2. Implement Azure API Management for API gateway
3. Set up Azure DevOps for CI/CD
4. Configure disaster recovery
5. Implement comprehensive monitoring

For more information, see:
- [Azure Container Instances Documentation](https://docs.microsoft.com/azure/container-instances/)
- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)
- [Azure Kubernetes Service Documentation](https://docs.microsoft.com/azure/aks/)
