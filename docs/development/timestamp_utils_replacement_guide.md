# Timestamp Utils Replacement Guide

## Overview

The `fakeai.shared.timestamp_utils` module consolidates 86+ timestamp patterns into reusable, well-tested functions. This guide shows how to replace common timestamp patterns throughout the codebase.

## Statistics

**Total Replaceable Patterns:** 86 across 13 unique files

| Pattern | Count | Files | Replacement Function |
|---------|-------|-------|---------------------|
| `int(time.time())` | 68 | 8 | `current_timestamp()` |
| `int(time.time()) - offset` | 4 | 2 | `backdated_timestamp(offset)` |
| `time.time() * 1000` | 1 | 1 | `current_timestamp_ms()` |
| `time.time_ns()` | 8 | 2 | `current_timestamp_ns()` |
| `time.time() - offset` | 5 | 2 | `backdated_timestamp()` + conversion |

## Import Statement

```python
from fakeai.shared.timestamp_utils import (
    current_timestamp,
    current_timestamp_float,
    current_timestamp_ms,
    current_timestamp_ns,
    backdated_timestamp,
    timestamp_to_iso,
    iso_to_timestamp,
    time_ago_ms,
    time_ago_seconds,
)
```

Or import from shared package:

```python
from fakeai.shared import current_timestamp, backdated_timestamp
```

## Replacement Examples

### 1. Current Timestamp (Integer Seconds)

**Before:**
```python
import time

created_at = int(time.time())
timestamp = int(time.time())
```

**After:**
```python
from fakeai.shared import current_timestamp

created_at = current_timestamp()
timestamp = current_timestamp()
```

**Occurrences:** 68 instances in:
- `fakeai/fakeai_service.py` (58)
- `fakeai/file_manager.py` (2)
- `fakeai/app.py` (1)
- `fakeai/audio.py` (1)
- `fakeai/middleware/logging.py` (1)
- `fakeai/middleware/integration.py` (1)
- `fakeai/models_registry/definition.py` (1)
- `tests/test_usage_billing.py` (9)

### 2. Backdated Timestamps (Creation Time)

**Before:**
```python
import time

# Default 10000 seconds ago
creation_time = int(time.time()) - 10000

# Custom offset (5000 seconds ago)
creation_time = int(time.time()) - 5000
```

**After:**
```python
from fakeai.shared import backdated_timestamp

# Default 10000 seconds ago
creation_time = backdated_timestamp()

# Custom offset (5000 seconds ago)
creation_time = backdated_timestamp(5000)
```

**Occurrences:** 4 instances in:
- `fakeai/fakeai_service.py` (3)
- `fakeai/models_registry/definition.py` (1)

### 3. Timestamp in Milliseconds

**Before:**
```python
import time

timestamp_ms = int(time.time() * 1000)
```

**After:**
```python
from fakeai.shared import current_timestamp_ms

timestamp_ms = current_timestamp_ms()
```

**Occurrences:** 1 instance in:
- `examples/example_production_workflow.py` (1)

### 4. Timestamp in Nanoseconds

**Before:**
```python
import time

start_time_ns = time.time_ns()
timestamp_ns = time.time_ns()
completion_time_ns = time.time_ns()
```

**After:**
```python
from fakeai.shared import current_timestamp_ns

start_time_ns = current_timestamp_ns()
timestamp_ns = current_timestamp_ns()
completion_time_ns = current_timestamp_ns()
```

**Occurrences:** 8 instances in:
- `fakeai/streaming_metrics.py` (4)

### 5. Time Elapsed Calculations

**Before:**
```python
import time

start_ns = time.time_ns()
# ... do work ...
elapsed_ms = (time.time_ns() - start_ns) / 1_000_000

start_time = time.time()
# ... do work ...
elapsed_seconds = time.time() - start_time
```

**After:**
```python
from fakeai.shared import current_timestamp_ns, time_ago_ms, time_ago_seconds, current_timestamp_float

start_ns = current_timestamp_ns()
# ... do work ...
elapsed_ms = time_ago_ms(start_ns)

start_time = current_timestamp_float()
# ... do work ...
elapsed_seconds = time_ago_seconds(start_time)
```

### 6. Relative Time Windows (Cutoff Times)

**Before:**
```python
import time

# 24 hours ago
cutoff_time = time.time() - 86400

# 7 days ago
cutoff_time = time.time() - (7 * 86400)

# Custom period
cutoff_time = time.time() - (period_hours * 3600)
```

**After:**
```python
from fakeai.shared import backdated_timestamp

# 24 hours ago
cutoff_time = backdated_timestamp(86400)

# 7 days ago
cutoff_time = backdated_timestamp(7 * 86400)

# Custom period
cutoff_time = backdated_timestamp(period_hours * 3600)
```

**Occurrences:** 5 instances in:
- `fakeai/cost_tracker.py` (5)

### 7. ISO 8601 Conversions

**Before:**
```python
from datetime import datetime, timezone

# Timestamp to ISO
iso_string = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()

# ISO to timestamp
timestamp = int(datetime.fromisoformat(iso_string).timestamp())
```

**After:**
```python
from fakeai.shared import timestamp_to_iso, iso_to_timestamp

# Timestamp to ISO
iso_string = timestamp_to_iso(timestamp)

# ISO to timestamp
timestamp = iso_to_timestamp(iso_string)
```

