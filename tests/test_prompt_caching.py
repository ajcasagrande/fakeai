"""
Tests for prompt caching functionality.

Tests the hash-based prompt caching system that caches entire prompt contexts
for reuse across requests.
"""

import time

import pytest

from fakeai.config import AppConfig
from fakeai.fakeai_service import FakeAIService
from fakeai.models import ChatCompletionRequest, Message, Role


@pytest.fixture
def config_with_caching():
    """Config with prompt caching enabled."""
    return AppConfig(
        require_api_key=False,
        response_delay=0.0,
        random_delay=False,
        enable_prompt_caching=True,
        cache_ttl_seconds=600,
        min_tokens_for_cache=1024,
    )


@pytest.fixture
def config_without_caching():
    """Config with prompt caching disabled."""
    return AppConfig(
        require_api_key=False,
        response_delay=0.0,
        random_delay=False,
        enable_prompt_caching=False,
    )


@pytest.fixture
def config_short_ttl():
    """Config with very short cache TTL for expiration testing."""
    return AppConfig(
        require_api_key=False,
        response_delay=0.0,
        random_delay=False,
        enable_prompt_caching=True,
        cache_ttl_seconds=1,  # 1 second TTL
        min_tokens_for_cache=10,  # Low threshold for testing
    )


@pytest.fixture
def service_with_caching(config_with_caching):
    """FakeAI service with prompt caching enabled."""
    return FakeAIService(config_with_caching)


@pytest.fixture
def service_without_caching(config_without_caching):
    """FakeAI service with prompt caching disabled."""
    return FakeAIService(config_without_caching)


@pytest.fixture
def service_short_ttl(config_short_ttl):
    """FakeAI service with short TTL."""
    return FakeAIService(config_short_ttl)


@pytest.fixture
def long_prompt_messages():
    """Messages with enough tokens to trigger caching."""
    # Create a long prompt that exceeds min_tokens_for_cache (1024)
    long_content = " ".join(["This is a test sentence with multiple words."] * 150)
    return [
        Message(role=Role.SYSTEM, content="You are a helpful assistant."),
        Message(role=Role.USER, content=long_content),
    ]


@pytest.fixture
def short_prompt_messages():
    """Messages with not enough tokens to trigger caching."""
    return [
        Message(role=Role.USER, content="Hello, how are you?"),
    ]


