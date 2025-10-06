"""
FakeAI Client SDK and Testing Utilities.

This module provides a convenient wrapper around the OpenAI client for testing,
along with utilities for starting/stopping the server and validating responses.
"""

#  SPDX-License-Identifier: Apache-2.0

import contextlib
import subprocess
import threading
import time
from typing import Any, Generator

import pytest
from openai import OpenAI
from openai.types import CreateEmbeddingResponse
from openai.types.chat import ChatCompletion

try:
    from openai.types.moderation import ModerationCreateResponse
except ImportError:
    from openai.types import Moderation as ModerationCreateResponse

from fakeai.config import AppConfig
from fakeai.models import Usage


class FakeAIClient:
    """
    Wrapper around OpenAI client for testing with FakeAI server.

    Automatically points to localhost:8000 and provides convenience methods
    for testing. Can be used as a context manager to auto-start/stop server.

    Examples:
        # Basic usage (server already running)
        client = FakeAIClient()
        response = client.chat("Hello!")

        # With auto-started server
        with FakeAIClient(auto_start=True) as client:
            response = client.chat("Hello!")

        # Custom configuration
        config = AppConfig(response_delay=0.0, debug=True)
        with FakeAIClient(config=config, auto_start=True) as client:
            response = client.chat("Hello!")
    """

    def __init__(
        self,
        api_key: str = "test-key",
        base_url: str = "http://localhost:8000/v1",
        config: AppConfig | None = None,
        auto_start: bool = False,
        port: int = 8000,
        host: str = "127.0.0.1",
    ):
        """
        Initialize FakeAI client wrapper.

        Args:
            api_key: API key for authentication (default: "test-key")
            base_url: Base URL for the server (default: "http://localhost:8000/v1")
            config: AppConfig for server if auto_start is True
            auto_start: Whether to auto-start the server
            port: Port for server if auto_start is True
            host: Host for server if auto_start is True
        """
        self.api_key = api_key
        self.base_url = base_url
        self.config = config or AppConfig()
        self.auto_start = auto_start
        self.port = port
        self.host = host
        self._process: subprocess.Popen | None = None
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        """Get the underlying OpenAI client."""
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    def __enter__(self) -> "FakeAIClient":
        """Context manager entry - start server if auto_start is True."""
        if self.auto_start:
            self.start_server()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stop server if it was auto-started."""
        if self.auto_start and self._process is not None:
            self.stop_server()

    def start_server(self, timeout: float = 10.0) -> None:
        """
        Start the FakeAI server in a subprocess.

        Args:
            timeout: Maximum time to wait for server to start (seconds)

        Raises:
            RuntimeError: If server fails to start within timeout
        """
        import sys
        from pathlib import Path

        # Build command to start server
        cmd = [
            sys.executable,
            "-m",
            "fakeai.cli",
            "server",  # Add server subcommand
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--response-delay",
            str(self.config.response_delay),
        ]

        # Add API key if configured
        if self.config.api_keys:
            for key in self.config.api_keys:
                cmd.extend(["--api-key", key])

        # Start server process
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait for server to be ready
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Try to connect to health endpoint
                import json
                import urllib.request

                url = f"http://{self.host}:{self.port}/health"
                with urllib.request.urlopen(url, timeout=1.0) as response:
                    if response.status == 200:
                        # Check if server reports ready
                        data = json.loads(response.read().decode("utf-8"))
                        if data.get("ready", True):  # Default true for backward compat
                            return
            except Exception:
                pass
            time.sleep(0.1)

        # Server failed to start
        self.stop_server()
        raise RuntimeError(f"Server failed to start within {timeout}s")

    def stop_server(self) -> None:
        """Stop the FakeAI server if it's running."""
        if self._process is not None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
            self._process = None

    # Convenience methods for common operations

    def chat(
        self,
        message: str,
        model: str = "openai/gpt-oss-120b",
        system: str | None = None,
        **kwargs,
    ) -> ChatCompletion:
        """
        Simple chat completion with a single user message.

        Args:
            message: User message content
            model: Model ID (default: "openai/gpt-oss-120b")
            system: Optional system message
            **kwargs: Additional arguments for chat.completions.create

        Returns:
            ChatCompletion response
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs,
        )

    def stream_chat(
        self,
        message: str,
        model: str = "openai/gpt-oss-120b",
        system: str | None = None,
        **kwargs,
    ):
        """
        Streaming chat completion with a single user message.

        Args:
            message: User message content
            model: Model ID (default: "openai/gpt-oss-120b")
            system: Optional system message
            **kwargs: Additional arguments for chat.completions.create

        Returns:
            Generator of ChatCompletionChunk objects
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            **kwargs,
        )

    def embed(
        self,
        text: str | list[str],
        model: str = "sentence-transformers/all-mpnet-base-v2",
    ) -> CreateEmbeddingResponse:
        """
        Create embeddings for text.

        Args:
            text: Text or list of texts to embed
            model: Embedding model ID

        Returns:
            CreateEmbeddingResponse with embeddings
        """
        return self.client.embeddings.create(
            model=model,
            input=text,
        )

    def moderate(self, text: str | list[str]) -> ModerationCreateResponse:
        """
        Check content for moderation violations.

        Args:
            text: Text or list of texts to moderate

        Returns:
            ModerationCreateResponse with moderation results
        """
        return self.client.moderations.create(input=text)

    def list_models(self):
        """List available models."""
        return self.client.models.list()

    def get_model(self, model_id: str):
        """Get information about a specific model."""
        return self.client.models.retrieve(model_id)


