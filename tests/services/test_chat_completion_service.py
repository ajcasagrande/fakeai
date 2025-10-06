"""
Comprehensive tests for ChatCompletionService

Tests cover the core functionality of the chat completion service.
"""

#  SPDX-License-Identifier: Apache-2.0

import time

import pytest

from fakeai.config import AppConfig
from fakeai.dynamo_metrics import DynamoMetricsCollector
from fakeai.kv_cache import KVCacheMetrics, SmartRouter
from fakeai.metrics import MetricsTracker
from fakeai.models import (
    ChatCompletionRequest,
    Message,
    Role,
    StreamOptions,
)
from fakeai.services.chat_completion_service import ChatCompletionService


class MockModelRegistry:
    """Mock model registry for testing."""

    def __init__(self):
        self.models = {}

    def ensure_model_exists(self, model_id: str):
        """Auto-create models as needed."""
        if model_id not in self.models:
            self.models[model_id] = {"id": model_id, "created": int(time.time())}


@pytest.fixture
def config():
    """Create a test configuration."""
    return AppConfig(
        host="localhost",
        port=8000,
        debug=True,
        response_delay=0.0,  # Disable delay for testing
        ttft_ms=100.0,  # 100ms TTFT
        ttft_variance_percent=10.0,
        itl_ms=20.0,  # 20ms ITL
        itl_variance_percent=10.0,
    )


@pytest.fixture
def metrics_tracker():
    """Create a metrics tracker."""
    return MetricsTracker()


@pytest.fixture
def model_registry():
    """Create a model registry."""
    return MockModelRegistry()


@pytest.fixture
def kv_cache_router():
    """Create a KV cache router."""
    return SmartRouter(
        kv_overlap_weight=1.0,
        load_balance_weight=0.5,
        block_size=16,
        num_workers=4,
    )


@pytest.fixture
def kv_cache_metrics():
    """Create KV cache metrics tracker."""
    return KVCacheMetrics()


@pytest.fixture
def dynamo_metrics():
    """Create Dynamo metrics tracker."""
    return DynamoMetricsCollector()


@pytest.fixture
def chat_service(
    config,
    metrics_tracker,
    model_registry,
    kv_cache_router,
    kv_cache_metrics,
    dynamo_metrics,
):
    """Create a chat completion service."""
    return ChatCompletionService(
        config=config,
        metrics_tracker=metrics_tracker,
        model_registry=model_registry,
        kv_cache_router=kv_cache_router,
        kv_cache_metrics=kv_cache_metrics,
        dynamo_metrics=dynamo_metrics,
        usage_tracker=None,  # Optional
    )


# Basic Completion Tests


@pytest.mark.asyncio
async def test_basic_completion(chat_service):
    """Test basic non-streaming completion."""
    request = ChatCompletionRequest(
        model="gpt-3.5-turbo",
        messages=[
            Message(role=Role.USER, content="Hello, how are you?"),
        ],
    )

    response = await chat_service.create_chat_completion(request)

    assert response.id.startswith("chatcmpl-")
    assert response.model == "gpt-3.5-turbo"
    assert len(response.choices) == 1
    assert response.choices[0].message.role == Role.ASSISTANT
    assert response.choices[0].message.content is not None
    assert len(response.choices[0].message.content) > 0
    assert response.choices[0].finish_reason in ["stop", "length"]
    assert response.usage.prompt_tokens > 0
    assert response.usage.completion_tokens > 0
    assert response.usage.total_tokens > 0


@pytest.mark.asyncio
async def test_basic_streaming(chat_service):
    """Test basic streaming completion."""
    request = ChatCompletionRequest(
        model="gpt-3.5-turbo",
        messages=[
            Message(role=Role.USER, content="Count to 5."),
        ],
        stream=True,
    )

    chunks = []
    async for chunk in chat_service.create_chat_completion_stream(request):
        chunks.append(chunk)

    # Should have first chunk (role), content chunks, and final chunk
    assert len(chunks) > 2

    # First chunk has role
    assert chunks[0].choices[0].delta.role == Role.ASSISTANT

    # Last chunk has finish_reason
    assert chunks[-1].choices[0].finish_reason == "stop"

    # Reconstruct content from deltas
    content = "".join(
        chunk.choices[0].delta.content or ""
        for chunk in chunks
        if chunk.choices[0].delta.content
    )
    assert len(content) > 0


