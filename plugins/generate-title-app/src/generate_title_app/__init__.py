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

import uuid

from agent_core import Session

from agent_app.config import resolve_request_config

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from agent_app.application_future import AgentApplication


_DEFAULT_PROMPT = (
    "Generate a short (max 8 words) title for this conversation. "
    "If appropriate, also provide a one-line plain-text description on a second line."
)


def _collect_final_messages_from_stream(
    core: Any,
    session: Session,
    config: Dict[str, Any],
    *,
    request_id: str | None = None,
) -> List[Dict[str, Any]]:
    """Run an internal request via the streaming path and return final messages."""

    final_messages: List[Dict[str, Any]] = []
    for event in core.send_request_stream(session, config, request_id=request_id):
        if event.get("type") != "final":
            continue
        raw_messages = event.get("messages")
        if isinstance(raw_messages, list):
            final_messages = raw_messages
    return final_messages


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
                    "generating a title. When omitted or set to a value "
                    "less than or equal to zero, all messages are "
                    "included."
                ),
                "default": 0,
            },
            "generate_title_settings_overrides": {
                "type": "object",
                "description": (
                    "Request settings overrides (for example model or "
                    "reasoningEffort) applied to title generation requests."
                ),
            },
            "generate_title_enable_description": {
                "type": "boolean",
                "description": (
                    "When true, the plugin expects the model to return a "
                    "two-line response (title on the first line, optional "
                    "description on the second) and stores both title and "
                    "description metadata."
                ),
                "default": True,
            },
            "generate_title_description_metadata_key": {
                "type": "string",
                "description": (
                    "Metadata key used for storing generated descriptions. "
                    "When not set, the plugin reuses the application's "
                    "session_subtitle_metadata_key or falls back to "
                    "'subtitle'."
                ),
            },
            "generate_title_system_message": {
                "type": "string",
                "description": (
                    "Optional system message used for title generation "
                    "requests. When set, this replaces any existing system "
                    "messages in the ephemeral title-generation session so "
                    "that the model can be instructed (for example to "
                    "respond with exactly two lines)."
                ),
            },
            "generate_title_debug_save_session": {
                "type": "boolean",
                "description": (
                    "When true, the plugin saves the ephemeral "
                    "title-generation session to storage for debugging."
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
        enable_desc_val = application_cfg.get("generate_title_enable_description")
        desc_key_val = application_cfg.get("generate_title_description_metadata_key")
        system_message_val = application_cfg.get("generate_title_system_message")
        debug_save_val = application_cfg.get("generate_title_debug_save_session")

        if isinstance(prompt_val, str) and prompt_val.strip():
            prompt_template = prompt_val.strip()
        else:
            prompt_template = _DEFAULT_PROMPT

        agent_id: Optional[str]
        if isinstance(agent_id_val, str) and agent_id_val.strip():
            agent_id = agent_id_val.strip()
        else:
            agent_id = None

        if isinstance(max_messages_val, int) and max_messages_val > 0:
            max_messages: Optional[int] = max_messages_val
        else:
            # ``None`` means "no limit" – the full conversation (minus any
            # provider-native slicing decisions) is available to the title
            # generation request.
            max_messages = None

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

        # Decide whether descriptions are enabled and which metadata key to
        # use when storing them. When no explicit description key is
        # configured, reuse the application's subtitle metadata key when
        # available so that title/description remain aligned.
        if isinstance(enable_desc_val, bool):
            enable_description = enable_desc_val
        else:
            enable_description = True

        if isinstance(desc_key_val, str) and desc_key_val.strip():
            description_metadata_key = desc_key_val.strip()
        else:
            raw_subtitle = application_cfg.get("session_subtitle_metadata_key")
            if isinstance(raw_subtitle, str) and raw_subtitle.strip():
                description_metadata_key = raw_subtitle.strip()
            else:
                description_metadata_key = "subtitle"

        if isinstance(system_message_val, str) and system_message_val.strip():
            system_message = system_message_val.strip()
        else:
            system_message = None

        if isinstance(debug_save_val, bool):
            debug_save_session = debug_save_val
        else:
            debug_save_session = False

        self._state = {
            "agent_id": agent_id,
            "prompt_template": prompt_template,
            "max_messages": max_messages,
            "settings_overrides": settings_overrides,
            "metadata_key": metadata_key,
            "enable_description": enable_description,
            "description_metadata_key": description_metadata_key,
            "system_message": system_message,
            "debug_save_session": debug_save_session,
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
            max_messages: Optional[int] = max_messages_val
        else:
            max_messages = None

        system_prefix_end = 0
        for msg in messages:
            if msg.role == "system":
                system_prefix_end += 1
            else:
                break

        if max_messages is None:
            # No explicit limit: include the full conversation.
            keep_indices = set(range(message_count))
        else:
            # When a limit is configured, keep the *first* ``max_messages``
            # messages after any leading system prefix, not the last.
            if message_count <= system_prefix_end:
                end_recent = system_prefix_end
            else:
                end_recent = min(message_count, system_prefix_end + max_messages)

            keep_indices = set(range(end_recent))
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
        request_overrides: Dict[str, Any] = {
            "disable_all_tools": True,
            **combined_overrides,
        }
        config_for_add = resolve_request_config(base_config_title, combined_overrides)

        # Optionally replace any existing system messages in the
        # title-generation session with a dedicated system message from
        # configuration. This keeps title/description runs tightly
        # constrained (for example, to exactly two lines) without affecting
        # the original session. We use :meth:`AgentCore.modify_message` so
        # that provider-native history is preserved or cleanly updated when
        # possible.
        system_message_text = state.get("system_message")
        if isinstance(system_message_text, str) and system_message_text.strip():
            new_text = system_message_text.strip()
            # Try to modify the first existing system message; if none are
            # present, fall back to appending a new system message. Both
            # operations go through the core so that native history is kept
            # consistent.
            system_index: Optional[int] = None
            for idx, msg in enumerate(session_for_title.messages):
                if msg.role == "system":
                    system_index = idx
                    break

            if system_index is not None:
                session_for_title = core_title.modify_message(
                    session_for_title,
                    system_index,
                    new_text,
                    config_for_add,
                )
            else:
                session_for_title = core_title.add_message(
                    session_for_title,
                    "system",
                    new_text,
                    metadata=None,
                    config=config_for_add,
                )

        prompt_template = state.get("prompt_template") or _DEFAULT_PROMPT

        session_with_prompt = core_title.add_message(
            session_for_title,
            "user",
            prompt_template,
            metadata=None,
            config=config_for_add,
        )

        # Optionally persist the ephemeral title-generation session for
        # debugging so that it can be inspected via the normal sessions
        # list APIs. This is controlled purely by configuration and does
        # not affect normal flows.
        if state.get("debug_save_session"):
            debug_metadata: Dict[str, Any]
            if isinstance(session_with_prompt.metadata, dict):
                debug_metadata = dict(session_with_prompt.metadata)
            else:
                debug_metadata = {}

            debug_info = debug_metadata.get("debug")
            if isinstance(debug_info, dict):
                debug_meta = dict(debug_info)
            else:
                debug_meta = {}
            debug_meta.setdefault("plugin", "generate_title")
            debug_meta.setdefault("kind", "title_generation_ephemeral")
            debug_meta.setdefault("source_session_id", session_id)
            debug_metadata["debug"] = debug_meta

            debug_session_id = f"{session_id}-title-debug-{uuid.uuid4().hex[:8]}"
            debug_session = Session(
                session_id=debug_session_id,
                messages=session_with_prompt.messages,
                metadata=debug_metadata,
            )
            app.save_session(debug_session)

        # Run the title-generation request without persisting the temporary
        # title-generation session. We only need the model output here.
        try:
            core_title, _base_title, session_with_prompt, request_config, rid = (
                app.prepare_tools_for_session(
                    core_title,
                    session_with_prompt,
                    base_config_title,
                    request_overrides,
                )
            )
            last_final_messages = _collect_final_messages_from_stream(
                core_title,
                session_with_prompt,
                request_config,
                request_id=rid,
            )
        except Exception as exc:  # pragma: no cover - defensive
            return {
                "status": "error",
                "error_type": "plugin_error",
                "message": str(exc),
            }

        title_text: Optional[str] = None
        description_text: Optional[str] = None
        enable_description = bool(state.get("enable_description", True))
        if last_final_messages:
            for msg in reversed(last_final_messages):
                if not isinstance(msg, dict):
                    continue
                if msg.get("role") != "assistant":
                    continue
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
                    if not lines:
                        continue
                    if enable_description:
                        title_text = lines[0]
                        if len(lines) > 1:
                            description_text = lines[1]
                    else:
                        title_text = lines[0]
                    break

        if not title_text:
            return {
                "status": "error",
                "error_type": "plugin_error",
                "message": "Title generation failed (no assistant reply).",
            }

        metadata_key = state.get("metadata_key") or "title"
        description_metadata_key = state.get("description_metadata_key") or "subtitle"
        enable_description = bool(state.get("enable_description", True))

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
            if enable_description and description_text:
                new_metadata[description_metadata_key] = description_text

            new_session = Session(
                session_id=session_latest.session_id,
                messages=session_latest.messages,
                metadata=new_metadata,
            )
            app.save_session(new_session)

            fields = [metadata_key]
            if enable_description and description_text:
                fields.append(description_metadata_key)

            stored = app.publish_event(
                {
                    "type": "session_metadata_updated",
                    "session_id": new_session.session_id,
                    "fields": fields,
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
            "ui_effects": {},
            "message": "Generated title for session.",
        }


__all__ = ["GenerateTitleAppPlugin"]
