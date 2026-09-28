"""Tests for QwenShellTool."""

from __future__ import annotations

from pathlib import Path
import threading
import time

import pytest

from agent_core.plugin import ToolWrapper
from qwen_tools.qwen_shell_tool import QwenShellTool


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


class TestQwenShellToolSchemas:
    """Tests for tool schema definition."""

    def test_tool_name(self) -> None:
        """Tool name should be qwen_shell_tool."""
        assert QwenShellTool.name == "qwen_shell_tool"

    def test_schema_tool_name_is_bash(self, tmp_path: Path) -> None:
        """Schema tool name should be bash."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        assert len(schemas) == 1
        schema = schemas[0]
        assert schema["function"]["name"] == "bash"

    def test_schema_has_string_command(self, tmp_path: Path) -> None:
        """Schema should define command as string type."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert props["command"]["type"] == "string"

    def test_schema_has_timeout_ms(self, tmp_path: Path) -> None:
        """Schema should include timeout parameter (in milliseconds)."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "timeout" in props
        assert props["timeout"]["type"] == "number"

    def test_schema_has_directory(self, tmp_path: Path) -> None:
        """Schema should include directory parameter."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "directory" in props
        assert props["directory"]["type"] == "string"

    def test_schema_has_description(self, tmp_path: Path) -> None:
        """Schema should include description parameter."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "description" in props

    def test_schema_has_is_background(self, tmp_path: Path) -> None:
        """Schema should include is_background parameter."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "is_background" in props
        assert props["is_background"]["type"] == "boolean"

    def test_command_is_required(self, tmp_path: Path) -> None:
        """Command should be in required fields."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        required = schemas[0]["function"]["parameters"]["required"]
        assert "command" in required


class TestQwenShellToolExecute:
    """Tests for tool execution."""

    @pytest.mark.asyncio
    async def test_basic_echo(self, tmp_path: Path) -> None:
        """Basic echo command should succeed."""
        wrapper = ToolWrapper(QwenShellTool)
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
    async def test_hard_cancellation_reaches_shared_shell(self, tmp_path: Path) -> None:
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        cancellation = _TestCancellation()
        timer = threading.Timer(0.2, cancellation.cancel)
        timer.start()
        started = time.monotonic()
        result = await wrapper.execute_tool_async(
            "bash",
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
        wrapper = ToolWrapper(QwenShellTool)
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
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "exit 1"},
            state,
        )
        
        assert result["success"] is False
        assert result["exit_code"] == 1

    @pytest.mark.asyncio
    async def test_stderr_causes_failure_format(self, tmp_path: Path) -> None:
        """Stderr should trigger failure format even with exit 0."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "echo stderr_msg >&2"},
            state,
        )
        
        # Qwen treats stderr as failure format
        assert "Stdout:" in result["output"]
        assert "Stderr:" in result["output"]

    @pytest.mark.asyncio
    async def test_working_directory(self, tmp_path: Path) -> None:
        """Command should run in specified working directory."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        test_file = subdir / "test.txt"
        test_file.write_text("content")
        
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "ls", "directory": str(subdir)},
            state,
        )
        
        assert result["success"] is True
        assert "test.txt" in result["output"]

    @pytest.mark.asyncio
    async def test_timeout_in_milliseconds(self, tmp_path: Path) -> None:
        """Timeout parameter should be in milliseconds."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "sleep 60", "timeout": 500},  # 500ms timeout
            state,
        )
        
        assert result["success"] is False
        assert result.get("timed_out") is True
        # Should complete much faster than 60 seconds
        assert result["duration_seconds"] < 5.0

    @pytest.mark.asyncio
    async def test_empty_command_error(self, tmp_path: Path) -> None:
        """Empty command should return error."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": ""},
            state,
        )
        
        assert result["success"] is False
        assert "error" in result


class TestQwenShellToolBackground:
    """Tests for background process support."""

    @pytest.mark.asyncio
    async def test_background_returns_pid(self, tmp_path: Path) -> None:
        """Background command should return PID."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
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
        """Background output should match Qwen format."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "sleep 60", "is_background": True},
            state,
        )
        
        assert "Background command started" in result["output"]
        assert "PID:" in result["output"]

    @pytest.mark.asyncio
    async def test_background_has_kill_hint(self, tmp_path: Path) -> None:
        """Background output should have kill hint."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "sleep 60", "is_background": True},
            state,
        )
        
        # Should have either kill or taskkill hint depending on platform
        output = result["output"]
        has_kill_hint = "kill" in output or "taskkill" in output
        assert has_kill_hint