@pytest.mark.asyncio
async def test_multiple_choices(chat_service):
    """Test generating multiple completions (n > 1)."""
    request = ChatCompletionRequest(
        model="gpt-3.5-turbo",
        messages=[
            Message(role=Role.USER, content="Hello!"),
        ],
        n=3,
    )

    response = await chat_service.create_chat_completion(request)

    assert len(response.choices) == 3
    for i, choice in enumerate(response.choices):
        assert choice.index == i
        assert choice.message.content is not None


@pytest.mark.asyncio
async def test_reasoning_model(chat_service):
    """Test reasoning model (GPT-OSS)."""
    request = ChatCompletionRequest(
        model="gpt-oss-120b",
        messages=[
            Message(role=Role.USER, content="Solve this math problem: 2 + 2 = ?"),
        ],
    )

    response = await chat_service.create_chat_completion(request)

    # Should have reasoning content
    assert response.choices[0].message.reasoning_content is not None
    assert len(response.choices[0].message.reasoning_content) > 0

    # Should have reasoning tokens in usage
    assert response.usage.completion_tokens_details is not None
    assert response.usage.completion_tokens_details.reasoning_tokens > 0


@pytest.mark.asyncio
async def test_streaming_with_usage(chat_service):
    """Test streaming with usage information."""
    request = ChatCompletionRequest(
        model="gpt-3.5-turbo",
        messages=[
            Message(role=Role.USER, content="Hello!"),
        ],
        stream=True,
        stream_options=StreamOptions(include_usage=True),
    )

    chunks = []
    async for chunk in chat_service.create_chat_completion_stream(request):
        chunks.append(chunk)

    # Last chunk should have usage
    assert chunks[-1].usage is not None
    assert chunks[-1].usage.prompt_tokens > 0
    assert chunks[-1].usage.completion_tokens > 0


@pytest.mark.asyncio
async def test_max_tokens_limit(chat_service):
    """Test that max_tokens is respected."""
    request = ChatCompletionRequest(
        model="gpt-3.5-turbo",
        messages=[
            Message(role=Role.USER, content="Write a very long story."),
        ],
        max_tokens=10,
    )

    response = await chat_service.create_chat_completion(request)

    # Should respect max_tokens (with some tolerance)
    assert response.usage.completion_tokens <= 15
    assert response.choices[0].finish_reason == "length"


@pytest.mark.asyncio
async def test_seed_determinism(chat_service):
    """Test that seed produces deterministic results."""
    request = ChatCompletionRequest(
        model="gpt-3.5-turbo",
        messages=[
            Message(role=Role.USER, content="Generate a random number."),
        ],
        seed=42,
        temperature=0.7,
    )

    # Generate twice with same seed
    response1 = await chat_service.create_chat_completion(request)
    response2 = await chat_service.create_chat_completion(request)

    # Should have deterministic fingerprints
    assert response1.system_fingerprint == response2.system_fingerprint
    assert response1.system_fingerprint.startswith("fp_")


@pytest.mark.asyncio
async def test_conversation_context(chat_service):
    """Test multi-turn conversation."""
    messages = [
        Message(role=Role.SYSTEM, content="You are a helpful assistant."),
        Message(role=Role.USER, content="My name is Alice."),
        Message(role=Role.ASSISTANT, content="Hello Alice! Nice to meet you."),
        Message(role=Role.USER, content="What's my name?"),
    ]

    request = ChatCompletionRequest(
        model="gpt-3.5-turbo",
        messages=messages,
    )

    response = await chat_service.create_chat_completion(request)

    # Should generate response based on context
    assert response.choices[0].message.content is not None
    assert len(response.choices[0].message.content) > 0
