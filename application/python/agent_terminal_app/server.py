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


# ---------------------------------------------------------------------------
# Application wiring: AgentApplication, config, sessions, and events
# ---------------------------------------------------------------------------

_BASE_DIR = Path(__file__).resolve().parent
_DEFAULT_CONFIG_PATH = _BASE_DIR / "config_echo_app.json"
_DEFAULT_SESSION_ROOT = _BASE_DIR / "sessions"

_app: Optional[AgentApplication] = None
_event_store: Optional[InMemoryEventStore] = None

app = FastAPI(title="Agent Terminal App - Echo provider (AgentApplication)")


def configure_application(
    config_path: Optional[str | Path] = None,
    session_root: Optional[str | Path] = None,
    *,
    reset: bool = False,
) -> None:
    """Initialise or reconfigure the application-layer instance.

    - ``config_path``: optional path to a JSON config file. Defaults to
      the package's ``config_echo_app.json``.
    - ``session_root``: optional directory for filesystem-backed
      sessions. Defaults to ``agent_terminal_app/sessions``.
    - ``reset``: when ``True``, forces reinitialisation even if an
      instance already exists. This is primarily intended for tests.
    """

    global _app, _event_store

    if _app is not None and _event_store is not None and not reset:
        return

    cfg_path = Path(config_path) if config_path is not None else _DEFAULT_CONFIG_PATH
    root = Path(session_root) if session_root is not None else _DEFAULT_SESSION_ROOT
    root.mkdir(parents=True, exist_ok=True)

    _app = AgentApplication(str(cfg_path), str(root))
    _event_store = InMemoryEventStore()


def _require_app() -> Tuple[AgentApplication, InMemoryEventStore]:
    """Return the configured application and event store.

    If the application has not yet been configured, it is initialised
    with default paths. This keeps runtime usage simple while allowing
    tests to reconfigure paths explicitly via :func:`configure_application`.
    """

    if _app is None or _event_store is None:
        configure_application()

    assert _app is not None
    assert _event_store is not None
    return _app, _event_store


# ---------------------------------------------------------------------------
# Internal helpers shared by HTTP routes and terminal client
# ---------------------------------------------------------------------------


def get_event_store() -> InMemoryEventStore:
    """Return the in-memory event store instance.

    This is shared between the FastAPI routes and the in-process
    terminal client so that all frontends can observe the same stream
    of request events.
    """

    _application, event_store = _require_app()
    return event_store


def create_session_core(agent_id: str = "default", system_message: Optional[str] = None) -> Session:
    """Create and persist a new session for the given agent.

    A ``Session`` instance is returned. A corresponding
    ``session_created`` event is published to the shared event store.
    """

    application, event_store = _require_app()

    core, base_config, session = application.create_session(agent_id)

    if isinstance(system_message, str) and system_message:
        session = core.add_message(session, "system", system_message)
        application.save_session(session)

    event_store.publish(
        {
            "type": "session_created",
            "session_id": session.session_id,
            "agent_id": agent_id,
            "session": session.to_dict(),
        }
    )

    return session


