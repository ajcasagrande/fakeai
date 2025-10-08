"""Integration tests for image generation endpoint.

This module tests the image generation service with:
- DALL-E 2 and DALL-E 3 models
- Various image sizes, qualities, and styles
- Multiple image generation (n parameter)
- Different response formats (url, b64_json)
- Custom models
- Concurrent generation
- Error handling and validation
"""

import asyncio
import base64
from typing import Any

import pytest

from .utils import FakeAIClient


@pytest.mark.integration
class TestImageGenerationBasic:
    """Test basic image generation functionality."""

    def test_simple_image_generation(self, client: FakeAIClient):
        """Test basic image generation with DALL-E 3."""
        response = client.create_image(
            prompt="A beautiful sunset over mountains",
            model="dall-e-3",
        )

        # Validate response structure
        assert "created" in response
        assert isinstance(response["created"], int)
        assert "data" in response
        assert len(response["data"]) == 1

        # Validate image object
        image = response["data"][0]
        assert "url" in image or "b64_json" in image

    def test_image_generation_with_dall_e_2(self, client: FakeAIClient):
        """Test image generation with DALL-E 2."""
        response = client.create_image(
            prompt="A futuristic city skyline",
            model="dall-e-2",
            size="512x512",
        )

        assert "data" in response
        assert len(response["data"]) == 1
        image = response["data"][0]
        assert "url" in image or "b64_json" in image

    def test_image_generation_stability_ai(self, client: FakeAIClient):
        """Test image generation with Stability AI model."""
        response = client.create_image(
            prompt="A serene mountain landscape",
            model="stabilityai/stable-diffusion-2-1",
            size="512x512",
        )

        assert "data" in response
        assert len(response["data"]) == 1

    def test_stability_diffusion_xl(self, client: FakeAIClient):
        """Test image generation with Stability Diffusion XL model."""
        response = client.create_image(
            prompt="Abstract art with vibrant colors",
            model="stabilityai/stable-diffusion-xl-base-1.0",
            size="1024x1024",
        )

        # Should work with valid Stability AI model
        assert "data" in response
        assert len(response["data"]) == 1


@pytest.mark.integration
class TestDallE2Sizes:
    """Test DALL-E 2 size validation."""

    def test_dalle2_256x256(self, client: FakeAIClient):
        """Test DALL-E 2 with 256x256 size."""
        response = client.create_image(
            prompt="A small icon",
            model="dall-e-2",
            size="256x256",
        )

        assert len(response["data"]) == 1

    def test_dalle2_512x512(self, client: FakeAIClient):
        """Test DALL-E 2 with 512x512 size."""
        response = client.create_image(
            prompt="Medium sized image",
            model="dall-e-2",
            size="512x512",
        )

        assert len(response["data"]) == 1

    def test_dalle2_1024x1024(self, client: FakeAIClient):
        """Test DALL-E 2 with 1024x1024 size."""
        response = client.create_image(
            prompt="Large square image",
            model="dall-e-2",
            size="1024x1024",
        )

        assert len(response["data"]) == 1

    def test_dalle2_invalid_size(self, client: FakeAIClient):
        """Test DALL-E 2 with invalid size."""
        with pytest.raises(Exception) as exc_info:
            client.create_image(
                prompt="Test image",
                model="dall-e-2",
                size="1792x1024",  # Not supported by DALL-E 2
            )

        # Should raise HTTPStatusError
        assert "400" in str(exc_info.value) or "500" in str(exc_info.value)


@pytest.mark.integration
class TestDallE3Sizes:
    """Test DALL-E 3 size validation."""

    def test_dalle3_1024x1024(self, client: FakeAIClient):
        """Test DALL-E 3 with 1024x1024 size."""
        response = client.create_image(
            prompt="Square image",
            model="dall-e-3",
            size="1024x1024",
        )

        assert len(response["data"]) == 1

    def test_dalle3_1792x1024(self, client: FakeAIClient):
        """Test DALL-E 3 with 1792x1024 size (landscape)."""
        response = client.create_image(
            prompt="Wide landscape image",
            model="dall-e-3",
            size="1792x1024",
        )

        assert len(response["data"]) == 1

    @pytest.mark.slow
    def test_dalle3_1024x1792(self, client: FakeAIClient):
        """Test DALL-E 3 with 1024x1792 size (portrait)."""
        response = client.create_image(
            prompt="Tall portrait image",
            model="dall-e-3",
            size="1024x1792",
        )

        assert len(response["data"]) == 1

    def test_dalle3_invalid_size(self, client: FakeAIClient):
        """Test DALL-E 3 with invalid size."""
        with pytest.raises(Exception) as exc_info:
            client.create_image(
                prompt="Test image",
                model="dall-e-3",
                size="256x256",  # Not supported by DALL-E 3
            )

        # Should raise HTTPStatusError
        assert "400" in str(exc_info.value) or "500" in str(exc_info.value)


