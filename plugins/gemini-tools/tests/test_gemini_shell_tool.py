"""Tests for GeminiShellTool."""

from __future__ import annotations

from pathlib import Path
import threading
import time

import pytest

from agent_core.plugin import ToolWrapper
from gemini_tools.gemini_shell_tool import GeminiShellTool


class _TestCancellation:
    def __init__(self) -> None:
        self._callback = None

    def add_callback(self, callback):
        self._callback = callback
        return 1

    def remove_callback(self, token: int) -> None:
        self._callback = None

    def cancel(self) -> None:
        if self._callback is not None:
            self._callback()


class TestGeminiShellToolSchemas:
    """Tests for tool schema definition."""

    def test_tool_name(self) -> None:
        """Tool name should be gemini_shell_tool."""
        assert GeminiShellTool.name == "gemini_shell_tool"

    def test_schema_tool_name_is_run_shell_command(self, tmp_path: Path) -> None:
        """Schema tool name should be run_shell_command."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        assert len(schemas) == 1
        schema = schemas[0]
        assert schema["function"]["name"] == "run_shell_command"

    def test_schema_has_string_command(self, tmp_path: Path) -> None:
        """Schema should define command as string type."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert props["command"]["type"] == "string"

    def test_schema_has_dir_path(self, tmp_path: Path) -> None:
        """Schema should include dir_path parameter."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "dir_path" in props
        assert props["dir_path"]["type"] == "string"

    def test_schema_has_description(self, tmp_path: Path) -> None:
        """Schema should include description parameter."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "description" in props
        assert props["description"]["type"] == "string"

    def test_schema_has_is_background(self, tmp_path: Path) -> None:
        """Schema should include is_background parameter."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "is_background" in props
        assert props["is_background"]["type"] == "boolean"

    def test_command_is_required(self, tmp_path: Path) -> None:
        """Command should be in required fields."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        required = schemas[0]["function"]["parameters"]["required"]
        assert "command" in required


class TestGeminiShellToolExecute:
    """Tests for tool execution."""

    @pytest.mark.asyncio
    async def test_basic_echo(self, tmp_path: Path) -> None:
        """Basic echo command should succeed."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "run_shell_command",
            {"command": "echo hello"},
            state,
        )
        
        assert result["success"] is True
        assert result["exit_code"] == 0
        assert "hello" in result["output"]

    @pytest.mark.asyncio
    async def test_hard_cancellation_reaches_shared_shell(self, tmp_path: Path) -> None:
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        cancellation = _TestCancellation()
        timer = threading.Timer(0.2, cancellation.cancel)
        timer.start()
        started = time.monotonic()
        result = await wrapper.execute_tool_async(
            "run_shell_command",
            {"command": "sleep 60"},
            state,
            cancellation=cancellation,
        )
        timer.join(timeout=1)
        assert result["success"] is False
        assert result["cancelled"] is True
        assert time.monotonic() - started < 5

    @pytest.mark.asyncio
    async def test_exit_code_zero_success(self, tmp_path: Path) -> None:
        """Exit code 0 should set success=True."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "run_shell_command",
            {"command": "exit 0"},
            state,
        )
        
        assert result["success"] is True
        assert result["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_exit_code_nonzero_failure(self, tmp_path: Path) -> None:
        """Non-zero exit code should set success=False."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "run_shell_command",
            {"command": "exit 1"},
            state,
        )
        
        assert result["success"] is False
        assert result["exit_code"] == 1
        assert "Exit Code:" in result["output"]

    @pytest.mark.asyncio
    async def test_stderr_capture(self, tmp_path: Path) -> None:
        """Stderr should be captured in output."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "run_shell_command",
            {"command": "echo stderr_msg >&2"},
            state,
        )
        
        assert result["success"] is True
        # Stderr should appear in combined output
        assert "stderr_msg" in result["output"]

    @pytest.mark.asyncio
    async def test_working_directory(self, tmp_path: Path) -> None:
        """Command should run in specified working directory."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        test_file = subdir / "test.txt"
        test_file.write_text("content")
        
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "run_shell_command",
            {"command": "ls", "dir_path": str(subdir)},
            state,
        )
        
        assert result["success"] is True
        assert "test.txt" in result["output"]

    @pytest.mark.asyncio
    async def test_timeout(self, tmp_path: Path) -> None:
        """Timeout should kill long-running command."""
        wrapper = ToolWrapper(GeminiShellTool)
        # Set a short timeout via config
        state = wrapper.init({"working_directory": str(tmp_path), "shell_timeout_seconds": 1})
        
        result = await wrapper.execute_tool_async(
            "run_shell_command",
            {"command": "sleep 60"},
            state,
        )
        
        assert result["success"] is False
        assert result.get("timed_out") is True
        assert result["exit_code"] is None
        # Should complete much faster than 60 seconds
        assert result["duration_seconds"] < 10.0

    @pytest.mark.asyncio
    async def test_empty_command_error(self, tmp_path: Path) -> None:
        """Empty command should return error."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "run_shell_command",
            {"command": ""},
            state,
        )
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_tool_name_error(self, tmp_path: Path) -> None:
        """Invalid tool name should return error."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "wrong_tool",
            {"command": "echo hello"},
            state,
        )
        
        assert result["success"] is False
        assert "Unknown tool" in result.get("error", "")


class TestGeminiShellToolBackground:
    """Tests for background process support."""

    @pytest.mark.asyncio
    async def test_background_returns_pid(self, tmp_path: Path) -> None:
        """Background command should return PID."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "run_shell_command",
            {"command": "sleep 60", "is_background": True},
            state,
        )
        
        assert result["success"] is True
        assert result.get("background") is True
        assert "pid" in result
        assert isinstance(result["pid"], int)
        assert result["pid"] > 0

    @pytest.mark.asyncio
    async def test_background_output_format(self, tmp_path: Path) -> None:
        """Background output should match Gemini format."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "run_shell_command",
            {"command": "sleep 60", "is_background": True},
            state,
        )
        
        assert "Command moved to background" in result["output"]
        assert "PID:" in result["output"]
        assert "Output hidden" in result["output"]


class TestGeminiShellToolFormatting:
    """Tests for output formatting."""

    @pytest.mark.asyncio
    async def test_success_output_has_prefix(self, tmp_path: Path) -> None:
        """Success output should have 'Output:' prefix."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "run_shell_command",
            {"command": "echo hello"},
            state,
        )
        
        assert "Output:" in result["output"]

    @pytest.mark.asyncio
    async def test_failure_output_has_exit_code(self, tmp_path: Path) -> None:
        """Failure output should include exit code."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "run_shell_command",
            {"command": "exit 42"},
            state,
        )
        
        assert "Exit Code: 42" in result["output"]

    @pytest.mark.asyncio
    async def test_format_tool_result_returns_output(self, tmp_path: Path) -> None:
        """format_tool_result should return the output field."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "run_shell_command",
            {"command": "echo hello"},
            state,
        )
        
        formatted = wrapper.format_tool_result(result, state)
        assert formatted == result["output"]


