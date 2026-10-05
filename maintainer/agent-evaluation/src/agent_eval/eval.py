"""Generic evaluation lifecycle."""

from __future__ import annotations

import shutil
import traceback
import uuid
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Generic, TypeVar, cast

from .artifacts import write_run_artifacts
from .cache import CacheStore, pickle_bytes, stable_hash
from .environment import RunEnvironment
from .result import Run, RunError
from .services import (
    ArtifactWriter,
    EvidenceJournal,
    EvidenceVisibility,
    RunServices,
)
from .workspace import (
    PreparedWorkspace,
    WorkspaceFactory,
    WorkspaceObservation,
    apply_cached_workspace,
    copy_untracked_files,
    observe_workspace,
    prepare_workspace,
)


ContextT = TypeVar("ContextT")
ResultT = TypeVar("ResultT")


class AgentEval(Generic[ContextT]):
    """Run arbitrary programs inside replaceable execution environments."""

    def __init__(
        self,
        *,
        default_environment: RunEnvironment[ContextT],
        artifact_root: Path,
        cache_root: Path | None = None,
    ) -> None:
        self.default_environment = default_environment
        self.artifact_root = artifact_root.expanduser().resolve()
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self.cache = CacheStore(cache_root) if cache_root is not None else None
        self._cleanups: list[Callable[[], None]] = []
        self._closed = False

    def __enter__(self) -> "AgentEval[ContextT]":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for cleanup in reversed(self._cleanups):
            try:
                cleanup()
            except Exception:
                pass
        self._cleanups.clear()

    def run(
        self,
        name: str,
        program: Callable[[ContextT], ResultT],
        *,
        environment: RunEnvironment[ContextT] | None = None,
        continue_from: Run[object] | None = None,
        workspace: Path | WorkspaceFactory | None = None,
        cache_key: str | None = None,
        cache_read: bool = True,
        cache_publish: Callable[[Run[ResultT]], bool] | None = None,
    ) -> Run[ResultT]:
        if self._closed:
            raise RuntimeError("AgentEval is closed")

        selected_environment = environment or self.default_environment
        run_id = _run_id(name)
        run_dir = self.artifact_root / "runs" / run_id
        writer = ArtifactWriter(run_dir)
        evidence = EvidenceJournal()

        workspace_source = workspace
        if workspace_source is None and continue_from is not None:
            if continue_from.workspace is None:
                workspace_source = None
            elif continue_from._workspace_reusable:
                workspace_source = cast(
                    Path | WorkspaceFactory | None,
                    continue_from._workspace_source,
                )
            else:
                return self._preparation_failure(
                    run_id=run_id,
                    name=name,
                    writer=writer,
                    evidence=evidence,
                    environment=selected_environment,
                    continue_from=continue_from,
                    phase="workspace.restore",
                    exc=ValueError(
                        "parent workspace is not reusable; provide workspace= "
                        "for the continuation"
                    ),
                )

        try:
            prepared_workspace = prepare_workspace(
                workspace_source,
                run_dir=run_dir,
            )
        except BaseException as exc:
            return self._preparation_failure(
                run_id=run_id,
                name=name,
                writer=writer,
                evidence=evidence,
                environment=selected_environment,
                continue_from=continue_from,
                phase="workspace.prepare",
                exc=exc,
            )

        if prepared_workspace.cleanup is not None:
            self._cleanups.append(prepared_workspace.cleanup)

        try:
            environment_fingerprint = selected_environment.fingerprint()
            continuation_fingerprint = _continuation_fingerprint(selected_environment)
        except BaseException as exc:
            return self._failure_with_workspace(
                run_id=run_id,
                name=name,
                writer=writer,
                evidence=evidence,
                environment_fingerprint={"unavailable": True},
                prepared_workspace=prepared_workspace,
                continue_from=continue_from,
                phase="environment.fingerprint",
                exc=exc,
            )

        parent_snapshot = None
        parent_snapshot_sha256 = None
        if continue_from is not None:
            if continue_from.snapshot is None:
                return self._failure_with_workspace(
                    run_id=run_id,
                    name=name,
                    writer=writer,
                    evidence=evidence,
                    environment_fingerprint=environment_fingerprint,
                    prepared_workspace=prepared_workspace,
                    continue_from=continue_from,
                    phase="environment.restore",
                    exc=ValueError("parent run has no reusable snapshot"),
                )
            parent_continuation_fingerprint = (
                continue_from.continuation_fingerprint
                if continue_from.continuation_fingerprint is not None
                else continue_from.environment_fingerprint
            )
            if stable_hash(parent_continuation_fingerprint) != stable_hash(
                continuation_fingerprint
            ):
                return self._failure_with_workspace(
                    run_id=run_id,
                    name=name,
                    writer=writer,
                    evidence=evidence,
                    environment_fingerprint=environment_fingerprint,
                    prepared_workspace=prepared_workspace,
                    continue_from=continue_from,
                    phase="environment.restore",
                    exc=ValueError("parent and selected environment are incompatible"),
                )
            parent_snapshot = continue_from.snapshot
            try:
                parent_snapshot_sha256 = _snapshot_hash(
                    selected_environment,
                    parent_snapshot,
                )
            except BaseException as exc:
                return self._failure_with_workspace(
                    run_id=run_id,
                    name=name,
                    writer=writer,
                    evidence=evidence,
                    environment_fingerprint=environment_fingerprint,
                    prepared_workspace=prepared_workspace,
                    continue_from=continue_from,
                    phase="environment.restore",
                    exc=exc,
                )

        cache_hash = None
        if cache_key is not None:
            if self.cache is None:
                return self._failure_with_workspace(
                    run_id=run_id,
                    name=name,
                    writer=writer,
                    evidence=evidence,
                    environment_fingerprint=environment_fingerprint,
                    prepared_workspace=prepared_workspace,
                    continue_from=continue_from,
                    phase="cache.prepare",
                    exc=ValueError("cache_key requires AgentEval(cache_root=...)"),
                )
            cache_hash = self.cache.key(
                caller_key=cache_key,
                environment_fingerprint=environment_fingerprint,
                workspace_fingerprint=prepared_workspace.fingerprint,
                parent_snapshot_sha256=parent_snapshot_sha256,
            )

        lock = (
            self.cache.lock(cache_hash) if self.cache and cache_hash else nullcontext()
        )
        with lock:
            if self.cache is not None and cache_hash is not None and cache_read:
                try:
                    cached = self.cache.load(cache_hash)
                except BaseException as exc:
                    return self._failure_with_workspace(
                        run_id=run_id,
                        name=name,
                        writer=writer,
                        evidence=evidence,
                        environment_fingerprint=environment_fingerprint,
                        prepared_workspace=prepared_workspace,
                        continue_from=continue_from,
                        phase="cache.load",
                        exc=exc,
                    )
                if cached is not None:
                    try:
                        apply_cached_workspace(
                            prepared_workspace,
                            patch=cached.workspace_patch,
                            untracked_root=cached.untracked_root,
                        )
                    except BaseException as exc:
                        return self._failure_with_workspace(
                            run_id=run_id,
                            name=name,
                            writer=writer,
                            evidence=evidence,
                            environment_fingerprint=environment_fingerprint,
                            prepared_workspace=prepared_workspace,
                            continue_from=continue_from,
                            phase="cache.restore_workspace",
                            exc=exc,
                        )
                    evidence.extend(cached.evidence)
                    _copy_directory_contents(
                        cached.raw_environment_root,
                        writer.path("raw/environment"),
                    )
                    _copy_directory_contents(
                        cached.records_root,
                        writer.path("records"),
                    )
                    evidence.emit(
                        "cache.hit",
                        {
                            "key": cache_hash,
                            "source_run_id": cached.manifest.get("source_run_id"),
                        },
                        source="kernel",
                    )
                    snapshot_sha256 = (
                        str(cached.manifest.get("snapshot_sha256"))
                        if cached.manifest.get("snapshot_sha256")
                        else None
                    )
                    try:
                        cached_snapshot = _deserialize_snapshot(
                            selected_environment,
                            cached.snapshot_data,
                        )
                    except BaseException as exc:
                        return self._failure_with_workspace(
                            run_id=run_id,
                            name=name,
                            writer=writer,
                            evidence=evidence,
                            environment_fingerprint=environment_fingerprint,
                            prepared_workspace=prepared_workspace,
                            continue_from=continue_from,
                            phase="cache.restore_snapshot",
                            exc=exc,
                        )
                    observation = observe_workspace(prepared_workspace)
                    run = Run(
                        run_id=run_id,
                        name=name,
                        value=cast(ResultT, cached.value),
                        snapshot=cached_snapshot,
                        environment=cached.environment,
                        environment_fingerprint=environment_fingerprint,
                        continuation_fingerprint=continuation_fingerprint,
                        workspace=prepared_workspace.path,
                        workspace_fingerprint=prepared_workspace.fingerprint,
                        changed_paths=observation.changed_paths,
                        artifact_dir=run_dir,
                        error=None,
                        cache_hit=True,
                        parent_run_id=(
                            continue_from.run_id if continue_from is not None else None
                        ),
                        snapshot_sha256=snapshot_sha256,
                        _workspace_source=prepared_workspace.source,
                        _workspace_reusable=prepared_workspace.reusable,
                    )
                    self._write_completed_run(
                        run=run,
                        writer=writer,
                        evidence=evidence,
                        observation=observation,
                    )
                    return run

            run = self._execute(
                run_id=run_id,
                name=name,
                program=program,
                environment=selected_environment,
                environment_fingerprint=environment_fingerprint,
                continuation_fingerprint=continuation_fingerprint,
                prepared_workspace=prepared_workspace,
                continue_from=continue_from,
                parent_snapshot=parent_snapshot,
                writer=writer,
                evidence=evidence,
            )
            if (
                self.cache is not None
                and cache_hash is not None
                and run.error is None
                and (cache_publish is None or cache_publish(run))
            ):
                observation = observe_workspace(prepared_workspace)
                untracked_root = run_dir / "raw" / "workspace" / "untracked"
                copy_untracked_files(
                    prepared_workspace,
                    observation,
                    untracked_root,
                )
                manifest = {
                    "schema": 1,
                    "cache_key": cache_hash,
                    "source_run_id": run.run_id,
                    "snapshot_sha256": run.snapshot_sha256,
                    "changed_paths": run.changed_paths,
                }
                try:
                    self.cache.publish(
                        cache_hash,
                        manifest=manifest,
                        value=run.value,
                        snapshot_data=(
                            _serialize_snapshot(
                                selected_environment,
                                run.snapshot,
                            )
                            if run.snapshot is not None
                            else None
                        ),
                        environment=run.environment,
                        evidence=evidence.items(),
                        workspace_patch=observation.git_diff,
                        untracked_root=(
                            untracked_root if untracked_root.is_dir() else None
                        ),
                        raw_environment_root=(run_dir / "raw" / "environment"),
                        records_root=run_dir / "records",
                    )
                except BaseException as exc:
                    return self._replace_with_error(
                        run,
                        writer=writer,
                        evidence=evidence,
                        prepared_workspace=prepared_workspace,
                        phase="cache.publish",
                        exc=exc,
                    )
            return run

    def _execute(
        self,
        *,
        run_id: str,
        name: str,
        program: Callable[[ContextT], ResultT],
        environment: RunEnvironment[ContextT],
        environment_fingerprint: object,
        continuation_fingerprint: object,
        prepared_workspace: PreparedWorkspace,
        continue_from: Run[object] | None,
        parent_snapshot: object | None,
        writer: ArtifactWriter,
        evidence: EvidenceJournal,
    ) -> Run[ResultT]:
        services = RunServices(
            run_id=run_id,
            name=name,
            artifact_dir=writer.root,
            workspace=prepared_workspace.path,
            parent=continue_from,
            evidence=evidence,
            artifacts=writer,
        )
        evidence.emit(
            "run.started",
            {"run_id": run_id, "name": name},
            source="kernel",
        )

        context: ContextT | None = None
        value: object = None
        snapshot: object | None = None
        environment_observation: object = {}
        error: RunError | None = None
        try:
            with environment.open(
                services=services,
                workspace=prepared_workspace.path,
                parent_snapshot=parent_snapshot,
            ) as opened_context:
                context = opened_context
                try:
                    value = program(context)
                except BaseException as exc:
                    error = _capture_error(writer, "program", exc)

                try:
                    snapshot = environment.snapshot(context)
                except BaseException as exc:
                    if error is None:
                        error = _capture_error(
                            writer,
                            "environment.snapshot",
                            exc,
                        )

                try:
                    environment_observation = environment.finalize(context)
                except BaseException as exc:
                    if error is None:
                        error = _capture_error(
                            writer,
                            "environment.finalize",
                            exc,
                        )
        except BaseException as exc:
            if error is None:
                error = _capture_error(writer, "environment.open_or_close", exc)

        snapshot_sha256 = None
        if snapshot is not None:
            try:
                snapshot_data = _serialize_snapshot(environment, snapshot)
                snapshot_sha256 = _snapshot_hash(environment, snapshot)
                writer.write_bytes("raw/environment/snapshot.bin", snapshot_data)
            except BaseException as exc:
                if error is None:
                    error = _capture_error(
                        writer,
                        "environment.snapshot_serialize",
                        exc,
                    )

        _write_optional_pickle(
            writer,
            evidence,
            name="value",
            value=value,
        )
        _write_optional_pickle(
            writer,
            evidence,
            name="observation",
            value=environment_observation,
        )

        observation = observe_workspace(prepared_workspace)
        evidence.emit(
            "run.completed" if error is None else "run.failed",
            {
                "changed_paths": observation.changed_paths,
                "error": error,
            },
            source="kernel",
        )
        run = Run(
            run_id=run_id,
            name=name,
            value=cast(ResultT, value),
            snapshot=snapshot,
            environment=environment_observation,
            environment_fingerprint=environment_fingerprint,
            continuation_fingerprint=continuation_fingerprint,
            workspace=prepared_workspace.path,
            workspace_fingerprint=prepared_workspace.fingerprint,
            changed_paths=observation.changed_paths,
            artifact_dir=writer.root,
            error=error,
            cache_hit=False,
            parent_run_id=continue_from.run_id if continue_from is not None else None,
            snapshot_sha256=snapshot_sha256,
            _workspace_source=prepared_workspace.source,
            _workspace_reusable=prepared_workspace.reusable,
        )
        self._write_completed_run(
            run=run,
            writer=writer,
            evidence=evidence,
            observation=observation,
        )
        return run

    def _write_completed_run(
        self,
        *,
        run: Run[ResultT],
        writer: ArtifactWriter,
        evidence: EvidenceJournal,
        observation: WorkspaceObservation,
    ) -> None:
        write_run_artifacts(
            writer,
            run_id=run.run_id,
            name=run.name,
            status="failed" if run.error else "completed",
            cache_hit=run.cache_hit,
            parent_run_id=run.parent_run_id,
            environment_fingerprint=run.environment_fingerprint,
            workspace=run.workspace,
            workspace_fingerprint=run.workspace_fingerprint,
            snapshot_sha256=run.snapshot_sha256,
            value=run.value,
            environment=run.environment,
            error=run.error,
            evidence=evidence.items(),
            workspace_observation=observation,
        )

    def _preparation_failure(
        self,
        *,
        run_id: str,
        name: str,
        writer: ArtifactWriter,
        evidence: EvidenceJournal,
        environment: RunEnvironment[ContextT],
        continue_from: Run[object] | None,
        phase: str,
        exc: BaseException,
    ) -> Run[ResultT]:
        try:
            fingerprint = environment.fingerprint()
        except Exception:
            fingerprint = {"unavailable": True}
        prepared = PreparedWorkspace(
            path=None,
            fingerprint=None,
            source=None,
            reusable=False,
            git_root=None,
            baseline_revision=None,
            initial_status="",
            cleanup=None,
        )
        return self._failure_with_workspace(
            run_id=run_id,
            name=name,
            writer=writer,
            evidence=evidence,
            environment_fingerprint=fingerprint,
            prepared_workspace=prepared,
            continue_from=continue_from,
            phase=phase,
            exc=exc,
        )

    def _failure_with_workspace(
        self,
        *,
        run_id: str,
        name: str,
        writer: ArtifactWriter,
        evidence: EvidenceJournal,
        environment_fingerprint: object,
        prepared_workspace: PreparedWorkspace,
        continue_from: Run[object] | None,
        phase: str,
        exc: BaseException,
    ) -> Run[ResultT]:
        error = _capture_error(writer, phase, exc)
        observation = observe_workspace(prepared_workspace)
        evidence.emit(
            "run.failed",
            {"phase": phase, "error": error},
            source="kernel",
        )
        run = Run(
            run_id=run_id,
            name=name,
            value=cast(ResultT, None),
            snapshot=None,
            environment={},
            environment_fingerprint=environment_fingerprint,
            workspace=prepared_workspace.path,
            workspace_fingerprint=prepared_workspace.fingerprint,
            changed_paths=observation.changed_paths,
            artifact_dir=writer.root,
            error=error,
            cache_hit=False,
            parent_run_id=continue_from.run_id if continue_from else None,
            snapshot_sha256=None,
            _workspace_source=prepared_workspace.source,
            _workspace_reusable=prepared_workspace.reusable,
        )
        self._write_completed_run(
            run=run,
            writer=writer,
            evidence=evidence,
            observation=observation,
        )
        return run

    def _replace_with_error(
        self,
        run: Run[ResultT],
        *,
        writer: ArtifactWriter,
        evidence: EvidenceJournal,
        prepared_workspace: PreparedWorkspace,
        phase: str,
        exc: BaseException,
    ) -> Run[ResultT]:
        error = _capture_error(writer, phase, exc)
        observation = observe_workspace(prepared_workspace)
        failed = Run(
            **{
                **run.__dict__,
                "error": error,
                "changed_paths": observation.changed_paths,
            }
        )
        evidence.emit(
            "run.failed",
            {"phase": phase, "error": error},
            source="kernel",
        )
        self._write_completed_run(
            run=failed,
            writer=writer,
            evidence=evidence,
            observation=observation,
        )
        return failed


