# Cost Tracker Integration Tests

## Overview

This document describes the comprehensive integration test suite for the CostTracker module (`test_cost_tracker_integration.py`).

## Test Coverage

### 1. Usage Recording Tests (`TestUsageRecording`)

Tests that verify usage recording and cost calculation accuracy:

- **`test_record_usage_calculates_cost_correctly`**: Validates that `record_usage()` calculates and returns the correct cost for a given model and token usage
- **`test_per_model_pricing_accuracy_gpt4`**: Verifies GPT-4 pricing ($30/1M input, $60/1M output)
- **`test_per_model_pricing_accuracy_gpt4o`**: Verifies GPT-4o pricing ($5/1M input, $15/1M output)
- **`test_per_model_pricing_accuracy_gpt4o_mini`**: Verifies GPT-4o-mini pricing ($0.15/1M input, $0.60/1M output)
- **`test_per_model_pricing_accuracy_o1`**: Verifies O1 model pricing ($15/1M input, $60/1M output)
- **`test_cached_token_discount_applied`**: Validates that cached tokens receive 50% discount (e.g., $2.50 vs $5.00 for GPT-4o)
- **`test_totals_updated_correctly`**: Ensures all aggregated totals (by key, model, endpoint) are updated correctly

### 2. Cost Calculation Tests (`TestCostCalculation`)

Detailed tests for different pricing models:

- **GPT-4 Models**:
  - Standard GPT-4 ($30/$60 per 1M tokens)
  - GPT-4-32k ($60/$120 per 1M tokens)

- **GPT-4o Models**:
  - Standard ($5/$15 per 1M tokens)
  - With caching ($2.50 cached / $5 regular input)

- **GPT-4o-mini**:
  - Ultra-low-cost model ($0.15/$0.60 per 1M tokens)

- **O1 Models**:
  - O1 standard ($15/$60 per 1M tokens)
  - O1-mini ($3/$12 per 1M tokens)

- **Fine-Tuned Models**:
  - Custom pricing for fine-tuned variants (e.g., GPT-4o fine-tuned: $3.75/$15.00)

- **Image Generation**:
  - DALL-E 3 standard quality ($0.040 per image)
  - DALL-E 3 HD quality ($0.080-$0.120 depending on size)
  - Multiple image generation (cost × n)

- **Audio Services**:
  - TTS-1 ($15 per 1M characters)
  - TTS-1-HD ($30 per 1M characters)
  - Whisper transcription ($6 per 1M characters)

### 3. Budget Management Tests (`TestBudgetManagement`)

Tests for budget creation, tracking, and enforcement:

- **`test_set_budget_creates_budget`**: Validates budget creation with limits, periods, and thresholds
- **`test_check_budget_returns_correct_status`**: Ensures `check_budget()` returns accurate (used, remaining, over_limit) status
- **`test_budget_alerts_triggered_at_threshold`**: Verifies alerts trigger at the configured threshold (e.g., 80% of budget)
- **`test_budget_soft_vs_hard_limits`**: Tests difference between SOFT (warning only) and HARD (blocking) limits
- **`test_budget_reset_by_period`**: Validates budget reset for DAILY, WEEKLY, MONTHLY, and NEVER periods

### 4. Aggregation Tests (`TestAggregation`)

Tests for cost aggregation and filtering:

- **`test_get_cost_by_key_accurate`**: Validates `get_cost_by_key()` returns accurate data with by_model and by_endpoint breakdowns
- **`test_get_cost_by_model_correct`**: Tests `get_cost_by_model()` aggregation
- **`test_get_cost_by_endpoint_works`**: Tests `get_cost_by_endpoint()` aggregation
- **`test_time_filtering_period_hours`**: Validates time-based filtering (last N hours)

### 5. Optimization Tests (`TestOptimization`)

Tests for cost optimization suggestions:

- **`test_suggestions_generated`**: Verifies that optimization suggestions are automatically generated
- **`test_cheaper_model_recommendations`**: Tests suggestion to switch from expensive models (e.g., GPT-4) to cheaper alternatives (e.g., GPT-4o)
- **`test_cache_suggestions`**: Validates cache usage suggestions for high-volume applications
- **`test_batch_suggestions`**: Documents support for batch processing suggestions

### 6. Projection Tests (`TestProjections`)

Tests for cost projection functionality:

