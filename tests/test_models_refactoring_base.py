"""
Tests for models refactoring - Base module.

This test suite verifies backward compatibility of the new models package structure.
Tests that imports work from both old (fakeai.models) and new (fakeai.models._base,
fakeai.models._content) paths and that they reference the same classes.
"""

#  SPDX-License-Identifier: Apache-2.0

import pytest
from pydantic import ValidationError


class TestImportsFromModelsPackage:
    """Test that all models can be imported from the models package."""

    def test_import_base_models_from_package(self):
        """Test importing base models from fakeai.models package."""
        from fakeai.models import (
            AudioOutput,
            CompletionTokensDetails,
            ErrorDetail,
            ErrorResponse,
            Model,
            ModelCapabilitiesResponse,
            ModelListResponse,
            ModelPermission,
            ModelPricing,
            PromptTokensDetails,
            Role,
            Usage,
        )

        # Verify classes are imported correctly
        assert ModelPermission is not None
        assert ModelPricing is not None
        assert Model is not None
        assert ModelListResponse is not None
        assert ModelCapabilitiesResponse is not None
        assert PromptTokensDetails is not None
        assert CompletionTokensDetails is not None
        assert Usage is not None
        assert ErrorDetail is not None
        assert ErrorResponse is not None
        assert Role is not None
        assert AudioOutput is not None

    def test_import_content_models_from_package(self):
        """Test importing content models from fakeai.models package."""
        from fakeai.models import (
            AudioConfig,
            ContentPart,
            ImageContent,
            ImageUrl,
            InputAudio,
            InputAudioContent,
            RagDocument,
            TextContent,
            VideoContent,
            VideoUrl,
        )

        # Verify classes are imported correctly
        assert TextContent is not None
        assert ImageUrl is not None
        assert ImageContent is not None
        assert InputAudio is not None
        assert InputAudioContent is not None
        assert VideoUrl is not None
        assert VideoContent is not None
        assert AudioConfig is not None
        assert ContentPart is not None
        assert RagDocument is not None


class TestImportsFromBaseModule:
    """Test that models can be imported from the _base module."""

    def test_import_from_base_module(self):
        """Test importing from fakeai.models._base module."""
        from fakeai.models._base import (
            AudioOutput,
            CompletionTokensDetails,
            ErrorDetail,
            ErrorResponse,
            Model,
            ModelCapabilitiesResponse,
            ModelListResponse,
            ModelPermission,
            ModelPricing,
            PromptTokensDetails,
            Role,
            Usage,
        )

        # Verify classes are imported correctly
        assert ModelPermission is not None
        assert ModelPricing is not None
        assert Model is not None
        assert ModelListResponse is not None
        assert ModelCapabilitiesResponse is not None
        assert PromptTokensDetails is not None
        assert CompletionTokensDetails is not None
        assert Usage is not None
        assert ErrorDetail is not None
        assert ErrorResponse is not None
        assert Role is not None
        assert AudioOutput is not None


class TestImportsFromContentModule:
    """Test that models can be imported from the _content module."""

    def test_import_from_content_module(self):
        """Test importing from fakeai.models._content module."""
        from fakeai.models._content import (
            AudioConfig,
            ContentPart,
            ImageContent,
            ImageUrl,
            InputAudio,
            InputAudioContent,
            RagDocument,
            TextContent,
            VideoContent,
            VideoUrl,
        )

        # Verify classes are imported correctly
        assert TextContent is not None
        assert ImageUrl is not None
        assert ImageContent is not None
        assert InputAudio is not None
        assert InputAudioContent is not None
        assert VideoUrl is not None
        assert VideoContent is not None
        assert AudioConfig is not None
        assert ContentPart is not None
        assert RagDocument is not None


