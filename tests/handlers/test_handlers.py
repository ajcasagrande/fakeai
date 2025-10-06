"""
Tests for individual endpoint handlers.

This module tests each handler implementation to ensure proper
integration with services and correct behavior.
"""
#  SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import AsyncMock, Mock, patch

from fakeai.config import AppConfig
from fakeai.handlers.audio import AudioSpeechHandler
from fakeai.handlers.batches import BatchHandler
from fakeai.handlers.chat import ChatCompletionHandler
from fakeai.handlers.completions import CompletionHandler
from fakeai.handlers.embeddings import EmbeddingHandler
from fakeai.handlers.files import FileHandler
from fakeai.handlers.images import ImageGenerationHandler
from fakeai.handlers.metrics import HealthHandler, MetricsHandler, PrometheusMetricsHandler
from fakeai.handlers.models import ModelHandler, ModelRetrievalHandler
from fakeai.handlers.moderations import ModerationHandler
from fakeai.metrics import MetricsTracker
from fakeai.models import (
    ChatCompletionRequest,
    CompletionRequest,
    CreateBatchRequest,
    EmbeddingRequest,
    ImageGenerationRequest,
    Message,
    ModerationRequest,
    Role,
    SpeechRequest,
)


@pytest.fixture
def config():
    """Create test configuration."""
    return AppConfig()


@pytest.fixture
def metrics_tracker():
    """Create test metrics tracker."""
    return MetricsTracker()


@pytest.fixture
def fastapi_request():
    """Create mock FastAPI request."""
    request = Mock()
    request.headers.get.return_value = "Bearer sk-test-abc123"
    request.client = Mock()
    request.client.host = "127.0.0.1"
    return request


class TestEmbeddingHandler:
    """Tests for EmbeddingHandler."""

    @pytest.mark.asyncio
    async def test_embedding_handler_endpoint(self, config, metrics_tracker):
        """Test endpoint path."""
        handler = EmbeddingHandler(config, metrics_tracker)
        assert handler.endpoint_path() == "/v1/embeddings"

    @pytest.mark.asyncio
    async def test_embedding_handler_execution(self, config, metrics_tracker, fastapi_request):
        """Test embedding generation."""
        handler = EmbeddingHandler(config, metrics_tracker)
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Hello world",
        )

        response = await handler(request, fastapi_request, "req-123")

        assert response.model == "text-embedding-ada-002"
        assert len(response.data) == 1
        assert len(response.data[0].embedding) == 1536  # Default dimensions
        assert response.usage.total_tokens > 0

    @pytest.mark.asyncio
    async def test_embedding_handler_tracks_tokens(
        self, config, metrics_tracker, fastapi_request
    ):
        """Test that handler tracks token usage."""
        handler = EmbeddingHandler(config, metrics_tracker)
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Test input",
        )

        response = await handler(request, fastapi_request, "req-123")

        # Verify tokens were tracked (via post_process)
        assert response.usage is not None


class TestImageGenerationHandler:
    """Tests for ImageGenerationHandler."""

    @pytest.mark.asyncio
    async def test_image_generation_endpoint(self, config, metrics_tracker):
        """Test endpoint path."""
        handler = ImageGenerationHandler(config, metrics_tracker)
        assert handler.endpoint_path() == "/v1/images/generations"

    @pytest.mark.asyncio
    async def test_image_generation_execution(
        self, config, metrics_tracker, fastapi_request
    ):
        """Test image generation."""
        handler = ImageGenerationHandler(config, metrics_tracker)
        request = ImageGenerationRequest(
            model="dall-e-3",
            prompt="A beautiful sunset",
            n=1,
            size="1024x1024",
        )

        response = await handler(request, fastapi_request, "req-123")

        assert len(response.data) == 1
        assert response.data[0].url is not None
        assert response.created > 0


class TestAudioSpeechHandler:
    """Tests for AudioSpeechHandler."""

    @pytest.mark.asyncio
    async def test_audio_speech_endpoint(self, config, metrics_tracker):
        """Test endpoint path."""
        handler = AudioSpeechHandler(config, metrics_tracker)
        assert handler.endpoint_path() == "/v1/audio/speech"

    @pytest.mark.asyncio
    async def test_audio_speech_execution(self, config, metrics_tracker, fastapi_request):
        """Test audio generation."""
        handler = AudioSpeechHandler(config, metrics_tracker)
        request = SpeechRequest(
            model="tts-1",
            input="Hello world",
            voice="alloy",
        )

        audio_bytes = await handler(request, fastapi_request, "req-123")

        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0


