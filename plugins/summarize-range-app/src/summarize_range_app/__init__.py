"""Application-level plugin that summarizes a range of messages.

This plugin operates at the :class:`agent_app.application_future.AgentApplication`
layer and exposes two logical actions:

* ``summarize_range`` starts a background process that summarizes a
  contiguous range of messages in a session and replaces the original range
  with a single assistant message while keeping the rest of the history
  intact. The action returns promptly with an accepted operation envelope;
  progress, cancellation, and completion are delivered through session
  notifications, mirroring the OpenAI Responses native-compaction flow.
* ``cancel_summarize_range`` requests cancellation of a running background
  summarization.

The background process respects provider/native history as far as possible
when *building* the temporary summarization session:

* It uses :meth:`agent_core.AgentCore.slice_session` with a resolved
  configuration to construct an ephemeral slice of the conversation.
* If a dedicated summarizer agent is configured, it switches agent on that
  sliced session via :meth:`AgentApplication.update_agent`.
* The summarization prompt is appended via :meth:`AgentCore.add_message` with
  the effective configuration before sending a request.

When rewriting the original session to insert the summary, the process
constructs a new :class:`agent_core.types.Session` object with adjusted
messages and drops provider-native history fields so that subsequent requests
can rebuild native state from the core message list.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from agent_app.managed_processes import get_managed_process_registry
from agent_app.operations import (
    ApplicationOperationBusyError,
    get_application_operation_service,
    session_operation_exclusivity_key,
)

from .process import (
    PLUGIN_ID,
    SummarizeRangeProcess,
    _normalize_slice_bounds,
)

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from agent_app.application_future import AgentApplication


_DEFAULT_PROMPT = (
    "Summarize the selected part of this conversation in a concise paragraph."
)


class SummarizeRangeAppPlugin:
    """Application-level plugin implementing range summarization."""

    name = "summarize_range"
    version = "1.1.0"

    def __init__(self) -> None:  # pragma: no cover - trivial initializer
        self._state: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # ApplicationPlugin protocol methods
    # ------------------------------------------------------------------

    def get_config_schema(self) -> Dict[str, Any]:
        """Return config schema keys under the top-level ``application`` key.

        All keys are flattened so configuration UIs can present them
        directly from the ``application`` section.
        """

        return {
            "summarize_range_agent_id": {
                "type": "string",
                "description": (
                    "Agent id to use for summarization (optional). When not "
                    "set, the session's agent is used."
                ),
            },
            "summarize_range_prompt": {
                "type": "string",
                "description": (
                    "Default prompt text for summarizing a selected range of "
                    "messages."
                ),
                "default": _DEFAULT_PROMPT,
            },
            "summarize_range_settings_overrides": {
                "type": "object",
                "description": (
                    "Request settings overrides (for example model or "
                    "reasoningEffort) applied to summarization requests."
                ),
            },
        }

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Return UI schema elements for the summarization action.

        The effective prompt (default or configuration-provided) is surfaced
        as the default value for the dialog's ``prompt`` field so that UIs
        can display and edit it inline.
        """

        prompt = state.get("prompt") or _DEFAULT_PROMPT

        return [
            {
                "ui_type": "session_action",
                "id": "summarize_range",
                "label": "Summarize range",
                "icon": "file-text",
                "order": 40,
                "action_id": "summarize_range",
                "action_owner": "application",
                "fixed_params": {},
                "param_map": {
                    "session_id": "$session.session_id",
                    "start": "$dialog.start",
                    "end": "$dialog.end",
                    "prompt": "$dialog.prompt",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Summarize range",
                    "message": (
                        "Python-style range (start:end). The selected messages "
                        "will be summarized into a single assistant message "
                        "in the background."
                    ),
                    "inputs": [
                        {
                            "name": "start",
                            "type": "integer",
                            "label": "Start index",
                            # Optional; when omitted, Python-style slice
                            # semantics use 0 as the default.
                            "required": False,
                            "placeholder": "e.g. 0 or -10 (leave blank for start)",
                        },
                        {
                            "name": "end",
                            "type": "integer",
                            "label": "End index",
                            # Optional; when omitted, Python-style slice
                            # semantics use the end of the list.
                            "required": False,
                            "placeholder": "e.g. 10 or -1 (leave blank for end)",
                        },
                        {
                            "name": "prompt",
                            # Custom input type interpreted by frontends as a
                            # multiline text field.
                            "type": "multiline",
                            "label": "Prompt",
                            "required": False,
                            "default": prompt,
                            "placeholder": "Optional – edit the instruction if needed",
                        },
                    ],
                },
            },
            {
                "ui_type": "message_action",
                "id": "summarize_before_message",
                "label": "Summarize messages up to here",
                "icon": "file-text",
                "order": 20,
                "action_id": "summarize_range",
                "action_owner": "application",
                "fixed_params": {"start": 0, "end_inclusive": True},
                "param_map": {
                    "session_id": "$session.session_id",
                    "end": "$message.index",
                    "prompt": "$dialog.prompt",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Summarize messages up to here",
                    "message": (
                        "The messages up to here will be summarized into a "
                        "single assistant message in the background."
                    ),
                    "inputs": [
                        {
                            "name": "prompt",
                            # Custom input type interpreted by frontends as a
                            # multiline text field.
                            "type": "multiline",
                            "label": "Prompt",
                            "required": False,
                            "default": prompt,
                            "placeholder": "Optional – edit the instruction if needed",
                        },
                    ],
                },
            },
        ]

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        application_cfg = app_config.get("application")
        if not isinstance(application_cfg, dict):
            application_cfg = {}

        agent_id_val = application_cfg.get("summarize_range_agent_id")
        prompt_val = application_cfg.get("summarize_range_prompt")
        overrides_val = application_cfg.get("summarize_range_settings_overrides")

        if isinstance(prompt_val, str) and prompt_val.strip():
            prompt = prompt_val.strip()
        else:
            prompt = _DEFAULT_PROMPT

        agent_id: Optional[str]
        if isinstance(agent_id_val, str) and agent_id_val.strip():
            agent_id = agent_id_val.strip()
        else:
            agent_id = None

        settings_overrides: Dict[str, Any]
        if isinstance(overrides_val, dict):
            settings_overrides = dict(overrides_val)
        else:
            settings_overrides = {}

        self._state = {
            "agent_id": agent_id,
            "prompt": prompt,
            "settings_overrides": settings_overrides,
        }
        return dict(self._state)

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:  # type: ignore[override]
        return [
            {
                "id": "summarize_range",
                "label": "Summarize range",
                "description": (
                    "Summarize a contiguous range of messages in a session "
                    "in the background."
                ),
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    # ``start`` and ``end`` are optional so that callers can
                    # rely on Python-style slice semantics when omitted.
                    "start": {"type": "integer", "required": False},
                    "end": {"type": "integer", "required": False},
                    "end_inclusive": {"type": "boolean", "required": False},
                    # Prompt is optional and, when omitted, falls back to the
                    # config-derived default stored in plugin state.
                    "prompt": {"type": "string", "required": False},
                },
            },
            {
                "id": "cancel_summarize_range",
                "label": "Cancel range summarization",
                "description": (
                    "Request cancellation of a running background range "
                    "summarization."
                ),
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "operation_id": {"type": "string", "required": True},
                },
            },
        ]

    def execute_action(
        self,
        app: "AgentApplication",  # type: ignore[override]
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if action_id == "summarize_range":
            return self._start(app, params, context, state)

        if action_id == "cancel_summarize_range":
            return self._cancel(app, params)

        raise ValueError(f"Unknown action_id {action_id!r} for SummarizeRangeAppPlugin")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _effective_prompt(self, params: Dict[str, Any], state: Dict[str, Any]) -> str:
        prompt_from_state = state.get("prompt") or _DEFAULT_PROMPT
        prompt_param = params.get("prompt")
        if isinstance(prompt_param, str) and prompt_param.strip():
            return prompt_param.strip()
        return str(prompt_from_state)

    def _start(
        self,
        app: "AgentApplication",
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        if app.get_selected_session_snapshot(session_id) is not None:
            raise RuntimeError(f"Session {session_id!r} is viewing a readonly snapshot")

        # Inputs have already been validated by AgentApplication for primitive
        # types. ``start`` and ``end`` are optional; when omitted they are
        # treated as ``None`` and interpreted via Python-style slice
        # semantics.
        start_raw = params.get("start")
        end_raw = params.get("end")
        end_inclusive = params.get("end_inclusive", False)
        start_int = (
            start_raw
            if isinstance(start_raw, int) and not isinstance(start_raw, bool)
            else None
        )
        end_int = (
            end_raw
            if isinstance(end_raw, int) and not isinstance(end_raw, bool)
            else None
        )

        effective_prompt = self._effective_prompt(params, state)

        with app.acquire_session_lock(session_id):
            loaded = app.load_session(session_id)
            if loaded is None:
                raise KeyError(f"Session {session_id!r} not found")
            core, base_config, session = loaded
            baseline_file_state = app.get_session_file_state(session_id)

        message_count = len(session.messages)
        start_idx, end_idx = _normalize_slice_bounds(message_count, start_int, end_int)
        if end_inclusive and end_raw is not None:
            end_idx = min(end_idx + 1, message_count)

        operation_id = f"{PLUGIN_ID}:{uuid.uuid4().hex}"
        operations = get_application_operation_service(app.get_runtime_store())
        try:
            operation = operations.reserve(
                operation_id=operation_id,
                owner_id=PLUGIN_ID,
                session_id=session_id,
                exclusivity_keys=(session_operation_exclusivity_key(session_id),),
            )
        except ApplicationOperationBusyError as exc:
            return {
                "status": "error",
                "error_type": "session_busy",
                "message": "The session is busy with another operation.",
                "operation": exc.current.to_dict(),
            }

        registry = get_managed_process_registry(app.get_runtime_store())
        process = SummarizeRangeProcess(
            app=app,
            registry=registry,
            process_id=operation_id,
            operation=operation,
            session_id=session_id,
            core=core,
            base_config=base_config,
            session=session,
            baseline_file_state=baseline_file_state,
            start_idx=start_idx,
            end_idx=end_idx,
            prompt=effective_prompt,
            agent_id=state.get("agent_id"),
            settings_overrides=state.get("settings_overrides"),
            action_context=context,
        )
        try:
            registry.start(operation_id, process)
        except Exception:
            operation.release()
            raise

        return {
            "status": "ok",
            "operation_status": "accepted",
            "message": "Range summarization started.",
            "operation_id": operation_id,
            "notification_id": process.notification_id,
        }

    def _cancel(
        self, app: "AgentApplication", params: Dict[str, Any]
    ) -> Dict[str, Any]:
        session_id = params["session_id"]
        operation_id = params["operation_id"]
        operations = get_application_operation_service(app.get_runtime_store())
        current = operations.get(operation_id)
        if (
            current is None
            or current.owner_id != PLUGIN_ID
            or current.session_id != session_id
        ):
            return {
                "status": "error",
                "error_type": "operation_not_found",
                "message": "The summarization operation is no longer active.",
            }
        registry = get_managed_process_registry(app.get_runtime_store())
        process = registry.get(operation_id)
        if not isinstance(process, SummarizeRangeProcess):
            return {
                "status": "error",
                "error_type": "operation_not_found",
                "message": "The summarization process is no longer active.",
            }
        if not process.matches(
            session_id=session_id,
            operation_id=operation_id,
        ):
            return {
                "status": "error",
                "error_type": "stale_operation",
                "message": "The summarization action no longer matches this session.",
            }
        if not process.request_cancel():
            return {
                "status": "error",
                "error_type": "operation_not_cancellable",
                "message": "The summarization operation can no longer be cancelled.",
            }
        return {
            "status": "ok",
            "operation_status": "cancellation_requested",
            "message": "Summarization cancellation requested.",
        }


__all__ = ["SummarizeRangeAppPlugin"]
