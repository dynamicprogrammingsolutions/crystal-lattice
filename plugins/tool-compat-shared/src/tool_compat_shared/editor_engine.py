from __future__ import annotations

from pathlib import Path
from typing import Any

from .reader_engine import detect_bom, read_file_with_encoding


def _bom_prefix_and_encoding(file_path: Path) -> tuple[bytes, str] | None:
    if not file_path.exists() or file_path.is_dir():
        return None
    payload = file_path.read_bytes()
    if not payload:
        return None
    bom = detect_bom(payload)
    if not bom:
        return None
    encoding, bom_length = bom
    prefix = payload[:bom_length]
    codec = {
        "utf8": "utf-8",
        "utf16le": "utf-16le",
        "utf16be": "utf-16be",
        "utf32le": "utf-32le",
        "utf32be": "utf-32be",
    }[encoding]
    return prefix, codec


def _write_text_preserving_bom(file_path: Path, content: str) -> None:
    bom_info = _bom_prefix_and_encoding(file_path)
    if bom_info is None:
        file_path.write_text(content, encoding="utf-8")
        return
    prefix, codec = bom_info
    file_path.write_bytes(prefix + content.encode(codec))


def write_text_file(
    file_path: str | Path,
    content: str,
    *,
    create_only: bool = False,
    mode: str = "overwrite",
) -> dict[str, Any]:
    target = Path(file_path)
    if target.exists() and target.is_dir():
        return {
            "ok": False,
            "code": "directory",
            "file_path": str(target),
            "error": f"Path is a directory, not a file: {target}",
        }
    if create_only and target.exists():
        return {
            "ok": False,
            "code": "already_exists",
            "file_path": str(target),
            "error": f"File already exists, cannot create: {target}",
        }

    file_existed = target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)

    if mode == "append" and file_existed:
        existing = read_file_with_encoding(target)
        final_content = existing + content
        _write_text_preserving_bom(target, final_content)
        return {
            "ok": True,
            "code": "appended",
            "file_path": str(target),
            "file_existed": file_existed,
            "created": False,
            "content": final_content,
            "kind": "text",
            "llm_content": final_content,
        }

    _write_text_preserving_bom(target, content)
    return {
        "ok": True,
        "code": "written",
        "file_path": str(target),
        "file_existed": file_existed,
        "created": not file_existed,
        "content": content,
        "kind": "text",
        "llm_content": content,
    }


def replace_literal_text(
    file_path: str | Path,
    old_string: str,
    new_string: str,
    *,
    replace_all: bool = False,
    allow_missing_with_empty_old: bool = True,
) -> dict[str, Any]:
    target = Path(file_path)
    if target.exists() and target.is_dir():
        return {
            "ok": False,
            "code": "directory",
            "file_path": str(target),
            "error": f"Path is a directory, not a file: {target}",
        }

    if old_string == new_string:
        return {
            "ok": False,
            "code": "no_change",
            "file_path": str(target),
            "error": f"No changes to apply. The old_string and new_string are identical in file: {target}",
        }

    file_exists = target.exists()
    if not file_exists:
        if old_string == "" and allow_missing_with_empty_old:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(new_string, encoding="utf-8")
            return {
                "ok": True,
                "code": "created",
                "file_path": str(target),
                "file_existed": False,
                "created": True,
                "occurrences": 0,
                "content": new_string,
                "kind": "text",
                "llm_content": new_string,
            }
        return {
            "ok": False,
            "code": "not_found",
            "file_path": str(target),
            "error": f"File not found: {target}",
        }

    current_content = read_file_with_encoding(target)
    if old_string == "":
        return {
            "ok": False,
            "code": "already_exists",
            "file_path": str(target),
            "error": f"File already exists, cannot create: {target}",
        }

    occurrences = current_content.count(old_string)
    if occurrences == 0:
        return {
            "ok": False,
            "code": "no_occurrences",
            "file_path": str(target),
            "occurrences": 0,
            "error": f"Failed to edit, 0 occurrences found for old_string in {target}",
        }
    if not replace_all and occurrences != 1:
        return {
            "ok": False,
            "code": "multiple_occurrences",
            "file_path": str(target),
            "occurrences": occurrences,
            "error": f"Failed to edit. Found {occurrences} occurrences for old_string in {target}",
        }

    new_content = (
        current_content.replace(old_string, new_string)
        if replace_all
        else current_content.replace(old_string, new_string, 1)
    )
    if new_content == current_content:
        return {
            "ok": False,
            "code": "no_change",
            "file_path": str(target),
            "error": f"No changes to apply. The new content is identical to the current content in file: {target}",
        }

    _write_text_preserving_bom(target, new_content)
    return {
        "ok": True,
        "code": "replaced",
        "file_path": str(target),
        "file_existed": True,
        "created": False,
        "occurrences": occurrences,
        "content": new_content,
        "kind": "text",
        "llm_content": new_content,
    }


def apply_text_replacements(
    content: str,
    old: str,
    new: str,
    *,
    replace_all: bool = False,
) -> tuple[str, int]:
    """Apply a single text replacement in memory.

    Returns (new_content, replacement_count).
    """
    if not old:
        return content, 0
    if old == new:
        return content, 0
    count = content.count(old)
    if count == 0:
        return content, 0
    if replace_all:
        return content.replace(old, new), count
    return content.replace(old, new, 1), 1