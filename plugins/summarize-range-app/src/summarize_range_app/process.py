"""Background process for the ``summarize_range`` application action.

The process mirrors the OpenAI Responses native-compaction process: it runs
the summarization model request on a worker thread, publishes progress
through session notifications with heartbeat updates, supports prompt user
cancellation, and commits the summarized session under the session lock with
snapshot, reconciliation, and conflict-safe persistence.
"""

from __future__ import annotations

import concurrent.futures
from datetime import datetime, timezone
import queue
import threading
import time
from typing import Any, Dict, List, Optional

from agent_app.config import resolve_request_config
from agent_app.notifications import (
    NotificationOperationSupersededError,
    NotificationTransitionError,
)
from agent_app.operations import ApplicationOperationLease
from agent_app.tool_loop import RequestCancellation
from agent_core import Session

PLUGIN_ID = "summarize_range"
OPERATION_TYPE = "summarize_range"
NOTIFICATION_KEY = "summarize_range:range_summarization"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _collect_final_messages_from_stream(
    core: Any,
    session: Session,
    config: Dict[str, Any],
    *,
    request_id: str | None = None,
    context: Dict[str, Any] | None = None,
    cancellation: Any | None = None,
) -> List[Dict[str, Any]]:
    """Run an internal request via the streaming path and return final messages."""

    final_messages: List[Dict[str, Any]] = []
    for event in core.send_request_stream(
        session,
        config,
        request_id=request_id,
        context=context,
        cancellation=cancellation,
    ):
        if event.get("type") != "final":
            continue
        raw_messages = event.get("messages")
        if isinstance(raw_messages, list):
            final_messages = raw_messages
    return final_messages


def _normalize_slice_bounds(
    message_count: int,
    start: int | None,
    end: int | None,
) -> tuple[int, int]:
    """Return concrete ``(start_idx, end_idx)`` for slice-like bounds.

    Semantics match the helper used by the server actions plugins:

    - ``start`` and ``end`` follow Python slice rules, including support
      for ``None`` and negative indices.
    - Indices are clamped to ``[0, message_count]``.
    - ``ValueError`` is raised when the range selects no messages.
    """

    def _bound(value: int | None, default: int) -> int:
        if value is None:
            return default
        idx = value
        if idx < 0:
            idx = message_count + idx
        if idx < 0:
            return 0
        if idx > message_count:
            return message_count
        return idx

    start_idx = _bound(start, 0)
    end_idx = _bound(end, message_count)

    if start_idx >= end_idx:
        raise ValueError("range selects no messages")

    return start_idx, end_idx


def _session_overrides(session: Session) -> Dict[str, Any]:
    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    overrides = metadata.get("overrides")
    return overrides if isinstance(overrides, dict) else {}


