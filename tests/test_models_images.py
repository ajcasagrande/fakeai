"""
Tests for image generation models.

This test suite verifies the image generation models including:
- ImageSize, ImageQuality, ImageStyle enums
- ImageResponseFormat enum
- GeneratedImage, ImageGenerationRequest, ImageGenerationResponse
- ImagesUsageResponse
- Backward compatibility and validation
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest
from pydantic import ValidationError


class TestImportsFromModelsPackage:
    """Test that all image models can be imported from the models package."""

    def test_import_image_models_from_package(self):
        """Test importing image models from fakeai.models package."""
        from fakeai.models import (
            GeneratedImage,
            ImageGenerationRequest,
            ImageGenerationResponse,
            ImageQuality,
            ImageResponseFormat,
            ImageSize,
            ImageStyle,
            ImagesUsageResponse,
        )

        # Verify classes are imported correctly
        assert ImageSize is not None
        assert ImageQuality is not None
        assert ImageStyle is not None
        assert ImageResponseFormat is not None
        assert GeneratedImage is not None
        assert ImageGenerationRequest is not None
        assert ImageGenerationResponse is not None
        assert ImagesUsageResponse is not None


class TestImportsFromImagesModule:
    """Test that models can be imported from the images module."""

    def test_import_from_images_module(self):
        """Test importing from fakeai.models.images module."""
        from fakeai.models.images import (
            GeneratedImage,
            ImageGenerationRequest,
            ImageGenerationResponse,
            ImageQuality,
            ImageResponseFormat,
            ImageSize,
            ImageStyle,
            ImagesUsageResponse,
        )

        # Verify classes are imported correctly
        assert ImageSize is not None
        assert ImageQuality is not None
        assert ImageStyle is not None
        assert ImageResponseFormat is not None
        assert GeneratedImage is not None
        assert ImageGenerationRequest is not None
        assert ImageGenerationResponse is not None
        assert ImagesUsageResponse is not None


class TestBackwardCompatibility:
    """Test that imports from different paths reference the same classes."""

    def test_image_models_reference_same_class(self):
        """Test that image models imported from different paths are the same class."""
        from fakeai.models import ImageGenerationRequest as RequestFromPackage
        from fakeai.models.images import ImageGenerationRequest as RequestFromImages

        # Verify they reference the same class
        assert RequestFromPackage is RequestFromImages

    def test_all_image_models_reference_same_class(self):
        """Test that all image models reference the same classes."""
        from fakeai.models import (
            GeneratedImage,
            ImageGenerationRequest,
            ImageGenerationResponse,
            ImageQuality,
            ImageResponseFormat,
            ImageSize,
            ImageStyle,
            ImagesUsageResponse,
        )
        from fakeai.models.images import GeneratedImage as GeneratedImageFromImages
        from fakeai.models.images import (
            ImageGenerationRequest as ImageGenerationRequestFromImages,
        )
        from fakeai.models.images import (
            ImageGenerationResponse as ImageGenerationResponseFromImages,
        )
        from fakeai.models.images import ImageQuality as ImageQualityFromImages
        from fakeai.models.images import (
            ImageResponseFormat as ImageResponseFormatFromImages,
        )
        from fakeai.models.images import ImageSize as ImageSizeFromImages
        from fakeai.models.images import ImageStyle as ImageStyleFromImages
        from fakeai.models.images import (
            ImagesUsageResponse as ImagesUsageResponseFromImages,
        )

        # Verify all classes reference the same objects
        assert ImageSize is ImageSizeFromImages
        assert ImageQuality is ImageQualityFromImages
        assert ImageStyle is ImageStyleFromImages
        assert ImageResponseFormat is ImageResponseFormatFromImages
        assert GeneratedImage is GeneratedImageFromImages
        assert ImageGenerationRequest is ImageGenerationRequestFromImages
        assert ImageGenerationResponse is ImageGenerationResponseFromImages
        assert ImagesUsageResponse is ImagesUsageResponseFromImages


class TestImageEnums:
    """Test image enumeration types."""

    def test_image_sizes(self):
        """Test ImageSize enum values."""
        from fakeai.models import ImageSize

        assert ImageSize.SIZE_256 == "256x256"
        assert ImageSize.SIZE_512 == "512x512"
        assert ImageSize.SIZE_1024 == "1024x1024"
        assert ImageSize.SIZE_1792_1024 == "1792x1024"
        assert ImageSize.SIZE_1024_1792 == "1024x1792"

        # Test that all expected sizes are present
        sizes = [e.value for e in ImageSize]
        assert "256x256" in sizes
        assert "512x512" in sizes
        assert "1024x1024" in sizes
        assert "1792x1024" in sizes
        assert "1024x1792" in sizes

    def test_quality_modes(self):
        """Test ImageQuality enum values."""
        from fakeai.models import ImageQuality

        assert ImageQuality.STANDARD == "standard"
        assert ImageQuality.HD == "hd"

        # Test that all expected qualities are present
        qualities = [e.value for e in ImageQuality]
        assert "standard" in qualities
        assert "hd" in qualities
        assert len(qualities) == 2

    def test_style_modes(self):
        """Test ImageStyle enum values."""
        from fakeai.models import ImageStyle

        assert ImageStyle.VIVID == "vivid"
        assert ImageStyle.NATURAL == "natural"

        # Test that all expected styles are present
        styles = [e.value for e in ImageStyle]
        assert "vivid" in styles
        assert "natural" in styles
        assert len(styles) == 2

    def test_response_format_modes(self):
        """Test ImageResponseFormat enum values."""
        from fakeai.models import ImageResponseFormat

        assert ImageResponseFormat.URL == "url"
        assert ImageResponseFormat.B64_JSON == "b64_json"

        # Test that all expected formats are present
        formats = [e.value for e in ImageResponseFormat]
        assert "url" in formats
        assert "b64_json" in formats
        assert len(formats) == 2


class TestModelInstantiation:
    """Test that models can be instantiated and validated correctly."""

    def test_generated_image_with_url(self):
        """Test GeneratedImage instantiation with URL."""
        from fakeai.models import GeneratedImage

        image = GeneratedImage(
            url="https://example.com/image.png",
            revised_prompt="A beautiful landscape",
        )

        assert image.url == "https://example.com/image.png"
        assert image.b64_json is None
        assert image.revised_prompt == "A beautiful landscape"

    def test_generated_image_with_base64(self):
        """Test GeneratedImage instantiation with base64."""
        from fakeai.models import GeneratedImage

        image = GeneratedImage(
            b64_json="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            revised_prompt="A red pixel",
        )

        assert image.url is None
        assert (
            image.b64_json
            == "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        assert image.revised_prompt == "A red pixel"

    def test_generated_image_minimal(self):
        """Test GeneratedImage instantiation with minimal fields."""
        from fakeai.models import GeneratedImage

        # Should allow all fields to be None
        image = GeneratedImage()

        assert image.url is None
        assert image.b64_json is None
        assert image.revised_prompt is None

    def test_image_generation_request_minimal(self):
        """Test ImageGenerationRequest with minimal required fields."""
        from fakeai.models import ImageGenerationRequest

        request = ImageGenerationRequest(prompt="A beautiful sunset")

        assert request.prompt == "A beautiful sunset"
        assert request.model == "stabilityai/stable-diffusion-2-1"
        assert request.n == 1
        assert request.quality.value == "standard"
        assert request.response_format.value == "url"
        assert request.size.value == "1024x1024"
        assert request.style.value == "vivid"
        assert request.user is None

    def test_image_generation_request_full(self):
        """Test ImageGenerationRequest with all fields."""
        from fakeai.models import (
            ImageGenerationRequest,
            ImageQuality,
            ImageResponseFormat,
            ImageSize,
            ImageStyle,
        )

        request = ImageGenerationRequest(
            prompt="A futuristic cityscape",
            model="dall-e-3",
            n=4,
            quality=ImageQuality.HD,
            response_format=ImageResponseFormat.B64_JSON,
            size=ImageSize.SIZE_1792_1024,
            style=ImageStyle.NATURAL,
            user="user-123",
        )

        assert request.prompt == "A futuristic cityscape"
        assert request.model == "dall-e-3"
        assert request.n == 4
        assert request.quality == ImageQuality.HD
        assert request.response_format == ImageResponseFormat.B64_JSON
        assert request.size == ImageSize.SIZE_1792_1024
        assert request.style == ImageStyle.NATURAL
        assert request.user == "user-123"

    def test_image_generation_response(self):
        """Test ImageGenerationResponse instantiation."""
        from fakeai.models import GeneratedImage, ImageGenerationResponse

        images = [
            GeneratedImage(url="https://example.com/image1.png"),
            GeneratedImage(url="https://example.com/image2.png"),
        ]

        response = ImageGenerationResponse(created=1234567890, data=images)

        assert response.created == 1234567890
        assert len(response.data) == 2
        assert response.data[0].url == "https://example.com/image1.png"
        assert response.data[1].url == "https://example.com/image2.png"

    def test_images_usage_response(self):
        """Test ImagesUsageResponse instantiation."""
        from fakeai.models import ImagesUsageResponse

        usage = ImagesUsageResponse(
            object="page",
            data=[],
            has_more=False,
            next_page=None,
        )

        assert usage.object == "page"
        assert usage.data == []
        assert usage.has_more is False
        assert usage.next_page is None

    def test_images_usage_response_with_pagination(self):
        """Test ImagesUsageResponse with pagination."""
        from fakeai.models import ImagesUsageResponse

        usage = ImagesUsageResponse(
            data=[{"some": "data"}],
            has_more=True,
            next_page="https://api.example.com/v1/usage/images?page=2",
        )

        assert usage.object == "page"
        assert len(usage.data) == 1
        assert usage.has_more is True
        assert usage.next_page == "https://api.example.com/v1/usage/images?page=2"


class TestModelValidation:
    """Test that models validate correctly."""

    def test_request_validation_prompt_required(self):
        """Test that prompt is required."""
        from fakeai.models import ImageGenerationRequest

        # Missing required prompt should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest()

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("prompt",) for error in errors)

    def test_request_validation_prompt_max_length(self):
        """Test that prompt has max length validation."""
        from fakeai.models import ImageGenerationRequest

        # Prompt longer than 1000 characters should raise ValidationError
        long_prompt = "a" * 1001
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationRequest(prompt=long_prompt)

        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("prompt",) and error["type"] == "string_too_long"
            for error in errors
        )

    def test_request_validation_n_range(self):
        """Test that n has valid range (1-10)."""
        from fakeai.models import ImageGenerationRequest

        # Valid n values
        request = ImageGenerationRequest(prompt="test", n=1)
        assert request.n == 1

        request = ImageGenerationRequest(prompt="test", n=10)
        assert request.n == 10

        # n=0 should raise ValidationError
        with pytest.raises(ValidationError):
            ImageGenerationRequest(prompt="test", n=0)

        # n=11 should raise ValidationError
        with pytest.raises(ValidationError):
            ImageGenerationRequest(prompt="test", n=11)

    def test_request_validation_invalid_quality(self):
        """Test that invalid quality value raises ValidationError."""
        from fakeai.models import ImageGenerationRequest

        # Invalid quality string should raise ValidationError
        with pytest.raises(ValidationError):
            ImageGenerationRequest(prompt="test", quality="ultra")

    def test_request_validation_invalid_size(self):
        """Test that invalid size value raises ValidationError."""
        from fakeai.models import ImageGenerationRequest

        # Invalid size string should raise ValidationError
        with pytest.raises(ValidationError):
            ImageGenerationRequest(prompt="test", size="2048x2048")

    def test_request_validation_invalid_style(self):
        """Test that invalid style value raises ValidationError."""
        from fakeai.models import ImageGenerationRequest

        # Invalid style string should raise ValidationError
        with pytest.raises(ValidationError):
            ImageGenerationRequest(prompt="test", style="realistic")

    def test_response_validation_created_required(self):
        """Test that created timestamp is required."""
        from fakeai.models import ImageGenerationResponse

        # Missing required created field should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationResponse(data=[])

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("created",) for error in errors)

    def test_response_validation_data_required(self):
        """Test that data is required."""
        from fakeai.models import ImageGenerationResponse

        # Missing required data field should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            ImageGenerationResponse(created=1234567890)

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("data",) for error in errors)


class TestModuleStructure:
    """Test the module structure and organization."""

    def test_images_module_exports(self):
        """Test that images module has correct exports."""
        import fakeai.models.images as images_module

        # Check that expected classes are available
        assert hasattr(images_module, "ImageSize")
        assert hasattr(images_module, "ImageQuality")
        assert hasattr(images_module, "ImageStyle")
        assert hasattr(images_module, "ImageResponseFormat")
        assert hasattr(images_module, "GeneratedImage")
        assert hasattr(images_module, "ImageGenerationRequest")
        assert hasattr(images_module, "ImageGenerationResponse")
        assert hasattr(images_module, "ImagesUsageResponse")

    def test_package_init_exports_images(self):
        """Test that package __init__ exports image models."""
        import fakeai.models as models_package

        # Check __all__ exists
        assert hasattr(models_package, "__all__")

        # Check all expected image exports are in __all__
        expected_exports = [
            "ImageSize",
            "ImageQuality",
            "ImageStyle",
            "ImageResponseFormat",
            "GeneratedImage",
            "ImageGenerationRequest",
            "ImageGenerationResponse",
            "ImagesUsageResponse",
        ]

        for export in expected_exports:
            assert export in models_package.__all__, f"{export} not in __all__"
            assert hasattr(models_package, export), f"{export} not available in package"


class TestDALLECompatibility:
    """Test DALL-E API compatibility."""

    def test_dalle_2_request(self):
        """Test DALL-E 2 compatible request."""
        from fakeai.models import (
            ImageGenerationRequest,
            ImageQuality,
            ImageSize,
        )

        # DALL-E 2 typically uses smaller sizes and standard quality
        request = ImageGenerationRequest(
            prompt="A white siamese cat",
            model="dall-e-2",
            n=1,
            size=ImageSize.SIZE_512,
            quality=ImageQuality.STANDARD,
        )

        assert request.prompt == "A white siamese cat"
        assert request.model == "dall-e-2"
        assert request.size == ImageSize.SIZE_512
        assert request.quality == ImageQuality.STANDARD

    def test_dalle_3_request(self):
        """Test DALL-E 3 compatible request."""
        from fakeai.models import (
            ImageGenerationRequest,
            ImageQuality,
            ImageSize,
            ImageStyle,
        )

        # DALL-E 3 supports larger sizes, HD quality, and style
        request = ImageGenerationRequest(
            prompt="A futuristic robot in a cyberpunk city",
            model="dall-e-3",
            n=1,
            size=ImageSize.SIZE_1792_1024,
            quality=ImageQuality.HD,
            style=ImageStyle.VIVID,
        )

        assert request.prompt == "A futuristic robot in a cyberpunk city"
        assert request.model == "dall-e-3"
        assert request.size == ImageSize.SIZE_1792_1024
        assert request.quality == ImageQuality.HD
        assert request.style == ImageStyle.VIVID

    def test_stable_diffusion_request(self):
        """Test Stable Diffusion compatible request."""
        from fakeai.models import ImageGenerationRequest, ImageSize

        # Stable Diffusion uses default model
        request = ImageGenerationRequest(
            prompt="A majestic mountain landscape at sunset",
            n=4,
            size=ImageSize.SIZE_1024,
        )

        assert request.prompt == "A majestic mountain landscape at sunset"
        assert request.model == "stabilityai/stable-diffusion-2-1"
        assert request.n == 4
        assert request.size == ImageSize.SIZE_1024
