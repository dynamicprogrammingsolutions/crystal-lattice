from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Optional, Any, Dict, List
import time
import json

from agent_core import AgentCore, Session


class SessionStore(Protocol):
    """Abstract session persistence interface for the application layer."""

    def list_records(self) -> List["SessionStoreRecord"]:  # pragma: no cover - interface
        ...

    def get_record(
        self,
        session_id: str,
    ) -> Optional["SessionStoreRecord"]:  # pragma: no cover - interface
        ...

    def load(
        self,
        session_id: str,
        *,
        snapshot_id: Optional[str] = None,
    ) -> Optional[Session]:  # pragma: no cover - interface
        ...

    def save(self, session: Session) -> None:  # pragma: no cover - interface
        ...

    def delete(self, session_id: str) -> None:  # pragma: no cover - interface
        ...


@dataclass(frozen=True)
class SessionStoreRecord:
    """Implementation-neutral information about one live stored session.

    ``revision`` is opaque to application consumers. It is compared only for
    equality so a store can choose the change token appropriate to its backing
    implementation without exposing paths, etags, database versions, or other
    storage details.
    """

    session_id: str
    modified: float
    revision: object
    accessed: Optional[float] = None
    created: Optional[float] = None
    size: Optional[int] = None


@dataclass(frozen=True, eq=False)
class SessionFileState:
    exists: bool
    mtime_ns: Optional[int]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SessionFileState):
            return NotImplemented
        if not self.exists or not other.exists:
            return False
        if self.mtime_ns is None or other.mtime_ns is None:
            return False
        return self.mtime_ns == other.mtime_ns


@dataclass(frozen=True)
class SessionSnapshotRecord:
    snapshot_id: str
    session_id: str
    created_at: str
    reason: str
    metadata: Dict[str, Any]
    path: Path


class SnapshotSelectionStore(Protocol):
    def get_selected_snapshot(self, session_id: str) -> Optional[str]:  # pragma: no cover - interface
        ...

    def select_snapshot(self, session_id: str, snapshot_id: str) -> None:  # pragma: no cover - interface
        ...

    def clear_selected_snapshot(self, session_id: str) -> None:  # pragma: no cover - interface
        ...


class NullSnapshotSelectionStore:
    def get_selected_snapshot(self, session_id: str) -> Optional[str]:
        return None

    def select_snapshot(self, session_id: str, snapshot_id: str) -> None:
        return None

    def clear_selected_snapshot(self, session_id: str) -> None:
        return None