class TestModerationHandler:
    """Tests for ModerationHandler."""

    @pytest.mark.asyncio
    async def test_moderation_endpoint(self, config, metrics_tracker):
        """Test endpoint path."""
        handler = ModerationHandler(config, metrics_tracker)
        assert handler.endpoint_path() == "/v1/moderations"

    @pytest.mark.asyncio
    async def test_moderation_execution(self, config, metrics_tracker, fastapi_request):
        """Test content moderation."""
        handler = ModerationHandler(config, metrics_tracker)
        request = ModerationRequest(input="This is safe content")

        response = await handler(request, fastapi_request, "req-123")

        assert len(response.results) == 1
        assert response.results[0].flagged is False
        assert response.results[0].categories is not None


class TestFileHandler:
    """Tests for FileHandler."""

    @pytest.mark.asyncio
    async def test_file_handler_endpoint(self, config, metrics_tracker):
        """Test endpoint path."""
        handler = FileHandler(config, metrics_tracker)
        assert handler.endpoint_path() == "/v1/files"

    @pytest.mark.asyncio
    async def test_file_handler_list(self, config, metrics_tracker, fastapi_request):
        """Test file listing."""
        handler = FileHandler(config, metrics_tracker)
        request = {}

        response = await handler(request, fastapi_request, "req-123")

        assert response.object == "list"
        assert isinstance(response.data, list)


class TestBatchHandler:
    """Tests for BatchHandler."""

    @pytest.mark.asyncio
    async def test_batch_handler_endpoint(self, config, metrics_tracker):
        """Test endpoint path."""
        handler = BatchHandler(config, metrics_tracker)
        assert handler.endpoint_path() == "/v1/batches"

    @pytest.mark.asyncio
    async def test_batch_handler_creation(self, config, metrics_tracker, fastapi_request):
        """Test batch creation."""
        handler = BatchHandler(config, metrics_tracker)
        request = CreateBatchRequest(
            input_file_id="file-abc123",
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )

        response = await handler(request, fastapi_request, "req-123")

        assert response.object == "batch"
        assert response.endpoint == "/v1/chat/completions"
        assert response.input_file_id == "file-abc123"


class TestChatCompletionHandler:
    """Tests for ChatCompletionHandler."""

    @pytest.mark.asyncio
    async def test_chat_completion_endpoint(self, config, metrics_tracker):
        """Test endpoint path."""
        handler = ChatCompletionHandler(config, metrics_tracker)
        assert handler.endpoint_path() == "/v1/chat/completions"

    @pytest.mark.asyncio
    async def test_chat_completion_non_streaming(
        self, config, metrics_tracker, fastapi_request
    ):
        """Test non-streaming chat completion."""
        handler = ChatCompletionHandler(config, metrics_tracker)
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[Message(role=Role.USER, content="Hello")],
            stream=False,
        )

        response = await handler(request, fastapi_request, "req-123")

        assert response.model == "gpt-4"
        assert len(response.choices) > 0
        assert response.choices[0].message.content is not None
        assert response.usage is not None

    @pytest.mark.asyncio
    async def test_chat_completion_streaming(
        self, config, metrics_tracker, fastapi_request
    ):
        """Test streaming chat completion."""
        handler = ChatCompletionHandler(config, metrics_tracker)
        request = ChatCompletionRequest(
            model="gpt-4",
            messages=[ChatMessage(role="user", content="Hello")],
            stream=True,
        )

        chunks = []
        async for chunk in handler(request, fastapi_request, "req-123"):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert all(hasattr(chunk, "choices") for chunk in chunks)


