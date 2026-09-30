from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent_core.types import FeaturePlugin
from embedded_tools_shared import (
    WorkspacePathError,
    resolve_workspace_boundaries,
    resolve_workspace_root,
)


_DEFAULT_MAX_DIRECTORY_OPTIONS = 200
_DEFAULT_MAX_DIRECTORY_DEPTH = 8


class EmbeddedWorkspaceSettingsFeature(FeaturePlugin):
    name = "embedded_workspace_settings"
    version = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "working_directory": {
                "type": "string",
                "required": True,
                "description": (
                    "Session working directory contained by the fixed workspace root."
                ),
            }
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = tags, models
        effective_config = config if isinstance(config, dict) else {}
        options = self._directory_options(effective_config)
        if not options:
            return []
        return [
            {
                "ui_type": "config",
                "type": "directory",
                "key": "working_directory",
                "label": "Working directory",
                "description": (
                    "Choose the directory used for relative file operations in "
                    "this session."
                ),
                "placeholder": "Select a workspace directory",
                "options": options,
            }
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        _ = config
        return state

    def _directory_options(self, config: Dict[str, Any]) -> List[Dict[str, str]]:
        boundaries = resolve_workspace_boundaries(config)
        if not boundaries:
            return []
        workspace_root = boundaries[0]
        workspace_root.mkdir(parents=True, exist_ok=True)
        workspace_root = workspace_root.resolve()

        try:
            selected = resolve_workspace_root(config)
        except WorkspacePathError:
            selected = workspace_root

        max_options = self._positive_int(
            config.get("workspace_directory_max_options"),
            _DEFAULT_MAX_DIRECTORY_OPTIONS,
        )
        max_depth = self._positive_int(
            config.get("workspace_directory_max_depth"),
            _DEFAULT_MAX_DIRECTORY_DEPTH,
        )

        directories = [workspace_root]
        pending = [(workspace_root, 0)]
        while pending and len(directories) < max_options:
            parent, depth = pending.pop()
            if depth >= max_depth:
                continue
            try:
                children = sorted(
                    (
                        child
                        for child in parent.iterdir()
                        if child.is_dir()
                        and not child.is_symlink()
                        and not child.name.startswith(".")
                    ),
                    key=lambda child: child.name.casefold(),
                    reverse=True,
                )
            except OSError:
                continue
            for child in children:
                resolved = child.resolve()
                try:
                    resolved.relative_to(workspace_root)
                except ValueError:
                    continue
                if resolved not in directories:
                    directories.append(resolved)
                    if len(directories) >= max_options:
                        break
                pending.append((resolved, depth + 1))

        if selected not in directories:
            directories.append(selected)

        root_option = {
            "value": str(workspace_root),
            "label": "Workspace root",
        }
        descendant_options = sorted(
            (
                {
                    "value": str(directory),
                    "label": directory.relative_to(workspace_root).as_posix(),
                }
                for directory in directories
                if directory != workspace_root
            ),
            key=lambda option: option["label"].casefold(),
        )
        return [root_option, *descendant_options]

    @staticmethod
    def _positive_int(raw: Any, default: int) -> int:
        if isinstance(raw, bool):
            return default
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return default
        return value if value > 0 else default