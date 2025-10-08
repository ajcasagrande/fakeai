"""Integration tests for moderation service.

This module tests the /v1/moderations endpoint with comprehensive coverage of:
- Text moderation across all 13 categories
- Category scores and thresholds
- Flagged content detection
- Multiple input moderation (batch)
- Different moderation models
- Multi-modal moderation (text + images)
- Concurrent moderation requests
- Edge cases (empty input, very long input)
- Different languages
- Category-specific filtering
"""


import pytest

from .utils import FakeAIClient


class TestModerationBasic:
    """Test basic moderation functionality."""

    @pytest.mark.integration
    def test_safe_text_moderation(self, client: FakeAIClient):
        """Test moderation with safe content."""
        response = client.create_moderation(
            input="Hello, world! This is a friendly message."
        )

        # Validate response structure
        assert "id" in response
        assert response["id"].startswith("modr-")
        assert "model" in response
        assert response["model"] == "omni-moderation-latest"
        assert "results" in response
        assert len(response["results"]) == 1

        # Validate result
        result = response["results"][0]
        assert "flagged" in result
        assert result["flagged"] is False
        assert "categories" in result
        assert "category_scores" in result

        # All categories should be False for safe content
        categories = result["categories"]
        assert categories["sexual"] is False
        assert categories["hate"] is False
        assert categories["harassment"] is False
        assert categories["self-harm"] is False
        assert categories["violence"] is False

        # All scores should be very low
        scores = result["category_scores"]
        assert scores["sexual"] < 0.1
        assert scores["hate"] < 0.1
        assert scores["harassment"] < 0.1
        assert scores["self-harm"] < 0.1
        assert scores["violence"] < 0.1

    @pytest.mark.integration
    def test_default_model(self, client: FakeAIClient):
        """Test that default model is used when not specified."""
        response = client.create_moderation(input="Test message")

        assert response["model"] == "omni-moderation-latest"

    @pytest.mark.integration
    def test_custom_model(self, client: FakeAIClient):
        """Test moderation with custom model."""
        response = client.create_moderation(
            input="Test message", model="text-moderation-007"
        )

        assert response["model"] == "text-moderation-007"


class TestModerationCategories:
    """Test moderation categories and detection."""

    @pytest.mark.integration
    def test_violence_detection(self, client: FakeAIClient):
        """Test violence content detection."""
        response = client.create_moderation(
            input="I want to kill and attack someone with a weapon"
        )

        result = response["results"][0]
        assert result["flagged"] is True
        assert result["categories"]["violence"] is True
        assert result["category_scores"]["violence"] > 0.5

    @pytest.mark.integration
    def test_violence_graphic_detection(self, client: FakeAIClient):
        """Test graphic violence content detection."""
        response = client.create_moderation(
            input="There was blood and gore everywhere, dismembered bodies"
        )

        result = response["results"][0]
        assert result["flagged"] is True
        assert result["categories"]["violence/graphic"] is True
        assert result["category_scores"]["violence/graphic"] > 0.5

    @pytest.mark.integration
    def test_hate_detection(self, client: FakeAIClient):
        """Test hate speech detection."""
        response = client.create_moderation(
            input="I hate this racist discriminatory bigot"
        )

        result = response["results"][0]
        assert result["flagged"] is True
        assert result["categories"]["hate"] is True
        assert result["category_scores"]["hate"] > 0.5

    @pytest.mark.integration
    def test_hate_threatening_detection(self, client: FakeAIClient):
        """Test threatening hate speech detection."""
        response = client.create_moderation(
            input="Death threat to lynch and exterminate them"
        )

        result = response["results"][0]
        assert result["flagged"] is True
        assert result["categories"]["hate/threatening"] is True
        assert result["category_scores"]["hate/threatening"] > 0.5

    @pytest.mark.integration
    def test_sexual_detection(self, client: FakeAIClient):
        """Test sexual content detection."""
        response = client.create_moderation(
            input="Explicit sexual porn content xxx nsfw erotic"
        )

        result = response["results"][0]
        assert result["flagged"] is True
        assert result["categories"]["sexual"] is True
        assert result["category_scores"]["sexual"] > 0.5

    @pytest.mark.integration
    def test_self_harm_detection(self, client: FakeAIClient):
        """Test self-harm content detection."""
        response = client.create_moderation(
            input="I want to commit suicide and end my life, self-harm"
        )

        result = response["results"][0]
        assert result["flagged"] is True
        assert result["categories"]["self-harm"] is True
        assert result["category_scores"]["self-harm"] > 0.5

    @pytest.mark.integration
    def test_self_harm_intent_detection(self, client: FakeAIClient):
        """Test self-harm intent detection."""
        response = client.create_moderation(
            input="I want to die and going to kill myself, planning suicide"
        )

        result = response["results"][0]
        assert result["flagged"] is True
        assert result["categories"]["self-harm/intent"] is True
        assert result["category_scores"]["self-harm/intent"] > 0.5

    @pytest.mark.integration
    def test_self_harm_instructions_detection(self, client: FakeAIClient):
        """Test self-harm instructions detection."""
        response = client.create_moderation(
            input="Here's how to commit suicide and ways to kill yourself"
        )

        result = response["results"][0]
        assert result["flagged"] is True
        assert result["categories"]["self-harm/instructions"] is True
        assert result["category_scores"]["self-harm/instructions"] > 0.5

    @pytest.mark.integration
    def test_harassment_detection(self, client: FakeAIClient):
        """Test harassment content detection."""
        response = client.create_moderation(
            input="You are a bully, harassing and threatening people"
        )

        result = response["results"][0]
        assert result["flagged"] is True
        assert result["categories"]["harassment"] is True
        assert result["category_scores"]["harassment"] > 0.5

    @pytest.mark.integration
    def test_harassment_threatening_detection(self, client: FakeAIClient):
        """Test threatening harassment detection."""
        response = client.create_moderation(
            input="I will hurt you and you will regret this, watch your back"
        )

        result = response["results"][0]
        assert result["flagged"] is True
        assert result["categories"]["harassment/threatening"] is True
        assert result["category_scores"]["harassment/threatening"] > 0.5

    @pytest.mark.integration
    def test_illicit_detection(self, client: FakeAIClient):
        """Test illicit activity detection."""
        response = client.create_moderation(
            input="How to hack systems and steal things illegally, sell drugs"
        )

        result = response["results"][0]
        assert result["flagged"] is True
        assert result["categories"]["illicit"] is True
        assert result["category_scores"]["illicit"] > 0.5

    @pytest.mark.integration
    def test_illicit_violent_detection(self, client: FakeAIClient):
        """Test violent illicit activity detection."""
        response = client.create_moderation(
            input="How to make a bomb and build explosives for mass shooting"
        )

        result = response["results"][0]
        assert result["flagged"] is True
        assert result["categories"]["illicit/violent"] is True
        assert result["category_scores"]["illicit/violent"] > 0.5


