from __future__ import annotations

import json
import os
import secrets
import shlex
import signal
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Literal, Mapping

from .shell_engine import (
    ShellInfo,
    build_sync_subprocess_kwargs,
    detect_shell,
    terminate_process_tree,
)

BackgroundProcessStatus = Literal[
    "running",
    "succeeded",
    "failed",
    "cancelled",
    "lost",
]
BackgroundProcessOwnershipMode = Literal["owned", "tracked"]
BackgroundProcessShutdownPolicy = Literal["terminate", "leave_running"]

DEFAULT_BACKGROUND_START_DELAY_SECONDS = 0.2
DEFAULT_BACKGROUND_OWNERSHIP_MODE: BackgroundProcessOwnershipMode = "owned"
DEFAULT_BACKGROUND_SHUTDOWN_POLICY: BackgroundProcessShutdownPolicy = "terminate"

_BACKGROUND_ID_ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"
_SHELL_STATUS_WRITER = (
    "import json, os, sys;"
    "from datetime import datetime, timezone;"
    "path=sys.argv[1]; code=int(sys.argv[2]);"
    "payload={"
    "'exit_code': code,"
    "'finished_at': datetime.now(timezone.utc).replace(microsecond=0).isoformat(),"
    "'signal': None"
    "};"
    "tmp=path + '.tmp';"
    "open(tmp,'w',encoding='utf-8').write(json.dumps(payload, indent=2, sort_keys=True));"
    "os.replace(tmp, path)"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_ownership_mode(value: Any) -> BackgroundProcessOwnershipMode:
    return "tracked" if value == "tracked" else "owned"


def _normalize_shutdown_policy(value: Any) -> BackgroundProcessShutdownPolicy:
    return "leave_running" if value == "leave_running" else "terminate"


def _normalize_runtime_root(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


def _process_alive(pid: int, pgid: int | None = None) -> bool:
    if pid <= 0:
        return False
    if os.name != "nt" and isinstance(pgid, int) and pgid > 0:
        try:
            os.killpg(pgid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _terminate_process_id(
    pid: int,
    *,
    pgid: int | None = None,
    grace_seconds: float = 0.2,
) -> None:
    if pid <= 0:
        return
    if os.name != "nt" and isinstance(pgid, int) and pgid > 0:
        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            return
        deadline = time.monotonic() + grace_seconds
        while time.monotonic() < deadline:
            if not _process_alive(pid, pgid):
                return
            time.sleep(0.02)
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            return
        except PermissionError:
            if not _process_alive(pid, pgid):
                return
            try:
                os.kill(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                return
        deadline = time.monotonic() + grace_seconds
        while time.monotonic() < deadline:
            if not _process_alive(pid, pgid):
                return
            time.sleep(0.02)
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if not _process_alive(pid, None):
            return
        time.sleep(0.02)
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return


def _returncode_signal(returncode: int | None) -> int | None:
    if not isinstance(returncode, int):
        return None
    if returncode < 0:
        return -returncode
    return None


def _new_process_id() -> str:
    return "".join(secrets.choice(_BACKGROUND_ID_ALPHABET) for _ in range(9))


def _detect_background_shell() -> ShellInfo:
    shell = detect_shell()
    if shell.name in {"bash", "zsh"}:
        return ShellInfo(name=shell.name, path=shell.path, args=("-lc",))
    return shell


def _wrap_background_command(
    command: str,
    *,
    completion_path: Path,
    python_executable: str,
) -> str:
    quoted_command = shlex.quote(command)
    quoted_python = shlex.quote(python_executable)
    quoted_completion = shlex.quote(str(completion_path))
    quoted_writer = shlex.quote(_SHELL_STATUS_WRITER)
    return (
        f"eval {quoted_command}; "
        'STATUS=$?; '
        f"{quoted_python} -c {quoted_writer} {quoted_completion} \"$STATUS\"; "
        "exit $STATUS"
    )


@dataclass(frozen=True)
class BackgroundProcessCompletion:
    process_id: str
    exit_code: int | None
    finished_at: str | None
    signal: int | None
    path: Path

    def payload(self) -> Dict[str, Any]:
        return {
            "process_id": self.process_id,
            "exit_code": self.exit_code,
            "finished_at": self.finished_at,
            "signal": self.signal,
        }


@dataclass(frozen=True)
class BackgroundProcessRecord:
    process_id: str
    pid: int
    pgid: int | None
    command: str
    cwd: str
    shell: str
    status: BackgroundProcessStatus
    ownership_mode: BackgroundProcessOwnershipMode
    shutdown_policy: BackgroundProcessShutdownPolicy
    started_at: str
    finished_at: str | None
    exit_code: int | None
    signal: int | None
    termination_reason: str | None
    output_path: Path
    completion_path: Path
    last_observed_at: str
    agent_id: str | None
    session_id: str | None
    request_id: str | None
    app_instance_id: str | None
    manifest_path: Path

    def payload(self) -> Dict[str, Any]:
        return {
            "process_id": self.process_id,
            "pid": self.pid,
            "pgid": self.pgid,
            "command": self.command,
            "cwd": self.cwd,
            "shell": self.shell,
            "status": self.status,
            "ownership_mode": self.ownership_mode,
            "shutdown_policy": self.shutdown_policy,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "exit_code": self.exit_code,
            "signal": self.signal,
            "termination_reason": self.termination_reason,
            "output_path": str(self.output_path),
            "completion_path": str(self.completion_path),
            "last_observed_at": self.last_observed_at,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "app_instance_id": self.app_instance_id,
        }


class FilesystemBackgroundProcessStore:
    """Filesystem-backed persistent state for background commands."""

    def __init__(self, runtime_state_root: str | Path) -> None:
        self._root_dir = _normalize_runtime_root(runtime_state_root)
        self._process_root = self._root_dir / "processes"
        self._records_dir = self._process_root / "records"
        self._output_dir = self._process_root / "output"
        self._records_dir.mkdir(parents=True, exist_ok=True)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def root_dir(self) -> Path:
        return self._root_dir

    @property
    def process_root(self) -> Path:
        return self._process_root

    @property
    def records_dir(self) -> Path:
        return self._records_dir

    @property
    def output_dir(self) -> Path:
        return self._output_dir

    def _validate_process_id(self, process_id: str) -> str:
        if not isinstance(process_id, str) or not process_id:
            raise ValueError("process_id must be a non-empty string")
        if process_id in {".", ".."} or "/" in process_id or "\\" in process_id:
            raise ValueError("process_id must be path-safe")
        return process_id

    def manifest_path(self, process_id: str) -> Path:
        normalized = self._validate_process_id(process_id)
        return self._records_dir / f"{normalized}.json"

    def completion_path(self, process_id: str) -> Path:
        normalized = self._validate_process_id(process_id)
        return self._records_dir / f"{normalized}.exit.json"

    def output_path(self, process_id: str) -> Path:
        normalized = self._validate_process_id(process_id)
        return self._output_dir / f"{normalized}.log"

    def _write_json_atomic(self, path: Path, payload: Dict[str, Any]) -> None:
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        tmp_path.replace(path)

    def save_record(self, record: BackgroundProcessRecord) -> BackgroundProcessRecord:
        self._write_json_atomic(record.manifest_path, record.payload())
        return record

    def load_record(self, process_id: str) -> BackgroundProcessRecord:
        path = self.manifest_path(process_id)
        if not path.exists():
            raise FileNotFoundError(f"Background process {process_id!r} not found")
        payload = json.loads(path.read_text(encoding="utf-8"))
        return self._record_from_payload(path, payload)

    def list_records(self) -> list[BackgroundProcessRecord]:
        records: list[BackgroundProcessRecord] = []
        for path in sorted(self._records_dir.glob("*.json")):
            if path.name.endswith(".exit.json"):
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            try:
                records.append(self._record_from_payload(path, payload))
            except Exception:
                continue
        return records

    def save_completion(self, completion: BackgroundProcessCompletion) -> BackgroundProcessCompletion:
        self._write_json_atomic(completion.path, completion.payload())
        return completion

    def load_completion(self, process_id: str) -> BackgroundProcessCompletion | None:
        path = self.completion_path(process_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return None
        exit_code_raw = payload.get("exit_code")
        signal_raw = payload.get("signal")
        return BackgroundProcessCompletion(
            process_id=self._validate_process_id(
                str(payload.get("process_id") or process_id)
            ),
            exit_code=exit_code_raw if isinstance(exit_code_raw, int) else None,
            finished_at=(
                str(payload.get("finished_at"))
                if isinstance(payload.get("finished_at"), str)
                else None
            ),
            signal=signal_raw if isinstance(signal_raw, int) else None,
            path=path,
        )

    def allocate_process_id(self) -> str:
        while True:
            process_id = _new_process_id()
            if not self.manifest_path(process_id).exists():
                return process_id

    def _record_from_payload(
        self,
        manifest_path: Path,
        payload: Dict[str, Any],
    ) -> BackgroundProcessRecord:
        if not isinstance(payload, dict):
            raise ValueError("background process manifest must be a dict")
        process_id = self._validate_process_id(str(payload.get("process_id") or ""))
        pid = payload.get("pid")
        pgid = payload.get("pgid")
        if not isinstance(pid, int) or pid < 0:
            raise ValueError("background process manifest has invalid pid")
        if pgid is not None and (not isinstance(pgid, int) or pgid < 0):
            raise ValueError("background process manifest has invalid pgid")
        return BackgroundProcessRecord(
            process_id=process_id,
            pid=pid,
            pgid=pgid,
            command=str(payload.get("command") or ""),
            cwd=str(payload.get("cwd") or ""),
            shell=str(payload.get("shell") or ""),
            status=(
                payload.get("status")
                if payload.get("status")
                in {"running", "succeeded", "failed", "cancelled", "lost"}
                else "lost"
            ),
            ownership_mode=_normalize_ownership_mode(payload.get("ownership_mode")),
            shutdown_policy=_normalize_shutdown_policy(payload.get("shutdown_policy")),
            started_at=str(payload.get("started_at") or ""),
            finished_at=(
                str(payload.get("finished_at"))
                if isinstance(payload.get("finished_at"), str)
                else None
            ),
            exit_code=payload.get("exit_code")
            if isinstance(payload.get("exit_code"), int)
            else None,
            signal=payload.get("signal")
            if isinstance(payload.get("signal"), int)
            else None,
            termination_reason=(
                str(payload.get("termination_reason"))
                if isinstance(payload.get("termination_reason"), str)
                else None
            ),
            output_path=Path(str(payload.get("output_path") or self.output_path(process_id))),
            completion_path=Path(
                str(payload.get("completion_path") or self.completion_path(process_id))
            ),
            last_observed_at=str(payload.get("last_observed_at") or ""),
            agent_id=(
                str(payload.get("agent_id"))
                if isinstance(payload.get("agent_id"), str)
                else None
            ),
            session_id=(
                str(payload.get("session_id"))
                if isinstance(payload.get("session_id"), str)
                else None
            ),
            request_id=(
                str(payload.get("request_id"))
                if isinstance(payload.get("request_id"), str)
                else None
            ),
            app_instance_id=(
                str(payload.get("app_instance_id"))
                if isinstance(payload.get("app_instance_id"), str)
                else None
            ),
            manifest_path=manifest_path,
        )


class BackgroundProcessRegistry:
    """App-lifetime manager for live background commands with durable state."""

    def __init__(
        self,
        runtime_state_root: str | Path,
        *,
        start_delay_seconds: float = DEFAULT_BACKGROUND_START_DELAY_SECONDS,
        app_instance_id: str | None = None,
    ) -> None:
        self._store = FilesystemBackgroundProcessStore(runtime_state_root)
        self._start_delay_seconds = start_delay_seconds
        self._app_instance_id = app_instance_id or uuid.uuid4().hex
        self._lock = threading.RLock()
        self._live: dict[str, subprocess.Popen[Any]] = {}
        self._closed = False
        self.reconcile_on_startup()

    @property
    def store(self) -> FilesystemBackgroundProcessStore:
        return self._store

    def start_background_command(
        self,
        command: str,
        *,
        working_directory: str,
        shell: ShellInfo | None = None,
        ownership_mode: BackgroundProcessOwnershipMode = DEFAULT_BACKGROUND_OWNERSHIP_MODE,
        shutdown_policy: BackgroundProcessShutdownPolicy = DEFAULT_BACKGROUND_SHUTDOWN_POLICY,
        agent_id: str | None = None,
        session_id: str | None = None,
        request_id: str | None = None,
        env: Mapping[str, str] | None = None,
        python_executable: str | None = None,
    ) -> BackgroundProcessRecord:
        if self._closed:
            raise RuntimeError("BackgroundProcessRegistry is closed")
        if not isinstance(command, str) or not command.strip():
            raise ValueError("command must be a non-empty string")
        cwd = str(Path(working_directory).expanduser().resolve())
        process_id = self._store.allocate_process_id()
        completion_path = self._store.completion_path(process_id)
        output_path = self._store.output_path(process_id)
        shell_info = shell or _detect_background_shell()
        wrapped_command = _wrap_background_command(
            command.strip(),
            completion_path=completion_path,
            python_executable=python_executable or sys.executable,
        )
        args = [shell_info.path, *shell_info.args, wrapped_command]
        with output_path.open("w", encoding="utf-8") as output_handle:
            process = subprocess.Popen(
                args,
                cwd=cwd,
                env={**os.environ, **dict(env)} if env is not None else None,
                stdout=output_handle,
                stderr=subprocess.STDOUT,
                text=True,
                **build_sync_subprocess_kwargs(),
            )
        record = BackgroundProcessRecord(
            process_id=process_id,
            pid=int(process.pid or 0),
            pgid=int(process.pid) if os.name != "nt" and process.pid is not None else None,
            command=command.strip(),
            cwd=cwd,
            shell=shell_info.path,
            status="running",
            ownership_mode=_normalize_ownership_mode(ownership_mode),
            shutdown_policy=_normalize_shutdown_policy(shutdown_policy),
            started_at=_utc_now_iso(),
            finished_at=None,
            exit_code=None,
            signal=None,
            termination_reason=None,
            output_path=output_path,
            completion_path=completion_path,
            last_observed_at=_utc_now_iso(),
            agent_id=agent_id,
            session_id=session_id,
            request_id=request_id,
            app_instance_id=self._app_instance_id,
            manifest_path=self._store.manifest_path(process_id),
        )
        with self._lock:
            self._store.save_record(record)
            self._live[process_id] = process
        time.sleep(self._start_delay_seconds)
        return self.refresh_process(process_id)

    def get_process(self, process_id: str, *, refresh: bool = True) -> BackgroundProcessRecord:
        if refresh:
            return self.refresh_process(process_id)
        return self._store.load_record(process_id)

    def list_processes(self, *, refresh: bool = True) -> list[BackgroundProcessRecord]:
        records = self._store.list_records()
        if not refresh:
            return records
        refreshed: list[BackgroundProcessRecord] = []
        for record in records:
            refreshed.append(self.refresh_process(record.process_id))
        return refreshed

    def refresh_process(self, process_id: str) -> BackgroundProcessRecord:
        with self._lock:
            record = self._store.load_record(process_id)
            if record.status != "running":
                return record
            completion = self._store.load_completion(process_id)
            if completion is not None:
                return self._finalize_from_completion(record, completion)
            process = self._live.get(process_id)
            if process is not None:
                exit_code = process.poll()
                if exit_code is not None:
                    finished = BackgroundProcessCompletion(
                        process_id=record.process_id,
                        exit_code=exit_code,
                        finished_at=_utc_now_iso(),
                        signal=_returncode_signal(exit_code),
                        path=record.completion_path,
                    )
                    self._store.save_completion(finished)
                    return self._finalize_from_completion(record, finished)
            if _process_alive(record.pid, record.pgid):
                updated = self._replace_record(
                    record,
                    last_observed_at=_utc_now_iso(),
                )
                return self._store.save_record(updated)
            updated = self._replace_record(
                record,
                status="failed",
                finished_at=_utc_now_iso(),
                termination_reason="process exited without completion record",
                last_observed_at=_utc_now_iso(),
            )
            self._live.pop(process_id, None)
            return self._store.save_record(updated)

    def cancel_process(
        self,
        process_id: str,
        *,
        reason: str = "cancelled",
    ) -> BackgroundProcessRecord:
        with self._lock:
            record = self._store.load_record(process_id)
            if record.status != "running":
                return record
            process = self._live.pop(process_id, None)
            returncode: int | None = None
            if process is not None:
                terminate_process_tree(process)
                returncode = process.poll()
            else:
                _terminate_process_id(record.pid, pgid=record.pgid)
            updated = self._replace_record(
                record,
                status="cancelled",
                finished_at=_utc_now_iso(),
                exit_code=returncode,
                signal=_returncode_signal(returncode) or signal.SIGTERM,
                termination_reason=reason,
                last_observed_at=_utc_now_iso(),
            )
            return self._store.save_record(updated)

    def reconcile_on_startup(self) -> list[BackgroundProcessRecord]:
        reconciled: list[BackgroundProcessRecord] = []
        with self._lock:
            for record in self._store.list_records():
                if record.status != "running":
                    reconciled.append(record)
                    continue
                completion = self._store.load_completion(record.process_id)
                if completion is not None:
                    reconciled.append(self._finalize_from_completion(record, completion))
                    continue
                if _process_alive(record.pid, record.pgid):
                    refreshed = self._replace_record(
                        record,
                        last_observed_at=_utc_now_iso(),
                    )
                    reconciled.append(self._store.save_record(refreshed))
                    continue
                reconciled.append(
                    self._store.save_record(
                        self._replace_record(
                            record,
                            status="failed",
                            finished_at=_utc_now_iso(),
                            termination_reason="process not running during startup reconciliation",
                            last_observed_at=_utc_now_iso(),
                        )
                    )
                )
        return reconciled

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for record in self.list_processes(refresh=True):
            if record.status != "running":
                continue
            if record.ownership_mode != "owned":
                continue
            if record.shutdown_policy != "terminate":
                continue
            try:
                self.cancel_process(
                    record.process_id,
                    reason="application_shutdown",
                )
            except Exception:
                continue
        with self._lock:
            self._live.clear()

    def _replace_record(
        self,
        record: BackgroundProcessRecord,
        **changes: Any,
    ) -> BackgroundProcessRecord:
        payload = record.payload()
        payload.update(changes)
        return BackgroundProcessRecord(
            process_id=record.process_id,
            pid=int(payload["pid"]),
            pgid=payload.get("pgid")
            if isinstance(payload.get("pgid"), int)
            else None,
            command=str(payload["command"]),
            cwd=str(payload["cwd"]),
            shell=str(payload["shell"]),
            status=payload["status"],
            ownership_mode=_normalize_ownership_mode(payload.get("ownership_mode")),
            shutdown_policy=_normalize_shutdown_policy(payload.get("shutdown_policy")),
            started_at=str(payload["started_at"]),
            finished_at=(
                str(payload.get("finished_at"))
                if isinstance(payload.get("finished_at"), str)
                else None
            ),
            exit_code=payload.get("exit_code")
            if isinstance(payload.get("exit_code"), int)
            else None,
            signal=payload.get("signal")
            if isinstance(payload.get("signal"), int)
            else None,
            termination_reason=(
                str(payload.get("termination_reason"))
                if isinstance(payload.get("termination_reason"), str)
                else None
            ),
            output_path=Path(str(payload["output_path"])),
            completion_path=Path(str(payload["completion_path"])),
            last_observed_at=str(payload.get("last_observed_at") or record.last_observed_at),
            agent_id=(
                str(payload.get("agent_id"))
                if isinstance(payload.get("agent_id"), str)
                else None
            ),
            session_id=(
                str(payload.get("session_id"))
                if isinstance(payload.get("session_id"), str)
                else None
            ),
            request_id=(
                str(payload.get("request_id"))
                if isinstance(payload.get("request_id"), str)
                else None
            ),
            app_instance_id=(
                str(payload.get("app_instance_id"))
                if isinstance(payload.get("app_instance_id"), str)
                else None
            ),
            manifest_path=record.manifest_path,
        )

    def _finalize_from_completion(
        self,
        record: BackgroundProcessRecord,
        completion: BackgroundProcessCompletion,
    ) -> BackgroundProcessRecord:
        status: BackgroundProcessStatus = "failed"
        if completion.exit_code == 0:
            status = "succeeded"
        updated = self._replace_record(
            record,
            status=status,
            finished_at=completion.finished_at or _utc_now_iso(),
            exit_code=completion.exit_code,
            signal=completion.signal,
            termination_reason=None,
            last_observed_at=_utc_now_iso(),
        )
        self._live.pop(record.process_id, None)
        return self._store.save_record(updated)


def ensure_background_process_registry(
    *,
    runtime_state_root: str | Path,
    tool_runtime: Any | None = None,
    store_key: str = "tool_compat_shared.background_process_registry",
) -> BackgroundProcessRegistry:
    if tool_runtime is not None and hasattr(tool_runtime, "get_or_create"):
        registry = tool_runtime.get_or_create(
            store_key,
            lambda: BackgroundProcessRegistry(runtime_state_root),
        )
        if isinstance(registry, BackgroundProcessRegistry):
            return registry
    return BackgroundProcessRegistry(runtime_state_root)


__all__ = [
    "BackgroundProcessCompletion",
    "BackgroundProcessOwnershipMode",
    "BackgroundProcessRecord",
    "BackgroundProcessRegistry",
    "BackgroundProcessShutdownPolicy",
    "BackgroundProcessStatus",
    "DEFAULT_BACKGROUND_OWNERSHIP_MODE",
    "DEFAULT_BACKGROUND_SHUTDOWN_POLICY",
    "FilesystemBackgroundProcessStore",
    "ensure_background_process_registry",
]