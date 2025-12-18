from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import json

try:  # Optional convenience in local usage
    from dotenv import load_dotenv  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional dependency
    load_dotenv = None  # type: ignore[assignment]

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
    """Build a process-wide AgentApplication with default config.

    Construction is intentionally lazy so that applications (including the
    terminal CLI entrypoint) can configure logging before any AgentCore
    instances are created. This avoids get_logger() being called during
    import, which would lock in logging configuration before CLI flags like
    ``--log-level`` are processed.
    """

    cfg = _DEFAULT_CONFIG_PATH
    root = _DEFAULT_SESSION_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return AgentApplication(str(cfg), str(root))


_agent_app: Optional[AgentApplication] = None


def get_agent_app() -> AgentApplication:
    """Return the process-wide AgentApplication instance.

    FastAPI uses this via dependency injection; tests can call the
    route functions directly and pass a custom ``AgentApplication``
    instance for isolation.
    """

    global _agent_app

    if _agent_app is None:
        _agent_app = _build_default_agent_app()

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


def _get_session_root(app_instance: AgentApplication) -> Path:
    """Best-effort access to the filesystem session root for an application.

    AgentApplication currently uses :class:`FilesystemSessionStore` internally,
    but does not expose the root directory publicly. For the server's
    purposes, it is sufficient to read the private ``_root_dir`` attribute
    when present.
    """

    store = getattr(app_instance, "_session_store", None)
    root = getattr(store, "_root_dir", None)
    if not isinstance(root, Path):  # pragma: no cover - defensive guard
        raise HTTPException(status_code=500, detail="Session store does not expose a filesystem root")
    return root


def _normalize_slice_bounds(
    message_count: int,
    start: Optional[int],
    end: Optional[int],
) -> Tuple[int, int]:
    """Return concrete ``(start_idx, end_idx)`` for slice-like bounds.

    Semantics mirror :meth:`TerminalApplication._normalize_slice_bounds`:
    - ``start`` and ``end`` follow Python slice rules, including support
      for ``None`` and negative indices.
    - Indices are clamped to ``[0, message_count]``.
    - ``ValueError`` is raised when the range selects no messages.
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

        core, base_config, session = ctx

        normalized_role = role if role in {"system", "user", "assistant", "tool"} else "user"

        new_session = core.add_message(session, normalized_role, content, metadata, base_config)
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
            etype = ev.get("type")

            # Internal checkpoint events carry the live Session object so the
            # server can persist progress incrementally. They are not
            # published to the shared event store or serialized in responses.
            if etype == "session_checkpoint":
                session_obj = ev.get("session")
                if isinstance(session_obj, Session):
                    try:
                        app_instance.save_session(session_obj)
                    except Exception:  # pragma: no cover - defensive
                        pass
                    try:
                        final_session_dict = session_obj.to_dict()
                    except Exception:  # pragma: no cover - defensive
                        pass
                continue

            stored = store.publish(ev)

            if stored.get("type") == "final":
                final_messages = list(stored.get("messages") or [])
                request_id = stored.get("request_id")
            elif "session" in stored and isinstance(stored.get("session"), dict):
                # Backwards compatibility for older event shapes that include
                # a serialized session payload.
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


@app.get("/sessions")
def list_sessions(
    limit: Optional[int] = None,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """List stored sessions with basic metadata.

    Response shape mirrors :meth:`TerminalApplication.list_sessions_metadata`:
    each entry contains ``session_id``, ``modified`` (float timestamp),
    and ``preview`` (first user message snippet).
    """

    root = _get_session_root(app_instance)

    try:
        exists = root.exists()
    except Exception:  # pragma: no cover - defensive
        exists = False

    if not exists:
        return {"sessions": []}

    items: List[Dict[str, Any]] = []
    for path in root.glob("*.json"):
        try:
            stat = path.stat()
        except OSError:  # pragma: no cover - defensive
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
        except Exception:  # pragma: no cover - defensive
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

    return {"sessions": items}


@app.get("/sessions/{session_id}/messages")
def list_session_messages(
    session_id: str,
    start: Optional[int] = None,
    end: Optional[int] = None,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """List messages for a session with optional slice-style bounds."""

    try:
        ctx = app_instance.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")

        _core, _base_config, session = ctx
        message_count = len(session.messages)

        if message_count == 0:
            return {"messages": []}

        try:
            start_idx, end_idx = _normalize_slice_bounds(message_count, start, end)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        results: List[Dict[str, Any]] = []
        for idx in range(start_idx, end_idx):
            msg = session.messages[idx]
            results.append({"index": idx, "message": msg.to_dict()})

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"messages": results}


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


@app.post("/requests/{request_id}/cancel")
def cancel_request(
    request_id: str,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Request cooperative cancellation for an in-flight request.

    This is a thin wrapper around :meth:`AgentApplication.cancel_request`.
    """

    try:
        app_instance.cancel_request(request_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"request_id": request_id, "status": "cancelled"}


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
