from __future__ import annotations

from pathlib import Path
from typing import Protocol, Optional

from agent_core import AgentCore, Session


class SessionStore(Protocol):
    """Abstract session persistence interface for the application layer."""

    def load(self, session_id: str) -> Optional[Session]:  # pragma: no cover - interface
        ...

    def save(self, session: Session) -> None:  # pragma: no cover - interface
        ...

    def delete(self, session_id: str) -> None:  # pragma: no cover - interface
        ...


class FilesystemSessionStore(SessionStore):
    """Filesystem-backed session store using JSON serialization.

    Each session is stored as a single JSON file named ``<session_id>.json``
    under the configured root directory. Serialization is delegated to
    :class:`agent_core.AgentCore` to keep the wire format consistent with
    the core SDK.
    """

    def __init__(self, root_dir: Path, core: AgentCore) -> None:
        self._root_dir = Path(root_dir)
        self._root_dir.mkdir(parents=True, exist_ok=True)
        self._core = core

    def _path_for(self, session_id: str) -> Path:
        # Simple mapping; callers are responsible for using opaque IDs.
        return self._root_dir / f"{session_id}.json"

    def load(self, session_id: str) -> Optional[Session]:
        path = self._path_for(session_id)
        if not path.exists():
            return None
        data = path.read_text(encoding="utf-8")
        return self._core.import_session(data)

    def save(self, session: Session) -> None:
        path = self._path_for(session.session_id)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        serialized = self._core.export_session(session)
        tmp_path.write_text(serialized, encoding="utf-8")
        tmp_path.replace(path)

    def delete(self, session_id: str) -> None:
        path = self._path_for(session_id)
        try:
            path.unlink()
        except FileNotFoundError:  # pragma: no cover - defensive
            return
