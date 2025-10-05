"""
Video token calculation for multi-modal content (NVIDIA Cosmos extension).

This module implements video token calculation for chat completions.
Based on frame extraction and image-like token accounting.

For NVIDIA Cosmos models:
- Videos are processed frame-by-frame
- Each frame is treated similar to an image
- Token count = base_tokens + (frames × tokens_per_frame)
"""
#  SPDX-License-Identifier: Apache-2.0

import re
from typing import Any
from urllib.parse import urlparse


def estimate_video_tokens(
    duration_seconds: float,
    fps: float,
    width: int,
    height: int,
    detail: str,
    model: str
) -> int:
    """
    Estimate video tokens based on duration, resolution, and frame rate.

    Video token calculation formula:
    - Base tokens: 85 (similar to images)
    - Frames = duration × fps
    - Per-frame tokens depend on resolution and detail level
    - Total = base + (frames × tokens_per_frame × detail_multiplier)

    Args:
        duration_seconds: Video duration in seconds
        fps: Frames per second
        width: Video width in pixels
        height: Video height in pixels
        detail: Detail level ("low", "high", or "auto")
        model: Model ID

    Returns:
        Estimated number of tokens for the video
    """
    # Base tokens for any video
    base_tokens = 85

    # Calculate total frames
    total_frames = int(duration_seconds * fps)

    # Detail level multipliers
    if detail == "low":
        # Low detail: minimal processing, fewer tokens per frame
        tokens_per_frame = 10
    elif detail == "high":
        # High detail: full resolution processing
        # Scale based on resolution (similar to image tiles)
        tile_size = 512
        tiles_per_frame = max(1, (width // tile_size) * (height // tile_size))
        tokens_per_frame = 20 + (tiles_per_frame * 10)
    else:  # auto
        # Auto: heuristic based on resolution
        if width <= 512 and height <= 512:
            tokens_per_frame = 10  # Low detail for small videos
        else:
            # High detail for larger videos
            tile_size = 512
            tiles_per_frame = max(1, (width // tile_size) * (height // tile_size))
            tokens_per_frame = 20 + (tiles_per_frame * 10)

    # Total tokens
    total_tokens = base_tokens + (total_frames * tokens_per_frame)

    return total_tokens


def parse_video_metadata_from_url(url: str) -> dict[str, Any]:
    """
    Extract video metadata from URL or data URI.

    Supports:
    - Query parameter hints: ?width=512&height=288&duration=5.0&fps=4
    - Data URI with metadata: data:video/mp4;meta=512x288:5.0s@4fps;base64,...
    - Default values for missing metadata

    Args:
        url: Video URL or data URI

    Returns:
        Dictionary with keys: width, height, duration, fps
    """
    # Default metadata
    metadata = {
        "width": 512,
        "height": 288,
        "duration": 5.0,
        "fps": 4.0,
    }

    # Check for data URI with metadata
    if url.startswith("data:"):
        # Look for metadata hint in data URI
        # Format: data:video/mp4;meta=512x288:5.0s@4fps;base64,...
        match = re.search(r'meta=(\d+)x(\d+):(\d+\.?\d*)s@(\d+\.?\d*)fps', url)
        if match:
            metadata["width"] = int(match.group(1))
            metadata["height"] = int(match.group(2))
            metadata["duration"] = float(match.group(3))
            metadata["fps"] = float(match.group(4))
            return metadata

    # Parse URL for query parameters
    parsed = urlparse(url)

    # Check query parameters
    if parsed.query:
        query_params = {}
        for param in parsed.query.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                query_params[key] = value

        if "width" in query_params:
            try:
                metadata["width"] = int(query_params["width"])
            except ValueError:
                pass

        if "height" in query_params:
            try:
                metadata["height"] = int(query_params["height"])
            except ValueError:
                pass

        if "duration" in query_params:
            try:
                metadata["duration"] = float(query_params["duration"])
            except ValueError:
                pass

        if "fps" in query_params:
            try:
                metadata["fps"] = float(query_params["fps"])
            except ValueError:
                pass

    # Check for metadata in path
    # Format: /videos/512x288_5s_4fps/video.mp4
    path_match = re.search(r'(\d+)x(\d+)_(\d+\.?\d*)s_(\d+\.?\d*)fps', parsed.path)
    if path_match:
        metadata["width"] = int(path_match.group(1))
        metadata["height"] = int(path_match.group(2))
        metadata["duration"] = float(path_match.group(3))
        metadata["fps"] = float(path_match.group(4))

    return metadata


def extract_video_content(content: str | list[Any] | None) -> list[dict[str, Any]]:
    """
    Extract video content parts from message content.

    Args:
        content: Message content (string, content parts array, or None)

    Returns:
        List of video content dictionaries with 'url' and 'detail' keys
    """
    if content is None or isinstance(content, str):
        return []

    if not isinstance(content, list):
        return []

    videos = []
    for part in content:
        # Handle dict format (from JSON)
        if isinstance(part, dict):
            if part.get("type") == "video_url":
                video_url = part.get("video_url", {})
                url = video_url.get("url", "")
                detail = video_url.get("detail", "auto")
                if url:
                    videos.append({"url": url, "detail": detail})
        # Handle Pydantic model format
        elif hasattr(part, "type") and part.type == "video_url":
            if hasattr(part, "video_url"):
                url = part.video_url.url if hasattr(part.video_url, "url") else ""
                detail = part.video_url.detail if hasattr(part.video_url, "detail") else "auto"
                if url:
                    videos.append({"url": url, "detail": detail})

    return videos


def calculate_message_video_tokens(content: str | list[Any] | None, model: str) -> int:
    """
    Calculate total video tokens for a message.

    Args:
        content: Message content (string, content parts array, or None)
        model: Model ID (affects token calculation)

    Returns:
        Total number of video tokens in the message
    """
    videos = extract_video_content(content)
    total_tokens = 0

    for video in videos:
        url = video["url"]
        detail = video["detail"]

        # Parse metadata from URL
        metadata = parse_video_metadata_from_url(url)

        # Calculate tokens
        tokens = estimate_video_tokens(
            duration_seconds=metadata["duration"],
            fps=metadata["fps"],
            width=metadata["width"],
            height=metadata["height"],
            detail=detail,
            model=model
        )
        total_tokens += tokens

    return total_tokens
