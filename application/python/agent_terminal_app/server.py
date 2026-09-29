from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import asyncio
import hashlib
import json
import os
import threading
import logging
import time
import uuid
from datetime import datetime, timezone

from agent_core.utils import get_logger

from fastapi import (  # type: ignore[reportMissingImports]
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request,
    Response,
)
from fastapi.responses import JSONResponse  # type: ignore[reportMissingImports]

from agent_app.application_owner import (
    AgentApplicationOwner,
    ApplicationReloadPendingError,
)
from agent_app.application_future import (
    AgentApplication,
    ReadonlySessionViewError,
    SessionConflictError,
)
from agent_app.config import resolve_request_config
from agent_app.notifications import (
    NotificationOperationSupersededError,
    NotificationRevisionConflictError,
    NotificationTransitionError,
)
from agent_app.request_execution import (
    SessionOperationBusyError,
    SessionRequestCoordinatorClosedError,
    StaleApplicationGenerationError,
)
from agent_app.sessions import FilesystemSnapshotSelectionStore
from agent_core import Message, Session
from agent_terminal_app import bonjour as bonjour_mod
from agent_terminal_app import bridge_client as bridge_mod
from agent_terminal_app.runtime_layout import load_runtime_layout


_DEFAULT_RUNTIME_LAYOUT = load_runtime_layout()
_DEFAULT_CONFIG_PATH = _DEFAULT_RUNTIME_LAYOUT.config_examples / "config_fallback.json"
_DEFAULT_SESSION_ROOT = _DEFAULT_RUNTIME_LAYOUT.user_path("default_sessions_dir")

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# FastAPI application and dependency wiring
# ---------------------------------------------------------------------------


app = FastAPI(title="Agent Terminal App - Echo provider (AgentApplication)")


@app.middleware("http")
async def application_operation_gate(
    request: Request,
    call_next: Any,
) -> Any:
    owner = _application_owner
    if owner is None or request.url.path.startswith("/__test/"):
        return await call_next(request)
    try:
        operation = owner.acquire_operation()
    except ApplicationReloadPendingError as exc:
        return JSONResponse(
            status_code=503,
            content={
                "detail": {
                    "error_type": exc.error_type,
                    "message": str(exc),
                }
            },
        )
    try:
        return await call_next(request)
    finally:
        operation.release()


# ---------------------------------------------------------------------------
# Optional integrations: Bonjour/mDNS and bridge client
# ---------------------------------------------------------------------------


_bonjour_handle: Optional[bonjour_mod.BonjourServiceHandle] = None
_bridge_client: Optional[bridge_mod.BridgeClient] = None
_bridge_task: Optional[asyncio.Task[None]] = None


@dataclass(frozen=True)
class BonjourRuntimeConfig:
    service_name: str
    port: int


@dataclass(frozen=True)
class ServerIntegrationRuntimeConfig:
    bonjour: Optional[BonjourRuntimeConfig] = None
    bridge: Optional[bridge_mod.BridgeConfig] = None


_integration_config_explicit = False
_integration_config: Optional[ServerIntegrationRuntimeConfig] = None


def configure_integrations(
    config: Optional[ServerIntegrationRuntimeConfig],
) -> None:
    """Configure optional integrations for the current process.

    The CLI entrypoint uses this hook to pass bridge/Bonjour settings without
    mutating ``os.environ``. When this hook is not used, startup falls back to
    environment variables for direct ``uvicorn agent_terminal_app.server:app``
    launches.
    """

    global _integration_config_explicit, _integration_config
    _integration_config_explicit = True
    _integration_config = config


def clear_configured_integrations() -> None:
    """Return startup integration wiring to direct-env fallback mode."""

    global _integration_config_explicit, _integration_config
    _integration_config_explicit = False
    _integration_config = None


_log = logging.getLogger(__name__)


_IDEMPOTENCY_TTL_SECONDS = 10 * 60.0
_IDEMPOTENCY_MAX_ENTRIES = 2048

_idempotency_lock = threading.Lock()
_idempotency_cache: Dict[Tuple[str, str], Tuple[float, str, Any]] = {}


def _normalize_idempotency_key(raw: Optional[str]) -> Optional[str]:
    # When these route functions are called directly (outside FastAPI's
    # dependency injection), default parameters that use ``Header(...)``
    # will be instances of ``fastapi.params.Header`` rather than a string.
    if not isinstance(raw, str):
        return None
    key = raw.strip()
    return key or None


def _payload_fingerprint(payload: Any) -> str:
    try:
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
    except Exception:
        encoded = repr(payload).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _idempotency_cleanup_locked(now: float) -> None:
    if len(_idempotency_cache) <= _IDEMPOTENCY_MAX_ENTRIES and not _idempotency_cache:
        return

    expired: List[Tuple[str, str]] = []
    for cache_key, (created_at, _fingerprint, _resp) in _idempotency_cache.items():
        if (now - created_at) > _IDEMPOTENCY_TTL_SECONDS:
            expired.append(cache_key)
    for cache_key in expired:
        _idempotency_cache.pop(cache_key, None)

    if len(_idempotency_cache) <= _IDEMPOTENCY_MAX_ENTRIES:
        return

    # Best-effort eviction: drop the oldest entries.
    ordered = sorted(_idempotency_cache.items(), key=lambda item: item[1][0])
    overflow = len(_idempotency_cache) - _IDEMPOTENCY_MAX_ENTRIES
    for idx in range(max(0, overflow)):
        cache_key, _ = ordered[idx]
        _idempotency_cache.pop(cache_key, None)


def _idempotency_maybe_replay(
    scope: str, key: Optional[str], payload: Any
) -> Optional[Any]:
    idem_key = _normalize_idempotency_key(key)
    if idem_key is None:
        return None

    now = time.monotonic()
    fingerprint = _payload_fingerprint(payload)
    cache_key = (scope, idem_key)

    with _idempotency_lock:
        _idempotency_cleanup_locked(now)
        entry = _idempotency_cache.get(cache_key)
        if entry is None:
            return None

        created_at, stored_fingerprint, response = entry
        if (now - created_at) > _IDEMPOTENCY_TTL_SECONDS:
            _idempotency_cache.pop(cache_key, None)
            return None

        if stored_fingerprint != fingerprint:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Idempotency-Key has already been used with a different payload "
                    f"for scope {scope!r}"
                ),
            )

        return response


def _idempotency_store(
    scope: str, key: Optional[str], payload: Any, response: Any
) -> None:
    idem_key = _normalize_idempotency_key(key)
    if idem_key is None:
        return

    now = time.monotonic()
    fingerprint = _payload_fingerprint(payload)
    cache_key = (scope, idem_key)

    with _idempotency_lock:
        _idempotency_cleanup_locked(now)
        _idempotency_cache[cache_key] = (now, fingerprint, response)


def _snapshot_response_fields(
    app_instance: AgentApplication,
    session_id: str,
) -> Dict[str, Any]:
    snapshot_id = app_instance.get_selected_session_snapshot(session_id)
    return {
        "readonly": bool(snapshot_id),
        "snapshot_id": snapshot_id,
    }


