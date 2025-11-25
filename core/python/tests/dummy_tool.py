"""
Dummy tool plugin for testing purposes.

This plugin provides a simple calculator tool.
Follows the state-based plugin protocol with explicit state dicts.
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class DummyCalculator:
    """
    Dummy calculator tool plugin (stateless with state parameter).
    Instance methods use the provided state parameter.
    """

    name: str = "dummy_calculator"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        """Return configuration schema."""
        return {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Return UI elements."""
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize tool state.

        Args:
            config: Configuration dictionary

        Returns:
            Initial state dictionary
        """
        return {"config": dict(config)}


    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return tool schemas."""
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
            }
        ]

    def execute_tool(
        self,
        tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tool."""
        if tool_name == "add":
            a = arguments.get("a", 0)
            b = arguments.get("b", 0)
            return {"success": True, "result": a + b}

        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Format tool result."""
        if result["success"]:
            return f"Result: {result['result']}"
        else:
            return f"Error: {result['error']}"
