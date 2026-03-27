"""Tests for GrokShellTool."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_core.plugin import ToolWrapper
from grok_tools.grok_shell_tool import GrokShellTool


class TestGrokShellToolSchemas:
    """Tests for tool schema definition."""

    def test_tool_name(self) -> None:
        """Tool name should be grok_shell_tool."""
        assert GrokShellTool.name == "grok_shell_tool"

    def test_schema_tool_name_is_bash(self, tmp_path: Path) -> None:
        """Schema tool name should be bash."""
        wrapper = ToolWrapper(GrokShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        assert len(schemas) == 1
        schema = schemas[0]
        assert schema["function"]["name"] == "bash"

    def test_schema_has_string_command(self, tmp_path: Path) -> None:
        """Schema should define command as string type."""
        wrapper = ToolWrapper(GrokShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert props["command"]["type"] == "string"

    def test_schema_minimal(self, tmp_path: Path) -> None:
        """Schema should be minimal - only command parameter."""
        wrapper = ToolWrapper(GrokShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        # Grok only has command - no timeout, workdir, background
        assert set(props.keys()) == {"command"}

    def test_command_is_required(self, tmp_path: Path) -> None:
        """Command should be in required fields."""
        wrapper = ToolWrapper(GrokShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        required = schemas[0]["function"]["parameters"]["required"]
        assert required == ["command"]


class TestGrokShellToolExecute:
    """Tests for tool execution."""

    @pytest.mark.asyncio
    async def test_basic_echo(self, tmp_path: Path) -> None:
        """Basic echo command should succeed."""
        wrapper = ToolWrapper(GrokShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "echo hello"},
            state,
        )
        
        assert result["success"] is True
        assert result["exit_code"] == 0
        assert "hello" in result["output"]

    @pytest.mark.asyncio
    async def test_exit_code_zero_success(self, tmp_path: Path) -> None:
        """Exit code 0 should set success=True."""
        wrapper = ToolWrapper(GrokShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "exit 0"},
            state,
        )
        
        assert result["success"] is True
        assert result["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_exit_code_nonzero_failure(self, tmp_path: Path) -> None:
        """Non-zero exit code should set success=False."""
        wrapper = ToolWrapper(GrokShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "exit 1"},
            state,
        )
        
        assert result["success"] is False
        assert result["exit_code"] == 1

    @pytest.mark.asyncio
    async def test_stderr_capture(self, tmp_path: Path) -> None:
        """Stderr should be captured in output."""
        wrapper = ToolWrapper(GrokShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "echo stderr_msg >&2"},
            state,
        )
        
        # Grok returns raw output including stderr
        assert "stderr_msg" in result["output"]

    @pytest.mark.asyncio
    async def test_empty_command_error(self, tmp_path: Path) -> None:
        """Empty command should return error."""
        wrapper = ToolWrapper(GrokShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": ""},
            state,
        )
        
        assert result["success"] is False
        assert "error" in result


class TestGrokShellToolFormatting:
    """Tests for output formatting."""

    @pytest.mark.asyncio
    async def test_raw_output_no_formatting(self, tmp_path: Path) -> None:
        """Output should be raw - no special formatting."""
        wrapper = ToolWrapper(GrokShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "echo hello"},
            state,
        )
        
        # Grok returns raw output without prefixes
        assert result["output"].strip() == "hello"

    @pytest.mark.asyncio
    async def test_no_truncation(self, tmp_path: Path) -> None:
        """Grok should not truncate output."""
        wrapper = ToolWrapper(GrokShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        # Generate a lot of output
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "for i in $(seq 1 5000); do echo \"Line $i\"; done"},
            state,
        )
        
        # Should NOT have truncated key
        assert "truncated" not in result or result.get("truncated") is False


class TestGrokShellToolNoExtraFeatures:
    """Tests that Grok lacks features other vendors have."""

    @pytest.mark.asyncio
    async def test_no_timeout_support(self, tmp_path: Path) -> None:
        """Grok should not support timeout parameter."""
        wrapper = ToolWrapper(GrokShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        # Grok schema doesn't have timeout, so this would be ignored
        schemas = wrapper.get_tool_schemas(state)
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "timeout" not in props

    def test_no_background_support(self, tmp_path: Path) -> None:
        """Grok should not support is_background parameter."""
        wrapper = ToolWrapper(GrokShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        schemas = wrapper.get_tool_schemas(state)
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "is_background" not in props

    def test_no_workdir_support(self, tmp_path: Path) -> None:
        """Grok should not support working directory parameter."""
        wrapper = ToolWrapper(GrokShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        schemas = wrapper.get_tool_schemas(state)
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "directory" not in props
        assert "dir_path" not in props


class TestGrokShellToolConfig:
    """Tests for config handling."""

    def test_project_temp_dir_default(self, tmp_path: Path) -> None:
        """project_temp_dir should default to <working_directory>/.temp."""
        wrapper = ToolWrapper(GrokShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        expected = str(tmp_path / ".temp")
        assert state["project_temp_dir"] == expected


class TestGrokShellToolPreview:
    """Tests for tool call preview."""

    def test_preview_shows_command(self, tmp_path: Path) -> None:
        """Preview should show the command."""
        wrapper = ToolWrapper(GrokShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        preview = wrapper.format_tool_call_preview(
            "bash",
            {"command": "echo hello world"},
            state,
        )
        
        assert "echo hello world" in preview