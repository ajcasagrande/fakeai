"""
Architecture Validation Tests

Tests that the codebase architecture is sound:
- No circular dependencies
- All modules importable
- Services are independent
- Shared utilities work correctly
- Model registry is functional
"""

import importlib
import inspect
import os
import sys
import pytest
from pathlib import Path


# ==============================================================================
# Module Import Tests
# ==============================================================================


def test_all_core_modules_importable():
    """Test that all core modules can be imported."""
    core_modules = [
        "fakeai.app",
        "fakeai.config",
        "fakeai.fakeai_service",
        "fakeai.models",
        "fakeai.metrics",
        "fakeai.utils",
        "fakeai.cli",
    ]

    for module_name in core_modules:
        try:
            importlib.import_module(module_name)
        except Exception as e:
            pytest.fail(f"Failed to import {module_name}: {e}")


def test_all_service_modules_importable():
    """Test that all service modules can be imported."""
    service_modules = [
        "fakeai.services.audio_service",
        "fakeai.services.batch_service",
        "fakeai.services.embedding_service",
        "fakeai.services.file_service",
        "fakeai.services.image_generation_service",
        "fakeai.services.moderation_service",
    ]

    for module_name in service_modules:
        try:
            importlib.import_module(module_name)
        except Exception as e:
            pytest.fail(f"Failed to import {module_name}: {e}")


def test_all_metrics_modules_importable():
    """Test that all metrics modules can be imported."""
    metrics_modules = [
        "fakeai.metrics",
        "fakeai.model_metrics",
        "fakeai.batch_metrics",
        "fakeai.streaming_metrics",
        "fakeai.dynamo_metrics",
        "fakeai.dynamo_metrics_advanced",
        "fakeai.dcgm_metrics",
        "fakeai.cost_tracker",
        "fakeai.rate_limiter_metrics",
        "fakeai.error_metrics",
    ]

    for module_name in metrics_modules:
        try:
            importlib.import_module(module_name)
        except Exception as e:
            pytest.fail(f"Failed to import {module_name}: {e}")


def test_all_utility_modules_importable():
    """Test that all utility modules can be imported."""
    utility_modules = [
        "fakeai.utils",
        "fakeai.audio",
        "fakeai.video",
        "fakeai.security",
        "fakeai.rate_limiter",
        "fakeai.prompt_caching",
        "fakeai.context_validator",
        "fakeai.error_injector",
    ]

    for module_name in utility_modules:
        try:
            importlib.import_module(module_name)
        except Exception as e:
            pytest.fail(f"Failed to import {module_name}: {e}")


def test_optional_dependencies_handled():
    """Test that optional dependencies are handled gracefully."""
    # Try importing modules that require optional deps
    try:
        from fakeai.semantic_embeddings import SemanticEmbeddingGenerator
        # If import succeeds, that's good
    except ImportError:
        # If import fails, that's also acceptable (optional dependency)
        pass

    try:
        from fakeai.llm_generator import LLMGenerator
    except ImportError:
        pass


# ==============================================================================
# Circular Dependency Tests
# ==============================================================================


def test_no_circular_dependencies_in_core():
    """Test that core modules don't have circular dependencies."""
    # Import order should work without errors
    import fakeai.models
    import fakeai.config
    import fakeai.utils
    import fakeai.metrics
    import fakeai.fakeai_service
    import fakeai.app

    # If we got here, no circular dependencies


def test_no_circular_dependencies_in_services():
    """Test that service modules don't have circular dependencies."""
    import fakeai.services.audio_service
    import fakeai.services.batch_service
    import fakeai.services.embedding_service
    import fakeai.services.file_service
    import fakeai.services.image_generation_service
    import fakeai.services.moderation_service


def test_no_circular_dependencies_in_metrics():
    """Test that metrics modules don't have circular dependencies."""
    import fakeai.metrics
    import fakeai.model_metrics
    import fakeai.batch_metrics
    import fakeai.streaming_metrics


# ==============================================================================
# Service Independence Tests
# ==============================================================================


def test_audio_service_independent():
    """Test that AudioService can work independently."""
    from fakeai.services.audio_service import AudioService
    from fakeai.config import AppConfig

    config = AppConfig()
    service = AudioService(config)

    # Should be able to create without other services
    assert service is not None


def test_batch_service_independent():
    """Test that BatchService can work independently."""
    from fakeai.services.batch_service import BatchService
    from fakeai.config import AppConfig

    config = AppConfig()
    service = BatchService(config)

    assert service is not None


def test_embedding_service_independent():
    """Test that EmbeddingService can work independently."""
    from fakeai.services.embedding_service import EmbeddingService
    from fakeai.config import AppConfig

    config = AppConfig()
    service = EmbeddingService(config)

    assert service is not None


