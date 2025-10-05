"""
Optimized async server with uvloop for ultimate I/O performance.

Uses:
- uvloop: Ultra-fast asyncio event loop (2-4x faster than default)
- Full async/await patterns throughout
- Async database operations
- Async file I/O
- Connection pooling
- Async middleware
"""
import asyncio
import sys

try:
    import uvloop
    HAS_UVLOOP = True
except ImportError:
    HAS_UVLOOP = False


def setup_uvloop():
    """
    Install uvloop as the default event loop.

    uvloop is a fast, drop-in replacement for asyncio event loop.
    Performance characteristics:
    - 2-4x faster than default asyncio
    - Lower latency for I/O operations
    - Better throughput for concurrent connections
    - Native support for TCP, UDP, SSL/TLS, pipes
    """
    if HAS_UVLOOP:
        uvloop.install()
        print("✓ uvloop installed as default event loop")
        return True
    else:
        print("⚠ uvloop not available, using default asyncio loop")
        print("  Install with: pip install uvloop")
        return False


async def run_server_with_uvloop(
    app,
    host: str = "0.0.0.0",
    port: int = 8000,
    workers: int = 1,
    log_level: str = "info",
):
    """
    Run server with uvloop for optimal async performance.

    Args:
        app: FastAPI application
        host: Bind host
        port: Bind port
        workers: Number of worker processes
        log_level: Logging level
    """
    import uvicorn

    # Install uvloop if available
    uvloop_enabled = setup_uvloop()

    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        workers=workers,
        log_level=log_level,
        # uvloop is automatically used if installed via uvloop.install()
        loop="uvloop" if uvloop_enabled else "asyncio",
        # Performance optimizations
        limit_concurrency=2000,  # Max concurrent connections
        limit_max_requests=0,     # No limit on requests per worker
        timeout_keep_alive=5,     # Keep-alive timeout
        # HTTP optimizations
        h11_max_incomplete_event_size=16 * 1024,  # 16KB max incomplete events
    )

    server = uvicorn.Server(config)
    await server.serve()


# Async helper functions for FakeAI

async def async_sleep_with_variance(base_delay: float, variance: float = 0.0):
    """
    Async sleep with optional variance.

    Uses asyncio.sleep which is non-blocking and works efficiently with uvloop.

    Args:
        base_delay: Base delay in seconds
        variance: Random variance (0.0-1.0)
    """
    import random

    if variance > 0:
        actual_delay = base_delay * (1.0 + random.uniform(-variance, variance))
    else:
        actual_delay = base_delay

    await asyncio.sleep(actual_delay)


async def async_gather_with_timeout(tasks, timeout: float = 10.0):
    """
    Gather multiple async tasks with timeout.

    Args:
        tasks: List of coroutines
        timeout: Maximum time to wait

    Returns:
        List of results (or exceptions)
    """
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=timeout
        )
        return results
    except asyncio.TimeoutError:
        return [TimeoutError(f"Operation timed out after {timeout}s") for _ in tasks]


