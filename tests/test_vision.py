"""
Unit tests for vision token calculation module.
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest

from fakeai.vision import (
    calculate_image_tokens,
    calculate_message_image_tokens,
    extract_image_content,
    parse_image_dimensions_from_url,
)


class TestCalculateImageTokens:
    """Test image token calculation using OpenAI's formula."""

    def test_low_detail_fixed_tokens(self):
        """Low detail should always return 85 tokens regardless of size."""
        assert calculate_image_tokens(100, 100, "low", "openai/gpt-oss-120b") == 85
        assert calculate_image_tokens(512, 512, "low", "openai/gpt-oss-120b") == 85
        assert calculate_image_tokens(2048, 2048, "low", "openai/gpt-oss-120b") == 85
        assert calculate_image_tokens(4096, 4096, "low", "openai/gpt-oss-120b") == 85

    def test_high_detail_single_tile(self):
        """High detail for small images."""
        # Images get scaled to 768px on shortest side, then tiled
        # 512×512 -> 768×768 = 2×2 = 4 tiles = 765 tokens
        assert calculate_image_tokens(512, 512, "high", "openai/gpt-oss-120b") == 765
        # 256×256 -> 768×768 = 2×2 = 4 tiles = 765 tokens
        assert calculate_image_tokens(256, 256, "high", "openai/gpt-oss-120b") == 765
        # 400×300 -> 1024×768 = 2×2 = 4 tiles = 765 tokens
        assert calculate_image_tokens(400, 300, "high", "openai/gpt-oss-120b") == 765

    def test_high_detail_single_tile_mini(self):
        """High detail for small images on openai/gpt-oss-20b."""
        # openai/gpt-oss-20b: scaled to 768px shortest side
        # 512×512 -> 768×768 = 2×2 = 4 tiles: 2833 + (5667 × 4) = 25501
        assert calculate_image_tokens(512, 512, "high", "openai/gpt-oss-20b") == 25501
        # 256×256 -> 768×768 = 2×2 = 4 tiles: 2833 + (5667 × 4) = 25501
        assert calculate_image_tokens(256, 256, "high", "openai/gpt-oss-20b") == 25501

    def test_high_detail_multiple_tiles(self):
        """High detail for larger images requiring multiple tiles."""
        # 1024×1024: shortest=1024, scale to 768: 768×768 = 2×2 = 4 tiles
        # openai/gpt-oss-120b: 85 + (170 × 4) = 765
        assert calculate_image_tokens(1024, 1024, "high", "openai/gpt-oss-120b") == 765

        # 2048×1024: shortest=1024, scale to 768: 1536×768 = 3×2 = 6 tiles
        # openai/gpt-oss-120b: 85 + (170 × 6) = 1105
        assert calculate_image_tokens(2048, 1024, "high", "openai/gpt-oss-120b") == 1105

        # 2048×2048: shortest=2048, scale to 768: 768×768 = 2×2 = 4 tiles
        # openai/gpt-oss-120b: 85 + (170 × 4) = 765
        assert calculate_image_tokens(2048, 2048, "high", "openai/gpt-oss-120b") == 765

    def test_high_detail_multiple_tiles_mini(self):
        """High detail for larger images on openai/gpt-oss-20b."""
        # 1024×1024: shortest=1024, scale to 768: 768×768 = 2×2 = 4 tiles
        # openai/gpt-oss-20b: 2833 + (5667 × 4) = 25501
        assert calculate_image_tokens(1024, 1024, "high", "openai/gpt-oss-20b") == 25501

    def test_high_detail_wide_image(self):
        """High detail for wide rectangular images."""
        # 3000×500 → scales to 2048×341 → then scale shortest (341) to 768: ~4607×768
        # Tiles: 10×2 = 20 tiles (ceil(4607/512) × ceil(768/512))
        # openai/gpt-oss-120b: 85 + (170 × 20) = 3485
        result = calculate_image_tokens(3000, 500, "high", "openai/gpt-oss-120b")
        assert result == 3485

    def test_high_detail_tall_image(self):
        """High detail for tall rectangular images."""
        # 500×3000 → scales to 341×2048 → then scale shortest (341) to 768: 768×~4607
        # Tiles: 2×10 = 20 tiles
        # openai/gpt-oss-120b: 85 + (170 × 20) = 3485
        result = calculate_image_tokens(500, 3000, "high", "openai/gpt-oss-120b")
        assert result == 3485

    def test_high_detail_very_large_image(self):
        """High detail for very large images requiring initial downscaling."""
        # 4096×4096 → scales to 2048×2048 → then scale shortest (2048) to 768: 768×768
        # Tiles: 2×2 = 4 tiles
        # openai/gpt-oss-120b: 85 + (170 × 4) = 765
        assert calculate_image_tokens(4096, 4096, "high", "openai/gpt-oss-120b") == 765

    def test_auto_detail_small_image_uses_low(self):
        """Auto detail should use low for small images."""
        # Images under 512×512 should use low detail (85 tokens)
        assert calculate_image_tokens(256, 256, "auto", "openai/gpt-oss-120b") == 85
        assert calculate_image_tokens(512, 512, "auto", "openai/gpt-oss-120b") == 85
        assert calculate_image_tokens(400, 500, "auto", "openai/gpt-oss-120b") == 85

    def test_auto_detail_large_image_uses_high(self):
        """Auto detail should use high for large images."""
        # Images over 512×512 should use high detail
        # 1024×1024: scales to 768×768 = 4 tiles = 765 tokens
        assert calculate_image_tokens(1024, 1024, "auto", "openai/gpt-oss-120b") == 765
        # 2048×2048: scales to 768×768 = 4 tiles = 765 tokens
        assert calculate_image_tokens(2048, 2048, "auto", "openai/gpt-oss-120b") == 765


