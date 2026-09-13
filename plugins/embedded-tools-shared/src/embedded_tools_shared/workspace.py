from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


class WorkspacePathError(ValueError):
    """A model-supplied path is invalid for the configured workspace."""


@dataclass(frozen=True)
class ResolvedWorkspacePath:
    root: Path
    path: Path
    logical_path: str


def resolve_workspace_root(config: Mapping[str, Any]) -> Path:
    raw_root = config.get("working_directory")
    if not isinstance(raw_root, str) or not raw_root.strip():
        raise WorkspacePathError("working_directory is required")
    root = Path(raw_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_workspace_path(
    root: Path,
    raw_path: Any,
    *,
    field_name: str = "file_path",
) -> ResolvedWorkspacePath:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise WorkspacePathError(f"{field_name} must be a non-empty string")

    logical_path = raw_path.strip()
    untrusted = Path(logical_path)
    if untrusted.is_absolute():
        raise WorkspacePathError(
            "Absolute paths are not allowed. Remove the leading slash and use "
            "a workspace-relative path such as input.txt."
        )

    resolved = (root / untrusted).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as error:
        raise WorkspacePathError("Path escapes the configured workspace") from error

    return ResolvedWorkspacePath(
        root=root,
        path=resolved,
        logical_path=relative.as_posix(),
    )