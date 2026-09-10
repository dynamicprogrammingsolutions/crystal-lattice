from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .workspace import resolve_workspace_path


DEFAULT_MAX_READ_BYTES = 256 * 1024
DEFAULT_MAX_READ_LINES = 2000


@dataclass(frozen=True)
class ReadTextResult:
    path: str
    text: str
    offset: int
    returned_lines: int


@dataclass(frozen=True)
class WriteTextResult:
    path: str
    bytes_written: int


def read_text_file(
    root: Path,
    raw_path: Any,
    *,
    offset: int = 0,
    limit: int = DEFAULT_MAX_READ_LINES,
    max_bytes: int = DEFAULT_MAX_READ_BYTES,
    number_lines: bool = True,
) -> ReadTextResult:
    resolved = resolve_workspace_path(root, raw_path)
    if not resolved.path.is_file():
        raise ValueError(f"File does not exist: {resolved.logical_path}")
    if resolved.path.stat().st_size > max_bytes:
        raise ValueError(f"File is larger than the {max_bytes // 1024} KB read limit")

    text = resolved.path.read_text(encoding="utf-8")
    lines = text.splitlines()
    safe_offset = max(0, offset)
    safe_limit = max(1, min(limit, DEFAULT_MAX_READ_LINES))
    selected = lines[safe_offset : safe_offset + safe_limit]
    if number_lines:
        rendered = "\n".join(
            f"{safe_offset + index + 1}\t{line}"
            for index, line in enumerate(selected)
        )
    else:
        rendered = "\n".join(selected)
    return ReadTextResult(
        path=resolved.logical_path,
        text=rendered,
        offset=safe_offset,
        returned_lines=len(selected),
    )


def write_text_file(
    root: Path,
    raw_path: Any,
    content: str,
) -> WriteTextResult:
    if not isinstance(content, str):
        raise ValueError("content must be a string")
    resolved = resolve_workspace_path(root, raw_path)
    resolved.path.parent.mkdir(parents=True, exist_ok=True)
    resolved.path.write_text(content, encoding="utf-8")
    return WriteTextResult(
        path=resolved.logical_path,
        bytes_written=len(content.encode("utf-8")),
    )