"""
Math tools plugin: simple calculator tools for testing parallel and chained tool calls.
"""

from __future__ import annotations

from typing import Any, Dict, List

from agent_core.types import ToolPlugin


class MathTools(ToolPlugin):
    name: str = "math_tools"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "add",
                    "description": "Add two numbers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"},
                        },
                        "required": ["a", "b"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "multiply",
                    "description": "Multiply two numbers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"},
                        },
                        "required": ["a", "b"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "square",
                    "description": "Square a number (multiply it by itself)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number", "description": "Number to square"},
                        },
                        "required": ["x"],
                    },
                },
            },
        ]

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if tool_name == "add":
            a = arguments.get("a", 0)
            b = arguments.get("b", 0)
            result = a + b
            return {"success": True, "result": result}
        elif tool_name == "multiply":
            a = arguments.get("a", 0)
            b = arguments.get("b", 0)
            result = a * b
            return {"success": True, "result": result}
        elif tool_name == "square":
            x = arguments.get("x", 0)
            result = x * x
            return {"success": True, "result": result}
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        if result.get("success"):
            return str(result["result"])
        else:
            return f"Error: {result.get('error')}"
