from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .workspace import ResolvedWorkspacePath, resolve_workspace_path


DEFAULT_MAX_PATCH_BYTES = 2 * 1024 * 1024


class PatchError(ValueError):
    """The patch is invalid or cannot be applied to the workspace."""


@dataclass(frozen=True)
class PatchChange:
    type: Literal["add", "update", "delete"]
    path: str
    move_path: str | None = None


@dataclass(frozen=True)
class PatchResult:
    changes: tuple[PatchChange, ...]
    fuzz: int


@dataclass(frozen=True)
class _PendingChange:
    change: PatchChange
    source: ResolvedWorkspacePath
    destination: ResolvedWorkspacePath | None
    content: str | None


def _find_sequence(
    lines: list[str],
    expected: list[str],
    start: int,
) -> tuple[int, int]:
    if not expected:
        return start, 0
    last_start = len(lines) - len(expected)
    for index in range(start, last_start + 1):
        if lines[index : index + len(expected)] == expected:
            return index, 0
    stripped_expected = [line.rstrip() for line in expected]
    for index in range(start, last_start + 1):
        if [line.rstrip() for line in lines[index : index + len(expected)]] == (
            stripped_expected
        ):
            return index, 1
    whitespace_expected = [line.strip() for line in expected]
    for index in range(start, last_start + 1):
        if [line.strip() for line in lines[index : index + len(expected)]] == (
            whitespace_expected
        ):
            return index, 100
    return -1, 0


def _anchor_start(lines: list[str], header: str, start: int) -> tuple[int, int]:
    if not header:
        return start, 0
    for index in range(start, len(lines)):
        if lines[index] == header:
            return index + 1, 0
    for index in range(start, len(lines)):
        if lines[index].strip() == header.strip():
            return index + 1, 1
    raise PatchError(f"Update context header not found: {header}")


def _apply_update_hunks(
    original: str,
    hunk_lines: list[str],
    *,
    path: str,
) -> tuple[str, int]:
    had_trailing_newline = original.endswith("\n")
    lines = original.splitlines()
    cursor = 0
    index = 0
    fuzz = 0
    hunk_count = 0

    while index < len(hunk_lines):
        header_line = hunk_lines[index]
        if not header_line.startswith("@@"):
            raise PatchError(f"Invalid update line for {path}: {header_line}")
        header = header_line[2:].strip()
        index += 1
        body: list[str] = []
        end_of_file = False
        while index < len(hunk_lines) and not hunk_lines[index].startswith("@@"):
            line = hunk_lines[index]
            if line == "*** End of File":
                end_of_file = True
                index += 1
                break
            if line.startswith("***"):
                raise PatchError(f"Invalid update line for {path}: {line}")
            if not line or line[0] not in {" ", "+", "-"}:
                raise PatchError(f"Invalid hunk line for {path}: {line}")
            body.append(line)
            index += 1
        if not body:
            raise PatchError(f"Empty update hunk for {path}")

        search_start, header_fuzz = _anchor_start(lines, header, cursor)
        fuzz += header_fuzz
        expected: list[str] = []
        replacement: list[str] = []
        for line in body:
            marker, value = line[0], line[1:]
            if marker in {" ", "-"}:
                expected.append(value)
            if marker in {" ", "+"}:
                replacement.append(value)

        if expected:
            if end_of_file:
                candidate_start = max(0, len(lines) - len(expected))
                found, match_fuzz = _find_sequence(
                    lines,
                    expected,
                    candidate_start,
                )
                if found < candidate_start:
                    found = -1
            else:
                found, match_fuzz = _find_sequence(lines, expected, search_start)
            if found < 0:
                context = "\n".join(expected)
                raise PatchError(f"Update context not found in {path}:\n{context}")
        else:
            found = len(lines) if end_of_file else search_start
            match_fuzz = 0

        fuzz += match_fuzz
        lines[found : found + len(expected)] = replacement
        cursor = found + len(replacement)
        hunk_count += 1

    if hunk_count == 0:
        raise PatchError(f"Update file has no hunks: {path}")
    updated = "\n".join(lines)
    if had_trailing_newline:
        updated += "\n"
    return updated, fuzz


def _next_section_index(lines: list[str], start: int) -> int:
    index = start
    while index < len(lines):
        if lines[index].startswith(
            (
                "*** Add File: ",
                "*** Update File: ",
                "*** Delete File: ",
                "*** End Patch",
            )
        ):
            break
        index += 1
    return index


