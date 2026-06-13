from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


_DIGEST_IGNORE_DIRS = {".git", "__pycache__"}
_DIGEST_IGNORE_SUFFIXES = {".pyc", ".pyo", ".log"}


@dataclass(frozen=True)
class StagedContainerBuildContext:
    context_dir: Path
    dockerfile: Path
    dockerfile_relative_path: str
    digest: str


def stage_container_build_context(
    container: Mapping[str, Any],
    *,
    workspace_dir: Path,
    destination_dir: Path,
) -> StagedContainerBuildContext:
    """Create a sanitized Docker build context for a resolved container profile."""

    context_dir = destination_dir / "context"
    if context_dir.exists():
        shutil.rmtree(context_dir)
    context_dir.mkdir(parents=True, exist_ok=True)

    context_entries = _entries(container.get("context_entries"))
    if context_entries:
        for entry in context_entries:
            _stage_entry(entry, workspace_dir=workspace_dir, context_dir=context_dir)
        dockerfile_relative_path = _safe_relative_path(
            container.get("dockerfile"), label="Dockerfile path"
        )
    else:
        context_source = _resolved_path(
            container.get("context_path"), container.get("context"), workspace_dir
        )
        if not context_source.is_dir():
            raise RuntimeError(
                f"Container build context does not exist: {context_source}"
            )
        dockerfile_source = _resolved_path(
            container.get("dockerfile_path"), container.get("dockerfile"), workspace_dir
        )
        if not dockerfile_source.is_file():
            raise RuntimeError(
                f"Container Dockerfile does not exist: {dockerfile_source}"
            )

        _copy_tree_contents(context_source, context_dir)
        dockerfile_relative_path = _stage_dockerfile(
            dockerfile_source, context_source=context_source, context_dir=context_dir
        )

    for asset in _entries(container.get("build_assets")):
        _stage_entry(asset, workspace_dir=workspace_dir, context_dir=context_dir)

    dockerfile = context_dir / dockerfile_relative_path
    if not dockerfile.is_file():
        raise RuntimeError(f"Container Dockerfile does not exist: {dockerfile}")

    digest = container_build_digest(
        {**dict(container), "dockerfile": dockerfile_relative_path.as_posix()},
        context_dir=context_dir,
    )
    return StagedContainerBuildContext(
        context_dir=context_dir,
        dockerfile=dockerfile,
        dockerfile_relative_path=dockerfile_relative_path.as_posix(),
        digest=digest,
    )


def container_build_digest(container: Mapping[str, Any], *, context_dir: Path) -> str:
    digest = hashlib.sha256()
    metadata = {
        "build_args": _string_mapping(container.get("build_args")),
        "dockerfile": str(container.get("dockerfile") or ""),
        "target": str(container.get("target") or ""),
    }
    digest.update(json.dumps(metadata, sort_keys=True).encode("utf-8"))
    digest.update(b"\0")
    for path in _digest_paths(context_dir):
        relative = path.relative_to(context_dir).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _copy_tree_contents(source: Path, destination: Path) -> None:
    for child in sorted(source.iterdir(), key=lambda item: item.name):
        if child.name in _DIGEST_IGNORE_DIRS or any(
            child.name.endswith(suffix) for suffix in _DIGEST_IGNORE_SUFFIXES
        ):
            continue
        _copy_path(child, destination / child.name)


def _copy_path(source: Path, destination: Path) -> None:
    if source.is_dir():
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination, ignore=_copy_ignore)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _stage_entry(
    entry: Mapping[str, Any], *, workspace_dir: Path, context_dir: Path
) -> None:
    source = _resolved_path(
        entry.get("source_path"), entry.get("source"), workspace_dir
    )
    if not source.exists():
        raise RuntimeError(f"Container build source does not exist: {source}")
    target = _safe_relative_path(entry.get("target"), label="build source target")
    _copy_path(source, context_dir / target)


def _copy_ignore(_dir: str, names: list[str]) -> set[str]:
    return {
        name
        for name in names
        if name in _DIGEST_IGNORE_DIRS
        or any(name.endswith(suffix) for suffix in _DIGEST_IGNORE_SUFFIXES)
    }


def _digest_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for current, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            name for name in dirnames if name not in _DIGEST_IGNORE_DIRS
        )
        for filename in sorted(filenames):
            if any(filename.endswith(suffix) for suffix in _DIGEST_IGNORE_SUFFIXES):
                continue
            paths.append(Path(current) / filename)
    return paths


def _resolved_path(resolved: Any, raw: Any, workspace_dir: Path) -> Path:
    if isinstance(resolved, str) and resolved.strip():
        return Path(resolved).expanduser().resolve()
    if not isinstance(raw, str) or not raw.strip():
        raise RuntimeError("Container build path must be a non-empty string")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = workspace_dir / path
    return path.resolve()


def _stage_dockerfile(
    dockerfile_source: Path, *, context_source: Path, context_dir: Path
) -> Path:
    try:
        relative = dockerfile_source.relative_to(context_source)
    except ValueError:
        relative = Path("__dockerfile__") / dockerfile_source.name
        _copy_path(dockerfile_source, context_dir / relative)
        return relative

    staged = context_dir / relative
    if not staged.is_file():
        _copy_path(dockerfile_source, staged)
    return relative


def _safe_relative_path(raw: Any, *, label: str) -> Path:
    if not isinstance(raw, str) or not raw.strip():
        raise RuntimeError(f"Container {label} must be a non-empty string")
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise RuntimeError(
            f"Container {label} must be a relative path inside the context"
        )
    return path


def _entries(raw: Any) -> list[Mapping[str, Any]]:
    if not isinstance(raw, list):
        return []
    return [entry for entry in raw if isinstance(entry, Mapping)]


def _string_mapping(raw: Any) -> dict[str, str]:
    if not isinstance(raw, Mapping):
        return {}
    return {str(key): str(value) for key, value in raw.items()}


__all__ = [
    "StagedContainerBuildContext",
    "container_build_digest",
    "stage_container_build_context",
]
