from __future__ import annotations

from typing import Any, Dict, List

from agent_core.types import ToolPlugin


class TemplateEchoTool(ToolPlugin):
    name = "template_echo_tool"
    version = "0.1.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "template_echo",
                    "description": "Echo back the provided value.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "string"},
                        },
                        "required": ["value"],
                    },
                },
            }
        ]

    def format_tool_call_preview(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> str:
        if tool_name != "template_echo":
            return ""
        value = arguments.get("value")
        return (
            f"template_echo value={value!r}"
            if isinstance(value, str)
            else "template_echo"
        )

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if tool_name != "template_echo":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        value = arguments.get("value")
        if not isinstance(value, str):
            return {"success": False, "error": "value must be a string"}
        return {"success": True, "result": value}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        if result.get("success") is True:
            return str(result.get("result") or "")
        return f"Error: {result.get('error')}"

    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {"type": "text", "content": text, "single_line": "template_echo"}


__all__ = ["TemplateEchoTool"]