class TestParseImageDimensionsFromUrl:
    """Test URL dimension parsing."""

    def test_data_uri_with_dimension_hint(self):
        """Data URI with dimension hint in metadata."""
        url = "data:image/png;dim=800x600;base64,iVBORw0KG..."
        assert parse_image_dimensions_from_url(url) == (800, 600)

    def test_data_uri_without_hint(self):
        """Data URI without dimension hint defaults to 1024×1024."""
        url = "data:image/png;base64,iVBORw0KG..."
        assert parse_image_dimensions_from_url(url) == (1024, 1024)

    def test_url_with_query_parameters(self):
        """URL with width and height query parameters."""
        url = "https://example.com/image.png?width=1920&height=1080"
        assert parse_image_dimensions_from_url(url) == (1920, 1080)

    def test_url_with_dimensions_in_path(self):
        """URL with dimensions in the path."""
        url = "https://example.com/images/1280x720/photo.jpg"
        assert parse_image_dimensions_from_url(url) == (1280, 720)

    def test_url_without_hints_defaults(self):
        """URL without dimension hints defaults to 1024×1024."""
        url = "https://example.com/photo.jpg"
        assert parse_image_dimensions_from_url(url) == (1024, 1024)

    def test_simulated_url_format(self):
        """Simulated URLs with dimensions in filename."""
        url = "https://simulated-openai-images.example.com/2048x1024_abc123.png"
        assert parse_image_dimensions_from_url(url) == (2048, 1024)


class TestExtractImageContent:
    """Test image content extraction from messages."""

    def test_none_content(self):
        """None content returns empty list."""
        assert extract_image_content(None) == []

    def test_string_content(self):
        """String content returns empty list (no images)."""
        assert extract_image_content("Hello world") == []

    def test_empty_list(self):
        """Empty list returns empty list."""
        assert extract_image_content([]) == []

    def test_text_only_content(self):
        """Content with only text parts returns empty list."""
        content = [
            {"type": "text", "text": "Hello"},
            {"type": "text", "text": "World"},
        ]
        assert extract_image_content(content) == []

    def test_single_image_dict_format(self):
        """Extract single image from dict format."""
        content = [
            {"type": "text", "text": "What's in this image?"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/photo.jpg",
                    "detail": "high",
                },
            },
        ]
        images = extract_image_content(content)
        assert len(images) == 1
        assert images[0]["url"] == "https://example.com/photo.jpg"
        assert images[0]["detail"] == "high"

    def test_single_image_auto_detail(self):
        """Image without explicit detail defaults to auto."""
        content = [
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/photo.jpg",
                },
            },
        ]
        images = extract_image_content(content)
        assert len(images) == 1
        assert images[0]["detail"] == "auto"

    def test_multiple_images(self):
        """Extract multiple images from content."""
        content = [
            {"type": "text", "text": "Compare these images:"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/image1.jpg",
                    "detail": "high",
                },
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/image2.jpg",
                    "detail": "low",
                },
            },
        ]
        images = extract_image_content(content)
        assert len(images) == 2
        assert images[0]["url"] == "https://example.com/image1.jpg"
        assert images[0]["detail"] == "high"
        assert images[1]["url"] == "https://example.com/image2.jpg"
        assert images[1]["detail"] == "low"

    def test_image_with_data_uri(self):
        """Extract image with data URI."""
        content = [
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/png;dim=800x600;base64,iVBORw0KG...",
                    "detail": "high",
                },
            },
        ]
        images = extract_image_content(content)
        assert len(images) == 1
        assert images[0]["url"].startswith("data:image/png")

    def test_pydantic_model_format(self):
        """Test extraction from Pydantic model instances."""

        # Simulate Pydantic model with attributes
        class MockImageUrl:
            def __init__(self, url, detail="auto"):
                self.url = url
                self.detail = detail

        class MockImageContent:
            def __init__(self, url, detail="auto"):
                self.type = "image_url"
                self.image_url = MockImageUrl(url, detail)

        content = [
            MockImageContent("https://example.com/photo.jpg", "high"),
        ]
        images = extract_image_content(content)
        assert len(images) == 1
        assert images[0]["url"] == "https://example.com/photo.jpg"
        assert images[0]["detail"] == "high"