class TestGeminiShellToolTruncation:
    """Tests for output truncation."""

    @pytest.mark.asyncio
    async def test_short_output_not_truncated(self, tmp_path: Path) -> None:
        """Short output should not be truncated."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "run_shell_command",
            {"command": "echo hello"},
            state,
        )
        
        assert result["truncated"] is False

    @pytest.mark.asyncio
    async def test_long_output_truncated(self, tmp_path: Path) -> None:
        """Long output should be truncated at 40k chars."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        # Generate output larger than 40k chars
        result = await wrapper.execute_tool_async(
            "run_shell_command",
            {"command": "for i in $(seq 1 5000); do echo \"Line $i with some padding text to make it longer\"; done"},
            state,
        )
        
        # Should be truncated
        assert result["truncated"] is True
        # Should have truncation message
        assert "Output too large" in result["output"]

    @pytest.mark.asyncio
    async def test_truncation_has_temp_file_reference(self, tmp_path: Path) -> None:
        """Truncated output should reference temp file."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        # Generate output larger than 40k chars
        result = await wrapper.execute_tool_async(
            "run_shell_command",
            {"command": "for i in $(seq 1 5000); do echo \"Line $i with some padding text\"; done"},
            state,
        )
        
        if result["truncated"]:
            assert "For full output see:" in result["output"]


class TestGeminiShellToolPreview:
    """Tests for tool call preview."""

    def test_preview_shows_command(self, tmp_path: Path) -> None:
        """Preview should show the command."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        preview = wrapper.format_tool_call_preview(
            "run_shell_command",
            {"command": "echo hello world"},
            state,
        )
        
        assert "echo hello world" in preview

    def test_preview_multiline_shows_first_line(self, tmp_path: Path) -> None:
        """Preview should show only first line of multiline command."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        preview = wrapper.format_tool_call_preview(
            "run_shell_command",
            {"command": "echo hello\necho world"},
            state,
        )
        
        assert "echo hello" in preview
        assert "\n" not in preview or preview.count("\n") == 0


class TestGeminiShellToolConfig:
    """Tests for config handling."""

    def test_default_timeout(self, tmp_path: Path) -> None:
        """Default timeout should be 120 seconds."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        assert state["timeout_seconds"] == 120

    def test_config_timeout_override(self, tmp_path: Path) -> None:
        """Config should override default timeout."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path), "shell_timeout_seconds": 300})
        
        assert state["timeout_seconds"] == 300

    def test_default_max_output_chars(self, tmp_path: Path) -> None:
        """Default max output chars should be 40000."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        assert state["max_output_chars"] == 40000

    def test_default_truncation_head_ratio(self, tmp_path: Path) -> None:
        """Default truncation head ratio should be 0.2 (20/80 split)."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        assert state["truncation_head_ratio"] == 0.2

    def test_project_temp_dir_default(self, tmp_path: Path) -> None:
        """project_temp_dir should default to <working_directory>/.temp."""
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        expected = str(tmp_path / ".temp")
        assert state["project_temp_dir"] == expected

    def test_project_temp_dir_config_override(self, tmp_path: Path) -> None:
        """project_temp_dir can be overridden via config."""
        custom_temp = tmp_path / "custom_temp"
        
        wrapper = ToolWrapper(GeminiShellTool)
        state = wrapper.init({
            "working_directory": str(tmp_path),
            "project_temp_dir": str(custom_temp),
        })
        
        assert state["project_temp_dir"] == str(custom_temp.resolve())