## Benefits

1. **Consistency**: Single source of truth for timestamp handling
2. **Testability**: All functions thoroughly tested (36 tests)
3. **Readability**: Named functions are more self-documenting
4. **Maintainability**: Changes to timestamp logic in one place
5. **Type Safety**: Proper type hints on all functions
6. **Documentation**: Comprehensive docstrings with examples
7. **Performance**: No overhead (direct time module calls)

## Migration Strategy

### Phase 1: High-Impact Files (Recommended First)

1. **fakeai/fakeai_service.py** (61 patterns)
   - Replace `int(time.time())` with `current_timestamp()`
   - Replace `int(time.time()) - 10000` with `backdated_timestamp()`
   - Replace `int(time.time()) - 5000` with `backdated_timestamp(5000)`

2. **fakeai/streaming_metrics.py** (4 patterns)
   - Replace `time.time_ns()` with `current_timestamp_ns()`

3. **fakeai/cost_tracker.py** (5 patterns)
   - Replace `time.time() - (period * seconds)` with `backdated_timestamp(period * seconds)`

4. **tests/test_usage_billing.py** (9 patterns)
   - Replace `int(time.time())` with `current_timestamp()`

### Phase 2: Supporting Files

5. **fakeai/file_manager.py** (2 patterns)
6. **fakeai/middleware/logging.py** (1 pattern)
7. **fakeai/middleware/integration.py** (1 pattern)
8. **fakeai/models_registry/definition.py** (2 patterns)
9. **fakeai/audio.py** (1 pattern)
10. **fakeai/app.py** (1 pattern)
11. **examples/example_production_workflow.py** (1 pattern)

### Phase 3: Testing & Validation

After each file replacement:
1. Run unit tests: `pytest tests/test_<module>.py -v`
2. Run integration tests: `pytest tests/test_integration*.py -v`
3. Check for any behavioral changes
4. Verify timestamp values are consistent

## Testing the New Module

```bash
# Run timestamp utils tests
pytest tests/test_shared_timestamp_utils.py -v

# All tests should pass (36 tests)
```

## Example Migration: fakeai_service.py

**Before:**
```python
import time

class FakeAIService:
    def _ensure_model_exists(self, model_id: str) -> None:
        if model_id in self.models:
            return
        creation_time = int(time.time()) - 10000
        # ... rest of method

    async def create_chat_completion(self, request):
        response = ChatCompletion(
            id=f"chatcmpl-{uuid.uuid4().hex}",
            created=int(time.time()),
            model=request.model,
            # ... rest of response
        )
```

**After:**
```python
import time
from fakeai.shared import current_timestamp, backdated_timestamp

class FakeAIService:
    def _ensure_model_exists(self, model_id: str) -> None:
        if model_id in self.models:
            return
        creation_time = backdated_timestamp()
        # ... rest of method

    async def create_chat_completion(self, request):
        response = ChatCompletion(
            id=f"chatcmpl-{uuid.uuid4().hex}",
            created=current_timestamp(),
            model=request.model,
            # ... rest of response
        )
```

## Common Patterns Summary

| Use Case | Old Pattern | New Function |
|----------|-------------|-------------|
| Current time (seconds) | `int(time.time())` | `current_timestamp()` |
| Current time (float) | `time.time()` | `current_timestamp_float()` |
| Current time (ms) | `int(time.time() * 1000)` | `current_timestamp_ms()` |
| Current time (ns) | `time.time_ns()` | `current_timestamp_ns()` |
| Time X seconds ago | `int(time.time()) - X` | `backdated_timestamp(X)` |
| Default backdate | `int(time.time()) - 10000` | `backdated_timestamp()` |
| Elapsed time (ms) | `(time.time_ns() - start) / 1e6` | `time_ago_ms(start)` |
| Elapsed time (s) | `time.time() - start` | `time_ago_seconds(start)` |
| To ISO string | `datetime.fromtimestamp(...).isoformat()` | `timestamp_to_iso(ts)` |
| From ISO string | `int(datetime.fromisoformat(...).timestamp())` | `iso_to_timestamp(iso)` |

## Additional Utilities

### Time Range Generation
```python
from fakeai.shared import timestamp_range

# Get timestamps for last hour
start, end = timestamp_range(3600, 0)

# Get timestamps from 2 hours ago to 1 hour ago
start, end = timestamp_range(7200, 3600)
```

### Timestamp Validation
```python
from fakeai.shared import is_future_timestamp, is_past_timestamp

if is_future_timestamp(expires_at):
    # Token is still valid
    pass

if is_past_timestamp(created_at):
    # Resource was created in the past
    pass
```

### Duration Formatting
```python
from fakeai.shared import format_duration_seconds

duration = 3661  # seconds
formatted = format_duration_seconds(duration)  # "1h 1m 1s"
```

## Questions?

See the module documentation:
```python
from fakeai.shared import timestamp_utils
help(timestamp_utils)
```

Or read the source:
- `/home/anthony/projects/fakeai/fakeai/shared/timestamp_utils.py`
- `/home/anthony/projects/fakeai/tests/test_shared_timestamp_utils.py`
