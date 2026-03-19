from __future__ import annotations

import base64
import fnmatch
import json
import mimetypes
import os
import re
from pathlib import Path
from typing import Any, Optional

MAX_FILE_BYTES = 20 * 1024 * 1024
SVG_MAX_SIZE_BYTES = 1 * 1024 * 1024
DEFAULT_GEMINI_LINE_LIMIT = 2000
DEFAULT_GEMINI_LINE_CHAR_LIMIT = 2000
DEFAULT_QWEN_LINE_LIMIT = 500
DEFAULT_QWEN_CHAR_LIMIT = 2500


def detect_bom(payload: bytes) -> tuple[str, int] | None:
    if len(payload) >= 4:
        if payload[:4] == b"\xff\xfe\x00\x00":
            return ("utf32le", 4)
        if payload[:4] == b"\x00\x00\xfe\xff":
            return ("utf32be", 4)
    if len(payload) >= 3 and payload[:3] == b"\xef\xbb\xbf":
        return ("utf8", 3)
    if len(payload) >= 2:
        if payload[:2] == b"\xff\xfe" and payload[:4] != b"\xff\xfe\x00\x00":
            return ("utf16le", 2)
        if payload[:2] == b"\xfe\xff":
            return ("utf16be", 2)
    return None


def _decode_utf16be(payload: bytes) -> str:
    swapped = bytearray(payload)
    for index in range(0, len(swapped) - 1, 2):
        swapped[index], swapped[index + 1] = swapped[index + 1], swapped[index]
    return bytes(swapped).decode("utf-16le", errors="replace")


def _decode_utf32(payload: bytes, *, little_endian: bool) -> str:
    usable = len(payload) - (len(payload) % 4)
    out: list[str] = []
    for index in range(0, usable, 4):
        chunk = payload[index : index + 4]
        code_point = int.from_bytes(chunk, "little" if little_endian else "big")
        if code_point <= 0x10FFFF and not (0xD800 <= code_point <= 0xDFFF):
            out.append(chr(code_point))
        else:
            out.append("\uFFFD")
    return "".join(out)


def read_file_with_encoding(file_path: str | Path) -> str:
    payload = Path(file_path).read_bytes()
    if not payload:
        return ""
    bom = detect_bom(payload)
    if not bom:
        return payload.decode("utf-8", errors="replace")
    encoding, bom_length = bom
    content = payload[bom_length:]
    if encoding == "utf8":
        return content.decode("utf-8", errors="replace")
    if encoding == "utf16le":
        return content.decode("utf-16le", errors="replace")
    if encoding == "utf16be":
        return _decode_utf16be(content)
    if encoding == "utf32le":
        return _decode_utf32(content, little_endian=True)
    return _decode_utf32(content, little_endian=False)


def is_within(base_path: str | Path, candidate_path: str | Path) -> bool:
    try:
        Path(candidate_path).resolve().relative_to(Path(base_path).resolve())
        return True
    except ValueError:
        return False


def resolve_path(
    raw_path: str,
    *,
    working_directory: str,
    allow_relative: bool,
) -> str:
    if allow_relative and not os.path.isabs(raw_path):
        return str((Path(working_directory) / raw_path).resolve())
    return str(Path(raw_path).resolve())


