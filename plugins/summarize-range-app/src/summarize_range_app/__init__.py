"""Application-level plugin that summarizes a range of messages.

This plugin operates at the :class:`agent_app.application_future.AgentApplication`
layer and exposes a single logical action, ``summarize_range``. The action
summarizes a contiguous range of messages in a session and replaces the
original range with a single assistant message while keeping the rest of the
history intact.

The implementation is designed to respect provider/native history as far as
possible when *building* the temporary summarization session:

* It uses :meth:`agent_core.AgentCore.slice_session` with a resolved
  configuration to construct an ephemeral slice of the conversation.
* If a dedicated summarizer agent is configured, it switches agent on that
  sliced session via :meth:`AgentApplication.update_agent`.
* The summarization prompt is appended via :meth:`AgentCore.add_message` with
  the effective configuration before sending a request.

When rewriting the original session to insert the summary, the plugin
constructs a new :class:`agent_core.types.Session` object with adjusted
messages and drops provider-native history fields so that subsequent requests
can rebuild native state from the core message list.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from agent_core import Message, Session

from agent_app.config import resolve_request_config

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from agent_app.application_future import AgentApplication


def _collect_final_messages_from_stream(
    core: Any,
    session: Session,
    config: Dict[str, Any],
    *,
    request_id: str | None = None,
    context: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Run an internal request via the streaming path and return final messages."""

    final_messages: List[Dict[str, Any]] = []
    for event in core.send_request_stream(session, config, request_id=request_id, context=context):
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


_DEFAULT_PROMPT = (
    "Summarize the selected part of this conversation in a concise paragraph."
)