class SummarizeRangeProcess:
    """Managed background process owning one ``summarize_range`` execution."""

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
        baseline_file_state: Any,
        start_idx: int,
        end_idx: int,
        prompt: str,
        agent_id: Optional[str] = None,
        settings_overrides: Optional[Dict[str, Any]] = None,
        action_context: Optional[Dict[str, Any]] = None,
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
        self._baseline_file_state = baseline_file_state
        self._start_idx = start_idx
        self._end_idx = end_idx
        self._prompt = prompt
        self._agent_id = agent_id
        self._settings_overrides = settings_overrides or {}
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
        with self._state_lock:
            self._cancellation = cancellation
        worker = threading.Thread(
            target=self._run,
            args=(cancellation,),
            name=f"summarize-range-{self.operation_id}",
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
            body="Cancelling range summarization…",
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
            "Range summarization was interrupted because the application "
            "reloaded or shut down.",
            interrupted=True,
        )

    # ------------------------------------------------------------------
    # Provider work
    # ------------------------------------------------------------------

    def _summarize_range(self, cancellation: RequestCancellation) -> str:
        """Run the summarization model request and return the summary text."""

        app = self._app
        core_orig = self._core
        base_config_orig = self._base_config
        session_orig = self._session

        message_count = len(session_orig.messages)

        # Compute a slice that always keeps leading system messages as context.
        system_prefix_end = 0
        for msg in session_orig.messages:
            if msg.role == "system":
                system_prefix_end += 1
            else:
                break

        keep_indices = set(range(system_prefix_end)) | set(
            range(self._start_idx, self._end_idx)
        )
        remove_indices = sorted(
            index for index in set(range(message_count)) if index not in keep_indices
        )

        md_overrides = _session_overrides(session_orig)
        slice_config = resolve_request_config(base_config_orig, md_overrides)

        sliced_for_sum = core_orig.slice_session(
            session_orig,
            slice_config,
            remove_indices=remove_indices,
        )

        # Choose summarizer agent: either a dedicated one from config or the
        # current session agent.
        md_sliced = (
            sliced_for_sum.metadata if isinstance(sliced_for_sum.metadata, dict) else {}
        )
        session_agent_id = md_sliced.get("agent_id")
        if not isinstance(session_agent_id, str) or not session_agent_id:
            raise RuntimeError("session metadata must contain non-empty 'agent_id'")

        if isinstance(self._agent_id, str) and self._agent_id.strip():
            target_agent_id = self._agent_id.strip()
        else:
            target_agent_id = session_agent_id

        if target_agent_id == session_agent_id:
            core_sum = core_orig
            base_config_sum = base_config_orig
            session_for_sum = sliced_for_sum
        else:
            core_sum, base_config_sum, session_for_sum = app.update_agent(
                target_agent_id, sliced_for_sum
            )

        # Build overrides for the summarization request: per-session overrides
        # plus any summarize_range-specific settings from configuration.
        md_overrides2 = _session_overrides(session_for_sum)
        combined_overrides: Dict[str, Any] = {
            **md_overrides2,
            **self._settings_overrides,
        }
        request_overrides: Dict[str, Any] = {
            "disable_all_tools": True,
            **combined_overrides,
        }
        config_for_add = resolve_request_config(base_config_sum, combined_overrides)

        # Append the prompt as a user message using the summarizer core and
        # configuration so that any provider-native history stays consistent.
        # The handoff context carries the session asset store so providers
        # that expand session assets during native-history rebuilds (for
        # example the OpenAI Responses provider) can resolve attachments.
        add_context = app.build_core_handoff_context(
            base_config=base_config_sum,
            config=config_for_add,
            extra=self._action_context,
        )
        session_with_prompt = core_sum.add_message(
            session_for_sum,
            "user",
            self._prompt,
            metadata=None,
            config=config_for_add,
            context=add_context,
        )

        core_sum, _base_sum, session_with_prompt, request_config, rid = (
            app.prepare_tools_for_session(
                core_sum,
                session_with_prompt,
                base_config_sum,
                request_overrides,
            )
        )
        handoff_context = app.build_core_handoff_context(
            base_config=base_config_sum,
            config=request_config,
            extra=self._action_context,
        )
        last_final_messages = _collect_final_messages_from_stream(
            core_sum,
            session_with_prompt,
            request_config,
            request_id=rid,
            context=handoff_context,
            cancellation=cancellation,
        )

        summary_text: Optional[str] = None
        if last_final_messages:
            for msg in reversed(last_final_messages):
                if not isinstance(msg, dict):
                    continue
                if msg.get("role") != "assistant":
                    continue
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    summary_text = content.strip()
                    break

        if not summary_text:
            raise RuntimeError("Summarization failed (no assistant reply).")
        return summary_text

    # ------------------------------------------------------------------
    # Commit
    # ------------------------------------------------------------------

    def _apply_summary(self, summary_text: str) -> Session:
        edit_config = resolve_request_config(
            self._base_config,
            _session_overrides(self._session),
        )
        remove_indices = list(range(self._start_idx, self._end_idx))
        session_after_delete = self._core.slice_session(
            self._session,
            edit_config,
            remove_indices=remove_indices,
        )
        summary_metadata: Dict[str, Any] = {
            "summarized_range": {
                "start_index": self._start_idx,
                "end_index": self._end_idx,
            }
        }
        # Pass the handoff context (with the session asset store) so the
        # commit-phase native-history rebuild can expand session assets.
        commit_context = self._app.build_core_handoff_context(
            base_config=self._base_config,
            config=edit_config,
        )
        return self._core.add_message(
            session_after_delete,
            "assistant",
            summary_text,
            metadata=summary_metadata,
            config=edit_config,
            after_index=self._start_idx - 1,
            context=commit_context,
        )

    # ------------------------------------------------------------------
    # Worker
    # ------------------------------------------------------------------

    def _run(self, cancellation: RequestCancellation) -> None:
        results: queue.Queue[tuple[str, Any]] = queue.Queue()

        def _provider_work() -> None:
            try:
                results.put(("result", self._summarize_range(cancellation)))
            except BaseException as exc:
                results.put(("error", exc))

        provider_thread = threading.Thread(
            target=_provider_work,
            name=f"summarize-range-provider-{self.operation_id}",
            daemon=True,
        )
        provider_thread.start()
        self._safe_notification_update(
            severity="warning",
            phase="waiting_for_model",
            body=self._progress_body("Waiting for the range summarization model."),
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

            summary_text = value
            self._safe_notification_update(
                severity="warning",
                phase="committing",
                body=self._progress_body("Applying the summarized range."),
                cancellable=False,
            )

            new_session: Session
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
                        reason=(
                            f"Before summarizing messages "
                            f"[{self._start_idx}:{self._end_idx}]"
                        ),
                        metadata={
                            "origin": "automatic",
                            "plugin": PLUGIN_ID,
                            "action": "summarize_range",
                            "operation_id": self.operation_id,
                            "range": {
                                "start": self._start_idx,
                                "end": self._end_idx,
                            },
                        },
                    )
                    try:
                        new_session = self._apply_summary(summary_text)
                        self._app.save_session(
                            new_session,
                            reconcile=True,
                            baseline_session=self._session,
                            baseline_file_state=self._baseline_file_state,
                            conflict_prefix=(
                                "Concurrent session modification detected while "
                                "summarizing messages; "
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

            stored = self._app.publish_event(
                {
                    "type": "range_summarized",
                    "session_id": new_session.session_id,
                    "start_index": self._start_idx,
                    "end_index": self._end_idx,
                }
            )
            try:
                self._app.record_checkpoint(
                    new_session.session_id,
                    stored.get("request_id"),
                )
            except Exception:  # pragma: no cover - defensive
                pass

            self._safe_notification_completion(
                title="Summarization complete",
                body="Summarized messages in the selected range.",
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
            "Cancelling range summarization…"
            if cancel_requested
            else self._progress_body("Waiting for the range summarization model.")
        )
        self._safe_notification_update(
            severity="warning",
            phase=phase,
            body=body,
            cancellable=not cancel_requested,
        )

    def _finish_cancelled(self) -> None:
        self._safe_notification_completion(
            title="Summarization cancelled",
            body="Range summarization was cancelled.",
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

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    def _create_notification(self) -> None:
        body = "Preparing range summarization. Elapsed: 0 seconds."
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
            "key": NOTIFICATION_KEY,
            "severity": severity,
            "title": "Summarizing messages",
            "body": body,
            "source": {"plugin": PLUGIN_ID},
            "display": {
                "format": "text",
                "title": "Summarizing messages",
                "body": body,
                "variant": severity,
                "presentation": "banner",
                "dismissible": True,
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
        title = "Summarization interrupted" if interrupted else "Summarization failed"
        body = detail if interrupted else f"Range summarization failed: {detail}"
        with self._notification_lock:
            if not isinstance(self._notification, dict):
                return
            payload = {
                "key": NOTIFICATION_KEY,
                "severity": "warning" if interrupted else "error",
                "title": title,
                "body": body,
                "source": {"plugin": PLUGIN_ID},
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
                "source": {"plugin": PLUGIN_ID},
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
                "label": "Cancel summarization",
                "plugin": PLUGIN_ID,
                "action_id": "cancel_summarize_range",
                "action_owner": "application",
                "fixed_params": {
                    "session_id": self.session_id,
                    "operation_id": self.operation_id,
                },
            }
        ]

    def _retry_followups(self) -> list[Dict[str, Any]]:
        fixed_params: Dict[str, Any] = {
            "session_id": self.session_id,
            "start": self._start_idx,
            "end": self._end_idx,
        }
        if self._prompt:
            fixed_params["prompt"] = self._prompt
        return [
            {
                "kind": "run_action",
                "id": "retry",
                "label": "Retry",
                "plugin": PLUGIN_ID,
                "action_id": "summarize_range",
                "action_owner": "application",
                "fixed_params": fixed_params,
            }
        ]


__all__ = [
    "NOTIFICATION_KEY",
    "OPERATION_TYPE",
    "PLUGIN_ID",
    "SummarizeRangeProcess",
    "_collect_final_messages_from_stream",
    "_normalize_slice_bounds",
]
