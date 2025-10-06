"""
Tests for streaming chunking utilities.
"""

#  SPDX-License-Identifier: Apache-2.0

import time

import pytest

from fakeai.streaming.chunking import (
    AdaptiveChunker,
    DeltaGenerator,
    ProgressTracker,
    TokenChunker,
)


class TestTokenChunker:
    """Test TokenChunker class."""

    def test_tokenize_simple_text(self):
        """Test tokenizing simple text."""
        chunker = TokenChunker()
        tokens = chunker.tokenize("Hello world!")

        assert len(tokens) == 3
        assert tokens == ["Hello", "world", "!"]

    def test_tokenize_with_punctuation(self):
        """Test tokenizing text with punctuation."""
        chunker = TokenChunker()
        tokens = chunker.tokenize("Hello, how are you?")

        assert "Hello" in tokens
        assert "," in tokens
        assert "how" in tokens
        assert "?" in tokens

    def test_tokenize_empty_string(self):
        """Test tokenizing empty string."""
        chunker = TokenChunker()
        tokens = chunker.tokenize("")

        assert tokens == []

    def test_chunk_tokens(self):
        """Test chunking tokens."""
        chunker = TokenChunker(min_chunk_size=1, max_chunk_size=3)
        tokens = ["Hello", ",", "world", "!", "How", "are", "you", "?"]

        chunks = chunker.chunk_tokens(tokens)

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk) <= 3

    def test_chunk_text(self):
        """Test chunking text directly."""
        chunker = TokenChunker(min_chunk_size=1, max_chunk_size=5)
        text = "Hello world! How are you today?"

        chunks = chunker.chunk_text(text)

        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)

        # Verify we can reconstruct something similar
        reconstructed = " ".join(chunks)
        assert len(reconstructed) > 0


class TestDeltaGenerator:
    """Test DeltaGenerator class."""

    def test_generate_chat_delta_role(self):
        """Test generating chat delta with role."""
        generator = DeltaGenerator()
        delta = generator.generate_chat_delta(role="assistant")

        assert delta == {"role": "assistant"}

    def test_generate_chat_delta_content(self):
        """Test generating chat delta with content."""
        generator = DeltaGenerator()
        delta = generator.generate_chat_delta(content="Hello")

        assert delta == {"content": "Hello"}

    def test_generate_chat_delta_finish_reason(self):
        """Test generating chat delta with finish reason."""
        generator = DeltaGenerator()
        delta = generator.generate_chat_delta(finish_reason="stop")

        assert delta == {"finish_reason": "stop"}

    def test_generate_chat_delta_combined(self):
        """Test generating chat delta with multiple fields."""
        generator = DeltaGenerator()
        delta = generator.generate_chat_delta(
            role="assistant",
            content="Hello",
            finish_reason="stop",
        )

        assert delta["role"] == "assistant"
        assert delta["content"] == "Hello"
        assert delta["finish_reason"] == "stop"

    def test_generate_completion_delta(self):
        """Test generating completion delta."""
        generator = DeltaGenerator()
        delta = generator.generate_completion_delta(text="Hello")

        assert delta == {"text": "Hello"}

    def test_generate_audio_delta(self):
        """Test generating audio delta."""
        generator = DeltaGenerator()
        audio_data = b"audio_bytes"
        delta = generator.generate_audio_delta(
            audio_chunk=audio_data,
            transcript_delta="Hello",
        )

        assert delta["audio"] == audio_data
        assert delta["transcript"] == "Hello"

    def test_reset(self):
        """Test resetting delta generator."""
        generator = DeltaGenerator()
        generator._previous_state = {"test": "data"}

        generator.reset()

        assert generator._previous_state == {}


