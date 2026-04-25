"""Generic feature for request-time tool gating."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent_core.types import FeaturePlugin, ToolDescriptor


class ToolGatingFeature(FeaturePlugin):
    """Allow requests to suppress all tools through config/UI."""

    name = "tool_gating_feature"
    version = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "disable_all_tools": {
                "type": "boolean",
                "default": False,
                "description": "Hide all tool schemas from the outbound model request.",
            }
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        available_tools = (
            context.get("available_tools") if isinstance(context, dict) else []
        )
        tool_names = [
            descriptor.tool_name
            for descriptor in (available_tools or [])
            if isinstance(descriptor, ToolDescriptor) and descriptor.tool_name
        ]
        description = "Disable all tools for this request."
        if tool_names:
            description = (
                "Disable all tools for this request. Currently available: "
                + ", ".join(sorted(tool_names))
            )
        return [
            {
                "ui_type": "config",
                "type": "checkbox",
                "key": "disable_all_tools",
                "label": "Disable All Tools",
                "description": description,
            }
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return state

    def prepare_tools(
        self,
        config: Dict[str, Any],
        tools: List[ToolDescriptor],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ToolDescriptor]:
        if isinstance(config, dict) and config.get("disable_all_tools"):
            return []
        return list(tools)