# Testing Utilities


def assert_response_valid(response: ChatCompletion) -> None:
    """
    Validate that a chat completion response has valid schema.

    Args:
        response: ChatCompletion response to validate

    Raises:
        AssertionError: If response is invalid
    """
    assert response.id is not None, "Response ID is missing"
    assert response.id.startswith(
        "chatcmpl-"
    ), f"Invalid response ID format: {response.id}"
    assert response.model is not None, "Model is missing"
    assert response.created > 0, "Invalid created timestamp"
    assert len(response.choices) > 0, "No choices in response"

    # Validate first choice
    choice = response.choices[0]
    assert choice.message is not None, "Message is missing"
    assert choice.message.role == "assistant", f"Invalid role: {choice.message.role}"
    assert choice.finish_reason is not None, "Finish reason is missing"

    # Validate usage
    if response.usage:
        assert response.usage.prompt_tokens >= 0, "Invalid prompt tokens"
        assert response.usage.completion_tokens >= 0, "Invalid completion tokens"
        assert response.usage.total_tokens >= 0, "Invalid total tokens"
        assert (
            response.usage.total_tokens
            == response.usage.prompt_tokens + response.usage.completion_tokens
        ), "Total tokens doesn't match sum"


def assert_tokens_in_range(
    usage: Usage,
    min_prompt: int = 0,
    max_prompt: int | None = None,
    min_completion: int = 0,
    max_completion: int | None = None,
) -> None:
    """
    Assert that token counts are within expected ranges.

    Args:
        usage: Usage object from response
        min_prompt: Minimum expected prompt tokens
        max_prompt: Maximum expected prompt tokens (None for no limit)
        min_completion: Minimum expected completion tokens
        max_completion: Maximum expected completion tokens (None for no limit)

    Raises:
        AssertionError: If token counts are out of range
    """
    assert (
        usage.prompt_tokens >= min_prompt
    ), f"Prompt tokens {usage.prompt_tokens} < minimum {min_prompt}"
    if max_prompt is not None:
        assert (
            usage.prompt_tokens <= max_prompt
        ), f"Prompt tokens {usage.prompt_tokens} > maximum {max_prompt}"

    assert (
        usage.completion_tokens >= min_completion
    ), f"Completion tokens {usage.completion_tokens} < minimum {min_completion}"
    if max_completion is not None:
        assert (
            usage.completion_tokens <= max_completion
        ), f"Completion tokens {usage.completion_tokens} > maximum {max_completion}"


def assert_cache_hit(response: ChatCompletion) -> None:
    """
    Assert that response indicates a cache hit.

    Args:
        response: ChatCompletion response to check

    Raises:
        AssertionError: If response doesn't indicate cache hit
    """
    assert hasattr(response, "usage"), "Response has no usage information"
    usage = response.usage

    # Check for cached tokens in prompt_tokens_details
    if hasattr(usage, "prompt_tokens_details"):
        details = usage.prompt_tokens_details
        if hasattr(details, "cached_tokens"):
            assert details.cached_tokens > 0, "No cached tokens found"
        else:
            raise AssertionError("prompt_tokens_details has no cached_tokens field")
    else:
        raise AssertionError("Usage has no prompt_tokens_details")


def assert_moderation_flagged(
    result: ModerationCreateResponse,
    category: str | None = None,
) -> None:
    """
    Assert that content was flagged by moderation.

    Args:
        result: ModerationCreateResponse to check
        category: Optional specific category to check (e.g., "violence", "hate")

    Raises:
        AssertionError: If content was not flagged
    """
    assert len(result.results) > 0, "No moderation results"

    first_result = result.results[0]
    assert first_result.flagged, "Content was not flagged"

    if category:
        # Check specific category
        categories = first_result.categories
        category_dict = (
            categories.model_dump()
            if hasattr(categories, "model_dump")
            else dict(categories)
        )
        assert category_dict.get(
            category, False
        ), f"Category '{category}' was not flagged"


# Context Manager for Temporary Server


@contextlib.contextmanager
def temporary_server(
    config: AppConfig | None = None,
    port: int = 8000,
    host: str = "127.0.0.1",
    timeout: float = 10.0,
) -> Generator[FakeAIClient, None, None]:
    """
    Context manager that starts a temporary FakeAI server.

    Args:
        config: AppConfig for the server
        port: Port to bind server to
        host: Host to bind server to
        timeout: Maximum time to wait for server to start

    Yields:
        FakeAIClient connected to the temporary server

    Example:
        with temporary_server() as client:
            response = client.chat("Hello!")
            assert_response_valid(response)
    """
    config = config or AppConfig(
        response_delay=0.0,
        random_delay=False,
        require_api_key=False,
    )

    client = FakeAIClient(
        config=config,
        auto_start=True,
        port=port,
        host=host,
        base_url=f"http://{host}:{port}/v1",
    )

    try:
        client.start_server(timeout=timeout)
        yield client
    finally:
        client.stop_server()