class TestProgressTracker:
    """Test ProgressTracker class."""

    def test_create_tracker(self):
        """Test creating progress tracker."""
        tracker = ProgressTracker(total_tokens=100)

        assert tracker.total_tokens == 100
        assert tracker.tokens_generated == 0
        assert tracker.chunks_generated == 0

    def test_record_chunk(self):
        """Test recording a chunk."""
        tracker = ProgressTracker(total_tokens=100)

        tracker.record_chunk(token_count=5)

        assert tracker.chunks_generated == 1
        assert tracker.tokens_generated == 5
        assert tracker.first_chunk_time is not None

    def test_progress_percentage(self):
        """Test calculating progress percentage."""
        tracker = ProgressTracker(total_tokens=100)

        tracker.record_chunk(token_count=25)
        assert tracker.progress_percentage() == 25.0

        tracker.record_chunk(token_count=50)
        assert tracker.progress_percentage() == 75.0

    def test_progress_percentage_exceeds_100(self):
        """Test progress percentage caps at 100."""
        tracker = ProgressTracker(total_tokens=100)

        tracker.record_chunk(token_count=150)
        assert tracker.progress_percentage() == 100.0

    def test_time_to_first_chunk(self):
        """Test time to first chunk calculation."""
        tracker = ProgressTracker(total_tokens=100)

        time.sleep(0.05)
        tracker.record_chunk(token_count=10)

        ttfc = tracker.time_to_first_chunk_ms()
        assert ttfc is not None
        assert ttfc >= 50  # At least 50ms

    def test_tokens_per_second(self):
        """Test tokens per second calculation."""
        tracker = ProgressTracker(total_tokens=100)

        tracker.record_chunk(token_count=10)
        time.sleep(0.1)
        tracker.record_chunk(token_count=10)

        tps = tracker.tokens_per_second()
        assert tps > 0
        # Should be around 100-200 tokens/sec given 20 tokens in 0.1s

    def test_estimated_time_remaining(self):
        """Test estimating time remaining."""
        tracker = ProgressTracker(total_tokens=100)

        tracker.record_chunk(token_count=25)
        time.sleep(0.1)
        tracker.record_chunk(token_count=25)

        remaining = tracker.estimated_time_remaining_seconds()
        assert remaining is not None
        assert remaining > 0

    def test_to_dict(self):
        """Test converting tracker to dictionary."""
        tracker = ProgressTracker(total_tokens=100)
        tracker.record_chunk(token_count=25)

        tracker_dict = tracker.to_dict()

        assert tracker_dict["total_tokens"] == 100
        assert tracker_dict["tokens_generated"] == 25
        assert tracker_dict["chunks_generated"] == 1
        assert "progress_percentage" in tracker_dict
        assert "tokens_per_second" in tracker_dict


class TestAdaptiveChunker:
    """Test AdaptiveChunker class."""

    def test_create_adaptive_chunker(self):
        """Test creating adaptive chunker."""
        chunker = AdaptiveChunker(
            initial_chunk_size=5,
            min_chunk_size=1,
            max_chunk_size=10,
        )

        assert chunker.current_chunk_size == 5
        assert chunker.min_chunk_size == 1
        assert chunker.max_chunk_size == 10

    def test_get_chunk_size(self):
        """Test getting current chunk size."""
        chunker = AdaptiveChunker(initial_chunk_size=5)

        assert chunker.get_chunk_size() == 5

    def test_adjust_chunk_size_too_fast(self):
        """Test adjusting chunk size when too fast."""
        chunker = AdaptiveChunker(
            initial_chunk_size=5,
            max_chunk_size=10,
            target_chunk_delay_ms=50.0,
        )

        # Simulate fast chunks (30ms < 50ms target)
        for _ in range(5):
            chunker.adjust_chunk_size(30.0)

        # Should increase chunk size
        assert chunker.get_chunk_size() > 5

    def test_adjust_chunk_size_too_slow(self):
        """Test adjusting chunk size when too slow."""
        chunker = AdaptiveChunker(
            initial_chunk_size=5,
            min_chunk_size=1,
            target_chunk_delay_ms=50.0,
        )

        # Simulate slow chunks (80ms > 50ms target)
        for _ in range(5):
            chunker.adjust_chunk_size(80.0)

        # Should decrease chunk size
        assert chunker.get_chunk_size() < 5

    def test_chunk_size_bounds(self):
        """Test chunk size respects min/max bounds."""
        chunker = AdaptiveChunker(
            initial_chunk_size=5,
            min_chunk_size=2,
            max_chunk_size=8,
        )

        # Try to increase beyond max
        for _ in range(20):
            chunker.adjust_chunk_size(10.0)  # Very fast

        assert chunker.get_chunk_size() <= 8

        # Try to decrease below min
        chunker.reset()
        chunker.current_chunk_size = 5
        for _ in range(20):
            chunker.adjust_chunk_size(200.0)  # Very slow

        assert chunker.get_chunk_size() >= 2

    def test_reset(self):
        """Test resetting adaptive chunker."""
        chunker = AdaptiveChunker()

        chunker.adjust_chunk_size(30.0)
        chunker.adjust_chunk_size(35.0)

        assert len(chunker._recent_delays) > 0

        chunker.reset()

        assert len(chunker._recent_delays) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
