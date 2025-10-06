# FakeAI Configuration Reference

Complete reference for all configuration options in FakeAI.

## Configuration Methods

FakeAI supports three ways to configure the server (in order of precedence):

1. **CLI Arguments** (highest priority)
2. **Environment Variables** (medium priority)
3. **Default Values** (lowest priority)

---

## Server Settings

### Host and Port

**CLI Arguments:**
```bash
--host 0.0.0.0
--port 8000
```

**Environment Variables:**
```bash
FAKEAI_HOST=0.0.0.0
FAKEAI_PORT=8000
```

**Defaults:**
- Host: `127.0.0.1`
- Port: `8000`

---

## HTTP/2 Settings

### Enable HTTP/2

**CLI Arguments:**
```bash
--http2
--ssl-certfile /path/to/cert.pem
--ssl-keyfile /path/to/key.pem
```

**Note:** HTTP/2 requires SSL certificates in production.

---

## Response Settings

### Response Timing

**CLI Arguments:**
```bash
--response-delay 0.5
--random-delay / --no-random-delay
--max-variance 0.3
```

**Environment Variables:**
```bash
FAKEAI_RESPONSE_DELAY=0.5
FAKEAI_RANDOM_DELAY=true
FAKEAI_MAX_VARIANCE=0.3
```

**Defaults:**
- Response delay: `0.5` seconds
- Random delay: `true`
- Max variance: `0.3` (30% variation)

---

## Authentication Settings

### API Keys

**CLI Arguments:**
```bash
--api-key sk-test-key-1
--api-key sk-test-key-2
--api-key /path/to/keys.txt
```

**Environment Variables:**
```bash
FAKEAI_API_KEYS=["sk-key-1", "sk-key-2"]  # JSON array format
FAKEAI_REQUIRE_API_KEY=true
```

**Defaults:**
- API keys: `[]` (empty list)
- Require API key: `false`

**Note:** Authentication is automatically enabled when API keys are provided via CLI.

---

## Rate Limiting

### Rate Limit Settings

**CLI Arguments:**
```bash
--rate-limit-enabled
--requests-per-minute 10000
```

**Environment Variables:**
```bash
FAKEAI_RATE_LIMIT_ENABLED=true
FAKEAI_RATE_LIMIT_TIER=tier-1  # free, tier-1, tier-2, tier-3, tier-4, tier-5
FAKEAI_RATE_LIMIT_RPM=500      # Custom requests per minute
FAKEAI_RATE_LIMIT_TPM=50000    # Custom tokens per minute
```

**Defaults:**
- Rate limit enabled: `false`
- Rate limit tier: `tier-1`
- Custom RPM: `None` (uses tier defaults)
- Custom TPM: `None` (uses tier defaults)

---

## KV Cache Settings

### KV Cache Configuration

**CLI Arguments:**
```bash
--kv-cache-enabled / --no-kv-cache-enabled
--kv-cache-block-size 16
--kv-cache-num-workers 4
--kv-overlap-weight 1.0
```

**Environment Variables:**
```bash
FAKEAI_KV_CACHE_ENABLED=true
FAKEAI_KV_CACHE_BLOCK_SIZE=16
FAKEAI_KV_CACHE_NUM_WORKERS=4
FAKEAI_KV_OVERLAP_WEIGHT=1.0
```

**Defaults:**
- KV cache enabled: `true`
- Block size: `16` tokens (range: 1-128)
- Number of workers: `4` (range: 1-64)
- Overlap weight: `1.0` (range: 0.0-2.0)

**Description:**
- **Block size**: Number of tokens per cache block (smaller = more granular, larger = faster)
- **Workers**: Number of parallel workers for cache processing
- **Overlap weight**: Weight for scoring overlapping content (higher = more aggressive caching)

---

## Safety Settings

### Content Moderation

**CLI Arguments:**
```bash
--enable-moderation / --no-enable-moderation
--moderation-threshold 0.5
--enable-refusals / --no-enable-refusals
--enable-jailbreak-detection / --no-enable-jailbreak-detection
```

**Environment Variables:**
```bash
FAKEAI_ENABLE_MODERATION=true
FAKEAI_MODERATION_THRESHOLD=0.5
FAKEAI_ENABLE_REFUSALS=true
FAKEAI_ENABLE_JAILBREAK_DETECTION=true
FAKEAI_ENABLE_SAFETY_FEATURES=true
FAKEAI_PREPEND_SAFETY_MESSAGE=false
```

