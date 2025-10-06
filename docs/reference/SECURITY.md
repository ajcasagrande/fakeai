# Security Policy

## Overview

FakeAI is designed with security in mind, implementing multiple layers of protection against common attacks and abuse patterns. While FakeAI is primarily a testing and development tool, we take security seriously to ensure it can be safely deployed in various environments.

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Security Features

### 1. Input Validation and Sanitization

FakeAI implements comprehensive input validation to prevent malicious payloads:

- **String Sanitization**: Removes control characters and validates string lengths
- **Array Validation**: Enforces maximum array sizes to prevent memory exhaustion
- **Dictionary Validation**: Validates allowed keys and values
- **Payload Size Limits**: Enforces maximum request sizes (default: 10 MB)

**Configuration:**
```bash
FAKEAI_ENABLE_INPUT_VALIDATION=true  # Default: true
FAKEAI_MAX_REQUEST_SIZE=10485760     # 10 MB in bytes
```

### 2. Injection Attack Detection

FakeAI detects and blocks common injection attacks:

- **SQL Injection**: Detects SQL keywords and patterns (UNION, DROP, INSERT, etc.)
- **Command Injection**: Blocks shell command patterns (|, ;, &&, etc.)
- **Path Traversal**: Prevents directory traversal attempts (../, etc.)
- **Script Injection**: Detects XSS and script tags
- **LDAP Injection**: Identifies LDAP filter manipulation attempts
- **XXE Attacks**: Blocks XML entity expansion attempts

**Configuration:**
```bash
FAKEAI_ENABLE_INJECTION_DETECTION=true  # Default: true
```

**Example Response (Injection Detected):**
```json
{
  "error": {
    "code": "injection_detected",
    "message": "Potential injection attack detected in request.",
    "type": "security_error"
  }
}
```

### 3. Secure API Key Management

FakeAI supports both plaintext and hashed API key storage:

**Hashed Storage (Recommended):**
- API keys are hashed using SHA-256 before storage
- Original keys are never stored in memory or logs
- Supports key expiration and rotation
- Tracks usage statistics per key

**Configuration:**
```bash
FAKEAI_HASH_API_KEYS=true                           # Default: true
FAKEAI_REQUIRE_API_KEY=true                         # Default: false
FAKEAI_API_KEYS="sk-key1,sk-key2,sk-key3"          # Comma-separated keys
```

**Generating Secure Keys:**
```python
from fakeai.security import generate_api_key

# Generate a secure random key
api_key = generate_api_key()  # Returns: sk-fake-<64-char-hex>
```

**Key Rotation:**
```python
from fakeai.security import ApiKeyManager

manager = ApiKeyManager()

# Add new key with expiration
from datetime import datetime, timedelta
expires_at = datetime.now() + timedelta(days=30)
manager.add_key("sk-new-key", expires_at=expires_at)

# Revoke old key
manager.revoke_key("sk-old-key")
```

### 4. Rate Limiting

FakeAI implements token bucket rate limiting with multiple tiers:

**Rate Limit Tiers:**
| Tier   | RPM (Requests/Min) | TPM (Tokens/Min) |
|--------|-------------------|------------------|
| free   | 60                | 10,000           |
| tier-1 | 500               | 30,000           |
| tier-2 | 5,000             | 450,000          |
| tier-3 | 10,000            | 1,000,000        |
| tier-4 | 30,000            | 5,000,000        |
| tier-5 | 100,000           | 15,000,000       |

**Configuration:**
```bash
FAKEAI_RATE_LIMIT_ENABLED=true      # Default: false
FAKEAI_RATE_LIMIT_TIER="tier-1"     # Default: tier-1
FAKEAI_RATE_LIMIT_RPM=1000          # Optional: override tier RPM
FAKEAI_RATE_LIMIT_TPM=50000         # Optional: override tier TPM
```

**Rate Limit Headers:**
```
x-ratelimit-limit-requests: 500
x-ratelimit-limit-tokens: 30000
x-ratelimit-remaining-requests: 485
x-ratelimit-remaining-tokens: 28500
x-ratelimit-reset-requests: 1699564800
x-ratelimit-reset-tokens: 1699564800
```

### 5. IP-Based Abuse Detection

FakeAI tracks and automatically bans abusive IP addresses:

