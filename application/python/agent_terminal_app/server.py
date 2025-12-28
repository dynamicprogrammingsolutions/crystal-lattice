from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import asyncio
import json
import logging
import os
import threading
import uuid
from datetime import datetime

try:  # Optional convenience in local usage
    from dotenv import load_dotenv  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional dependency
    load_dotenv = None  # type: ignore[assignment]

from fastapi import Depends, FastAPI, HTTPException  # type: ignore[reportMissingImports]

from agent_app.application_future import AgentApplication
from agent_app.config import resolve_request_config
from agent_core import Session
from agent_terminal_app import bonjour as bonjour_mod
from agent_terminal_app import bridge_client as bridge_mod


_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config_openrouter_app_layer.json"
_DEFAULT_SESSION_ROOT = Path(__file__).resolve().parent / "sessions"


# ---------------------------------------------------------------------------
# FastAPI application and dependency wiring
# ---------------------------------------------------------------------------


app = FastAPI(title="Agent Terminal App - Echo provider (AgentApplication)")


# ---------------------------------------------------------------------------
# Optional integrations: Bonjour/mDNS and bridge client
# ---------------------------------------------------------------------------


_bonjour_handle: Optional[bonjour_mod.BonjourServiceHandle] = None
_bridge_client: Optional[bridge_mod.BridgeClient] = None
_bridge_task: Optional[asyncio.Task[None]] = None

_log = logging.getLogger(__name__)


@app.on_event("startup")
async def _on_startup() -> None:
    """FastAPI startup hook.

    * Optionally advertise the HTTP API via Bonjour/mDNS when the
      ``ENABLE_BONJOUR`` environment variable is set.
    * Optionally start the bridge client when ``BRIDGE_URL`` is set.
    """

    global _bonjour_handle, _bridge_client, _bridge_task

    # Bonjour advertising -------------------------------------------------
    if os.getenv("ENABLE_BONJOUR"):
        # The advertised port can be configured explicitly via
        # ``BONJOUR_PORT``. When not set, fall back to ``SERVER_PORT`` or
        # the common FastAPI default of 8000.
        port_str = os.getenv("BONJOUR_PORT") or os.getenv("SERVER_PORT") or "8000"
        try:
            port = int(port_str)
        except ValueError:  # pragma: no cover - defensive
            port = 8000

        service_name = os.getenv("BONJOUR_SERVICE_NAME") or "Agent Terminal App"
        _log.info(
            "[bonjour] starting registration: service=%r port=%d", service_name, port
        )
        # ``zeroconf`` uses its own asyncio machinery under the hood and
        # calling it directly from within FastAPI's event loop can lead to
        # deadlocks (manifesting as ``EventLoopBlocked``). Run the blocking
        # registration in a separate thread instead.
        _bonjour_handle = await asyncio.to_thread(
            bonjour_mod.start_bonjour, service_name, port
        )

        if _bonjour_handle is not None:
            _log.info(
                "[bonjour] registration finished: service=%r port=%d", service_name, port
            )
        else:
            _log.warning(
                "[bonjour] registration failed; see earlier logs for details "
                "(service=%r port=%d)",
                service_name,
                port,
            )

    # Bridge client -------------------------------------------------------
    client = bridge_mod.create_bridge_client_from_env()
    if client is not None:
        _bridge_client = client
        # Run the bridge client in the background for the lifetime of the
        # FastAPI application.
        _bridge_task = asyncio.create_task(client.run())


@app.on_event("shutdown")
async def _on_shutdown() -> None:
    """FastAPI shutdown hook for cleaning up integrations."""

    global _bonjour_handle, _bridge_client, _bridge_task

    # Stop bridge client first so that any in-flight requests are
    # cancelled before the HTTP server itself is torn down.
    if _bridge_client is not None:
        try:
            await _bridge_client.stop()
        except Exception:  # pragma: no cover - defensive
            pass

    if _bridge_task is not None:
        try:
            await _bridge_task
        except Exception:  # pragma: no cover - defensive
            pass

    _bridge_client = None
    _bridge_task = None

    # Tear down Bonjour advertisement last.
    if _bonjour_handle is not None:
        _log.info("[bonjour] stopping registration")
        # See comment in ``_on_startup``: perform zeroconf operations in a
        # worker thread to avoid blocking the main event loop.
        await asyncio.to_thread(bonjour_mod.stop_bonjour, _bonjour_handle)
        _bonjour_handle = None
        _log.info("[bonjour] registration stopped")


