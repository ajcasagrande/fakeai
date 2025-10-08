"""Model discovery and fuzzy matching system.

This module provides intelligent model matching, normalization, and discovery
capabilities for the FakeAI models registry. It includes fuzzy matching algorithms,
model characteristic inference, and similarity-based suggestions.

Key Features:
- Fuzzy matching with multiple strategies (exact, normalized, substring, edit distance)
- Model ID normalization and standardization
- Automatic model characteristic inference (reasoning, MoE, vision, etc.)
- Similar model suggestions
- Fine-tuned model parsing (LoRA format)
- Learning-based matching with feedback

Example:
    >>> match, confidence = fuzzy_match_model("gpt4", ["gpt-4", "gpt-3.5-turbo"])
    >>> print(f"{match} (confidence: {confidence:.2f})")
    gpt-4 (confidence: 0.95)

    >>> base, org, job_id = parse_fine_tuned_model("ft:gpt-4:acme::abc123")
    >>> print(f"Base: {base}, Org: {org}, Job: {job_id}")
    Base: gpt-4, Org: acme, Job: abc123
"""

import difflib
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelCharacteristics:
    """Inferred characteristics of a model based on its ID.

    Attributes:
        is_reasoning: Whether the model supports reasoning/chain-of-thought
        is_moe: Whether the model uses Mixture of Experts architecture
        is_vision: Whether the model supports vision/image inputs
        is_audio: Whether the model supports audio inputs
        is_video: Whether the model supports video inputs
        is_fine_tuned: Whether this is a fine-tuned model
        base_model: Base model for fine-tuned models (None otherwise)
        estimated_size: Estimated parameter count (e.g., "120b", "7b")
        provider: Inferred provider (e.g., "openai", "meta", "anthropic")
    """

    is_reasoning: bool = False
    is_moe: bool = False
    is_vision: bool = False
    is_audio: bool = False
    is_video: bool = False
    is_fine_tuned: bool = False
    base_model: Optional[str] = None
    estimated_size: Optional[str] = None
    provider: Optional[str] = None


@dataclass
class FineTunedModelInfo:
    """Parsed information from a fine-tuned model ID.

    Format: ft:base_model:organization::job_id
    Example: ft:gpt-4:acme::abc123

    Attributes:
        base_model: The base model being fine-tuned
        organization: Organization that created the fine-tune
        job_id: Fine-tuning job identifier
        full_id: Original full model ID
    """

    base_model: str
    organization: str
    job_id: str
    full_id: str


@dataclass
class MatchResult:
    """Result of a fuzzy match operation.

    Attributes:
        matched_model: The model ID that was matched
        confidence: Match confidence score (0.0 to 1.0)
        strategy: Matching strategy used (exact, normalized, substring, edit_distance)
        normalized_query: Normalized version of the query
        normalized_match: Normalized version of the matched model
    """

    matched_model: str
    confidence: float
    strategy: str
    normalized_query: str
    normalized_match: str


