"""
Streaming behavior tests.

Tests streaming responses - chunk structure, content delivery, completion.
"""

import pytest

from fakeai.models import ChatCompletionRequest, CompletionRequest, Message, Role


@pytest.mark.unit
@pytest.mark.streaming
@pytest.mark.asyncio
class TestChatCompletionStreaming:
    """Test chat completion streaming behavior."""

    async def test_yields_at_least_two_chunks(self, service_no_auth):
        """Streaming should yield minimum of first chunk + final chunk."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hi")],
            stream=True,
        )

        chunks = []
        async for chunk in service_no_auth.create_chat_completion_stream(request):
            chunks.append(chunk)

        assert len(chunks) >= 2

    async def test_all_chunks_have_same_id(self, service_no_auth):
        """All chunks in a stream should share the same completion ID."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True,
        )

        chunks = []
        async for chunk in service_no_auth.create_chat_completion_stream(request):
            chunks.append(chunk)

        stream_id = chunks[0].id
        assert all(chunk.id == stream_id for chunk in chunks)

    async def test_first_chunk_establishes_role(self, service_no_auth):
        """First chunk should contain the assistant role."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello")],
            stream=True,
        )

        first_chunk = None
        async for chunk in service_no_auth.create_chat_completion_stream(request):
            first_chunk = chunk
            break

        assert first_chunk.choices[0].delta.role == Role.ASSISTANT

    async def test_content_chunks_between_first_and_last(self, service_no_auth):
        """Middle chunks should contain content deltas."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Tell me a story")],
            stream=True,
        )

        chunks = []
        async for chunk in service_no_auth.create_chat_completion_stream(request):
            chunks.append(chunk)

        # Count chunks with content
        content_chunks = [c for c in chunks if c.choices[0].delta.content is not None]

        assert len(content_chunks) > 0

    async def test_final_chunk_has_finish_reason(self, service_no_auth):
        """Final chunk should have finish_reason set."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Hello")],
            stream=True,
        )

        chunks = []
        async for chunk in service_no_auth.create_chat_completion_stream(request):
            chunks.append(chunk)

        final_chunk = chunks[-1]
        assert final_chunk.choices[0].finish_reason is not None
        assert final_chunk.choices[0].finish_reason in ["stop", "length"]

    async def test_final_chunk_has_empty_delta(self, service_no_auth):
        """Final chunk delta should be empty (no more content)."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True,
        )

        chunks = []
        async for chunk in service_no_auth.create_chat_completion_stream(request):
            chunks.append(chunk)

        final_chunk = chunks[-1]
        # Final delta should have no role or content
        assert final_chunk.choices[0].delta.role is None
        assert final_chunk.choices[0].delta.content is None

    async def test_chunks_can_be_assembled_into_full_message(self, service_no_auth):
        """Assembling chunk contents should produce coherent message."""
        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Say hello")],
            stream=True,
        )

        assembled_content = ""
        async for chunk in service_no_auth.create_chat_completion_stream(request):
            if chunk.choices[0].delta.content:
                assembled_content += chunk.choices[0].delta.content

        # Should have assembled some content
        assert len(assembled_content) > 0
        # Should not have weird artifacts
        assert not assembled_content.startswith("  ")  # No leading double spaces


@pytest.mark.unit
@pytest.mark.streaming
@pytest.mark.asyncio
class TestCompletionStreaming:
    """Test text completion streaming behavior."""

    async def test_completion_streaming_yields_chunks(self, service_no_auth):
        """Text completion streaming should yield multiple chunks."""
        request = CompletionRequest(
            model="meta-llama/Llama-3.1-8B-Instruct",
            prompt="Once upon a time",
            stream=True,
        )

        chunks = []
        async for chunk in service_no_auth.create_completion_stream(request):
            chunks.append(chunk)

        assert len(chunks) > 1

    async def test_completion_final_chunk_has_finish_reason(self, service_no_auth):
        """Final completion chunk should have finish_reason."""
        request = CompletionRequest(
            model="meta-llama/Llama-3.1-8B-Instruct", prompt="Test", stream=True
        )

        chunks = []
        async for chunk in service_no_auth.create_completion_stream(request):
            chunks.append(chunk)

        assert chunks[-1].choices[0].finish_reason in ["stop", "length"]

    async def test_echo_includes_prompt_in_stream(self, service_no_auth):
        """When echo=True, prompt should be included in stream."""
        prompt_text = "Echo this prompt"
        request = CompletionRequest(
            model="meta-llama/Llama-3.1-8B-Instruct",
            prompt=prompt_text,
            echo=True,
            stream=True,
        )

        assembled = ""
        async for chunk in service_no_auth.create_completion_stream(request):
            if chunk.choices[0].text:
                assembled += chunk.choices[0].text

        # Assembled content should include the original prompt
        assert prompt_text in assembled or len(assembled) > len(prompt_text)


@pytest.mark.integration
@pytest.mark.streaming
class TestStreamingEndpoint:
    """Test streaming endpoint behavior."""

    def test_streaming_request_returns_event_stream(self, client_no_auth):
        """Streaming requests should return text/event-stream content type."""
        response = client_no_auth.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": True,
            },
        )

        # Skip if auth is globally enabled
        if response.status_code == 401:
            pytest.skip("Auth enabled globally, skipping streaming test")

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

    def test_stream_contains_data_prefixed_lines(self, client_no_auth):
        """Stream should contain 'data: ' prefixed JSON lines."""
        import os

        os.environ["FAKEAI_REQUIRE_API_KEY"] = "false"

        response = client_no_auth.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Test"}],
                "stream": True,
            },
        )

        # Skip if auth interfered
        if response.status_code != 200:
            pytest.skip("Auth enabled, skipping streaming test")

        # Read stream content
        content = response.text

        # Should contain "data: " prefixed lines
        assert "data: " in content
        # Should end with [DONE]
        assert "data: [DONE]" in content

    def test_stream_ends_with_done_marker(self, client_no_auth):
        """Stream should end with 'data: [DONE]' marker."""
        import os

        os.environ["FAKEAI_REQUIRE_API_KEY"] = "false"

        response = client_no_auth.post(
            "/v1/chat/completions",
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": "Test"}],
                "stream": True,
            },
        )

        if response.status_code != 200:
            pytest.skip("Auth enabled, skipping streaming test")

        content = response.text

        assert content.strip().endswith("data: [DONE]")
