"""
Unit tests for ToolWrapper (adapters removed).
"""

from agent_core.plugin import ToolWrapper
from .dummy_tool import DummyCalculator


def test_tool_wrapper_execute_and_format():
    wrapper = ToolWrapper(DummyCalculator)
    state = wrapper.init({})

    schemas = wrapper.get_tool_schemas(state)
    assert schemas and schemas[0]["function"]["name"] == "add"

    result = wrapper.execute_tool("add", {"a": 2, "b": 3}, state)
    assert result["success"] and result["result"] == 5
    formatted = wrapper.format_tool_result(result, state)
    assert formatted == "Result: 5"
