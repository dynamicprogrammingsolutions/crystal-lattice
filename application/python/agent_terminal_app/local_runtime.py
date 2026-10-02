from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import threading
from typing import Any, Callable, Collection, Dict, Literal, Mapping, Sequence

from agent_app import (
    AgentApplication,
    CompactHistory,
    InMemoryApplicationNotificationStore,
    SessionRequestError,
)
from agent_app.sessions import FilesystemSnapshotSelectionStore

from .runtime_environment import collect_additional_dotenv_values
from .runtime_layout import RuntimeLayout, load_runtime_layout


RunStatus = Literal["succeeded", "failed", "cancelled", "interrupted"]
RunProgressKind = Literal[
    "request_started",
    "assistant_started",
    "assistant_progress",
    "tool_started",
    "tool_progress",
    "tool_completed",
    "request_failed",
    "request_cancelled",
    "request_completed",
]
ProgressCallback = Callable[["RunProgress"], None]
_PROGRESS_MESSAGE_LIMIT = 240


@dataclass(frozen=True)
class RunError:
    category: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "category": self.category,
            "message": self.message,
        }


@dataclass(frozen=True)
class RunProgress:
    kind: RunProgressKind
    session_id: str
    request_id: str
    message: str
    tool_name: str | None = None
    tool_call_id: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "message": self.message,
            "tool_name": self.tool_name,
            "tool_call_id": self.tool_call_id,
        }


@dataclass(frozen=True)
class AgentRunResult:
    status: RunStatus
    session_id: str
    request_id: str
    agent_id: str
    output_text: str
    final_messages: tuple[Mapping[str, Any], ...]
    error: RunError | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "output_text": self.output_text,
            "final_messages": list(self.final_messages),
            "error": self.error.to_dict() if self.error is not None else None,
        }


def _bounded_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    normalized = " ".join(value.split())
    if len(normalized) <= _PROGRESS_MESSAGE_LIMIT:
        return normalized
    return normalized[: _PROGRESS_MESSAGE_LIMIT - 3] + "..."


def _event_identity(event: Mapping[str, Any]) -> tuple[str, str]:
    session_id = event.get("session_id")
    request_id = event.get("request_id")
    return (
        session_id if isinstance(session_id, str) else "",
        request_id if isinstance(request_id, str) else "",
    )


def _tool_call_identity(call: Any) -> tuple[str | None, str | None]:
    if not isinstance(call, dict):
        return None, None
    call_id = call.get("id") or call.get("tool_call_id")
    function = call.get("function")
    name = function.get("name") if isinstance(function, dict) else call.get("name")
    return (
        name if isinstance(name, str) and name else None,
        call_id if isinstance(call_id, str) and call_id else None,
    )


def _tool_result_identity(message: Any) -> tuple[str | None, str | None, str]:
    if not isinstance(message, dict):
        return None, None, ""
    metadata = message.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    tool_name = metadata.get("tool_name")
    call_id = metadata.get("tool_call_id")
    display = metadata.get("display")
    preview = ""
    if isinstance(display, dict):
        preview = _bounded_text(
            display.get("single_line")
            or display.get("content_text")
            or display.get("text_fallback")
        )
    if not preview:
        preview = _bounded_text(message.get("content"))
    return (
        tool_name if isinstance(tool_name, str) and tool_name else None,
        call_id if isinstance(call_id, str) and call_id else None,
        preview,
    )


