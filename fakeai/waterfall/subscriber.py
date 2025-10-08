"""
Event subscriber for automatic waterfall data collection.

Integrates with FakeAI's event bus to automatically capture request timing.
"""

#  SPDX-License-Identifier: Apache-2.0

from fakeai.events import BaseEvent
from fakeai.events.event_types import (
    RequestCompletedEvent,
    RequestStartedEvent,
    StreamingTokenGeneratedEvent,
)

from .collector import get_timing_collector


class WaterfallCollectorSubscriber:
    """
    Event subscriber that collects timing data for waterfall charts.

    Listens to:
    - RequestStartedEvent: Record request start
    - StreamingTokenGeneratedEvent: Record TTFT and token times
    - RequestCompletedEvent: Record request completion
    """

    def __init__(self):
        """Initialize the subscriber."""
        self.collector = get_timing_collector()

    async def on_request_started(self, event: BaseEvent) -> None:
        """Handle request started event."""
        if not isinstance(event, RequestStartedEvent):
            return

        self.collector.start_request(
            request_id=event.request_id,
            endpoint=event.endpoint,
            model=event.model,
            is_streaming=event.metadata.get("stream", False),
            input_tokens=event.metadata.get("input_tokens", 0),
            metadata={
                "user": event.user,
                "timestamp": event.timestamp,
            },
        )

    async def on_token_generated(self, event: BaseEvent) -> None:
        """Handle streaming token generated event."""
        if not isinstance(event, StreamingTokenGeneratedEvent):
            return

        # First token = TTFT
        if event.token_index == 0:
            self.collector.record_first_token(
                request_id=event.request_id, token_text=event.token_text
            )
        else:
            self.collector.record_token(
                request_id=event.request_id,
                token_index=event.token_index,
                token_text=event.token_text,
            )

    async def on_request_completed(self, event: BaseEvent) -> None:
        """Handle request completed event."""
        if not isinstance(event, RequestCompletedEvent):
            return

        self.collector.complete_request(
            request_id=event.request_id,
            output_tokens=event.output_tokens,
            success=True,
        )
