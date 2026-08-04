from __future__ import annotations

from agent_core.tool_interop import ToolInteropRegistry, ToolInteropTarget

from reference_openai_compatible_provider.provider import OpenAICompatibleProvider
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


def test_round_trip_preserves_display_and_namespaced_metadata_on_tool_messages() -> (
    None
):
    """``display`` and namespaced tool metadata (e.g. ``bash.end_cwd``) must
    survive a provider + tools-extension round-trip on tool-result messages.

    The provider pops ``display`` from the generic ``_metadata`` carry, so the
    tools extension must re-add it. Namespaced keys like ``bash.end_cwd`` are
    not in the provider's pop-list and ride through automatically."""
    provider = OpenAICompatibleProvider()
    state = provider.init({"model": "test-model"})
    ext = OpenAICompatibleToolsExtension()

    display_payload = {"type": "text", "content": "Bash command", "single_line": True}
    core_messages = [
        {
            "role": "assistant",
            "content": "",
            "metadata": {
                "tool_calls": [
                    {
                        "id": "call_bash_1",
                        "type": "function",
                        "function": {
                            "name": "Bash",
                            "arguments": '{"command":"pwd"}',
                        },
                    }
                ],
            },
        },
        {
            "role": "tool",
            "content": "/workspace",
            "metadata": {
                "tool_call_id": "call_bash_1",
                "tool_name": "Bash",
                "tool_plugin": "claude_bash_tool",
                "display": display_payload,
                "bash": {"end_cwd": "."},
            },
        },
    ]

    native_from_provider = provider.to_native_messages(core_messages, state)
    native_with_tools = ext.to_native_messages(core_messages, native_from_provider)

    tool_native = next(
        item
        for item in native_with_tools
        if isinstance(item, dict) and item.get("role") == "tool"
    )
    internal_md = tool_native.get("_metadata") or {}
    assert internal_md.get("display") == display_payload
    assert internal_md.get("tool_name") == "Bash"
    assert internal_md.get("tool_plugin") == "claude_bash_tool"
    assert internal_md.get("bash") == {"end_cwd": "."}

    core_from_provider = provider.from_native_messages(native_with_tools, state)
    rebuilt_core = ext.from_native_messages(native_with_tools, core_from_provider)

    tool_message = next(
        msg
        for msg in rebuilt_core
        if isinstance(msg, dict) and msg.get("role") == "tool"
    )
    metadata = tool_message.get("metadata") or {}
    assert metadata.get("tool_call_id") == "call_bash_1"
    assert metadata.get("display") == display_payload
    assert metadata.get("tool_name") == "Bash"
    assert metadata.get("tool_plugin") == "claude_bash_tool"
    assert metadata.get("bash") == {"end_cwd": "."}
