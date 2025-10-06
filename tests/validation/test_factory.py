"""
Tests for validator factory.
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest
from pydantic import BaseModel

from fakeai.validation.factory import (
    create_audio_validators,
    create_batch_validators,
    create_chat_validators,
    create_completion_validators,
    create_embedding_validators,
    create_image_validators,
    create_moderation_validators,
    create_validators_for_endpoint,
)
from fakeai.validation.pipeline import ValidationPipeline


class DummySchema(BaseModel):
    """Dummy schema for testing."""

    model: str
    test_field: str = "default"


class TestChatValidators:
    """Tests for create_chat_validators."""

    def test_basic_chat_pipeline(self):
        """Test creating basic chat validation pipeline."""
        pipeline = create_chat_validators()

        assert isinstance(pipeline, ValidationPipeline)
        assert pipeline.name == "ChatCompletionPipeline"
        assert len(pipeline) > 0

    def test_chat_pipeline_with_schema(self):
        """Test creating chat pipeline with schema validation."""
        pipeline = create_chat_validators(schema=DummySchema)

        assert len(pipeline) > 0
        # Schema validator should be included
        validator_names = [v.name for v in pipeline._validators]
        assert any("Schema" in name for name in validator_names)

    def test_chat_pipeline_no_auth(self):
        """Test creating chat pipeline without auth."""
        pipeline_with_auth = create_chat_validators(require_auth=True)
        pipeline_without_auth = create_chat_validators(require_auth=False)

        # Without auth should have fewer validators
        assert len(pipeline_without_auth) < len(pipeline_with_auth)

    def test_chat_pipeline_no_rate_limits(self):
        """Test creating chat pipeline without rate limits."""
        pipeline_with_limits = create_chat_validators(check_rate_limits=True)
        pipeline_without_limits = create_chat_validators(check_rate_limits=False)

        assert len(pipeline_without_limits) < len(pipeline_with_limits)

    def test_chat_pipeline_with_content_policy(self):
        """Test creating chat pipeline with content policy."""
        pipeline = create_chat_validators(check_content_policy=True)

        validator_names = [v.name for v in pipeline._validators]
        assert any("ContentPolicy" in name for name in validator_names)

    def test_chat_pipeline_fail_fast(self):
        """Test creating chat pipeline with fail-fast mode."""
        pipeline_fail_fast = create_chat_validators(fail_fast=True)
        pipeline_collect_all = create_chat_validators(fail_fast=False)

        assert pipeline_fail_fast._fail_fast is True
        assert pipeline_collect_all._fail_fast is False


class TestCompletionValidators:
    """Tests for create_completion_validators."""

    def test_basic_completion_pipeline(self):
        """Test creating basic completion validation pipeline."""
        pipeline = create_completion_validators()

        assert isinstance(pipeline, ValidationPipeline)
        assert pipeline.name == "CompletionPipeline"
        assert len(pipeline) > 0

    def test_completion_pipeline_structure(self):
        """Test completion pipeline has expected validators."""
        pipeline = create_completion_validators()

        validator_names = [v.name for v in pipeline._validators]

        # Should have model availability, parameter, and context length validators
        assert any("Model" in name for name in validator_names)
        assert any("Parameter" in name for name in validator_names)
        assert any("Context" in name for name in validator_names)


class TestEmbeddingValidators:
    """Tests for create_embedding_validators."""

    def test_basic_embedding_pipeline(self):
        """Test creating basic embedding validation pipeline."""
        pipeline = create_embedding_validators()

        assert isinstance(pipeline, ValidationPipeline)
        assert pipeline.name == "EmbeddingPipeline"
        assert len(pipeline) > 0

    def test_embedding_pipeline_simpler_than_chat(self):
        """Test embedding pipeline is simpler than chat pipeline."""
        embedding_pipeline = create_embedding_validators()
        chat_pipeline = create_chat_validators()

        # Embedding pipeline should be simpler (no context length, multimodal, etc.)
        assert len(embedding_pipeline) < len(chat_pipeline)


class TestImageValidators:
    """Tests for create_image_validators."""

    def test_basic_image_pipeline(self):
        """Test creating basic image generation validation pipeline."""
        pipeline = create_image_validators()

        assert isinstance(pipeline, ValidationPipeline)
        assert pipeline.name == "ImageGenerationPipeline"
        assert len(pipeline) > 0

    def test_image_pipeline_has_parameter_validator(self):
        """Test image pipeline includes parameter validation."""
        pipeline = create_image_validators()

        validator_names = [v.name for v in pipeline._validators]
        assert any("Parameter" in name for name in validator_names)


class TestAudioValidators:
    """Tests for create_audio_validators."""

    def test_basic_audio_pipeline(self):
        """Test creating basic audio validation pipeline."""
        pipeline = create_audio_validators()

        assert isinstance(pipeline, ValidationPipeline)
        assert pipeline.name == "AudioPipeline"
        assert len(pipeline) > 0


class TestModerationValidators:
    """Tests for create_moderation_validators."""

    def test_basic_moderation_pipeline(self):
        """Test creating basic moderation validation pipeline."""
        pipeline = create_moderation_validators()

        assert isinstance(pipeline, ValidationPipeline)
        assert pipeline.name == "ModerationPipeline"
        assert len(pipeline) > 0


class TestBatchValidators:
    """Tests for create_batch_validators."""

    def test_basic_batch_pipeline(self):
        """Test creating basic batch validation pipeline."""
        pipeline = create_batch_validators()

        assert isinstance(pipeline, ValidationPipeline)
        assert pipeline.name == "BatchPipeline"
        assert len(pipeline) > 0


class TestCreateValidatorsForEndpoint:
    """Tests for create_validators_for_endpoint factory function."""

    def test_chat_endpoint(self):
        """Test creating validators for chat endpoint."""
        pipeline = create_validators_for_endpoint("chat")
        assert pipeline.name == "ChatCompletionPipeline"

        # Test variations
        pipeline = create_validators_for_endpoint("chat_completion")
        assert pipeline.name == "ChatCompletionPipeline"

        pipeline = create_validators_for_endpoint("chat_completions")
        assert pipeline.name == "ChatCompletionPipeline"

    def test_completion_endpoint(self):
        """Test creating validators for completion endpoint."""
        pipeline = create_validators_for_endpoint("completion")
        assert pipeline.name == "CompletionPipeline"

        pipeline = create_validators_for_endpoint("completions")
        assert pipeline.name == "CompletionPipeline"

    def test_embedding_endpoint(self):
        """Test creating validators for embedding endpoint."""
        pipeline = create_validators_for_endpoint("embedding")
        assert pipeline.name == "EmbeddingPipeline"

        pipeline = create_validators_for_endpoint("embeddings")
        assert pipeline.name == "EmbeddingPipeline"

    def test_image_endpoint(self):
        """Test creating validators for image endpoint."""
        pipeline = create_validators_for_endpoint("image")
        assert pipeline.name == "ImageGenerationPipeline"

        pipeline = create_validators_for_endpoint("images")
        assert pipeline.name == "ImageGenerationPipeline"

        pipeline = create_validators_for_endpoint("image_generation")
        assert pipeline.name == "ImageGenerationPipeline"

    def test_audio_endpoint(self):
        """Test creating validators for audio endpoint."""
        pipeline = create_validators_for_endpoint("audio")
        assert pipeline.name == "AudioPipeline"

        pipeline = create_validators_for_endpoint("speech")
        assert pipeline.name == "AudioPipeline"

        pipeline = create_validators_for_endpoint("transcription")
        assert pipeline.name == "AudioPipeline"

    def test_moderation_endpoint(self):
        """Test creating validators for moderation endpoint."""
        pipeline = create_validators_for_endpoint("moderation")
        assert pipeline.name == "ModerationPipeline"

    def test_batch_endpoint(self):
        """Test creating validators for batch endpoint."""
        pipeline = create_validators_for_endpoint("batch")
        assert pipeline.name == "BatchPipeline"

    def test_case_insensitive(self):
        """Test endpoint names are case-insensitive."""
        pipeline1 = create_validators_for_endpoint("CHAT")
        pipeline2 = create_validators_for_endpoint("Chat")
        pipeline3 = create_validators_for_endpoint("chat")

        assert pipeline1.name == pipeline2.name == pipeline3.name

    def test_unknown_endpoint_raises(self):
        """Test unknown endpoint raises ValueError."""
        with pytest.raises(ValueError, match="Unknown endpoint"):
            create_validators_for_endpoint("unknown_endpoint")

    def test_with_all_options(self):
        """Test creating validators with all options."""
        pipeline = create_validators_for_endpoint(
            "chat",
            schema=DummySchema,
            require_auth=True,
            check_rate_limits=True,
            check_content_policy=True,
            fail_fast=False,
        )

        assert isinstance(pipeline, ValidationPipeline)
        assert pipeline._fail_fast is False
        assert len(pipeline) > 0


class TestValidatorOrdering:
    """Tests for validator ordering in pipelines."""

    def test_auth_before_other_validators(self):
        """Test auth validator comes early in pipeline."""
        pipeline = create_chat_validators(require_auth=True)

        validator_names = [v.name for v in pipeline._validators]

        # Auth should be near the beginning (after schema if present)
        auth_index = next(i for i, name in enumerate(validator_names) if "Auth" in name)
        assert auth_index < len(validator_names) / 2

    def test_rate_limit_last(self):
        """Test rate limit validator comes last in pipeline."""
        pipeline = create_chat_validators(check_rate_limits=True)

        validator_names = [v.name for v in pipeline._validators]

        # Rate limit should be last
        assert "RateLimit" in validator_names[-1]

    def test_schema_validation_first(self):
        """Test schema validation comes first when present."""
        pipeline = create_chat_validators(schema=DummySchema)

        validator_names = [v.name for v in pipeline._validators]

        # Schema validator should be first
        assert "Schema" in validator_names[0]
