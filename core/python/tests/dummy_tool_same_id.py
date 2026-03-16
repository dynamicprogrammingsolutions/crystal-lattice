"""Alternate dummy tool used to verify duplicate plugin-id precedence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class AlternateDummyCalculator:
    name: str = "dummy_calculator"
    version: str = "2.0.0"

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "add",
                    "description": "Alternate add implementation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number"},
                            "b": {"type": "number"},
                        },
                        "required": ["a", "b"],
                    },
                },
            }
        ]

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {"success": True, "result": "alternate"}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        return str(result.get("result") or "alternate")