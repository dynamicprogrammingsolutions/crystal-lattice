"""Interactive process engine for unified exec sessions.

Spawns shell commands as long-lived interactive sessions that can be polled
and (for PTY sessions) written to across tool calls and requests. Sessions
are pipe-backed by default and PTY-backed when requested, mirroring the
Codex CLI "unified exec" process model:

- Sessions are identified by small monotonically increasing integer ids.
- Output is accumulated by reader threads and drained per call; draining
  never blocks the caller.
- A finished session stays registered (with its exit code and any pending
  output) until it is observed by a draining call or reaped by the idle TTL,
  so a final ``write_stdin`` poll can still collect the process tail.
- The manager enforces a concurrent-session cap and terminates live
  sessions on idle expiry and interpreter exit.

The engine returns only structured data; vendor tool wrappers own schema and
model-facing formatting. POSIX only: ``tty`` sessions require the stdlib
``pty`` module (Windows support is tracked separately).
"""

from __future__ import annotations

import atexit
import os
import signal
import struct
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .shell_engine import ShellInfo, terminate_process_tree

try:  # pragma: no cover - platform guard
    import pty as _pty_module
except ImportError:  # pragma: no cover - Windows
    _pty_module = None

try:  # pragma: no cover - platform guard
    import fcntl as _fcntl_module
    import termios as _termios_module
except ImportError:  # pragma: no cover - Windows
    _fcntl_module = None
    _termios_module = None


DEFAULT_MAX_SESSIONS = 8
"""Default cap on concurrently registered unified exec sessions."""

DEFAULT_SESSION_TTL_SECONDS = 900.0
"""Default idle lifetime before a session is reaped."""

_READ_CHUNK_BYTES = 65536
_READER_JOIN_TIMEOUT_SECONDS = 2.0
_DEFAULT_PTY_ROWS = 24
_DEFAULT_PTY_COLS = 80


class InteractiveProcessError(Exception):
    """Raised when an interactive process operation fails."""


class StdinClosedError(InteractiveProcessError):
    """Raised when writing to a session that has no interactive stdin."""


class SessionLimitError(InteractiveProcessError):
    """Raised when the concurrent-session cap is reached."""


@dataclass(frozen=True)
class InteractiveSpawnSpec:
    """Description of a session to spawn.

    Attributes:
        command: Shell command text to execute.
        workdir: Working directory for the command.
        tty: Whether to allocate a PTY (interactive stdin) for the session.
        shell: Resolved shell (path, args) used to wrap the command.
        env: Environment for the child process (defaults to os.environ).
    """

    command: str
    workdir: Optional[str] = None
    tty: bool = False
    shell: Optional[ShellInfo] = None
    env: Optional[Dict[str, str]] = None


@dataclass
class SessionStats:
    """Observability metadata for a session."""

    session_id: int
    command: str
    workdir: Optional[str]
    tty: bool
    started_at: float
    last_activity_at: float = field(default_factory=time.monotonic)

    def payload(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "command": self.command,
            "workdir": self.workdir,
            "tty": self.tty,
        }


def _set_pty_winsize(master_fd: int) -> None:
    """Best-effort default terminal size for a newly opened PTY."""

    if _fcntl_module is None or _termios_module is None:
        return
    try:
        winsize = struct.pack(
            "HHHH", _DEFAULT_PTY_ROWS, _DEFAULT_PTY_COLS, 0, 0
        )
        _fcntl_module.ioctl(master_fd, _termios_module.TIOCSWINSZ, winsize)
    except Exception:
        pass