class FilesystemSnapshotSelectionStore:
    """Filesystem-backed per-session snapshot selection state."""

    def __init__(self, root_dir: Path) -> None:
        self._root_dir = Path(root_dir)
        self._root_dir.mkdir(parents=True, exist_ok=True)

    def _validate_component(self, value: str, *, field_name: str) -> str:
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field_name} must be a non-empty string")
        if value in {".", ".."} or "/" in value or "\\" in value:
            raise ValueError(f"{field_name} must be path-safe")
        return value

    def _selection_path_for(self, session_id: str) -> Path:
        normalized = self._validate_component(session_id, field_name="session_id")
        return self._root_dir / f"{normalized}.selected.json"

    def get_selected_snapshot(self, session_id: str) -> Optional[str]:
        path = self._selection_path_for(session_id)
        if not path.exists():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        selected = raw.get("selected_snapshot_id")
        return selected if isinstance(selected, str) and selected else None

    def select_snapshot(self, session_id: str, snapshot_id: str) -> None:
        path = self._selection_path_for(session_id)
        payload = {
            "selected_snapshot_id": self._validate_component(
                snapshot_id, field_name="snapshot_id"
            ),
            "selected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        tmp_path.replace(path)

    def clear_selected_snapshot(self, session_id: str) -> None:
        path = self._selection_path_for(session_id)
        try:
            path.unlink()
        except FileNotFoundError:
            return


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
        self._snapshot_root = self._root_dir / ".snapshots"
        self._snapshot_root.mkdir(parents=True, exist_ok=True)
        self._core = core

    def _path_for(self, session_id: str) -> Path:
        # Simple mapping; callers are responsible for using opaque IDs.
        return self._root_dir / f"{session_id}.json"

    def _snapshot_path_for(self, snapshot_id: str) -> Path:
        return self._snapshot_root / f"{snapshot_id}.json"

    def _snapshot_id_for(self, session_id: str, stamp_ns: int) -> str:
        return f"{session_id}.{stamp_ns}"

    def _is_selection_file(self, path: Path) -> bool:
        return path.name.endswith(".selected.json")

    def _snapshot_record_from_payload(self, path: Path, payload: Dict[str, Any]) -> SessionSnapshotRecord:
        session_id = str(payload.get("session_id") or "")
        snapshot_id = str(payload.get("snapshot_id") or path.stem)
        created_at = str(payload.get("snapshot_created_at") or "")
        reason = str(payload.get("snapshot_reason") or "")
        metadata = payload.get("snapshot_metadata")
        return SessionSnapshotRecord(
            snapshot_id=snapshot_id,
            session_id=session_id,
            created_at=created_at,
            reason=reason,
            metadata=dict(metadata) if isinstance(metadata, dict) else {},
            path=path,
        )

    @property
    def snapshot_root(self) -> Path:
        return self._snapshot_root

    @staticmethod
    def _store_record_for_path(path: Path, session_id: str) -> SessionStoreRecord:
        stat = path.stat()
        revision = (
            getattr(stat, "st_mtime_ns", None),
            getattr(stat, "st_ctime_ns", None),
            getattr(stat, "st_size", None),
            getattr(stat, "st_ino", None),
        )
        return SessionStoreRecord(
            session_id=session_id,
            modified=float(stat.st_mtime),
            revision=revision,
            accessed=float(stat.st_atime),
            created=float(getattr(stat, "st_birthtime", stat.st_ctime)),
            size=int(stat.st_size),
        )

    def list_records(self) -> List[SessionStoreRecord]:
        records: List[SessionStoreRecord] = []
        for path in self._root_dir.glob("*.json"):
            try:
                if not path.is_file():
                    continue
                records.append(self._store_record_for_path(path, path.stem))
            except OSError:
                continue
        records.sort(key=lambda record: record.session_id)
        return records

    def get_record(self, session_id: str) -> Optional[SessionStoreRecord]:
        path = self._path_for(session_id)
        try:
            if not path.is_file():
                return None
            return self._store_record_for_path(path, session_id)
        except OSError:
            return None

    def load(
        self,
        session_id: str,
        *,
        snapshot_id: Optional[str] = None,
    ) -> Optional[Session]:
        path = self._snapshot_path_for(snapshot_id) if isinstance(snapshot_id, str) and snapshot_id else self._path_for(session_id)
        if not path.exists():
            return None
        data = path.read_text(encoding="utf-8")
        session = self._core.import_session(data)
        if session.session_id != session_id:
            return None
        return session

    def get_file_state(
        self,
        session_id: str,
        *,
        snapshot_id: Optional[str] = None,
    ) -> SessionFileState:
        path = self._snapshot_path_for(snapshot_id) if isinstance(snapshot_id, str) and snapshot_id else self._path_for(session_id)
        try:
            stat = path.stat()
        except FileNotFoundError:
            return SessionFileState(exists=False, mtime_ns=None)
        return SessionFileState(
            exists=True,
            mtime_ns=getattr(stat, "st_mtime_ns", None),
        )

    def save(self, session: Session) -> None:
        path = self._path_for(session.session_id)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        serialized = self._core.export_session(session)
        tmp_path.write_text(serialized, encoding="utf-8")
        tmp_path.replace(path)

    def create_snapshot(
        self,
        session: Session,
        *,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionSnapshotRecord:
        stamp_ns = time.time_ns()
        snapshot_id = self._snapshot_id_for(session.session_id, stamp_ns)
        path = self._snapshot_path_for(snapshot_id)
        payload = session.to_dict()
        payload["snapshot_id"] = snapshot_id
        payload["readonly"] = True
        payload["snapshot_created_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        payload["snapshot_reason"] = reason
        payload["snapshot_metadata"] = dict(metadata) if isinstance(metadata, dict) else {}
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        tmp_path.replace(path)
        return self._snapshot_record_from_payload(path, payload)

    def list_snapshots(self, session_id: str) -> List[SessionSnapshotRecord]:
        pattern = f"{session_id}.*.json"
        results: List[SessionSnapshotRecord] = []
        for path in self._snapshot_root.glob(pattern):
            if self._is_selection_file(path):
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if str(payload.get("session_id") or "") != session_id:
                continue
            results.append(self._snapshot_record_from_payload(path, payload))
        results.sort(key=lambda item: item.snapshot_id, reverse=True)
        return results

    def delete_snapshot(self, session_id: str, snapshot_id: str) -> bool:
        path = self._snapshot_path_for(snapshot_id)
        if not path.exists():
            return False
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        if str(payload.get("session_id") or "") not in {"", session_id}:
            return False
        path.unlink()
        return True

    def save_backup(
        self,
        session: Session,
        *,
        request_id: str,
        suffix: str = "tool-loop-conflict",
    ) -> Path:
        path = self._path_for(session.session_id)
        stamp = time.time_ns()
        backup_name = (
            f"{session.session_id}.{suffix}.{request_id}.{stamp}.json"
        )
        backup_path = path.with_name(backup_name)
        serialized = self._core.export_session(session)
        backup_path.write_text(serialized, encoding="utf-8")
        return backup_path

    def delete(self, session_id: str) -> None:
        path = self._path_for(session_id)
        try:
            path.unlink()
        except FileNotFoundError:  # pragma: no cover - defensive
            return
