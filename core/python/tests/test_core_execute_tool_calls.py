"""
Unit test for AgentCore.execute_tool_calls using DummyCalculator tool.
"""

from agent_core import AgentCore
from .dummy_tool import DummyCalculator


def test_execute_tool_calls_with_dummy_tool():
    core = AgentCore()
    core.register_tool(DummyCalculator)

    tool_calls = [
        {"id": "call_1", "name": "add", "arguments": {"a": 2, "b": 3}},
    ]

    results = core.execute_tool_calls(tool_calls, config={})
    assert results and isinstance(results, list)
    msg = results[0]
    assert msg.get("role") == "tool"
    assert msg.get("metadata", {}).get("tool_call_id") == "call_1"
    assert "Result: 5" in msg.get("content", "")