def test_file_service_independent():
    """Test that FileService can work independently."""
    from fakeai.services.file_service import FileService
    from fakeai.config import AppConfig

    config = AppConfig()
    service = FileService(config)

    assert service is not None


def test_image_generation_service_independent():
    """Test that ImageGenerationService can work independently."""
    from fakeai.services.image_generation_service import ImageGenerationService
    from fakeai.config import AppConfig

    config = AppConfig()
    service = ImageGenerationService(config)

    assert service is not None


def test_moderation_service_independent():
    """Test that ModerationService can work independently."""
    from fakeai.services.moderation_service import ModerationService
    from fakeai.config import AppConfig

    config = AppConfig()
    service = ModerationService(config)

    assert service is not None


# ==============================================================================
# Shared Utilities Tests
# ==============================================================================


def test_utils_extract_text_content():
    """Test extract_text_content utility."""
    from fakeai.utils import extract_text_content

    # String input
    result = extract_text_content("Hello")
    assert result == "Hello"

    # List input
    result = extract_text_content([
        {"type": "text", "text": "Hello"},
        {"type": "text", "text": "World"},
    ])
    assert "Hello" in result and "World" in result

    # None input
    result = extract_text_content(None)
    assert result == ""


def test_utils_calculate_token_count():
    """Test calculate_token_count utility."""
    from fakeai.utils import calculate_token_count

    # Simple text
    count = calculate_token_count("Hello world")
    assert count > 0

    # Empty text
    count = calculate_token_count("")
    assert count == 0

    # Text with punctuation
    count = calculate_token_count("Hello, world! How are you?")
    assert count > 5


def test_utils_tokenize_text():
    """Test tokenize_text utility."""
    from fakeai.utils import tokenize_text

    tokens = tokenize_text("Hello world! This is a test.")
    assert len(tokens) > 0
    assert isinstance(tokens, list)


def test_utils_generate_completion():
    """Test generate_completion utility."""
    from fakeai.utils import generate_completion

    text = generate_completion("Hello", max_tokens=10)
    assert len(text) > 0
    assert isinstance(text, str)


def test_audio_utils_work():
    """Test audio utilities."""
    from fakeai.audio import estimate_audio_tokens, generate_audio_output

    # Estimate tokens
    tokens = estimate_audio_tokens(duration_seconds=5.0)
    assert tokens > 0

    # Generate audio
    audio = generate_audio_output("Test text", voice="alloy")
    assert "data" in audio or "transcript" in audio


def test_video_utils_work():
    """Test video utilities."""
    from fakeai.video import estimate_video_tokens

    tokens = estimate_video_tokens(
        duration_seconds=5.0,
        fps=4,
        width=512,
        height=288,
        detail="low",
    )
    assert tokens > 0


# ==============================================================================
# Model Registry Tests
# ==============================================================================


def test_model_registry_has_models():
    """Test that model registry contains models."""
    from fakeai.fakeai_service import FakeAIService
    from fakeai.config import AppConfig

    config = AppConfig()
    service = FakeAIService(config)

    models = service.models
    assert len(models) > 0


def test_model_registry_auto_creates():
    """Test that models are auto-created."""
    from fakeai.fakeai_service import FakeAIService
    from fakeai.config import AppConfig

    config = AppConfig()
    service = FakeAIService(config)

    # Request a non-existent model
    service._ensure_model_exists("test-model-123")

    # Should now exist
    assert "test-model-123" in service.models


def test_model_registry_has_required_models():
    """Test that required models are in registry."""
    from fakeai.fakeai_service import FakeAIService
    from fakeai.config import AppConfig

    config = AppConfig()
    service = FakeAIService(config)

    required_models = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "gpt-4o",
        "gpt-4o-mini",
        "text-embedding-3-small",
    ]

    for model in required_models:
        service._ensure_model_exists(model)
        assert model in service.models


# ==============================================================================
# Configuration Tests
# ==============================================================================


def test_config_can_be_instantiated():
    """Test that AppConfig can be instantiated."""
    from fakeai.config import AppConfig

    config = AppConfig()
    assert config is not None


def test_config_has_required_fields():
    """Test that config has all required fields."""
    from fakeai.config import AppConfig

    config = AppConfig()

    required_fields = [
        "host",
        "port",
        "debug",
        "response_delay",
        "random_delay",
        "require_api_key",
    ]

    for field in required_fields:
        assert hasattr(config, field)


def test_config_validation_works():
    """Test that config validation works."""
    from fakeai.config import AppConfig

    # Valid config
    config = AppConfig(
        host="127.0.0.1",
        port=8000,
        debug=False,
    )
    assert config.port == 8000

    # Invalid port should raise error
    with pytest.raises(Exception):
        AppConfig(port=99999999)


# ==============================================================================
# Dependency Injection Tests
# ==============================================================================


