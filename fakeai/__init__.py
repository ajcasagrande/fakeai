"""
FakeAI - OpenAI Compatible API Server

A fully-featured FastAPI implementation that mimics the OpenAI API.
It supports all endpoints and features of the official OpenAI API while returning
simulated responses instead of performing actual inference.
"""

#  SPDX-License-Identifier: Apache-2.0

__version__ = "0.0.4"

__all__ = [
    "app",
    "AppConfig",
    "FakeAIService",
    "RateLimiter",
    "run_server",
]
# Make key modules available at the package level for convenience

from fakeai.app import app as app
from fakeai.config import AppConfig as AppConfig
from fakeai.fakeai_service import FakeAIService as FakeAIService
from fakeai.rate_limiter import RateLimiter as RateLimiter
from fakeai.cli import main as run_server

# Optional imports for testing/development (requires dev dependencies)
try:
    from fakeai.client import (
        FakeAIClient,
        temporary_server,
        assert_response_valid,
        assert_tokens_in_range,
        assert_cache_hit,
        assert_moderation_flagged,
        assert_streaming_valid,
        collect_stream_content,
        measure_stream_timing,
    )
    __all__.extend([
        "FakeAIClient",
        "temporary_server",
        "assert_response_valid",
        "assert_tokens_in_range",
        "assert_cache_hit",
        "assert_moderation_flagged",
        "assert_streaming_valid",
        "collect_stream_content",
        "measure_stream_timing",
    ])
except ImportError:
    # Dev dependencies not installed, skip client utilities
    pass
