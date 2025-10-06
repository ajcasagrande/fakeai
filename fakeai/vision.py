"""
Vision token calculation for multi-modal content.

This module implements OpenAI's tile-based vision token calculation formula
for images in chat completions. Supports low, high, and auto detail modes.
"""

#  SPDX-License-Identifier: Apache-2.0

import base64
import math
import re
from typing import Any
from urllib.parse import urlparse


def calculate_image_tokens(width: int, height: int, detail: str, model: str) -> int:
    """
    Calculate image tokens using OpenAI's tile-based formula.

    OpenAI's formula:
    - Low detail: 85 tokens (fixed)
    - High detail: 85 + (170 × num_tiles) for openai/gpt-oss-120b, 2833 + (5667 × num_tiles) for openai/gpt-oss-20b
    - Auto detail: Heuristic-based selection

    Tile calculation:
    1. Scale image to fit within 2048×2048
    2. Scale shortest side to 768px
    3. Divide into 512×512 tiles

    Args:
        width: Image width in pixels
        height: Image height in pixels
        detail: Detail level ("low", "high", or "auto")
        model: Model ID (affects high detail token counts)

    Returns:
        Number of tokens for the image
    """
    if detail == "low":
        return 85

    # Auto detail heuristic: use low detail for small images
    if detail == "auto":
        # Use low detail if image is small (under 512×512)
        if width <= 512 and height <= 512:
            return 85
        # Otherwise use high detail
        detail = "high"

    # High detail calculation
    # Step 1: Scale to fit within 2048×2048 if needed
    max_dimension = max(width, height)
    if max_dimension > 2048:
        scale_factor = 2048 / max_dimension
        width = int(width * scale_factor)
        height = int(height * scale_factor)

    # Step 2: Scale shortest side to exactly 768px
    min_dimension = min(width, height)
    scale_factor = 768 / min_dimension
    width = int(width * scale_factor)
    height = int(height * scale_factor)

    # Step 3: Calculate number of 512×512 tiles
    tiles_width = math.ceil(width / 512)
    tiles_height = math.ceil(height / 512)
    num_tiles = tiles_width * tiles_height

    # Different models use different base costs
    is_mini = (
        "mini" in model.lower()
        or model.endswith("gpt-oss-20b")
        or "gpt-oss-20b" == model.split("/")[-1]
    )
    if is_mini:
        # openai/gpt-oss-20b (mini models): 2833 + (5667 × tiles)
        return 2833 + (5667 * num_tiles)
    else:
        # openai/gpt-oss-120b and other vision models: 85 + (170 × tiles)
        return 85 + (170 * num_tiles)


def parse_image_dimensions_from_url(url: str) -> tuple[int, int] | None:
    """
    Extract image dimensions from URL or data URI.

    Supports:
    - Query parameter hints: ?width=800&height=600
    - Data URI with dimension hints: data:image/png;dim=800x600;base64,...
    - Placeholder/simulated URLs with dimensions in path

    Args:
        url: Image URL or data URI

    Returns:
        Tuple of (width, height) if dimensions found, None otherwise
    """
    # Check for data URI
    if url.startswith("data:"):
        # Look for dimension hint in data URI
        match = re.search(r"dim=(\d+)x(\d+)", url)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        # Default dimensions for data URIs without hints
        return (1024, 1024)

    # Parse URL for query parameters
    parsed = urlparse(url)

    # Check query parameters
    query_params = {}
    if parsed.query:
        for param in parsed.query.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                query_params[key] = value

    if "width" in query_params and "height" in query_params:
        try:
            width = int(query_params["width"])
            height = int(query_params["height"])
            return (width, height)
        except ValueError:
            pass

    # Check for dimensions in path (common in simulated URLs)
    match = re.search(r"(\d+)x(\d+)", parsed.path)
    if match:
        return (int(match.group(1)), int(match.group(2)))

    # Default dimensions for regular URLs without hints
    return (1024, 1024)


def extract_image_content(content: str | list[Any] | None) -> list[dict[str, Any]]:
    """
    Extract image content parts from message content.

    Args:
        content: Message content (string, content parts array, or None)

    Returns:
        List of image content dictionaries with 'url' and 'detail' keys
    """
    if content is None or isinstance(content, str):
        return []

    if not isinstance(content, list):
        return []

    images = []
    for part in content:
        # Handle dict format (from JSON)
        if isinstance(part, dict):
            if part.get("type") == "image_url":
                image_url = part.get("image_url", {})
                url = image_url.get("url", "")
                detail = image_url.get("detail", "auto")
                if url:
                    images.append({"url": url, "detail": detail})
        # Handle Pydantic model format
        elif hasattr(part, "type") and part.type == "image_url":
            if hasattr(part, "image_url"):
                url = part.image_url.url if hasattr(part.image_url, "url") else ""
                detail = (
                    part.image_url.detail
                    if hasattr(part.image_url, "detail")
                    else "auto"
                )
                if url:
                    images.append({"url": url, "detail": detail})

    return images


def calculate_message_image_tokens(content: str | list[Any] | None, model: str) -> int:
    """
    Calculate total image tokens for a message.

    Args:
        content: Message content (string, content parts array, or None)
        model: Model ID (affects token calculation)

    Returns:
        Total number of image tokens in the message
    """
    images = extract_image_content(content)
    total_tokens = 0

    for image in images:
        url = image["url"]
        detail = image["detail"]

        # Parse dimensions from URL
        dimensions = parse_image_dimensions_from_url(url)
        if dimensions:
            width, height = dimensions
            tokens = calculate_image_tokens(width, height, detail, model)
            total_tokens += tokens

    return total_tokens
