from __future__ import annotations

"""Application-level plugin that generates titles for sessions.

This plugin operates at the :class:`agent_app.application_future.AgentApplication`
layer and exposes a single logical action, ``generate_title_for_session``.
The action runs a model call over a subset of the session's messages and
writes the resulting assistant content into a configurable metadata field
used as the session title.

The implementation mirrors :mod:`plugins.summarize_range_app` in how it:

* uses :meth:`agent_core.AgentCore.slice_session` with a resolved
  configuration to construct an ephemeral slice of the conversation,
* optionally switches to a dedicated agent via
  :meth:`AgentApplication.update_agent`, and
* appends a prompt via :meth:`AgentCore.add_message` before calling
  :meth:`AgentApplication.send_request`.

Unlike the summarization plugin, this plugin never mutates the session
messages; it only updates session metadata to add or replace a title
field and publishes a lightweight ``session_metadata_updated`` event.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from agent_core import Session

from agent_app.config import resolve_request_config

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from agent_app.application_future import AgentApplication


_DEFAULT_PROMPT = "Generate a short (max 8 words) title for this conversation."


class GenerateTitleAppPlugin:
    """Application-level plugin for generating session titles."""

    name = "generate_title"
    version = "1.0.0"

    def __init__(self) -> None:  # pragma: no cover - trivial initializer
        self._state: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # ApplicationPlugin protocol methods
    # ------------------------------------------------------------------

    def get_config_schema(self) -> Dict[str, Any]:
        """Return config schema keys under the top-level ``application`` key."""

        return {
            "generate_title_agent_id": {
                "type": "string",
                "description": (
                    "Agent id to use for title generation (optional). When "
                    "not set, the session's agent is used."
                ),
            },
            "generate_title_prompt_template": {
                "type": "string",
                "description": (
                    "Prompt template used when asking the model to generate "
                    "a title for a session."
                ),
                "default": _DEFAULT_PROMPT,
            },
            "generate_title_max_messages": {
                "type": "integer",
                "description": (
                    "Maximum number of recent messages to include when "
                    "generating a title."
                ),
                "default": 50,
            },
            "generate_title_settings_overrides": {
                "type": "object",
                "description": (
                    "Request settings overrides (for example model or "
                    "reasoningEffort) applied to title generation requests."
                ),
            },
        }

    def get_ui_elements(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return UI schema elements contributed by this plugin.

        The plugin exposes two actions (session-list and session-view) that
        both invoke ``generate_title_for_session`` with only a session id.
        Frontends remain plugin-agnostic and simply render these entries
        based on their ``ui_type``.
        """

        return [
            {
                "ui_type": "session_list_action",
                "id": "generate_title_from_list",
                "label": "Generate title",
                "icon": "sparkles",
                "order": 6,
                "action_id": "generate_title_for_session",
                "fixed_params": {"source": "session_list"},
                "param_map": {
                    "session_id": "$session.session_id",
                },
                "dialog": {
                    "kind": "none",
                },
            },
            {
                "ui_type": "session_action",
                "id": "generate_title_from_view",
                "label": "Generate title",
                "icon": "sparkles",
                "order": 16,
                "action_id": "generate_title_for_session",
                "fixed_params": {"source": "session_view"},
                "param_map": {
                    "session_id": "$session.session_id",
                },
                "dialog": {
                    "kind": "none",
                },
            },
        ]

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        application_cfg = app_config.get("application")
        if not isinstance(application_cfg, dict):
            application_cfg = {}

        agent_id_val = application_cfg.get("generate_title_agent_id")
        prompt_val = application_cfg.get("generate_title_prompt_template")
        max_messages_val = application_cfg.get("generate_title_max_messages")
        overrides_val = application_cfg.get("generate_title_settings_overrides")

        if isinstance(prompt_val, str) and prompt_val.strip():
            prompt_template = prompt_val.strip()
        else:
            prompt_template = _DEFAULT_PROMPT

        agent_id: Optional[str]
        if isinstance(agent_id_val, str) and agent_id_val.strip():
            agent_id = agent_id_val.strip()
        else:
            agent_id = None

        max_messages: int
        if isinstance(max_messages_val, int) and max_messages_val > 0:
            max_messages = max_messages_val
        else:
            max_messages = 50

        settings_overrides: Dict[str, Any]
        if isinstance(overrides_val, dict):
            settings_overrides = dict(overrides_val)
        else:
            settings_overrides = {}

        # Reuse the metadata key configured for titles when available. This
        # keeps GenerateTitleAppPlugin aligned with SessionTitleAppPlugin.
        raw_field = application_cfg.get("session_title_metadata_key")
        if isinstance(raw_field, str) and raw_field.strip():
            metadata_key = raw_field.strip()
        else:
            metadata_key = "title"

        self._state = {
            "agent_id": agent_id,
            "prompt_template": prompt_template,
            "max_messages": max_messages,
            "settings_overrides": settings_overrides,
            "metadata_key": metadata_key,
        }
        return dict(self._state)

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:  # type: ignore[override]
        return [
            {
                "id": "generate_title_for_session",
                "label": "Generate title for session",
                "description": "Generate a short title based on recent messages.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "source": {"type": "string", "required": False},
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
        if action_id == "generate_title_for_session":
            return self._do_generate_title_for_session(app, params, state)

        raise ValueError(f"Unknown action_id {action_id!r} for GenerateTitleAppPlugin")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _do_generate_title_for_session(
        self,
        app: "AgentApplication",
        params: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        ctx = app.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")

        core_orig, base_config_orig, session_orig = ctx

        messages = session_orig.messages
        message_count = len(messages)

        # Determine how many messages to keep from the tail of the
        # conversation while always preserving a leading system prefix if
        # present.
        max_messages_val = state.get("max_messages")
        if isinstance(max_messages_val, int) and max_messages_val > 0:
            max_messages = max_messages_val
        else:
            max_messages = 50

        system_prefix_end = 0
        for msg in messages:
            if msg.role == "system":
                system_prefix_end += 1
            else:
                break

        if message_count <= system_prefix_end:
            start_recent = system_prefix_end
        else:
            start_recent = max(system_prefix_end, message_count - max_messages)

        keep_indices = set(range(system_prefix_end)) | set(
            range(start_recent, message_count)
        )
        all_indices = set(range(message_count))
        remove_indices = sorted(i for i in all_indices if i not in keep_indices)

        # Build a config for slicing that respects any per-session overrides.
        metadata = session_orig.metadata if isinstance(session_orig.metadata, dict) else {}
        md_overrides_val = metadata.get("overrides")
        md_overrides: Dict[str, Any] = (
            md_overrides_val if isinstance(md_overrides_val, dict) else {}
        )
        slice_config = resolve_request_config(base_config_orig, md_overrides)

        sliced_for_title = core_orig.slice_session(
            session_orig,
            slice_config,
            remove_indices=remove_indices,
        )

        # Choose agent: either a dedicated one from config or the current
        # session agent.
        agent_id_cfg = state.get("agent_id")
        md_sliced = (
            sliced_for_title.metadata
            if isinstance(sliced_for_title.metadata, dict)
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
            core_title = core_orig
            base_config_title = base_config_orig
            session_for_title = sliced_for_title
        else:
            core_title, base_config_title, session_for_title = app.update_agent(
                target_agent_id,
                sliced_for_title,
            )

        # Build overrides for the title generation request: per-session
        # overrides plus any generate_title-specific settings from
        # configuration.
        md2 = (
            session_for_title.metadata
            if isinstance(session_for_title.metadata, dict)
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
        config_for_add = resolve_request_config(base_config_title, combined_overrides)

        prompt_template = state.get("prompt_template") or _DEFAULT_PROMPT

        session_with_prompt = core_title.add_message(
            session_for_title,
            "user",
            prompt_template,
            metadata=None,
            config=config_for_add,
        )

        # Run the title-generation request using AgentApplication.send_request.
        try:
            events = app.send_request(
                core_title,
                session_with_prompt,
                base_config_title,
                combined_overrides,
                stream=False,
            )
            last_final_messages: Optional[List[Dict[str, Any]]] = None
            for ev in events:
                if not isinstance(ev, dict):
                    continue
                if ev.get("type") == "final":
                    msgs = ev.get("messages") or []
                    if isinstance(msgs, list):
                        last_final_messages = msgs
        except Exception as exc:  # pragma: no cover - defensive
            return {
                "status": "error",
                "error_type": "plugin_error",
                "message": str(exc),
            }

        title_text: Optional[str] = None
        if last_final_messages:
            for msg in reversed(last_final_messages):
                if not isinstance(msg, dict):
                    continue
                if msg.get("role") != "assistant":
                    continue
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    # Use the first line as the title; providers can still
                    # return longer content if desired.
                    title_text = content.strip().splitlines()[0]
                    break

        if not title_text:
            return {
                "status": "error",
                "error_type": "plugin_error",
                "message": "Title generation failed (no assistant reply).",
            }

        metadata_key = state.get("metadata_key") or "title"

        # Apply the title to the original session under a lock.
        with app.acquire_session_lock(session_id):
            ctx_latest = app.load_session(session_id)
            if ctx_latest is None:
                raise KeyError(f"Session {session_id!r} not found")

            _core_latest, _base_latest, session_latest = ctx_latest
            md_latest = (
                session_latest.metadata
                if isinstance(session_latest.metadata, dict)
                else {}
            )

            new_metadata = {**md_latest, metadata_key: title_text}

            new_session = Session(
                session_id=session_latest.session_id,
                messages=session_latest.messages,
                metadata=new_metadata,
            )
            app.save_session(new_session)

            stored = app.publish_event(
                {
                    "type": "session_metadata_updated",
                    "session_id": new_session.session_id,
                    "fields": [metadata_key],
                }
            )

            try:
                app.record_checkpoint(new_session.session_id, stored.get("request_id"))
            except Exception:  # pragma: no cover - defensive
                pass

        return {
            "created_session_ids": [],
            "updated_session_ids": [session_id],
            "deleted_session_ids": [],
            "message": "Generated title for session.",
        }


__all__ = ["GenerateTitleAppPlugin"]