**Tracked Violations:**
- Failed authentication attempts (threshold: 5)
- Injection attack attempts (threshold: 3)
- Oversized payload attempts (threshold: 10)
- Rate limit violations (threshold: 20)

**Ban Durations:**
- **Temporary Ban**: 5 minutes (10-29 violations)
- **Extended Ban**: 1 hour (30-49 violations)
- **Long Ban**: 24 hours (50+ violations)

**Configuration:**
```bash
FAKEAI_ENABLE_ABUSE_DETECTION=true           # Default: true
FAKEAI_ABUSE_CLEANUP_INTERVAL=3600           # Cleanup interval (seconds)
```

**Ban Response (403 Forbidden):**
```json
{
  "error": {
    "code": "ip_banned",
    "message": "IP address temporarily banned due to abuse. Retry after 300 seconds.",
    "type": "security_error"
  }
}
```

### 6. CORS Configuration

FakeAI supports configurable CORS policies:

**Configuration:**
```bash
# Allow specific origins (recommended for production)
FAKEAI_CORS_ALLOWED_ORIGINS='["https://app.example.com","https://api.example.com"]'

# Allow all origins (development only)
FAKEAI_CORS_ALLOWED_ORIGINS='["*"]'

# Enable credentials
FAKEAI_CORS_ALLOW_CREDENTIALS=true  # Default: true
```

**Example Configuration:**
```python
from fakeai.config import AppConfig

config = AppConfig(
    cors_allowed_origins=[
        "https://app.example.com",
        "https://dashboard.example.com",
    ],
    cors_allow_credentials=True,
)
```

## Threat Model

### Assets

1. **API Server**: The FakeAI service itself
2. **API Keys**: Authentication credentials for accessing the service
3. **Configuration Data**: Server settings and security parameters
4. **Request/Response Data**: User inputs and generated responses

### Threats

#### 1. Injection Attacks

**Threat**: Attacker attempts SQL injection, command injection, or XSS attacks
**Mitigation**: Input validation and injection detection system blocks malicious patterns
**Residual Risk**: Low - Multiple pattern matching layers catch most attacks

#### 2. Denial of Service (DoS)

**Threat**: Attacker floods server with requests or large payloads
**Mitigations**:
- Rate limiting enforces request and token quotas
- Payload size limits prevent memory exhaustion
- Abuse detection identifies and bans aggressive IPs
**Residual Risk**: Medium - Distributed attacks may bypass IP bans

#### 3. API Key Theft

**Threat**: Attacker steals API keys through various means
**Mitigations**:
- Keys are hashed using SHA-256 (not stored plaintext)
- Support for key expiration and rotation
- Failed auth attempts trigger IP bans
**Residual Risk**: Low - Even if database is compromised, keys cannot be recovered

#### 4. Brute Force Attacks

**Threat**: Attacker attempts to guess API keys
**Mitigations**:
- Failed auth attempts are tracked per IP
- IP ban after 5 failed attempts
- Rate limiting prevents rapid guessing
**Residual Risk**: Low - Key space is large (2^256), bans prevent sustained attempts

#### 5. Data Exfiltration

**Threat**: Attacker attempts to extract sensitive data
**Mitigation**: FakeAI is stateless and generates fake data - no real user data to exfiltrate
**Residual Risk**: Very Low - Service design prevents sensitive data storage

#### 6. Configuration Manipulation

**Threat**: Attacker attempts to modify server configuration
**Mitigation**: Configuration is loaded at startup from environment variables
**Residual Risk**: Low - Requires host-level access

### Non-Threats

The following are explicitly **not** in scope for FakeAI's threat model:

1. **Realistic ML Inference**: FakeAI generates fake responses, not real ML outputs
2. **Data Privacy**: No real user data is processed or stored
3. **Model Security**: No actual ML models are served
4. **Training Data Protection**: No training data exists

## Security Best Practices

### For Deployment

1. **Always Enable Authentication**:
   ```bash
   FAKEAI_REQUIRE_API_KEY=true
   FAKEAI_HASH_API_KEYS=true
   ```

2. **Use Strong API Keys**:
   ```python
   # Generate cryptographically secure keys
   from fakeai.security import generate_api_key
   key = generate_api_key()
   ```

3. **Enable All Security Features**:
   ```bash
   FAKEAI_ENABLE_INPUT_VALIDATION=true
   FAKEAI_ENABLE_INJECTION_DETECTION=true
   FAKEAI_ENABLE_ABUSE_DETECTION=true
   FAKEAI_RATE_LIMIT_ENABLED=true
   ```

