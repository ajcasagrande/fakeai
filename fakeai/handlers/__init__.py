"""
Endpoint handlers for FakeAI.

This package provides a handler-based architecture for endpoint processing.
Handlers follow a consistent lifecycle pattern and provide automatic metrics
tracking, context management, and error handling.

Handler Types:
    - EndpointHandler: Base class for non-streaming handlers
    - StreamingHandler: Base class for streaming handlers

Available Handlers:
    - EmbeddingHandler: /v1/embeddings
    - ImageGenerationHandler: /v1/images/generations
    - AudioSpeechHandler: /v1/audio/speech
    - ModerationHandler: /v1/moderations
    - FileHandler: /v1/files
    - BatchHandler: /v1/batches
    - ChatCompletionHandler: /v1/chat/completions
    - CompletionHandler: /v1/completions
    - ModelHandler: /v1/models
    - ModelRetrievalHandler: /v1/models/{model_id}
    - MetricsHandler: /metrics
    - PrometheusMetricsHandler: /metrics/prometheus
    - HealthHandler: /health

Usage:
    # Get a handler from the registry
    from fakeai.handlers.registry import HandlerRegistry

    registry = HandlerRegistry.instance()
    handler = registry.get_handler("/v1/embeddings", config, metrics_tracker)

    # Process a request
    response = await handler(request, fastapi_request, request_id)

Registry:
    All handlers are automatically registered using the @register_handler
    decorator. The registry provides discovery and instantiation.

Lifecycle:
    1. pre_process() - Validate and prepare
    2. execute() or execute_stream() - Main logic
    3. post_process() - Track metrics and process response
    4. on_error() - Handle errors

Context:
    RequestContext provides:
    - request_id: Unique identifier
    - endpoint: API endpoint path
    - user_id: Extracted from authorization
    - client_ip: Client IP address
    - start_time: Request start timestamp
    - model: Model name (if applicable)
    - streaming: Whether request is streaming
    - metadata: Additional context data
"""
#  SPDX-License-Identifier: Apache-2.0

from fakeai.handlers.audio import AudioSpeechHandler
from fakeai.handlers.base import (
    EndpointHandler,
    RequestContext,
    StreamingHandler,
)
from fakeai.handlers.batches import BatchHandler
from fakeai.handlers.chat import ChatCompletionHandler
from fakeai.handlers.completions import CompletionHandler
from fakeai.handlers.embeddings import EmbeddingHandler
from fakeai.handlers.files import FileHandler
from fakeai.handlers.images import ImageGenerationHandler
from fakeai.handlers.metrics import (
    HealthHandler,
    MetricsHandler,
    PrometheusMetricsHandler,
)
from fakeai.handlers.models import ModelHandler, ModelRetrievalHandler
from fakeai.handlers.moderations import ModerationHandler
from fakeai.handlers.registry import HandlerRegistry, register_handler

__all__ = [
    # Base classes
    "EndpointHandler",
    "StreamingHandler",
    "RequestContext",
    # Registry
    "HandlerRegistry",
    "register_handler",
    # Handlers
    "EmbeddingHandler",
    "ImageGenerationHandler",
    "AudioSpeechHandler",
    "ModerationHandler",
    "FileHandler",
    "BatchHandler",
    "ChatCompletionHandler",
    "CompletionHandler",
    "ModelHandler",
    "ModelRetrievalHandler",
    "MetricsHandler",
    "PrometheusMetricsHandler",
    "HealthHandler",
]
