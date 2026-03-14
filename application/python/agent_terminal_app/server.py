from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import asyncio
import hashlib
import json
import os
import threading
import logging
import time
import uuid
from datetime import datetime

from agent_core.utils import get_logger

try:  # Optional convenience in local usage
    from dotenv import load_dotenv  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - optional dependency
    load_dotenv = None  # type: ignore[assignment]

from fastapi import Depends, FastAPI, Header, HTTPException  # type: ignore[reportMissingImports]

from agent_app.application_future import AgentApplication
from agent_app.config import resolve_request_config
from agent_core import Session
from agent_terminal_app import bonjour as bonjour_mod
from agent_terminal_app import bridge_client as bridge_mod


_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config_openrouter_app_layer.json"
_DEFAULT_SESSION_ROOT = Path(__file__).resolve().parent / "sessions"

_log = get_logger(__name__)


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


# ---------------------------------------------------------------------------
# Process-local concurrency guards
# ---------------------------------------------------------------------------


_send_single_flight_lock = threading.Lock()
_active_send_request_by_session: Dict[str, str] = {}


def _get_active_send_request_id(session_id: str) -> Optional[str]:
    with _send_single_flight_lock:
        return _active_send_request_by_session.get(session_id)


def _set_active_send_request_id(session_id: str, request_id: str) -> None:
    with _send_single_flight_lock:
        _active_send_request_by_session[session_id] = request_id


def _reserve_active_send_request_id(session_id: str, request_id: str) -> Optional[str]:
    """Reserve ``request_id`` as the active send for ``session_id``.

    Returns the existing active request id when the session already has
    a send in flight; returns ``None`` when the reservation succeeds.
    """

    with _send_single_flight_lock:
        existing = _active_send_request_by_session.get(session_id)
        if existing is not None:
            return existing
        _active_send_request_by_session[session_id] = request_id
        return None


def _clear_active_send_request_id(session_id: str, request_id: str) -> None:
    with _send_single_flight_lock:
        current = _active_send_request_by_session.get(session_id)
        if current == request_id:
            _active_send_request_by_session.pop(session_id, None)


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


def _idempotency_maybe_replay(scope: str, key: Optional[str], payload: Any) -> Optional[Any]:
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


def _idempotency_store(scope: str, key: Optional[str], payload: Any, response: Any) -> None:
    idem_key = _normalize_idempotency_key(key)
    if idem_key is None:
        return

    now = time.monotonic()
    fingerprint = _payload_fingerprint(payload)
    cache_key = (scope, idem_key)

    with _idempotency_lock:
        _idempotency_cleanup_locked(now)
        _idempotency_cache[cache_key] = (now, fingerprint, response)


def _generate_request_id(app_instance: AgentApplication) -> str:
    """Generate a request id matching AgentApplication conventions."""

    new_rid = getattr(app_instance, "_new_request_id", None)
    if callable(new_rid):
        try:
            rid = new_rid()
            if isinstance(rid, str) and rid:
                return rid
        except Exception:  # pragma: no cover - defensive
            pass
    return str(uuid.uuid4())