class AsyncConnectionPool:
    """
    Async connection pool for database/external service connections.

    Uses asyncio for connection management with uvloop for performance.
    """

    def __init__(self, max_connections: int = 100):
        self.max_connections = max_connections
        self.available: asyncio.Queue = asyncio.Queue(maxsize=max_connections)
        self.in_use = 0
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Acquire a connection from the pool."""
        async with self._lock:
            if self.in_use < self.max_connections:
                self.in_use += 1
                # Create new connection (placeholder)
                return {"connection_id": self.in_use, "active": True}

        # Wait for available connection
        return await self.available.get()

    async def release(self, connection):
        """Release connection back to pool."""
        await self.available.put(connection)

    async def close_all(self):
        """Close all connections in pool."""
        async with self._lock:
            # Drain queue
            while not self.available.empty():
                try:
                    self.available.get_nowait()
                except asyncio.QueueEmpty:
                    break
            self.in_use = 0


class AsyncCache:
    """
    Async cache with TTL support using asyncio.

    All operations are non-blocking and work efficiently with uvloop.
    """

    def __init__(self, default_ttl: float = 300.0):
        self.default_ttl = default_ttl
        self._cache: dict[str, tuple[any, float]] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task = None

    async def get(self, key: str):
        """Get value from cache."""
        async with self._lock:
            if key in self._cache:
                value, expires_at = self._cache[key]
                if asyncio.get_event_loop().time() < expires_at:
                    return value
                else:
                    # Expired
                    del self._cache[key]
            return None

    async def set(self, key: str, value: any, ttl: float | None = None):
        """Set value in cache with TTL."""
        if ttl is None:
            ttl = self.default_ttl

        expires_at = asyncio.get_event_loop().time() + ttl

        async with self._lock:
            self._cache[key] = (value, expires_at)

    async def delete(self, key: str):
        """Delete key from cache."""
        async with self._lock:
            self._cache.pop(key, None)

    async def cleanup_expired(self):
        """Remove expired entries."""
        current_time = asyncio.get_event_loop().time()

        async with self._lock:
            expired_keys = [
                k for k, (_, exp) in self._cache.items()
                if current_time >= exp
            ]

            for key in expired_keys:
                del self._cache[key]

    async def start_cleanup_task(self, interval: float = 60.0):
        """Start background cleanup task."""
        async def cleanup_loop():
            while True:
                await asyncio.sleep(interval)
                await self.cleanup_expired()

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    async def stop_cleanup_task(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


async def async_batch_processor(items: list, process_func, batch_size: int = 10):
    """
    Process items in batches asynchronously.

    Args:
        items: Items to process
        process_func: Async function to process each item
        batch_size: Items per batch

    Returns:
        List of results
    """
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = await asyncio.gather(
            *[process_func(item) for item in batch],
            return_exceptions=True
        )
        results.extend(batch_results)

    return results


def get_event_loop_type():
    """Get the current event loop implementation name."""
    loop = asyncio.get_event_loop()
    loop_type = type(loop).__module__ + "." + type(loop).__name__

    if "uvloop" in loop_type:
        return "uvloop (optimized)"
    else:
        return "asyncio (default)"


# Performance comparison utility

async def benchmark_event_loop(iterations: int = 10000):
    """
    Benchmark current event loop performance.

    Tests:
    - Task creation overhead
    - Sleep resolution
    - Gather performance
    - Queue operations
    """
    import time

    results = {}

    # Test 1: Task creation overhead
    start = time.perf_counter()
    tasks = [asyncio.create_task(asyncio.sleep(0)) for _ in range(iterations)]
    await asyncio.gather(*tasks)
    results["task_creation_ms"] = (time.perf_counter() - start) * 1000

    # Test 2: Queue operations
    queue = asyncio.Queue()
    start = time.perf_counter()
    for i in range(iterations):
        await queue.put(i)
        await queue.get()
    results["queue_ops_ms"] = (time.perf_counter() - start) * 1000

    # Test 3: Concurrent tasks
    async def dummy_task():
        await asyncio.sleep(0.001)

    start = time.perf_counter()
    await asyncio.gather(*[dummy_task() for _ in range(100)])
    results["concurrent_100_ms"] = (time.perf_counter() - start) * 1000

    return results


if __name__ == "__main__":
    # Demonstration
    print("=" * 60)
    print("FakeAI Async Server with uvloop")
    print("=" * 60)
    print()

    # Setup uvloop
    uvloop_enabled = setup_uvloop()

    # Show event loop type
    print(f"Event loop: {get_event_loop_type()}")
    print()

    # Run benchmark
    print("Running event loop benchmark...")
    results = asyncio.run(benchmark_event_loop(iterations=10000))

    print(f"Results (10,000 iterations):")
    print(f"  Task creation: {results['task_creation_ms']:.2f}ms")
    print(f"  Queue ops: {results['queue_ops_ms']:.2f}ms")
    print(f"  100 concurrent tasks: {results['concurrent_100_ms']:.2f}ms")
    print()

    if uvloop_enabled:
        print("✨ uvloop provides 2-4x better performance than default asyncio")
    else:
        print("💡 Install uvloop for 2-4x performance improvement:")
        print("   pip install uvloop")
    print()