class InteractiveProcessSession:
    """One spawned process with drainable output and optional PTY stdin."""

    def __init__(
        self,
        session_id: int,
        spec: InteractiveSpawnSpec,
        process: subprocess.Popen[Any],
        *,
        master_fd: Optional[int] = None,
    ) -> None:
        self.session_id = session_id
        self.spec = spec
        self.process = process
        self.master_fd = master_fd
        self.started_at = time.monotonic()
        self.last_activity_at = self.started_at
        self._lock = threading.Lock()
        self._pending: List[bytes] = []
        self._readers: List[threading.Thread] = []
        self._write_error: Optional[str] = None
        self._closed = False

    # -- introspection -----------------------------------------------------

    @property
    def command(self) -> str:
        return self.spec.command

    @property
    def workdir(self) -> Optional[str]:
        return self.spec.workdir

    @property
    def tty(self) -> bool:
        return self.spec.tty

    @property
    def alive(self) -> bool:
        return self.process.poll() is None

    @property
    def exit_code(self) -> Optional[int]:
        return self.process.returncode

    @property
    def write_error(self) -> Optional[str]:
        with self._lock:
            return self._write_error

    def stats(self) -> SessionStats:
        return SessionStats(
            session_id=self.session_id,
            command=self.spec.command,
            workdir=self.spec.workdir,
            tty=self.spec.tty,
            started_at=self.started_at,
            last_activity_at=self.last_activity_at,
        )

    # -- output ------------------------------------------------------------

    def start_readers(self) -> None:
        """Start the reader threads that accumulate session output."""

        if self.master_fd is not None:
            thread = threading.Thread(
                target=self._read_fd_loop,
                args=(self.master_fd,),
                daemon=True,
                name=f"unified-exec-pty-{self.session_id}",
            )
            self._readers.append(thread)
        else:
            for stream, label in (
                (self.process.stdout, "stdout"),
                (self.process.stderr, "stderr"),
            ):
                if stream is None:
                    continue
                thread = threading.Thread(
                    target=self._read_fd_loop,
                    args=(stream.fileno(),),
                    daemon=True,
                    name=f"unified-exec-{label}-{self.session_id}",
                )
                self._readers.append(thread)
        for thread in self._readers:
            thread.start()

    def _read_fd_loop(self, fd: int) -> None:
        while True:
            try:
                chunk = os.read(fd, _READ_CHUNK_BYTES)
            except (OSError, ValueError):
                # EOF, closed descriptor, or EIO when a PTY slave closes.
                return
            if not chunk:
                return
            with self._lock:
                self._pending.append(chunk)

    def drain(self) -> str:
        """Return and clear output accumulated since the previous drain."""

        with self._lock:
            chunks = self._pending
            self._pending = []
            self.last_activity_at = time.monotonic()
        if not chunks:
            return ""
        return b"".join(chunks).decode("utf-8", errors="replace")

    def collect_final_output(self) -> str:
        """Drain output after process exit, waiting briefly for readers."""

        if self.process.poll() is not None:
            for thread in self._readers:
                if thread.is_alive():
                    thread.join(timeout=_READER_JOIN_TIMEOUT_SECONDS)
        return self.drain()

    # -- input -------------------------------------------------------------

    def write(self, chars: str) -> None:
        """Write characters to the session stdin (PTY sessions only)."""

        if self.master_fd is None:
            raise StdinClosedError(
                "stdin is closed for this session; rerun exec_command with "
                "tty=true to keep stdin open"
            )
        data = chars.encode("utf-8")
        try:
            os.write(self.master_fd, data)
        except OSError as exc:
            self._write_error = str(exc)
            raise InteractiveProcessError(f"failed to write to stdin: {exc}") from exc
        with self._lock:
            self.last_activity_at = time.monotonic()

    def interrupt(self) -> None:
        """Interrupt the session (^C semantics)."""

        if self.master_fd is not None:
            # The PTY line discipline turns ^C into SIGINT for the foreground
            # process group.
            try:
                os.write(self.master_fd, b"\x03")
                return
            except OSError:
                pass
        pgid = os.getpgid(self.process.pid) if self.process.pid else None
        if pgid is not None:
            try:
                os.killpg(pgid, signal.SIGINT)
                return
            except (ProcessLookupError, PermissionError, OSError):
                pass
        if self.process.pid:
            try:
                self.process.send_signal(signal.SIGINT)
            except (ProcessLookupError, OSError):
                pass

    # -- teardown ----------------------------------------------------------

    def terminate(self) -> None:
        """Terminate the process tree and close session descriptors."""

        if not self._closed:
            self._closed = True
            try:
                terminate_process_tree(self.process)
            except Exception:
                pass
        self._close_master()

    def _close_master(self) -> None:
        if self.master_fd is None:
            return
        try:
            os.close(self.master_fd)
        except OSError:
            pass
        self.master_fd = None


