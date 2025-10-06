"""
Tests for TTFT and ITL configuration.

Validates that --ttft and --itl CLI arguments work correctly with variance support.
"""

import time

import pytest

from fakeai import AppConfig
from fakeai.cli import parse_latency_spec
from fakeai.fakeai_service import FakeAIService
from fakeai.models import ChatCompletionRequest, Message, Role


class TestLatencySpecParsing:
    """Test parse_latency_spec function."""

    def test_simple_value(self):
        """Test simple number uses default 10% variance."""
        value, variance = parse_latency_spec("20")
        assert value == 20.0
        assert variance == 10.0

    def test_value_with_variance(self):
        """Test value:variance format."""
        value, variance = parse_latency_spec("30:5")
        assert value == 30.0
        assert variance == 5.0

    def test_zero_variance(self):
        """Test exact value with no jitter."""
        value, variance = parse_latency_spec("15:0")
        assert value == 15.0
        assert variance == 0.0

    def test_max_variance(self):
        """Test 100% variance."""
        value, variance = parse_latency_spec("50:100")
        assert value == 50.0
        assert variance == 100.0

    def test_float_values(self):
        """Test float values work."""
        value, variance = parse_latency_spec("12.5:7.5")
        assert value == 12.5
        assert variance == 7.5

    def test_invalid_format_raises(self):
        """Test invalid formats raise ValueError."""
        with pytest.raises(ValueError, match="Invalid latency spec"):
            parse_latency_spec("20:5:10")  # Too many colons

    def test_non_numeric_raises(self):
        """Test non-numeric values raise ValueError."""
        with pytest.raises(ValueError):
            parse_latency_spec("abc")

        with pytest.raises(ValueError):
            parse_latency_spec("20:xyz")

    def test_negative_value_raises(self):
        """Test negative values raise ValueError."""
        with pytest.raises(ValueError, match="must be >= 0"):
            parse_latency_spec("-10")

    def test_variance_out_of_range_raises(self):
        """Test variance outside 0-100 raises ValueError."""
        with pytest.raises(ValueError, match="0-100%"):
            parse_latency_spec("20:-5")

        with pytest.raises(ValueError, match="0-100%"):
            parse_latency_spec("20:150")


class TestTTFTConfiguration:
    """Test TTFT configuration."""

    def test_default_ttft(self):
        """Test default TTFT is 20ms with 10% variance."""
        config = AppConfig()
        assert config.ttft_ms == 20.0
        assert config.ttft_variance_percent == 10.0

    def test_custom_ttft_via_config(self):
        """Test setting TTFT via config."""
        config = AppConfig(ttft_ms=50.0, ttft_variance_percent=5.0)
        assert config.ttft_ms == 50.0
        assert config.ttft_variance_percent == 5.0

    @pytest.mark.asyncio
    async def test_ttft_affects_streaming(self):
        """Test TTFT config actually affects streaming timing."""
        config = AppConfig(
            response_delay=0.0,
            ttft_ms=100.0,  # 100ms
            ttft_variance_percent=0.0,  # No variance for predictable test
        )
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True,
        )

        start = time.time()
        first_content_time = None

        async for chunk in service.create_chat_completion_stream(request):
            # First chunk with content (not role) - this is after TTFT delay
            if (
                chunk.choices
                and chunk.choices[0].delta.content
                and first_content_time is None
            ):
                first_content_time = time.time()
                break

        if first_content_time:
            ttft_actual = (first_content_time - start) * 1000  # ms
            # Should be close to 100ms (within 20ms tolerance for overhead + jitter)
            assert (
                80 <= ttft_actual <= 120
            ), f"TTFT was {ttft_actual:.1f}ms, expected ~100ms"


class TestITLConfiguration:
    """Test ITL configuration."""

    def test_default_itl(self):
        """Test default ITL is 5ms with 10% variance."""
        config = AppConfig()
        assert config.itl_ms == 5.0
        assert config.itl_variance_percent == 10.0

    def test_custom_itl_via_config(self):
        """Test setting ITL via config."""
        config = AppConfig(itl_ms=10.0, itl_variance_percent=20.0)
        assert config.itl_ms == 10.0
        assert config.itl_variance_percent == 20.0

    @pytest.mark.asyncio
    async def test_itl_affects_streaming(self):
        """Test ITL config actually affects inter-token timing."""
        config = AppConfig(
            response_delay=0.0,
            itl_ms=50.0,  # 50ms
            itl_variance_percent=0.0,  # No variance
        )
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True,
            max_tokens=5,  # Just 5 tokens
        )

        token_times = []
        async for chunk in service.create_chat_completion_stream(request):
            if chunk.choices and chunk.choices[0].delta.content:
                token_times.append(time.time())

        # Calculate inter-token intervals
        if len(token_times) >= 2:
            itl_actual = (token_times[1] - token_times[0]) * 1000  # ms
            # Should be close to 50ms (within 10ms tolerance)
            assert 40 <= itl_actual <= 60, f"ITL was {itl_actual:.1f}ms, expected ~50ms"