class TestModerationScores:
    """Test category scores and thresholds."""

    @pytest.mark.integration
    def test_score_ranges(self, client: FakeAIClient):
        """Test that all scores are in valid range [0, 1]."""
        response = client.create_moderation(
            input="This is a test message with some violence keywords like kill"
        )

        scores = response["results"][0]["category_scores"]

        # All scores should be between 0 and 1
        for category, score in scores.items():
            assert 0.0 <= score <= 1.0, f"{category} score {score} out of range"

    @pytest.mark.integration
    def test_flagging_threshold(self, client: FakeAIClient):
        """Test that flagging is based on 0.5 threshold."""
        response = client.create_moderation(
            input="Message with violence: kill and attack with weapon"
        )

        result = response["results"][0]
        scores = result["category_scores"]
        categories = result["categories"]

        # Categories with score > 0.5 should be flagged
        for category, score in scores.items():
            flagged = categories[category]
            if score > 0.5:
                assert flagged is True, f"{category} should be flagged (score: {score})"

    @pytest.mark.integration
    def test_multiple_categories_flagged(self, client: FakeAIClient):
        """Test content that triggers multiple categories."""
        response = client.create_moderation(
            input="Violent hate speech: I want to kill those racist bigots with weapons"
        )

        result = response["results"][0]
        assert result["flagged"] is True

        # Should trigger both violence and hate
        assert result["category_scores"]["violence"] > 0.5
        assert result["category_scores"]["hate"] > 0.5


class TestModerationBatch:
    """Test multiple input moderation."""

    @pytest.mark.integration
    def test_multiple_text_inputs(self, client: FakeAIClient):
        """Test moderation with multiple text inputs."""
        inputs = [
            "This is safe content",
            "This contains violence: kill and attack",
            "This is also safe",
        ]

        response = client.create_moderation(input=inputs)

        # Should have 3 results
        assert len(response["results"]) == 3

        # First and third should be safe
        assert response["results"][0]["flagged"] is False
        assert response["results"][2]["flagged"] is False

        # Second should be flagged
        assert response["results"][1]["flagged"] is True
        assert response["results"][1]["categories"]["violence"] is True

    @pytest.mark.integration
    def test_batch_consistency(self, client: FakeAIClient):
        """Test that batch moderation is consistent with single moderation."""
        text = "Violence: kill and attack with weapons"

        # Single moderation
        single_response = client.create_moderation(input=text)

        # Batch moderation
        batch_response = client.create_moderation(input=[text])

        # Results should be similar (scores may vary due to randomness)
        single_result = single_response["results"][0]
        batch_result = batch_response["results"][0]

        assert single_result["flagged"] == batch_result["flagged"]
        assert (
            single_result["categories"]["violence"]
            == batch_result["categories"]["violence"]
        )

    @pytest.mark.integration
    def test_large_batch(self, client: FakeAIClient):
        """Test moderation with large batch of inputs."""
        inputs = [f"Test message number {i}" for i in range(50)]

        response = client.create_moderation(input=inputs)

        # Should have 50 results
        assert len(response["results"]) == 50

        # All should be safe
        for result in response["results"]:
            assert result["flagged"] is False


