from __future__ import annotations

import fnmatch
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path, PurePosixPath
from typing import Any

from .reader_engine import is_binary_file, is_path_ignored, read_file_with_encoding


RECENT_FILE_THRESHOLD_MS = 24 * 60 * 60 * 1000
MAX_QWEN_GLOB_RESULTS = 100


def _match_path(pattern: str, relative_path: str, *, case_sensitive: bool) -> bool:
    candidate = relative_path.replace(os.sep, "/")
    if not case_sensitive:
        candidate = candidate.lower()
        pattern = pattern.lower()
    return PurePosixPath(candidate).match(pattern)


def _path_is_ignored(
    path_value: str,
    *,
    display_root: str,
    vendor_ignore_filename: str | None,
    respect_git_ignore: bool,
    respect_vendor_ignore: bool,
) -> str | None:
    if respect_git_ignore and is_path_ignored(path_value, root=display_root, ignore_filename=".gitignore"):
        return "git"
    if vendor_ignore_filename and respect_vendor_ignore:
        if is_path_ignored(path_value, root=display_root, ignore_filename=vendor_ignore_filename):
            return "vendor"
    return None


def list_directory_entries(
    directory_path: str,
    *,
    display_root: str,
    ignore_patterns: list[str] | None = None,
    vendor_ignore_filename: str | None = None,
    respect_git_ignore: bool = True,
    respect_vendor_ignore: bool = True,
) -> dict[str, Any]:
    target = Path(directory_path)
    if not target.exists():
        return {"ok": False, "error": f"Directory not found or inaccessible: {target}", "code": "not_found"}
    if not target.is_dir():
        return {"ok": False, "error": f"Path is not a directory: {target}", "code": "not_directory"}

    entries: list[dict[str, Any]] = []
    git_ignored_count = 0
    vendor_ignored_count = 0
    for child in target.iterdir():
        if ignore_patterns and any(fnmatch.fnmatch(child.name, pattern) for pattern in ignore_patterns):
            continue
        ignored_kind = _path_is_ignored(
            str(child.resolve()),
            display_root=display_root,
            vendor_ignore_filename=vendor_ignore_filename,
            respect_git_ignore=respect_git_ignore,
            respect_vendor_ignore=respect_vendor_ignore,
        )
        if ignored_kind == "git":
            git_ignored_count += 1
            continue
        if ignored_kind == "vendor":
            vendor_ignored_count += 1
            continue
        stats = child.stat()
        entries.append(
            {
                "name": child.name,
                "path": str(child.resolve()),
                "is_directory": child.is_dir(),
                "size": 0 if child.is_dir() else stats.st_size,
                "mtime_ms": int(stats.st_mtime * 1000),
            }
        )

    entries.sort(key=lambda entry: (not entry["is_directory"], entry["name"].lower()))
    return {
        "ok": True,
        "directory": str(target.resolve()),
        "entries": entries,
        "git_ignored_count": git_ignored_count,
        "vendor_ignored_count": vendor_ignored_count,
    }


def _iter_files(search_root: Path) -> list[Path]:
    if search_root.is_file():
        return [search_root]
    results: list[Path] = []
    for root, _dirs, files in os.walk(search_root):
        base = Path(root)
        for file_name in files:
            results.append((base / file_name).resolve())
    return results


def _sort_paths_by_recency(paths: list[Path]) -> list[Path]:
    now_ms = int(time.time() * 1000)

    def sort_key(path_value: Path) -> tuple[int, float, str]:
        mtime_ms = path_value.stat().st_mtime * 1000
        is_recent = 0 if (now_ms - mtime_ms) < RECENT_FILE_THRESHOLD_MS else 1
        if is_recent == 0:
            return (is_recent, -mtime_ms, str(path_value))
        return (is_recent, 0.0, str(path_value))

    return sorted(paths, key=sort_key)


def glob_search(
    pattern: str,
    *,
    search_directories: list[str],
    display_root: str,
    vendor_ignore_filename: str | None = None,
    case_sensitive: bool = False,
    respect_git_ignore: bool = True,
    respect_vendor_ignore: bool = True,
) -> dict[str, Any]:
    matched: list[Path] = []
    ignored_count = 0
    for directory in search_directories:
        root = Path(directory).resolve()
        if not root.exists():
            continue
        for candidate in _iter_files(root):
            ignored_kind = _path_is_ignored(
                str(candidate),
                display_root=display_root,
                vendor_ignore_filename=vendor_ignore_filename,
                respect_git_ignore=respect_git_ignore,
                respect_vendor_ignore=respect_vendor_ignore,
            )
            if ignored_kind is not None:
                ignored_count += 1
                continue
            try:
                relative = candidate.relative_to(root).as_posix()
            except ValueError:
                relative = candidate.name
            if _match_path(pattern, relative, case_sensitive=case_sensitive):
                matched.append(candidate)

    sorted_matches = _sort_paths_by_recency(list({path: None for path in matched}.keys()))
    return {
        "ok": True,
        "paths": [str(path) for path in sorted_matches],
        "count": len(sorted_matches),
        "ignored_count": ignored_count,
    }