class TestVarianceRange:
    """Test variance produces values in correct range."""

    @pytest.mark.asyncio
    async def test_ttft_variance_range(self):
        """Test TTFT variance produces values in expected range."""
        config = AppConfig(
            response_delay=0.0,
            ttft_ms=100.0,
            ttft_variance_percent=20.0,  # ±20%
        )
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True,
        )

        # Collect 10 TTFT samples
        ttft_samples = []
        for i in range(10):
            start = time.time()
            first_content = None

            async for chunk in service.create_chat_completion_stream(request):
                # Measure to first content chunk (after TTFT delay)
                if (
                    chunk.choices
                    and chunk.choices[0].delta.content
                    and first_content is None
                ):
                    first_content = time.time()
                    break

            if first_content:
                ttft_ms = (first_content - start) * 1000
                ttft_samples.append(ttft_ms)

        # All samples should be in range [75, 125] (100ms ± 20% + overhead)
        assert all(
            75 <= s <= 125 for s in ttft_samples
        ), f"TTFT samples {ttft_samples} should all be in [75, 125]ms"

    @pytest.mark.asyncio
    async def test_zero_variance_exact(self):
        """Test 0% variance produces exact value."""
        config = AppConfig(
            response_delay=0.0,
            ttft_ms=50.0,
            ttft_variance_percent=0.0,  # No variance
        )
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Test")],
            stream=True,
        )

        # Sample TTFT
        start = time.time()
        first_content = None

        async for chunk in service.create_chat_completion_stream(request):
            # Measure to first content (after TTFT delay)
            if (
                chunk.choices
                and chunk.choices[0].delta.content
                and first_content is None
            ):
                first_content = time.time()
                break

        if first_content:
            ttft_ms = (first_content - start) * 1000
            # With 0% variance, should be exactly 50ms (within system overhead tolerance)
            assert (
                48 <= ttft_ms <= 55
            ), f"TTFT with 0% variance was {ttft_ms:.1f}ms, expected ~50ms"


class TestCLIIntegration:
    """Test CLI argument parsing integration."""

    def test_cli_ttft_simple(self):
        """Test --ttft with simple value."""
        from fakeai.cli import parse_latency_spec

        value, variance = parse_latency_spec("25")
        assert value == 25.0
        assert variance == 10.0

    def test_cli_ttft_with_variance(self):
        """Test --ttft with variance."""
        value, variance = parse_latency_spec("30:15")
        assert value == 30.0
        assert variance == 15.0

    def test_cli_itl_simple(self):
        """Test --itl with simple value."""
        value, variance = parse_latency_spec("8")
        assert value == 8.0
        assert variance == 10.0

    def test_cli_itl_with_variance(self):
        """Test --itl with variance."""
        value, variance = parse_latency_spec("12:25")
        assert value == 12.0
        assert variance == 25.0


class TestEndToEnd:
    """End-to-end tests with different configurations."""

    @pytest.mark.asyncio
    async def test_ultra_fast_config(self):
        """Test ultra-fast configuration (1ms TTFT, 0.5ms ITL)."""
        config = AppConfig(
            response_delay=0.0,
            ttft_ms=1.0,
            ttft_variance_percent=0.0,
            itl_ms=0.5,
            itl_variance_percent=0.0,
        )
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Fast")],
            stream=True,
            max_tokens=10,
        )

        start = time.time()
        chunk_count = 0

        async for chunk in service.create_chat_completion_stream(request):
            if chunk.choices and chunk.choices[0].delta.content:
                chunk_count += 1

        elapsed_ms = (time.time() - start) * 1000

        # Total time should be approximately: 1ms TTFT + (10 tokens × 0.5ms)
        # = 1 + 5 = 6ms (allow for overhead, should be < 20ms)
        assert elapsed_ms < 20, f"Ultra-fast config took {elapsed_ms:.1f}ms"

    @pytest.mark.asyncio
    async def test_slow_config(self):
        """Test slow configuration (200ms TTFT, 50ms ITL)."""
        config = AppConfig(
            response_delay=0.0,
            ttft_ms=200.0,
            ttft_variance_percent=0.0,
            itl_ms=50.0,
            itl_variance_percent=0.0,
        )
        service = FakeAIService(config)

        request = ChatCompletionRequest(
            model="openai/gpt-oss-120b",
            messages=[Message(role=Role.USER, content="Slow")],
            stream=True,
            max_tokens=5,
        )

        start = time.time()
        chunk_count = 0

        async for chunk in service.create_chat_completion_stream(request):
            if chunk.choices and chunk.choices[0].delta.content:
                chunk_count += 1

        elapsed_ms = (time.time() - start) * 1000

        # Total time should be approximately: 200ms TTFT + (5 tokens × 50ms)
        # = 200 + 250 = 450ms (should be > 400ms)
        assert (
            elapsed_ms >= 400
        ), f"Slow config only took {elapsed_ms:.1f}ms, expected > 400ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
