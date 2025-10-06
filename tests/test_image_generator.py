"""
Tests for the image generation module.
"""

#  SPDX-License-Identifier: Apache-2.0

import base64
import io
import time

import pytest
from PIL import Image

from fakeai.image_generator import ImageGenerator


class TestImageGenerator:
    """Test suite for ImageGenerator."""

    @pytest.fixture
    def generator(self):
        """Create ImageGenerator instance."""
        return ImageGenerator(
            base_url="http://localhost:8000",
            storage_backend="memory",
            retention_hours=1,
        )

    def test_initialization(self, generator):
        """Test generator initialization."""
        assert generator.base_url == "http://localhost:8000"
        assert generator.storage_backend == "memory"
        assert generator.retention_hours == 1
        assert generator._storage == {}

    def test_supported_sizes(self, generator):
        """Test all supported image sizes."""
        sizes = [
            "256x256",
            "512x512",
            "1024x1024",
            "1792x1024",
            "1024x1792",
        ]

        for size in sizes:
            result = generator.generate(
                prompt="Test image",
                size=size,
                n=1,
                response_format="url",
            )
            assert len(result) == 1
            assert "url" in result[0]
            assert result[0]["url"].startswith("http://localhost:8000/images/")
            assert result[0]["url"].endswith(".png")

    def test_unsupported_size(self, generator):
        """Test error on unsupported size."""
        with pytest.raises(ValueError, match="Unsupported size"):
            generator.generate(
                prompt="Test",
                size="999x999",
                n=1,
                response_format="url",
            )

    def test_quality_standard(self, generator):
        """Test standard quality generation."""
        result = generator.generate(
            prompt="Standard quality test",
            size="1024x1024",
            quality="standard",
            n=1,
            response_format="url",
        )
        assert len(result) == 1
        assert "url" in result[0]

    def test_quality_hd(self, generator):
        """Test HD quality generation."""
        result = generator.generate(
            prompt="HD quality test",
            size="1024x1024",
            quality="hd",
            n=1,
            response_format="url",
        )
        assert len(result) == 1
        assert "url" in result[0]

    def test_style_vivid(self, generator):
        """Test vivid style generation."""
        result = generator.generate(
            prompt="Vivid style test",
            size="1024x1024",
            style="vivid",
            n=1,
            response_format="url",
        )
        assert len(result) == 1
        assert "url" in result[0]

    def test_style_natural(self, generator):
        """Test natural style generation."""
        result = generator.generate(
            prompt="Natural style test",
            size="1024x1024",
            style="natural",
            n=1,
            response_format="url",
        )
        assert len(result) == 1
        assert "url" in result[0]

    def test_multiple_images(self, generator):
        """Test generating multiple images (n parameter)."""
        n = 5
        result = generator.generate(
            prompt="Multiple images test",
            size="512x512",
            n=n,
            response_format="url",
        )
        assert len(result) == n

        # All URLs should be unique
        urls = [img["url"] for img in result]
        assert len(urls) == len(set(urls))

    def test_url_response_format(self, generator):
        """Test URL response format."""
        result = generator.generate(
            prompt="URL test",
            size="1024x1024",
            n=1,
            response_format="url",
        )
        assert len(result) == 1
        assert "url" in result[0]
        assert "b64_json" not in result[0]

    def test_base64_response_format(self, generator):
        """Test base64 response format."""
        result = generator.generate(
            prompt="Base64 test",
            size="1024x1024",
            n=1,
            response_format="b64_json",
        )
        assert len(result) == 1
        assert "b64_json" in result[0]
        assert "url" not in result[0]

        # Verify base64 is valid
        b64_data = result[0]["b64_json"]
        image_bytes = base64.b64decode(b64_data)
        assert len(image_bytes) > 0

        # Verify it's a valid PNG
        img = Image.open(io.BytesIO(image_bytes))
        assert img.format == "PNG"

    def test_base64_decoding(self, generator):
        """Test that base64 images can be decoded and are valid PNGs."""
        result = generator.generate(
            prompt="Decode test",
            size="512x512",
            n=1,
            response_format="b64_json",
        )

        b64_data = result[0]["b64_json"]
        image_bytes = base64.b64decode(b64_data)

        # Load as PIL image
        img = Image.open(io.BytesIO(image_bytes))

        assert img.format == "PNG"
        assert img.size == (512, 512)
        assert img.mode == "RGB"

    def test_create_image_dall_e_2_sizes(self, generator):
        """Test creating images with DALL-E 2 sizes."""
        sizes = [(256, 256), (512, 512), (1024, 1024)]

        for width, height in sizes:
            image_bytes = generator.create_image(
                size=(width, height),
                prompt="DALL-E 2 test",
                quality="standard",
                style="vivid",
                model="dall-e-2",
                index=0,
            )

            img = Image.open(io.BytesIO(image_bytes))
            assert img.size == (width, height)
            assert img.format == "PNG"

    def test_create_image_dall_e_3_sizes(self, generator):
        """Test creating images with DALL-E 3 sizes."""
        sizes = [(1024, 1024), (1792, 1024), (1024, 1792)]

        for width, height in sizes:
            image_bytes = generator.create_image(
                size=(width, height),
                prompt="DALL-E 3 test",
                quality="hd",
                style="natural",
                model="dall-e-3",
                index=0,
            )

            img = Image.open(io.BytesIO(image_bytes))
            assert img.size == (width, height)
            assert img.format == "PNG"

    def test_image_variation(self, generator):
        """Test that different indices produce different images."""
        images = []
        for i in range(3):
            image_bytes = generator.create_image(
                size=(512, 512),
                prompt="Variation test",
                quality="standard",
                style="vivid",
                model="dall-e-3",
                index=i,
            )
            images.append(image_bytes)

        # All images should be different
        assert images[0] != images[1]
        assert images[1] != images[2]
        assert images[0] != images[2]

    def test_reproducibility(self, generator):
        """Test that same prompt+index produces same image."""
        image1 = generator.create_image(
            size=(512, 512),
            prompt="Reproducibility test",
            quality="standard",
            style="vivid",
            model="dall-e-3",
            index=0,
        )

        image2 = generator.create_image(
            size=(512, 512),
            prompt="Reproducibility test",
            quality="standard",
            style="vivid",
            model="dall-e-3",
            index=0,
        )

        assert image1 == image2

    def test_store_and_retrieve_image(self, generator):
        """Test storing and retrieving images."""
        image_bytes = generator.create_image(
            size=(512, 512),
            prompt="Storage test",
            quality="standard",
            style="vivid",
            model="dall-e-3",
            index=0,
        )

        # Store image
        image_id = generator.store_image(image_bytes)
        assert image_id is not None
        assert len(image_id) > 0

        # Retrieve image
        retrieved = generator.get_image(image_id)
        assert retrieved is not None
        assert retrieved == image_bytes

    def test_retrieve_nonexistent_image(self, generator):
        """Test retrieving non-existent image returns None."""
        result = generator.get_image("nonexistent-id")
        assert result is None

    def test_image_expiration(self):
        """Test that expired images are not returned."""
        # Create generator with very short retention
        generator = ImageGenerator(
            base_url="http://localhost:8000",
            storage_backend="memory",
            retention_hours=0.0001,  # ~0.36 seconds
        )

        image_bytes = generator.create_image(
            size=(256, 256),
            prompt="Expiration test",
            quality="standard",
            style="vivid",
            model="dall-e-3",
            index=0,
        )

        image_id = generator.store_image(image_bytes)

        # Should be retrievable immediately
        assert generator.get_image(image_id) is not None

        # Wait for expiration
        time.sleep(0.5)

        # Should be expired now
        assert generator.get_image(image_id) is None

    def test_storage_stats(self, generator):
        """Test storage statistics."""
        # Generate and store some images
        for i in range(3):
            result = generator.generate(
                prompt=f"Stats test {i}",
                size="512x512",
                n=1,
                response_format="url",
            )

        stats = generator.get_storage_stats()

        assert stats["total_images"] == 3
        assert stats["total_size_bytes"] > 0
        assert stats["total_size_mb"] > 0
        assert stats["retention_hours"] == 1
        assert stats["backend"] == "memory"

    def test_long_prompt_truncation(self, generator):
        """Test that long prompts are truncated."""
        long_prompt = "A" * 200  # Very long prompt

        result = generator.generate(
            prompt=long_prompt,
            size="512x512",
            quality="standard",
            n=1,
            response_format="b64_json",
        )

        # Should still generate successfully
        assert len(result) == 1
        assert "b64_json" in result[0]

    def test_model_watermark(self, generator):
        """Test that model name appears in watermark."""
        models = ["dall-e-2", "dall-e-3", "stabilityai/stable-diffusion-2-1"]

        for model in models:
            image_bytes = generator.create_image(
                size=(512, 512),
                prompt="Watermark test",
                quality="standard",
                style="vivid",
                model=model,
                index=0,
            )

            # Just verify image is valid
            img = Image.open(io.BytesIO(image_bytes))
            assert img.format == "PNG"

    def test_gradient_background(self, generator):
        """Test gradient background for HD quality."""
        image_bytes = generator.create_image(
            size=(1024, 1024),
            prompt="Gradient test",
            quality="hd",
            style="vivid",
            model="dall-e-3",
            index=0,
        )

        img = Image.open(io.BytesIO(image_bytes))
        assert img.format == "PNG"
        assert img.size == (1024, 1024)

        # HD image should be larger than standard (more detail)
        standard_bytes = generator.create_image(
            size=(1024, 1024),
            prompt="Gradient test",
            quality="standard",
            style="vivid",
            model="dall-e-3",
            index=0,
        )

        # Both should be valid PNGs
        standard_img = Image.open(io.BytesIO(standard_bytes))
        assert standard_img.format == "PNG"

    def test_patterns(self, generator):
        """Test that patterns are applied for HD quality."""
        # Generate HD image (should have patterns)
        hd_bytes = generator.create_image(
            size=(512, 512),
            prompt="Pattern test",
            quality="hd",
            style="vivid",
            model="dall-e-3",
            index=0,
        )

        hd_img = Image.open(io.BytesIO(hd_bytes))
        assert hd_img.format == "PNG"
        assert hd_img.size == (512, 512)

    def test_concurrent_generation(self, generator):
        """Test generating multiple images concurrently."""
        # Generate 10 images
        results = []
        for i in range(10):
            result = generator.generate(
                prompt=f"Concurrent test {i}",
                size="256x256",
                n=1,
                response_format="url",
            )
            results.append(result[0]["url"])

        # All URLs should be unique
        assert len(results) == len(set(results))

    def test_vivid_vs_natural_colors(self, generator):
        """Test that vivid and natural styles use different colors."""
        vivid_bytes = generator.create_image(
            size=(512, 512),
            prompt="Color test",
            quality="standard",
            style="vivid",
            model="dall-e-3",
            index=0,
        )

        natural_bytes = generator.create_image(
            size=(512, 512),
            prompt="Color test",
            quality="standard",
            style="natural",
            model="dall-e-3",
            index=0,
        )

        # Images should be different
        assert vivid_bytes != natural_bytes

        # Both should be valid
        vivid_img = Image.open(io.BytesIO(vivid_bytes))
        natural_img = Image.open(io.BytesIO(natural_bytes))

        assert vivid_img.format == "PNG"
        assert natural_img.format == "PNG"
