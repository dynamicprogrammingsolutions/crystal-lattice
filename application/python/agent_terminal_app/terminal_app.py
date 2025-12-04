from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent_app.application_future import AgentApplication
from agent_core import Session


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
    ) -> None:
        if agent_app is not None:
            self._app = agent_app
        else:
            root = Path(session_root)
            root.mkdir(parents=True, exist_ok=True)
            self._app = AgentApplication(str(config_path), str(root))

        self._session: Session | None = None
        self._last_event_id: str | None = None

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def agent_app(self) -> AgentApplication:
        return self._app

    @property
    def session(self) -> Session:
        if self._session is None:
            raise RuntimeError("No active session; create one first")
        return self._session

    @property
    def session_id(self) -> str:
        return self.session.session_id

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------


    def start_new_session(self, system_message: Optional[str] = None, agent_id: Optional[str] = None) -> Session:
        """Start a new active session, replacing any previous one."""

        if agent_id is None and self._session is not None:
            metadata = self._session.metadata or {}
            current_agent = metadata.get("agent_id")
            agent_id = current_agent if isinstance(current_agent, str) and current_agent else "default"
        elif agent_id is None:
            agent_id = "default"

        core, _base_config, base_session = self._app.create_session(agent_id)
        session = base_session

        if isinstance(system_message, str) and system_message:
            session = core.add_message(session, "system", system_message)
            self._app.save_session(session)

        store = self._app.get_event_store()
        store.publish(
            {
                "type": "session_created",
                "session_id": session.session_id,
                "agent_id": agent_id,
                "session": session.to_dict(),
            }
        )

        self._session = session
        self._last_event_id = None
        return session

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    def append_user_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Session:
        """Append a user message to the active session."""

        if self._session is None:
            raise RuntimeError("No active session; cannot append message")

        ctx = self._app.load_session(self._session.session_id)
        if ctx is None:
            raise KeyError(f"Session {self._session.session_id!r} not found")

        core, _base_config, session = ctx
        new_session = core.add_message(session, "user", content, metadata)
        self._app.save_session(new_session)

        last_message = new_session.messages[-1] if new_session.messages else None

        store = self._app.get_event_store()
        store.publish(
            {
                "type": "message_appended",
                "session_id": new_session.session_id,
                "role": "user",
                "content": content,
                "metadata": metadata or {},
                "message": last_message.to_dict() if last_message is not None else None,
                "session": new_session.to_dict(),
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
        overrides: Optional[Dict[str, Any]] = None,
        stream: bool = True,
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
        """Run the core send_request loop for the active session.

        Configuration overrides are loaded from the session's metadata
        under ``overrides`` and merged with any explicit ``overrides``
        mapping provided to this function (explicit values winning).
        """

        if self._session is None:
            raise RuntimeError("No active session; cannot send request")

        if overrides is not None and not isinstance(overrides, dict):
            raise ValueError("config_overrides must be a mapping if provided")

        ctx = self._app.load_session(self._session.session_id)
        if ctx is None:
            raise KeyError(f"Session {self._session.session_id!r} not found")

        core, base_config, session = ctx

        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        stored_val = metadata.get("overrides")
        stored_overrides: Dict[str, Any] = dict(stored_val) if isinstance(stored_val, dict) else {}

        if overrides is None:
            effective_overrides: Optional[Dict[str, Any]] = dict(stored_overrides) if stored_overrides else None
        else:
            base = dict(stored_overrides) if stored_overrides else {}
            effective_overrides = {**base, **overrides}

        final_session_dict: Optional[Dict[str, Any]] = session.to_dict()
        final_messages: List[Dict[str, Any]] = []
        request_id: Optional[str] = None

        store = self._app.get_event_store()

        for ev in self._app.send_request(core, session, base_config, effective_overrides, stream=stream):
            stored = store.publish(ev)

            if stored.get("type") == "final":
                final_session_dict = stored.get("session") or final_session_dict
                final_messages = list(stored.get("messages") or [])
                request_id = stored.get("request_id")
            elif "session" in stored and isinstance(stored.get("session"), dict):
                final_session_dict = stored["session"]

        if final_session_dict is not None:
            try:
                final_session = Session.from_dict(final_session_dict)
                self._app.save_session(final_session)
                self._session = final_session
            except Exception:  # pragma: no cover - defensive
                pass

        return final_session_dict, final_messages, request_id


    def poll_new_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return events for the active session since the last poll."""

        if self._session is None:
            return []

        store = self._app.get_event_store()
        events = store.list(
            since_id=self._last_event_id,
            request_id=None,
            session_id=self._session.session_id,
            limit=limit,
        )
        if events:
            last = events[-1].get("event_id")
            if isinstance(last, str):
                self._last_event_id = last
        return events


    def reset_event_cursor(self) -> None:
        self._last_event_id = None

    # ------------------------------------------------------------------
    # Agents and configuration
    # ------------------------------------------------------------------

    def current_agent_id(self) -> str:
        if self._session is None:
            return "default"
        metadata = self._session.metadata or {}
        agent = metadata.get("agent_id")
        return agent if isinstance(agent, str) and agent else "default"

    def available_agents(self) -> List[str]:
        try:
            agents = self._app.list_agents()
        except Exception:
            agents = ["default"]

        agents = [a for a in agents if isinstance(a, str) and a]
        # Deduplicate while preserving insertion order, then sort.
        unique: Dict[str, None] = {}
        for agent in agents:
            if agent not in unique:
                unique[agent] = None
        return sorted(unique.keys())

    def switch_agent(self, target_agent_id: str) -> Session:
        if self._session is None:
            raise RuntimeError("No active session; cannot switch agent")

        if target_agent_id not in self.available_agents():
            raise KeyError(f"Unknown agent: {target_agent_id!r}")

        metadata = self._session.metadata or {}
        new_metadata = {**metadata, "agent_id": target_agent_id}
        new_session = Session(
            session_id=self._session.session_id,
            messages=list(self._session.messages),
            metadata=new_metadata,
        )
        self._app.save_session(new_session)
        self._session = new_session
        self._last_event_id = None
        return new_session



    def _flatten_ui_schema(self, ui_schema: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        flat: Dict[str, Dict[str, Any]] = {}

        for el in ui_schema or []:
            if not isinstance(el, dict):
                continue
            key = el.get("key")
            if not isinstance(key, str) or not key:
                continue

            ui_type = el.get("ui_type", "config")
            if ui_type != "config":
                continue

            entry = flat.get(key)
            if entry is None:
                entry = {"key": key, "type": el.get("type"), "options": []}
                flat[key] = entry

            opts = el.get("options") or []
            if isinstance(opts, list):
                for opt in opts:
                    if isinstance(opt, dict):
                        val = opt.get("value")
                        if isinstance(val, str) and val not in entry["options"]:
                            entry["options"].append(val)
                    elif isinstance(opt, str) and opt not in entry["options"]:
                        entry["options"].append(opt)

        return sorted(flat.values(), key=lambda e: e["key"])

    def session_ui_elements(self) -> List[Dict[str, Any]]:
        if self._session is None:
            return []

        ctx = self._app.load_session(self._session.session_id)
        if ctx is None:
            return []
        core, _base_config, _session = ctx
        try:
            ui_schema = core.get_ui_schema()
        except Exception:
            return []
        return self._flatten_ui_schema(ui_schema)


    def update_override(self, key: str, value: Any) -> Session:
        if self._session is None:
            raise RuntimeError("No active session; cannot update overrides")

        metadata = self._session.metadata if isinstance(self._session.metadata, dict) else {}
        overrides_val = metadata.get("overrides")
        overrides: Dict[str, Any] = dict(overrides_val) if isinstance(overrides_val, dict) else {}

        new_overrides = {**overrides, key: value}
        new_metadata = {**metadata, "overrides": new_overrides}

        new_session = Session(
            session_id=self._session.session_id,
            messages=list(self._session.messages),
            metadata=new_metadata,
        )
        self._app.save_session(new_session)
        self._session = new_session
        return new_session


    def list_agents(self) -> List[str]:
        """Legacy alias returning the available agents."""

        return self.available_agents()
