"""
Validator factory for creating endpoint-specific validation pipelines.

This module provides factory functions for creating pre-configured validation
pipelines for different API endpoints.
"""

#  SPDX-License-Identifier: Apache-2.0

from typing import Any

from fakeai.validation.pipeline import ValidationPipeline
from fakeai.validation.validators.auth import AuthValidator
from fakeai.validation.validators.content_policy import ContentPolicyValidator
from fakeai.validation.validators.context_length import ContextLengthValidator
from fakeai.validation.validators.model_availability import ModelAvailabilityValidator
from fakeai.validation.validators.multimodal import MultiModalValidator
from fakeai.validation.validators.parameters import ParameterValidator
from fakeai.validation.validators.rate_limit import RateLimitValidator
from fakeai.validation.validators.schema import SchemaValidator


def create_chat_validators(
    schema: Any | None = None,
    require_auth: bool = True,
    check_rate_limits: bool = True,
    check_content_policy: bool = False,
    fail_fast: bool = True,
) -> ValidationPipeline:
    """
    Create validation pipeline for chat completions endpoint.

    Args:
        schema: Pydantic schema for request validation (optional)
        require_auth: Whether to require authentication
        check_rate_limits: Whether to check rate limits
        check_content_policy: Whether to check content policy
        fail_fast: Whether to stop on first error

    Returns:
        Configured ValidationPipeline
    """
    pipeline = ValidationPipeline(
        fail_fast=fail_fast,
        name="ChatCompletionPipeline")

    # 1. Schema validation (if schema provided)
    if schema:
        pipeline.add_validator(SchemaValidator(schema=schema))

    # 2. Authentication (if required)
    if require_auth:
        pipeline.add_validator(AuthValidator(require_api_key=True))

    # 3. Model availability
    pipeline.add_validator(ModelAvailabilityValidator(allow_auto_create=True))

    # 4. Parameter validation
    pipeline.add_validator(ParameterValidator())

    # 5. Multi-modal content validation
    pipeline.add_validator(MultiModalValidator())

    # 6. Context length validation
    pipeline.add_validator(ContextLengthValidator())

    # 7. Content policy (if enabled)
    if check_content_policy:
        pipeline.add_validator(ContentPolicyValidator(strict_mode=False))

    # 8. Rate limiting (if enabled) - should be last
    if check_rate_limits:
        pipeline.add_validator(RateLimitValidator())

    return pipeline


def create_completion_validators(
    schema: Any | None = None,
    require_auth: bool = True,
    check_rate_limits: bool = True,
    check_content_policy: bool = False,
    fail_fast: bool = True,
) -> ValidationPipeline:
    """
    Create validation pipeline for completions endpoint (legacy).

    Args:
        schema: Pydantic schema for request validation (optional)
        require_auth: Whether to require authentication
        check_rate_limits: Whether to check rate limits
        check_content_policy: Whether to check content policy
        fail_fast: Whether to stop on first error

    Returns:
        Configured ValidationPipeline
    """
    pipeline = ValidationPipeline(
        fail_fast=fail_fast,
        name="CompletionPipeline")

    # 1. Schema validation (if schema provided)
    if schema:
        pipeline.add_validator(SchemaValidator(schema=schema))

    # 2. Authentication (if required)
    if require_auth:
        pipeline.add_validator(AuthValidator(require_api_key=True))

    # 3. Model availability
    pipeline.add_validator(ModelAvailabilityValidator(allow_auto_create=True))

    # 4. Parameter validation
    pipeline.add_validator(ParameterValidator())

    # 5. Context length validation
    pipeline.add_validator(ContextLengthValidator())

    # 6. Content policy (if enabled)
    if check_content_policy:
        pipeline.add_validator(ContentPolicyValidator(strict_mode=False))

    # 7. Rate limiting (if enabled)
    if check_rate_limits:
        pipeline.add_validator(RateLimitValidator())

    return pipeline