def _guess_file_type(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    if suffix in {".ts", ".mts", ".cts", ".tsx"}:
        return "text"
    if suffix == ".svg":
        return "svg"
    mime_type, _encoding = mimetypes.guess_type(file_path)
    if isinstance(mime_type, str):
        if mime_type.startswith("image/"):
            return "image"
        if mime_type.startswith("audio/"):
            return "audio" if is_binary_file(file_path) else "text"
        if mime_type.startswith("video/"):
            return "video" if is_binary_file(file_path) else "text"
        if mime_type == "application/pdf":
            return "pdf"
    if is_binary_file(file_path):
        return "binary"
    return "text"


def is_binary_file(file_path: str | Path) -> bool:
    file_path = str(file_path)
    with open(file_path, "rb") as handle:
        sample = handle.read(4096)
    if not sample:
        return False
    if detect_bom(sample[:4]):
        return False
    if b"\x00" in sample:
        return True
    non_printable = 0
    for byte in sample:
        if byte < 9 or (13 < byte < 32):
            non_printable += 1
    return (non_printable / len(sample)) > 0.3


def _inline_data_payload(file_path: str, *, include_display_name: bool) -> dict[str, Any]:
    mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    payload = {
        "data": base64.b64encode(Path(file_path).read_bytes()).decode("ascii"),
        "mimeType": mime_type,
    }
    if include_display_name:
        payload["displayName"] = Path(file_path).name
    return {"inlineData": payload}


def _read_common_file(file_path: str, *, display_root: str, include_display_name: bool) -> dict[str, Any]:
    target = Path(file_path)
    display_path = _display_path(target, Path(display_root))
    if not target.exists():
        return {
            "ok": False,
            "llm_content": "Could not read file because no file was found at the specified path.",
            "return_display": "File not found.",
            "error": f"File not found: {target}",
            "kind": "error",
        }
    if target.is_dir():
        return {
            "ok": False,
            "llm_content": "Could not read file because the provided path is a directory, not a file.",
            "return_display": "Path is a directory.",
            "error": f"Path is a directory, not a file: {target}",
            "kind": "error",
        }
    if target.stat().st_size > MAX_FILE_BYTES:
        size_mb = target.stat().st_size / (1024 * 1024)
        return {
            "ok": False,
            "llm_content": "File size exceeds the 20MB limit.",
            "return_display": "File size exceeds the 20MB limit.",
            "error": f"File size exceeds the 20MB limit: {target} ({size_mb:.2f}MB)",
            "kind": "error",
        }

    file_type = _guess_file_type(str(target))
    if file_type == "binary":
        return {
            "ok": True,
            "llm_content": f"Cannot display content of binary file: {display_path}",
            "return_display": f"Skipped binary file: {display_path}",
            "kind": "text",
        }
    if file_type == "svg":
        if target.stat().st_size > SVG_MAX_SIZE_BYTES:
            return {
                "ok": True,
                "llm_content": f"Cannot display content of SVG file larger than 1MB: {display_path}",
                "return_display": f"Skipped large SVG file (>1MB): {display_path}",
                "kind": "text",
            }
        return {
            "ok": True,
            "llm_content": read_file_with_encoding(target),
            "return_display": f"Read SVG as text: {display_path}",
            "kind": "text",
        }
    if file_type in {"image", "audio", "video", "pdf"}:
        return {
            "ok": True,
            "llm_content": _inline_data_payload(str(target), include_display_name=include_display_name),
            "return_display": f"Read {file_type} file: {display_path}",
            "kind": "inline",
        }

    return {
        "ok": True,
        "llm_content": read_file_with_encoding(target),
        "return_display": "",
        "kind": "text-source",
    }


def _display_path(file_path: Path, root: Path) -> str:
    try:
        relative = file_path.resolve().relative_to(root.resolve())
        return relative.as_posix() or "."
    except ValueError:
        return file_path.name


def gemini_display_path(file_path: str, root: str) -> str:
    return _display_path(Path(file_path), Path(root))


def qwen_display_path(file_path: str, root: str) -> str:
    return _display_path(Path(file_path), Path(root))


def _slice_gemini_text(content: str, *, start_line: Optional[int], end_line: Optional[int], display_path: str) -> dict[str, Any]:
    lines = content.split("\n")
    original_line_count = len(lines)
    slice_start = start_line - 1 if isinstance(start_line, int) else 0
    if isinstance(end_line, int):
        slice_end = min(end_line, original_line_count)
    elif isinstance(start_line, int):
        slice_end = min(slice_start + DEFAULT_GEMINI_LINE_LIMIT, original_line_count)
    else:
        slice_end = min(DEFAULT_GEMINI_LINE_LIMIT, original_line_count)
    actual_start = min(slice_start, original_line_count)
    selected = lines[actual_start:slice_end]
    shortened = False
    formatted: list[str] = []
    for line in selected:
        if len(line) > DEFAULT_GEMINI_LINE_CHAR_LIMIT:
            shortened = True
            formatted.append(line[:DEFAULT_GEMINI_LINE_CHAR_LIMIT] + "... [truncated]")
        else:
            formatted.append(line)
    body = "\n".join(formatted)
    is_truncated = actual_start > 0 or slice_end < original_line_count or shortened
    return_display = ""
    if actual_start > 0 or slice_end < original_line_count:
        return_display = f"Read lines {actual_start + 1}-{slice_end} of {original_line_count} from {display_path}"
        if shortened:
            return_display += " (some lines were shortened)"
    elif shortened:
        return_display = f"Read all {original_line_count} lines from {display_path} (some lines were shortened)"
    if is_truncated:
        body = (
            "IMPORTANT: The file content has been truncated.\n"
            f"Status: Showing lines {actual_start + 1}-{slice_end} of {original_line_count} total lines.\n"
            "Action: To read more of the file, you can use the 'start_line' and 'end_line' parameters in a subsequent 'read_file' call. "
            f"For example, to read the next section of the file, use start_line: {slice_end + 1}.\n\n"
            "--- FILE CONTENT (truncated) ---\n"
            f"{body}"
        )
    return {
        "llm_content": body,
        "return_display": return_display,
        "is_truncated": is_truncated,
        "original_line_count": original_line_count,
        "lines_shown": [actual_start + 1, slice_end],
    }


def read_gemini_style_file(
    file_path: str,
    *,
    display_root: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
) -> dict[str, Any]:
    common = _read_common_file(file_path, display_root=display_root, include_display_name=False)
    if common["kind"] != "text-source":
        return common
    display_path = gemini_display_path(file_path, display_root)
    text_result = _slice_gemini_text(
        str(common["llm_content"]),
        start_line=start_line,
        end_line=end_line,
        display_path=display_path,
    )
    return {"ok": True, "kind": "text", **text_result}


def _slice_qwen_text(
    content: str,
    *,
    offset: Optional[int],
    limit: Optional[int],
    display_path: str,
    line_limit: int,
    char_limit: Optional[int],
) -> dict[str, Any]:
    lines = [line.rstrip() for line in content.split("\n")]
    original_line_count = len(lines)
    start_line = offset or 0
    effective_limit = line_limit if limit is None else limit
    end_line = min(start_line + effective_limit, original_line_count)
    actual_start = min(start_line, original_line_count)
    selected = lines[actual_start:end_line]
    included = 0
    length_truncated = False
    if isinstance(char_limit, int):
        out_lines: list[str] = []
        current_length = 0
        for line in selected:
            separator = 1 if included > 0 else 0
            projected = current_length + len(line) + separator
            if projected <= char_limit:
                out_lines.append(line)
                current_length = projected
                included += 1
                continue
            remaining = max(char_limit - current_length - separator, 10)
            out_lines.append(line[:remaining] + "... [truncated]")
            included += 1
            length_truncated = True
            break
        body = "\n".join(out_lines)
    else:
        body = "\n".join(selected)
        included = len(selected)
    actual_end = actual_start + included if length_truncated else end_line
    content_range_truncated = start_line > 0 or actual_end < original_line_count
    is_truncated = content_range_truncated or length_truncated
    return_display = ""
    if is_truncated:
        return_display = f"Read lines {actual_start + 1}-{actual_end} of {original_line_count} from {display_path}"
        if length_truncated:
            return_display += " (truncated)"
        body = build_qwen_truncation_wrapper(body, actual_start + 1, actual_end, original_line_count)
    return {
        "llm_content": body,
        "return_display": return_display,
        "is_truncated": is_truncated,
        "original_line_count": original_line_count,
        "lines_shown": [actual_start + 1, actual_end],
    }


def build_qwen_truncation_wrapper(body: str, start_line: int, end_line: int, total_lines: int) -> str:
    return f"Showing lines {start_line}-{end_line} of {total_lines} total lines.\n\n---\n\n{body}"


def read_qwen_style_file(
    file_path: str,
    *,
    display_root: str,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    line_limit: int = DEFAULT_QWEN_LINE_LIMIT,
    char_limit: Optional[int] = DEFAULT_QWEN_CHAR_LIMIT,
) -> dict[str, Any]:
    common = _read_common_file(file_path, display_root=display_root, include_display_name=True)
    if common["kind"] != "text-source":
        return common
    display_path = qwen_display_path(file_path, display_root)
    text_result = _slice_qwen_text(
        str(common["llm_content"]),
        offset=offset,
        limit=limit,
        display_path=display_path,
        line_limit=line_limit,
        char_limit=char_limit,
    )
    return {"ok": True, "kind": "text", **text_result}


def grok_directory_listing(directory_path: str, *, display_root: str) -> dict[str, Any]:
    target = Path(directory_path)
    display_path = _display_path(target, Path(display_root))
    entries = []
    for child in sorted(target.iterdir(), key=lambda item: item.name.lower()):
        name = child.name + ("/" if child.is_dir() else "")
        entries.append(name)
    body = "\n".join(entries)
    if display_path == ".":
        return {"ok": True, "kind": "text", "llm_content": body, "return_display": "Listed directory contents."}
    return {
        "ok": True,
        "kind": "text",
        "llm_content": f"Directory listing for {display_path}:\n{body}" if body else f"Directory listing for {display_path}:",
        "return_display": f"Listed directory contents for {display_path}.",
    }


def validate_path_within_directories(path_value: str, directories: list[str]) -> bool:
    return any(is_within(directory, path_value) for directory in directories)


def _load_ignore_patterns(root: str, ignore_filename: str) -> list[str]:
    ignore_path = Path(root) / ignore_filename
    if not ignore_path.is_file():
        return []
    patterns: list[str] = []
    for raw_line in ignore_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)
    return patterns


