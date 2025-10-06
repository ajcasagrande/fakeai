"""
Unit tests for video token calculation module (NVIDIA Cosmos extension).
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest

from fakeai.video import (
    calculate_message_video_tokens,
    estimate_video_tokens,
    extract_video_content,
    parse_video_metadata_from_url,
)


class TestEstimateVideoTokens:
    """Test video token estimation."""

    def test_low_detail_short_video(self):
        """Low detail short video should have minimal tokens."""
        # 5 seconds at 4 fps = 20 frames
        # Low detail: 85 + (20 × 10) = 285 tokens
        tokens = estimate_video_tokens(
            duration_seconds=5.0,
            fps=4.0,
            width=512,
            height=288,
            detail="low",
            model="nvidia/cosmos-reason1-7b",
        )
        assert tokens == 285

    def test_high_detail_small_resolution(self):
        """High detail with small resolution."""
        # 5 seconds at 4 fps = 20 frames
        # 512×288 is 1 tile (< 512×512)
        # High detail: 85 + (20 × (20 + 1×10)) = 85 + 600 = 685 tokens
        tokens = estimate_video_tokens(
            duration_seconds=5.0,
            fps=4.0,
            width=512,
            height=288,
            detail="high",
            model="nvidia/cosmos-reason1-7b",
        )
        assert tokens == 685

    def test_high_detail_large_resolution(self):
        """High detail with larger resolution requires more tokens."""
        # 10 seconds at 8 fps = 80 frames
        # 1024×1024 = 4 tiles (2×2)
        # High detail: 85 + (80 × (20 + 4×10)) = 85 + 4800 = 4885 tokens
        tokens = estimate_video_tokens(
            duration_seconds=10.0,
            fps=8.0,
            width=1024,
            height=1024,
            detail="high",
            model="nvidia/cosmos-reason1-7b",
        )
        assert tokens == 4885

    def test_auto_detail_small_video(self):
        """Auto detail should use low for small videos."""
        # Small resolution (≤512×512) should use low detail
        tokens = estimate_video_tokens(
            duration_seconds=5.0,
            fps=4.0,
            width=512,
            height=288,
            detail="auto",
            model="nvidia/cosmos-reason1-7b",
        )
        # Should match low detail calculation
        assert tokens == 285

    def test_auto_detail_large_video(self):
        """Auto detail should use high for large videos."""
        # Large resolution (>512×512) should use high detail
        tokens = estimate_video_tokens(
            duration_seconds=5.0,
            fps=4.0,
            width=1024,
            height=768,
            detail="auto",
            model="nvidia/cosmos-reason1-7b",
        )
        # Should match high detail calculation
        # 1024×768 = 4 tiles (2×2)
        # 85 + (20 frames × (20 + 4×10)) = 85 + (20 × 60) = 85 + 800 = 885
        assert tokens == 885

    def test_longer_duration(self):
        """Longer videos have proportionally more tokens."""
        # 30 seconds at 24 fps = 720 frames
        # Low detail: 85 + (720 × 10) = 7285 tokens
        tokens = estimate_video_tokens(
            duration_seconds=30.0,
            fps=24.0,
            width=512,
            height=288,
            detail="low",
            model="nvidia/cosmos-reason1-7b",
        )
        assert tokens == 7285

    def test_higher_fps(self):
        """Higher FPS increases token count."""
        # 5 seconds at 30 fps = 150 frames
        # Low detail: 85 + (150 × 10) = 1585 tokens
        tokens = estimate_video_tokens(
            duration_seconds=5.0,
            fps=30.0,
            width=512,
            height=288,
            detail="low",
            model="nvidia/cosmos-reason1-7b",
        )
        assert tokens == 1585


class TestParseVideoMetadataFromUrl:
    """Test video metadata parsing from URLs."""

    def test_query_parameters_full(self):
        """Parse all metadata from query parameters."""
        url = "https://example.com/video.mp4?width=512&height=288&duration=5.0&fps=4"
        metadata = parse_video_metadata_from_url(url)

        assert metadata["width"] == 512
        assert metadata["height"] == 288
        assert metadata["duration"] == 5.0
        assert metadata["fps"] == 4.0

    def test_query_parameters_partial(self):
        """Parse partial metadata with defaults."""
        url = "https://example.com/video.mp4?width=1024&height=768"
        metadata = parse_video_metadata_from_url(url)

        assert metadata["width"] == 1024
        assert metadata["height"] == 768
        assert metadata["duration"] == 5.0  # default
        assert metadata["fps"] == 4.0  # default

    def test_path_encoded_metadata(self):
        """Parse metadata from path."""
        url = "https://example.com/videos/512x288_5.0s_4.0fps/video.mp4"
        metadata = parse_video_metadata_from_url(url)

        assert metadata["width"] == 512
        assert metadata["height"] == 288
        assert metadata["duration"] == 5.0
        assert metadata["fps"] == 4.0

    def test_data_uri_with_metadata(self):
        """Parse metadata from data URI."""
        url = "data:video/mp4;meta=1024x768:10.0s@24fps;base64,AAAAA..."
        metadata = parse_video_metadata_from_url(url)

        assert metadata["width"] == 1024
        assert metadata["height"] == 768
        assert metadata["duration"] == 10.0
        assert metadata["fps"] == 24.0

    def test_data_uri_without_metadata(self):
        """Data URI without metadata uses defaults."""
        url = "data:video/mp4;base64,AAAAA..."
        metadata = parse_video_metadata_from_url(url)

        assert metadata["width"] == 512
        assert metadata["height"] == 288
        assert metadata["duration"] == 5.0
        assert metadata["fps"] == 4.0

    def test_plain_url_uses_defaults(self):
        """Plain URL without hints uses default values."""
        url = "https://example.com/video.mp4"
        metadata = parse_video_metadata_from_url(url)

        assert metadata["width"] == 512
        assert metadata["height"] == 288
        assert metadata["duration"] == 5.0
        assert metadata["fps"] == 4.0


class TestExtractVideoContent:
    """Test video content extraction from messages."""

    def test_none_content(self):
        """None content returns empty list."""
        assert extract_video_content(None) == []

    def test_string_content(self):
        """String content returns empty list (no videos)."""
        assert extract_video_content("Hello world") == []

    def test_empty_list(self):
        """Empty list returns empty list."""
        assert extract_video_content([]) == []

    def test_text_only_content(self):
        """Content with only text parts returns empty list."""
        content = [
            {"type": "text", "text": "Hello"},
            {"type": "text", "text": "World"},
        ]
        assert extract_video_content(content) == []

    def test_single_video_dict_format(self):
        """Extract single video from dict format."""
        content = [
            {"type": "text", "text": "What's in this video?"},
            {
                "type": "video_url",
                "video_url": {
                    "url": "https://example.com/video.mp4",
                    "detail": "high",
                },
            },
        ]
        videos = extract_video_content(content)
        assert len(videos) == 1
        assert videos[0]["url"] == "https://example.com/video.mp4"
        assert videos[0]["detail"] == "high"

    def test_single_video_auto_detail(self):
        """Video without explicit detail defaults to auto."""
        content = [
            {
                "type": "video_url",
                "video_url": {
                    "url": "https://example.com/video.mp4",
                },
            },
        ]
        videos = extract_video_content(content)
        assert len(videos) == 1
        assert videos[0]["detail"] == "auto"

    def test_multiple_videos(self):
        """Extract multiple videos from content."""
        content = [
            {"type": "text", "text": "Compare these videos:"},
            {
                "type": "video_url",
                "video_url": {
                    "url": "https://example.com/video1.mp4",
                    "detail": "high",
                },
            },
            {
                "type": "video_url",
                "video_url": {
                    "url": "https://example.com/video2.mp4",
                    "detail": "low",
                },
            },
        ]
        videos = extract_video_content(content)
        assert len(videos) == 2
        assert videos[0]["url"] == "https://example.com/video1.mp4"
        assert videos[0]["detail"] == "high"
        assert videos[1]["url"] == "https://example.com/video2.mp4"
        assert videos[1]["detail"] == "low"

    def test_pydantic_model_format(self):
        """Test extraction from Pydantic model instances."""

        # Simulate Pydantic model with attributes
        class MockVideoUrl:
            def __init__(self, url, detail="auto"):
                self.url = url
                self.detail = detail

        class MockVideoContent:
            def __init__(self, url, detail="auto"):
                self.type = "video_url"
                self.video_url = MockVideoUrl(url, detail)

        content = [
            MockVideoContent("https://example.com/video.mp4", "high"),
        ]
        videos = extract_video_content(content)
        assert len(videos) == 1
        assert videos[0]["url"] == "https://example.com/video.mp4"
        assert videos[0]["detail"] == "high"


class TestCalculateMessageVideoTokens:
    """Test total video token calculation for messages."""

    def test_no_videos(self):
        """Message without videos returns 0 tokens."""
        content = "Hello, how are you?"
        assert calculate_message_video_tokens(content, "nvidia/cosmos-reason1-7b") == 0

        content = [{"type": "text", "text": "Hello"}]
        assert calculate_message_video_tokens(content, "nvidia/cosmos-reason1-7b") == 0

    def test_single_video_low_detail(self):
        """Single low detail video."""
        content = [
            {
                "type": "video_url",
                "video_url": {
                    "url": "https://example.com/video.mp4?width=512&height=288&duration=5.0&fps=4",
                    "detail": "low",
                },
            },
        ]
        # 5s at 4fps, low detail = 285 tokens
        assert (
            calculate_message_video_tokens(content, "nvidia/cosmos-reason1-7b") == 285
        )

    def test_single_video_high_detail(self):
        """Single high detail video."""
        content = [
            {
                "type": "video_url",
                "video_url": {
                    "url": "https://example.com/512x288_5.0s_4.0fps/video.mp4",
                    "detail": "high",
                },
            },
        ]
        # 5s at 4fps, high detail, 512×288 = 685 tokens
        assert (
            calculate_message_video_tokens(content, "nvidia/cosmos-reason1-7b") == 685
        )

    def test_multiple_videos(self):
        """Multiple videos with different details."""
        content = [
            {"type": "text", "text": "Compare these:"},
            {
                "type": "video_url",
                "video_url": {
                    "url": "https://example.com/video1.mp4?width=512&height=288&duration=5.0&fps=4",
                    "detail": "high",
                },
            },
            {
                "type": "video_url",
                "video_url": {
                    "url": "https://example.com/video2.mp4?width=512&height=288&duration=5.0&fps=4",
                    "detail": "low",
                },
            },
        ]
        # First video: high detail = 685
        # Second video: low detail = 285
        # Total: 970 tokens
        assert (
            calculate_message_video_tokens(content, "nvidia/cosmos-reason1-7b") == 970
        )

    def test_data_uri_with_metadata(self):
        """Data URI with metadata."""
        content = [
            {
                "type": "video_url",
                "video_url": {
                    "url": "data:video/mp4;meta=512x288:5.0s@4fps;base64,AAAAA...",
                    "detail": "high",
                },
            },
        ]
        # 5s at 4fps, high detail = 685 tokens
        assert (
            calculate_message_video_tokens(content, "nvidia/cosmos-reason1-7b") == 685
        )


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_duration(self):
        """Zero duration video still has base tokens."""
        tokens = estimate_video_tokens(
            0.0, 4.0, 512, 288, "low", "nvidia/cosmos-reason1-7b"
        )
        assert tokens >= 85  # At least base tokens

    def test_fractional_frames(self):
        """Fractional frames are rounded."""
        # 2.5 seconds at 4 fps = 10 frames
        tokens = estimate_video_tokens(
            2.5, 4.0, 512, 288, "low", "nvidia/cosmos-reason1-7b"
        )
        assert tokens == 85 + (10 * 10)

    def test_very_high_fps(self):
        """Very high FPS increases token count significantly."""
        # 5 seconds at 60 fps = 300 frames
        tokens = estimate_video_tokens(
            5.0, 60.0, 512, 288, "low", "nvidia/cosmos-reason1-7b"
        )
        assert tokens == 85 + (300 * 10)

    def test_malformed_url_defaults(self):
        """Malformed URLs default to standard metadata."""
        metadata = parse_video_metadata_from_url("not-a-valid-url")
        assert metadata["width"] == 512
        assert metadata["height"] == 288
        assert metadata["duration"] == 5.0
        assert metadata["fps"] == 4.0

    def test_empty_video_list(self):
        """Empty video list in content."""
        content = [{"type": "text", "text": "No videos here"}]
        assert calculate_message_video_tokens(content, "nvidia/cosmos-reason1-7b") == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
