"""
Dummy tool plugins for testing purposes.

These plugins provide a simple calculator plus a cancellable blocking tool used
by application-layer cancellation tests.
"""

import threading
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
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
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

    def stream_tool(
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ):
        """Streaming variant of the add tool used in tests.

        Emits a single partial display chunk followed by a final RESULT dict.
        """
        if tool_name != "add":
            return
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        try:
            result = a + b
        except Exception:
            yield {"success": False, "error": "invalid arguments"}
            return
        # Partial display payload
        yield {"part": {"type": "text", "content": f"partial: {result}"}}
        # Final RESULT dict
        yield {"success": True, "result": result}


@dataclass
class CancellableBlockingTool:
    """Blocking tool that exits only when the request cancellation fires."""

    name: str = "cancellable_blocking_tool"
    version: str = "1.0.0"

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "block_until_cancel",
                    "description": "Block until cancellation is requested",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "emit_partial": {
                                "type": "boolean",
                                "description": "Emit a partial message before blocking",
                            }
                        },
                    },
                },
            }
        ]

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if tool_name != "block_until_cancel":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        return {"success": False, "error": "blocking tool requires streaming"}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        if result.get("cancelled"):
            return "Cancelled"
        if result.get("success"):
            return str(result.get("result", ""))
        return f"Error: {result.get('error')}"

    def stream_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        *,
        cancellation: Any | None = None,
    ):
        if tool_name != "block_until_cancel":
            return

        cancelled = threading.Event()
        cancel_token: int | None = None

        def _request_cancel() -> None:
            cancelled.set()

        if cancellation is not None and hasattr(cancellation, "add_callback"):
            try:
                cancel_token = cancellation.add_callback(_request_cancel)
            except Exception:
                cancel_token = None

        try:
            if arguments.get("emit_partial"):
                yield {"part": {"type": "text", "content": "blocking partial"}}
            while not cancelled.wait(0.05):
                continue
            yield {"success": False, "error": "Tool cancelled", "cancelled": True}
        finally:
            if (
                cancellation is not None
                and cancel_token is not None
                and hasattr(cancellation, "remove_callback")
            ):
                try:
                    cancellation.remove_callback(cancel_token)
                except Exception:
                    pass

