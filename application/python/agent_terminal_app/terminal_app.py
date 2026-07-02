from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from agent_app.application_future import AgentApplication
from agent_app.config import resolve_request_config
from agent_core import Session


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
        env_overrides: Mapping[str, str] | None = None,
    ) -> None:
        self._session_root: Path = Path(session_root)

        if agent_app is not None:
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

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def agent_app(self) -> AgentApplication:
        return self._app

    def close(self) -> None:
        """Release resources owned by the underlying application."""

        self._app.close()

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
        if (
            cache_key == self._ui_schema_cache_key
            and self._ui_schema_cache is not None
        ):
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

    def start_new_session(self, agent_id: Optional[str] = None, *, persist: bool = True) -> Session:
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
        return session

    def list_sessions_metadata(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return metadata for stored sessions ordered by modification time.

        Each entry contains ``session_id``, ``modified`` (float timestamp),
        and ``preview`` (first user message snippet).
        """

        root = self._session_root
        try:
            exists = root.exists()
        except Exception:
            return []
        if not exists:
            return []

        items: List[Dict[str, Any]] = []
        for path in root.glob("*.json"):
            try:
                stat = path.stat()
            except OSError:
                continue

            session_id = path.stem
            preview = ""

            try:
                data = path.read_text(encoding="utf-8")
                raw = json.loads(data)
                messages = raw.get("messages") or []
                for msg in messages:
                    if not isinstance(msg, dict):
                        continue
                    if msg.get("role") != "user":
                        continue
                    content = msg.get("content")
                    if isinstance(content, str) and content:
                        single = " ".join(content.split())
                        if len(single) > 80:
                            preview = single[:77] + "..."
                        else:
                            preview = single
                        break
            except Exception:
                preview = ""

            items.append(
                {
                    "session_id": session_id,
                    "modified": float(stat.st_mtime),
                    "preview": preview,
                }
            )

        items.sort(key=lambda entry: entry["modified"], reverse=True)
        if limit is not None and limit >= 0:
            items = items[:limit]
        return items

    def switch_session(self, session_id: str) -> Session:
        """Load an existing session by id and make it active."""
        if not isinstance(session_id, str) or not session_id:
            raise TerminalUserError("session_id must be a non-empty string")

        try:
            ctx = self._app.load_session(session_id)
        except KeyError as exc:
            detail = exc.args[0] if exc.args and isinstance(exc.args[0], str) else str(exc)
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
            self._last_event_id = self._app.get_session_cursor_event_id(session.session_id)
        except Exception:  # pragma: no cover - defensive
            self._last_event_id = None
        return session

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    def append_user_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Session:
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


    def send_request(
        self,
        *,
        stream: bool = True,
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
        """Run the core send_request loop for the active session.

        Configuration overrides are loaded from the session's metadata
        under ``overrides`` and passed to the core. Explicit overrides
        are not supported at the terminal level.
        """

        core, base_config, session = self.require_session()

        overrides = session.metadata.get("overrides")
        with self._app.acquire_session_lock(session.session_id):
            baseline_file_state = self._app.get_session_file_state(session.session_id)

        final_session_dict: Optional[Dict[str, Any]] = session.to_dict()
        final_messages: List[Dict[str, Any]] = []
        request_id: Optional[str] = None

        store = self._app.get_event_store()

        for ev in self._app.send_request(
            core,
            session,
            base_config,
            overrides,
            stream=stream,
            baseline_file_state=baseline_file_state,
        ):
            etype = ev.get("type")

            # Internal checkpoint events carry the live Session object so the
            # terminal can track progress incrementally. They are not
            # published to the shared event store or exposed over the
            # network.
            if etype == "session_checkpoint":
                session_obj = ev.get("session")
                if isinstance(session_obj, Session):
                    self._session = session_obj
                    try:
                        final_session_dict = session_obj.to_dict()
                    except Exception:  # pragma: no cover - defensive
                        pass
                continue

            stored = store.publish(ev)

            if stored.get("type") == "final":
                final_messages = stored.get("messages") or []
                request_id = stored.get("request_id")
            elif "session" in stored and isinstance(stored.get("session"), dict):
                # Backwards compatibility for older event shapes that include
                # a serialized session payload.
                final_session_dict = stored["session"]

        if final_session_dict is not None:
            try:
                final_session = Session.from_dict(final_session_dict)
                self._session = final_session
            except Exception:  # pragma: no cover - defensive
                pass

        return final_session_dict, final_messages, request_id

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
        return (store.list(
            since_id=since_id,
            request_id=request_id,
            session_id=sid,
            limit=limit,
        ).get("events") or [])

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

        normalized_role = role if role in {"system", "user", "assistant", "tool"} else "user"

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

        if self._session is not None and self._session.session_id == new_session.session_id:
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
        core, base_config, new_session = self._app.update_agent(target_agent_id, session)

        # Decide whether to persist:
        # - If the session has messages, always save.
        # - If it is empty but was previously saved, update the file.
        # - If it is empty and has never been saved (initial ephemeral
        #   session), keep it purely in memory.
        session_path = self._session_root / f"{session.session_id}.json"
        is_empty = not session.messages
        is_persisted = session_path.exists()
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

        all_plugins = self._app.list_plugins_for_agent(agent_id) if agent_id else self._app.list_plugins()

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