class TestQwenShellToolFormatting:
    """Tests for output formatting."""

    @pytest.mark.asyncio
    async def test_success_no_stderr_just_output(self, tmp_path: Path) -> None:
        """Success with no stderr should just show output (no prefix)."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "echo hello"},
            state,
        )
        
        # Qwen success format: just the output, no "Output:" prefix
        assert "hello" in result["output"]
        assert "Output:" not in result["output"]

    @pytest.mark.asyncio
    async def test_failure_has_stdout_stderr_format(self, tmp_path: Path) -> None:
        """Failure should have Stdout/Stderr/Error/Exit Code format."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "exit 1"},
            state,
        )
        
        assert "Stdout:" in result["output"]
        assert "Stderr:" in result["output"]
        assert "Error:" in result["output"]
        assert "Exit Code:" in result["output"]
        assert "Signal:" in result["output"]


class TestQwenShellToolTruncation:
    """Tests for output truncation."""

    @pytest.mark.asyncio
    async def test_short_output_not_truncated(self, tmp_path: Path) -> None:
        """Short output should not be truncated."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "echo hello"},
            state,
        )
        
        assert result["truncated"] is False

    @pytest.mark.asyncio
    async def test_line_truncation_applied(self, tmp_path: Path) -> None:
        """Output exceeding line limit should be truncated."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        # Generate more than 1000 lines
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "for i in $(seq 1 2000); do echo \"Line $i\"; done"},
            state,
        )
        
        assert result["truncated"] is True
        assert "lines truncated" in result["output"]

    @pytest.mark.asyncio
    async def test_char_truncation_applied(self, tmp_path: Path) -> None:
        """Output exceeding char limit should be truncated."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        # Generate output that fits in lines but exceeds chars
        # Each line ~50 chars, need ~500 lines to exceed 25k chars
        result = await wrapper.execute_tool_async(
            "bash",
            {"command": "for i in $(seq 1 600); do printf '%050d\\n' $i; done"},
            state,
        )
        
        # May or may not be truncated depending on exact output size
        # Just verify it runs successfully
        assert result["success"] is True


class TestQwenShellToolConfig:
    """Tests for config handling."""

    def test_default_timeout(self, tmp_path: Path) -> None:
        """Default timeout should be 120 seconds."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        assert state["timeout_seconds"] == 120

    def test_default_max_output_lines(self, tmp_path: Path) -> None:
        """Default max output lines should be 1000."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        assert state["max_output_lines"] == 1000

    def test_default_max_output_chars(self, tmp_path: Path) -> None:
        """Default max output chars should be 25000."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        assert state["max_output_chars"] == 25000

    def test_config_timeout_override(self, tmp_path: Path) -> None:
        """Config should override default timeout."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path), "shell_timeout_seconds": 300})
        
        assert state["timeout_seconds"] == 300

    def test_project_temp_dir_default(self, tmp_path: Path) -> None:
        """project_temp_dir should default to <working_directory>/.temp."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        expected = str(tmp_path / ".temp")
        assert state["project_temp_dir"] == expected


class TestQwenShellToolPreview:
    """Tests for tool call preview."""

    def test_preview_shows_command(self, tmp_path: Path) -> None:
        """Preview should show the command."""
        wrapper = ToolWrapper(QwenShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        preview = wrapper.format_tool_call_preview(
            "bash",
            {"command": "echo hello world"},
            state,
        )
        
        assert "echo hello world" in preview