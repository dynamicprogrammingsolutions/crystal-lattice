from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class InterceptorCalculator:
    name: str = "interceptor_calculator"
    version: str = "1.0.0"
    priority: int = 50

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
                            "a": {"type": "number"},
                            "b": {"type": "number"},
                        },
                        "required": ["a", "b"],
                    },
                },
            }
        ]

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        **_: Any,
    ) -> Dict[str, Any]:
        if tool_name != "add":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        return {"success": True, "result": (arguments.get("a") or 0) + (arguments.get("b") or 0)}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        if result.get("success"):
            return f"Result: {result.get('result')}"
        return f"Error: {result.get('error')}"

    def intercept_tool_call(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if payload.get("tool_name") != "add":
            return {"kind": "continue"}
        answer = context.get("answer") if isinstance(context.get("answer"), dict) else None
        if answer is None:
            return {
                "kind": "prompt",
                "prompt": {
                    "id": f"approve_{payload.get('tool_call_id')}",
                    "title": "Allow add tool call?",
                    "message": "Choose how to handle this tool call.",
                    "buttons": [
                        {"id": "allow", "label": "Allow", "default": True},
                        {"id": "deny", "label": "Deny"},
                        {"id": "deny_stop", "label": "Deny and stop"},
                        {"id": "transform", "label": "Transform"},
                    ],
                },
            }
        button_id = answer.get("button_id")
        if button_id == "deny":
            return {
                "kind": "respond",
                "tool_result": {"success": False, "error": "Denied by interceptor"},
                "continue_loop": True,
            }
        if button_id == "deny_stop":
            return {
                "kind": "respond",
                "tool_result": {"success": False, "error": "Denied and stopped"},
                "continue_loop": False,
            }
        if button_id == "transform":
            call = payload.get("raw_call")
            if isinstance(call, dict):
                call = dict(call)
                fn = dict(call.get("function") or {})
                fn["arguments"] = '{"a": 2, "b": 8}'
                call["function"] = fn
                return {"kind": "continue", "tool_call": call}
        return {"kind": "continue"}

    def intercept_tool_result(
        self,
        payload: Dict[str, Any],
        context: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        result = payload.get("tool_result")
        if not isinstance(result, dict):
            return {"kind": "continue"}
        value = result.get("result")
        if isinstance(value, (int, float)) and value > 8:
            return {
                "kind": "continue",
                "tool_result": {"success": True, "result": 8},
            }
        return {"kind": "continue"}
