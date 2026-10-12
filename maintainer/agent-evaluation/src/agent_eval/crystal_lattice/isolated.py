"""Fork-based worker isolation for Crystal Lattice runs.

The application runtime resolves per-run values (``REPO_ROOT``,
``WORKING_DIR``, …) through a process-global environment overlay, so
two simultaneously-live applications with different roots cannot share
one process. Evaluation cases each own a workspace, and a mixed-agent
matrix therefore needs one runtime process per run.

This module runs the whole kernel lifecycle —
open → program → snapshot → finalize — inside a forked worker. The
worker inherits the program closure and configuration by fork (suite
programs are closures and not picklable), builds a fresh application
and fresh services (never touching inherited locks or the inherited
evidence journal), and reports the outcome plus its drained evidence
over a pipe. The parent merges the evidence, so journals, artifacts,
and the cache keep working unchanged on the parent side.
"""

from __future__ import annotations

import gc
import logging
import os
import pickle
import signal
import struct
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from agent_eval.environment import IsolatedExecutionOutcome
from agent_eval.result import RunError, capture_error_record
from agent_eval.services import (
    ArtifactWriter,
    Evidence,
    EvidenceJournal,
    RunServices,
)

from .environment import CrystalLatticeEnvironment

_FRAME = struct.Struct("!Q")
_MAX_PICKLE_ATTEMPTS = 2


class IsolatedWorkerDied(RuntimeError):
    """The forked worker exited without reporting an outcome."""


@dataclass
class _ChildReport:
    """Everything the worker ships back to the parent."""

    value: object = None
    snapshot_data: bytes | None = None
    observation: object = field(default_factory=dict)
    error: tuple[str, str, str, str] | None = None
    evidence_items: tuple[Evidence, ...] = ()


def run_isolated(
    environment: CrystalLatticeEnvironment,
    *,
    services: RunServices,
    workspace: Path | None,
    parent_snapshot: object | None,
    program: Callable[[object], object],
    writer: ArtifactWriter,
) -> IsolatedExecutionOutcome:
    """Execute one run in a forked worker and merge its report."""

    if not hasattr(os, "fork"):
        raise RuntimeError(
            "isolated Crystal Lattice execution requires os.fork " "(POSIX platforms)"
        )

    # Finalize unreachable parent resources (operation-scoped SQLite
    # connections from earlier applications, ...) so the fork does not
    # inherit their file descriptors; SQLite connections must never
    # cross a fork boundary.
    gc.collect()
    # Concurrent sibling threads may be inside Objective-C +initialize
    # when we fork (the runtime stack touches Foundation on macOS); the
    # standard guard disabled here keeps forked workers from aborting
    # on that check. Children inherit the value before any ObjC use.
    os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")

    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        _run_worker(
            environment,
            services=services,
            workspace=workspace,
            parent_snapshot=parent_snapshot,
            program=program,
            write_fd=write_fd,
            read_fd=read_fd,
        )  # never returns

    os.close(write_fd)
    try:
        payload = _read_frame(read_fd)
    finally:
        os.close(read_fd)
    _, status = os.waitpid(pid, 0)

    if payload is None:
        raise IsolatedWorkerDied(
            "isolated worker exited without reporting; waitpid status " f"{status}"
        )

    kind, body = pickle.loads(payload)
    if kind == "worker-failure":
        raise IsolatedWorkerDied(
            "isolated worker failed before reporting an outcome: " f"{body}"
        )
    report: _ChildReport = body
    services.evidence.extend(report.evidence_items)

    error: RunError | None = None
    if report.error is not None:
        phase, type_name, message, traceback_text = report.error
        error = capture_error_record(
            writer,
            phase=phase,
            type=type_name,
            message=message,
            traceback=traceback_text,
        )
    snapshot: object | None = None
    if report.snapshot_data is not None:
        snapshot = environment.deserialize_snapshot(report.snapshot_data)
    return IsolatedExecutionOutcome(
        value=report.value,
        snapshot=snapshot,
        observation=report.observation,
        error=error,
    )


def _run_worker(
    environment: CrystalLatticeEnvironment,
    *,
    services: RunServices,
    workspace: Path | None,
    parent_snapshot: object | None,
    program: Callable[[object], object],
    write_fd: int,
    read_fd: int,
) -> None:
    """Child-side main; write one report frame and exit without teardown."""

    payload: bytes
    try:
        os.close(read_fd)
        _close_inherited_descriptors(keep=write_fd)
        _prepare_worker_process()
        report = _execute_in_worker(
            environment,
            services=services,
            workspace=workspace,
            parent_snapshot=parent_snapshot,
            program=program,
        )
        payload = _pickle_report(report)
    except BaseException:
        try:
            payload = pickle.dumps(
                ("worker-failure", traceback.format_exc()),
                protocol=pickle.HIGHEST_PROTOCOL,
            )
        except BaseException:
            payload = pickle.dumps(
                ("worker-failure", "unpicklable worker failure"),
            )
    try:
        _write_frame(write_fd, payload)
    finally:
        os.close(write_fd)
        os._exit(0)


