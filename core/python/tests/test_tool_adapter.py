"""
Unit tests for ToolWrapper and ToolAdapter.
"""

from agent_core.plugin import ToolWrapper, ToolAdapter
from .dummy_tool import DummyCalculator


def test_tool_adapter_execute_and_format():
    wrapper = ToolWrapper(DummyCalculator)
    adapter = ToolAdapter(wrapper)
    adapter.initialize({})

    schemas = adapter.get_tool_schemas()
    assert schemas and schemas[0]["function"]["name"] == "add"

    result = adapter.execute_tool("add", {"a": 2, "b": 3})
    assert result["success"] and result["result"] == 5
    formatted = adapter.format_tool_result(result)
    assert formatted == "Result: 5"
