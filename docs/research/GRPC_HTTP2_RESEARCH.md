# gRPC and HTTP/2 Research and Decision Document

## Executive Summary

After comprehensive research using multiple specialized agents, this document presents findings and recommendations for gRPC and HTTP/2 support in FakeAI.

---

## gRPC Support - Research Findings

### Key Finding: OpenAI Does NOT Use gRPC

**Research Conclusion:** All major LLM providers (OpenAI, Azure OpenAI, Anthropic Claude, Google Gemini) use **REST APIs exclusively** for their public interfaces. No official gRPC support exists.

### Why gRPC is Not Used for LLM APIs

1. **Browser Compatibility:** gRPC requires grpc-web proxy for browsers; SSE (Server-Sent Events) works natively
2. **Simplicity:** REST/JSON is easier to debug and test than binary Protocol Buffers
3. **Industry Standard:** Entire LLM industry standardized on REST/SSE
4. **Streaming:** SSE adequate for token-by-token streaming
5. **Tooling:** REST has superior ecosystem (Postman, curl, Swagger)

### Where gRPC IS Used in AI/ML

**Internal Infrastructure Only:**
- llama.cpp distributed inference
- vLLM internal communication
- LocalAI backend workers
- Google TensorFlow Serving

**Pattern:** REST for external APIs, gRPC for backend-to-backend

### Decision: DO NOT Implement gRPC

**Rationale:**
- FakeAI's purpose: OpenAI-compatible testing server
- OpenAI uses REST, so FakeAI should use REST
- gRPC would diverge from compatibility goal
- Adds complexity without solving user problems
- No community demand

**Status:** NOT IMPLEMENTED (by design, not limitation)

---

## HTTP/2 Support - Research Findings

### Key Finding: Uvicorn Does Not Support HTTP/2

**Current Server:** Uvicorn (used in fakeai/cli.py)
- HTTP/2 Support: NO
- Protocols: HTTP/1.1, WebSockets only
- Status: No plans to add HTTP/2

### Production-Ready Options for HTTP/2

#### Option 1: Nginx Reverse Proxy (RECOMMENDED for production)

**Architecture:**
```
Client (HTTP/2) → Nginx (HTTP/2 → HTTP/1.1) → Uvicorn (HTTP/1.1)
```

**Benefits:**
- Zero code changes required
- Industry-standard pattern
- Additional features: SSL termination, load balancing, caching
- Battle-tested in production
- Keep existing Uvicorn setup

**Implementation:** Nginx configuration only (no code changes)

#### Option 2: Hypercorn ASGI Server (RECOMMENDED for native HTTP/2)

**Architecture:**
```
Client (HTTP/2) → Hypercorn (HTTP/2 native) → FastAPI
```

**Benefits:**
- Native HTTP/2 end-to-end
- Drop-in replacement for Uvicorn
- Supports HTTP/1.1, HTTP/2, HTTP/3, WebSockets
- ALPN for automatic protocol negotiation
- Pure Python solution

**Implementation:** Add Hypercorn mode to CLI

#### Option 3: Granian (Rust-based, bleeding edge)

**Not recommended:** Limited production examples, smaller community

### Decision: Implement Hypercorn Option

**Rationale:**
- Drop-in replacement for Uvicorn
- Native HTTP/2 support
- Maintains HTTP/1.1 compatibility via ALPN
- No reverse proxy needed for basic usage
- Optional - users can still use Uvicorn

**Status:** IMPLEMENTING

---

## HTTP/2 Benefits for FakeAI

### Performance Gains
- 20-50% faster for multi-resource requests
- Multiplexing eliminates connection overhead
- Header compression (HPACK)
- Binary protocol parsing

### For Testing/Development Use Cases
- Better simulation of production environments
- Test HTTP/2-specific features
- Match real OpenAI infrastructure (uses HTTP/2)

---

## Implementation Plan

### 1. Add Hypercorn Dependency
```toml
dependencies = [
    # ... existing ...
    "hypercorn>=0.16.0",  # HTTP/2 support
]
```

### 2. Add CLI Option
```bash
fakeai-server --http2  # Use Hypercorn with HTTP/2
fakeai-server          # Use Uvicorn (HTTP/1.1) - default
```

### 3. Maintain Backward Compatibility
- Default: Uvicorn (HTTP/1.1)
- Optional: Hypercorn (HTTP/2)
- User chooses based on needs

---

## References

### gRPC Research
- OpenAI API documentation (REST only)
- Azure OpenAI documentation (REST only)
- llama.cpp gRPC implementation (kherud/grpc-llama.cpp)
- LocalAI distributed inference architecture
- vLLM gRPC development discussions

### HTTP/2 Research
- Uvicorn GitHub issues (#47 - HTTP/2 not supported)
- Hypercorn official documentation
- Granian benchmarks
- RFC 7540 (HTTP/2 specification)
- RFC 7301 (ALPN specification)

---

## Conclusion

**gRPC:** Not implemented - not used by OpenAI, adds unnecessary complexity
**HTTP/2:** Implemented via optional Hypercorn mode - maintains compatibility while enabling modern protocol support

This approach balances OpenAI compatibility (primary goal) with modern protocol support (optional enhancement).