4. **Restrict CORS Origins**:
   ```bash
   # Never use "*" in production
   FAKEAI_CORS_ALLOWED_ORIGINS='["https://your-app.com"]'
   ```

5. **Set Reasonable Rate Limits**:
   ```bash
   FAKEAI_RATE_LIMIT_TIER="tier-1"  # Adjust based on needs
   ```

6. **Monitor for Abuse**:
   ```bash
   # Check metrics regularly
   curl http://localhost:8000/metrics
   ```

### For Development

1. **Use Separate Keys**: Never reuse production keys in development
2. **Test Security Features**: Run security tests regularly
3. **Review Logs**: Monitor for suspicious activity
4. **Keep Dependencies Updated**: Regular security patches

### For Integration

1. **Validate All Inputs**: Even though FakeAI validates, validate on client side too
2. **Handle Rate Limits**: Implement exponential backoff
3. **Secure Key Storage**: Never commit keys to version control
4. **Use HTTPS**: Always use TLS in production (via reverse proxy)

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow responsible disclosure:

### How to Report

**Email**: Send details to `security@fakeai.dev` (or maintainer email)

**Include**:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

**PGP Key**: [Available on request]

### What to Expect

1. **Initial Response**: Within 48 hours
2. **Assessment**: Within 1 week
3. **Fix Development**: Depends on severity
4. **Disclosure**: Coordinated disclosure after fix is released

### Severity Levels

**Critical**: Remote code execution, authentication bypass
- **Response Time**: 24 hours
- **Fix Timeline**: 1 week

**High**: Injection attacks, privilege escalation
- **Response Time**: 48 hours
- **Fix Timeline**: 2 weeks

**Medium**: DoS, information disclosure
- **Response Time**: 1 week
- **Fix Timeline**: 1 month

**Low**: Minor configuration issues
- **Response Time**: 2 weeks
- **Fix Timeline**: Next release

## Security Testing

### Running Security Tests

```bash
# Run all security tests
pytest tests/test_security.py -v

# Run specific test classes
pytest tests/test_security.py::TestInjectionDetection -v
pytest tests/test_security.py::TestApiKeyManagement -v
pytest tests/test_security.py::TestAbuseDetection -v
```

### Manual Security Testing

#### Test Injection Detection
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-oss-120b","messages":[{"role":"user","content":"'"'"'; DROP TABLE users; --"}]}'
```

Expected: 400 Bad Request (injection detected)

#### Test Oversized Payload
```bash
python -c "print('a' * 11000000)" | \
  curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  --data-binary @-
```

Expected: 413 Payload Too Large

#### Test Rate Limiting
```bash
# Make many rapid requests
for i in {1..100}; do
  curl http://localhost:8000/v1/models \
    -H "Authorization: Bearer sk-test-key"
done
```

Expected: Eventually 429 Too Many Requests

## Compliance

### Security Standards

FakeAI follows these security standards:

- **OWASP Top 10**: Protection against common web vulnerabilities
- **CWE Top 25**: Mitigation of most dangerous software weaknesses
- **SANS Top 25**: Defense against critical software errors

### Certifications

FakeAI is designed to support deployments requiring:

- **SOC 2 Type II**: Security controls for service organizations
- **ISO 27001**: Information security management
- **GDPR**: Data protection and privacy (minimal data processing)

*Note: FakeAI itself is not certified, but provides features needed for compliant deployments*

## Security Roadmap

### Planned Enhancements

1. **mTLS Support**: Mutual TLS authentication (v1.1)
2. **JWT Tokens**: Support for JWT-based authentication (v1.1)
3. **Audit Logging**: Detailed security event logging (v1.2)
4. **Anomaly Detection**: ML-based abuse detection (v1.3)
5. **Secrets Management**: Integration with HashiCorp Vault (v1.3)

### Under Consideration

- Rate limiting per endpoint
- IP whitelisting/blacklisting
- Request signing (HMAC)
- API key scopes and permissions

## Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CWE/SANS Top 25](https://www.sans.org/top25-software-errors/)

## License

This security policy is licensed under [Apache-2.0](LICENSE).

## Acknowledgments

We thank the security research community for responsible disclosure and contributions to FakeAI's security.

---

**Last Updated**: 2025-10-04
**Version**: 1.0.0