def test_service_dependencies_injected():
    """Test that FakeAIService gets all dependencies."""
    from fakeai.fakeai_service import FakeAIService
    from fakeai.config import AppConfig

    config = AppConfig()
    service = FakeAIService(config)

    # Should have metrics
    assert hasattr(service, "metrics_tracker")

    # Should have cost tracker
    assert hasattr(service, "cost_tracker")

    # Should have model metrics
    assert hasattr(service, "model_metrics_tracker")


def test_app_dependencies_injected():
    """Test that FastAPI app gets all dependencies."""
    from fakeai.app import app, fakeai_service, metrics_tracker

    # Should have service
    assert fakeai_service is not None

    # Should have metrics
    assert metrics_tracker is not None


# ==============================================================================
# Interface Tests
# ==============================================================================


def test_service_has_required_methods():
    """Test that FakeAIService has all required methods."""
    from fakeai.fakeai_service import FakeAIService
    from fakeai.config import AppConfig

    config = AppConfig()
    service = FakeAIService(config)

    required_methods = [
        "create_chat_completion",
        "create_completion",
        "create_embedding",
        "create_image_generation",
        "create_speech",
        "create_moderation",
        "list_models",
        "get_model",
    ]

    for method in required_methods:
        assert hasattr(service, method)
        assert callable(getattr(service, method))


def test_services_implement_required_interfaces():
    """Test that services implement required interfaces."""
    from fakeai.services.audio_service import AudioService
    from fakeai.services.embedding_service import EmbeddingService

    # Check they have required methods
    assert hasattr(AudioService, "generate_speech")
    assert hasattr(EmbeddingService, "create_embeddings")


# ==============================================================================
# Code Quality Tests
# ==============================================================================


def test_no_star_imports():
    """Test that code doesn't use star imports (bad practice)."""
    fakeai_dir = Path(__file__).parent.parent.parent / "fakeai"

    for py_file in fakeai_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue

        with open(py_file, "r") as f:
            content = f.read()

        # Check for "from X import *"
        if "from " in content and " import *" in content:
            # Allow in __init__.py files
            if not py_file.name == "__init__.py":
                pytest.fail(f"Star import found in {py_file}")


def test_all_modules_have_docstrings():
    """Test that all modules have docstrings."""
    fakeai_dir = Path(__file__).parent.parent.parent / "fakeai"

    for py_file in fakeai_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        if py_file.name == "__init__.py":
            continue

        with open(py_file, "r") as f:
            content = f.read()

        # Should have a module docstring
        if not ('"""' in content[:500] or "'''" in content[:500]):
            pytest.fail(f"No module docstring in {py_file}")


def test_critical_functions_have_docstrings():
    """Test that critical functions have docstrings."""
    from fakeai.fakeai_service import FakeAIService
    from fakeai.config import AppConfig

    config = AppConfig()
    service = FakeAIService(config)

    critical_methods = [
        "create_chat_completion",
        "create_embedding",
        "create_image_generation",
    ]

    for method_name in critical_methods:
        method = getattr(service, method_name)
        assert method.__doc__ is not None, f"{method_name} missing docstring"


# ==============================================================================
# File Structure Tests
# ==============================================================================


def test_required_files_exist():
    """Test that required files exist."""
    project_root = Path(__file__).parent.parent.parent

    required_files = [
        "fakeai/__init__.py",
        "fakeai/app.py",
        "fakeai/config.py",
        "fakeai/fakeai_service.py",
        "fakeai/models.py",
        "fakeai/metrics.py",
        "fakeai/utils.py",
        "fakeai/cli.py",
        "pyproject.toml",
        "README.md",
    ]

    for file_path in required_files:
        full_path = project_root / file_path
        assert full_path.exists(), f"Required file missing: {file_path}"


def test_services_directory_structure():
    """Test services directory structure."""
    services_dir = Path(__file__).parent.parent.parent / "fakeai" / "services"

    assert services_dir.exists()
    assert (services_dir / "__init__.py").exists()


def test_tests_directory_structure():
    """Test tests directory structure."""
    tests_dir = Path(__file__).parent.parent.parent / "tests"

    assert tests_dir.exists()
    assert (tests_dir / "conftest.py").exists()
    assert (tests_dir / "integration").exists()


# ==============================================================================
# Package Metadata Tests
# ==============================================================================


def test_package_metadata_exists():
    """Test that package metadata exists."""
    import fakeai

    assert hasattr(fakeai, "__version__")


def test_package_exports_correct_items():
    """Test that package __all__ is correct."""
    import fakeai

    assert hasattr(fakeai, "__all__")

    # Should export key classes
    assert "FakeAIService" in fakeai.__all__
    assert "AppConfig" in fakeai.__all__
    assert "app" in fakeai.__all__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