def _execute_in_worker(
    environment: CrystalLatticeEnvironment,
    *,
    services: RunServices,
    workspace: Path | None,
    parent_snapshot: object | None,
    program: Callable[[object], object],
) -> _ChildReport:
    """Mirror the kernel's inline composition inside the worker."""

    worker_journal = EvidenceJournal()
    worker_services = RunServices(
        run_id=services.run_id,
        name=services.name,
        artifact_dir=services.artifact_dir,
        workspace=workspace,
        parent=services.parent,
        evidence=worker_journal,
        artifacts=ArtifactWriter(services.artifact_dir),
    )
    value: object = None
    snapshot: object | None = None
    observation: object = {}
    error: tuple[str, str, str, str] | None = None

    def capture(phase: str, exc: BaseException) -> None:
        nonlocal error
        if error is None:
            error = (
                phase,
                type(exc).__name__,
                str(exc),
                "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            )

    try:
        with environment.open(
            services=worker_services,
            workspace=workspace,
            parent_snapshot=parent_snapshot,
        ) as context:
            try:
                value = program(context)
            except BaseException as exc:
                capture("program", exc)
            try:
                snapshot = environment.snapshot(context)
            except BaseException as exc:
                capture("environment.snapshot", exc)
            try:
                observation = environment.finalize(context)
            except BaseException as exc:
                capture("environment.finalize", exc)
    except BaseException as exc:
        capture("environment.open_or_close", exc)

    snapshot_data: bytes | None = None
    if snapshot is not None:
        try:
            snapshot_data = environment.serialize_snapshot(snapshot)
        except BaseException as exc:
            capture("environment.snapshot", exc)

    return _ChildReport(
        value=value,
        snapshot_data=snapshot_data,
        observation=observation,
        error=error,
        evidence_items=tuple(worker_journal.items()),
    )


def _close_inherited_descriptors(*, keep: int) -> None:
    """Close every inherited descriptor except the report pipe.

    The parent may hold SQLite database/WAL descriptors from earlier
    applications; those must never cross a fork boundary (using a
    database through an inherited descriptor can crash the process).
    The worker opens everything it needs fresh, by path, so only its
    own pipe end survives.
    """

    try:
        import resource

        limit = int(resource.getrlimit(resource.RLIMIT_NOFILE)[0])
    except BaseException:
        limit = 4096
    os.closerange(3, keep - 1)
    os.closerange(keep + 1, max(limit - 1, keep + 1))


def _prepare_worker_process() -> None:
    """Make the forked child safe and independent of parent state."""

    # The worker is single-threaded; inherited locks may never be
    # released (their holders did not survive the fork), so replace or
    # avoid them before any inherited machinery is touched.
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    logging.disable(logging.CRITICAL)
    try:
        from agent_app.runtime_env import RuntimeEnvOverlay

        # Live overlays inherited from the parent would collide with this
        # worker's own roots; the parent's environ bookkeeping is
        # irrelevant here, so drop it without taking the inherited lock
        # (the registry itself keeps the child's installs consistent).
        RuntimeEnvOverlay._managed.clear()  # noqa: SLF001 - fork hygiene
    except BaseException:
        pass


def _pickle_report(report: _ChildReport) -> bytes:
    """Pickle the report, degrading unpicklable evidence if needed."""

    last_error: BaseException | None = None
    for attempt in range(_MAX_PICKLE_ATTEMPTS):
        try:
            return pickle.dumps(("report", report), protocol=pickle.HIGHEST_PROTOCOL)
        except BaseException as exc:  # noqa: BLE001 - degrade, then fail loudly
            last_error = exc
            if attempt + 1 < _MAX_PICKLE_ATTEMPTS:
                report.evidence_items = tuple(
                    _jsonable_item(item) for item in report.evidence_items
                )
    raise (
        last_error
        if last_error is not None
        else RuntimeError("the isolated worker report could not be pickled")
    )


def _jsonable_item(item: object) -> object:
    from agent_eval.services import jsonable

    try:
        return jsonable(item)
    except BaseException:
        return repr(item)


def _write_frame(fd: int, payload: bytes) -> None:
    _write_all(fd, _FRAME.pack(len(payload)))
    _write_all(fd, payload)


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        view = view[written:]


def _read_frame(fd: int) -> bytes | None:
    header = _read_exact(fd, _FRAME.size)
    if header is None:
        return None
    (length,) = _FRAME.unpack(header)
    body = _read_exact(fd, length)
    if body is None:
        return None
    return body


def _read_exact(fd: int, count: int) -> bytes | None:
    chunks: list[bytes] = []
    remaining = count
    while remaining > 0:
        chunk = os.read(fd, remaining)
        if not chunk:
            return None
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)
