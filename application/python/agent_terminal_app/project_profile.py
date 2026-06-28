"""Per-project profile persistence for the Crystal Lattice CLI.

This module reads and writes per-project settings (name, port,
bridge-server-id) so the CLI can auto-configure without requiring the
user to repeat flags every run.

Settings are resolved with the following priority::

    CLI flag  >  .crystal/profile.json  >  ~/.crystal/projects.json  >  built-in default

Auto-generated or updated values are persisted to the user-level file
(``~/.crystal/projects.json``).  CLI-provided and local-override values
are never persisted — they are explicit choices for the current run.

If a profile file exists but contains invalid JSON, a clear
``RuntimeError`` is raised so the user can fix the file rather than
silently losing their settings.
"""

from __future__ import annotations

import json
import socket
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProjectProfile:
    """Resolved per-project settings."""

    name: str
    port: int
    bridge_server_id: str
    bridge_url: str | None = None


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _is_valid_port(value: Any) -> bool:
    """Return ``True`` when *value* is a positive int (not bool)."""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_valid_str(value: Any) -> bool:
    """Return ``True`` when *value* is a non-empty string."""
    return isinstance(value, str) and len(value) > 0


# ---------------------------------------------------------------------------
# Port helpers
# ---------------------------------------------------------------------------


def _find_free_port() -> int:
    """Bind to ``0.0.0.0:0``, read the OS-assigned port, and close the socket."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("0.0.0.0", 0))
        return sock.getsockname()[1]


def _try_bind(port: int) -> bool:
    """Attempt to bind to *port*; return ``True`` if the port is available."""
    if not _is_valid_port(port):
        return False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("0.0.0.0", port))
            return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Name disambiguation
# ---------------------------------------------------------------------------


def _generate_unique_name(project_dir: Path, existing_names: set[str]) -> str:
    """Generate a unique project name from the directory path.

    1. Start with the directory basename (e.g. ``iocharts``).
    2. If the name collides with an existing entry (from a different path),
       prepend the parent directory basename: ``frontend-iocharts``.
    3. Keep prepending parent names until no collision remains:
       ``dev-frontend-iocharts``.
    4. At the filesystem root (no more parents), append a numeric suffix:
       ``iocharts-2``.
    """
    candidate = project_dir.name
    if candidate not in existing_names:
        return candidate

    parent = project_dir.parent
    while candidate in existing_names:
        if parent == parent.parent:
            # Filesystem root — no more parents to prepend.
            break
        candidate = f"{parent.name}-{candidate}"
        parent = parent.parent

    if candidate not in existing_names:
        return candidate

    # Numeric-suffix fallback (project at root or all parents exhausted).
    base = project_dir.name
    suffix = 2
    while f"{base}-{suffix}" in existing_names:
        suffix += 1
    return f"{base}-{suffix}"


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------


def _load_user_file(path: Path) -> dict[str, Any]:
    """Read the user-level projects file.

    Returns ``{"projects": {}}`` when the file does not exist.  Raises
    ``RuntimeError`` with a clear message when the file exists but
    contains invalid JSON or a non-object top-level value.
    """
    if not path.is_file():
        return {"projects": {}}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(
            f"Could not read project profile file {path}: {exc}"
        ) from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Could not parse project profile file {path}: "
            f"invalid JSON at line {exc.lineno} column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(data, dict):
        raise RuntimeError(
            f"Project profile file {path} must contain a JSON object, "
            f"got {type(data).__name__}"
        )
    return data


def _save_user_file(path: Path, data: dict[str, Any]) -> None:
    """Write the user-level projects file as pretty-printed JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")


def _load_local_override(path: Path) -> dict[str, Any]:
    """Read the project-local override file.

    Returns ``{}`` when the file does not exist.  Raises ``RuntimeError``
    with a clear message when the file exists but contains invalid JSON
    or a non-object top-level value.
    """
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(
            f"Could not read project profile override {path}: {exc}"
        ) from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Could not parse project profile override {path}: "
            f"invalid JSON at line {exc.lineno} column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(data, dict):
        raise RuntimeError(
            f"Project profile override {path} must contain a JSON object, "
            f"got {type(data).__name__}"
        )
    return data


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------