# Pytest Fixtures


@pytest.fixture
def fakeai_client() -> Generator[FakeAIClient, None, None]:
    """
    Pytest fixture providing a FakeAIClient with auto-started server.

    Example:
        def test_chat(fakeai_client):
            response = fakeai_client.chat("Hello!")
            assert_response_valid(response)
    """
    config = AppConfig(
        response_delay=0.0,
        random_delay=False,
        require_api_key=False,
    )

    client = FakeAIClient(
        config=config,
        auto_start=True,
    )

    try:
        client.start_server()
        yield client
    finally:
        client.stop_server()


@pytest.fixture
def fakeai_client_with_auth() -> Generator[FakeAIClient, None, None]:
    """
    Pytest fixture providing a FakeAIClient with authentication enabled.

    Example:
        def test_auth(fakeai_client_with_auth):
            response = fakeai_client_with_auth.chat("Hello!")
            assert_response_valid(response)
    """
    config = AppConfig(
        response_delay=0.0,
        random_delay=False,
        require_api_key=True,
        api_keys=["test-key"],
    )

    client = FakeAIClient(
        config=config,
        auto_start=True,
        api_key="test-key",
    )

    try:
        client.start_server()
        yield client
    finally:
        client.stop_server()


@pytest.fixture
def fakeai_running_server() -> Generator[dict[str, Any], None, None]:
    """
    Pytest fixture that starts a FakeAI server and provides connection info.

    Returns dict with 'url', 'host', 'port', 'config' keys.

    Example:
        def test_with_server(fakeai_running_server):
            client = OpenAI(
                api_key="test",
                base_url=fakeai_running_server["url"],
            )
            response = client.chat.completions.create(...)
    """
    config = AppConfig(
        response_delay=0.0,
        random_delay=False,
        require_api_key=False,
    )

    port = 8000
    host = "127.0.0.1"

    client = FakeAIClient(
        config=config,
        auto_start=True,
        port=port,
        host=host,
    )

    try:
        client.start_server()
        yield {
            "url": f"http://{host}:{port}/v1",
            "host": host,
            "port": port,
            "config": config,
            "client": client,
        }
    finally:
        client.stop_server()


# Advanced Testing Utilities


def collect_stream_content(stream) -> str:
    """
    Collect all content from a streaming response.

    Args:
        stream: Stream of ChatCompletionChunk objects

    Returns:
        Complete concatenated content from stream
    """
    content_parts = []
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            content_parts.append(chunk.choices[0].delta.content)
    return "".join(content_parts)


def measure_stream_timing(stream) -> dict[str, float]:
    """
    Measure timing metrics for a streaming response.

    Args:
        stream: Stream of ChatCompletionChunk objects

    Returns:
        Dict with timing metrics:
            - time_to_first_token: Time to first content chunk (seconds)
            - total_time: Total time for entire stream (seconds)
            - chunks_count: Number of chunks received
            - avg_inter_token_latency: Average time between chunks (seconds)
    """
    start_time = time.time()
    first_token_time = None
    chunk_times = []
    chunk_count = 0

    for chunk in stream:
        current_time = time.time()
        if chunk.choices and chunk.choices[0].delta.content:
            if first_token_time is None:
                first_token_time = current_time - start_time
            chunk_times.append(current_time)
            chunk_count += 1

    total_time = time.time() - start_time

    # Calculate inter-token latency
    avg_itl = 0.0
    if len(chunk_times) > 1:
        latencies = [
            chunk_times[i] - chunk_times[i - 1] for i in range(1, len(chunk_times))
        ]
        avg_itl = sum(latencies) / len(latencies)

    return {
        "time_to_first_token": first_token_time or 0.0,
        "total_time": total_time,
        "chunks_count": chunk_count,
        "avg_inter_token_latency": avg_itl,
    }


def assert_streaming_valid(stream) -> None:
    """
    Assert that a streaming response is valid.

    Args:
        stream: Stream of ChatCompletionChunk objects

    Raises:
        AssertionError: If stream is invalid
    """
    chunk_count = 0
    has_content = False
    has_finish_reason = False

    for chunk in stream:
        chunk_count += 1
        assert chunk.id is not None, "Chunk ID is missing"
        assert len(chunk.choices) > 0, "No choices in chunk"

        choice = chunk.choices[0]
        if choice.delta.content:
            has_content = True

        if choice.finish_reason:
            has_finish_reason = True

    assert chunk_count > 0, "Stream produced no chunks"
    assert has_content, "Stream contained no content"
    assert has_finish_reason, "Stream had no finish_reason"
