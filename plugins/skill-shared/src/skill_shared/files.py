from __future__ import annotations

from pathlib import Path


def sanitize_single_line(value: str) -> str:
    return " ".join(str(value).split())


def validate_max_len(value: str, max_len: int, field: str) -> None:
    if len(value) > max_len:
        raise ValueError(f"{field} exceeds maximum length of {max_len} characters")


def resolved_path_within_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False