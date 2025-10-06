"""
Comprehensive tests for the 12 new model modules.

Tests all models extracted from models.py into their own modules:
- completions.py
- files.py
- moderation.py
- vector_stores.py
- organization.py
- billing.py
- realtime.py
- fine_tuning.py
- assistants.py
- responses.py
- rankings.py
- azure.py
"""
#  SPDX-License-Identifier: Apache-2.0

import pytest
from pydantic import ValidationError

# Completions module tests
from fakeai.models.completions import (
    CompletionRequest,
    CompletionResponse,
    CompletionChoice,
    CompletionChunk,
    LogProbs,
)


def test_completion_request():
    """Test CompletionRequest model."""
    request = CompletionRequest(
        model="openai/gpt-oss-20b",
        prompt="Hello, world!",
        max_tokens=100,
        temperature=0.7,
    )
    assert request.model == "openai/gpt-oss-20b"
    assert request.prompt == "Hello, world!"
    assert request.max_tokens == 100
    assert request.temperature == 0.7


def test_completion_response():
    """Test CompletionResponse model."""
    from fakeai.models import Usage

    response = CompletionResponse(
        id="cmpl-123",
        created=1234567890,
        model="openai/gpt-oss-20b",
        choices=[
            CompletionChoice(
                text="Hello! How can I help?",
                index=0,
                finish_reason="stop",
            )
        ],
        usage=Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
    )
    assert response.id == "cmpl-123"
    assert len(response.choices) == 1
    assert response.choices[0].text == "Hello! How can I help?"


# Files module tests
from fakeai.models.files import FileObject, FileListResponse


def test_file_object():
    """Test FileObject model."""
    file_obj = FileObject(
        id="file-123",
        bytes=1024,
        created_at=1234567890,
        filename="training_data.jsonl",
        purpose="fine-tune",
        status="uploaded",
    )
    assert file_obj.id == "file-123"
    assert file_obj.bytes == 1024
    assert file_obj.filename == "training_data.jsonl"
    assert file_obj.purpose == "fine-tune"


def test_file_list_response():
    """Test FileListResponse model."""
    response = FileListResponse(
        data=[
            FileObject(
                id="file-1",
                bytes=100,
                created_at=123,
                filename="file1.txt",
                purpose="fine-tune",
            )
        ]
    )
    assert len(response.data) == 1
    assert response.object == "list"


# Moderation module tests
from fakeai.models.moderation import (
    ModerationRequest,
    ModerationResponse,
    ModerationResult,
    ModerationCategories,
    ModerationCategoryScores,
)


def test_moderation_request():
    """Test ModerationRequest model."""
    request = ModerationRequest(
        input="This is a test message",
        model="omni-moderation-latest",
    )
    assert request.input == "This is a test message"
    assert request.model == "omni-moderation-latest"


def test_moderation_response():
    """Test ModerationResponse model."""
    response = ModerationResponse(
        id="modr-123",
        model="omni-moderation-latest",
        results=[
            ModerationResult(
                flagged=False,
                categories=ModerationCategories(),
                category_scores=ModerationCategoryScores(),
            )
        ],
    )
    assert response.id == "modr-123"
    assert not response.results[0].flagged


# Vector stores module tests
from fakeai.models.vector_stores import (
    VectorStore,
    CreateVectorStoreRequest,
    FileCounts,
    ExpiresAfter,
    ChunkingStrategyType,
    StaticChunkingStrategy,
    AutoChunkingStrategy,
)


def test_vector_store():
    """Test VectorStore model."""
    vs = VectorStore(
        id="vs-123",
        created_at=1234567890,
        name="My Vector Store",
        status="completed",
        file_counts=FileCounts(completed=10, total=10),
    )
    assert vs.id == "vs-123"
    assert vs.name == "My Vector Store"
    assert vs.status == "completed"
    assert vs.file_counts.completed == 10


def test_static_chunking_strategy():
    """Test StaticChunkingStrategy model."""
    strategy = StaticChunkingStrategy(
        max_chunk_size_tokens=1024,
        chunk_overlap_tokens=128,
    )
    assert strategy.type == "static"
    assert strategy.max_chunk_size_tokens == 1024
    assert strategy.chunk_overlap_tokens == 128


def test_auto_chunking_strategy():
    """Test AutoChunkingStrategy model."""
    strategy = AutoChunkingStrategy()
    assert strategy.type == "auto"


# Organization module tests
from fakeai.models.organization import (
    OrganizationUser,
    OrganizationRole,
    OrganizationProject,
    ProjectUser,
    ProjectRole,
    ServiceAccount,
    ServiceAccountRole,
    CreateOrganizationUserRequest,
)


def test_organization_user():
    """Test OrganizationUser model."""
    user = OrganizationUser(
        id="user-123",
        name="John Doe",
        email="john@example.com",
        role=OrganizationRole.OWNER,
        added_at=1234567890,
    )
    assert user.id == "user-123"
    assert user.name == "John Doe"
    assert user.role == OrganizationRole.OWNER