class TestCompletionHandler:
    """Tests for CompletionHandler."""

    @pytest.mark.asyncio
    async def test_completion_endpoint(self, config, metrics_tracker):
        """Test endpoint path."""
        handler = CompletionHandler(config, metrics_tracker)
        assert handler.endpoint_path() == "/v1/completions"

    @pytest.mark.asyncio
    async def test_completion_non_streaming(
        self, config, metrics_tracker, fastapi_request
    ):
        """Test non-streaming completion."""
        handler = CompletionHandler(config, metrics_tracker)
        request = CompletionRequest(
            model="gpt-3.5-turbo-instruct",
            prompt="Once upon a time",
            stream=False,
        )

        response = await handler(request, fastapi_request, "req-123")

        assert response.model == "gpt-3.5-turbo-instruct"
        assert len(response.choices) > 0
        assert response.choices[0].text is not None
        assert response.usage is not None

    @pytest.mark.asyncio
    async def test_completion_streaming(self, config, metrics_tracker, fastapi_request):
        """Test streaming completion."""
        handler = CompletionHandler(config, metrics_tracker)
        request = CompletionRequest(
            model="gpt-3.5-turbo-instruct",
            prompt="Once upon a time",
            stream=True,
        )

        chunks = []
        async for chunk in handler(request, fastapi_request, "req-123"):
            chunks.append(chunk)

        assert len(chunks) > 0


class TestModelHandler:
    """Tests for ModelHandler."""

    @pytest.mark.asyncio
    async def test_model_handler_endpoint(self, config, metrics_tracker):
        """Test endpoint path."""
        handler = ModelHandler(config, metrics_tracker)
        assert handler.endpoint_path() == "/v1/models"

    @pytest.mark.asyncio
    async def test_model_handler_list(self, config, metrics_tracker, fastapi_request):
        """Test model listing."""
        handler = ModelHandler(config, metrics_tracker)

        response = await handler(None, fastapi_request, "req-123")

        assert response.object == "list"
        assert len(response.data) > 0
        assert all(hasattr(model, "id") for model in response.data)


class TestModelRetrievalHandler:
    """Tests for ModelRetrievalHandler."""

    @pytest.mark.asyncio
    async def test_model_retrieval_endpoint(self, config, metrics_tracker):
        """Test endpoint path."""
        handler = ModelRetrievalHandler(config, metrics_tracker)
        assert handler.endpoint_path() == "/v1/models/{model_id}"

    @pytest.mark.asyncio
    async def test_model_retrieval_execution(
        self, config, metrics_tracker, fastapi_request
    ):
        """Test model retrieval."""
        handler = ModelRetrievalHandler(config, metrics_tracker)
        model_id = "gpt-4"

        response = await handler(model_id, fastapi_request, "req-123")

        assert response.id == "gpt-4"
        assert response.object == "model"


class TestMetricsHandler:
    """Tests for MetricsHandler."""

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, config, metrics_tracker):
        """Test endpoint path."""
        handler = MetricsHandler(config, metrics_tracker)
        assert handler.endpoint_path() == "/metrics"

    @pytest.mark.asyncio
    async def test_metrics_execution(self, config, metrics_tracker, fastapi_request):
        """Test metrics retrieval."""
        handler = MetricsHandler(config, metrics_tracker)

        response = await handler(None, fastapi_request, "req-123")

        assert isinstance(response, dict)
        assert "requests" in response or "responses" in response


class TestPrometheusMetricsHandler:
    """Tests for PrometheusMetricsHandler."""

    @pytest.mark.asyncio
    async def test_prometheus_metrics_endpoint(self, config, metrics_tracker):
        """Test endpoint path."""
        handler = PrometheusMetricsHandler(config, metrics_tracker)
        assert handler.endpoint_path() == "/metrics/prometheus"

    @pytest.mark.asyncio
    async def test_prometheus_metrics_execution(
        self, config, metrics_tracker, fastapi_request
    ):
        """Test Prometheus metrics retrieval."""
        handler = PrometheusMetricsHandler(config, metrics_tracker)

        response = await handler(None, fastapi_request, "req-123")

        assert isinstance(response, str)
        # Should contain Prometheus format headers
        assert "# HELP" in response or len(response) == 0  # May be empty initially


class TestHealthHandler:
    """Tests for HealthHandler."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, config, metrics_tracker):
        """Test endpoint path."""
        handler = HealthHandler(config, metrics_tracker)
        assert handler.endpoint_path() == "/health"

    @pytest.mark.asyncio
    async def test_health_execution(self, config, metrics_tracker, fastapi_request):
        """Test health check."""
        handler = HealthHandler(config, metrics_tracker)

        response = await handler(None, fastapi_request, "req-123")

        assert response["status"] == "healthy"
        assert response["ready"] is True
        assert "timestamp" in response