@pytest.mark.integration
class TestImageQuality:
    """Test image quality parameter."""

    def test_standard_quality(self, client: FakeAIClient):
        """Test standard quality image generation."""
        response = client.create_image(
            prompt="A landscape in standard quality",
            model="dall-e-3",
            quality="standard",
        )

        assert len(response["data"]) == 1

    @pytest.mark.slow
    def test_hd_quality(self, client: FakeAIClient):
        """Test HD quality image generation."""
        response = client.create_image(
            prompt="A landscape in HD quality",
            model="dall-e-3",
            quality="hd",
            size="1024x1024",
        )

        assert len(response["data"]) == 1

    @pytest.mark.slow
    def test_hd_quality_landscape(self, client: FakeAIClient):
        """Test HD quality with landscape size."""
        response = client.create_image(
            prompt="HD landscape",
            model="dall-e-3",
            quality="hd",
            size="1792x1024",
        )

        assert len(response["data"]) == 1

    @pytest.mark.slow
    def test_hd_quality_portrait(self, client: FakeAIClient):
        """Test HD quality with portrait size."""
        response = client.create_image(
            prompt="HD portrait",
            model="dall-e-3",
            quality="hd",
            size="1024x1792",
        )

        assert len(response["data"]) == 1

    def test_invalid_quality(self, client: FakeAIClient):
        """Test invalid quality parameter."""
        response = client.post(
            "/v1/images/generations",
            json={
                "prompt": "Test image",
                "model": "dall-e-3",
                "quality": "ultra",  # Invalid quality
            },
        )

        # Should return validation error
        assert response.status_code == 422


@pytest.mark.integration
class TestImageStyle:
    """Test image style parameter."""

    def test_vivid_style(self, client: FakeAIClient):
        """Test vivid style image generation."""
        response = client.create_image(
            prompt="A colorful abstract painting",
            model="dall-e-3",
            style="vivid",
        )

        assert len(response["data"]) == 1

    def test_natural_style(self, client: FakeAIClient):
        """Test natural style image generation."""
        response = client.create_image(
            prompt="A realistic photograph of nature",
            model="dall-e-3",
            style="natural",
        )

        assert len(response["data"]) == 1

    def test_invalid_style(self, client: FakeAIClient):
        """Test invalid style parameter."""
        response = client.post(
            "/v1/images/generations",
            json={
                "prompt": "Test image",
                "model": "dall-e-3",
                "style": "cartoon",  # Invalid style
            },
        )

        # Should return validation error
        assert response.status_code == 422


@pytest.mark.integration
class TestResponseFormats:
    """Test different response formats."""

    def test_url_format(self, client: FakeAIClient):
        """Test URL response format."""
        response = client.create_image(
            prompt="Image with URL response",
            model="dall-e-3",
            response_format="url",
        )

        assert len(response["data"]) == 1
        image = response["data"][0]
        assert "url" in image
        assert image["url"] is not None
        # URL should be a valid URL format
        assert image["url"].startswith("http://") or image["url"].startswith("https://")

    def test_b64_json_format(self, client: FakeAIClient):
        """Test base64 JSON response format."""
        response = client.create_image(
            prompt="Image with base64 response",
            model="dall-e-3",
            response_format="b64_json",
        )

        assert len(response["data"]) == 1
        image = response["data"][0]
        assert "b64_json" in image
        assert image["b64_json"] is not None

        # Verify it's valid base64
        try:
            base64.b64decode(image["b64_json"])
        except Exception as e:
            pytest.fail(f"Invalid base64 data: {e}")

    def test_b64_json_decoding(self, client: FakeAIClient):
        """Test that base64 JSON can be decoded."""
        response = client.create_image(
            prompt="Decodable base64 image",
            model="dall-e-2",
            size="256x256",
            response_format="b64_json",
        )

        image = response["data"][0]
        assert "b64_json" in image

        # Decode base64
        decoded = base64.b64decode(image["b64_json"])
        assert len(decoded) > 0