def test_organization_project():
    """Test OrganizationProject model."""
    project = OrganizationProject(
        id="proj-123",
        name="My Project",
        created_at=1234567890,
        status="active",
    )
    assert project.id == "proj-123"
    assert project.name == "My Project"
    assert project.status == "active"


def test_service_account():
    """Test ServiceAccount model."""
    sa = ServiceAccount(
        id="sa-123",
        name="API Service",
        role=ServiceAccountRole.MEMBER,
        created_at=1234567890,
    )
    assert sa.id == "sa-123"
    assert sa.role == ServiceAccountRole.MEMBER


# Billing module tests
from fakeai.models.billing import (
    UsageAggregationBucket,
    UsageResultItem,
    CompletionsUsageResponse,
    CostAmount,
    CostResult,
    CostsResponse,
)


def test_usage_result_item():
    """Test UsageResultItem model."""
    item = UsageResultItem(
        input_tokens=100,
        output_tokens=50,
        num_model_requests=5,
    )
    assert item.input_tokens == 100
    assert item.output_tokens == 50
    assert item.num_model_requests == 5


def test_cost_result():
    """Test CostResult model."""
    cost = CostResult(
        amount=CostAmount(value=1.50),
        line_item="completions",
        project_id="proj-123",
    )
    assert cost.amount.value == 1.50
    assert cost.amount.currency == "usd"
    assert cost.line_item == "completions"


# Realtime module tests
from fakeai.models.realtime import (
    RealtimeSession,
    RealtimeVoice,
    RealtimeAudioFormat,
    RealtimeModality,
    RealtimeItem,
    RealtimeItemType,
    RealtimeItemRole,
    RealtimeItemStatus,
    RealtimeContent,
    RealtimeContentType,
)


def test_realtime_session():
    """Test RealtimeSession model."""
    session = RealtimeSession(
        id="sess-123",
        model="openai/gpt-oss-20b",
        voice=RealtimeVoice.ALLOY,
        input_audio_format=RealtimeAudioFormat.PCM16,
        output_audio_format=RealtimeAudioFormat.PCM16,
    )
    assert session.id == "sess-123"
    assert session.voice == RealtimeVoice.ALLOY
    assert session.model == "openai/gpt-oss-20b"


def test_realtime_item():
    """Test RealtimeItem model."""
    item = RealtimeItem(
        id="item-123",
        type=RealtimeItemType.MESSAGE,
        status=RealtimeItemStatus.COMPLETED,
        role=RealtimeItemRole.USER,
        content=[
            RealtimeContent(
                type=RealtimeContentType.TEXT,
                text="Hello, world!",
            )
        ],
    )
    assert item.id == "item-123"
    assert item.type == RealtimeItemType.MESSAGE
    assert len(item.content) == 1
    assert item.content[0].text == "Hello, world!"


# Fine-tuning module tests
from fakeai.models.fine_tuning import (
    FineTuningJob,
    FineTuningJobRequest,
    Hyperparameters,
    FineTuningEvent,
    FineTuningCheckpoint,
)


def test_fine_tuning_job_request():
    """Test FineTuningJobRequest model."""
    request = FineTuningJobRequest(
        training_file="file-123",
        model="openai/gpt-oss-20b",
        hyperparameters=Hyperparameters(n_epochs=3),
        suffix="my-model",
    )
    assert request.training_file == "file-123"
    assert request.model == "openai/gpt-oss-20b"
    assert request.suffix == "my-model"


def test_fine_tuning_job():
    """Test FineTuningJob model."""
    job = FineTuningJob(
        id="ftjob-123",
        created_at=1234567890,
        model="openai/gpt-oss-20b",
        organization_id="org-123",
        status="running",
        hyperparameters=Hyperparameters(n_epochs="auto"),
        training_file="file-123",
    )
    assert job.id == "ftjob-123"
    assert job.status == "running"
    assert job.model == "openai/gpt-oss-20b"


# Assistants module tests
from fakeai.models.assistants import (
    Assistant,
    CreateAssistantRequest,
    Thread,
    ThreadMessage,
    Run,
    RunStatus,
    RunStep,
)


def test_create_assistant_request():
    """Test CreateAssistantRequest model."""
    request = CreateAssistantRequest(
        model="openai/gpt-oss-20b",
        name="Math Tutor",
        instructions="You are a helpful math tutor.",
        temperature=0.7,
    )
    assert request.model == "openai/gpt-oss-20b"
    assert request.name == "Math Tutor"


def test_assistant():
    """Test Assistant model."""
    assistant = Assistant(
        id="asst-123",
        created_at=1234567890,
        model="openai/gpt-oss-20b",
        name="Math Tutor",
    )
    assert assistant.id == "asst-123"
    assert assistant.model == "openai/gpt-oss-20b"
    assert assistant.object == "assistant"


def test_thread():
    """Test Thread model."""
    thread = Thread(
        id="thread-123",
        created_at=1234567890,
    )
    assert thread.id == "thread-123"
    assert thread.object == "thread"


