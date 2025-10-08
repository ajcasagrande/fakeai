# Live Cost Tracking Verification Test

## Overview

`verify_cost_tracking_live.py` is a comprehensive test suite that verifies the cost tracking functionality of FakeAI by making real API requests and validating:

- Cost calculations for different models
- Token counting accuracy
- Budget alerts and thresholds
- Cost aggregation
- Optimization suggestions
- Precision to 6 decimal places

## Features

### Test Coverage

1. **Basic Model Testing** - Tests multiple models (GPT-4, GPT-4o, GPT-4o-mini) with varying token counts
2. **Cached Token Calculation** - Verifies cost savings from prompt caching
3. **Cost Aggregation** - Tests accumulation of costs across multiple requests
4. **Budget Alerts** - Sets a $1 budget and verifies alert triggers at 80% threshold
5. **Optimization Suggestions** - Generates expensive usage patterns to trigger cost-saving recommendations
6. **Model Cost Comparison** - Compares costs across different model tiers
7. **Precision Verification** - Tests accuracy to 6 decimal places for very small costs

### Detailed Output

The test provides:
- Token-by-token cost breakdown
- Expected vs actual cost comparison
- Difference calculations
- Pass/fail status for each test
- Comprehensive summary at the end

## Usage

### Prerequisites

1. FakeAI server must be running on `localhost:8000` (or specify custom URL)
2. Required dependencies installed (openai, fakeai)

### Running the Test

#### Basic Usage (Default Settings)

```bash
# Start the FakeAI server first
python -m fakeai.app

# In another terminal, run the test
python tests/verify_cost_tracking_live.py
```

#### Custom Server URL

```bash
python tests/verify_cost_tracking_live.py http://localhost:8080/v1
```

#### Custom API Key

```bash
python tests/verify_cost_tracking_live.py http://localhost:8000/v1 my-custom-key
```

#### As a Python Module

```python
from tests.verify_cost_tracking_live import run_full_verification

# Run with defaults
success = run_full_verification()

# Run with custom parameters
success = run_full_verification(
    base_url="http://localhost:8000/v1",
    api_key="test-key"
)

if success:
    print("All tests passed!")
else:
    print("Some tests failed")
```

## Example Output

```
================================================================================
                           TEST 1: Different Models
================================================================================

Test: GPT-4 - Small request
  Model: gpt-4
  Tokens:
    Prompt:            100
    Completion:         50
  Pricing (per 1M tokens):
    Input:      $     30.00
    Output:     $     60.00
  Cost:
    Expected:   $  0.006000
    Actual:     $  0.006000
    Difference: $  0.000000
  Status: PASS

...

================================================================================
                              TEST 4: Budget Alerts
================================================================================

Budget Configuration:
  Limit: $1.00
  Period: MONTHLY
  Type: SOFT
  Alert Threshold: 80%

  Alert Triggered at Request #145:
    Used: $0.802340 (80.23%)
    Remaining: $0.197660

  Budget Exceeded at Request #182:
    Used: $1.003452 (100.35%)
    Remaining: $-0.003452

...

================================================================================
                              TEST SUMMARY
================================================================================

  Total Tests: 25
  Passed: 25
  Failed: 0
  Pass Rate: 100.0%

  Result: ALL TESTS PASSED!
```

## Test Structure

### CostVerifier Class

Helper class for cost calculation and verification:
- `calculate_expected_cost()` - Computes expected cost based on pricing model
- `verify_cost()` - Compares expected vs actual with tolerance checking

### LiveCostTrackingTest Class

Main test suite with the following methods:

1. `test_basic_models()` - Tests 9 different model/token combinations
2. `test_cached_tokens()` - Tests 4 caching scenarios
3. `test_cost_aggregation()` - Tests cost accumulation across 10 requests
4. `test_budget_alerts()` - Tests budget alert system (1 comprehensive test)
5. `test_optimization_suggestions()` - Tests suggestion generation
6. `test_cost_comparison()` - Tests 5 model cost comparisons
7. `test_precision_accuracy()` - Tests 4 precision scenarios

## Technical Details

### Cost Calculation

The test independently calculates expected costs using the same pricing model as the CostTracker:

```python
# For regular tokens
input_cost = prompt_tokens / 1_000_000 * input_price_per_million
output_cost = completion_tokens / 1_000_000 * output_price_per_million

# For cached tokens
cached_cost = cached_tokens / 1_000_000 * cached_price_per_million
regular_input_cost = (prompt_tokens - cached_tokens) / 1_000_000 * input_price_per_million
```

### Precision Tolerance

The test uses a tolerance of 0.000001 (1 millionth of a dollar) for cost comparisons:

```python
def verify_cost(expected: float, actual: float, tolerance: float = 0.000001):
    diff = abs(expected - actual)
    return diff <= tolerance, diff
```

### Budget Testing

The budget test:
1. Sets a $1.00 budget with 80% alert threshold
2. Makes requests until budget is exceeded
3. Verifies alert triggered before exceeding
4. Reports exact request number where alert/exceed occurred

## Troubleshooting

### Server Not Running

```
Error: Connection refused
```

**Solution**: Start the FakeAI server before running the test:
```bash
python -m fakeai.app
```

### Import Errors

```
ModuleNotFoundError: No module named 'fakeai'
```

**Solution**: Install FakeAI in development mode:
```bash
pip install -e .
```

### Test Failures

If tests fail:
1. Check that the server is responding correctly
2. Verify pricing models are up to date in `fakeai/cost_tracker.py`
3. Check for any recent API changes
4. Review the detailed output to identify which specific test failed

## Integration with CI/CD

### As a Pytest Test

To run as part of pytest suite:

```python
# In conftest.py or test setup
import pytest
from tests.verify_cost_tracking_live import LiveCostTrackingTest

@pytest.fixture(scope="session")
def cost_tracking_test(live_server):
    """Fixture for cost tracking tests."""
    return LiveCostTrackingTest(
        base_url=f"http://localhost:{live_server.port}/v1"
    )

def test_cost_tracking_verification(cost_tracking_test):
    """Run full cost tracking verification."""
    success = cost_tracking_test.run_all_tests()
    assert success, "Cost tracking verification failed"
```

### Standalone Test

Can be run as a standalone verification step:

```bash
#!/bin/bash
# start_server_and_test.sh

# Start server in background
python -m fakeai.app &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Run verification
python tests/verify_cost_tracking_live.py

# Capture exit code
EXIT_CODE=$?

# Cleanup
kill $SERVER_PID

# Exit with test result
exit $EXIT_CODE
```

## Future Enhancements

Potential additions to this test suite:

1. **Image Generation Costs** - Verify DALL-E pricing
2. **Audio API Costs** - Verify TTS and Whisper pricing
3. **Batch API Costs** - Verify batch processing discounts
4. **Fine-tuned Model Costs** - Verify custom model pricing
5. **Streaming Costs** - Verify costs match for streaming vs non-streaming
6. **Rate Limit Integration** - Test budget + rate limit interaction
7. **Multi-key Testing** - Verify isolation between different API keys

## Related Files

- `/fakeai/cost_tracker.py` - Core cost tracking implementation
- `/tests/test_cost_tracker.py` - Unit tests for cost tracker
- `/tests/test_budget_alerts.py` - Comprehensive budget alert tests
- `/tests/test_cost_calculations.py` - Cost calculation unit tests
- `/examples/cost_tracking_example.py` - Example usage of cost tracking

## License

Apache-2.0

## Author

Generated for FakeAI project cost tracking verification