def is_path_ignored(path_value: str, *, root: str, ignore_filename: str) -> bool:
    target = Path(path_value).resolve()
    try:
        relative = target.relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return False
    for pattern in _load_ignore_patterns(root, ignore_filename):
        normalized = pattern.lstrip("/")
        if normalized.endswith("/"):
            prefix = normalized.rstrip("/")
            if relative == prefix or relative.startswith(prefix + "/"):
                return True
            continue
        if fnmatch.fnmatch(relative, normalized) or fnmatch.fnmatch(target.name, normalized):
            return True
    return False


def truncate_line(line: str, max_length: int, marker: str = "...") -> str:
    """Truncate a line if it exceeds max_length, preserving trailing line breaks.

    The output may be longer than max_length if it is too short to fit the marker.
    """
    if len(line) <= max_length:
        return line
    m = re.search(r"[\r\n]+$", line)
    linebreak = m.group(0) if m else ""
    end = marker + linebreak
    effective_max = max(max_length, len(end))
    return line[: effective_max - len(end)] + end


def format_with_line_numbers(lines: list[str], start_line: int = 1, width: int = 6) -> str:
    """Format lines with right-aligned line numbers and a tab separator (cat -n style).

    Each line is terminated with a newline character. The input lines should
    not include their own trailing newlines.
    """
    parts: list[str] = []
    for index, line in enumerate(lines):
        line_num = start_line + index
        parts.append(f"{line_num:{width}d}\t{line}\n")
    return "".join(parts)


def format_tool_result_payload(outcome: dict[str, Any]) -> dict[str, Any]:
    if not outcome.get("ok"):
        return {
            "success": False,
            "error": str(outcome.get("error") or outcome.get("llm_content") or "Unknown error"),
            "result": outcome.get("llm_content", ""),
            "return_display": outcome.get("return_display", ""),
        }
    return {
        "success": True,
        "result": outcome.get("llm_content", ""),
        "kind": outcome.get("kind", "text"),
        "return_display": outcome.get("return_display", ""),
        "lines_shown": outcome.get("lines_shown"),
        "original_line_count": outcome.get("original_line_count"),
        "is_truncated": outcome.get("is_truncated", False),
    }


def format_tool_result_text(result: dict[str, Any]) -> str:
    if result.get("success") is not True:
        return f"Error: {result.get('error')}"
    payload = result.get("result", "")
    if isinstance(payload, str):
        return payload
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)