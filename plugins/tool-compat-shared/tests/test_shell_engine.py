"""Tests for the shell engine core functionality."""

from __future__ import annotations

import os
import platform
from pathlib import Path

import pytest

from tool_compat_shared import (
    ShellInfo,
    build_shell_args,
    detect_shell,
    run_shell_command,
)


class TestDetectShell:
    """Tests for shell detection."""

    def test_detect_shell_returns_shell_info(self) -> None:
        """detect_shell returns a ShellInfo instance."""
        shell = detect_shell()
        assert isinstance(shell, ShellInfo)
        assert isinstance(shell.name, str)
        assert isinstance(shell.path, str)
        assert isinstance(shell.args, tuple)
        assert len(shell.args) > 0

    def test_detect_shell_path_exists(self) -> None:
        """The detected shell path should exist on the system."""
        shell = detect_shell()
        # On Windows, the path might be just the executable name if in PATH
        if platform.system() == "Windows":
            # Either the path exists, or it's a known Windows executable
            assert shell.name in ("powershell", "cmd")
        else:
            assert Path(shell.path).exists(), f"Shell path does not exist: {shell.path}"

    def test_detect_shell_unix_has_c_arg(self) -> None:
        """Unix shells should use -c argument."""
        shell = detect_shell()
        if platform.system() != "Windows":
            assert "-c" in shell.args

    def test_detect_shell_windows_powershell_args(self) -> None:
        """Windows PowerShell should use -command argument."""
        shell = detect_shell()
        if platform.system() == "Windows" and shell.name == "powershell":
            assert "-command" in shell.args

    def test_detect_shell_windows_cmd_args(self) -> None:
        """Windows cmd should use /c argument."""
        shell = detect_shell()
        if platform.system() == "Windows" and shell.name == "cmd":
            assert "/c" in shell.args


class TestBuildShellArgs:
    """Tests for building shell argument lists."""

    def test_build_shell_args_with_default_shell(self) -> None:
        """build_shell_args uses detected shell when none provided."""
        args = build_shell_args("echo hello")
        assert len(args) >= 2
        # First arg should be the shell path
        assert isinstance(args[0], str)
        # Last arg should be the command
        assert args[-1] == "echo hello"

    def test_build_shell_args_with_custom_shell(self) -> None:
        """build_shell_args uses provided shell."""
        custom = ShellInfo(name="test", path="/bin/test", args=("-x",))
        args = build_shell_args("echo test", shell=custom)
        assert args == ["/bin/test", "-x", "echo test"]

    def test_build_shell_args_preserves_command(self) -> None:
        """The command string is preserved as the final argument."""
        args = build_shell_args("ls -la /tmp")
        assert args[-1] == "ls -la /tmp"