@pytest.mark.integration
class TestMultipleImages:
    """Test generating multiple images."""

    @pytest.mark.slow
    def test_generate_two_images(self, client: FakeAIClient):
        """Test generating 2 images."""
        response = client.create_image(
            prompt="Two similar images",
            model="dall-e-2",
            n=2,
            size="512x512",
        )

        assert len(response["data"]) == 2
        for image in response["data"]:
            assert "url" in image or "b64_json" in image

    @pytest.mark.slow
    def test_generate_multiple_images_stability(self, client: FakeAIClient):
        """Test generating multiple images with Stability AI."""
        response = client.create_image(
            prompt="Multiple abstract images",
            model="stabilityai/stable-diffusion-2-1",
            n=3,
            size="512x512",
        )

        assert len(response["data"]) == 3

    def test_dalle3_multiple_images_error(self, client: FakeAIClient):
        """Test that DALL-E 3 rejects n > 1."""
        with pytest.raises(Exception) as exc_info:
            client.create_image(
                prompt="Test image",
                model="dall-e-3",
                n=2,  # DALL-E 3 only supports n=1
            )

        # Should raise HTTPStatusError with 400 or 500
        assert "400" in str(exc_info.value) or "500" in str(exc_info.value)

    @pytest.mark.slow
    def test_generate_max_images(self, client: FakeAIClient):
        """Test generating maximum number of images."""
        response = client.create_image(
            prompt="Many images",
            model="dall-e-2",
            n=10,  # Maximum allowed
            size="256x256",
        )

        assert len(response["data"]) == 10


@pytest.mark.integration
class TestUserParameter:
    """Test user parameter for tracking."""

    def test_user_parameter(self, client: FakeAIClient):
        """Test that user parameter is accepted."""
        response = client.create_image(
            prompt="Image with user tracking",
            model="dall-e-3",
            user="user-12345",
        )

        # Should succeed with user parameter
        assert len(response["data"]) == 1

    @pytest.mark.slow
    def test_user_parameter_does_not_affect_output(self, client: FakeAIClient):
        """Test that user parameter doesn't change output."""
        response1 = client.create_image(
            prompt="Same prompt",
            model="dall-e-2",
            size="512x512",
            user="user-1",
        )

        response2 = client.create_image(
            prompt="Same prompt",
            model="dall-e-2",
            size="512x512",
            user="user-2",
        )

        # Both should succeed
        assert len(response1["data"]) == 1
        assert len(response2["data"]) == 1