class TestModerationMultimodal:
    """Test multi-modal moderation (text + images)."""

    @pytest.mark.integration
    def test_multimodal_safe_content(self, client: FakeAIClient):
        """Test multimodal moderation with safe content."""
        response = client.create_moderation(
            input=[
                {"type": "text", "text": "This is a safe message"},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/image.jpg"},
                },
            ]
        )

        result = response["results"][0]
        assert result["flagged"] is False

    @pytest.mark.integration
    def test_multimodal_harmful_text(self, client: FakeAIClient):
        """Test multimodal moderation with harmful text."""
        response = client.create_moderation(
            input=[
                {"type": "text", "text": "Violence: kill and attack with weapons"},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/image.jpg"},
                },
            ]
        )

        result = response["results"][0]
        assert result["flagged"] is True
        assert result["categories"]["violence"] is True

    @pytest.mark.integration
    def test_multimodal_applied_input_types(self, client: FakeAIClient):
        """Test that applied input types are returned for multimodal content."""
        response = client.create_moderation(
            input=[
                {"type": "text", "text": "Sexual content: porn and nude explicit"},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/image.jpg"},
                },
            ]
        )

        result = response["results"][0]
        if result["flagged"]:
            # Should have applied_input_types for flagged categories
            assert "category_applied_input_types" in result

            # Sexual is a multimodal category
            if result["categories"]["sexual"]:
                applied = result["category_applied_input_types"].get("sexual")
                if applied:
                    assert isinstance(applied, list)
                    assert len(applied) > 0
                    # Should contain 'text' and/or 'image'
                    assert all(t in ["text", "image"] for t in applied)

    @pytest.mark.integration
    def test_multimodal_multiple_text_parts(self, client: FakeAIClient):
        """Test multimodal with multiple text parts."""
        response = client.create_moderation(
            input=[
                {"type": "text", "text": "First text part"},
                {
                    "type": "image_url",
                    "image_url": {"url": "https://example.com/image.jpg"},
                },
                {"type": "text", "text": "Second text part with violence: kill"},
            ]
        )

        result = response["results"][0]
        # Should combine all text parts
        assert result["flagged"] is True


class TestModerationEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.integration
    def test_empty_string_input(self, client: FakeAIClient):
        """Test moderation with empty string."""
        response = client.create_moderation(input="")

        result = response["results"][0]
        assert result["flagged"] is False

    @pytest.mark.integration
    def test_empty_list_input(self, client: FakeAIClient):
        """Test moderation with empty list."""
        response = client.create_moderation(input=[])

        # Should return at least one result
        assert len(response["results"]) >= 1
        assert response["results"][0]["flagged"] is False

    @pytest.mark.integration
    def test_very_long_input(self, client: FakeAIClient):
        """Test moderation with very long input."""
        long_text = "This is a safe message. " * 1000  # ~25,000 characters

        response = client.create_moderation(input=long_text)

        result = response["results"][0]
        assert "flagged" in result
        assert result["flagged"] is False

    @pytest.mark.integration
    def test_whitespace_only_input(self, client: FakeAIClient):
        """Test moderation with whitespace-only input."""
        response = client.create_moderation(input="   \n\t  ")

        result = response["results"][0]
        assert result["flagged"] is False

    @pytest.mark.integration
    def test_special_characters(self, client: FakeAIClient):
        """Test moderation with special characters."""
        response = client.create_moderation(input="!@#$%^&*()_+-=[]{}|;':\",./<>?")

        result = response["results"][0]
        assert result["flagged"] is False

    @pytest.mark.integration
    def test_unicode_characters(self, client: FakeAIClient):
        """Test moderation with unicode characters."""
        response = client.create_moderation(input="Hello 世界 🌍 мир 🎉")

        result = response["results"][0]
        assert result["flagged"] is False


