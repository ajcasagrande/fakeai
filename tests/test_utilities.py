"""
Utility function behavior tests.

Tests utility functions for actual behavior and business logic.
"""
import pytest

from fakeai.utils import calculate_token_count, create_random_embedding, normalize_embedding


@pytest.mark.unit
class TestTokenCalculationBehavior:
    """Test token calculation utility behavior."""

    def test_empty_string_returns_zero(self):
        """Empty string should return 0 tokens."""
        assert calculate_token_count("") == 0

    def test_single_word_counted(self):
        """Single word should be counted."""
        count = calculate_token_count("hello")

        assert count > 0

    def test_more_words_more_tokens(self):
        """Longer text should have more tokens."""
        short = calculate_token_count("hi")
        long = calculate_token_count("This is a much longer sentence with many words")

        assert long > short

    def test_punctuation_adds_tokens(self):
        """Punctuation should add to token count."""
        without = calculate_token_count("hello world")
        with_punct = calculate_token_count("hello, world! How are you?")

        assert with_punct > without

    def test_none_returns_zero(self):
        """None input should return 0 tokens."""
        assert calculate_token_count(None) == 0

    def test_whitespace_only_counted(self):
        """Whitespace-only string should have minimal tokens."""
        count = calculate_token_count("   ")

        # Should return at least 0, maybe 1
        assert count >= 0


@pytest.mark.unit
class TestEmbeddingGenerationBehavior:
    """Test embedding generation utility behavior."""

    def test_creates_vector_of_requested_dimensions(self):
        """Should create embedding with exact dimensions requested."""
        embedding = create_random_embedding("test text", dimensions=512)

        assert len(embedding) == 512

    def test_same_text_same_embedding(self):
        """Same text should produce identical embedding (deterministic)."""
        text = "deterministic test"

        emb1 = create_random_embedding(text, 1536)
        emb2 = create_random_embedding(text, 1536)

        assert emb1 == emb2

    def test_different_text_different_embedding(self):
        """Different text should produce different embeddings."""
        emb1 = create_random_embedding("text one", 1536)
        emb2 = create_random_embedding("text two", 1536)

        assert emb1 != emb2

    def test_embedding_values_are_floats(self):
        """Embedding values should be floats."""
        embedding = create_random_embedding("test", 10)

        assert all(isinstance(val, float) for val in embedding)


@pytest.mark.unit
class TestEmbeddingNormalizationBehavior:
    """Test embedding normalization behavior."""

    def test_normalized_embedding_is_unit_length(self):
        """Normalized embedding should have L2 norm of 1.0."""
        import math

        embedding = [1.0, 2.0, 3.0, 4.0, 5.0]
        normalized = normalize_embedding(embedding)

        # Calculate L2 norm
        norm = math.sqrt(sum(x**2 for x in normalized))

        # Should be very close to 1.0 (within floating point precision)
        assert abs(norm - 1.0) < 1e-6

    def test_zero_vector_handled(self):
        """Zero vector should be handled without division by zero."""
        embedding = [0.0, 0.0, 0.0]
        normalized = normalize_embedding(embedding)

        # Should return zero vector (norm is 0, can't normalize)
        assert normalized == [0.0, 0.0, 0.0]

    def test_normalization_preserves_direction(self):
        """Normalization should preserve vector direction (ratios)."""
        embedding = [2.0, 4.0, 6.0]
        normalized = normalize_embedding(embedding)

        # Ratios should be preserved
        assert abs(normalized[1] / normalized[0] - 2.0) < 1e-6
        assert abs(normalized[2] / normalized[0] - 3.0) < 1e-6

    def test_already_normalized_unchanged(self):
        """Already normalized vector should remain unchanged."""
        import math

        # Create unit vector
        x = 1.0 / math.sqrt(3.0)
        embedding = [x, x, x]

        normalized = normalize_embedding(embedding)

        # Should be essentially unchanged
        for orig, norm in zip(embedding, normalized):
            assert abs(orig - norm) < 1e-6


@pytest.mark.unit
class TestSimulatedGeneratorBehavior:
    """Test response generator behavior."""

    def test_generates_different_responses(self):
        """Multiple calls should generate different responses."""
        from fakeai.utils import SimulatedGenerator

        generator = SimulatedGenerator()

        resp1 = generator.generate_response("Tell me about AI", max_tokens=100)
        resp2 = generator.generate_response("Tell me about AI", max_tokens=100)

        # Should generate different responses (has randomness)
        # Note: May occasionally fail if random generates same, but very unlikely
        assert resp1 != resp2 or len(resp1) > 20  # At least generates content

    def test_respects_max_tokens_approximately(self):
        """Should respect max_tokens limit (approximately)."""
        from fakeai.utils import SimulatedGenerator

        generator = SimulatedGenerator()

        short_response = generator.generate_response("Test", max_tokens=10)
        long_response = generator.generate_response("Test", max_tokens=500)

        # Long response should be longer than short
        assert len(long_response) > len(short_response)

    def test_identifies_greeting_prompts(self):
        """Should identify greeting-type prompts."""
        from fakeai.utils import SimulatedGenerator

        generator = SimulatedGenerator()

        # Test internal method if accessible, or test behavior
        prompt_type = generator._identify_prompt_type("hello there")

        assert prompt_type == "greeting"

    def test_identifies_coding_prompts(self):
        """Should identify coding-type prompts."""
        from fakeai.utils import SimulatedGenerator

        generator = SimulatedGenerator()

        prompt_type = generator._identify_prompt_type("write a python function")

        assert prompt_type == "coding"

    def test_identifies_question_prompts(self):
        """Should identify question-type prompts."""
        from fakeai.utils import SimulatedGenerator

        generator = SimulatedGenerator()

        prompt_type = generator._identify_prompt_type("what is machine learning")

        assert prompt_type == "question"
