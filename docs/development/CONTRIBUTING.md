# Contributing to FakeAI

Thank you for your interest in contributing to FakeAI! This guide will help you understand our project architecture, coding standards, and development workflow.

FakeAI is an advanced OpenAI-compatible API server featuring **90+ beautifully architected modules**, **1,400+ comprehensive tests**, and **production-grade engineering** throughout. We welcome contributions that maintain this standard of excellence.

---

## Table of Contents

1. [Welcome & Mission](#welcome--mission)
2. [Code of Conduct](#code-of-conduct)
3. [Getting Started](#getting-started)
4. [Development Workflow](#development-workflow)
5. [Code Standards](#code-standards)
6. [Architecture Principles](#architecture-principles)
7. [Testing Requirements](#testing-requirements)
8. [Documentation Requirements](#documentation-requirements)
9. [Pull Request Process](#pull-request-process)
10. [Areas to Contribute](#areas-to-contribute)
11. [Recognition](#recognition)

---

## Welcome & Mission

### Project Mission

FakeAI aims to be the most comprehensive, production-grade OpenAI-compatible API server for testing and development. Our mission is to provide:

- **100% schema compliance** with OpenAI API specifications
- **Realistic simulation** of API behavior, timing, and responses
- **Zero external dependencies** for core functionality (no actual LLM inference required)
- **Production-grade engineering** that developers can learn from and trust

### Core Values

1. **Excellence**: We maintain 90%+ test coverage and follow best practices throughout
2. **Modularity**: Every module has a single, clear responsibility
3. **Zero Duplication**: We extract common patterns into shared utilities
4. **Developer Experience**: Our code is clear, well-documented, and easy to understand
5. **Backward Compatibility**: We never break existing APIs without major version bump

### What Makes FakeAI Special

- **90+ modules** organized by domain and responsibility
- **1,400+ tests** with 0.87:1 test-to-code ratio
- **8 shared utility modules** eliminating all duplication
- **18 production-grade metrics systems** for comprehensive observability
- **Model registry** with fuzzy matching and capability queries
- **Real implementations** - no stubs, no mocks in production code

---

## Code of Conduct

### Our Standards

**We expect all contributors to:**

- **Be respectful and professional** in all interactions
- **Be collaborative** - work together, help each other grow
- **Be constructive** - provide helpful, actionable feedback
- **Be inclusive** - welcome contributors of all backgrounds and skill levels
- **Be patient** - everyone was a beginner once

**Examples of acceptable behavior:**

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community and project
- Showing empathy towards other community members

**Examples of unacceptable behavior:**

- Harassment, discrimination, or trolling of any kind
- Insulting or derogatory comments, personal or political attacks
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Project maintainers are responsible for clarifying standards of acceptable behavior and will take appropriate action in response to unacceptable behavior.

Consequences for violations may include:
1. **First offense**: Warning and request for correction
2. **Second offense**: Temporary ban from contributing
3. **Serious violations**: Permanent ban

---

## Getting Started

### Prerequisites

**Required:**
- Python 3.10 or higher
- Git version control
- Basic understanding of FastAPI and Pydantic
- Familiarity with async/await patterns in Python

**Recommended:**
- Experience with pytest for testing
- Understanding of type hints
- Familiarity with OpenAI API specifications

### Initial Setup

#### 1. Fork and Clone

```bash
# Fork the repository on GitHub (click "Fork" button)
# Then clone your fork:
git clone https://github.com/YOUR_USERNAME/fakeai.git
cd fakeai

# Add upstream remote for syncing
git remote add upstream https://github.com/ajcasagrande/fakeai.git

# Verify remotes
git remote -v
```

#### 2. Create Virtual Environment

```bash
# Create isolated Python environment
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

# Verify Python version
python --version  # Should be 3.10+
```

#### 3. Install Dependencies

```bash
# Install FakeAI in editable mode with all dev dependencies
pip install -e ".[dev]"

# This installs:
# - Core dependencies (FastAPI, Uvicorn, Pydantic, Faker, etc.)
# - Development tools (pytest, black, isort, mypy, flake8)
# - Testing libraries (pytest-asyncio, httpx, OpenAI client)
```

**Optional: Install additional feature sets:**

```bash
# For LLM generation features (DistilGPT-2/GPT-2)
pip install -e ".[llm]"

# For semantic embeddings (sentence-transformers)
pip install -e ".[embeddings]"

# For vector store functionality (FAISS)
pip install -e ".[vector]"

# Or install everything
pip install -e ".[all]"
```

#### 4. Verify Installation

```bash
# Start the server
fakeai server

# In another terminal, test basic endpoints
curl http://localhost:8000/health
# Should return: {"status":"healthy","timestamp":...}

curl http://localhost:8000/v1/models
# Should return list of models

# Run tests to ensure everything works
pytest tests/ -v

# Check code formatting
black --check fakeai/
isort --check fakeai/
```

#### 5. Set Up Development Environment

**Configure your editor/IDE:**

- Enable Python type checking (use Pylance, mypy, or similar)
- Configure Black formatter (88 character line length)
- Set up isort for import sorting
- Enable pytest test discovery

**VS Code example (.vscode/settings.json):**

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.rulers": [88],
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### Project Structure Overview

Understanding the project structure is crucial for contributing:

```
fakeai/
 fakeai/                           # Main package
    app.py                        # FastAPI application (100+ endpoints)
    fakeai_service.py             # Main service orchestration
    cli.py                        # CLI interface (cyclopts)
   
    config/                       # Configuration system (11 modules)
       __init__.py
       base.py                   # Base configuration classes
       server.py, auth.py, rate_limits.py, kv_cache.py
       generation.py, metrics.py, storage.py, security.py, features.py
   
    models/                       # Pydantic schemas (7 organized modules)
       _base.py                  # Base models (Model, Usage, etc.)
       _content.py               # Content parts (Text, Image, Video, Audio)
       chat.py                   # Chat completion models
       embeddings.py             # Embedding models
       images.py, audio.py, batches.py
       organization.py, files.py, moderation.py
   
    models_registry/              # Model registry (9 modules)
       registry.py               # Central ModelRegistry
       definition.py             # ModelDefinition schema
       capabilities.py           # ModelCapabilities schema
       discovery.py              # Fuzzy matching, inference
       catalog/                  # Provider catalogs (6 providers)
           openai.py, anthropic.py, meta.py, mistral.py, deepseek.py, nvidia.py
   
    services/                     # Service layer (6 extracted services)
       embedding_service.py
       image_generation_service.py
       audio_service.py
       moderation_service.py
       file_service.py
       batch_service.py
   
    shared/                       # Shared utilities (8 modules - ZERO duplication)
       content_utils.py          # Multi-modal content extraction
       delay_utils.py            # Named delay patterns
       id_generators.py          # All ID types (37 functions)
       timestamp_utils.py        # Time operations
       usage_builder.py          # Fluent Usage API
       decorators.py             # Common patterns (10 decorators)
       validators.py             # Parameter validation (24 validators)
   
    utils/                        # Utilities (6 focused modules)
       tokens.py                 # Token calculation
       embeddings.py             # Embedding generation
       text_generation.py        # Text generation helpers
       audio_generation.py       # Audio synthesis helpers
   
    metrics/                      # Metrics systems (18 modules)
       metrics.py                # Core MetricsTracker (singleton)
       metrics_aggregator.py     # Cross-system aggregation
       metrics_persistence.py    # SQLite time-series storage
       metrics_streaming.py      # WebSocket real-time streaming
       kv_cache.py, dcgm_metrics.py, dynamo_metrics.py
       cost_tracker.py, latency_histograms.py, model_metrics.py
   
    infrastructure/               # Infrastructure (10 modules)
        error_injector.py         # Error injection for testing
        context_validator.py      # Context length validation
        rate_limiter.py           # Rate limiting enforcement
        security.py               # Security features
        file_manager.py, tool_calling.py, structured_outputs.py

 tests/                            # Test suite (1,400+ tests)
    test_*.py                     # Comprehensive test coverage
    conftest.py                   # Shared fixtures

 examples/                         # Usage examples (50+)
    *.py                          # Comprehensive examples

 CLAUDE.md                         # Project knowledge base (for AI assistants)
 README.md                         # User documentation
 CONTRIBUTING.md                   # This file
 pyproject.toml                    # Project metadata and dependencies
 run_server.py                     # Direct server runner (legacy)
```

### Request Flow

Understanding the request flow helps you know where to add features:

```
1. Client HTTP Request
   ↓
2. FastAPI Middleware (logging, request tracking)
   ↓
3. Authentication (API Key via config/auth.py)
   ↓
4. Rate Limiting (if enabled via rate_limiter.py)
   ↓
5. Error Injection (if enabled via error_injector.py)
   ↓
6. Route Handler (app.py)
   ↓
7. Request Validation (Pydantic models/*)
   ↓
8. Service Layer (services/* or fakeai_service.py)
   ↓
9. Model Auto-Creation (_ensure_model_exists via models_registry)
   ↓
10. Content Extraction (shared/content_utils.py)
    ↓
11. Response Generation (with delays via shared/delay_utils.py)
    ↓
12. ID Generation (shared/id_generators.py)
    ↓
13. Usage Construction (shared/usage_builder.py)
    ↓
14. KV Cache Update (if enabled via kv_cache.py)
    ↓
15. Metrics Recording (metrics_*.py systems)
    ↓
16. Response Serialization (Pydantic)
    ↓
17. Client Response
```

---

## Development Workflow

### Standard Workflow

Follow this workflow for all contributions:

#### 1. Sync with Upstream

```bash
# Fetch latest changes from upstream
git fetch upstream

# Merge upstream main into your local main
git checkout main
git merge upstream/main

# Push to your fork
git push origin main
```

#### 2. Create Feature Branch

```bash
# Create and checkout feature branch
git checkout -b feature/your-feature-name

# Branch naming conventions:
# feature/add-xxx          - New features
# fix/bug-description      - Bug fixes
# refactor/module-name     - Code refactoring
# docs/update-xxx          - Documentation updates
# test/add-xxx-tests       - Test additions
```

#### 3. Make Changes

Follow the [Code Standards](#code-standards) and [Architecture Principles](#architecture-principles) sections.

**Key principles:**
- Make small, focused commits
- Write tests alongside code (aim for 1:1 ratio)
- Update documentation as you go
- Use type hints everywhere
- Follow existing patterns

#### 4. Write Tests (REQUIRED)

**Tests are mandatory for all changes.** See [Testing Requirements](#testing-requirements).

```bash
# Run tests frequently during development
pytest tests/ -v

# Run tests for specific module
pytest tests/test_your_feature.py -v

# Run with coverage
pytest --cov=fakeai --cov-report=term-missing
```

#### 5. Run Quality Checks Locally

```bash
# Format code (do this frequently)
black fakeai/
isort fakeai/

# Lint
flake8 fakeai/ --max-line-length=88 --extend-ignore=E203,W503

# Type check
mypy fakeai/ --ignore-missing-imports

# Run all tests
pytest tests/ -v

# Check coverage (should be 90%+)
pytest --cov=fakeai --cov-report=term-missing
```

#### 6. Commit with Descriptive Messages

```bash
# Stage your changes
git add .

# Commit with clear message
git commit -m "Add new feature: brief description

Detailed explanation of what this commit does:
- Implemented XYZ functionality
- Added comprehensive tests (25 tests)
- Updated documentation
- Added examples

Related to #123"
```

**Commit message format:**
```
<type>: <subject line>

<body - detailed explanation>

<footer - related issues>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `docs:` - Documentation updates
- `style:` - Code formatting
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks

#### 7. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Go to GitHub and create Pull Request
# Use the PR template (see Pull Request Process section)
```

### Development Commands

**Common commands you'll use frequently:**

```bash
# Start server for testing
fakeai server                              # Production mode
fakeai server --debug                      # Debug mode (auto-reload)
fakeai server --response-delay 0           # No delays (faster testing)
fakeai server --port 9000                  # Custom port

# Run tests
pytest tests/ -v                           # All tests, verbose
pytest tests/test_specific.py -v           # Specific test file
pytest -k "test_name" -v                   # Tests matching pattern
pytest --cov=fakeai --cov-report=html      # With HTML coverage report
pytest -x                                  # Stop on first failure
pytest -s                                  # Show print statements

# Code quality
black fakeai/                              # Format code
isort fakeai/                              # Sort imports
black --check fakeai/                      # Check formatting (no changes)
flake8 fakeai/ --max-line-length=88 --extend-ignore=E203,W503
mypy fakeai/ --ignore-missing-imports      # Type checking

# View metrics
curl http://localhost:8000/metrics | jq
curl http://localhost:8000/kv-cache-metrics | jq
fakeai metrics                             # CLI metrics viewer
fakeai cache-stats                         # KV cache statistics

# Build package
python -m build                            # Build wheel and sdist
pip install -e .                           # Install in editable mode
```

---

## Code Standards

### PEP 8 Compliance

**All code must follow PEP 8 with these specific settings:**

- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces (no tabs, ever)
- **Blank lines**: 2 between top-level functions/classes, 1 between methods
- **Imports**: Grouped and sorted by isort
- **Quotes**: Prefer double quotes for strings (Black default)

### Naming Conventions

```python
# Classes: PascalCase
class FakeAIService:
    pass

class ChatCompletionRequest:
    pass

# Functions and methods: snake_case
def extract_text_content(content: str) -> str:
    pass

async def create_chat_completion(request):
    pass

# Variables: snake_case
prompt_text = "Hello"
token_count = 100

# Constants: UPPER_CASE
MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 1.0
API_VERSION = "v1"

# Private methods/variables: _leading_underscore
def _ensure_model_exists(model_id: str):
    pass

self._internal_state = {}

# Module-level private: _single_underscore
_internal_cache = {}
```

### Type Hints (MANDATORY)

**Every function must have complete type hints:**

```python
#  GOOD: Full type hints
def calculate_token_count(text: str, model: str = "openai/gpt-oss-120b") -> int:
    """Calculate approximate token count for text."""
    return len(text.split())

async def create_embedding(
    text: str,
    model: str,
    dimensions: int | None = None
) -> list[float]:
    """Generate embedding vector for text."""
    # Implementation...

#  GOOD: Use Python 3.10+ union syntax
def process_content(content: str | list[dict] | None) -> str:
    """Extract text from content."""
    if content is None:
        return ""
    # Implementation...

#  BAD: No type hints
def calculate_token_count(text, model="openai/gpt-oss-120b"):
    return len(text.split())

#  BAD: Old typing syntax
from typing import Union, Optional, List

def process_content(content: Optional[Union[str, List[dict]]]) -> str:
    pass
```

**Type hint guidelines:**
- Use Python 3.10+ syntax: `str | int | None` instead of `Union[str, int, None]`
- Use `list[T]` instead of `List[T]`
- Use `dict[K, V]` instead of `Dict[K, V]`
- Use `tuple[T, ...]` instead of `Tuple[T, ...]`
- Use `type | None` instead of `Optional[type]`

### Docstring Format

**Use Google-style docstrings for all public functions:**

```python
def create_embedding(
    text: str,
    model: str = "text-embedding-ada-002",
    dimensions: int | None = None
) -> list[float]:
    """
    Generate a simulated embedding vector for the given text.

    This function creates a deterministic embedding based on text hashing,
    ensuring the same input always produces the same output. The embedding
    is L2-normalized to have a magnitude of 1.0.

    Args:
        text: The input text to embed. Must not be empty.
        model: The embedding model to use. Defaults to "text-embedding-ada-002".
        dimensions: Optional number of dimensions. If None, uses model default.

    Returns:
        A normalized embedding vector as a list of floats.
        The vector has L2 norm of 1.0.

    Raises:
        ValueError: If text is empty or model is invalid.
        RuntimeError: If embedding generation fails.

    Examples:
        >>> embedding = create_embedding("Hello world")
        >>> len(embedding)
        1536
        >>> import numpy as np
        >>> np.linalg.norm(embedding)
        1.0

        >>> # With custom dimensions
        >>> embedding = create_embedding("Hello", dimensions=256)
        >>> len(embedding)
        256

    Note:
        The embedding is deterministic - same input produces same output.
        This makes testing and debugging easier.
    """
    if not text:
        raise ValueError("Text cannot be empty")

    # Implementation...
```

**Docstring requirements:**
- One-line summary (imperative mood: "Generate", not "Generates")
- Detailed explanation (what, why, how)
- Args section with type and description
- Returns section with type and description
- Raises section for exceptions
- Examples section with actual usage
- Notes section for important details

### DRY Principle (Don't Repeat Yourself)

**NEVER duplicate code. Always use shared utilities.**

```python
#  BAD: Duplicated content extraction
def method_a(self, content):
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                texts.append(part.get("text", ""))
            elif hasattr(part, "type") and part.type == "text":
                texts.append(part.text)
        text = " ".join(texts)
    return text

def method_b(self, content):
    # Same code repeated!
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        texts = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                texts.append(part.get("text", ""))
            elif hasattr(part, "type") and part.type == "text":
                texts.append(part.text)
        text = " ".join(texts)
    return text

#  GOOD: Use shared utility
from fakeai.shared.content_utils import extract_text_content

def method_a(self, content):
    return extract_text_content(content)

def method_b(self, content):
    return extract_text_content(content)
```

**Always use shared utilities from `fakeai/shared/`:**

```python
# Content extraction
from fakeai.shared.content_utils import (
    extract_text_content,
    extract_all_content_parts,
    has_image_content,
    has_audio_content,
    has_video_content
)

# Delays
from fakeai.shared.delay_utils import (
    generate_chat_delay,
    generate_embedding_delay,
    generate_streaming_first_token_delay,
    generate_streaming_inter_token_delay
)

# ID generation
from fakeai.shared.id_generators import (
    generate_chat_completion_id,
    generate_embedding_id,
    generate_batch_id
)

# Timestamps
from fakeai.shared.timestamp_utils import (
    get_current_timestamp,
    format_iso_timestamp
)

# Usage construction
from fakeai.shared.usage_builder import UsageBuilder

# Validation
from fakeai.shared.validators import (
    validate_temperature,
    validate_max_tokens,
    validate_top_p
)
```

### Pythonic Patterns

**Write idiomatic Python code:**

```python
#  GOOD: List comprehension
texts = [extract_text_content(msg.content) for msg in messages if msg.content]

#  BAD: Manual loop
texts = []
for msg in messages:
    if msg.content:
        texts.append(extract_text_content(msg.content))

#  GOOD: Generator expression (memory efficient)
total_tokens = sum(calculate_token_count(text) for text in texts)

#  BAD: List comprehension for sum
total_tokens = sum([calculate_token_count(text) for text in texts])

#  GOOD: Context manager
with open(path, 'r') as f:
    data = f.read()

#  BAD: Manual file handling
f = open(path, 'r')
data = f.read()
f.close()

#  GOOD: Dictionary comprehension
token_counts = {msg.id: calculate_token_count(msg.content) for msg in messages}

#  GOOD: Enumerate instead of range(len())
for i, message in enumerate(messages):
    print(f"Message {i}: {message.content}")

#  BAD: range(len())
for i in range(len(messages)):
    print(f"Message {i}: {messages[i].content}")

#  GOOD: Use walrus operator (Python 3.8+)
if (text := extract_text_content(content)):
    tokens = calculate_token_count(text)

#  GOOD: Use f-strings
message = f"Processed {count} tokens in {duration:.2f}s"

#  BAD: String concatenation or .format()
message = "Processed " + str(count) + " tokens in " + str(duration) + "s"
```

### Error Handling

**Always handle errors gracefully and log them:**

```python
import logging
from fastapi import HTTPException
from fakeai.models._base import ErrorResponse, ErrorDetail

logger = logging.getLogger(__name__)

async def create_chat_completion(self, request):
    """Create chat completion with proper error handling."""
    try:
        # Main logic
        self._ensure_model_exists(request.model)
        response = await self._generate_response(request)

        # Track success metrics
        self.metrics_tracker.record_request(
            endpoint="/v1/chat/completions",
            latency_ms=123.45,
            status_code=200
        )

        return response

    except ValueError as e:
        # Validation errors
        logger.error(f"Validation error: {e}")
        self.metrics_tracker.record_error(
            endpoint="/v1/chat/completions",
            error_type="validation_error"
        )
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="invalid_request_error",
                    message=str(e),
                    type="invalid_request_error",
                )
            ).model_dump()
        )

    except Exception as e:
        # Unexpected errors
        logger.exception(f"Unexpected error in create_chat_completion: {e}")
        self.metrics_tracker.record_error(
            endpoint="/v1/chat/completions",
            error_type="internal_error"
        )
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="internal_server_error",
                    message="An unexpected error occurred.",
                    type="server_error",
                )
            ).model_dump()
        )
```

**Error handling guidelines:**
- Always log errors with appropriate level (error, exception)
- Track errors in metrics
- Return proper HTTP status codes
- Use OpenAI-compatible error format
- Never expose internal details to clients

### Async/Await

**Always use async/await for I/O operations:**

```python
#  GOOD: Async service methods
async def create_chat_completion(self, request: ChatCompletionRequest):
    """Create chat completion."""
    # Simulate processing delay
    await generate_chat_delay(self.config)

    # Generate response
    response = await self._generate_response(request)

    return response

#  GOOD: Async streaming
async def create_chat_completion_stream(
    self,
    request: ChatCompletionRequest
) -> AsyncGenerator[ChatCompletionChunk, None]:
    """Stream chat completion chunks."""
    await generate_streaming_first_token_delay()

    for token in tokens:
        await generate_streaming_inter_token_delay()
        yield chunk

#  GOOD: Async context manager
async with httpx.AsyncClient() as client:
    response = await client.get(url)

#  BAD: Blocking operations
import time
time.sleep(1)  # NEVER use time.sleep() in async code!

#  BAD: Sync code in async function
def create_chat_completion(self, request):  # Should be async!
    response = self._generate_response(request)  # Should be await!
    return response
```

---

## Architecture Principles

### Core Principles

FakeAI follows these architectural principles. **All contributions must adhere to them:**

#### 1. Single Responsibility Principle

**Each module has ONE clear purpose.**

```python
#  GOOD: Single responsibility
# fakeai/shared/content_utils.py
"""Content extraction utilities."""

def extract_text_content(content):
    """Extract text from content."""
    pass

def has_image_content(content):
    """Check if content has images."""
    pass

#  BAD: Multiple responsibilities
# fakeai/utils.py (old style)
def extract_text_content(content):
    pass

def generate_delay():  # Different responsibility!
    pass

def generate_id():  # Another different responsibility!
    pass
```

#### 2. Decoupled Modules

**Modules should have minimal dependencies on each other.**

```python
#  GOOD: Decoupled
# Service depends on abstract config, not concrete implementation
class EmbeddingService:
    def __init__(self, config: AppConfig):
        self.config = config

#  GOOD: Inject dependencies
service = EmbeddingService(config)
service._ensure_model_exists = main_service._ensure_model_exists

#  BAD: Tight coupling
class EmbeddingService:
    def __init__(self):
        self.main_service = FakeAIService()  # Creates dependency!
```

#### 3. Protocol-Based Design

**Use protocols/interfaces for flexibility.**

```python
from typing import Protocol

#  GOOD: Protocol for flexibility
class MetricsTracker(Protocol):
    def record_request(self, endpoint: str, latency_ms: float) -> None:
        ...

def handle_request(metrics: MetricsTracker):
    # Works with any metrics implementation
    metrics.record_request("/v1/chat/completions", 123.45)
```

#### 4. Dependency Injection

**Pass dependencies explicitly, don't create them.**

```python
#  GOOD: Dependencies injected
def __init__(self, config: AppConfig, metrics: MetricsTracker):
    self.config = config
    self.metrics = metrics

#  BAD: Creates dependencies internally
def __init__(self):
    self.config = AppConfig()  # Hardcoded!
    self.metrics = MetricsTracker()  # Can't be mocked in tests!
```

#### 5. Immutability Where Possible

**Prefer immutable data structures.**

```python
#  GOOD: Immutable Pydantic model
from pydantic import BaseModel

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[Message]

    class Config:
        frozen = False  # Allow for Pydantic operations

#  GOOD: Immutable tuple
SUPPORTED_MODELS = (
    "openai/gpt-oss-120b",
    "meta-llama/Llama-3.1-8B-Instruct",
)

#  BAD: Mutable default argument
def process_messages(messages=[]):  # NEVER!
    messages.append("new")
    return messages

#  GOOD: None default
def process_messages(messages: list[str] | None = None) -> list[str]:
    if messages is None:
        messages = []
    messages = messages.copy()  # Don't mutate input
    messages.append("new")
    return messages
```

#### 6. Thread-Safe Operations

**Ensure thread safety for shared state.**

```python
import threading

#  GOOD: Thread-safe singleton
class MetricsTracker:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        with self._lock:
            if not self._initialized:
                self.data = {}
                self._data_lock = threading.Lock()
                self._initialized = True

    def record_request(self, endpoint: str, latency_ms: float):
        with self._data_lock:
            # Thread-safe update
            if endpoint not in self.data:
                self.data[endpoint] = []
            self.data[endpoint].append(latency_ms)
```

#### 7. Graceful Degradation

**Features should degrade gracefully when dependencies unavailable.**

```python
#  GOOD: Graceful degradation
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken not available, using fallback tokenizer")

def tokenize_text(text: str) -> list[str]:
    """Tokenize text using best available method."""
    if TIKTOKEN_AVAILABLE:
        # Use tiktoken for 95%+ accuracy
        encoding = tiktoken.get_encoding("cl100k_base")
        return encoding.encode(text)
    else:
        # Fallback to regex tokenization
        return re.findall(r'\w+|[^\w\s]', text)
```

### Module Organization

**Organize code by domain and responsibility:**

```
fakeai/
 config/          # Configuration (domain: settings)
 models/          # Data models (domain: schemas)
 services/        # Business logic (domain: features)
 shared/          # Common utilities (domain: cross-cutting)
 utils/           # Specific utilities (domain: helpers)
 metrics/         # Observability (domain: monitoring)
 infrastructure/  # Cross-cutting concerns (domain: support)
```

**Each domain is self-contained:**
- Has its own `__init__.py` with exports
- Minimizes dependencies on other domains
- Has comprehensive tests
- Has clear documentation

---

## Testing Requirements

### Test Philosophy

**Tests are not optional. They are a first-class citizen in our codebase.**

- **Test coverage target**: 90%+ for all new code
- **Test-to-code ratio**: Aim for 1:1 (1 line of test for every line of code)
- **Test quality**: Tests should be clear, comprehensive, and maintainable

### Test Organization

```
tests/
 unit/                           # Unit tests (fast, isolated)
    test_shared_utils.py       # Shared utilities
    test_services.py           # Service layer
    test_models.py             # Pydantic models

 integration/                    # Integration tests (slower)
    test_api_endpoints.py      # API endpoints
    test_streaming.py          # Streaming functionality
    test_metrics.py            # Metrics systems

 behavior/                       # Behavior tests (user-focused)
    test_chat_behavior.py      # Chat completion behavior
    test_embedding_behavior.py # Embedding behavior

 conftest.py                     # Shared fixtures
```

### Unit Test Requirements

**Every service method MUST have unit tests:**

```python
# tests/test_embedding_service.py
import pytest
from fakeai.services.embedding_service import EmbeddingService
from fakeai.models.embeddings import EmbeddingRequest
from fakeai.config import AppConfig


class TestEmbeddingService:
    """Test suite for EmbeddingService."""

    @pytest.fixture
    def config(self):
        """Provide test config with zero delays."""
        return AppConfig(response_delay=0.0)

    @pytest.fixture
    def service(self, config):
        """Provide service instance."""
        return EmbeddingService(config)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_embedding_basic(self, service):
        """Test basic embedding creation."""
        # Arrange
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Hello world"
        )

        # Act
        response = await service.create_embedding(request)

        # Assert
        assert response.object == "list"
        assert len(response.data) == 1
        assert len(response.data[0].embedding) == 1536
        assert response.usage.prompt_tokens > 0
        assert response.usage.total_tokens > 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_embedding_list_input(self, service):
        """Test embedding with list input."""
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input=["Hello", "World"]
        )

        response = await service.create_embedding(request)

        assert len(response.data) == 2
        assert response.data[0].index == 0
        assert response.data[1].index == 1

    @pytest.mark.asyncio
    @pytest.mark.edge_case
    async def test_create_embedding_empty_string(self, service):
        """Test error handling for empty input."""
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input=""
        )

        with pytest.raises(ValueError, match="Input cannot be empty"):
            await service.create_embedding(request)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_create_embedding_custom_dimensions(self, service):
        """Test embedding with custom dimensions."""
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Hello",
            dimensions=256
        )

        response = await service.create_embedding(request)

        assert len(response.data[0].embedding) == 256

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_embedding_deterministic(self, service):
        """Test that same input produces same embedding."""
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Test string"
        )

        response1 = await service.create_embedding(request)
        response2 = await service.create_embedding(request)

        assert response1.data[0].embedding == response2.data[0].embedding
```

**Unit test checklist:**
- [ ] Test basic functionality (happy path)
- [ ] Test edge cases (empty input, boundary values)
- [ ] Test error conditions (invalid input, exceptions)
- [ ] Test with different parameter combinations
- [ ] Test determinism where applicable
- [ ] Use descriptive test names
- [ ] Use AAA pattern (Arrange, Act, Assert)
- [ ] Use appropriate markers (`@pytest.mark.unit`, etc.)

### Integration Test Requirements

**Test API endpoints end-to-end:**

```python
# tests/integration/test_embedding_endpoint.py
import pytest
from httpx import AsyncClient
from fakeai.app import app


class TestEmbeddingEndpoint:
    """Integration tests for embedding endpoint."""

    @pytest.fixture
    async def client(self):
        """Provide test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embedding_endpoint_success(self, client):
        """Test successful embedding creation."""
        response = await client.post(
            "/v1/embeddings",
            headers={"Authorization": "Bearer sk-fakeai-test"},
            json={
                "model": "text-embedding-ada-002",
                "input": "Hello world"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 1
        assert len(data["data"][0]["embedding"]) == 1536

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embedding_endpoint_requires_auth(self, client):
        """Test that endpoint requires authentication."""
        response = await client.post(
            "/v1/embeddings",
            json={
                "model": "text-embedding-ada-002",
                "input": "Hello"
            }
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_embedding_endpoint_validates_input(self, client):
        """Test input validation."""
        response = await client.post(
            "/v1/embeddings",
            headers={"Authorization": "Bearer sk-fakeai-test"},
            json={
                "model": "text-embedding-ada-002",
                "input": ""  # Empty input
            }
        )

        assert response.status_code == 400
```

**Integration test checklist:**
- [ ] Test successful request/response
- [ ] Test authentication requirements
- [ ] Test input validation
- [ ] Test error responses
- [ ] Test rate limiting (if applicable)
- [ ] Test with OpenAI client library
- [ ] Test response schema compliance

### Test Markers

**Use pytest markers to categorize tests:**

```python
@pytest.mark.unit          # Unit tests (fast, isolated)
@pytest.mark.integration   # Integration tests (slower)
@pytest.mark.service       # Service layer tests
@pytest.mark.edge_case     # Edge case and error handling
@pytest.mark.slow          # Slow tests
@pytest.mark.asyncio       # Async tests (REQUIRED for async)
@pytest.mark.streaming     # Streaming tests
@pytest.mark.multimodal    # Multi-modal content tests
@pytest.mark.metrics       # Metrics tests
```

**Run specific test categories:**

```bash
# Run only unit tests
pytest -m unit -v

# Run only integration tests
pytest -m integration -v

# Run everything except slow tests
pytest -m "not slow" -v

# Run specific combination
pytest -m "unit and not slow" -v
```

### Coverage Requirements

**All new code must have 90%+ test coverage:**

```bash
# Check coverage
pytest --cov=fakeai --cov-report=term-missing --cov-report=html

# View HTML report
open htmlcov/index.html

# Check specific module
pytest --cov=fakeai.services.embedding_service --cov-report=term-missing
```

**Coverage targets by module type:**
- **Service methods**: 100% coverage required
- **Shared utilities**: 100% coverage required
- **API endpoints**: 90%+ coverage
- **Error handling**: All error paths tested
- **Edge cases**: All boundary conditions tested

### Test Best Practices

**1. Use fixtures for common setup:**

```python
@pytest.fixture
def config():
    """Provide test config with zero delays."""
    return AppConfig(response_delay=0.0, random_delay=False)

@pytest.fixture
def service(config):
    """Provide service instance."""
    return FakeAIService(config)

@pytest.fixture
def sample_messages():
    """Provide sample messages."""
    return [
        Message(role=Role.USER, content="Hello"),
        Message(role=Role.ASSISTANT, content="Hi there!"),
    ]
```

**2. Use parametrize for multiple test cases:**

```python
@pytest.mark.parametrize("model,expected_provider", [
    ("openai/gpt-oss-120b", "openai"),
    ("meta-llama/Llama-3.1-8B-Instruct", "meta"),
    ("mistral/mixtral-8x7b", "mistral"),
])
@pytest.mark.asyncio
async def test_multiple_models(service, model, expected_provider):
    """Test multiple models."""
    request = ChatCompletionRequest(
        model=model,
        messages=[Message(role=Role.USER, content="test")]
    )

    response = await service.create_chat_completion(request)

    assert response.model == model
    assert expected_provider in model
```

**3. Test edge cases explicitly:**

```python
@pytest.mark.asyncio
@pytest.mark.edge_case
async def test_empty_messages(service):
    """Test handling of empty message list."""
    request = ChatCompletionRequest(model="openai/gpt-oss-120b", messages=[])

    with pytest.raises(ValueError, match="Messages cannot be empty"):
        await service.create_chat_completion(request)

@pytest.mark.asyncio
@pytest.mark.edge_case
async def test_none_content(service):
    """Test handling of None content."""
    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[Message(role=Role.USER, content=None)]
    )

    response = await service.create_chat_completion(request)

    # Should handle gracefully, not crash
    assert response.choices[0].message.content
```

**4. Test error conditions:**

```python
@pytest.mark.asyncio
async def test_invalid_temperature(service):
    """Test that invalid temperature raises error."""
    request = ChatCompletionRequest(
        model="openai/gpt-oss-120b",
        messages=[Message(role=Role.USER, content="test")],
        temperature=3.0,  # Invalid: > 2.0
    )

    with pytest.raises(ValidationError):
        await service.create_chat_completion(request)
```

---

## Documentation Requirements

### Code Documentation

**All public functions and classes must have docstrings:**

```python
def extract_text_content(content: str | list[dict] | None) -> str:
    """
    Extract text from content (string or content parts array).

    Handles multiple content formats:
    - Simple string: Returns as-is
    - List of content parts: Extracts text from text parts
    - None: Returns empty string

    Args:
        content: Content to extract text from. Can be string,
            list of content parts (dicts or Pydantic models), or None.

    Returns:
        Extracted text as string. Empty string if no text found.

    Examples:
        >>> extract_text_content("Hello world")
        'Hello world'

        >>> extract_text_content([
        ...     {"type": "text", "text": "Hello"},
        ...     {"type": "image_url", "image_url": {"url": "..."}}
        ... ])
        'Hello'

        >>> extract_text_content(None)
        ''
    """
    # Implementation...
```

### Update Documentation Files

**When adding features, update these files:**

#### 1. README.md

Add user-facing documentation:

```markdown
### New Feature Endpoint

**POST /v1/new-feature**

Generate responses for the new feature.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Model to use |
| `input` | string | Yes | Input text |
| `temperature` | float | No | Sampling temperature (0-2) |

**Example:**

\`\`\`python
from openai import OpenAI

client = OpenAI(
    api_key="sk-fakeai-test",
    base_url="http://localhost:8000"
)

response = client.post(
    "/v1/new-feature",
    json={
        "model": "openai/gpt-oss-120b",
        "input": "test input"
    }
)
\`\`\`
```

#### 2. CLAUDE.md

Add technical documentation for AI assistants:

```markdown
### New Feature Implementation

**Pattern:**
\`\`\`python
async def create_new_feature(self, request: NewFeatureRequest) -> NewFeatureResponse:
    # 1. Ensure model exists
    self._ensure_model_exists(request.model)

    # 2. Extract content
    text = extract_text_content(request.input)

    # 3. Generate response with delay
    await generate_custom_delay(self.config, "new_feature")

    # 4. Build usage
    usage = UsageBuilder().with_prompt_tokens(tokens).build()

    # 5. Return response
    return NewFeatureResponse(...)
\`\`\`

**Key points:**
- Always call `_ensure_model_exists()` first
- Use `shared/` utilities for all common operations
- Track metrics via `self.metrics_tracker`
```

#### 3. API Reference

Add to API documentation:

```markdown
## New Feature API

### POST /v1/new-feature

Creates a new feature response.

**Request Body:**
\`\`\`json
{
  "model": "openai/gpt-oss-120b",
  "input": "test input",
  "temperature": 0.7
}
\`\`\`

**Response:**
\`\`\`json
{
  "id": "nf-abc123",
  "object": "new_feature.response",
  "created": 1234567890,
  "model": "openai/gpt-oss-120b",
  "output": "Generated output...",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
\`\`\`
```

### Module README Files

**Complex modules should have their own README:**

```markdown
# Module Name

## Purpose

One-line description of what this module does.

## Components

### Class1

Description of class and its responsibility.

### Class2

Description of class and its responsibility.

## Usage

\`\`\`python
from fakeai.module import Class1

instance = Class1()
result = instance.method()
\`\`\`

## Architecture

Explain key design decisions and patterns.

## Testing

Explain testing approach and how to run tests.
```

---

## Pull Request Process

### Before Submitting

**Complete this checklist before creating a PR:**

```bash
# 1. Sync with upstream
git fetch upstream
git rebase upstream/main

# 2. Run all quality checks
black fakeai/
isort fakeai/
flake8 fakeai/ --max-line-length=88 --extend-ignore=E203,W503
mypy fakeai/ --ignore-missing-imports

# 3. Run tests
pytest tests/ -v
pytest --cov=fakeai --cov-report=term-missing

# 4. Check coverage (must be 90%+)
# Review the coverage report

# 5. Build package (verify no errors)
python -m build

# 6. Manual testing
fakeai server --debug
# Test your changes manually

# 7. Update documentation
# Update README.md, CLAUDE.md, etc.
```

### Pull Request Template

**Use this template when creating your PR:**

```markdown
## Description

Brief description of what this PR does (1-2 sentences).

## Motivation

Why is this change needed? What problem does it solve?

## Changes

Detailed list of changes made:

- Added new endpoint `/v1/new-feature`
- Implemented `NewFeatureService` with comprehensive tests
- Created `NewFeatureRequest` and `NewFeatureResponse` models
- Added 25 unit tests and 10 integration tests
- Updated README.md and CLAUDE.md documentation
- Added examples in `examples/new_feature_example.py`

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring
- [ ] Test coverage improvement

## Testing

### Test Coverage

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing locally
- [ ] Coverage is 90%+ for new code
- [ ] Manual testing completed

### Test Results

\`\`\`bash
# Paste test results here
pytest tests/ -v
# ... output ...

# Coverage report
pytest --cov=fakeai --cov-report=term-missing
# ... output ...
\`\`\`

## Code Quality

- [ ] Code follows PEP 8 style guidelines
- [ ] Code formatted with Black (88 char line length)
- [ ] Imports sorted with isort
- [ ] Type hints added to all functions
- [ ] Docstrings added (Google style)
- [ ] flake8 passes with no errors
- [ ] mypy passes with no errors
- [ ] No duplicate code (uses shared utilities)

## Backward Compatibility

- [ ] No breaking changes
- [ ] OR: Breaking changes documented and justified
- [ ] API version incremented if needed

## Documentation

- [ ] README.md updated (user-facing changes)
- [ ] CLAUDE.md updated (architectural changes)
- [ ] API reference updated
- [ ] Module docstrings added/updated
- [ ] Examples added/updated
- [ ] Changelog entry added (if applicable)

## Checklist

- [ ] My code follows the project's code standards
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Screenshots / Examples

If applicable, add screenshots or code examples demonstrating the feature:

\`\`\`python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000", api_key="sk-fakeai-test")

# Example usage of new feature
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Test"}]
)

print(response.choices[0].message.content)
\`\`\`

## Performance Impact

- [ ] No performance impact
- [ ] Performance improved
- [ ] Performance benchmarks added
- [ ] OR: Performance impact documented and justified

## Related Issues

Closes #123
Fixes #456
Related to #789

## Additional Notes

Any additional information reviewers should know.
```

### Review Process

**Your PR will be reviewed for:**

1. **Code Quality**
   - [ ] Follows project code standards
   - [ ] No code duplication
   - [ ] Clear, readable code
   - [ ] Appropriate use of patterns

2. **Type Safety**
   - [ ] All functions have type hints
   - [ ] Type hints are correct and complete
   - [ ] No use of `Any` unless absolutely necessary

3. **Testing**
   - [ ] Comprehensive unit tests
   - [ ] Integration tests for new endpoints
   - [ ] Edge cases covered
   - [ ] Error conditions tested
   - [ ] 90%+ coverage on new code

4. **Documentation**
   - [ ] All public functions have docstrings
   - [ ] Documentation files updated
   - [ ] Examples provided
   - [ ] Clear commit messages

5. **Architecture**
   - [ ] Follows single responsibility principle
   - [ ] Uses shared utilities (no duplication)
   - [ ] Proper separation of concerns
   - [ ] Dependencies injected, not created

6. **Backward Compatibility**
   - [ ] No breaking changes (or properly documented)
   - [ ] Existing tests still pass
   - [ ] API contracts maintained

7. **Security**
   - [ ] No hardcoded secrets
   - [ ] No security vulnerabilities introduced
   - [ ] Proper error handling
   - [ ] Input validation present

8. **Performance**
   - [ ] No obvious performance issues
   - [ ] Async/await used correctly
   - [ ] No blocking operations

### Getting Your PR Merged

**Tips for quick PR approval:**

1. **Keep PRs small and focused**
   - Aim for < 500 lines changed
   - One feature/fix per PR
   - Split large changes into multiple PRs

2. **Write clear PR descriptions**
   - Explain the "why", not just the "what"
   - Include examples and screenshots
   - Link related issues

3. **Respond promptly to feedback**
   - Address all review comments
   - Ask clarifying questions if needed
   - Update PR description as changes are made

4. **Keep PR up-to-date**
   - Rebase on main before requesting review
   - Resolve conflicts promptly
   - Keep passing CI checks

5. **Be patient and professional**
   - Reviews take time
   - Be open to feedback
   - Thank reviewers for their time

---

## Areas to Contribute

### High-Priority Areas

**We especially welcome contributions in these areas:**

#### 1. New Metrics Systems

Expand our observability capabilities:

- Custom metrics exporters (Datadog, New Relic, etc.)
- Application Performance Monitoring (APM) integration
- Distributed tracing support (OpenTelemetry)
- Custom dashboard widgets
- Alerting and notification systems

**Example contribution:**
```python
# fakeai/metrics/datadog_exporter.py
from fakeai.metrics import MetricsTracker

class DatadogExporter:
    """Export metrics to Datadog."""

    def export_metrics(self, metrics: dict):
        """Export metrics to Datadog API."""
        # Implementation...
```

#### 2. New Model Providers

Add support for additional model providers:

- Cohere models
- AI21 Labs models
- Google Vertex AI models
- Azure OpenAI variants
- Custom local models

**Example contribution:**
```python
# fakeai/models_registry/catalog/cohere.py
from fakeai.models_registry import ModelDefinition, ModelCapabilities

COHERE_MODELS = [
    ModelDefinition(
        id="cohere/command-r-plus",
        provider="cohere",
        context_window=128000,
        max_output_tokens=4096,
        capabilities=ModelCapabilities(
            chat=True,
            completion=True,
            vision=False,
        )
    ),
    # More models...
]
```

#### 3. New Validation Rules

Enhance input validation:

- Advanced parameter validation
- Custom validation for specific models
- Business logic validation
- Security validation (content filtering)

**Example contribution:**
```python
# fakeai/shared/validators.py
def validate_json_schema(schema: dict) -> None:
    """Validate JSON schema for structured outputs."""
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dictionary")

    if "type" not in schema:
        raise ValueError("Schema must have 'type' field")

    # More validation...
```

#### 4. Performance Optimizations

Improve performance:

- Caching improvements
- Memory optimization
- Async performance
- Database query optimization (metrics persistence)
- Streaming optimizations

**Example contribution:**
```python
# fakeai/kv_cache_advanced.py
class LRUCache:
    """LRU cache for KV cache blocks."""

    def __init__(self, max_size: int):
        self.max_size = max_size
        self.cache = OrderedDict()

    def get(self, key: str) -> Any | None:
        """Get value from cache, updating LRU."""
        if key not in self.cache:
            return None

        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]
```

#### 5. Documentation Improvements

Enhance documentation:

- Tutorial articles
- How-to guides
- Architecture deep dives
- Best practices guides
- Video tutorials

#### 6. Bug Fixes

Always welcome:

- Fix reported bugs
- Fix edge cases
- Improve error handling
- Fix performance issues

#### 7. Test Coverage

Expand test coverage:

- Add tests for uncovered code
- Add edge case tests
- Add integration tests
- Add performance tests
- Add stress tests

### Good First Issues

**New contributors should look for:**

- Issues labeled `good-first-issue`
- Documentation improvements
- Test coverage improvements
- Simple bug fixes
- Example additions

### Advanced Contributions

**Experienced contributors can tackle:**

- Architectural improvements
- New major features
- Performance optimizations
- Complex bug fixes
- Security enhancements

---

## Recognition

### Contributor Recognition

**We recognize contributions in multiple ways:**

#### 1. Contributors List

All contributors are listed in:
- README.md (Contributors section)
- GitHub contributors page
- Release notes

#### 2. Commit Attribution

Your commits will be attributed to you in:
- Git history
- GitHub interface
- Release notes
- Changelog

#### 3. Public Thanks

We publicly thank contributors:
- In release announcements
- On social media
- In community updates
- In documentation

#### 4. Maintainer Status

**Significant contributors may be invited to become maintainers:**

Requirements for maintainer status:
- Multiple high-quality contributions
- Demonstrated understanding of project architecture
- Active participation in reviews
- Commitment to project values
- Community involvement

Maintainer privileges:
- Write access to repository
- Ability to merge PRs
- Involvement in project direction
- Priority support

### Contribution Types Recognized

**We value all types of contributions:**

-  Code contributions
-  Documentation improvements
-  Bug reports
-  Feature suggestions
-  Design improvements
-  Test additions
-  Community building
-  Code reviews
-  Tutorial creation
-  Helping others in issues/discussions

---

## License

By contributing to FakeAI, you agree that your contributions will be licensed under the **Apache License 2.0**.

All contributed code must be your original work or properly attributed.

---

## Getting Help

### Resources

**Before asking for help, check these resources:**

1. **Documentation**
   - README.md - User guide
   - CLAUDE.md - Technical architecture
   - API_REFERENCE.md - Complete API docs
   - examples/ - 50+ code examples

2. **Search Existing Issues**
   - Check if your question has been asked
   - Look for similar problems
   - Review closed issues

3. **Run Server Docs**
   ```bash
   fakeai server
   # Visit http://localhost:8000/docs
   ```

### Asking Questions

**When asking questions:**

1. **Provide context**
   - What are you trying to achieve?
   - What have you tried?
   - What error did you get?

2. **Include details**
   - Python version
   - FakeAI version
   - Operating system
   - Relevant code snippet
   - Error messages and stack traces

3. **Create minimal reproducible example**
   ```python
   # Minimal example that demonstrates the issue
   from fakeai import FakeAIService
   from fakeai.config import AppConfig

   config = AppConfig()
   service = FakeAIService(config)

   # Code that produces the issue
   ```

### Reporting Bugs

**Good bug reports include:**

**Template:**

```markdown
## Bug Description

Clear, concise description of the bug.

## Steps to Reproduce

1. Start server with `fakeai server`
2. Send request:
   \`\`\`python
   # Code to reproduce
   \`\`\`
3. Observe error

## Expected Behavior

What you expected to happen.

## Actual Behavior

What actually happened.

## Error Messages

\`\`\`
Paste full error message and stack trace here
\`\`\`

## Environment

- FakeAI version: 3.0.0
- Python version: 3.10.12
- Operating system: Ubuntu 22.04
- Installation method: pip / git clone

## Additional Context

Any other relevant information.
```

### Suggesting Features

**Good feature requests include:**

**Template:**

```markdown
## Feature Description

Clear description of the proposed feature.

## Motivation

Why is this feature needed? What problem does it solve?

## Proposed Solution

How should this feature work?

\`\`\`python
# Example API or usage
\`\`\`

## Alternatives Considered

What other solutions did you consider?

## Additional Context

Any other relevant information.
```

---

## Contact

### Maintainers

**Project Lead:**
- Anthony Casagrande

### Communication Channels

**GitHub:**
- Issues: Bug reports and feature requests
- Discussions: General questions and discussions
- Pull Requests: Code contributions

### Response Times

**Expected response times:**
- Bug reports: 1-3 business days
- Feature requests: 1-7 business days
- Pull requests: 2-7 business days
- Questions: 1-3 business days

Please be patient - this is an open source project maintained by volunteers.

---

## Thank You!

**Thank you for contributing to FakeAI!**

Your contributions help make this project better for everyone. We appreciate your time, effort, and dedication to maintaining high-quality standards.

Every contribution, no matter how small, makes a difference. Whether you're fixing a typo, adding a test, or implementing a major feature, we value your work.

**Happy coding!**

---

*Last updated: October 5, 2025*
*Version: 3.0.0 "Perfection Edition"*