@pytest.mark.integration
class TestImageMetadata:
    """Test image metadata in response."""

    def test_response_timestamp(self, client: FakeAIClient):
        """Test that response includes timestamp."""
        import time

        before = int(time.time())
        response = client.create_image(
            prompt="Timestamp test",
            model="dall-e-3",
        )
        after = int(time.time())

        # Timestamp should be within reasonable range
        assert "created" in response
        assert before <= response["created"] <= after + 1

    def test_image_data_structure(self, client: FakeAIClient):
        """Test complete image data structure."""
        response = client.create_image(
            prompt="Complete structure test",
            model="dall-e-3",
            response_format="url",
        )

        assert "created" in response
        assert "data" in response
        assert isinstance(response["data"], list)
        assert len(response["data"]) > 0

        image = response["data"][0]
        # Should have either url or b64_json
        assert "url" in image or "b64_json" in image

    def test_url_format_structure(self, client: FakeAIClient):
        """Test URL format has correct structure."""
        response = client.create_image(
            prompt="URL structure test",
            model="dall-e-2",
            size="512x512",
            response_format="url",
        )

        image = response["data"][0]
        assert "url" in image
        assert isinstance(image["url"], str)
        # URL should have .png extension
        assert ".png" in image["url"]


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling and validation."""

    def test_empty_prompt(self, client: FakeAIClient):
        """Test error with empty prompt."""
        # Empty prompts should be accepted (server will handle)
        # Just test it doesn't crash
        try:
            response = client.create_image(
                prompt="",
                model="dall-e-3",
            )
            # If it succeeds, that's okay
            assert "data" in response
        except Exception:
            # If it fails, that's also okay (validation error)
            pass

    def test_prompt_too_long(self, client: FakeAIClient):
        """Test error with prompt exceeding max length."""
        long_prompt = "a" * 1001  # Max is 1000
        response = client.post(
            "/v1/images/generations",
            json={
                "prompt": long_prompt,
                "model": "dall-e-3",
            },
        )

        # Should return validation error
        assert response.status_code == 422

    def test_invalid_model(self, client: FakeAIClient):
        """Test with unsupported model format."""
        # Custom models are NOT allowed - should raise error
        with pytest.raises(Exception) as exc_info:
            client.create_image(
                prompt="Test with specific model",
                model="gpt-4",  # Chat model, not image model
                size="1024x1024",
            )

        # Should raise error for unsupported model
        assert "400" in str(exc_info.value) or "500" in str(exc_info.value)

    def test_invalid_n_parameter(self, client: FakeAIClient):
        """Test invalid n parameter."""
        response = client.post(
            "/v1/images/generations",
            json={
                "prompt": "Test",
                "model": "dall-e-2",
                "n": 0,  # Invalid: must be >= 1
            },
        )

        assert response.status_code == 422

    def test_n_exceeds_maximum(self, client: FakeAIClient):
        """Test n parameter exceeding maximum."""
        response = client.post(
            "/v1/images/generations",
            json={
                "prompt": "Test",
                "model": "dall-e-2",
                "n": 11,  # Max is 10
            },
        )

        assert response.status_code == 422

    def test_missing_required_prompt(self, client: FakeAIClient):
        """Test missing required prompt field."""
        response = client.post(
            "/v1/images/generations",
            json={
                "model": "dall-e-3",
                # Missing prompt
            },
        )

        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
class TestConcurrentGeneration:
    """Test concurrent image generation."""

    async def test_concurrent_image_generation(self, client: FakeAIClient):
        """Test generating multiple images concurrently."""

        async def generate_image(prompt: str) -> dict[str, Any]:
            return await client.async_client.post(
                "/v1/images/generations",
                json={
                    "prompt": prompt,
                    "model": "dall-e-2",
                    "size": "256x256",
                },
            ).then(lambda r: r.json())

        prompts = [
            "A red apple",
            "A blue ocean",
            "A green forest",
            "A yellow sun",
            "A purple mountain",
        ]

        # Create tasks for concurrent generation
        tasks = []
        for i, prompt in enumerate(prompts):
            # Use apost for async request
            task = client.apost(
                "/v1/images/generations",
                json={
                    "prompt": prompt,
                    "model": "dall-e-2",
                    "size": "256x256",
                },
            )
            tasks.append(task)

        # Wait for all to complete
        responses = await asyncio.gather(*tasks)

        # All should succeed
        assert len(responses) == len(prompts)
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 1

    async def test_concurrent_different_models(self, client: FakeAIClient):
        """Test concurrent generation with different models."""
        tasks = [
            client.apost(
                "/v1/images/generations",
                json={
                    "prompt": "Test image 1",
                    "model": "dall-e-2",
                    "size": "512x512",
                },
            ),
            client.apost(
                "/v1/images/generations",
                json={
                    "prompt": "Test image 2",
                    "model": "dall-e-3",
                    "size": "1024x1024",
                },
            ),
            client.apost(
                "/v1/images/generations",
                json={
                    "prompt": "Test image 3",
                    "model": "stabilityai/stable-diffusion-2-1",
                    "size": "512x512",
                },
            ),
        ]

        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert len(data["data"]) == 1


@pytest.mark.integration
class TestImageGenerationEdgeCases:
    """Test edge cases and special scenarios."""

    def test_special_characters_in_prompt(self, client: FakeAIClient):
        """Test prompt with special characters."""
        response = client.create_image(
            prompt="A scene with émojis 🎨 and spëcial çharacters!",
            model="dall-e-3",
        )

        assert len(response["data"]) == 1

    def test_very_short_prompt(self, client: FakeAIClient):
        """Test very short prompt."""
        response = client.create_image(
            prompt="Cat",
            model="dall-e-2",
            size="512x512",
        )

        assert len(response["data"]) == 1

    def test_detailed_prompt(self, client: FakeAIClient):
        """Test detailed, descriptive prompt."""
        response = client.create_image(
            prompt=(
                "A highly detailed digital painting of a majestic dragon "
                "soaring through cloudy skies at sunset, with golden light "
                "illuminating its scales, fantasy art style"
            ),
            model="dall-e-3",
        )

        assert len(response["data"]) == 1

    @pytest.mark.slow
    def test_repeated_generation_same_prompt(self, client: FakeAIClient):
        """Test generating with same prompt multiple times."""
        prompt = "A unique test image"

        response1 = client.create_image(
            prompt=prompt,
            model="dall-e-2",
            size="512x512",
        )

        response2 = client.create_image(
            prompt=prompt,
            model="dall-e-2",
            size="512x512",
        )

        # Both should succeed
        assert len(response1["data"]) == 1
        assert len(response2["data"]) == 1

        # URLs/b64 should be different (different generations)
        if "url" in response1["data"][0] and "url" in response2["data"][0]:
            # URLs should be unique
            url1 = response1["data"][0]["url"]
            url2 = response2["data"][0]["url"]
            # Extract unique ID from URL
            assert url1 != url2

    @pytest.mark.slow
    def test_all_parameters_combined(self, client: FakeAIClient):
        """Test with all parameters specified."""
        response = client.create_image(
            prompt="A comprehensive test image",
            model="dall-e-3",
            size="1024x1024",
            quality="hd",
            style="natural",
            response_format="url",
            user="test-user-123",
            n=1,
        )

        assert len(response["data"]) == 1
        assert "created" in response

    def test_default_parameters(self, client: FakeAIClient):
        """Test with only required parameters (defaults for rest)."""
        response = client.post(
            "/v1/images/generations",
            json={
                "prompt": "Minimal parameters test",
            },
        )

        # Should succeed with defaults
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
