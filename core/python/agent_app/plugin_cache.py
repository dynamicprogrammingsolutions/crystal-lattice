"""Process leases and startup cleanup for dynamically installed plugins."""

from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import threading
import time
from typing import BinaryIO, Iterator
import uuid
import weakref

from agent_core.utils import get_logger


HEARTBEAT_SECONDS = 30
LEASE_SECONDS = 120
TEMP_AGE_SECONDS = 24 * 60 * 60
_logger = get_logger("PluginCache")


def _lock(file: BinaryIO, *, blocking: bool = True) -> bool:
    if os.name == "nt":
        import msvcrt

        file.seek(0)
        file.write(b"\0")
        file.flush()
        file.seek(0)
        try:
            msvcrt.locking(file.fileno(), msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK, 1)
        except OSError:
            if not blocking:
                return False
            raise
    else:
        import fcntl

        try:
            fcntl.flock(file.fileno(), fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError:
            return False
    return True


def _unlock(file: BinaryIO) -> None:
    if os.name == "nt":
        import msvcrt

        file.seek(0)
        msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(file.fileno(), fcntl.LOCK_UN)


class PluginCache:
    """One application's claims; all cache mutations use the same disk lock."""

    def __init__(self, cache_dir: Path) -> None:
        self.root = cache_dir.resolve()
        self.control = self.root.parent / f".{self.root.name}.cache_control"
        leases = self.control / "leases"
        leases.mkdir(parents=True, exist_ok=True)
        self.token = uuid.uuid4().hex
        self.lease_path = leases / f"{self.token}.json"
        self.lock_path = leases / f"{self.token}.lock"
        self._lease_lock = self.lock_path.open("a+b")
        _lock(self._lease_lock)
        self._entries: set[str] = set()
        self._entry_lock = threading.Lock()
        self._write_lease()
        self._stopped = threading.Event()
        self._thread = threading.Thread(
            target=PluginCache._heartbeat,
            args=(weakref.ref(self), self._stopped),
            name="plugin-cache-heartbeat",
            daemon=True,
        )
        self._thread.start()
        self._finalizer = weakref.finalize(
            self,
            self._release,
            self._stopped,
            self._thread,
            self._lease_lock,
            self.lease_path,
            self.lock_path,
        )

    @contextmanager
    def locked(self) -> Iterator[None]:
        with (self.control / "cache.lock").open("a+b") as file:
            _lock(file)
            try:
                yield
            finally:
                _unlock(file)

    def claim(self, path: Path) -> None:
        relative = path.resolve().relative_to(self.root)
        with self._entry_lock:
            self._entries.add(str(relative))
            self._write_lease()

    def in_use_by_other(self, path: Path) -> bool:
        relative = str(path.resolve().relative_to(self.root))
        active = self._active_entries(exclude_self=True)
        return active is None or relative in active

    def cleanup(self, *, pip_cache: Path | None = None) -> None:
        """Call under the cache lock after claiming this application's plugins."""
        active = self._active_entries()
        if active is None:
            _logger.warning("plugin_cache_cleanup_skipped", reason="invalid_lease")
            return
        now = time.time()
        for parent in (self.root, self.root / "node", self.root / "bash", self.root / "src"):
            if not parent.is_dir() or parent.is_symlink():
                continue
            for entry in parent.iterdir():
                if not entry.is_dir() or entry.is_symlink():
                    continue
                if parent == self.root:
                    if entry.name in {".cache_control", ".locks", "node", "bash", "src", "pip"}:
                        continue
                    candidate = "@" in entry.name
                    temporary = entry.name.startswith(".") and entry.name.endswith(".tmp")
                elif parent.name == "src":
                    candidate = False
                    temporary = entry.name.startswith(
                        ("plugin_clone_", "node_tool_clone_", "bash_tool_clone_")
                    )
                else:
                    candidate = "@" in entry.name
                    temporary = False
                if not candidate and not temporary:
                    continue
                if str(entry.relative_to(self.root)) in active:
                    continue
                if temporary and now - entry.stat().st_mtime < TEMP_AGE_SECONDS:
                    continue
                try:
                    shutil.rmtree(entry)
                except OSError as exc:
                    _logger.warning("plugin_cache_cleanup_failed", path=str(entry), error=str(exc))
        install_locks = self.root / ".locks"
        if install_locks.is_dir() and not install_locks.is_symlink():
            for lock_file in install_locks.glob("*.lock"):
                install_name = lock_file.name[:-5]
                if (
                    not lock_file.is_symlink()
                    and "@" in install_name
                    and not (self.root / install_name).exists()
                    and install_name not in active
                ):
                    try:
                        lock_file.unlink()
                    except OSError as exc:
                        _logger.warning(
                            "plugin_cache_cleanup_failed",
                            path=str(lock_file),
                            error=str(exc),
                        )
        if pip_cache is not None and pip_cache.is_dir() and not pip_cache.is_symlink():
            try:
                shutil.rmtree(pip_cache)
            except OSError as exc:
                _logger.warning(
                    "plugin_pip_cache_cleanup_failed", path=str(pip_cache), error=str(exc)
                )

    def _active_entries(self, *, exclude_self: bool = False) -> set[str] | None:
        active: set[str] = set()
        for lease in (self.control / "leases").glob("*.json"):
            if exclude_self and lease == self.lease_path:
                continue
            lock_path = lease.with_suffix(".lock")
            try:
                with lock_path.open("a+b") as file:
                    held = _lock(file, blocking=False)
                    if held:
                        _unlock(file)
                data = json.loads(lease.read_text(encoding="utf-8"))
                if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
                    return None
                if held and data.get("expires_at", 0) <= time.time():
                    lease.unlink(missing_ok=True)
                    lock_path.unlink(missing_ok=True)
                else:
                    active.update(str(value) for value in data["entries"])
            except (OSError, ValueError, TypeError):
                return None
        return active

    def _write_lease(self) -> None:
        temp = self.lease_path.with_name(f".{self.token}.{uuid.uuid4().hex}.tmp")
        try:
            temp.write_text(
                json.dumps(
                    {
                        "expires_at": time.time() + LEASE_SECONDS,
                        "entries": sorted(self._entries),
                    }
                ),
                encoding="utf-8",
            )
            temp.replace(self.lease_path)
        finally:
            temp.unlink(missing_ok=True)

    @staticmethod
    def _heartbeat(owner: weakref.ReferenceType[PluginCache], stopped: threading.Event) -> None:
        while not stopped.wait(HEARTBEAT_SECONDS):
            cache = owner()
            if cache is None:
                return
            try:
                with cache._entry_lock:
                    cache._write_lease()
            except OSError as exc:
                _logger.warning("plugin_cache_heartbeat_failed", error=str(exc))
            finally:
                del cache

    @staticmethod
    def _release(
        stopped: threading.Event,
        thread: threading.Thread,
        file: BinaryIO,
        lease: Path,
        lock_path: Path,
    ) -> None:
        stopped.set()
        if thread is not threading.current_thread():
            thread.join(timeout=HEARTBEAT_SECONDS + 1)
        try:
            lease.unlink(missing_ok=True)
        finally:
            try:
                _unlock(file)
            finally:
                file.close()
                lock_path.unlink(missing_ok=True)

    def close(self) -> None:
        if self._finalizer.alive:
            self._finalizer()
