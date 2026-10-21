from __future__ import annotations

from dataclasses import dataclass, replace
import math
import re
import threading
from typing import Any, Callable, Dict, Literal, Optional

from agent_core import Session

from .application_owner import ApplicationControl
from .operations import (
    ApplicationOperationBusyError,
    ApplicationOperationLease,
    ApplicationOperationService,
    session_operation_exclusivity_key,
)
from .sessions import SessionFileState


SessionRequestStartStatus = Literal["started", "already_running"]
SessionRequestResultStatus = Literal[
    "succeeded",
    "failed",
    "cancelled",
    "interrupted",
]

_ERROR_DETAIL_LIMIT = 500
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|authorization|password|secret|token)\b"
    r"(\s*[:=]\s*)([^\s,;]+)"
)
_BEARER_RE = re.compile(r"(?i)\bbearer\s+[^\s,;]+")


def _safe_error_message(detail: Any) -> str:
    text = " ".join(str(detail or "").split())
    if not text:
        return "Agent request failed"
    text = _SECRET_ASSIGNMENT_RE.sub(r"\1\2[redacted]", text)
    text = _BEARER_RE.sub("Bearer [redacted]", text)
    if len(text) > _ERROR_DETAIL_LIMIT:
        return text[: _ERROR_DETAIL_LIMIT - 3] + "..."
    return text


@dataclass(frozen=True)
class SessionRequestError:
    category: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "category": self.category,
            "message": self.message,
        }


@dataclass(frozen=True)
class SessionRequestStart:
    status: SessionRequestStartStatus
    session_id: str
    request_id: str


@dataclass(frozen=True)
class SessionRequestResult:
    session_id: str
    request_id: str
    final_session: Dict[str, Any] | None
    final_messages: list[Dict[str, Any]]
    status: SessionRequestResultStatus = "interrupted"
    error: SessionRequestError | None = None


@dataclass(frozen=True)
class _PreparedSessionRequest:
    core: Any
    base_config: Dict[str, Any]
    session: Session
    overrides: Dict[str, Any]
    request_id: str
    baseline_file_state: SessionFileState | None
    operation: ApplicationOperationLease
    persist_session: bool


class SessionRequestAlreadyRunningError(RuntimeError):
    def __init__(self, session_id: str, request_id: str) -> None:
        super().__init__(
            f"Session {session_id!r} already has active request {request_id!r}"
        )
        self.session_id = session_id
        self.request_id = request_id


class SessionRequestCoordinatorClosedError(RuntimeError):
    pass


class SessionOperationBusyError(RuntimeError):
    def __init__(self, session_id: str, operation: Dict[str, Any]) -> None:
        super().__init__(
            f"Session {session_id!r} is busy with operation "
            f"{operation.get('operation_id')!r} owned by "
            f"{operation.get('owner_id')!r}"
        )
        self.session_id = session_id
        self.operation = operation


class StaleApplicationGenerationError(RuntimeError):
    pass


