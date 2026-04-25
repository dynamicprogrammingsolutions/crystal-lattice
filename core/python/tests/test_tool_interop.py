from __future__ import annotations

import pytest

from agent_core.tool_interop import (
    DEFAULT_TOOL_INTEROP_REGISTRY,
    OpenAIChatToolCallAccessor,
    OpenAIChatToolSchemaAccessor,
    OpenAIChatToolSchemaToOpenAIResponsesToolSchema,
    OpenAIResponsesCustomToolCallAccessor,
    OpenAIResponsesCustomToolSchemaAccessor,
    OpenAIResponsesToolCallToOpenAIChatToolCall,
    ToolInteropRegistry,
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
    assert accessor.get_payload(call) == {"a": 2, "b": 3}

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
    # Arguments are parsed and re-serialized, so whitespace may differ
    assert out["id"] == "call_1"
    assert out["type"] == "function"
    assert out["function"]["name"] == "add"
    # Parse to compare semantically
    import json
    assert json.loads(out["function"]["arguments"]) == {"a": 2, "b": 3}

    event_wrapper = {"type": "response.output_item.added", "item": responses_call}
    assert adapter.can_handle(event_wrapper)
    out2 = adapter.convert(event_wrapper, target=ToolInteropTarget(name="openai.chat_completions"))
    assert out2 == out


def test_responses_custom_schema_and_call_are_inspected_and_passed_through() -> None:
    schema = {
        "type": "custom",
        "name": "apply_patch",
        "description": "Apply a freeform patch",
        "format": {
            "type": "grammar",
            "syntax": "lark",
            "definition": "start: /.+/",
        },
    }
    call = {
        "type": "custom_tool_call",
        "call_id": "call_patch_1",
        "name": "apply_patch",
        "input": "*** Begin Patch\n*** End Patch",
    }

    inspected_schema = DEFAULT_TOOL_INTEROP_REGISTRY.inspect_schema(schema)
    inspected_call = DEFAULT_TOOL_INTEROP_REGISTRY.inspect_call(call)

    assert inspected_schema.format_id == OpenAIResponsesCustomToolSchemaAccessor.format_id
    assert inspected_schema.tool_name == "apply_patch"
    assert inspected_call.format_id == OpenAIResponsesCustomToolCallAccessor.format_id
    assert inspected_call.tool_name == "apply_patch"
    assert inspected_call.payload == "*** Begin Patch\n*** End Patch"
    assert inspected_call.payload_kind == "text"

    converted = DEFAULT_TOOL_INTEROP_REGISTRY.convert_schemas(
        [schema],
        target=ToolInteropTarget(name="openai.responses"),
        target_formats=[OpenAIResponsesCustomToolSchemaAccessor.format_id],
    )
    assert converted == [schema]


def test_schema_conversion_can_use_multihop_adapter_chain() -> None:
    class FormatAAccessor:
        format_id = "test.a"
        format = format_id
        priority = 100

        def can_handle(self, schema):
            return isinstance(schema, dict) and schema.get("type") == "a"

        def get_tool_type(self, schema):
            return "custom"

        def get_tool_name(self, schema):
            return schema.get("name")

        def get_description(self, schema):
            return None

        def get_parameters_schema(self, schema):
            return None

        def get_tool_kind(self, schema):
            return "custom"

        def get_schema_format(self, schema):
            return self.format_id

    class AToB:
        source_format = "test.a"
        target_format = "test.b"
        priority = 100

        def can_handle(self, schema):
            return isinstance(schema, dict) and schema.get("type") == "a"

        def convert(self, schema, *, target):
            return {"type": "b", "name": schema["name"]}

    class BToC:
        source_format = "test.b"
        target_format = "test.c"
        priority = 100

        def can_handle(self, schema):
            return isinstance(schema, dict) and schema.get("type") == "b"

        def convert(self, schema, *, target):
            return {"type": "c", "name": schema["name"], "target": target.name}

    registry = ToolInteropRegistry(
        schema_accessors=[FormatAAccessor()],
        schema_adapters=[AToB(), BToC()],
    )

    converted = registry.convert_schemas(
        [{"type": "a", "name": "demo"}],
        target=ToolInteropTarget(name="multihop"),
        target_formats=["test.c"],
    )

    assert converted == [{"type": "c", "name": "demo", "target": "multihop"}]
