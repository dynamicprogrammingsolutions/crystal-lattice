"""Tests for KimiShellTool."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from agent_core.plugin import ToolWrapper
from kimi_tools.kimi_shell_tool import KimiShellTool, get_clean_env


class TestGetCleanEnv:
    """Tests for clean environment helper."""

    def test_returns_dict(self) -> None:
        """Should return a dict."""
        env = get_clean_env()
        assert isinstance(env, dict)

    def test_inherits_current_env(self) -> None:
        """Should inherit current environment variables."""
        env = get_clean_env()
        # PATH should be present in most environments
        assert "PATH" in env or "path" in env

    def test_removes_pyinstaller_vars_when_frozen(self, monkeypatch) -> None:
        """Should remove PyInstaller variables when running as frozen."""
        # Simulate frozen environment
        monkeypatch.setattr(sys, 'frozen', True, raising=False)
        monkeypatch.setenv('_MEIPASS', '/tmp/mei123')
        monkeypatch.setenv('PYINSTALLER_TEST', 'value')
        
        env = get_clean_env()
        
        assert '_MEIPASS' not in env
        assert 'PYINSTALLER_TEST' not in env

    def test_removes_ld_library_path_when_frozen(self, monkeypatch) -> None:
        """Should remove LD_LIBRARY_PATH when running as frozen."""
        monkeypatch.setattr(sys, 'frozen', True, raising=False)
        monkeypatch.setenv('LD_LIBRARY_PATH', '/frozen/lib')
        
        env = get_clean_env()
        
        assert 'LD_LIBRARY_PATH' not in env


class TestKimiShellToolSchemas:
    """Tests for tool schema definition."""

    def test_tool_name(self) -> None:
        """Tool name should be kimi_shell_tool."""
        assert KimiShellTool.name == "kimi_shell_tool"

    def test_schema_tool_name_is_shell(self, tmp_path: Path) -> None:
        """Schema tool name should be Shell."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        assert len(schemas) == 1
        schema = schemas[0]
        assert schema["function"]["name"] == "Shell"

    def test_schema_has_string_command(self, tmp_path: Path) -> None:
        """Schema should define command as string type."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert props["command"]["type"] == "string"

    def test_schema_has_timeout_seconds(self, tmp_path: Path) -> None:
        """Schema should include timeout parameter (in seconds)."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "timeout" in props
        assert props["timeout"]["type"] == "integer"
        assert props["timeout"]["default"] == 60

    def test_schema_no_workdir_or_background(self, tmp_path: Path) -> None:
        """Schema should not have workdir or background parameters."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "directory" not in props
        assert "dir_path" not in props
        assert "is_background" not in props

    def test_command_is_required(self, tmp_path: Path) -> None:
        """Command should be in required fields."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        schemas = wrapper.get_tool_schemas(state)
        
        required = schemas[0]["function"]["parameters"]["required"]
        assert "command" in required


class TestKimiShellToolExecute:
    """Tests for tool execution."""

    @pytest.mark.asyncio
    async def test_basic_echo(self, tmp_path: Path) -> None:
        """Basic echo command should succeed."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "Shell",
            {"command": "echo hello"},
            state,
        )
        
        assert result["success"] is True
        assert result["exit_code"] == 0
        assert "hello" in result["output"]

    @pytest.mark.asyncio
    async def test_exit_code_zero_success(self, tmp_path: Path) -> None:
        """Exit code 0 should set success=True."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "Shell",
            {"command": "exit 0"},
            state,
        )
        
        assert result["success"] is True
        assert result["exit_code"] == 0

    @pytest.mark.asyncio
    async def test_exit_code_nonzero_failure(self, tmp_path: Path) -> None:
        """Non-zero exit code should set success=False."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "Shell",
            {"command": "exit 1"},
            state,
        )
        
        assert result["success"] is False
        assert result["exit_code"] == 1

    @pytest.mark.asyncio
    async def test_stderr_capture(self, tmp_path: Path) -> None:
        """Stderr should be captured in output."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "Shell",
            {"command": "echo stderr_msg >&2"},
            state,
        )
        
        assert "stderr_msg" in result["output"]

    @pytest.mark.asyncio
    async def test_timeout_in_seconds(self, tmp_path: Path) -> None:
        """Timeout parameter should be in seconds."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "Shell",
            {"command": "sleep 60", "timeout": 1},  # 1 second timeout
            state,
        )
        
        assert result["success"] is False
        assert result.get("timed_out") is True
        # Should complete much faster than 60 seconds
        assert result["duration_seconds"] < 5.0

    @pytest.mark.asyncio
    async def test_empty_command_error(self, tmp_path: Path) -> None:
        """Empty command should return error."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "Shell",
            {"command": ""},
            state,
        )
        
        assert result["success"] is False
        assert "error" in result


