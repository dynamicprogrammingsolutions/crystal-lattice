# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Track cross-tool Claude file activity within a request-like context."""

from __future__ import annotations

import os
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional, Set


_READ_PATHS_BY_CONTEXT: Dict[str, Set[str]] = {}
_LOCK = Lock()


def _context_key(
    *,
    context: Optional[Dict[str, Any]],
    state: Dict[str, Any],
) -> str:
    if isinstance(context, dict):
        request_id = context.get("request_id")
        if isinstance(request_id, str) and request_id:
            return f"request:{request_id}"
        session_id = context.get("session_id")
        if isinstance(session_id, str) and session_id:
            return f"session:{session_id}"
    working_directory = str(state.get("working_directory") or os.getcwd())
    return f"working_directory:{Path(working_directory).resolve()}"


def record_read_path(
    path: str | Path,
    *,
    context: Optional[Dict[str, Any]],
    state: Dict[str, Any],
) -> None:
    key = _context_key(context=context, state=state)
    normalized = str(Path(path).resolve())
    with _LOCK:
        paths = _READ_PATHS_BY_CONTEXT.setdefault(key, set())
        paths.add(normalized)


def has_read_path(
    path: str | Path,
    *,
    context: Optional[Dict[str, Any]],
    state: Dict[str, Any],
) -> bool:
    key = _context_key(context=context, state=state)
    normalized = str(Path(path).resolve())
    with _LOCK:
        return normalized in _READ_PATHS_BY_CONTEXT.get(key, set())


__all__ = ["has_read_path", "record_read_path"]