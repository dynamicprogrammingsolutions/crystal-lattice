"""
Tests for multi-interceptor ordering and priority handling.

Verifies that interceptors run in deterministic order based on
(priority asc, registration order) and that multiple interceptors
can coexist correctly.
"""
import json
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any

from agent_core.core import AgentCore
from agent_core.types import Session, Message
from agent_app.application_future import AgentApplication


class LowPriorityInterceptor:
    """Test interceptor with priority 50 (runs first)."""
    
    name = "low_priority_interceptor"
    priority = 50
    
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {}
    
    def get_tool_schemas(self, state: Dict[str, Any]) -> list:
        return [{
            "type": "function",
            "function": {
                "name": "multiply",
                "description": "Multiply two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number"},
                        "y": {"type": "number"},
                    },
                    "required": ["x", "y"],
                },
            },
        }]
    
    def execute_tool(
        self, name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if name == "multiply":
            x = arguments.get("x", 0)
            y = arguments.get("y", 0)
            return {"success": True, "result": x * y}
        return {"success": False, "error": "Unknown tool"}
    
    def format_tool_result(
        self, tool_result: Dict[str, Any], state: Dict[str, Any]
    ) -> str:
        if tool_result.get("success"):
            return f"Product: {tool_result['result']}"
        return f"Error: {tool_result.get('error', 'Unknown')}"
    
    def intercept_tool_call(
        self, payload: Dict[str, Any], context: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add metadata to track interception order."""
        # Just pass through but mark that we were called
        return {"kind": "continue", "metadata": {"intercepted_by_low": True}}
    
    def intercept_tool_result(
        self, payload: Dict[str, Any], context: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {"kind": "continue"}


class HighPriorityInterceptor:
    """Test interceptor with priority 150 (runs second)."""
    
    name = "high_priority_interceptor"
    priority = 150
    
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {}
    
    def get_tool_schemas(self, state: Dict[str, Any]) -> list:
        return []
    
    def execute_tool(
        self, name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {"success": False, "error": "Not implemented"}
    
    def format_tool_result(
        self, tool_result: Dict[str, Any], state: Dict[str, Any]
    ) -> str:
        return ""
    
    def intercept_tool_call(
        self, payload: Dict[str, Any], context: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify low-priority interceptor ran first, then add our marker."""
        metadata = payload.get("metadata", {})
        assert metadata.get("intercepted_by_low") is True, \
            "Low priority interceptor should have run first"
        return {"kind": "continue", "metadata": {"intercepted_by_high": True}}
    
    def intercept_tool_result(
        self, payload: Dict[str, Any], context: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {"kind": "continue"}


def test_interceptor_priority_ordering(tmp_path: Path) -> None:
    """Verify interceptors run in priority order (lower priority first)."""
    # Register both interceptors inline
    from tests.dummy_provider import DummyProvider
    
    config = {
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.test_interceptor_ordering.LowPriorityInterceptor",
            "tests.test_interceptor_ordering.HighPriorityInterceptor",
        ],
        "agents": {
            "default": {
                "provider": "dummy_provider",
                "model": "test",
                "tools": [
                    "tests.test_interceptor_ordering.LowPriorityInterceptor",
                    "tests.test_interceptor_ordering.HighPriorityInterceptor",
                ],
            }
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config, indent=2))
    
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    
    # Create session and trigger tool call
    core, base_config, session = app.create_session("default")
    tool_call: Dict[str, Any] = {
        "id": "call_order_test",
        "type": "function",
        "function": {"name": "multiply", "arguments": json.dumps({"x": 3, "y": 4})},
    }
    session = core.add_message(
        session, "assistant", "", {"tool_calls": [tool_call]}, config=base_config
    )
    app.save_session(session)
    
    # Send request - interceptors should run in order
    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    
    # If we reach here without assertion errors, priority ordering is correct
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert len(checkpoints) > 0


class EqualPriorityFirst:
    """Test interceptor with priority 100, registered first."""
    
    name = "equal_priority_first"
    priority = 100
    
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {}
    
    def get_tool_schemas(self, state: Dict[str, Any]) -> list:
        return [{
            "type": "function",
            "function": {
                "name": "concat",
                "description": "Concatenate strings",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "a": {"type": "string"},
                        "b": {"type": "string"},
                    },
                    "required": ["a", "b"],
                },
            },
        }]
    
    def execute_tool(
        self, name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if name == "concat":
            a = arguments.get("a", "")
            b = arguments.get("b", "")
            return {"success": True, "result": a + b}
        return {"success": False, "error": "Unknown tool"}
    
    def format_tool_result(
        self, tool_result: Dict[str, Any], state: Dict[str, Any]
    ) -> str:
        if tool_result.get("success"):
            return f"Result: {tool_result['result']}"
        return f"Error: {tool_result.get('error', 'Unknown')}"
    
    def intercept_tool_call(
        self, payload: Dict[str, Any], context: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {"kind": "continue", "metadata": {"order": ["first"]}}
    
    def intercept_tool_result(
        self, payload: Dict[str, Any], context: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {"kind": "continue"}


class EqualPrioritySecond:
    """Test interceptor with priority 100, registered second."""
    
    name = "equal_priority_second"
    priority = 100
    
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {}
    
    def get_tool_schemas(self, state: Dict[str, Any]) -> list:
        return []
    
    def execute_tool(
        self, name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {"success": False, "error": "Not implemented"}
    
    def format_tool_result(
        self, tool_result: Dict[str, Any], state: Dict[str, Any]
    ) -> str:
        return ""
    
    def intercept_tool_call(
        self, payload: Dict[str, Any], context: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Verify first interceptor ran, then append our marker."""
        metadata = payload.get("metadata", {})
        order = metadata.get("order", [])
        assert order == ["first"], f"Expected ['first'], got {order}"
        order.append("second")
        return {"kind": "continue", "metadata": {"order": order}}
    
    def intercept_tool_result(
        self, payload: Dict[str, Any], context: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {"kind": "continue"}


def test_interceptor_equal_priority_registration_order(tmp_path: Path) -> None:
    """Verify equal-priority interceptors run in registration order."""
    from tests.dummy_provider import DummyProvider
    
    config = {
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.test_interceptor_ordering.EqualPriorityFirst",
            "tests.test_interceptor_ordering.EqualPrioritySecond",
        ],
        "agents": {
            "default": {
                "provider": "dummy_provider",
                "model": "test",
                "tools": [
                    "tests.test_interceptor_ordering.EqualPriorityFirst",
                    "tests.test_interceptor_ordering.EqualPrioritySecond",
                ],
            }
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config, indent=2))
    
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    
    core, base_config, session = app.create_session("default")
    tool_call: Dict[str, Any] = {
        "id": "call_equal_priority",
        "type": "function",
        "function": {"name": "concat", "arguments": json.dumps({"a": "hello", "b": "world"})},
    }
    session = core.add_message(
        session, "assistant", "", {"tool_calls": [tool_call]}, config=base_config
    )
    app.save_session(session)
    
    # Send request - should complete without assertion errors
    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert len(checkpoints) > 0