**Defaults:**
- Enable moderation: `true`
- Moderation threshold: `0.5` (range: 0.0-1.0)
- Enable refusals: `true`
- Enable jailbreak detection: `true`
- Enable safety features: `true`
- Prepend safety message: `false`

**Description:**
- **Moderation**: Content moderation API endpoint
- **Threshold**: Sensitivity for content flags (lower = more sensitive)
- **Refusals**: Generate refusal responses for harmful content
- **Jailbreak detection**: Detect and block prompt injection attempts

---

## Audio Settings

### Audio Configuration

**CLI Arguments:**
```bash
--enable-audio / --no-enable-audio
--default-voice alloy
--default-audio-format mp3
```

**Environment Variables:**
```bash
FAKEAI_ENABLE_AUDIO=true
FAKEAI_DEFAULT_VOICE=alloy
FAKEAI_DEFAULT_AUDIO_FORMAT=mp3
```

**Defaults:**
- Enable audio: `true`
- Default voice: `alloy`
- Default audio format: `mp3`

**Valid Voices:**
- `alloy`
- `ash`
- `ballad`
- `coral`
- `echo`
- `fable`
- `onyx`
- `nova`
- `shimmer`
- `sage`
- `verse`

**Valid Audio Formats:**
- `mp3`
- `opus`
- `aac`
- `flac`
- `wav`
- `pcm16`

---

## Performance Settings

### Performance Optimization

**CLI Arguments:**
```bash
--enable-context-validation / --no-enable-context-validation
--strict-token-counting / --no-strict-token-counting
```

**Environment Variables:**
```bash
FAKEAI_ENABLE_CONTEXT_VALIDATION=true
FAKEAI_STRICT_TOKEN_COUNTING=false
```

**Defaults:**
- Enable context validation: `true`
- Strict token counting: `false`

**Description:**
- **Context validation**: Validate context window limits and warn on overflow
- **Strict token counting**: Use more accurate but slower token counting algorithm

---

## Prompt Caching Settings

### Prompt Cache Configuration

**Environment Variables:**
```bash
FAKEAI_ENABLE_PROMPT_CACHING=true
FAKEAI_CACHE_TTL_SECONDS=600
FAKEAI_MIN_TOKENS_FOR_CACHE=1024
```

**Defaults:**
- Enable prompt caching: `true`
- Cache TTL: `600` seconds (10 minutes)
- Minimum tokens for cache: `1024`

---

## Streaming Settings

### Streaming Configuration

**Environment Variables:**
```bash
FAKEAI_STREAM_TIMEOUT_SECONDS=300.0
FAKEAI_STREAM_TOKEN_TIMEOUT_SECONDS=30.0
FAKEAI_STREAM_KEEPALIVE_ENABLED=true
FAKEAI_STREAM_KEEPALIVE_INTERVAL_SECONDS=15.0
```

**Defaults:**
- Stream timeout: `300.0` seconds (5 minutes)
- Stream token timeout: `30.0` seconds
- Keep-alive enabled: `true`
- Keep-alive interval: `15.0` seconds

---

## Debug Settings

### Debug Mode

**CLI Arguments:**
```bash
--debug
```

**Environment Variables:**
```bash
FAKEAI_DEBUG=true
```

**Defaults:**
- Debug: `false`

**Description:**
Debug mode enables:
- Auto-reload on code changes
- Verbose logging
- Access logs
- Detailed error messages

---

## Configuration Examples

### Production Configuration

```bash
fakeai-server \
  --host 0.0.0.0 \
  --port 8000 \
  --api-key /path/to/production-keys.txt \
  --rate-limit-enabled \
  --kv-cache-block-size 32 \
  --kv-cache-num-workers 8 \
  --enable-moderation \
  --moderation-threshold 0.8 \
  --enable-refusals \
  --enable-jailbreak-detection \
  --default-voice alloy
```

### Development Configuration

```bash
fakeai-server \
  --host 127.0.0.1 \
  --port 8000 \
  --debug \
  --response-delay 0.0 \
  --no-random-delay \
  --no-enable-moderation \
  --no-enable-refusals
```

### Performance Testing Configuration

```bash
fakeai-server \
  --response-delay 0.0 \
  --no-random-delay \
  --kv-cache-block-size 64 \
  --kv-cache-num-workers 16 \
  --no-enable-moderation \
  --no-enable-context-validation \
  --no-strict-token-counting
```

