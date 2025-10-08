"""
Asynchronous task execution utilities.

This module provides the AsyncExecutor class for running CPU-bound tasks
asynchronously with optional delays.
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import TypeVar

T = TypeVar("T")


class AsyncExecutor:
    """Executor for asynchronous tasks with delays.

    Optimized for CPU-bound tasks with configurable worker pool.
    """

    def __init__(self, max_workers: int = 8):
        """Initialize the async executor with optimized worker count.

        Args:
            max_workers: Number of worker threads (default: 8 for better throughput)
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def run_with_delay(
        self, func: Callable[..., T], *args, delay: float = 0, **kwargs
    ) -> T:
        """Run a function with a delay."""
        if delay > 0:
            await asyncio.sleep(delay)

        # Run the potentially CPU-bound function in a thread pool
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, lambda: func(*args, **kwargs))

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the executor and cleanup resources.

        Args:
            wait: If True, wait for all pending tasks to complete before shutting down
        """
        self.executor.shutdown(wait=wait)
