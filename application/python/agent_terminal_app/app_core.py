from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config_echo_app.json"
_DEFAULT_SESSION_ROOT = Path(__file__).resolve().parent / "sessions"

_agent_app: Optional[AgentApplication] = None
_event_store: Optional[InMemoryEventStore] = None


def init_shared_app(
    config_path: Optional[str | Path] = None,
    session_root: Optional[str | Path] = None,
    *,
    reset: bool = False,
) -> Tuple[AgentApplication, InMemoryEventStore]:
    """Initialise or reinitialise the shared AgentApplication and event store.

    This helper is used by the FastAPI server, the terminal client, and
    tests so that they can share the same application-layer instance and
    in-memory event store when running in a single process.
    """

    global _agent_app, _event_store

    if _agent_app is not None and _event_store is not None and not reset:
        return _agent_app, _event_store

    cfg = Path(config_path) if config_path is not None else _DEFAULT_CONFIG_PATH
    root = Path(session_root) if session_root is not None else _DEFAULT_SESSION_ROOT
    root.mkdir(parents=True, exist_ok=True)

    _agent_app = AgentApplication(str(cfg), str(root))
    _event_store = InMemoryEventStore()
    return _agent_app, _event_store


def get_shared_agent_app() -> AgentApplication:
    """Return the shared AgentApplication, initialising it on first use."""

    app, _ = init_shared_app()
    return app


def get_shared_event_store() -> InMemoryEventStore:
    """Return the shared in-memory event store, initialising if needed."""

    _, store = init_shared_app()
    return store
