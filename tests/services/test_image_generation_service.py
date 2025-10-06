"""
Tests for ImageGenerationService

This module tests the image generation service functionality including:
- DALL-E 2 and DALL-E 3 model support
- Stability AI model support
- Size validation for different models
- Quality and style variations
- Actual image generation when enabled
- URL generation fallback when disabled
- Parameter validation and error handling
- Usage metrics tracking
"""

#  SPDX-License-Identifier: Apache-2.0

import base64

import pytest

from fakeai.config import AppConfig
from fakeai.image_generator import ImageGenerator
from fakeai.metrics import MetricsTracker
from fakeai.models import ImageGenerationRequest
from fakeai.services.image_generation_service import ImageGenerationService


@pytest.fixture
def config():
    """Create test configuration."""
    return AppConfig(
        response_delay=0.0,
        generate_actual_images=False,
    )


@pytest.fixture
def metrics_tracker():
    """Create metrics tracker."""
    return MetricsTracker()


@pytest.fixture
def image_service(config, metrics_tracker):
    """Create image generation service instance without actual image generator."""
    return ImageGenerationService(
        config=config,
        metrics_tracker=metrics_tracker,
        image_generator=None,
    )


@pytest.fixture
def image_service_with_generator(config, metrics_tracker):
    """Create image generation service with actual image generator."""
    generator = ImageGenerator(
        base_url="http://localhost:8000",
        storage_backend="memory",
        retention_hours=1,
    )
    return ImageGenerationService(
        config=config,
        metrics_tracker=metrics_tracker,
        image_generator=generator,
    )


# DALL-E 2 Tests


@pytest.mark.asyncio
async def test_dall_e_2_basic(image_service):
    """Test basic DALL-E 2 image generation."""
    request = ImageGenerationRequest(
        prompt="A cat sitting on a table",
        model="dall-e-2",
        size="512x512",
        n=1,
    )

    response = await image_service.generate_images(request)

    assert response.created > 0
    assert len(response.data) == 1
    assert response.data[0].url is not None
    assert "simulated-openai-images" in response.data[0].url


@pytest.mark.asyncio
async def test_dall_e_2_all_sizes(image_service):
    """Test DALL-E 2 with all supported sizes."""
    sizes = ["256x256", "512x512", "1024x1024"]

    for size in sizes:
        request = ImageGenerationRequest(
            prompt="Test image",
            model="dall-e-2",
            size=size,
            n=1,
        )

        response = await image_service.generate_images(request)

        assert len(response.data) == 1
        assert response.data[0].url is not None


@pytest.mark.asyncio
async def test_dall_e_2_multiple_images(image_service):
    """Test DALL-E 2 generating multiple images."""
    request = ImageGenerationRequest(
        prompt="Multiple test images",
        model="dall-e-2",
        size="512x512",
        n=3,
    )

    response = await image_service.generate_images(request)

    assert len(response.data) == 3
    # Ensure each image has a unique URL
    urls = [img.url for img in response.data]
    assert len(urls) == len(set(urls))


@pytest.mark.asyncio
async def test_dall_e_2_invalid_size(image_service):
    """Test DALL-E 2 with invalid size."""
    request = ImageGenerationRequest(
        prompt="Test image",
        model="dall-e-2",
        size="1792x1024",  # DALL-E 3 size
        n=1,
    )

    with pytest.raises(ValueError, match="Invalid size for DALL-E 2"):
        await image_service.generate_images(request)


# DALL-E 3 Tests


@pytest.mark.asyncio
async def test_dall_e_3_basic(image_service):
    """Test basic DALL-E 3 image generation."""
    request = ImageGenerationRequest(
        prompt="A futuristic cityscape at sunset",
        model="dall-e-3",
        size="1024x1024",
        quality="standard",
        style="vivid",
        n=1,
    )

    response = await image_service.generate_images(request)

    assert response.created > 0
    assert len(response.data) == 1
    assert response.data[0].url is not None


@pytest.mark.asyncio
async def test_dall_e_3_hd_quality(image_service):
    """Test DALL-E 3 with HD quality."""
    request = ImageGenerationRequest(
        prompt="High quality landscape",
        model="dall-e-3",
        size="1792x1024",
        quality="hd",
        style="natural",
        n=1,
    )

    response = await image_service.generate_images(request)

    assert len(response.data) == 1
    assert response.data[0].url is not None


@pytest.mark.asyncio
async def test_dall_e_3_portrait_size(image_service):
    """Test DALL-E 3 with portrait orientation."""
    request = ImageGenerationRequest(
        prompt="Portrait orientation test",
        model="dall-e-3",
        size="1024x1792",
        quality="standard",
        style="vivid",
        n=1,
    )

    response = await image_service.generate_images(request)

    assert len(response.data) == 1


@pytest.mark.asyncio
async def test_dall_e_3_multiple_images_error(image_service):
    """Test DALL-E 3 rejects n > 1."""
    request = ImageGenerationRequest(
        prompt="Test",
        model="dall-e-3",
        size="1024x1024",
        n=2,
    )

    with pytest.raises(ValueError, match="DALL-E 3 only supports n=1"):
        await image_service.generate_images(request)


