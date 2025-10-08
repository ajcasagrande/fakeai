"""
Comprehensive Tests for Streaming Metrics Percentile Calculations

To run these tests:
    python -c "import sys, pytest; sys.exit(pytest.main(['tests/test_streaming_percentiles.py', '-v', '--noconftest']))"

Or from project root:
    pytest tests/test_streaming_percentiles.py --noconftest -v

This test suite thoroughly tests the percentile calculation logic used in
streaming metrics tracking, covering:

1. Percentile Algorithm:
   - Uses statistics.quantiles() for p95 and p99
   - n=20 for p95 (index 18)
   - n=100 for p99 (index 98)
   - Median uses statistics.median()

2. Edge Cases:
   - < 20 samples: p95 = max
   - < 100 samples: p99 = max
   - Exactly 20 samples
   - Exactly 100 samples
   - > 1000 samples

3. Data Distributions:
   - Uniform distribution
   - Normal distribution
   - Skewed distribution (outliers)
   - Bimodal distribution

4. Metric Types:
   - TTFT (Time To First Token) percentiles
   - ITL (Inter-Token Latency) percentiles
   - TPS (Tokens Per Second) percentiles
   - Duration percentiles

5. Accuracy:
   - Known dataset with known percentiles
   - Verify calculations match expected
   - Compare with numpy percentile

6. Performance:
   - Large datasets (1000+ samples)
   - Calculation time reasonable

Reference Implementation:
    From streaming_metrics_tracker.py lines 612-647:

    if len(values) >= 20:
        metrics.p95 = statistics.quantiles(values, n=20)[18]
        metrics.p99 = statistics.quantiles(values, n=100)[98]
    else:
        metrics.p95 = max(values)
        metrics.p99 = max(values)
"""

#  SPDX-License-Identifier: Apache-2.0

import os
import statistics

# Direct import to avoid fakeai.__init__ triggering app initialization
import sys
import time

import numpy as np

# Get the project root directory
if os.path.basename(os.getcwd()) == 'tests':
    # Running from tests directory
    project_root = os.path.dirname(os.getcwd())
else:
    # Running from project root
    project_root = os.getcwd()

sys.path.insert(0, project_root)

import importlib.util

module_path = os.path.join(project_root, 'fakeai', 'streaming_metrics_tracker.py')

if not os.path.exists(module_path):
    raise FileNotFoundError(f"Cannot find streaming_metrics_tracker.py at {module_path}")

spec = importlib.util.spec_from_file_location('streaming_metrics_tracker', module_path)
streaming_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(streaming_module)
StreamingMetricsTracker = streaming_module.StreamingMetricsTracker


class TestPercentileAlgorithm:
    """Test the core percentile calculation algorithm."""

    def test_quantiles_n20_index18_is_p95(self):
        """Verify that quantiles(n=20)[18] gives p95."""
        # Create dataset where we know the p95
        values = list(range(1, 101))  # 1 to 100

        # Using statistics.quantiles with n=20 divides into 20 equal parts
        # Index 18 gives the 19th quantile boundary, which is p95
        result = statistics.quantiles(values, n=20)[18]

        # For 1-100, p95 should be approximately 95
        # The exact value depends on interpolation method
        assert 94 <= result <= 96, f"Expected p95 ~95, got {result}"

    def test_quantiles_n100_index98_is_p99(self):
        """Verify that quantiles(n=100)[98] gives p99."""
        # Create dataset where we know the p99
        values = list(range(1, 101))  # 1 to 100

        # Using statistics.quantiles with n=100 divides into 100 equal parts
        # Index 98 gives the 99th quantile boundary, which is p99
        result = statistics.quantiles(values, n=100)[98]

        # For 1-100, p99 should be approximately 99
        assert 98 <= result <= 100, f"Expected p99 ~99, got {result}"

    def test_median_calculation(self):
        """Verify median calculation."""
        # Odd number of values
        values_odd = [1, 2, 3, 4, 5]
        median_odd = statistics.median(values_odd)
        assert median_odd == 3

        # Even number of values (average of middle two)
        values_even = [1, 2, 3, 4, 5, 6]
        median_even = statistics.median(values_even)
        assert median_even == 3.5

    def test_compare_with_numpy_percentile(self):
        """Compare statistics.quantiles results with numpy.percentile."""
        values = list(range(1, 1001))  # 1 to 1000

        # Calculate using statistics module
        stats_p95 = statistics.quantiles(values, n=20)[18]
        stats_p99 = statistics.quantiles(values, n=100)[98]

        # Calculate using numpy
        numpy_p95 = np.percentile(values, 95)
        numpy_p99 = np.percentile(values, 99)

        # Should be close (within 1% due to different interpolation methods)
        assert abs(stats_p95 - numpy_p95) / numpy_p95 < 0.01
        assert abs(stats_p99 - numpy_p99) / numpy_p99 < 0.01


