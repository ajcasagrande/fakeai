"""
Models package for FakeAI.

This package contains Pydantic models organized into logical modules:
- _base: Foundational models (Model, Usage, Error, Role, etc.)
- _content: Multi-modal content models (Text, Image, Audio, Video, RAG)
- chat: Chat completion models (Request, Response, Streaming, Tools, Logprobs)
- embeddings: Embedding models (Request, Response, Usage)
- batches: Batch processing models (Batch, CreateBatchRequest, etc.)
- audio: Audio models (TTS, Whisper, Usage)
- images: Image generation models (DALL-E compatible)
- completions: Legacy completion models (Request, Response, Streaming)
- files: File management models (FileObject, FileListResponse)
- moderation: Content moderation models (Request, Response, Categories, Scores)
- vector_stores: Vector store models for RAG (VectorStore, ChunkingStrategy, etc.)
- organization: Organization and project management models
- billing: Usage and billing tracking models
- realtime: Realtime WebSocket API models
- fine_tuning: Fine-tuning job and checkpoint models
- assistants: Assistants API models (Assistant, Thread, Message, Run, etc.)
- responses: Responses API models (stateful conversation API)
- rankings: NVIDIA NIM rankings and Solido RAG models
- azure: Azure API compatibility models

All models are re-exported at the package level for backward compatibility.
"""
#  SPDX-License-Identifier: Apache-2.0

# Rebuild all BaseModel subclasses to resolve forward references
from pydantic import BaseModel as _BaseModel