def test_run():
    """Test Run model."""
    from fakeai.models import Usage

    run = Run(
        id="run-123",
        created_at=1234567890,
        thread_id="thread-123",
        assistant_id="asst-123",
        status=RunStatus.COMPLETED,
        model="openai/gpt-oss-20b",
        usage=Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
    )
    assert run.id == "run-123"
    assert run.status == RunStatus.COMPLETED


# Responses module tests
from fakeai.models.responses import (
    ResponsesRequest,
    ResponsesResponse,
    ResponseMessageOutput,
)


def test_responses_request():
    """Test ResponsesRequest model."""
    request = ResponsesRequest(
        model="openai/gpt-oss-20b",
        input="Hello, world!",
        temperature=0.7,
    )
    assert request.model == "openai/gpt-oss-20b"
    assert request.input == "Hello, world!"


def test_responses_response():
    """Test ResponsesResponse model."""
    from fakeai.models import Usage

    response = ResponsesResponse(
        id="resp-123",
        created_at=1234567890,
        model="openai/gpt-oss-20b",
        status="completed",
        output=[],
        usage=Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
    )
    assert response.id == "resp-123"
    assert response.status == "completed"


# Rankings module tests
from fakeai.models.rankings import (
    RankingRequest,
    RankingQuery,
    RankingPassage,
    RankingResponse,
    RankingObject,
    SolidoRagRequest,
    SolidoRagResponse,
)


def test_ranking_request():
    """Test RankingRequest model."""
    request = RankingRequest(
        model="reranker-v1",
        query=RankingQuery(text="What is machine learning?"),
        passages=[
            RankingPassage(text="Machine learning is a subset of AI."),
            RankingPassage(text="Python is a programming language."),
        ],
    )
    assert request.model == "reranker-v1"
    assert len(request.passages) == 2


def test_ranking_response():
    """Test RankingResponse model."""
    response = RankingResponse(
        rankings=[
            RankingObject(index=0, logit=0.95),
            RankingObject(index=1, logit=0.23),
        ]
    )
    assert len(response.rankings) == 2
    assert response.rankings[0].logit > response.rankings[1].logit


def test_solido_rag_request():
    """Test SolidoRagRequest model."""
    request = SolidoRagRequest(
        query="What is PVTMC?",
        filters={"family": "Solido", "tool": "SDE"},
        inference_model="meta-llama/Llama-3.1-70B-Instruct",
        top_k=5,
    )
    assert request.query == "What is PVTMC?"
    assert request.filters["family"] == "Solido"
    assert request.top_k == 5


# Azure module tests
from fakeai.models.azure import TextGenerationRequest, TextGenerationResponse


def test_text_generation_request():
    """Test TextGenerationRequest model."""
    request = TextGenerationRequest(
        input="Generate a story",
        model="openai/gpt-oss-20b",
        max_output_tokens=200,
        temperature=0.8,
    )
    assert request.input == "Generate a story"
    assert request.model == "openai/gpt-oss-20b"
    assert request.max_output_tokens == 200


def test_text_generation_response():
    """Test TextGenerationResponse model."""
    from fakeai.models import Usage

    response = TextGenerationResponse(
        id="gen-123",
        created=1234567890,
        output="Once upon a time...",
        usage=Usage(prompt_tokens=5, completion_tokens=50, total_tokens=55),
        model="openai/gpt-oss-20b",
    )
    assert response.id == "gen-123"
    assert response.output == "Once upon a time..."


# Integration tests
def test_all_modules_import():
    """Test that all 12 modules can be imported."""
    from fakeai.models import (
        completions,
        files,
        moderation,
        vector_stores,
        organization,
        billing,
        realtime,
        fine_tuning,
        assistants,
        responses,
        rankings,
        azure,
    )
    # Verify each module has expected models
    assert hasattr(completions, "CompletionRequest")
    assert hasattr(files, "FileObject")
    assert hasattr(moderation, "ModerationRequest")
    assert hasattr(vector_stores, "VectorStore")
    assert hasattr(organization, "OrganizationUser")
    assert hasattr(billing, "CostAmount")
    assert hasattr(realtime, "RealtimeSession")
    assert hasattr(fine_tuning, "FineTuningJob")
    assert hasattr(assistants, "Assistant")
    assert hasattr(responses, "ResponsesRequest")
    assert hasattr(rankings, "RankingRequest")
    assert hasattr(azure, "TextGenerationRequest")


def test_backward_compatibility():
    """Test that all models are still available from fakeai.models."""
    from fakeai.models import (
        CompletionRequest,
        FileObject,
        ModerationRequest,
        VectorStore,
        OrganizationUser,
        CostAmount,
        RealtimeSession,
        FineTuningJob,
        Assistant,
        ResponsesRequest,
        RankingRequest,
        TextGenerationRequest,
    )
    # All imports should work without error
    assert CompletionRequest is not None
    assert FileObject is not None
    assert ModerationRequest is not None
    assert VectorStore is not None
    assert OrganizationUser is not None
    assert CostAmount is not None
    assert RealtimeSession is not None
    assert FineTuningJob is not None
    assert Assistant is not None
    assert ResponsesRequest is not None
    assert RankingRequest is not None
    assert TextGenerationRequest is not None
