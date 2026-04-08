"""
Unit tests for ToolWrapper (adapters removed).
"""

import asyncio

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


def test_tool_wrapper_prepare_and_async_execute_helpers() -> None:
    class PreparedAsyncTool:
        name = "prepared_async_tool"
        version = "1.0.0"

        def init(self, config):
            return {"config": config}

        def prepare(self, config, state, *, context=None):
            return {"suffix": "prepared"}

        def get_tool_schemas(self, state, *, prepared=None):
            return []

        async def execute_tool_async(
            self,
            tool_name,
            payload,
            state,
            *,
            prepared=None,
            **_kwargs,
        ):
            return {
                "success": True,
                "result": f"{tool_name}:{payload['value']}:{prepared['suffix']}",
            }

    class LegacyAwaitableTool:
        name = "legacy_awaitable_tool"
        version = "1.0.0"

        def init(self, config):
            return {"config": config}

        async def execute_tool(self, tool_name, payload, state, *, prepared=None, **_kwargs):
            return {
                "success": True,
                "result": f"{tool_name}:{payload['value']}:{prepared['suffix']}",
            }

    wrapper = ToolWrapper(PreparedAsyncTool)
    state = wrapper.init({})
    prepared = wrapper.prepare({}, state)
    result = asyncio.run(
        wrapper.execute_tool_async(
            "echo",
            {"value": "hello"},
            state,
            prepared=prepared,
        )
    )
    assert result == {"success": True, "result": "echo:hello:prepared"}

    legacy_wrapper = ToolWrapper(LegacyAwaitableTool)
    legacy_state = legacy_wrapper.init({})
    legacy_result = asyncio.run(
        legacy_wrapper.execute_tool_async(
            "echo",
            {"value": "hello"},
            legacy_state,
            prepared={"suffix": "legacy"},
        )
    )
    assert legacy_result == {"success": True, "result": "echo:hello:legacy"}
