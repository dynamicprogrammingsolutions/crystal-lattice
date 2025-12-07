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
