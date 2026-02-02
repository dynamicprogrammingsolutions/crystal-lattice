"""Extra ToolPlugin used in tests to validate descriptor precedence.

When a package is loaded via module-only discovery without an
``agent_plugin.json`` descriptor, discovery should find this tool.

When a descriptor is present and lists only FileReaderTool and FileWriterTool,
this tool should not be loaded.
"""

from __future__ import annotations

from typing import Any, Dict, List

from agent_core.types import ToolPlugin


class ExtraTool(ToolPlugin):
    name: str = "extra_tool"
    version: str = "0.0.1"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "extra_tool",
                    "description": "Extra tool used for descriptor precedence tests",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if tool_name != "extra_tool":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        return {"success": True, "result": "ok"}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return str(result)