# ---------------------------------------------------------------------------
# Simple in-memory data store for Bonjour-style example endpoints
# ---------------------------------------------------------------------------


class DataStore:
    """Thread-safe in-memory key/value store used by /api/* endpoints.

    The semantics mirror the ``DataStore`` used by the standalone Bonjour
    example server: a mutable mapping initialised with a ``message`` and
    ``count`` field that can be read in full and updated via ``update``.
    """

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None) -> None:
        self._data: Dict[str, Any] = dict(initial_data or {"message": "Initial data", "count": 0})
        self._lock = threading.Lock()

    def get(self) -> Dict[str, Any]:
        """Return a shallow copy of the current data mapping."""

        with self._lock:
            return dict(self._data)

    def update(self, new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge ``new_data`` into the store and return the updated mapping."""

        if not isinstance(new_data, dict):  # Defensive guard; FastAPI normally enforces this
            raise ValueError("new_data must be a mapping")

        with self._lock:
            self._data.update(new_data)
            return dict(self._data)


_bonjour_data_store = DataStore()


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
# Bonjour-style example HTTP endpoints
# ---------------------------------------------------------------------------


@app.get("/api/data")
def get_api_data() -> Dict[str, Any]:
    """Return the current contents of the in-memory ``DataStore``.

    Shape matches the standalone Bonjour example server:

    .. code-block:: json

        {
          "success": true,
          "data": { ... },
          "timestamp": "2025-01-01T00:00:00Z"
        }
    """

    return {
        "success": True,
        "data": _bonjour_data_store.get(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.put("/api/data")
def put_api_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Merge the given JSON body into the ``DataStore`` and return it.

    The behaviour mirrors the Bonjour example server's ``PUT /api/data``
    handler: the body is treated as a partial update and the response
    includes the full updated mapping under ``updated``.
    """

    try:
        updated = _bonjour_data_store.update(payload or {})
    except ValueError as exc:  # pragma: no cover - defensive; FastAPI validates payload
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"success": True, "updated": updated}