class SessionRequestCoordinator:
    """Application-owned orchestration for starting and running requests."""

    def __init__(
        self,
        *,
        app: Any,
        application_control: ApplicationControl | None,
        operations: ApplicationOperationService,
        new_request_id: Callable[[], str],
        logger: Any,
    ) -> None:
        self._app = app
        self._application_control = application_control
        self._operations = operations
        self._new_request_id = new_request_id
        self._logger = logger
        self._lock = threading.RLock()
        self._active_by_session: dict[str, str] = {}
        self._threads_by_request: dict[str, threading.Thread] = {}
        self._closed = False

    def get_active_request_id(self, session_id: str) -> str | None:
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")
        with self._lock:
            return self._active_by_session.get(session_id)

    def start(
        self,
        session_id: str,
        overrides: Optional[Dict[str, Any]] = None,
        *,
        stream: bool = True,
        message: Dict[str, Any] | None = None,
    ) -> SessionRequestStart:
        operation = self._acquire_application_operation()
        prepared: _PreparedSessionRequest | None = None
        try:
            prepared, existing_request_id = self._prepare(
                session_id,
                overrides,
                message=message,
            )
            if existing_request_id is not None:
                self._release_operation(operation)
                return SessionRequestStart(
                    status="already_running",
                    session_id=session_id,
                    request_id=existing_request_id,
                )

            assert prepared is not None
            worker = threading.Thread(
                target=self._run_background,
                args=(prepared, bool(stream), operation),
                name=f"session-request-{prepared.request_id}",
                daemon=True,
            )
            with self._lock:
                if self._closed:
                    self._clear_active(prepared.session.session_id, prepared.request_id)
                    raise SessionRequestCoordinatorClosedError(
                        "Session request coordinator is closed"
                    )
                self._threads_by_request[prepared.request_id] = worker
            worker.start()
            return SessionRequestStart(
                status="started",
                session_id=session_id,
                request_id=prepared.request_id,
            )
        except Exception:
            if prepared is not None:
                self._clear_active(prepared.session.session_id, prepared.request_id)
                prepared.operation.release()
            self._release_operation(operation)
            raise

    def run(
        self,
        session_id: str,
        overrides: Optional[Dict[str, Any]] = None,
        *,
        stream: bool = True,
        on_checkpoint: Callable[[Session], None] | None = None,
        on_event: Callable[[Dict[str, Any]], None] | None = None,
        message: Dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> SessionRequestResult:
        normalized_timeout = self._normalize_timeout(timeout)
        operation = self._acquire_application_operation()
        prepared: _PreparedSessionRequest | None = None
        try:
            prepared, existing_request_id = self._prepare(
                session_id,
                overrides,
                message=message,
            )
            if existing_request_id is not None:
                raise SessionRequestAlreadyRunningError(session_id, existing_request_id)
            assert prepared is not None
            return self._execute_with_timeout(
                prepared,
                stream=bool(stream),
                on_checkpoint=on_checkpoint,
                on_event=on_event,
                timeout=normalized_timeout,
            )
        finally:
            if prepared is not None:
                self._clear_active(prepared.session.session_id, prepared.request_id)
                prepared.operation.release()
            self._release_operation(operation)

    def run_ephemeral(
        self,
        core: Any,
        base_config: Dict[str, Any],
        session: Session,
        overrides: Optional[Dict[str, Any]] = None,
        *,
        stream: bool = True,
        on_checkpoint: Callable[[Session], None] | None = None,
        on_event: Callable[[Dict[str, Any]], None] | None = None,
        message: Dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> SessionRequestResult:
        """Run one coordinated request without persisting its session."""

        normalized_timeout = self._normalize_timeout(timeout)
        application_operation = self._acquire_application_operation()
        prepared: _PreparedSessionRequest | None = None
        try:
            prepared = self._prepare_ephemeral(
                core,
                base_config,
                session,
                overrides,
                message=message,
            )
            return self._execute_with_timeout(
                prepared,
                stream=bool(stream),
                on_checkpoint=on_checkpoint,
                on_event=on_event,
                timeout=normalized_timeout,
            )
        finally:
            if prepared is not None:
                self._clear_active(prepared.session.session_id, prepared.request_id)
                prepared.operation.release()
            self._release_operation(application_operation)

    def _execute_with_timeout(
        self,
        prepared: _PreparedSessionRequest,
        *,
        stream: bool,
        on_checkpoint: Callable[[Session], None] | None,
        on_event: Callable[[Dict[str, Any]], None] | None,
        timeout: float | None,
    ) -> SessionRequestResult:
        timer: threading.Timer | None = None
        timeout_fired = threading.Event()
        try:
            if timeout is not None:
                timer = threading.Timer(
                    timeout,
                    self._cancel_timed_out_request,
                    args=(prepared.request_id, timeout_fired),
                )
                timer.daemon = True
                timer.start()
            result = self._execute(
                prepared,
                stream=stream,
                on_checkpoint=on_checkpoint,
                on_event=on_event,
            )
            if not timeout_fired.is_set():
                return result
            return replace(
                result,
                status="cancelled",
                error=SessionRequestError(
                    category="timeout",
                    message=(
                        "Agent request exceeded the configured timeout and "
                        "was cancelled"
                    ),
                ),
            )
        finally:
            if timer is not None:
                timer.cancel()

    @staticmethod
    def _normalize_timeout(timeout: float | None) -> float | None:
        if timeout is None:
            return None
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(float(timeout))
            or float(timeout) <= 0
        ):
            raise ValueError("timeout must be a finite positive number")
        return float(timeout)

    def _cancel_timed_out_request(
        self,
        request_id: str,
        timeout_fired: threading.Event,
    ) -> None:
        timeout_fired.set()
        self._app.cancel_request(request_id)

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            request_ids = list(self._threads_by_request.keys())
        for request_id in request_ids:
            try:
                self._app.cancel_request(request_id)
            except Exception:
                continue

    def _acquire_application_operation(self) -> Any | None:
        with self._lock:
            if self._closed:
                raise SessionRequestCoordinatorClosedError(
                    "Session request coordinator is closed"
                )
        control = self._application_control
        acquire = getattr(control, "acquire_operation", None)
        if not callable(acquire):
            return None
        operation = acquire()
        if getattr(operation, "application", None) is self._app:
            return operation
        self._release_operation(operation)
        raise StaleApplicationGenerationError(
            "Cannot start a request through a stale AgentApplication generation"
        )

    @staticmethod
    def _release_operation(operation: Any | None) -> None:
        release = getattr(operation, "release", None)
        if callable(release):
            release()

    def _prepare(
        self,
        session_id: str,
        overrides: Optional[Dict[str, Any]],
        *,
        message: Dict[str, Any] | None,
    ) -> tuple[_PreparedSessionRequest | None, str | None]:
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")
        request_overrides = dict(overrides or {})
        request_id = self._new_request_id()
        operation: ApplicationOperationLease | None = None

        with self._app.acquire_session_lock(session_id):
            self._app._require_live_session_writable(session_id)
            ctx = self._app.load_session(session_id, overrides=request_overrides)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")
            core, base_config, session = ctx
            session_metadata = (
                session.metadata if isinstance(session.metadata, dict) else {}
            )
            stored_overrides = session_metadata.get("overrides")
            effective_overrides = {
                **(stored_overrides if isinstance(stored_overrides, dict) else {}),
                **request_overrides,
            }

            try:
                operation = self._operations.reserve(
                    operation_id=request_id,
                    owner_id="agent_app.session_request",
                    session_id=session_id,
                    exclusivity_keys=(session_operation_exclusivity_key(session_id),),
                )
            except ApplicationOperationBusyError as exc:
                current = exc.current
                if current.owner_id == "agent_app.session_request":
                    return None, current.operation_id
                raise SessionOperationBusyError(
                    session_id,
                    current.to_dict(),
                ) from exc

            with self._lock:
                if self._closed:
                    operation.release()
                    raise SessionRequestCoordinatorClosedError(
                        "Session request coordinator is closed"
                    )
                self._active_by_session[session_id] = request_id

            try:
                if message is not None:
                    session = self._append_message_locked(
                        core=core,
                        base_config=base_config,
                        session=session,
                        overrides=effective_overrides,
                        message=message,
                    )
                baseline_file_state = self._app.get_session_file_state(session_id)
            except Exception:
                self._clear_active(session_id, request_id)
                if operation is not None:
                    operation.release()
                raise

        assert operation is not None
        return (
            _PreparedSessionRequest(
                core=core,
                base_config=base_config,
                session=session,
                overrides=effective_overrides,
                request_id=request_id,
                baseline_file_state=baseline_file_state,
                operation=operation,
                persist_session=True,
            ),
            None,
        )

    def _prepare_ephemeral(
        self,
        core: Any,
        base_config: Dict[str, Any],
        session: Session,
        overrides: Optional[Dict[str, Any]],
        *,
        message: Dict[str, Any] | None,
    ) -> _PreparedSessionRequest:
        if not isinstance(session.session_id, str) or not session.session_id:
            raise ValueError("session_id must be a non-empty string")

        request_overrides = dict(overrides or {})
        request_id = self._new_request_id()
        operation: ApplicationOperationLease | None = None

        with self._app.acquire_session_lock(session.session_id):
            try:
                operation = self._operations.reserve(
                    operation_id=request_id,
                    owner_id="agent_app.session_request",
                    session_id=session.session_id,
                    exclusivity_keys=(
                        session_operation_exclusivity_key(session.session_id),
                    ),
                )
            except ApplicationOperationBusyError as exc:
                current = exc.current
                if current.owner_id == "agent_app.session_request":
                    raise SessionRequestAlreadyRunningError(
                        session.session_id,
                        current.operation_id,
                    ) from exc
                raise SessionOperationBusyError(
                    session.session_id,
                    current.to_dict(),
                ) from exc

            with self._lock:
                if self._closed:
                    operation.release()
                    raise SessionRequestCoordinatorClosedError(
                        "Session request coordinator is closed"
                    )
                self._active_by_session[session.session_id] = request_id

            try:
                if message is not None:
                    session = self._append_message_locked(
                        core=core,
                        base_config=base_config,
                        session=session,
                        overrides=request_overrides,
                        message=message,
                        persist_session=False,
                    )
            except Exception:
                self._clear_active(session.session_id, request_id)
                operation.release()
                raise

        return _PreparedSessionRequest(
            core=core,
            base_config=base_config,
            session=session,
            overrides=request_overrides,
            request_id=request_id,
            baseline_file_state=None,
            operation=operation,
            persist_session=False,
        )

    def _append_message_locked(
        self,
        *,
        core: Any,
        base_config: Dict[str, Any],
        session: Session,
        overrides: Dict[str, Any],
        message: Dict[str, Any],
        persist_session: bool = True,
    ) -> Session:
        role = message.get("role")
        content = message.get("content")
        metadata = message.get("metadata")
        multipart_content = message.get("multipart_content")
        if not isinstance(role, str) or not role:
            raise ValueError("message role must be a non-empty string")
        if not isinstance(content, str):
            raise ValueError("message content must be a string")
        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError("message metadata must be a mapping if provided")
        if multipart_content is not None and not isinstance(multipart_content, list):
            raise ValueError("multipart_content must be a list if provided")

        effective_config = self._app.resolve_effective_config(
            base_config,
            session,
            overrides,
        )
        new_session = core.add_message(
            session,
            role,
            content,
            metadata,
            effective_config,
            multipart_content=multipart_content,
            context=self._app._context.build_core_handoff_context(
                base_config=base_config,
                config=effective_config,
            ),
        )
        updated_session = (
            self._app.save_session(new_session, acquire_lock=False)
            if persist_session
            else new_session
        )
        last_message = (
            updated_session.messages[-1] if updated_session.messages else None
        )
        last_index = len(updated_session.messages) - 1
        stored = self._app.publish_event(
            {
                "type": "message_appended",
                "session_id": updated_session.session_id,
                "index": last_index,
                "role": role,
                "content": content,
                "metadata": metadata or {},
                "message": (
                    last_message.to_dict() if last_message is not None else None
                ),
            }
        )
        if persist_session:
            try:
                self._app.record_checkpoint(
                    updated_session.session_id,
                    stored.get("request_id"),
                )
            except Exception as exc:
                self._logger.warning(
                    "request_message_checkpoint_failed",
                    session_id=updated_session.session_id,
                    error=str(exc),
                )
        return updated_session

    def _run_background(
        self,
        prepared: _PreparedSessionRequest,
        stream: bool,
        operation: Any | None,
    ) -> None:
        try:
            self._execute(
                prepared,
                stream=stream,
                on_checkpoint=None,
                on_event=None,
            )
        except Exception as exc:
            self._logger.warning(
                "session_request_background_worker_failed",
                session_id=prepared.session.session_id,
                request_id=prepared.request_id,
                error=str(exc),
            )
        finally:
            self._clear_active(
                prepared.session.session_id,
                prepared.request_id,
            )
            with self._lock:
                self._threads_by_request.pop(prepared.request_id, None)
            prepared.operation.release()
            self._release_operation(operation)

    def _execute(
        self,
        prepared: _PreparedSessionRequest,
        *,
        stream: bool,
        on_checkpoint: Callable[[Session], None] | None,
        on_event: Callable[[Dict[str, Any]], None] | None,
    ) -> SessionRequestResult:
        final_session: Dict[str, Any] | None = prepared.session.to_dict()
        final_messages: list[Dict[str, Any]] = []
        final_request_id = prepared.request_id
        saw_successful_final = False
        saw_cancelled = False
        request_error: SessionRequestError | None = None
        observer_error: Exception | None = None

        send_options: Dict[str, Any] = {
            "stream": stream,
            "request_id": prepared.request_id,
            "baseline_file_state": prepared.baseline_file_state,
        }
        if not prepared.persist_session:
            send_options["persist_session"] = False
        for event in self._app.send_request(
            prepared.core,
            prepared.session,
            prepared.base_config,
            prepared.overrides,
            **send_options,
        ):
            event_type = event.get("type")
            if event_type == "session_checkpoint":
                session_obj = event.get("session")
                if isinstance(session_obj, Session):
                    final_session = session_obj.to_dict()
                    if on_checkpoint is not None:
                        on_checkpoint(session_obj)
                continue

            with self._lock:
                closed = self._closed
            if closed:
                continue

            stored = self._app.publish_event(event)
            stored_type = stored.get("type")
            if stored_type == "final":
                final_messages = [
                    item
                    for item in list(stored.get("messages") or [])
                    if isinstance(item, dict)
                ]
                saw_successful_final = any(
                    item.get("role") == "assistant" for item in final_messages
                )
                request_id = stored.get("request_id")
                if isinstance(request_id, str) and request_id:
                    final_request_id = request_id
            elif stored_type == "request_cancelled":
                saw_cancelled = True
            elif stored_type == "error":
                request_error = SessionRequestError(
                    category="request_failed",
                    message=_safe_error_message(stored.get("detail")),
                )
            elif isinstance(stored.get("session"), dict):
                final_session = stored["session"]

            if on_event is not None and observer_error is None:
                try:
                    on_event(stored)
                except Exception as exc:
                    observer_error = exc
                    self._app.cancel_request(prepared.request_id)

        if observer_error is not None:
            raise observer_error

        if saw_cancelled:
            status: SessionRequestResultStatus = "cancelled"
        elif request_error is not None:
            status = "failed"
        elif saw_successful_final:
            status = "succeeded"
        else:
            status = "interrupted"

        return SessionRequestResult(
            session_id=prepared.session.session_id,
            request_id=final_request_id,
            final_session=final_session,
            final_messages=final_messages,
            status=status,
            error=request_error,
        )

    def _clear_active(self, session_id: str, request_id: str) -> None:
        with self._lock:
            if self._active_by_session.get(session_id) == request_id:
                self._active_by_session.pop(session_id, None)


__all__ = [
    "SessionRequestAlreadyRunningError",
    "SessionRequestCoordinator",
    "SessionRequestCoordinatorClosedError",
    "SessionOperationBusyError",
    "SessionRequestError",
    "SessionRequestResult",
    "SessionRequestResultStatus",
    "SessionRequestStart",
    "StaleApplicationGenerationError",
]