def normalize_run_progress(event: Mapping[str, Any]) -> tuple[RunProgress, ...]:
    """Convert one public request event into bounded convenience progress."""

    event_type = event.get("type")
    session_id, request_id = _event_identity(event)

    if event_type == "request_started":
        return (
            RunProgress(
                kind="request_started",
                session_id=session_id,
                request_id=request_id,
                message="Request started",
            ),
        )
    if event_type == "assistant_message" and event.get("phase") == "start":
        return (
            RunProgress(
                kind="assistant_started",
                session_id=session_id,
                request_id=request_id,
                message="Assistant response started",
            ),
        )
    if event_type == "tool_calls":
        progress: list[RunProgress] = []
        for call in event.get("tool_calls") or []:
            tool_name, call_id = _tool_call_identity(call)
            progress.append(
                RunProgress(
                    kind="tool_started",
                    session_id=session_id,
                    request_id=request_id,
                    message=(
                        f"Tool started: {tool_name}"
                        if tool_name is not None
                        else "Tool started"
                    ),
                    tool_name=tool_name,
                    tool_call_id=call_id,
                )
            )
        return tuple(progress)
    if event_type == "tool_results":
        progress = []
        for message in event.get("messages") or []:
            tool_name, call_id, preview = _tool_result_identity(message)
            label = (
                f"Tool completed: {tool_name}"
                if tool_name is not None
                else "Tool completed"
            )
            if preview:
                label = f"{label} — {preview}"
            progress.append(
                RunProgress(
                    kind="tool_completed",
                    session_id=session_id,
                    request_id=request_id,
                    message=_bounded_text(label),
                    tool_name=tool_name,
                    tool_call_id=call_id,
                )
            )
        return tuple(progress)
    if event_type == "error":
        return (
            RunProgress(
                kind="request_failed",
                session_id=session_id,
                request_id=request_id,
                message="Request failed",
            ),
        )
    if event_type == "request_cancelled":
        return (
            RunProgress(
                kind="request_cancelled",
                session_id=session_id,
                request_id=request_id,
                message="Request cancelled",
            ),
        )
    if event_type == "request_completed":
        return (
            RunProgress(
                kind="request_completed",
                session_id=session_id,
                request_id=request_id,
                message="Request completed",
            ),
        )
    return ()


def _resolve_config_path(
    config_path: str | Path | None,
    layout: RuntimeLayout,
) -> Path:
    if config_path is not None:
        resolved = Path(config_path).expanduser().resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Crystal Lattice config not found: {resolved}")
        return resolved

    for candidate in (
        layout.user_path("local_config"),
        layout.user_path("home_config"),
    ):
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(
        "Crystal Lattice config not found; create ./.crystal/config.json, "
        "~/.crystal/config.json, or pass config_path"
    )