# Import from base module
from ._base import (
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

# Import from content module
from ._content import (
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

# Import from assistants module
from .assistants import (
    Assistant,
    AssistantList,
    AssistantToolResources,
    CreateAssistantRequest,
    CreateMessageRequest,
    CreateRunRequest,
    CreateThreadRequest,
    MessageList,
    ModifyAssistantRequest,
    ModifyRunRequest,
    ModifyThreadRequest,
    Run,
    RunList,
    RunStatus,
    RunStep,
    RunStepList,
    Thread,
    ThreadMessage,
)

# Import from audio module
from .audio import (
    AudioTranslationRequest,
    SpeechRequest,
    TranscriptionRequest,
    TranscriptionResponse,
    TranscriptionSegment,
    TranscriptionWord,
    VerboseTranscriptionResponse,
)

# Import from azure module
from .azure import (
    TextGenerationRequest,
    TextGenerationResponse,
)

# Import from batches module
from .batches import (
    Batch,
    BatchListResponse,
    BatchOutputResponse,
    BatchRequest,
    BatchRequestCounts,
    CreateBatchRequest,
)

# Import from billing module
from .billing import (
    AudioSpeechesUsageResponse,
    AudioTranscriptionsUsageResponse,
    CompletionsUsageResponse,
    CostAmount,
    CostBucket,
    CostResult,
    CostsResponse,
    EmbeddingsUsageResponse,
    ImagesUsageResponse,
    UsageAggregationBucket,
    UsageResultItem,
    UsageTimeBucket,
)

# Import from chat module
from .chat import (
    ChatCompletionChoice,
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatLogprob,
    ChatLogprobs,
    Delta,
    FunctionCall,
    FunctionDelta,
    JsonSchema,
    JsonSchemaResponseFormat,
    Message,
    PredictionContent,
    ResponseFormat,
    StreamOptions,
    Tool,
    ToolCall,
    ToolCallDelta,
    ToolCallFunction,
    ToolChoice,
    TopLogprob,
)

# Import from completions module
from .completions import (
    CompletionChoice,
    CompletionChunk,
    CompletionRequest,
    CompletionResponse,
    LogProbs,
)

# Import from embeddings module
from .embeddings import (
    Embedding,
    EmbeddingRequest,
    EmbeddingResponse,
)

# Import from files module
from .files import (
    FileListResponse,
    FileObject,
)

# Import from fine_tuning module
from .fine_tuning import (
    FineTuningCheckpoint,
    FineTuningCheckpointList,
    FineTuningEvent,
    FineTuningEventList,
    FineTuningJob,
    FineTuningJobError,
    FineTuningJobList,
    FineTuningJobRequest,
    Hyperparameters,
)

# Import from images module
from .images import (
    GeneratedImage,
    GeneratedVideo,
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageQuality,
    ImageResponseFormat,
    ImageSize,
    ImageStyle,
    VideoFormat,
    VideoGenerationRequest,
    VideoGenerationResponse,
    VideoSize,
)

# Import from moderation module
from .moderation import (
    ModerationCategories,
    ModerationCategoryScores,
    ModerationRequest,
    ModerationResponse,
    ModerationResult,
)

# Import from organization module
from .organization import (
    ArchiveOrganizationProjectResponse,
    CreateOrganizationInviteRequest,
    CreateOrganizationProjectRequest,
    CreateOrganizationUserRequest,
    CreateProjectUserRequest,
    CreateServiceAccountRequest,
    DeleteOrganizationInviteResponse,
    DeleteProjectUserResponse,
    DeleteServiceAccountResponse,
    ModifyOrganizationProjectRequest,
    ModifyOrganizationUserRequest,
    ModifyProjectUserRequest,
    OrganizationInvite,
    OrganizationInviteListResponse,
    OrganizationProject,
    OrganizationProjectListResponse,
    OrganizationRole,
    OrganizationUser,
    OrganizationUserListResponse,
    ProjectRole,
    ProjectUser,
    ProjectUserListResponse,
    ServiceAccount,
    ServiceAccountListResponse,
    ServiceAccountRole,
)

# Import from rankings module
from .rankings import (
    RankingObject,
    RankingPassage,
    RankingQuery,
    RankingRequest,
    RankingResponse,
    SolidoRagRequest,
    SolidoRagResponse,
)

# Import from realtime module
from .realtime import (
    RealtimeAudioFormat,
    RealtimeContent,
    RealtimeContentType,
    RealtimeError,
    RealtimeEvent,
    RealtimeEventType,
    RealtimeInputAudioTranscription,
    RealtimeItem,
    RealtimeItemRole,
    RealtimeItemStatus,
    RealtimeItemType,
    RealtimeModality,
    RealtimeRateLimits,
    RealtimeResponse,
    RealtimeSession,
    RealtimeSessionConfig,
    RealtimeTool,
    RealtimeToolChoice,
    RealtimeToolType,
    RealtimeTurnDetection,
    RealtimeTurnDetectionType,
    RealtimeVoice,
)

# Import from responses module
from .responses import (
    ResponseFunctionCallOutput,
    ResponseMessageOutput,
    ResponseOutputItem,
    ResponsesInput,
    ResponsesRequest,
    ResponsesResponse,
)

# Import from vector_stores module
from .vector_stores import (
    AutoChunkingStrategy,
    ChunkingStrategy,
    ChunkingStrategyType,
    CreateVectorStoreFileBatchRequest,
    CreateVectorStoreFileRequest,
    CreateVectorStoreRequest,
    ExpiresAfter,
    FileCounts,
    ModifyVectorStoreRequest,
    RankingOptions,
    StaticChunkingStrategy,
    VectorStore,
    VectorStoreFile,
    VectorStoreFileBatch,
    VectorStoreFileListResponse,
    VectorStoreListResponse,
)

for _name, _obj in list(globals().items()):
    if (
        not _name.startswith("_") and
        isinstance(_obj, type) and
        issubclass(_obj, _BaseModel) and
        hasattr(_obj, "model_rebuild")
    ):
        try:
            _obj.model_rebuild()
        except Exception:
            # Ignore errors during rebuild - some models may not need it
            pass

# Re-export all models for backward compatibility
__all__ = [
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
    # Chat models
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatCompletionChoice",
    "Message",
    "ChatCompletionChunk",
    "ChatCompletionChunkChoice",
    "Delta",
    "Tool",
    "ToolCall",
    "ToolChoice",
    "ToolCallFunction",
    "FunctionCall",
    "FunctionDelta",
    "ToolCallDelta",
    "ResponseFormat",
    "JsonSchema",
    "JsonSchemaResponseFormat",
    "StreamOptions",
    "PredictionContent",
    "ChatLogprob",
    "TopLogprob",
    "ChatLogprobs",
    # Embedding models
    "EmbeddingRequest",
    "Embedding",
    "EmbeddingResponse",
    "EmbeddingsUsageResponse",
    # Batch models
    "BatchRequestCounts",
    "Batch",
    "CreateBatchRequest",
    "BatchListResponse",
    "BatchRequest",
    "BatchOutputResponse",
    # Audio models
    "SpeechRequest",
    "TranscriptionRequest",
    "TranscriptionResponse",
    "VerboseTranscriptionResponse",
    "TranscriptionWord",
    "TranscriptionSegment",
    "AudioTranslationRequest",
    "AudioSpeechesUsageResponse",
    "AudioTranscriptionsUsageResponse",
    # Image models
    "ImageSize",
    "ImageQuality",
    "ImageStyle",
    "ImageResponseFormat",
    "GeneratedImage",
    "ImageGenerationRequest",
    "ImageGenerationResponse",
    "VideoGenerationRequest",
    "VideoGenerationResponse",
    "VideoSize",
    "VideoFormat",
    "GeneratedVideo",
    "ImagesUsageResponse",
    # Completion models (legacy)
    "CompletionRequest",
    "CompletionResponse",
    "CompletionChoice",
    "CompletionChunk",
    "LogProbs",
    # File models
    "FileObject",
    "FileListResponse",
    # Moderation models
    "ModerationRequest",
    "ModerationResponse",
    "ModerationResult",
    "ModerationCategories",
    "ModerationCategoryScores",
    # Vector store models
    "ChunkingStrategyType",
    "StaticChunkingStrategy",
    "AutoChunkingStrategy",
    "ChunkingStrategy",
    "FileCounts",
    "ExpiresAfter",
    "RankingOptions",
    "VectorStore",
    "CreateVectorStoreRequest",
    "ModifyVectorStoreRequest",
    "VectorStoreListResponse",
    "VectorStoreFile",
    "CreateVectorStoreFileRequest",
    "VectorStoreFileListResponse",
    "VectorStoreFileBatch",
    "CreateVectorStoreFileBatchRequest",
    # Organization models
    "OrganizationRole",
    "ProjectRole",
    "ServiceAccountRole",
    "OrganizationUser",
    "OrganizationUserListResponse",
    "CreateOrganizationUserRequest",
    "ModifyOrganizationUserRequest",
    "OrganizationInvite",
    "OrganizationInviteListResponse",
    "CreateOrganizationInviteRequest",
    "DeleteOrganizationInviteResponse",
    "OrganizationProject",
    "OrganizationProjectListResponse",
    "CreateOrganizationProjectRequest",
    "ModifyOrganizationProjectRequest",
    "ArchiveOrganizationProjectResponse",
    "ProjectUser",
    "ProjectUserListResponse",
    "CreateProjectUserRequest",
    "ModifyProjectUserRequest",
    "DeleteProjectUserResponse",
    "ServiceAccount",
    "ServiceAccountListResponse",
    "CreateServiceAccountRequest",
    "DeleteServiceAccountResponse",
    # Billing models
    "UsageTimeBucket",
    "UsageResultItem",
    "UsageAggregationBucket",
    "CompletionsUsageResponse",
    "EmbeddingsUsageResponse",
    "ImagesUsageResponse",
    "AudioSpeechesUsageResponse",
    "AudioTranscriptionsUsageResponse",
    "CostAmount",
    "CostResult",
    "CostBucket",
    "CostsResponse",
    # Realtime models
    "RealtimeVoice",
    "RealtimeAudioFormat",
    "RealtimeModality",
    "RealtimeTurnDetectionType",
    "RealtimeToolType",
    "RealtimeToolChoice",
    "RealtimeEventType",
    "RealtimeItemType",
    "RealtimeItemRole",
    "RealtimeContentType",
    "RealtimeItemStatus",
    "RealtimeInputAudioTranscription",
    "RealtimeTurnDetection",
    "RealtimeTool",
    "RealtimeSessionConfig",
    "RealtimeSession",
    "RealtimeContent",
    "RealtimeItem",
    "RealtimeResponse",
    "RealtimeRateLimits",
    "RealtimeError",
    "RealtimeEvent",
    # Fine-tuning models
    "Hyperparameters",
    "FineTuningJobRequest",
    "FineTuningJobError",
    "FineTuningJob",
    "FineTuningJobList",
    "FineTuningEvent",
    "FineTuningEventList",
    "FineTuningCheckpoint",
    "FineTuningCheckpointList",
    # Assistants models
    "AssistantToolResources",
    "Assistant",
    "CreateAssistantRequest",
    "ModifyAssistantRequest",
    "AssistantList",
    "Thread",
    "CreateThreadRequest",
    "ModifyThreadRequest",
    "ThreadMessage",
    "CreateMessageRequest",
    "MessageList",
    "RunStatus",
    "Run",
    "CreateRunRequest",
    "ModifyRunRequest",
    "RunList",
    "RunStep",
    "RunStepList",
    # Responses API models
    "ResponsesInput",
    "ResponsesRequest",
    "ResponseOutputItem",
    "ResponseMessageOutput",
    "ResponseFunctionCallOutput",
    "ResponsesResponse",
    # Rankings models
    "RankingQuery",
    "RankingPassage",
    "RankingRequest",
    "RankingObject",
    "RankingResponse",
    "SolidoRagRequest",
    "SolidoRagResponse",
    # Azure models
    "TextGenerationRequest",
    "TextGenerationResponse",
]
