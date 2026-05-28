"""Tests for ShellCommandTool (string-based shell command)."""

from __future__ import annotations

import shlex
import subprocess
import sys
import time
from pathlib import Path

import pytest

from agent_core.plugin import ToolWrapper
from codex_tools.shell_command_tool import ShellCommandTool


class _TestCancellation:
    def __init__(self) -> None:
        self._callbacks: dict[int, object] = {}
        self._next = 0

    def add_callback(self, callback):
        token = self._next
        self._next += 1
        self._callbacks[token] = callback
        return token

    def remove_callback(self, token: int) -> None:
        self._callbacks.pop(token, None)

    def cancel(self) -> None:
        for callback in list(self._callbacks.values()):
            callback()


def _pid_is_live(pid: int) -> bool:
    proc = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)],
        capture_output=True,
        text=True,
        check=False,
    )
    status = proc.stdout.strip()
    return bool(status) and not status.startswith("Z")


def _assert_pid_exits(pid: int, *, timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _pid_is_live(pid):
            return
        time.sleep(0.05)
    raise AssertionError(f"process {pid} remained alive past timeout")


def _write_sleepy_parent_script(path: Path, pid_file: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "import subprocess",
                "import sys",
                "import time",
                "",
                f"pid_file = {str(pid_file)!r}",
                "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])",
                "with open(pid_file, 'w', encoding='utf-8') as handle:",
                "    handle.write(str(child.pid))",
                "time.sleep(60)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


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
        assert schema["function"]["name"] == "shell_command"
        
        # Command should be string type
        command_prop = schema["function"]["parameters"]["properties"]["command"]
        assert command_prop["type"] == "string"

    def test_schema_has_workdir(self, tmp_path: Path) -> None:
        """Schema should include workdir parameter."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "workdir" in props
        assert props["workdir"]["type"] == "string"

    def test_schema_has_timeout_ms(self, tmp_path: Path) -> None:
        """Schema should include timeout_ms parameter."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "timeout_ms" in props
        assert props["timeout_ms"]["type"] == "number"

    def test_schema_has_login(self, tmp_path: Path) -> None:
        """Schema should include login parameter."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        schemas = wrapper.get_tool_schemas(state)
        
        props = schemas[0]["function"]["parameters"]["properties"]
        assert "login" in props
        assert props["login"]["type"] == "boolean"

    def test_command_is_required(self, tmp_path: Path) -> None:
        """Command should be in required fields."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        schemas = wrapper.get_tool_schemas(state)
        
        required = schemas[0]["function"]["parameters"]["required"]
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
    async def test_execute_stdin_reader_receives_eof(self, tmp_path: Path) -> None:
        """Non-streaming execution should not inherit interactive stdin."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        command = (
            f"{shlex.quote(sys.executable)} -c "
            "\"import sys; data = sys.stdin.read(); print('stdin-bytes', len(data))\""
        )

        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": command},
            state,
        )

        assert result["success"] is True
        assert result["exit_code"] == 0
        assert "stdin-bytes 0" in result["output"]

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
    async def test_missing_workdir_uses_configured_turn_cwd(self, tmp_path: Path) -> None:
        """Missing workdir should fall back to the configured turn cwd."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        command = f"{shlex.quote(sys.executable)} -c 'import os; print(os.getcwd())'"

        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": command},
            state,
        )

        assert result["success"] is True
        assert str(tmp_path) in result["output"]
        assert result["workdir"] == str(tmp_path)

    @pytest.mark.asyncio
    async def test_empty_workdir_uses_configured_turn_cwd(self, tmp_path: Path) -> None:
        """Empty-string workdir should fall back to the configured turn cwd."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({"working_directory": str(tmp_path)})
        command = f"{shlex.quote(sys.executable)} -c 'import os; print(os.getcwd())'"

        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": command, "workdir": ""},
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

        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({"working_directory": str(base_dir)})
        command = f"{shlex.quote(sys.executable)} -c 'import os; print(os.getcwd())'"

        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": command, "workdir": "nested"},
            state,
        )

        assert result["success"] is True
        assert str(subdir) in result["output"]
        assert result["workdir"] == str(subdir)

    @pytest.mark.asyncio
    async def test_intercepts_apply_patch_command_when_enabled(self, tmp_path: Path) -> None:
        """Shell command can route apply_patch heredocs to the internal patch runtime."""
        target = tmp_path / "hello.txt"
        target.write_text("before\n", encoding="utf-8")

        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init(
            {
                "working_directory": str(tmp_path),
                "allowed_paths": [str(tmp_path)],
                "intercept_apply_patch": True,
            }
        )

        patch_script = """apply_patch <<'PATCH'
*** Begin Patch
*** Update File: hello.txt
@@
-before
+after
*** End Patch
PATCH"""

        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": patch_script, "workdir": str(tmp_path)},
            state,
        )

        assert result["success"] is True
        assert result.get("intercepted_tool") == "apply_patch"
        assert target.read_text(encoding="utf-8") == "after\n"

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
    @pytest.mark.skipif(sys.platform == "win32", reason="uses POSIX ps semantics")
    async def test_timeout_kills_compound_shell_process_tree(self, tmp_path: Path) -> None:
        """Timeout should terminate shell descendants spawned by a compound script."""
        script_path = tmp_path / "spawn_child.py"
        pid_file = tmp_path / "child.pid"
        _write_sleepy_parent_script(script_path, pid_file)

        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})

        command = (
            f"{shlex.quote(sys.executable)} {shlex.quote(str(script_path))}\n"
            "echo after >/dev/null"
        )
        result = await wrapper.execute_tool_async(
            "shell_command",
            {"command": command, "timeout_ms": 300},
            state,
        )

        assert result["success"] is False
        assert result["timed_out"] is True
        assert result["exit_code"] is None

    @pytest.mark.asyncio
    async def test_invalid_workdir_returns_codex_like_spawn_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        monkeypatch.delenv("CRYSTAL_SHELL_ERROR_CONTEXT", raising=False)

        result = await wrapper.execute_tool_async(
            "shell_command",
            {
                "command": "date",
                "workdir": "/definitely/missing/workdir",
            },
            state,
        )

        assert result["success"] is False
        assert result["exit_code"] is None
        assert "Error: failed to spawn command:" in result["output"]
        assert "workdir: /definitely/missing/workdir" in result["output"]

    @pytest.mark.asyncio
    async def test_invalid_workdir_can_include_cloud_context(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        monkeypatch.setenv("CRYSTAL_SHELL_ERROR_CONTEXT", "1")
        monkeypatch.setenv("CLOUD_AGENT_INSTANCE_DIR", "/cloud-agent/instance")

        result = await wrapper.execute_tool_async(
            "shell_command",
            {
                "command": "date",
                "workdir": "/definitely/missing/workdir",
            },
            state,
        )

        assert result["success"] is False
        assert "Running in dockerized cloud environment." in result["output"]
        assert "Current working directory:" in result["output"]

    @pytest.mark.asyncio
    async def test_invalid_workdir_in_closed_cloud_session_includes_local_hint(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        monkeypatch.delenv("CRYSTAL_SHELL_ERROR_CONTEXT", raising=False)
        monkeypatch.delenv("CLOUD_AGENT_INSTANCE_DIR", raising=False)

        result = await wrapper.execute_tool_async(
            "shell_command",
            {
                "command": "date",
                "workdir": "/definitely/missing/workdir",
            },
            state,
            context={
                "session": {
                    "session_id": "session-1",
                    "metadata": {
                        "cloud_agent_last_runtime": {
                            "was_cloud": True,
                            "current_workdir": "/cloud-agent/instance/workspace",
                        }
                    },
                },
                "session_id": "session-1",
            },
        )

        assert result["success"] is False
        assert (
            "This session previously ran in a dockerized cloud environment."
            in result["output"]
        )
        assert "Current working directory:" in result["output"]
        assert "Last cloud working directory: /cloud-agent/instance/workspace" in result["output"]

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

    def test_format_tool_result_falls_back_to_error_when_output_missing(self) -> None:
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        state["_last_tool_context"] = {
            "session_id": "session-1",
            "tool_call_id": "call-1",
        }

        formatted = wrapper.format_tool_result(
            {
                "success": False,
                "error": "Error: failed to spawn command: No such file or directory (os error 2)\nworkdir: /missing",
            },
            state,
        )

        assert formatted.startswith("Error: failed to spawn command:")
        assert "workdir: /missing" in formatted

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

    def test_stream_stdin_reader_receives_eof(self, tmp_path: Path) -> None:
        """Streaming execution should not inherit interactive stdin."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        command = (
            f"{shlex.quote(sys.executable)} -c "
            "\"import sys; data = sys.stdin.read(); print('stdin-bytes', len(data))\""
        )

        chunks = list(
            wrapper.stream_tool(
                "shell_command",
                {"command": command},
                state,
            )
        )

        final_results = [c for c in chunks if isinstance(c, dict) and "success" in c]
        assert final_results
        final = final_results[-1]
        assert final["success"] is True
        assert final["exit_code"] == 0
        assert "stdin-bytes 0" in final["output"]

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

    def test_stream_invalid_workdir_returns_spawn_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        monkeypatch.delenv("CRYSTAL_SHELL_ERROR_CONTEXT", raising=False)

        chunks = list(
            wrapper.stream_tool(
                "shell_command",
                {"command": "date", "workdir": "/definitely/missing/workdir"},
                state,
            )
        )

        final_results = [c for c in chunks if isinstance(c, dict) and "success" in c]
        assert final_results
        final = final_results[-1]
        assert final["success"] is False
        assert "Error: failed to spawn command:" in final["output"]
        assert "workdir: /definitely/missing/workdir" in final["output"]

    def test_stream_cancel_stops_silent_process(self, tmp_path: Path) -> None:
        """Explicit cancellation should stop a running shell command promptly."""
        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})
        cancellation = _TestCancellation()
        command = f"{shlex.quote(sys.executable)} -c 'import time; time.sleep(60)'"

        chunks: list[dict] = []

        def _consume() -> None:
            chunks.extend(
                wrapper.stream_tool(
                    "shell_command",
                    {"command": command},
                    state,
                    cancellation=cancellation,
                )
            )

        import threading

        worker = threading.Thread(target=_consume)
        worker.start()
        time.sleep(0.2)
        cancellation.cancel()
        worker.join(timeout=5)
        assert not worker.is_alive()

        final_results = [c for c in chunks if isinstance(c, dict) and "success" in c]
        assert final_results
        final = final_results[-1]
        assert final["success"] is False
        assert final["cancelled"] is True
        assert final["timed_out"] is False
        assert final["exit_code"] is None
        assert final["duration_seconds"] < 5.0

    @pytest.mark.skipif(sys.platform == "win32", reason="uses POSIX ps semantics")
    def test_stream_timeout_kills_process_tree(self, tmp_path: Path) -> None:
        """Streaming timeout should terminate descendants, not only the shell PID."""
        script_path = tmp_path / "spawn_child.py"
        pid_file = tmp_path / "child.pid"
        _write_sleepy_parent_script(script_path, pid_file)

        wrapper = ToolWrapper(ShellCommandTool)
        state = wrapper.init({})

        command = (
            f"{shlex.quote(sys.executable)} {shlex.quote(str(script_path))}\n"
            "echo after >/dev/null"
        )
        chunks = list(
            wrapper.stream_tool(
                "shell_command",
                {"command": command, "timeout_ms": 300},
                state,
            )
        )

        final_results = [c for c in chunks if isinstance(c, dict) and "success" in c]
        assert final_results

        final = final_results[-1]
        assert final["success"] is False
        assert final["timed_out"] is True
        assert final["exit_code"] is None
        assert pid_file.exists()
        _assert_pid_exits(int(pid_file.read_text(encoding="utf-8")))


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