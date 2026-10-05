"""Content-addressed local cache for completed evaluation runs."""

from __future__ import annotations

import hashlib
import json
import os
import pickle
import shutil
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Mapping

from .services import Evidence, jsonable

try:
    import fcntl
except ImportError:  # pragma: no cover - supported development hosts are POSIX
    fcntl = None  # type: ignore[assignment]


CACHE_SCHEMA = 1


@dataclass(frozen=True)
class CachedRun:
    manifest: Mapping[str, object]
    value: object
    snapshot_data: bytes | None
    environment: object
    evidence: tuple[Evidence, ...]
    workspace_patch: bytes
    untracked_root: Path | None
    raw_environment_root: Path | None
    records_root: Path | None


def stable_bytes(value: object) -> bytes:
    return json.dumps(
        jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def stable_hash(value: object) -> str:
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def pickle_bytes(value: object) -> bytes:
    return pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)


class CacheStore:
    """Atomic cache with process-level file locking."""

    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()
        self.entries = self.root / "entries"
        self.locks = self.root / "locks"
        self.entries.mkdir(parents=True, exist_ok=True)
        self.locks.mkdir(parents=True, exist_ok=True)

    def key(
        self,
        *,
        caller_key: str,
        environment_fingerprint: object,
        workspace_fingerprint: object | None,
        parent_snapshot_sha256: str | None,
    ) -> str:
        return stable_hash(
            {
                "schema": CACHE_SCHEMA,
                "caller_key": caller_key,
                "environment": environment_fingerprint,
                "workspace": workspace_fingerprint,
                "parent_snapshot_sha256": parent_snapshot_sha256,
            }
        )

    @contextmanager
    def lock(self, key: str) -> Iterator[None]:
        lock_path = self.locks / f"{key}.lock"
        lock_file = lock_path.open("a+b")
        try:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()

    def load(self, key: str) -> CachedRun | None:
        entry = self.entries / key
        if not entry.exists():
            return None
        complete = entry / "complete"
        if not complete.is_file():
            raise ValueError(f"cache entry is incomplete: {entry}")
        try:
            manifest = json.loads(
                entry.joinpath("manifest.json").read_text(encoding="utf-8")
            )
            if manifest.get("schema") != CACHE_SCHEMA:
                raise ValueError(
                    f"unsupported cache schema: {manifest.get('schema')!r}"
                )
            value = pickle.loads(entry.joinpath("value.pkl").read_bytes())
            snapshot_path = entry / "snapshot.bin"
            snapshot_data = (
                snapshot_path.read_bytes() if snapshot_path.is_file() else None
            )
            environment = pickle.loads(entry.joinpath("environment.pkl").read_bytes())
            evidence = pickle.loads(entry.joinpath("evidence.pkl").read_bytes())
            if not isinstance(evidence, tuple) or not all(
                isinstance(item, Evidence) for item in evidence
            ):
                raise ValueError("evidence.pkl does not contain Evidence items")
            patch_path = entry / "workspace.patch"
            patch = patch_path.read_bytes() if patch_path.is_file() else b""
            untracked_root = entry / "untracked"
            raw_environment_root = entry / "raw-environment"
            records_root = entry / "records"
            return CachedRun(
                manifest=manifest,
                value=value,
                snapshot_data=snapshot_data,
                environment=environment,
                evidence=evidence,
                workspace_patch=patch,
                untracked_root=untracked_root if untracked_root.is_dir() else None,
                raw_environment_root=(
                    raw_environment_root if raw_environment_root.is_dir() else None
                ),
                records_root=records_root if records_root.is_dir() else None,
            )
        except Exception as exc:
            raise ValueError(f"cache entry is corrupt: {entry}: {exc}") from exc

    def publish(
        self,
        key: str,
        *,
        manifest: Mapping[str, object],
        value: object,
        snapshot_data: bytes | None,
        environment: object,
        evidence: tuple[Evidence, ...],
        workspace_patch: bytes,
        untracked_root: Path | None,
        raw_environment_root: Path | None,
        records_root: Path | None,
    ) -> Path:
        destination = self.entries / key
        if destination.joinpath("complete").is_file():
            return destination

        temporary = self.entries / f".{key}.tmp-{os.getpid()}-{uuid.uuid4().hex}"
        temporary.mkdir(parents=True)
        try:
            temporary.joinpath("manifest.json").write_text(
                json.dumps(
                    jsonable(dict(manifest)),
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            temporary.joinpath("value.pkl").write_bytes(pickle_bytes(value))
            if snapshot_data is not None:
                temporary.joinpath("snapshot.bin").write_bytes(snapshot_data)
            temporary.joinpath("environment.pkl").write_bytes(pickle_bytes(environment))
            temporary.joinpath("evidence.pkl").write_bytes(pickle_bytes(evidence))
            if workspace_patch:
                temporary.joinpath("workspace.patch").write_bytes(workspace_patch)
            if untracked_root is not None and untracked_root.is_dir():
                shutil.copytree(untracked_root, temporary / "untracked")
            if raw_environment_root is not None and raw_environment_root.is_dir():
                shutil.copytree(
                    raw_environment_root,
                    temporary / "raw-environment",
                )
            if records_root is not None and records_root.is_dir():
                shutil.copytree(records_root, temporary / "records")
            temporary.joinpath("complete").write_text("complete\n", encoding="utf-8")
            try:
                temporary.replace(destination)
            except FileExistsError:
                shutil.rmtree(temporary)
        except BaseException:
            shutil.rmtree(temporary, ignore_errors=True)
            raise
        return destination
