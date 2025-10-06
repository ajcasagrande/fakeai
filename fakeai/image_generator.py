"""
Image Generation Module

This module provides actual image generation using PIL (Pillow) instead of
just returning fake URLs. Generates placeholder images with various styles,
qualities, and patterns.
"""

#  SPDX-License-Identifier: Apache-2.0

import base64
import hashlib
import io
import logging
import random
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Literal

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class ImageGenerator:
    """
    Generate actual placeholder images using PIL.

    Features:
    - Solid color backgrounds with text overlay
    - Gradient backgrounds (optional)
    - Random geometric patterns
    - Model name + timestamp watermark
    - Multiple size support (all DALL-E sizes)
    - Quality modes (standard/HD)
    - Style support (vivid/natural)
    - Response formats (URL/base64)
    - Multiple image generation
    - In-memory storage with automatic cleanup
    """

    # All supported DALL-E sizes
    SUPPORTED_SIZES = {
        "256x256": (256, 256),  # DALL-E 2
        "512x512": (512, 512),  # DALL-E 2
        "1024x1024": (1024, 1024),  # DALL-E 2 & 3
        "1792x1024": (1792, 1024),  # DALL-E 3
        "1024x1792": (1024, 1792),  # DALL-E 3
    }

    # Color palettes for different styles
    VIVID_COLORS = [
        (255, 59, 48),  # Red
        (255, 149, 0),  # Orange
        (255, 204, 0),  # Yellow
        (52, 199, 89),  # Green
        (0, 199, 190),  # Teal
        (48, 176, 199),  # Light Blue
        (50, 173, 230),  # Blue
        (94, 92, 230),  # Indigo
        (175, 82, 222),  # Purple
        (255, 45, 85),  # Pink
    ]

    NATURAL_COLORS = [
        (139, 69, 19),  # Saddle Brown
        (160, 82, 45),  # Sienna
        (210, 180, 140),  # Tan
        (188, 143, 143),  # Rosy Brown
        (112, 128, 144),  # Slate Gray
        (119, 136, 153),  # Light Slate Gray
        (176, 196, 222),  # Light Steel Blue
        (143, 188, 143),  # Dark Sea Green
        (85, 107, 47),  # Dark Olive Green
        (128, 128, 105),  # Olive Drab
    ]

    # Pattern types
    PATTERNS = ["grid", "circles", "triangles", "lines", "dots", "waves"]

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        storage_backend: Literal["memory", "disk"] = "memory",
        retention_hours: int = 1,
    ):
        """
        Initialize the image generator.

        Args:
            base_url: Base URL for image endpoints
            storage_backend: Storage backend (memory or disk)
            retention_hours: Hours to retain generated images
        """
        self.base_url = base_url.rstrip("/")
        self.storage_backend = storage_backend
        self.retention_hours = retention_hours

        # In-memory storage: {image_id: {"data": bytes, "created_at": timestamp}}
        self._storage: dict[str, dict] = {}
        self._storage_lock = threading.Lock()

        # Start cleanup thread
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_expired_images,
            daemon=True,
        )
        self._cleanup_thread.start()

        logger.info(
            f"ImageGenerator initialized: backend={storage_backend}, "
            f"retention={retention_hours}h"
        )

    def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        n: int = 1,
        response_format: str = "url",
        model: str = "dall-e-3",
    ) -> list[dict]:
        """
        Generate n images based on the prompt.

        Args:
            prompt: Text description of desired image
            size: Image size (e.g., "1024x1024")
            quality: Quality mode ("standard" or "hd")
            style: Style mode ("vivid" or "natural")
            n: Number of images to generate
            response_format: Response format ("url" or "b64_json")
            model: Model name for watermark

        Returns:
            List of dicts with 'url' or 'b64_json' key
        """
        if size not in self.SUPPORTED_SIZES:
            raise ValueError(
                f"Unsupported size: {size}. "
                f"Supported: {', '.join(self.SUPPORTED_SIZES.keys())}"
            )

        dimensions = self.SUPPORTED_SIZES[size]
        images = []

        for i in range(n):
            # Generate unique image
            image_bytes = self.create_image(
                size=dimensions,
                prompt=prompt,
                quality=quality,
                style=style,
                model=model,
                index=i,
            )

            if response_format == "url":
                # Store image and return URL
                image_id = self.store_image(image_bytes)
                url = f"{self.base_url}/images/{image_id}.png"
                images.append({"url": url})
            else:  # b64_json
                # Return base64-encoded image
                b64_data = base64.b64encode(image_bytes).decode("utf-8")
                images.append({"b64_json": b64_data})

        logger.info(
            f"Generated {n} image(s): size={size}, quality={quality}, "
            f"style={style}, format={response_format}"
        )

        return images

    def create_image(
        self,
        size: tuple[int, int],
        prompt: str,
        quality: str,
        style: str,
        model: str,
        index: int = 0,
    ) -> bytes:
        """
        Create actual PNG image with PIL.

        Args:
            size: Image dimensions (width, height)
            prompt: Text prompt for image
            quality: Quality mode ("standard" or "hd")
            style: Style mode ("vivid" or "natural")
            model: Model name for watermark
            index: Image index for variation

        Returns:
            PNG image as bytes
        """
        width, height = size

        # Select color palette based on style
        colors = self.VIVID_COLORS if style == "vivid" else self.NATURAL_COLORS

        # Use prompt hash + index to seed randomness for reproducibility
        seed = int(hashlib.md5(f"{prompt}_{index}".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        # Create image
        if quality == "hd":
            # HD: Gradient background
            img = self._create_gradient_background(width, height, colors, rng)
        else:
            # Standard: Solid color background
            color = colors[rng.randint(0, len(colors) - 1)]
            img = Image.new("RGB", (width, height), color)

        draw = ImageDraw.Draw(img)

        # Add pattern overlay
        if quality == "hd":
            pattern = self.PATTERNS[rng.randint(0, len(self.PATTERNS) - 1)]
            self._draw_pattern(draw, width, height, pattern, rng, alpha=40)

        # Add text overlay
        self._draw_text_overlay(draw, width, height, prompt, quality)

        # Add watermark
        self._draw_watermark(draw, width, height, model)

        # Convert to PNG bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        buffer.seek(0)

        return buffer.read()

    def _create_gradient_background(
        self,
        width: int,
        height: int,
        colors: list[tuple[int, int, int]],
        rng: random.Random,
    ) -> Image.Image:
        """Create gradient background image."""
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        # Pick two colors for gradient
        color1 = colors[rng.randint(0, len(colors) - 1)]
        color2 = colors[rng.randint(0, len(colors) - 1)]

        # Vertical or horizontal gradient
        horizontal = rng.choice([True, False])

        if horizontal:
            # Horizontal gradient
            for x in range(width):
                r = int(color1[0] + (color2[0] - color1[0]) * x / width)
                g = int(color1[1] + (color2[1] - color1[1]) * x / width)
                b = int(color1[2] + (color2[2] - color1[2]) * x / width)
                draw.line([(x, 0), (x, height)], fill=(r, g, b))
        else:
            # Vertical gradient
            for y in range(height):
                r = int(color1[0] + (color2[0] - color1[0]) * y / height)
                g = int(color1[1] + (color2[1] - color1[1]) * y / height)
                b = int(color1[2] + (color2[2] - color1[2]) * y / height)
                draw.line([(0, y), (width, y)], fill=(r, g, b))

        return img

    def _draw_pattern(
        self,
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
        pattern: str,
        rng: random.Random,
        alpha: int = 40,
    ):
        """Draw geometric pattern overlay."""
        # Create semi-transparent overlay color
        overlay_color = (255, 255, 255, alpha)

        if pattern == "grid":
            # Grid pattern
            step = max(width, height) // 20
            for x in range(0, width, step):
                draw.line([(x, 0), (x, height)], fill=overlay_color, width=1)
            for y in range(0, height, step):
                draw.line([(0, y), (width, y)], fill=overlay_color, width=1)

        elif pattern == "circles":
            # Random circles
            for _ in range(rng.randint(10, 30)):
                cx = rng.randint(0, width)
                cy = rng.randint(0, height)
                r = rng.randint(20, min(width, height) // 10)
                draw.ellipse(
                    [(cx - r, cy - r), (cx + r, cy + r)],
                    outline=overlay_color,
                    width=2,
                )

        elif pattern == "triangles":
            # Random triangles
            for _ in range(rng.randint(5, 15)):
                x1, y1 = rng.randint(0, width), rng.randint(0, height)
                x2, y2 = rng.randint(0, width), rng.randint(0, height)
                x3, y3 = rng.randint(0, width), rng.randint(0, height)
                draw.polygon(
                    [(x1, y1), (x2, y2), (x3, y3)],
                    outline=overlay_color,
                )

        elif pattern == "lines":
            # Random lines
            for _ in range(rng.randint(10, 30)):
                x1, y1 = rng.randint(0, width), rng.randint(0, height)
                x2, y2 = rng.randint(0, width), rng.randint(0, height)
                draw.line([(x1, y1), (x2, y2)], fill=overlay_color, width=2)

        elif pattern == "dots":
            # Random dots
            for _ in range(rng.randint(50, 150)):
                cx = rng.randint(0, width)
                cy = rng.randint(0, height)
                r = rng.randint(2, 8)
                draw.ellipse(
                    [(cx - r, cy - r), (cx + r, cy + r)],
                    fill=overlay_color,
                )

        elif pattern == "waves":
            # Wave pattern
            amplitude = height // 20
            frequency = 0.02
            for y in range(0, height, 5):
                points = []
                for x in range(0, width, 10):
                    wave_y = y + int(
                        amplitude * rng.random() * (1 + 0.5 * (x * frequency % 1))
                    )
                    points.append((x, wave_y))
                if len(points) > 1:
                    draw.line(points, fill=overlay_color, width=2)

    def _draw_text_overlay(
        self,
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
        prompt: str,
        quality: str,
    ):
        """Draw text overlay with prompt."""
        # Truncate long prompts
        max_length = 100 if quality == "hd" else 60
        if len(prompt) > max_length:
            prompt = prompt[: max_length - 3] + "..."

        # Calculate font size based on image dimensions
        base_font_size = min(width, height) // 25

        try:
            # Try to load a nice font (fallback to default if not available)
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", base_font_size
            )
        except (OSError, IOError):
            # Fallback to default font
            font = ImageFont.load_default()

        # Draw text in center
        text_bbox = draw.textbbox((0, 0), prompt, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        x = (width - text_width) // 2
        y = (height - text_height) // 2

        # Draw text with shadow for better visibility
        shadow_offset = 2
        draw.text(
            (x + shadow_offset, y + shadow_offset),
            prompt,
            fill=(0, 0, 0, 180),
            font=font,
        )
        draw.text((x, y), prompt, fill=(255, 255, 255, 255), font=font)

    def _draw_watermark(
        self,
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
        model: str,
    ):
        """Draw watermark with model name and timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        watermark = f"{model} | {timestamp}"

        # Small font for watermark
        font_size = max(10, min(width, height) // 80)

        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size
            )
        except (OSError, IOError):
            font = ImageFont.load_default()

        # Position in bottom-right corner
        text_bbox = draw.textbbox((0, 0), watermark, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        x = width - text_width - 10
        y = height - text_height - 10

        # Semi-transparent background for watermark
        padding = 5
        draw.rectangle(
            [
                (x - padding, y - padding),
                (x + text_width + padding, y + text_height + padding),
            ],
            fill=(0, 0, 0, 100),
        )

        draw.text((x, y), watermark, fill=(255, 255, 255, 200), font=font)

    def store_image(self, image_bytes: bytes) -> str:
        """
        Store generated image in memory.

        Args:
            image_bytes: PNG image data

        Returns:
            Image ID for retrieval
        """
        image_id = uuid.uuid4().hex

        with self._storage_lock:
            self._storage[image_id] = {
                "data": image_bytes,
                "created_at": time.time(),
            }

        logger.debug(f"Stored image: {image_id} ({len(image_bytes)} bytes)")

        return image_id

    def get_image(self, image_id: str) -> bytes | None:
        """
        Retrieve stored image.

        Args:
            image_id: Image ID from store_image

        Returns:
            PNG image bytes or None if not found/expired
        """
        with self._storage_lock:
            if image_id not in self._storage:
                logger.warning(f"Image not found: {image_id}")
                return None

            entry = self._storage[image_id]

            # Check if expired
            age_hours = (time.time() - entry["created_at"]) / 3600
            if age_hours > self.retention_hours:
                logger.info(f"Image expired: {image_id} (age: {age_hours:.1f}h)")
                del self._storage[image_id]
                return None

            return entry["data"]

    def _cleanup_expired_images(self):
        """Background thread to cleanup expired images."""
        while True:
            try:
                time.sleep(300)  # Check every 5 minutes

                current_time = time.time()
                expired_ids = []

                with self._storage_lock:
                    for image_id, entry in self._storage.items():
                        age_hours = (current_time - entry["created_at"]) / 3600
                        if age_hours > self.retention_hours:
                            expired_ids.append(image_id)

                    for image_id in expired_ids:
                        del self._storage[image_id]

                if expired_ids:
                    logger.info(f"Cleaned up {len(expired_ids)} expired images")

            except Exception as e:
                logger.error(f"Error in image cleanup thread: {e}")

    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.

        Returns:
            Dict with storage stats
        """
        with self._storage_lock:
            total_size = sum(len(entry["data"]) for entry in self._storage.values())

            return {
                "total_images": len(self._storage),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "retention_hours": self.retention_hours,
                "backend": self.storage_backend,
            }
