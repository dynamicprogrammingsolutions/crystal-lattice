"""High- and low-level context for Crystal Lattice evaluation programs."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Iterable, Mapping, cast

from agent_app import AgentApplication
from agent_core import AgentCore, MessageRole, Session

from agent_eval.services import EvidenceJournal, EvidenceVisibility, RunServices

from .requests import (
    CrystalRequest,
    CrystalRequestOutcome,
    MutationClassifier,
    RequestDriver,
    RequestObserver,
    StopCondition,
)
from .snapshots import CrystalSnapshotter, application_session_snapshot


class CrystalLatticeContext:
    """Mutable run-local handle around immutable Crystal Lattice sessions."""

    def __init__(
        self,
        *,
        application: AgentApplication,
        workspace: Path | None,
        services: RunServices,
        default_request_driver: RequestDriver,
    ) -> None:
        self.application = application
        self.workspace = workspace
        self.services = services
        self.evidence: EvidenceJournal = services.evidence
        self._default_request_driver = default_request_driver
        self._core: AgentCore | None = None
        self._session: Session | None = None
        self._base_config: dict[str, object] = {}
        self._request_defaults: dict[str, object] = {}
        self._requests: list[CrystalRequestOutcome] = []
        self._named_snapshots: dict[str, object] = {}

    @property
    def core(self) -> AgentCore:
        if self._core is None:
            raise RuntimeError("Crystal Lattice context has not started an agent")
        return self._core

    @property
    def session(self) -> Session:
        if self._session is None:
            raise RuntimeError("Crystal Lattice context has not started an agent")
        return self._session

    @property
    def session_or_none(self) -> Session | None:
        return self._session

    @property
    def config(self) -> dict[str, object]:
        """Return mutable default overrides applied to subsequent operations."""

        return self._request_defaults

    @property
    def base_config(self) -> Mapping[str, object]:
        return self._base_config

    @property
    def requests(self) -> tuple[CrystalRequestOutcome, ...]:
        return tuple(self._requests)

    @property
    def named_snapshots(self) -> Mapping[str, object]:
        return self._named_snapshots

    def start(self, agent_id: str) -> None:
        """Create a session or switch the current session to ``agent_id``."""

        if self._session is None:
            core, base_config, session = self.application.create_session(agent_id)
        else:
            core, base_config, session = self.application.update_agent(
                agent_id,
                self._session,
            )
            session = self.application.save_session(session)
        self.replace_runtime(
            core=core,
            base_config=base_config,
            session=session,
        )
        self.services.record(
            "crystal_lattice.agent_started",
            {
                "agent_id": agent_id,
                "session_id": session.session_id,
            },
        )

    def replace_runtime(
        self,
        *,
        core: AgentCore,
        base_config: Mapping[str, object],
        session: Session,
        persist: bool = False,
    ) -> None:
        """Replace the current runtime after custom low-level operations."""

        if persist:
            session = self.application.save_session(session)
        self._core = core
        self._base_config = dict(base_config)
        self._session = session

    def restore_session(self, session: Session) -> None:
        """Persist and resolve a session restored from an environment snapshot."""

        stored = self.application.save_session(session)
        loaded = self.application.load_session(stored.session_id)
        if loaded is None:
            raise RuntimeError(f"failed to load restored session {stored.session_id}")
        core, base_config, loaded_session = loaded
        self.replace_runtime(
            core=core,
            base_config=base_config,
            session=loaded_session,
        )
        self.services.record(
            "crystal_lattice.session_restored",
            {
                "session_id": loaded_session.session_id,
                "message_count": len(loaded_session.messages),
            },
        )

    def add_message(
        self,
        role: MessageRole,
        content: object,
        *,
        metadata: dict[str, object] | None = None,
        multipart_content: list[dict[str, object]] | None = None,
        tool_result: dict[str, object] | None = None,
    ) -> Session:
        if self._request_defaults:
            self._reload_for_overrides(None)
        effective_config = self.effective_config()
        session = self.core.add_message(
            self.session,
            role,
            content,
            cast(dict[str, Any] | None, metadata),
            cast(dict[str, Any], effective_config),
            multipart_content=cast(list[dict[str, Any]] | None, multipart_content),
            tool_result=cast(dict[str, Any] | None, tool_result),
        )
        session = self.application.save_session(session)
        self._session = session
        self.services.record(
            "crystal_lattice.message_added",
            {
                "role": role,
                "content": content,
                "metadata": metadata,
            },
            visibility=EvidenceVisibility.RAW,
        )
        return session

    def effective_config(
        self,
        overrides: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        combined_overrides = {
            **self._request_defaults,
            **dict(overrides or {}),
        }
        return cast(
            dict[str, object],
            self.application.resolve_effective_config(
                cast(dict[str, Any], self._base_config),
                self.session,
                cast(dict[str, Any], combined_overrides),
            ),
        )

    def _reload_for_overrides(
        self,
        overrides: Mapping[str, object] | None,
    ) -> tuple[AgentCore, dict[str, object], Session]:
        combined_overrides = {
            **self._request_defaults,
            **dict(overrides or {}),
        }
        loaded = self.application.load_session(
            self.session.session_id,
            overrides=cast(dict[str, Any], combined_overrides),
        )
        if loaded is None:
            raise RuntimeError(f"failed to reload session {self.session.session_id}")
        core, base_config, session = loaded
        self._core = core
        self._base_config = dict(base_config)
        self._session = session
        return core, self._base_config, session

    def request(
        self,
        *,
        messages: Mapping[str, object] | Iterable[Mapping[str, object]] | None = None,
        overrides: Mapping[str, object] | None = None,
        driver: RequestDriver | None = None,
        observers: tuple[RequestObserver, ...] = (),
        stop_when: StopCondition | None = None,
        mutation_classifier: MutationClassifier | None = None,
        stream: bool = False,
        request_id: str | None = None,
        max_events: int | None = None,
    ) -> CrystalRequestOutcome:
        if messages is not None:
            message_values = (
                [messages] if isinstance(messages, Mapping) else list(messages)
            )
            for message in message_values:
                role = message.get("role")
                if role not in {"system", "user", "assistant", "tool"}:
                    raise ValueError(f"unsupported message role: {role!r}")
                self.add_message(
                    cast(MessageRole, role),
                    message.get("content", ""),
                    metadata=cast(
                        dict[str, object] | None,
                        message.get("metadata"),
                    ),
                    multipart_content=cast(
                        list[dict[str, object]] | None,
                        message.get("multipart_content")
                        or message.get("multipartContent"),
                    ),
                    tool_result=cast(
                        dict[str, object] | None,
                        message.get("tool_result") or message.get("toolResult"),
                    ),
                )

        rid = request_id or f"eval_{uuid.uuid4().hex}"
        core, base_config, session = self._reload_for_overrides(overrides)
        combined_overrides = {
            **self._request_defaults,
            **dict(overrides or {}),
        }
        request = CrystalRequest(
            context=self,
            core=core,
            session=session,
            base_config=base_config,
            overrides=combined_overrides or None,
            stream=stream,
            request_id=rid,
            observers=observers,
            stop_when=stop_when,
            mutation_classifier=mutation_classifier,
            max_events=max_events,
        )
        selected_driver = driver or self._default_request_driver
        self.services.record(
            "crystal_lattice.request_started",
            {
                "request_id": rid,
                "stream": stream,
                "overrides": dict(overrides or {}),
                "driver": _callable_name(selected_driver),
            },
            visibility=EvidenceVisibility.RAW,
        )
        outcome = selected_driver(request)
        self.replace_runtime(
            core=outcome.core,
            base_config=outcome.base_config,
            session=outcome.session,
        )
        self._requests.append(outcome)
        self.services.record(
            "crystal_lattice.request_summary",
            {
                "request_id": outcome.request_id,
                "completed": outcome.completed,
                "cancelled": outcome.cancelled,
                "event_count": len(outcome.events),
                "tool_event_count": outcome.tool_event_count,
                "mutation_count": outcome.mutation_count,
                "errors": outcome.error_messages,
                "stop_reason": outcome.stop_reason,
                "duration_seconds": outcome.duration_seconds,
                "final_response": outcome.final_response,
            },
        )
        return outcome

    def create_snapshot(
        self,
        name: str,
        *,
        using: CrystalSnapshotter | None = None,
    ) -> object:
        snapshotter = using or application_session_snapshot
        snapshot = snapshotter(self)
        self._named_snapshots[name] = snapshot
        self.services.artifacts.write_json(
            f"raw/environment/snapshots/{name}.json",
            snapshot,
        )
        self.services.record(
            "crystal_lattice.snapshot_created",
            {
                "name": name,
                "snapshotter": _callable_name(snapshotter),
            },
        )
        return snapshot

    def evaluate(
        self,
        name: str,
        value: object,
        *,
        using,
    ):
        self.services.record(
            f"crystal_lattice.evaluation.{name}.input",
            value,
            visibility=EvidenceVisibility.RAW,
        )
        result = using(value)
        self.services.record(
            f"crystal_lattice.evaluation.{name}.result",
            result,
        )
        return result

    def present(
        self,
        name: str,
        value: object,
        *,
        using,
    ) -> tuple[str, ...]:
        before = _artifact_files(self.services.artifact_dir)
        using(value, self.services.artifacts)
        after = _artifact_files(self.services.artifact_dir)
        created = tuple(sorted(after - before))
        self.services.record(
            f"crystal_lattice.presentation.{name}",
            {"created": created},
        )
        return created

    def final_response(self) -> str:
        if self._requests:
            response = self._requests[-1].final_response
            if response:
                return response
        if self._session is None:
            return ""
        for message in reversed(self._session.messages):
            if message.role == "assistant" and isinstance(message.content, str):
                return message.content
        return ""

    def observation(self) -> dict[str, object]:
        session = self._session
        return {
            "agent_id": (
                session.metadata.get("agent_id") if session is not None else None
            ),
            "session_id": session.session_id if session is not None else None,
            "message_count": len(session.messages) if session is not None else 0,
            "request_count": len(self._requests),
            "tool_event_count": sum(
                request.tool_event_count for request in self._requests
            ),
            "mutation_count": sum(request.mutation_count for request in self._requests),
            "error_count": sum(
                len(request.error_messages) for request in self._requests
            ),
            "named_snapshots": tuple(sorted(self._named_snapshots)),
            "final_response": self.final_response(),
        }


def _artifact_files(root: Path) -> set[str]:
    return {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}


def _callable_name(value: object) -> str:
    module = getattr(value, "__module__", type(value).__module__)
    qualname = getattr(value, "__qualname__", type(value).__qualname__)
    return f"{module}.{qualname}"
