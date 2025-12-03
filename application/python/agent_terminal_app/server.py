from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

try:  # Optional convenience in local usage
    from dotenv import load_dotenv  # type: ignore[import-not-found]

    load_dotenv()
except Exception:  # pragma: no cover - optional dependency
    pass

from fastapi import FastAPI, HTTPException  # type: ignore[reportMissingImports]

from agent_core import Session

from .app_core import get_shared_agent_app, get_shared_event_store, init_shared_app


# ---------------------------------------------------------------------------
# FastAPI wiring around the shared AgentApplication / EventStore
# ---------------------------------------------------------------------------


app = FastAPI(title="Agent Terminal App - Echo provider (AgentApplication)")


def _create_session_impl(agent_id: str, system_message: Optional[str]) -> Session:
    """Create a session via AgentApplication and publish an event."""

    agent_app = get_shared_agent_app()
    events = get_shared_event_store()

    core, base_config, session = agent_app.create_session(agent_id)

    if isinstance(system_message, str) and system_message:
        session = core.add_message(session, "system", system_message)
        agent_app.save_session(session)

    events.publish(
        {
            "type": "session_created",
            "session_id": session.session_id,
            "agent_id": agent_id,
            "session": session.to_dict(),
        }
    )

    return session


def _add_message_impl(
    session_id: str,
    *,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Session:
    """Append a message via AgentApplication and publish an event."""

    agent_app = get_shared_agent_app()
    events = get_shared_event_store()

    ctx = agent_app.load_session(session_id)
    if ctx is None:
        raise KeyError(f"Session {session_id!r} not found")

    core, base_config, session = ctx

    normalized_role = role if role in {"system", "user", "assistant", "tool"} else "user"

    new_session = core.add_message(session, normalized_role, content, metadata)
    agent_app.save_session(new_session)

    last_message = new_session.messages[-1] if new_session.messages else None

    events.publish(
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


def _send_request_impl(
    session_id: str,
    overrides: Optional[Dict[str, Any]] = None,
    *,
    stream: bool = True,
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
    """Run AgentApplication.send_request and publish all events."""

    agent_app = get_shared_agent_app()
    events = get_shared_event_store()

    if overrides is not None and not isinstance(overrides, dict):
        raise ValueError("config_overrides must be an object")

    ctx = agent_app.load_session(session_id)
    if ctx is None:
        raise KeyError(f"Session {session_id!r} not found")

    core, base_config, session = ctx

    final_session_dict: Optional[Dict[str, Any]] = session.to_dict()
    final_messages: List[Dict[str, Any]] = []
    request_id: Optional[str] = None

    for ev in agent_app.send_request(core, session, base_config, overrides, stream=stream):
        stored = events.publish(ev)

        if stored.get("type") == "final":
            final_session_dict = stored.get("session") or final_session_dict
            final_messages = list(stored.get("messages") or [])
            request_id = stored.get("request_id")
        elif "session" in stored and isinstance(stored.get("session"), dict):
            final_session_dict = stored["session"]

    if final_session_dict is not None:
        try:
            final_session = Session.from_dict(final_session_dict)
            agent_app.save_session(final_session)
        except Exception:  # pragma: no cover - defensive
            pass

    return final_session_dict, final_messages, request_id


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
        session = _create_session_impl(agent_id=agent_id, system_message=system_message)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    agent_app = get_shared_agent_app()
    return {"session": session.to_dict(), "errors": agent_app.get_config_errors()}


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
        new_session = _add_message_impl(session_id, role=role, content=content, metadata=metadata)
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

    try:
        final_session_dict, final_messages, request_id = _send_request_impl(
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
    """List events from the shared in-memory event store."""

    events_store = get_shared_event_store()

    events = events_store.list(
        since_id=since_id,
        request_id=request_id,
        session_id=session_id,
        limit=limit,
    )
    return {"events": events}


# ---------------------------------------------------------------------------
# Helper for running under uvicorn or from the CLI
# ---------------------------------------------------------------------------


def run_api(host: str = "127.0.0.1", port: int = 8000) -> None:  # pragma: no cover
    """Run the FastAPI app with uvicorn on the given host/port."""

    try:
        import uvicorn  # type: ignore[reportMissingImports]
    except Exception:  # pragma: no cover - optional dependency
        import sys as _sys

        print(
            "Uvicorn is not installed. Run with: "
            "`pip install uvicorn[standard]` and then "
            "`uvicorn agent_terminal_app.server:app`.",
            file=_sys.stderr,
        )
        return

    # Ensure the shared application is initialised before starting the server.
    init_shared_app()

    uvicorn.run("agent_terminal_app.server:app", host=host, port=port, reload=False)