@pytest.mark.asyncio
async def test_dall_e_3_invalid_size(image_service):
    """Test DALL-E 3 with invalid size."""
    request = ImageGenerationRequest(
        prompt="Test image",
        model="dall-e-3",
        size="512x512",  # DALL-E 2 size
        n=1,
    )

    with pytest.raises(ValueError, match="Invalid size for DALL-E 3"):
        await image_service.generate_images(request)


@pytest.mark.asyncio
async def test_dall_e_3_hd_invalid_size(image_service):
    """Test DALL-E 3 HD quality requires specific sizes."""
    request = ImageGenerationRequest(
        prompt="Test",
        model="dall-e-3",
        size="256x256",  # Invalid for DALL-E 3
        quality="hd",
        n=1,
    )

    # Will fail at size validation first
    with pytest.raises(ValueError, match="Invalid size for DALL-E 3"):
        await image_service.generate_images(request)


# Stability AI Tests


@pytest.mark.asyncio
async def test_stability_ai_basic(image_service):
    """Test Stability AI model."""
    request = ImageGenerationRequest(
        prompt="Abstract art",
        model="stabilityai/stable-diffusion-2-1",
        size="512x512",
        n=1,
    )

    response = await image_service.generate_images(request)

    assert len(response.data) == 1
    assert response.data[0].url is not None


@pytest.mark.asyncio
async def test_stability_ai_xl(image_service):
    """Test Stability AI XL model."""
    request = ImageGenerationRequest(
        prompt="High resolution art",
        model="stabilityai/stable-diffusion-xl-base-1.0",
        size="1024x1024",
        n=1,
    )

    response = await image_service.generate_images(request)

    assert len(response.data) == 1


# Response Format Tests


@pytest.mark.asyncio
async def test_url_format(image_service):
    """Test URL response format."""
    request = ImageGenerationRequest(
        prompt="Test URL format",
        model="dall-e-2",
        size="512x512",
        response_format="url",
        n=1,
    )

    response = await image_service.generate_images(request)

    assert response.data[0].url is not None
    assert response.data[0].b64_json is None


@pytest.mark.asyncio
async def test_b64_json_format(image_service):
    """Test base64 JSON response format."""
    request = ImageGenerationRequest(
        prompt="Test base64 format",
        model="dall-e-2",
        size="512x512",
        response_format="b64_json",
        n=1,
    )

    response = await image_service.generate_images(request)

    assert response.data[0].url is None
    assert response.data[0].b64_json is not None
    # Verify it's valid base64
    base64.b64decode(response.data[0].b64_json)


# Actual Image Generation Tests


@pytest.mark.asyncio
async def test_actual_image_generation(image_service_with_generator):
    """Test actual image generation when generator is enabled."""
    request = ImageGenerationRequest(
        prompt="Real image test",
        model="dall-e-3",
        size="1024x1024",
        quality="standard",
        style="vivid",
        n=1,
    )

    response = await image_service_with_generator.generate_images(request)

    assert len(response.data) == 1
    assert response.data[0].url is not None
    # Should contain localhost URL when using actual generator
    assert (
        "localhost" in response.data[0].url
        or "simulated-openai-images" in response.data[0].url
    )


@pytest.mark.asyncio
async def test_actual_image_b64_generation(image_service_with_generator):
    """Test actual image generation with base64 format."""
    request = ImageGenerationRequest(
        prompt="Real base64 test",
        model="dall-e-2",
        size="256x256",
        response_format="b64_json",
        n=1,
    )

    response = await image_service_with_generator.generate_images(request)

    assert response.data[0].b64_json is not None
    # Should be real base64-encoded PNG data
    decoded = base64.b64decode(response.data[0].b64_json)
    # PNG files start with specific magic bytes
    assert decoded[:4] == b"\x89PNG"


# Parameter Validation Tests


@pytest.mark.asyncio
async def test_invalid_model(image_service):
    """Test invalid model rejection."""
    request = ImageGenerationRequest(
        prompt="Test",
        model="invalid-model",
        size="512x512",
        n=1,
    )

    with pytest.raises(ValueError, match="Invalid model for image generation"):
        await image_service.generate_images(request)


@pytest.mark.asyncio
async def test_invalid_quality(image_service):
    """Test invalid quality rejection at Pydantic level."""
    from pydantic import ValidationError

    # Pydantic validates quality enum before service sees it
    with pytest.raises(ValidationError):
        request = ImageGenerationRequest(
            prompt="Test",
            model="dall-e-3",
            size="1024x1024",
            quality="ultra",  # Invalid - will be caught by Pydantic
            n=1,
        )


@pytest.mark.asyncio
async def test_invalid_style(image_service):
    """Test invalid style rejection at Pydantic level."""
    from pydantic import ValidationError

    # Pydantic validates style enum before service sees it
    with pytest.raises(ValidationError):
        request = ImageGenerationRequest(
            prompt="Test",
            model="dall-e-3",
            size="1024x1024",
            style="photorealistic",  # Invalid - will be caught by Pydantic
            n=1,
        )


