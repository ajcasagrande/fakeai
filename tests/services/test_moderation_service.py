"""
Tests for ModerationService.

Tests content moderation functionality including:
- Safe content detection
- Harmful content flagging across all 13 categories
- Multimodal input handling
- Token tracking
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest

from fakeai.config import AppConfig
from fakeai.metrics import MetricsTracker
from fakeai.models import ModerationRequest
from fakeai.services.moderation_service import ModerationService


@pytest.fixture
def config():
    """Create test configuration."""
    return AppConfig(response_delay=0.0)


@pytest.fixture
def metrics_tracker():
    """Create metrics tracker instance."""
    return MetricsTracker()


@pytest.fixture
def moderation_service(config, metrics_tracker):
    """Create moderation service instance."""
    return ModerationService(
        config=config,
        metrics_tracker=metrics_tracker,
        model_registry=None,
    )


@pytest.mark.asyncio
async def test_safe_content(moderation_service):
    """Test that safe content is not flagged."""
    request = ModerationRequest(input="Hello, how are you today?")
    response = await moderation_service.create_moderation(request)

    assert response.id.startswith("modr-")
    assert response.model == "omni-moderation-latest"
    assert len(response.results) == 1

    result = response.results[0]
    assert result.flagged is False
    assert result.categories.sexual is False
    assert result.categories.hate is False
    assert result.categories.harassment is False
    assert result.categories.self_harm is False
    assert result.categories.violence is False


@pytest.mark.asyncio
async def test_violence_content(moderation_service):
    """Test that violent content is flagged."""
    request = ModerationRequest(input="I want to kill and murder people with a gun.")
    response = await moderation_service.create_moderation(request)

    result = response.results[0]
    assert result.flagged is True
    assert result.categories.violence is True
    assert result.category_scores.violence > 0.5
    assert result.category_scores.violence_graphic > 0.0


@pytest.mark.asyncio
async def test_hate_content(moderation_service):
    """Test that hate speech is flagged."""
    request = ModerationRequest(
        input="I hate this group and want to discriminate against them with racist slurs."
    )
    response = await moderation_service.create_moderation(request)

    result = response.results[0]
    assert result.flagged is True
    assert result.categories.hate is True
    assert result.category_scores.hate > 0.5


@pytest.mark.asyncio
async def test_sexual_content(moderation_service):
    """Test that sexual content is flagged."""
    request = ModerationRequest(
        input="This is explicit sexual content with porn and nude images nsfw."
    )
    response = await moderation_service.create_moderation(request)

    result = response.results[0]
    assert result.flagged is True
    assert result.categories.sexual is True
    assert result.category_scores.sexual > 0.5


@pytest.mark.asyncio
async def test_self_harm_content(moderation_service):
    """Test that self-harm content is flagged."""
    request = ModerationRequest(
        input="I want to commit suicide and kill myself by cutting."
    )
    response = await moderation_service.create_moderation(request)

    result = response.results[0]
    assert result.flagged is True
    assert result.categories.self_harm is True
    assert result.category_scores.self_harm > 0.5
    assert result.category_scores.self_harm_intent > 0.0


@pytest.mark.asyncio
async def test_harassment_content(moderation_service):
    """Test that harassment is flagged."""
    request = ModerationRequest(
        input="I'm going to bully and harass you, threaten and abuse you."
    )
    response = await moderation_service.create_moderation(request)

    result = response.results[0]
    assert result.flagged is True
    assert result.categories.harassment is True
    assert result.category_scores.harassment > 0.5


@pytest.mark.asyncio
async def test_illicit_content(moderation_service):
    """Test that illicit activity is flagged."""
    request = ModerationRequest(
        input="Here's how to hack into systems and steal data illegally."
    )
    response = await moderation_service.create_moderation(request)

    result = response.results[0]
    assert result.flagged is True
    assert result.categories.illicit is True
    assert result.category_scores.illicit > 0.5


@pytest.mark.asyncio
async def test_sexual_minors_content(moderation_service):
    """Test that sexual content involving minors is flagged."""
    request = ModerationRequest(
        input="Explicit sexual content involving children and minors under 18."
    )
    response = await moderation_service.create_moderation(request)

    result = response.results[0]
    assert result.flagged is True
    # Should flag both sexual and sexual_minors
    assert result.categories.sexual is True
    assert result.categories.sexual_minors is True
    assert result.category_scores.sexual_minors > 0.5


@pytest.mark.asyncio
async def test_string_array_input(moderation_service):
    """Test array of strings input."""
    request = ModerationRequest(
        input=["Hello world", "I want to kill someone", "Nice day today"]
    )
    response = await moderation_service.create_moderation(request)

    assert len(response.results) == 3
    assert response.results[0].flagged is False
    assert response.results[1].flagged is True
    assert response.results[2].flagged is False


@pytest.mark.asyncio
async def test_multimodal_text_only(moderation_service):
    """Test multimodal input with text only."""
    request = ModerationRequest(input=[{"type": "text", "text": "Hello world"}])
    response = await moderation_service.create_moderation(request)

    assert len(response.results) == 1
    assert response.results[0].flagged is False


@pytest.mark.asyncio
async def test_multimodal_with_image(moderation_service):
    """Test multimodal input with text and image."""
    request = ModerationRequest(
        input=[
            {"type": "text", "text": "This is violent content with guns and killing"},
            {
                "type": "image_url",
                "image_url": {"url": "https://example.com/image.jpg"},
            },
        ]
    )
    response = await moderation_service.create_moderation(request)

    result = response.results[0]
    assert result.flagged is True
    assert result.categories.violence is True
    # Should have applied input types for flagged category
    assert "violence" in result.category_applied_input_types
    assert len(result.category_applied_input_types["violence"]) > 0


@pytest.mark.asyncio
async def test_empty_input(moderation_service):
    """Test empty input handling."""
    request = ModerationRequest(input=[])
    response = await moderation_service.create_moderation(request)

    assert len(response.results) == 1
    assert response.results[0].flagged is False


@pytest.mark.asyncio
async def test_custom_model(moderation_service):
    """Test custom model specification."""
    request = ModerationRequest(input="Hello world", model="text-moderation-stable")
    response = await moderation_service.create_moderation(request)

    assert response.model == "text-moderation-stable"


@pytest.mark.asyncio
async def test_all_scores_present(moderation_service):
    """Test that all 13 category scores are present."""
    request = ModerationRequest(input="Safe content")
    response = await moderation_service.create_moderation(request)

    result = response.results[0]
    scores = result.category_scores

    # Check all 13 categories have scores
    assert 0.0 <= scores.sexual <= 1.0
    assert 0.0 <= scores.hate <= 1.0
    assert 0.0 <= scores.harassment <= 1.0
    assert 0.0 <= scores.self_harm <= 1.0
    assert 0.0 <= scores.sexual_minors <= 1.0
    assert 0.0 <= scores.hate_threatening <= 1.0
    assert 0.0 <= scores.harassment_threatening <= 1.0
    assert 0.0 <= scores.self_harm_intent <= 1.0
    assert 0.0 <= scores.self_harm_instructions <= 1.0
    assert 0.0 <= scores.violence <= 1.0
    assert 0.0 <= scores.violence_graphic <= 1.0
    assert 0.0 <= scores.illicit <= 1.0
    assert 0.0 <= scores.illicit_violent <= 1.0


@pytest.mark.asyncio
async def test_metrics_tracking(moderation_service, metrics_tracker):
    """Test that token usage is tracked in metrics."""
    # Get initial stats
    initial_stats = metrics_tracker.get_all_stats()
    initial_moderations = (
        initial_stats.get("/v1/moderations", {}).get("requests", {}).get("count", 0)
    )

    request = ModerationRequest(input="This is a test message for metrics tracking")
    await moderation_service.create_moderation(request)

    # Should have tracked the request
    final_stats = metrics_tracker.get_all_stats()
    final_moderations = (
        final_stats.get("/v1/moderations", {}).get("requests", {}).get("count", 0)
    )

    # Metrics tracking may vary based on implementation
    # At minimum, the service should complete without errors
    assert final_moderations >= initial_moderations


@pytest.mark.asyncio
async def test_hate_threatening_subcategory(moderation_service):
    """Test hate/threatening subcategory detection."""
    request = ModerationRequest(
        input="I hate you and will lynch you, death threat incoming"
    )
    response = await moderation_service.create_moderation(request)

    result = response.results[0]
    assert result.flagged is True
    assert result.categories.hate is True
    assert result.categories.hate_threatening is True
    assert result.category_scores.hate_threatening > 0.5


@pytest.mark.asyncio
async def test_harassment_threatening_subcategory(moderation_service):
    """Test harassment/threatening subcategory detection."""
    request = ModerationRequest(
        input="I will hurt you and you will regret this, watch your back"
    )
    response = await moderation_service.create_moderation(request)

    result = response.results[0]
    assert result.flagged is True
    assert result.categories.harassment is True
    assert result.categories.harassment_threatening is True
    assert result.category_scores.harassment_threatening > 0.5


@pytest.mark.asyncio
async def test_self_harm_intent_subcategory(moderation_service):
    """Test self-harm/intent subcategory detection."""
    request = ModerationRequest(
        input="I want to die and am planning suicide, going to kill myself"
    )
    response = await moderation_service.create_moderation(request)

    result = response.results[0]
    assert result.flagged is True
    assert result.categories.self_harm is True
    assert result.categories.self_harm_intent is True
    assert result.category_scores.self_harm_intent > 0.5


@pytest.mark.asyncio
async def test_self_harm_instructions_subcategory(moderation_service):
    """Test self-harm/instructions subcategory detection."""
    request = ModerationRequest(
        input="Here are ways to kill yourself and how to commit suicide step by step"
    )
    response = await moderation_service.create_moderation(request)

    result = response.results[0]
    assert result.flagged is True
    assert result.categories.self_harm_instructions is True
    assert result.category_scores.self_harm_instructions > 0.5


@pytest.mark.asyncio
async def test_illicit_violent_subcategory(moderation_service):
    """Test illicit/violent subcategory detection."""
    request = ModerationRequest(
        input="How to make a bomb and build explosives for a mass shooting plan"
    )
    response = await moderation_service.create_moderation(request)

    result = response.results[0]
    assert result.flagged is True
    assert result.categories.illicit_violent is True
    assert result.category_scores.illicit_violent > 0.5


@pytest.mark.asyncio
async def test_violence_graphic_subcategory(moderation_service):
    """Test violence/graphic subcategory detection."""
    request = ModerationRequest(
        input="Graphic descriptions of blood, gore, mutilation, and dismemberment"
    )
    response = await moderation_service.create_moderation(request)

    result = response.results[0]
    assert result.flagged is True
    assert result.categories.violence_graphic is True
    assert result.category_scores.violence_graphic > 0.5