def _compile_pattern(pattern: str, *, ignore_case: bool) -> re.Pattern[str]:
    flags = re.IGNORECASE if ignore_case else 0
    return re.compile(pattern, flags)


def _run_ripgrep(
    pattern: str,
    *,
    search_path: str,
    glob_pattern: str | None,
    ignore_case: bool,
    names_only: bool,
    max_matches_per_file: int | None,
    respect_git_ignore: bool,
) -> dict[str, Any]:
    rg = shutil.which("rg")
    if not rg:
        return {"ok": False, "error": "rg not available", "code": "missing_rg"}

    target = Path(search_path).resolve()
    cwd = str(target if target.is_dir() else target.parent)
    target_arg = "." if target.is_dir() else target.name
    args = [rg]
    if names_only:
        args.extend(["--files-with-matches", "--no-messages"])
    else:
        args.extend(["--json", "-n", "--no-messages"])
    if ignore_case:
        args.append("-i")
    if not respect_git_ignore:
        args.append("--no-ignore")
    if max_matches_per_file is not None and max_matches_per_file > 0 and not names_only:
        args.extend(["--max-count", str(max_matches_per_file)])
    if glob_pattern:
        args.extend(["--glob", glob_pattern])
    args.extend([pattern, target_arg])
    completed = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    if completed.returncode not in {0, 1}:
        stderr = completed.stderr.strip() or completed.stdout.strip() or "ripgrep failed"
        return {"ok": False, "error": stderr, "code": "rg_failed"}
    return {"ok": True, "stdout": completed.stdout, "names_only": names_only, "cwd": cwd}


