# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Background process for the ``compact_conversation`` application action.

The process mirrors the OpenAI Responses native-compaction process: the
Claude compaction feature's synchronous session action runs on a worker
thread, progress is published through session notifications with heartbeat
updates, prompt user cancellation interrupts the internal model request, and
the compacted session commits under the session lock with snapshot,
reconciliation, and conflict-safe persistence.
"""

from __future__ import annotations

import concurrent.futures
from datetime import datetime, timezone
import queue
import threading
import time
from typing import Any, Dict

from agent_app.notifications import (
    NotificationOperationSupersededError,
    NotificationTransitionError,
)
from agent_app.operations import ApplicationOperationLease
from agent_app.tool_loop import RequestCancellation
from agent_core import Session

from .claude_compaction_feature import CANCELLATION_CONTEXT_KEY

APP_PLUGIN_ID = "claude_compaction_app"
FEATURE_PLUGIN_ID = "claude_compaction"
SYNC_ACTION_ID = "compact_conversation"
OPERATION_TYPE = "claude_compaction"
NOTIFICATION_KEY = "claude_tools:compaction"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ClaudeCompactionProcess:
    """Managed background process owning one Claude compaction execution."""

    def __init__(
        self,
        *,
        app: Any,
        registry: Any,
        process_id: str,
        operation: ApplicationOperationLease,
        session_id: str,
        core: Any,
        base_config: Dict[str, Any],
        session: Session,
        effective_config: Dict[str, Any],
        baseline_file_state: Any,
        action_params: Dict[str, Any],
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
        self._core = core
        self._base_config = base_config
        self._session = session
        self._effective_config = effective_config
        self._baseline_file_state = baseline_file_state
        self._action_params = action_params
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
        self._cancellation: RequestCancellation | None = None

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
        cancellation = RequestCancellation()
        handoff_context = self._app.build_core_handoff_context(
            base_config=self._base_config,
            config=self._effective_config,
            extra={
                **(self._action_context or {}),
                CANCELLATION_CONTEXT_KEY: cancellation,
            },
        )
        with self._state_lock:
            self._cancellation = cancellation
        worker = threading.Thread(
            target=self._run,
            args=(cancellation, handoff_context),
            name=f"claude-compaction-{self.operation_id}",
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
            cancellation = self._cancellation
        self._safe_notification_update(
            severity="warning",
            phase="cancellation_requested",
            body="Cancelling Claude compaction…",
            cancellable=False,
        )
        if cancellation is not None:
            cancellation.cancel()
        return True

    def close(self) -> None:
        with self._state_lock:
            if self._closed or self._terminal:
                return
            self._closed = True
            self._invalidated = True
            cancellation = self._cancellation
        if cancellation is not None:
            cancellation.cancel()
        self._operation.release()
        self._safe_notification_failure(
            "Claude compaction was interrupted because the application "
            "reloaded or shut down.",
            interrupted=True,
        )

    def _run(
        self,
        cancellation: RequestCancellation,
        handoff_context: Dict[str, Any],
    ) -> None:
        results: queue.Queue[tuple[str, Any]] = queue.Queue()

        def _provider_work() -> None:
            try:
                new_session, result = self._core.execute_session_action(
                    self._session,
                    self._effective_config,
                    FEATURE_PLUGIN_ID,
                    SYNC_ACTION_ID,
                    dict(self._action_params),
                    context=handoff_context,
                )
                error = result.get("error") if isinstance(result, dict) else None
                if isinstance(error, dict):
                    message = error.get("message")
                    results.put(
                        (
                            "error",
                            RuntimeError(
                                message
                                if isinstance(message, str) and message
                                else "Claude compaction failed."
                            ),
                        )
                    )
                    return
                results.put(("result", (new_session, result)))
            except BaseException as exc:
                results.put(("error", exc))

        provider_thread = threading.Thread(
            target=_provider_work,
            name=f"claude-compaction-provider-{self.operation_id}",
            daemon=True,
        )
        provider_thread.start()
        self._safe_notification_update(
            severity="warning",
            phase="waiting_for_model",
            body=self._progress_body("Waiting for the Claude compaction model."),
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
            message = (
                action_result.get("message")
                if isinstance(action_result, dict)
                else None
            )
            self._safe_notification_update(
                severity="warning",
                phase="committing",
                body=self._progress_body("Applying the compacted conversation."),
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
                    snapshot = self._app.create_session_snapshot(
                        self.session_id,
                        reason="Before compacting conversation",
                        metadata={
                            "origin": "automatic",
                            "plugin": APP_PLUGIN_ID,
                            "action": SYNC_ACTION_ID,
                            "operation_id": self.operation_id,
                        },
                    )
                    try:
                        self._app.save_session(
                            new_session,
                            reconcile=True,
                            baseline_session=self._session,
                            baseline_file_state=self._baseline_file_state,
                            conflict_prefix=(
                                "Concurrent session modification detected while "
                                "compacting the conversation; "
                            ),
                            backup_on_conflict=True,
                            acquire_lock=False,
                        )
                    except BaseException:
                        self._app.delete_session_snapshot(
                            self.session_id,
                            snapshot.snapshot_id,
                        )
                        raise

            self._safe_notification_completion(
                title="Compaction complete",
                body=(
                    message
                    if isinstance(message, str) and message
                    else "Claude compaction completed."
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
        phase = "cancellation_requested" if cancel_requested else "waiting_for_model"
        body = (
            "Cancelling Claude compaction…"
            if cancel_requested
            else self._progress_body("Waiting for the Claude compaction model.")
        )
        self._safe_notification_update(
            severity="warning",
            phase=phase,
            body=body,
            cancellable=not cancel_requested,
        )

    def _finish_cancelled(self) -> None:
        self._safe_notification_completion(
            title="Compaction cancelled",
            body="Claude compaction was cancelled.",
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
        body = "Preparing Claude compaction. Elapsed: 0 seconds."
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
    ) -> Dict[str, Any]:
        operation_state = (
            "cancelling" if phase == "cancellation_requested" else "running"
        )
        return {
            "key": NOTIFICATION_KEY,
            "severity": severity,
            "title": "Compacting conversation",
            "body": body,
            "source": {"plugin": APP_PLUGIN_ID},
            "display": {
                "format": "text",
                "title": "Compacting conversation",
                "body": body,
                "variant": severity,
                "presentation": "banner",
                "dismissible": True,
                "actions": self._cancel_followups() if cancellable else [],
            },
            "model_visibility": "hidden",
            "retention": {"version": 1, "policy": "until_resolved"},
            "operation": {
                "version": 1,
                "type": OPERATION_TYPE,
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
            if not isinstance(self._notification, dict):
                return
            # Re-check lifecycle state under the notification lock so a
            # heartbeat that straddles close() or a terminal completion
            # cannot overwrite the terminal notification.
            if self._closed or self._terminal:
                return
            payload = self._notification_payload(
                severity=severity,
                phase=phase,
                body=body,
                cancellable=cancellable,
            )
            try:
                stored = self._app.create_session_notification(
                    self.session_id,
                    payload,
                )
            except (
                NotificationTransitionError,
                NotificationOperationSupersededError,
                KeyError,
                ValueError,
            ):
                return
            self._notification = stored

    def _safe_notification_failure(
        self,
        detail: str,
        *,
        interrupted: bool = False,
    ) -> None:
        title = "Compaction interrupted" if interrupted else "Compaction failed"
        body = detail if interrupted else f"Claude compaction failed: {detail}"
        with self._notification_lock:
            if not isinstance(self._notification, dict):
                return
            payload = {
                "key": NOTIFICATION_KEY,
                "severity": "warning" if interrupted else "error",
                "title": title,
                "body": body,
                "source": {"plugin": APP_PLUGIN_ID},
                "display": {
                    "format": "text",
                    "title": title,
                    "body": body,
                    "variant": "warning" if interrupted else "error",
                    "presentation": "banner",
                    "dismissible": True,
                    "actions": self._retry_followups(),
                },
                "model_visibility": "hidden",
                "retention": {"version": 1, "policy": "until_resolved"},
                "operation": {
                    "version": 1,
                    "type": OPERATION_TYPE,
                    "id": self.operation_id,
                    "state": "interrupted" if interrupted else "failed",
                    "phase": "interrupted" if interrupted else "failed",
                    "started_at": self._started_at,
                    "elapsed_seconds": self._elapsed_seconds(),
                    "cancellable": False,
                },
            }
            try:
                stored = self._app.create_session_notification(
                    self.session_id,
                    payload,
                )
            except (
                NotificationTransitionError,
                NotificationOperationSupersededError,
                KeyError,
                ValueError,
            ):
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
            if not isinstance(self._notification, dict):
                return
            payload = {
                "key": NOTIFICATION_KEY,
                "severity": severity,
                "title": title,
                "body": body,
                "source": {"plugin": APP_PLUGIN_ID},
                "display": {
                    "format": "text",
                    "title": title,
                    "body": body,
                    "variant": severity,
                    "presentation": "banner",
                    "dismissible": True,
                    "actions": [],
                },
                "model_visibility": "hidden",
                "retention": {"version": 1, "policy": "until_resolved"},
                "operation": {
                    "version": 1,
                    "type": OPERATION_TYPE,
                    "id": self.operation_id,
                    "state": state,
                    "phase": phase,
                    "started_at": self._started_at,
                    "elapsed_seconds": self._elapsed_seconds(),
                    "cancellable": False,
                },
            }
            if state == "succeeded":
                payload["ui_effects"] = {
                    "reload_session_ids": [self.session_id],
                }
            try:
                stored = self._app.create_session_notification(
                    self.session_id,
                    payload,
                )
            except (
                NotificationTransitionError,
                NotificationOperationSupersededError,
                KeyError,
                ValueError,
            ):
                return
            self._notification = stored

    def _cancel_followups(self) -> list[Dict[str, Any]]:
        return [
            {
                "kind": "run_action",
                "id": "cancel",
                "label": "Cancel compaction",
                "plugin": APP_PLUGIN_ID,
                "action_id": "cancel_claude_compaction",
                "action_owner": "application",
                "fixed_params": {
                    "session_id": self.session_id,
                    "operation_id": self.operation_id,
                },
            }
        ]

    def _retry_followups(self) -> list[Dict[str, Any]]:
        fixed_params: Dict[str, Any] = {"session_id": self.session_id}
        for key in ("start", "end", "instructions"):
            value = self._action_params.get(key)
            if value is not None:
                fixed_params[key] = value
        return [
            {
                "kind": "run_action",
                "id": "retry",
                "label": "Retry",
                "plugin": APP_PLUGIN_ID,
                "action_id": SYNC_ACTION_ID,
                "action_owner": "application",
                "fixed_params": fixed_params,
            }
        ]


__all__ = [
    "APP_PLUGIN_ID",
    "ClaudeCompactionProcess",
    "FEATURE_PLUGIN_ID",
    "NOTIFICATION_KEY",
    "OPERATION_TYPE",
    "SYNC_ACTION_ID",
]
