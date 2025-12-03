from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:  # Optional convenience in local usage
    from dotenv import load_dotenv  # type: ignore[import-not-found]

    load_dotenv()
except Exception:  # pragma: no cover - optional dependency
    pass

from fastapi import FastAPI, HTTPException  # type: ignore[reportMissingImports]

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import Session


_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config_openrouter_app_layer.json"
_DEFAULT_SESSION_ROOT = Path(__file__).resolve().parent / "sessions"


class ServerApplication:
    """Server-side application wrapping AgentApplication and event store.

    This class owns its own :class:`AgentApplication` instance and an
    :class:`InMemoryEventStore`. FastAPI routes call methods on this
    class instead of sharing helpers with the terminal application.
    """

    def __init__(
        self,
        *,
        config_path: str | Path,
        session_root: str | Path,
        agent_app: Optional[AgentApplication] = None,
        event_store: Optional[InMemoryEventStore] = None,
    ) -> None:
        cfg = Path(config_path)
        root = Path(session_root)
        root.mkdir(parents=True, exist_ok=True)

        self._agent_app = agent_app or AgentApplication(str(cfg), str(root))
        self._events = event_store or InMemoryEventStore()

    @property
    def agent_app(self) -> AgentApplication:
        return self._agent_app

    @property
    def event_store(self) -> InMemoryEventStore:
        return self._events

    def create_session(self, agent_id: str, system_message: Optional[str]) -> Session:
        """Create and persist a session, publishing ``session_created``."""

        core, base_config, session = self._agent_app.create_session(agent_id)

        if isinstance(system_message, str) and system_message:
            session = core.add_message(session, "system", system_message)
            self._agent_app.save_session(session)

        self._events.publish(
            {
                "type": "session_created",
                "session_id": session.session_id,
                "agent_id": agent_id,
                "session": session.to_dict(),
            }
        )

        return session

    def add_message(
        self,
        session_id: str,
        *,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """Append a message and publish ``message_appended``."""

        ctx = self._agent_app.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")

        core, base_config, session = ctx

        normalized_role = role if role in {"system", "user", "assistant", "tool"} else "user"

        new_session = core.add_message(session, normalized_role, content, metadata)
        self._agent_app.save_session(new_session)

        last_message = new_session.messages[-1] if new_session.messages else None

        self._events.publish(
            {
                "type": "message_appended",
                "session_id": new_session.session_id,
                "role": normalized_role,
                "content": content,
                "metadata": metadata or {},
                "message": last_message.to_dict() if last_message is not None else None,
                "session": new_session.to_dict(),
            }
        )

        return new_session

    def send_request(
        self,
        session_id: str,
        *,
        overrides: Optional[Dict[str, Any]] = None,
        stream: bool = True,
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
        """Run AgentApplication.send_request and publish all events."""

        if overrides is not None and not isinstance(overrides, dict):
            raise ValueError("config_overrides must be a mapping if provided")

        ctx = self._agent_app.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")

        core, base_config, session = ctx

        final_session_dict: Optional[Dict[str, Any]] = session.to_dict()
        final_messages: List[Dict[str, Any]] = []
        request_id: Optional[str] = None

        for ev in self._agent_app.send_request(core, session, base_config, overrides, stream=stream):
            stored = self._events.publish(ev)

            if stored.get("type") == "final":
                final_session_dict = stored.get("session") or final_session_dict
                final_messages = list(stored.get("messages") or [])
                request_id = stored.get("request_id")
            elif "session" in stored and isinstance(stored.get("session"), dict):
                final_session_dict = stored["session"]

        if final_session_dict is not None:
            try:
                final_session = Session.from_dict(final_session_dict)
                self._agent_app.save_session(final_session)
            except Exception:  # pragma: no cover - defensive
                pass

        return final_session_dict, final_messages, request_id

    def list_events(
        self,
        *,
        since_id: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        return self._events.list(
            since_id=since_id,
            request_id=request_id,
            session_id=session_id,
            limit=limit,
        )

    def get_config_errors(self) -> List[Dict[str, Any]]:
        return self._agent_app.get_config_errors()


# ---------------------------------------------------------------------------
# FastAPI wiring
# ---------------------------------------------------------------------------


app = FastAPI(title="Agent Terminal App - Echo provider (AgentApplication)")

_server_app = ServerApplication(config_path=_DEFAULT_CONFIG_PATH, session_root=_DEFAULT_SESSION_ROOT)


def get_server_app() -> ServerApplication:
    return _server_app


@app.post("/sessions")
def create_session(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data = payload or {}
    agent_id = data.get("agent_id") or "default"
    system_message = data.get("system_message")

    app_instance = get_server_app()

    try:
        session = app_instance.create_session(agent_id=agent_id, system_message=system_message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"session": session.to_dict(), "errors": app_instance.get_config_errors()}


@app.post("/sessions/{session_id}/messages")
def add_message(session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    role = payload.get("role")
    content = payload.get("content")
    metadata = payload.get("metadata")

    if not isinstance(role, str) or not isinstance(content, str):
        raise HTTPException(status_code=400, detail="role and content must be strings")

    app_instance = get_server_app()

    try:
        new_session = app_instance.add_message(session_id, role=role, content=content, metadata=metadata)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"session": new_session.to_dict()}


@app.post("/sessions/{session_id}/send")
def send_request(session_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data = payload or {}
    overrides = data.get("config_overrides") or {}

    app_instance = get_server_app()

    try:
        final_session_dict, final_messages, request_id = app_instance.send_request(
            session_id, overrides=overrides, stream=True
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "session": final_session_dict,
        "messages": final_messages,
        "request_id": request_id,
    }


@app.get("/events")
def list_events(
    since_id: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    app_instance = get_server_app()
    events = app_instance.list_events(
        since_id=since_id,
        request_id=request_id,
        session_id=session_id,
        limit=limit,
    )
    return {"events": events}


# ---------------------------------------------------------------------------
# Helper for running under uvicorn or from the CLI
# ---------------------------------------------------------------------------


def run_api(
    host: str = "127.0.0.1",
    port: int = 8000,
    app_instance: Optional[ServerApplication] = None,
) -> None:  # pragma: no cover
    """Run the FastAPI app with uvicorn on the given host/port."""

    try:
        import uvicorn  # type: ignore[import-not-found]
    except Exception:  # pragma: no cover - optional dependency
        import sys as _sys

        print(
            "Uvicorn is not installed. Run with: "
            "`pip install uvicorn[standard]` and then "
            "`uvicorn agent_terminal_app.server:app`.",
            file=_sys.stderr,
        )
        return

    global _server_app
    if app_instance is not None:
        _server_app = app_instance

    uvicorn.run("agent_terminal_app.server:app", host=host, port=port, reload=False)
