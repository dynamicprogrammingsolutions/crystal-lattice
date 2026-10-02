"""
Dummy tool plugins for testing purposes.

These plugins provide a simple calculator plus a cancellable blocking tool used
by application-layer cancellation tests.
"""

import threading
from typing import Dict, Any, List
from dataclasses import dataclass


_finite_tool_entered = threading.Event()
_finite_tool_release = threading.Event()
_finite_tool_interrupted = threading.Event()
_finite_tool_call_count = 0


def reset_finite_blocking_tool_state() -> None:
    global _finite_tool_call_count
    _finite_tool_entered.clear()
    _finite_tool_release.clear()
    _finite_tool_interrupted.clear()
    _finite_tool_call_count = 0


def get_finite_blocking_tool_state() -> Dict[str, bool]:
    return {
        "entered": _finite_tool_entered.is_set(),
        "released": _finite_tool_release.is_set(),
        "interrupted": _finite_tool_interrupted.is_set(),
        "call_count": _finite_tool_call_count,
    }


def release_finite_blocking_tool() -> None:
    _finite_tool_release.set()


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


@dataclass
class FiniteBlockingTool:
    """Finite tool used to distinguish soft completion from hard interruption."""

    name: str = "finite_blocking_tool"
    version: str = "1.0.0"

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "finish_when_released",
                    "description": "Wait for the test to release the tool",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        if result.get("cancelled"):
            return "Cancelled"
        return str(result.get("result") or result.get("error") or "")

    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = tool_name, arguments, state
        return {"success": False, "error": "finite tool requires streaming"}

    def stream_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        *,
        cancellation: Any | None = None,
    ):
        global _finite_tool_call_count
        _ = arguments, state
        if tool_name != "finish_when_released":
            return
        _finite_tool_call_count += 1

        interrupted = threading.Event()
        cancel_token: int | None = None

        def _interrupt() -> None:
            _finite_tool_interrupted.set()
            interrupted.set()

        if cancellation is not None and hasattr(cancellation, "add_callback"):
            cancel_token = cancellation.add_callback(_interrupt)

        _finite_tool_entered.set()
        try:
            while not _finite_tool_release.wait(0.02):
                if interrupted.is_set():
                    yield {
                        "success": False,
                        "error": "Tool cancelled",
                        "cancelled": True,
                    }
                    return
            yield {"success": True, "result": "finished normally"}
        finally:
            if (
                cancellation is not None
                and cancel_token is not None
                and hasattr(cancellation, "remove_callback")
            ):
                cancellation.remove_callback(cancel_token)


@dataclass
class FailingPrepareTool:
    """Tool whose prepare hook fails before provider execution starts."""

    name: str = "failing_prepare_tool"
    version: str = "1.0.0"

    def prepare(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        _ = config, state, context
        raise RuntimeError("prepare exploded")

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return []

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        _ = tool_name, arguments, state
        return {"success": False, "error": "not implemented"}