def _capture_error(
    writer: ArtifactWriter,
    phase: str,
    exc: BaseException,
) -> RunError:
    safe_phase = phase.replace(".", "-").replace("/", "-")
    relative = f"raw/errors/{safe_phase}.txt"
    writer.write_text(
        relative,
        "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
    )
    return RunError(
        phase=phase,
        type=type(exc).__name__,
        message=str(exc),
        traceback_artifact=relative,
    )


def _run_id(name: str) -> str:
    safe_name = "".join(
        character if character.isalnum() else "-" for character in name.lower()
    ).strip("-")
    safe_name = "-".join(part for part in safe_name.split("-") if part)
    if not safe_name:
        raise ValueError("run name must contain an alphanumeric character")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    return f"{timestamp}-{safe_name}-{uuid.uuid4().hex[:8]}"


def _continuation_fingerprint(
    environment: RunEnvironment[object],
) -> object:
    """The environment's snapshot-compatibility surface.

    Environments without an explicit continuation fingerprint keep the
    strict behavior: continuation stays within one environment
    configuration.
    """

    method = getattr(environment, "continuation_fingerprint", None)
    if callable(method):
        value = method()
        # Protocol subclasses inherit a stub that returns None; that
        # means "not defined" and keeps the strict fingerprint rule.
        if value is not None:
            return value
    return environment.fingerprint()