def create_embedding_validators(
    schema: Any | None = None,
    require_auth: bool = True,
    check_rate_limits: bool = True,
    fail_fast: bool = True,
) -> ValidationPipeline:
    """
    Create validation pipeline for embeddings endpoint.

    Args:
        schema: Pydantic schema for request validation (optional)
        require_auth: Whether to require authentication
        check_rate_limits: Whether to check rate limits
        fail_fast: Whether to stop on first error

    Returns:
        Configured ValidationPipeline
    """
    pipeline = ValidationPipeline(
        fail_fast=fail_fast,
        name="EmbeddingPipeline")

    # 1. Schema validation (if schema provided)
    if schema:
        pipeline.add_validator(SchemaValidator(schema=schema))

    # 2. Authentication (if required)
    if require_auth:
        pipeline.add_validator(AuthValidator(require_api_key=True))

    # 3. Model availability
    pipeline.add_validator(ModelAvailabilityValidator(allow_auto_create=True))

    # 4. Rate limiting (if enabled)
    if check_rate_limits:
        pipeline.add_validator(RateLimitValidator())

    return pipeline


def create_image_validators(
    schema: Any | None = None,
    require_auth: bool = True,
    check_rate_limits: bool = True,
    fail_fast: bool = True,
) -> ValidationPipeline:
    """
    Create validation pipeline for image generation endpoint.

    Args:
        schema: Pydantic schema for request validation (optional)
        require_auth: Whether to require authentication
        check_rate_limits: Whether to check rate limits
        fail_fast: Whether to stop on first error

    Returns:
        Configured ValidationPipeline
    """
    pipeline = ValidationPipeline(
        fail_fast=fail_fast,
        name="ImageGenerationPipeline")

    # 1. Schema validation (if schema provided)
    if schema:
        pipeline.add_validator(SchemaValidator(schema=schema))

    # 2. Authentication (if required)
    if require_auth:
        pipeline.add_validator(AuthValidator(require_api_key=True))

    # 3. Model availability
    pipeline.add_validator(ModelAvailabilityValidator(allow_auto_create=True))

    # 4. Parameter validation
    pipeline.add_validator(ParameterValidator())

    # 5. Rate limiting (if enabled)
    if check_rate_limits:
        pipeline.add_validator(RateLimitValidator())

    return pipeline


def create_audio_validators(
    schema: Any | None = None,
    require_auth: bool = True,
    check_rate_limits: bool = True,
    fail_fast: bool = True,
) -> ValidationPipeline:
    """
    Create validation pipeline for audio endpoints (speech, transcription).

    Args:
        schema: Pydantic schema for request validation (optional)
        require_auth: Whether to require authentication
        check_rate_limits: Whether to check rate limits
        fail_fast: Whether to stop on first error

    Returns:
        Configured ValidationPipeline
    """
    pipeline = ValidationPipeline(fail_fast=fail_fast, name="AudioPipeline")

    # 1. Schema validation (if schema provided)
    if schema:
        pipeline.add_validator(SchemaValidator(schema=schema))

    # 2. Authentication (if required)
    if require_auth:
        pipeline.add_validator(AuthValidator(require_api_key=True))

    # 3. Model availability
    pipeline.add_validator(ModelAvailabilityValidator(allow_auto_create=True))

    # 4. Rate limiting (if enabled)
    if check_rate_limits:
        pipeline.add_validator(RateLimitValidator())

    return pipeline


def create_moderation_validators(
    schema: Any | None = None,
    require_auth: bool = True,
    check_rate_limits: bool = True,
    fail_fast: bool = True,
) -> ValidationPipeline:
    """
    Create validation pipeline for moderation endpoint.

    Args:
        schema: Pydantic schema for request validation (optional)
        require_auth: Whether to require authentication
        check_rate_limits: Whether to check rate limits
        fail_fast: Whether to stop on first error

    Returns:
        Configured ValidationPipeline
    """
    pipeline = ValidationPipeline(
        fail_fast=fail_fast,
        name="ModerationPipeline")

    # 1. Schema validation (if schema provided)
    if schema:
        pipeline.add_validator(SchemaValidator(schema=schema))

    # 2. Authentication (if required)
    if require_auth:
        pipeline.add_validator(AuthValidator(require_api_key=True))

    # 3. Model availability
    pipeline.add_validator(ModelAvailabilityValidator(allow_auto_create=True))

    # 4. Rate limiting (if enabled)
    if check_rate_limits:
        pipeline.add_validator(RateLimitValidator())

    return pipeline


