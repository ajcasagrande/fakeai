# API Key Management Guide

This guide explains how to manage API keys in FakeAI for secure access control.

## Default Behavior (No Authentication)

By default, FakeAI runs **without authentication**. This is perfect for:
- Local development
- Testing
- Internal networks
- Quick prototyping

```bash
# No authentication required
fakeai-server
```

## Enabling Authentication

Authentication is automatically enabled when you provide API keys via the `--api-key` flag.

### Method 1: Direct Keys on Command Line

Pass keys directly as command-line arguments:

```bash
fakeai-server --api-key sk-test-key-1 --api-key sk-test-key-2
```

**Best for:**
- Quick testing
- Single-key scenarios
- Development environments

### Method 2: Keys from File

Store keys in a file and reference it:

```bash
fakeai-server --api-key /path/to/keys.txt
```

**File format:**
```
# API Keys for FakeAI
# Lines starting with # are comments
sk-production-key-1
sk-production-key-2

# Blank lines are ignored
sk-production-key-3
```

**Best for:**
- Production environments
- Managing many keys
- Team sharing
- Version control (with proper .gitignore)

### Method 3: Mix Direct Keys and Files

Combine both approaches:

```bash
fakeai-server \
  --api-key sk-admin-key \
  --api-key /etc/fakeai/team-keys.txt \
  --api-key /etc/fakeai/service-keys.txt
```

**Best for:**
- Complex setups
- Different key categories
- Gradual migration

## File Organization

### Recommended Structure

```
/etc/fakeai/
 api-keys.txt          # Main production keys
 team-keys.txt         # Team member keys
 service-keys.txt      # Service account keys
 archived-keys.txt     # Revoked keys (for reference)
```

### Example Production Setup

**Main keys file (`/etc/fakeai/api-keys.txt`):**
```
# Production API Keys
# Generated: 2025-01-15
# Owner: DevOps Team

# Service accounts
sk-prod-service-1-abc123def456
sk-prod-service-2-xyz789uvw012

# Team leads
sk-prod-alice-lead-key123
sk-prod-bob-lead-key456
```

**Start server:**
```bash
fakeai-server \
  --host 0.0.0.0 \
  --port 8000 \
  --api-key /etc/fakeai/api-keys.txt
```

## Security Best Practices

### 1. File Permissions

Protect your API key files:

```bash
# Set proper ownership
sudo chown fakeai:fakeai /etc/fakeai/api-keys.txt

# Restrict permissions (read-only for owner)
sudo chmod 400 /etc/fakeai/api-keys.txt
```

### 2. Version Control

**Never commit keys directly!**

Add to `.gitignore`:
```gitignore
# API Keys
api-keys.txt
*.key
*-keys.txt
```

Instead, commit a template:
```bash
# api-keys.txt.example
# Copy to api-keys.txt and add your keys
# sk-your-key-here
```

### 3. Key Rotation

Regularly rotate keys:

```bash
# 1. Generate new keys
echo "sk-new-key-$(date +%s)" >> /etc/fakeai/api-keys.txt

# 2. Update clients

# 3. Remove old keys
# Comment out or remove old keys from file

# 4. Restart server
sudo systemctl restart fakeai
```

### 4. Key Naming Convention

Use descriptive key prefixes:

```
sk-prod-{service}-{environment}-{random}
sk-dev-{username}-{random}
sk-test-{purpose}-{random}

Examples:
sk-prod-api-gateway-live-abc123
sk-dev-alice-local-xyz789
sk-test-integration-suite-def456
```

## Environment Variables

Alternative to CLI for automation:

```bash
# Set via environment
export FAKEAI_API_KEYS="sk-key1,sk-key2,sk-key3"
fakeai-server
```

**Note:** CLI arguments override environment variables.

## Validation

FakeAI validates API keys on every request:

```python
# Valid request
curl http://localhost:8000/v1/models \
  -H "Authorization: Bearer sk-valid-key"

# Invalid request (401 Unauthorized)
curl http://localhost:8000/v1/models \
  -H "Authorization: Bearer sk-invalid-key"
```

## Monitoring

Check active configuration:

```bash
# Server startup shows authentication status
fakeai-server --api-key /path/to/keys.txt
# Output:
#   • Authentication: ENABLED (5 keys configured)
```

## Troubleshooting

### Keys Not Working

1. **Check file path:**
   ```bash
   ls -la /path/to/keys.txt
   ```

2. **Check file permissions:**
   ```bash
   cat /path/to/keys.txt  # Should be readable
   ```

3. **Check file format:**
   ```bash
   # Each key on separate line, no extra whitespace
   cat -A /path/to/keys.txt
   ```

4. **Test with direct key:**
   ```bash
   fakeai-server --api-key sk-test-direct
   ```

### Authentication Not Enabled

Authentication only enables when keys are provided:

```bash
# No authentication (no keys)
fakeai-server

# Authentication enabled
fakeai-server --api-key sk-test
```

### Multiple Files Not Loading

Ensure all files are readable:

```bash
fakeai-server \
  --api-key /path/to/file1.txt \
  --api-key /path/to/file2.txt

# Check both files
ls -la /path/to/file1.txt /path/to/file2.txt
```

## Examples

### Development Team Setup

```bash
# Create team keys file
cat > team-keys.txt << 'EOF'
# Development Team Keys
sk-dev-alice-local-123
sk-dev-bob-local-456
sk-dev-charlie-local-789
EOF

# Start server
fakeai-server --api-key team-keys.txt
```

### CI/CD Pipeline

```bash
# .gitlab-ci.yml or .github/workflows/
- name: Start FakeAI
  run: |
    echo "$FAKEAI_API_KEY" > /tmp/key.txt
    fakeai-server --api-key /tmp/key.txt &
```

### Docker Compose

```yaml
version: '3.8'
services:
  fakeai:
    image: fakeai:latest
    command: fakeai-server --host 0.0.0.0 --api-key /keys/api-keys.txt
    volumes:
      - ./api-keys.txt:/keys/api-keys.txt:ro
    ports:
      - "8000:8000"
```

### Kubernetes

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fakeai-keys
data:
  api-keys.txt: |
    sk-prod-service-1
    sk-prod-service-2
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fakeai
spec:
  template:
    spec:
      containers:
      - name: fakeai
        image: fakeai:latest
        command: ["fakeai-server"]
        args:
          - "--host=0.0.0.0"
          - "--api-key=/etc/fakeai/api-keys.txt"
        volumeMounts:
        - name: keys
          mountPath: /etc/fakeai
      volumes:
      - name: keys
        configMap:
          name: fakeai-keys
```

## Summary

- **Default:** No authentication (open access)
- **Enable:** Use `--api-key` flag with keys or file paths
- **File format:** One key per line, comments with `#`, blank lines ignored
- **Security:** Protect key files with proper permissions
- **Best practice:** Use files for production, direct keys for development
- **Flexibility:** Mix direct keys and files as needed