def _effective_session_config(
    app_instance: AgentApplication,
    base_config: Any,
    session: Session,
    request_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    cfg = base_config if isinstance(base_config, dict) else {}
    return app_instance.resolve_effective_config(cfg, session, request_overrides)


def _append_message_to_session_locked(
    app_instance: AgentApplication,
    core: Any,
    config: Any,
    session: Session,
    *,
    role: str,
    content: str,
    metadata: Any,
    multipart_content: Optional[List[Dict[str, Any]]],
) -> Session:
    new_session = core.add_message(
        session,
        role,
        content,
        metadata,
        config,
        multipart_content=multipart_content,
        context=app_instance._context.build_core_handoff_context(base_config=config),
    )
    app_instance.save_session(new_session)

    last_message = new_session.messages[-1] if new_session.messages else None
    last_index = len(new_session.messages) - 1

    stored = app_instance.publish_event(
        {
            "type": "message_appended",
            "session_id": new_session.session_id,
            "index": last_index,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "message": last_message.to_dict() if last_message is not None else None,
        },
    )

    try:
        app_instance.record_checkpoint(new_session.session_id, stored.get("request_id"))
    except Exception:  # pragma: no cover - defensive
        _log.exception(
            "failed to publish checkpoint event after message append for %r",
            new_session.session_id,
        )

    return new_session


@app.on_event("startup")
async def _on_startup() -> None:
    """FastAPI startup hook.

    * Optionally advertise the HTTP API via Bonjour/mDNS.
    * Optionally start the bridge client.

    CLI launches configure these integrations explicitly so bridge identities
    are not added to ambient process env. Direct uvicorn launches continue to
    use environment variables as a fallback.
    """

    global _agent_app, _bonjour_handle, _bridge_client, _bridge_task

    explicit_config = _integration_config if _integration_config_explicit else None

    # Bonjour advertising -------------------------------------------------
    bonjour_config = explicit_config.bonjour if explicit_config is not None else None
    if bonjour_config is not None:
        port = bonjour_config.port
        service_name = bonjour_config.service_name
        _log.info(
            "[bonjour] starting registration: service=%r port=%d", service_name, port
        )
        _bonjour_handle = await asyncio.to_thread(
            bonjour_mod.start_bonjour, service_name, port
        )
        if _bonjour_handle is not None:
            _log.info(
                "[bonjour] registration finished: service=%r port=%d",
                service_name,
                port,
            )
        else:
            _log.warning(
                "[bonjour] registration failed; see earlier logs for details "
                "(service=%r port=%d)",
                service_name,
                port,
            )
    elif os.getenv("ENABLE_BONJOUR"):
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
                "[bonjour] registration finished: service=%r port=%d",
                service_name,
                port,
            )
        else:
            _log.warning(
                "[bonjour] registration failed; see earlier logs for details "
                "(service=%r port=%d)",
                service_name,
                port,
            )

    # Bridge client -------------------------------------------------------
    if explicit_config is not None and explicit_config.bridge is not None:
        client = bridge_mod.BridgeClient(explicit_config.bridge)
    else:
        client = bridge_mod.create_bridge_client_from_env()
    if client is not None:
        _bridge_client = client
        # Run the bridge client in the background for the lifetime of the
        # FastAPI application.
        _bridge_task = asyncio.create_task(client.run())


@app.on_event("shutdown")
async def _on_shutdown() -> None:
    """FastAPI shutdown hook for cleaning up integrations."""

    global _agent_app, _application_owner
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

    if _application_owner is not None:
        try:
            _application_owner.close()
        except Exception:  # pragma: no cover - defensive
            pass
        _application_owner = None
        _agent_app = None
    elif _agent_app is not None:
        try:
            _agent_app.close()
        except Exception:  # pragma: no cover - defensive
            pass
        _agent_app = None


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
        self._data: Dict[str, Any] = dict(
            initial_data or {"message": "Initial data", "count": 0}
        )
        self._lock = threading.Lock()

    def get(self) -> Dict[str, Any]:
        """Return a shallow copy of the current data mapping."""

        with self._lock:
            return dict(self._data)

    def update(self, new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge ``new_data`` into the store and return the updated mapping."""

        if not isinstance(
            new_data, dict
        ):  # Defensive guard; FastAPI normally enforces this
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
    snapshot_selector = FilesystemSnapshotSelectionStore(root / ".snapshots")
    return AgentApplication(
        str(cfg),
        str(root),
        snapshot_selection_store=snapshot_selector,
        env_overrides=_DEFAULT_RUNTIME_LAYOUT.env_overrides(),
    )


_agent_app: Optional[AgentApplication] = None
_application_owner: Optional[AgentApplicationOwner] = None


def configure_application_owner(
    owner: Optional[AgentApplicationOwner],
) -> None:
    """Use ``owner`` for process-wide application lookup and reload gating."""

    global _application_owner, _agent_app
    _application_owner = owner
    _agent_app = owner.current if owner is not None else None


# ---------------------------------------------------------------------------
# Test control hooks (integration-test only)
# ---------------------------------------------------------------------------


_TEST_CONTROL_ENABLED = os.getenv("AGENT_APP_TEST_CONTROL") == "1"

_test_events_paused = False
_test_events_release = threading.Event()
_test_events_release.set()
_test_events_waiters = 0
_test_events_lock = threading.Lock()


def _maybe_block_events_for_tests() -> None:
    if not _TEST_CONTROL_ENABLED:
        return
    global _test_events_waiters
    if not _test_events_paused:
        return

    with _test_events_lock:
        _test_events_waiters += 1
    try:
        # Bound the wait so a stuck test doesn't hang indefinitely.
        _test_events_release.wait(timeout=5)
    finally:
        with _test_events_lock:
            _test_events_waiters -= 1


def get_agent_app() -> AgentApplication:
    """Return the process-wide AgentApplication instance.

    FastAPI uses this via dependency injection; tests can call the
    route functions directly and pass a custom ``AgentApplication``
    instance for isolation.
    """

    global _agent_app

    if _application_owner is not None:
        return _application_owner.current

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
def put_api_data(
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
) -> Dict[str, Any]:
    """Merge the given JSON body into the ``DataStore`` and return it.

    The behaviour mirrors the Bonjour example server's ``PUT /api/data``
    handler: the body is treated as a partial update and the response
    includes the full updated mapping under ``updated``.
    """

    scope = "PUT /api/data"
    cached = _idempotency_maybe_replay(scope, idempotency_key, payload)
    if cached is not None:
        return cached

    try:
        updated = _bonjour_data_store.update(payload or {})
    except ValueError as exc:  # pragma: no cover - defensive; FastAPI validates payload
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response = {"success": True, "updated": updated}
    _idempotency_store(scope, idempotency_key, payload, response)
    return response


@app.get("/api/hello")
def get_api_hello() -> Dict[str, Any]:
    """Return a static greeting payload matching the Bonjour example."""

    return {
        "message": "Hello from Bonjour Server!",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "method": "GET",
    }


if _TEST_CONTROL_ENABLED:

    @app.api_route("/__test/binary", methods=["GET", "PUT"])
    async def _test_binary(
        request: Request,
        size: int = 0,
    ) -> Response:
        if request.method == "PUT":
            payload = await request.body()
        else:
            bounded_size = max(0, min(size, 5 * 1024 * 1024))
            payload = bytes(index % 251 for index in range(bounded_size))
        return Response(content=payload, media_type="application/octet-stream")

    @app.get("/__test/sleep")
    def _test_sleep(ms: int = 0) -> Dict[str, Any]:
        delay_ms = max(0, min(ms, 5000))
        if delay_ms:
            time.sleep(delay_ms / 1000.0)
        return {"slept_ms": delay_ms}

    @app.get("/__test/events/status")
    def _test_events_status() -> Dict[str, Any]:
        with _test_events_lock:
            waiters = _test_events_waiters
        return {"paused": _test_events_paused, "waiters": waiters}

    @app.post("/__test/events/pause")
    def _test_events_pause() -> Dict[str, Any]:
        global _test_events_paused
        _test_events_paused = True
        _test_events_release.clear()
        return {"paused": True}

    @app.post("/__test/events/resume")
    def _test_events_resume() -> Dict[str, Any]:
        global _test_events_paused
        _test_events_paused = False
        _test_events_release.set()
        return {"paused": False}

    @app.post("/__test/sessions/{session_id}/inject_pending_tool_call")
    def _test_inject_pending_tool_call(
        session_id: str,
        payload: Optional[Dict[str, Any]] = None,
        app_instance: AgentApplication = Depends(get_agent_app),
    ) -> Dict[str, Any]:
        body = payload or {}
        tool_name = (
            body.get("tool_name") if isinstance(body.get("tool_name"), str) else "add"
        )
        arguments = body.get("arguments")
        if not isinstance(arguments, dict):
            arguments = {"a": 2, "b": 3}
        assistant_content = (
            body.get("assistant_content")
            if isinstance(body.get("assistant_content"), str)
            else "Running tools."
        )

        ctx = app_instance.load_session(session_id)
        if ctx is None:
            raise HTTPException(
                status_code=404, detail=f"Session {session_id!r} not found"
            )
        _core, _base_config, session = ctx
        tool_call = {
            "id": "test-call-1",
            "type": "function",
            "function": {
                "name": tool_name,
                "arguments": json.dumps(arguments),
            },
        }
        updated = Session(
            session_id=session.session_id,
            messages=[
                *session.messages,
                Message(
                    role="assistant",
                    content=assistant_content,
                    metadata={"tool_calls": [tool_call]},
                ),
            ],
            metadata=session.metadata,
        )
        app_instance.save_session(updated)
        return {"session": updated.to_dict(), "tool_call": tool_call}


# ---------------------------------------------------------------------------
# Route handlers (single implementation per operation)
# ---------------------------------------------------------------------------


@app.post("/sessions")
def create_session(
    payload: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Create a session and publish a ``session_created`` event.

    The same function serves as both the FastAPI route handler and the
    core implementation: when called directly in tests, a custom
    ``AgentApplication`` can be injected via ``app_instance``.
    """

    data = payload or {}
    scope = "POST /sessions"
    cached = _idempotency_maybe_replay(scope, idempotency_key, data)
    if cached is not None:
        return cached
    raw_agent_id = data.get("agent_id")
    agent_id = raw_agent_id if isinstance(raw_agent_id, str) else ""
    agent_id = agent_id.strip()

    if not agent_id:
        agents = [a for a in app_instance.list_agents() if isinstance(a, str) and a]
        if not agents:
            raise HTTPException(status_code=400, detail="no agents configured")
        agent_id = agents[0]
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
                },
            )

            try:
                app_instance.record_checkpoint(
                    session.session_id, stored.get("request_id")
                )
            except Exception:  # pragma: no cover - defensive
                _log.exception(
                    "failed to publish checkpoint event after session create for %r",
                    session.session_id,
                )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    response = {
        "session": session.to_dict(),
        "errors": app_instance.get_config_errors(),
    }
    _idempotency_store(scope, idempotency_key, data, response)
    return response


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