class LocalAgentRuntime:
    """Context-managed local runtime for configured agent tasks."""

    def __init__(
        self,
        *,
        application: AgentApplication,
        notification_store: InMemoryApplicationNotificationStore,
        config_path: Path,
        session_root: Path,
    ) -> None:
        self._application = application
        self._notification_store = notification_store
        self.config_path = config_path
        self.session_root = session_root
        self._close_lock = threading.Lock()
        self._closed = False

    @property
    def application(self) -> AgentApplication:
        self._require_open()
        return self._application

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("LocalAgentRuntime is closed")

    def __enter__(self) -> "LocalAgentRuntime":
        self._require_open()
        return self

    def __exit__(self, _exc_type: Any, _exc: Any, _traceback: Any) -> None:
        self.close()

    def close(self) -> None:
        with self._close_lock:
            if self._closed:
                return
            self._closed = True
        try:
            self._application.close()
        finally:
            self._notification_store.close()

    def list_agents(self) -> tuple[str, ...]:
        self._require_open()
        return tuple(self._application.list_agents())

    def run(
        self,
        prompt: str,
        *,
        agent_id: str | None = None,
        session_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        multipart_content: Sequence[Mapping[str, Any]] | None = None,
        overrides: Mapping[str, Any] | None = None,
        stream: bool = True,
        timeout: float | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> AgentRunResult:
        self._require_open()
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt must be a non-empty string")
        if bool(agent_id) == bool(session_id):
            raise ValueError("exactly one of agent_id or session_id is required")
        if timeout is not None and (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(float(timeout))
            or float(timeout) <= 0
        ):
            raise ValueError("timeout must be a finite positive number")

        if agent_id is not None:
            _core, _base_config, session = self._application.create_session(agent_id)
            selected_agent_id = agent_id
        else:
            assert session_id is not None
            session = self._application.load_session_record(session_id)
            if session is None:
                raise KeyError(f"Session {session_id!r} not found")
            raw_agent_id = (
                session.metadata.get("agent_id")
                if isinstance(session.metadata, dict)
                else None
            )
            if not isinstance(raw_agent_id, str) or not raw_agent_id:
                raise ValueError(
                    f"Session {session_id!r} has no configured agent identity"
                )
            selected_agent_id = raw_agent_id

        active_request_id: str | None = None

        def observe(event: Dict[str, Any]) -> None:
            nonlocal active_request_id
            request_id = event.get("request_id")
            if isinstance(request_id, str) and request_id:
                active_request_id = request_id
            if on_progress is None:
                return
            for progress in normalize_run_progress(event):
                on_progress(progress)

        try:
            result = self._application.run_session_request_with_message(
                session.session_id,
                role="user",
                content=prompt,
                metadata=dict(metadata) if metadata is not None else None,
                multipart_content=(
                    [dict(part) for part in multipart_content]
                    if multipart_content is not None
                    else None
                ),
                overrides=dict(overrides) if overrides is not None else None,
                stream=stream,
                on_event=observe,
                timeout=timeout,
            )
        except KeyboardInterrupt:
            if active_request_id is not None:
                self._application.cancel_request(active_request_id)
            raise

        output_text = "\n".join(
            message.get("content", "")
            for message in result.final_messages
            if message.get("role") == "assistant"
            and isinstance(message.get("content"), str)
            and message.get("content")
        )
        error = self._convert_error(result.error)
        return AgentRunResult(
            status=result.status,
            session_id=result.session_id,
            request_id=result.request_id,
            agent_id=selected_agent_id,
            output_text=output_text,
            final_messages=tuple(result.final_messages),
            error=error,
        )

    @staticmethod
    def _convert_error(error: SessionRequestError | None) -> RunError | None:
        if error is None:
            return None
        return RunError(category=error.category, message=error.message)

    def cancel_request(self, request_id: str) -> None:
        self._require_open()
        self._application.cancel_request(request_id)

    def list_sessions(
        self,
        *,
        filter_values: Dict[str, object] | None = None,
        apply_filter_defaults: bool = True,
        limit: int | None = None,
        include: Sequence[str] | None = None,
        exclude: Sequence[str] | None = None,
    ) -> Any:
        """Return shared session summaries with optional filtering and projection."""

        self._require_open()
        return self._application.list_session_summaries_document(
            filter_values=filter_values,
            apply_filter_defaults=apply_filter_defaults,
            limit=limit,
            include=include,
            exclude=exclude,
        )

    def list_messages(
        self,
        session_id: str,
        *,
        start: int | None = None,
        end: int | None = None,
        include: Sequence[str] | None = None,
        exclude: Sequence[str] | None = None,
    ) -> Any:
        """Return one canonical message range with optional JSONPath projection."""

        self._require_open()
        return self._application.list_session_messages_document(
            session_id,
            start=start,
            end=end,
            include=include,
            exclude=exclude,
        )

    def history(
        self,
        session_id: str,
        *,
        start: int | None = None,
        end: int | None = None,
        roles: Collection[str] | None = None,
        max_messages: int = 100,
        max_content_chars: int = 500,
        max_total_content_chars: int = 20_000,
    ) -> CompactHistory:
        self._require_open()
        return self._application.get_compact_session_history(
            session_id,
            start=start,
            end=end,
            roles=roles,
            max_messages=max_messages,
            max_content_chars=max_content_chars,
            max_total_content_chars=max_total_content_chars,
        )

    def get_message(self, session_id: str, index: int) -> Dict[str, Any]:
        self._require_open()
        return self._application.get_session_message(session_id, index)


def open_runtime(
    *,
    config_path: str | Path | None = None,
    session_root: str | Path | None = None,
    runtime_layout: RuntimeLayout | None = None,
    env_overrides: Mapping[str, str] | None = None,
) -> LocalAgentRuntime:
    """Open a supported local Crystal Lattice runtime."""

    layout = runtime_layout or load_runtime_layout()
    resolved_config = _resolve_config_path(config_path, layout)
    resolved_sessions = (
        Path(session_root).expanduser().resolve()
        if session_root is not None
        else layout.user_path("default_sessions_dir").resolve()
    )
    resolved_sessions.mkdir(parents=True, exist_ok=True)

    notification_store = InMemoryApplicationNotificationStore()
    resolved_env_overrides = layout.application_env_overrides(
        config_path=resolved_config,
        session_root=resolved_sessions,
        env_overrides=env_overrides,
    )
    try:
        application = AgentApplication(
            resolved_config,
            resolved_sessions,
            application_notification_store=notification_store,
            snapshot_selection_store=FilesystemSnapshotSelectionStore(
                resolved_sessions / ".snapshots"
            ),
            config_env=collect_additional_dotenv_values(resolved_config),
            env_overrides=resolved_env_overrides,
        )
    except Exception:
        notification_store.close()
        raise
    return LocalAgentRuntime(
        application=application,
        notification_store=notification_store,
        config_path=resolved_config,
        session_root=resolved_sessions,
    )


__all__ = [
    "AgentRunResult",
    "LocalAgentRuntime",
    "RunError",
    "RunProgress",
    "RunProgressKind",
    "RunStatus",
    "normalize_run_progress",
    "open_runtime",
]