class ProjectProfileManager:
    """Reads, resolves, and persists per-project settings.

    The manager is constructed with the user-level file path
    (``~/.crystal/projects.json``) and the project directory.  The
    local override file defaults to ``<project_dir>/.crystal/profile.json``
    but can be overridden for testing.
    """

    def __init__(
        self,
        *,
        user_file: Path,
        project_dir: Path,
        local_override_file: Path | None = None,
    ) -> None:
        self._user_file = user_file
        self._project_dir = project_dir.resolve()
        self._local_override_file = (
            local_override_file
            if local_override_file is not None
            else self._project_dir / ".crystal" / "profile.json"
        )

    def resolve(
        self,
        *,
        cli_name: str | None = None,
        cli_port: int | None = None,
        cli_bridge_server_id: str | None = None,
        cli_bridge_url: str | None = None,
    ) -> ProjectProfile:
        """Resolve all settings and persist auto-generated/updated values.

        Each setting follows the priority::

            CLI flag > local override > user-level entry > built-in default

        Only values that were **not** provided by CLI or local override
        are persisted to the user-level file.

        ``bridge_url`` is never auto-generated or persisted — it is a
        user-provided configuration value.  When no source provides it,
        the resolved ``bridge_url`` is ``None``.
        """
        user_data = _load_user_file(self._user_file)
        projects = user_data.get("projects")
        if not isinstance(projects, dict):
            projects = {}
        entry = projects.get(str(self._project_dir))
        if not isinstance(entry, dict):
            entry = {}

        local_override = _load_local_override(self._local_override_file)

        # Collect existing names from other projects for disambiguation.
        existing_names: set[str] = set()
        for other_path, other_entry in projects.items():
            if other_path == str(self._project_dir):
                continue
            if isinstance(other_entry, dict) and _is_valid_str(other_entry.get("name")):
                existing_names.add(other_entry["name"])

        # --- Resolve name ---
        if cli_name is not None:
            name = cli_name
            persist_name = False
        elif _is_valid_str(local_override.get("name")):
            name = local_override["name"]
            persist_name = False
        elif _is_valid_str(entry.get("name")):
            name = entry["name"]
            persist_name = False
        else:
            name = _generate_unique_name(self._project_dir, existing_names)
            persist_name = True

        # --- Resolve bridge_server_id ---
        if cli_bridge_server_id is not None:
            bridge_server_id = cli_bridge_server_id
            persist_bridge_id = False
        elif _is_valid_str(local_override.get("bridge_server_id")):
            bridge_server_id = local_override["bridge_server_id"]
            persist_bridge_id = False
        elif _is_valid_str(entry.get("bridge_server_id")):
            bridge_server_id = entry["bridge_server_id"]
            persist_bridge_id = False
        else:
            bridge_server_id = str(uuid.uuid4())
            persist_bridge_id = True

        # --- Resolve port ---
        if cli_port is not None:
            port = cli_port
            persist_port = False
        elif _is_valid_port(local_override.get("port")):
            port = local_override["port"]
            if _try_bind(port):
                persist_port = False
            else:
                port = _find_free_port()
                persist_port = False
        elif _is_valid_port(entry.get("port")):
            port = entry["port"]
            if _try_bind(port):
                persist_port = False
            else:
                port = _find_free_port()
                persist_port = True
        else:
            port = _find_free_port()
            persist_port = True

        # --- Resolve bridge_url (never auto-generated, never persisted) ---
        if cli_bridge_url is not None:
            bridge_url: str | None = cli_bridge_url
        elif _is_valid_str(local_override.get("bridge_url")):
            bridge_url = local_override["bridge_url"]
        elif _is_valid_str(entry.get("bridge_url")):
            bridge_url = entry["bridge_url"]
        else:
            bridge_url = None

        # --- Persist changes to user-level file ---
        if persist_name or persist_port or persist_bridge_id:
            if not isinstance(user_data.get("projects"), dict):
                user_data["projects"] = {}
            projects = user_data["projects"]
            entry = projects.get(str(self._project_dir))
            if not isinstance(entry, dict):
                entry = {}
            if persist_name:
                entry["name"] = name
            if persist_port:
                entry["port"] = port
            if persist_bridge_id:
                entry["bridge_server_id"] = bridge_server_id
            projects[str(self._project_dir)] = entry
            _save_user_file(self._user_file, user_data)

        return ProjectProfile(
            name=name,
            port=port,
            bridge_server_id=bridge_server_id,
            bridge_url=bridge_url,
        )