@app.get("/api/hello")
def get_api_hello() -> Dict[str, Any]:
    """Return a static greeting payload matching the Bonjour example."""

    return {
        "message": "Hello from Bonjour Server!",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "method": "GET",
    }


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
        with app_instance.acquire_session_lock(session.session_id):
            if isinstance(system_message, str) and system_message:
                session = core.add_message(session, "system", system_message)
                app_instance.save_session(session)

            stored = app_instance.publish_event(
                {
                    "type": "session_created",
                    "session_id": session.session_id,
                    "agent_id": agent_id,
                    "session": session.to_dict(),
                },
            )

            try:
                app_instance.record_checkpoint(session.session_id, stored.get("request_id"))
            except Exception:  # pragma: no cover - defensive
                _log.exception(
                    "failed to publish checkpoint event after session create for %r",
                    session.session_id,
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


def _normalize_index(raw_index: int, message_count: int) -> int:
    """Normalize a Python-style index for a sequence of ``message_count``.

    Semantics mirror :meth:`TerminalApplication._normalize_index`:

    * Negative indices are translated relative to the end.
    * ``IndexError`` is raised when the resulting index is out of bounds.
    """

    target_index = raw_index
    if target_index < 0:
        target_index = message_count + target_index
    if target_index < 0 or target_index >= message_count:
        raise IndexError("message index out of range")
    return target_index


def _run_send_request_background(
    app_instance: AgentApplication,
    session_id: str,
    overrides: Dict[str, Any],
) -> None:
    """Run ``AgentApplication.send_request`` and publish all events.

    This helper mirrors the previous behaviour of :func:`send_request`
    but is designed to run in a background thread so that the HTTP
    route can return immediately.
    """

    try:
        ctx = app_instance.load_session(session_id)
        if ctx is None:
            _log.warning("send_request background worker: session %r not found", session_id)
            return

        core, base_config, session = ctx

        final_session_dict: Optional[Dict[str, Any]] = session.to_dict()
        final_messages: List[Dict[str, Any]] = []
        request_id: Optional[str] = None

        for ev in app_instance.send_request(core, session, base_config, overrides, stream=True):
            etype = ev.get("type")

            # Internal checkpoint events carry the live Session object so the
            # server can persist progress incrementally. They are not
            # published to the shared event store or serialized in responses.
            if etype == "session_checkpoint":
                session_obj = ev.get("session")
                if isinstance(session_obj, Session):
                    with app_instance.acquire_session_lock(session_obj.session_id):
                        try:
                            app_instance.save_session(session_obj)
                        except Exception:  # pragma: no cover - defensive
                            _log.exception(
                                "failed to save session checkpoint for %r", session_id
                            )
                        try:
                            final_session_dict = session_obj.to_dict()
                        except Exception:  # pragma: no cover - defensive
                            _log.exception(
                                "failed to serialize session checkpoint for %r", session_id
                            )
                        try:
                            app_instance.record_checkpoint(
                                session_obj.session_id, ev.get("request_id")
                            )
                        except Exception:  # pragma: no cover - defensive
                            _log.exception(
                                "failed to publish checkpoint event for %r", session_id
                            )
                continue

            stored = app_instance.publish_event(ev)

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
                _log.exception("failed to persist final session for %r", session_id)

        # ``final_messages`` and ``request_id`` are intentionally unused
        # here; callers are expected to observe results via the event
        # store and session history.

    except Exception:  # pragma: no cover - defensive
        _log.exception(
            "unexpected error in send_request background worker for session %r",
            session_id,
        )


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
        with app_instance.acquire_session_lock(session_id):
            ctx = app_instance.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            core, base_config, session = ctx

            normalized_role = (
                role if role in {"system", "user", "assistant", "tool"} else "user"
            )

            new_session = core.add_message(
                session, normalized_role, content, metadata, base_config
            )
            app_instance.save_session(new_session)

            last_message = new_session.messages[-1] if new_session.messages else None

            stored = app_instance.publish_event(
                {
                    "type": "message_appended",
                    "session_id": new_session.session_id,
                    "role": normalized_role,
                    "content": content,
                    "metadata": metadata or {},
                    "message": last_message.to_dict() if last_message is not None else None,
                    "session": new_session.to_dict(),
                },
            )

            try:
                app_instance.record_checkpoint(new_session.session_id, stored.get("request_id"))
            except Exception:  # pragma: no cover - defensive
                _log.exception(
                    "failed to publish checkpoint event after message append for %r",
                    session_id,
                )

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"session": new_session.to_dict()}