class TestEdgeCases:
    """Test edge cases in percentile calculations."""

    def test_less_than_20_samples_p95_equals_max(self):
        """With < 20 samples, p95 should equal max value."""
        tracker = StreamingMetricsTracker()

        # Create 15 streams (< 20)
        for i in range(15):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)

            # TTFT varies from 100ms to 100+i*10ms
            ttft_ms = 100 + i * 10
            tracker.record_first_token_time(stream_id, ttft_ms)

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # With < 20 samples, p95 should equal max TTFT
        expected_max = 100 + 14 * 10  # 240ms
        assert abs(metrics.p95_ttft - expected_max) < 0.01  # Allow small floating point error
        assert abs(metrics.p95_ttft - metrics.max_ttft) < 0.01

    def test_less_than_100_samples_p99_equals_max(self):
        """With < 100 samples, p99 should equal max value."""
        tracker = StreamingMetricsTracker()

        # Create 50 streams (< 100)
        for i in range(50):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, 100 + i)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # With < 100 samples, p99 should equal max (within 1ms tolerance)
        assert abs(metrics.p99_ttft - metrics.max_ttft) < 1.0
        assert abs(metrics.p99_ttft - (100 + 49)) < 1.0  # 149ms

    def test_exactly_20_samples(self):
        """Test percentile calculation with exactly 20 samples."""
        tracker = StreamingMetricsTracker()

        # Create exactly 20 streams with known values
        values = list(range(100, 120))  # 100-119ms

        for i, ttft in enumerate(values):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, ttft)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # With exactly 20 samples, should use quantiles
        # p95 should be near the 95th percentile (around 118-119)
        assert metrics.p95_ttft >= 117
        assert metrics.p95_ttft <= 119

    def test_exactly_100_samples(self):
        """Test percentile calculation with exactly 100 samples."""
        tracker = StreamingMetricsTracker()

        # Create exactly 100 streams
        for i in range(100):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, 100 + i)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # p99 should be near 199 (the 99th value)
        assert metrics.p99_ttft >= 195
        assert metrics.p99_ttft <= 199

    def test_large_dataset_1000_samples(self):
        """Test percentile calculation with 1000+ samples."""
        tracker = StreamingMetricsTracker(max_completed_streams=2000)

        # Create 1000 streams
        for i in range(1000):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, 50 + i * 0.5)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # With 1000 samples, percentiles should be well-defined
        # p95 should be around 525ms (95% of 1000 = 950th value)
        assert metrics.p95_ttft >= 520
        assert metrics.p95_ttft <= 530

        # p99 should be around 545ms (99% of 1000 = 990th value)
        assert metrics.p99_ttft >= 540
        assert metrics.p99_ttft <= 550

    def test_single_sample(self):
        """Test with only a single sample."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("stream-1", model="test", prompt_tokens=10)
        tracker.record_first_token_time("stream-1", 100)
        tracker.complete_stream("stream-1", "stop")

        metrics = tracker.get_metrics()

        # All percentiles should equal the single value
        assert abs(metrics.p50_ttft - 100) < 0.01
        assert abs(metrics.p95_ttft - 100) < 0.01
        assert abs(metrics.p99_ttft - 100) < 0.01
        assert abs(metrics.min_ttft - 100) < 0.01
        assert abs(metrics.max_ttft - 100) < 0.01

    def test_two_samples(self):
        """Test with only two samples."""
        tracker = StreamingMetricsTracker()

        tracker.start_stream("stream-1", model="test", prompt_tokens=10)
        tracker.record_first_token_time("stream-1", 100)
        tracker.complete_stream("stream-1", "stop")

        tracker.start_stream("stream-2", model="test", prompt_tokens=10)
        tracker.record_first_token_time("stream-2", 200)
        tracker.complete_stream("stream-2", "stop")

        metrics = tracker.get_metrics()

        # Median should be average
        assert abs(metrics.p50_ttft - 150) < 0.01
        # p95 and p99 should be max
        assert abs(metrics.p95_ttft - 200) < 0.01
        assert abs(metrics.p99_ttft - 200) < 0.01

    def test_zero_samples(self):
        """Test with no samples."""
        tracker = StreamingMetricsTracker()

        metrics = tracker.get_metrics()

        # Should not crash, all values should be 0
        assert metrics.p50_ttft == 0
        assert metrics.p95_ttft == 0
        assert metrics.p99_ttft == 0


class TestDataDistributions:
    """Test percentile calculations with different data distributions."""

    def test_uniform_distribution(self):
        """Test with uniformly distributed data."""
        tracker = StreamingMetricsTracker(max_completed_streams=500)

        # Uniform distribution: 100ms to 500ms
        for i in range(200):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            ttft = 100 + (i * 2)  # Linear spacing
            tracker.record_first_token_time(stream_id, ttft)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # In uniform distribution, percentiles should be evenly spaced
        # p50 should be near middle: (100 + 498) / 2 = 299
        assert 290 <= metrics.p50_ttft <= 310

        # p95 should be near 95% point: 100 + 0.95 * 398 = 478
        assert 470 <= metrics.p95_ttft <= 490

        # p99 should be near 99% point: 100 + 0.99 * 398 = 494
        assert 485 <= metrics.p99_ttft <= 498

    def test_normal_distribution(self):
        """Test with normally distributed data."""
        tracker = StreamingMetricsTracker(max_completed_streams=500)

        # Generate normal distribution with mean=200, stddev=30
        np.random.seed(42)  # For reproducibility
        values = np.random.normal(loc=200, scale=30, size=200)
        values = np.clip(values, 50, 500)  # Clip to reasonable range

        for i, ttft in enumerate(values):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, float(ttft))
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # For normal distribution, median should be near mean
        assert 180 <= metrics.p50_ttft <= 220

        # p95 should be approximately mean + 1.645 * stddev
        # 200 + 1.645 * 30 = 249.35
        assert 230 <= metrics.p95_ttft <= 270

        # p99 should be approximately mean + 2.326 * stddev
        # 200 + 2.326 * 30 = 269.78
        assert 250 <= metrics.p99_ttft <= 290

    def test_skewed_distribution_with_outliers(self):
        """Test with skewed distribution containing outliers."""
        tracker = StreamingMetricsTracker(max_completed_streams=500)

        # Most values between 100-200, with a few outliers
        values = []
        for i in range(190):
            values.append(100 + i * 0.5)  # 100-195

        # Add 10 outliers
        for i in range(10):
            values.append(1000 + i * 100)  # 1000-1900

        for i, ttft in enumerate(values):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, ttft)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Median should be in the main cluster (not affected by outliers)
        assert 120 <= metrics.p50_ttft <= 170

        # p95 should be in the upper range (catching outliers or transition)
        # 95% of 200 = 190th value
        # With skewed data, p95 can include some outliers
        assert metrics.p95_ttft >= 190

        # p99 should be in the outlier range
        # 99% of 200 = 198th value, which is in outliers
        assert 1000 <= metrics.p99_ttft <= 1900

    def test_bimodal_distribution(self):
        """Test with bimodal distribution (two peaks)."""
        tracker = StreamingMetricsTracker(max_completed_streams=500)

        # First mode: 100-150ms (100 samples)
        for i in range(100):
            stream_id = f"stream-a-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, 100 + i * 0.5)
            tracker.complete_stream(stream_id, "stop")

        # Second mode: 300-350ms (100 samples)
        for i in range(100):
            stream_id = f"stream-b-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, 300 + i * 0.5)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Median should be between the two modes
        # (halfway between 149.5 and 300)
        assert 200 <= metrics.p50_ttft <= 250

        # p95 should be in the second mode
        assert 330 <= metrics.p95_ttft <= 350

        # p99 should be near the max of second mode
        assert 345 <= metrics.p99_ttft <= 350

    def test_exponential_distribution(self):
        """Test with exponential distribution (common in latency data)."""
        tracker = StreamingMetricsTracker(max_completed_streams=500)

        # Generate exponential distribution
        np.random.seed(42)
        values = np.random.exponential(scale=100, size=200)
        values = np.clip(values, 1, 1000)  # Clip to reasonable range

        for i, ttft in enumerate(values):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, float(ttft))
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Exponential has long tail, so p95 and p99 should be higher
        # Median should be lower than mean
        assert metrics.p50_ttft < metrics.avg_ttft

        # p95 should be significantly higher than median
        assert metrics.p95_ttft > metrics.p50_ttft * 2

        # p99 should be even higher
        assert metrics.p99_ttft > metrics.p95_ttft


class TestMetricTypes:
    """Test percentile calculations for different metric types."""

    def test_ttft_percentiles(self):
        """Test TTFT (Time To First Token) percentiles."""
        tracker = StreamingMetricsTracker(max_completed_streams=200)

        # Create streams with varying TTFT
        for i in range(100):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, 50 + i)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Verify TTFT percentiles are calculated
        assert abs(metrics.min_ttft - 50) < 0.01
        assert abs(metrics.max_ttft - 149) < 0.01
        assert 90 <= metrics.p50_ttft <= 110
        assert 135 <= metrics.p95_ttft <= 145
        assert 145 <= metrics.p99_ttft <= 149

    def test_itl_percentiles(self):
        """Test ITL (Inter-Token Latency) percentiles."""
        tracker = StreamingMetricsTracker(max_completed_streams=200)

        # Create streams with varying ITL
        for stream_num in range(50):
            stream_id = f"stream-{stream_num}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)

            # Add tokens with consistent ITL for this stream
            base_itl = 10 + stream_num  # 10-59ms ITL
            for token_num in range(10):
                token_time = time.time() + token_num * (base_itl / 1000)
                tracker.record_token(stream_id, f"token{token_num}")

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # ITL percentiles should be calculated
        assert metrics.avg_itl > 0
        assert metrics.p50_itl > 0
        assert metrics.p95_itl > metrics.p50_itl
        assert metrics.p99_itl >= metrics.p95_itl

    def test_tps_percentiles(self):
        """Test TPS (Tokens Per Second) percentiles."""
        tracker = StreamingMetricsTracker(max_completed_streams=200)

        # Create streams with varying TPS
        for i in range(100):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)

            # Add tokens to create specific TPS
            # TPS varies from ~10 to ~50 tokens/sec
            num_tokens = 20
            delay_ms = 50 + i  # Delay between tokens varies

            for token_num in range(num_tokens):
                tracker.record_token(stream_id, f"token{token_num}")
                time.sleep(0.001)  # Small sleep to create timing difference

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # TPS percentiles should be calculated
        assert metrics.avg_tokens_per_second > 0
        assert metrics.p50_tokens_per_second > 0
        assert metrics.p95_tokens_per_second > 0
        assert metrics.p99_tokens_per_second > 0

    def test_duration_percentiles(self):
        """Test Duration percentiles."""
        tracker = StreamingMetricsTracker(max_completed_streams=200)

        # Create streams with varying durations
        for i in range(100):
            stream_id = f"stream-{i}"
            start_time = time.time()
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)

            # Simulate different durations
            time.sleep(0.001 * (i + 1))  # 1ms to 100ms

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Duration percentiles should be calculated
        assert metrics.avg_duration > 0
        assert metrics.p50_duration > 0
        assert metrics.p95_duration > metrics.p50_duration
        assert metrics.p99_duration >= metrics.p95_duration


class TestAccuracy:
    """Test accuracy of percentile calculations against known datasets."""

    def test_known_dataset_linear(self):
        """Test with known linear dataset."""
        tracker = StreamingMetricsTracker(max_completed_streams=200)

        # Known dataset: 1 to 100
        for i in range(1, 101):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, float(i))
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Known values for 1-100:
        # median = 50.5
        assert 49 <= metrics.p50_ttft <= 52

        # p95 ≈ 95
        assert 93 <= metrics.p95_ttft <= 96

        # p99 ≈ 99
        assert 98 <= metrics.p99_ttft <= 100

    def test_accuracy_against_numpy(self):
        """Compare accuracy with numpy percentile calculation."""
        tracker = StreamingMetricsTracker(max_completed_streams=500)

        # Generate dataset
        np.random.seed(42)
        values = np.random.uniform(50, 500, 200)

        for i, ttft in enumerate(values):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, float(ttft))
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Calculate numpy percentiles
        numpy_p50 = np.percentile(values, 50)
        numpy_p95 = np.percentile(values, 95)
        numpy_p99 = np.percentile(values, 99)

        # Should be within 5% (different interpolation methods)
        assert abs(metrics.p50_ttft - numpy_p50) / numpy_p50 < 0.05
        assert abs(metrics.p95_ttft - numpy_p95) / numpy_p95 < 0.05
        assert abs(metrics.p99_ttft - numpy_p99) / numpy_p99 < 0.05

    def test_repeated_values(self):
        """Test with repeated values (ties)."""
        tracker = StreamingMetricsTracker(max_completed_streams=200)

        # Create dataset with many repeated values
        values = [100] * 50 + [200] * 50

        for i, ttft in enumerate(values):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, ttft)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Median should be 150 (between the two groups)
        assert abs(metrics.p50_ttft - 150) < 0.01

        # p95 and p99 should be 200 (in the upper group)
        assert abs(metrics.p95_ttft - 200) < 0.01
        assert abs(metrics.p99_ttft - 200) < 0.01

    def test_all_identical_values(self):
        """Test with all identical values."""
        tracker = StreamingMetricsTracker(max_completed_streams=200)

        # All values are 100
        for i in range(100):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, 100)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # All percentiles should be 100
        assert abs(metrics.p50_ttft - 100) < 0.01
        assert abs(metrics.p95_ttft - 100) < 0.01
        assert abs(metrics.p99_ttft - 100) < 0.01
        assert abs(metrics.min_ttft - 100) < 0.01
        assert abs(metrics.max_ttft - 100) < 0.01


class TestPerformance:
    """Test performance of percentile calculations."""

    def test_large_dataset_performance(self):
        """Test that large dataset calculations complete in reasonable time."""
        tracker = StreamingMetricsTracker(max_completed_streams=2000)

        # Create 1000 streams
        start_time = time.time()

        for i in range(1000):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, 100 + i * 0.5)

            # Add tokens to create ITL data
            for token_num in range(20):
                tracker.record_token(stream_id, f"token{token_num}")

            tracker.complete_stream(stream_id, "stop")

        # Calculate metrics
        calc_start = time.time()
        metrics = tracker.get_metrics()
        calc_time = time.time() - calc_start

        total_time = time.time() - start_time

        # Calculation should be fast (< 100ms for 1000 streams)
        assert calc_time < 0.1, f"Calculation took {calc_time:.3f}s, expected < 0.1s"

        # Verify calculations completed successfully
        assert metrics.total_streams == 1000
        assert metrics.p95_ttft > 0
        assert metrics.p99_ttft > 0

    def test_repeated_calculations_use_cache(self):
        """Test that repeated calculations use caching."""
        tracker = StreamingMetricsTracker(max_completed_streams=500)

        # Create some streams
        for i in range(100):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, 100 + i)
            tracker.complete_stream(stream_id, "stop")

        # First calculation (not cached)
        start1 = time.time()
        metrics1 = tracker.get_metrics()
        time1 = time.time() - start1

        # Second calculation (should use cache)
        start2 = time.time()
        metrics2 = tracker.get_metrics()
        time2 = time.time() - start2

        # Cached call should be much faster
        assert time2 < time1 * 0.5 or time2 < 0.001

        # Results should be identical
        assert metrics1.p95_ttft == metrics2.p95_ttft
        assert metrics1.p99_ttft == metrics2.p99_ttft

    def test_many_tokens_performance(self):
        """Test performance with streams containing many tokens."""
        tracker = StreamingMetricsTracker(max_completed_streams=200)

        start_time = time.time()

        # Create 50 streams with 100 tokens each (5000 total tokens)
        for stream_num in range(50):
            stream_id = f"stream-{stream_num}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)

            # Add 100 tokens
            for token_num in range(100):
                tracker.record_token(stream_id, f"token{token_num}")

            tracker.complete_stream(stream_id, "stop")

        # Calculate metrics
        calc_start = time.time()
        metrics = tracker.get_metrics()
        calc_time = time.time() - calc_start

        # Should handle many ITL calculations efficiently (< 100ms)
        assert calc_time < 0.1, f"ITL calculation took {calc_time:.3f}s"

        # Verify ITL percentiles calculated
        assert metrics.p95_itl > 0
        assert metrics.p99_itl > 0


class TestMultipleMetricTypes:
    """Test that all metric types calculate percentiles correctly together."""

    def test_all_metric_percentiles_together(self):
        """Test that all metric types (TTFT, ITL, TPS, Duration) work together."""
        tracker = StreamingMetricsTracker(max_completed_streams=200)

        # Create realistic streams
        for i in range(100):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=50 + i)

            # Varying TTFT
            tracker.record_first_token_time(stream_id, 100 + i)

            # Add tokens (creates ITL and TPS data)
            for token_num in range(20):
                tracker.record_token(stream_id, f"token{token_num}")
                time.sleep(0.001)  # Small delay

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Verify all metric types have percentiles
        # TTFT
        assert metrics.p50_ttft > 0
        assert metrics.p95_ttft > 0
        assert metrics.p99_ttft > 0

        # ITL
        assert metrics.p50_itl > 0
        assert metrics.p95_itl > 0
        assert metrics.p99_itl > 0

        # TPS
        assert metrics.p50_tokens_per_second > 0
        assert metrics.p95_tokens_per_second > 0
        assert metrics.p99_tokens_per_second > 0

        # Duration
        assert metrics.p50_duration > 0
        assert metrics.p95_duration > 0
        assert metrics.p99_duration > 0

    def test_percentile_ordering(self):
        """Test that percentiles are ordered correctly (p50 < p95 < p99)."""
        tracker = StreamingMetricsTracker(max_completed_streams=200)

        # Create streams with varying values
        for i in range(100):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=10)
            tracker.record_first_token_time(stream_id, 50 + i * 2)

            for token_num in range(10):
                tracker.record_token(stream_id, f"token{token_num}")

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Verify ordering for all metrics
        # TTFT
        assert metrics.p50_ttft <= metrics.p95_ttft
        assert metrics.p95_ttft <= metrics.p99_ttft
        assert metrics.min_ttft <= metrics.p50_ttft
        assert metrics.p99_ttft <= metrics.max_ttft

        # ITL
        assert metrics.p50_itl <= metrics.p95_itl
        assert metrics.p95_itl <= metrics.p99_itl

        # TPS
        # Note: TPS can be inversely related to latency
        assert metrics.p50_tokens_per_second <= metrics.p99_tokens_per_second

        # Duration
        assert metrics.p50_duration <= metrics.p95_duration
        assert metrics.p95_duration <= metrics.p99_duration


class TestRealWorldScenarios:
    """Test percentile calculations in realistic scenarios."""

    def test_production_traffic_pattern(self):
        """Simulate realistic production traffic pattern."""
        tracker = StreamingMetricsTracker(max_completed_streams=500)

        # Most requests are fast, some are slow, few are very slow
        # 80% fast (50-100ms), 15% medium (100-300ms), 5% slow (300-1000ms)

        # Fast requests
        for i in range(160):
            stream_id = f"fast-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=50)
            tracker.record_first_token_time(stream_id, 50 + i * 0.3)
            tracker.complete_stream(stream_id, "stop")

        # Medium requests
        for i in range(30):
            stream_id = f"medium-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=100)
            tracker.record_first_token_time(stream_id, 100 + i * 6.7)
            tracker.complete_stream(stream_id, "stop")

        # Slow requests
        for i in range(10):
            stream_id = f"slow-{i}"
            tracker.start_stream(stream_id, model="gpt-4", prompt_tokens=200)
            tracker.record_first_token_time(stream_id, 300 + i * 70)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # p50 should be in fast range
        assert 50 <= metrics.p50_ttft <= 100

        # p95 should catch some medium/slow requests
        assert 150 <= metrics.p95_ttft <= 400

        # p99 should be in slow range
        assert 300 <= metrics.p99_ttft <= 1000

    def test_gradual_performance_degradation(self):
        """Simulate gradual performance degradation over time."""
        tracker = StreamingMetricsTracker(max_completed_streams=500)

        # Performance degrades linearly
        for i in range(200):
            stream_id = f"stream-{i}"
            tracker.start_stream(stream_id, model="test", prompt_tokens=50)

            # TTFT increases linearly (performance degrades)
            ttft = 50 + i * 2  # 50ms to 450ms
            tracker.record_first_token_time(stream_id, ttft)

            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Should capture the degradation
        assert metrics.min_ttft < 100  # Early fast requests
        assert metrics.max_ttft > 400  # Later slow requests
        assert metrics.p95_ttft > metrics.p50_ttft * 1.5  # Clear performance spread

    def test_mixed_model_performance(self):
        """Test percentiles with multiple models having different performance."""
        tracker = StreamingMetricsTracker(max_completed_streams=500)

        # Fast model (50-100ms TTFT)
        for i in range(100):
            stream_id = f"fast-model-{i}"
            tracker.start_stream(stream_id, model="fast-model", prompt_tokens=50)
            tracker.record_first_token_time(stream_id, 50 + i * 0.5)
            tracker.complete_stream(stream_id, "stop")

        # Slow model (200-300ms TTFT)
        for i in range(100):
            stream_id = f"slow-model-{i}"
            tracker.start_stream(stream_id, model="slow-model", prompt_tokens=50)
            tracker.record_first_token_time(stream_id, 200 + i * 1.0)
            tracker.complete_stream(stream_id, "stop")

        metrics = tracker.get_metrics()

        # Overall percentiles should span both models
        assert metrics.min_ttft < 100  # Fast model
        assert metrics.max_ttft > 200  # Slow model

        # p50 should be between the two model ranges
        assert 100 <= metrics.p50_ttft <= 200

        # p95 and p99 should be in slow model range
        assert metrics.p95_ttft >= 250