def _load_session_ctx_for_send(
    app_instance: AgentApplication,
    session_id: str,
    overrides: Optional[Dict[str, Any]] = None,
) -> Tuple[Any, Any, Session]:
    try:
        session_record = app_instance.load_session_record(session_id)
        if session_record is None:
            raise KeyError(f"Session {session_id!r} not found")

        ctx = app_instance.load_session(session_id, overrides=overrides)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")

        return ctx
    except KeyError as exc:
        detail = exc.args[0] if exc.args and isinstance(exc.args[0], str) else str(exc)
        if isinstance(detail, str) and detail.startswith("Unknown agent_id"):
            raise HTTPException(status_code=400, detail=detail) from exc
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _merged_session_overrides(
    session: Session,
    request_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    stored_val = metadata.get("overrides")
    stored_overrides: Dict[str, Any] = (
        stored_val if isinstance(stored_val, dict) else {}
    )
    http_overrides = request_overrides if isinstance(request_overrides, dict) else {}
    return {**stored_overrides, **http_overrides}


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


class SessionListCache:
    """In-memory cache for ``/sessions`` summaries.

    Entries are keyed by ``session_id`` and store the file modification
    time along with the precomputed preview and metadata. The cache is
    maintained per session-root directory so that tests and multiple
    AgentApplication instances do not interfere with each other.
    """

    def __init__(self) -> None:
        self.entries_by_id: Dict[str, Dict[str, Any]] = {}
        # Per-session ordering specs returned by ``session_list`` actions.
        # Each value is a list of raw spec descriptors as consumed by
        # ``_apply_session_list_ordering``.
        self.order_specs_by_id: Dict[str, List[Dict[str, Any]]] = {}
        self.lock = threading.Lock()


_session_list_caches_lock = threading.Lock()
_session_list_caches: Dict[Path, SessionListCache] = {}


_MISSING = object()


def _get_session_list_cache(root: Path) -> SessionListCache:
    """Return (or create) the :class:`SessionListCache` for ``root``."""

    with _session_list_caches_lock:
        cache = _session_list_caches.get(root)
        if cache is None:
            cache = SessionListCache()
            _session_list_caches[root] = cache
        return cache


def _clear_session_list_cache(root: Path) -> None:
    """Remove any cached summaries for ``root``.

    Used when the session root directory no longer exists so that stale
    entries do not accumulate across tests or configuration changes.
    """

    with _session_list_caches_lock:
        _session_list_caches.pop(root, None)


def _resolve_dotted_path(data: Dict[str, Any], path: str) -> Any:
    """Resolve a dotted-path (e.g. ``"metadata.title"``) on ``data``.

    Returns a sentinel object when the path cannot be resolved so callers
    can distinguish between ``None`` values and missing paths.
    """

    if not isinstance(path, str) or not path:
        return _MISSING

    parts = path.split(".")
    current: Any = data
    for part in parts:
        if not isinstance(current, dict):
            return _MISSING
        if part not in current:
            return _MISSING
        current = current[part]
    return current


def _get_session_list_trigger_actions(
    app_instance: AgentApplication,
) -> List[Tuple[str, int, Dict[str, Any]]]:
    """Return application actions that should run when listing sessions.

    Actions are identified by a ``trigger`` field containing the string
    ``"session_list"``. The :class:`AgentApplication` treats the
    ``trigger`` field as opaque; this helper interprets it for the HTTP
    layer.
    """

    all_actions = app_instance.get_application_actions()
    trigger_actions: List[Tuple[str, int, Dict[str, Any]]] = []

    # Preserve configuration order when multiple plugins contribute actions.
    plugin_index_map: Dict[str, int] = {}
    for idx, meta in enumerate(app_instance.list_application_plugins()):
        pid = meta.get("id")
        if isinstance(pid, str) and pid not in plugin_index_map:
            plugin_index_map[pid] = idx

    for action in all_actions:
        if not isinstance(action, Dict):
            continue
        plugin_id = action.get("plugin")
        if not isinstance(plugin_id, str) or not plugin_id:
            continue
        plugin_index = plugin_index_map.get(plugin_id, 0)
        trigger_val = action.get("trigger")
        if isinstance(trigger_val, str):
            if trigger_val == "session_list":
                trigger_actions.append((plugin_id, plugin_index, action))
        elif isinstance(trigger_val, list):
            if any(isinstance(t, str) and t == "session_list" for t in trigger_val):
                trigger_actions.append((plugin_id, plugin_index, action))

    return trigger_actions


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

    response = {"session": session.to_dict(), "errors": app_instance.get_config_errors()}
    _idempotency_store(scope, idempotency_key, data, response)
    return response


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

    all_plugins = app_instance.list_plugins()
    metadata = session.metadata or {}

    plugins_from_session = metadata.get("plugins")
    enabled_ids: Optional[set[str]]
    source: str

    if isinstance(plugins_from_session, list):
        enabled_ids = {p for p in plugins_from_session if isinstance(p, str)}
        source = "session"
    else:
        agent_val = metadata.get("agent_id")
        agent_id = agent_val.strip() if isinstance(agent_val, str) else ""
        if not agent_id:
            agents = [a for a in app_instance.list_agents() if isinstance(a, str) and a]
            agent_id = agents[0] if agents else ""

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
            {**entry, "enabled": enabled, "source": src, "active": _is_active(kind, pid)}
        )

    return result