class TestBackwardCompatibility:
    """Test that imports from different paths reference the same classes."""

    def test_base_models_reference_same_class(self):
        """Test that base models imported from different paths are the same class."""
        from fakeai.models import Model as ModelFromPackage
        from fakeai.models._base import Model as ModelFromBase

        # Verify they reference the same class
        assert ModelFromPackage is ModelFromBase

    def test_content_models_reference_same_class(self):
        """Test that content models imported from different paths are the same class."""
        from fakeai.models import TextContent as TextContentFromPackage
        from fakeai.models._content import TextContent as TextContentFromBase

        # Verify they reference the same class
        assert TextContentFromPackage is TextContentFromBase

    def test_all_base_models_reference_same_class(self):
        """Test that all base models reference the same classes."""
        from fakeai.models import (
            AudioOutput,
            CompletionTokensDetails,
            ErrorDetail,
            ErrorResponse,
            Model,
            ModelCapabilitiesResponse,
            ModelListResponse,
            ModelPermission,
            ModelPricing,
            PromptTokensDetails,
            Role,
            Usage,
        )
        from fakeai.models._base import AudioOutput as AudioOutputBase
        from fakeai.models._base import (
            CompletionTokensDetails as CompletionTokensDetailsBase,
        )
        from fakeai.models._base import ErrorDetail as ErrorDetailBase
        from fakeai.models._base import ErrorResponse as ErrorResponseBase
        from fakeai.models._base import Model as ModelBase
        from fakeai.models._base import (
            ModelCapabilitiesResponse as ModelCapabilitiesResponseBase,
        )
        from fakeai.models._base import ModelListResponse as ModelListResponseBase
        from fakeai.models._base import ModelPermission as ModelPermissionBase
        from fakeai.models._base import ModelPricing as ModelPricingBase
        from fakeai.models._base import PromptTokensDetails as PromptTokensDetailsBase
        from fakeai.models._base import Role as RoleBase
        from fakeai.models._base import Usage as UsageBase

        # Verify all classes reference the same objects
        assert ModelPermission is ModelPermissionBase
        assert ModelPricing is ModelPricingBase
        assert Model is ModelBase
        assert ModelListResponse is ModelListResponseBase
        assert ModelCapabilitiesResponse is ModelCapabilitiesResponseBase
        assert PromptTokensDetails is PromptTokensDetailsBase
        assert CompletionTokensDetails is CompletionTokensDetailsBase
        assert Usage is UsageBase
        assert ErrorDetail is ErrorDetailBase
        assert ErrorResponse is ErrorResponseBase
        assert Role is RoleBase
        assert AudioOutput is AudioOutputBase

    def test_all_content_models_reference_same_class(self):
        """Test that all content models reference the same classes."""
        from fakeai.models import (
            AudioConfig,
            ContentPart,
            ImageContent,
            ImageUrl,
            InputAudio,
            InputAudioContent,
            RagDocument,
            TextContent,
            VideoContent,
            VideoUrl,
        )
        from fakeai.models._content import AudioConfig as AudioConfigBase
        from fakeai.models._content import ContentPart as ContentPartBase
        from fakeai.models._content import ImageContent as ImageContentBase
        from fakeai.models._content import ImageUrl as ImageUrlBase
        from fakeai.models._content import InputAudio as InputAudioBase
        from fakeai.models._content import InputAudioContent as InputAudioContentBase
        from fakeai.models._content import RagDocument as RagDocumentBase
        from fakeai.models._content import TextContent as TextContentBase
        from fakeai.models._content import VideoContent as VideoContentBase
        from fakeai.models._content import VideoUrl as VideoUrlBase

        # Verify all classes reference the same objects
        assert TextContent is TextContentBase
        assert ImageUrl is ImageUrlBase
        assert ImageContent is ImageContentBase
        assert InputAudio is InputAudioBase
        assert InputAudioContent is InputAudioContentBase
        assert VideoUrl is VideoUrlBase
        assert VideoContent is VideoContentBase
        assert AudioConfig is AudioConfigBase
        assert ContentPart is ContentPartBase
        assert RagDocument is RagDocumentBase