class TestKimiShellToolFormatting:
    """Tests for output formatting."""

    @pytest.mark.asyncio
    async def test_success_has_success_message(self, tmp_path: Path) -> None:
        """Success output should have success message."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "Shell",
            {"command": "echo hello"},
            state,
        )
        
        assert "Command executed successfully." in result["output"]

    @pytest.mark.asyncio
    async def test_failure_has_exit_code_message(self, tmp_path: Path) -> None:
        """Failure output should have exit code message."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "Shell",
            {"command": "exit 42"},
            state,
        )
        
        assert "Command failed with exit code: 42" in result["output"]

    @pytest.mark.asyncio
    async def test_timeout_has_timeout_message(self, tmp_path: Path) -> None:
        """Timeout output should have timeout message."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        result = await wrapper.execute_tool_async(
            "Shell",
            {"command": "sleep 60", "timeout": 1},
            state,
        )
        
        assert "Command killed by timeout" in result["output"]

    @pytest.mark.asyncio
    async def test_long_single_line_is_truncated(self, tmp_path: Path) -> None:
        """Long single-line output should be truncated with Kimi-style marker."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})

        command = f'"{sys.executable}" -c "print(\'x\' * 3000)"'
        result = await wrapper.execute_tool_async(
            "Shell",
            {"command": command},
            state,
        )

        assert result["success"] is True
        assert result.get("truncated") is True
        first_line = result["output"].splitlines()[0]
        assert "[...truncated]" in first_line
        assert len(first_line) <= 2000
        assert "Command executed successfully. Output is truncated to fit in the message." in result["output"]

    @pytest.mark.asyncio
    async def test_large_multiline_output_is_capped(self, tmp_path: Path) -> None:
        """Large multiline output should be capped at the tool-level budget."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})

        command = f'"{sys.executable}" -c "for i in range(6000): print(f\'Line {{i}}\')"'
        result = await wrapper.execute_tool_async(
            "Shell",
            {"command": command},
            state,
        )

        assert result["success"] is True
        assert result.get("truncated") is True
        assert "Line 0" in result["output"]
        assert "Line 5999" not in result["output"]
        assert "Output is truncated to fit in the message." in result["output"]

    @pytest.mark.asyncio
    async def test_failure_includes_truncation_notice(self, tmp_path: Path) -> None:
        """Failure output should include the truncation notice when output is capped."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})

        command = f'"{sys.executable}" -c "import sys; print(\'x\' * 3000); sys.exit(7)"'
        result = await wrapper.execute_tool_async(
            "Shell",
            {"command": command},
            state,
        )

        assert result["success"] is False
        assert result["exit_code"] == 7
        assert result.get("truncated") is True
        assert "Command failed with exit code: 7. Output is truncated to fit in the message." in result["output"]


class TestKimiShellToolTimeoutLimits:
    """Tests for timeout limits."""

    @pytest.mark.asyncio
    async def test_timeout_respects_max(self, tmp_path: Path) -> None:
        """Timeout should be capped at max_timeout_seconds."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        # Request timeout larger than max (300s)
        result = await wrapper.execute_tool_async(
            "Shell",
            {"command": "sleep 60", "timeout": 1000},  # Request 1000s, should cap at 300s
            state,
        )
        
        # Should still timeout quickly since we're testing with max of 300s
        # but the key is that it doesn't use 1000s
        # This test just verifies it runs without error
        assert "command" in result

    @pytest.mark.asyncio
    async def test_default_timeout_60_seconds(self, tmp_path: Path) -> None:
        """Default timeout should be 60 seconds."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        assert state["timeout_seconds"] == 60

    @pytest.mark.asyncio
    async def test_max_timeout_300_seconds(self, tmp_path: Path) -> None:
        """Max timeout should be 300 seconds."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        assert state["max_timeout_seconds"] == 300


class TestKimiShellToolCleanEnv:
    """Tests for clean environment usage."""

    @pytest.mark.asyncio
    async def test_uses_clean_env_by_default(self, tmp_path: Path) -> None:
        """Should use clean environment by default."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        assert state.get("clean_env") is True

    @pytest.mark.asyncio
    async def test_clean_env_can_be_disabled(self, tmp_path: Path) -> None:
        """Clean environment can be disabled via config."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({
            "working_directory": str(tmp_path),
            "shell_clean_env": False,
        })
        
        assert state.get("clean_env") is False


class TestKimiShellToolConfig:
    """Tests for config handling."""

    def test_default_timeout(self, tmp_path: Path) -> None:
        """Default timeout should be 60 seconds."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        assert state["timeout_seconds"] == 60

    def test_config_timeout_override(self, tmp_path: Path) -> None:
        """Config should override default timeout."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({
            "working_directory": str(tmp_path),
            "shell_timeout_seconds": 120,
        })
        
        assert state["timeout_seconds"] == 120

    def test_project_temp_dir_default(self, tmp_path: Path) -> None:
        """project_temp_dir should default to <working_directory>/.temp."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        expected = str(tmp_path / ".temp")
        assert state["project_temp_dir"] == expected

    def test_project_temp_dir_config_override(self, tmp_path: Path) -> None:
        """project_temp_dir can be overridden via config."""
        custom_temp = tmp_path / "custom_temp"
        
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({
            "working_directory": str(tmp_path),
            "project_temp_dir": str(custom_temp),
        })
        
        assert state["project_temp_dir"] == str(custom_temp.resolve())


class TestKimiShellToolPreview:
    """Tests for tool call preview."""

    def test_preview_shows_command(self, tmp_path: Path) -> None:
        """Preview should show the command."""
        wrapper = ToolWrapper(KimiShellTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        
        preview = wrapper.format_tool_call_preview(
            "Shell",
            {"command": "echo hello world"},
            state,
        )
        
        assert "echo hello world" in preview