- **`test_monthly_cost_projection`**: Validates monthly cost projection based on recent usage
- **`test_projection_based_on_7day_average`**: Ensures projections use 7-day rolling average
- **`test_projection_scales_correctly`**: Verifies projections scale linearly with usage

### 7. Savings Tracking Tests (`TestSavingsTracking`)

Tests for savings calculations:

- **`test_cache_savings_calculated`**: Validates cache savings calculation (50% discount on cached tokens)
- **`test_batch_savings_calculated`**: Validates batch processing savings (50% discount on completion tokens)

### 8. Realistic Usage Pattern Tests (`TestRealisticUsagePatterns`)

Integration tests with realistic application scenarios:

- **`test_mixed_model_usage_scenario`**: Simulates a day of usage with multiple models:
  - High-quality responses with GPT-4o (20 requests)
  - Bulk processing with GPT-4o-mini (100 requests)
  - Embeddings for search (50 requests)
  - Image generation (3 images)

- **`test_high_volume_caching_scenario`**: Simulates application with 80% cache hit rate

- **`test_budget_conscious_organization`**: Tests multiple teams with different budgets:
  - Research team: $1000/month, GPT-4o
  - Production team: $500/month, GPT-4o-mini
  - Experimental team: $100/month, GPT-3.5-turbo

- **`test_multi_service_application`**: Tests application using all OpenAI services:
  - Chat completions (30 requests)
  - Embeddings for RAG (50 requests)
  - Image generation (5 images)
  - TTS audio (10 requests)

- **`test_cost_summary_comprehensive`**: Tests comprehensive summary with 5 users × 3 models × 10 requests

## Running the Tests

### Standard pytest execution:

```bash
pytest tests/test_cost_tracker_integration.py -v
```

### Run specific test class:

```bash
pytest tests/test_cost_tracker_integration.py::TestUsageRecording -v
```

### Run specific test:

```bash
pytest tests/test_cost_tracker_integration.py::TestUsageRecording::test_record_usage_calculates_cost_correctly -v
```

### Validation script (standalone):

If pytest has issues with the environment, use the standalone validation script:

```bash
python validate_cost_tracker_tests.py
```

## Key Features Tested

1. **Accurate Cost Calculation**: All pricing models match OpenAI's actual pricing (as of January 2025)
2. **Cached Token Discounts**: Proper 50% discount applied to cached tokens
3. **Budget Management**: SOFT/HARD limits, multiple reset periods, threshold alerts
4. **Multi-Service Support**: Chat, embeddings, images, audio all tested
5. **Fine-Tuned Models**: Custom pricing for fine-tuned model variants
6. **Aggregation**: By key, model, endpoint with time filtering
7. **Optimization**: Automatic suggestions for cost reduction
8. **Projections**: Monthly cost forecasting based on 7-day average
9. **Savings Tracking**: Cache and batch savings calculations

## Pricing Reference (as of January 2025)

| Model | Input ($/1M tokens) | Output ($/1M tokens) | Cached Input ($/1M tokens) |
|-------|---------------------|----------------------|----------------------------|
| GPT-4 | $30.00 | $60.00 | - |
| GPT-4-32k | $60.00 | $120.00 | - |
| GPT-4o | $5.00 | $15.00 | $2.50 |
| GPT-4o-mini | $0.15 | $0.60 | $0.075 |
| O1 | $15.00 | $60.00 | - |
| O1-mini | $3.00 | $12.00 | - |
| GPT-3.5-turbo | $0.50 | $1.50 | - |

| Service | Pricing |
|---------|---------|
| DALL-E 3 Standard 1024x1024 | $0.040 per image |
| DALL-E 3 HD 1024x1024 | $0.080 per image |
| TTS-1 | $15.00 per 1M characters |
| TTS-1-HD | $30.00 per 1M characters |
| Whisper-1 | $6.00 per 1M characters |

## Test Data Patterns

The tests use realistic token counts:
- Small requests: 100-500 tokens
- Medium requests: 1,000-5,000 tokens
- Large requests: 10,000+ tokens

This mirrors actual application usage patterns.

## Notes

- Tests are designed to be independent and can run in any order
- Each test uses unique API keys to avoid cross-contamination
- The `tracker` fixture ensures a clean state for each test class
- All floating-point comparisons use appropriate epsilon values (0.000001 for costs)