class TestCalculateMessageImageTokens:
    """Test total image token calculation for messages."""

    def test_no_images(self):
        """Message without images returns 0 tokens."""
        content = "Hello, how are you?"
        assert calculate_message_image_tokens(content, "openai/gpt-oss-120b") == 0

        content = [{"type": "text", "text": "Hello"}]
        assert calculate_message_image_tokens(content, "openai/gpt-oss-120b") == 0

    def test_single_image_low_detail(self):
        """Single low detail image."""
        content = [
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/photo.jpg",
                    "detail": "low",
                },
            },
        ]
        # Low detail = 85 tokens
        assert calculate_message_image_tokens(content, "openai/gpt-oss-120b") == 85

    def test_single_image_high_detail(self):
        """Single high detail image with known dimensions."""
        content = [
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/1024x1024/photo.jpg",
                    "detail": "high",
                },
            },
        ]
        # 1024×1024: 4 tiles = 765 tokens (openai/gpt-oss-120b)
        assert calculate_message_image_tokens(content, "openai/gpt-oss-120b") == 765

    def test_multiple_images(self):
        """Multiple images with different details."""
        content = [
            {"type": "text", "text": "Compare these:"},
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/512x512/img1.jpg",
                    "detail": "high",
                },
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/img2.jpg",
                    "detail": "low",
                },
            },
        ]
        # First image: 512×512 high -> 768×768 = 4 tiles = 765 tokens
        # Second image: low = 85 tokens
        # Total: 850 tokens
        assert calculate_message_image_tokens(content, "openai/gpt-oss-120b") == 850

    def test_gpt_4o_mini_higher_costs(self):
        """openai/gpt-oss-20b has higher token costs."""
        content = [
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/512x512/photo.jpg",
                    "detail": "high",
                },
            },
        ]
        # 512×512 scaled to 768×768 = 4 tiles on openai/gpt-oss-20b: 2833 + (5667 × 4) = 25501
        assert calculate_message_image_tokens(content, "openai/gpt-oss-20b") == 25501

        # Same image on openai/gpt-oss-120b: 85 + (170 × 4) = 765
        assert calculate_message_image_tokens(content, "openai/gpt-oss-120b") == 765

    def test_auto_detail_selection(self):
        """Auto detail selection based on image size."""
        # Small image - should use low detail (85 tokens)
        content_small = [
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/400x400/small.jpg",
                    "detail": "auto",
                },
            },
        ]
        assert (
            calculate_message_image_tokens(content_small, "openai/gpt-oss-120b") == 85
        )

        # Large image - should use high detail
        content_large = [
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://example.com/1024x1024/large.jpg",
                    "detail": "auto",
                },
            },
        ]
        assert (
            calculate_message_image_tokens(content_large, "openai/gpt-oss-120b") == 765
        )

    def test_data_uri_with_dimensions(self):
        """Data URI with dimension hints."""
        content = [
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/png;dim=2048x1024;base64,iVBORw0KG...",
                    "detail": "high",
                },
            },
        ]
        # 2048×1024: shortest=1024, scale to 768: 1536×768 = 3×2 = 6 tiles = 1105 tokens
        assert calculate_message_image_tokens(content, "openai/gpt-oss-120b") == 1105


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_image(self):
        """Very small images get scaled up."""
        # 1×1: shortest=1, scale to 768: 768×768 = 2×2 = 4 tiles = 765 tokens
        assert calculate_image_tokens(1, 1, "high", "openai/gpt-oss-120b") == 765

    def test_exact_tile_boundaries(self):
        """Images at various boundaries."""
        # 512×512: scales to 768×768 = 2×2 = 4 tiles = 765 tokens
        assert calculate_image_tokens(512, 512, "high", "openai/gpt-oss-120b") == 765
        # 1024×512: shortest=512, scale to 768: 1536×768 = 3×2 = 6 tiles = 1105 tokens
        assert calculate_image_tokens(1024, 512, "high", "openai/gpt-oss-120b") == 1105

    def test_aspect_ratio_preservation(self):
        """Verify aspect ratio is considered in scaling."""
        # 4000×2000 (2:1): scale to 2048×1024, then shortest (1024) to 768: 1536×768
        # Tiles: 3×2 = 6 tiles = 1105 tokens
        assert calculate_image_tokens(4000, 2000, "high", "openai/gpt-oss-120b") == 1105

    def test_malformed_url_defaults(self):
        """Malformed URLs default to 1024×1024."""
        result = parse_image_dimensions_from_url("not-a-url")
        assert result == (1024, 1024)

    def test_empty_image_list(self):
        """Empty image list in content."""
        content = [{"type": "text", "text": "No images here"}]
        assert calculate_message_image_tokens(content, "openai/gpt-oss-120b") == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
