from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .workspace import resolve_workspace_path


DEFAULT_MAX_ENUMERATED_PATHS = 500
DEFAULT_MAX_SEARCH_MATCHES = 500
DEFAULT_MAX_SEARCH_FILE_BYTES = 1024 * 1024


@dataclass(frozen=True)
class EnumeratedPath:
    path: str
    is_file: bool
    is_directory: bool


@dataclass(frozen=True)
class EnumerationResult:
    paths: tuple[EnumeratedPath, ...]
    truncated: bool


@dataclass(frozen=True)
class TextMatch:
    path: str
    line_number: int
    line: str
    before: tuple[tuple[int, str], ...]
    after: tuple[tuple[int, str], ...]


@dataclass(frozen=True)
class TextSearchResult:
    matches: tuple[TextMatch, ...]
    counts: tuple[tuple[str, int], ...]
    truncated: bool

    @property
    def files(self) -> tuple[str, ...]:
        return tuple(path for path, _count in self.counts)


def _is_hidden(relative: Path) -> bool:
    return any(part.startswith(".") for part in relative.parts)


def _matches_path_glob(path: str, pattern: str) -> bool:
    if fnmatch.fnmatch(path, pattern):
        return True
    if pattern.startswith("**/"):
        return fnmatch.fnmatch(path, pattern[3:])
    return False


def _matches_any_path_glob(path: str, patterns: Sequence[str] | None) -> bool:
    if not patterns:
        return True
    return any(_matches_path_glob(path, pattern) for pattern in patterns)


def enumerate_workspace_paths(
    root: Path,
    *,
    start_path: str = ".",
    path_globs: Sequence[str] | None = None,
    name_globs: Sequence[str] | None = None,
    kind: str = "file",
    include_hidden: bool = False,
    max_depth: int | None = None,
    max_results: int = DEFAULT_MAX_ENUMERATED_PATHS,
    sort_results: bool = True,
) -> EnumerationResult:
    start = resolve_workspace_path(root, start_path, field_name="path")
    if not start.path.exists():
        raise ValueError(f"Path does not exist: {start.logical_path}")
    if kind not in {"file", "directory", "any"}:
        raise ValueError("kind must be file, directory, or any")

    limit = max(1, min(max_results, DEFAULT_MAX_ENUMERATED_PATHS))
    candidates: Iterable[Path]
    if start.path.is_file():
        candidates = (start.path,)
    else:
        candidates = start.path.rglob("*")

    matches: list[EnumeratedPath] = []
    truncated = False
    for candidate in candidates:
        relative_to_root = candidate.relative_to(root)
        relative_to_start = (
            Path(candidate.name)
            if start.path.is_file()
            else candidate.relative_to(start.path)
        )
        if max_depth is not None and len(relative_to_start.parts) > max_depth:
            continue
        if not include_hidden and _is_hidden(relative_to_start):
            continue

        safe = resolve_workspace_path(
            root,
            relative_to_root.as_posix(),
            field_name="path",
        )
        is_file = safe.path.is_file()
        is_directory = safe.path.is_dir()
        if kind == "file" and not is_file:
            continue
        if kind == "directory" and not is_directory:
            continue

        logical = safe.logical_path
        scoped = relative_to_start.as_posix()
        if not _matches_any_path_glob(scoped, path_globs):
            continue
        if name_globs and not any(
            fnmatch.fnmatch(candidate.name, pattern) for pattern in name_globs
        ):
            continue

        if len(matches) >= limit:
            truncated = True
            break
        matches.append(
            EnumeratedPath(
                path=logical,
                is_file=is_file,
                is_directory=is_directory,
            )
        )

    if sort_results:
        matches.sort(key=lambda entry: entry.path)
    return EnumerationResult(paths=tuple(matches), truncated=truncated)


def search_workspace_text(
    root: Path,
    pattern: str,
    *,
    start_path: str = ".",
    fixed_strings: bool = False,
    case_sensitive: bool = True,
    include_hidden: bool = False,
    path_globs: Sequence[str] | None = None,
    context_before: int = 0,
    context_after: int = 0,
    max_results: int = DEFAULT_MAX_SEARCH_MATCHES,
    max_file_bytes: int = DEFAULT_MAX_SEARCH_FILE_BYTES,
) -> TextSearchResult:
    if not isinstance(pattern, str) or not pattern:
        raise ValueError("pattern must be a non-empty string")

    flags = 0 if case_sensitive else re.IGNORECASE
    expression = re.compile(re.escape(pattern) if fixed_strings else pattern, flags)
    limit = max(1, min(max_results, DEFAULT_MAX_SEARCH_MATCHES))
    before_count = max(0, min(context_before, 20))
    after_count = max(0, min(context_after, 20))

    start = resolve_workspace_path(root, start_path, field_name="path")
    if not start.path.exists():
        raise ValueError(f"Path does not exist: {start.logical_path}")

    if start.path.is_file():
        candidates = (start.path,)
    else:
        candidates = start.path.rglob("*")

    matches: list[TextMatch] = []
    counts: dict[str, int] = {}
    truncated = False
    for candidate in candidates:
        if not candidate.is_file():
            continue
        relative_to_start = (
            Path(candidate.name)
            if start.path.is_file()
            else candidate.relative_to(start.path)
        )
        if not include_hidden and _is_hidden(relative_to_start):
            continue
        if not _matches_any_path_glob(relative_to_start.as_posix(), path_globs):
            continue

        relative_to_root = candidate.relative_to(root).as_posix()
        safe = resolve_workspace_path(root, relative_to_root, field_name="path")
        if safe.path.stat().st_size > max_file_bytes:
            continue
        try:
            lines = safe.path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue

        file_count = 0
        for index, line in enumerate(lines):
            if expression.search(line) is None:
                continue
            file_count += 1
            if len(matches) >= limit:
                truncated = True
                break
            before = tuple(
                (line_index + 1, lines[line_index])
                for line_index in range(max(0, index - before_count), index)
            )
            after = tuple(
                (line_index + 1, lines[line_index])
                for line_index in range(
                    index + 1,
                    min(len(lines), index + after_count + 1),
                )
            )
            matches.append(
                TextMatch(
                    path=safe.logical_path,
                    line_number=index + 1,
                    line=line,
                    before=before,
                    after=after,
                )
            )
        if file_count:
            counts[safe.logical_path] = file_count
        if truncated:
            break

    return TextSearchResult(
        matches=tuple(matches),
        counts=tuple(sorted(counts.items())),
        truncated=truncated,
    )