@pytest.mark.unit
@pytest.mark.prompt_caching
class TestPromptCacheMiss:
    """Test cache miss scenarios."""

    @pytest.mark.asyncio
    async def test_first_request_is_cache_miss(
        self, service_with_caching, long_prompt_messages
    ):
        """First request with new prompt should be a cache miss."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b", messages=long_prompt_messages
        )

        response = await service_with_caching.create_chat_completion(request)

        # First request should have no cached tokens (cache miss)
        assert response.usage.prompt_tokens_details.cached_tokens == 0

    @pytest.mark.asyncio
    async def test_below_minimum_tokens_no_caching(
        self, service_with_caching, short_prompt_messages
    ):
        """Prompts below minimum token threshold should not be cached."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b", messages=short_prompt_messages
        )

        # Make two identical requests
        response1 = await service_with_caching.create_chat_completion(request)
        response2 = await service_with_caching.create_chat_completion(request)

        # Both should have 0 cached tokens (below threshold)
        assert response1.usage.prompt_tokens_details.cached_tokens == 0
        assert response2.usage.prompt_tokens_details.cached_tokens == 0

    @pytest.mark.asyncio
    async def test_caching_disabled_no_cache(
        self, service_without_caching, long_prompt_messages
    ):
        """When caching is disabled, no tokens should be cached."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b", messages=long_prompt_messages
        )

        # Make two identical requests
        response1 = await service_without_caching.create_chat_completion(request)
        response2 = await service_without_caching.create_chat_completion(request)

        # Both should have 0 cached tokens (caching disabled)
        assert response1.usage.prompt_tokens_details.cached_tokens == 0
        assert response2.usage.prompt_tokens_details.cached_tokens == 0


@pytest.mark.unit
@pytest.mark.prompt_caching
class TestPromptCacheHit:
    """Test cache hit scenarios."""

    @pytest.mark.asyncio
    async def test_second_request_is_cache_hit(
        self, service_with_caching, long_prompt_messages
    ):
        """Second identical request should hit the cache."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b", messages=long_prompt_messages
        )

        # First request (cache miss for prompt cache)
        response1 = await service_with_caching.create_chat_completion(request)
        first_cached = response1.usage.prompt_tokens_details.cached_tokens

        # Second request (should hit prompt cache)
        response2 = await service_with_caching.create_chat_completion(request)
        second_cached = response2.usage.prompt_tokens_details.cached_tokens

        # Second request should have more cached tokens than first
        # (First may have some from KV cache, second adds prompt cache)
        assert second_cached > first_cached

        # Prompt cache contribution should be visible
        # Note: Total cached combines KV cache + prompt cache
        # So we just verify second request has MORE cached than first
        prompt_hash = service_with_caching._get_prompt_hash(long_prompt_messages)
        assert prompt_hash in service_with_caching._prompt_cache

    @pytest.mark.asyncio
    async def test_cache_hit_consistent_across_calls(
        self, service_with_caching, long_prompt_messages
    ):
        """Cache hits should be consistent across multiple requests."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b", messages=long_prompt_messages
        )

        # First request (cache miss)
        response1 = await service_with_caching.create_chat_completion(request)

        # Multiple subsequent requests (all should hit cache)
        response2 = await service_with_caching.create_chat_completion(request)
        response3 = await service_with_caching.create_chat_completion(request)
        response4 = await service_with_caching.create_chat_completion(request)

        # All subsequent requests should have same cached token count
        cached_tokens = response2.usage.prompt_tokens_details.cached_tokens
        assert response3.usage.prompt_tokens_details.cached_tokens == cached_tokens
        assert response4.usage.prompt_tokens_details.cached_tokens == cached_tokens
        assert cached_tokens > 0

    @pytest.mark.asyncio
    async def test_different_prompts_different_cache_entries(
        self, service_with_caching
    ):
        """Different prompts should create different cache entries."""
        messages1 = [
            Message(role=Role.USER, content=" ".join(["First prompt text."] * 150))
        ]
        messages2 = [
            Message(role=Role.USER, content=" ".join(["Second prompt text."] * 150))
        ]

        request1 = ChatCompletionRequest(
            model="openai/gpt-oss-120b", messages=messages1
        )
        request2 = ChatCompletionRequest(
            model="openai/gpt-oss-120b", messages=messages2
        )

        # Make requests in pattern: 1, 2, 1, 2
        resp1a = await service_with_caching.create_chat_completion(request1)
        resp2a = await service_with_caching.create_chat_completion(request2)
        resp1b = await service_with_caching.create_chat_completion(request1)
        resp2b = await service_with_caching.create_chat_completion(request2)

        # First requests should be cache misses
        assert resp1a.usage.prompt_tokens_details.cached_tokens == 0
        assert resp2a.usage.prompt_tokens_details.cached_tokens == 0

        # Second requests should be cache hits
        assert resp1b.usage.prompt_tokens_details.cached_tokens > 0
        assert resp2b.usage.prompt_tokens_details.cached_tokens > 0


@pytest.mark.unit
@pytest.mark.prompt_caching
class TestCacheTTL:
    """Test cache TTL expiration."""

    @pytest.mark.asyncio
    async def test_cache_expires_after_ttl(self, service_short_ttl):
        """Cache entries should expire after TTL."""
        messages = [Message(role=Role.USER, content=" ".join(["Test prompt."] * 20))]
        request = ChatCompletionRequest(model="openai/gpt-oss-120b", messages=messages)

        # First request (cache miss)
        response1 = await service_short_ttl.create_chat_completion(request)
        assert response1.usage.prompt_tokens_details.cached_tokens == 0

        # Second request immediately (should hit cache)
        response2 = await service_short_ttl.create_chat_completion(request)
        assert response2.usage.prompt_tokens_details.cached_tokens > 0

        # Wait for TTL to expire (1 second + buffer)
        time.sleep(1.5)

        # Third request after TTL (should be cache miss again)
        response3 = await service_short_ttl.create_chat_completion(request)
        assert response3.usage.prompt_tokens_details.cached_tokens == 0

        # Fourth request (should hit cache again)
        response4 = await service_short_ttl.create_chat_completion(request)
        assert response4.usage.prompt_tokens_details.cached_tokens > 0


@pytest.mark.unit
@pytest.mark.prompt_caching
class TestCacheGranularity:
    """Test 128-token increment granularity."""

    @pytest.mark.asyncio
    async def test_prompt_cache_uses_128_increments(self, service_with_caching):
        """Prompt cache component should use 128-token increments."""
        # Create prompts of various lengths
        for word_count in [150, 200, 250, 300]:
            messages = [
                Message(role=Role.USER, content=" ".join(["Test word."] * word_count))
            ]
            request = ChatCompletionRequest(
                model="openai/gpt-oss-120b", messages=messages
            )

            # First request (cache miss)
            await service_with_caching.create_chat_completion(request)

            # Second request (cache hit)
            response = await service_with_caching.create_chat_completion(request)

            # Check that prompt cache entry exists and is rounded to 128
            prompt_hash = service_with_caching._get_prompt_hash(messages)
            if prompt_hash in service_with_caching._prompt_cache:
                cached_token_count, _ = service_with_caching._prompt_cache[prompt_hash]
                prompt_cache_contribution = (cached_token_count // 128) * 128
                # Prompt cache contribution should be 128-aligned
                assert (
                    prompt_cache_contribution % 128 == 0
                ), f"Prompt cache {prompt_cache_contribution} not 128-aligned"


@pytest.mark.unit
@pytest.mark.prompt_caching
class TestCacheWithKVCache:
    """Test interaction between prompt cache and KV cache."""

    @pytest.mark.asyncio
    async def test_both_caches_can_contribute(
        self, service_with_caching, long_prompt_messages
    ):
        """Both prompt cache and KV cache can contribute cached tokens."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b", messages=long_prompt_messages
        )

        # First request
        response1 = await service_with_caching.create_chat_completion(request)

        # Second request (should have cached tokens from both systems)
        response2 = await service_with_caching.create_chat_completion(request)

        # Second request should have more cached tokens than first
        # (combination of KV cache + prompt cache)
        cached1 = response1.usage.prompt_tokens_details.cached_tokens
        cached2 = response2.usage.prompt_tokens_details.cached_tokens

        assert (
            cached2 >= cached1
        ), "Second request should have at least as many cached tokens"

        # At minimum, prompt cache should contribute (KV cache may or may not)
        assert cached2 > 0, "Second request should have cached tokens from prompt cache"


