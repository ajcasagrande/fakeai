"""
Image Generation Service

This module provides the image generation service, handling DALL-E 2, DALL-E 3,
and Stability AI models with support for various sizes, qualities, and styles.
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import base64
import logging
import random
import time
import uuid

from fakeai.config import AppConfig
from fakeai.image_generator import ImageGenerator
from fakeai.metrics import MetricsTracker
from fakeai.models import (
    GeneratedImage,
    ImageGenerationRequest,
    ImageGenerationResponse,
)

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """
    Service for generating images with DALL-E 2, DALL-E 3, and Stability AI models.

    Features:
    - Model validation (dall-e-2, dall-e-3, stability models)
    - Size/quality/style validation
    - Actual image generation when enabled
    - Fallback to fake URLs when disabled
    - Usage tracking for billing
    - Metrics recording
    """

    # Valid models for image generation
    VALID_MODELS = [
        "stabilityai/stable-diffusion-2-1",
        "stabilityai/stable-diffusion-xl-base-1.0",
        "dall-e-2",
        "dall-e-3",
    ]

    # DALL-E 2 supported sizes
    DALLE_2_SIZES = ["256x256", "512x512", "1024x1024"]

    # DALL-E 3 supported sizes
    DALLE_3_SIZES = ["1024x1024", "1792x1024", "1024x1792"]

    # Valid quality values
    VALID_QUALITIES = ["standard", "hd"]

    # Valid style values
    VALID_STYLES = ["vivid", "natural"]

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
        image_generator: ImageGenerator | None = None,
    ):
        """
        Initialize the image generation service.

        Args:
            config: Application configuration
            metrics_tracker: Metrics tracker instance
            image_generator: Optional image generator for actual image generation
        """
        self.config = config
        self.metrics_tracker = metrics_tracker
        self.image_generator = image_generator

        logger.info(
            f"ImageGenerationService initialized: "
            f"generator_enabled={image_generator is not None}"
        )

    async def generate_images(
        self,
        request: ImageGenerationRequest,
    ) -> ImageGenerationResponse:
        """
        Generate images based on prompt.

        Args:
            request: Image generation request with prompt, model, size, etc.

        Returns:
            ImageGenerationResponse with generated images

        Raises:
            ValueError: If model or parameters are invalid
        """
        # Validate model
        model = request.model or "stabilityai/stable-diffusion-2-1"
        if model not in self.VALID_MODELS:
            raise ValueError(
                f"Invalid model for image generation: {model}. "
                f"Valid models: {', '.join(self.VALID_MODELS)}"
            )

        # Validate size based on model
        size = request.size or "1024x1024"
        self._validate_size(model, size)

        # Validate quality
        quality = request.quality or "standard"
        if quality not in self.VALID_QUALITIES:
            raise ValueError(
                f"Invalid quality: {quality}. "
                f"Valid qualities: {', '.join(self.VALID_QUALITIES)}"
            )

        # Validate style
        style = request.style or "vivid"
        if style not in self.VALID_STYLES:
            raise ValueError(
                f"Invalid style: {style}. "
                f"Valid styles: {', '.join(self.VALID_STYLES)}"
            )

        # DALL-E 3 specific validations
        if model == "dall-e-3":
            if request.n and request.n > 1:
                raise ValueError("DALL-E 3 only supports n=1")
            if quality == "hd" and size not in ["1024x1024", "1792x1024", "1024x1792"]:
                raise ValueError(
                    f"HD quality for DALL-E 3 requires size to be one of: "
                    f"1024x1024, 1792x1024, 1024x1792"
                )

        # Simulate processing delay based on image size, quality, and number
        delay = self._calculate_processing_delay(size, quality, request.n or 1)
        await asyncio.sleep(delay)

        # Generate images (actual or simulated)
        images = await self._generate_image_data(
            prompt=request.prompt,
            model=model,
            size=size,
            quality=quality,
            style=style,
            n=request.n or 1,
            response_format=request.response_format or "url",
        )

        # Create response
        response = ImageGenerationResponse(
            created=int(time.time()),
            data=images,
        )

        # Track metrics
        self.metrics_tracker.track_request("/v1/images/generations")

        # Log generation
        logger.info(
            f"Generated {len(images)} image(s): model={model}, size={size}, "
            f"quality={quality}, style={style}, format={request.response_format}"
        )

        return response

    def _validate_size(self, model: str, size: str) -> None:
        """
        Validate size based on model.

        Args:
            model: Model name
            size: Image size (e.g., "1024x1024")

        Raises:
            ValueError: If size is not valid for the model
        """
        if model == "dall-e-2":
            if size not in self.DALLE_2_SIZES:
                raise ValueError(
                    f"Invalid size for DALL-E 2: {size}. "
                    f"Valid sizes: {', '.join(self.DALLE_2_SIZES)}"
                )
        elif model == "dall-e-3":
            if size not in self.DALLE_3_SIZES:
                raise ValueError(
                    f"Invalid size for DALL-E 3: {size}. "
                    f"Valid sizes: {', '.join(self.DALLE_3_SIZES)}"
                )
        # Stability AI models support all sizes

    def _calculate_processing_delay(self, size: str, quality: str, n: int) -> float:
        """
        Calculate simulated processing delay.

        Args:
            size: Image size
            quality: Quality mode
            n: Number of images

        Returns:
            Delay in seconds
        """
        # Base delay factors
        size_factor = 1.0
        if size == "1024x1024":
            size_factor = 1.5
        elif size in ["1792x1024", "1024x1792"]:
            size_factor = 2.0

        quality_factor = 1.5 if quality == "hd" else 1.0

        # Calculate delay with randomness
        base_delay = 1.0 * n * size_factor * quality_factor
        delay = base_delay + random.uniform(0.5, 2.0)

        return delay

    async def _generate_image_data(
        self,
        prompt: str,
        model: str,
        size: str,
        quality: str,
        style: str,
        n: int,
        response_format: str,
    ) -> list[GeneratedImage]:
        """
        Generate actual or simulated image data.

        Args:
            prompt: Text description of desired image
            model: Model name
            size: Image size
            quality: Quality mode
            style: Style mode
            n: Number of images
            response_format: Response format (url or b64_json)

        Returns:
            List of GeneratedImage objects
        """
        images = []

        if self.image_generator:
            # Use actual image generation
            try:
                generated = self.image_generator.generate(
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    style=style,
                    n=n,
                    response_format=response_format,
                    model=model,
                )

                for img in generated:
                    if "url" in img:
                        images.append(GeneratedImage(url=img["url"]))
                    else:
                        images.append(GeneratedImage(b64_json=img["b64_json"]))

                logger.info(f"Generated {n} actual image(s) using ImageGenerator")

            except Exception as e:
                logger.error(f"Image generation failed: {e}, falling back to fake URLs")
                # Fallback to fake URLs
                images = self._generate_fake_images(n, response_format)
        else:
            # Fallback to fake URLs when image generator is disabled
            images = self._generate_fake_images(n, response_format)

        return images

    def _generate_fake_images(
        self, n: int, response_format: str
    ) -> list[GeneratedImage]:
        """
        Generate fake image URLs or base64 data.

        Args:
            n: Number of images
            response_format: Response format (url or b64_json)

        Returns:
            List of GeneratedImage objects with fake data
        """
        images = []

        for _ in range(n):
            if response_format == "url":
                url = f"https://simulated-openai-images.example.com/{uuid.uuid4().hex}.png"
                images.append(GeneratedImage(url=url))
            else:
                # Generate fake base64 data
                fake_b64 = base64.b64encode(b"simulated_image_data").decode("utf-8")
                images.append(GeneratedImage(b64_json=fake_b64))

        logger.debug(f"Generated {n} fake image(s) in {response_format} format")

        return images