def create_batch_validators(
    schema: Any | None = None,
    require_auth: bool = True,
    check_rate_limits: bool = True,
    fail_fast: bool = True,
) -> ValidationPipeline:
    """
    Create validation pipeline for batch processing endpoint.

    Args:
        schema: Pydantic schema for request validation (optional)
        require_auth: Whether to require authentication
        check_rate_limits: Whether to check rate limits
        fail_fast: Whether to stop on first error

    Returns:
        Configured ValidationPipeline
    """
    pipeline = ValidationPipeline(fail_fast=fail_fast, name="BatchPipeline")

    # 1. Schema validation (if schema provided)
    if schema:
        pipeline.add_validator(SchemaValidator(schema=schema))

    # 2. Authentication (if required)
    if require_auth:
        pipeline.add_validator(AuthValidator(require_api_key=True))

    # 3. Rate limiting (if enabled)
    if check_rate_limits:
        pipeline.add_validator(RateLimitValidator())

    return pipeline


def create_validators_for_endpoint(
    endpoint: str,
    schema: Any | None = None,
    require_auth: bool = True,
    check_rate_limits: bool = True,
    check_content_policy: bool = False,
    fail_fast: bool = True,
) -> ValidationPipeline:
    """
    Create validation pipeline for a specific endpoint.

    Args:
        endpoint: Endpoint name (chat, completion, embedding, image, audio, moderation, batch)
        schema: Pydantic schema for request validation (optional)
        require_auth: Whether to require authentication
        check_rate_limits: Whether to check rate limits
        check_content_policy: Whether to check content policy (for chat/completion)
        fail_fast: Whether to stop on first error

    Returns:
        Configured ValidationPipeline

    Raises:
        ValueError: If endpoint is not recognized
    """
    endpoint_lower = endpoint.lower()

    if endpoint_lower in ("chat", "chat_completion", "chat_completions"):
        return create_chat_validators(
            schema=schema,
            require_auth=require_auth,
            check_rate_limits=check_rate_limits,
            check_content_policy=check_content_policy,
            fail_fast=fail_fast,
        )

    elif endpoint_lower in ("completion", "completions"):
        return create_completion_validators(
            schema=schema,
            require_auth=require_auth,
            check_rate_limits=check_rate_limits,
            check_content_policy=check_content_policy,
            fail_fast=fail_fast,
        )

    elif endpoint_lower in ("embedding", "embeddings"):
        return create_embedding_validators(
            schema=schema,
            require_auth=require_auth,
            check_rate_limits=check_rate_limits,
            fail_fast=fail_fast,
        )

    elif endpoint_lower in ("image", "images", "image_generation"):
        return create_image_validators(
            schema=schema,
            require_auth=require_auth,
            check_rate_limits=check_rate_limits,
            fail_fast=fail_fast,
        )

    elif endpoint_lower in ("audio", "speech", "transcription"):
        return create_audio_validators(
            schema=schema,
            require_auth=require_auth,
            check_rate_limits=check_rate_limits,
            fail_fast=fail_fast,
        )

    elif endpoint_lower == "moderation":
        return create_moderation_validators(
            schema=schema,
            require_auth=require_auth,
            check_rate_limits=check_rate_limits,
            fail_fast=fail_fast,
        )

    elif endpoint_lower == "batch":
        return create_batch_validators(
            schema=schema,
            require_auth=require_auth,
            check_rate_limits=check_rate_limits,
            fail_fast=fail_fast,
        )

    else:
        raise ValueError(
            f"Unknown endpoint: {endpoint}. Supported endpoints: "
            "chat, completion, embedding, image, audio, moderation, batch"
        )