class TestModelInstantiation:
    """Test that models can be instantiated and validated correctly."""

    def test_model_permission_instantiation(self):
        """Test ModelPermission instantiation."""
        from fakeai.models import ModelPermission

        permission = ModelPermission(
            id="perm-123",
            created=1234567890,
            allow_create_engine=True,
            allow_sampling=True,
            allow_logprobs=True,
            allow_search_indices=False,
            allow_view=True,
            allow_fine_tuning=False,
            organization="test-org",
            is_blocking=False,
        )

        assert permission.id == "perm-123"
        assert permission.object == "model_permission"
        assert permission.allow_create_engine is True

    def test_model_instantiation(self):
        """Test Model instantiation."""
        from fakeai.models import Model, ModelPermission, ModelPricing

        pricing = ModelPricing(
            input_per_million=1.0,
            output_per_million=2.0,
        )

        permission = ModelPermission(
            id="perm-123",
            created=1234567890,
            allow_create_engine=True,
            allow_sampling=True,
            allow_logprobs=True,
            allow_search_indices=False,
            allow_view=True,
            allow_fine_tuning=False,
            organization="test-org",
            is_blocking=False,
        )

        model = Model(
            id="gpt-4",
            created=1234567890,
            owned_by="openai",
            permission=[permission],
            context_window=8192,
            max_output_tokens=4096,
            pricing=pricing,
        )

        assert model.id == "gpt-4"
        assert model.object == "model"
        assert model.context_window == 8192
        assert model.pricing.input_per_million == 1.0

    def test_usage_instantiation(self):
        """Test Usage instantiation."""
        from fakeai.models import CompletionTokensDetails, PromptTokensDetails, Usage

        prompt_details = PromptTokensDetails(cached_tokens=10, audio_tokens=5)
        completion_details = CompletionTokensDetails(
            reasoning_tokens=20,
            audio_tokens=3,
            accepted_prediction_tokens=15,
            rejected_prediction_tokens=2,
        )

        usage = Usage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            prompt_tokens_details=prompt_details,
            completion_tokens_details=completion_details,
        )

        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.prompt_tokens_details.cached_tokens == 10
        assert usage.completion_tokens_details.reasoning_tokens == 20

    def test_error_response_instantiation(self):
        """Test ErrorResponse instantiation."""
        from fakeai.models import ErrorDetail, ErrorResponse

        error_detail = ErrorDetail(
            message="Invalid API key",
            type="authentication_error",
            code="invalid_api_key",
        )

        error_response = ErrorResponse(error=error_detail)

        assert error_response.error.message == "Invalid API key"
        assert error_response.error.type == "authentication_error"
        assert error_response.error.code == "invalid_api_key"

    def test_text_content_instantiation(self):
        """Test TextContent instantiation."""
        from fakeai.models import TextContent

        content = TextContent(text="Hello, world!")

        assert content.type == "text"
        assert content.text == "Hello, world!"

    def test_image_content_instantiation(self):
        """Test ImageContent instantiation."""
        from fakeai.models import ImageContent, ImageUrl

        image_url = ImageUrl(url="https://example.com/image.png", detail="high")
        content = ImageContent(image_url=image_url)

        assert content.type == "image_url"
        assert content.image_url.url == "https://example.com/image.png"
        assert content.image_url.detail == "high"

    def test_audio_content_instantiation(self):
        """Test InputAudioContent instantiation."""
        from fakeai.models import InputAudio, InputAudioContent

        audio = InputAudio(data="base64data", format="mp3")
        content = InputAudioContent(input_audio=audio)

        assert content.type == "input_audio"
        assert content.input_audio.data == "base64data"
        assert content.input_audio.format == "mp3"

    def test_video_content_instantiation(self):
        """Test VideoContent instantiation."""
        from fakeai.models import VideoContent, VideoUrl

        video_url = VideoUrl(url="https://example.com/video.mp4", detail="low")
        content = VideoContent(video_url=video_url)

        assert content.type == "video_url"
        assert content.video_url.url == "https://example.com/video.mp4"
        assert content.video_url.detail == "low"

    def test_rag_document_instantiation(self):
        """Test RagDocument instantiation."""
        from fakeai.models import RagDocument

        doc = RagDocument(
            id="doc-123",
            content="Document content",
            score=0.95,
            metadata={"source": "manual"},
            source="User Guide p.100",
        )

        assert doc.id == "doc-123"
        assert doc.content == "Document content"
        assert doc.score == 0.95
        assert doc.metadata["source"] == "manual"
        assert doc.source == "User Guide p.100"

    def test_audio_config_instantiation(self):
        """Test AudioConfig instantiation."""
        from fakeai.models import AudioConfig

        config = AudioConfig(voice="alloy", format="mp3")

        assert config.voice == "alloy"
        assert config.format == "mp3"

    def test_audio_output_instantiation(self):
        """Test AudioOutput instantiation."""
        from fakeai.models import AudioOutput

        output = AudioOutput(
            id="audio-123",
            data="base64audiodata",
            transcript="Hello, this is audio",
            expires_at=1234567890,
        )

        assert output.id == "audio-123"
        assert output.data == "base64audiodata"
        assert output.transcript == "Hello, this is audio"
        assert output.expires_at == 1234567890

    def test_role_enum_values(self):
        """Test Role enum values."""
        from fakeai.models import Role

        assert Role.SYSTEM == "system"
        assert Role.USER == "user"
        assert Role.ASSISTANT == "assistant"
        assert Role.TOOL == "tool"
        assert Role.FUNCTION == "function"


