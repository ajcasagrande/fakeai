# Test Runner Quick Start Guide

## 5-Minute Quick Start

### 1. Run All Tests (Sequential)
```bash
cd /home/anthony/projects/fakeai
python tests/integration/RUN_ALL_TESTS.py
```

### 2. Run All Tests (Parallel - Fast!)
```bash
python tests/integration/RUN_ALL_TESTS.py --parallel 8 --timeout 30
```

### 3. Show Only Failed Tests
```bash
python tests/integration/RUN_ALL_TESTS.py --filter failed
```

### 4. Test Specific Directory
```bash
python tests/integration/RUN_ALL_TESTS.py --dir tests/services
```

### 5. Export Results to JSON
```bash
python tests/integration/RUN_ALL_TESTS.py --export results.json
```

## Common Workflows

### Morning Health Check
```bash
# Quick parallel run to check everything
python tests/integration/RUN_ALL_TESTS.py --parallel 8 --timeout 20
```

### Before Committing Changes
```bash
# Test affected areas
python tests/integration/RUN_ALL_TESTS.py --dir tests/services --parallel 4
```

### Debugging Failures
```bash
# See detailed output for failed tests only
python tests/integration/RUN_ALL_TESTS.py --filter failed --verbose
```

### CI/CD Pipeline
```bash
# Export results for tracking
python tests/integration/RUN_ALL_TESTS.py --parallel $(nproc) --no-color --export ci_results.json
```

## Understanding the Output

### Real-Time Progress
```
[5/142] test_audio.py                                   ✓ PASS (5.23s)
[6/142] test_batch_service.py                           ✗ FAIL (11.43s)
```

### Summary Report
```
SUMMARY:
  Total Test Files:     142
  ✓ Passed Files:      120 (84.5%)    <- Your pass rate
  ✗ Failed Files:      15              <- Tests that need fixing
  ⚠ Error Files:       5               <- Tests with errors
  ⏱ Timeout Files:     2               <- Tests that timed out
```

### What to Fix First
The report shows "Common Failure Patterns" - start with the most frequent ones!

## Tips

- **Parallel is faster** but sequential is better for debugging
- **Increase timeout** if you see lots of timeout errors
- **Use filters** to focus on specific issues
- **Export JSON** to track progress over time
- **Check recommendations** at the end of the report

## Getting Help
```bash
python tests/integration/RUN_ALL_TESTS.py --help
```

## That's It!
Start testing and let the runner guide you to fixes with its intelligent recommendations.
