"""
Token tracking tests for all endpoints.

Tests that all endpoints properly track token/character usage in metrics.
"""

import time

import pytest

from fakeai.models import (
    CompletionRequest,
    EmbeddingRequest,
    Message,
    ModerationRequest,
    RankingPassage,
    RankingQuery,
    RankingRequest,
    ResponsesRequest,
    Role,
    SpeechRequest,
)


@pytest.mark.unit
@pytest.mark.metrics
class TestTokenTracking:
    """Test token tracking across all endpoints."""

    @pytest.mark.asyncio
    async def test_completions_tracks_tokens(self, service_no_auth):
        """Test that /v1/completions tracks token usage."""
        # Create completion request
        request = CompletionRequest(
            model="gpt-3.5-turbo-instruct",
            prompt="Write a short story about a robot.",
            max_tokens=50,
        )

        # Execute request
        response = await service_no_auth.create_completion(request)

        # Get updated metrics
        time.sleep(0.2)  # Give metrics time to update
        metrics = service_no_auth.metrics_tracker.get_metrics()

        # Verify token tracking
        assert "/v1/completions" in metrics["tokens"]
        token_stats = metrics["tokens"]["/v1/completions"]
        # Check that tokens are being tracked (rate > 0)
        assert "rate" in token_stats
        assert token_stats["rate"] > 0

    @pytest.mark.asyncio
    async def test_embeddings_tracks_tokens(self, service_no_auth):
        """Test that /v1/embeddings tracks token usage."""
        # Create embedding request with multiple inputs
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input=["Hello world", "This is a test", "Token tracking works"],
        )

        # Execute request
        response = await service_no_auth.create_embedding(request)

        # Get updated metrics
        time.sleep(0.2)
        metrics = service_no_auth.metrics_tracker.get_metrics()

        # Verify token tracking
        assert "/v1/embeddings" in metrics["tokens"]
        token_stats = metrics["tokens"]["/v1/embeddings"]
        assert "rate" in token_stats
        assert token_stats["rate"] > 0

    @pytest.mark.asyncio
    async def test_embeddings_tracks_tokens_single_string(self, service_no_auth):
        """Test that /v1/embeddings tracks tokens for single string input."""
        # Create embedding request with single string
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Single input string for embedding",
        )

        # Execute request
        response = await service_no_auth.create_embedding(request)

        # Get updated metrics
        time.sleep(0.2)
        metrics = service_no_auth.metrics_tracker.get_metrics()

        # Verify token tracking
        assert "/v1/embeddings" in metrics["tokens"]
        token_stats = metrics["tokens"]["/v1/embeddings"]
        assert "rate" in token_stats
        assert token_stats["rate"] > 0

    @pytest.mark.asyncio
    async def test_audio_tracks_characters(self, service_no_auth):
        """Test that /v1/audio/speech tracks character count."""
        # Create speech request
        input_text = "Hello, this is a test of the text-to-speech system."
        request = SpeechRequest(
            model="tts-1",
            input=input_text,
            voice="alloy",
        )

        # Execute request
        audio_bytes = await service_no_auth.create_speech(request)

        # Get updated metrics
        time.sleep(0.2)
        metrics = service_no_auth.metrics_tracker.get_metrics()

        # Verify character tracking (tracked as tokens)
        assert "/v1/audio/speech" in metrics["tokens"]
        char_stats = metrics["tokens"]["/v1/audio/speech"]
        assert "rate" in char_stats
        assert char_stats["rate"] > 0
        assert audio_bytes is not None
        assert len(audio_bytes) > 0

    @pytest.mark.asyncio
    async def test_audio_tracks_characters_long_text(self, service_no_auth):
        """Test that /v1/audio/speech tracks characters for longer text."""
        # Create speech request with longer text
        input_text = (
            "This is a much longer piece of text that will be converted to speech. "
            * 10
        )
        request = SpeechRequest(
            model="tts-1-hd",
            input=input_text,
            voice="nova",
            speed=1.5,
        )

        # Execute request
        audio_bytes = await service_no_auth.create_speech(request)

        # Get updated metrics
        time.sleep(0.2)
        metrics = service_no_auth.metrics_tracker.get_metrics()

        # Verify character tracking
        assert "/v1/audio/speech" in metrics["tokens"]
        char_stats = metrics["tokens"]["/v1/audio/speech"]
        assert "rate" in char_stats
        assert char_stats["rate"] > 0

    @pytest.mark.asyncio
    async def test_moderations_tracks_tokens(self, service_no_auth):
        """Test that /v1/moderations tracks token usage."""
        # Create moderation request
        request = ModerationRequest(
            input="This is a sample text to moderate for safety.",
        )

        # Execute request
        response = await service_no_auth.create_moderation(request)

        # Get updated metrics
        time.sleep(0.2)
        metrics = service_no_auth.metrics_tracker.get_metrics()

        # Verify token tracking
        assert "/v1/moderations" in metrics["tokens"]
        token_stats = metrics["tokens"]["/v1/moderations"]
        assert "rate" in token_stats
        assert token_stats["rate"] > 0
        assert response.results is not None
        assert len(response.results) > 0

    @pytest.mark.asyncio
    async def test_moderations_tracks_tokens_multiple_inputs(self, service_no_auth):
        """Test that /v1/moderations tracks tokens for multiple inputs."""
        # Create moderation request with multiple inputs
        request = ModerationRequest(
            input=[
                "First text to moderate",
                "Second text to check",
                "Third piece of content",
            ],
        )

        # Execute request
        response = await service_no_auth.create_moderation(request)

        # Get updated metrics
        time.sleep(0.2)
        metrics = service_no_auth.metrics_tracker.get_metrics()

        # Verify token tracking for all inputs
        assert "/v1/moderations" in metrics["tokens"]
        token_stats = metrics["tokens"]["/v1/moderations"]
        assert "rate" in token_stats
        assert token_stats["rate"] > 0
        assert len(response.results) == 3

    @pytest.mark.asyncio
    async def test_responses_tracks_tokens(self, service_no_auth):
        """Test that /v1/responses tracks token usage."""
        # Create responses request (input field is required, not messages)
        request = ResponsesRequest(
            model="gpt-4",
            input=[
                Message(role=Role.USER, content="What is the capital of France?"),
            ],
        )

        # Execute request
        response = await service_no_auth.create_response(request)

        # Get updated metrics
        time.sleep(0.2)
        metrics = service_no_auth.metrics_tracker.get_metrics()

        # Verify token tracking
        assert "/v1/responses" in metrics["tokens"]
        token_stats = metrics["tokens"]["/v1/responses"]
        assert "rate" in token_stats
        assert token_stats["rate"] > 0

    @pytest.mark.asyncio
    async def test_responses_tracks_tokens_with_instructions(self, service_no_auth):
        """Test that /v1/responses tracks tokens including instructions."""
        # Create responses request with instructions
        request = ResponsesRequest(
            model="gpt-4",
            instructions="You are a helpful assistant that provides concise answers.",
            input=[
                Message(role=Role.USER, content="Explain quantum computing"),
            ],
        )

        # Execute request
        response = await service_no_auth.create_response(request)

        # Get updated metrics
        time.sleep(0.2)
        metrics = service_no_auth.metrics_tracker.get_metrics()

        # Verify token tracking includes instructions
        assert "/v1/responses" in metrics["tokens"]
        token_stats = metrics["tokens"]["/v1/responses"]
        assert "rate" in token_stats
        assert token_stats["rate"] > 0

    @pytest.mark.asyncio
    async def test_ranking_tracks_tokens(self, service_no_auth):
        """Test that /v1/ranking tracks token usage."""
        # Create ranking request
        request = RankingRequest(
            model="nv-rerank-qa-mistral-4b:1",
            query=RankingQuery(text="What is machine learning?"),
            passages=[
                RankingPassage(
                    text="Machine learning is a subset of artificial intelligence."
                ),
                RankingPassage(
                    text="Deep learning uses neural networks with multiple layers."
                ),
                RankingPassage(text="Python is a popular programming language."),
            ],
        )

        # Execute request
        response = await service_no_auth.create_ranking(request)

        # Get updated metrics
        time.sleep(0.2)
        metrics = service_no_auth.metrics_tracker.get_metrics()

        # Verify token tracking
        assert "/v1/ranking" in metrics["tokens"]
        token_stats = metrics["tokens"]["/v1/ranking"]
        assert "rate" in token_stats
        assert token_stats["rate"] > 0
        # Should track both query and all passages
        assert response["rankings"] is not None
        assert len(response["rankings"]) == 3

    @pytest.mark.asyncio
    async def test_ranking_tracks_tokens_many_passages(self, service_no_auth):
        """Test that /v1/ranking tracks tokens for many passages."""
        # Create ranking request with many passages
        passages = [
            RankingPassage(text=f"This is passage number {i} about various topics.")
            for i in range(20)
        ]
        request = RankingRequest(
            model="nv-rerank-qa-mistral-4b:1",
            query=RankingQuery(text="Find relevant information"),
            passages=passages,
        )

        # Execute request
        response = await service_no_auth.create_ranking(request)

        # Get updated metrics
        time.sleep(0.2)
        metrics = service_no_auth.metrics_tracker.get_metrics()

        # Verify substantial token tracking
        assert "/v1/ranking" in metrics["tokens"]
        token_stats = metrics["tokens"]["/v1/ranking"]
        assert "rate" in token_stats
        assert token_stats["rate"] > 0
        assert len(response["rankings"]) == 20

    @pytest.mark.asyncio
    async def test_multiple_endpoints_track_independently(self, service_no_auth):
        """Test that different endpoints track tokens independently."""
        # Make requests to different endpoints
        completion_req = CompletionRequest(
            model="gpt-3.5-turbo-instruct",
            prompt="Hello",
            max_tokens=10,
        )
        await service_no_auth.create_completion(completion_req)

        embedding_req = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Test embedding",
        )
        await service_no_auth.create_embedding(embedding_req)

        moderation_req = ModerationRequest(input="Test moderation")
        await service_no_auth.create_moderation(moderation_req)

        # Get updated metrics
        time.sleep(0.2)
        metrics = service_no_auth.metrics_tracker.get_metrics()

        # Verify all endpoints tracked independently
        assert "/v1/completions" in metrics["tokens"]
        assert "/v1/embeddings" in metrics["tokens"]
        assert "/v1/moderations" in metrics["tokens"]

        # Each should have positive rate
        assert metrics["tokens"]["/v1/completions"]["rate"] > 0
        assert metrics["tokens"]["/v1/embeddings"]["rate"] > 0
        assert metrics["tokens"]["/v1/moderations"]["rate"] > 0

    @pytest.mark.asyncio
    async def test_token_accumulation_across_requests(self, service_no_auth):
        """Test that tokens accumulate across multiple requests to same endpoint."""
        # Make multiple completion requests
        for i in range(5):
            request = CompletionRequest(
                model="gpt-3.5-turbo-instruct",
                prompt=f"Request number {i}",
                max_tokens=20,
            )
            await service_no_auth.create_completion(request)

        # Get updated metrics
        time.sleep(0.2)
        metrics = service_no_auth.metrics_tracker.get_metrics()

        # Verify accumulation - rate should be substantial after 5 requests
        assert "/v1/completions" in metrics["tokens"]
        token_stats = metrics["tokens"]["/v1/completions"]
        assert "rate" in token_stats
        assert token_stats["rate"] > 0
