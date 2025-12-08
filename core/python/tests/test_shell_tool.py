"""Unit tests for ShellTool plugin."""

from agent_core.plugin import ToolWrapper
from plugins.shell_tool import ShellTool


def test_shell_tool_runs_basic_command(tmp_path):
    wrapper = ToolWrapper(ShellTool)
    state = wrapper.init({"working_directory": str(tmp_path)})

    schemas = wrapper.get_tool_schemas(state)
    assert schemas and schemas[0]["function"]["name"] == "shell"

    # Run a very simple, fast command
    result = wrapper.execute_tool(
        "shell",
        {"command": "echo 'hello from shell'", "workdir": str(tmp_path)},
        state,
    )

    assert result["success"] is True
    assert "hello from shell" in result.get("stdout", "")

    formatted = wrapper.format_tool_result(result, state)
    assert "Command succeeded" in formatted
    assert "STDOUT:" in formatted


def test_shell_tool_streams_stdout(tmp_path):
    wrapper = ToolWrapper(ShellTool)
    state = wrapper.init({"working_directory": str(tmp_path)})

    chunks = list(
        wrapper.stream_tool(
            "shell",
            {"command": "printf 'a\\n'", "workdir": str(tmp_path)},
            state,
        )
    )

    assert chunks, "expected at least one streamed chunk"
    partials = [
        p
        for c in chunks
        if isinstance(c, dict)
        for p in [c.get("part")]
        if isinstance(p, dict)
    ]
    assert partials, "expected at least one streamed partial payload"
    assert any(p.get("type") == "text" for p in partials)
    assert any("a" in str(p.get("content", "")) for p in partials)
    # Final RESULT dict should also be present
    assert any(isinstance(c, dict) and "success" in c for c in chunks)
