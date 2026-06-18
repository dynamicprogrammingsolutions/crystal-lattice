from __future__ import annotations

from agent_core.tool_interop import ToolInteropRegistry, ToolInteropTarget

from reference_openai_compatible_provider.tools_extension import (
    OpenAICompatibleToolsExtension,
)


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


def test_initialize_request_uses_tool_interop_context_for_schema_conversion() -> None:
    ext = OpenAICompatibleToolsExtension()
    registry = ToolInteropRegistry(
        schema_accessors=[_CustomSchemaAccessor()],
        schema_adapters=[_CustomSchemaAdapter()],
    )
    state = {
        "_tools": [{"type": "test_custom", "name": "apply_patch"}],
        "request": {"payload": {}},
        "config": {},
    }

    _native, new_state = ext.initialize_request(
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


def test_finalize_uses_tool_interop_context_for_sanitization() -> None:
    ext = OpenAICompatibleToolsExtension()
    registry = ToolInteropRegistry(call_accessors=[_SanitizingAccessor()])
    state = {
        "accumulator": {
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

    assert new_state["accumulator"]["tool_calls"][0]["payload"] == "sanitized"
