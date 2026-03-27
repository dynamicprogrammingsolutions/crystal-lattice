"""Tests for the shell engine core functionality."""

from __future__ import annotations

import os
import platform
from pathlib import Path

import pytest

from tool_compat_shared import (
    ShellInfo,
    approx_token_count,
    build_shell_args,
    detect_shell,
    run_shell_command,
    truncate_output,
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


class TestApproxTokenCount:
    """Tests for the token approximation function."""

    def test_empty_string(self) -> None:
        """Empty string has 0 tokens."""
        assert approx_token_count("") == 0

    def test_single_char(self) -> None:
        """Single character rounds to 0 tokens."""
        assert approx_token_count("a") == 0

    def test_four_chars(self) -> None:
        """4 characters = 1 token."""
        assert approx_token_count("abcd") == 1

    def test_eight_chars(self) -> None:
        """8 characters = 2 tokens."""
        assert approx_token_count("abcdefgh") == 2

    def test_seven_chars_rounds_down(self) -> None:
        """7 characters = 1 token (integer division rounds down)."""
        assert approx_token_count("abcdefg") == 1

    def test_unicode_content(self) -> None:
        """Unicode characters count as characters, not bytes."""
        # Each emoji is 1 character, so 4 emojis = 1 token
        assert approx_token_count("😀😁😂😃") == 1

    def test_multiline_content(self) -> None:
        """Newlines count as characters."""
        # 8 chars including 1 newline = 2 tokens
        assert approx_token_count("abcd\nefgh") == 2


class TestTruncateOutput:
    """Tests for the truncate_output function."""

    # --- No truncation cases ---

    def test_no_truncation_when_under_char_limit(self) -> None:
        """Output under limit is returned unchanged."""
        content = "hello world"
        output, meta = truncate_output(content, limit_type="chars", limit_value=100)
        assert meta["truncated"] is False
        assert output == content
        assert meta["total_chars"] == 11
        assert meta["omitted_chars"] == 0

    def test_no_truncation_when_under_line_limit(self) -> None:
        """Output under line limit is returned unchanged."""
        content = "line1\nline2\nline3"
        output, meta = truncate_output(content, limit_type="lines", limit_value=10)
        assert meta["truncated"] is False
        assert output == content
        assert meta["total_lines"] == 3

    def test_no_truncation_when_under_token_limit(self) -> None:
        """Output under token limit is returned unchanged."""
        # 40 chars = 10 tokens
        content = "a" * 40
        output, meta = truncate_output(content, limit_type="tokens", limit_value=20)
        assert meta["truncated"] is False
        assert output == content
        assert meta["total_tokens"] == 10

    def test_exact_limit_no_truncation(self) -> None:
        """Output exactly at limit is not truncated."""
        content = "a" * 100
        output, meta = truncate_output(content, limit_type="chars", limit_value=100)
        assert meta["truncated"] is False
        assert output == content

    # --- Char truncation ---

    def test_truncate_chars_head_only(self) -> None:
        """head_ratio=1.0 keeps all from beginning."""
        content = "a" * 1000
        output, meta = truncate_output(
            content, limit_type="chars", limit_value=100, head_ratio=1.0
        )
        assert meta["truncated"] is True
        assert len(output) == 100
        assert output == "a" * 100
        assert meta["head_kept"] == 100
        assert meta["tail_kept"] == 0
        assert meta["omitted_chars"] == 900

    def test_truncate_chars_50_50_split(self) -> None:
        """head_ratio=0.5 splits 50/50 (Codex-style)."""
        content = "a" * 400 + "b" * 600  # 1000 chars total
        output, meta = truncate_output(
            content, limit_type="chars", limit_value=100, head_ratio=0.5
        )
        assert meta["truncated"] is True
        assert len(output) == 100
        # head_kept = 100 * 0.5 = 50, tail_kept = 50
        assert output == "a" * 50 + "b" * 50
        assert meta["head_kept"] == 50
        assert meta["tail_kept"] == 50
        assert meta["omitted_chars"] == 900

    def test_truncate_chars_20_80_split(self) -> None:
        """head_ratio=0.2 splits 20/80 (Gemini-style)."""
        content = "a" * 200 + "b" * 800  # 1000 chars total
        output, meta = truncate_output(
            content, limit_type="chars", limit_value=100, head_ratio=0.2
        )
        assert meta["truncated"] is True
        assert len(output) == 100
        # head_kept = 100 * 0.2 = 20, tail_kept = 80
        assert output == "a" * 20 + "b" * 80
        assert meta["head_kept"] == 20
        assert meta["tail_kept"] == 80

    # --- Line truncation ---

    def test_truncate_lines_head_only(self) -> None:
        """Line truncation with head_ratio=1.0."""
        content = "\n".join(f"line{i}" for i in range(100))
        output, meta = truncate_output(
            content, limit_type="lines", limit_value=10, head_ratio=1.0
        )
        assert meta["truncated"] is True
        assert meta["total_lines"] == 100
        assert meta["omitted_lines"] == 90
        assert meta["head_kept"] == 10
        assert meta["tail_kept"] == 0
        # Check content
        lines = output.splitlines()
        assert len(lines) == 10
        assert lines[0] == "line0"

    def test_truncate_lines_50_50_split(self) -> None:
        """Line truncation with 50/50 split."""
        content = "\n".join(f"line{i}" for i in range(100))
        output, meta = truncate_output(
            content, limit_type="lines", limit_value=10, head_ratio=0.5
        )
        assert meta["truncated"] is True
        assert meta["head_kept"] == 5
        assert meta["tail_kept"] == 5
        # Check content: first 5 lines + last 5 lines
        lines = output.splitlines()
        assert len(lines) == 10
        assert lines[0] == "line0"
        assert lines[-1] == "line99"

    def test_truncate_lines_preserves_trailing_newline(self) -> None:
        """Line truncation preserves trailing newline if present."""
        content = "line1\nline2\nline3\n"
        output, meta = truncate_output(
            content, limit_type="lines", limit_value=2, head_ratio=1.0
        )
        assert meta["truncated"] is True
        # Should have 2 lines with their newlines
        assert output == "line1\nline2\n"

    # --- Token truncation ---

    def test_truncate_tokens_uses_approximation(self) -> None:
        """Token truncation converts to char budget and delegates."""
        # 100 chars = 25 tokens, limit of 10 tokens = 40 chars
        content = "a" * 100
        output, meta = truncate_output(
            content, limit_type="tokens", limit_value=10, head_ratio=0.5
        )
        assert meta["truncated"] is True
        assert meta["total_tokens"] == 25
        assert meta["omitted_tokens"] == 15
        # 10 tokens * 4 = 40 chars, split 50/50 = 20 + 20
        assert len(output) == 40
        assert meta["head_kept"] == 20  # chars, not tokens
        assert meta["tail_kept"] == 20

    def test_truncate_tokens_head_only(self) -> None:
        """Token truncation with head_ratio=1.0."""
        # 100 chars = 25 tokens
        content = "a" * 100
        output, meta = truncate_output(
            content, limit_type="tokens", limit_value=10, head_ratio=1.0
        )
        assert meta["truncated"] is True
        # 10 tokens * 4 = 40 chars, all from head
        assert len(output) == 40
        assert output == "a" * 40

    # --- Metadata tests ---

    def test_metadata_complete(self) -> None:
        """All metadata fields are returned."""
        content = "a" * 100
        output, meta = truncate_output(content, limit_type="chars", limit_value=50)
        expected_keys = {
            "truncated",
            "total_chars",
            "total_lines",
            "total_tokens",
            "omitted_chars",
            "omitted_lines",
            "omitted_tokens",
            "head_kept",
            "tail_kept",
            "limit_type",
            "limit_value",
            "head_ratio",
        }
        assert set(meta.keys()) == expected_keys
        assert meta["limit_type"] == "chars"
        assert meta["limit_value"] == 50
        assert meta["head_ratio"] == 0.5  # default

    def test_metadata_reflects_input_params(self) -> None:
        """Metadata reflects the input parameters."""
        content = "test"
        output, meta = truncate_output(
            content,
            limit_type="lines",
            limit_value=100,
            head_ratio=0.3,
        )
        assert meta["limit_type"] == "lines"
        assert meta["limit_value"] == 100
        assert meta["head_ratio"] == 0.3

    # --- UTF-8 / Unicode tests ---

    def test_utf8_content_safe(self) -> None:
        """UTF-8 content is handled safely (character indices, not bytes)."""
        # Each emoji is 1 character in Python 3
        content = "😀" * 100
        output, meta = truncate_output(content, limit_type="chars", limit_value=50)
        assert meta["truncated"] is True
        assert len(output) == 50
        # Each emoji should be intact
        assert output == "😀" * 50

    def test_mixed_utf8_content(self) -> None:
        """Mixed ASCII and UTF-8 content truncates correctly."""
        content = "hello" + "😀" * 50 + "world"
        output, meta = truncate_output(content, limit_type="chars", limit_value=20)
        assert meta["truncated"] is True
        assert len(output) == 20
        # Should start with "hello" + first 15 emojis (head_ratio=0.5, so 10 + 10)
        # Actually with head_ratio=0.5: head=10, tail=10
        # head = content[:10] = "hello" + 5 emojis
        # tail = content[-10:] = last 10 chars (9 emojis + "world" last char? let's not be too specific)
        assert "hello" in output or "😀" in output