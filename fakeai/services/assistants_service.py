"""
Assistants service for FakeAI.

This module provides the Assistants API service including:
- Assistant creation, listing, retrieval, modification, deletion
- Thread creation, modification, deletion
- Message creation and listing
- Run creation, status polling, cancellation, tool outputs
- Run steps retrieval
- Streaming support

Features:
- Full Assistants API implementation
- Tool support (code interpreter, file search, function calling)
- Streaming runs with Server-Sent Events
- Background async processing
- State management for assistants, threads, messages, runs, and steps
"""

#  SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import random
import time
import uuid
from typing import Any

from fakeai.config import AppConfig
from fakeai.metrics import MetricsTracker
from fakeai.models import (
    Assistant,
    AssistantList,
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
    Usage,
)

logger = logging.getLogger(__name__)


class AssistantsService:
    """
    Assistants service for managing the Assistants API.

    Provides high-level operations including:
    - Assistant CRUD operations
    - Thread management
    - Message creation and retrieval
    - Run creation and lifecycle management
    - Run steps tracking
    - Tool calling support
    - Streaming runs

    Features:
    - In-memory storage for all entities
    - Background async processing for runs
    - Full pagination support
    - Streaming with Server-Sent Events
    - Tool calling simulation (function, code interpreter, file search)
    """

    def __init__(
        self,
        config: AppConfig,
        metrics_tracker: MetricsTracker,
    ):
        """
        Initialize assistants service.

        Args:
            config: Application configuration
            metrics_tracker: Metrics tracker for monitoring
        """
        self.config = config
        self.metrics_tracker = metrics_tracker

        # In-memory storage
        self.assistants_storage: dict[str, Assistant] = {}
        self.threads_storage: dict[str, dict] = {}
        self.messages_storage: dict[str, list[ThreadMessage]] = {}
        self.runs_storage: dict[str, dict[str, Run]] = {}
        self.run_steps_storage: dict[str, dict[str, list[RunStep]]] = {}

        logger.info("AssistantsService initialized")

    # ==============================================================================
    # ID Generators (following FakeAI pattern)
    # ==============================================================================

    def _generate_assistant_id(self) -> str:
        """Generate a unique assistant ID."""
        return f"asst_{uuid.uuid4().hex}"

    def _generate_thread_id(self) -> str:
        """Generate a unique thread ID."""
        return f"thread_{uuid.uuid4().hex}"

    def _generate_message_id(self) -> str:
        """Generate a unique message ID."""
        return f"msg_{uuid.uuid4().hex}"

    def _generate_run_id(self) -> str:
        """Generate a unique run ID."""
        return f"run_{uuid.uuid4().hex}"

    def _generate_step_id(self) -> str:
        """Generate a unique step ID."""
        return f"step_{uuid.uuid4().hex}"

    # ==============================================================================
    # Assistant CRUD Operations
    # ==============================================================================

    async def create_assistant(
            self, request: CreateAssistantRequest) -> Assistant:
        """
        Create a new assistant.

        Args:
            request: Assistant creation request

        Returns:
            Assistant object with metadata
        """
        start_time = time.time()
        endpoint = "/v1/assistants"

        try:

            # Generate assistant
            assistant_id = self._generate_assistant_id()
            created_at = int(time.time())

            assistant = Assistant(
                id=assistant_id,
                created_at=created_at,
                name=request.name,
                description=request.description,
                model=request.model,
                instructions=request.instructions,
                tools=request.tools,
                tool_resources=request.tool_resources,
                metadata=request.metadata,
                temperature=request.temperature,
                top_p=request.top_p,
                response_format=request.response_format,
            )

            # Store assistant
            self.assistants_storage[assistant_id] = assistant

            logger.info(f"Created assistant {assistant_id}")
            return assistant

        except Exception as e:
            logger.error(f"Error creating assistant: {e}")
            raise

    async def list_assistants(
        self,
        limit: int = 20,
        order: str = "desc",
        after: str | None = None,
        before: str | None = None,
    ) -> AssistantList:
        """
        List assistants with pagination.

        Args:
            limit: Maximum number of assistants to return (1-100, default: 20)
            order: Sort order ('asc' or 'desc', default: 'desc')
            after: Cursor for pagination (assistant ID)
            before: Cursor for pagination (assistant ID)

        Returns:
            AssistantList with paginated assistants
        """
        start_time = time.time()
        endpoint = "/v1/assistants"

        try:

            # Get all assistants
            assistants = list(self.assistants_storage.values())

            # Sort by created_at
            assistants.sort(
                key=lambda a: a.created_at, reverse=(
                    order == "desc"))

            # Apply pagination
            if after:
                try:
                    after_idx = next(
                        i for i, a in enumerate(assistants) if a.id == after)
                    assistants = assistants[after_idx + 1:]
                except StopIteration:
                    pass

            if before:
                try:
                    before_idx = next(
                        i for i, a in enumerate(assistants) if a.id == before)
                    assistants = assistants[:before_idx]
                except StopIteration:
                    pass

            # Limit results
            has_more = len(assistants) > limit
            assistants = assistants[:limit]

            return AssistantList(
                data=assistants,
                first_id=assistants[0].id if assistants else None,
                last_id=assistants[-1].id if assistants else None,
                has_more=has_more,
            )

        except Exception as e:
            logger.error(f"Error listing assistants: {e}")
            raise

    async def retrieve_assistant(self, assistant_id: str) -> Assistant:
        """
        Retrieve a specific assistant.

        Args:
            assistant_id: Assistant identifier

        Returns:
            Assistant object

        Raises:
            ValueError: If assistant not found
        """
        start_time = time.time()
        endpoint = "/v1/assistants"

        try:

            if assistant_id not in self.assistants_storage:
                raise ValueError(f"Assistant {assistant_id} not found")

            assistant = self.assistants_storage[assistant_id]

            return assistant

        except Exception as e:
            logger.error(f"Error retrieving assistant {assistant_id}: {e}")
            raise

    async def modify_assistant(
        self, assistant_id: str, request: ModifyAssistantRequest
    ) -> Assistant:
        """
        Modify an existing assistant.

        Args:
            assistant_id: Assistant identifier
            request: Modification request with updated fields

        Returns:
            Updated Assistant object

        Raises:
            ValueError: If assistant not found
        """
        start_time = time.time()
        endpoint = "/v1/assistants"

        try:

            if assistant_id not in self.assistants_storage:
                raise ValueError(f"Assistant {assistant_id} not found")

            assistant = self.assistants_storage[assistant_id]

            # Update fields if provided
            if request.model is not None:
                assistant.model = request.model
            if request.name is not None:
                assistant.name = request.name
            if request.description is not None:
                assistant.description = request.description
            if request.instructions is not None:
                assistant.instructions = request.instructions
            if request.tools is not None:
                assistant.tools = request.tools
            if request.tool_resources is not None:
                assistant.tool_resources = request.tool_resources
            if request.metadata is not None:
                assistant.metadata = request.metadata
            if request.temperature is not None:
                assistant.temperature = request.temperature
            if request.top_p is not None:
                assistant.top_p = request.top_p
            if request.response_format is not None:
                assistant.response_format = request.response_format

            logger.info(f"Modified assistant {assistant_id}")
            return assistant

        except Exception as e:
            logger.error(f"Error modifying assistant {assistant_id}: {e}")
            raise

    async def delete_assistant(self, assistant_id: str) -> dict:
        """
        Delete an assistant.

        Args:
            assistant_id: Assistant identifier

        Returns:
            Deletion confirmation dictionary

        Raises:
            ValueError: If assistant not found
        """
        start_time = time.time()
        endpoint = "/v1/assistants"

        try:

            if assistant_id not in self.assistants_storage:
                raise ValueError(f"Assistant {assistant_id} not found")

            # Delete assistant
            del self.assistants_storage[assistant_id]

            logger.info(f"Deleted assistant {assistant_id}")
            return {
                "id": assistant_id,
                "object": "assistant.deleted",
                "deleted": True,
            }

        except Exception as e:
            logger.error(f"Error deleting assistant {assistant_id}: {e}")
            raise

    # ==============================================================================
    # Thread Operations
    # ==============================================================================

    async def create_thread(self, request: CreateThreadRequest) -> Thread:
        """
        Create a new thread.

        Args:
            request: Thread creation request

        Returns:
            Thread object
        """
        start_time = time.time()
        endpoint = "/v1/threads"

        try:

            # Generate thread
            thread_id = self._generate_thread_id()
            created_at = int(time.time())

            thread = Thread(
                id=thread_id,
                created_at=created_at,
                metadata=request.metadata,
                tool_resources=request.tool_resources,
            )

            # Store thread
            self.threads_storage[thread_id] = thread.model_dump()
            self.messages_storage[thread_id] = []

            # Create initial messages if provided
            if request.messages:
                for msg_data in request.messages:
                    message_id = self._generate_message_id()
                    content = msg_data.get("content", "")

                    # Convert string content to content array format
                    if isinstance(content, str):
                        content_array = [
                            {"type": "text", "text": {"value": content}}]
                    else:
                        content_array = content

                    message = ThreadMessage(
                        id=message_id,
                        created_at=int(time.time()),
                        thread_id=thread_id,
                        role=msg_data.get("role", "user"),
                        content=content_array,
                        metadata=msg_data.get("metadata", {}),
                    )
                    self.messages_storage[thread_id].append(message)

            logger.info(f"Created thread {thread_id}")
            return thread

        except Exception as e:
            logger.error(f"Error creating thread: {e}")
            raise

    async def retrieve_thread(self, thread_id: str) -> Thread:
        """
        Retrieve a specific thread.

        Args:
            thread_id: Thread identifier

        Returns:
            Thread object

        Raises:
            ValueError: If thread not found
        """
        start_time = time.time()
        endpoint = "/v1/threads"

        try:

            if thread_id not in self.threads_storage:
                raise ValueError(f"Thread {thread_id} not found")

            thread = Thread(**self.threads_storage[thread_id])

            return thread

        except Exception as e:
            logger.error(f"Error retrieving thread {thread_id}: {e}")
            raise

    async def modify_thread(
        self, thread_id: str, request: ModifyThreadRequest
    ) -> Thread:
        """
        Modify a thread.

        Args:
            thread_id: Thread identifier
            request: Modification request

        Returns:
            Updated Thread object

        Raises:
            ValueError: If thread not found
        """
        start_time = time.time()
        endpoint = "/v1/threads"

        try:

            if thread_id not in self.threads_storage:
                raise ValueError(f"Thread {thread_id} not found")

            thread_data = self.threads_storage[thread_id]

            # Update fields if provided
            if request.metadata is not None:
                thread_data["metadata"] = request.metadata
            if request.tool_resources is not None:
                thread_data["tool_resources"] = request.tool_resources

            thread = Thread(**thread_data)

            logger.info(f"Modified thread {thread_id}")
            return thread

        except Exception as e:
            logger.error(f"Error modifying thread {thread_id}: {e}")
            raise

    async def delete_thread(self, thread_id: str) -> dict:
        """
        Delete a thread and all associated messages, runs, and steps.

        Args:
            thread_id: Thread identifier

        Returns:
            Deletion confirmation dictionary

        Raises:
            ValueError: If thread not found
        """
        start_time = time.time()
        endpoint = "/v1/threads"

        try:

            if thread_id not in self.threads_storage:
                raise ValueError(f"Thread {thread_id} not found")

            # Delete thread and associated data
            del self.threads_storage[thread_id]
            if thread_id in self.messages_storage:
                del self.messages_storage[thread_id]
            if thread_id in self.runs_storage:
                del self.runs_storage[thread_id]
            if thread_id in self.run_steps_storage:
                del self.run_steps_storage[thread_id]

            logger.info(f"Deleted thread {thread_id}")
            return {
                "id": thread_id,
                "object": "thread.deleted",
                "deleted": True,
            }

        except Exception as e:
            logger.error(f"Error deleting thread {thread_id}: {e}")
            raise

    # ==============================================================================
    # Message Operations
    # ==============================================================================

    async def create_message(
        self, thread_id: str, request: CreateMessageRequest
    ) -> ThreadMessage:
        """
        Create a message in a thread.

        Args:
            thread_id: Thread identifier
            request: Message creation request

        Returns:
            ThreadMessage object

        Raises:
            ValueError: If thread not found
        """
        start_time = time.time()
        endpoint = "/v1/threads/messages"

        try:

            if thread_id not in self.threads_storage:
                raise ValueError(f"Thread {thread_id} not found")

            # Generate message
            message_id = self._generate_message_id()
            created_at = int(time.time())

            # Convert string content to content array format
            if isinstance(request.content, str):
                content_array = [
                    {"type": "text", "text": {"value": request.content}}]
            else:
                content_array = request.content

            message = ThreadMessage(
                id=message_id,
                created_at=created_at,
                thread_id=thread_id,
                role=request.role,
                content=content_array,
                attachments=request.attachments,
                metadata=request.metadata,
            )

            # Store message
            if thread_id not in self.messages_storage:
                self.messages_storage[thread_id] = []

            self.messages_storage[thread_id].append(message)

            logger.info(f"Created message {message_id} in thread {thread_id}")
            return message

        except Exception as e:
            logger.error(f"Error creating message: {e}")
            raise

    async def list_messages(
        self,
        thread_id: str,
        limit: int = 20,
        order: str = "desc",
        after: str | None = None,
        before: str | None = None,
    ) -> MessageList:
        """
        List messages in a thread with pagination.

        Args:
            thread_id: Thread identifier
            limit: Maximum number of messages to return (1-100, default: 20)
            order: Sort order ('asc' or 'desc', default: 'desc')
            after: Cursor for pagination (message ID)
            before: Cursor for pagination (message ID)

        Returns:
            MessageList with paginated messages

        Raises:
            ValueError: If thread not found
        """
        start_time = time.time()
        endpoint = "/v1/threads/messages"

        try:

            if thread_id not in self.threads_storage:
                raise ValueError(f"Thread {thread_id} not found")

            # Get messages
            messages = self.messages_storage.get(thread_id, [])

            # Sort by created_at
            messages = sorted(
                messages,
                key=lambda m: m.created_at,
                reverse=(
                    order == "desc"))

            # Apply pagination
            if after:
                try:
                    after_idx = next(
                        i for i, m in enumerate(messages) if m.id == after)
                    messages = messages[after_idx + 1:]
                except StopIteration:
                    pass

            if before:
                try:
                    before_idx = next(
                        i for i, m in enumerate(messages) if m.id == before)
                    messages = messages[:before_idx]
                except StopIteration:
                    pass

            # Limit results
            has_more = len(messages) > limit
            messages = messages[:limit]

            return MessageList(
                data=messages,
                first_id=messages[0].id if messages else None,
                last_id=messages[-1].id if messages else None,
                has_more=has_more,
            )

        except Exception as e:
            logger.error(f"Error listing messages: {e}")
            raise

    async def retrieve_message(
            self,
            thread_id: str,
            message_id: str) -> ThreadMessage:
        """
        Retrieve a specific message.

        Args:
            thread_id: Thread identifier
            message_id: Message identifier

        Returns:
            ThreadMessage object

        Raises:
            ValueError: If thread or message not found
        """
        start_time = time.time()
        endpoint = "/v1/threads/messages"

        try:

            if thread_id not in self.threads_storage:
                raise ValueError(f"Thread {thread_id} not found")

            messages = self.messages_storage.get(thread_id, [])
            message = next((m for m in messages if m.id == message_id), None)

            if not message:
                raise ValueError(f"Message {message_id} not found")

            return message

        except Exception as e:
            logger.error(f"Error retrieving message {message_id}: {e}")
            raise

    async def modify_message(
        self, thread_id: str, message_id: str, metadata: dict | None = None
    ) -> ThreadMessage:
        """
        Modify a message (only metadata can be modified).

        Args:
            thread_id: Thread identifier
            message_id: Message identifier
            metadata: New metadata dictionary

        Returns:
            Updated ThreadMessage object

        Raises:
            ValueError: If thread or message not found
        """
        start_time = time.time()
        endpoint = "/v1/threads/messages"

        try:

            if thread_id not in self.threads_storage:
                raise ValueError(f"Thread {thread_id} not found")

            messages = self.messages_storage.get(thread_id, [])
            message = next((m for m in messages if m.id == message_id), None)

            if not message:
                raise ValueError(f"Message {message_id} not found")

            # Only metadata can be modified
            if metadata is not None:
                message.metadata = metadata

            logger.info(f"Modified message {message_id}")
            return message

        except Exception as e:
            logger.error(f"Error modifying message {message_id}: {e}")
            raise

    # ==============================================================================
    # Run Operations
    # ==============================================================================

    async def create_run(
        self, thread_id: str, request: CreateRunRequest
    ) -> Run | Any:
        """
        Create a run in a thread.

        This initiates the assistant to process the thread's messages and generate
        a response. Supports both streaming and non-streaming modes.

        Args:
            thread_id: Thread identifier
            request: Run creation request

        Returns:
            Run object (or StreamingResponse if streaming)

        Raises:
            ValueError: If thread or assistant not found
        """
        if thread_id not in self.threads_storage:
            raise ValueError(f"Thread {thread_id} not found")

        if request.assistant_id not in self.assistants_storage:
            raise ValueError(f"Assistant {request.assistant_id} not found")

        assistant = self.assistants_storage[request.assistant_id]
        run_id = self._generate_run_id()
        created_at = int(time.time())

        # Determine model and instructions
        model = request.model or assistant.model
        instructions = request.instructions or assistant.instructions
        tools = request.tools if request.tools is not None else assistant.tools

        run = Run(
            id=run_id,
            created_at=created_at,
            thread_id=thread_id,
            assistant_id=request.assistant_id,
            status=RunStatus.QUEUED,
            model=model,
            instructions=instructions,
            tools=tools,
            metadata=request.metadata,
            temperature=request.temperature or assistant.temperature,
            top_p=request.top_p or assistant.top_p,
            max_prompt_tokens=request.max_prompt_tokens,
            max_completion_tokens=request.max_completion_tokens,
            truncation_strategy=request.truncation_strategy,
            tool_choice=request.tool_choice,
            parallel_tool_calls=request.parallel_tool_calls,
            response_format=request.response_format or assistant.response_format,
        )

        # Store run
        if thread_id not in self.runs_storage:
            self.runs_storage[thread_id] = {}

        self.runs_storage[thread_id][run_id] = run

        # Initialize run steps storage
        if thread_id not in self.run_steps_storage:
            self.run_steps_storage[thread_id] = {}
        if run_id not in self.run_steps_storage[thread_id]:
            self.run_steps_storage[thread_id][run_id] = []

        # Handle streaming
        if request.stream:
            return self._create_streaming_run(
                run, thread_id, run_id, request.assistant_id, tools)

        # Non-streaming: start background processing
        asyncio.create_task(
            self._process_run(
                run,
                thread_id,
                run_id,
                request.assistant_id,
                tools))

        logger.info(f"Created run {run_id} in thread {thread_id}")
        return run

    async def _create_streaming_run(
            self,
            run: Run,
            thread_id: str,
            run_id: str,
            assistant_id: str,
            tools: list) -> Any:
        """
        Create a streaming run response.

        Args:
            run: Run object
            thread_id: Thread identifier
            run_id: Run identifier
            assistant_id: Assistant identifier
            tools: List of tools

        Returns:
            StreamingResponse with Server-Sent Events
        """
        from fastapi.responses import StreamingResponse

        async def generate_run_stream():
            # Send initial event
            yield f"event: thread.run.created\ndata: {run.model_dump_json()}\n\n"

            # Update to in_progress
            await asyncio.sleep(0.1)
            run.status = RunStatus.IN_PROGRESS
            run.started_at = int(time.time())
            yield f"event: thread.run.in_progress\ndata: {run.model_dump_json()}\n\n"

            # Create a message step
            step_id = self._generate_step_id()
            step = RunStep(
                id=step_id,
                created_at=int(
                    time.time()),
                run_id=run_id,
                assistant_id=assistant_id,
                thread_id=thread_id,
                type="message_creation",
                status="in_progress",
                step_details={
                    "type": "message_creation",
                    "message_creation": {
                        "message_id": self._generate_message_id()},
                },
            )

            self.run_steps_storage[thread_id][run_id].append(step)

            yield f"event: thread.run.step.created\ndata: {step.model_dump_json()}\n\n"

            # Generate assistant message
            await asyncio.sleep(0.2)
            assistant_message = ThreadMessage(
                id=self._generate_message_id(),
                created_at=int(
                    time.time()),
                thread_id=thread_id,
                role="assistant",
                content=[
                    {
                        "type": "text",
                        "text": {
                            "value": "I'm an AI assistant. I can help you with various tasks."},
                    }],
                assistant_id=assistant_id,
                run_id=run_id,
            )
            self.messages_storage[thread_id].append(assistant_message)

            # Complete the step
            step.status = "completed"
            step.completed_at = int(time.time())
            yield f"event: thread.run.step.completed\ndata: {step.model_dump_json()}\n\n"

            # Complete the run
            await asyncio.sleep(0.1)
            run.status = RunStatus.COMPLETED
            run.completed_at = int(time.time())
            run.usage = Usage(
                prompt_tokens=50,
                completion_tokens=20,
                total_tokens=70,
            )
            yield f"event: thread.run.completed\ndata: {run.model_dump_json()}\n\n"
            yield f"data: [DONE]\n\n"

        return StreamingResponse(
            generate_run_stream(),
            media_type="text/event-stream",
        )

    async def _process_run(
            self,
            run: Run,
            thread_id: str,
            run_id: str,
            assistant_id: str,
            tools: list) -> None:
        """
        Background task to process a non-streaming run.

        Args:
            run: Run object
            thread_id: Thread identifier
            run_id: Run identifier
            assistant_id: Assistant identifier
            tools: List of tools
        """
        try:
            await asyncio.sleep(0.5)

            # Update status to in_progress
            run.status = RunStatus.IN_PROGRESS
            run.started_at = int(time.time())

            # Create a message step
            step_id = self._generate_step_id()
            step = RunStep(
                id=step_id,
                created_at=int(
                    time.time()),
                run_id=run_id,
                assistant_id=assistant_id,
                thread_id=thread_id,
                type="message_creation",
                status="in_progress",
                step_details={
                    "type": "message_creation",
                    "message_creation": {
                        "message_id": self._generate_message_id()},
                },
            )

            self.run_steps_storage[thread_id][run_id].append(step)

            # Check if any function tools are present
            has_function_tools = any(
                tool.get("type") == "function" for tool in tools)

            if has_function_tools and random.random() < 0.3:  # 30% chance to require action
                # Simulate requiring tool call
                tool_call_id = f"call_{uuid.uuid4().hex}"
                function_tool = next(
                    (t for t in tools if t.get("type") == "function"), None)

                run.status = RunStatus.REQUIRES_ACTION
                run.required_action = {
                    "type": "submit_tool_outputs",
                    "submit_tool_outputs": {
                        "tool_calls": [
                            {
                                "id": tool_call_id,
                                "type": "function",
                                "function": {
                                    "name": function_tool["function"]["name"],
                                    "arguments": '{"location": "San Francisco"}',
                                },
                            }]},
                }
            else:
                # Generate assistant message
                await asyncio.sleep(0.3)
                assistant_message = ThreadMessage(
                    id=self._generate_message_id(),
                    created_at=int(
                        time.time()),
                    thread_id=thread_id,
                    role="assistant",
                    content=[
                        {
                            "type": "text",
                            "text": {
                                "value": "I'm an AI assistant. I can help you with various tasks."},
                        }],
                    assistant_id=assistant_id,
                    run_id=run_id,
                )
                self.messages_storage[thread_id].append(assistant_message)

                # Complete the step
                step.status = "completed"
                step.completed_at = int(time.time())

                # Complete the run
                run.status = RunStatus.COMPLETED
                run.completed_at = int(time.time())
                run.usage = Usage(
                    prompt_tokens=50,
                    completion_tokens=20,
                    total_tokens=70,
                )
        except Exception as e:
            logger.error(f"Error processing run {run_id}: {e}")
            run.status = RunStatus.FAILED
            run.failed_at = int(time.time())

    async def list_runs(
        self,
        thread_id: str,
        limit: int = 20,
        order: str = "desc",
        after: str | None = None,
        before: str | None = None,
    ) -> RunList:
        """
        List runs in a thread with pagination.

        Args:
            thread_id: Thread identifier
            limit: Maximum number of runs to return (1-100, default: 20)
            order: Sort order ('asc' or 'desc', default: 'desc')
            after: Cursor for pagination (run ID)
            before: Cursor for pagination (run ID)

        Returns:
            RunList with paginated runs

        Raises:
            ValueError: If thread not found
        """
        start_time = time.time()
        endpoint = "/v1/threads/runs"

        try:

            if thread_id not in self.threads_storage:
                raise ValueError(f"Thread {thread_id} not found")

            # Get runs
            runs = list(self.runs_storage.get(thread_id, {}).values())

            # Sort by created_at
            runs = sorted(
                runs,
                key=lambda r: r.created_at,
                reverse=(
                    order == "desc"))

            # Apply pagination
            if after:
                try:
                    after_idx = next(
                        i for i, r in enumerate(runs) if r.id == after)
                    runs = runs[after_idx + 1:]
                except StopIteration:
                    pass

            if before:
                try:
                    before_idx = next(
                        i for i, r in enumerate(runs) if r.id == before)
                    runs = runs[:before_idx]
                except StopIteration:
                    pass

            # Limit results
            has_more = len(runs) > limit
            runs = runs[:limit]

            return RunList(
                data=runs,
                first_id=runs[0].id if runs else None,
                last_id=runs[-1].id if runs else None,
                has_more=has_more,
            )

        except Exception as e:
            logger.error(f"Error listing runs: {e}")
            raise

    async def retrieve_run(self, thread_id: str, run_id: str) -> Run:
        """
        Retrieve a specific run.

        Args:
            thread_id: Thread identifier
            run_id: Run identifier

        Returns:
            Run object

        Raises:
            ValueError: If thread or run not found
        """
        start_time = time.time()
        endpoint = "/v1/threads/runs"

        try:

            if thread_id not in self.threads_storage:
                raise ValueError(f"Thread {thread_id} not found")

            run = self.runs_storage.get(thread_id, {}).get(run_id)

            if not run:
                raise ValueError(f"Run {run_id} not found")

            return run

        except Exception as e:
            logger.error(f"Error retrieving run {run_id}: {e}")
            raise

    async def modify_run(
        self, thread_id: str, run_id: str, request: ModifyRunRequest
    ) -> Run:
        """
        Modify a run (only metadata can be modified).

        Args:
            thread_id: Thread identifier
            run_id: Run identifier
            request: Modification request

        Returns:
            Updated Run object

        Raises:
            ValueError: If thread or run not found
        """
        start_time = time.time()
        endpoint = "/v1/threads/runs"

        try:

            if thread_id not in self.threads_storage:
                raise ValueError(f"Thread {thread_id} not found")

            run = self.runs_storage.get(thread_id, {}).get(run_id)

            if not run:
                raise ValueError(f"Run {run_id} not found")

            # Only metadata can be modified
            if request.metadata is not None:
                run.metadata = request.metadata

            logger.info(f"Modified run {run_id}")
            return run

        except Exception as e:
            logger.error(f"Error modifying run {run_id}: {e}")
            raise

    async def cancel_run(self, thread_id: str, run_id: str) -> Run:
        """
        Cancel a run.

        Args:
            thread_id: Thread identifier
            run_id: Run identifier

        Returns:
            Run object with updated status

        Raises:
            ValueError: If thread or run not found
        """
        start_time = time.time()
        endpoint = "/v1/threads/runs"

        try:

            if thread_id not in self.threads_storage:
                raise ValueError(f"Thread {thread_id} not found")

            run = self.runs_storage.get(thread_id, {}).get(run_id)

            if not run:
                raise ValueError(f"Run {run_id} not found")

            # Update status to cancelling or cancelled
            if run.status in [RunStatus.QUEUED, RunStatus.IN_PROGRESS]:
                run.status = RunStatus.CANCELLING
                run.cancelled_at = int(time.time())

                # Simulate quick cancellation
                async def complete_cancellation():
                    await asyncio.sleep(0.1)
                    run.status = RunStatus.CANCELLED

                asyncio.create_task(complete_cancellation())

            logger.info(f"Cancelled run {run_id}")
            return run

        except Exception as e:
            logger.error(f"Error cancelling run {run_id}: {e}")
            raise

    async def submit_tool_outputs(
        self, thread_id: str, run_id: str, tool_outputs: list[dict]
    ) -> Run:
        """
        Submit tool outputs for a run that requires action.

        Args:
            thread_id: Thread identifier
            run_id: Run identifier
            tool_outputs: List of tool output dictionaries

        Returns:
            Run object with updated status

        Raises:
            ValueError: If thread or run not found, or run not in requires_action state
        """
        start_time = time.time()
        endpoint = "/v1/threads/runs"

        try:

            if thread_id not in self.threads_storage:
                raise ValueError(f"Thread {thread_id} not found")

            run = self.runs_storage.get(thread_id, {}).get(run_id)

            if not run:
                raise ValueError(f"Run {run_id} not found")

            if run.status != RunStatus.REQUIRES_ACTION:
                raise ValueError(
                    f"Run is in {run.status} status, not requires_action"
                )

            # Clear required action and continue processing
            run.required_action = None
            run.status = RunStatus.IN_PROGRESS

            # Simulate completing the run
            async def complete_run():
                await asyncio.sleep(0.3)

                # Generate assistant message with tool results
                output_text = (
                    tool_outputs[0].get(
                        "output",
                        "unknown") if tool_outputs else "unknown")
                assistant_message = ThreadMessage(
                    id=self._generate_message_id(),
                    created_at=int(
                        time.time()),
                    thread_id=thread_id,
                    role="assistant",
                    content=[
                        {
                            "type": "text",
                            "text": {
                                "value": f"Based on the tool output, the result is: {output_text}"},
                        }],
                    assistant_id=run.assistant_id,
                    run_id=run_id,
                )
                self.messages_storage[thread_id].append(assistant_message)

                # Complete the run
                run.status = RunStatus.COMPLETED
                run.completed_at = int(time.time())
                run.usage = Usage(
                    prompt_tokens=60,
                    completion_tokens=25,
                    total_tokens=85,
                )

            asyncio.create_task(complete_run())

            logger.info(f"Submitted tool outputs for run {run_id}")
            return run

        except Exception as e:
            logger.error(f"Error submitting tool outputs: {e}")
            raise

    # ==============================================================================
    # Run Steps Operations
    # ==============================================================================

    async def list_run_steps(
        self,
        thread_id: str,
        run_id: str,
        limit: int = 20,
        order: str = "desc",
        after: str | None = None,
        before: str | None = None,
    ) -> RunStepList:
        """
        List steps for a run with pagination.

        Args:
            thread_id: Thread identifier
            run_id: Run identifier
            limit: Maximum number of steps to return (1-100, default: 20)
            order: Sort order ('asc' or 'desc', default: 'desc')
            after: Cursor for pagination (step ID)
            before: Cursor for pagination (step ID)

        Returns:
            RunStepList with paginated steps

        Raises:
            ValueError: If thread or run not found
        """
        start_time = time.time()
        endpoint = "/v1/threads/runs/steps"

        try:

            if thread_id not in self.threads_storage:
                raise ValueError(f"Thread {thread_id} not found")

            if run_id not in self.runs_storage.get(thread_id, {}):
                raise ValueError(f"Run {run_id} not found")

            # Get steps
            steps = self.run_steps_storage.get(thread_id, {}).get(run_id, [])

            # Sort by created_at
            steps = sorted(
                steps,
                key=lambda s: s.created_at,
                reverse=(
                    order == "desc"))

            # Apply pagination
            if after:
                try:
                    after_idx = next(
                        i for i, s in enumerate(steps) if s.id == after)
                    steps = steps[after_idx + 1:]
                except StopIteration:
                    pass

            if before:
                try:
                    before_idx = next(
                        i for i, s in enumerate(steps) if s.id == before)
                    steps = steps[:before_idx]
                except StopIteration:
                    pass

            # Limit results
            has_more = len(steps) > limit
            steps = steps[:limit]

            return RunStepList(
                data=steps,
                first_id=steps[0].id if steps else None,
                last_id=steps[-1].id if steps else None,
                has_more=has_more,
            )

        except Exception as e:
            logger.error(f"Error listing run steps: {e}")
            raise

    async def retrieve_run_step(
        self, thread_id: str, run_id: str, step_id: str
    ) -> RunStep:
        """
        Retrieve a specific run step.

        Args:
            thread_id: Thread identifier
            run_id: Run identifier
            step_id: Step identifier

        Returns:
            RunStep object

        Raises:
            ValueError: If thread, run, or step not found
        """
        start_time = time.time()
        endpoint = "/v1/threads/runs/steps"

        try:

            if thread_id not in self.threads_storage:
                raise ValueError(f"Thread {thread_id} not found")

            if run_id not in self.runs_storage.get(thread_id, {}):
                raise ValueError(f"Run {run_id} not found")

            steps = self.run_steps_storage.get(thread_id, {}).get(run_id, [])
            step = next((s for s in steps if s.id == step_id), None)

            if not step:
                raise ValueError(f"Step {step_id} not found")

            return step

        except Exception as e:
            logger.error(f"Error retrieving run step {step_id}: {e}")
            raise
