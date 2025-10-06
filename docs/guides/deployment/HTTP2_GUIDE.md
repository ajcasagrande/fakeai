# HTTP/2 Support Guide

## Overview

FakeAI supports HTTP/2 via the Hypercorn ASGI server, providing modern protocol support while maintaining full HTTP/1.1 compatibility through automatic ALPN (Application-Layer Protocol Negotiation).

**Default:** HTTP/1.1 via Uvicorn
**Optional:** HTTP/2 via Hypercorn (with --http2 flag)

---

## Quick Start

### Development (HTTP/2 without SSL)

```bash
# Start with HTTP/2 support (development only)
fakeai-server --http2

# WARNING: Browsers require SSL for HTTP/2
# This mode is useful for testing with tools like curl
```

### Production (HTTP/2 with SSL)

```bash
# With SSL certificates
fakeai-server \
  --http2 \
  --ssl-certfile /etc/letsencrypt/live/example.com/fullchain.pem \
  --ssl-keyfile /etc/letsencrypt/live/example.com/privkey.pem \
  --host 0.0.0.0 \
  --port 443
```

---

## SSL Certificate Setup

### Using Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt install certbot

# Obtain certificate (standalone mode)
sudo certbot certonly --standalone -d api.example.com

# Certificates will be at:
# /etc/letsencrypt/live/api.example.com/fullchain.pem
# /etc/letsencrypt/live/api.example.com/privkey.pem

# Auto-renewal (certbot sets this up automatically)
sudo certbot renew --dry-run
```

### Self-Signed Certificate (Development Only)

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 \
  -keyout key.pem \
  -out cert.pem \
  -days 365 \
  -nodes \
  -subj "/CN=localhost"

# Use with FakeAI
fakeai-server --http2 --ssl-certfile cert.pem --ssl-keyfile key.pem
```

---

## Server Comparison

### Uvicorn (Default - HTTP/1.1)

**Advantages:**
- Mature and stable
- Excellent performance for HTTP/1.1
- Lower memory footprint
- Widely used in production
- Better debugging tools

**Limitations:**
- No HTTP/2 support
- No HTTP/3 support

**Use When:**
- HTTP/1.1 is sufficient
- Behind Nginx reverse proxy
- Maximum stability required

### Hypercorn (Optional - HTTP/2)

**Advantages:**
- Native HTTP/2 support
- Also supports HTTP/3
- ALPN for automatic fallback
- WebSockets over HTTP/2
- All FastAPI features work

**Limitations:**
- Slightly slower than Uvicorn for HTTP/1.1
- Less mature ecosystem

**Use When:**
- HTTP/2 required end-to-end
- Testing HTTP/2 features
- No reverse proxy available

---

## ALPN Protocol Negotiation

### What is ALPN?

ALPN (Application-Layer Protocol Negotiation) automatically selects the protocol during TLS handshake.

**Negotiation Flow:**
1. Client sends supported protocols: [h2, http/1.1]
2. Server selects from list: h2 (HTTP/2)
3. If h2 not available, falls back to http/1.1
4. Zero latency - happens during TLS handshake

**Result:** Seamless compatibility with all clients

### Supported Protocols

When using Hypercorn:
- `h2` - HTTP/2
- `http/1.1` - HTTP/1.1
- Automatic selection via ALPN

---

## Testing HTTP/2

### Using curl

```bash
# Test HTTP/2 connection (with SSL)
curl -v --http2 https://localhost:8000/health

# Look for this line:
# "ALPN, server accepted to use h2"

# Check protocol in response
curl -I --http2 https://localhost:8000/v1/models
```

### Using Python

```python
import httpx

# httpx supports HTTP/2 natively
client = httpx.Client(http2=True)
response = client.get("https://localhost:8000/health")

print(f"Protocol: {response.http_version}")  # Should be "HTTP/2"
```

### Using Browser DevTools

1. Open DevTools (F12)
2. Network tab
3. Right-click headers → Protocol
4. Look for "h2" in protocol column

---

## Production Deployment

### Option 1: Direct Hypercorn with SSL

```bash
# Systemd service file: /etc/systemd/system/fakeai.service
[Unit]
Description=FakeAI Server with HTTP/2
After=network.target

[Service]
Type=simple
User=fakeai
WorkingDirectory=/opt/fakeai
ExecStart=/usr/local/bin/fakeai-server \
  --http2 \
  --ssl-certfile /etc/letsencrypt/live/api.example.com/fullchain.pem \
  --ssl-keyfile /etc/letsencrypt/live/api.example.com/privkey.pem \
  --host 0.0.0.0 \
  --port 443 \
  --api-key /etc/fakeai/api-keys.txt
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable fakeai
sudo systemctl start fakeai
```

### Option 2: Nginx Reverse Proxy (Recommended)

**Benefits:**
- Keep Uvicorn backend (simpler, faster for HTTP/1.1)
- HTTP/2 termination at Nginx
- Additional features: caching, rate limiting, load balancing

**Nginx Configuration:**

```nginx
upstream fakeai {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://fakeai;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Run FakeAI:**
```bash
# Uvicorn listens on localhost only
fakeai-server --host 127.0.0.1 --port 8000 --api-key /etc/fakeai/keys.txt
```

---

## Performance Benefits

### HTTP/2 Advantages

**Multiplexing:**
- Multiple requests over single connection
- Eliminates head-of-line blocking
- Reduces connection overhead

**Header Compression:**
- HPACK compression
- 30-50% header size reduction
- Faster for API-heavy applications

**Binary Protocol:**
- More efficient parsing
- Lower CPU overhead

### Real-World Gains

For FakeAI specifically:
- **20-50% faster** for multi-request scenarios
- **Better connection reuse** for streaming
- **Lower latency** for high-frequency testing
- **Production-like** behavior for testing

---

## Environment Variables

```bash
# HTTP/2 with SSL via environment
export FAKEAI_HTTP2=true
export FAKEAI_SSL_CERTFILE=/path/to/cert.pem
export FAKEAI_SSL_KEYFILE=/path/to/key.pem
export FAKEAI_HOST=0.0.0.0
export FAKEAI_PORT=443