@app.patch("/sessions/{session_id}/messages/{index}")
def update_message(
    session_id: str,
    index: int,
    payload: Dict[str, Any],
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Modify the content of a single message at ``index``.

    This mirrors :meth:`TerminalApplication.modify_message` using
    Python-style indices (0-based, negatives allowed).
    """

    content = payload.get("content")
    if not isinstance(content, str):
        raise HTTPException(status_code=400, detail="content must be a string")

    try:
        with app_instance.acquire_session_lock(session_id):
            ctx = app_instance.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            core, base_config, session = ctx

            message_count = len(session.messages)
            if message_count == 0:
                raise HTTPException(status_code=400, detail="no messages to modify")

            try:
                target_index = _normalize_index(index, message_count)
            except IndexError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            overrides_val = metadata.get("overrides")
            overrides: Dict[str, Any] = (
                overrides_val if isinstance(overrides_val, dict) else {}
            )
            config = resolve_request_config(base_config, overrides)

            new_session = core.modify_message(session, target_index, content, config)
            app_instance.save_session(new_session)

            stored = app_instance.publish_event(
                {
                    "type": "message_modified",
                    "session_id": new_session.session_id,
                    "index": target_index,
                    "content": content,
                    "session": new_session.to_dict(),
                },
            )

            try:
                app_instance.record_checkpoint(new_session.session_id, stored.get("request_id"))
            except Exception:  # pragma: no cover - defensive
                _log.exception(
                    "failed to publish checkpoint event after message modify for %r",
                    session_id,
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
    """Start ``AgentApplication.send_request`` in the background.

    The HTTP response is an immediate acknowledgement; clients are
    expected to observe progress and results via the event store and
    session history rather than the response body.
    """

    data = payload or {}
    overrides = data.get("config_overrides") or {}

    if overrides is not None and not isinstance(overrides, dict):
        raise HTTPException(
            status_code=400,
            detail="config_overrides must be a mapping if provided",
        )

    try:
        # Validate that the session exists before starting the
        # background worker so that clients receive an immediate 404 for
        # unknown sessions.
        ctx = app_instance.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Start the send_request flow in a background thread so that the
    # HTTP response can return immediately.
    threading.Thread(
        target=_run_send_request_background,
        args=(app_instance, session_id, overrides),
        daemon=True,
    ).start()

    # The response intentionally omits session/messages/request_id; they
    # can be observed via the event store and subsequent session loads.
    return {}


@app.delete("/sessions/{session_id}/messages")
def delete_messages(
    session_id: str,
    payload: Dict[str, Any],
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Delete one or more messages from a session.

    The body supports three shapes:

    * ``{"indices": [int, ...]}`` – delete specific indices.
    * ``{"range": {"start": Optional[int], "end": Optional[int]}}`` –
      delete a Python-style slice.
    * ``{"last": int}`` – delete the last *N* messages.

    Response shape: ``{"session": <Session>, "deleted_indices": [int, ...]}``.
    """

    body = payload or {}
    has_indices = "indices" in body
    has_range = "range" in body
    has_last = "last" in body

    if int(has_indices) + int(has_range) + int(has_last) != 1:
        raise HTTPException(
            status_code=400,
            detail="Exactly one of 'indices', 'range', or 'last' must be provided",
        )

    try:
        with app_instance.acquire_session_lock(session_id):
            ctx = app_instance.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            core, base_config, session = ctx
            message_count = len(session.messages)

            if message_count == 0:
                raise HTTPException(status_code=400, detail="no messages to delete")

            # Determine concrete indices to delete based on the chosen mode.
            delete_indices: List[int]

            if has_indices:
                raw_indices = body.get("indices")
                if not isinstance(raw_indices, list):
                    raise HTTPException(
                        status_code=400, detail="indices must be a list of integers"
                    )
                if not raw_indices:
                    # Nothing to delete; return the current session unchanged.
                    return {"session": session.to_dict(), "deleted_indices": []}

                delete_indices = []
                for raw in raw_indices:
                    if not isinstance(raw, int):
                        raise HTTPException(
                            status_code=400, detail="indices must be integers"
                        )
                    try:
                        idx = _normalize_index(raw, message_count)
                    except IndexError as exc:
                        raise HTTPException(status_code=400, detail=str(exc)) from exc
                    delete_indices.append(idx)

            elif has_range:
                range_spec = body.get("range") or {}
                if not isinstance(range_spec, dict):
                    raise HTTPException(status_code=400, detail="range must be an object")

                start = range_spec.get("start")
                end = range_spec.get("end")
                if start is not None and not isinstance(start, int):
                    raise HTTPException(
                        status_code=400, detail="start must be an integer or null"
                    )
                if end is not None and not isinstance(end, int):
                    raise HTTPException(
                        status_code=400, detail="end must be an integer or null"
                    )

                try:
                    start_idx, end_idx = _normalize_slice_bounds(message_count, start, end)
                except ValueError as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc

                delete_indices = list(range(start_idx, end_idx))

            else:  # has_last
                last = body.get("last")
                if not isinstance(last, int):
                    raise HTTPException(status_code=400, detail="last must be an integer")
                if last <= 0:
                    raise HTTPException(
                        status_code=400, detail="count must be a positive integer"
                    )

                count = min(last, message_count)
                start_idx = message_count - count
                delete_indices = list(range(start_idx, message_count))

            if not delete_indices:
                raise HTTPException(status_code=400, detail="no messages selected for deletion")

            # Perform the deletion via the core, mirroring TerminalApplication.delete_messages.
            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            overrides_val = metadata.get("overrides")
            overrides: Dict[str, Any] = (
                overrides_val if isinstance(overrides_val, dict) else {}
            )
            config = resolve_request_config(base_config, overrides)

            new_session = core.slice_session(session, config, remove_indices=delete_indices)
            app_instance.save_session(new_session)

            concrete_indices = sorted(set(delete_indices))

            stored = app_instance.publish_event(
                {
                    "type": "messages_deleted",
                    "session_id": new_session.session_id,
                    "indices": sorted(delete_indices),
                    "session": new_session.to_dict(),
                },
            )

            try:
                app_instance.record_checkpoint(new_session.session_id, stored.get("request_id"))
            except Exception:  # pragma: no cover - defensive
                _log.exception(
                    "failed to publish checkpoint event after messages delete for %r",
                    session_id,
                )

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"session": new_session.to_dict(), "deleted_indices": concrete_indices}


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


