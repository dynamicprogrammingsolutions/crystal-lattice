"""Application-level plugin providing basic session actions.

This plugin implements copy/fork/delete operations at the application layer
on top of :class:`agent_app.application_future.AgentApplication`.

It exposes logical actions suitable for use via the generic ``POST /actions``
endpoint and contributes UI schema elements that higher-level frontends can
use to render buttons and menus.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from agent_core import Session

from agent_app.config import resolve_request_config

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from agent_app.application_future import AgentApplication


def _normalize_index(raw_index: int, message_count: int) -> int:
    """Normalize a Python-style index for a given message count.

    Mirrors the semantics used by the HTTP server and terminal
    application: negative indices are relative to the end and
    ``IndexError`` is raised when the resulting index is out of range.
    """

    idx = raw_index
    if idx < 0:
        idx = message_count + idx
    if idx < 0 or idx >= message_count:
        raise IndexError("message index out of range")
    return idx


def _normalize_slice_bounds(
    message_count: int,
    start: Optional[int],
    end: Optional[int],
) -> tuple[int, int]:
    """Return concrete ``(start_idx, end_idx)`` for slice-like bounds.

    Semantics match the helper used by the HTTP server:

    - ``start`` and ``end`` follow Python slice rules, including support
      for ``None`` and negative indices.
    - Indices are clamped to ``[0, message_count]``.
    - ``ValueError`` is raised when the range selects no messages.
    """

    def _bound(value: Optional[int], default: int) -> int:
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


def _deletion_snapshot_reason(
    *,
    concrete_indices: List[int],
    has_indices: bool,
    has_start_end: bool,
    start_idx: int,
    end_idx: int,
    raw_start: Optional[int],
    raw_end: Optional[int],
) -> str:
    if has_indices:
        if len(concrete_indices) == 1:
            return f"Before deleting message [{concrete_indices[0]}]"
        joined = ", ".join(str(index) for index in concrete_indices)
        return f"Before deleting messages [{joined}]"

    if has_start_end:
        start_text = "" if raw_start is None else str(start_idx)
        end_text = "" if raw_end is None else str(end_idx)
        return f"Before deleting messages [{start_text}:{end_text}]"

    return f"Before deleting messages [{start_idx}:]"


class SessionActionsAppPlugin:
    """Application-level plugin implementing copy/fork/delete operations."""

    name = "session_actions"
    version = "1.0.0"

    def __init__(self) -> None:
        self._state: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # ApplicationPlugin protocol methods
    # ------------------------------------------------------------------

    def get_config_schema(self) -> Dict[str, Any]:
        # Minimal schema describing the allow_delete toggle; applications
        # may surface this in configuration UIs.
        return {
            "allow_delete": {
                "type": "boolean",
                "default": True,
                "description": "Allow deleting entire sessions via actions.",
            }
        }

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        # A small set of UI elements covering common flows. Frontends
        # may choose to ignore or extend these definitions.
        return [
            {
                "ui_type": "session_list_action",
                "id": "copy_session_from_list",
                "label": "Copy",
                "icon": "copy",
                "order": 10,
                "action_id": "copy_session",
                "fixed_params": {"source": "session_list"},
                "param_map": {"session_id": "$session.session_id"},
                "dialog": {"kind": "none"},
            },
            {
                "ui_type": "session_list_action",
                "id": "delete_session_from_list",
                "label": "Delete session",
                "icon": "trash-2",
                "order": 20,
                "action_id": "delete_session",
                "fixed_params": {"source": "session_list"},
                "param_map": {"session_id": "$session.session_id"},
                "dialog": {
                    "kind": "confirm",
                    "title": "Delete session",
                    "message": "Delete this session and its messages?",
                },
            },
            {
                "ui_type": "session_action",
                "id": "copy_session_from_view",
                "label": "Copy session",
                "icon": "copy",
                "order": 10,
                "action_id": "copy_session",
                "fixed_params": {"source": "session_view"},
                "param_map": {"session_id": "$session.session_id"},
                "dialog": {"kind": "none"},
            },
            {
                "ui_type": "message_action",
                "id": "fork_session_at_message",
                "label": "Fork here",
                "icon": "git-branch",
                "order": 20,
                "action_id": "fork_session_at",
                "fixed_params": {"source": "message_menu"},
                "param_map": {
                    "session_id": "$session.session_id",
                    "index": "$message.index",
                },
                "dialog": {"kind": "none"},
            },
            {
                "ui_type": "message_action",
                "id": "delete_single_message",
                "label": "Delete",
                "icon": "trash-2",
                "order": 30,
                "action_id": "delete_messages",
                "fixed_params": {},
                "param_map": {
                    "session_id": "$session.session_id",
                    "indices": "$message.index",
                },
                "dialog": {
                    "kind": "confirm",
                    "title": "Delete message",
                    "message": "Delete this message?",
                },
            },
            {
                "ui_type": "message_action",
                "id": "delete_from_here",
                "label": "Delete from here",
                "icon": "trash-2",
                "order": 35,
                "action_id": "delete_messages",
                "fixed_params": {},
                "param_map": {
                    "session_id": "$session.session_id",
                    "start": "$message.index",
                },
                "dialog": {
                    "kind": "confirm",
                    "title": "Delete from here",
                    "message": "Delete this message and all later messages?",
                },
            },
            {
                "ui_type": "session_action",
                "id": "delete_last_messages",
                "label": "Delete messages",
                "icon": "trash-2",
                "order": 30,
                "action_id": "delete_messages",
                "fixed_params": {"source": "session_view"},
                "param_map": {
                    "session_id": "$session.session_id",
                    "start": "$dialog.start",
                    "end": "$dialog.end",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Delete messages",
                    "message": (
                        "Python-style range (start:end). Messages in this range "
                        "will be removed."
                    ),
                    "inputs": [
                        {
                            "name": "start",
                            "type": "integer",
                            "label": "Start index",
                            "required": False,
                            "placeholder": "e.g. 0 or -10",
                        },
                        {
                            "name": "end",
                            "type": "integer",
                            "label": "End index (optional)",
                            "required": False,
                            "placeholder": "leave blank for end",
                        },
                    ],
                },
            },
        ]

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        application_cfg = app_config.get("application")
        if not isinstance(application_cfg, dict):
            application_cfg = {}

        raw_sa = application_cfg.get("session_actions")
        sa_cfg = raw_sa if isinstance(raw_sa, dict) else {}

        allow_delete = bool(sa_cfg.get("allow_delete", True))

        self._state = {"allow_delete": allow_delete}
        return dict(self._state)

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:  # type: ignore[override]
        # Primitive fields use the standard types; more structured
        # fields (such as indices arrays) are validated by the plugin
        # itself so they use a generic type here.
        return [
            {
                "id": "copy_session",
                "label": "Copy session",
                "description": "Duplicate a session.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "source": {
                        "type": "string",
                        "required": False,
                        "default": "manual",
                    },
                },
            },
            {
                "id": "fork_session_at",
                "label": "Fork session at index",
                "description": "Create a fork up to the given message index.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "index": {"type": "integer", "required": True},
                    "source": {"type": "string", "required": False},
                },
            },
            {
                "id": "delete_session",
                "label": "Delete session",
                "description": "Delete an entire session.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "source": {"type": "string", "required": False},
                },
            },
            {
                "id": "delete_messages",
                "label": "Delete messages",
                "description": "Delete one or more messages from a session.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    # indices / start / end / last use non-primitive
                    # structures and are validated inside the plugin.
                    "indices": {"type": "array", "required": False},
                    "start": {"type": "integer", "required": False},
                    "end": {"type": "integer", "required": False},
                    "last": {"type": "integer", "required": False},
                    "source": {"type": "string", "required": False},
                },
            },
        ]

    def execute_action(
        self,
        app: "AgentApplication",  # type: ignore[override]
        action_id: str,
        params: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if action_id == "copy_session":
            return self._do_copy_session(app, params)
        if action_id == "fork_session_at":
            return self._do_fork_session_at(app, params)
        if action_id == "delete_session":
            return self._do_delete_session(app, params, state)
        if action_id == "delete_messages":
            return self._do_delete_messages(app, params)

        raise ValueError(f"Unknown action_id {action_id!r} for SessionActionsAppPlugin")

    # ------------------------------------------------------------------
    # Action implementations
    # ------------------------------------------------------------------

    def _do_copy_session(
        self, app: "AgentApplication", params: Dict[str, Any]
    ) -> Dict[str, Any]:
        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        source_val = params.get("source")
        source = source_val if isinstance(source_val, str) else ""

        new_session_id = str(uuid.uuid4())

        with app.acquire_session_lock(session_id):
            ctx = app.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            core, base_config, session = ctx

            message_count = len(session.messages)
            metadata = session.metadata if isinstance(session.metadata, dict) else {}

            if message_count == 0:
                # For empty sessions, perform a shallow copy of metadata and
                # messages while assigning a new session id.
                new_session = Session(
                    session_id=new_session_id,
                    messages=list(session.messages),
                    metadata=dict(metadata) if isinstance(metadata, dict) else None,
                )
                _new_core, _new_base_config, new_session, _ = app.run_session_lifecycle(
                    "session_fork",
                    new_session,
                    base_config=base_config,
                    context={
                        "session_id": new_session.session_id,
                        "fork_upto_index": -1,
                        "original_session": session.to_dict(),
                    },
                )
            else:
                _new_core, _new_base_config, new_session = app.fork_session(
                    core,
                    session,
                    base_config,
                    upto_index=message_count - 1,
                    new_session_id=new_session_id,
                )

            app.save_session(new_session)

            md = new_session.metadata if isinstance(new_session.metadata, dict) else {}
            agent_val = md.get("agent_id")
            agent_id = agent_val.strip() if isinstance(agent_val, str) else ""

            stored = app.publish_event(
                {
                    "type": "session_created",
                    "session_id": new_session.session_id,
                    "agent_id": agent_id,
                    "source_session_id": session.session_id,
                }
            )

            try:
                app.record_checkpoint(new_session.session_id, stored.get("request_id"))
            except Exception:  # pragma: no cover - defensive
                # Checkpoint failures should not make the action fail.
                pass

        navigate_to_session_id = new_session_id if source != "session_list" else None

        return {
            "mutations": {
                "created_session_ids": [new_session_id],
                "updated_session_ids": [],
                "deleted_session_ids": [],
            },
            "ui_effects": {
                "navigate_to_session_id": navigate_to_session_id,
            },
            "message": "Session copied successfully.",
        }

    def _do_fork_session_at(
        self, app: "AgentApplication", params: Dict[str, Any]
    ) -> Dict[str, Any]:
        session_id = params.get("session_id")
        index = params.get("index")

        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")
        if not isinstance(index, int):
            raise ValueError("index must be an integer")

        new_session_id = str(uuid.uuid4())

        with app.acquire_session_lock(session_id):
            ctx = app.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            core, base_config, session = ctx

            message_count = len(session.messages)
            if message_count == 0:
                raise ValueError("no messages to fork")

            try:
                target_index = _normalize_index(index, message_count)
            except IndexError as exc:
                raise ValueError(str(exc)) from exc

            _new_core, _new_base_config, new_session = app.fork_session(
                core,
                session,
                base_config,
                upto_index=target_index,
                new_session_id=new_session_id,
            )

            app.save_session(new_session)

            md = new_session.metadata if isinstance(new_session.metadata, dict) else {}
            agent_val = md.get("agent_id")
            agent_id = agent_val.strip() if isinstance(agent_val, str) else ""

            stored = app.publish_event(
                {
                    "type": "session_created",
                    "session_id": new_session.session_id,
                    "agent_id": agent_id,
                    "source_session_id": session.session_id,
                }
            )

            try:
                app.record_checkpoint(new_session.session_id, stored.get("request_id"))
            except Exception:  # pragma: no cover - defensive
                pass

        return {
            "mutations": {
                "created_session_ids": [new_session_id],
                "updated_session_ids": [],
                "deleted_session_ids": [],
            },
            "ui_effects": {
                "navigate_to_session_id": new_session_id,
            },
            "message": "Session forked successfully.",
        }

    def _do_delete_session(
        self,
        app: "AgentApplication",
        params: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        allow_delete = bool(state.get("allow_delete", True))
        if not allow_delete:
            raise ValueError("session deletion is disabled by configuration")

        with app.acquire_session_lock(session_id):
            session = app.load_session_record(session_id)
            if session is None:
                raise KeyError(f"Session {session_id!r} not found")

            app.delete_session(session.session_id)

            stored = app.publish_event(
                {
                    "type": "session_deleted",
                    "session_id": session.session_id,
                }
            )

            try:
                app.record_checkpoint(session.session_id, stored.get("request_id"))
            except Exception:  # pragma: no cover - defensive
                pass

        return {
            "mutations": {
                "created_session_ids": [],
                "updated_session_ids": [],
                "deleted_session_ids": [session_id],
            },
            "ui_effects": {},
            "message": "Session deleted.",
        }

    def _do_delete_messages(
        self, app: "AgentApplication", params: Dict[str, Any]
    ) -> Dict[str, Any]:
        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        has_indices = "indices" in params
        has_start_end = ("start" in params) or ("end" in params)
        has_last = "last" in params

        if int(has_indices) + int(has_start_end) + int(has_last) != 1:
            raise ValueError(
                "Exactly one of 'indices', 'start'/'end', or 'last' must be provided",
            )

        with app.acquire_session_lock(session_id):
            ctx = app.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            core, base_config, session = ctx

            message_count = len(session.messages)
            if message_count == 0:
                raise ValueError("no messages to delete")

            delete_indices: List[int]
            start_idx = 0
            end_idx = message_count
            raw_start: Optional[int] = None
            raw_end: Optional[int] = None

            if has_indices:
                raw_indices = params.get("indices")
                if not isinstance(raw_indices, list):
                    raise ValueError("indices must be a list of integers")
                if not raw_indices:
                    # Nothing to delete; keep the session unchanged.
                    return {
                        "mutations": {
                            "created_session_ids": [],
                            "updated_session_ids": [],
                            "deleted_session_ids": [],
                        },
                        "ui_effects": {},
                        "deleted_indices": [],
                        "message": "No messages deleted.",
                    }

                delete_indices = []
                for raw in raw_indices:
                    if not isinstance(raw, int):
                        raise ValueError("indices must be integers")
                    try:
                        idx = _normalize_index(raw, message_count)
                    except IndexError as exc:
                        raise ValueError(str(exc)) from exc
                    delete_indices.append(idx)

            elif has_start_end:
                start = params.get("start")
                end = params.get("end")
                if start is not None and not isinstance(start, int):
                    raise ValueError("start must be an integer or null")
                if end is not None and not isinstance(end, int):
                    raise ValueError("end must be an integer or null")

                try:
                    start_idx, end_idx = _normalize_slice_bounds(
                        message_count,
                        start if isinstance(start, int) else None,
                        end if isinstance(end, int) else None,
                    )
                except ValueError as exc:
                    raise ValueError(str(exc)) from exc

                delete_indices = list(range(start_idx, end_idx))
                raw_start = start if isinstance(start, int) else None
                raw_end = end if isinstance(end, int) else None

            else:  # has_last
                last = params.get("last")
                if not isinstance(last, int):
                    raise ValueError("last must be an integer")
                if last <= 0:
                    raise ValueError("count must be a positive integer")

                count = min(last, message_count)
                start_idx = message_count - count
                end_idx = message_count
                delete_indices = list(range(start_idx, message_count))

            if not delete_indices:
                raise ValueError("no messages selected for deletion")

            concrete_indices = sorted(set(delete_indices))
            snapshot_reason = _deletion_snapshot_reason(
                concrete_indices=concrete_indices,
                has_indices=has_indices,
                has_start_end=has_start_end,
                start_idx=start_idx,
                end_idx=end_idx,
                raw_start=raw_start,
                raw_end=raw_end,
            )
            snapshot = app.create_session_snapshot(
                session_id,
                reason=snapshot_reason,
                metadata={
                    "origin": "automatic",
                    "plugin": self.name,
                    "action": "delete_messages",
                    "deleted_indices": concrete_indices,
                    "range": {
                        "start": concrete_indices[0],
                        "end": concrete_indices[-1] + 1,
                    },
                },
            )

            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            overrides_val = metadata.get("overrides")
            overrides: Dict[str, Any] = (
                overrides_val if isinstance(overrides_val, dict) else {}
            )
            config = resolve_request_config(base_config, overrides)

            new_session = core.slice_session(
                session, config, remove_indices=delete_indices
            )
            try:
                new_session = app.save_session(new_session)
            except BaseException:
                app.delete_session_snapshot(session_id, snapshot.snapshot_id)
                raise

            stored = app.publish_event(
                {
                    "type": "messages_deleted",
                    "session_id": new_session.session_id,
                    "indices": concrete_indices,
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
            "deleted_indices": concrete_indices,
            "message": "Messages deleted.",
        }


__all__ = ["SessionActionsAppPlugin"]
