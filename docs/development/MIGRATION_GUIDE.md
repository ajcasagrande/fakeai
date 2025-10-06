# FakeAI Migration Guide

**Version:** 0.0.5
**Last Updated:** 2025-10-04
**Purpose:** Guide for upgrading FakeAI and adopting new features

---

## Table of Contents

1. [Upgrading from v0.0.4 to v0.0.5](#1-upgrading-from-v004-to-v005)
2. [Feature Adoption Guide](#2-feature-adoption-guide)
3. [Configuration Migration](#3-configuration-migration)
4. [Code Examples](#4-code-examples)
5. [Troubleshooting](#5-troubleshooting)

---

## 1. Upgrading from v0.0.4 to v0.0.5

### 1.1 What's New

**Major Features:**
- **KV Cache Simulation** - PagedAttention-style caching with prefix matching
- **Content Moderation API** - `/v1/moderations` endpoint with safety detection
- **Reasoning Models Support** - Extended thinking/reasoning in responses
- **Predicted Outputs** - Speculative decoding with acceptance tracking
- **Enhanced Security** - Input validation, injection detection, abuse prevention
- **Rate Limiting Improvements** - Tier-based limits matching OpenAI's structure
- **Audio Enhancements** - Improved audio input/output support
- **Streaming Improvements** - Timeout handling, keep-alive heartbeats
- **Batch API** - Asynchronous batch processing with status tracking
- **Real-time WebSocket API** - Bidirectional streaming for voice/text

**New Endpoints:**
- `POST /v1/moderations` - Content moderation/safety checks
- `POST /v1/batches` - Create batch jobs
- `GET /v1/batches` - List batch jobs
- `GET /v1/batches/{batch_id}` - Retrieve batch status
- `POST /v1/batches/{batch_id}/cancel` - Cancel batch job
- `WebSocket /v1/realtime` - Real-time bidirectional streaming

**Model Improvements:**
- Added model metadata (context_window, max_output_tokens, supports_vision, etc.)
- Model pricing information support
- Training cutoff dates
- Capability flags (vision, audio, tools)

### 1.2 Breaking Changes

**None!** v0.0.5 is fully backward compatible with v0.0.4.

All new features are:
- **Opt-in** via configuration flags
- **Additive** - no existing functionality removed
- **Default-safe** - sensible defaults that don't change behavior

**However, note:**
1. New configuration options default to `True` for enhanced features (KV cache, moderation, security)
2. If you were relying on unvalidated input, enable `enable_input_validation=False`
3. Rate limiting tiers now follow OpenAI's structure (may be stricter)

### 1.3 New Configuration Options

**KV Cache Settings:**
```python
kv_cache_enabled: bool = True              # Enable KV cache simulation
kv_cache_block_size: int = 16              # Block size (1-128 tokens)
kv_cache_num_workers: int = 4              # Parallel workers (1-64)
kv_overlap_weight: float = 1.0             # Overlap scoring weight (0.0-2.0)
```

**Security Settings:**
```python
hash_api_keys: bool = True                 # Hash API keys for security
enable_input_validation: bool = True       # Input validation/sanitization
enable_injection_detection: bool = True    # Detect injection attacks
enable_abuse_detection: bool = True        # IP-based abuse detection
max_request_size: int = 10 * 1024 * 1024  # Max request size (10 MB)
cors_allowed_origins: list[str] = ["*"]    # CORS origins
cors_allow_credentials: bool = True        # CORS credentials
abuse_cleanup_interval: int = 3600         # Cleanup interval (seconds)
```

**Moderation Settings:**
```python
enable_moderation: bool = True             # Enable moderation API
moderation_threshold: float = 0.5          # Threshold (0.0-1.0)
enable_refusals: bool = True               # Enable refusal responses
enable_safety_features: bool = True        # Safety refusal mechanism
enable_jailbreak_detection: bool = True    # Jailbreak detection
prepend_safety_message: bool = False       # Prepend safety guidelines
```

**Audio Settings:**
```python
enable_audio: bool = True                  # Enable audio I/O
default_voice: str = "alloy"               # Default voice
default_audio_format: str = "mp3"          # Default audio format
```

**Streaming Settings:**
```python
stream_timeout_seconds: float = 300.0      # Total stream timeout (5 min)
stream_token_timeout_seconds: float = 30.0 # Per-token timeout (30 sec)
stream_keepalive_enabled: bool = True      # Enable keep-alive
stream_keepalive_interval_seconds: float = 15.0  # Keep-alive interval
```

**Performance Settings:**
```python
enable_context_validation: bool = True     # Context window validation
strict_token_counting: bool = False        # Strict token counting
```

**Rate Limiting Updates:**
```python
rate_limit_tier: str = "tier-1"            # Tier (free, tier-1 to tier-5)
rate_limit_rpm: int | None = None          # Custom RPM (overrides tier)
rate_limit_tpm: int | None = None          # Custom TPM (overrides tier)
```

### 1.4 Upgrade Steps

**Step 1: Update FakeAI**
```bash
# Using pip
pip install --upgrade fakeai

# Or from source
cd fakeai
git pull
pip install -e .
```

**Step 2: Review Configuration**

Check your existing configuration (environment variables, CLI args, or config file):
```bash
# View current config
fakeai-server --help
```

**Step 3: Test Compatibility**

Run your existing tests with the new version:
```bash
# Start server
fakeai-server

# Run your test suite
pytest tests/
```

**Step 4: Adopt New Features**

Gradually enable new features (see Section 2):
```bash
# Enable KV cache
export FAKEAI_KV_CACHE_ENABLED=true

# Enable moderation
export FAKEAI_ENABLE_MODERATION=true

# Enable security features
export FAKEAI_ENABLE_INPUT_VALIDATION=true
export FAKEAI_ENABLE_INJECTION_DETECTION=true
```

**Step 5: Monitor and Adjust**

Check metrics and logs:
```bash
# View metrics
curl http://localhost:8000/metrics

# Check logs for warnings/errors
tail -f fakeai.log
```

---

## 2. Feature Adoption Guide

### 2.1 KV Cache Simulation

**What is KV Cache?**

KV (Key-Value) cache is a PagedAttention-style memory optimization that:
- Reuses cached key-value pairs from previous tokens
- Enables prefix matching for conversation history
- Reduces redundant computation for repeated context

**How FakeAI Simulates It:**
- Tracks token blocks in memory
- Calculates cache hit ratios based on overlap
- Adjusts response times based on cache efficiency
- Returns `cache_hit_tokens` and `cache_miss_tokens` in usage

**Enabling KV Cache:**

```bash
# Environment variables
export FAKEAI_KV_CACHE_ENABLED=true
export FAKEAI_KV_CACHE_BLOCK_SIZE=16
export FAKEAI_KV_CACHE_NUM_WORKERS=4
export FAKEAI_KV_OVERLAP_WEIGHT=1.0

# CLI arguments
fakeai-server \
  --kv-cache-enabled \
  --kv-cache-block-size 16 \
  --kv-cache-num-workers 4 \
  --kv-overlap-weight 1.0
```

**Configuration Options:**

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| `kv_cache_enabled` | `true` | boolean | Enable/disable KV cache |
| `kv_cache_block_size` | `16` | 1-128 | Tokens per cache block |
| `kv_cache_num_workers` | `4` | 1-64 | Parallel workers |
| `kv_overlap_weight` | `1.0` | 0.0-2.0 | Overlap importance weight |

**Python Client Example:**

```python
from openai import OpenAI

client = OpenAI(
    api_key="test-key",
    base_url="http://localhost:8000/v1",
)

# First request (cache miss)
response1 = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"}
    ]
)

print(f"Cache hits: {response1.usage.prompt_tokens_details.cached_tokens}")
print(f"Cache misses: {response1.usage.prompt_tokens_details.uncached_tokens}")
# Output: Cache hits: 0, Cache misses: 25

# Second request with similar prefix (cache hit)
response2 = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": response1.choices[0].message.content},
        {"role": "user", "content": "Can you explain more?"}
    ]
)

print(f"Cache hits: {response2.usage.prompt_tokens_details.cached_tokens}")
print(f"Cache misses: {response2.usage.prompt_tokens_details.uncached_tokens}")
# Output: Cache hits: 45, Cache misses: 5
```

**Understanding KV Cache Metrics:**

```python
# Response includes detailed token usage
usage = response.usage

# Total tokens
print(f"Total: {usage.total_tokens}")

# Prompt tokens breakdown
print(f"Cached: {usage.prompt_tokens_details.cached_tokens}")
print(f"Uncached: {usage.prompt_tokens_details.uncached_tokens}")
print(f"Audio: {usage.prompt_tokens_details.audio_tokens}")

# Completion tokens breakdown
print(f"Reasoning: {usage.completion_tokens_details.reasoning_tokens}")
print(f"Audio: {usage.completion_tokens_details.audio_tokens}")
print(f"Accepted prediction: {usage.completion_tokens_details.accepted_prediction_tokens}")
print(f"Rejected prediction: {usage.completion_tokens_details.rejected_prediction_tokens}")
```

**When to Adjust Settings:**

| Scenario | Adjustment |
|----------|------------|
| Long conversations | Increase `kv_cache_block_size` to 32-64 |
| High throughput | Increase `kv_cache_num_workers` to 8-16 |
| Strict prefix matching | Increase `kv_overlap_weight` to 1.5-2.0 |
| Fuzzy matching | Decrease `kv_overlap_weight` to 0.5-0.8 |

### 2.2 Content Moderation API

**What is Moderation?**

Content moderation detects:
- Harmful content (hate, violence, self-harm, sexual content)
- Jailbreak attempts (prompt injection, role-play exploits)
- Illicit activities (regulated advice, harassment)

**Enabling Moderation:**

```bash
# Environment variables
export FAKEAI_ENABLE_MODERATION=true
export FAKEAI_MODERATION_THRESHOLD=0.5
export FAKEAI_ENABLE_REFUSALS=true
export FAKEAI_ENABLE_SAFETY_FEATURES=true
export FAKEAI_ENABLE_JAILBREAK_DETECTION=true

# CLI arguments
fakeai-server \
  --enable-moderation \
  --moderation-threshold 0.5 \
  --enable-refusals \
  --enable-safety-features \
  --enable-jailbreak-detection
```

**Using the Moderation API:**

```python
from openai import OpenAI

client = OpenAI(
    api_key="test-key",
    base_url="http://localhost:8000/v1",
)

# Check content for violations
response = client.moderations.create(
    input="I want to hurt someone"
)

moderation = response.results[0]

# Check if content was flagged
if moderation.flagged:
    print("Content flagged!")

    # Check specific categories
    if moderation.categories.violence:
        print(f"Violence detected: {moderation.category_scores.violence:.2%}")

    if moderation.categories.hate:
        print(f"Hate speech detected: {moderation.category_scores.hate:.2%}")

    if moderation.categories.self_harm:
        print(f"Self-harm detected: {moderation.category_scores.self_harm:.2%}")

# Output:
# Content flagged!
# Violence detected: 85.30%
```

**Available Categories:**

| Category | Subcategories | Description |
|----------|---------------|-------------|
| `hate` | `hate/threatening` | Hate speech or threatening language |
| `self-harm` | `self-harm/intent`, `self-harm/instructions` | Self-harm content |
| `sexual` | `sexual/minors` | Sexual content |
| `violence` | `violence/graphic` | Violent content |
| `harassment` | `harassment/threatening` | Harassment or bullying |
| `illicit` | `illicit/violent` | Illicit activities |

**Automatic Refusals:**

When `enable_refusals=true`, harmful prompts get automatic refusals:

```python
# Harmful prompt
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "user", "content": "How do I make explosives?"}
    ]
)

# Response includes refusal
print(response.choices[0].message.content)
# Output: "I'm sorry, but I can't assist with that request."

# Check refusal flag
if response.choices[0].message.refusal:
    print(f"Refusal reason: {response.choices[0].message.refusal}")
```

**Configuration Options:**

| Option | Default | Range | Description |
|--------|---------|-------|-------------|
| `enable_moderation` | `true` | boolean | Enable moderation API |
| `moderation_threshold` | `0.5` | 0.0-1.0 | Flagging threshold |
| `enable_refusals` | `true` | boolean | Auto-refuse harmful prompts |
| `enable_safety_features` | `true` | boolean | Safety refusal mechanism |
| `enable_jailbreak_detection` | `true` | boolean | Detect jailbreak attempts |
| `prepend_safety_message` | `false` | boolean | Add safety system message |

**Adjusting Sensitivity:**

```python
# Strict moderation (more false positives)
export FAKEAI_MODERATION_THRESHOLD=0.3

# Lenient moderation (fewer false positives)
export FAKEAI_MODERATION_THRESHOLD=0.7
```

### 2.3 Reasoning Models Support

**What are Reasoning Models?**

Reasoning models (like deepseek-ai/DeepSeek-R1, o3) provide:
- Extended thinking before responding
- Chain-of-thought reasoning
- Problem decomposition
- Self-correction

**FakeAI Simulation:**

When using reasoning models, FakeAI simulates:
- Extended processing time
- Reasoning tokens in usage statistics
- "Thinking" phase before response

**Using Reasoning Models:**

```python
from openai import OpenAI

client = OpenAI(
    api_key="test-key",
    base_url="http://localhost:8000/v1",
)

# Use deepseek-ai/DeepSeek-R1 reasoning model
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1",
    messages=[
        {"role": "user", "content": "Solve: If x^2 = 16, what are all possible values of x?"}
    ]
)

# Check reasoning tokens
print(f"Reasoning tokens: {response.usage.completion_tokens_details.reasoning_tokens}")
print(f"Regular tokens: {response.usage.completion_tokens}")

# Output:
# Reasoning tokens: 150
# Regular tokens: 50
```

**Available Reasoning Models:**

| Model | Context | Description |
|-------|---------|-------------|
| `deepseek-ai/DeepSeek-R1` | 128K | Most capable reasoning model |
| `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` | 128K | Faster, more affordable reasoning |
| `o3-mini` | 200K | Latest reasoning model |

**Reasoning vs. Regular Models:**

```python
# Regular model (fast, direct answer)
response_gpt4 = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "What is 2+2?"}]
)
# Latency: ~0.5s, Tokens: 5

# Reasoning model (thinking time + answer)
response_o1 = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1",
    messages=[{"role": "user", "content": "What is 2+2?"}]
)
# Latency: ~2.5s, Reasoning tokens: 50, Regular tokens: 5
```

**Best Practices:**

1. **Use reasoning models for:**
   - Math problems
   - Logic puzzles
   - Complex analysis
   - Code debugging
   - Multi-step reasoning

2. **Avoid reasoning models for:**
   - Simple queries
   - Chat conversations
   - Real-time responses
   - High-throughput scenarios

### 2.4 Predicted Outputs (Speculative Decoding)

**What are Predicted Outputs?**

Predicted outputs enable speculative decoding:
- You provide a prediction of what the model will generate
- Model verifies/corrects your prediction
- If correct, saves computation time
- Tracks acceptance/rejection rates

**Enabling Predicted Outputs:**

```python
from openai import OpenAI

client = OpenAI(
    api_key="test-key",
    base_url="http://localhost:8000/v1",
)

# Provide prediction
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "user", "content": "Say 'Hello, world!'"}
    ],
    prediction={
        "type": "content",
        "content": "Hello, world!"
    }
)

# Check acceptance rate
details = response.usage.completion_tokens_details
print(f"Accepted: {details.accepted_prediction_tokens}")
print(f"Rejected: {details.rejected_prediction_tokens}")

# Output:
# Accepted: 3 (if prediction matched)
# Rejected: 0
```

**Use Cases:**

| Scenario | Prediction Strategy |
|----------|---------------------|
| Code completion | Previous version of code |
| Translation | Machine translation draft |
| Summarization | Extractive summary |
| Chat continuation | Template response |

**Best Practices:**

```python
# Good prediction (high acceptance rate)
prediction = {
    "type": "content",
    "content": "I'd be happy to help! Let me explain..."
}

# Poor prediction (low acceptance rate)
prediction = {
    "type": "content",
    "content": "Random unrelated text that won't match"
}
```

**Monitoring Performance:**

```python
# Track prediction accuracy across requests
total_accepted = 0
total_rejected = 0

for request in requests:
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=request.messages,
        prediction=request.prediction
    )

    total_accepted += response.usage.completion_tokens_details.accepted_prediction_tokens
    total_rejected += response.usage.completion_tokens_details.rejected_prediction_tokens

acceptance_rate = total_accepted / (total_accepted + total_rejected)
print(f"Prediction accuracy: {acceptance_rate:.2%}")
```

### 2.5 Enhanced Security Features

**What's New in Security?**

v0.0.5 adds comprehensive security:
- Input validation and sanitization
- Injection attack detection
- IP-based abuse prevention
- Request size limits
- CORS configuration
- API key hashing

**Enabling Security Features:**

```bash
# Enable all security features
export FAKEAI_HASH_API_KEYS=true
export FAKEAI_ENABLE_INPUT_VALIDATION=true
export FAKEAI_ENABLE_INJECTION_DETECTION=true
export FAKEAI_ENABLE_ABUSE_DETECTION=true
export FAKEAI_MAX_REQUEST_SIZE=10485760  # 10 MB

# Configure CORS
export FAKEAI_CORS_ALLOWED_ORIGINS="https://example.com,https://app.example.com"
export FAKEAI_CORS_ALLOW_CREDENTIALS=true
```

**Input Validation:**

Automatically validates and sanitizes:
- SQL injection patterns
- XSS attempts
- Path traversal
- Command injection
- Null bytes

**Injection Detection:**

Detects and blocks:
- Prompt injection attempts
- Role-switching attacks
- System prompt leakage
- Multi-stage exploits

**Abuse Detection:**

Tracks per-IP:
- Request rate
- Error rate
- Malicious pattern frequency
- Automatic banning after threshold

**Configuration:**

| Option | Default | Description |
|--------|---------|-------------|
| `hash_api_keys` | `true` | Hash API keys (recommended) |
| `enable_input_validation` | `true` | Validate/sanitize input |
| `enable_injection_detection` | `true` | Detect injection attacks |
| `enable_abuse_detection` | `true` | IP-based abuse prevention |
| `max_request_size` | `10 MB` | Max request size |
| `cors_allowed_origins` | `["*"]` | CORS allowed origins |
| `cors_allow_credentials` | `true` | CORS credentials |
| `abuse_cleanup_interval` | `3600` | Cleanup interval (seconds) |

**Monitoring Security:**

```bash
# Check metrics for security events
curl http://localhost:8000/metrics | jq '.security'

# Example output:
{
  "blocked_requests": 42,
  "injection_attempts": 15,
  "banned_ips": 3,
  "validation_errors": 27
}
```

### 2.6 Rate Limiting Improvements

**What Changed?**

Rate limiting now matches OpenAI's tier structure:

| Tier | RPM | TPM | Description |
|------|-----|-----|-------------|
| `free` | 3 | 40,000 | Free tier limits |
| `tier-1` | 500 | 200,000 | Paid tier 1 |
| `tier-2` | 5,000 | 2,000,000 | Paid tier 2 |
| `tier-3` | 10,000 | 10,000,000 | Paid tier 3 |
| `tier-4` | 30,000 | 100,000,000 | Paid tier 4 |
| `tier-5` | 100,000 | 300,000,000 | Paid tier 5 |

**Configuring Rate Limits:**

```bash
# Use tier-based limits
export FAKEAI_RATE_LIMIT_ENABLED=true
export FAKEAI_RATE_LIMIT_TIER=tier-2

# Or use custom limits
export FAKEAI_RATE_LIMIT_ENABLED=true
export FAKEAI_RATE_LIMIT_RPM=1000
export FAKEAI_RATE_LIMIT_TPM=500000
```

**Handling Rate Limit Errors:**

```python
from openai import OpenAI, RateLimitError

client = OpenAI(
    api_key="test-key",
    base_url="http://localhost:8000/v1",
)

try:
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Hello"}]
    )
except RateLimitError as e:
    print(f"Rate limited: {e}")
    # Response headers include:
    # - x-ratelimit-limit-requests
    # - x-ratelimit-limit-tokens
    # - x-ratelimit-remaining-requests
    # - x-ratelimit-remaining-tokens
    # - x-ratelimit-reset-requests
    # - x-ratelimit-reset-tokens
```

### 2.7 Batch API

**What is Batch API?**

Process multiple requests asynchronously:
- Submit batch jobs
- Track status
- Retrieve results
- Cost-effective for large volumes

**Creating Batch Jobs:**

```python
from openai import OpenAI

client = OpenAI(
    api_key="test-key",
    base_url="http://localhost:8000/v1",
)

# Create batch job
batch = client.batches.create(
    input_file_id="file-abc123",
    endpoint="/v1/chat/completions",
    completion_window="24h"
)

print(f"Batch ID: {batch.id}")
print(f"Status: {batch.status}")
# Output: Status: validating
```

**Checking Batch Status:**

```python
# Get batch status
batch = client.batches.retrieve(batch_id)

print(f"Status: {batch.status}")
print(f"Completed: {batch.request_counts.completed}")
print(f"Failed: {batch.request_counts.failed}")
print(f"Total: {batch.request_counts.total}")

# Statuses: validating, in_progress, completed, failed, cancelling, cancelled
```

**Listing Batches:**

```python
# List all batches
batches = client.batches.list(limit=10)

for batch in batches.data:
    print(f"{batch.id}: {batch.status}")
```

**Cancelling Batches:**

```python
# Cancel a batch
batch = client.batches.cancel(batch_id)

print(f"Status: {batch.status}")
# Output: Status: cancelling
```

### 2.8 Real-time WebSocket API

**What is Real-time API?**

Bidirectional streaming via WebSocket:
- Real-time voice/text conversation
- Function calling during conversation
- Audio/text modalities
- Turn detection

**Connecting to Real-time API:**

```python
import websocket
import json

ws = websocket.create_connection(
    "ws://localhost:8000/v1/realtime?model=openai/gpt-oss-120b-realtime-preview"
)

# Configure session
ws.send(json.dumps({
    "type": "session.update",
    "session": {
        "modalities": ["text", "audio"],
        "voice": "alloy",
        "turn_detection": {
            "type": "server_vad",
            "threshold": 0.5,
            "silence_duration_ms": 500
        }
    }
}))

# Send user message
ws.send(json.dumps({
    "type": "conversation.item.create",
    "item": {
        "type": "message",
        "role": "user",
        "content": [{"type": "text", "text": "Hello!"}]
    }
}))

# Request response
ws.send(json.dumps({
    "type": "response.create"
}))

# Receive events
while True:
    message = ws.recv()
    event = json.loads(message)

    if event["type"] == "response.done":
        break

    print(f"Event: {event['type']}")

ws.close()
```

**Event Types:**

| Client → Server | Description |
|-----------------|-------------|
| `session.update` | Update session configuration |
| `conversation.item.create` | Add message to conversation |
| `response.create` | Request model response |
| `response.cancel` | Cancel in-progress response |

| Server → Client | Description |
|-----------------|-------------|
| `session.created` | Session initialized |
| `conversation.item.created` | Item added |
| `response.created` | Response started |
| `response.done` | Response completed |
| `response.audio.delta` | Audio chunk |
| `response.text.delta` | Text chunk |

---

## 3. Configuration Migration

### 3.1 Environment Variables

**Old (v0.0.4):**
```bash
export FAKEAI_HOST=127.0.0.1
export FAKEAI_PORT=8000
export FAKEAI_DEBUG=false
export FAKEAI_RESPONSE_DELAY=0.5
export FAKEAI_RANDOM_DELAY=true
export FAKEAI_MAX_VARIANCE=0.3
export FAKEAI_API_KEYS=sk-key1,sk-key2
export FAKEAI_REQUIRE_API_KEY=false
export FAKEAI_RATE_LIMIT_ENABLED=false
export FAKEAI_REQUESTS_PER_MINUTE=10000
```

**New (v0.0.5):**
```bash
# Server settings (unchanged)
export FAKEAI_HOST=127.0.0.1
export FAKEAI_PORT=8000
export FAKEAI_DEBUG=false

# Simulated settings (unchanged)
export FAKEAI_RESPONSE_DELAY=0.5
export FAKEAI_RANDOM_DELAY=true
export FAKEAI_MAX_VARIANCE=0.3

# API settings (updated)
export FAKEAI_API_KEYS=sk-key1,sk-key2
export FAKEAI_REQUIRE_API_KEY=false
export FAKEAI_RATE_LIMIT_ENABLED=false
export FAKEAI_RATE_LIMIT_TIER=tier-1          # NEW: tier-based limits
export FAKEAI_RATE_LIMIT_RPM=500              # NEW: custom RPM
export FAKEAI_RATE_LIMIT_TPM=200000           # NEW: custom TPM

# Security settings (NEW)
export FAKEAI_HASH_API_KEYS=true
export FAKEAI_ENABLE_INPUT_VALIDATION=true
export FAKEAI_ENABLE_INJECTION_DETECTION=true
export FAKEAI_ENABLE_ABUSE_DETECTION=true
export FAKEAI_MAX_REQUEST_SIZE=10485760
export FAKEAI_CORS_ALLOWED_ORIGINS="*"
export FAKEAI_CORS_ALLOW_CREDENTIALS=true
export FAKEAI_ABUSE_CLEANUP_INTERVAL=3600

# Prompt caching settings (unchanged)
export FAKEAI_ENABLE_PROMPT_CACHING=true
export FAKEAI_CACHE_TTL_SECONDS=600
export FAKEAI_MIN_TOKENS_FOR_CACHE=1024

# KV cache settings (NEW)
export FAKEAI_KV_CACHE_ENABLED=true
export FAKEAI_KV_CACHE_BLOCK_SIZE=16
export FAKEAI_KV_CACHE_NUM_WORKERS=4
export FAKEAI_KV_OVERLAP_WEIGHT=1.0

# Moderation settings (NEW)
export FAKEAI_ENABLE_MODERATION=true
export FAKEAI_MODERATION_THRESHOLD=0.5
export FAKEAI_ENABLE_REFUSALS=true
export FAKEAI_ENABLE_SAFETY_FEATURES=true
export FAKEAI_ENABLE_JAILBREAK_DETECTION=true
export FAKEAI_PREPEND_SAFETY_MESSAGE=false

# Audio settings (NEW)
export FAKEAI_ENABLE_AUDIO=true
export FAKEAI_DEFAULT_VOICE=alloy
export FAKEAI_DEFAULT_AUDIO_FORMAT=mp3

# Performance settings (NEW)
export FAKEAI_ENABLE_CONTEXT_VALIDATION=true
export FAKEAI_STRICT_TOKEN_COUNTING=false

# Streaming settings (NEW)
export FAKEAI_STREAM_TIMEOUT_SECONDS=300.0
export FAKEAI_STREAM_TOKEN_TIMEOUT_SECONDS=30.0
export FAKEAI_STREAM_KEEPALIVE_ENABLED=true
export FAKEAI_STREAM_KEEPALIVE_INTERVAL_SECONDS=15.0
```

### 3.2 CLI Arguments

**Old (v0.0.4):**
```bash
fakeai-server \
  --host 127.0.0.1 \
  --port 8000 \
  --debug \
  --response-delay 0.5 \
  --api-key sk-test-key \
  --require-api-key
```

**New (v0.0.5):**
```bash
fakeai-server \
  --host 127.0.0.1 \
  --port 8000 \
  --debug \
  --response-delay 0.5 \
  --api-key sk-test-key \
  --require-api-key \
  --rate-limit-tier tier-1 \
  --kv-cache-enabled \
  --enable-moderation \
  --enable-input-validation \
  --enable-audio
```

### 3.3 Python Configuration

**Old (v0.0.4):**
```python
from fakeai import AppConfig

config = AppConfig(
    host="127.0.0.1",
    port=8000,
    debug=False,
    response_delay=0.5,
    random_delay=True,
    max_variance=0.3,
    api_keys=["sk-key1"],
    require_api_key=False,
    rate_limit_enabled=False,
    requests_per_minute=10000,
)
```

**New (v0.0.5):**
```python
from fakeai import AppConfig

config = AppConfig(
    # Server settings (unchanged)
    host="127.0.0.1",
    port=8000,
    debug=False,

    # Simulated settings (unchanged)
    response_delay=0.5,
    random_delay=True,
    max_variance=0.3,

    # API settings (updated)
    api_keys=["sk-key1"],
    require_api_key=False,
    rate_limit_enabled=False,
    rate_limit_tier="tier-1",        # NEW
    rate_limit_rpm=500,              # NEW
    rate_limit_tpm=200000,           # NEW

    # Security settings (NEW)
    hash_api_keys=True,
    enable_input_validation=True,
    enable_injection_detection=True,
    enable_abuse_detection=True,
    max_request_size=10 * 1024 * 1024,
    cors_allowed_origins=["*"],
    cors_allow_credentials=True,

    # KV cache settings (NEW)
    kv_cache_enabled=True,
    kv_cache_block_size=16,
    kv_cache_num_workers=4,
    kv_overlap_weight=1.0,

    # Moderation settings (NEW)
    enable_moderation=True,
    moderation_threshold=0.5,
    enable_refusals=True,
    enable_safety_features=True,
    enable_jailbreak_detection=True,

    # Audio settings (NEW)
    enable_audio=True,
    default_voice="alloy",
    default_audio_format="mp3",

    # Streaming settings (NEW)
    stream_timeout_seconds=300.0,
    stream_token_timeout_seconds=30.0,
    stream_keepalive_enabled=True,
    stream_keepalive_interval_seconds=15.0,
)
```

### 3.4 Migration Checklist

- [ ] Update FakeAI to v0.0.5
- [ ] Review configuration changes
- [ ] Update environment variables
- [ ] Update CLI arguments
- [ ] Update Python configuration
- [ ] Test existing functionality
- [ ] Enable new features incrementally
- [ ] Monitor metrics and logs
- [ ] Update client code for new features
- [ ] Update tests for new features
- [ ] Document configuration changes

---

## 4. Code Examples

### 4.1 Before/After: Basic Chat

**Before (v0.0.4):**
```python
from openai import OpenAI

client = OpenAI(
    api_key="test-key",
    base_url="http://localhost:8000/v1",
)

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

**After (v0.0.5) - Same code works!**
```python
from openai import OpenAI

client = OpenAI(
    api_key="test-key",
    base_url="http://localhost:8000/v1",
)

# Same code, but now with:
# - KV cache tracking
# - Security validation
# - Enhanced metrics
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)

# NEW: Check KV cache metrics
print(f"Cached tokens: {response.usage.prompt_tokens_details.cached_tokens}")
```

### 4.2 Before/After: Streaming

**Before (v0.0.4):**
```python
stream = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

**After (v0.0.5) - Enhanced streaming:**
```python
stream = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True,
    stream_options={"include_usage": True}  # NEW: Include usage in stream
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")

    # NEW: Get usage from final chunk
    if chunk.usage:
        print(f"\n\nTotal tokens: {chunk.usage.total_tokens}")
        print(f"Cached: {chunk.usage.prompt_tokens_details.cached_tokens}")
```

### 4.3 Before/After: Embeddings

**Before (v0.0.4):**
```python
response = client.embeddings.create(
    model="sentence-transformers/all-mpnet-base-v2",
    input="Hello, world!"
)

embedding = response.data[0].embedding
print(f"Embedding dimension: {len(embedding)}")
```

**After (v0.0.5) - Same code works!**
```python
response = client.embeddings.create(
    model="sentence-transformers/all-mpnet-base-v2",
    input="Hello, world!"
)

embedding = response.data[0].embedding
print(f"Embedding dimension: {len(embedding)}")

# NEW: Check usage
print(f"Total tokens: {response.usage.total_tokens}")
```

### 4.4 New Feature: Moderation

```python
# NEW in v0.0.5
response = client.moderations.create(
    input="I want to hurt someone"
)

moderation = response.results[0]

if moderation.flagged:
    print("Content flagged!")

    for category in ["violence", "hate", "self-harm", "sexual", "harassment"]:
        score = getattr(moderation.category_scores, category.replace("-", "_"))
        if score > 0.5:
            print(f"{category}: {score:.2%}")
```

### 4.5 New Feature: Predicted Outputs

```python
# NEW in v0.0.5
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {"role": "user", "content": "Complete this: The sky is"}
    ],
    prediction={
        "type": "content",
        "content": " blue."
    }
)

# Check if prediction was accepted
details = response.usage.completion_tokens_details
if details.accepted_prediction_tokens > 0:
    print(f"Prediction accepted: {details.accepted_prediction_tokens} tokens")
else:
    print(f"Prediction rejected: {details.rejected_prediction_tokens} tokens")
```

### 4.6 New Feature: Reasoning Models

```python
# NEW in v0.0.5
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1",  # Reasoning model
    messages=[
        {"role": "user", "content": "Solve: x^2 - 5x + 6 = 0"}
    ]
)

# Check reasoning tokens
print(f"Reasoning tokens: {response.usage.completion_tokens_details.reasoning_tokens}")
print(f"Response: {response.choices[0].message.content}")
```

### 4.7 New Feature: Batch Processing

```python
# NEW in v0.0.5
import json

# Create batch file
requests = [
    {"custom_id": "req-1", "method": "POST", "url": "/v1/chat/completions",
     "body": {"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hi"}]}},
    {"custom_id": "req-2", "method": "POST", "url": "/v1/chat/completions",
     "body": {"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hello"}]}},
]

# Upload file
with open("batch_input.jsonl", "w") as f:
    for req in requests:
        f.write(json.dumps(req) + "\n")

file = client.files.create(
    file=open("batch_input.jsonl", "rb"),
    purpose="batch"
)

# Create batch
batch = client.batches.create(
    input_file_id=file.id,
    endpoint="/v1/chat/completions",
    completion_window="24h"
)

# Poll for completion
import time

while batch.status in ["validating", "in_progress"]:
    time.sleep(5)
    batch = client.batches.retrieve(batch.id)
    print(f"Status: {batch.status}")

# Get results
if batch.status == "completed":
    output_file = client.files.content(batch.output_file_id)
    print(output_file.read())
```

### 4.8 New Feature: Real-time API

```python
# NEW in v0.0.5
import websocket
import json
import base64

ws = websocket.create_connection(
    "ws://localhost:8000/v1/realtime?model=openai/gpt-oss-120b-realtime-preview"
)

# Configure audio
ws.send(json.dumps({
    "type": "session.update",
    "session": {
        "modalities": ["audio", "text"],
        "voice": "alloy",
        "input_audio_format": "pcm16",
        "output_audio_format": "pcm16"
    }
}))

# Send audio
with open("input.wav", "rb") as f:
    audio_data = base64.b64encode(f.read()).decode()

ws.send(json.dumps({
    "type": "input_audio_buffer.append",
    "audio": audio_data
}))

ws.send(json.dumps({
    "type": "input_audio_buffer.commit"
}))

# Request response
ws.send(json.dumps({
    "type": "response.create"
}))

# Receive audio response
audio_chunks = []
while True:
    message = ws.recv()
    event = json.loads(message)

    if event["type"] == "response.audio.delta":
        audio_chunks.append(event["delta"])

    if event["type"] == "response.done":
        break

# Save audio
with open("output.wav", "wb") as f:
    f.write(base64.b64decode("".join(audio_chunks)))

ws.close()
```

---

## 5. Troubleshooting

### 5.1 Common Issues

#### Issue 1: "Model not found" errors

**Symptoms:**
```
Error: Model 'my-custom-model' not found
```

**Solution:**

FakeAI auto-creates models on first use. This should not happen in v0.0.5.

If it does:
```python
# Explicitly create model via API
response = requests.get(
    "http://localhost:8000/v1/models/my-custom-model"
)
# Model is now created
```

#### Issue 2: KV cache not working

**Symptoms:**
```python
# All requests show 0 cached tokens
response.usage.prompt_tokens_details.cached_tokens  # Always 0
```

**Solution:**

1. Check KV cache is enabled:
   ```bash
   curl http://localhost:8000/health | jq '.config.kv_cache_enabled'
   ```

2. Ensure requests have overlapping context:
   ```python
   # First request
   messages1 = [{"role": "user", "content": "Hello"}]

   # Second request must include first request's context
   messages2 = [
       {"role": "user", "content": "Hello"},
       {"role": "assistant", "content": response1.choices[0].message.content},
       {"role": "user", "content": "How are you?"}
   ]
   ```

3. Check minimum token threshold:
   ```bash
   # Default is 1024 tokens
   export FAKEAI_MIN_TOKENS_FOR_CACHE=100  # Lower threshold
   ```

#### Issue 3: Moderation blocking legitimate content

**Symptoms:**
```python
# Legitimate requests get flagged
response = client.moderations.create(input="How to cook chicken")
response.results[0].flagged  # True (false positive)
```

**Solution:**

Adjust moderation threshold:
```bash
# Make moderation less sensitive
export FAKEAI_MODERATION_THRESHOLD=0.7  # Higher = less sensitive
```

Or disable specific categories:
```bash
# Disable moderation entirely for testing
export FAKEAI_ENABLE_MODERATION=false
```

#### Issue 4: Rate limiting too strict

**Symptoms:**
```
Error: Rate limit exceeded (429)
```

**Solution:**

1. Increase tier:
   ```bash
   export FAKEAI_RATE_LIMIT_TIER=tier-5
   ```

2. Or disable rate limiting:
   ```bash
   export FAKEAI_RATE_LIMIT_ENABLED=false
   ```

3. Or set custom limits:
   ```bash
   export FAKEAI_RATE_LIMIT_RPM=100000
   export FAKEAI_RATE_LIMIT_TPM=50000000
   ```

#### Issue 5: Input validation errors

**Symptoms:**
```
Error: Input validation failed
```

**Solution:**

1. Check for special characters:
   ```python
   # Avoid null bytes, SQL injection patterns
   content = content.replace("\x00", "")
   ```

2. Disable validation for testing:
   ```bash
   export FAKEAI_ENABLE_INPUT_VALIDATION=false
   ```

#### Issue 6: Streaming timeouts

**Symptoms:**
```
Error: Stream timeout after 30 seconds
```

**Solution:**

Increase timeout:
```bash
export FAKEAI_STREAM_TIMEOUT_SECONDS=600.0  # 10 minutes
export FAKEAI_STREAM_TOKEN_TIMEOUT_SECONDS=60.0  # 1 minute per token
```

#### Issue 7: Audio not working

**Symptoms:**
```python
# Audio input/output not included in response
response.choices[0].message.audio  # None
```

**Solution:**

1. Enable audio:
   ```bash
   export FAKEAI_ENABLE_AUDIO=true
   ```

2. Use audio-capable model:
   ```python
   response = client.chat.completions.create(
       model="openai/gpt-oss-120b-audio-preview",  # Audio-capable model
       messages=[...],
       modalities=["text", "audio"],
       audio={"voice": "alloy", "format": "mp3"}
   )
   ```

#### Issue 8: Batch jobs stuck in "validating"

**Symptoms:**
```python
batch = client.batches.retrieve(batch_id)
batch.status  # "validating" for too long
```

**Solution:**

1. Check batch file format:
   ```jsonl
   {"custom_id": "req-1", "method": "POST", "url": "/v1/chat/completions", "body": {...}}
   ```

2. Cancel and recreate:
   ```python
   client.batches.cancel(batch_id)
   batch = client.batches.create(...)
   ```

3. Check server logs:
   ```bash
   tail -f fakeai.log
   ```

#### Issue 9: WebSocket connection refused

**Symptoms:**
```
Error: Connection refused to ws://localhost:8000/v1/realtime
```

**Solution:**

1. Check server is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Use correct URL format:
   ```python
   ws_url = "ws://localhost:8000/v1/realtime?model=openai/gpt-oss-120b-realtime-preview"
   ```

3. Check WebSocket support:
   ```bash
   # FakeAI uses Hypercorn which supports WebSocket
   pip show hypercorn
   ```

### 5.2 FAQ

**Q: Is v0.0.5 backward compatible with v0.0.4?**

A: Yes! All existing code will work without changes. New features are opt-in.

---

**Q: Do I need to update my client code?**

A: No, unless you want to use new features (KV cache metrics, moderation, etc.).

---

**Q: Will my existing configuration still work?**

A: Yes. All v0.0.4 configuration options are still supported. New options have sensible defaults.

---

**Q: How do I disable new features?**

A: Set corresponding environment variables to `false`:
```bash
export FAKEAI_KV_CACHE_ENABLED=false
export FAKEAI_ENABLE_MODERATION=false
export FAKEAI_ENABLE_INPUT_VALIDATION=false
```

---

**Q: Are there any performance impacts?**

A: Minimal. New features add negligible overhead:
- KV cache: ~5ms per request (caching overhead)
- Moderation: ~10ms per request (pattern matching)
- Security validation: ~2ms per request (input checks)

---

**Q: Can I use new features with old OpenAI client versions?**

A: Most features yes, but for full support use OpenAI Python client v1.0.0+:
```bash
pip install --upgrade openai
```

---

**Q: How do I monitor KV cache performance?**

A: Check metrics endpoint:
```bash
curl http://localhost:8000/metrics | jq '.kv_cache'
```

---

**Q: What happens if I exceed rate limits?**

A: You'll receive a 429 error with retry-after headers:
```python
try:
    response = client.chat.completions.create(...)
except RateLimitError as e:
    retry_after = e.response.headers.get("retry-after")
    print(f"Retry after {retry_after} seconds")
```

---

**Q: Can I customize moderation categories?**

A: Not currently. FakeAI uses predefined categories matching OpenAI's API. You can adjust the threshold:
```bash
export FAKEAI_MODERATION_THRESHOLD=0.7
```

---

**Q: How accurate is the KV cache simulation?**

A: FakeAI simulates cache behavior realistically:
- Prefix matching based on token overlap
- Block-level caching (configurable block size)
- Cache hit/miss ratios in metrics
- Time savings reflected in response times

However, it's a simulation - actual cache behavior may vary.

---

**Q: Do reasoning models actually "think"?**

A: No. FakeAI simulates reasoning by:
- Adding extra processing time
- Generating longer responses
- Including "reasoning tokens" in usage

It's for testing API integration, not actual reasoning.

---

**Q: Can I run FakeAI in production?**

A: FakeAI is designed for testing/development. For production:
-  Use for: Testing, CI/CD, development, demos
-  Don't use for: Real AI inference, production APIs

---

**Q: How do I report bugs or request features?**

A: Open an issue on GitHub:
https://github.com/ajcasagrande/fakeai/issues

---

### 5.3 Getting Help

**Documentation:**
- README: https://github.com/ajcasagrande/fakeai#readme
- API Docs: http://localhost:8000/docs (when server is running)
- CLAUDE.md: Comprehensive knowledge base

**Support:**
- GitHub Issues: https://github.com/ajcasagrande/fakeai/issues
- GitHub Discussions: https://github.com/ajcasagrande/fakeai/discussions

**Debugging:**
```bash
# Enable debug mode
fakeai-server --debug

# Check logs
tail -f fakeai.log

# Check metrics
curl http://localhost:8000/metrics | jq

# Check health
curl http://localhost:8000/health | jq
```

---

## Summary

FakeAI v0.0.5 introduces powerful new features while maintaining full backward compatibility:

 **No breaking changes** - existing code works without modifications
 **Opt-in features** - enable what you need, when you need it
 **Enhanced security** - input validation, injection detection, abuse prevention
 **Better performance** - KV cache simulation, predicted outputs
 **Safety features** - content moderation, jailbreak detection
 **New APIs** - batch processing, real-time WebSocket, moderation

**Quick Start:**
```bash
# Update FakeAI
pip install --upgrade fakeai

# Start server with new features
fakeai-server \
  --kv-cache-enabled \
  --enable-moderation \
  --enable-input-validation

# Your existing code works unchanged!
```

**Next Steps:**
1. Read feature adoption guide (Section 2)
2. Update configuration as needed (Section 3)
3. Try code examples (Section 4)
4. Monitor metrics and logs
5. Report issues/feedback on GitHub

Happy testing! 

---

**End of Migration Guide**
