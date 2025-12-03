from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:  # Optional convenience in local usage
    from dotenv import load_dotenv  # type: ignore[import-not-found]

    load_dotenv()
except Exception:  # pragma: no cover - optional dependency
    pass

from fastapi import Depends, FastAPI, HTTPException  # type: ignore[reportMissingImports]

from agent_app.application_future import AgentApplication
from agent_core import Session


_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config_openrouter_app_layer.json"
_DEFAULT_SESSION_ROOT = Path(__file__).resolve().parent / "sessions"


# ---------------------------------------------------------------------------
# FastAPI application and dependency wiring
# ---------------------------------------------------------------------------


app = FastAPI(title="Agent Terminal App - Echo provider (AgentApplication)")


def _build_default_agent_app() -> AgentApplication:
    cfg = _DEFAULT_CONFIG_PATH
    root = _DEFAULT_SESSION_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return AgentApplication(str(cfg), str(root))


_agent_app: AgentApplication = _build_default_agent_app()


def get_agent_app() -> AgentApplication:
    """Return the process-wide AgentApplication instance.

    FastAPI uses this via dependency injection; tests can call the
    route functions directly and pass a custom ``AgentApplication``
    instance for isolation.
    """

    return _agent_app


# ---------------------------------------------------------------------------
# Route handlers (single implementation per operation)
# ---------------------------------------------------------------------------


@app.post("/sessions")
def create_session(
    payload: Optional[Dict[str, Any]] = None,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Create a session and publish a ``session_created`` event.

    The same function serves as both the FastAPI route handler and the
    core implementation: when called directly in tests, a custom
    ``AgentApplication`` can be injected via ``app_instance``.
    """

    data = payload or {}
    agent_id = data.get("agent_id") or "default"
    system_message = data.get("system_message")

    try:
        core, _base_config, session = app_instance.create_session(agent_id)

        if isinstance(system_message, str) and system_message:
            session = core.add_message(session, "system", system_message)
            app_instance.save_session(session)

        store = app_instance.get_event_store()
        store.publish(
            {
                "type": "session_created",
                "session_id": session.session_id,
                "agent_id": agent_id,
                "session": session.to_dict(),
            }
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"session": session.to_dict(), "errors": app_instance.get_config_errors()}


@app.post("/sessions/{session_id}/messages")
def add_message(
    session_id: str,
    payload: Dict[str, Any],
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Append a message and publish a ``message_appended`` event."""

    role = payload.get("role")
    content = payload.get("content")
    metadata = payload.get("metadata")

    if not isinstance(role, str) or not isinstance(content, str):
        raise HTTPException(status_code=400, detail="role and content must be strings")

    try:
        ctx = app_instance.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")

        core, _base_config, session = ctx

        normalized_role = role if role in {"system", "user", "assistant", "tool"} else "user"

        new_session = core.add_message(session, normalized_role, content, metadata)
        app_instance.save_session(new_session)

        last_message = new_session.messages[-1] if new_session.messages else None

        store = app_instance.get_event_store()
        store.publish(
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

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"session": new_session.to_dict()}


@app.post("/sessions/{session_id}/send")
def send_request(
    session_id: str,
    payload: Optional[Dict[str, Any]] = None,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Run ``AgentApplication.send_request`` and publish all events."""

    data = payload or {}
    overrides = data.get("config_overrides") or {}

    if overrides is not None and not isinstance(overrides, dict):
        raise HTTPException(status_code=400, detail="config_overrides must be a mapping if provided")

    try:
        ctx = app_instance.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")

        core, base_config, session = ctx

        final_session_dict: Optional[Dict[str, Any]] = session.to_dict()
        final_messages: List[Dict[str, Any]] = []
        request_id: Optional[str] = None

        store = app_instance.get_event_store()

        for ev in app_instance.send_request(core, session, base_config, overrides, stream=True):
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
                app_instance.save_session(final_session)
            except Exception:  # pragma: no cover - defensive
                pass

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
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """List events from the application's event store."""

    store = app_instance.get_event_store()
    events = store.list(
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
    app_instance: Optional[AgentApplication] = None,
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

    global _agent_app
    if app_instance is not None:
        _agent_app = app_instance

    uvicorn.run("agent_terminal_app.server:app", host=host, port=port, reload=False)
