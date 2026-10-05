"""Request-driver contracts and the production application driver."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Mapping

from agent_core import AgentCore, Session

from agent_eval.services import EvidenceVisibility

if TYPE_CHECKING:
    from .context import CrystalLatticeContext


RequestObserver = Callable[[Mapping[str, object]], None]
MutationClassifier = Callable[[Mapping[str, object]], bool | int]
StopCondition = Callable[["CrystalRequestProgress"], bool]
RequestDriver = Callable[["CrystalRequest"], "CrystalRequestOutcome"]


@dataclass(frozen=True)
class CrystalRequest:
    """Complete input to one request driver."""

    context: "CrystalLatticeContext"
    core: AgentCore
    session: Session
    base_config: dict[str, object]
    overrides: dict[str, object] | None
    stream: bool
    request_id: str
    observers: tuple[RequestObserver, ...] = ()
    stop_when: StopCondition | None = None
    mutation_classifier: MutationClassifier | None = None
    max_events: int | None = None


@dataclass(frozen=True)
class CrystalRequestProgress:
    """Immutable request state supplied to stop conditions."""

    request: CrystalRequest
    event: Mapping[str, object]
    event_count: int
    final_messages: tuple[Mapping[str, object], ...]
    latest_session: Session
    error_messages: tuple[str, ...]
    tool_event_count: int
    mutation_count: int
    completed: bool
    cancelled: bool


@dataclass(frozen=True)
class CrystalRequestOutcome:
    """Normalized result returned by any request driver."""

    core: AgentCore
    session: Session
    base_config: dict[str, object]
    events: tuple[Mapping[str, object], ...]
    final_messages: tuple[Mapping[str, object], ...]
    request_id: str
    completed: bool
    cancelled: bool
    error_messages: tuple[str, ...]
    tool_event_count: int
    mutation_count: int
    stop_reason: str | None
    duration_seconds: float

    @property
    def final_response(self) -> str:
        for message in reversed(self.final_messages):
            if message.get("role") != "assistant":
                continue
            content = message.get("content")
            if isinstance(content, str):
                return content
        for message in reversed(self.session.messages):
            if message.role == "assistant" and isinstance(message.content, str):
                return message.content
        return ""

    def to_dict(self) -> dict[str, object]:
        return {
            "session": self.session.to_dict(),
            "base_config": self.base_config,
            "events": self.events,
            "final_messages": self.final_messages,
            "request_id": self.request_id,
            "completed": self.completed,
            "cancelled": self.cancelled,
            "error_messages": self.error_messages,
            "tool_event_count": self.tool_event_count,
            "mutation_count": self.mutation_count,
            "stop_reason": self.stop_reason,
            "duration_seconds": self.duration_seconds,
            "final_response": self.final_response,
        }


def application_request_driver() -> RequestDriver:
    """Return a driver over the production ``AgentApplication.send_request`` path."""

    def drive(request: CrystalRequest) -> CrystalRequestOutcome:
        started = time.monotonic()
        application = request.context.application
        events: list[Mapping[str, object]] = []
        final_messages: list[Mapping[str, object]] = []
        latest_session = request.session
        error_messages: list[str] = []
        tool_event_count = 0
        mutation_count = 0
        completed = False
        cancelled = False
        stop_reason: str | None = None

        iterator = application.send_request(
            request.core,
            request.session,
            request.base_config,
            overrides=request.overrides,
            stream=request.stream,
            request_id=request.request_id,
        )
        try:
            for raw_event in iterator:
                event = dict(raw_event)
                events.append(event)
                event_type = event.get("type")

                event_session = event.get("session")
                if isinstance(event_session, Session):
                    latest_session = event_session

                if event_type == "final":
                    messages = event.get("messages")
                    if isinstance(messages, list):
                        final_messages.extend(
                            message
                            for message in messages
                            if isinstance(message, Mapping)
                        )
                elif event_type == "error":
                    detail = event.get("detail")
                    error_messages.append(str(detail or "unknown request error"))
                elif event_type == "request_completed":
                    completed = True
                elif event_type == "request_cancelled":
                    cancelled = True

                if isinstance(event_type, str) and event_type.startswith("tool"):
                    tool_event_count += 1

                if request.mutation_classifier is not None:
                    classified = request.mutation_classifier(event)
                    mutation_count += (
                        int(classified)
                        if isinstance(classified, int)
                        else int(bool(classified))
                    )

                request.context.services.evidence.emit(
                    "crystal_lattice.request_event",
                    event,
                    source="crystal_lattice",
                    metadata={"request_id": request.request_id},
                    visibility=EvidenceVisibility.RAW,
                )

                for observer in request.observers:
                    observer(event)

                progress = CrystalRequestProgress(
                    request=request,
                    event=event,
                    event_count=len(events),
                    final_messages=tuple(final_messages),
                    latest_session=latest_session,
                    error_messages=tuple(error_messages),
                    tool_event_count=tool_event_count,
                    mutation_count=mutation_count,
                    completed=completed,
                    cancelled=cancelled,
                )
                if request.stop_when is not None and request.stop_when(progress):
                    stop_reason = "stop_condition"
                    application.cancel_request(request.request_id)
                    break
                if request.max_events is not None and len(events) >= request.max_events:
                    stop_reason = "max_events"
                    application.cancel_request(request.request_id)
                    break
        finally:
            close = getattr(iterator, "close", None)
            if callable(close):
                close()

        loaded = application.load_session(
            latest_session.session_id,
            overrides=request.overrides,
        )
        if loaded is None:
            core = request.core
            base_config = request.base_config
            session = latest_session
        else:
            core, loaded_base_config, session = loaded
            base_config = dict(loaded_base_config)

        return CrystalRequestOutcome(
            core=core,
            session=session,
            base_config=base_config,
            events=tuple(events),
            final_messages=tuple(final_messages),
            request_id=request.request_id,
            completed=completed,
            cancelled=cancelled,
            error_messages=tuple(error_messages),
            tool_event_count=tool_event_count,
            mutation_count=mutation_count,
            stop_reason=stop_reason,
            duration_seconds=time.monotonic() - started,
        )

    return drive
