from __future__ import annotations

import pytest

from agent_core.tool_interop import (
    OpenAIChatToolCallAccessor,
    OpenAIChatToolSchemaAccessor,
    OpenAIChatToolSchemaToOpenAIResponsesToolSchema,
    OpenAIResponsesToolCallToOpenAIChatToolCall,
    ToolInteropError,
    ToolInteropTarget,
)


def test_openai_chat_tool_schema_accessor_strict() -> None:
    accessor = OpenAIChatToolSchemaAccessor()
    schema = {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file",
            "parameters": {"type": "object", "properties": {}},
        },
    }

    assert accessor.can_handle(schema)
    assert accessor.get_tool_type(schema) == "function"
    assert accessor.get_tool_name(schema) == "read_file"
    assert accessor.get_description(schema) == "Read a file"
    assert accessor.get_parameters_schema(schema) == {"type": "object", "properties": {}}

    assert not accessor.can_handle({"name": "read_file"})
    with pytest.raises(ToolInteropError):
        accessor.get_tool_name({"name": "read_file"})  # type: ignore[arg-type]


def test_openai_chat_tool_call_accessor_strict() -> None:
    accessor = OpenAIChatToolCallAccessor()
    call = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "add", "arguments": {"a": 2, "b": 3}},
    }
    assert accessor.can_handle(call)
    assert accessor.get_call_id(call) == "call_1"
    assert accessor.get_tool_type(call) == "function"
    assert accessor.get_tool_name(call) == "add"
    assert accessor.get_arguments(call) == {"a": 2, "b": 3}

    assert not accessor.can_handle({"id": "call_1", "name": "add"})
    with pytest.raises(ToolInteropError):
        accessor.get_tool_name({"id": "call_1"})  # type: ignore[arg-type]


def test_openai_chat_schema_to_responses_schema_adapter() -> None:
    adapter = OpenAIChatToolSchemaToOpenAIResponsesToolSchema()
    schema = {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file",
            "parameters": {"type": "object", "properties": {}},
        },
    }
    out = adapter.convert(schema, target=ToolInteropTarget(name="openai.responses"))
    assert out == {
        "type": "function",
        "name": "read_file",
        "description": "Read a file",
        "parameters": {"type": "object", "properties": {}},
    }


def test_openai_responses_call_to_openai_chat_tool_call_adapter() -> None:
    adapter = OpenAIResponsesToolCallToOpenAIChatToolCall()
    responses_call = {
        "type": "function_call",
        "call_id": "call_1",
        "name": "add",
        "arguments": "{\"a\":2,\"b\":3}",
    }
    assert adapter.can_handle(responses_call)
    out = adapter.convert(responses_call, target=ToolInteropTarget(name="openai.chat_completions"))
    assert out == {
        "id": "call_1",
        "type": "function",
        "function": {"name": "add", "arguments": "{\"a\":2,\"b\":3}"},
    }

    event_wrapper = {"type": "response.output_item.added", "item": responses_call}
    assert adapter.can_handle(event_wrapper)
    out2 = adapter.convert(event_wrapper, target=ToolInteropTarget(name="openai.chat_completions"))
    assert out2 == out
