"""
Unit tests for OpenRouterToolsExtension behavior (stateless functions tested via instance methods).
"""

from __future__ import annotations

import sys
import os

# Ensure repo root is importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from agent_core.tool_interop import OpenAIChatToolCallAccessor, OpenAIChatToolSchemaAccessor, ToolInteropRegistry, ToolInteropTarget  # noqa: E402
from openrouter_plugins.openrouter_tools_extension import OpenRouterToolsExtension as Ext  # noqa: E402


def test_extension_metadata():
    """Test extension metadata and tags."""
    ext = Ext()
    assert ext.name == "openrouter_tools"
    assert ext.version == "0.1.0"
    assert "ext:openrouter_tools" in ext.get_tags({}, [])
    assert "openrouter" in ext.required_tags()
    assert "supports_tools" in ext.required_tags()


def test_extension_declares_chat_tool_formats():
    ext = Ext()
    assert ext.accepted_tool_schema_formats({}, None) == [OpenAIChatToolSchemaAccessor.format_id]
    assert ext.emitted_tool_call_formats({}, None) == [OpenAIChatToolCallAccessor.format_id]


def test_init_stores_tools_in_state():
    """Test that init stores tools in state."""
    ext = Ext()
    config = {
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read a file",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]
    }
    state = ext.init(config, {})
    assert "_openrouter_tools" in state
    assert isinstance(state["_openrouter_tools"], list)
    assert len(state["_openrouter_tools"]) == 1


def test_initialize_request_adds_tools_to_payload():
    """Test that initialize_request adds tools to the request payload."""
    ext = Ext()
    tools = [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file",
                "parameters": {"type": "object", "properties": {}},
            },
        }
    ]
    state = {"_openrouter_tools": tools, "request": {"payload": {}}}
    new_state = ext.initialize_request([], state)
    payload = new_state["request"]["payload"]
    assert "tools" in payload
    assert payload["tools"] == tools
    assert payload["tool_choice"] == "auto"


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


def test_initialize_request_uses_context_registry_for_schema_conversion():
    ext = Ext()
    registry = ToolInteropRegistry(
        schema_accessors=[_CustomSchemaAccessor()],
        schema_adapters=[_CustomSchemaAdapter()],
    )
    state = {
        "_openrouter_tools": [{"type": "test_custom", "name": "apply_patch"}],
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


def test_to_native_messages_maps_tool_call_id_and_tool_calls():
    """Test that to_native_messages maps tool_call_id and tool_calls."""
    ext = Ext()
    messages = [
        {
            "role": "assistant",
            "content": "",
            "metadata": {
                "tool_calls": [
                    {
                        "id": "c1",
                        "type": "function",
                        "function": {"name": "read_file", "arguments": '{"file_path": "x"}'},
                    }
                ]
            },
        },
        {"role": "tool", "content": "ok", "metadata": {"tool_call_id": "abc"}},
    ]
    native = [
        {"role": "assistant", "content": ""},
        {"role": "tool", "content": "ok"},
    ]
    out = ext.to_native_messages(messages, native)
    assert (
        isinstance(out[0].get("tool_calls"), list)
        and (out[0]["tool_calls"][0].get("function") or {}).get("name") == "read_file"
    )
    assert out[1].get("tool_call_id") == "abc"


def test_from_native_messages_attaches_metadata_tool_calls():
    """Test that from_native_messages attaches tool_calls to metadata."""
    ext = Ext()
    messages = [{"role": "assistant", "content": ""}]
    native = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "x1",
                    "type": "function",
                    "function": {"name": "read_file", "arguments": '{"file_path": "baz.txt"}'},
                }
            ],
        }
    ]
    out = ext.from_native_messages(native, messages)
    md = out[0].get("metadata") or {}
    tcs = md.get("tool_calls") or []
    assert tcs and (tcs[0].get("function") or {}).get("name") == "read_file"
    import json as _json

    args_raw = (tcs[0].get("function") or {}).get("arguments")
    if isinstance(args_raw, str):
        args = _json.loads(args_raw)
    else:
        args = args_raw or {}
    assert args.get("file_path") == "baz.txt"



def test_finalize_is_noop():
    """Test that finalize is a no-op."""
    ext = Ext()
    finals, native, state = ext.finalize([], [], {})
    assert finals == [] and native == [] and state == {}


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


def test_finalize_uses_context_registry():
    ext = Ext()
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