class SummarizeRangeAppPlugin:
    """Application-level plugin implementing range summarization."""

    name = "summarize_range"
    version = "1.0.0"

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
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
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
                        "will be summarized into a single assistant message."
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
                        "The messages up to here will be summarized into a single assistant message."
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
                "description": "Summarize a contiguous range of messages in a session.",
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
            }
        ]

    def execute_action(
        self,
        app: "AgentApplication",  # type: ignore[override]
        action_id: str,
        params: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if action_id == "summarize_range":
            return self._do_summarize_range(app, params, state)

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

    def _clone_message_without_native_indices(self, message: Message) -> Message:
        data = message.to_dict()
        md = data.get("metadata") or {}
        if not isinstance(md, dict):
            md = {}
        md.pop("native_indices", None)
        role = data.get("role", "user")
        content = data.get("content", "")
        if md:
            return Message(role=role, content=content, metadata=md)
        return Message(role=role, content=content, metadata=None)

    def _replace_range_with_summary(
        self,
        session: Session,
        start_idx: int,
        end_idx: int,
        summary_text: str,
    ) -> Session:
        # Legacy helper retained for backwards compatibility; no longer used.
        # The new implementation applies range replacement via AgentCore
        # slice_session and add_message to keep provider-native history
        # consistent. This stub is kept to avoid breaking external imports.
        raise NotImplementedError("_replace_range_with_summary is no longer used")

    def _do_summarize_range(
        self,
        app: "AgentApplication",
        params: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        # Inputs have already been validated by AgentApplication for primitive
        # types. ``start`` and ``end`` are optional; when omitted they are
        # treated as ``None`` and interpreted via Python-style slice
        # semantics.
        start_raw = params.get("start")
        end_raw = params.get("end")
        end_inclusive = params.get("end_inclusive", False)
        start_int = start_raw if isinstance(start_raw, int) else None
        end_int = end_raw if isinstance(end_raw, int) else None

        effective_prompt = self._effective_prompt(params, state)

        with app.acquire_session_lock(session_id):
            ctx = app.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")
            core_orig, base_config_orig, session_orig = ctx
            baseline_file_state = app.get_session_file_state(session_id)

        message_count = len(session_orig.messages)
        start_idx, end_idx = _normalize_slice_bounds(message_count, start_int, end_int)
        if end_inclusive and end_raw is not None:
            end_idx = min(end_idx + 1, message_count)

        # Compute a slice that always keeps leading system messages as context.
        system_prefix_end = 0
        for msg in session_orig.messages:
            if msg.role == "system":
                system_prefix_end += 1
            else:
                break

        keep_indices = set(range(system_prefix_end)) | set(range(start_idx, end_idx))
        all_indices = set(range(message_count))
        remove_indices = sorted(i for i in all_indices if i not in keep_indices)

        # Build a config for slicing that respects any per-session overrides.
        metadata = session_orig.metadata if isinstance(session_orig.metadata, dict) else {}
        md_overrides_val = metadata.get("overrides")
        md_overrides: Dict[str, Any] = (
            md_overrides_val if isinstance(md_overrides_val, dict) else {}
        )
        slice_config = resolve_request_config(base_config_orig, md_overrides)

        sliced_for_sum = core_orig.slice_session(
            session_orig,
            slice_config,
            remove_indices=remove_indices,
        )

        # Choose summarizer agent: either a dedicated one from config or the
        # current session agent.
        agent_id_cfg = state.get("agent_id")
        md_sliced = (
            sliced_for_sum.metadata
            if isinstance(sliced_for_sum.metadata, dict)
            else {}
        )
        session_agent_id = md_sliced.get("agent_id")
        if not isinstance(session_agent_id, str) or not session_agent_id:
            raise RuntimeError("session metadata must contain non-empty 'agent_id'")

        if isinstance(agent_id_cfg, str) and agent_id_cfg.strip():
            target_agent_id = agent_id_cfg.strip()
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
        md2 = (
            session_for_sum.metadata
            if isinstance(session_for_sum.metadata, dict)
            else {}
        )
        md_overrides2_val = md2.get("overrides")
        md_overrides2: Dict[str, Any] = (
            md_overrides2_val if isinstance(md_overrides2_val, dict) else {}
        )

        cfg_overrides_val = state.get("settings_overrides")
        cfg_overrides: Dict[str, Any] = (
            cfg_overrides_val if isinstance(cfg_overrides_val, dict) else {}
        )

        combined_overrides: Dict[str, Any] = {**md_overrides2, **cfg_overrides}
        request_overrides: Dict[str, Any] = {
            "disable_all_tools": True,
            **combined_overrides,
        }
        config_for_add = resolve_request_config(base_config_sum, combined_overrides)

        # Append the prompt as a user message using the summarizer core and
        # configuration so that any provider-native history stays consistent.
        session_with_prompt = core_sum.add_message(
            session_for_sum,
            "user",
            effective_prompt,
            metadata=None,
            config=config_for_add,
        )

        # Run the summarization request without persisting the temporary
        # summarizer session. We only need the model output here.
        try:
            core_sum, _base_sum, session_with_prompt, request_config, rid = (
                app.prepare_tools_for_session(
                    core_sum,
                    session_with_prompt,
                    base_config_sum,
                    request_overrides,
                )
            )
            handoff_context = app._context.build_core_handoff_context(
                base_config=base_config_sum,
                config=request_config,
            )
            last_final_messages = _collect_final_messages_from_stream(
                core_sum,
                session_with_prompt,
                request_config,
                request_id=rid,
                context=handoff_context,
            )
        except Exception as exc:  # pragma: no cover - defensive
            return {
                "status": "error",
                "error_type": "plugin_error",
                "message": str(exc),
            }

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
            return {
                "status": "error",
                "error_type": "plugin_error",
                "message": "Summarization failed (no assistant reply).",
            }

        # Apply the summary to the original session snapshot and reconcile
        # when saving so concurrent message edits fail instead of being
        # silently rewritten onto a later session version.
        edit_config = resolve_request_config(base_config_orig, md_overrides)
        remove_indices = list(range(start_idx, end_idx))
        session_after_delete = core_orig.slice_session(
            session_orig,
            edit_config,
            remove_indices=remove_indices,
        )

        insert_after = start_idx - 1
        summary_metadata: Dict[str, Any] = {
            "summarized_range": {
                "start_index": start_idx,
                "end_index": end_idx,
            }
        }

        new_session = core_orig.add_message(
            session_after_delete,
            "assistant",
            summary_text,
            metadata=summary_metadata,
            config=edit_config,
            after_index=insert_after,
        )
        new_session = app.save_session(
            new_session,
            reconcile=True,
            baseline_session=session_orig,
            baseline_file_state=baseline_file_state,
            conflict_prefix="Concurrent session modification detected while summarizing messages; ",
            backup_on_conflict=True,
            acquire_lock=True,
        )

        stored = app.publish_event(
            {
                "type": "range_summarized",
                "session_id": new_session.session_id,
                "start_index": start_idx,
                "end_index": end_idx,
            }
        )

        try:
            app.record_checkpoint(new_session.session_id, stored.get("request_id"))
        except Exception:  # pragma: no cover - defensive
            pass

        return {
            "mutations": {
                "created_session_ids": [],
                "updated_session_ids": [session_id],
                "deleted_session_ids": [],
            },
            "ui_effects": {
                "reload_session_ids": [session_id],
            },
            "message": "Summarized messages in the selected range.",
        }


__all__ = ["SummarizeRangeAppPlugin"]
