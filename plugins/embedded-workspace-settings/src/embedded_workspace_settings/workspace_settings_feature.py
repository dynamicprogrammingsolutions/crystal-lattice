from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent_core.types import FeaturePlugin


class EmbeddedWorkspaceSettingsFeature(FeaturePlugin):
    name = "embedded_workspace_settings"
    version = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "workspace_id": {
                "type": "string",
                "required": False,
                "description": "Opaque identifier of the selected workspace.",
            },
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
        _ = config
        return []

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        _ = config
        return state