class ModelMatcher:
    """Learning-based model matcher that improves over time.

    Tracks successful and failed matches to improve matching accuracy.
    Uses frequency analysis to prefer commonly used models in ambiguous cases.

    Example:
        >>> matcher = ModelMatcher()
        >>> match = matcher.match("gpt4", ["gpt-4", "gpt-40"])
        >>> matcher.record_success("gpt4", "gpt-4")
        >>> # Future matches of "gpt4" will prefer "gpt-4"
    """

    def __init__(self):
        """Initialize the matcher with empty learning data."""
        self.successful_matches: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self.failed_matches: set[tuple[str, str]] = set()
        self.model_usage_count: dict[str, int] = defaultdict(int)

    def match(
        self, query: str, available_models: list[str], threshold: float = 0.6
    ) -> Optional[MatchResult]:
        """Match a query to available models using learned preferences.

        Args:
            query: The model query string
            available_models: List of available model IDs
            threshold: Minimum confidence threshold (0.0 to 1.0)

        Returns:
            MatchResult if a match is found, None otherwise
        """
        # Check for learned matches first
        if query in self.successful_matches:
            learned_matches = self.successful_matches[query]
            # Sort by frequency, highest first
            sorted_matches = sorted(
                learned_matches.items(), key=lambda x: x[1], reverse=True
            )
            for model_id, count in sorted_matches:
                if model_id in available_models:
                    normalized_query = normalize_model_id(query)
                    normalized_match = normalize_model_id(model_id)
                    return MatchResult(
                        matched_model=model_id,
                        confidence=min(1.0, 0.8 + (count * 0.05)
                                       ),  # Boost by usage
                        strategy="learned",
                        normalized_query=normalized_query,
                        normalized_match=normalized_match,
                    )

        # Fall back to standard fuzzy matching
        match, confidence = fuzzy_match_model(
            query, available_models, threshold)
        if match:
            normalized_query = normalize_model_id(query)
            normalized_match = normalize_model_id(match)
            return MatchResult(
                matched_model=match,
                confidence=confidence,
                strategy="fuzzy",
                normalized_query=normalized_query,
                normalized_match=normalized_match,
            )

        return None

    def record_success(self, query: str, matched_model: str) -> None:
        """Record a successful match for learning.

        Args:
            query: The query string that was used
            matched_model: The model that was successfully matched
        """
        self.successful_matches[query][matched_model] += 1
        self.model_usage_count[matched_model] += 1

    def record_failure(self, query: str, attempted_model: str) -> None:
        """Record a failed match attempt.

        Args:
            query: The query string that was used
            attempted_model: The model that failed to match
        """
        self.failed_matches.add((query, attempted_model))

    def get_match_history(self, query: str) -> dict[str, int]:
        """Get the match history for a query.

        Args:
            query: The query string to look up

        Returns:
            Dictionary mapping model IDs to match counts
        """
        return dict(self.successful_matches.get(query, {}))

    def get_popular_models(self, limit: int = 10) -> list[tuple[str, int]]:
        """Get the most frequently used models.

        Args:
            limit: Maximum number of models to return

        Returns:
            List of (model_id, usage_count) tuples, sorted by usage
        """
        sorted_models = sorted(
            self.model_usage_count.items(), key=lambda x: x[1], reverse=True
        )
        return sorted_models[:limit]


def normalize_model_id(model_id: str) -> str:
    """Normalize a model ID for matching.

    Normalization steps:
    1. Convert to lowercase
    2. Remove provider prefixes (openai/, meta/, etc.)
    3. Standardize separators (convert _ to -, remove /)
    4. Remove version suffixes (-v1, -v2, etc.)
    5. Trim whitespace

    Args:
        model_id: The model ID to normalize

    Returns:
        Normalized model ID string

    Example:
        >>> normalize_model_id("OpenAI/GPT-4_turbo-v2")
        'gpt4turbo'
    """
    if not model_id:
        return ""

    # Convert to lowercase
    normalized = model_id.lower().strip()

    # Remove common provider prefixes
    provider_prefixes = [
        "openai/",
        "meta/",
        "anthropic/",
        "google/",
        "mistral/",
        "meta-llama/",
        "deepseek-ai/",
        "nvidia/",
        "cohere/",
    ]
    for prefix in provider_prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
            break

    # Remove version suffixes like -v1, -v2, etc.
    normalized = re.sub(r"-v\d+$", "", normalized)

    # Standardize separators: remove hyphens, underscores, and slashes
    normalized = normalized.replace("-", "").replace("_", "").replace("/", "")

    return normalized