def _serialize_snapshot(
    environment: object,
    snapshot: object,
) -> bytes:
    serializer = getattr(environment, "serialize_snapshot", None)
    if callable(serializer):
        payload = serializer(snapshot)
        if not isinstance(payload, bytes):
            raise TypeError("environment serialize_snapshot() must return bytes")
        return payload
    return pickle_bytes(snapshot)


def _deserialize_snapshot(
    environment: object,
    data: bytes | None,
) -> object | None:
    if data is None:
        return None
    deserializer = getattr(environment, "deserialize_snapshot", None)
    if callable(deserializer):
        return deserializer(data)
    import pickle

    return pickle.loads(data)


def _snapshot_hash(
    environment: object,
    snapshot: object,
) -> str:
    import hashlib

    return hashlib.sha256(_serialize_snapshot(environment, snapshot)).hexdigest()


def _copy_directory_contents(
    source: Path | None,
    destination: Path,
) -> None:
    if source is None or not source.is_dir():
        return
    for item in source.rglob("*"):
        relative = item.relative_to(source)
        target = destination / relative
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif item.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def _write_optional_pickle(
    writer: ArtifactWriter,
    evidence: EvidenceJournal,
    *,
    name: str,
    value: object,
) -> None:
    try:
        writer.write_bytes(
            f"raw/environment/{name}.pkl",
            pickle_bytes(value),
        )
    except BaseException as exc:
        writer.write_text(
            f"raw/environment/{name}.txt",
            repr(value) + "\n",
        )
        evidence.emit(
            "artifact.serialization_fallback",
            {
                "name": name,
                "error_type": type(exc).__name__,
                "error": str(exc),
            },
            source="kernel",
            visibility=EvidenceVisibility.RAW,
        )