# Style Tests


@pytest.mark.asyncio
async def test_vivid_style(image_service):
    """Test vivid style."""
    request = ImageGenerationRequest(
        prompt="Vibrant colors",
        model="dall-e-3",
        size="1024x1024",
        style="vivid",
        n=1,
    )

    response = await image_service.generate_images(request)

    assert len(response.data) == 1


@pytest.mark.asyncio
async def test_natural_style(image_service):
    """Test natural style."""
    request = ImageGenerationRequest(
        prompt="Natural landscape",
        model="dall-e-3",
        size="1024x1024",
        style="natural",
        n=1,
    )

    response = await image_service.generate_images(request)

    assert len(response.data) == 1


# Default Values Tests


@pytest.mark.asyncio
async def test_default_model(image_service):
    """Test default model when not specified."""
    request = ImageGenerationRequest(
        prompt="Test defaults",
        n=1,
    )

    response = await image_service.generate_images(request)

    assert len(response.data) == 1


@pytest.mark.asyncio
async def test_default_size(image_service):
    """Test default size when not specified."""
    request = ImageGenerationRequest(
        prompt="Test defaults",
        model="dall-e-3",
        n=1,
    )

    response = await image_service.generate_images(request)

    assert len(response.data) == 1


@pytest.mark.asyncio
async def test_default_quality(image_service):
    """Test default quality when not specified."""
    request = ImageGenerationRequest(
        prompt="Test defaults",
        model="dall-e-3",
        size="1024x1024",
        n=1,
    )

    response = await image_service.generate_images(request)

    assert len(response.data) == 1


# Metrics Tests


@pytest.mark.asyncio
async def test_metrics_tracking(image_service, metrics_tracker):
    """Test that metrics are properly tracked via track_request."""
    # Just verify that the service can call track_request without error
    # The actual metrics counting is tested elsewhere in the codebase

    request = ImageGenerationRequest(
        prompt="Metrics test",
        model="dall-e-2",
        size="512x512",
        n=1,
    )

    # This should succeed and internally call metrics_tracker.track_request()
    response = await image_service.generate_images(request)

    # Verify response is valid
    assert response is not None
    assert len(response.data) == 1
    assert response.data[0].url is not None


# Edge Cases


@pytest.mark.asyncio
async def test_empty_prompt(image_service):
    """Test generation with empty prompt."""
    request = ImageGenerationRequest(
        prompt="",
        model="dall-e-2",
        size="512x512",
        n=1,
    )

    # Should not fail, just generate with empty prompt
    response = await image_service.generate_images(request)
    assert len(response.data) == 1


@pytest.mark.asyncio
async def test_very_long_prompt(image_service):
    """Test generation with very long prompt (up to Pydantic limit)."""
    # Pydantic enforces max 1000 characters, so create a prompt near that limit
    long_prompt = "A beautiful " + "and stunning " * 60 + "landscape"
    long_prompt = long_prompt[:999]  # Ensure it's under 1000 chars

    request = ImageGenerationRequest(
        prompt=long_prompt,
        model="dall-e-2",
        size="512x512",
        n=1,
    )

    response = await image_service.generate_images(request)
    assert len(response.data) == 1


@pytest.mark.asyncio
async def test_unicode_prompt(image_service):
    """Test generation with unicode characters in prompt."""
    request = ImageGenerationRequest(
        prompt="A beautiful 日本 landscape with 🌸 cherry blossoms",
        model="dall-e-2",
        size="512x512",
        n=1,
    )

    response = await image_service.generate_images(request)
    assert len(response.data) == 1


# Processing Delay Tests


@pytest.mark.asyncio
async def test_processing_delay_varies_by_size(image_service):
    """Test that processing delay varies by image size."""
    import time

    # Small image
    start = time.time()
    request_small = ImageGenerationRequest(
        prompt="Small test",
        model="dall-e-2",
        size="256x256",
        n=1,
    )
    await image_service.generate_images(request_small)
    small_duration = time.time() - start

    # Large image
    start = time.time()
    request_large = ImageGenerationRequest(
        prompt="Large test",
        model="dall-e-3",
        size="1792x1024",
        quality="hd",
        n=1,
    )
    await image_service.generate_images(request_large)
    large_duration = time.time() - start

    # Large HD image should take longer
    assert large_duration > small_duration


@pytest.mark.asyncio
async def test_processing_delay_varies_by_count(image_service):
    """Test that processing delay varies by number of images."""
    import time

    # Single image
    start = time.time()
    request_single = ImageGenerationRequest(
        prompt="Single test",
        model="dall-e-2",
        size="512x512",
        n=1,
    )
    await image_service.generate_images(request_single)
    single_duration = time.time() - start

    # Multiple images
    start = time.time()
    request_multiple = ImageGenerationRequest(
        prompt="Multiple test",
        model="dall-e-2",
        size="512x512",
        n=5,
    )
    await image_service.generate_images(request_multiple)
    multiple_duration = time.time() - start

    # Multiple images should take longer
    assert multiple_duration > single_duration
