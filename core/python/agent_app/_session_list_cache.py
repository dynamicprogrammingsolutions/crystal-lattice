"""Private persistent storage for derived session-list summaries."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple


_CACHE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class _PersistedSessionSummary:
    """JSON-compatible complete summary data stored by one implementation."""

    session_id: str
    revision_token: str
    contract_token: str
    summary: Dict[str, Any]
    order_specs: Tuple[Dict[str, Any], ...]
    diagnostics: Tuple[Dict[str, Any], ...]


class _SQLiteSessionSummaryCache:
    """Small process-safe cache using a fresh SQLite connection per operation."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._lock = threading.RLock()
        self._available = True
        self._last_error: Optional[str] = None
        self._initialize()

    @property
    def available(self) -> bool:
        with self._lock:
            return self._available

    def take_error(self) -> Optional[str]:
        with self._lock:
            error = self._last_error
            self._last_error = None
            return error

    def _record_error(self, exc: Exception) -> None:
        with self._lock:
            self._available = False
            self._last_error = str(exc)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self._path), timeout=0.1)
        connection.execute("PRAGMA busy_timeout = 100")
        return connection

    def _initialize(self) -> None:
        try:
            self._initialize_database()
        except sqlite3.DatabaseError as exc:
            try:
                self._replace_corrupt_database()
                self._initialize_database()
                with self._lock:
                    self._last_error = (
                        "Persistent session-list cache was corrupt and was rebuilt: " f"{exc}"
                    )
            except (OSError, sqlite3.Error) as recovery_exc:
                self._record_error(recovery_exc)
        except (OSError, sqlite3.Error) as exc:
            self._record_error(exc)

    def _initialize_database(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._path.parent.chmod(0o700)
        except OSError:
            pass
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if version not in {0, _CACHE_SCHEMA_VERSION}:
                connection.execute("DROP TABLE IF EXISTS session_summaries")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS session_summaries (
                    session_id TEXT PRIMARY KEY,
                    revision_token TEXT NOT NULL,
                    contract_token TEXT NOT NULL,
                    summary_json TEXT NOT NULL,
                    order_specs_json TEXT NOT NULL,
                    diagnostics_json TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )
            connection.execute(f"PRAGMA user_version = {_CACHE_SCHEMA_VERSION}")
        try:
            self._path.chmod(0o600)
        except OSError:
            pass

    def _replace_corrupt_database(self) -> None:
        stamp = f"{time.time_ns()}-{os.getpid()}"
        for path in (
            self._path,
            Path(f"{self._path}-wal"),
            Path(f"{self._path}-shm"),
        ):
            try:
                path.replace(path.with_name(f"{path.name}.corrupt-{stamp}"))
            except FileNotFoundError:
                continue
        backups = sorted(
            self._path.parent.glob(f"{self._path.name}*.corrupt-*"),
            key=lambda path: path.stat().st_mtime_ns,
            reverse=True,
        )
        for obsolete in backups[9:]:
            try:
                obsolete.unlink()
            except FileNotFoundError:
                continue

    def load_valid(
        self,
        *,
        revision_tokens: Mapping[str, str],
        contract_token: str,
    ) -> Dict[str, _PersistedSessionSummary]:
        if not revision_tokens or not self.available:
            return {}
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT
                        session_id,
                        revision_token,
                        contract_token,
                        summary_json,
                        order_specs_json,
                        diagnostics_json
                    FROM session_summaries
                    WHERE contract_token = ?
                    """,
                    (contract_token,),
                ).fetchall()
        except (OSError, sqlite3.Error) as exc:
            self._record_error(exc)
            return {}

        results: Dict[str, _PersistedSessionSummary] = {}
        for row in rows:
            session_id, revision_token, stored_contract = row[:3]
            if revision_tokens.get(session_id) != revision_token:
                continue
            try:
                summary = json.loads(row[3])
                order_specs = json.loads(row[4])
                diagnostics = json.loads(row[5])
            except (TypeError, ValueError):
                continue
            if (
                not isinstance(summary, dict)
                or not isinstance(order_specs, list)
                or not isinstance(diagnostics, list)
            ):
                continue
            if not all(isinstance(item, dict) for item in order_specs):
                continue
            if not all(isinstance(item, dict) for item in diagnostics):
                continue
            results[session_id] = _PersistedSessionSummary(
                session_id=session_id,
                revision_token=revision_token,
                contract_token=stored_contract,
                summary=summary,
                order_specs=tuple(order_specs),
                diagnostics=tuple(diagnostics),
            )
        return results

    def put(self, record: _PersistedSessionSummary) -> None:
        if not self.available:
            return
        try:
            payload = (
                record.session_id,
                record.revision_token,
                record.contract_token,
                json.dumps(
                    record.summary,
                    allow_nan=False,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                json.dumps(
                    record.order_specs,
                    allow_nan=False,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                json.dumps(
                    record.diagnostics,
                    allow_nan=False,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                    default=repr,
                ),
                time.time(),
            )
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO session_summaries (
                        session_id,
                        revision_token,
                        contract_token,
                        summary_json,
                        order_specs_json,
                        diagnostics_json,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        revision_token = excluded.revision_token,
                        contract_token = excluded.contract_token,
                        summary_json = excluded.summary_json,
                        order_specs_json = excluded.order_specs_json,
                        diagnostics_json = excluded.diagnostics_json,
                        updated_at = excluded.updated_at
                    """,
                    payload,
                )
        except (OSError, TypeError, ValueError, sqlite3.Error) as exc:
            self._record_error(exc)

    def invalidate(self, session_id: Optional[str] = None) -> None:
        if not self.available:
            return
        try:
            with self._connect() as connection:
                if session_id is None:
                    connection.execute("DELETE FROM session_summaries")
                else:
                    connection.execute(
                        "DELETE FROM session_summaries WHERE session_id = ?",
                        (session_id,),
                    )
        except (OSError, sqlite3.Error) as exc:
            self._record_error(exc)

    def remove_missing(self, existing_session_ids: Sequence[str]) -> None:
        if not self.available:
            return
        existing = frozenset(existing_session_ids)
        try:
            with self._connect() as connection:
                stored_ids = {
                    str(row[0])
                    for row in connection.execute(
                        "SELECT session_id FROM session_summaries"
                    ).fetchall()
                }
                missing = stored_ids.difference(existing)
                connection.executemany(
                    "DELETE FROM session_summaries WHERE session_id = ?",
                    ((session_id,) for session_id in missing),
                )
        except (OSError, sqlite3.Error) as exc:
            self._record_error(exc)

    def close(self) -> None:
        """Connections are operation-scoped, so closure only disables new work."""

        with self._lock:
            self._available = False