class InteractiveProcessManager:
    """Registry of interactive sessions with id allocation and reaping."""

    def __init__(
        self,
        *,
        max_sessions: int = DEFAULT_MAX_SESSIONS,
        session_ttl_seconds: float = DEFAULT_SESSION_TTL_SECONDS,
        register_atexit: bool = True,
    ) -> None:
        self.max_sessions = max(1, int(max_sessions))
        self.session_ttl_seconds = max(0.0, float(session_ttl_seconds))
        self._sessions: Dict[int, InteractiveProcessSession] = {}
        self._next_session_id = 1
        self._lock = threading.Lock()
        self._atexit_registered = False
        if register_atexit:
            self._register_atexit()

    def _register_atexit(self) -> None:
        if self._atexit_registered:
            return
        self._atexit_registered = True
        atexit.register(self.terminate_all)

    # -- spawn -------------------------------------------------------------

    def spawn(self, spec: InteractiveSpawnSpec) -> InteractiveProcessSession:
        """Spawn a new session, enforcing the session cap."""

        self.reap_idle()
        with self._lock:
            if len(self._sessions) >= self.max_sessions:
                raise SessionLimitError(
                    f"unified exec session limit reached "
                    f"({self.max_sessions}); poll or finish existing "
                    f"sessions before starting new ones"
                )
            session_id = self._next_session_id
            self._next_session_id += 1

        if spec.tty and (_pty_module is None or sys.platform == "win32"):
            raise InteractiveProcessError(
                "tty sessions are not supported on this platform"
            )
        pty_module = _pty_module

        if spec.shell is None:
            raise InteractiveProcessError("shell must be resolved by the caller")

        from .shell_engine import build_shell_args

        args = build_shell_args(spec.command, spec.shell)
        env = spec.env if spec.env is not None else os.environ

        master_fd: Optional[int] = None
        try:
            if spec.tty and pty_module is not None:
                master_fd, slave_fd = pty_module.openpty()
                _set_pty_winsize(master_fd)
                process = subprocess.Popen(
                    args,
                    cwd=spec.workdir,
                    env=env,
                    stdin=slave_fd,
                    stdout=slave_fd,
                    stderr=slave_fd,
                    start_new_session=True,
                    close_fds=True,
                )
                os.close(slave_fd)
            else:
                process = subprocess.Popen(
                    args,
                    cwd=spec.workdir,
                    env=env,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True,
                )
        except Exception as exc:
            if master_fd is not None:
                try:
                    os.close(master_fd)
                except OSError:
                    pass
            raise InteractiveProcessError(str(exc)) from exc

        session = InteractiveProcessSession(
            session_id, spec, process, master_fd=master_fd
        )
        with self._lock:
            self._sessions[session_id] = session
        session.start_readers()
        return session

    # -- lookup ------------------------------------------------------------

    def get(self, session_id: int) -> Optional[InteractiveProcessSession]:
        with self._lock:
            return self._sessions.get(session_id)

    def remove(self, session_id: int) -> Optional[InteractiveProcessSession]:
        with self._lock:
            return self._sessions.pop(session_id, None)

    def session_count(self) -> int:
        with self._lock:
            return len(self._sessions)

    def list_sessions(self) -> List[SessionStats]:
        with self._lock:
            return [
                session.stats()
                for session in sorted(
                    self._sessions.values(), key=lambda s: s.session_id
                )
            ]

    # -- reaping -----------------------------------------------------------

    def reap_idle(self, *, now: Optional[float] = None) -> List[int]:
        """Terminate/drop sessions idle beyond the TTL; return their ids."""

        current = time.monotonic() if now is None else now
        reaped: List[int] = []
        with self._lock:
            candidates = [
                session
                for session in self._sessions.values()
                if current - session.last_activity_at >= self.session_ttl_seconds
            ]
        for session in candidates:
            session.terminate()
            with self._lock:
                self._sessions.pop(session.session_id, None)
            reaped.append(session.session_id)
        return reaped

    def terminate_all(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            session.terminate()


_default_manager: Optional[InteractiveProcessManager] = None
_default_manager_lock = threading.Lock()


def get_default_manager() -> InteractiveProcessManager:
    """Return the process-wide fallback manager (used without a store)."""

    global _default_manager
    with _default_manager_lock:
        if _default_manager is None:
            _default_manager = InteractiveProcessManager()
        return _default_manager


__all__ = [
    "DEFAULT_MAX_SESSIONS",
    "DEFAULT_SESSION_TTL_SECONDS",
    "InteractiveProcessError",
    "InteractiveProcessManager",
    "InteractiveProcessSession",
    "InteractiveSpawnSpec",
    "SessionLimitError",
    "SessionStats",
    "StdinClosedError",
    "get_default_manager",
]
