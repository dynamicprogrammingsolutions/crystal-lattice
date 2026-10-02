from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from threading import Lock
from typing import Any


_MAX_CONTEXTS = 256
_READ_PATHS_BY_CONTEXT: OrderedDict[str, set[str]] = OrderedDict()
_LOCK = Lock()


def _context_key(
    *,
    context: dict[str, Any] | None,
    workspace_root: Path,
) -> str:
    if isinstance(context, dict):
        request_id = context.get("request_id")
        if isinstance(request_id, str) and request_id:
            return f"request:{request_id}"
        session_id = context.get("session_id")
        if isinstance(session_id, str) and session_id:
            return f"session:{session_id}"
    return f"workspace:{workspace_root.resolve()}"


def record_read_path(
    path: Path,
    *,
    context: dict[str, Any] | None,
    workspace_root: Path,
) -> None:
    key = _context_key(context=context, workspace_root=workspace_root)
    normalized = str(path.resolve())
    with _LOCK:
        paths = _READ_PATHS_BY_CONTEXT.setdefault(key, set())
        paths.add(normalized)
        _READ_PATHS_BY_CONTEXT.move_to_end(key)
        while len(_READ_PATHS_BY_CONTEXT) > _MAX_CONTEXTS:
            _READ_PATHS_BY_CONTEXT.popitem(last=False)


def has_read_path(
    path: Path,
    *,
    context: dict[str, Any] | None,
    workspace_root: Path,
) -> bool:
    key = _context_key(context=context, workspace_root=workspace_root)
    normalized = str(path.resolve())
    with _LOCK:
        paths = _READ_PATHS_BY_CONTEXT.get(key)
        if paths is None:
            return False
        _READ_PATHS_BY_CONTEXT.move_to_end(key)
        return normalized in paths