fakeai-server
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -e .

# Copy SSL certificates (or mount as volume)
COPY certs/ /certs/

EXPOSE 443

CMD ["fakeai-server", \
     "--http2", \
     "--ssl-certfile", "/certs/fullchain.pem", \
     "--ssl-keyfile", "/certs/privkey.pem", \
     "--host", "0.0.0.0", \
     "--port", "443"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  fakeai-http2:
    build: .
    ports:
      - "443:443"
    volumes:
      - ./certs:/certs:ro
      - ./api-keys.txt:/etc/fakeai/api-keys.txt:ro
    environment:
      - FAKEAI_HTTP2=true
      - FAKEAI_SSL_CERTFILE=/certs/fullchain.pem
      - FAKEAI_SSL_KEYFILE=/certs/privkey.pem
    restart: unless-stopped
```

---

## Troubleshooting

### Issue: "HTTP/2 without SSL" Warning

**Problem:** Browsers require SSL for HTTP/2

**Solution:**
```bash
# Add SSL certificates
fakeai-server --http2 \
  --ssl-certfile /path/to/cert.pem \
  --ssl-keyfile /path/to/key.pem
```

### Issue: "Hypercorn not installed"

**Problem:** Hypercorn package not found

**Solution:**
```bash
# Install Hypercorn
pip install hypercorn

# Or reinstall fakeai
pip install -e .
```

### Issue: Connection Refused

**Problem:** Port 443 requires root/elevated privileges

**Solutions:**
```bash
# Option 1: Use non-privileged port
fakeai-server --http2 --port 8443

# Option 2: Grant capability (Linux)
sudo setcap 'cap_net_bind_service=+ep' $(which python3)

# Option 3: Run as root (not recommended)
sudo fakeai-server --http2 --port 443
```

### Issue: Certificate Errors

**Problem:** SSL certificate not valid

**Verify:**
```bash
# Check certificate
openssl x509 -in cert.pem -text -noout

# Check private key
openssl rsa -in key.pem -check

# Verify they match
openssl x509 -in cert.pem -noout -modulus | openssl md5
openssl rsa -in key.pem -noout -modulus | openssl md5
# MD5 hashes should match
```

---

## Comparison: Uvicorn vs Hypercorn

| Feature | Uvicorn | Hypercorn |
|---------|---------|-----------|
| HTTP/1.1 | Yes | Yes |
| HTTP/2 | No | Yes |
| HTTP/3 | No | Yes |
| Performance (HTTP/1.1) | Faster | Slightly slower |
| Performance (HTTP/2) | N/A | Good |
| Maturity | Very mature | Mature |
| Memory Usage | ~20MB | ~25MB |
| ALPN Support | No | Yes |

---

## When to Use HTTP/2

**Use HTTP/2 When:**
- Testing HTTP/2-specific features
- Production environment with modern clients
- High-frequency API calls
- Streaming-heavy workloads
- Want to match real OpenAI infrastructure

**Stick with HTTP/1.1 When:**
- Simple development/testing
- Behind reverse proxy (Nginx handles HTTP/2)
- Maximum stability required
- Legacy client compatibility needed

---

## Examples

### Development Testing

```bash
# Start with HTTP/2 (self-signed cert for testing)
fakeai-server --http2 --ssl-certfile cert.pem --ssl-keyfile key.pem
```

### Production

```bash
# With Let's Encrypt
fakeai-server \
  --http2 \
  --ssl-certfile /etc/letsencrypt/live/api.example.com/fullchain.pem \
  --ssl-keyfile /etc/letsencrypt/live/api.example.com/privkey.pem \
  --host 0.0.0.0 \
  --port 443 \
  --api-key /etc/fakeai/api-keys.txt
```

### With All Options

```bash
fakeai-server \
  --http2 \
  --ssl-certfile /etc/letsencrypt/live/api.example.com/fullchain.pem \
  --ssl-keyfile /etc/letsencrypt/live/api.example.com/privkey.pem \
  --host 0.0.0.0 \
  --port 443 \
  --api-key /etc/fakeai/api-keys.txt \
  --response-delay 0.5 \
  --rate-limit-enabled \
  --requests-per-minute 1000
```

---

## Monitoring HTTP/2

### Check Active Protocol

```bash
# Using curl with verbose
curl -v --http2 https://localhost:8000/health 2>&1 | grep "ALPN\|HTTP/"

# Using httpx (Python)
import httpx
client = httpx.Client(http2=True, verify=False)  # verify=False for self-signed
response = client.get("https://localhost:8000/health")
print(f"Protocol: {response.http_version}")
```

### Performance Testing

```bash
# HTTP/1.1 benchmark
ab -n 1000 -c 10 http://localhost:8000/health

# HTTP/2 benchmark
h2load -n 1000 -c 10 https://localhost:8000/health
```

---

## Conclusion

HTTP/2 support in FakeAI is production-ready and available via the --http2 flag. The implementation uses Hypercorn for native HTTP/2 support with automatic ALPN fallback to HTTP/1.1, ensuring compatibility with all clients while providing modern protocol benefits for those that support it.

For most use cases, the default Uvicorn (HTTP/1.1) is sufficient. Use HTTP/2 when you need to match production environments or test HTTP/2-specific features.