def _parse_ripgrep_output(payload: dict[str, Any], *, search_path: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if payload.get("names_only"):
        cwd = Path(payload["cwd"]).resolve()
        for raw_line in str(payload["stdout"]).splitlines():
            if not raw_line.strip():
                continue
            absolute_path = str((cwd / raw_line).resolve())
            results.append({"path": absolute_path})
        return results

    cwd = Path(payload["cwd"]).resolve()
    for raw_line in str(payload["stdout"]).splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        event = json.loads(raw_line)
        if event.get("type") != "match":
            continue
        data = event.get("data") or {}
        path_data = data.get("path") or {}
        text_path = path_data.get("text")
        if not isinstance(text_path, str):
            continue
        absolute_path = str((cwd / text_path).resolve())
        line_text = ((data.get("lines") or {}).get("text") or "").rstrip("\n")
        results.append(
            {
                "path": absolute_path,
                "line_number": int(data.get("line_number") or 0),
                "line": line_text,
            }
        )
    return results


def grep_search(
    pattern: str,
    *,
    search_path: str,
    display_root: str,
    glob_pattern: str | None = None,
    exclude_pattern: str | None = None,
    names_only: bool = False,
    max_matches_per_file: int | None = None,
    total_max_matches: int | None = None,
    ignore_case: bool = False,
    vendor_ignore_filename: str | None = None,
    respect_git_ignore: bool = True,
    respect_vendor_ignore: bool = True,
    use_rg: bool | None = None,
) -> dict[str, Any]:
    compiled = _compile_pattern(pattern, ignore_case=ignore_case)
    excluded = re.compile(exclude_pattern) if exclude_pattern else None

    raw_results: list[dict[str, Any]] = []
    used_rg = False
    if use_rg is not False:
        rg_payload = _run_ripgrep(
            pattern,
            search_path=search_path,
            glob_pattern=glob_pattern,
            ignore_case=ignore_case,
            names_only=names_only,
            max_matches_per_file=max_matches_per_file,
            respect_git_ignore=respect_git_ignore,
        )
        if rg_payload.get("ok"):
            raw_results = _parse_ripgrep_output(rg_payload, search_path=search_path)
            used_rg = True

    if not raw_results and use_rg is not True:
        root = Path(search_path).resolve()
        files = _iter_files(root)
        per_file_counts: dict[str, int] = {}
        for candidate in files:
            ignored_kind = _path_is_ignored(
                str(candidate),
                display_root=display_root,
                vendor_ignore_filename=vendor_ignore_filename,
                respect_git_ignore=respect_git_ignore,
                respect_vendor_ignore=respect_vendor_ignore,
            )
            if ignored_kind is not None:
                continue
            if glob_pattern:
                base = root if root.is_dir() else root.parent
                relative = candidate.relative_to(base).as_posix()
                if not _match_path(glob_pattern, relative, case_sensitive=False):
                    continue
            if is_binary_file(candidate):
                continue
            try:
                text = read_file_with_encoding(candidate)
            except OSError:
                continue
            for line_number, line in enumerate(text.splitlines(), start=1):
                if not compiled.search(line):
                    continue
                if excluded and excluded.search(line):
                    continue
                key = str(candidate)
                if names_only:
                    raw_results.append({"path": key})
                    break
                seen = per_file_counts.get(key, 0)
                if max_matches_per_file is not None and seen >= max_matches_per_file:
                    continue
                per_file_counts[key] = seen + 1
                raw_results.append({"path": key, "line_number": line_number, "line": line.rstrip()})

    filtered_results: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for item in raw_results:
        path_value = str(Path(item["path"]).resolve())
        ignored_kind = _path_is_ignored(
            path_value,
            display_root=display_root,
            vendor_ignore_filename=vendor_ignore_filename,
            respect_git_ignore=respect_git_ignore,
            respect_vendor_ignore=respect_vendor_ignore,
        )
        if ignored_kind is not None:
            continue
        if names_only:
            if path_value in seen_paths:
                continue
            seen_paths.add(path_value)
            filtered_results.append({"path": path_value})
        else:
            line = str(item.get("line") or "")
            if not compiled.search(line):
                continue
            if excluded and excluded.search(line):
                continue
            filtered_results.append(
                {"path": path_value, "line_number": int(item.get("line_number") or 0), "line": line.rstrip()}
            )
        if total_max_matches is not None and len(filtered_results) >= total_max_matches:
            break

    return {"ok": True, "results": filtered_results, "used_rg": used_rg}


def format_gemini_list_result(outcome: dict[str, Any]) -> dict[str, Any]:
    entries = outcome["entries"]
    content = "\n".join(
        f"[DIR] {entry['name']}" if entry["is_directory"] else f"{entry['name']} ({entry['size']} bytes)"
        for entry in entries
    )
    message = f"Directory listing for {outcome['directory']}:"
    if content:
        message += f"\n{content}"
    else:
        message += "\n"
    ignored_count = outcome["git_ignored_count"] + outcome["vendor_ignored_count"]
    if ignored_count > 0:
        message += f"\n\n({ignored_count} ignored)"
    display = f"Listed {len(entries)} item(s)."
    if ignored_count > 0:
        display += f" ({ignored_count} ignored)"
    return {"success": True, "result": message, "kind": "text", "return_display": display}


def format_qwen_list_result(outcome: dict[str, Any], *, vendor_label: str) -> dict[str, Any]:
    entries = outcome["entries"]
    content = "\n".join(f"[DIR] {entry['name']}" if entry["is_directory"] else entry["name"] for entry in entries)
    message = f"Directory listing for {outcome['directory']}:"
    if content:
        message += f"\n{content}"
    else:
        message += "\n"
    ignored_messages: list[str] = []
    if outcome["git_ignored_count"] > 0:
        ignored_messages.append(f"{outcome['git_ignored_count']} git-ignored")
    if outcome["vendor_ignored_count"] > 0:
        ignored_messages.append(f"{outcome['vendor_ignored_count']} {vendor_label}-ignored")
    if ignored_messages:
        message += f"\n\n({', '.join(ignored_messages)})"
    display = f"Listed {len(entries)} item(s)."
    if ignored_messages:
        display += f" ({', '.join(ignored_messages)})"
    return {"success": True, "result": message, "kind": "text", "return_display": display}


def format_gemini_glob_result(outcome: dict[str, Any], *, pattern: str, search_description: str) -> dict[str, Any]:
    count = outcome["count"]
    if count == 0:
        message = f'No files found matching pattern "{pattern}" {search_description}'
        if outcome["ignored_count"] > 0:
            message += f" ({outcome['ignored_count']} files were ignored)"
        return {"success": True, "result": message, "kind": "text", "return_display": "No files found"}
    message = (
        f'Found {count} file(s) matching "{pattern}" {search_description}, '
        "sorted by modification time (newest first):\n"
        + "\n".join(outcome["paths"])
    )
    if outcome["ignored_count"] > 0:
        message += f"\n\n({outcome['ignored_count']} additional files were ignored)"
    return {"success": True, "result": message, "kind": "text", "return_display": f"Found {count} matching file(s)"}


def format_qwen_glob_result(
    outcome: dict[str, Any],
    *,
    pattern: str,
    search_description: str,
    line_limit: int,
) -> dict[str, Any]:
    paths = list(outcome["paths"])
    total_count = outcome["count"]
    if total_count == 0:
        return {
            "success": True,
            "result": f'No files found matching pattern "{pattern}" {search_description}',
            "kind": "text",
            "return_display": "No files found",
        }
    file_limit = min(MAX_QWEN_GLOB_RESULTS, max(1, line_limit))
    truncated = total_count > file_limit
    visible_paths = paths[:file_limit] if truncated else paths
    message = (
        f'Found {total_count} file(s) matching "{pattern}" {search_description}, '
        "sorted by modification time (newest first):\n---\n"
        + "\n".join(visible_paths)
    )
    if truncated:
        omitted = total_count - file_limit
        noun = "file" if omitted == 1 else "files"
        message += f"\n---\n[{omitted} {noun} truncated] ..."
    display = f"Found {total_count} matching file(s)"
    if truncated:
        display += " (truncated)"
    return {"success": True, "result": message, "kind": "text", "return_display": display}


def format_gemini_grep_result(
    outcome: dict[str, Any],
    *,
    pattern: str,
    search_description: str,
    names_only: bool,
) -> dict[str, Any]:
    results = outcome["results"]
    if not results:
        return {
            "success": True,
            "result": f'No matches found for pattern "{pattern}" {search_description}.',
            "kind": "text",
            "return_display": "No matches found",
        }
    if names_only:
        body = "\n".join(item["path"] for item in results)
        count = len(results)
        noun = "file" if count == 1 else "files"
        message = f'Found {count} {noun} with matches for pattern "{pattern}" {search_description}:\n{body}'
        return {"success": True, "result": message, "kind": "text", "return_display": f"Found {count} {noun}"}

    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in results:
        grouped.setdefault(item["path"], []).append(item)
    blocks: list[str] = []
    for path_value, matches in grouped.items():
        lines = [f"File: {path_value}"]
        for match in matches:
            lines.append(f"L{match['line_number']}: {match['line'].rstrip()}")
        blocks.append("\n".join(lines))
    match_count = len(results)
    noun = "match" if match_count == 1 else "matches"
    message = f'Found {match_count} {noun} for pattern "{pattern}" {search_description}:\n' + "\n---\n".join(blocks)
    return {"success": True, "result": message, "kind": "text", "return_display": f"Found {match_count} {noun}"}


def format_qwen_grep_result(
    outcome: dict[str, Any],
    *,
    pattern: str,
    search_description: str,
    glob_pattern: str | None,
    line_limit: int,
    char_limit: int,
) -> dict[str, Any]:
    results = outcome["results"]
    filter_description = f' (filter: "{glob_pattern}")' if glob_pattern else ""
    if not results:
        return {
            "success": True,
            "result": f'No matches found for pattern "{pattern}" {search_description}{filter_description}.',
            "kind": "text",
            "return_display": "No matches found",
        }

    total_matches = len(results)
    included = results[: max(1, line_limit)]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in included:
        grouped.setdefault(item["path"], []).append(item)
    body_parts: list[str] = []
    for path_value, matches in grouped.items():
        body_parts.append(f"File: {path_value}")
        for match in matches:
            body_parts.append(f"L{match['line_number']}: {match['line'].strip()}")
        body_parts.append("---")
    grep_output = "\n".join(body_parts)
    truncated = False
    if len(grep_output) > char_limit:
        grep_output = grep_output[:char_limit] + "..."
        truncated = True
    if total_matches > len(included):
        truncated = True
    noun = "match" if total_matches == 1 else "matches"
    message = f'Found {total_matches} {noun} for pattern "{pattern}" {search_description}{filter_description}:\n---\n{grep_output}'.rstrip()
    if truncated:
        omitted = max(total_matches - len(included), 0)
        noun2 = "line" if omitted == 1 else "lines"
        message += f" [{omitted} {noun2} truncated] ..."
    display = f"Found {total_matches} {noun}"
    if truncated:
        display += " (truncated)"
    return {"success": True, "result": message, "kind": "text", "return_display": display}
