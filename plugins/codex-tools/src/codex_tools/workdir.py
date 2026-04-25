"""Working-directory helpers for Codex shell tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def _resolve_path(raw_path: str, *, base: Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = base / path
    try:
        return path.resolve()
    except Exception:
        return path.absolute()


def resolve_turn_cwd(config: Dict[str, Any] | None) -> str:
    """Resolve the effective per-turn cwd from config."""

    process_cwd = Path.cwd().resolve()
    configured = (config or {}).get("working_directory")
    if isinstance(configured, str) and configured.strip():
        return str(_resolve_path(configured, base=process_cwd))
    return str(process_cwd)


def resolve_tool_workdir(
    config: Dict[str, Any] | None,
    requested_workdir: Any,
) -> str:
    """Resolve the effective tool cwd using Codex-style defaults."""

    turn_cwd = Path(resolve_turn_cwd(config))
    if requested_workdir is None:
        return str(turn_cwd)
    if isinstance(requested_workdir, str):
        if not requested_workdir.strip():
            return str(turn_cwd)
        return str(_resolve_path(requested_workdir, base=turn_cwd))
    return str(turn_cwd)


__all__ = ["resolve_tool_workdir", "resolve_turn_cwd"]