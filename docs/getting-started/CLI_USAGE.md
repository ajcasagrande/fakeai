# FakeAI CLI Usage Guide

The FakeAI server uses **Cyclopts** for a modern, Pydantic-based CLI with full type validation and excellent help messages.

## Quick Start

Start the server with default settings:
```bash
fakeai-server
```

## Command-Line Options

### Server Binding

#### `--host HOST`
Host address to bind the server to.
- **Default:** `127.0.0.1`
- **Example:** `fakeai-server --host 0.0.0.0`  (listen on all interfaces)

#### `--port PORT`
Port number to bind the server to (1-65535).
- **Default:** `8000`
- **Example:** `fakeai-server --port 9000`

### Server Behavior

#### `--debug` / `--no-debug`
Enable debug mode with auto-reload and verbose logging.
- **Default:** `False`
- **Example:** `fakeai-server --debug`

### Response Timing

#### `--response-delay SECONDS`
Base delay for responses in seconds.
- **Default:** `0.5`
- **Example:** `fakeai-server --response-delay 1.0`

#### `--random-delay` / `--no-random-delay`
Add random variation to response delays for realistic behavior.
- **Default:** `True`
- **Example:** `fakeai-server --no-random-delay`

#### `--max-variance FACTOR`
Maximum variance for random delays (as a factor of response-delay).
- **Default:** `0.3`
- **Example:** `fakeai-server --max-variance 0.5`

### Authentication

#### `--api-key KEY_OR_FILE`
API key or path to file containing keys (one per line). Can be specified multiple times.
- **Default:** None (authentication disabled)
- **File Format:**
  - One key per line
  - Lines starting with `#` are treated as comments
  - Blank lines are ignored
- **Examples:**
  ```bash
  # Direct API keys
  fakeai-server --api-key sk-test-1 --api-key sk-test-2

  # Load from file
  fakeai-server --api-key /path/to/keys.txt

  # Mix direct keys and files
  fakeai-server --api-key sk-direct-key --api-key /path/to/keys.txt
  ```

**Note:** Authentication is automatically enabled when any `--api-key` is provided. If no keys are specified, the server runs without authentication (open access).

### Rate Limiting

#### `--rate-limit-enabled` / `--no-rate-limit-enabled`
Enable rate limiting.
- **Default:** `False`
- **Example:** `fakeai-server --rate-limit-enabled`

#### `--requests-per-minute COUNT`
Maximum requests per minute per API key (when rate limiting is enabled).
- **Default:** `10000`
- **Example:** `fakeai-server --rate-limit-enabled --requests-per-minute 100`

## Usage Examples

### Development Mode
Start the server in debug mode on all interfaces:
```bash
fakeai-server --host 0.0.0.0 --port 8000 --debug
```

### Testing Without Authentication
By default, authentication is disabled. Just start the server:
```bash
fakeai-server
```

### Production-Like Setup
Run on a specific port with authentication and rate limiting:
```bash
fakeai-server \
  --host 0.0.0.0 \
  --port 9000 \
  --api-key sk-prod-key1 \
  --api-key sk-prod-key2 \
  --rate-limit-enabled \
  --requests-per-minute 1000
```

Or load keys from a file:
```bash
fakeai-server \
  --host 0.0.0.0 \
  --port 9000 \
  --api-key /etc/fakeai/api-keys.txt \
  --rate-limit-enabled \
  --requests-per-minute 1000
```

### High-Performance Setup
Minimal delays for performance testing (authentication disabled by default):
```bash
fakeai-server \
  --response-delay 0.0 \
  --no-random-delay
```

### Realistic Simulation
Simulate realistic API behavior with delays:
```bash
fakeai-server \
  --response-delay 0.8 \
  --random-delay \
  --max-variance 0.4
```

### Custom API Keys
Use custom API keys for your team:
```bash
fakeai-server --api-key sk-team-alice --api-key sk-team-bob --api-key sk-team-charlie
```

Or create a keys file:
```bash
# /etc/fakeai/team-keys.txt
# Team API Keys
sk-team-alice
sk-team-bob
sk-team-charlie

# Load the file
fakeai-server --api-key /etc/fakeai/team-keys.txt
```

## Environment Variables

All CLI options can also be set via environment variables with the `FAKEAI_` prefix:

```bash
export FAKEAI_HOST=0.0.0.0
export FAKEAI_PORT=9000
export FAKEAI_DEBUG=true
export FAKEAI_RESPONSE_DELAY=1.0

fakeai-server
```

For API keys via environment (comma-separated):
```bash
export FAKEAI_API_KEYS="sk-test-1,sk-test-2,sk-test-3"
fakeai-server
```

**Note:** CLI arguments take precedence over environment variables.

## Getting Help

View all available options:
```bash
fakeai-server --help
```

Check the version:
```bash
fakeai-server --version
```

## Validation Features

The CLI includes automatic validation:

- **Port validation:** Only accepts ports between 1-65535
- **Response delay validation:** Must be >= 0
- **Max variance validation:** Must be >= 0
- **Requests per minute validation:** Must be >= 1
- **Type safety:** All arguments are type-checked with Pydantic

Invalid values will be rejected with clear error messages:
```bash
$ fakeai-server --port 99999
Error: Port must be between 1 and 65535
```

## Startup Display

When starting the server, you'll see a detailed startup banner:

### Without Authentication (default)
```
======================================================================
FakeAI - OpenAI Compatible API Server
======================================================================
Starting server at http://127.0.0.1:8000
API documentation: http://127.0.0.1:8000/docs
Metrics endpoint: http://127.0.0.1:8000/metrics
Health check: http://127.0.0.1:8000/health

Configuration:
  • Debug mode: False
  • Response delay: 0.5s
  • Random delay: True
  • Rate limiting: False
  • Authentication: DISABLED (no API keys required)
======================================================================
```

### With Authentication
```
======================================================================
FakeAI - OpenAI Compatible API Server
======================================================================
Starting server at http://127.0.0.1:8000
API documentation: http://127.0.0.1:8000/docs
Metrics endpoint: http://127.0.0.1:8000/metrics
Health check: http://127.0.0.1:8000/health

Configuration:
  • Debug mode: False
  • Response delay: 0.5s
  • Random delay: True
  • Rate limiting: False
  • Authentication: ENABLED (3 keys configured)
======================================================================
```

## Integration with Docker

Create a `Dockerfile`:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
RUN pip install fakeai
EXPOSE 8000
CMD ["fakeai-server", "--host", "0.0.0.0", "--port", "8000"]
```

Run with custom options:
```bash
docker run -p 9000:9000 fakeai-image \
  fakeai-server --host 0.0.0.0 --port 9000
```

With authentication:
```bash
docker run -p 9000:9000 -v /path/to/keys.txt:/keys.txt fakeai-image \
  fakeai-server --host 0.0.0.0 --port 9000 --api-key /keys.txt
```

## Systemd Service

Create `/etc/systemd/system/fakeai.service`:
```ini
[Unit]
Description=FakeAI OpenAI Compatible API Server
After=network.target

[Service]
Type=simple
User=fakeai
WorkingDirectory=/opt/fakeai
ExecStart=/usr/local/bin/fakeai-server --host 0.0.0.0 --port 8000 --api-key /etc/fakeai/api-keys.txt
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable fakeai
sudo systemctl start fakeai
```
