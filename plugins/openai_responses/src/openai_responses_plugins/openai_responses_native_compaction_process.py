from __future__ import annotations

import concurrent.futures
from datetime import datetime, timezone
import queue
import threading
import time
from typing import Any, Dict

from agent_app.notifications import (
    NotificationRevisionConflictError,
    NotificationTransitionError,
)
from agent_app.operations import ApplicationOperationLease
from agent_core import Session

from .openai_responses_native_compaction import (
    COMPACTION_TRANSPORT_CONTEXT_KEY,
    CancellableAsyncOpenAIResponsesCompactionTransport,
)


PLUGIN_ID = "openai_responses_native_compaction_app"
EXTENSION_ID = "openai_responses_native_compaction"
SYNC_ACTION_ID = "compact_native_history_sync"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class OpenAIResponsesNativeCompactionProcess:
    def __init__(
        self,
        *,
        app: Any,
        registry: Any,
        process_id: str,
        operation: ApplicationOperationLease,
        session_id: str,
        end_index: int | None,
        action_context: Dict[str, Any] | None = None,
        heartbeat_interval: float = 15.0,
        monotonic: Any = time.monotonic,
    ) -> None:
        self._app = app
        self._registry = registry
        self.process_id = process_id
        self.operation_id = operation.operation_id
        self.session_id = session_id
        self._operation = operation
        self._end_index = end_index
        self._action_context = action_context
        self._heartbeat_interval = heartbeat_interval
        self._monotonic = monotonic
        self._started_monotonic = 0.0
        self._started_at = _timestamp()
        self._state_lock = threading.RLock()
        self._notification_lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._invalidated = False
        self._closed = False
        self._cancel_requested = False
        self._commit_started = False
        self._terminal = False
        self._notification: Dict[str, Any] | None = None
        self._transport: CancellableAsyncOpenAIResponsesCompactionTransport | None = (
            None
        )

    @property
    def notification_id(self) -> str | None:
        with self._notification_lock:
            notification = self._notification
            value = notification.get("id") if isinstance(notification, dict) else None
            return value if isinstance(value, str) and value else None

    def matches(self, *, session_id: str, operation_id: str) -> bool:
        return self.session_id == session_id and self.operation_id == operation_id

    def start(self) -> None:
        self._started_monotonic = self._monotonic()
        self._create_notification()
        core, base_config, session, effective_config, baseline_file_state = (
            self._capture_baseline()
        )
        transport = CancellableAsyncOpenAIResponsesCompactionTransport(
            run_awaitable_blocking=self._app.run_awaitable_blocking,
        )
        handoff_extra = {
            **(self._action_context or {}),
            COMPACTION_TRANSPORT_CONTEXT_KEY: transport,
        }
        handoff_context = self._app.build_core_handoff_context(
            base_config=base_config,
            config=effective_config,
            extra=handoff_extra,
        )
        with self._state_lock:
            self._transport = transport
        worker = threading.Thread(
            target=self._run,
            args=(
                core,
                session,
                effective_config,
                baseline_file_state,
                transport,
                handoff_context,
            ),
            name=f"openai-native-compaction-{self.operation_id}",
            daemon=True,
        )
        with self._state_lock:
            self._thread = worker
        worker.start()

    def request_cancel(self) -> bool:
        with self._state_lock:
            if (
                self._closed
                or self._invalidated
                or self._commit_started
                or self._terminal
            ):
                return False
            self._invalidated = True
            self._cancel_requested = True
            transport = self._transport
        self._safe_notification_update(
            severity="warning",
            phase="cancellation_requested",
            body="Cancelling OpenAI native compaction…",
            cancellable=False,
        )
        if transport is not None:
            transport.cancel()
        return True

    def close(self) -> None:
        with self._state_lock:
            if self._closed or self._terminal:
                return
            self._closed = True
            self._invalidated = True
            transport = self._transport
        if transport is not None:
            transport.cancel()
        self._operation.release()
        self._safe_notification_failure(
            "Compaction was interrupted because the application reloaded or shut down.",
            interrupted=True,
        )

    def _capture_baseline(
        self,
    ) -> tuple[Any, Dict[str, Any], Session, Dict[str, Any], Any]:
        with self._app.acquire_session_lock(self.session_id):
            loaded = self._app.load_session(self.session_id)
            if loaded is None:
                raise KeyError(f"Session {self.session_id!r} not found")
            core, base_config, session = loaded
            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            overrides = metadata.get("overrides")
            if not isinstance(overrides, dict):
                overrides = {}
            effective_config = self._app.resolve_effective_config(
                base_config,
                session,
                overrides,
            )
            baseline_file_state = self._app.get_session_file_state(self.session_id)
        return core, base_config, session, effective_config, baseline_file_state

    def _run(
        self,
        core: Any,
        session: Session,
        effective_config: Dict[str, Any],
        baseline_file_state: Any,
        transport: CancellableAsyncOpenAIResponsesCompactionTransport,
        handoff_context: Dict[str, Any],
    ) -> None:
        results: queue.Queue[tuple[str, Any]] = queue.Queue()

        def _provider_work() -> None:
            try:
                params = (
                    {"end_index": self._end_index}
                    if self._end_index is not None
                    else {}
                )
                new_session, result = core.execute_session_action(
                    session,
                    effective_config,
                    EXTENSION_ID,
                    SYNC_ACTION_ID,
                    params,
                    context=handoff_context,
                )
                results.put(("result", (new_session, result)))
            except BaseException as exc:
                results.put(("error", exc))

        provider_thread = threading.Thread(
            target=_provider_work,
            name=f"openai-native-compaction-provider-{self.operation_id}",
            daemon=True,
        )
        provider_thread.start()
        self._safe_notification_update(
            severity="warning",
            phase="waiting_for_provider",
            body=self._progress_body("Waiting for OpenAI native compaction."),
            cancellable=True,
        )

        try:
            while True:
                try:
                    kind, value = results.get(timeout=self._heartbeat_interval)
                    break
                except queue.Empty:
                    self._heartbeat()

            with self._state_lock:
                invalidated = self._invalidated
                cancel_requested = self._cancel_requested
                closed = self._closed
            if invalidated:
                if cancel_requested and not closed:
                    self._finish_cancelled()
                return

            if kind == "error":
                if isinstance(
                    value,
                    (
                        concurrent.futures.CancelledError,
                        TimeoutError,
                    ),
                ):
                    with self._state_lock:
                        cancel_requested = self._cancel_requested
                    if cancel_requested:
                        self._finish_cancelled()
                        return
                self._finish_failed(value)
                return

            new_session, action_result = value
            self._safe_notification_update(
                severity="warning",
                phase="committing",
                body=self._progress_body("Applying compacted native history."),
                cancellable=False,
            )

            with self._state_lock:
                if self._invalidated:
                    if self._cancel_requested and not self._closed:
                        self._finish_cancelled()
                    return
                with self._app.acquire_session_lock(self.session_id):
                    if self._invalidated:
                        if self._cancel_requested and not self._closed:
                            self._finish_cancelled()
                        return
                    self._commit_started = True
                    self._app.save_session(
                        new_session,
                        reconcile=True,
                        baseline_session=session,
                        baseline_file_state=baseline_file_state,
                        conflict_prefix=(
                            "Concurrent session modification detected while "
                            "committing native compaction; "
                        ),
                        backup_on_conflict=True,
                        acquire_lock=False,
                    )

            self._safe_notification_completion(
                title="Native compaction complete",
                body=(
                    action_result.get("message")
                    if isinstance(action_result.get("message"), str)
                    else "OpenAI native compaction completed."
                ),
                severity="success",
                state="succeeded",
                phase="completed",
            )
            with self._state_lock:
                self._terminal = True
        except BaseException as exc:
            with self._state_lock:
                cancel_requested = self._cancel_requested
                closed = self._closed
            if cancel_requested and not closed:
                self._finish_cancelled()
            elif not closed:
                self._finish_failed(exc)
        finally:
            self._registry.remove(self.process_id, self)
            self._operation.release()

    def _heartbeat(self) -> None:
        with self._state_lock:
            if self._closed:
                return
            cancel_requested = self._cancel_requested
        phase = "cancellation_requested" if cancel_requested else "waiting_for_provider"
        body = (
            "Cancelling OpenAI native compaction…"
            if cancel_requested
            else self._progress_body("Waiting for OpenAI native compaction.")
        )
        self._safe_notification_update(
            severity="warning",
            phase=phase,
            body=body,
            cancellable=not cancel_requested,
        )

    def _finish_cancelled(self) -> None:
        self._safe_notification_completion(
            title="Native compaction cancelled",
            body="OpenAI native compaction was cancelled.",
            severity="warning",
            state="cancelled",
            phase="cancelled",
        )
        with self._state_lock:
            self._terminal = True

    def _finish_failed(self, exc: BaseException) -> None:
        detail = str(exc) or type(exc).__name__
        safe_detail = detail[:500]
        self._safe_notification_failure(safe_detail)
        with self._state_lock:
            self._terminal = True

    def _elapsed_seconds(self) -> int:
        return max(0, int(self._monotonic() - self._started_monotonic))

    def _progress_body(self, prefix: str) -> str:
        elapsed = self._elapsed_seconds()
        unit = "second" if elapsed == 1 else "seconds"
        return f"{prefix} Elapsed: {elapsed} {unit}."

    def _create_notification(self) -> None:
        body = "Preparing OpenAI native compaction. Elapsed: 0 seconds."
        stored = self._app.create_session_notification(
            self.session_id,
            self._notification_payload(
                severity="warning",
                phase="preparing",
                body=body,
                cancellable=True,
            ),
        )
        with self._notification_lock:
            self._notification = stored

    def _notification_payload(
        self,
        *,
        severity: str,
        phase: str,
        body: str,
        cancellable: bool,
        actions: list[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        operation_state = (
            "cancelling" if phase == "cancellation_requested" else "running"
        )
        return {
            "key": f"openai_responses:native_compaction:{self.operation_id}",
            "severity": severity,
            "title": "Compacting native history",
            "body": body,
            "source": {"plugin": PLUGIN_ID},
            "display": {
                "format": "text",
                "title": "Compacting native history",
                "body": body,
                "variant": severity,
                "presentation": "banner",
                "dismissible": False,
                "actions": (
                    actions
                    if actions is not None
                    else self._cancel_followups() if cancellable else []
                ),
            },
            "model_visibility": "hidden",
            "retention": {"version": 1, "policy": "until_resolved"},
            "operation": {
                "version": 1,
                "type": "openai_responses_native_compaction",
                "id": self.operation_id,
                "state": operation_state,
                "phase": phase,
                "started_at": self._started_at,
                "elapsed_seconds": self._elapsed_seconds(),
                "cancellable": cancellable,
            },
        }

    def _safe_notification_update(
        self,
        *,
        severity: str,
        phase: str,
        body: str,
        cancellable: bool,
    ) -> None:
        with self._notification_lock:
            notification = self._notification
            if not isinstance(notification, dict):
                return
            notification_id = notification.get("id")
            revision = notification.get("revision") or notification.get("updated_at")
            if not isinstance(notification_id, str):
                return
            patch = self._notification_payload(
                severity=severity,
                phase=phase,
                body=body,
                cancellable=cancellable,
            )
            patch.pop("key", None)
            try:
                stored = self._app.update_session_notification(
                    self.session_id,
                    notification_id,
                    patch,
                    expected_revision=revision,
                )
            except NotificationRevisionConflictError as exc:
                current = exc.current
                if (
                    current.get("status") != "pending"
                    or (current.get("operation") or {}).get("id") != self.operation_id
                ):
                    self._notification = current
                    return
                stored = self._app.update_session_notification(
                    self.session_id,
                    notification_id,
                    patch,
                    expected_revision=current.get("revision")
                    or current.get("updated_at"),
                )
            except (NotificationTransitionError, KeyError, ValueError):
                return
            self._notification = stored

    def _safe_notification_failure(
        self,
        detail: str,
        *,
        interrupted: bool = False,
    ) -> None:
        title = (
            "Native compaction interrupted"
            if interrupted
            else "Native compaction failed"
        )
        body = detail if interrupted else f"OpenAI native compaction failed: {detail}"
        with self._notification_lock:
            notification = self._notification
            if not isinstance(notification, dict):
                return
            notification_id = notification.get("id")
            revision = notification.get("revision") or notification.get("updated_at")
            if not isinstance(notification_id, str):
                return
            patch = {
                "severity": "warning" if interrupted else "error",
                "title": title,
                "body": body,
                "display": {
                    "format": "text",
                    "title": title,
                    "body": body,
                    "variant": "warning" if interrupted else "error",
                    "presentation": "banner",
                    "dismissible": True,
                    "actions": self._retry_followups(),
                },
                "operation": {
                    "version": 1,
                    "type": "openai_responses_native_compaction",
                    "id": self.operation_id,
                    "state": "interrupted" if interrupted else "failed",
                    "phase": "interrupted" if interrupted else "failed",
                    "started_at": self._started_at,
                    "elapsed_seconds": self._elapsed_seconds(),
                    "cancellable": False,
                },
            }
            try:
                stored = self._app.update_session_notification(
                    self.session_id,
                    notification_id,
                    patch,
                    expected_revision=revision,
                )
            except Exception:
                return
            self._notification = stored

    def _safe_notification_completion(
        self,
        *,
        title: str,
        body: str,
        severity: str,
        state: str,
        phase: str,
    ) -> None:
        with self._notification_lock:
            notification = self._notification
            if not isinstance(notification, dict):
                return
            notification_id = notification.get("id")
            revision = notification.get("revision") or notification.get("updated_at")
            if not isinstance(notification_id, str):
                return
            patch = {
                "severity": severity,
                "title": title,
                "body": body,
                "display": {
                    "format": "text",
                    "title": title,
                    "body": body,
                    "variant": severity,
                    "presentation": "banner",
                    "dismissible": True,
                    "actions": [],
                },
                "operation": {
                    "version": 1,
                    "type": "openai_responses_native_compaction",
                    "id": self.operation_id,
                    "state": state,
                    "phase": phase,
                    "started_at": self._started_at,
                    "elapsed_seconds": self._elapsed_seconds(),
                    "cancellable": False,
                },
            }
            try:
                stored = self._app.update_session_notification(
                    self.session_id,
                    notification_id,
                    patch,
                    expected_revision=revision,
                )
            except Exception:
                return
            self._notification = stored

    def _cancel_followups(self) -> list[Dict[str, Any]]:
        return [
            {
                "kind": "run_action",
                "id": "cancel",
                "label": "Cancel compaction",
                "plugin": PLUGIN_ID,
                "action_id": "cancel_native_compaction",
                "action_owner": "application",
                "fixed_params": {
                    "session_id": self.session_id,
                    "operation_id": self.operation_id,
                },
            }
        ]

    def _retry_followups(self) -> list[Dict[str, Any]]:
        fixed_params: Dict[str, Any] = {"session_id": self.session_id}
        if self._end_index is not None:
            fixed_params["end_index"] = self._end_index
        return [
            {
                "kind": "run_action",
                "id": "retry",
                "label": "Retry",
                "plugin": PLUGIN_ID,
                "action_id": "compact_native_history",
                "action_owner": "application",
                "fixed_params": fixed_params,
            }
        ]


__all__ = [
    "EXTENSION_ID",
    "OpenAIResponsesNativeCompactionProcess",
    "PLUGIN_ID",
    "SYNC_ACTION_ID",
]
