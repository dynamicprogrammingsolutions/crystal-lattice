"""Public run result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Generic, TypeVar

from .services import ArtifactWriter


ResultT = TypeVar("ResultT", covariant=True)


@dataclass(frozen=True)
class RunError:
    """Failure captured without discarding the surrounding run evidence."""

    phase: str
    type: str
    message: str
    traceback_artifact: str | None = None


class RunFailedError(RuntimeError):
    """Raised by :meth:`Run.raise_for_error`."""

    def __init__(self, run: "Run[object]") -> None:
        assert run.error is not None
        super().__init__(
            f"evaluation run {run.name!r} failed during {run.error.phase}: "
            f"{run.error.type}: {run.error.message}"
        )
        self.run = run


@dataclass(frozen=True)
class Run(Generic[ResultT]):
    """Completed, failed, or cache-restored evaluation run."""

    run_id: str
    name: str
    value: ResultT
    snapshot: object | None
    environment: object
    environment_fingerprint: object
    workspace: Path | None
    workspace_fingerprint: object | None
    changed_paths: tuple[str, ...]
    artifact_dir: Path
    error: RunError | None
    cache_hit: bool
    parent_run_id: str | None
    snapshot_sha256: str | None
    continuation_fingerprint: object | None = None
    _workspace_source: object | None = field(default=None, repr=False, compare=False)
    _workspace_reusable: bool = field(default=False, repr=False, compare=False)

    def raise_for_error(self) -> None:
        if self.error is not None:
            raise RunFailedError(self)  # type: ignore[arg-type]

    def canonical_text(self) -> str:
        return self.artifact_dir.joinpath("result.md").read_text(encoding="utf-8")

    def record(self, name: str, value: object) -> Path:
        return ArtifactWriter(self.artifact_dir).record(name, value)
