"""
Moderation service for content safety classification.

Provides content moderation capabilities for text and multimodal inputs,
classifying content across 13 safety categories with confidence scores.
"""

#  SPDX-License-Identifier: Apache-2.0

import random
import uuid
from typing import Any

from fakeai.config import AppConfig
from fakeai.metrics import MetricsTracker
from fakeai.models import (
    ModerationCategories,
    ModerationCategoryScores,
    ModerationRequest,
    ModerationResponse,
    ModerationResult,
)
from fakeai.models_registry.registry import ModelRegistry
from fakeai.utils.tokens import calculate_token_count


class ModerationService:
    """
    Content moderation service for safety classification.

    Analyzes text and multimodal content to detect harmful content across
    13 categories: sexual, hate, harassment, self-harm, violence, illicit,
    and their subcategories.

    Features:
    - Support for string, list[str], and multimodal content
    - Confidence scores (0.0-1.0) for each category
    - Flagged determination (threshold: 0.5)
    - Token usage tracking
    - Image detection for multimodal categories
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
        model_registry: ModelRegistry,
    ):
        """
        Initialize the moderation service.

        Args:
            config: Application configuration
            metrics_tracker: Singleton metrics tracker
            model_registry: Model registry for model management
        """
        self.config = config
        self.metrics_tracker = metrics_tracker
        self.model_registry = model_registry
        self.harmful_keywords = self._load_harmful_keywords()

    def _load_harmful_keywords(self) -> dict[str, list[str]]:
        """
        Load harmful content keywords for each category.

        Returns:
            Dictionary mapping category names to keyword lists
        """
        return {
            "violence": [
                "kill",
                "murder",
                "attack",
                "weapon",
                "gun",
                "stab",
                "shoot",
                "assault",
                "fight",
            ],
            "violence_graphic": [
                "blood",
                "gore",
                "mutilate",
                "dismember",
                "decapitate",
            ],
            "hate": [
                "hate",
                "racist",
                "discriminate",
                "slur",
                "bigot",
                "nazi",
                "supremacist",
            ],
            "hate_threatening": ["death threat", "lynch", "exterminate", "cleanse"],
            "sexual": ["sex", "porn", "nude", "explicit", "nsfw", "erotic", "xxx"],
            "sexual_minors": [
                "child",
                "minor",
                "underage",
                "kid",
                "teen",
                "adolescent",
            ],
            "self_harm": [
                "suicide",
                "kill myself",
                "self-harm",
                "cut myself",
                "end my life",
            ],
            "self_harm_intent": [
                "want to die",
                "going to kill myself",
                "planning suicide",
            ],
            "self_harm_instructions": [
                "how to commit suicide",
                "ways to kill yourself",
            ],
            "harassment": [
                "bully",
                "harass",
                "threaten",
                "insult",
                "abuse",
                "intimidate",
            ],
            "harassment_threatening": [
                "i will hurt you",
                "you will regret",
                "watch your back",
            ],
            "illicit": [
                "how to hack",
                "how to steal",
                "illegal",
                "drug deal",
                "sell drugs",
            ],
            "illicit_violent": [
                "make a bomb",
                "build explosives",
                "mass shooting plan",
            ],
        }

    async def create_moderation(
        self,
        request: ModerationRequest,
    ) -> ModerationResponse:
        """
        Classify content for safety across 13 categories.

        Analyzes input content (text, array of texts, or multimodal) and returns
        moderation results with category flags and confidence scores.

        Args:
            request: Moderation request with input content and model

        Returns:
            ModerationResponse with results for each input

        Example:
            >>> request = ModerationRequest(input="Hello world", model="omni-moderation-latest")
            >>> response = await service.create_moderation(request)
            >>> response.results[0].flagged
            False
        """
        # Normalize input to list of (text, has_image) tuples
        inputs = self._normalize_moderation_input(request.input)

        # Generate results for each input
        results = []
        for text, has_image in inputs:
            result = self._generate_moderation_result(text, has_image)
            results.append(result)

        # Track token usage
        total_tokens = sum(calculate_token_count(text) for text, _ in inputs)
        self.metrics_tracker.track_tokens("/v1/moderations", total_tokens)

        return ModerationResponse(
            id=f"modr-{uuid.uuid4().hex}",
            model=request.model or "omni-moderation-latest",
            results=results,
        )

    def _normalize_moderation_input(
        self,
        input_data: str | list[str] | list[dict[str, Any]],
    ) -> list[tuple[str, bool]]:
        """
        Normalize moderation input to list of (text, has_image) tuples.

        Handles three input formats:
        1. Single string: "text to moderate"
        2. Array of strings: ["text1", "text2"]
        3. Multimodal: [{"type": "text", "text": "..."}, {"type": "image_url", "image_url": {...}}]

        Args:
            input_data: Input in one of the three formats

        Returns:
            List of (text, has_image) tuples
        """
        if isinstance(input_data, str):
            return [(input_data, False)]

        if isinstance(input_data, list):
            if not input_data:
                return [("", False)]

            # Check if multimodal (list of dicts with type field)
            if isinstance(input_data[0], dict):
                # Could be multimodal or just text
                if input_data[0].get("type") in ["text", "image_url"]:
                    # Multimodal input
                    text_parts = []
                    has_image = False
                    for item in input_data:
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif item.get("type") == "image_url":
                            has_image = True
                    return [(" ".join(text_parts), has_image)]

            # Array of strings
            return [(text, False) for text in input_data]

        return [("", False)]

    def _generate_moderation_result(
        self,
        text: str,
        has_image: bool,
    ) -> ModerationResult:
        """
        Generate moderation scores for text/image content.

        Scans content for harmful keywords and calculates confidence scores
        for each category. Determines which input types (text/image) triggered
        each flagged category.

        Args:
            text: Text content to moderate
            has_image: Whether the input contains an image

        Returns:
            ModerationResult with flags, scores, and applied input types
        """
        # Scan content and get categories/scores
        categories, scores = self._scan_for_harmful_content(text)

        # Determine applied input types for flagged categories
        applied_types = {}
        multimodal_categories = [
            "violence",
            "violence/graphic",
            "self-harm",
            "self-harm/intent",
            "self-harm/instructions",
            "sexual",
        ]

        for cat, flagged in categories.items():
            if flagged:
                types = []
                base_cat = cat.split("/")[0]
                if base_cat in multimodal_categories:
                    # For multimodal categories, determine if text and/or image triggered it
                    if text and random.random() > 0.4:
                        types.append("text")
                    if has_image and random.random() > 0.3:
                        types.append("image")
                    if not types:
                        types.append("image" if has_image else "text")
                else:
                    # Non-multimodal categories only apply to text
                    if text:
                        types.append("text")
                applied_types[cat] = types

        return ModerationResult(
            flagged=any(categories.values()),
            categories=ModerationCategories(
                **{k.replace("/", "_"): v for k, v in categories.items()}
            ),
            category_scores=ModerationCategoryScores(
                **{k.replace("/", "_"): v for k, v in scores.items()}
            ),
            category_applied_input_types=applied_types,
        )

    def _scan_for_harmful_content(
        self,
        text: str,
    ) -> tuple[dict[str, bool], dict[str, float]]:
        """
        Scan text for harmful content and calculate category scores.

        Uses keyword matching with random confidence scores to simulate
        a content safety classifier. Real implementations would use ML models.

        Args:
            text: Text to scan

        Returns:
            Tuple of (categories dict, scores dict) where:
            - categories: {category: is_flagged} (threshold: 0.5)
            - scores: {category: confidence} (0.0-1.0)
        """
        # Base scores (safe by default)
        scores = {
            "sexual": 0.00001,
            "hate": 0.00002,
            "harassment": 0.0001,
            "self_harm": 0.00003,
            "sexual_minors": 0.000001,
            "hate_threatening": 0.00001,
            "harassment_threatening": 0.00005,
            "self_harm_intent": 0.00002,
            "self_harm_instructions": 0.00001,
            "violence": 0.0002,
            "violence_graphic": 0.0001,
            "illicit": 0.0001,
            "illicit_violent": 0.00001,
        }

        text_lower = text.lower()

        # Violence keywords
        if any(word in text_lower for word in self.harmful_keywords["violence"]):
            scores["violence"] = random.uniform(0.6, 0.9)
            scores["violence_graphic"] = random.uniform(0.4, 0.7)

        # Violence graphic keywords
        if any(
            word in text_lower for word in self.harmful_keywords["violence_graphic"]
        ):
            scores["violence_graphic"] = random.uniform(0.7, 0.95)

        # Hate keywords
        if any(word in text_lower for word in self.harmful_keywords["hate"]):
            scores["hate"] = random.uniform(0.5, 0.8)
            scores["hate_threatening"] = random.uniform(0.3, 0.6)

        # Hate threatening keywords
        if any(
            word in text_lower for word in self.harmful_keywords["hate_threatening"]
        ):
            scores["hate_threatening"] = random.uniform(0.7, 0.95)
            # Also elevate base category if not already high
            scores["hate"] = max(scores["hate"], random.uniform(0.5, 0.7))

        # Sexual keywords
        if any(word in text_lower for word in self.harmful_keywords["sexual"]):
            scores["sexual"] = random.uniform(0.6, 0.9)

        # Self-harm keywords
        if any(word in text_lower for word in self.harmful_keywords["self_harm"]):
            scores["self_harm"] = random.uniform(0.7, 0.95)
            scores["self_harm_intent"] = random.uniform(0.5, 0.8)

        # Self-harm intent keywords
        if any(
            word in text_lower for word in self.harmful_keywords["self_harm_intent"]
        ):
            scores["self_harm_intent"] = random.uniform(0.8, 0.98)
            # Also elevate base category if not already high
            scores["self_harm"] = max(scores["self_harm"], random.uniform(0.5, 0.7))

        # Self-harm instructions keywords
        if any(
            word in text_lower
            for word in self.harmful_keywords["self_harm_instructions"]
        ):
            scores["self_harm_instructions"] = random.uniform(0.8, 0.98)
            # Also elevate base category if not already high
            scores["self_harm"] = max(scores["self_harm"], random.uniform(0.5, 0.7))

        # Harassment keywords
        if any(word in text_lower for word in self.harmful_keywords["harassment"]):
            scores["harassment"] = random.uniform(0.5, 0.8)
            scores["harassment_threatening"] = random.uniform(0.3, 0.6)

        # Harassment threatening keywords
        if any(
            word in text_lower
            for word in self.harmful_keywords["harassment_threatening"]
        ):
            scores["harassment_threatening"] = random.uniform(0.7, 0.95)
            # Also elevate base category if not already high
            scores["harassment"] = max(scores["harassment"], random.uniform(0.5, 0.7))

        # Illicit keywords
        if any(word in text_lower for word in self.harmful_keywords["illicit"]):
            scores["illicit"] = random.uniform(0.6, 0.9)

        # Illicit violent keywords
        if any(word in text_lower for word in self.harmful_keywords["illicit_violent"]):
            scores["illicit_violent"] = random.uniform(0.8, 0.98)
            # Also elevate base category if not already high
            scores["illicit"] = max(scores["illicit"], random.uniform(0.5, 0.7))

        # Minors keywords (only flag if sexual content is already detected)
        if (
            any(word in text_lower for word in self.harmful_keywords["sexual_minors"])
            and scores["sexual"] > 0.5
        ):
            scores["sexual_minors"] = random.uniform(0.7, 0.95)

        # Add noise for realism
        for key in scores:
            scores[key] += random.uniform(-0.0001, 0.0001)
            scores[key] = max(0.0, min(1.0, scores[key]))

        # Convert to slash format for API compatibility
        scores_with_slash = {k.replace("_", "/"): v for k, v in scores.items()}

        # Determine flags (threshold 0.5)
        categories = {k: (v > 0.5) for k, v in scores_with_slash.items()}

        return categories, scores_with_slash