class _NullSessionSummaryCache:
    """No-op cache used when persistence is disabled or unavailable."""

    available = False

    def take_error(self) -> Optional[str]:
        return None

    def load_valid(
        self,
        *,
        revision_tokens: Mapping[str, str],
        contract_token: str,
    ) -> Dict[str, _PersistedSessionSummary]:
        return {}

    def put(self, record: _PersistedSessionSummary) -> None:
        return None

    def invalidate(self, session_id: Optional[str] = None) -> None:
        return None

    def remove_missing(self, existing_session_ids: Sequence[str]) -> None:
        return None

    def close(self) -> None:
        return None


def _default_cache_path(
    *,
    session_store_identity: str,
    override: Optional[str] = None,
) -> Path:
    """Resolve the current local implementation's private cache database."""

    if isinstance(override, str) and override.strip():
        root = Path(override).expanduser()
    else:
        root = Path.home() / ".crystal" / "cache" / "session-list"
        store_path = Path(session_store_identity).expanduser()
        if store_path.is_absolute():
            resolved_store = store_path.resolve()
            temporary_root = Path(tempfile.gettempdir()).resolve()
            if resolved_store.is_relative_to(temporary_root):
                root = resolved_store.parent / ".session-list-cache"
    namespace = _stable_token(session_store_identity)
    return root / f"{namespace}.sqlite3"


def _stable_revision_token(revision: object) -> str:
    return _stable_token(revision)


def _stable_token(value: object) -> str:
    import hashlib

    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=repr,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
