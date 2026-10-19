from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from agent_app.application_owner import AgentApplicationOwner
from agent_app.application_future import AgentApplication
from agent_app.command_ui import match_command_path
from agent_app.config import resolve_request_config
from agent_app.notifications import (
    is_active_notification,
    notification_revision_token,
)
from agent_app.request_execution import SessionRequestStart
from agent_app.utils.ui_condition import evaluate_condition
from agent_core import Session

from .session_query import parse_multi_select_csv


class TerminalUserError(Exception):
    """Error caused by invalid user input (indices, arguments, etc.)."""


class TerminalApplicationError(Exception):
    """Error caused by unexpected terminal application state/invariants."""

    # Currently used only for internal categorization; all non-user
    # exceptions are surfaced by the terminal's centralized error
    # handler.


class TerminalApplication:
    """Stateful application logic for the terminal frontend.

    This class owns an :class:`AgentApplication` instance and tracks a
    single active :class:`Session` plus its last-seen event id for
    incremental polling. All session and event semantics for the
    terminal UI go through this class; the prompt_toolkit-based UI in
    ``terminal.py`` is responsible only for representation and user
    interaction.
    """

    def __init__(
        self,
        *,
        config_path: str | Path,
        session_root: str | Path,
        agent_app: AgentApplication | None = None,
        application_owner: AgentApplicationOwner | None = None,
        env_overrides: Mapping[str, str] | None = None,
    ) -> None:
        self._session_root: Path = Path(session_root)
        self._application_owner = application_owner

        if application_owner is not None:
            self._app = application_owner.current
            application_owner.add_replacement_listener(self.replace_agent_app)
        elif agent_app is not None:
            self._app = agent_app
        else:
            self._session_root.mkdir(parents=True, exist_ok=True)
            self._app = AgentApplication(
                str(config_path),
                str(self._session_root),
                env_overrides=env_overrides,
            )

        self._session: Session | None = None
        self._core: Any | None = None
        self._base_config: Any | None = None
        self._last_event_id: str | None = None
        self._ui_schema_cache_key: Tuple[int, str] | None = None
        self._ui_schema_cache: List[Dict[str, object]] | None = None
        self._application_generation = 1
        self._action_references: Dict[str, Dict[str, Any]] = {}
        self._notification_reference_ids: Dict[
            Tuple[str, str, str, str], str
        ] = {}
        self._direct_display_references: Dict[str, set[str]] = {}
        self._direct_reference_displays: Dict[str, str] = {}
        self._next_action_reference = 1
        self._notification_event_id: str | None = None
        self._notification_hydration_required = True
        self._notification_versions: Dict[
            Tuple[str, str | None, str], int | str
        ] = {}

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def agent_app(self) -> AgentApplication:
        return self._app

    def close(self) -> None:
        """Release resources owned by the underlying application."""

        if self._application_owner is None:
            self._app.close()

    def replace_agent_app(self, application: AgentApplication) -> None:
        """Switch to a replacement application and invalidate runtime caches."""

        self._app = application
        self._application_generation += 1
        self._action_references = {}
        self._notification_reference_ids = {}
        self._direct_display_references = {}
        self._direct_reference_displays = {}
        self._notification_versions = {}
        self._notification_event_id = None
        self._notification_hydration_required = True
        self._core = None
        self._base_config = None
        if self._session is not None:
            loaded = application.load_session(self._session.session_id)
            if loaded is not None:
                self._core, self._base_config, self._session = loaded
        self._ui_schema_cache_key = None
        self._ui_schema_cache = None

    @property
    def session(self) -> Session:
        if self._session is None:
            raise RuntimeError("No active session; create one first")
        return self._session

    @property
    def session_id(self) -> str:
        return self.session.session_id

    def require_session(self) -> Tuple[Any, Any, Session]:
        """Return (core, base_config, session) for the active session.

        Raises ``RuntimeError`` if no session (or core/config) is loaded.
        """

        session = self.session
        core = self._core
        base_config = self._base_config
        if core is None or base_config is None:
            raise RuntimeError("No active core; create a session first")
        return core, base_config, session

    @staticmethod
    def _stable_config_cache_key(config: Dict[str, Any]) -> str:
        """Return a stable representation for UI-schema cache keys."""

        try:
            return json.dumps(
                config,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )
        except TypeError:
            try:
                return repr(sorted(config.items()))
            except Exception:
                return repr(config)

    def _ui_schema_for_current_effective_config(self) -> List[Dict[str, object]]:
        """Return cached UI schema for the active core and effective config."""

        core, base_config, session = self.require_session()
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        raw = metadata.get("overrides")
        overrides = raw if isinstance(raw, dict) else {}
        effective_config = resolve_request_config(base_config, overrides)

        cache_key = (
            id(core),
            self._stable_config_cache_key(effective_config),
        )
        if cache_key == self._ui_schema_cache_key and self._ui_schema_cache is not None:
            return self._ui_schema_cache

        try:
            ui_schema = core.get_ui_schema(config=effective_config)
        except Exception:
            return []

        result = [el for el in ui_schema or [] if isinstance(el, dict)]
        self._ui_schema_cache_key = cache_key
        self._ui_schema_cache = result
        return result

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def start_new_session(
        self, agent_id: Optional[str] = None, *, persist: bool = True
    ) -> Session:
        """Start a new active session, replacing any previous one.

        When ``persist`` is ``False``, the new session is created but not yet
        written to the underlying session store; it will be persisted by later
        operations such as :meth:`append_user_message`.
        """

        if agent_id is None and self._session is not None:
            metadata = self._session.metadata or {}
            current_agent = metadata.get("agent_id")
            if isinstance(current_agent, str) and current_agent.strip():
                agent_id = current_agent.strip()

        if agent_id is None:
            agents = self.available_agents()
            if not agents:
                raise TerminalUserError("no agents configured")
            agent_id = agents[0]

        if persist:
            core, base_config, session = self._app.create_session(agent_id)
        else:
            core, base_config, session = self._app.create_session_ephemeral(agent_id)

        # For ephemeral sessions we still publish a lifecycle event so
        # the terminal can show them in the events view. For persisted
        # sessions, also emit a checkpoint marker so that the session
        # cursor advances to a concrete persistence point.
        self._app.publish_event(
            {
                "type": "session_created",
                "session_id": session.session_id,
                "agent_id": agent_id,
            },
        )

        if persist:
            try:
                self._app.record_checkpoint(session.session_id, None)
            except Exception:
                # Best-effort; do not fail session creation on
                # checkpoint emission issues.
                pass

        self._session = session
        self._core = core
        self._base_config = base_config
        self._last_event_id = None
        self._notification_hydration_required = True
        return session

    def list_sessions_metadata(
        self,
        limit: Optional[int] = None,
        *,
        filter_values: Optional[Dict[str, object]] = None,
        apply_filter_defaults: bool = False,
    ) -> List[Dict[str, Any]]:
        """Return shared application-layer summaries for stored sessions."""

        return self._app.list_session_summaries(
            filter_values=filter_values,
            apply_filter_defaults=apply_filter_defaults,
            limit=limit,
        )

    def session_filter_schema(self) -> Dict[str, Any]:
        """Return the normalized filter schema used by terminal queries."""

        return self._app.get_session_list_filter_schema()

    def is_saved_session_id(self, session_id: str) -> bool:
        """Return whether an exact stored session exists, ignoring filters."""

        if not isinstance(session_id, str) or not session_id:
            return False
        try:
            self._app.get_session_summary(session_id)
        except KeyError:
            return False
        return True

    def query_sessions_metadata(
        self,
        *,
        search_text: str = "",
        filter_inputs: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Apply plugin defaults plus command-local terminal filter inputs."""

        schema = self.session_filter_schema()
        declarations = {
            declaration["id"]: declaration
            for declaration in schema.get("filters", [])
            if isinstance(declaration, dict) and isinstance(declaration.get("id"), str)
        }
        main_search_id = schema.get("main_search_id")
        if search_text:
            if schema.get("main_search_conflict"):
                raise TerminalUserError(
                    "session main-search schema is ambiguous; "
                    "disable one of the competing plugins"
                )
            if not isinstance(main_search_id, str) or not main_search_id:
                raise TerminalUserError(
                    "free-text session search requires a main-search plugin"
                )

        values: Dict[str, object] = {}
        for filter_id, raw_value in (filter_inputs or {}).items():
            declaration = declarations.get(filter_id)
            if declaration is None:
                raise TerminalUserError(f"unknown session filter: {filter_id!r}")
            if declaration.get("main_search") is True:
                raise TerminalUserError(
                    f"main-search filter {filter_id!r} is set by trailing search text"
                )
            try:
                if (
                    declaration.get("type") == "select"
                    and declaration.get("multiple") is True
                ):
                    input_value: str | List[str] = parse_multi_select_csv(raw_value)
                else:
                    input_value = raw_value
                values[filter_id] = self._app.coerce_session_list_filter_input(
                    filter_id, input_value
                )
            except (KeyError, ValueError) as exc:
                raise TerminalUserError(str(exc)) from exc

        if search_text and isinstance(main_search_id, str):
            values[main_search_id] = search_text

        return self.list_sessions_metadata(
            limit=limit,
            filter_values=values,
            apply_filter_defaults=True,
        )

    def session_filter_completion_values(self, filter_id: str) -> List[str]:
        """Return terminal spellings accepted for one non-text filter."""

        schema = self.session_filter_schema()
        declaration = next(
            (
                item
                for item in schema.get("filters", [])
                if isinstance(item, dict) and item.get("id") == filter_id
            ),
            None,
        )
        if not isinstance(declaration, dict):
            return []
        if declaration.get("type") == "boolean":
            return ["any", "true", "false"]
        if declaration.get("type") == "select":
            values = ["any"]
            for option in declaration.get("options", []):
                if not isinstance(option, dict):
                    continue
                value = option.get("value")
                if isinstance(value, bool):
                    values.append("true" if value else "false")
                elif isinstance(value, str):
                    values.append(value)
            return values
        return []

    def switch_session(self, session_id: str) -> Session:
        """Load an existing session by id and make it active."""
        if not isinstance(session_id, str) or not session_id:
            raise TerminalUserError("session_id must be a non-empty string")

        try:
            ctx = self._app.load_session(session_id)
        except KeyError as exc:
            detail = (
                exc.args[0] if exc.args and isinstance(exc.args[0], str) else str(exc)
            )
            if not (isinstance(detail, str) and detail.startswith("Unknown agent_id")):
                raise
            session = self._app.load_session_record(session_id)
            if session is None:
                raise TerminalUserError(f"session {session_id!r} not found") from exc
            self._core = None
            self._base_config = None
            self._session = session
        else:
            if ctx is None:
                raise TerminalUserError(f"session {session_id!r} not found")

            core, base_config, session = ctx
            self._core = core
            self._base_config = base_config
            self._session = session
        # Resume polling from the persisted cursor for this session so
        # that switching does not replay the entire event history.
        try:
            self._last_event_id = self._app.get_session_cursor_event_id(
                session.session_id
            )
        except Exception:  # pragma: no cover - defensive
            self._last_event_id = None
        self._notification_hydration_required = True
        return session

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    def append_user_message(
        self, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """Append a user message to the active session."""

        core, _base_config, session = self.require_session()

        base_md: Dict[str, Any] = metadata or {}

        # Append via core so that features (including timestamp plugins)
        # can enrich metadata such as ``metadata.timestamp``.
        new_session = core.add_message(
            session,
            "user",
            content,
            base_md,
            config=_base_config,
            context=self._app._context.build_core_handoff_context(
                base_config=_base_config
            ),
        )
        self._app.save_session(new_session)

        last_message = new_session.messages[-1] if new_session.messages else None
        last_md: Dict[str, Any] = {}
        if last_message is not None:
            data = last_message.to_dict()
            raw_md = data.get("metadata") or {}
            if isinstance(raw_md, dict):
                last_md = raw_md

        self._app.publish_event(
            {
                "type": "message_appended",
                "session_id": new_session.session_id,
                "index": len(new_session.messages) - 1,
                "role": "user",
                "content": content,
                # Use the metadata from the appended message so that
                # plugin-provided fields (e.g., timestamp) are visible
                # to renderers.
                "metadata": last_md,
                "message": last_message.to_dict() if last_message is not None else None,
            },
        )
        try:
            self._app.record_checkpoint(new_session.session_id, None)
        except Exception:
            pass

        self._session = new_session
        return new_session

    # Internal helpers for index and slice normalization.

    @staticmethod
    def _normalize_index(raw_index: int, message_count: int) -> int:
        """Normalize a Python-style index for a sequence of ``message_count``.

        Negative indices are translated relative to the end. Raises
        :class:`IndexError` if the resulting index is out of bounds.
        """

        target_index = raw_index
        if target_index < 0:
            target_index = message_count + target_index
        if target_index < 0 or target_index >= message_count:
            raise IndexError("message index out of range")
        return target_index

    @staticmethod
    def _normalize_slice_bounds(
        message_count: int,
        start: Optional[int],
        end: Optional[int],
    ) -> Tuple[int, int]:
        """Return concrete ``(start_idx, end_idx)`` for slice-like bounds.

        Bounds follow Python slice semantics with support for ``None`` and
        negative indices. Raises :class:`ValueError` when the range selects
        no messages.
        """

        def _normalize_bound(value: Optional[int], default: int) -> int:
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

        start_idx = _normalize_bound(start, 0)
        end_idx = _normalize_bound(end, message_count)

        if start_idx >= end_idx:
            raise ValueError("range selects no messages")

        return start_idx, end_idx

    def fork_session(self, index: int) -> Session:
        """Fork the active session up to and including ``index``.

        Index semantics follow Python list indexing (0-based with
        negative indices relative to the end). The forked session is
        persisted via the underlying application and becomes the active
        session.
        """

        core, base_config, session = self.require_session()

        if not isinstance(index, int):
            raise TypeError("index must be an integer")

        message_count = len(session.messages)
        if message_count == 0:
            raise ValueError("no messages to fork")

        target_index = self._normalize_index(index, message_count)

        new_session_id = str(uuid.uuid4())
        _new_core, _new_base_config, new_session = self._app.fork_session(
            core,
            session,
            base_config,
            upto_index=target_index,
            new_session_id=new_session_id,
        )

        self._app.save_session(new_session)

        # Publish a lifecycle event so renderers can surface the fork
        # and advance the session cursor via a checkpoint marker.
        md = new_session.metadata if isinstance(new_session.metadata, dict) else {}
        agent = md.get("agent_id")
        agent_id = agent.strip() if isinstance(agent, str) else ""
        self._app.publish_event(
            {
                "type": "session_created",
                "session_id": new_session.session_id,
                "agent_id": agent_id,
                "source_session_id": session.session_id,
                "fork_upto_index": target_index,
            },
        )
        try:
            self._app.record_checkpoint(new_session.session_id, None)
        except Exception:
            pass

        self._session = new_session
        self._core = core
        self._base_config = base_config
        self._last_event_id = None
        return new_session

    def delete_messages(self, indices: List[int]) -> Session:
        """Delete one or more messages by core index.

        Indices are 0-based; negative values follow Python semantics
        relative to the current message list length. Deletion uses the
        core's config-aware slice_session helper so that provider-native
        history is preserved when possible.
        """

        if not indices:
            return self.session

        core, base_config, session = self.require_session()

        message_count = len(session.messages)
        if message_count == 0:
            raise TerminalUserError("no messages to delete")

        normalized: List[int] = []
        for raw in indices:
            if not isinstance(raw, int):
                raise TerminalUserError("indices must be integers")
            try:
                idx = self._normalize_index(raw, message_count)
            except IndexError:
                raise TerminalUserError("message index out of range")
            normalized.append(idx)

        if not normalized:
            raise TerminalUserError("no messages selected for deletion")

        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides_val = metadata.get("overrides")
        overrides: Dict[str, Any] = (
            overrides_val if isinstance(overrides_val, dict) else {}
        )
        config = resolve_request_config(base_config, overrides)

        new_session = core.slice_session(session, config, remove_indices=normalized)
        self._app.save_session(new_session)

        concrete_indices = sorted(set(normalized))

        self._app.publish_event(
            {
                "type": "messages_deleted",
                "session_id": new_session.session_id,
                "indices": concrete_indices,
            },
        )
        try:
            self._app.record_checkpoint(new_session.session_id, None)
        except Exception:
            pass

        self._session = new_session
        return new_session

    def delete_messages_by_range(
        self,
        start: Optional[int],
        end: Optional[int],
    ) -> Tuple[Session, List[int]]:
        """Delete messages using Python-style slice semantics.

        ``start`` and ``end`` are interpreted like slice bounds, including
        support for negative indices. Returns the updated session and the
        concrete indices that were removed.
        """

        core, _base_config, session = self.require_session()
        message_count = len(session.messages)

        if message_count == 0:
            raise TerminalUserError("no messages to delete")

        try:
            start_idx, end_idx = self._normalize_slice_bounds(message_count, start, end)
        except ValueError:
            raise TerminalUserError("range selects no messages")

        indices = list(range(start_idx, end_idx))
        new_session = self.delete_messages(indices)
        return new_session, sorted(set(indices))

    def delete_last_messages(self, count: int) -> Tuple[Session, List[int]]:
        """Delete the last ``count`` messages in the active session.

        Returns the updated session and the concrete indices that were
        removed.
        """

        if count <= 0:
            raise TerminalUserError("count must be a positive integer")

        core, _base_config, session = self.require_session()
        message_count = len(session.messages)

        if message_count == 0:
            raise TerminalUserError("no messages to delete")

        if count > message_count:
            count = message_count

        start_idx = message_count - count
        indices = list(range(start_idx, message_count))
        new_session = self.delete_messages(indices)
        return new_session, sorted(set(indices))

    def list_messages_by_range(
        self,
        start: Optional[int],
        end: Optional[int],
    ) -> List[Tuple[int, Any]]:
        """List messages for the active session using Python-style slice bounds.

        When the active session has been persisted, the latest version is
        reloaded from the underlying application so that external
        modifications are reflected. For in-memory or ephemeral sessions that
        have not yet been saved, the currently loaded session is used
        directly.
        """

        # Prefer the latest persisted version of the active session when
        # available, but fall back to the in-memory session for ephemeral
        # sessions that are not yet stored on disk.
        sid = self.session_id
        ctx = self._app.load_session(sid)
        if ctx is not None:
            core, base_config, session = ctx
            self._core = core
            self._base_config = base_config
            self._session = session
        else:
            _core, _base_config, session = self.require_session()

        message_count = len(session.messages)
        if message_count == 0:
            raise TerminalUserError("no messages to list")

        try:
            start_idx, end_idx = self._normalize_slice_bounds(message_count, start, end)
        except ValueError:
            raise TerminalUserError("range selects no messages")

        indices = range(start_idx, end_idx)
        return [(i, session.messages[i]) for i in indices]

    def show_message(self, index: int) -> Tuple[int, Any]:
        """Return a single message by Python-style index.

        Negative indices are resolved relative to the end of the
        message list using :meth:`_normalize_index`. When the active
        session has been persisted, the latest version is reloaded from
        the application first so that external modifications are
        visible. For in-memory or ephemeral sessions that are not yet
        stored, the currently loaded session is used directly.
        """

        # Prefer the latest persisted version of the active session when
        # available, but fall back to the in-memory session for ephemeral
        # sessions that are not yet stored on disk.
        sid = self.session_id
        ctx = self._app.load_session(sid)
        if ctx is not None:
            core, base_config, session = ctx
            self._core = core
            self._base_config = base_config
            self._session = session
        else:
            _core, _base_config, session = self.require_session()

        if not isinstance(index, int):
            raise TerminalUserError("index must be an integer")

        message_count = len(session.messages)
        if message_count == 0:
            raise TerminalUserError("no messages to show")

        try:
            target_index = self._normalize_index(index, message_count)
        except IndexError:
            raise TerminalUserError("message index out of range")

        return target_index, session.messages[target_index]

    def modify_message(self, index: int, content: str) -> Session:
        """Modify the content of a message in the active session.

        Index semantics follow Python list indexing (0-based, negatives
        allowed). The underlying core enforces supported roles and
        native-history behaviour.
        """

        core, base_config, session = self.require_session()

        if not isinstance(index, int):
            raise TerminalUserError("index must be an integer")
        if not isinstance(content, str):
            raise TerminalUserError("content must be a string")

        message_count = len(session.messages)
        if message_count == 0:
            raise TerminalUserError("no messages to modify")

        try:
            target_index = self._normalize_index(index, message_count)
        except IndexError:
            raise TerminalUserError("message index out of range")

        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides_val = metadata.get("overrides")
        overrides: Dict[str, Any] = (
            overrides_val if isinstance(overrides_val, dict) else {}
        )
        config = resolve_request_config(base_config, overrides)

        new_session = core.modify_message(
            session,
            target_index,
            content,
            config,
            context=self._app._context.build_core_handoff_context(
                base_config=base_config
            ),
        )
        self._app.save_session(new_session)

        updated_message = new_session.messages[target_index]

        store = self._app.get_event_store()
        store.publish(
            {
                "type": "message_modified",
                "session_id": new_session.session_id,
                "index": target_index,
                "content": content,
                "message": updated_message.to_dict(),
            }
        )

        self._session = new_session
        return new_session

    # ------------------------------------------------------------------
    # Requests and events
    # ------------------------------------------------------------------

    def start_request(self, *, stream: bool = True) -> SessionRequestStart:
        """Start a request for the active session without appending a message."""

        session = self.session
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides = metadata.get("overrides")
        request_overrides = overrides if isinstance(overrides, dict) else {}
        return self._app.start_session_request(
            session.session_id,
            request_overrides,
            stream=stream,
        )

    def append_user_message_and_start_request(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        *,
        stream: bool = True,
    ) -> SessionRequestStart:
        """Atomically append a user message and start a request."""

        session = self.session
        if self._app.load_live_session_record(session.session_id) is None:
            self._session = self._app.save_session(session)

        current = self.session
        current_metadata = (
            current.metadata if isinstance(current.metadata, dict) else {}
        )
        overrides = current_metadata.get("overrides")
        request_overrides = overrides if isinstance(overrides, dict) else {}
        started = self._app.start_session_request_with_message(
            current.session_id,
            role="user",
            content=content,
            metadata=metadata,
            overrides=request_overrides,
            stream=stream,
        )
        loaded = self._app.load_session(current.session_id)
        if loaded is not None:
            self._core, self._base_config, self._session = loaded
        return started

    def send_request(
        self,
        *,
        stream: bool = True,
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
        """Run the coordinated request flow for the active session."""

        session = self.session
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides = metadata.get("overrides")
        request_overrides = overrides if isinstance(overrides, dict) else {}

        def _on_checkpoint(session_obj: Session) -> None:
            self._session = session_obj

        result = self._app.run_session_request(
            session.session_id,
            request_overrides,
            stream=stream,
            on_checkpoint=_on_checkpoint,
        )

        if result.final_session is not None:
            try:
                final_session = Session.from_dict(result.final_session)
                self._session = final_session
            except Exception:  # pragma: no cover - defensive
                pass

        loaded = self._app.load_session(session.session_id)
        if loaded is not None:
            self._core, self._base_config, loaded_session = loaded
            self._session = loaded_session

        return result.final_session, result.final_messages, result.request_id

    def poll_new_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return events for the active session since the last poll."""

        try:
            session = self.session
        except RuntimeError:
            return []

        store = self._app.get_event_store()
        listed = store.list(
            since_id=self._last_event_id,
            request_id=None,
            session_id=session.session_id,
            limit=limit,
        )
        raw_events = listed.get("events") or []
        if listed.get("cursor_expired"):
            latest_event_id = listed.get("latest_event_id")
            if isinstance(latest_event_id, str) and latest_event_id:
                self._last_event_id = latest_event_id
            return [
                {
                    "type": "events_cursor_expired",
                    "session_id": session.session_id,
                    "message": "Event cursor expired; reload recommended.",
                    "latest_event_id": latest_event_id,
                }
            ]
        events = self._app.compact_events(raw_events)
        if raw_events:
            last = raw_events[-1].get("event_id")
            if isinstance(last, str):
                self._last_event_id = last
        return events

    def list_events(
        self,
        *,
        session_id: Optional[str] = None,
        limit: int = 100,
        since_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List events from the shared event store.

        If ``session_id`` is not provided, uses the current session id.
        """
        sid = session_id or self.session.session_id
        store = self._app.get_event_store()
        return (
            store.list(
                since_id=since_id,
                request_id=request_id,
                session_id=sid,
                limit=limit,
            ).get("events")
            or []
        )

    def get_feature_completions(self, text: str) -> List[Dict[str, Any]]:
        """Return feature-driven completion suggestions for the active session.

        The base configuration for the current agent is merged with any
        per-session overrides before delegating to the core's
        ``get_completions`` method.
        """

        core, base_config, session = self.require_session()

        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides_val = metadata.get("overrides")
        overrides: Dict[str, Any] = (
            overrides_val if isinstance(overrides_val, dict) else {}
        )

        config = resolve_request_config(base_config, overrides)

        try:
            return core.get_completions(config, text)
        except Exception:
            return []

    def add_message(
        self,
        session_id: str,
        *,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Append a message to an arbitrary session and publish an event.

        Returns a dict with the updated session under the "session" key.
        """

        core, _base_config, session = self.require_session()

        normalized_role = (
            role if role in {"system", "user", "assistant", "tool"} else "user"
        )

        new_session: Session = core.add_message(
            session,
            normalized_role,
            content,
            metadata,
            config=_base_config,
            context=self._app._context.build_core_handoff_context(
                base_config=_base_config
            ),
        )
        self._app.save_session(new_session)

        if (
            self._session is not None
            and self._session.session_id == new_session.session_id
        ):
            self._session = new_session

        last_message = new_session.messages[-1] if new_session.messages else None
        last_md: Dict[str, Any] = {}
        if last_message is not None:
            data = last_message.to_dict()
            raw_md = data.get("metadata") or {}
            if isinstance(raw_md, dict):
                last_md = raw_md

        store = self._app.get_event_store()
        store.publish(
            {
                "type": "message_appended",
                "session_id": new_session.session_id,
                "index": len(new_session.messages) - 1,
                "role": normalized_role,
                "content": content,
                # Surface metadata from the stored message (including
                # plugin-provided fields) for renderers and clients.
                "metadata": last_md,
                "message": last_message.to_dict() if last_message is not None else None,
            }
        )

        return {"session": new_session.to_dict()}

    def reset_event_cursor(self) -> None:
        self._last_event_id = None

    # ------------------------------------------------------------------
    # Agents and configuration
    # ------------------------------------------------------------------

    def current_agent_id(self) -> str:
        session = self.session
        metadata = session.metadata or {}
        agent = metadata.get("agent_id")
        return agent.strip() if isinstance(agent, str) else ""

    def available_agents(self) -> List[str]:
        agents = self._app.list_agents()

        agents = [a for a in agents if isinstance(a, str) and a]
        # Deduplicate while preserving insertion order, then sort.
        unique: Dict[str, None] = {}
        for agent in agents:
            if agent not in unique:
                unique[agent] = None
        return sorted(unique.keys())

    def switch_agent(self, target_agent_id: str) -> Session:
        session = self.session

        if not isinstance(target_agent_id, str) or not target_agent_id:
            raise TerminalUserError("agent_id must be a non-empty string")

        if target_agent_id not in self.available_agents():
            raise TerminalUserError(f"unknown agent: {target_agent_id!r}")

        # Rebuild core/base_config for the new agent and update
        # session metadata, but do not decide on persistence here.
        core, base_config, new_session = self._app.update_agent(
            target_agent_id, session
        )

        # Decide whether to persist:
        # - If the session has messages, always save.
        # - If it is empty but was previously saved, update the file.
        # - If it is empty and has never been saved (initial ephemeral
        #   session), keep it purely in memory.
        is_empty = not session.messages
        is_persisted = (
            self._app.load_live_session_record(session.session_id) is not None
        )
        should_save = (not is_empty) or is_persisted

        if should_save:
            self._app.save_session(new_session)

        self._core = core
        self._base_config = base_config
        self._session = new_session
        return new_session

    def session_ui_elements(self) -> list[dict[str, object]]:
        ui_schema = self._ui_schema_for_current_effective_config()

        def _is_config_element(el: object) -> bool:
            match el:
                case {"ui_type": "config", "key": str(key)} if key:
                    return True
                case {"key": str(key)} if key and "ui_type" not in el:
                    return True
                case _:
                    return False

        return [el for el in ui_schema or [] if _is_config_element(el)]

    def message_footer_elements(self) -> list[dict[str, object]]:
        """Return UI schema elements that describe message footers.

        Plugins may contribute elements with ui_type == "message_footer" that
        reference JSON paths within messages for display in the terminal
        footer area.
        """

        ui_schema = self._ui_schema_for_current_effective_config()

        result: list[dict[str, object]] = []
        for el in ui_schema or []:
            if not isinstance(el, dict):
                continue
            if el.get("ui_type") == "message_footer":
                result.append(el)
        return result

    def status_bar_elements(self) -> list[dict[str, object]]:
        """Return UI schema elements that describe status bar fields.

        Plugins may contribute elements with ui_type == "status_bar" that
        reference JSON paths within messages. These are extracted from the
        last assistant message and displayed in the terminal's bottom toolbar.
        """
        ui_schema = self._ui_schema_for_current_effective_config()

        result: list[dict[str, object]] = []
        for el in ui_schema or []:
            if not isinstance(el, dict):
                continue
            if el.get("ui_type") == "status_bar":
                result.append(el)
        return result

    def session_application_ui_elements(self) -> list[dict[str, object]]:
        """Return session-scoped application UI schema elements.

        This method queries application plugins with the session's effective
        config, enabling config-aware UI filtering (e.g., hiding compaction
        actions when compaction is disabled for the session's agent).

        This completes the implementation started in:
        - tasks/20260128-sandboxing-prereqs/040-session-aware-app-plugin-ui-and-conditions.md
        - tasks/20260130-openrouter-usage-round-cost-and-ui-schema/010-config-aware-ui-schema-and-conditions.md
        """
        core, base_config, session = self.require_session()
        return [
            el
            for el in self._app.get_session_application_ui_schema_for_session(
                core,
                base_config,
                session,
            )
            if isinstance(el, dict)
        ]

    # ------------------------------------------------------------------
    # Action-backed command and /action surfaces
    # ------------------------------------------------------------------

    def slash_command_elements(
        self,
        *,
        reserved_names: List[str] | None = None,
    ) -> List[Dict[str, Any]]:
        """Return applicable, collision-checked slash command UI elements."""

        core, base_config, session = self.require_session()
        elements = self._app.get_session_command_ui_elements_for_session(
            core,
            base_config,
            session,
            "slash_command",
            reserved_paths=[(name,) for name in (reserved_names or [])],
        )
        session_context = session.to_dict()
        return [
            element
            for element in elements
            if evaluate_condition(element.get("condition"), session_context)
        ]

    def match_slash_command(
        self,
        tokens: List[str],
        *,
        reserved_names: List[str] | None = None,
    ) -> Tuple[Dict[str, Any] | None, List[str]]:
        return match_command_path(
            self.slash_command_elements(reserved_names=reserved_names),
            tokens,
        )

    def _active_session_context(
        self,
        *,
        message_index: int | None = None,
    ) -> Dict[str, Any]:
        core, base_config, session = self.require_session()
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides = metadata.get("overrides")
        if not isinstance(overrides, dict):
            overrides = {}
        config = resolve_request_config(base_config, overrides)
        try:
            summary = self._app.get_session_summary(session.session_id)
        except Exception:
            summary = session.to_dict()
        context: Dict[str, Any] = {
            "session_id": session.session_id,
            "session": session.to_dict(),
            "session_summary": summary,
            "base_config": base_config,
            "config": config,
            "application_generation": self._application_generation,
        }
        if message_index is not None:
            canonical_index, message = self.show_message(message_index)
            context["message_index"] = canonical_index
            context["message"] = message.to_dict()
        _ = core
        return context

    def action_context(
        self,
        *,
        message_index: int | None = None,
    ) -> Dict[str, Any]:
        """Return the current immutable-by-convention terminal action context."""

        return self._active_session_context(message_index=message_index)

    @staticmethod
    def _element_scope(element: Mapping[str, Any]) -> str:
        ui_type = element.get("ui_type")
        if ui_type == "application_action":
            return "application"
        if ui_type == "session_list_action":
            return "session-list"
        if ui_type == "message_action":
            return "message"
        return str(element.get("scope") or "session")

    @staticmethod
    def _validate_action_ui_element(element: Mapping[str, Any]) -> None:
        identity = f"{element.get('plugin')}.{element.get('id')}"
        fixed = element.get("fixed_params")
        if fixed is not None and not isinstance(fixed, Mapping):
            raise TerminalUserError(f"{identity}.fixed_params must be a mapping")
        mappings = element.get("param_map")
        if mappings is not None:
            prefixes = (
                "$session.",
                "$message.",
                "$dialog.",
                "$form.",
                "$context.",
            )
            if not isinstance(mappings, Mapping) or any(
                not isinstance(name, str)
                or not name
                or not isinstance(source, str)
                or not source.startswith(prefixes)
                for name, source in mappings.items()
            ):
                raise TerminalUserError(
                    f"{identity}.param_map contains an invalid mapping"
                )
        dialog = element.get("dialog")
        if dialog is not None:
            if not isinstance(dialog, Mapping) or dialog.get("kind") not in {
                "none",
                "confirm",
                "form",
            }:
                raise TerminalUserError(
                    f"{identity}.dialog must be none, confirm, or form"
                )
            inputs = dialog.get("inputs")
            if dialog.get("kind") == "form" and (
                inputs is not None
                and (
                    not isinstance(inputs, list)
                    or any(
                        not isinstance(field, Mapping)
                        or not isinstance(field.get("name"), str)
                        or not field.get("name")
                        for field in inputs
                    )
                )
            ):
                raise TerminalUserError(
                    f"{identity}.dialog.inputs contains an invalid field"
                )

    def action_elements(
        self,
        *,
        message_index: int | None = None,
    ) -> List[Dict[str, Any]]:
        """Return applicable action-oriented UI elements for ``/action``."""

        context = self._active_session_context(message_index=message_index)
        session = context["session"]
        summary = context["session_summary"]
        message = context.get("message")

        application_elements = self._app.get_application_ui_schema(
            context={"ui_context": "application"},
        )
        session_elements: List[Dict[str, Any]] = [
            dict(element) for element in self.session_application_ui_elements()
        ]
        session_elements.extend(
            dict(element) for element in self._ui_schema_for_current_effective_config()
        )

        wanted = {"message_action"} if message_index is not None else {
            "application_action",
            "session_action",
            "session_list_action",
        }
        candidates: List[Dict[str, Any]] = []
        if message_index is None:
            candidates.extend(
                dict(element)
                for element in application_elements
                if isinstance(element, dict)
                and element.get("ui_type")
                in {"application_action", "session_list_action"}
            )
        candidates.extend(
            element
            for element in session_elements
            if element.get("ui_type") in wanted
        )

        deduplicated: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        declaration_order: Dict[Tuple[str, str, str], int] = {}
        for position, element in enumerate(candidates):
            ui_type = element.get("ui_type")
            plugin = element.get("plugin")
            element_id = element.get("id")
            action_id = element.get("action_id")
            label = element.get("label")
            if (
                not isinstance(ui_type, str)
                or not ui_type
                or not isinstance(plugin, str)
                or not plugin
                or not isinstance(element_id, str)
                or not element_id
                or not isinstance(action_id, str)
                or not action_id
                or not isinstance(label, str)
                or not label
            ):
                continue
            self._validate_action_ui_element(element)
            root: Any
            if ui_type == "message_action":
                root = {"index": context.get("message_index"), **(message or {})}
            elif ui_type == "session_list_action":
                root = summary
            elif ui_type == "session_action":
                root = session
            else:
                root = context
            if not evaluate_condition(element.get("condition"), root):
                continue
            key = (ui_type, plugin, element_id)
            if key not in declaration_order:
                declaration_order[key] = position
            deduplicated[key] = {
                **element,
                "scope": self._element_scope(element),
            }

        def _sort_key(element: Dict[str, Any]) -> Tuple[int, float, int]:
            order = element.get("order")
            order_value = (
                float(order)
                if isinstance(order, (int, float))
                and not isinstance(order, bool)
                and float(order) == float(order)
                else None
            )
            ordered = isinstance(order_value, float)
            key = (
                str(element.get("ui_type")),
                str(element.get("plugin")),
                str(element.get("id")),
            )
            return (
                0 if ordered else 1,
                order_value if ordered else 0.0,
                declaration_order.get(key, 0),
            )

        return sorted(deduplicated.values(), key=_sort_key)

    def resolve_action_element(
        self,
        element_id: str,
        *,
        plugin: str | None = None,
        scope: str | None = None,
        message_index: int | None = None,
    ) -> Dict[str, Any]:
        matches = [
            element
            for element in self.action_elements(message_index=message_index)
            if element.get("id") == element_id
            and (plugin is None or element.get("plugin") == plugin)
            and (scope is None or element.get("scope") == scope)
        ]
        if not matches:
            raise TerminalUserError(
                f"no applicable action element matches {element_id!r}"
            )
        if len(matches) > 1:
            choices = ", ".join(
                f"{item['scope']}:{item['plugin']}:{item['id']}"
                for item in matches
            )
            raise TerminalUserError(
                f"ambiguous action element {element_id!r}; choose one of {choices}"
            )
        element = matches[0]
        if element.get("disabled") is True:
            reason = element.get("disabled_reason") or element.get("description")
            suffix = f": {reason}" if isinstance(reason, str) and reason else ""
            raise TerminalUserError(f"action {element_id!r} is disabled{suffix}")
        return element

    @staticmethod
    def _resolve_mapping_path(root: Any, path: str) -> Tuple[bool, Any]:
        current = root
        for part in [piece for piece in path.split(".") if piece]:
            if not isinstance(current, Mapping) or part not in current:
                return False, None
            current = current[part]
        return True, current

    def _mapped_action_inputs(
        self,
        element: Mapping[str, Any],
        context: Mapping[str, Any],
        *,
        dialog_values: Mapping[str, Any] | None = None,
        form_values: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        fixed = element.get("fixed_params")
        inputs: Dict[str, Any] = dict(fixed) if isinstance(fixed, Mapping) else {}
        mappings = element.get("param_map")
        if not isinstance(mappings, Mapping):
            return inputs
        raw_message = context.get("message")
        message_values = dict(raw_message) if isinstance(raw_message, Mapping) else {}
        roots: Dict[str, Any] = {
            "session": (
                context.get("session_summary")
                if element.get("ui_type") == "session_list_action"
                else context.get("session")
            ),
            "message": (
                {
                    "index": context.get("message_index"),
                    **message_values,
                }
            ),
            "dialog": dialog_values or {},
            "form": form_values or {},
            "context": context,
        }
        for name, source in mappings.items():
            if not isinstance(name, str) or not isinstance(source, str):
                continue
            if not source.startswith("$") or "." not in source:
                continue
            prefix, _, path = source[1:].partition(".")
            if prefix not in roots:
                continue
            found, value = self._resolve_mapping_path(roots[prefix], path)
            if found:
                inputs[name] = value
        return inputs

    def execute_ui_element(
        self,
        element: Mapping[str, Any],
        *,
        context: Mapping[str, Any] | None = None,
        dialog_values: Mapping[str, Any] | None = None,
        form_values: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Map and execute one preflighted action-backed UI element."""

        if element.get("disabled") is True:
            reason = element.get("disabled_reason") or element.get("description")
            suffix = f": {reason}" if isinstance(reason, str) and reason else ""
            raise TerminalUserError(f"action is disabled{suffix}")
        effective_context = dict(context or self._active_session_context())
        if (
            element.get("ui_type") == "application_action"
            or (
                element.get("ui_type") in {"cli_command", "slash_command"}
                and element.get("scope") == "application"
            )
        ):
            effective_context = {
                "application_generation": effective_context.get(
                    "application_generation",
                    self._application_generation,
                )
            }
        if (
            effective_context.get("application_generation")
            not in {None, self._application_generation}
        ):
            raise TerminalUserError(
                "action reference belongs to a replaced application"
            )
        plugin = element.get("plugin")
        action_id = element.get("action_id")
        if not isinstance(plugin, str) or not plugin:
            raise TerminalUserError("action element is missing plugin")
        if not isinstance(action_id, str) or not action_id:
            raise TerminalUserError("action element is missing action_id")
        params = self._mapped_action_inputs(
            element,
            effective_context,
            dialog_values=dialog_values,
            form_values=form_values,
        )
        executed = self._app.execute_action_with_metadata(
            plugin,
            action_id,
            params,
            action_owner=(
                element.get("action_owner")
                if isinstance(element.get("action_owner"), str)
                else None
            ),
            context=effective_context,
        )
        session_id = effective_context.get("session_id")
        if isinstance(session_id, str) and self._session is not None:
            loaded = self._app.load_session(session_id)
            if loaded is not None and session_id == self._session.session_id:
                self._core, self._base_config, self._session = loaded
                self._ui_schema_cache_key = None
                self._ui_schema_cache = None
        return executed.result

    def execute_action_element(
        self,
        element_id: str,
        *,
        plugin: str | None = None,
        scope: str | None = None,
        message_index: int | None = None,
        dialog_values: Mapping[str, Any] | None = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        element = self.resolve_action_element(
            element_id,
            plugin=plugin,
            scope=scope,
            message_index=message_index,
        )
        context = self._active_session_context(message_index=message_index)
        return (
            self.execute_ui_element(
                element,
                context=context,
                dialog_values=dialog_values,
            ),
            element,
            context,
        )

    def register_run_action_followup(
        self,
        action: Mapping[str, Any],
        display: Mapping[str, Any],
        context: Mapping[str, Any],
        *,
        notification: Mapping[str, Any] | None = None,
    ) -> str:
        """Register a direct or notification ``run_action`` follow-up."""

        if action.get("kind") != "run_action":
            raise TerminalUserError("follow-up is not a run_action")
        required = (action.get("id"), action.get("plugin"), action.get("action_id"))
        if not all(isinstance(value, str) and value for value in required):
            raise TerminalUserError("run_action follow-up is malformed")
        self._app.validate_action_binding(
            action["plugin"],
            action["action_id"],
            action_owner=(
                action.get("action_owner")
                if isinstance(action.get("action_owner"), str)
                else None
            ),
            context=dict(context),
        )

        reference: str | None = None
        notification_key: Tuple[str, str, str, str] | None = None
        stored_notification: Dict[str, Any] | None = None
        if isinstance(notification, Mapping):
            scope = notification.get("scope")
            notification_id = notification.get("notification_id")
            session_id = notification.get("session_id")
            action_id = action.get("id")
            if (
                isinstance(scope, str)
                and scope
                and isinstance(notification_id, str)
                and notification_id
                and isinstance(action_id, str)
                and action_id
            ):
                notification_key = (
                    scope,
                    session_id if isinstance(session_id, str) else "",
                    notification_id,
                    action_id,
                )
                reference = self._notification_reference_ids.get(notification_key)
                stored_notification = {
                    **notification,
                    "followup_id": action_id,
                }
        if reference is None:
            prefix = "notification" if notification_key is not None else "result"
            reference = f"{prefix}-{self._next_action_reference}"
            self._next_action_reference += 1
        if notification_key is not None:
            self._notification_reference_ids[notification_key] = reference
        else:
            display_id = display.get("display_id")
            if isinstance(display_id, str) and display_id:
                self._direct_display_references.setdefault(display_id, set()).add(
                    reference
                )
                self._direct_reference_displays[reference] = display_id

        self._action_references[reference] = {
            "element": {
                "ui_type": "action_result_followup",
                "plugin": action["plugin"],
                "id": action["id"],
                "label": action.get("label") or action["id"],
                "action_id": action["action_id"],
                "action_owner": action.get("action_owner"),
                "fixed_params": action.get("fixed_params"),
                "param_map": action.get("param_map"),
                "dialog": action.get("dialog"),
                "form": display.get("form"),
                "preserve_display": action.get("preserve_display"),
            },
            "context": dict(context),
            "notification": stored_notification,
        }
        return reference

    def begin_action_display(self, display: Mapping[str, Any]) -> None:
        """Supersede direct references owned by an existing ``display_id``."""

        display_id = display.get("display_id")
        if not isinstance(display_id, str) or not display_id:
            return
        for reference in self._direct_display_references.pop(display_id, set()):
            self._action_references.pop(reference, None)
            self._direct_reference_displays.pop(reference, None)
        self._direct_display_references[display_id] = set()

    def get_action_reference(self, reference: str) -> Dict[str, Any]:
        entry = self._action_references.get(reference)
        if not isinstance(entry, dict):
            raise TerminalUserError(f"unknown or expired action reference {reference!r}")
        notification = entry.get("notification")
        if isinstance(notification, Mapping):
            return self._refresh_notification_reference(reference, entry)
        return entry

    def _authoritative_notification(
        self,
        *,
        scope: str,
        notification_id: str,
        session_id: str | None,
    ) -> Dict[str, Any] | None:
        try:
            if scope == "application":
                items = self._app.list_application_notifications(include_terminal=True)
            elif (
                scope == "session"
                and isinstance(session_id, str)
                and self._session is not None
                and session_id == self._session.session_id
            ):
                items = self._app.list_session_notifications(
                    session_id,
                    include_terminal=True,
                )
            else:
                return None
        except Exception:
            return None
        return next(
            (
                item
                for item in items
                if isinstance(item, dict) and item.get("id") == notification_id
            ),
            None,
        )

    def _refresh_notification_reference(
        self,
        reference: str,
        entry: Mapping[str, Any],
    ) -> Dict[str, Any]:
        metadata = entry.get("notification")
        if not isinstance(metadata, Mapping):
            raise TerminalUserError("notification reference metadata is invalid")
        scope = metadata.get("scope")
        notification_id = metadata.get("notification_id")
        session_id = metadata.get("session_id")
        followup_id = metadata.get("followup_id")
        if (
            not isinstance(scope, str)
            or not scope
            or not isinstance(notification_id, str)
            or not notification_id
            or not isinstance(followup_id, str)
            or not followup_id
        ):
            raise TerminalUserError("notification reference metadata is invalid")
        current = self._authoritative_notification(
            scope=scope,
            notification_id=notification_id,
            session_id=session_id if isinstance(session_id, str) else None,
        )
        if current is None or not is_active_notification(current):
            self._action_references.pop(reference, None)
            raise TerminalUserError("notification is no longer active")
        display = current.get("display")
        if not isinstance(display, Mapping):
            self._action_references.pop(reference, None)
            raise TerminalUserError(
                "notification follow-up display is no longer available"
            )
        actions = display.get("actions")
        action = next(
            (
                item
                for item in (actions or [])
                if isinstance(item, Mapping)
                and item.get("kind") == "run_action"
                and item.get("id") == followup_id
            ),
            None,
        )
        if action is None:
            self._action_references.pop(reference, None)
            raise TerminalUserError(
                "notification follow-up is no longer available"
            )
        context = self._active_session_context()
        refreshed_metadata = {
            "scope": scope,
            "session_id": session_id,
            "notification_id": notification_id,
            "revision": notification_revision_token(current),
            "followup_id": followup_id,
        }
        self.register_run_action_followup(
            action,
            display,
            context,
            notification=refreshed_metadata,
        )
        return self._action_references[reference]

    def execute_action_reference(
        self,
        reference: str,
        *,
        dialog_values: Mapping[str, Any] | None = None,
        form_values: Mapping[str, Any] | None = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        entry = self.get_action_reference(reference)
        element = entry["element"]
        context = entry["context"]
        result = self.execute_ui_element(
            element,
            context=context,
            dialog_values=dialog_values,
            form_values=form_values,
        )
        if element.get("preserve_display") is not True:
            self._action_references.pop(reference, None)
            display_id = self._direct_reference_displays.pop(reference, None)
            if isinstance(display_id, str):
                references = self._direct_display_references.get(display_id)
                if references is not None:
                    references.discard(reference)
        return result, element, context

    # ------------------------------------------------------------------
    # Automatic application/current-session notifications
    # ------------------------------------------------------------------

    def _notification_identity(
        self,
        scope: str,
        notification: Mapping[str, Any],
        session_id: str | None,
    ) -> Tuple[str, str | None, str] | None:
        notification_id = notification.get("id")
        if not isinstance(notification_id, str) or not notification_id:
            return None
        return scope, session_id, notification_id

    def _retire_notification_references(
        self,
        scope: str,
        notification_id: str,
        session_id: str | None,
    ) -> None:
        normalized_session_id = session_id or ""
        keys = [
            key
            for key in self._notification_reference_ids
            if key[0] == scope
            and key[1] == normalized_session_id
            and key[2] == notification_id
        ]
        for key in keys:
            reference = self._notification_reference_ids.pop(key)
            self._action_references.pop(reference, None)

    def _supersede_notification_references(
        self,
        scope: str,
        notification_id: str,
        session_id: str | None,
        notification: Mapping[str, Any],
    ) -> None:
        display = notification.get("display")
        actions = display.get("actions") if isinstance(display, Mapping) else None
        current_ids = {
            action.get("id")
            for action in (actions or [])
            if isinstance(action, Mapping)
            and action.get("kind") == "run_action"
            and isinstance(action.get("id"), str)
            and action.get("id")
        }
        normalized_session_id = session_id or ""
        obsolete = [
            key
            for key in self._notification_reference_ids
            if key[0] == scope
            and key[1] == normalized_session_id
            and key[2] == notification_id
            and key[3] not in current_ids
        ]
        for key in obsolete:
            reference = self._notification_reference_ids.pop(key)
            self._action_references.pop(reference, None)

    def _accept_notification(
        self,
        scope: str,
        notification: Mapping[str, Any],
        *,
        session_id: str | None = None,
    ) -> Dict[str, Any] | None:
        identity = self._notification_identity(scope, notification, session_id)
        if identity is None:
            return None
        revision = notification_revision_token(notification)
        previous = self._notification_versions.get(identity)
        if previous is not None:
            if isinstance(previous, int) and isinstance(revision, int):
                if revision <= previous:
                    return None
            elif str(revision) <= str(previous):
                return None
        self._notification_versions[identity] = revision
        if not is_active_notification(notification):
            self._retire_notification_references(
                scope,
                identity[2],
                session_id,
            )
            return None
        self._supersede_notification_references(
            scope,
            identity[2],
            session_id,
            notification,
        )
        return {
            "scope": scope,
            "session_id": session_id,
            "notification": dict(notification),
        }

    def _hydrate_notifications(self) -> List[Dict[str, Any]]:
        updates: List[Dict[str, Any]] = []
        application_loaded = False
        try:
            application_items = self._app.list_application_notifications(
                include_terminal=False
            )
            application_loaded = True
        except Exception:
            application_items = []
        active_application_ids: set[str] = set()
        for notification in application_items:
            if isinstance(notification, Mapping):
                notification_id = notification.get("id")
                if isinstance(notification_id, str) and notification_id:
                    active_application_ids.add(notification_id)
                accepted = self._accept_notification(
                    "application",
                    notification,
                )
                if accepted is not None:
                    updates.append(accepted)
        if application_loaded:
            for scope, _session_id, notification_id in list(
                self._notification_versions
            ):
                if (
                    scope == "application"
                    and notification_id not in active_application_ids
                ):
                    self._retire_notification_references(
                        "application",
                        notification_id,
                        None,
                    )

        if self._session is not None:
            session_id = self._session.session_id
            session_loaded = False
            try:
                session_items = self._app.list_session_notifications(
                    session_id,
                    include_terminal=False,
                )
                session_loaded = True
            except Exception:
                session_items = []
            active_session_ids: set[str] = set()
            for notification in session_items:
                if isinstance(notification, Mapping):
                    notification_id = notification.get("id")
                    if isinstance(notification_id, str) and notification_id:
                        active_session_ids.add(notification_id)
                    accepted = self._accept_notification(
                        "session",
                        notification,
                        session_id=session_id,
                    )
                    if accepted is not None:
                        updates.append(accepted)
            if session_loaded:
                for scope, known_session_id, notification_id in list(
                    self._notification_versions
                ):
                    if (
                        scope == "session"
                        and known_session_id == session_id
                        and notification_id not in active_session_ids
                    ):
                        self._retire_notification_references(
                            "session",
                            notification_id,
                            session_id,
                        )
        return updates

    def poll_notification_updates(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Return newly accepted application/current-session notifications."""

        store = self._app.get_event_store()
        updates: List[Dict[str, Any]] = []
        if self._notification_hydration_required:
            try:
                self._notification_event_id = store.get_latest_event_id()
            except Exception:
                self._notification_event_id = None
            updates.extend(self._hydrate_notifications())
            self._notification_hydration_required = False

        listed = store.list(
            since_id=self._notification_event_id,
            request_id=None,
            session_id=None,
            limit=limit,
        )
        if listed.get("cursor_expired"):
            self._notification_hydration_required = True
            return [*updates, *self.poll_notification_updates(limit=limit)]
        events = listed.get("events") or []
        for event in events:
            if not isinstance(event, Mapping):
                continue
            event_type = event.get("type")
            notification = event.get("notification")
            if not isinstance(notification, Mapping):
                continue
            if isinstance(event_type, str) and event_type.startswith(
                "application_notification_"
            ):
                accepted = self._accept_notification(
                    "application",
                    notification,
                )
            elif isinstance(event_type, str) and event_type.startswith(
                "session_notification_"
            ):
                event_session_id = event.get("session_id")
                if (
                    self._session is None
                    or event_session_id != self._session.session_id
                ):
                    continue
                accepted = self._accept_notification(
                    "session",
                    notification,
                    session_id=event_session_id,
                )
            else:
                continue
            if accepted is not None:
                updates.append(accepted)
        if events:
            event_id = events[-1].get("event_id")
            if isinstance(event_id, str):
                self._notification_event_id = event_id
        return updates

    def get_last_assistant_message(self) -> Optional[Dict[str, Any]]:
        """Get the last assistant message from the active session.

        Returns:
            Dictionary representation of the last assistant message, or None
            if no assistant messages exist.
        """
        try:
            session = self.session
        except RuntimeError:
            return None

        # Iterate backwards to find the last assistant message
        for message in reversed(session.messages):
            msg_dict = message.to_dict()
            if msg_dict.get("role") == "assistant":
                return msg_dict

        return None

    def get_application_config_schema(self) -> Dict[str, Dict[str, Any]]:
        """Return schema for application-level configuration keys.

        The schema describes options under the top-level "application"
        section of the config that are consumed by the terminal app
        itself (for example, tool output rendering limits).
        """

        return {
            "tool_output_line_limit": {
                "type": "int",
                "default": 100,
                "description": "Maximum number of lines of tool output shown per tool call (full view).",
            },
            "tool_output_char_limit": {
                "type": "int",
                "default": 8000,
                "description": "Maximum number of characters of tool output shown per tool call (full view).",
            },
            "tool_output_short_char_limit": {
                "type": "int",
                "default": 200,
                "description": "Maximum characters of tool output shown in short view (e.g. /list short).",
            },
            "tool_output_short_one_line": {
                "type": "bool",
                "default": True,
                "description": "If true, short tool output is rendered on a single condensed line.",
            },
            "tool_output_short_line_limit": {
                "type": "int",
                "default": 20,
                "description": "Maximum number of lines for short tool output when one-line mode is disabled.",
            },
            "tool_output_live_one_line": {
                "type": "bool",
                "default": False,
                "description": "If true, live tool results use one-line previews at startup (change at runtime with /tool-output).",
            },
            "terminal_startup_help": {
                "type": "string",
                "default": "summary",
                "description": "Startup guidance mode: summary, hint, or off.",
            },
        }

    def update_override(self, key: str, value: Any) -> Session:
        session = self.session

        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides_val = metadata.get("overrides")
        overrides: Dict[str, Any] = (
            overrides_val if isinstance(overrides_val, dict) else {}
        )

        new_overrides = {**overrides, key: value}
        new_metadata = {**metadata, "overrides": new_overrides}

        new_session = Session(
            session_id=session.session_id,
            messages=session.messages,
            metadata=new_metadata,
        )
        self._app.save_session(new_session)

        ctx = self._app.load_session(new_session.session_id)
        if ctx is not None:
            core, base_config, loaded_session = ctx
            self._core = core
            self._base_config = base_config
            self._session = loaded_session
            return loaded_session

        self._session = new_session
        return new_session

    def list_agents(self) -> List[str]:
        """Legacy alias returning the available agents."""

        return self.available_agents()

    # ------------------------------------------------------------------
    # Plugins
    # ------------------------------------------------------------------

    def list_plugins_for_session(self) -> List[Dict[str, Any]]:
        """Return plugin metadata with enabled state for the active session.

        The result is derived from the session's ``metadata['plugins']``
        list when present; otherwise from the agent-level default plugin
        configuration. When neither is present, all plugins are treated
        as enabled (implicit default).
        """

        core, base_config, session = self.require_session()
        metadata = session.metadata or {}

        agent_val = metadata.get("agent_id")
        agent_id = agent_val.strip() if isinstance(agent_val, str) else ""
        if not agent_id:
            agents = self.available_agents()
            agent_id = agents[0] if agents else ""

        all_plugins = (
            self._app.list_plugins_for_agent(agent_id)
            if agent_id
            else self._app.list_plugins()
        )

        plugins_from_session = metadata.get("plugins")
        if isinstance(plugins_from_session, list):
            enabled_ids: Optional[set[str]] = {
                p for p in plugins_from_session if isinstance(p, str)
            }
            source = "session"
        else:
            default_ids = self._app.get_agent_plugins(agent_id) if agent_id else None
            if default_ids is None:
                enabled_ids = None  # treat as "all enabled"
                source = "implicit"
            else:
                enabled_ids = {p for p in default_ids if isinstance(p, str)}
                source = "agent"

        overrides_val = metadata.get("overrides")
        overrides: Dict[str, Any] = (
            overrides_val if isinstance(overrides_val, dict) else {}
        )
        config = resolve_request_config(base_config, overrides)

        try:
            active_by_kind = core.get_plugins_for_config(config)
        except Exception:
            active_by_kind = None

        def _is_active(kind: str, pid: str) -> bool:
            if not isinstance(active_by_kind, dict):
                return True
            raw = active_by_kind.get(kind)
            if not isinstance(raw, list):
                return True
            return pid in raw

        result: List[Dict[str, Any]] = []
        for entry in all_plugins:
            pid = entry.get("id")
            if not isinstance(pid, str) or not pid:
                continue

            kind_val = entry.get("kind")
            kind = kind_val if isinstance(kind_val, str) else ""

            if enabled_ids is None:
                enabled = True
                src = "implicit"
            else:
                enabled = pid in enabled_ids
                src = source

            active = _is_active(kind, pid)

            result.append(
                {**entry, "enabled": enabled, "source": src, "active": active}
            )

        return result

    def set_session_plugins(self, enabled_ids: List[str]) -> Session:
        """Persist an explicit list of enabled plugin ids for this session.

        The provided list is normalized to unique string ids while
        preserving order. After saving, the active core and base
        configuration are reloaded from the underlying AgentApplication
        so subsequent requests use the updated plugin set.
        """

        session = self.session
        metadata = session.metadata if isinstance(session.metadata, dict) else {}

        seen: Dict[str, None] = {}
        normalized: List[str] = []
        for pid in enabled_ids:
            if not isinstance(pid, str) or not pid:
                continue
            if pid in seen:
                continue
            seen[pid] = None
            normalized.append(pid)

        new_metadata = {**metadata, "plugins": normalized}

        new_session = Session(
            session_id=session.session_id,
            messages=session.messages,
            metadata=new_metadata,
        )
        self._app.save_session(new_session)

        ctx = self._app.load_session(new_session.session_id)
        if ctx is not None:
            core, base_config, loaded_session = ctx
            self._core = core
            self._base_config = base_config
            self._session = loaded_session
            self._last_event_id = None

        return self.session

    def clear_session_plugins(self) -> Session:
        """Remove any session-specific plugin overrides.

        After clearing, the effective plugin set is derived from the
        agent-level defaults (or implicit all-enabled behaviour).
        """

        session = self.session
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        if "plugins" not in metadata:
            return session

        new_metadata = dict(metadata)
        new_metadata.pop("plugins", None)

        new_session = Session(
            session_id=session.session_id,
            messages=session.messages,
            metadata=new_metadata,
        )
        self._app.save_session(new_session)

        ctx = self._app.load_session(new_session.session_id)
        if ctx is not None:
            core, base_config, loaded_session = ctx
            self._core = core
            self._base_config = base_config
            self._session = loaded_session
            self._last_event_id = None

        return self.session
