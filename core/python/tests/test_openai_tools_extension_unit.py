from __future__ import annotations

from agent_core.tool_interop import (
    OpenAIChatToolCallAccessor,
    OpenAIChatToolSchemaAccessor,
    ToolInteropRegistry,
    ToolInteropTarget,
)
from plugins.openai_tools_extension import OpenAIToolsExtension


def test_openai_tools_extension_declares_chat_tool_formats() -> None:
    ext = OpenAIToolsExtension()
    assert ext.accepted_tool_schema_formats({}, None) == [OpenAIChatToolSchemaAccessor.format_id]
    assert ext.emitted_tool_call_formats({}, None) == [OpenAIChatToolCallAccessor.format_id]


class _SanitizingAccessor:
    format = "test.call"
    format_id = "test.call"
    priority = 0

    def can_handle(self, call):
        return isinstance(call, dict) and call.get("type") == "test_call"

    def get_call_id(self, call):
        return call.get("id")

    def get_tool_type(self, call):
        return str(call.get("type") or "")

    def get_tool_name(self, call):
        return call.get("name")

    def get_payload(self, call):
        return call.get("payload")

    def get_payload_kind(self, call):
        return "text"

    def get_payload_format(self, call):
        return None

    def get_payload_metadata(self, call):
        return {}

    def sanitize_call(self, call):
        return {**call, "payload": "sanitized"}


def test_openai_tools_extension_finalize_uses_context_registry() -> None:
    ext = OpenAIToolsExtension()
    registry = ToolInteropRegistry(call_accessors=[_SanitizingAccessor()])
    state = {
        "partial": {
            "tool_calls": [
                {"type": "test_call", "id": "call_1", "name": "test", "payload": "bad"}
            ]
        }
    }

    _finals, _native, new_state = ext.finalize(
        [],
        [],
        state,
        context={"tool_interop": {"registry": registry}},
    )

    assert new_state["partial"]["tool_calls"][0]["payload"] == "sanitized"


class _CustomSchemaAccessor:
    format = "test.custom.schema"
    format_id = "test.custom.schema"
    priority = 0

    def can_handle(self, schema):
        return isinstance(schema, dict) and schema.get("type") == "test_custom"

    def get_tool_type(self, schema):
        return str(schema.get("type") or "")

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


class _CustomSchemaAdapter:
    source_format = "test.custom.schema"
    target_format = "openai.chat_completions.function"
    priority = 0

    def can_handle(self, schema):
        return isinstance(schema, dict) and schema.get("type") == "test_custom"

    def convert(self, schema, *, target: ToolInteropTarget):
        return {
            "type": "function",
            "function": {"name": "converted", "description": target.name},
        }


def test_openai_tools_extension_initialize_request_uses_context_registry() -> None:
    ext = OpenAIToolsExtension()
    registry = ToolInteropRegistry(
        schema_accessors=[_CustomSchemaAccessor()],
        schema_adapters=[_CustomSchemaAdapter()],
    )
    state = {
        "_openai_tools": [{"type": "test_custom", "name": "apply_patch"}],
        "request": {"payload": {}},
        "config": {},
    }

    new_state = ext.initialize_request(
        [],
        state,
        context={
            "tool_interop": {
                "registry": registry,
                "schema_target_formats": ["openai.chat_completions.function"],
            }
        },
    )

    assert new_state["request"]["payload"]["tools"] == [
        {
            "type": "function",
            "function": {
                "name": "converted",
                "description": "openai.chat_completions",
            },
        }
    ]