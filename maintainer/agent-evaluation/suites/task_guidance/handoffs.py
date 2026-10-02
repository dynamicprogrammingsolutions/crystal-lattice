from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .fixtures import (
    SUITE_ROOT,
    TaskGuidanceWorkspaceFactory,
)
from .scenarios import TaskGuidanceScenario


HANDOFF_ROOT = SUITE_ROOT / "fixtures" / "handoffs"
PLAN_PROMPT = (
    "Read the task files and present the Draft implementation plan. "
    "Do not modify files or implement the task."
)


@dataclass(frozen=True)
class CanonicalHandoffWorkspaceFactory:
    scenario: TaskGuidanceScenario
    variant: str
    bundle: Path

    def fingerprint(self) -> object:
        source = self.source_path
        return {
            "type": "task-guidance-canonical-handoff",
            "scenario_id": self.scenario.scenario_id,
            "variant": self.variant,
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "base": self._base().fingerprint(),
        }

    @property
    def source_path(self) -> Path:
        if self.variant not in {"retain", "omit", "incomplete"}:
            raise ValueError("handoff variant must be retain, omit, or incomplete")
        path = HANDOFF_ROOT / self.scenario.scenario_id / f"{self.variant}.md"
        if not path.is_file():
            raise FileNotFoundError(f"canonical handoff is missing: {path}")
        return path

    def __call__(self, staging_dir: Path) -> Path:
        base = self._base()
        workspace = base(staging_dir)
        relative = Path("tasks") / f"20260919-{self.scenario.scenario_id}.md"
        target = workspace / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(self.source_path.read_bytes())
        from .fixtures import _commit_fixture

        _commit_fixture(workspace)
        return workspace

    def cleanup(self, workspace: Path) -> None:
        self._base().cleanup(workspace)

    def _base(self) -> TaskGuidanceWorkspaceFactory:
        return TaskGuidanceWorkspaceFactory(
            scenario=self.scenario,
            bundle=self.bundle,
        )


@dataclass(frozen=True)
class GeneratedTaskWorkspaceFactory:
    """A fresh fixture-project workspace carrying generated task files.

    The files come from one producer run's recorded ``task_files``; a new
    agent plans from them exactly as they were written, with no access to
    the producer's session or scratch state.
    """

    scenario: TaskGuidanceScenario
    bundle: Path
    task_files: Mapping[str, str]

    def fingerprint(self) -> object:
        digest = hashlib.sha256()
        for path in sorted(self.task_files):
            digest.update(path.encode("utf-8"))
            digest.update(b"\0")
            digest.update(self.task_files[path].encode("utf-8"))
            digest.update(b"\0")
        return {
            "type": "task-guidance-generated-task",
            "scenario_id": self.scenario.scenario_id,
            "files_sha256": digest.hexdigest(),
            "base": self._base().fingerprint(),
        }

    def __call__(self, staging_dir: Path) -> Path:
        base = self._base()
        workspace = base(staging_dir)
        for relative, content in sorted(self.task_files.items()):
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        from .fixtures import _commit_fixture

        _commit_fixture(workspace)
        return workspace

    def cleanup(self, workspace: Path) -> None:
        self._base().cleanup(workspace)

    def _base(self) -> TaskGuidanceWorkspaceFactory:
        return TaskGuidanceWorkspaceFactory(
            scenario=self.scenario,
            bundle=self.bundle,
        )
