"""Tests for ShellCommandTool (string-based shell command)."""

from __future__ import annotations

import platform
from pathlib import Path

import pytest

from agent_core.plugin import ToolWrapper
from codex_tools.shell_command_tool import ShellCommandTool


class TestShellCommandToolSchemas:
    """Tests for tool schema definition."""

    def test_tool_name(self) -> None:
        """Tool name should be shell_command."""
        assert ShellCommandTool.name == "shell_command"

    def test_schema_has_string_command(self, tmp_path: Path) -> None:
        """Schema should define command as string type."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        schemas = wrapper.get_tool_schemas(state)
        
        assert len(schemas) == 1
        schema = schemas[0]
        assert schema["name"] == "shell_command"
        
        # Command should be string type
        command_prop = schema["parameters"]["properties"]["command"]
        assert command_prop["type"] == "string"

    def test_schema_has_workdir(self, tmp_path: Path) -> None:
        """Schema should include workdir parameter."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["parameters"]["properties"]
        assert "workdir" in props
        assert props["workdir"]["type"] == "string"

    def test_schema_has_timeout_ms(self, tmp_path: Path) -> None:
        """Schema should include timeout_ms parameter."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["parameters"]["properties"]
        assert "timeout_ms" in props
        assert props["timeout_ms"]["type"] == "number"

    def test_schema_has_login(self, tmp_path: Path) -> None:
        """Schema should include login parameter."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["parameters"]["properties"]
        assert "login" in props
        assert props["login"]["type"] == "boolean"

    def test_command_is_required(self, tmp_path: Path) -> None:
        """Command should be in required fields."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        schemas = wrapper.get_tool_schemas(state)
        
        required = schemas[0]["parameters"]["required"]
        assert "command" in required


class TestShellCommandToolExecute:
    """Tests for tool execution."""

    @pytest.mark.asyncio
    async def test_basic_echo(self, tmp_path: Path) -> None:
        """Basic echo command should succeed."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": "echo hello"},
            state,
        )
        
        assert result["success"] is True
        assert result["exit_code"] == 0
        assert "hello" in result["output"]
        assert "timed_out" not in result or result["timed_out"] is False

    @pytest.mark.asyncio
    async def test_exit_code_zero_success(self, tmp_path: Path) -> None:
        """Exit code 0 should set success=True."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": "exit 0"},
            state,
        )
        
        assert result["success"] is True
        assert result["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_exit_code_nonzero_failure(self, tmp_path: Path) -> None:
        """Non-zero exit code should set success=False."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": "exit 1"},
            state,
        )
        
        assert result["success"] is False
        assert result["exit_code"] == 1

    @pytest.mark.asyncio
    async def test_stderr_capture(self, tmp_path: Path) -> None:
        """Stderr should be captured in output."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": "echo stderr_msg >&2"},
            state,
        )
        
        assert result["success"] is True
        # Stderr should appear in combined output
        output = result["output"].lower()
        assert "stderr_msg" in output or "stderr" in output

    @pytest.mark.asyncio
    async def test_working_directory(self, tmp_path: Path) -> None:
        """Command should run in specified working directory."""
        # Create a subdirectory with a test file
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        test_file = subdir / "test.txt"
        test_file.write_text("content")
        
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": "ls", "workdir": str(subdir)},
            state,
        )
        
        assert result["success"] is True
        assert "test.txt" in result["output"]

    @pytest.mark.asyncio
    async def test_timeout(self, tmp_path: Path) -> None:
        """Timeout should kill long-running command."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": "sleep 60", "timeout_ms": 500},
            state,
        )
        
        assert result["success"] is False
        assert result["timed_out"] is True
        assert result["exit_code"] is None
        # Should complete much faster than 60 seconds
        assert result["duration_seconds"] < 5.0

    @pytest.mark.asyncio
    async def test_empty_command_error(self, tmp_path: Path) -> None:
        """Empty command should return error."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": ""},
            state,
        )
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_tool_name_error(self, tmp_path: Path) -> None:
        """Invalid tool name should return error."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "wrong_tool",
            {"command": "echo hello"},
            state,
        )
        
        assert result["success"] is False
        assert "Unknown tool" in result.get("error", "")