class TestModerationLanguages:
    """Test moderation with different languages."""

    @pytest.mark.integration
    def test_spanish_safe_content(self, client: FakeAIClient):
        """Test moderation with safe Spanish content."""
        response = client.create_moderation(
            input="Hola, ¿cómo estás? Este es un mensaje amistoso."
        )

        result = response["results"][0]
        assert result["flagged"] is False

    @pytest.mark.integration
    def test_french_safe_content(self, client: FakeAIClient):
        """Test moderation with safe French content."""
        response = client.create_moderation(
            input="Bonjour, comment allez-vous? C'est un message amical."
        )

        result = response["results"][0]
        assert result["flagged"] is False

    @pytest.mark.integration
    def test_german_safe_content(self, client: FakeAIClient):
        """Test moderation with safe German content."""
        response = client.create_moderation(
            input="Guten Tag, wie geht es Ihnen? Dies ist eine freundliche Nachricht."
        )

        result = response["results"][0]
        assert result["flagged"] is False

    @pytest.mark.integration
    def test_mixed_language_content(self, client: FakeAIClient):
        """Test moderation with mixed language content."""
        response = client.create_moderation(
            input="Hello world! Hola mundo! Bonjour le monde! 你好世界!"
        )

        result = response["results"][0]
        assert result["flagged"] is False


class TestModerationConcurrency:
    """Test concurrent moderation requests."""

    @pytest.mark.integration
    def test_concurrent_requests(self, client: FakeAIClient):
        """Test multiple sequential moderation requests (simulates concurrency)."""
        # TestClient doesn't support true async concurrency, so we test sequential requests
        # which still validates the endpoint works correctly for multiple calls
        responses = []
        for i in range(10):
            response = client.create_moderation(input=f"Test message {i}")
            responses.append(response)

        # All should succeed
        assert len(responses) == 10
        for response in responses:
            assert "results" in response
            assert len(response["results"]) == 1

    @pytest.mark.integration
    def test_concurrent_batch_requests(self, client: FakeAIClient):
        """Test multiple sequential batch moderation requests (simulates concurrency)."""
        # TestClient doesn't support true async concurrency, so we test sequential requests
        responses = []
        for i in range(5):
            response = client.create_moderation(
                input=[
                    f"Message {i}-1",
                    f"Message {i}-2 with violence: kill",
                    f"Message {i}-3",
                ]
            )
            responses.append(response)

        # All should succeed with 3 results each
        assert len(responses) == 5
        for response in responses:
            assert len(response["results"]) == 3


class TestModerationResponseStructure:
    """Test moderation response structure and validation."""

    @pytest.mark.integration
    def test_response_has_all_categories(self, client: FakeAIClient):
        """Test that response includes all 13 categories."""
        response = client.create_moderation(input="Test message")

        result = response["results"][0]
        categories = result["categories"]
        scores = result["category_scores"]

        # Expected categories
        expected_categories = [
            "sexual",
            "hate",
            "harassment",
            "self-harm",
            "sexual/minors",
            "hate/threatening",
            "harassment/threatening",
            "self-harm/intent",
            "self-harm/instructions",
            "violence",
            "violence/graphic",
            "illicit",
            "illicit/violent",
        ]

        # All categories should be present
        for category in expected_categories:
            assert category in categories, f"Missing category: {category}"
            assert category in scores, f"Missing score for: {category}"

    @pytest.mark.integration
    def test_response_id_format(self, client: FakeAIClient):
        """Test that response ID has correct format."""
        response = client.create_moderation(input="Test message")

        # ID should start with "modr-"
        assert response["id"].startswith("modr-")
        # ID should be reasonable length
        assert len(response["id"]) > 10

    @pytest.mark.integration
    def test_response_model_field(self, client: FakeAIClient):
        """Test that response includes model field."""
        response = client.create_moderation(
            input="Test message", model="text-moderation-stable"
        )

        assert response["model"] == "text-moderation-stable"

    @pytest.mark.integration
    def test_category_scores_are_floats(self, client: FakeAIClient):
        """Test that all category scores are floats."""
        response = client.create_moderation(input="Test message")

        scores = response["results"][0]["category_scores"]
        for category, score in scores.items():
            assert isinstance(
                score, (float, int)
            ), f"{category} score is not numeric: {type(score)}"

    @pytest.mark.integration
    def test_categories_are_booleans(self, client: FakeAIClient):
        """Test that all category flags are booleans."""
        response = client.create_moderation(input="Test message")

        categories = response["results"][0]["categories"]
        for category, flagged in categories.items():
            assert isinstance(
                flagged, bool
            ), f"{category} flag is not boolean: {type(flagged)}"
