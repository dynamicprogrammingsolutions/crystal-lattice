"""
Unit test for AgentCore.execute_tool_calls using DummyCalculator tool.
"""

from agent_core import AgentCore
from .dummy_tool import DummyCalculator
from plugins.file_reader_tool import FileReaderTool


def test_execute_tool_calls_with_dummy_tool():
    core = AgentCore()
    core.register_tool(DummyCalculator)

    tool_calls = [
        {"id": "call_1", "name": "add", "arguments": {"a": 2, "b": 3}},
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