def _parse_patch(
    root: Path,
    patch_text: str,
) -> tuple[list[_PendingChange], int]:
    lines = patch_text.strip().splitlines()
    if len(lines) < 3 or lines[0] != "*** Begin Patch":
        raise PatchError("Patch must start with '*** Begin Patch'")
    if lines[-1] != "*** End Patch":
        raise PatchError("Patch must end with '*** End Patch'")

    pending: list[_PendingChange] = []
    seen_paths: set[str] = set()
    fuzz = 0
    index = 1
    while index < len(lines) - 1:
        header = lines[index]
        if header.startswith("*** Add File: "):
            raw_path = header.removeprefix("*** Add File: ").strip()
            source = resolve_workspace_path(root, raw_path, field_name="path")
            if source.logical_path in seen_paths:
                raise PatchError(f"Duplicate patch path: {source.logical_path}")
            if source.path.exists():
                raise PatchError(f"Add File already exists: {source.logical_path}")
            seen_paths.add(source.logical_path)
            index += 1
            end = _next_section_index(lines, index)
            content_lines: list[str] = []
            for line in lines[index:end]:
                if not line.startswith("+"):
                    raise PatchError(f"Invalid Add File line: {line}")
                content_lines.append(line[1:])
            if not content_lines:
                raise PatchError(f"Add File has no content: {source.logical_path}")
            pending.append(
                _PendingChange(
                    change=PatchChange(type="add", path=source.logical_path),
                    source=source,
                    destination=None,
                    content="\n".join(content_lines),
                )
            )
            index = end
            continue

        if header.startswith("*** Delete File: "):
            raw_path = header.removeprefix("*** Delete File: ").strip()
            source = resolve_workspace_path(root, raw_path, field_name="path")
            if source.logical_path in seen_paths:
                raise PatchError(f"Duplicate patch path: {source.logical_path}")
            if not source.path.is_file():
                raise PatchError(f"Delete File does not exist: {source.logical_path}")
            seen_paths.add(source.logical_path)
            pending.append(
                _PendingChange(
                    change=PatchChange(type="delete", path=source.logical_path),
                    source=source,
                    destination=None,
                    content=None,
                )
            )
            index += 1
            continue

        if header.startswith("*** Update File: "):
            raw_path = header.removeprefix("*** Update File: ").strip()
            source = resolve_workspace_path(root, raw_path, field_name="path")
            if source.logical_path in seen_paths:
                raise PatchError(f"Duplicate patch path: {source.logical_path}")
            if not source.path.is_file():
                raise PatchError(f"Update File does not exist: {source.logical_path}")
            seen_paths.add(source.logical_path)
            index += 1

            destination: ResolvedWorkspacePath | None = None
            if index < len(lines) and lines[index].startswith("*** Move to: "):
                raw_destination = lines[index].removeprefix("*** Move to: ").strip()
                destination = resolve_workspace_path(
                    root,
                    raw_destination,
                    field_name="path",
                )
                if (
                    destination.logical_path != source.logical_path
                    and destination.path.exists()
                ):
                    raise PatchError(
                        f"Move destination already exists: {destination.logical_path}"
                    )
                index += 1

            end = _next_section_index(lines, index)
            updated, update_fuzz = _apply_update_hunks(
                source.path.read_text(encoding="utf-8"),
                lines[index:end],
                path=source.logical_path,
            )
            fuzz += update_fuzz
            pending.append(
                _PendingChange(
                    change=PatchChange(
                        type="update",
                        path=source.logical_path,
                        move_path=(
                            destination.logical_path if destination is not None else None
                        ),
                    ),
                    source=source,
                    destination=destination,
                    content=updated,
                )
            )
            index = end
            continue

        raise PatchError(f"Unknown patch line: {header}")

    return pending, fuzz


def apply_workspace_patch(
    root: Path,
    patch_text: str,
    *,
    max_bytes: int = DEFAULT_MAX_PATCH_BYTES,
) -> PatchResult:
    if not isinstance(patch_text, str) or not patch_text.strip():
        raise PatchError("input must be a non-empty string")
    if len(patch_text.encode("utf-8")) > max_bytes:
        raise PatchError(f"Patch too large (>{max_bytes} bytes)")

    pending, fuzz = _parse_patch(root, patch_text)
    for item in pending:
        if item.change.type == "delete":
            item.source.path.unlink()
            continue

        destination = item.destination or item.source
        destination.path.parent.mkdir(parents=True, exist_ok=True)
        destination.path.write_text(item.content or "", encoding="utf-8")
        if item.destination is not None and item.destination.path != item.source.path:
            item.source.path.unlink()

    return PatchResult(
        changes=tuple(item.change for item in pending),
        fuzz=fuzz,
    )