def _list_plugins_for_session(
    app_instance: AgentApplication,
    core: Any,
    base_config: Dict[str, Any],
    session: Session,
) -> List[Dict[str, Any]]:
    """Return plugin metadata with enabled/source/active state for a session.

    Mirrors :meth:`TerminalApplication.list_plugins_for_session` so that
    mobile/desktop clients can manage plugins via HTTP without drifting
    from terminal behaviour.
    """

    metadata = session.metadata or {}

    agent_val = metadata.get("agent_id")
    agent_id = agent_val.strip() if isinstance(agent_val, str) else ""
    if not agent_id:
        agents = [a for a in app_instance.list_agents() if isinstance(a, str) and a]
        agent_id = agents[0] if agents else ""

    all_plugins = (
        app_instance.list_plugins_for_agent(agent_id)
        if agent_id
        else app_instance.list_plugins()
    )

    plugins_from_session = metadata.get("plugins")
    enabled_ids: Optional[set[str]]
    source: str

    if isinstance(plugins_from_session, list):
        enabled_ids = {p for p in plugins_from_session if isinstance(p, str)}
        source = "session"
    else:
        default_ids = app_instance.get_agent_plugins(agent_id) if agent_id else None
        if default_ids is None:
            enabled_ids = None
            source = "implicit"
        else:
            enabled_ids = {p for p in default_ids if isinstance(p, str)}
            source = "agent"

    overrides_val = metadata.get("overrides")
    overrides: Dict[str, Any] = overrides_val if isinstance(overrides_val, dict) else {}
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

        result.append(
            {
                **entry,
                "enabled": enabled,
                "source": src,
                "active": _is_active(kind, pid),
            }
        )

    return result


@app.get("/sessions/{session_id}/ui-schema")
def get_session_ui_schema(
    session_id: str,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return the full flattened UI schema for this session.

    The schema is computed using the session's effective config (base
    agent config merged with ``session.metadata["overrides"]``), so
    plugins can vary the returned elements by config (e.g. hide usage
    footer when ``show_usage`` is false).

    The returned list mirrors :meth:`AgentCore.get_ui_schema` for the
    session's configured agent and plugins. Each element is an
    application-defined dictionary that may describe:

    * configuration inputs (``ui_type == "config"`` or omitted),
    * per-message footer fields (``ui_type == "message_footer"``),
    * status bar fields (``ui_type == "status_bar"``), or
    * other future UI element types.

    Frontends are expected to filter elements by ``ui_type`` for their
    specific needs (for example, building settings UIs from
    configuration elements and rendering message footers or status bars
    from the corresponding schema entries).
    """

    try:
        ctx = app_instance.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")

        core, base_config, session = ctx
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides = metadata.get("overrides")
        if not isinstance(overrides, dict):
            overrides = {}
        effective_config = resolve_request_config(base_config, overrides)

        try:
            ui_schema = core.get_ui_schema(config=effective_config)
        except Exception as exc:  # pragma: no cover - defensive
            _log.exception("error getting ui_schema: %s", exc)
            ui_schema = []
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"elements": ui_schema or []}


@app.get("/sessions/{session_id}/application/ui-schema")
def get_session_application_ui_schema(
    session_id: str,
    plugin: Optional[str] = None,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return application-level UI schema for a specific session.

    The returned list contains UI elements from all registered application
    plugins, filtered by the optional ``plugin`` query parameter if provided.
    Each element includes a ``plugin`` field identifying its source.

    Frontends should call this endpoint when displaying session-scoped actions
    (e.g., "Compact range") that depend on the session's configuration.
    """

    try:
        elements = app_instance.get_session_application_ui_schema(
            session_id,
            plugin=plugin,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"elements": elements}


@app.get("/sessions/{session_id}/config/schema")
def get_session_config_schema(
    session_id: str,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return flattened config schema entries for the session's agent.

    This exposes the same data used by the terminal application's
    ``/help config`` command via :meth:`AgentCore.get_config_schema`.
    """

    try:
        ctx = app_instance.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")

        core, _base_config, _session = ctx
        try:
            schema_entries = core.get_config_schema()
        except Exception:  # pragma: no cover - defensive
            schema_entries = []
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"schema": schema_entries}


@app.get("/sessions/{session_id}/config/base")
def get_session_base_config(
    session_id: str,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return the base configuration for the session's agent.

    The base config is the agent-level configuration before any
    per-session overrides are applied. It corresponds to the "agent
    config" layer shown in the terminal ``/help config`` output.
    """

    try:
        ctx = app_instance.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")

        _core, base_config, _session = ctx
        cfg = base_config if isinstance(base_config, dict) else {}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"config": cfg}