class TestModelValidation:
    """Test that models validate correctly."""

    def test_model_pricing_validation(self):
        """Test ModelPricing validation."""
        from fakeai.models import ModelPricing

        # Valid pricing
        pricing = ModelPricing(input_per_million=1.0, output_per_million=2.0)
        assert pricing.input_per_million == 1.0

        # Invalid pricing should raise ValidationError
        with pytest.raises(ValidationError):
            ModelPricing(input_per_million="invalid", output_per_million=2.0)

    def test_rag_document_score_validation(self):
        """Test RagDocument score validation (should be 0.0-1.0)."""
        from fakeai.models import RagDocument

        # Valid score
        doc = RagDocument(id="doc-1", content="content", score=0.5)
        assert doc.score == 0.5

        # Score too high should raise ValidationError
        with pytest.raises(ValidationError):
            RagDocument(id="doc-1", content="content", score=1.5)

        # Score too low should raise ValidationError
        with pytest.raises(ValidationError):
            RagDocument(id="doc-1", content="content", score=-0.5)

    def test_content_part_union_type(self):
        """Test ContentPart union type."""
        from fakeai.models import ImageContent, ImageUrl, TextContent

        # TextContent should be valid
        text_content = TextContent(text="Hello")
        assert isinstance(text_content, (type(text_content),))

        # ImageContent should be valid
        image_content = ImageContent(
            image_url=ImageUrl(url="https://example.com/image.png")
        )
        assert isinstance(image_content, (type(image_content),))


class TestModuleStructure:
    """Test the module structure and organization."""

    def test_base_module_exports(self):
        """Test that _base module has correct exports."""
        import fakeai.models._base as base_module

        # Check that expected classes are available
        assert hasattr(base_module, "ModelPermission")
        assert hasattr(base_module, "ModelPricing")
        assert hasattr(base_module, "Model")
        assert hasattr(base_module, "ModelListResponse")
        assert hasattr(base_module, "ModelCapabilitiesResponse")
        assert hasattr(base_module, "PromptTokensDetails")
        assert hasattr(base_module, "CompletionTokensDetails")
        assert hasattr(base_module, "Usage")
        assert hasattr(base_module, "ErrorDetail")
        assert hasattr(base_module, "ErrorResponse")
        assert hasattr(base_module, "Role")
        assert hasattr(base_module, "AudioOutput")

    def test_content_module_exports(self):
        """Test that _content module has correct exports."""
        import fakeai.models._content as content_module

        # Check that expected classes are available
        assert hasattr(content_module, "TextContent")
        assert hasattr(content_module, "ImageUrl")
        assert hasattr(content_module, "ImageContent")
        assert hasattr(content_module, "InputAudio")
        assert hasattr(content_module, "InputAudioContent")
        assert hasattr(content_module, "VideoUrl")
        assert hasattr(content_module, "VideoContent")
        assert hasattr(content_module, "AudioConfig")
        assert hasattr(content_module, "ContentPart")
        assert hasattr(content_module, "RagDocument")

    def test_package_init_exports(self):
        """Test that package __init__ has correct exports."""
        import fakeai.models as models_package

        # Check __all__ exists
        assert hasattr(models_package, "__all__")

        # Check all expected exports are in __all__
        expected_exports = [
            # Base models
            "ModelPermission",
            "ModelPricing",
            "Model",
            "ModelListResponse",
            "ModelCapabilitiesResponse",
            "PromptTokensDetails",
            "CompletionTokensDetails",
            "Usage",
            "ErrorDetail",
            "ErrorResponse",
            "Role",
            "AudioOutput",
            # Content models
            "TextContent",
            "ImageUrl",
            "ImageContent",
            "InputAudio",
            "InputAudioContent",
            "VideoUrl",
            "VideoContent",
            "AudioConfig",
            "ContentPart",
            "RagDocument",
        ]

        for export in expected_exports:
            assert export in models_package.__all__, f"{export} not in __all__"
            assert hasattr(models_package, export), f"{export} not available in package"