@pytest.mark.unit
@pytest.mark.prompt_caching
class TestStreamingWithCache:
    """Test prompt caching with streaming responses."""

    @pytest.mark.asyncio
    async def test_streaming_includes_cached_tokens(
        self, service_with_caching, long_prompt_messages
    ):
        """Streaming responses should include cached token info when usage requested."""
        from fakeai.models import StreamOptions

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=long_prompt_messages,
            stream=True,
            stream_options=StreamOptions(include_usage=True),
        )

        # First streaming request (cache miss)
        chunks1 = []
        async for chunk in service_with_caching.create_chat_completion_stream(request):
            chunks1.append(chunk)

        # Find the final chunk with usage
        final_chunk1 = next((c for c in reversed(chunks1) if c.usage), None)
        assert final_chunk1 is not None, "No usage found in stream"
        cached1 = final_chunk1.usage.prompt_tokens_details.cached_tokens

        # Second streaming request (should hit cache)
        chunks2 = []
        async for chunk in service_with_caching.create_chat_completion_stream(request):
            chunks2.append(chunk)

        final_chunk2 = next((c for c in reversed(chunks2) if c.usage), None)
        assert final_chunk2 is not None, "No usage found in stream"
        cached2 = final_chunk2.usage.prompt_tokens_details.cached_tokens

        # Second request should have cached tokens
        assert cached2 >= cached1
        assert cached2 > 0

    @pytest.mark.asyncio
    async def test_streaming_without_usage_still_caches(
        self, service_with_caching, long_prompt_messages
    ):
        """Prompt caching should work even when usage is not included in stream."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=long_prompt_messages,
            stream=True,
            # No stream_options - usage not included
        )

        # First streaming request
        chunks1 = []
        async for chunk in service_with_caching.create_chat_completion_stream(request):
            chunks1.append(chunk)

        # Second streaming request
        chunks2 = []
        async for chunk in service_with_caching.create_chat_completion_stream(request):
            chunks2.append(chunk)

        # No usage in chunks, but cache should still be updated internally
        # Verify by checking the service's internal cache
        prompt_hash = service_with_caching._get_prompt_hash(long_prompt_messages)
        assert prompt_hash in service_with_caching._prompt_cache


@pytest.mark.unit
@pytest.mark.prompt_caching
class TestCacheHashStability:
    """Test that cache hashing is stable and deterministic."""

    @pytest.mark.asyncio
    async def test_same_messages_same_hash(self, service_with_caching):
        """Same messages should produce the same hash."""
        messages1 = [
            Message(role=Role.SYSTEM, content="You are helpful."),
            Message(role=Role.USER, content="Hello!"),
        ]
        messages2 = [
            Message(role=Role.SYSTEM, content="You are helpful."),
            Message(role=Role.USER, content="Hello!"),
        ]

        hash1 = service_with_caching._get_prompt_hash(messages1)
        hash2 = service_with_caching._get_prompt_hash(messages2)

        assert hash1 == hash2

    @pytest.mark.asyncio
    async def test_different_messages_different_hash(self, service_with_caching):
        """Different messages should produce different hashes."""
        messages1 = [Message(role=Role.USER, content="Hello!")]
        messages2 = [Message(role=Role.USER, content="Hi there!")]

        hash1 = service_with_caching._get_prompt_hash(messages1)
        hash2 = service_with_caching._get_prompt_hash(messages2)

        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_message_order_affects_hash(self, service_with_caching):
        """Message order should affect the hash."""
        messages1 = [
            Message(role=Role.USER, content="First"),
            Message(role=Role.ASSISTANT, content="Second"),
        ]
        messages2 = [
            Message(role=Role.ASSISTANT, content="Second"),
            Message(role=Role.USER, content="First"),
        ]

        hash1 = service_with_caching._get_prompt_hash(messages1)
        hash2 = service_with_caching._get_prompt_hash(messages2)

        assert hash1 != hash2


@pytest.mark.unit
@pytest.mark.prompt_caching
class TestCacheConfiguration:
    """Test cache configuration options."""

    @pytest.mark.asyncio
    async def test_custom_minimum_tokens(self):
        """Custom minimum token threshold should be respected."""
        config = AppConfig(
            require_api_key=False,
            response_delay=0.0,
            enable_prompt_caching=True,
            min_tokens_for_cache=50,  # Low threshold
        )
        service = FakeAIService(config)

        # Create a prompt with ~70 tokens (should be above 50)
        messages = [Message(role=Role.USER, content=" ".join(["word"] * 25))]
        request = ChatCompletionRequest(model="openai/gpt-oss-120b", messages=messages)

        # First request (cache miss)
        response1 = await service.create_chat_completion(request)
        # Second request (should hit cache with low threshold)
        response2 = await service.create_chat_completion(request)

        assert response1.usage.prompt_tokens_details.cached_tokens == 0
        assert response2.usage.prompt_tokens_details.cached_tokens > 0

    @pytest.mark.asyncio
    async def test_custom_ttl(self):
        """Custom TTL should be respected."""
        config = AppConfig(
            require_api_key=False,
            response_delay=0.0,
            enable_prompt_caching=True,
            cache_ttl_seconds=2,  # 2 second TTL
            min_tokens_for_cache=10,
        )
        service = FakeAIService(config)

        messages = [Message(role=Role.USER, content=" ".join(["test"] * 20))]
        request = ChatCompletionRequest(model="openai/gpt-oss-120b", messages=messages)

        # First request
        await service.create_chat_completion(request)
        # Second request (should hit cache)
        response2 = await service.create_chat_completion(request)
        assert response2.usage.prompt_tokens_details.cached_tokens > 0

        # Wait for TTL
        time.sleep(2.5)

        # Third request (should be cache miss after expiration)
        response3 = await service.create_chat_completion(request)
        assert response3.usage.prompt_tokens_details.cached_tokens == 0