class TestShellCommandToolLogin:
    """Tests for login shell parameter."""

    @pytest.mark.asyncio
    async def test_login_default_true(self, tmp_path: Path) -> None:
        """Login should default to True."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        # When login is True (default), bash uses -lc
        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": "echo hello"},
            state,
        )
        
        assert result["success"] is True
        assert result.get("login", True) is True

    @pytest.mark.asyncio
    async def test_login_false(self, tmp_path: Path) -> None:
        """Login=False should use -c instead of -lc."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": "echo hello", "login": False},
            state,
        )
        
        assert result["success"] is True
        assert result.get("login") is False


class TestShellCommandToolFormatting:
    """Tests for output formatting."""

    @pytest.mark.asyncio
    async def test_output_has_exit_code(self, tmp_path: Path) -> None:
        """Output should include exit code line."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": "echo hello"},
            state,
        )
        
        assert "Exit code: 0" in result["output"]

    @pytest.mark.asyncio
    async def test_output_has_wall_time(self, tmp_path: Path) -> None:
        """Output should include wall time line."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": "echo hello"},
            state,
        )
        
        assert "Wall time:" in result["output"]
        assert "seconds" in result["output"]

    @pytest.mark.asyncio
    async def test_format_tool_result_returns_output(self, tmp_path: Path) -> None:
        """format_tool_result should return the output field."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": "echo hello"},
            state,
        )
        
        formatted = wrapper.format_tool_result(result, state)
        assert formatted == result["output"]

    @pytest.mark.asyncio
    async def test_nonzero_exit_in_output(self, tmp_path: Path) -> None:
        """Non-zero exit code should be in output."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": "exit 42"},
            state,
        )
        
        assert "Exit code: 42" in result["output"]


class TestShellCommandToolTruncation:
    """Tests for output truncation."""

    @pytest.mark.asyncio
    async def test_short_output_not_truncated(self, tmp_path: Path) -> None:
        """Short output should not be truncated."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": "echo hello"},
            state,
        )
        
        assert result["truncated"] is False
        assert "Total output lines" not in result["output"]

    @pytest.mark.asyncio
    async def test_long_output_truncated(self, tmp_path: Path) -> None:
        """Long output should be truncated at 10K tokens."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        # Generate a lot of output (more than 10K tokens ≈ 40K chars)
        # Each line is ~10 chars, so we need ~4000 lines
        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": "for i in $(seq 1 5000); do echo \"Line $i with some padding text\"; done"},
            state,
        )
        
        # Should be truncated
        assert result["truncated"] is True
        # Should have truncation info
        assert "Total output lines" in result["output"]


class TestShellCommandToolStreaming:
    """Tests for streaming output."""

    def test_streams_output(self, tmp_path: Path) -> None:
        """stream_tool should yield partial output chunks."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        chunks = list(wrapper.stream_tool(
            "shell_command",
            {"command": "echo hello"},
            state,
        ))
        
        # Should have at least one chunk and a final result
        assert len(chunks) >= 1
        
        # Find the final result (has 'success' key)
        final_results = [c for c in chunks if isinstance(c, dict) and "success" in c]
        assert len(final_results) >= 1
        
        final = final_results[-1]
        assert final["success"] is True
        assert "exit_code" in final

    def test_streams_exit_code(self, tmp_path: Path) -> None:
        """Streaming should include exit code in final result."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        chunks = list(wrapper.stream_tool(
            "shell_command",
            {"command": "exit 1"},
            state,
        ))
        
        final_results = [c for c in chunks if isinstance(c, dict) and "success" in c]
        assert len(final_results) >= 1
        
        final = final_results[-1]
        assert final["success"] is False
        assert final["exit_code"] == 1


class TestShellCommandToolPreview:
    """Tests for tool call preview."""

    def test_preview_shows_command(self, tmp_path: Path) -> None:
        """Preview should show the command."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        preview = wrapper.format_tool_call_preview(
            "shell_command",
            {"command": "echo hello world"},
            state,
        )
        
        assert "echo hello world" in preview

    def test_preview_multiline_shows_first_line(self, tmp_path: Path) -> None:
        """Preview should show only first line of multiline command."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        
        preview = wrapper.format_tool_call_preview(
            "shell_command",
            {"command": "echo hello\necho world"},
            state,
        )
        
        assert "echo hello" in preview
        assert "\n" not in preview or preview.count("\n") == 0