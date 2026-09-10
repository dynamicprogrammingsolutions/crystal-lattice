from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .workspace import resolve_workspace_path


DEFAULT_MAX_READ_BYTES = 256 * 1024
DEFAULT_MAX_READ_LINES = 2000
DEFAULT_MAX_EDIT_BYTES = 1024 * 1024


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


@dataclass(frozen=True)
class EditTextResult:
    path: str
    replacements: int
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


def edit_text_file(
    root: Path,
    raw_path: Any,
    old_text: str,
    new_text: str,
    *,
    replace_all: bool = False,
    max_bytes: int = DEFAULT_MAX_EDIT_BYTES,
) -> EditTextResult:
    if not isinstance(old_text, str) or not isinstance(new_text, str):
        raise ValueError("old_string and new_string must be strings")
    if old_text == new_text:
        raise ValueError("old_string and new_string must be different")
    if not old_text:
        raise ValueError("old_string must not be empty")

    resolved = resolve_workspace_path(root, raw_path)
    if not resolved.path.is_file():
        raise ValueError(f"File does not exist: {resolved.logical_path}")
    if resolved.path.stat().st_size > max_bytes:
        raise ValueError(f"File is larger than the {max_bytes // 1024} KB edit limit")

    content = resolved.path.read_text(encoding="utf-8")
    occurrences = content.count(old_text)
    if occurrences == 0:
        raise ValueError("String to replace not found in file")
    if occurrences > 1 and not replace_all:
        raise ValueError(
            f"Found {occurrences} matches; provide more context or set replace_all"
        )

    replacements = occurrences if replace_all else 1
    updated = content.replace(old_text, new_text, -1 if replace_all else 1)
    resolved.path.write_text(updated, encoding="utf-8")
    return EditTextResult(
        path=resolved.logical_path,
        replacements=replacements,
        bytes_written=len(updated.encode("utf-8")),
    )