class TestRunShellCommand:
    """Tests for shell command execution."""

    @pytest.mark.asyncio
    async def test_basic_echo(self) -> None:
        """echo command produces expected output."""
        result = await run_shell_command("echo hello")
        assert result["ok"] is True
        assert result["exit_code"] == 0
        assert "hello" in result["output"]
        assert "hello" in result["stdout"]
        assert result["timed_out"] is False

    @pytest.mark.asyncio
    async def test_exit_code_nonzero(self) -> None:
        """Command with non-zero exit code returns ok=False."""
        if platform.system() == "Windows":
            result = await run_shell_command("exit 1")
        else:
            result = await run_shell_command("sh -c 'exit 1'")
        assert result["ok"] is False
        assert result["exit_code"] == 1
        assert result["timed_out"] is False

    @pytest.mark.asyncio
    async def test_stderr_capture(self) -> None:
        """Command writing to stderr captures it separately."""
        if platform.system() == "Windows":
            result = await run_shell_command('Write-Error "error message"')
            # PowerShell writes errors differently
            assert result["exit_code"] is not None
        else:
            result = await run_shell_command("echo stderr_msg >&2")
            assert result["ok"] is True
            assert "stderr_msg" in result["stderr"]
            assert "stderr_msg" in result["output"]  # Also in combined

    @pytest.mark.asyncio
    async def test_combined_output_interleaved(self) -> None:
        """Both stdout and stderr appear in combined output."""
        if platform.system() == "Windows":
            # PowerShell equivalent
            result = await run_shell_command('Write-Output "stdout"; Write-Error "stderr"')
            # Note: PowerShell Write-Error behavior differs
        else:
            result = await run_shell_command('echo stdout; echo stderr >&2')
            assert result["ok"] is True
            assert "stdout" in result["output"]
            assert "stderr" in result["output"]

    @pytest.mark.asyncio
    async def test_timeout_kills_process(self) -> None:
        """Long-running command is killed on timeout."""
        if platform.system() == "Windows":
            # Windows: use a command that sleeps longer than timeout
            result = await run_shell_command("Start-Sleep -Seconds 60", timeout_seconds=0.5)
        else:
            result = await run_shell_command("sleep 60", timeout_seconds=0.5)

        assert result["timed_out"] is True
        assert result["exit_code"] is None
        assert result["ok"] is False
        # Should complete much faster than the sleep duration
        assert result["duration_seconds"] < 5.0

    @pytest.mark.asyncio
    async def test_working_directory(self, tmp_path: Path) -> None:
        """Command runs in specified working directory."""
        # Create a subdirectory with a test file
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        test_file = subdir / "test.txt"
        test_file.write_text("content")

        if platform.system() == "Windows":
            result = await run_shell_command("dir", workdir=str(subdir))
        else:
            result = await run_shell_command("ls", workdir=str(subdir))

        assert result["ok"] is True
        assert "test.txt" in result["output"]

    @pytest.mark.asyncio
    async def test_env_override(self) -> None:
        """Custom environment variables are used."""
        if platform.system() == "Windows":
            # Windows uses $env:VAR syntax in PowerShell
            result = await run_shell_command(
                '$env:TEST_VAR',
                env={"TEST_VAR": "custom_value", **dict(os.environ)}
            )
            # Note: env isolation may vary
        else:
            # Pass through PATH so commands work, plus our custom var
            env = {"PATH": os.environ.get("PATH", ""), "TEST_VAR": "custom_value"}
            result = await run_shell_command("echo $TEST_VAR", env=env)
            assert "custom_value" in result["output"]

    @pytest.mark.asyncio
    async def test_duration_tracking(self) -> None:
        """Duration is tracked with monotonic time."""
        result = await run_shell_command("echo test")
        assert "duration_seconds" in result
        assert isinstance(result["duration_seconds"], float)
        assert result["duration_seconds"] >= 0

    @pytest.mark.asyncio
    async def test_shell_info_in_result(self) -> None:
        """Result includes the shell used for execution."""
        result = await run_shell_command("echo test")
        assert "shell" in result
        assert isinstance(result["shell"], ShellInfo)

    @pytest.mark.asyncio
    async def test_custom_shell(self) -> None:
        """Custom shell can be specified."""
        # Use sh (available on Unix, not applicable on most Windows)
        if platform.system() != "Windows":
            custom = ShellInfo(name="sh", path="/bin/sh", args=("-c",))
            result = await run_shell_command("echo custom", shell=custom)
            assert result["ok"] is True
            assert "custom" in result["output"]

    @pytest.mark.asyncio
    async def test_no_timeout_means_no_limit(self) -> None:
        """None timeout means command runs to completion."""
        # A quick command should complete without timeout even with None
        result = await run_shell_command("echo quick", timeout_seconds=None)
        assert result["ok"] is True
        assert result["timed_out"] is False

    @pytest.mark.asyncio
    async def test_empty_command(self) -> None:
        """Empty command executes (shell behavior varies)."""
        result = await run_shell_command("")
        # Shell behavior for empty command varies; just check it doesn't crash
        assert "exit_code" in result
        assert "output" in result

    @pytest.mark.asyncio
    async def test_multiline_output(self) -> None:
        """Multiline output is preserved."""
        if platform.system() == "Windows":
            result = await run_shell_command('Write-Output "line1"; Write-Output "line2"')
        else:
            result = await run_shell_command('printf "line1\\nline2\\n"')
        assert result["ok"] is True
        assert "line1" in result["output"]
        assert "line2" in result["output"]
        # Check for newlines
        assert "\n" in result["output"] or "\r" in result["output"]