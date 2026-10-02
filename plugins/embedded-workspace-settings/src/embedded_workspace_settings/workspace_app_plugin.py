from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agent_app.application_future import AgentApplication


_SHARED_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,63}$")


def _workspace_root(config: Dict[str, Any]) -> Path:
    raw = config.get("workspace_root")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("workspace_root is required")
    return Path(raw).expanduser().resolve()


def _workspace_grants(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    raw = config.get("workspace_grants")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            raw = {}
    if not isinstance(raw, dict):
        return {}
    return {
        str(grant_id): dict(record)
        for grant_id, record in raw.items()
        if isinstance(grant_id, str) and isinstance(record, dict)
    }


def _workspace_id_for_internal_path(
    root: Path,
    session_id: str,
    path: Path,
) -> str:
    resolved = path.expanduser().resolve()
    private_root = root / ".sessions" / session_id
    try:
        private_relative = resolved.relative_to(private_root.resolve())
    except ValueError:
        private_relative = None
    if private_relative is not None:
        return f"private:{session_id}:{private_relative.as_posix()}"
    relative = resolved.relative_to(root)
    return "shared:root" if str(relative) == "." else f"shared:{relative.as_posix()}"


class EmbeddedWorkspaceAppPlugin:
    name = "embedded_workspace_app"
    version = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        _ = app_config
        return {}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "create_private_workspace",
                "label": "Use a new private workspace",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                },
            },
            {
                "id": "create_shared_workspace",
                "label": "New shared workspace",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "name": {"type": "string", "required": True},
                },
            },
            {
                "id": "select_external_workspace",
                "label": "Choose folder from Files",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "grant_id": {"type": "string", "required": True},
                },
            },
        ]

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = state
        if (context or {}).get("ui_context") != "session":
            return []
        effective = config if isinstance(config, dict) else {}
        session = (context or {}).get("session")
        if not isinstance(session, dict):
            return []
        session_id = str(session.get("session_id") or "")
        if not session_id:
            return []
        root = _workspace_root(effective)
        root.mkdir(parents=True, exist_ok=True)
        options = self._workspace_options(root, session_id, effective)
        metadata = session.get("metadata")
        overrides = metadata.get("overrides") if isinstance(metadata, dict) else {}
        selected_id = (
            overrides.get("workspace_id")
            if isinstance(overrides, dict)
            else None
        )
        if not isinstance(selected_id, str) or not selected_id:
            selected_path = (
                overrides.get("working_directory")
                if isinstance(overrides, dict)
                else None
            )
            if isinstance(selected_path, str) and selected_path:
                try:
                    selected_id = _workspace_id_for_internal_path(
                        root,
                        session_id,
                        Path(selected_path),
                    )
                except (ValueError, OSError):
                    selected_id = "shared:root"
            else:
                selected_id = "shared:root"
        selected_option = next(
            (option for option in options if option["value"] == selected_id),
            None,
        )
        external_action_id = (
            "restore_external_workspace"
            if isinstance(selected_option, dict)
            and selected_option.get("source") == "files"
            and selected_option.get("available") is False
            else "select_external_workspace"
        )
        external_action_label = (
            "Restore access…"
            if external_action_id == "restore_external_workspace"
            else "Choose folder from Files…"
        )
        return [
            {
                "ui_type": "config",
                "type": "workspace",
                "key": "workspace_id",
                "label": "Working directory",
                "description": (
                    "Choose the directory used for relative file operations in "
                    "this session."
                ),
                "default": selected_id,
                "options": options,
            },
            self._settings_action(
                "create_private_workspace",
                "Use a new private workspace",
                "lock",
                {"session_id": "$session.session_id"},
                order=1,
            ),
            {
                **self._settings_action(
                    "create_shared_workspace",
                    "New shared workspace…",
                    "folder-plus",
                    {
                        "session_id": "$session.session_id",
                        "name": "$dialog.name",
                    },
                    order=2,
                ),
                "dialog": {
                    "kind": "form",
                    "title": "New shared workspace",
                    "inputs": [
                        {
                            "name": "name",
                            "type": "string",
                            "label": "Name",
                            "required": True,
                        }
                    ],
                },
            },
            {
                **self._settings_action(
                    external_action_id,
                    external_action_label,
                    "folder",
                    {
                        "session_id": "$session.session_id",
                        "grant_id": "$client.workspace_grant_id",
                    },
                    order=3,
                    action_id="select_external_workspace",
                ),
                "client_input": {
                    "kind": "directory",
                    "input_name": "workspace_grant_id",
                    "access": "read_write",
                    "persistent": True,
                },
            },
        ]

    @staticmethod
    def _settings_action(
        element_id: str,
        label: str,
        icon: str,
        param_map: Dict[str, str],
        *,
        order: int,
        action_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "ui_type": "session_action",
            "id": element_id,
            "label": label,
            "icon": icon,
            "order": 3300 + order,
            "action_id": action_id or element_id,
            "action_owner": "application",
            "param_map": param_map,
            "dialog": {"kind": "none"},
            "rich_ui": {
                "kind": "button",
                "placements": ["session_settings"],
                "anchor_key": "workspace_id",
                "position": "after",
            },
        }

    @staticmethod
    def _workspace_options(
        root: Path,
        session_id: str,
        config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        options: List[Dict[str, Any]] = [
            {
                "value": "shared:root",
                "label": "Workspace root",
                "source": "shared",
                "available": True,
            }
        ]
        private_root = root / ".sessions" / session_id
        if private_root.is_dir():
            for child in sorted(private_root.iterdir(), key=lambda p: p.name.casefold()):
                if child.is_dir() and not child.is_symlink():
                    options.append(
                        {
                            "value": f"private:{session_id}:{child.name}",
                            "label": f"This session · {child.name[:6]}",
                            "source": "private",
                            "available": True,
                        }
                    )
        pending = [(root, 0)]
        while pending and len(options) < 200:
            parent, depth = pending.pop()
            if depth >= 8:
                continue
            try:
                children = sorted(
                    parent.iterdir(),
                    key=lambda path: path.name.casefold(),
                    reverse=True,
                )
            except OSError:
                continue
            for child in children:
                if (
                    child.name.startswith(".")
                    or not child.is_dir()
                    or child.is_symlink()
                ):
                    continue
                relative = child.relative_to(root).as_posix()
                options.append(
                    {
                        "value": f"shared:{relative}",
                        "label": relative,
                        "source": "shared",
                        "available": True,
                    }
                )
                pending.append((child, depth + 1))
                if len(options) >= 200:
                    break
        for grant_id, record in sorted(_workspace_grants(config).items()):
            options.append(
                {
                    "value": f"external:{grant_id}",
                    "label": str(record.get("display_name") or "Selected folder"),
                    "source": "files",
                    "available": record.get("available") is True,
                }
            )
        return options

    def execute_action(
        self,
        app: "AgentApplication",
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = context, state
        session_id = str(params.get("session_id") or "")
        loaded = app.load_session(session_id)
        if loaded is None:
            raise KeyError(f"Session {session_id!r} not found")
        _core, base_config, _session = loaded
        root = _workspace_root(base_config)

        if action_id == "create_private_workspace":
            token = uuid.uuid4().hex[:12]
            path = root / ".sessions" / session_id / token
            path.mkdir(parents=True, exist_ok=False)
            workspace_id = f"private:{session_id}:{token}"
        elif action_id == "create_shared_workspace":
            name = str(params.get("name") or "").strip()
            if not _SHARED_NAME.fullmatch(name) or name in {".", ".."}:
                raise ValueError("shared workspace name is invalid")
            path = root / name
            path.mkdir(parents=False, exist_ok=False)
            workspace_id = f"shared:{name}"
        elif action_id == "select_external_workspace":
            grant_id = str(params.get("grant_id") or "")
            record = _workspace_grants(base_config).get(grant_id)
            if not record or record.get("available") is not True:
                raise ValueError("selected Files folder is unavailable")
            workspace_id = f"external:{grant_id}"
        else:
            raise ValueError(f"Unknown action: {action_id}")

        app.patch_session_settings(
            session_id,
            {"workspace_id": workspace_id},
            source=f"action:{self.name}.{action_id}",
        )
        return {
            "message": "Working directory updated",
            "mutations": {"updated_session_ids": [session_id]},
            "ui_effects": {"reload_session_ids": [session_id]},
        }