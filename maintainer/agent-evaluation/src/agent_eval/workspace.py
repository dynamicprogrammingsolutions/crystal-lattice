"""Workspace preparation and Git-backed isolation."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, TypeAlias

from .services import jsonable


WorkspaceFactory: TypeAlias = Callable[[Path], Path]


@dataclass
class PreparedWorkspace:
    path: Path | None
    fingerprint: object | None
    source: object | None
    reusable: bool
    git_root: Path | None
    baseline_revision: str | None
    initial_status: str
    cleanup: Callable[[], None] | None


@dataclass(frozen=True)
class WorkspaceObservation:
    changed_paths: tuple[str, ...]
    git_status: str
    git_diff: bytes
    untracked_paths: tuple[str, ...]


@dataclass(frozen=True)
class GitWorkspaceFactory:
    """Prepare a detached worktree for a local repository or repository URL."""

    source: str
    revision: str
    cache_root: Path | None = None

    def fingerprint(self) -> object:
        return {
            "type": "git",
            "source": self.source,
            "revision": self.revision,
        }

    def __call__(self, staging_dir: Path) -> Path:
        repository = self._repository()
        target = staging_dir.resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            shutil.rmtree(target)
        _run(
            [
                "git",
                "-C",
                str(repository),
                "worktree",
                "add",
                "--detach",
                str(target),
                self.revision,
            ],
            timeout=600,
        )
        checked_out = _git(target, "rev-parse", "HEAD").strip()
        expected = _git(repository, "rev-parse", self.revision).strip()
        if checked_out != expected:
            raise RuntimeError(
                f"unexpected worktree revision: {checked_out} != {expected}"
            )
        return target

    def cleanup(self, workspace: Path) -> None:
        repository = self._repository(fetch=False)
        _run(
            [
                "git",
                "-C",
                str(repository),
                "worktree",
                "remove",
                "--force",
                str(workspace),
            ],
            timeout=120,
            check=False,
        )
        _run(
            ["git", "-C", str(repository), "worktree", "prune"],
            timeout=120,
            check=False,
        )

    def _repository(self, *, fetch: bool = True) -> Path:
        source_path = Path(self.source).expanduser()
        if source_path.exists():
            return source_path.resolve()

        cache_root = self.cache_root
        if cache_root is None:
            cache_root = Path(tempfile.gettempdir()) / "agent-eval-repository-cache"
        cache_root = cache_root.expanduser().resolve()
        cache_root.mkdir(parents=True, exist_ok=True)
        slug = hashlib.sha256(self.source.encode("utf-8")).hexdigest()[:20]
        repository = cache_root / slug
        if not repository.joinpath(".git").is_dir():
            _run(
                [
                    "git",
                    "clone",
                    "--filter=blob:none",
                    "--no-checkout",
                    self.source,
                    str(repository),
                ],
                timeout=600,
            )
        if fetch:
            _run(
                [
                    "git",
                    "-C",
                    str(repository),
                    "fetch",
                    "--depth=1",
                    "origin",
                    self.revision,
                ],
                timeout=600,
            )
        return repository


def git_workspace(
    *,
    source: str | Path,
    revision: str,
    cache_root: Path | None = None,
) -> GitWorkspaceFactory:
    """Return a reusable factory for clean pinned Git workspaces."""

    source_path = Path(source).expanduser()
    source_text = str(source_path.resolve()) if source_path.exists() else str(source)
    return GitWorkspaceFactory(
        source=source_text,
        revision=revision,
        cache_root=cache_root,
    )


def prepare_workspace(
    workspace: Path | WorkspaceFactory | None,
    *,
    run_dir: Path,
) -> PreparedWorkspace:
    if workspace is None:
        return PreparedWorkspace(
            path=None,
            fingerprint=None,
            source=None,
            reusable=True,
            git_root=None,
            baseline_revision=None,
            initial_status="",
            cleanup=None,
        )

    reusable = not isinstance(workspace, Path)
    cleanup: Callable[[], None] | None = None
    if isinstance(workspace, Path):
        path = workspace.expanduser().resolve()
        source: object = workspace
    else:
        staging = run_dir / "workspace"
        path = workspace(staging).expanduser().resolve()
        source = workspace
        cleanup_method = getattr(workspace, "cleanup", None)
        if callable(cleanup_method):

            def cleanup_workspace() -> None:
                cleanup_method(path)

            cleanup = cleanup_workspace

    if not path.exists():
        raise FileNotFoundError(f"workspace does not exist: {path}")

    git_root = _git_root(path)
    baseline_revision = (
        _git(git_root, "rev-parse", "HEAD").strip() if git_root is not None else None
    )
    initial_status = (
        _git(git_root, "status", "--short", "--untracked-files=all")
        if git_root is not None
        else ""
    )
    fingerprint = {
        "source": _source_fingerprint(source),
        "path_kind": "git" if git_root is not None else "directory",
        "revision": baseline_revision,
        "initial_status_sha256": hashlib.sha256(
            initial_status.encode("utf-8")
        ).hexdigest(),
    }
    return PreparedWorkspace(
        path=path,
        fingerprint=fingerprint,
        source=source,
        reusable=reusable,
        git_root=git_root,
        baseline_revision=baseline_revision,
        initial_status=initial_status,
        cleanup=cleanup,
    )


def observe_workspace(workspace: PreparedWorkspace) -> WorkspaceObservation:
    if workspace.git_root is None:
        return WorkspaceObservation(
            changed_paths=(),
            git_status="",
            git_diff=b"",
            untracked_paths=(),
        )
    status = _git(
        workspace.git_root,
        "status",
        "--short",
        "--untracked-files=all",
    )
    changed_paths = _status_paths(status)
    diff = _run(
        [
            "git",
            "-C",
            str(workspace.git_root),
            "diff",
            "--binary",
            "HEAD",
        ],
    ).stdout.encode("utf-8", errors="surrogateescape")
    untracked = tuple(
        line[3:] for line in status.splitlines() if line.startswith("?? ") and line[3:]
    )
    return WorkspaceObservation(
        changed_paths=changed_paths,
        git_status=status,
        git_diff=diff,
        untracked_paths=untracked,
    )


def apply_cached_workspace(
    workspace: PreparedWorkspace,
    *,
    patch: bytes,
    untracked_root: Path | None,
) -> None:
    if not patch and untracked_root is None:
        return
    if workspace.git_root is None:
        raise ValueError("cached workspace changes require a Git workspace")
    if patch:
        patch_path = workspace.git_root / ".agent-eval-cache.patch"
        patch_path.write_bytes(patch)
        try:
            _run(
                [
                    "git",
                    "-C",
                    str(workspace.git_root),
                    "apply",
                    "--binary",
                    str(patch_path),
                ],
            )
        finally:
            patch_path.unlink(missing_ok=True)
    if untracked_root is not None and untracked_root.is_dir():
        for source in untracked_root.rglob("*"):
            if not source.is_file():
                continue
            relative = source.relative_to(untracked_root)
            target = workspace.git_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def copy_untracked_files(
    workspace: PreparedWorkspace,
    observation: WorkspaceObservation,
    destination: Path,
) -> None:
    if workspace.git_root is None:
        return
    for relative_text in observation.untracked_paths:
        source = workspace.git_root / relative_text
        if not source.is_file():
            continue
        target = destination / relative_text
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _source_fingerprint(source: object) -> object:
    method = getattr(source, "fingerprint", None)
    if callable(method):
        return jsonable(method())
    if isinstance(source, Path):
        return {"type": "path", "path": str(source.expanduser().resolve())}
    module = getattr(source, "__module__", type(source).__module__)
    qualname = getattr(source, "__qualname__", type(source).__qualname__)
    return {"type": "callable", "callable": f"{module}.{qualname}"}


def _git_root(path: Path) -> Path | None:
    result = _run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        check=False,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()).resolve()


def _status_paths(status: str) -> tuple[str, ...]:
    paths: set[str] = set()
    for line in status.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            old, new = path.split(" -> ", 1)
            paths.add(old)
            paths.add(new)
        else:
            paths.add(path)
    return tuple(sorted(paths))


def _git(workspace: Path, *args: str) -> str:
    return _run(["git", "-C", str(workspace), *args]).stdout


def _run(
    command: list[str],
    *,
    timeout: int = 120,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=check,
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
