#!/usr/bin/env python3
"""
Start FakeAI server with uvloop for ultimate async I/O performance.

uvloop provides:
- 2-4x faster than default asyncio
- Lower latency for concurrent connections
- Better throughput under load
- Native implementation of asyncio protocols in Cython
"""

# Install uvloop as the default event loop BEFORE any asyncio imports
try:
    import uvloop

    uvloop.install()
    print("✓ uvloop installed - using ultra-fast event loop (2-4x faster)")
except ImportError:
    print("⚠ uvloop not available - using default asyncio loop")
    print("  Install for better performance: pip install uvloop")

# Now import uvicorn and app
import uvicorn

from fakeai.app import app
from fakeai.config import AppConfig


def main():
    """Run server with uvloop optimization."""
    config = AppConfig()

    print()
    print("=" * 70)
    print("  FakeAI Server with uvloop - Ultimate Async I/O")
    print("=" * 70)
    print()
    print(f"  🚀 Server URL: http://{config.host}:{config.port}")
    print(f"  📊 Dashboard: http://{config.host}:{config.port}/dashboard/dynamo")
    print(f"  📈 Metrics: http://{config.host}:{config.port}/metrics")
    print(f"  🏥 Health: http://{config.host}:{config.port}/health")
    print()
    print("  Performance Optimizations:")
    print("    • uvloop event loop (if installed)")
    print("    • HTTP/1.1 with keep-alive")
    print("    • Limit concurrency: 2000")
    print("    • Async I/O throughout")
    print("=" * 70)
    print()

    # Run with uvicorn
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info",
        # Performance settings
        loop="uvloop",  # Use uvloop if available
        http="h11",  # HTTP protocol
        limit_concurrency=2000,  # Max concurrent connections
        limit_max_requests=None,  # No request limit per worker
        timeout_keep_alive=5,  # Keep-alive timeout
        # Connection settings
        backlog=2048,  # Socket backlog
        # Lifecycle
        lifespan="auto",  # Auto lifecycle management
    )


if __name__ == "__main__":
    main()