### Environment Variables Configuration

```bash
# Set environment variables
export FAKEAI_HOST=0.0.0.0
export FAKEAI_PORT=9000
export FAKEAI_KV_CACHE_BLOCK_SIZE=32
export FAKEAI_DEFAULT_VOICE=nova
export FAKEAI_MODERATION_THRESHOLD=0.7
export FAKEAI_ENABLE_AUDIO=true

# Start server (will use environment variables)
fakeai-server
```

---

## Validation Rules

### Numeric Ranges

- **Port**: 1 - 65535
- **Response delay**: >= 0.0
- **Max variance**: >= 0.0
- **KV cache block size**: 1 - 128
- **KV cache workers**: 1 - 64
- **KV overlap weight**: 0.0 - 2.0
- **Moderation threshold**: 0.0 - 1.0
- **Cache TTL**: >= 0
- **Min tokens for cache**: >= 0
- **Stream timeout**: > 0.0
- **Keep-alive interval**: > 0.0

### String Enumerations

- **Default voice**: Must be one of the valid voices listed above
- **Default audio format**: Must be one of the valid formats listed above
- **Rate limit tier**: free, tier-1, tier-2, tier-3, tier-4, tier-5

---

## Complete Environment Variable Reference

All environment variables use the `FAKEAI_` prefix and are case-insensitive:

```bash
# Server
FAKEAI_HOST=127.0.0.1
FAKEAI_PORT=8000
FAKEAI_DEBUG=false

# Response
FAKEAI_RESPONSE_DELAY=0.5
FAKEAI_RANDOM_DELAY=true
FAKEAI_MAX_VARIANCE=0.3

# Authentication
FAKEAI_API_KEYS=["key1", "key2"]  # JSON array
FAKEAI_REQUIRE_API_KEY=false

# Rate Limiting
FAKEAI_RATE_LIMIT_ENABLED=false
FAKEAI_RATE_LIMIT_TIER=tier-1
FAKEAI_RATE_LIMIT_RPM=500
FAKEAI_RATE_LIMIT_TPM=50000

# KV Cache
FAKEAI_KV_CACHE_ENABLED=true
FAKEAI_KV_CACHE_BLOCK_SIZE=16
FAKEAI_KV_CACHE_NUM_WORKERS=4
FAKEAI_KV_OVERLAP_WEIGHT=1.0

# Safety
FAKEAI_ENABLE_MODERATION=true
FAKEAI_MODERATION_THRESHOLD=0.5
FAKEAI_ENABLE_REFUSALS=true
FAKEAI_ENABLE_SAFETY_FEATURES=true
FAKEAI_ENABLE_JAILBREAK_DETECTION=true
FAKEAI_PREPEND_SAFETY_MESSAGE=false

# Audio
FAKEAI_ENABLE_AUDIO=true
FAKEAI_DEFAULT_VOICE=alloy
FAKEAI_DEFAULT_AUDIO_FORMAT=mp3

# Performance
FAKEAI_ENABLE_CONTEXT_VALIDATION=true
FAKEAI_STRICT_TOKEN_COUNTING=false

# Prompt Caching
FAKEAI_ENABLE_PROMPT_CACHING=true
FAKEAI_CACHE_TTL_SECONDS=600
FAKEAI_MIN_TOKENS_FOR_CACHE=1024

# Streaming
FAKEAI_STREAM_TIMEOUT_SECONDS=300.0
FAKEAI_STREAM_TOKEN_TIMEOUT_SECONDS=30.0
FAKEAI_STREAM_KEEPALIVE_ENABLED=true
FAKEAI_STREAM_KEEPALIVE_INTERVAL_SECONDS=15.0
```

---

## Priority Order

When the same configuration is specified in multiple places:

1. **CLI arguments** (highest priority)
2. **Environment variables** (medium priority)
3. **Default values** (lowest priority)

Example:
```bash
# Environment variable
export FAKEAI_KV_CACHE_BLOCK_SIZE=16

# CLI argument overrides
fakeai-server --kv-cache-block-size 64

# Result: block size = 64 (CLI wins)
```

---

## See Also

- [README.md](README.md) - Main documentation
- [examples/test_new_config_options.py](examples/test_new_config_options.py) - Configuration examples
- [tests/test_configuration.py](tests/test_configuration.py) - Configuration tests