def append_message_core(
    session_id: str,
    *,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Session:
    """Append a message to an existing session and publish an event.

    A new immutable ``Session`` instance is returned. A
    ``message_appended`` event is published to the shared event store.
    """

    application, event_store = _require_app()

    ctx = application.load_session(session_id)
    if ctx is None:
        raise KeyError(f"Session {session_id!r} not found")

    core, base_config, session = ctx

    normalized_role = role if role in {"system", "user", "assistant", "tool"} else "user"

    new_session = core.add_message(session, normalized_role, content, metadata)
    application.save_session(new_session)

    last_message = new_session.messages[-1] if new_session.messages else None

    event_store.publish(
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


def _run_request_events(
    core: Any,
    base_config: Dict[str, Any],
    session: Session,
    overrides: Optional[Dict[str, Any]] = None,
    *,
    stream: bool,
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
    """Run ``AgentApplication.send_request`` and publish all events.

    Returns ``(final_session_dict, final_messages, request_id)`` where
    ``final_session_dict`` is the latest session snapshot seen in the
    event stream. The caller is responsible for converting this back to
    a :class:`Session` if desired.
    """

    application, event_store = _require_app()

    final_session_dict: Optional[Dict[str, Any]] = session.to_dict()
    final_messages: List[Dict[str, Any]] = []
    request_id: Optional[str] = None

    for ev in application.send_request(core, session, base_config, overrides, stream=stream):
        stored = event_store.publish(ev)

        if stored.get("type") == "final":
            final_session_dict = stored.get("session") or final_session_dict
            final_messages = list(stored.get("messages") or [])
            request_id = stored.get("request_id")
        elif "session" in stored and isinstance(stored.get("session"), dict):
            # Track the latest session snapshot even if no final event
            final_session_dict = stored["session"]

    if final_session_dict is not None:
        try:
            final_session = Session.from_dict(final_session_dict)
            application.save_session(final_session)
        except Exception:  # pragma: no cover - defensive
            pass

    return final_session_dict, final_messages, request_id


def run_request_for_session(
    session_id: str,
    overrides: Optional[Dict[str, Any]] = None,
    *,
    stream: bool = True,
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
    """High-level helper to run a request for a stored session.

    This is used by both the HTTP ``/sessions/{session_id}/send`` route
    and the terminal client. All events are published to the shared
    event store so that other frontends can observe streaming progress
    while the request is in flight.
    """

    application, event_store = _require_app()

    ctx = application.load_session(session_id)
    if ctx is None:
        raise KeyError(f"Session {session_id!r} not found")

    core, base_config, session = ctx

    if overrides is not None and not isinstance(overrides, dict):
        raise ValueError("config_overrides must be a mapping if provided")

    return _run_request_events(core, base_config, session, overrides, stream=stream)


# ---------------------------------------------------------------------------
# HTTP routes
# ---------------------------------------------------------------------------


@app.post("/sessions")
def create_session(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a new session for the default agent.

    Request JSON body (all fields optional)::

        {"agent_id": "default", "system_message": "..."}

    Response JSON::

        {"session": Session-as-dict, "errors": list[dict]}
    """

    data = payload or {}
    agent_id = data.get("agent_id") or "default"
    system_message = data.get("system_message")

    try:
        session = create_session_core(agent_id=agent_id, system_message=system_message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Access the application instance only for config errors; do not
    # trigger a reconfiguration.
    application, _ = _require_app()

    return {"session": session.to_dict(), "errors": application.get_config_errors()}


@app.post("/sessions/{session_id}/messages")
def add_message(session_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Append a message to an existing session.

    Request JSON body::

        {"role": "user", "content": "...", "metadata"?: {...}}

    Response JSON::

        {"session": Session-as-dict}
    """

    role = payload.get("role")
    content = payload.get("content")
    metadata = payload.get("metadata")

    if not isinstance(role, str) or not isinstance(content, str):
        raise HTTPException(status_code=400, detail="role and content must be strings")

    try:
        new_session = append_message_core(session_id, role=role, content=content, metadata=metadata)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"session": new_session.to_dict()}


@app.post("/sessions/{session_id}/send")
def send_request(session_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run the model for the current session and return the reply.

    Request JSON body (all fields optional)::

        {"config_overrides": {...}}

    Response JSON::

        {
            "session": Session-as-dict | null,
            "messages": [assistant messages for the final loop],
            "request_id": str | null,
        }
    """

    data = payload or {}
    overrides = data.get("config_overrides") or {}

    if overrides is not None and not isinstance(overrides, dict):
        raise HTTPException(status_code=400, detail="config_overrides must be an object")

    try:
        final_session_dict, final_messages, request_id = run_request_for_session(
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
    """List events from the shared in-memory event store.

    This is a simple polling API intended for experimentation. Callers
    can pass ``since_id`` to retrieve only events published after a
    given event identifier.
    """

    _application, event_store = _require_app()

    events = event_store.list(
        since_id=since_id,
        request_id=request_id,
        session_id=session_id,
        limit=limit,
    )
    return {"events": events}


# ---------------------------------------------------------------------------
# Helpers for running under uvicorn or tests
# ---------------------------------------------------------------------------


def run_api(host: str = "127.0.0.1", port: int = 8000) -> None:  # pragma: no cover
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

    # Ensure the application is initialised before starting the server.
    configure_application()

    uvicorn.run("agent_terminal_app.server:app", host=host, port=port, reload=False)