@app.post("/sessions/{session_id}/messages")
def add_message(
    session_id: str,
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Append a message and publish a ``message_appended`` event."""

    scope = f"POST /sessions/{session_id}/messages"
    cached = _idempotency_maybe_replay(scope, idempotency_key, payload)
    if cached is not None:
        return cached

    normalized_role, content, metadata, multipart_content = (
        _validate_and_normalize_message_payload(payload)
    )

    try:
        with app_instance.acquire_session_lock(session_id):
            ctx = app_instance.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            core, base_config, session = ctx
            effective_config = _effective_session_config(
                app_instance, base_config, session
            )
            new_session = _append_message_to_session_locked(
                app_instance,
                core,
                effective_config,
                session,
                role=normalized_role,
                content=content,
                metadata=metadata,
                multipart_content=multipart_content,
            )

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReadonlySessionViewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response = {"session": new_session.to_dict()}
    _idempotency_store(scope, idempotency_key, payload, response)
    return response


def _validate_and_normalize_message_payload(
    message_payload: Dict[str, Any],
) -> Tuple[str, str, Any, Optional[List[Dict[str, Any]]]]:
    role = message_payload.get("role")
    content = message_payload.get("content")
    metadata = message_payload.get("metadata")
    multipart_content = message_payload.get("multipartContent")

    if multipart_content is not None:
        if not isinstance(multipart_content, list):
            raise HTTPException(
                status_code=400, detail="multipartContent must be a list"
            )
        if not all(isinstance(part, dict) for part in multipart_content):
            raise HTTPException(
                status_code=400, detail="multipartContent parts must be objects"
            )

    if not isinstance(role, str) or not isinstance(content, str):
        raise HTTPException(status_code=400, detail="role and content must be strings")

    if content.strip() == "" and not (
        isinstance(multipart_content, list) and multipart_content
    ):
        raise HTTPException(
            status_code=400,
            detail="content may be empty only when multipartContent is non-empty",
        )

    normalized_role = (
        role if role in {"system", "user", "assistant", "tool"} else "user"
    )
    return normalized_role, content, metadata, multipart_content


@app.get("/sessions/{session_id}/overrides")
def get_session_overrides(
    session_id: str,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return per-session configuration overrides for this session.

    Overrides are stored on the session metadata under the "overrides"
    key and correspond to the same mechanism used by the terminal
    application's ``/set`` command.
    """

    try:
        overrides = app_instance.get_session_settings(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReadonlySessionViewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"overrides": overrides}


@app.get("/server/settings")
def get_server_settings(
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return application-owned server-scoped settings."""

    return {"settings": app_instance.get_server_settings()}


@app.get("/sessions/{session_id}/plugins")
def get_session_plugins(
    session_id: str,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return plugin metadata with enabled/source/active state for a session."""

    try:
        ctx = app_instance.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")
        core, base_config, session = ctx
        cfg = base_config if isinstance(base_config, dict) else {}
        plugins = _list_plugins_for_session(app_instance, core, cfg, session)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReadonlySessionViewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"plugins": plugins}


@app.put("/sessions/{session_id}/plugins")
def put_session_plugins(
    session_id: str,
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Persist an explicit list of enabled plugin ids for a session."""

    scope = f"PUT /sessions/{session_id}/plugins"
    cached = _idempotency_maybe_replay(scope, idempotency_key, payload)
    if cached is not None:
        return cached

    enabled_val = (payload or {}).get("enabled")
    if not isinstance(enabled_val, list):
        raise HTTPException(
            status_code=400, detail="enabled must be a list of plugin ids"
        )

    seen: Dict[str, None] = {}
    normalized: List[str] = []
    for pid in enabled_val:
        if not isinstance(pid, str) or not pid:
            continue
        if pid in seen:
            continue
        seen[pid] = None
        normalized.append(pid)

    try:
        with app_instance.acquire_session_lock(session_id):
            ctx = app_instance.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            _core, _base_config, session = ctx
            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            new_metadata = {**metadata, "plugins": normalized}
            updated = Session(
                session_id=session.session_id,
                messages=session.messages,
                metadata=new_metadata,
            )
            app_instance.save_session(updated)

            refreshed = app_instance.load_session(session_id)
            if refreshed is None:
                core, base_config, loaded_session = _core, _base_config, updated
            else:
                core, base_config, loaded_session = refreshed

            cfg = base_config if isinstance(base_config, dict) else {}
            plugins = _list_plugins_for_session(app_instance, core, cfg, loaded_session)

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReadonlySessionViewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    response = {"session": loaded_session.to_dict(), "plugins": plugins}
    _idempotency_store(scope, idempotency_key, payload, response)
    return response


@app.delete("/sessions/{session_id}/plugins")
def delete_session_plugins(
    session_id: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Clear session-specific plugin overrides (returning to agent defaults)."""

    scope = f"DELETE /sessions/{session_id}/plugins"
    cached = _idempotency_maybe_replay(scope, idempotency_key, {})
    if cached is not None:
        return cached

    try:
        with app_instance.acquire_session_lock(session_id):
            ctx = app_instance.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            _core, _base_config, session = ctx
            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            if "plugins" not in metadata:
                core, base_config, loaded_session = _core, _base_config, session
            else:
                new_metadata = dict(metadata)
                new_metadata.pop("plugins", None)
                updated = Session(
                    session_id=session.session_id,
                    messages=session.messages,
                    metadata=new_metadata,
                )
                app_instance.save_session(updated)

                refreshed = app_instance.load_session(session_id)
                if refreshed is None:
                    core, base_config, loaded_session = _core, _base_config, updated
                else:
                    core, base_config, loaded_session = refreshed

            cfg = base_config if isinstance(base_config, dict) else {}
            plugins = _list_plugins_for_session(app_instance, core, cfg, loaded_session)

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReadonlySessionViewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    response = {"session": loaded_session.to_dict(), "plugins": plugins}
    _idempotency_store(scope, idempotency_key, {}, response)
    return response


@app.patch("/sessions/{session_id}/overrides")
def patch_session_overrides(
    session_id: str,
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Upsert one or more configuration overrides for a session.

    The body supports two shapes (exactly one must be provided):

    * ``{"key": str, "value": Any}`` – update a single key.
    * ``{"values": {"k": v, ...}}`` – bulk update.

    The resulting overrides are stored under
    ``session.metadata["overrides"]`` and will be merged into the
    base configuration for subsequent requests.
    """

    body = payload or {}
    scope = f"PATCH /sessions/{session_id}/overrides"
    cached = _idempotency_maybe_replay(scope, idempotency_key, body)
    if cached is not None:
        return cached
    has_single = "key" in body or "value" in body
    has_bulk = "values" in body

    if int(bool(has_single)) + int(bool(has_bulk)) != 1:
        raise HTTPException(
            status_code=400,
            detail="Exactly one of ('key' & 'value') or 'values' must be provided",
        )

    updates: Dict[str, Any]
    if has_bulk:
        values = body.get("values")
        if not isinstance(values, dict):
            raise HTTPException(
                status_code=400,
                detail="'values' must be an object mapping keys to values",
            )
        updates = dict(values)
    else:
        key = body.get("key")
        if not isinstance(key, str) or not key:
            raise HTTPException(
                status_code=400,
                detail="'key' must be a non-empty string when using the single-key form",
            )
        # Allow any JSON-serializable value for overrides.
        updates = {key: body.get("value")}

    try:
        new_session = app_instance.patch_session_settings(
            session_id,
            updates,
            source="api",
        )

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReadonlySessionViewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response = {"session": new_session.to_dict()}
    _idempotency_store(scope, idempotency_key, body, response)
    return response


@app.patch("/server/settings")
def patch_server_settings(
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Upsert one or more server-scoped settings."""

    body = payload or {}
    scope = "PATCH /server/settings"
    cached = _idempotency_maybe_replay(scope, idempotency_key, body)
    if cached is not None:
        return cached

    values = body.get("values", body)
    if not isinstance(values, dict):
        raise HTTPException(
            status_code=400,
            detail="server settings body must be an object or {'values': object}",
        )

    try:
        settings = app_instance.patch_server_settings(values, source="api")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response = {"settings": settings}
    _idempotency_store(scope, idempotency_key, body, response)
    return response


@app.get("/sessions/{session_id}/config/schema")
def get_session_config_schema(
    session_id: str,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return flattened config schema entries for this session's agent.

    The schema entries are derived from ``core.get_config_schema()`` and
    correspond to the same data used by the terminal application's
    ``/help config`` output.
    """

    try:
        ctx = app_instance.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")
        core, _base_config, _session = ctx
        schema = core.get_config_schema()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception:  # pragma: no cover - defensive
        schema = []

    return {"schema": schema}


@app.get("/sessions/{session_id}/config/base")
def get_session_base_config(
    session_id: str,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return the base agent configuration for this session.

    The returned mapping corresponds to the configuration used for this
    session's agent before applying any per-session overrides.
    """

    try:
        ctx = app_instance.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")
        _core, base_config, _session = ctx
        cfg = base_config if isinstance(base_config, dict) else {}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"config": cfg}


@app.delete("/sessions/{session_id}/overrides/{key}")
def delete_session_override(
    session_id: str,
    key: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Remove a single configuration override for the given session.

    When the key is present under ``session.metadata['overrides']`` it
    is removed; any remaining overrides are preserved. If no overrides
    remain after deletion, the ``"overrides"`` key is removed from the
    metadata entirely. Deleting a non-existent key is treated as a
    no-op and returns the current session unchanged.
    """

    if not isinstance(key, str) or not key:
        raise HTTPException(
            status_code=400,
            detail="key must be a non-empty string",
        )

    scope = f"DELETE /sessions/{session_id}/overrides/{key}"
    cached = _idempotency_maybe_replay(scope, idempotency_key, {})
    if cached is not None:
        return cached

    try:
        result_session = app_instance.delete_session_setting(
            session_id,
            key,
            source="api",
        )
        response = {"session": result_session.to_dict()}

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReadonlySessionViewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _idempotency_store(scope, idempotency_key, {}, response)
    return response


@app.delete("/server/settings/{key}")
def delete_server_setting(
    key: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Remove one server-scoped setting."""

    scope = f"DELETE /server/settings/{key}"
    cached = _idempotency_maybe_replay(scope, idempotency_key, {})
    if cached is not None:
        return cached

    try:
        settings = app_instance.delete_server_setting(key, source="api")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response = {"settings": settings}
    _idempotency_store(scope, idempotency_key, {}, response)
    return response


@app.patch("/sessions/{session_id}/messages/{index}")
def update_message(
    session_id: str,
    index: int,
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Modify the content of a single message at ``index``.

    This mirrors :meth:`TerminalApplication.modify_message` using
    Python-style indices (0-based, negatives allowed).
    """

    scope = f"PATCH /sessions/{session_id}/messages/{index}"
    cached = _idempotency_maybe_replay(scope, idempotency_key, payload)
    if cached is not None:
        return cached

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

            new_session = core.modify_message(
                session,
                target_index,
                content,
                config,
                context=app_instance._context.build_core_handoff_context(
                    base_config=base_config
                ),
            )
            app_instance.save_session(new_session)

            updated_message = new_session.messages[target_index]

            stored = app_instance.publish_event(
                {
                    "type": "message_modified",
                    "session_id": new_session.session_id,
                    "index": target_index,
                    "content": content,
                    "message": updated_message.to_dict(),
                },
            )

            try:
                app_instance.record_checkpoint(
                    new_session.session_id, stored.get("request_id")
                )
            except Exception:  # pragma: no cover - defensive
                _log.exception(
                    "failed to publish checkpoint event after message modify for %r",
                    session_id,
                )

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    response = {"session": new_session.to_dict()}
    _idempotency_store(scope, idempotency_key, payload, response)
    return response


@app.post("/sessions/{session_id}/send")
def send_request(
    session_id: str,
    payload: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Start ``AgentApplication.send_request`` in the background.

    The HTTP response is an immediate acknowledgement; clients are
    expected to observe progress and results via the event store and
    session history rather than the response body.
    """

    data = payload or {}
    scope = f"POST /sessions/{session_id}/send"
    cached = _idempotency_maybe_replay(scope, idempotency_key, data)
    if cached is not None:
        return cached

    overrides = data.get("config_overrides") or {}

    if overrides is not None and not isinstance(overrides, dict):
        raise HTTPException(
            status_code=400,
            detail="config_overrides must be a mapping if provided",
        )

    try:
        started = app_instance.start_session_request(
            session_id,
            overrides,
            stream=True,
        )
    except KeyError as exc:
        detail = exc.args[0] if exc.args and isinstance(exc.args[0], str) else str(exc)
        if isinstance(detail, str) and detail.startswith("Unknown agent_id"):
            raise HTTPException(status_code=400, detail=detail) from exc
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReadonlySessionViewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except SessionOperationBusyError as exc:
        raise HTTPException(
            status_code=409,
            detail={"status": "session_busy", "operation": exc.operation},
        ) from exc
    except (
        ApplicationReloadPendingError,
        SessionRequestCoordinatorClosedError,
        StaleApplicationGenerationError,
    ) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response = {
        "status": started.status,
        "request_id": started.request_id,
    }
    _idempotency_store(scope, idempotency_key, data, response)
    return response


@app.post("/sessions/{session_id}/send_message")
def send_message(
    session_id: str,
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Atomically append a message and start ``send_request``.

    This endpoint exists to eliminate the retry window created by the
    legacy two-call flow (append message, then POST /send).
    """

    body = payload or {}
    message = body.get("message")
    if not isinstance(message, dict):
        raise HTTPException(status_code=400, detail="message must be an object")

    normalized_role, content, metadata, multipart_content = (
        _validate_and_normalize_message_payload(message)
    )

    raw_overrides = body.get("config_overrides")
    overrides = raw_overrides if raw_overrides is not None else {}
    if not isinstance(overrides, dict):
        raise HTTPException(
            status_code=400,
            detail="config_overrides must be a mapping if provided",
        )

    body_idem = body.get("idempotency_key")
    effective_idempotency_key = idempotency_key
    if _normalize_idempotency_key(effective_idempotency_key) is None and isinstance(
        body_idem, str
    ):
        effective_idempotency_key = body_idem

    scope = f"POST /sessions/{session_id}/send_message"
    idempotency_payload = {
        "message": message,
        "config_overrides": overrides,
    }

    cached = _idempotency_maybe_replay(
        scope, effective_idempotency_key, idempotency_payload
    )
    if cached is not None:
        return cached

    try:
        started = app_instance.start_session_request_with_message(
            session_id,
            role=normalized_role,
            content=content,
            metadata=metadata,
            multipart_content=multipart_content,
            overrides=overrides,
            stream=True,
        )
        if started.status == "already_running":
            raise HTTPException(
                status_code=409,
                detail={
                    "status": "already_running",
                    "request_id": started.request_id,
                },
            )

        response = {
            "status": "started",
            "request_id": started.request_id,
            "session_id": session_id,
        }
        _idempotency_store(
            scope, effective_idempotency_key, idempotency_payload, response
        )
    except ReadonlySessionViewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        detail = exc.args[0] if exc.args and isinstance(exc.args[0], str) else str(exc)
        if isinstance(detail, str) and detail.startswith("Unknown agent_id"):
            raise HTTPException(status_code=400, detail=detail) from exc
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SessionOperationBusyError as exc:
        raise HTTPException(
            status_code=409,
            detail={"status": "session_busy", "operation": exc.operation},
        ) from exc
    except (
        ApplicationReloadPendingError,
        SessionRequestCoordinatorClosedError,
        StaleApplicationGenerationError,
    ) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return response


@app.delete("/sessions/{session_id}/messages")
def delete_messages(
    session_id: str,
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
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
    scope = f"DELETE /sessions/{session_id}/messages"
    cached = _idempotency_maybe_replay(scope, idempotency_key, body)
    if cached is not None:
        return cached
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
                    response = {"session": session.to_dict(), "deleted_indices": []}
                    _idempotency_store(scope, idempotency_key, body, response)
                    return response

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
                    raise HTTPException(
                        status_code=400, detail="range must be an object"
                    )

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
                    start_idx, end_idx = _normalize_slice_bounds(
                        message_count, start, end
                    )
                except ValueError as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc

                delete_indices = list(range(start_idx, end_idx))

            else:  # has_last
                last = body.get("last")
                if not isinstance(last, int):
                    raise HTTPException(
                        status_code=400, detail="last must be an integer"
                    )
                if last <= 0:
                    raise HTTPException(
                        status_code=400, detail="count must be a positive integer"
                    )

                count = min(last, message_count)
                start_idx = message_count - count
                delete_indices = list(range(start_idx, message_count))

            if not delete_indices:
                raise HTTPException(
                    status_code=400, detail="no messages selected for deletion"
                )

            # Perform the deletion via the core, mirroring TerminalApplication.delete_messages.
            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            overrides_val = metadata.get("overrides")
            overrides: Dict[str, Any] = (
                overrides_val if isinstance(overrides_val, dict) else {}
            )
            config = resolve_request_config(base_config, overrides)

            new_session = core.slice_session(
                session, config, remove_indices=delete_indices
            )
            app_instance.save_session(new_session)

            concrete_indices = sorted(set(delete_indices))

            stored = app_instance.publish_event(
                {
                    "type": "messages_deleted",
                    "session_id": new_session.session_id,
                    "indices": concrete_indices,
                },
            )

            try:
                app_instance.record_checkpoint(
                    new_session.session_id, stored.get("request_id")
                )
            except Exception:  # pragma: no cover - defensive
                _log.exception(
                    "failed to publish checkpoint event after messages delete for %r",
                    session_id,
                )

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReadonlySessionViewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    response = {"session": new_session.to_dict(), "deleted_indices": concrete_indices}
    _idempotency_store(scope, idempotency_key, body, response)
    return response


@app.get("/sessions")
def list_sessions(
    limit: Optional[int] = None,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """List shared application-layer session summaries."""

    return {"sessions": app_instance.list_session_summaries(limit=limit)}


@app.post("/sessions/request-statuses")
def get_session_request_statuses(
    payload: Dict[str, Any],
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return derived request status for explicitly requested sessions."""

    if "session_ids" not in payload:
        raise HTTPException(status_code=400, detail="session_ids is required")
    session_ids = payload.get("session_ids")
    if not isinstance(session_ids, list):
        raise HTTPException(
            status_code=400,
            detail="session_ids must be a list of non-empty strings",
        )
    try:
        response = app_instance.get_session_request_statuses(session_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        **response,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/sessions/{session_id}/summary")
def get_session_summary(
    session_id: str,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return a fresh summary for one session.

    The shape matches a single item from ``GET /sessions`` so UI code can
    refresh the session context it uses for metadata-driven action surfaces
    without reloading the entire sessions list.
    """

    try:
        summary = app_instance.get_session_summary(session_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail=f"Session {session_id!r} not found"
        ) from exc
    return {"session": summary}


@app.get("/sessions/{session_id}/snapshots")
def list_session_snapshots(
    session_id: str,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    try:
        snapshots = app_instance.list_session_snapshots(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReadonlySessionViewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "snapshots": [
            {
                "snapshot_id": snap.snapshot_id,
                "session_id": snap.session_id,
                "created_at": snap.created_at,
                "reason": snap.reason,
            }
            for snap in snapshots
        ]
    }


@app.post("/sessions/{session_id}/snapshots")
def create_session_snapshot(
    session_id: str,
    payload: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    body = payload or {}
    scope = f"POST /sessions/{session_id}/snapshots"
    cached = _idempotency_maybe_replay(scope, idempotency_key, body)
    if cached is not None:
        return cached
    reason = body.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise HTTPException(status_code=400, detail="reason must be a non-empty string")
    try:
        with app_instance.acquire_session_lock(session_id):
            snapshot = app_instance.create_session_snapshot(
                session_id,
                reason=reason.strip(),
                metadata=(
                    body.get("metadata")
                    if isinstance(body.get("metadata"), dict)
                    else None
                ),
            )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    response = {
        "snapshot": {
            "snapshot_id": snapshot.snapshot_id,
            "session_id": snapshot.session_id,
            "created_at": snapshot.created_at,
            "reason": snapshot.reason,
        }
    }
    _idempotency_store(scope, idempotency_key, body, response)
    return response


@app.get("/sessions/{session_id}/snapshots/selected")
def get_selected_session_snapshot(
    session_id: str,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    selected = app_instance.get_selected_session_snapshot(session_id)
    return {"snapshot_id": selected}


@app.post("/sessions/{session_id}/snapshots/{snapshot_id}/select")
def select_session_snapshot(
    session_id: str,
    snapshot_id: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    scope = f"POST /sessions/{session_id}/snapshots/{snapshot_id}/select"
    cached = _idempotency_maybe_replay(scope, idempotency_key, {})
    if cached is not None:
        return cached
    if app_instance.get_active_session_request_id(session_id) is not None:
        raise HTTPException(
            status_code=409, detail="Cannot select snapshot while a request is running"
        )
    try:
        with app_instance.acquire_session_lock(session_id):
            app_instance.select_session_snapshot(session_id, snapshot_id)
            stored = app_instance.publish_event(
                {
                    "type": "session_snapshot_selected",
                    "session_id": session_id,
                    "snapshot_id": snapshot_id,
                }
            )
            event_id = stored.get("event_id")
            if isinstance(event_id, str) and event_id:
                app_instance.advance_session_cursor(session_id, event_id)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    response = {"status": "ok", "snapshot_id": snapshot_id}
    _idempotency_store(scope, idempotency_key, {}, response)
    return response


@app.delete("/sessions/{session_id}/snapshots/selected")
def clear_selected_session_snapshot(
    session_id: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    scope = f"DELETE /sessions/{session_id}/snapshots/selected"
    cached = _idempotency_maybe_replay(scope, idempotency_key, {})
    if cached is not None:
        return cached
    with app_instance.acquire_session_lock(session_id):
        app_instance.clear_selected_session_snapshot(session_id)
        stored = app_instance.publish_event(
            {
                "type": "session_snapshot_cleared",
                "session_id": session_id,
            }
        )
        event_id = stored.get("event_id")
        if isinstance(event_id, str) and event_id:
            app_instance.advance_session_cursor(session_id, event_id)
    response = {"status": "ok", "snapshot_id": None}
    _idempotency_store(scope, idempotency_key, {}, response)
    return response


@app.post("/sessions/{session_id}/snapshots/{snapshot_id}/restore")
def restore_session_snapshot(
    session_id: str,
    snapshot_id: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    scope = f"POST /sessions/{session_id}/snapshots/{snapshot_id}/restore"
    cached = _idempotency_maybe_replay(scope, idempotency_key, {})
    if cached is not None:
        return cached
    if app_instance.get_active_session_request_id(session_id) is not None:
        raise HTTPException(
            status_code=409, detail="Cannot restore snapshot while a request is running"
        )
    try:
        with app_instance.acquire_session_lock(session_id):
            restored = app_instance.restore_session_snapshot(session_id, snapshot_id)
            stored = app_instance.publish_event(
                {
                    "type": "session_restored_from_snapshot",
                    "session_id": session_id,
                    "snapshot_id": snapshot_id,
                }
            )
            event_id = stored.get("event_id")
            if isinstance(event_id, str) and event_id:
                app_instance.advance_session_cursor(session_id, event_id)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    response = {"status": "ok", "session": restored.to_dict()}
    _idempotency_store(scope, idempotency_key, {}, response)
    return response


@app.delete("/sessions/{session_id}/snapshots/{snapshot_id}")
def delete_session_snapshot(
    session_id: str,
    snapshot_id: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    scope = f"DELETE /sessions/{session_id}/snapshots/{snapshot_id}"
    cached = _idempotency_maybe_replay(scope, idempotency_key, {})
    if cached is not None:
        return cached
    try:
        deleted = app_instance.delete_session_snapshot(session_id, snapshot_id)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = {"status": "ok", "deleted": bool(deleted)}
    _idempotency_store(scope, idempotency_key, {}, response)
    return response


@app.post("/sessions/{session_id}/fork")
def fork_session(
    session_id: str,
    payload: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Create a new session by forking history up to ``index``.

    The body accepts ``{"index": int}`` where the index uses
    Python-style semantics (0-based, negatives allowed). When omitted,
    ``index`` defaults to ``-1`` (fork full history).
    """

    data = payload or {}
    scope = f"POST /sessions/{session_id}/fork"
    cached = _idempotency_maybe_replay(scope, idempotency_key, data)
    if cached is not None:
        return cached
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

            new_session_id = str(uuid.uuid4())
            _new_core, _new_base_config, new_session = app_instance.fork_session(
                core,
                session,
                base_config,
                upto_index=target_index,
                new_session_id=new_session_id,
            )

            app_instance.save_session(new_session)

            # Publish a lifecycle event so frontends can surface the fork.
            md = new_session.metadata if isinstance(new_session.metadata, dict) else {}
            agent_val = md.get("agent_id")
            agent_id = agent_val.strip() if isinstance(agent_val, str) else ""
            stored = app_instance.publish_event(
                {
                    "type": "session_created",
                    "session_id": new_session.session_id,
                    "agent_id": agent_id,
                    "source_session_id": session.session_id,
                    "fork_upto_index": target_index,
                },
            )

            try:
                app_instance.record_checkpoint(
                    new_session.session_id, stored.get("request_id")
                )
            except Exception:  # pragma: no cover - defensive
                _log.exception(
                    "failed to publish checkpoint event after fork for %r",
                    new_session.session_id,
                )

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReadonlySessionViewError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    response = {
        "session": new_session.to_dict(),
        "source_session_id": session.session_id,
    }
    _idempotency_store(scope, idempotency_key, data, response)
    return response


@app.get("/sessions/{session_id}/messages")
def list_session_messages(
    session_id: str,
    start: Optional[int] = None,
    end: Optional[int] = None,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """List messages for a session with optional slice-style bounds."""

    snapshot_fields = _snapshot_response_fields(app_instance, session_id)
    try:
        with app_instance.acquire_session_lock(session_id):
            session = app_instance.load_session_record(session_id)
            if session is None:
                raise KeyError(f"Session {session_id!r} not found")
            message_count = len(session.messages)

            if message_count == 0:
                return {
                    "messages": [],
                    "cursor_event_id": app_instance.get_session_cursor_event_id(
                        session_id
                    ),
                    **snapshot_fields,
                }

            try:
                start_idx, end_idx = _normalize_slice_bounds(message_count, start, end)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

            results: List[Dict[str, Any]] = []
            for idx in range(start_idx, end_idx):
                msg = session.messages[idx]
                results.append(
                    {
                        "index": idx,
                        "message": msg.to_dict(),
                    }
                )

            cursor_event_id = app_instance.get_session_cursor_event_id(session_id)

            # Derive the active_request_id for this snapshot from the
            # checkpoint event at cursor_event_id, if any. The
            # AgentApplication guarantees that the per-session cursor
            # corresponds to the event_id of a published "checkpoint"
            # event created via record_checkpoint(session_id,
            # request_id).
            active_request_id: Optional[str] = None
            if cursor_event_id is not None and not snapshot_fields["readonly"]:
                store = app_instance.get_event_store()
                ev = store.get_event_by_id(cursor_event_id)
                if ev is not None and ev.get("type") == "checkpoint":
                    rid = ev.get("request_id")
                    if isinstance(rid, str) and rid:
                        active_request_id = rid

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "messages": results,
        "cursor_event_id": cursor_event_id,
        "active_request_id": active_request_id,
        **snapshot_fields,
    }


@app.get("/events")
def list_events(
    since_id: Optional[str] = None,
    request_id: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 100,
    internal_limit: int = 5000,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """List events from the application's event store.

    The ``internal_limit`` parameter (default 5000) bounds the raw
    un-compacted event list retrieved from the store. After compaction,
    ``limit`` (default 100) caps the response so clients do not receive
    excessively large batches.
    """

    _maybe_block_events_for_tests()

    store = app_instance.get_event_store()
    try:
        latest_event_id = store.get_latest_event_id()
    except AttributeError:  # pragma: no cover - defensive
        latest_event_id = None
    # ``internal_limit`` bounds the number of raw events loaded from
    # the store so that compaction has sufficient context without
    # unbounded memory usage. ``limit`` caps the number of events
    # returned *after* compaction.
    if internal_limit <= 0:
        internal_limit = 5000
    if limit <= 0:
        limit = 100
    # Global bootstrap: when no filters or cursor are provided, do not
    # return the entire history. Instead, expose only the latest
    # event_id so that clients can start polling from "now".
    if since_id is None and session_id is None and request_id is None:
        return {
            "events": [],
            "latest_event_id": latest_event_id,
            "cursor_expired": False,
        }

    effective_since_id = since_id
    # When filtering by session but no since_id is provided, default to
    # the persisted cursor for that session so that polling does not
    # replay the entire history.
    if effective_since_id is None and session_id is not None:
        try:
            effective_since_id = app_instance.get_session_cursor_event_id(session_id)
        except Exception:  # pragma: no cover - defensive
            effective_since_id = None

    listed = store.list(
        since_id=effective_since_id,
        request_id=request_id,
        session_id=session_id,
        limit=internal_limit,
    )
    events = listed.get("events") or []
    compacted = app_instance.compact_events(events)
    if session_id is not None:
        selected_snapshot_id = app_instance.get_selected_session_snapshot(session_id)
        if isinstance(selected_snapshot_id, str) and selected_snapshot_id:
            allowed_types = {
                "session_snapshot_selected",
                "session_snapshot_cleared",
                "session_restored_from_snapshot",
            }
            compacted = [
                ev
                for ev in compacted
                if isinstance(ev, dict) and ev.get("type") in allowed_types
            ]
    if len(compacted) > limit:
        compacted = compacted[:limit]
    return {
        "events": compacted,
        "latest_event_id": latest_event_id,
        "cursor_expired": bool(listed.get("cursor_expired")),
    }


@app.post("/requests/{request_id}/cancel")
def cancel_request(
    request_id: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Request cooperative cancellation for an in-flight request.

    This is a thin wrapper around :meth:`AgentApplication.cancel_request`.
    """

    scope = f"POST /requests/{request_id}/cancel"
    cached = _idempotency_maybe_replay(scope, idempotency_key, {})
    if cached is not None:
        return cached

    try:
        app_instance.cancel_request(request_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response = {"request_id": request_id, "status": "cancelled"}
    _idempotency_store(scope, idempotency_key, {}, response)
    return response


@app.post("/requests/{request_id}/soft-cancel")
def soft_cancel_request(
    request_id: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Stop a request after its active foreground tool finishes."""

    scope = f"POST /requests/{request_id}/soft-cancel"
    cached = _idempotency_maybe_replay(scope, idempotency_key, {})
    if cached is not None:
        return cached

    try:
        app_instance.soft_cancel_request(request_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response = {
        "request_id": request_id,
        "status": "soft_cancel_requested",
    }
    _idempotency_store(scope, idempotency_key, {}, response)
    return response


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
        session = app_instance.load_session_record(session_id)
        if session is None:
            raise KeyError(f"Session {session_id!r} not found")
        metadata = session.metadata or {}
        agent_val = metadata.get("agent_id")
        agent_id = agent_val if isinstance(agent_val, str) else ""
        agent_id = agent_id.strip()

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"agent_id": agent_id}


@app.patch("/sessions/{session_id}/agent")
def update_session_agent(
    session_id: str,
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Switch the agent for a given session.

    Behaviour mirrors :meth:`TerminalApplication.switch_agent`:

    * ``agent_id`` must be a non-empty string.
    * The target agent id must exist in the configured agents.
    * The updated session metadata is persisted when the session has
      messages or has previously been saved to disk.
    """

    scope = f"PATCH /sessions/{session_id}/agent"
    cached = _idempotency_maybe_replay(scope, idempotency_key, payload)
    if cached is not None:
        return cached

    target_agent_id = payload.get("agent_id")
    if not isinstance(target_agent_id, str) or not target_agent_id:
        raise HTTPException(
            status_code=400, detail="agent_id must be a non-empty string"
        )

    # Validate the target agent using the same semantics as the terminal app.
    available = [a for a in app_instance.list_agents() if isinstance(a, str) and a]
    if target_agent_id not in available:
        raise HTTPException(
            status_code=400, detail=f"unknown agent: {target_agent_id!r}"
        )

    try:
        with app_instance.acquire_session_lock(session_id):
            session = app_instance.load_session_record(session_id)
            if session is None:
                raise KeyError(f"Session {session_id!r} not found")

            _core, _base_config, new_session = app_instance.update_agent(
                target_agent_id, session
            )

            # Decide whether to persist the updated session:
            # - If the session has messages, always save.
            # - If it is empty but was previously saved, update the file.
            # - If it is empty and has never been saved, keep it in memory.
            is_empty = not session.messages
            is_persisted = (
                app_instance.load_live_session_record(session.session_id) is not None
            )
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

    response = {"session": new_session.to_dict(), "agent_id": target_agent_id}
    _idempotency_store(scope, idempotency_key, payload, response)
    return response


def _notification_mutation_inputs(
    payload: Optional[Dict[str, Any]],
) -> tuple[int | str | None, str | None]:
    body = payload or {}
    expected_revision = body.get("expected_revision")
    if isinstance(expected_revision, bool) or not (
        expected_revision is None or isinstance(expected_revision, (int, str))
    ):
        raise HTTPException(
            status_code=400,
            detail="expected_revision must be an integer, string, or null",
        )
    if isinstance(expected_revision, int) and expected_revision <= 0:
        raise HTTPException(
            status_code=400,
            detail="expected_revision integer must be greater than zero",
        )
    if isinstance(expected_revision, str) and not expected_revision:
        raise HTTPException(
            status_code=400,
            detail="expected_revision string must be non-empty",
        )
    reason = body.get("reason")
    if reason is not None and not isinstance(reason, str):
        raise HTTPException(status_code=400, detail="reason must be a string or null")
    return expected_revision, reason


def _raise_notification_mutation_error(exc: Exception) -> None:
    if isinstance(
        exc,
        (
            NotificationRevisionConflictError,
            NotificationTransitionError,
            NotificationOperationSupersededError,
        ),
    ):
        raise HTTPException(
            status_code=409,
            detail={
                "error_type": exc.error_type,
                "message": str(exc),
                "notification": exc.current,
            },
        ) from exc
    if isinstance(exc, KeyError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise exc


@app.get("/application/notifications")
def list_application_notifications(
    include_terminal: bool = False,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return the current application-owner notification snapshot."""

    return {
        "notifications": app_instance.list_application_notifications(
            include_terminal=include_terminal
        )
    }


@app.post("/application/notifications/{notification_id}/dismiss")
def dismiss_application_notification(
    notification_id: str,
    payload: Optional[Dict[str, Any]] = None,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Persist dismissal in the application notification store."""

    expected_revision, reason = _notification_mutation_inputs(payload)
    try:
        notification = app_instance.dismiss_application_notification(
            notification_id,
            reason=reason,
            expected_revision=expected_revision,
        )
    except Exception as exc:
        _raise_notification_mutation_error(exc)
        raise AssertionError("unreachable") from exc
    return {"notification": notification}


@app.get("/sessions/{session_id}/notifications")
def list_session_notifications(
    session_id: str,
    include_terminal: bool = False,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return the authoritative notification collection for one session."""

    try:
        notifications = app_instance.list_session_notifications(
            session_id,
            include_terminal=include_terminal,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"notifications": notifications}


@app.post("/sessions/{session_id}/notifications/{notification_id}/dismiss")
def dismiss_session_notification(
    session_id: str,
    notification_id: str,
    payload: Optional[Dict[str, Any]] = None,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Persist dismissal in the owning session notification record."""

    expected_revision, reason = _notification_mutation_inputs(payload)
    try:
        notification = app_instance.dismiss_session_notification(
            session_id,
            notification_id,
            reason=reason,
            expected_revision=expected_revision,
        )
    except Exception as exc:
        _raise_notification_mutation_error(exc)
        raise AssertionError("unreachable") from exc
    return {"notification": notification}


@app.get("/application/actions")
def list_application_actions(
    plugin: Optional[str] = None,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return application-level action definitions.

    The response is a flat list of action dictionaries contributed by
    all registered application plugins. When ``plugin`` is provided,
    only actions for that plugin id are returned.
    """

    actions = app_instance.get_application_actions()
    if plugin:
        actions = [
            a for a in actions if isinstance(a, dict) and a.get("plugin") == plugin
        ]
    else:
        actions = [a for a in actions if isinstance(a, dict)]
    return {"actions": actions}


@app.get("/application/ui-schema")
def list_application_ui_schema(
    plugin: Optional[str] = None,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return application-level UI schema elements.

    The response is a flat list of UI element dictionaries from all
    application plugins. When ``plugin`` is provided, the list is
    filtered to entries whose ``plugin`` field matches the value.
    """

    elements = app_instance.get_application_ui_schema()
    if plugin:
        elements = [
            e for e in elements if isinstance(e, dict) and e.get("plugin") == plugin
        ]
    else:
        elements = [e for e in elements if isinstance(e, dict)]
    return {"elements": elements}


@app.get("/server/settings/ui-schema")
def get_server_settings_ui_schema(
    plugin: Optional[str] = None,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Return application UI schema elements for server settings."""

    elements = app_instance.get_server_settings_ui_schema()
    if plugin:
        elements = [
            e for e in elements if isinstance(e, dict) and e.get("plugin") == plugin
        ]
    else:
        elements = [e for e in elements if isinstance(e, dict)]
    return {"elements": elements}


def _execute_action_request(
    payload: Dict[str, Any],
    *,
    idempotency_key: Optional[str],
    app_instance: AgentApplication,
    scope_prefix: str,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute an application action request and return the standard envelope."""

    body = payload or {}
    plugin_id = body.get("plugin")
    action_id = body.get("action_id")
    action_owner = body.get("action_owner")
    raw_inputs = body.get("inputs") or {}

    scope = f"{scope_prefix}/{plugin_id}/{action_id}"
    cached = _idempotency_maybe_replay(scope, idempotency_key, body)
    if cached is not None:
        return cached

    resolved_plugin_id = plugin_id

    try:
        action_context = {"session_id": session_id} if session_id else None
        executed = app_instance.execute_action_with_metadata(
            plugin_id=plugin_id if "plugin" in body else None,
            action_id=action_id,
            params=raw_inputs,
            action_owner=action_owner if isinstance(action_owner, str) else None,
            context=action_context,
        )
        resolved_plugin_id = executed.plugin_id
        result = executed.result
        if not isinstance(result, dict):
            result = {}
        response: Dict[str, Any] = {
            "status": "ok",
            "plugin": resolved_plugin_id,
            "action_id": executed.action_id,
            "action_owner": executed.action_owner,
            "result": result,
        }
    except AgentApplication._ApplicationActionResolutionError as exc:  # type: ignore[attr-defined]
        response = {
            "status": "error",
            "plugin": resolved_plugin_id,
            "action_id": action_id,
            "action_owner": action_owner,
            "error_type": getattr(exc, "error_type", "unknown_action"),
            "message": str(exc),
            "details": getattr(exc, "details", {}) or {},
        }
    except AgentApplication._ApplicationActionValidationError as exc:  # type: ignore[attr-defined]
        response = {
            "status": "error",
            "plugin": resolved_plugin_id,
            "action_id": action_id,
            "action_owner": action_owner,
            "error_type": "validation",
            "message": str(exc),
            "details": getattr(exc, "details", {}) or {},
        }
    except KeyError as exc:
        response = {
            "status": "error",
            "plugin": resolved_plugin_id,
            "action_id": action_id,
            "action_owner": action_owner,
            "error_type": "not_found",
            "message": str(exc),
            "details": {},
        }
    except SessionConflictError as exc:
        response = {
            "status": "error",
            "plugin": resolved_plugin_id,
            "action_id": action_id,
            "action_owner": action_owner,
            "error_type": "conflict",
            "message": str(exc),
            "details": {},
        }
    except ReadonlySessionViewError as exc:
        response = {
            "status": "error",
            "plugin": resolved_plugin_id,
            "action_id": action_id,
            "action_owner": action_owner,
            "error_type": "readonly",
            "message": str(exc),
            "details": {},
        }
    except ValueError as exc:
        # Includes invalid plugin/action identifiers or non-dict params.
        response = {
            "status": "error",
            "plugin": resolved_plugin_id,
            "action_id": action_id,
            "action_owner": action_owner,
            "error_type": "validation",
            "message": str(exc),
            "details": {},
        }
    except Exception as exc:  # pragma: no cover - defensive
        _log.exception("unexpected error executing application action")
        response = {
            "status": "error",
            "plugin": resolved_plugin_id,
            "action_id": action_id,
            "action_owner": action_owner,
            "error_type": "internal",
            "message": str(exc),
            "details": {},
        }

    _idempotency_store(scope, idempotency_key, body, response)
    return response


@app.post("/actions")
def execute_action(
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Execute an application-level action.

    The response always uses an explicit status envelope and never
    embeds full session objects; callers should observe session
    changes via the existing /sessions and /sessions/{id}/messages
    endpoints.
    """

    return _execute_action_request(
        payload,
        idempotency_key=idempotency_key,
        app_instance=app_instance,
        scope_prefix="POST /actions",
    )


@app.post("/sessions/{session_id}/actions")
def execute_session_action(
    session_id: str,
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """Execute an application action through a session-scoped alias route."""

    return _execute_action_request(
        payload,
        idempotency_key=idempotency_key,
        app_instance=app_instance,
        scope_prefix=f"POST /sessions/{session_id}/actions",
        session_id=session_id,
    )


# ---------------------------------------------------------------------------
# Helper for running under uvicorn or from the CLI
# ---------------------------------------------------------------------------


def run_api(
    host: str = "127.0.0.1",
    port: int = 8000,
    app_instance: Optional[AgentApplication] = None,
    app_owner: Optional[AgentApplicationOwner] = None,
    *,
    log_config: object = "default",
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

    global _agent_app, _application_owner
    if app_owner is not None:
        configure_application_owner(app_owner)
    elif app_instance is not None:
        _application_owner = None
        _agent_app = app_instance

    # Expose host/port via environment variables so that optional
    # integrations (Bonjour, bridge client) can infer the local HTTP
    # base URL and advertised port when the server is launched via this
    # helper instead of directly through ``uvicorn``.
    os.environ.setdefault("SERVER_HOST", host)
    os.environ.setdefault("SERVER_PORT", str(port))

    kwargs: Dict[str, Any] = {
        "host": host,
        "port": port,
        "reload": False,
    }

    # By default, uvicorn configures logging (and emits to stdout). When the
    # terminal console is also running, that can be noisy. Allow the CLI to
    # disable uvicorn logging configuration by passing log_config=None.
    if log_config != "default":
        kwargs["log_config"] = log_config

    uvicorn.run("agent_terminal_app.server:app", **kwargs)