def fuzzy_match_model(
    query: str, available_models: list[str], threshold: float = 0.6
) -> tuple[Optional[str], float]:
    """Match a query to the best available model using fuzzy matching.

    Uses four matching strategies in order of preference:
    1. Exact match (confidence: 1.0)
    2. Normalized match (confidence: 0.95)
    3. Substring match (confidence: 0.8 - 0.9)
    4. Edit distance match using SequenceMatcher (confidence: similarity ratio)

    Args:
        query: The model query string
        available_models: List of available model IDs
        threshold: Minimum confidence threshold (0.0 to 1.0)

    Returns:
        Tuple of (matched_model_id, confidence) or (None, 0.0) if no match

    Example:
        >>> models = ["gpt-4", "gpt-3.5-turbo", "claude-3"]
        >>> match, conf = fuzzy_match_model("gpt4", models)
        >>> print(f"{match}: {conf}")
        gpt-4: 0.95
    """
    if not query or not available_models:
        return None, 0.0

    # Strategy 1: Exact match
    if query in available_models:
        return query, 1.0

    # Strategy 2: Normalized match
    normalized_query = normalize_model_id(query)
    for model in available_models:
        if normalize_model_id(model) == normalized_query:
            return model, 0.95

    # Strategy 3: Substring match
    best_substring_match = None
    best_substring_confidence = 0.0

    query_lower = query.lower()
    normalized_query_lower = normalized_query.lower()

    for model in available_models:
        model_lower = model.lower()
        normalized_model = normalize_model_id(model).lower()

        # Check if query is substring of model
        if query_lower in model_lower:
            confidence = 0.85 + (len(query_lower) / len(model_lower)) * 0.1
            if confidence > best_substring_confidence:
                best_substring_match = model
                best_substring_confidence = confidence

        # Check if normalized query is substring of normalized model
        elif normalized_query_lower in normalized_model:
            confidence = (0.80 + (len(normalized_query_lower) /
                                  len(normalized_model)) * 0.1)
            if confidence > best_substring_confidence:
                best_substring_match = model
                best_substring_confidence = confidence

    if best_substring_match and best_substring_confidence >= threshold:
        return best_substring_match, best_substring_confidence

    # Strategy 4: Edit distance using SequenceMatcher
    best_edit_match = None
    best_edit_confidence = 0.0

    matcher = difflib.SequenceMatcher()
    matcher.set_seq2(normalized_query_lower)

    for model in available_models:
        normalized_model = normalize_model_id(model).lower()
        matcher.set_seq1(normalized_model)
        ratio = matcher.ratio()

        if ratio > best_edit_confidence:
            best_edit_match = model
            best_edit_confidence = ratio

    if best_edit_match and best_edit_confidence >= threshold:
        return best_edit_match, best_edit_confidence

    # No match found
    return None, 0.0


def infer_model_characteristics(model_id: str) -> ModelCharacteristics:
    """Infer model characteristics from its ID.

    Uses pattern matching on the model ID to detect:
    - Reasoning capabilities (gpt-oss, deepseek-r1, o1, o3)
    - MoE architecture (mixtral, gpt-oss, deepseek-v)
    - Vision support (vision, gpt-4o, gpt-4-turbo, claude-3, gemini)
    - Audio support (audio, whisper)
    - Video support (video, cosmos)
    - Fine-tuned status (ft: prefix)
    - Parameter size (extract numbers like 7b, 120b, 405b)
    - Provider (from prefix)

    Args:
        model_id: The model ID to analyze

    Returns:
        ModelCharacteristics object with inferred properties

    Example:
        >>> chars = infer_model_characteristics("openai/gpt-oss-120b")
        >>> print(f"Reasoning: {chars.is_reasoning}, MoE: {chars.is_moe}, Size: {chars.estimated_size}")
        Reasoning: True, MoE: True, Size: 120b
    """
    if not model_id:
        return ModelCharacteristics()

    model_lower = model_id.lower()
    chars = ModelCharacteristics()

    # Check for fine-tuned model
    if model_lower.startswith("ft:"):
        chars.is_fine_tuned = True
        parsed = parse_fine_tuned_model(model_id)
        if parsed:
            chars.base_model = parsed.base_model
            model_lower = parsed.base_model.lower()  # Analyze base model

    # Detect provider
    provider_patterns = {
        "openai": r"^(openai/|gpt-)",
        "meta": r"^(meta/|meta-llama/|llama-)",
        "anthropic": r"^(anthropic/|claude-)",
        "google": r"^(google/|gemini-|palm-)",
        "mistral": r"^(mistral/|mixtral-)",
        "deepseek": r"^(deepseek-ai/|deepseek-)",
        "nvidia": r"^(nvidia/|cosmos-)",
        "cohere": r"^(cohere/|command-)",
    }

    for provider, pattern in provider_patterns.items():
        if re.search(pattern, model_lower):
            chars.provider = provider
            break

    # Detect reasoning models
    reasoning_patterns = [
        r"gpt-oss",
        r"deepseek-r1",
        r"\bo1\b",
        r"\bo3\b",
        r"reasoning",
    ]
    chars.is_reasoning = any(
        re.search(pattern, model_lower) for pattern in reasoning_patterns
    )

    # Detect MoE models
    moe_patterns = [r"mixtral", r"gpt-oss", r"deepseek-v\d+", r"moe"]
    chars.is_moe = any(re.search(pattern, model_lower)
                       for pattern in moe_patterns)

    # Detect vision models
    vision_patterns = [
        r"vision",
        r"gpt-4o",
        r"gpt-4-turbo",
        r"claude-3",
        r"gemini",
        r"llava",
    ]
    chars.is_vision = any(
        re.search(pattern, model_lower) for pattern in vision_patterns
    )

    # Detect audio models
    audio_patterns = [r"audio", r"whisper", r"speech"]
    chars.is_audio = any(re.search(pattern, model_lower)
                         for pattern in audio_patterns)

    # Detect video models
    video_patterns = [r"video", r"cosmos"]
    chars.is_video = any(re.search(pattern, model_lower)
                         for pattern in video_patterns)

    # Extract parameter size
    size_match = re.search(r"(\d+)b\b", model_lower)
    if size_match:
        chars.estimated_size = f"{size_match.group(1)}b"

    return chars