def _run_send_request_background(
    app_instance: AgentApplication,
    session_id: str,
    overrides: Dict[str, Any],
    request_id: Optional[str] = None,
) -> None:
    """Run ``AgentApplication.send_request`` and publish all events.

    This helper mirrors the previous behaviour of :func:`send_request`
    but is designed to run in a background thread so that the HTTP
    route can return immediately.
    """

    rid = request_id or _generate_request_id(app_instance)

    try:
        ctx = app_instance.load_session(session_id)
        if ctx is None:
            _log.warning("send_request background worker: session %r not found", session_id)
            return

        core, base_config, session = ctx

        # Merge per-session configuration overrides stored on the
        # session metadata with any overrides provided in the HTTP
        # request. Request-level overrides take precedence. This
        # mirrors the terminal application's behaviour where
        # `session.metadata["overrides"]` is always applied and
        # explicit overrides can further refine it.
        merged_overrides = _merged_session_overrides(session, overrides)

        final_session_dict: Optional[Dict[str, Any]] = session.to_dict()
        final_messages: List[Dict[str, Any]] = []
        final_request_id: Optional[str] = None

        for ev in app_instance.send_request(
            core,
            session,
            base_config,
            merged_overrides,
            stream=True,
            request_id=rid,
        ):
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
                final_request_id = stored.get("request_id")
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

        # Publish a post-completion checkpoint so that frontends can
        # observe that there is no active request at/after this point
        # when loading a session snapshot by cursor.
        try:
            app_instance.record_checkpoint(session_id, None)
        except Exception:  # pragma: no cover - defensive
            _log.exception(
                "failed to publish post-completion checkpoint for %r", session_id,
            )


    except Exception:  # pragma: no cover - defensive
        _log.exception(
            "unexpected error in send_request background worker for session %r",
            session_id,
        )
    finally:
        _clear_active_send_request_id(session_id, rid)


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

    normalized_role, content, metadata, multipart_content = _validate_and_normalize_message_payload(
        payload
    )

    try:
        with app_instance.acquire_session_lock(session_id):
            ctx = app_instance.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            core, base_config, session = ctx
            effective_config = _effective_session_config(app_instance, base_config, session)
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
            raise HTTPException(status_code=400, detail="multipartContent must be a list")
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

    normalized_role = role if role in {"system", "user", "assistant", "tool"} else "user"
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
        ctx = app_instance.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")

        _core, _base_config, session = ctx
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        raw_overrides = metadata.get("overrides")
        overrides: Dict[str, Any] = (
            raw_overrides if isinstance(raw_overrides, dict) else {}
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {"overrides": overrides}


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
        raise HTTPException(status_code=400, detail="enabled must be a list of plugin ids")

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
        with app_instance.acquire_session_lock(session_id):
            ctx = app_instance.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            _core, _base_config, session = ctx
            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            raw_overrides = metadata.get("overrides")
            overrides: Dict[str, Any] = (
                raw_overrides if isinstance(raw_overrides, dict) else {}
            )

            new_overrides = {**overrides, **updates}
            new_metadata = {**metadata, "overrides": new_overrides}

            new_session = Session(
                session_id=session.session_id,
                messages=session.messages,
                metadata=new_metadata,
            )
            app_instance.save_session(new_session)

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    response = {"session": new_session.to_dict()}
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
        with app_instance.acquire_session_lock(session_id):
            ctx = app_instance.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            _core, _base_config, session = ctx
            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            raw_overrides = metadata.get("overrides")
            overrides: Dict[str, Any] = (
                raw_overrides if isinstance(raw_overrides, dict) else {}
            )

            if key not in overrides:
                result_session = session
            else:
                new_overrides = dict(overrides)
                new_overrides.pop(key, None)

                new_metadata = dict(metadata)
                if new_overrides:
                    new_metadata["overrides"] = new_overrides
                else:
                    new_metadata.pop("overrides", None)

                result_session = Session(
                    session_id=session.session_id,
                    messages=session.messages,
                    metadata=new_metadata,
                )
                app_instance.save_session(result_session)

            response = {"session": result_session.to_dict()}

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

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

            new_session = core.modify_message(session, target_index, content, config)
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
                app_instance.record_checkpoint(new_session.session_id, stored.get("request_id"))
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

    _ = _load_session_ctx_for_send(app_instance, session_id, overrides=overrides)

    request_id = _generate_request_id(app_instance)
    existing = _reserve_active_send_request_id(session_id, request_id)
    if existing is not None:
        return {"status": "already_running", "request_id": existing}

    # Start the send_request flow in a background thread so that the
    # HTTP response can return immediately.
    threading.Thread(
        target=_run_send_request_background,
        args=(app_instance, session_id, overrides, request_id),
        daemon=True,
    ).start()

    response = {"status": "started", "request_id": request_id}
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

    normalized_role, content, metadata, multipart_content = _validate_and_normalize_message_payload(
        message
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

    cached = _idempotency_maybe_replay(scope, effective_idempotency_key, idempotency_payload)
    if cached is not None:
        return cached

    try:
        with app_instance.acquire_session_lock(session_id):
            cached = _idempotency_maybe_replay(
                scope, effective_idempotency_key, idempotency_payload
            )
            if cached is not None:
                return cached

            core, base_config, session = _load_session_ctx_for_send(
                app_instance,
                session_id,
                overrides=overrides,
            )

            request_id = _generate_request_id(app_instance)
            existing = _reserve_active_send_request_id(session_id, request_id)
            if existing is not None:
                raise HTTPException(
                    status_code=409,
                    detail={"status": "already_running", "request_id": existing},
                )

            try:
                effective_config = _effective_session_config(
                    app_instance,
                    base_config,
                    session,
                    overrides,
                )
                _append_message_to_session_locked(
                    app_instance,
                    core,
                    effective_config,
                    session,
                    role=normalized_role,
                    content=content,
                    metadata=metadata,
                    multipart_content=multipart_content,
                )
            except Exception:
                _clear_active_send_request_id(session_id, request_id)
                raise

            response = {
                "status": "started",
                "request_id": request_id,
                "session_id": session_id,
            }
            _idempotency_store(scope, effective_idempotency_key, idempotency_payload, response)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    threading.Thread(
        target=_run_send_request_background,
        args=(app_instance, session_id, overrides, request_id),
        daemon=True,
    ).start()

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
                    "indices": concrete_indices,
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

    response = {"session": new_session.to_dict(), "deleted_indices": concrete_indices}
    _idempotency_store(scope, idempotency_key, body, response)
    return response


@app.get("/sessions")
def list_sessions(
    limit: Optional[int] = None,
    app_instance: AgentApplication = Depends(get_agent_app),
) -> Dict[str, Any]:
    """List stored sessions with basic metadata.

    Response shape mirrors :meth:`TerminalApplication.list_sessions_metadata`:
    each entry contains ``session_id``, ``modified`` (float timestamp),
    ``preview`` (first user message snippet), and ``metadata`` (session
    metadata without messages).
    """

    root = _get_session_root(app_instance)

    try:
        exists = root.exists()
    except Exception:  # pragma: no cover - defensive
        exists = False

    if not exists:
        _clear_session_list_cache(root)
        return {"sessions": []}

    cache = _get_session_list_cache(root)

    trigger_actions = _get_session_list_trigger_actions(app_instance)

    # Resolve the metadata key used for pinned state once per call.
    raw_cfg = getattr(app_instance, "_config", {})
    app_cfg = raw_cfg.get("application") if isinstance(raw_cfg, dict) else {}
    raw_pinned_key = app_cfg.get("session_pinned_metadata_key") if isinstance(app_cfg, dict) else None
    if isinstance(raw_pinned_key, str) and raw_pinned_key.strip():
        pinned_metadata_key = raw_pinned_key.strip()
    else:
        pinned_metadata_key = "pinned"

    items: List[Dict[str, Any]] = []
    paths = list(root.glob("*.json"))

    # Global ordering specifications contributed by session_list actions
    # across all sessions (combining cached and freshly computed entries).
    order_specs_raw: List[Dict[str, Any]] = []

    with cache.lock:
        seen_ids: set[str] = set()

        # When no trigger actions are configured, clear any previously
        # cached ordering specs so legacy ordering is used.
        if not trigger_actions:
            cache.order_specs_by_id.clear()

        for path in paths:
            try:
                stat = path.stat()
            except OSError:  # pragma: no cover - defensive
                continue

            session_id = path.stem
            seen_ids.add(session_id)
            mtime = float(stat.st_mtime)

            cached = cache.entries_by_id.get(session_id)
            if cached is not None and isinstance(cached.get("modified"), (int, float)):
                try:
                    cached_mtime = float(cached["modified"])
                except Exception:  # pragma: no cover - defensive
                    cached_mtime = -1.0
                if cached_mtime >= mtime:
                    items.append(cached)
                    # Reuse any cached ordering specs for this session.
                    cached_specs = cache.order_specs_by_id.get(session_id) or []
                    order_specs_raw.extend(cached_specs)
                    continue

            preview = ""
            metadata: Dict[str, Any] = {}

            try:
                data = path.read_text(encoding="utf-8")
                raw = json.loads(data)
                raw_metadata = raw.get("metadata")
                if isinstance(raw_metadata, dict):
                    # ``native_messages`` can contain a full copy of
                    # the conversation in provider-native form and is
                    # significantly larger than the rest of the
                    # metadata. It is not needed for the sessions list
                    # and would unnecessarily bloat the ``/sessions``
                    # response, so strip it here.
                    metadata = {
                        key: value
                        for key, value in raw_metadata.items()
                        if key != "native_messages"
                    }
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

            pinned_val = metadata.get(pinned_metadata_key, False)

            entry: Dict[str, Any] = {
                "session_id": session_id,
                "modified": mtime,
                "preview": preview,
                "metadata": metadata,
                "pinned": bool(pinned_val),
            }

            # Run any application-level actions that are configured to
            # trigger when listing sessions. These actions can return
            # lightweight calculated fields (``session_list_fields``)
            # that are merged into the summary.
            if trigger_actions:
                session_obj: Optional[Session] = None
                per_session_specs: List[Dict[str, Any]] = []
                for plugin_id, plugin_index, action_def in trigger_actions:
                    inputs_schema = action_def.get("inputs") or {}
                    params: Dict[str, Any] = {}
                    needs_session = False

                    for name, spec in inputs_schema.items():
                        if name == "session_id":
                            params[name] = session_id
                        elif name == "session_summary":
                            params[name] = entry
                        elif name == "session":
                            needs_session = True

                    if needs_session and session_obj is None:
                        try:
                            ctx = app_instance.load_session(session_id)
                        except Exception:  # pragma: no cover - defensive
                            ctx = None
                        if ctx is None:
                            continue
                        _core, _base, session_obj = ctx

                    if needs_session and session_obj is not None:
                        params["session"] = session_obj

                    try:
                        result = app_instance.execute_application_action(
                            plugin_id,
                            action_def.get("id", ""),
                            params,
                        )
                    except Exception:  # pragma: no cover - defensive
                        continue

                    fields = result.get("session_list_fields")
                    if isinstance(fields, dict):
                        for k, v in fields.items():
                            entry[k] = v

                    # Optional ordering specifications contributed by this
                    # action for this specific session.
                    raw_specs = result.get("session_list_order")
                    if raw_specs:
                        if isinstance(raw_specs, dict):
                            specs_iter = [raw_specs]
                        elif isinstance(raw_specs, list):
                            specs_iter = [s for s in raw_specs if isinstance(s, dict)]
                        else:
                            specs_iter = []
                        for spec_index, spec in enumerate(specs_iter):
                            record = {
                                "spec": dict(spec),
                                "plugin_id": plugin_id,
                                "plugin_index": plugin_index,
                                "spec_index": spec_index,
                            }
                            order_specs_raw.append(record)
                            per_session_specs.append(record)

                # Cache per-session ordering specs so that future /sessions
                # calls can reuse them even when the entry itself is served
                # entirely from cache.
                cache.order_specs_by_id[session_id] = per_session_specs
            else:
                # No trigger actions configured; ensure we do not retain
                # stale per-session ordering specs for this session.
                cache.order_specs_by_id.pop(session_id, None)

            cache.entries_by_id[session_id] = entry
            items.append(entry)

        # Drop cache entries (and their ordering specs) whose files have
        # been removed.
        for session_id in list(cache.entries_by_id.keys()):
            if session_id not in seen_ids:
                cache.entries_by_id.pop(session_id, None)
                cache.order_specs_by_id.pop(session_id, None)

        # Apply plugin-driven ordering when available; otherwise fall back
        # to legacy behaviour (modified desc + pinned-first grouping).
        if order_specs_raw:
            items = _apply_session_list_ordering(items, order_specs_raw)
        else:
            items = _legacy_sort_sessions(items)

    if limit is not None and limit >= 0:
        items = items[:limit]

    return {"sessions": items}


def _legacy_sort_sessions(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return sessions ordered by legacy semantics.

    Legacy ordering sorts by ``modified`` (descending) and then surfaces
    pinned sessions before unpinned ones while preserving per-group
    ordering. This remains the fallback when no valid plugin ordering
    specs are provided.
    """

    if not items:
        return items

    items.sort(key=lambda entry: entry.get("modified", 0.0), reverse=True)

    pinned_items = [e for e in items if bool(e.get("pinned"))]
    unpinned_items = [e for e in items if not bool(e.get("pinned"))]
    return pinned_items + unpinned_items


def _apply_session_list_ordering(
    items: List[Dict[str, Any]],
    order_specs_raw: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Apply plugin-driven ordering to ``items`` when specs are valid.

    When no valid specs remain after validation, this falls back to
    :func:`_legacy_sort_sessions`.
    """

    if not items:
        return items

    if not order_specs_raw:
        return _legacy_sort_sessions(items)

    # Normalise and sort specs by (priority, plugin_index, spec_index).
    normalised: List[Dict[str, Any]] = []
    for raw in order_specs_raw:
        spec = raw.get("spec")
        if not isinstance(spec, dict):
            continue
        key = spec.get("key")
        direction = spec.get("direction")
        if not isinstance(key, str) or not key:
            _log.warning("Ignoring session_list_order spec with invalid key: %r", spec)
            continue
        if direction not in ("asc", "desc"):
            _log.warning(
                "Normalising invalid session_list_order direction %r to 'asc' for key %r",
                direction,
                key,
            )
            direction = "asc"
        has_fallback = "fallback" in spec
        fallback_value = spec.get("fallback") if has_fallback else None
        raw_priority = spec.get("priority")
        if isinstance(raw_priority, int) and not isinstance(raw_priority, bool):
            priority = raw_priority
        else:
            try:
                priority = int(raw_priority)
            except Exception:  # pragma: no cover - defensive
                priority = 100
        plugin_id = raw.get("plugin_id") or ""
        plugin_index = raw.get("plugin_index") or 0
        spec_index = raw.get("spec_index") or 0

        normalised.append(
            {
                "key": key,
                "direction": direction,
                "has_fallback": has_fallback,
                "fallback": fallback_value,
                "priority": priority,
                "plugin_id": plugin_id,
                "plugin_index": int(plugin_index),
                "spec_index": int(spec_index),
            }
        )

    if not normalised:
        return _legacy_sort_sessions(items)

    normalised.sort(key=lambda s: (s["priority"], s["plugin_index"], s["spec_index"]))

    # Global direction is taken from the highest-priority spec.
    global_direction = normalised[0]["direction"]

    # Filter out specs that violate the fallback contract.
    valid_specs: List[Dict[str, Any]] = []
    for spec in normalised:
        key = spec["key"]
        has_fallback = spec["has_fallback"]
        any_missing_without_fallback = False

        for entry in items:
            value = _resolve_dotted_path(entry, key)
            if value is _MISSING and not has_fallback:
                any_missing_without_fallback = True
                break

        if any_missing_without_fallback:
            _log.error(
                "Ignoring session_list_order spec from plugin %r: key %r missing for some sessions and no fallback provided.",
                spec.get("plugin_id"),
                key,
            )
            continue

        valid_specs.append(spec)

    if not valid_specs:
        # No usable specs; fall back to legacy ordering.
        return _legacy_sort_sessions(items)

    def _composite_key(entry: Dict[str, Any]) -> Tuple[Any, ...]:
        values: List[Any] = []
        for spec in valid_specs:
            key = spec["key"]
            has_fallback = spec["has_fallback"]
            fallback_value = spec["fallback"]
            value = _resolve_dotted_path(entry, key)
            if value is _MISSING:
                if has_fallback:
                    value = fallback_value
            values.append(value)

        # Always include legacy fields as final tiebreakers.
        values.append(entry.get("modified", 0.0))
        values.append(entry.get("session_id", ""))
        return tuple(values)

    # Sort ascending by composite key, then reverse if direction is desc.
    items.sort(key=_composite_key)
    if global_direction == "desc":
        items.reverse()

    return items


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
            md = (
                new_session.metadata if isinstance(new_session.metadata, dict) else {}
            )
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
                app_instance.record_checkpoint(new_session.session_id, stored.get("request_id"))
            except Exception:  # pragma: no cover - defensive
                _log.exception(
                    "failed to publish checkpoint event after fork for %r",
                    new_session.session_id,
                )

    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    response = {"session": new_session.to_dict(), "source_session_id": session.session_id}
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

            # Derive the active_request_id for this snapshot from the
            # checkpoint event at cursor_event_id, if any. The
            # AgentApplication guarantees that the per-session cursor
            # corresponds to the event_id of a published "checkpoint"
            # event created via record_checkpoint(session_id,
            # request_id).
            active_request_id: Optional[str] = None
            if cursor_event_id is not None:
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

    The ``limit`` parameter (default 5000) is applied to the raw
    un-compacted event list retrieved from the store. After the
    compaction pass, the response payload is further capped to a
    smaller window so that clients do not receive excessively large
    batches even when many raw events collapse into a handful of
    logical entries.
    """

    _maybe_block_events_for_tests()

    store = app_instance.get_event_store()
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
        latest_event_id: Optional[str]
        try:
            latest_event_id = store.get_latest_event_id()
        except AttributeError:  # pragma: no cover - defensive
            latest_event_id = None
        return {"events": [], "latest_event_id": latest_event_id}

    effective_since_id = since_id
    # When filtering by session but no since_id is provided, default to
    # the persisted cursor for that session so that polling does not
    # replay the entire history.
    if effective_since_id is None and session_id is not None:
        try:
            effective_since_id = app_instance.get_session_cursor_event_id(session_id)
        except Exception:  # pragma: no cover - defensive
            effective_since_id = None

    events = store.list(
        since_id=effective_since_id,
        request_id=request_id,
        session_id=session_id,
        limit=internal_limit,
    )
    compacted = app_instance.compact_events(events)
    if len(compacted) > limit:
        compacted = compacted[:limit]
    return {"events": compacted}


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

    response = {"session": new_session.to_dict(), "agent_id": target_agent_id}
    _idempotency_store(scope, idempotency_key, payload, response)
    return response


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
        actions = [a for a in actions if isinstance(a, dict) and a.get("plugin") == plugin]
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
        elements = [e for e in elements if isinstance(e, dict) and e.get("plugin") == plugin]
    else:
        elements = [e for e in elements if isinstance(e, dict)]
    return {"elements": elements}


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

    body = payload or {}
    plugin_id = body.get("plugin")
    action_id = body.get("action_id")
    action_owner = body.get("action_owner")
    raw_inputs = body.get("inputs") or {}

    scope = f"POST /actions/{plugin_id}/{action_id}"
    cached = _idempotency_maybe_replay(scope, idempotency_key, body)
    if cached is not None:
        return cached

    try:
        result = app_instance.execute_action(
            plugin_id=plugin_id,
            action_id=action_id,
            params=raw_inputs,
            action_owner=action_owner if isinstance(action_owner, str) else None,
        )
        if not isinstance(result, dict):
            result = {}
        response: Dict[str, Any] = {
            "status": "ok",
            "plugin": plugin_id,
            "action_id": action_id,
            "action_owner": action_owner,
            "result": result,
        }
    except AgentApplication._ApplicationActionValidationError as exc:  # type: ignore[attr-defined]
        response = {
            "status": "error",
            "plugin": plugin_id,
            "action_id": action_id,
            "action_owner": action_owner,
            "error_type": "validation",
            "message": str(exc),
            "details": getattr(exc, "details", {}) or {},
        }
    except KeyError as exc:
        response = {
            "status": "error",
            "plugin": plugin_id,
            "action_id": action_id,
            "action_owner": action_owner,
            "error_type": "not_found",
            "message": str(exc),
            "details": {},
        }
    except ValueError as exc:
        # Includes invalid plugin/action identifiers or non-dict params.
        response = {
            "status": "error",
            "plugin": plugin_id,
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
            "plugin": plugin_id,
            "action_id": action_id,
            "action_owner": action_owner,
            "error_type": "internal",
            "message": str(exc),
            "details": {},
        }

    _idempotency_store(scope, idempotency_key, body, response)
    return response


# ---------------------------------------------------------------------------
# Helper for running under uvicorn or from the CLI
# ---------------------------------------------------------------------------


def run_api(
    host: str = "127.0.0.1",
    port: int = 8000,
    app_instance: Optional[AgentApplication] = None,
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

    global _agent_app
    if app_instance is not None:
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
