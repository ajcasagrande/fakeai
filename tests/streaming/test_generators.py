"""
Tests for streaming generators.
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest

from fakeai.streaming.base import StreamContext, StreamType
from fakeai.streaming.generators.chat_stream import ChatStreamingGenerator
from fakeai.streaming.generators.completion_stream import CompletionStreamingGenerator


# Mock response objects
class MockChatResponse:
    """Mock chat completion response."""

    def __init__(self, content="Hello, world!"):
        self.id = "chatcmpl-test123"
        self.created = 1234567890
        self.model = "gpt-4o"
        self.choices = [MockChatChoice(content)]
        self.usage = MockUsage()


class MockChatChoice:
    """Mock chat choice."""

    def __init__(self, content):
        self.message = MockMessage(content)
        self.finish_reason = "stop"


class MockMessage:
    """Mock message."""

    def __init__(self, content):
        self.role = "assistant"
        self.content = content


class MockCompletionResponse:
    """Mock completion response."""

    def __init__(self, text="Hello, world!"):
        self.id = "cmpl-test123"
        self.created = 1234567890
        self.model = "gpt-3.5-turbo-instruct"
        self.choices = [MockCompletionChoice(text)]
        self.usage = MockUsage()


class MockCompletionChoice:
    """Mock completion choice."""

    def __init__(self, text):
        self.text = text
        self.finish_reason = "stop"


class MockUsage:
    """Mock usage."""

    def __init__(self):
        self.prompt_tokens = 10
        self.completion_tokens = 20
        self.total_tokens = 30


class TestChatStreamingGenerator:
    """Test ChatStreamingGenerator class."""

    @pytest.mark.asyncio
    async def test_generate_chat_chunks(self):
        """Test generating chat completion chunks."""
        generator = ChatStreamingGenerator()
        context = StreamContext(
            stream_id="test-123",
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            chunk_delay_seconds=0.0,
            enable_latency_simulation=False,
        )

        response = MockChatResponse(content="Hello world")
        chunks = []

        async for chunk in generator.generate(context, response):
            chunks.append(chunk)

        assert len(chunks) > 0

        # First chunk should have role
        first_chunk = chunks[0]
        assert first_chunk.is_first is True
        assert "choices" in first_chunk.data
        assert "delta" in first_chunk.data["choices"][0]
        assert first_chunk.data["choices"][0]["delta"].get("role") == "assistant"

        # Last chunk should have finish_reason
        last_chunk = chunks[-1]
        assert last_chunk.is_last is True
        assert last_chunk.data["choices"][0]["delta"].get("finish_reason") == "stop"

    @pytest.mark.asyncio
    async def test_chat_chunks_sequence(self):
        """Test chat chunks have proper sequence numbers."""
        generator = ChatStreamingGenerator()
        context = StreamContext(
            stream_id="test-123",
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            chunk_delay_seconds=0.0,
            enable_latency_simulation=False,
        )

        response = MockChatResponse(content="Test")
        chunks = []

        async for chunk in generator.generate(context, response):
            chunks.append(chunk)

        # Verify sequence numbers are sequential
        for i, chunk in enumerate(chunks):
            assert chunk.sequence_number == i

    @pytest.mark.asyncio
    async def test_empty_chat_response(self):
        """Test handling empty chat response."""
        generator = ChatStreamingGenerator()
        context = StreamContext(
            stream_id="test-123",
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            chunk_delay_seconds=0.0,
            enable_latency_simulation=False,
        )

        response = MockChatResponse(content="")
        chunks = []

        async for chunk in generator.generate(context, response):
            chunks.append(chunk)

        # Should still generate at least one chunk with role and finish
        assert len(chunks) >= 1
        assert chunks[0].is_first is True
        assert chunks[0].is_last is True

    @pytest.mark.asyncio
    async def test_chat_chunk_format(self):
        """Test chat chunks have correct OpenAI format."""
        generator = ChatStreamingGenerator()
        context = StreamContext(
            stream_id="test-123",
            stream_type=StreamType.CHAT,
            model="gpt-4o",
            endpoint="/v1/chat/completions",
            chunk_delay_seconds=0.0,
            enable_latency_simulation=False,
        )

        response = MockChatResponse(content="Hi")
        chunks = []

        async for chunk in generator.generate(context, response):
            chunks.append(chunk)

        # Check format of a content chunk
        content_chunk = next(
            (
                c
                for c in chunks
                if c.data["choices"][0]["delta"].get("content")
            ),
            None,
        )

        if content_chunk:
            assert "id" in content_chunk.data
            assert "object" in content_chunk.data
            assert content_chunk.data["object"] == "chat.completion.chunk"
            assert "created" in content_chunk.data
            assert "model" in content_chunk.data


class TestCompletionStreamingGenerator:
    """Test CompletionStreamingGenerator class."""

    @pytest.mark.asyncio
    async def test_generate_completion_chunks(self):
        """Test generating completion chunks."""
        generator = CompletionStreamingGenerator()
        context = StreamContext(
            stream_id="test-123",
            stream_type=StreamType.COMPLETION,
            model="gpt-3.5-turbo-instruct",
            endpoint="/v1/completions",
            chunk_delay_seconds=0.0,
            enable_latency_simulation=False,
        )

        response = MockCompletionResponse(text="Hello world")
        chunks = []

        async for chunk in generator.generate(context, response):
            chunks.append(chunk)

        assert len(chunks) > 0

        # Each chunk should have text
        for chunk in chunks:
            assert "choices" in chunk.data
            assert "text" in chunk.data["choices"][0]

        # Last chunk should have finish_reason
        last_chunk = chunks[-1]
        assert last_chunk.is_last is True
        assert last_chunk.data["choices"][0]["finish_reason"] == "stop"

    @pytest.mark.asyncio
    async def test_completion_chunks_sequence(self):
        """Test completion chunks have proper sequence numbers."""
        generator = CompletionStreamingGenerator()
        context = StreamContext(
            stream_id="test-123",
            stream_type=StreamType.COMPLETION,
            model="gpt-3.5-turbo-instruct",
            endpoint="/v1/completions",
            chunk_delay_seconds=0.0,
            enable_latency_simulation=False,
        )

        response = MockCompletionResponse(text="Test")
        chunks = []

        async for chunk in generator.generate(context, response):
            chunks.append(chunk)

        # Verify sequence numbers are sequential
        for i, chunk in enumerate(chunks):
            assert chunk.sequence_number == i

    @pytest.mark.asyncio
    async def test_empty_completion_response(self):
        """Test handling empty completion response."""
        generator = CompletionStreamingGenerator()
        context = StreamContext(
            stream_id="test-123",
            stream_type=StreamType.COMPLETION,
            model="gpt-3.5-turbo-instruct",
            endpoint="/v1/completions",
            chunk_delay_seconds=0.0,
            enable_latency_simulation=False,
        )

        response = MockCompletionResponse(text="")
        chunks = []

        async for chunk in generator.generate(context, response):
            chunks.append(chunk)

        # Should generate at least one chunk with finish reason
        assert len(chunks) >= 1
        assert chunks[0].is_first is True
        assert chunks[0].is_last is True

    @pytest.mark.asyncio
    async def test_completion_chunk_format(self):
        """Test completion chunks have correct OpenAI format."""
        generator = CompletionStreamingGenerator()
        context = StreamContext(
            stream_id="test-123",
            stream_type=StreamType.COMPLETION,
            model="gpt-3.5-turbo-instruct",
            endpoint="/v1/completions",
            chunk_delay_seconds=0.0,
            enable_latency_simulation=False,
        )

        response = MockCompletionResponse(text="Hi")
        chunks = []

        async for chunk in generator.generate(context, response):
            chunks.append(chunk)

        # Check format
        for chunk in chunks:
            assert "id" in chunk.data
            assert "object" in chunk.data
            assert chunk.data["object"] == "text_completion"
            assert "created" in chunk.data
            assert "model" in chunk.data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