def suggest_similar_models(
    query: str, all_models: list[str], limit: int = 5
) -> list[tuple[str, float]]:
    """Suggest similar models based on a query.

    Returns models ranked by similarity using the same fuzzy matching
    algorithms as fuzzy_match_model, but returns multiple results.

    Args:
        query: The model query string
        all_models: List of all available model IDs
        limit: Maximum number of suggestions to return

    Returns:
        List of (model_id, confidence) tuples, sorted by confidence descending

    Example:
        >>> models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3"]
        >>> suggestions = suggest_similar_models("gpt", models, limit=3)
        >>> for model, conf in suggestions:
        ...     print(f"{model}: {conf:.2f}")
        gpt-4: 0.90
        gpt-4-turbo: 0.88
        gpt-3.5-turbo: 0.85
    """
    if not query or not all_models:
        return []

    normalized_query = normalize_model_id(query).lower()
    query_lower = query.lower()

    # Calculate similarity for each model
    similarities: list[tuple[str, float]] = []
    matcher = difflib.SequenceMatcher()
    matcher.set_seq2(normalized_query)

    for model in all_models:
        model_lower = model.lower()
        normalized_model = normalize_model_id(model).lower()

        # Start with base edit distance similarity
        matcher.set_seq1(normalized_model)
        confidence = matcher.ratio()

        # Boost for exact match
        if query_lower == model_lower:
            confidence = 1.0
        # Boost for normalized exact match
        elif normalized_query == normalized_model:
            confidence = max(confidence, 0.95)
        # Boost for substring match
        elif query_lower in model_lower or normalized_query in normalized_model:
            substring_boost = (
                0.85 + (len(normalized_query) / len(normalized_model)) * 0.1
            )
            confidence = max(confidence, substring_boost)

        similarities.append((model, confidence))

    # Sort by confidence descending, then by model name for stability
    similarities.sort(key=lambda x: (-x[1], x[0]))

    return similarities[:limit]


def parse_fine_tuned_model(model_id: str) -> Optional[FineTunedModelInfo]:
    """Parse a fine-tuned model ID in LoRA format.

    Format: ft:base_model:organization::job_id
    Example: ft:gpt-4:acme::abc123

    Args:
        model_id: The fine-tuned model ID to parse

    Returns:
        FineTunedModelInfo object if parsing succeeds, None otherwise

    Example:
        >>> info = parse_fine_tuned_model("ft:gpt-4:acme::abc123")
        >>> print(f"Base: {info.base_model}, Org: {info.organization}")
        Base: gpt-4, Org: acme
    """
    if not model_id or not model_id.startswith("ft:"):
        return None

    # Remove "ft:" prefix
    remainder = model_id[3:]

    # Split by "::"
    if "::" not in remainder:
        return None

    before_double_colon, job_id = remainder.rsplit("::", 1)

    # Split remaining part by ":"
    parts = before_double_colon.split(":")

    if len(parts) < 2:
        return None

    base_model = parts[0]
    organization = parts[1]

    # Handle case where base_model might contain colons (e.g.,
    # provider/model:version)
    if len(parts) > 2:
        # Reconstruct base_model with all parts except the last (organization)
        base_model = ":".join(parts[:-1])
        organization = parts[-1]

    return FineTunedModelInfo(
        base_model=base_model,
        organization=organization,
        job_id=job_id,
        full_id=model_id,
    )
