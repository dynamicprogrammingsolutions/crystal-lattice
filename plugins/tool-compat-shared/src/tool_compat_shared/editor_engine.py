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


def replace_edits(
    file_path: str | Path,
    *,
    edits: list[dict[str, Any]],
) -> dict[str, Any]:
    """Apply one or more text replacements to a file.

    Each edit is a dict with keys:
      - ``old`` (str): the string to find.
      - ``new`` (str): the replacement string.
      - ``replace_all`` (bool, default ``False``): replace every occurrence.
      - ``reject_ambiguous`` (bool, default ``True``): when ``False`` and
        ``replace_all`` is ``False``, silently replace only the first
        occurrence even if there are many.  When ``True``, return an error
        if more than one occurrence is found.

    The file is read once, all edits are applied sequentially to the in-memory
    content, and the result is compared to the original.  If nothing changed
    an error is returned.  Otherwise the file is written with BOM preserved.

    Returns a dict with ``ok``, ``code``, ``file_path``, ``occurrences``
    (total replacement count across all edits), ``edit_count``, ``content``,
    etc.
    """
    target = Path(file_path)

    if target.exists() and target.is_dir():
        return {
            "ok": False,
            "code": "directory",
            "file_path": str(target),
            "error": f"Path is a directory, not a file: {target}",
        }

    if not target.exists():
        return {
            "ok": False,
            "code": "not_found",
            "file_path": str(target),
            "error": f"File not found: {target}",
        }

    current_content = read_file_with_encoding(target)
    original_content = current_content
    total_replacements = 0

    for edit in edits:
        old = edit.get("old", "")
        new = edit.get("new", "")
        replace_all = bool(edit.get("replace_all", False))
        reject_ambiguous = bool(edit.get("reject_ambiguous", True))

        if old == new or not old:
            continue

        occurrences = current_content.count(old)
        if occurrences == 0:
            continue

        if reject_ambiguous and not replace_all and occurrences != 1:
            return {
                "ok": False,
                "code": "multiple_occurrences",
                "file_path": str(target),
                "occurrences": occurrences,
                "error": f"Failed to edit. Found {occurrences} occurrences for old_string in {target}",
            }

        current_content = (
            current_content.replace(old, new)
            if replace_all
            else current_content.replace(old, new, 1)
        )
        total_replacements += occurrences

    if current_content == original_content:
        return {
            "ok": False,
            "code": "no_occurrences",
            "file_path": str(target),
            "occurrences": 0,
            "error": f"Failed to edit, 0 occurrences found for old_string in {target}",
        }

    _write_text_preserving_bom(target, current_content)
    return {
        "ok": True,
        "code": "replaced",
        "file_path": str(target),
        "file_existed": True,
        "created": False,
        "occurrences": total_replacements,
        "edit_count": len(edits),
        "content": current_content,
        "kind": "text",
        "llm_content": current_content,
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

    if not target.exists():
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

    # For an existing file with empty old_string, cannot create
    if old_string == "":
        return {
            "ok": False,
            "code": "already_exists",
            "file_path": str(target),
            "error": f"File already exists, cannot create: {target}",
        }

    return replace_edits(
        file_path,
        edits=[{
            "old": old_string,
            "new": new_string,
            "replace_all": replace_all,
            # reject_ambiguous=True preserves the original single-match-only behavior
            "reject_ambiguous": True,
        }],
    )