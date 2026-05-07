"""Unit test for AgentCore.execute_tool_calls using DummyCalculator tool."""

from agent_core import AgentCore
from agent_core.tool_result_payloads import (
    FORMAT_OPENAI_CHAT_COMPLETIONS,
    make_provider_native_tool_result,
)
from .dummy_tool import DummyCalculator
from plugins.file_reader_tool import FileReaderTool


class ExplodingTool:
    name = "exploding_tool"
    version = "1.0.0"

    def init(self, config):
        return {}

    def get_tool_schemas(self, state):
        return [
            {
                "type": "function",
                "function": {
                    "name": "explode",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

    def execute_tool(self, tool_name, arguments, state):
        raise RuntimeError("boom")

    def format_tool_result(self, result, state):
        return "unreachable"


class RawEchoTool:
    name = "raw_echo_tool"
    version = "1.0.0"

    def init(self, config):
        return {}

    def get_tool_schemas(self, state):
        return [
            {
                "type": "custom",
                "name": "raw_echo",
                "description": "Echo a raw text payload",
                "format": {
                    "type": "grammar",
                    "syntax": "lark",
                    "definition": "start: /.+/",
                },
            }
        ]

    def format_tool_call_preview(
        self,
        tool_name,
        payload,
        state,
        *,
        payload_kind=None,
        payload_format=None,
        payload_metadata=None,
        tool_call=None,
    ):
        return f"preview:{payload_kind}:{payload}"

    def execute_tool(
        self,
        tool_name,
        payload,
        state,
        *,
        payload_kind=None,
        payload_format=None,
        payload_metadata=None,
        tool_call=None,
    ):
        assert tool_name == "raw_echo"
        assert payload_kind == "text"
        return {"success": True, "result": str(payload).upper()}


class StructuredResultTool:
    name = "structured_result_tool"
    version = "1.0.0"

    def init(self, config):
        return {}

    def get_tool_schemas(self, state):
        return [
            {
                "type": "function",
                "function": {
                    "name": "structured",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

    def execute_tool(self, tool_name, arguments, state):
        return {"success": True}

    def format_tool_result(self, result, state):
        return make_provider_native_tool_result(
            format=FORMAT_OPENAI_CHAT_COMPLETIONS,
            content=[
                {"type": "text", "text": "<image>"},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/png;base64,QUJDRA=="},
                },
                {"type": "text", "text": "</image>"},
            ],
        )


def test_execute_tool_calls_with_dummy_tool():
    core = AgentCore()
    core.register_tool(DummyCalculator)

    tool_calls = [
        {
            "id": "call_1",
            "type": "function",
            "function": {"name": "add", "arguments": {"a": 2, "b": 3}},
        },
    ]

    results = core.execute_tool_calls(tool_calls, config={})
    assert results and isinstance(results, list)
    msg = results[0]
    assert msg.get("role") == "tool"
    md = msg.get("metadata", {})
    assert md.get("tool_call_id") == "call_1"
    assert md.get("tool_name") == "add"
    # ToolWrapper.name uses the plugin's ``name`` attribute when present.
    assert md.get("tool_plugin") == "dummy_calculator"
    display = md.get("display") or {}
    assert isinstance(display, dict)
    assert display.get("type") == "text"
    assert "Result: 5" in str(display.get("content", ""))
    assert "Result: 5" in msg.get("content", "")


def test_execute_tool_calls_preserves_provider_native_result_payload():
    core = AgentCore()
    core.register_tool(StructuredResultTool)

    results = core.execute_tool_calls(
        [
            {
                "id": "call_structured",
                "type": "function",
                "function": {"name": "structured", "arguments": {}},
            }
        ],
        config={},
    )

    assert len(results) == 1
    content = results[0].get("content")
    assert content["type"] == "provider_native_tool_result"
    assert content["format"] == FORMAT_OPENAI_CHAT_COMPLETIONS
    assert content["content"][1]["image_url"]["url"].startswith("data:image/png")
    display = (results[0].get("metadata") or {}).get("display") or {}
    assert display.get("type") == "text"
    assert display.get("content") == ""


def test_iter_tool_messages_non_streaming_file_reader(tmp_path):
    core = AgentCore()
    core.register_tool(FileReaderTool)

    config = {
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
    }

    path = tmp_path / "test.txt"
    path.write_text("hello", encoding="utf-8")

    tool_calls = [
        {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "read_file",
                "arguments": {"file_path": str(path)},
            },
        }
    ]

    items = list(core.iter_tool_messages(tool_calls, config))
    partials = [it for it in items if isinstance(it, dict) and "part" in it]
    finals = [it for it in items if isinstance(it, dict) and "part" not in it]

    assert not partials
    assert len(finals) == 1
    msg = finals[0]
    assert msg.get("role") == "tool"
    md = msg.get("metadata", {})
    assert md.get("tool_call_id") == "call_1"
    assert md.get("tool_name") == "read_file"
    assert md.get("tool_plugin") == "file_reader"
    display = md.get("display") or {}
    assert isinstance(display, dict)
    assert display.get("type") == "text"
    assert "File contents:" in str(msg.get("content", ""))


def test_iter_tool_messages_streaming_dummy_tool(tmp_path):
    core = AgentCore()
    core.register_tool(DummyCalculator)

    config = {
        "working_directory": str(tmp_path),
        "allowed_paths": [str(tmp_path)],
        "timeout_seconds": 10,
    }

    tool_calls = [
        {
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "add",
                "arguments": {"a": 2, "b": 3},
            },
        }
    ]

    items = list(core.iter_tool_messages(tool_calls, config))
    partials = [it for it in items if isinstance(it, dict) and "part" in it]
    finals = [it for it in items if isinstance(it, dict) and "part" not in it]

    assert partials, "expected at least one partial payload"
    assert len(finals) == 1
    msg = finals[0]
    assert msg.get("role") == "tool"
    md = msg.get("metadata", {})
    assert md.get("tool_call_id") == "call_1"
    assert md.get("tool_name") == "add"
    assert md.get("tool_plugin") == "dummy_calculator"
    display = md.get("display") or {}
    assert isinstance(display, dict)
    assert display.get("type") == "text"
    text = str(display.get("content", ""))
    assert "Result: 5" in text
    assert "Result: 5" in str(msg.get("content", ""))


def test_iter_tool_messages_turns_stream_exceptions_into_tool_errors(tmp_path):
    core = AgentCore()
    core.register_tool(ExplodingTool)

    tool_calls = [
        {
            "id": "call_1",
            "type": "function",
            "function": {"name": "explode", "arguments": {}},
        }
    ]

    items = list(core.iter_tool_messages(tool_calls, config={}))
    finals = [it for it in items if isinstance(it, dict) and "part" not in it]

    assert len(finals) == 1
    msg = finals[0]
    assert msg.get("role") == "tool"
    assert "Tool error: boom" in str(msg.get("content", ""))
    md = msg.get("metadata", {})
    assert md.get("tool_call_id") == "call_1"
    assert md.get("tool_name") == "explode"
    assert md.get("tool_plugin") == "exploding_tool"


def test_iter_tool_messages_executes_custom_raw_input_tool() -> None:
    core = AgentCore()
    core.register_tool(RawEchoTool)

    tool_calls = [
        {
            "type": "custom_tool_call",
            "call_id": "call_raw_1",
            "name": "raw_echo",
            "input": "hello raw tools",
        }
    ]

    items = list(core.iter_tool_messages(tool_calls, config={}))
    finals = [it for it in items if isinstance(it, dict) and "part" not in it]

    assert len(finals) == 1
    msg = finals[0]
    assert msg.get("role") == "tool"
    assert "HELLO RAW TOOLS" in str(msg.get("content", ""))
    md = msg.get("metadata", {})
    assert md.get("tool_call_id") == "call_raw_1"
    assert md.get("tool_name") == "raw_echo"
    assert md.get("tool_plugin") == "raw_echo_tool"


def test_tool_loop_previews_custom_raw_input_tool_calls() -> None:
    core = AgentCore()
    core.register_tool(RawEchoTool)

    previews = core.format_tool_call_previews(
        [
            {
                "type": "custom_tool_call",
                "call_id": "call_raw_1",
                "name": "raw_echo",
                "input": "hello preview",
            }
        ],
        {},
    )

    assert previews == [{"id": "call_raw_1", "preview": "preview:text:hello preview"}]
