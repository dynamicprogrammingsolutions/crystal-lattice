"""Tests for ShellArrayTool (array-based shell command)."""

from __future__ import annotations

import platform
import sys
from pathlib import Path

import pytest

from agent_core.plugin import ToolWrapper
from codex_tools.shell_tool import ShellArrayTool


class TestShellArrayToolSchemas:
    """Tests for tool schema definition."""

    def test_tool_name(self) -> None:
        """Tool name should be shell."""
        assert ShellArrayTool.name == "shell"

    def test_schema_has_array_command(self, tmp_path: Path) -> None:
        """Schema should define command as array type."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        schemas = wrapper.get_tool_schemas(state)
        
        assert len(schemas) == 1
        schema = schemas[0]
        assert schema["function"]["name"] == "shell"
        
        # Command should be array type
        command_prop = schema["function"]["parameters"]["properties"]["command"]
        assert command_prop["type"] == "array"
        assert "items" in command_prop
        assert command_prop["items"]["type"] == "string"

    def test_schema_has_workdir(self, tmp_path: Path) -> None:
        """Schema should include workdir parameter."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "workdir" in props
        assert props["workdir"]["type"] == "string"

    def test_schema_has_timeout_ms(self, tmp_path: Path) -> None:
        """Schema should include timeout_ms parameter."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "timeout_ms" in props
        assert props["timeout_ms"]["type"] == "number"

    def test_schema_no_login_param(self, tmp_path: Path) -> None:
        """Schema should NOT include login parameter (array commands specify shell directly)."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "login" not in props

    def test_command_is_required(self, tmp_path: Path) -> None:
        """Command should be in required fields."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        schemas = wrapper.get_tool_schemas(state)
        
        required = schemas[0]["function"]["parameters"]["required"]
        assert "command" in required


class TestShellArrayToolExecute:
    """Tests for tool execution."""

    @pytest.mark.asyncio
    async def test_basic_echo_array(self, tmp_path: Path) -> None:
        """Basic echo command with array should succeed."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell",
            {"command": ["echo", "hello"]},
            state,
        )
        
        assert result["success"] is True
        assert result["exit_code"] == 0
        assert "hello" in result["output"]

    @pytest.mark.asyncio
    async def test_bash_lc_wrapper(self, tmp_path: Path) -> None:
        """Command with bash -lc wrapper should work."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell",
            {"command": ["bash", "-lc", "echo hello from bash"]},
            state,
        )
        
        assert result["success"] is True
        assert "hello from bash" in result["output"]

    @pytest.mark.asyncio
    async def test_exit_code_zero_success(self, tmp_path: Path) -> None:
        """Exit code 0 should set success=True."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell",
            {"command": ["sh", "-c", "exit 0"]},
            state,
        )
        
        assert result["success"] is True
        assert result["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_exit_code_nonzero_failure(self, tmp_path: Path) -> None:
        """Non-zero exit code should set success=False."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell",
            {"command": ["sh", "-c", "exit 1"]},
            state,
        )
        
        assert result["success"] is False
        assert result["exit_code"] == 1

    @pytest.mark.asyncio
    async def test_stderr_capture(self, tmp_path: Path) -> None:
        """Stderr should be captured in output."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell",
            {"command": ["sh", "-c", "echo stderr_msg >&2"]},
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
        
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell",
            {"command": ["ls"], "workdir": str(subdir)},
            state,
        )
        
        assert result["success"] is True
        assert "test.txt" in result["output"]

    @pytest.mark.asyncio
    async def test_missing_workdir_uses_configured_turn_cwd(self, tmp_path: Path) -> None:
        """Missing workdir should fall back to the configured turn cwd."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({"working_directory": str(tmp_path)})

        result = await wrapper.execute_tool_async(
            "shell",
            {"command": [sys.executable, "-c", "import os; print(os.getcwd())"]},
            state,
        )

        assert result["success"] is True
        assert str(tmp_path) in result["output"]
        assert result["workdir"] == str(tmp_path)

    @pytest.mark.asyncio
    async def test_empty_workdir_uses_configured_turn_cwd(self, tmp_path: Path) -> None:
        """Empty-string workdir should fall back to the configured turn cwd."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({"working_directory": str(tmp_path)})

        result = await wrapper.execute_tool_async(
            "shell",
            {
                "command": [sys.executable, "-c", "import os; print(os.getcwd())"],
                "workdir": "",
            },
            state,
        )

        assert result["success"] is True
        assert str(tmp_path) in result["output"]
        assert result["workdir"] == str(tmp_path)

    @pytest.mark.asyncio
    async def test_relative_workdir_resolves_against_turn_cwd(self, tmp_path: Path) -> None:
        """Relative workdir should be normalized against the effective turn cwd."""
        base_dir = tmp_path / "workspace"
        subdir = base_dir / "nested"
        subdir.mkdir(parents=True)

        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({"working_directory": str(base_dir)})

        result = await wrapper.execute_tool_async(
            "shell",
            {
                "command": [sys.executable, "-c", "import os; print(os.getcwd())"],
                "workdir": "nested",
            },
            state,
        )

        assert result["success"] is True
        assert str(subdir) in result["output"]
        assert result["workdir"] == str(subdir)

    @pytest.mark.asyncio
    async def test_timeout(self, tmp_path: Path) -> None:
        """Timeout should kill long-running command."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell",
            {"command": ["sleep", "60"], "timeout_ms": 500},
            state,
        )
        
        assert result["success"] is False
        assert result["timed_out"] is True
        assert result["exit_code"] is None
        # Should complete much faster than 60 seconds
        assert result["duration_seconds"] < 5.0

    @pytest.mark.asyncio
    async def test_empty_array_error(self, tmp_path: Path) -> None:
        """Empty command array should return error."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell",
            {"command": []},
            state,
        )
        
        assert result["success"] is False
        assert "error" in result
        assert "empty" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_string_command_error(self, tmp_path: Path) -> None:
        """String command (instead of array) should return error."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell",
            {"command": "echo hello"},  # String instead of array
            state,
        )
        
        assert result["success"] is False
        assert "error" in result
        assert "array" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_invalid_tool_name_error(self, tmp_path: Path) -> None:
        """Invalid tool name should return error."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "wrong_tool",
            {"command": ["echo", "hello"]},
            state,
        )
        
        assert result["success"] is False
        assert "Unknown tool" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_command_not_found(self, tmp_path: Path) -> None:
        """Non-existent command should fail gracefully."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        # When the command doesn't exist, the subprocess should fail
        # On Unix, this typically results in exit code 127 or similar
        # The key thing is success should be False
        result = await wrapper.execute_tool_async(
            "shell",
            {"command": ["nonexistent_command_12345"]},
            state,
        )
        
        # Should fail (either FileNotFoundError caught or non-zero exit)
        assert result["success"] is False


class TestShellArrayToolFormatting:
    """Tests for output formatting."""

    @pytest.mark.asyncio
    async def test_output_has_exit_code(self, tmp_path: Path) -> None:
        """Output should include exit code line."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell",
            {"command": ["echo", "hello"]},
            state,
        )
        
        assert "Exit code: 0" in result["output"]

    @pytest.mark.asyncio
    async def test_output_has_wall_time(self, tmp_path: Path) -> None:
        """Output should include wall time line."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell",
            {"command": ["echo", "hello"]},
            state,
        )
        
        assert "Wall time:" in result["output"]
        assert "seconds" in result["output"]

    @pytest.mark.asyncio
    async def test_format_tool_result_returns_output(self, tmp_path: Path) -> None:
        """format_tool_result should return the output field."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell",
            {"command": ["echo", "hello"]},
            state,
        )
        
        formatted = wrapper.format_tool_result(result, state)
        assert formatted == result["output"]

    @pytest.mark.asyncio
    async def test_nonzero_exit_in_output(self, tmp_path: Path) -> None:
        """Non-zero exit code should be in output."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell",
            {"command": ["sh", "-c", "exit 42"]},
            state,
        )
        
        assert "Exit code: 42" in result["output"]


class TestShellArrayToolTruncation:
    """Tests for output truncation."""

    @pytest.mark.asyncio
    async def test_short_output_not_truncated(self, tmp_path: Path) -> None:
        """Short output should not be truncated."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        result = await wrapper.execute_tool_async(
            "shell",
            {"command": ["echo", "hello"]},
            state,
        )
        
        assert result["truncated"] is False
        assert "Total output lines" not in result["output"]

    @pytest.mark.asyncio
    async def test_long_output_truncated(self, tmp_path: Path) -> None:
        """Long output should be truncated at 10K tokens."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        # Generate a lot of output using bash
        result = await wrapper.execute_tool_async(
            "shell",
            {"command": ["bash", "-c", "for i in $(seq 1 5000); do echo \"Line $i with some padding text\"; done"]},
            state,
        )
        
        # Should be truncated
        assert result["truncated"] is True
        # Should have truncation info
        assert "Total output lines" in result["output"]


class TestShellArrayToolStreaming:
    """Tests for streaming output."""

    def test_streams_output(self, tmp_path: Path) -> None:
        """stream_tool should yield partial output chunks."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        chunks = list(wrapper.stream_tool(
            "shell",
            {"command": ["echo", "hello"]},
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
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        chunks = list(wrapper.stream_tool(
            "shell",
            {"command": ["sh", "-c", "exit 1"]},
            state,
        ))
        
        final_results = [c for c in chunks if isinstance(c, dict) and "success" in c]
        assert len(final_results) >= 1
        
        final = final_results[-1]
        assert final["success"] is False
        assert final["exit_code"] == 1


class TestShellArrayToolPreview:
    """Tests for tool call preview."""

    def test_preview_shows_command(self, tmp_path: Path) -> None:
        """Preview should show the command."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        preview = wrapper.format_tool_call_preview(
            "shell",
            {"command": ["echo", "hello", "world"]},
            state,
        )
        
        # Should show command elements
        assert "echo" in preview

    def test_preview_long_command_truncated(self, tmp_path: Path) -> None:
        """Preview should truncate long commands."""
        wrapper = ToolWrapper(ShellArrayTool)
        state = wrapper.init({})
        
        preview = wrapper.format_tool_call_preview(
            "shell",
            {"command": ["cmd1", "cmd2", "cmd3", "cmd4", "cmd5"]},
            state,
        )
        
        # Should show first few elements
        assert "cmd1" in preview