@app.post("/sessions/{session_id}/fork")
def fork_session(
    session_id: str,
    payload: Optional[Dict[str, Any]] = None,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Create a new session by forking history up to ``index``.

    The body accepts ``{"index": int}`` where the index uses
    Python-style semantics (0-based, negatives allowed). When omitted,
    ``index`` defaults to ``-1`` (fork full history).
    """

    data = payload or {}
    raw_index = data.get("index", -1)
    if not isinstance(raw_index, int):
        raise HTTPException(status_code=400, detail="index must be an integer")

    try:
        with app_instance.acquire_session_lock(session_id):
            ctx = app_instance.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            core, base_config, session = ctx

            message_count = len(session.messages)
            if message_count == 0:
                raise HTTPException(status_code=400, detail="no messages to fork")

            try:
                target_index = _normalize_index(raw_index, message_count)
            except IndexError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            overrides_val = metadata.get("overrides")
            overrides: Dict[str, Any] = (
                overrides_val if isinstance(overrides_val, dict) else {}
            )
            config = resolve_request_config(base_config, overrides)

            new_session_id = str(uuid.uuid4())
            new_session = core.fork_session(
                session,
                config,
                upto_index=target_index,
                new_session_id=new_session_id,
            )

            app_instance.save_session(new_session)

            # Publish a lifecycle event so frontends can surface the fork.
            md = (
                new_session.metadata if isinstance(new_session.metadata, dict) else {}
            )
            agent_val = md.get("agent_id")
            agent_id = (
                agent_val if isinstance(agent_val, str) and agent_val else "default"
            )
            stored = app_instance.publish_event(
                {
                    "type": "session_created",
                    "session_id": new_session.session_id,
                    "agent_id": agent_id,
                    "source_session_id": session.session_id,
                    "session": new_session.to_dict(),
                },
            )

            try:
                app_instance.record_checkpoint(new_session.session_id, stored.get("request_id"))
            except Exception:  # pragma: no cover - defensive
                _log.exception(
                    "failed to publish checkpoint event after fork for %r",
                    new_session.session_id,
                )

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"session": new_session.to_dict(), "source_session_id": session.session_id}


@app.get("/sessions/{session_id}/messages")
def list_session_messages(
    session_id: str,
    start: Optional[int] = None,
    end: Optional[int] = None,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """List messages for a session with optional slice-style bounds."""

    try:
        with app_instance.acquire_session_lock(session_id):
            ctx = app_instance.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            _core, _base_config, session = ctx
            message_count = len(session.messages)

            if message_count == 0:
                return {
                    "messages": [],
                    "cursor_event_id": app_instance.get_session_cursor_event_id(
                        session_id
                    ),
                }

            try:
                start_idx, end_idx = _normalize_slice_bounds(message_count, start, end)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

            results: List[Dict[str, Any]] = []
            for idx in range(start_idx, end_idx):
                msg = session.messages[idx]
                results.append({"index": idx, "message": msg.to_dict()})

            cursor_event_id = app_instance.get_session_cursor_event_id(session_id)

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"messages": results, "cursor_event_id": cursor_event_id}


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


@app.get("/agents")
def list_agents(
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return the configured agent identifiers.

    Response shape: ``{"agents": [str, ...]}`` mirroring
    :meth:`TerminalApplication.available_agents`.
    """

    agents = [a for a in app_instance.list_agents() if isinstance(a, str) and a]
    # Deduplicate while preserving order, then sort for stability.
    unique: Dict[str, None] = {}
    for agent in agents:
        if agent not in unique:
            unique[agent] = None
    return {"agents": sorted(unique.keys())}


@app.get("/sessions/{session_id}/agent")
def get_session_agent(
    session_id: str,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return the current agent id for a session."""

    try:
        ctx = app_instance.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")

        _core, _base_config, session = ctx
        metadata = session.metadata or {}
        agent_val = metadata.get("agent_id")
        agent_id = agent_val if isinstance(agent_val, str) and agent_val else "default"

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"agent_id": agent_id}


@app.patch("/sessions/{session_id}/agent")
def update_session_agent(
    session_id: str,
    payload: Dict[str, Any],
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Switch the agent for a given session.

    Behaviour mirrors :meth:`TerminalApplication.switch_agent`:

    * ``agent_id`` must be a non-empty string.
    * The target agent id must exist in the configured agents.
    * The updated session metadata is persisted when the session has
      messages or has previously been saved to disk.
    """

    target_agent_id = payload.get("agent_id")
    if not isinstance(target_agent_id, str) or not target_agent_id:
        raise HTTPException(status_code=400, detail="agent_id must be a non-empty string")

    # Validate the target agent using the same semantics as the terminal app.
    available = [a for a in app_instance.list_agents() if isinstance(a, str) and a]
    if target_agent_id not in available:
        raise HTTPException(status_code=400, detail=f"unknown agent: {target_agent_id!r}")

    try:
        with app_instance.acquire_session_lock(session_id):
            ctx = app_instance.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            _core, _base_config, session = ctx

            core, base_config, new_session = app_instance.update_agent(
                target_agent_id, session
            )

            # Decide whether to persist the updated session:
            # - If the session has messages, always save.
            # - If it is empty but was previously saved, update the file.
            # - If it is empty and has never been saved, keep it in memory.
            root = _get_session_root(app_instance)
            session_path = root / f"{session.session_id}.json"
            is_empty = not session.messages
            is_persisted = session_path.exists()
            should_save = (not is_empty) or is_persisted

            if should_save:
                app_instance.save_session(new_session)
                try:
                    app_instance.record_checkpoint(new_session.session_id, None)
                except Exception:  # pragma: no cover - defensive
                    _log.exception(
                        "failed to publish checkpoint event after agent switch for %r",
                        session_id,
                    )

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"session": new_session.to_dict(), "agent_id": target_agent_id}


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

    # Expose host/port via environment variables so that optional
    # integrations (Bonjour, bridge client) can infer the local HTTP
    # base URL and advertised port when the server is launched via this
    # helper instead of directly through ``uvicorn``.
    os.environ.setdefault("SERVER_HOST", host)
    os.environ.setdefault("SERVER_PORT", str(port))

    uvicorn.run("agent_terminal_app.server:app", host=host, port=port, reload=False)
